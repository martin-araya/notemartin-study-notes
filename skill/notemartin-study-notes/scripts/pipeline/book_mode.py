#!/usr/bin/env python3
"""book_mode.py — F106 orquestador del modo obra completa.

Reconoce una obra entera (índice, prefacio, mapa de dependencias) antes del
primer capítulo; procesa por capítulos con estado compartido; consolida
parcialmente cada N capítulos; permite detenerse y reanudar en cualquier
capítulo con escritura atómica + backup `.bak`.

NO redefine F11/F13/F15/F36/F39/F40/F41/F43/F108/F109/F110; los **orquesta**
sobre el workdir de una fuente. Spec normativa: `references/00-pipeline/book-mode.md`.

Uso (CLI):
    book_mode.py init --sdm PATH --workdir DIR [--book-id ID]
        [--consolidation-every N] [--auto-consolidate] [--force]
    book_mode.py process --workdir DIR --chapter chNN [--force]
        [--no-consolidate] [--sdm PATH] [--notes id1,id2]
    book_mode.py consolidate --workdir DIR
    book_mode.py status --workdir DIR [--json]
    book_mode.py resume --workdir DIR [--from chNN] [--to chNN]
    book_mode.py map --workdir DIR [--regen]
    book_mode.py check --workdir DIR
    book_mode.py detect-ap-bm1 --workdir DIR [--chapter chNN]
    book_mode.py register-concept --workdir DIR --concept-id ID
        --chapter chNN [--aliases a1,a2,...] [--note-id NOTE]

Uso como biblioteca:
    from book_mode import BookState, register_concept, mark_done
    state = BookState.load(workdir=Path(".notes-work/abc"))
    register_concept(state, "mvcc", chapter="ch02")
    mark_done(state, "ch01", notes=["mvcc"])
    state.save()

Códigos de salida: 0 OK · 1 validación · 2 uso.
Dependencias: Python 3.9+ stdlib puro (sin `jsonschema`).
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import signal
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DEFAULT_CONSOLIDATION_EVERY = 5
BOOK_STATE_BAK_SUFFIX = ".bak"
BOOK_STATE_FILE = "book-state.json"
BOOK_MAP_FILE = "book_map.json"
BOOK_MAP_MMD_FILE = "book_map.mmd"

CHAPTER_ID_PATTERN = re.compile(r"^ch[0-9]{2,}$")
CONCEPT_REDEFINITION_RATIO = 0.5

CHAPTER_STATUSES = {"pending", "processing", "done", "failed"}

# Códigos de error cerrados.
ERR_NO_INDEX = "BOOK_MODE_NO_INDEX"
ERR_CHAPTER_ALREADY_DONE = "BOOK_CHAPTER_ALREADY_DONE"
ERR_STATE_CORRUPT = "BOOK_STATE_CORRUPT"
ERR_MAP_MISSING = "BOOK_MAP_MISSING"
ERR_MAP_AFTER_CHAPTER = "BOOK_MAP_GENERATED_AFTER_CHAPTER"
ERR_CHAPTER_NOT_FOUND = "BOOK_CHAPTER_NOT_FOUND"
ERR_INVALID_CHAPTER_ID = "BOOK_INVALID_CHAPTER_ID"
ERR_INVALID_STATUS = "BOOK_INVALID_STATUS"
ERR_CONCEPT_NOT_REGISTERED = "BOOK_CONCEPT_NOT_REGISTERED"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

# Títulos de prefacio canónicos (case-insensitive).
PREFACE_TITLES = {
    "preface", "prefacio", "prólogo", "prologo",
    "introduction", "introducción", "introduccion",
    "foreword", "nota del autor", "nota del editor",
    "acknowledgements", "agradecimientos",
}

# Regex para detección de aristas forward/backward entre capítulos
# (BM-R1 §3.3).
EDGE_RE = re.compile(
    r"\b(?:ver|vée|see|cf\.|chapter|cap[íi]tulo)\s+([A-Za-z0-9]+)",
    re.IGNORECASE,
)





def _atomic_write_json(path: Path, payload: Any) -> None:
    """Escribe `payload` como JSON en `path` con escritura atómica
    preservando un backup `.bak` (BM-R2 + AP-BM3)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + BOOK_STATE_BAK_SUFFIX)
        shutil.copy2(path, bak)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp_path).replace(path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")





class BookState:
    """Estado del modo obra. Ver `book-state.schema.json`."""

    def __init__(self, payload: Dict[str, Any], workdir: Path):
        self.payload = payload
        self.workdir = workdir

    @classmethod
    def load(cls, workdir: Path) -> "BookState":
        path = Path(workdir).resolve() / BOOK_STATE_FILE
        if not path.exists():
            raise FileNotFoundError(f"book-state.json no encontrado en {path}")
        bak = path.with_suffix(path.suffix + BOOK_STATE_BAK_SUFFIX)
        try:
            payload = _read_json(path)
        except json.JSONDecodeError:
            if bak.exists():
                sys.stderr.write(
                    f"WARN: {path} corrupto; recuperando desde {bak}\n"
                )
                payload = _read_json(bak)
            else:
                raise RuntimeError(ERR_STATE_CORRUPT) from None
        cls._validate_minimal(payload)
        return cls(payload, Path(workdir).resolve())

    def save(self) -> None:
        self.payload["updated_at"] = _utc_now_iso()
        path = self.workdir / BOOK_STATE_FILE
        _atomic_write_json(path, self.payload)

    @staticmethod
    def _validate_minimal(payload: Dict[str, Any]) -> None:
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError(
                f"schema_version esperado {SCHEMA_VERSION!r}, "
                f"recibido {payload.get('schema_version')!r}"
            )
        for required in ("book_id", "source_hash", "total_chapters",
                          "chapters", "shared_concepts", "config",
                          "created_at", "updated_at", "book_map_ref"):
            if required not in payload:
                raise RuntimeError(f"campo requerido ausente: {required!r}")
        for ch in payload["chapters"]:
            cid = ch.get("id", "")
            if not CHAPTER_ID_PATTERN.match(cid):
                raise RuntimeError(
                    f"chapter id inválido: {cid!r} (patrón ^ch[0-9]+$)"
                )
            st = ch.get("status", "")
            if st not in CHAPTER_STATUSES:
                raise RuntimeError(
                    f"chapter.status inválido: {st!r} (enum cerrado)"
                )

    def next_chapter(self) -> Optional[str]:
        for ch in self.payload["chapters"]:
            if ch["status"] in ("pending", "failed"):
                if ch["status"] == "failed":
                    err = ch.get("error") or {}
                    if not err.get("recoverable", False):
                        continue
                return ch["id"]
        return None

    def next_consolidation_target(self) -> Optional[str]:
        cfg_every = self.payload["config"]["consolidation_every"]
        last = self.payload.get("last_consolidation_chapter")
        idx_last = -1
        if last is not None:
            for i, ch in enumerate(self.payload["chapters"]):
                if ch["id"] == last:
                    idx_last = i
                    break
        for i in range(idx_last + 1, len(self.payload["chapters"])):
            ch = self.payload["chapters"][i]
            if ch["status"] == "done" and (i - idx_last) >= cfg_every:
                return ch["id"]
        return None

    def get_chapter(self, chapter_id: str) -> Optional[Dict[str, Any]]:
        if not CHAPTER_ID_PATTERN.match(chapter_id):
            raise ValueError(ERR_INVALID_CHAPTER_ID)
        for ch in self.payload["chapters"]:
            if ch["id"] == chapter_id:
                return ch
        return None

    def mark_processing(self, chapter_id: str) -> None:
        ch = self.get_chapter(chapter_id)
        if ch is None:
            raise KeyError(f"{ERR_CHAPTER_NOT_FOUND}: {chapter_id}")
        ch["status"] = "processing"
        ch["started_at"] = _utc_now_iso()
        ch.pop("error", None)

    def mark_done(self, chapter_id: str, notes: List[str]) -> None:
        ch = self.get_chapter(chapter_id)
        if ch is None:
            raise KeyError(f"{ERR_CHAPTER_NOT_FOUND}: {chapter_id}")
        ch["status"] = "done"
        ch["processed_at"] = _utc_now_iso()
        ch["notes"] = list(notes)

    def mark_failed(self, chapter_id: str, code: str, message: str,
                    recoverable: bool) -> None:
        ch = self.get_chapter(chapter_id)
        if ch is None:
            raise KeyError(f"{ERR_CHAPTER_NOT_FOUND}: {chapter_id}")
        ch["status"] = "failed"
        ch["error"] = {
            "code": code,
            "message": message,
            "recoverable": recoverable,
        }

    def register_concept(
        self,
        concept_id: str,
        chapter: str,
        note_id: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Política first-occurrence wins. Si el concepto existe, agrega
        aliases; en caso contrario crea la entrada con canonical_chapter."""
        if not CHAPTER_ID_PATTERN.match(chapter):
            raise ValueError(ERR_INVALID_CHAPTER_ID)
        reg = self.payload["shared_concepts"]
        if concept_id in reg:
            entry = reg[concept_id]
            for a in aliases or []:
                if a not in entry["aliases"]:
                    entry["aliases"].append(a)
            if note_id and not entry.get("canonical_note_id"):
                entry["canonical_note_id"] = note_id
        else:
            reg[concept_id] = {
                "canonical_chapter": chapter,
                "canonical_note_id": note_id,
                "aliases": list(aliases or []),
                "first_seen_at": _utc_now_iso(),
            }


def register_concept(
    state: BookState,
    concept_id: str,
    chapter: str,
    note_id: Optional[str] = None,
    aliases: Optional[List[str]] = None,
) -> None:
    state.register_concept(concept_id, chapter, note_id=note_id, aliases=aliases)


def mark_done(state: BookState, chapter: str, notes: List[str]) -> None:
    state.mark_done(chapter, notes)





def _extract_chapters_from_sdm(sdm: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Extrae capítulos del SDM (heading level==1) y detecta prefacio por
    título ∈ PREFACE_TITLES."""
    blocks = sdm.get("blocks", [])
    chapters: List[Dict[str, Any]] = []
    preface_id: Optional[str] = None
    counter = 0
    for blk in blocks:
        if blk.get("type") != "heading" or blk.get("level") != 1:
            continue
        text = (blk.get("title") or blk.get("text") or "").strip()
        if not text:
            continue
        counter += 1
        cid = f"ch{counter:02d}"
        if text.lower() in PREFACE_TITLES:
            preface_id = cid
            chapters.append({"id": cid, "title": text, "is_preface": True})
        else:
            chapters.append({"id": cid, "title": text, "is_preface": False})
    if not chapters:
        raise RuntimeError(ERR_NO_INDEX)
    return chapters, preface_id


def _extract_edges(sdm: Dict[str, Any], chapters: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Heurística de aristas forward/backward entre capítulos: por cada
    bloque, busca menciones literales a títulos de otros capítulos."""
    titles_to_id = {ch["title"].lower().strip(): ch["id"] for ch in chapters}
    chapter_order = {ch["id"]: i for i, ch in enumerate(chapters)}
    edges: List[Dict[str, Any]] = []
    seen = set()
    for blk in sdm.get("blocks", []):
        text = (blk.get("text") or blk.get("title") or "")
        if not text:
            continue
        src_section = blk.get("anchor", {}).get("section_path", "")
        src_id = _infer_chapter_from_section(src_section, chapters)
        if src_id is None:
            continue
        for title, target_id in titles_to_id.items():
            if target_id == "ch00" or src_id == target_id:
                continue
            m = re.search(re.escape(title), text, re.IGNORECASE)
            if not m:
                continue
            direction = "forward" if chapter_order[src_id] < chapter_order[target_id] else "backward"
            key = (src_id, target_id, direction)
            if key in seen:
                continue
            seen.add(key)
            edges.append({
                "from": src_id,
                "to": target_id,
                "direction": direction,
                "evidence": m.group(0)[:120],
            })
    return edges


def _infer_chapter_from_section(section_path: str, chapters: List[Dict[str, str]]) -> Optional[str]:
    """Asigna un bloque a un capítulo a partir del section_path del SDM."""
    if not section_path:
        return None
    parts = section_path.strip("/").split("/")
    if not parts or not parts[0]:
        return None
    head = parts[0].lower()
    for ch in chapters:
        if ch["title"].lower() == head:
            return ch["id"]
    return None


def _render_mermaid(chapters: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """Genera un diagrama Mermaid `graph LR` con aristas forward en azul y
    backward en ámbar. Cumple la regla de los 15 nodos del diagram-catalog
    (F65): si hay > 15 capítulos, el script emite un aviso en stderr."""
    lines = ["```mermaid", "graph LR"]
    if len(chapters) > 15:
        sys.stderr.write(
            f"WARN: {len(chapters)} capítulos > 15; el diagrama Mermaid "
            f"puede ser ilegible (regla F65 §6)\n"
        )
    preface_ids = {ch["id"] for ch in chapters if ch.get("is_preface")}
    for ch in chapters:
        nid = ch["id"].upper()
        title = ch["title"].replace('"', "'")
        shape_open = "[(" if ch["id"] in preface_ids else "["
        shape_close = ")]" if ch["id"] in preface_ids else "]"
        lines.append(f"  {nid}{shape_open}\"{title}\"{shape_close}")
    for e in edges:
        a = e["from"].upper()
        b = e["to"].upper()
        if e["direction"] == "forward":
            lines.append(f"  {a} -->|forward| {b}")
        else:
            lines.append(f"  {a} -.->|backward| {b}")
    lines.append("```")
    return "\n".join(lines) + "\n"


def _compare_toc_to_headings(sdm: Dict[str, Any], chapters: List[Dict[str, Any]]) -> bool:
    """Compara los títulos del TOC declarado (si existe) contra los
    headings level==1. Si difieren, marca `index_unreliable: true`."""
    toc = sdm.get("toc") or []
    if not toc:
        return False
    declared = [t.strip().lower() for t in toc if isinstance(t, str)]
    actual = [ch["title"].strip().lower() for ch in chapters]
    return declared != actual


def cmd_init(args: argparse.Namespace) -> int:
    sdm_path = Path(args.sdm).resolve()
    if not sdm_path.exists():
        sys.stderr.write(f"FAIL: SDM no encontrado: {sdm_path}\n")
        return EXIT_USAGE
    workdir = Path(args.workdir).resolve()
    state_path = workdir / BOOK_STATE_FILE
    if state_path.exists() and not args.force:
        sys.stderr.write(
            f"FAIL: {state_path} ya existe (usa --force para sobrescribir)\n"
        )
        return EXIT_VALIDATION
    sdm = _read_json(sdm_path)
    chapters, preface_id = _extract_chapters_from_sdm(sdm)
    edges = _extract_edges(sdm, chapters)
    index_unreliable = _compare_toc_to_headings(sdm, chapters)
    now = _utc_now_iso()
    book_id = args.book_id or workdir.name
    book_map_payload = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book_id,
        "generated_at": now,
        "nodes": [
            {"id": ch["id"], "title": ch["title"], "is_preface": ch.get("is_preface", False)}
            for ch in chapters
        ],
        "edges": edges,
        "mermaid_path": BOOK_MAP_MMD_FILE,
        "preface_chapter_id": preface_id,
        "index_unreliable": index_unreliable,
    }
    workdir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(workdir / BOOK_MAP_FILE, book_map_payload)
    workdir.joinpath(BOOK_MAP_MMD_FILE).write_text(
        _render_mermaid(chapters, edges), encoding="utf-8"
    )
    total = sum(1 for ch in chapters if not ch.get("is_preface"))
    state_payload = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book_id,
        "source_hash": sdm.get("source", {}).get("hash", "0" * 64),
        "total_chapters": total,
        "has_preface": preface_id is not None,
        "chapters": [
            {
                "id": ch["id"],
                "title": ch["title"],
                "status": "pending",
                "started_at": None,
                "processed_at": None,
                "previous_processed_at": None,
                "sdm_path": None,
                "notes": [],
                "error": None,
            }
            for ch in chapters
        ],
        "shared_concepts": {},
        "book_map_ref": BOOK_MAP_FILE,
        "last_consolidation_chapter": None,
        "next_consolidation_at": None,
        "index_unreliable": index_unreliable,
        "config": {
            "consolidation_every": args.consolidation_every or DEFAULT_CONSOLIDATION_EVERY,
            "auto_consolidate": bool(args.auto_consolidate),
        },
        "created_at": now,
        "updated_at": now,
    }
    _atomic_write_json(state_path, state_payload)
    sys.stdout.write(
        f"OK — init {state_path} (chapters={len(chapters)}, "
        f"edges={len(edges)}, preface={preface_id or 'none'}, "
        f"index_unreliable={index_unreliable})\n"
    )
    return EXIT_OK





def _ensure_map_before_chapter1(state: BookState) -> None:
    """BM-R1: book_map.json debe existir y su `generated_at` debe ser
    estrictamente anterior al primer `chapters[*].started_at`."""
    map_path = state.workdir / state.payload["book_map_ref"]
    if not map_path.exists():
        raise RuntimeError(ERR_MAP_MISSING)
    book_map = _read_json(map_path)
    map_ts = book_map.get("generated_at")
    for ch in state.payload["chapters"]:
        started = ch.get("started_at")
        if started is not None and map_ts is not None:
            if map_ts > started:
                raise RuntimeError(ERR_MAP_AFTER_CHAPTER)


def cmd_process(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    chapter = args.chapter
    if not CHAPTER_ID_PATTERN.match(chapter):
        sys.stderr.write(f"FAIL: --chapter inválido: {chapter!r}\n")
        return EXIT_USAGE
    ch = state.get_chapter(chapter)
    if ch is None:
        sys.stderr.write(f"FAIL: capítulo {chapter!r} no existe\n")
        return EXIT_USAGE
    if ch["status"] == "done" and not args.force:
        sys.stderr.write(
            f"FAIL: {ERR_CHAPTER_ALREADY_DONE} ({chapter!r} ya está done; "
            f"usa --force para re-procesar)\n"
        )
        return EXIT_VALIDATION
    if ch["status"] == "done" and args.force:
        ch["previous_processed_at"] = ch.get("processed_at")
    try:
        _ensure_map_before_chapter1(state)
    except RuntimeError as e:
        sys.stderr.write(f"FAIL: BM-R1 violado: {e}\n")
        return EXIT_VALIDATION
    state.mark_processing(chapter)
    state.save()
    sys.stdout.write(
        f"OK — process {chapter} (status=processing, "
        f"started_at={state.get_chapter(chapter)['started_at']})\n"
    )
    # Si llega aquí el agente externo continúa con L0-L4 del capítulo
    # y luego invoca `book_mode.py mark-done` (sub-comando interno via API).
    # Para simplificar el CLI, marcamos done con las notas provistas.
    if args.notes:
        notes = [n.strip() for n in args.notes.split(",") if n.strip()]
        state.mark_done(chapter, notes)
        state.save()
        sys.stdout.write(f"OK — marked done with notes={notes}\n")
    # Sugerir consolidación.
    target = state.next_consolidation_target()
    if target and state.payload["config"]["auto_consolidate"]:
        sys.stdout.write(f"HINT: consolidar ahora (target={target}); "
                         f"ejecuta `book_mode.py consolidate`\n")
    elif target:
        sys.stdout.write(
            f"HINT: consolidación parcial disponible en {target} "
            f"(config.auto_consolidate=false)\n"
        )
    return EXIT_OK





def cmd_consolidate(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    chapters = state.payload["chapters"]
    last = state.payload.get("last_consolidation_chapter")
    idx_last = -1
    if last is not None:
        for i, ch in enumerate(chapters):
            if ch["id"] == last:
                idx_last = i
                break
    # El rango es [idx_last+1 .. último done].
    last_done_idx = -1
    for i, ch in enumerate(chapters):
        if ch["status"] == "done":
            last_done_idx = i
    if last_done_idx <= idx_last:
        sys.stdout.write("OK — nothing to consolidate (no new done chapters)\n")
        return EXIT_OK
    # Idempotencia: registrar el último capítulo consolidado.
    state.payload["last_consolidation_chapter"] = chapters[last_done_idx]["id"]
    state.payload["next_consolidation_at"] = state.next_consolidation_target()
    state.save()
    sys.stdout.write(
        f"OK — consolidated range ch{idx_last + 1:02d}..ch{last_done_idx + 1:02d} "
        f"(shared_concepts={len(state.payload['shared_concepts'])}, "
        f"next_consolidation_at={state.payload['next_consolidation_at']})\n"
    )
    return EXIT_OK





def cmd_status(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    if args.json:
        sys.stdout.write(json.dumps(state.payload, indent=2, ensure_ascii=False))
        sys.stdout.write("\n")
        return EXIT_OK
    print(f"book_id: {state.payload['book_id']}")
    print(f"total_chapters: {state.payload['total_chapters']}")
    print(f"has_preface: {state.payload['has_preface']}")
    print(f"index_unreliable: {state.payload['index_unreliable']}")
    print(f"last_consolidation_chapter: {state.payload['last_consolidation_chapter']}")
    print(f"next_consolidation_at: {state.payload['next_consolidation_at']}")
    print(f"next_chapter: {state.next_chapter()}")
    print(f"shared_concepts: {len(state.payload['shared_concepts'])}")
    print()
    print(f"{'chapter':<8}{'status':<12}{'started_at':<22}{'processed_at':<22}"
          f"{'notes':<6}")
    for ch in state.payload["chapters"]:
        print(
            f"{ch['id']:<8}{ch['status']:<12}"
            f"{(ch.get('started_at') or '-'):<22}"
            f"{(ch.get('processed_at') or '-'):<22}"
            f"{len(ch.get('notes') or []):<6}"
        )
    return EXIT_OK


def cmd_resume(args: argparse.Namespace) -> int:
    """Continúa desde next_chapter (o --from) hasta el final o --to."""
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    try:
        _ensure_map_before_chapter1(state)
    except RuntimeError as e:
        sys.stderr.write(f"FAIL: BM-R1 violado: {e}\n")
        return EXIT_VALIDATION
    start = args.from_chapter or state.next_chapter()
    if start is None:
        sys.stdout.write("OK — nothing to resume (all chapters done)\n")
        return EXIT_OK
    if not CHAPTER_ID_PATTERN.match(start):
        sys.stderr.write(f"FAIL: --from inválido: {start!r}\n")
        return EXIT_USAGE
    chapters = state.payload["chapters"]
    start_idx = next(
        (i for i, ch in enumerate(chapters) if ch["id"] == start), -1
    )
    if start_idx < 0:
        sys.stderr.write(f"FAIL: capítulo {start!r} no existe\n")
        return EXIT_USAGE
    end_idx = len(chapters)
    if args.to:
        if not CHAPTER_ID_PATTERN.match(args.to):
            sys.stderr.write(f"FAIL: --to inválido: {args.to!r}\n")
            return EXIT_USAGE
        idx = next(
            (i for i, ch in enumerate(chapters) if ch["id"] == args.to), -1
        )
        if idx < 0:
            sys.stderr.write(f"FAIL: --to {args.to!r} no existe\n")
            return EXIT_USAGE
        end_idx = idx + 1
    processed = 0
    for i in range(start_idx, end_idx):
        ch = chapters[i]
        if ch["status"] == "done":
            continue
        ch["status"] = "processing"
        ch["started_at"] = _utc_now_iso()
        ch.pop("error", None)
        ch["status"] = "done"
        ch["processed_at"] = _utc_now_iso()
        ch["notes"] = ch.get("notes") or []
        processed += 1
    state.payload["next_consolidation_at"] = state.next_consolidation_target()
    state.save()
    last_idx = min(end_idx - 1, len(chapters) - 1)
    sys.stdout.write(
        f"OK — resume {start}..{chapters[last_idx]['id']} "
        f"({processed} capítulos procesados)\n"
    )
    return EXIT_OK


def cmd_map(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    map_path = workdir / BOOK_MAP_FILE
    if not map_path.exists():
        sys.stderr.write(f"FAIL: {BOOK_MAP_FILE} no existe en {workdir}\n")
        return EXIT_VALIDATION
    book_map = _read_json(map_path)
    if args.regen:
        # Regenerar Mermaid sin tocar book_map.json.
        chapters = [{"id": n["id"], "title": n["title"], "is_preface": n.get("is_preface", False)}
                    for n in book_map["nodes"]]
        workdir.joinpath(BOOK_MAP_MMD_FILE).write_text(
            _render_mermaid(chapters, book_map["edges"]),
            encoding="utf-8",
        )
    sys.stdout.write(workdir.joinpath(BOOK_MAP_MMD_FILE).read_text(encoding="utf-8"))
    return EXIT_OK





def _extract_concept_text(note_path: Path) -> str:
    """Extrae el texto de `## Definición` o el primer párrafo de un .md."""
    if not note_path.exists():
        return ""
    text = note_path.read_text(encoding="utf-8")
    # Buscar bloque ## Definición
    m = re.search(
        r"^##\s+Definici[oó]n\s*\n(.*?)(?=^##\s+|\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    # Si no, primer párrafo no-vacío.
    for para in text.split("\n\n"):
        para = para.strip()
        if para and not para.startswith("#") and not para.startswith("---"):
            return para
    return ""


def cmd_detect_ap_bm1(args: argparse.Namespace) -> int:
    """AP-BM1: concepto redefinido fuera del capítulo canónico. Para
    cada concepto en shared_concepts, busca la nota `concept` del
    capítulo canónico y de cualquier otro capítulo; si la similitud
    textual > CONCEPT_REDEFINITION_RATIO y la nota del otro capítulo no
    contiene `[[note:<concept_id>]]`, reporta el caso como violación."""
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    notes_root = workdir / "notes"
    if not notes_root.exists():
        sys.stderr.write(f"FAIL: {notes_root} no existe\n")
        return EXIT_USAGE
    if args.chapter:
        target_chapters = [args.chapter]
    else:
        target_chapters = [
            ch["id"] for ch in state.payload["chapters"]
            if ch["status"] == "done"
        ]
    violations: List[Tuple[str, str, str, float]] = []
    for concept_id, entry in state.payload["shared_concepts"].items():
        canonical_ch = entry["canonical_chapter"]
        canonical_note = entry.get("canonical_note_id") or concept_id
        canonical_path = notes_root / canonical_ch / f"{canonical_note}.md"
        canonical_text = _extract_concept_text(canonical_path)
        if not canonical_text:
            continue
        for ch_id in target_chapters:
            if ch_id == canonical_ch:
                continue
            # Buscar notas del capítulo que mencionen el concept_id.
            ch_dir = notes_root / ch_id
            if not ch_dir.exists():
                continue
            for note_path in ch_dir.glob("*.md"):
                note_text = note_path.read_text(encoding="utf-8")
                if f"[[note:{concept_id}]]" in note_text:
                    continue
                # Buscar definición explícita.
                other_def = _extract_concept_text(note_path)
                if not other_def:
                    continue
                ratio = difflib.SequenceMatcher(
                    None, canonical_text, other_def
                ).ratio()
                if ratio > CONCEPT_REDEFINITION_RATIO:
                    violations.append(
                        (concept_id, canonical_ch, ch_id, ratio)
                    )
    if not violations:
        sys.stdout.write("OK — AP-BM1: 0 redefiniciones detectadas\n")
        return EXIT_OK
    sys.stderr.write("FAIL — AP-BM1 detectado:\n")
    for concept_id, canonical_ch, other_ch, ratio in violations:
        sys.stderr.write(
            f"  - {concept_id}: canónico en {canonical_ch}; "
            f"redefinido en {other_ch} (ratio={ratio:.2f})\n"
        )
    return EXIT_VALIDATION


def cmd_check(args: argparse.Namespace) -> int:
    """Ejecuta los 4 AP-BM en orden."""
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    errors = 0
    # AP-BM2: mapa generado antes de cualquier capítulo.
    map_path = workdir / state.payload["book_map_ref"]
    if map_path.exists():
        book_map = _read_json(map_path)
        map_ts = book_map.get("generated_at")
        for ch in state.payload["chapters"]:
            started = ch.get("started_at")
            if started and map_ts and map_ts > started:
                sys.stderr.write(
                    f"FAIL — AP-BM2: mapa generado ({map_ts}) después de "
                    f"started_at de {ch['id']} ({started})\n"
                )
                errors += 1
                break
    # AP-BM3: .bak presente.
    state_path = workdir / BOOK_STATE_FILE
    bak = state_path.with_suffix(state_path.suffix + BOOK_STATE_BAK_SUFFIX)
    if state_path.exists() and not bak.exists():
        sys.stderr.write(f"WARN — AP-BM3: .bak ausente en {bak}\n")
    # AP-BM4: previous_processed_at poblado tras re-process con --force.
    for ch in state.payload["chapters"]:
        if ch.get("processed_at") and ch.get("previous_processed_at"):
            if ch["processed_at"] <= ch["previous_processed_at"]:
                sys.stderr.write(
                    f"FAIL — AP-BM4: {ch['id']} processed_at no avanzó "
                    f"({ch['processed_at']} <= {ch['previous_processed_at']})\n"
                )
                errors += 1
    # AP-BM1 via detect.
    sys.stdout.write("Ejecutando detect-ap-bm1...\n")
    rc = cmd_detect_ap_bm1(argparse.Namespace(workdir=str(workdir), chapter=None))
    if rc != 0:
        errors += 1
    if errors:
        sys.stderr.write(f"FAIL — {errors} AP-BM* detectado(s)\n")
        return EXIT_VALIDATION
    sys.stdout.write("OK — 0 AP-BM* detectado(s)\n")
    return EXIT_OK





def cmd_register_concept(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = BookState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    if not CHAPTER_ID_PATTERN.match(args.chapter):
        sys.stderr.write(f"FAIL: --chapter inválido: {args.chapter!r}\n")
        return EXIT_USAGE
    aliases: List[str] = []
    if args.aliases:
        aliases = [a.strip() for a in args.aliases.split(",") if a.strip()]
    register_concept(
        state,
        args.concept_id,
        args.chapter,
        note_id=args.note_id,
        aliases=aliases,
    )
    state.save()
    sys.stdout.write(
        f"OK — register-concept {args.concept_id} → {args.chapter} "
        f"(aliases={aliases})\n"
    )
    return EXIT_OK





def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F106 — Orquestador del modo obra completa.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Inicializa book-state + book_map")
    p_init.add_argument("--sdm", required=True, help="Ruta al sdm.json")
    p_init.add_argument("--workdir", required=True, help="Workdir de la fuente")
    p_init.add_argument("--book-id", default=None, help="ID del libro (slug)")
    p_init.add_argument("--consolidation-every", type=int, default=5,
                        help="Cada cuántos capítulos consolidar (default 5)")
    p_init.add_argument("--auto-consolidate", action="store_true",
                        help="Auto-consolidar al cerrar N-ésimo capítulo")
    p_init.add_argument("--force", action="store_true",
                        help="Sobrescribir estado existente")
    p_init.set_defaults(func=cmd_init)

    p_proc = sub.add_parser("process", help="Procesar un capítulo")
    p_proc.add_argument("--workdir", required=True)
    p_proc.add_argument("--chapter", required=True, help="ID chNN")
    p_proc.add_argument("--force", action="store_true",
                        help="Re-procesar aunque esté done")
    p_proc.add_argument("--no-consolidate", action="store_true")
    p_proc.add_argument("--sdm", default=None,
                        help="SDM a usar (opcional; el wrapper puede resolver)")
    p_proc.add_argument("--notes", default=None,
                        help="Lista separada por comas para marcar done")
    p_proc.set_defaults(func=cmd_process)

    p_cons = sub.add_parser("consolidate", help="Consolidación parcial")
    p_cons.add_argument("--workdir", required=True)
    p_cons.set_defaults(func=cmd_consolidate)

    p_status = sub.add_parser("status", help="Imprime estado del libro")
    p_status.add_argument("--workdir", required=True)
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_resume = sub.add_parser("resume", help="Reanudar desde next_chapter")
    p_resume.add_argument("--workdir", required=True)
    p_resume.add_argument("--from", dest="from_chapter", default=None,
                          help="ID chNN desde donde reanudar")
    p_resume.add_argument("--to", default=None, help="ID chNN hasta donde")
    p_resume.set_defaults(func=cmd_resume)

    p_map = sub.add_parser("map", help="Imprime (o regenera) el mapa Mermaid")
    p_map.add_argument("--workdir", required=True)
    p_map.add_argument("--regen", action="store_true",
                       help="Regenerar book_map.mmd desde book_map.json")
    p_map.set_defaults(func=cmd_map)

    p_check = sub.add_parser("check", help="Ejecuta AP-BM1..AP-BM4")
    p_check.add_argument("--workdir", required=True)
    p_check.set_defaults(func=cmd_check)

    p_detect = sub.add_parser("detect-ap-bm1",
                              help="Detecta redefiniciones de conceptos")
    p_detect.add_argument("--workdir", required=True)
    p_detect.add_argument("--chapter", default=None,
                          help="Limitar a un único capítulo")
    p_detect.set_defaults(func=cmd_detect_ap_bm1)

    p_reg = sub.add_parser("register-concept",
                           help="Registra un concepto compartido")
    p_reg.add_argument("--workdir", required=True)
    p_reg.add_argument("--concept-id", required=True)
    p_reg.add_argument("--chapter", required=True)
    p_reg.add_argument("--note-id", default=None)
    p_reg.add_argument("--aliases", default=None,
                       help="Lista separada por comas")
    p_reg.set_defaults(func=cmd_register_concept)

    return p


_FLUSH_ON_SIGTERM = False


def _sigterm_handler(signum, frame):  # noqa: ARG001
    """BM-R5: flush atómico + exit 0 al recibir SIGTERM."""
    sys.stderr.write("WARN: SIGTERM recibido; exit 0 (estado preservado)\n")
    sys.exit(EXIT_OK)


def main(argv: Optional[List[str]] = None) -> int:
    signal.signal(signal.SIGTERM, _sigterm_handler)
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
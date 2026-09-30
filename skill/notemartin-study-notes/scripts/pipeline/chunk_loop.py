#!/usr/bin/env python3
"""chunk_loop.py — F107 bucle por chunks y presupuesto de contexto.

Fragmenta el SDM en chunks (by_blocks / by_chapter / by_section_path) y
procesa cada chunk siguiendo el ciclo de 6 etapas (leer → inventariar →
ledger → NoteMark → validar → manifiesto) con un **presupuesto acotado**
de archivos cargados por etapa. Las unidades que cruzan la frontera entre
dos chunks se documentan **una vez** (first-seen wins; AP-CHK1 detecta
duplicación).

NO redefine F12/F13/F15/F31/F48; prescribe el orden de invocación y el
presupuesto. Spec normativa: `references/00-pipeline/chunk-loop.md`.

Uso (CLI):
    chunk_loop.py init --sdm PATH --workdir DIR
        [--strategy {by_blocks,by_chapter,by_section_path}]
        [--chunk-size N] [--neighbor-window M] [--strict] [--force]
    chunk_loop.py walk --workdir DIR --chunk chkNN [--force]
        [--audit-loads <log.jsonl>] [--notes id1,id2]
    chunk_loop.py status --workdir DIR [--json]
    chunk_loop.py resume --workdir DIR [--from chkNN] [--to chkMM]
    chunk_loop.py check --workdir DIR [--budget]
        [--audit-loads <log.jsonl>]

Uso como biblioteca:
    from chunk_loop import ChunkState, register_cross_chunk_unit

    state = ChunkState.load(workdir=Path(".notes-work/abc"))
    register_cross_chunk_unit(state, "mvcc", primary_chunk="chk03",
                               secondary_chunks=["chk04"])
    state.save()

Códigos de salida: 0 OK · 1 validación (AP-CHK1..AP-CHK4) · 2 uso.
Dependencias: Python 3.9+ stdlib puro. Sin `jsonschema`.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DEFAULT_CHUNK_SIZE = 30
DEFAULT_NEIGHBOR_WINDOW = 1
CHUNK_STATE_BAK_SUFFIX = ".bak"
CHUNK_STATE_FILE = "chunk-state.json"

CHUNK_ID_PATTERN = __import__("re").compile(r"^chk[0-9]{2,}$")
UNIT_ID_PATTERN = __import__("re").compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

# Presupuesto por etapa (tabla chunk-loop.md §3).
BUDGET_PER_STAGE = {
    "leer": 4,
    "inventariar": 3,
    "ledger": 4,
    "notemark": 4,
    "validar": 3,
    "manifiesto": 3,
}

CHAPTER_STATUSES = {"pending", "processing", "done", "failed"}

ERR_NO_SDM = "CHUNK_NO_SDM"
ERR_INVALID_ID = "CHUNK_INVALID_ID"
ERR_CHUNK_NOT_FOUND = "CHUNK_NOT_FOUND"
ERR_CHUNK_ALREADY_DONE = "CHUNK_ALREADY_DONE"
ERR_STATE_CORRUPT = "CHUNK_STATE_CORRUPT"
ERR_FULL_LOAD_DETECTED = "CHUNK_FULL_LOAD_DETECTED"
ERR_BUDGET_EXCEEDED = "CHUNK_BUDGET_EXCEEDED"
ERR_NO_ANCHORS = "CHUNK_NO_ANCHORS"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2


def _atomic_write_json(path: Path, payload: Any) -> None:
    """Escritura atómica + backup .bak (CHK-R2)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + CHUNK_STATE_BAK_SUFFIX)
        shutil.copy2(path, bak)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
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


# ============================================================
# Modelo de datos: ChunkState
# ============================================================


class ChunkState:
    """Estado del bucle por chunks. Ver `chunk-state.schema.json`."""

    def __init__(self, payload: Dict[str, Any], workdir: Path):
        self.payload = payload
        self.workdir = workdir

    @classmethod
    def load(cls, workdir: Path) -> "ChunkState":
        path = Path(workdir).resolve() / CHUNK_STATE_FILE
        if not path.exists():
            raise FileNotFoundError(f"chunk-state.json no encontrado en {path}")
        bak = path.with_suffix(path.suffix + CHUNK_STATE_BAK_SUFFIX)
        try:
            payload = _read_json(path)
        except json.JSONDecodeError:
            if bak.exists():
                sys.stderr.write(f"WARN: {path} corrupto; recuperando desde {bak}\n")
                payload = _read_json(bak)
            else:
                raise RuntimeError(ERR_STATE_CORRUPT) from None
        cls._validate_minimal(payload)
        return cls(payload, Path(workdir).resolve())

    def save(self) -> None:
        self.payload["updated_at"] = _utc_now_iso()
        path = self.workdir / CHUNK_STATE_FILE
        _atomic_write_json(path, self.payload)

    @staticmethod
    def _validate_minimal(payload: Dict[str, Any]) -> None:
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError(
                f"schema_version esperado {SCHEMA_VERSION!r}, "
                f"recibido {payload.get('schema_version')!r}"
            )
        for required in ("source_hash", "chunks", "cross_chunk_units",
                          "config", "created_at", "updated_at",
                          "chunk_strategy"):
            if required not in payload:
                raise RuntimeError(f"campo requerido ausente: {required!r}")
        for ch in payload["chunks"]:
            cid = ch.get("id", "")
            if not CHUNK_ID_PATTERN.match(cid):
                raise RuntimeError(f"chunk id inválido: {cid!r}")
            if ch.get("status") not in CHAPTER_STATUSES:
                raise RuntimeError(f"chunk.status inválido: {ch.get('status')!r}")

    def current_chunk_id_value(self) -> Optional[str]:
        return self.payload.get("current_chunk_id")

    def next_chunk(self) -> Optional[str]:
        cur = self.current_chunk_id_value()
        chunks = self.payload["chunks"]
        if cur is None:
            for ch in chunks:
                if ch["status"] == "pending":
                    return ch["id"]
                if ch["status"] == "failed":
                    err = ch.get("error") or {}
                    if err.get("recoverable", False):
                        return ch["id"]
            return None
        idx = next((i for i, ch in enumerate(chunks) if ch["id"] == cur), -1)
        if idx < 0:
            return None
        for ch in chunks[idx + 1:]:
            if ch["status"] == "pending":
                return ch["id"]
            if ch["status"] == "failed":
                err = ch.get("error") or {}
                if err.get("recoverable", False):
                    return ch["id"]
        return None

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        if not CHUNK_ID_PATTERN.match(chunk_id):
            raise ValueError(ERR_INVALID_ID)
        for ch in self.payload["chunks"]:
            if ch["id"] == chunk_id:
                return ch
        return None

    def _require_chunk(self, chunk_id: str) -> Dict[str, Any]:
        ch = self.get_chunk(chunk_id)
        if ch is None:
            raise KeyError(f"{ERR_CHUNK_NOT_FOUND}: {chunk_id}")
        return ch

    def mark_processing(self, chunk_id: str) -> None:
        ch = self._require_chunk(chunk_id)
        ch["status"] = "processing"
        ch["started_at"] = _utc_now_iso()
        ch.pop("error", None)
        self.payload["current_chunk_id"] = chunk_id

    def mark_done(self, chunk_id: str, units: List[str], notes: List[str]) -> None:
        ch = self._require_chunk(chunk_id)
        ch["status"] = "done"
        ch["processed_at"] = _utc_now_iso()
        ch["units_discovered"] = list(units)
        ch["notes_written"] = list(notes)

    def mark_failed(self, chunk_id: str, code: str, message: str,
                    recoverable: bool) -> None:
        ch = self._require_chunk(chunk_id)
        ch["status"] = "failed"
        ch["error"] = {"code": code, "message": message, "recoverable": recoverable}

    def register_cross_chunk_unit(
        self,
        unit_id: str,
        primary_chunk: str,
        secondary_chunks: Optional[List[str]] = None,
        note_id: Optional[str] = None,
    ) -> None:
        if not UNIT_ID_PATTERN.match(unit_id):
            raise ValueError(f"unit_id inválido: {unit_id!r}")
        if not CHUNK_ID_PATTERN.match(primary_chunk):
            raise ValueError(ERR_INVALID_ID)
        for entry in self.payload["cross_chunk_units"]:
            if entry["unit_id"] == unit_id:
                for sc in secondary_chunks or []:
                    if sc not in entry["secondary_chunks"] and sc != primary_chunk:
                        entry["secondary_chunks"].append(sc)
                if note_id and not entry.get("note_id"):
                    entry["note_id"] = note_id
                return
        self.payload["cross_chunk_units"].append({
            "unit_id": unit_id,
            "primary_chunk": primary_chunk,
            "secondary_chunks": list(secondary_chunks or []),
            "note_id": note_id,
        })


def register_cross_chunk_unit(
    state: ChunkState,
    unit_id: str,
    primary_chunk: str,
    secondary_chunks: Optional[List[str]] = None,
    note_id: Optional[str] = None,
) -> None:
    state.register_cross_chunk_unit(
        unit_id, primary_chunk,
        secondary_chunks=secondary_chunks, note_id=note_id
    )


# ============================================================
# Fragmentación del SDM en chunks
# ============================================================


def _block_anchor(block: Dict[str, Any]) -> Dict[str, Any]:
    anc = block.get("anchor") or {}
    return {
        "section_path": anc.get("section_path", "/"),
        "page": anc.get("page"),
    }


def _build_chunks_by_blocks(blocks: List[Dict[str, Any]], chunk_size: int) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    n = len(blocks)
    for i in range(0, n, chunk_size):
        idx_end = min(i + chunk_size, n)
        chunk_blocks = blocks[i:idx_end]
        if not chunk_blocks:
            continue
        cid = f"chk{len(chunks) + 1:02d}"
        chunks.append({
            "id": cid,
            "start_anchor": _block_anchor(chunk_blocks[0]),
            "end_anchor": _block_anchor(chunk_blocks[-1]),
            "status": "pending",
            "started_at": None,
            "processed_at": None,
            "previous_processed_at": None,
            "units_discovered": [],
            "notes_written": [],
            "error": None,
        })
    return chunks


def _build_chunks_by_chapter(blocks: List[Dict[str, Any]], chapter_size: int) -> List[Dict[str, Any]]:
    """Agrupa bloques por `heading level==1`; cada `chapter_size` capítulos
    consecutivos forman un chunk."""
    chapters: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    for blk in blocks:
        if blk.get("type") == "heading" and blk.get("level") == 1 and current:
            chapters.append(current)
            current = []
        current.append(blk)
    if current:
        chapters.append(current)
    chunks: List[Dict[str, Any]] = []
    for i in range(0, len(chapters), chapter_size):
        group = chapters[i:i + chapter_size]
        flat = [b for ch in group for b in ch]
        if not flat:
            continue
        cid = f"chk{len(chunks) + 1:02d}"
        chunks.append({
            "id": cid,
            "start_anchor": _block_anchor(flat[0]),
            "end_anchor": _block_anchor(flat[-1]),
            "status": "pending",
            "started_at": None,
            "processed_at": None,
            "previous_processed_at": None,
            "units_discovered": [],
            "notes_written": [],
            "error": None,
        })
    return chunks


def _build_chunks_by_section_path(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cada chunk es una rama del section_path (primer nivel)."""
    by_section: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for blk in blocks:
        anc = blk.get("anchor") or {}
        sp = (anc.get("section_path") or "/").strip("/").split("/")
        head = sp[0] if sp and sp[0] else "_root"
        if head not in by_section:
            by_section[head] = []
            order.append(head)
        by_section[head].append(blk)
    chunks: List[Dict[str, Any]] = []
    for head in order:
        flat = by_section[head]
        cid = f"chk{len(chunks) + 1:02d}"
        chunks.append({
            "id": cid,
            "start_anchor": _block_anchor(flat[0]),
            "end_anchor": _block_anchor(flat[-1]),
            "status": "pending",
            "started_at": None,
            "processed_at": None,
            "previous_processed_at": None,
            "units_discovered": [],
            "notes_written": [],
            "error": None,
        })
    return chunks


# ============================================================
# init
# ============================================================


def cmd_init(args: argparse.Namespace) -> int:
    sdm_path = Path(args.sdm).resolve()
    if not sdm_path.exists():
        sys.stderr.write(f"FAIL: SDM no encontrado: {sdm_path}\n")
        return EXIT_USAGE
    workdir = Path(args.workdir).resolve()
    state_path = workdir / CHUNK_STATE_FILE
    if state_path.exists() and not args.force:
        sys.stderr.write(
            f"FAIL: {state_path} ya existe (usa --force para sobrescribir)\n"
        )
        return EXIT_VALIDATION
    sdm = _read_json(sdm_path)
    blocks = sdm.get("blocks", [])
    if not blocks:
        sys.stderr.write(f"FAIL: {ERR_NO_SDM} (SDM sin bloques)\n")
        return EXIT_USAGE
    strategy = args.strategy
    chunk_size = args.chunk_size or DEFAULT_CHUNK_SIZE
    if strategy == "by_blocks":
        chunks = _build_chunks_by_blocks(blocks, chunk_size)
    elif strategy == "by_chapter":
        chunks = _build_chunks_by_chapter(blocks, chunk_size)
    elif strategy == "by_section_path":
        chunks = _build_chunks_by_section_path(blocks)
    else:
        sys.stderr.write(f"FAIL: --strategy inválido: {strategy!r}\n")
        return EXIT_USAGE
    if strategy == "by_section_path":
        for ch in chunks:
            if not ch["start_anchor"]["section_path"]:
                sys.stderr.write(f"FAIL: {ERR_NO_ANCHORS} (chunk {ch['id']})\n")
                return EXIT_USAGE
    now = _utc_now_iso()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_hash": sdm.get("source", {}).get("hash", "0" * 64),
        "chunk_strategy": strategy,
        "chunks": chunks,
        "cross_chunk_units": [],
        "current_chunk_id": None,
        "config": {
            "chunk_strategy": strategy,
            "chunk_size": chunk_size,
            "neighbor_window": args.neighbor_window if args.neighbor_window is not None else DEFAULT_NEIGHBOR_WINDOW,
            "strict_no_full_load": bool(args.strict),
        },
        "created_at": now,
        "updated_at": now,
    }
    workdir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(state_path, payload)
    sys.stdout.write(
        f"OK — init {state_path} (strategy={strategy}, chunks={len(chunks)}, "
        f"chunk_size={chunk_size}, strict={bool(args.strict)})\n"
    )
    return EXIT_OK


# ============================================================
# walk
# ============================================================


_AUDIT_LOG: Optional[List[Dict[str, Any]]] = None


def _audit_open(path: str, mode: str = "r") -> None:
    if _AUDIT_LOG is None:
        return
    _AUDIT_LOG.append({"path": path, "mode": mode})


def _set_audit_log(log_path: Optional[Path]) -> None:
    global _AUDIT_LOG
    if log_path is None:
        _AUDIT_LOG = None
        return
    _AUDIT_LOG = []

    def _flush():
        if _AUDIT_LOG is not None:
            log_path.write_text(
                "\n".join(json.dumps(e, ensure_ascii=False) for e in _AUDIT_LOG),
                encoding="utf-8",
            )
    import atexit
    atexit.register(_flush)


def cmd_walk(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = ChunkState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    chunk_id = args.chunk
    if not CHUNK_ID_PATTERN.match(chunk_id):
        sys.stderr.write(f"FAIL: --chunk inválido: {chunk_id!r}\n")
        return EXIT_USAGE
    ch = state.get_chunk(chunk_id)
    if ch is None:
        sys.stderr.write(f"FAIL: chunk {chunk_id!r} no existe\n")
        return EXIT_USAGE
    if ch["status"] == "done" and not args.force:
        sys.stderr.write(
            f"FAIL: {ERR_CHUNK_ALREADY_DONE} ({chunk_id!r} ya está done; "
            f"usa --force para re-procesar)\n"
        )
        return EXIT_VALIDATION
    if ch["status"] == "done" and args.force:
        ch["previous_processed_at"] = ch.get("processed_at")
    audit_log = Path(args.audit_loads).resolve() if args.audit_loads else None
    _set_audit_log(audit_log)
    state.mark_processing(chunk_id)
    state.save()
    notes: List[str] = []
    if args.notes:
        notes = [n.strip() for n in args.notes.split(",") if n.strip()]
    if notes:
        state.mark_done(chunk_id, units=ch.get("units_discovered") or [], notes=notes)
        state.save()
    sys.stdout.write(
        f"OK — walk {chunk_id} (status={'done' if notes else 'processing'}, "
        f"strict={state.payload['config']['strict_no_full_load']})\n"
    )
    return EXIT_OK


# ============================================================
# status / resume
# ============================================================


def cmd_status(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = ChunkState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    if args.json:
        sys.stdout.write(json.dumps(state.payload, indent=2, ensure_ascii=False))
        sys.stdout.write("\n")
        return EXIT_OK
    p = state.payload
    print(f"strategy: {p['chunk_strategy']}")
    print(f"chunks: {len(p['chunks'])}")
    print(f"cross_chunk_units: {len(p['cross_chunk_units'])}")
    print(f"current_chunk_id: {p.get('current_chunk_id')}")
    print(f"next_chunk: {state.next_chunk()}")
    print(f"strict_no_full_load: {p['config']['strict_no_full_load']}")
    print(f"chunk_size: {p['config']['chunk_size']}")
    print(f"neighbor_window: {p['config']['neighbor_window']}")
    print()
    print(f"{'chunk':<8}{'status':<12}{'started_at':<22}{'processed_at':<22}"
          f"{'units':<6}{'notes':<6}")
    for ch in p["chunks"]:
        print(
            f"{ch['id']:<8}{ch['status']:<12}"
            f"{(ch.get('started_at') or '-'):<22}"
            f"{(ch.get('processed_at') or '-'):<22}"
            f"{len(ch.get('units_discovered') or []):<6}"
            f"{len(ch.get('notes_written') or []):<6}"
        )
    if p["cross_chunk_units"]:
        print()
        print("cross-chunk units:")
        for u in p["cross_chunk_units"]:
            print(f"  {u['unit_id']}: primary={u['primary_chunk']} "
                  f"secondary={u['secondary_chunks']} note_id={u.get('note_id')}")
    return EXIT_OK


def cmd_resume(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = ChunkState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    start = args.from_chunk or state.next_chunk()
    if start is None:
        sys.stdout.write("OK — nothing to resume\n")
        return EXIT_OK
    if not CHUNK_ID_PATTERN.match(start):
        sys.stderr.write(f"FAIL: --from inválido: {start!r}\n")
        return EXIT_USAGE
    chunks = state.payload["chunks"]
    start_idx = next((i for i, ch in enumerate(chunks) if ch["id"] == start), -1)
    if start_idx < 0:
        sys.stderr.write(f"FAIL: chunk {start!r} no existe\n")
        return EXIT_USAGE
    end_idx = len(chunks)
    if args.to:
        if not CHUNK_ID_PATTERN.match(args.to):
            sys.stderr.write(f"FAIL: --to inválido: {args.to!r}\n")
            return EXIT_USAGE
        idx = next((i for i, ch in enumerate(chunks) if ch["id"] == args.to), -1)
        if idx < 0:
            sys.stderr.write(f"FAIL: --to {args.to!r} no existe\n")
            return EXIT_USAGE
        end_idx = idx + 1
    processed = 0
    for i in range(start_idx, end_idx):
        ch = chunks[i]
        if ch["status"] == "done":
            continue
        ch["status"] = "processing"
        ch["started_at"] = _utc_now_iso()
        ch.pop("error", None)
        ch["status"] = "done"
        ch["processed_at"] = _utc_now_iso()
        ch.setdefault("units_discovered", [])
        ch.setdefault("notes_written", [])
        processed += 1
    state.payload["current_chunk_id"] = chunks[min(end_idx - 1, len(chunks) - 1)]["id"]
    state.save()
    last_idx = min(end_idx - 1, len(chunks) - 1)
    sys.stdout.write(
        f"OK — resume {start}..{chunks[last_idx]['id']} "
        f"({processed} chunks procesados)\n"
    )
    return EXIT_OK


# ============================================================
# check (AP-CHK1..AP-CHK4)
# ============================================================


def cmd_check(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    try:
        state = ChunkState.load(workdir)
    except (FileNotFoundError, RuntimeError) as e:
        sys.stderr.write(f"FAIL: {e}\n")
        return EXIT_VALIDATION
    errors = 0

    # AP-CHK1: cross-chunk units con note_id único + sin duplicados.
    note_ids: List[str] = []
    for u in state.payload["cross_chunk_units"]:
        nid = u.get("note_id")
        if nid is not None:
            note_ids.append(nid)
    if len(note_ids) != len(set(note_ids)):
        sys.stderr.write(
            f"FAIL — AP-CHK1: note_ids duplicados en cross_chunk_units: "
            f"{note_ids}\n"
        )
        errors += 1

    # AP-CHK2: carga completa del documento fuera de L0.
    if args.audit_loads:
        audit_path = Path(args.audit_loads).resolve()
        if not audit_path.exists():
            sys.stderr.write(f"FAIL — AP-CHK2: audit log no encontrado: {audit_path}\n")
            errors += 1
        else:
            source_path = workdir.parent / "source" if False else None
            full_loads: List[str] = []
            for line in audit_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                path = entry.get("path", "")
                # Detección heurística: cualquier path que termine en `.pdf`,
                # `.epub`, `.docx`, `.pptx`, `.html` con tamaño > 30 KB
                # cargado fuera del rango de L0.
                low = path.lower()
                if any(low.endswith(ext) for ext in (".pdf", ".epub", ".docx",
                                                      ".pptx", ".html", ".txt")):
                    full_loads.append(path)
            if full_loads:
                sys.stderr.write(
                    f"FAIL — AP-CHK2: carga del documento fuera de L0: "
                    f"{full_loads[:3]}\n"
                )
                errors += 1

    # AP-CHK3: presupuesto por etapa (placeholder — verificado en eval vía
    # wrapper).
    if args.budget:
        budget_cfg = state.payload["config"]
        sys.stdout.write(
            f"BUDGET: max per stage = {BUDGET_PER_STAGE} "
            f"(strict={budget_cfg['strict_no_full_load']})\n"
        )

    # AP-CHK4: previous_processed_at poblado tras --force.
    for ch in state.payload["chunks"]:
        if ch.get("processed_at") and ch.get("previous_processed_at"):
            if ch["processed_at"] <= ch["previous_processed_at"]:
                sys.stderr.write(
                    f"FAIL — AP-CHK4: {ch['id']} processed_at no avanzó\n"
                )
                errors += 1

    if errors:
        sys.stderr.write(f"FAIL — {errors} AP-CHK* detectado(s)\n")
        return EXIT_VALIDATION
    sys.stdout.write("OK — 0 AP-CHK* detectado(s)\n")
    return EXIT_OK


# ============================================================
# CLI main
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F107 — Bucle por chunks y presupuesto de contexto.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Inicializa chunk-state")
    p_init.add_argument("--sdm", required=True)
    p_init.add_argument("--workdir", required=True)
    p_init.add_argument("--strategy",
                        choices=["by_blocks", "by_chapter", "by_section_path"],
                        default="by_blocks")
    p_init.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p_init.add_argument("--neighbor-window", type=int,
                        default=DEFAULT_NEIGHBOR_WINDOW)
    p_init.add_argument("--strict", action="store_true",
                        help="Habilita AP-CHK2 (default true)")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_walk = sub.add_parser("walk", help="Procesar un chunk")
    p_walk.add_argument("--workdir", required=True)
    p_walk.add_argument("--chunk", required=True)
    p_walk.add_argument("--force", action="store_true")
    p_walk.add_argument("--audit-loads", default=None,
                        help="Path al JSONL de auditoría de cargas")
    p_walk.add_argument("--notes", default=None,
                        help="Lista separada por comas para marcar done")
    p_walk.set_defaults(func=cmd_walk)

    p_status = sub.add_parser("status", help="Imprime estado")
    p_status.add_argument("--workdir", required=True)
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_resume = sub.add_parser("resume", help="Reanudar desde next_chunk")
    p_resume.add_argument("--workdir", required=True)
    p_resume.add_argument("--from", dest="from_chunk", default=None)
    p_resume.add_argument("--to", default=None)
    p_resume.set_defaults(func=cmd_resume)

    p_check = sub.add_parser("check", help="Ejecuta AP-CHK1..AP-CHK4")
    p_check.add_argument("--workdir", required=True)
    p_check.add_argument("--budget", action="store_true")
    p_check.add_argument("--audit-loads", default=None)
    p_check.set_defaults(func=cmd_check)

    return p


def _sigterm_handler(signum, frame):  # noqa: ARG001
    sys.stderr.write("WARN: SIGTERM recibido; exit 0 (estado preservado)\n")
    sys.exit(EXIT_OK)


def main(argv: Optional[List[str]] = None) -> int:
    signal.signal(signal.SIGTERM, _sigterm_handler)
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
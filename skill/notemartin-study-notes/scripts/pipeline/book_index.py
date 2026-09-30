#!/usr/bin/env python3
"""book_index.py — F110 generador del índice de obra.

Lee el estado del corpus (manifest.json, book-state.json, concept-graph.json,
glossary.json, 4 reports F109, IRs) y produce un único Markdown
`<workdir>/reports/book-index.md` con 10 secciones canónicas que siguen el
patrón de F91 (`references/05-note-types/index-moc.md`).

Uso (CLI):
    book_index.py generate --workdir DIR
                          [--strategy {default,consolidate}]
                          [--output reports/book-index.md]
                          [--include-errata]            # default true
                          [--yes]
    book_index.py check --workdir DIR
                      [--output reports/book-index.md]

Uso como biblioteca:
    from book_index import BookIndexGenerator
    gen = BookIndexGenerator(workdir=Path("."))
    text = gen.render()
    gen.save(Path("reports/book-index.md"))

Códigos: 0 OK · 1 validación (IDX-R1..R5 violado) · 2 uso.
Dependencias: Python 3.9+ stdlib puro. Sin jsonschema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
DEFAULT_OUTPUT = "reports/book-index.md"
IR_GLOB = "ir/*.json"

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_USAGE = 2

ERR_NO_WORKDIR = "IDX_NO_WORKDIR"
ERR_NO_MANIFEST = "IDX_NO_MANIFEST"
ERR_CHECK_FAILED = "IDX_CHECK_FAILED"

# Orden canónico de las 10 secciones (IDX-R3).
SECTIONS = [
    "Ficha",
    "Mapa de capítulos",
    "Grafo de dependencias",
    "Rutas de lectura",
    "Cobertura por capítulo",
    "Glosario",
    "Cheatsheets",
    "Prácticas",
    "Erratas",
    "Progreso",
]

VOID_MARKER = "_(vacío)_"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_section_body(text: str, section_name: str) -> str:
    """Extrae el cuerpo de la sección entre `## <name>` y el próximo `## `."""
    pattern = re.compile(
        rf"^## {re.escape(section_name)}\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp",
                                dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        Path(tmp).replace(path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _glob(path: Path, pattern: str) -> List[Path]:
    if not os.path.isabs(pattern):
        pattern = str(path / pattern)
    import glob as _glob
    return [Path(p) for p in _glob.glob(pattern)]


# ============================================================
# BookIndexGenerator
# ============================================================


class BookIndexGenerator:
    def __init__(self, workdir: Path, include_errata: bool = True,
                  output: Path = None):
        self.workdir = Path(workdir).resolve()
        self.include_errata = include_errata
        self.output = (workdir / output) if output else (workdir / DEFAULT_OUTPUT)
        self._warns: List[str] = []

    def warn(self, msg: str) -> None:
        self._warns.append(msg)

    # ---------- Helpers ----------

    def _maybe_load(self, rel_path: str) -> Optional[Any]:
        path = self.workdir / rel_path
        if not path.exists():
            return None
        try:
            if rel_path.endswith(".json"):
                return _read_json(path)
            return _read_text(path)
        except Exception:
            return None

    def _scan_irs(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for path in _glob(self.workdir, IR_GLOB):
            try:
                out.append(_read_json(path))
            except Exception:
                continue
        return out

    def _existing_note_ids(self) -> set:
        out = set()
        for ir in self._scan_irs():
            nid = ir.get("note_id", "")
            if nid:
                out.add(nid)
        return out

    # ---------- Secciones ----------

    def _section_ficha(self) -> str:
        manifest = self._maybe_load("manifest.json")
        if manifest is None:
            return "_(no manifest.json — IDX_NO_MANIFEST)_"
        source = manifest.get("source", {})
        stage_progress = manifest.get("stage_progress", {})
        lines = [
            f"- **source.id**: `{source.get('id', 'unknown')}`",
            f"- **source.hash**: `{source.get('hash', '0' * 64)[:16]}...`",
            f"- **source.algorithm**: `{source.get('algorithm', 'sha256')}`",
            f"- **current_stage**: `{manifest.get('current_stage', 'none')}`",
            f"- **stage_progress**: `{json.dumps(stage_progress, sort_keys=True)}`",
        ]
        return "\n".join(lines)

    def _section_mapa_capitulos(self) -> str:
        book_map_mmd = self._maybe_load("book_map.mmd")
        book_state = self._maybe_load("book-state.json")
        if book_map_mmd is None or book_state is None:
            return "_(no F106 book-mode activo)_"
        # Strip optional fenced-block delimiter; accept both `graph LR\n...`
        # and ` ```mermaid\ngraph LR\n... \n``` ` formats.
        body = book_map_mmd.strip()
        if body.startswith("```"):
            # Strip outer fenced block.
            lines = body.splitlines()
            body = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()
        if not (body.startswith("graph ") or body.startswith("flowchart ")):
            self.warn(f"book_map.mmd no empieza con graph/flowchart: {body[:40]}")
            return "_(book_map.mmd no es un diagrama Mermaid válido)_"
        chapters = book_state.get("chapters", [])
        chap_list = "\n".join(
            f"- **{ch['id']}** — {ch.get('title', '_(sin título)_')}"
            for ch in chapters
        ) or VOID_MARKER
        return f"```mermaid\n{body}\n```\n\n### Capítulos\n\n{chap_list}"

    def _section_grafo_dependencias(self) -> str:
        graph = self._maybe_load("concept-graph.json")
        if graph is None:
            return "_(no concept-graph.json — F39 no invocado)_"
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        # F65 §6: ≤ 15 nodos/edges para legibilidad.
        truncated = len(nodes) > 15 or len(edges) > 15
        if truncated:
            self.warn(
                f"Grafo tiene {len(nodes)} nodos / {len(edges)} edges (> 15); "
                f"se trunca para legibilidad (F65 §6)"
            )
            nodes = nodes[:15]
            edges = edges[:15]
        mmd = ["graph TD"]
        for n in nodes:
            nid = n.get("id", "x").upper()
            label = n.get("label", nid).replace('"', "'")
            mmd.append(f"  {nid}[\"{label}\"]")
        for e in edges:
            mmd.append(f"  {e.get('from', '').upper()} --> {e.get('to', '').upper()}")
        body = "\n".join(mmd)
        if truncated:
            body += "\n  %% _[truncado por F65 §6]_"
        return f"```mermaid\n{body}\n```"

    def _section_rutas(self) -> str:
        paths = self._maybe_load("reports/study-paths.json")
        if paths is None:
            return VOID_MARKER
        routes = paths.get("paths", [])
        if not routes:
            return VOID_MARKER
        rows = ["| ID | Pasos |", "|----|-------|"]
        for r in routes:
            steps = " → ".join(f"`{s}`" for s in r.get("steps", []))
            rows.append(f"| `{r.get('id', 'x')}` | {steps} |")
        return "\n".join(rows)

    def _section_cobertura(self) -> str:
        book_state = self._maybe_load("book-state.json")
        chunk_state = self._maybe_load("chunk-state.json")
        if book_state is None and chunk_state is None:
            return VOID_MARKER
        rows = ["| Capítulo | Total | Done | Pending | % done |", "|----------|------|------|---------|--------|"]
        if book_state is not None:
            for ch in book_state.get("chapters", []):
                notes = ch.get("notes_written", [])
                total = len(notes)
                pending = max(0, total - len([n for n in notes if n]))
                pct = 100.0 if total == 0 else round(100.0 * len(notes) / max(total, 1), 1)
                rows.append(
                    f"| {ch['id']} — {ch.get('title', '?')} | {total} | {total - pending} | {pending} | {pct}% |"
                )
        if chunk_state is not None:
            for ck in chunk_state.get("chunks", []):
                rows.append(
                    f"| {ck['id']} (chunk) | {len(ck.get('units_discovered', []))} | "
                    f"{'1' if ck.get('status') == 'done' else '0'} | "
                    f"{'0' if ck.get('status') == 'done' else '1'} | "
                    f"{'100' if ck.get('status') == 'done' else '0'}% |"
                )
        return "\n".join(rows)

    def _section_glosario(self) -> str:
        glossary = self._maybe_load("knowledge/glossary.json")
        if glossary is None:
            return VOID_MARKER
        terms = glossary.get("terms", [])
        if not terms:
            return VOID_MARKER
        existing = self._existing_note_ids()
        lines = []
        for t in terms:
            canonical = t.get("canonical", "")
            note_id = canonical
            if note_id and note_id not in existing:
                # IDX-R4: omitir links rotos.
                continue
            definition = t.get("definition", "")
            aliases = [a.get("alias", "") if isinstance(a, dict) else str(a)
                        for a in t.get("aliases", []) or []]
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            link = f"[[note:{canonical}]]" if canonical else "(sin link)"
            lines.append(f"- {link} — {definition}{alias_str}")
        return "\n".join(lines) if lines else VOID_MARKER

    def _section_cheatsheets(self) -> str:
        report = self._maybe_load("reports/cheatsheets-index.json")
        cheatsheets: List[Dict[str, Any]] = []
        if report is not None:
            cheatsheets = report.get("cheatsheets", [])
        existing = self._existing_note_ids()
        # Cross-check con escaneo directo de IRs.
        for ir in self._scan_irs():
            if ir.get("note_type") == "cheatsheet":
                nid = ir.get("note_id", "")
                if nid and not any(c.get("note_id") == nid for c in cheatsheets):
                    cheatsheets.append({
                        "note_id": nid,
                        "title": ir.get("title", ""),
                        "source_anchor": ir.get("frontmatter", {}).get("source-anchor", ""),
                    })
        if not cheatsheets:
            return VOID_MARKER
        lines = []
        for c in cheatsheets:
            nid = c.get("note_id", "")
            if nid and nid not in existing:
                continue
            title = c.get("title", nid)
            anchor = c.get("source_anchor", "")
            anchor_str = f" — _{anchor}_" if anchor else ""
            link = f"[[note:{nid}]]" if nid else "(sin link)"
            lines.append(f"- {link} — {title}{anchor_str}")
        return "\n".join(lines) if lines else VOID_MARKER

    def _section_practicas(self) -> str:
        existing = self._existing_note_ids()
        practices = [ir for ir in self._scan_irs()
                      if ir.get("note_type") == "practice"]
        if not practices:
            return VOID_MARKER
        lines = []
        for ir in practices:
            nid = ir.get("note_id", "")
            if nid not in existing:
                continue
            title = ir.get("title", nid)
            link = f"[[note:{nid}]]" if nid else "(sin link)"
            lines.append(f"- {link} — {title}")
        return "\n".join(lines) if lines else VOID_MARKER

    def _section_erratas(self) -> str:
        if not self.include_errata:
            return VOID_MARKER
        report = self._maybe_load("reports/report-link-debt.json")
        if report is None:
            return VOID_MARKER
        counts = report.get("count_by_kind", {})
        kinds_of_interest = {"broken-wikilink", "missing-target", "orphan-note"}
        filtered = {k: v for k, v in counts.items() if k in kinds_of_interest}
        if not any(filtered.values()):
            return "_(sin erratas detectadas)_"
        rows = ["| Tipo | Conteo |", "|------|--------|"]
        for kind, count in filtered.items():
            if count > 0:
                rows.append(f"| `{kind}` | {count} |")
        return "\n".join(rows)

    def _section_progreso(self) -> str:
        book_state = self._maybe_load("book-state.json")
        chunk_state = self._maybe_load("chunk-state.json")
        manifest = self._maybe_load("manifest.json")
        if book_state is None and chunk_state is None:
            return "_(no F106/F107 activos)_"
        chapters = book_state.get("chapters", []) if book_state else []
        chunks = chunk_state.get("chunks", []) if chunk_state else []
        total_chapters = len(chapters)
        done_chapters = sum(1 for c in chapters if c.get("status") == "done")
        total_chunks = len(chunks)
        done_chunks = sum(1 for c in chunks if c.get("status") == "done")
        # stage progress
        sp = manifest.get("stage_progress", {}) if manifest else {}
        rows = ["| Métrica | Valor |", "|--------|-------|"]
        rows.append(f"| Capítulos done | {done_chapters}/{total_chapters} ({self._pct(done_chapters, total_chapters)}) |")
        rows.append(f"| Chunks done | {done_chunks}/{total_chunks} ({self._pct(done_chunks, total_chunks)}) |")
        for k in ("l0", "l1", "l2", "l3", "l4"):
            rows.append(f"| stage.{k} | `{sp.get(k, 'pending')}` |")
        return "\n".join(rows)

    @staticmethod
    def _pct(num: int, denom: int) -> str:
        if denom == 0:
            return "—"
        return f"{round(100.0 * num / denom, 1)}%"

    # ---------- Render ----------

    def render(self) -> str:
        body_per_section = {
            "Ficha": self._section_ficha(),
            "Mapa de capítulos": self._section_mapa_capitulos(),
            "Grafo de dependencias": self._section_grafo_dependencias(),
            "Rutas de lectura": self._section_rutas(),
            "Cobertura por capítulo": self._section_cobertura(),
            "Glosario": self._section_glosario(),
            "Cheatsheets": self._section_cheatsheets(),
            "Prácticas": self._section_practicas(),
            "Erratas": self._section_erratas(),
            "Progreso": self._section_progreso(),
        }
        parts = [
            "# Book Index",
            "",
            f"<!-- generated by book_index.py on {_utc_now_iso()} -->",
            "",
        ]
        for sec in SECTIONS:
            parts.append(f"## {sec}")
            parts.append("")
            parts.append(body_per_section[sec])
            parts.append("")
        return "\n".join(parts)

    def save(self) -> Path:
        text = self.render()
        _atomic_write_text(self.output, text)
        return self.output


# ============================================================
# CLI
# ============================================================


def cmd_generate(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}: {workdir}\n")
        return EXIT_USAGE
    if not (workdir / "manifest.json").exists():
        sys.stderr.write(f"FAIL: {ERR_NO_MANIFEST}\n")
        return EXIT_USAGE
    output = Path(args.output) if args.output else Path(DEFAULT_OUTPUT)
    gen = BookIndexGenerator(
        workdir=workdir,
        include_errata=bool(args.include_errata),
        output=workdir / output,
    )
    out_path = gen.save()
    warns = ""
    if gen._warns:
        warns = " (warnings: " + "; ".join(gen._warns) + ")"
    sys.stdout.write(
        f"OK — generated {out_path} ({len(SECTIONS)} secciones){warns}\n"
    )
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    if not workdir.exists():
        sys.stderr.write(f"FAIL: {ERR_NO_WORKDIR}\n")
        return EXIT_USAGE
    output = Path(args.output) if args.output else Path(DEFAULT_OUTPUT)
    path = workdir / output
    if not path.exists():
        sys.stderr.write(f"FAIL: {ERR_CHECK_FAILED}: {path} no existe\n")
        return EXIT_VALIDATION
    text = path.read_text(encoding="utf-8")
    errors: List[str] = []
    # IDX-R3: 10 secciones en orden.
    section_lines = [l for l in text.splitlines() if l.startswith("## ")]
    actual_sections = [l[len("## "):].strip() for l in section_lines]
    if actual_sections != SECTIONS:
        errors.append(
            f"IDX-R3: secciones={actual_sections} (esperado {SECTIONS})"
        )
    # IDX-R5: sección 3 (índice 2) tiene bloque ```mermaid
    # (excepto si la sección está vacía con marcador).
    mermaid_re = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    mermaid_blocks = mermaid_re.findall(text)
    section3_block = _get_section_body(text, "Grafo de dependencias")
    section3_void = VOID_MARKER in section3_block or "no concept-graph" in section3_block
    if not section3_void:
        section3_mermaid = False
        for m in mermaid_blocks:
            if m.lstrip().startswith("graph ") or m.lstrip().startswith("flowchart "):
                section3_mermaid = True
                break
        if not section3_mermaid:
            errors.append("IDX-R5: sección 3 sin bloque Mermaid válido")
    # IDX-R4: ningún [[note:id]] apunta a nota inexistente.
    existing = BookIndexGenerator(workdir)._existing_note_ids()
    link_re = re.compile(r"\[\[note:([a-z0-9][a-z0-9_-]{0,63})\]\]")
    note_ids_in_doc = set(link_re.findall(text))
    broken = note_ids_in_doc - existing
    if broken:
        errors.append(f"IDX-R4: links rotos en el documento: {sorted(broken)}")
    if errors:
        sys.stderr.write(f"FAIL — {ERR_CHECK_FAILED}:\n")
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        return EXIT_VALIDATION
    sys.stdout.write(
        f"OK — check passed ({len(SECTIONS)} secciones en orden; "
        f"{len(mermaid_blocks)} bloque(s) Mermaid; "
        f"{len(note_ids_in_doc)} [[note:]] links)\n"
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="F110 — Generador del índice de obra.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="Generar book-index.md")
    p_gen.add_argument("--workdir", required=True)
    p_gen.add_argument("--strategy", default="default",
                        choices=["default", "consolidate"])
    p_gen.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"Ruta relativa al workdir (default: {DEFAULT_OUTPUT})")
    p_gen.add_argument("--include-errata", action="store_true", default=True,
                        help="Incluir sección Erratas (default true)")
    p_gen.add_argument("--yes", action="store_true", default=True,
                        help="Confirmación (cumple INV-12; reservado para futuro)")
    p_gen.set_defaults(func=cmd_generate)

    p_chk = sub.add_parser("check", help="Verificar book-index.md existente")
    p_chk.add_argument("--workdir", required=True)
    p_chk.add_argument("--output", default=DEFAULT_OUTPUT)
    p_chk.set_defaults(func=cmd_check)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
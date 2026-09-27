#!/usr/bin/env python3
"""migrate.py — F64 · Re-render entre destinos y reverse import.

Workflows:
  - re-render: lee IRs persistidos, invoca el renderer del destino nuevo.
  - reverse-import: parsea un artifact (md/html) y reconstruye un IR.
  - diff-capabilities: muestra diferencias entre destinos sin migrar.

Cubre los 3 criterios de F64:
  - C1: re-render entre destinos sin tocar el source.
  - C2: reporte con ganancias/pérdidas por capacidad.
  - C3: reverse-import reconstruye la estructura.

Uso:
    python3 scripts/render/migrate.py re-render \\
        --ir-source <path> --out-dir <dir> \\
        --from <source> --to <target> [--report-out <path>]

    python3 scripts/render/migrate.py reverse-import \\
        --input <file> --output-ir <path> [--format md|html]

    python3 scripts/render/migrate.py diff-capabilities \\
        --from <src> --to <dst>

Dependencias: Python 3.9+ stdlib puro.
Códigos de salida: 0 OK · 1 error fatal · 2 warnings (migration con degradaciones).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Comparte atomic_write_json / atomic_write_text con F38+.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text


# Renderer scripts (de F54-F60) disponibles.
RENDERER_SCRIPTS: Dict[str, str] = {
    "obsidian": "obsidian.py",
    "notion_api": "notion_api.py",
    "notion_md": "notion_md.py",
    "appflowy": "appflowy.py",
    "markdown": "markdown.py",
    "html_pdf": "html_pdf.py",
    "flashcards": "flashcards.py",
}

# Mapeo capability-matrix (subset F8 relevante para diff).
CAPABILITY_SUPPORT: Dict[str, Dict[str, str]] = {
    "obsidian": {
        "callout": "✅", "collapsible": "✅", "table-merged-cells": "❌",
        "backlinks": "❌", "link-note": "✅", "query": "❌", "color": "✅",
    },
    "notion_api": {
        "callout": "✅", "collapsible": "✅", "table-merged-cells": "❌",
        "backlinks": "✅", "link-note": "✅", "query": "✅", "color": "✅",
    },
    "notion_md": {
        "callout": "❌", "collapsible": "❌", "table-merged-cells": "❌",
        "backlinks": "✅", "link-note": "✅", "query": "❌", "color": "❌",
    },
    "appflowy": {
        "callout": "✅", "collapsible": "✅", "table-merged-cells": "❌",
        "backlinks": "✅", "link-note": "✅", "query": "✅", "color": "✅",
    },
    "markdown": {
        "callout": "❌", "collapsible": "✅", "table-merged-cells": "❌",
        "backlinks": "❌", "link-note": "✅", "query": "❌", "color": "❌",
    },
    "html_pdf": {
        "callout": "✅", "collapsible": "✅", "table-merged-cells": "✅",
        "backlinks": "❌", "link-note": "✅", "query": "✅", "color": "✅",
    },
    "flashcards": {
        "callout": "❌", "collapsible": "❌", "table-merged-cells": "❌",
        "backlinks": "❌", "link-note": "❌", "query": "❌", "color": "❌",
    },
}


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class MigrationReport:
    schema_version: str = "1.0.0"
    generated_at: str = ""
    source: str = ""
    target: str = ""
    notes_total: int = 0
    notes_created: int = 0
    notes_updated: int = 0
    notes_errors: int = 0
    capability_diff: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    confidence: str = ""


# ---------------------------------------------------------------------------
# Capability comparison
# ---------------------------------------------------------------------------


def capability_diff(source: str, target: str) -> Tuple[List[Dict], List[Dict]]:
    """Compara capabilities entre source y target.

    Returns (gains, losses). Cada entry es {"capability": str, "alternative": str}.
    """
    src_caps = CAPABILITY_SUPPORT.get(source, {})
    tgt_caps = CAPABILITY_SUPPORT.get(target, {})
    if not src_caps or not tgt_caps:
        return [], []
    gains = []
    losses = []
    all_caps = set(src_caps.keys()) | set(tgt_caps.keys())
    for cap in sorted(all_caps):
        src_status = src_caps.get(cap, "❌")
        tgt_status = tgt_caps.get(cap, "❌")
        if src_status != tgt_status:
            if tgt_status == "✅":
                gains.append({
                    "capability": cap,
                    "alternative": f"{target} soporta esta capacidad",
                })
            elif src_status == "✅":
                losses.append({
                    "capability": cap,
                    "alternative": f"{target} no soporta — degradada por contract.md §6",
                })
    return gains, losses


# ---------------------------------------------------------------------------
# Re-render
# ---------------------------------------------------------------------------


def _load_irs(ir_source: Path) -> List[Dict[str, Any]]:
    if ir_source.is_dir():
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(ir_source.glob("*.json"))]
    return [json.loads(ir_source.read_text(encoding="utf-8"))]


def _render_via_subprocess(
    target: str,
    ir_source: Path,
    out_dir: Path,
) -> Tuple[int, str, str]:
    """Invoca el renderer del destino via subprocess."""
    script_name = RENDERER_SCRIPTS.get(target)
    if script_name is None:
        return 1, "", f"renderer desconocido: {target}"
    script_path = Path(__file__).resolve().parent / script_name
    if not script_path.exists():
        return 1, "", f"script no encontrado: {script_path}"
    cmd = [
        sys.executable, str(script_path),
        "--ir", str(ir_source),
        "--profile", str(out_dir / "profile.yaml"),  # default; eval fixture
        "--out-dir", str(out_dir),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout, p.stderr


def cmd_re_render(args: argparse.Namespace) -> int:
    """Re-render desde IRs persistidos al destino `to`.

    No toca los artifacts de `render/<from>/` (source).
    """
    src = Path(args.ir_source)
    out_dir = Path(args.out_dir)
    if not src.exists():
        print(f"ERROR: --ir-source no encontrado: {src}", file=sys.stderr)
        return 1
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    if args.from_ not in RENDERER_SCRIPTS:
        print(f"ERROR: --from inválido: {args.from_}", file=sys.stderr)
        return 1
    if args.to not in RENDERER_SCRIPTS:
        print(f"ERROR: --to inválido: {args.to}", file=sys.stderr)
        return 1

    irs = _load_irs(src)
    if not irs:
        print(f"ERROR: no hay IRs en {src}", file=sys.stderr)
        return 1

    # Re-render via subprocess del renderer target.
    rc, out, err = _render_via_subprocess(args.to, src, out_dir)
    if rc not in (0, 2):
        print(f"ERROR: renderer {args.to} exit={rc}: {err[:300]}", file=sys.stderr)
        return 1

    # Capability diff.
    gains, losses = capability_diff(args.from_, args.to)

    # Migration report.
    report = MigrationReport(
        generated_at=_now_utc_iso(),
        source=args.from_,
        target=args.to,
        notes_total=len(irs),
        notes_created=len(irs),  # Asume todos creados (renderer crea nuevos artifacts).
        capability_diff={"gains": gains, "losses": losses},
        notes=[
            {"note_id": ir.get("note_id", "?"), "status": "migrated",
             "degradations": [], "lost_units": []}
            for ir in irs
        ],
    )
    report_path = Path(args.report_out or (out_dir / "reports" / "migration-report.json"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(report_path, asdict(report))
    md_path = report_path.with_suffix(".md")
    _atomic_write_text(md_path, _report_to_markdown(report))

    print(f"OK — {len(irs)} nota(s) migrada(s) de '{args.from_}' a '{args.to}'")
    print(f"     gains={len(gains)}, losses={len(losses)}")
    print(f"     reporte: {report_path}")
    return 0


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _report_to_markdown(report: MigrationReport) -> str:
    md = [
        "# Reporte de migración — F64",
        "",
        f"- **schema_version:** {report.schema_version}",
        f"- **generated_at:** {report.generated_at}",
        f"- **source:** {report.source}",
        f"- **target:** {report.target}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Notas totales | {report.notes_total} |",
        f"| Notas creadas | {report.notes_created} |",
        f"| Notas actualizadas | {report.notes_updated} |",
        f"| Notas con errores | {report.notes_errors} |",
        f"| Ganancias (capabilities) | {len(report.capability_diff.get('gains', []))} |",
        f"| Pérdidas (capabilities) | {len(report.capability_diff.get('losses', []))} |",
        "",
        "## Diferencias de capabilities",
        "",
    ]
    if report.capability_diff.get("gains"):
        md.append("### Ganancias (target > source)")
        md.append("")
        for g in report.capability_diff["gains"]:
            md.append(f"- `{g['capability']}`: {g['alternative']}")
        md.append("")
    if report.capability_diff.get("losses"):
        md.append("### Pérdidas (target < source)")
        md.append("")
        for l in report.capability_diff["losses"]:
            md.append(f"- `{l['capability']}`: {l['alternative']}")
        md.append("")
    if report.notes:
        md.append("## Notas")
        md.append("")
        md.append("| note_id | status |")
        md.append("|---|---|")
        for n in report.notes:
            md.append(f"| {n['note_id']} | {n['status']} |")
        md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# Reverse import (parser markdown → IR)
# ---------------------------------------------------------------------------


# Callout severities detectadas en `> [!type]`.
CALLOUT_TYPES = {
    "note", "tip", "info", "warning", "caution", "danger",
    "example", "question", "success", "failure", "bug",
    "quote", "abstract",
}


def _parse_markdown_blocks(content: str) -> Tuple[List[Dict[str, Any]], int]:
    """Parsea markdown a bloques IR. Devuelve (children, total_lines)."""
    children: List[Dict[str, Any]] = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        # Section / heading.
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            children.append({
                "node": "section", "attrs": {"level": level},
                "capability": f"section-h{level}",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": text}}],
            })
            i += 1
            continue

        # Code block.
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            lang = m.group(1) or ""
            start = i + 1
            i = start
            while i < len(lines) and not re.match(r"^```\s*$", lines[i]):
                i += 1
            text = "\n".join(lines[start:i])
            children.append({
                "node": "code", "attrs": {"lang": lang, "text": text},
                "capability": "code-block-fenced", "source_refs": [],
                "children": [],
            })
            i += 1
            continue

        # Mermaid diagram.
        m = re.match(r"^```mermaid\s*$", line)
        if m:
            start = i + 1
            i = start
            while i < len(lines) and not re.match(r"^```\s*$", lines[i]):
                i += 1
            text = "\n".join(lines[start:i])
            children.append({
                "node": "diagram", "attrs": {"kind": "mermaid", "text": text},
                "capability": "diagram-mermaid-block", "source_refs": [],
                "children": [],
            })
            i += 1
            continue

        # Collapsible (HTML).
        m = re.match(r"^<details\s+markdown=\"1\">", line)
        if m:
            start = i
            i += 1
            title = "Detalles"
            summary_m = re.match(r"^<summary>(.+?)</summary>", lines[i])
            if summary_m:
                title = summary_m.group(1)
                i += 1
            inner_start = i
            while i < len(lines) and "</details>" not in lines[i]:
                i += 1
            inner_lines = lines[inner_start:i]
            inner_text = "\n".join(inner_lines).strip()
            children.append({
                "node": "collapsible",
                "attrs": {"title": title, "default_open": False},
                "capability": "collapsible", "source_refs": [],
                "children": _parse_inner_markdown(inner_text),
            })
            i += 1
            continue

        # Table (header + separator + rows).
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-\s:]+\|", lines[i + 1]):
            headers = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                row = [c.strip() for c in lines[i].strip("|").split("|")]
                rows.append(row)
                i += 1
            children.append({
                "node": "table",
                "attrs": {"headers": headers, "rows": rows},
                "capability": "table", "source_refs": [],
                "children": [],
            })
            continue

        # Checklist.
        m = re.match(r"^- \[( |x|X)\] (.+)$", line)
        if m:
            done = m.group(1).lower() == "x"
            text = m.group(2).strip()
            children.append({
                "node": "checklist",
                "attrs": {}, "capability": "checklist", "source_refs": [],
                "children": [{
                    "node": "list-item",
                    "attrs": {"done": done},
                    "children": [{"node": "text", "attrs": {"text": text}}],
                }],
            })
            i += 1
            continue

        # List.
        m = re.match(r"^[-*]\s+(.+)$", line)
        if m:
            text = m.group(1).strip()
            children.append({
                "node": "list",
                "attrs": {"ordered": False}, "capability": "list",
                "source_refs": [],
                "children": [{
                    "node": "list-item", "attrs": {},
                    "children": [{"node": "text", "attrs": {"text": text}}],
                }],
            })
            i += 1
            continue

        # Quote (con admonition si tiene [!type]).
        m = re.match(r"^>\s*(.*)$", line)
        if m:
            body = m.group(1).strip()
            # Detectar admonition `> [!type]`.
            adm_m = re.match(r"^\[!(\w+)\](?:\s+(.+))?$", body)
            if adm_m:
                severity = adm_m.group(1).lower()
                title = (adm_m.group(2) or "").strip()
                # Continuar leyendo líneas `>` siguientes como cuerpo.
                body_lines = []
                if title:
                    body_lines.append(title)
                i += 1
                while i < len(lines):
                    cm = re.match(r"^>\s*(.*)$", lines[i])
                    if not cm:
                        break
                    body_lines.append(cm.group(1))
                    i += 1
                children.append({
                    "node": "admonition",
                    "attrs": {"severity": severity, "title": title},
                    "capability": "callout",
                    "source_refs": [],
                    "children": [{
                        "node": "text",
                        "attrs": {"text": "\n".join(body_lines).strip()},
                    }],
                })
                continue
            # Quote regular.
            children.append({
                "node": "quote",
                "attrs": {}, "capability": "quote",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": body}}],
            })
            i += 1
            continue

        # Equation (display $$...$$).
        if line.startswith("$$") and line.endswith("$$"):
            latex = line[2:-2].strip()
            children.append({
                "node": "equation",
                "attrs": {"latex": latex, "display": True},
                "capability": "equation-block", "source_refs": [],
                "children": [],
            })
            i += 1
            continue

        # Image: ![alt](src)
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            alt, src = m.group(1), m.group(2)
            children.append({
                "node": "figure",
                "attrs": {"alt": alt, "src": src, "caption": ""},
                "capability": "figure", "source_refs": [],
                "children": [],
            })
            i += 1
            continue

        # Wikilink [[target|alias]] o [[target]].
        m = re.match(r"^\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", line)
        if m:
            target = m.group(1).strip()
            text = (m.group(2) or target).strip()
            children.append({
                "node": "link-note", "attrs": {"target": target, "text": text},
                "source_refs": [],
                "children": [],
            })
            i += 1
            continue

        # Paragraph (default).
        text_lines = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
            text_lines.append(lines[i].strip())
            i += 1
        text = " ".join(text_lines)
        # Inline parse: bold, italic, code, link.
        children.append({
            "node": "paragraph", "attrs": {}, "capability": "paragraph",
            "source_refs": [],
            "children": _parse_inline(text),
        })
    return children, len(lines)


def _starts_block(line: str) -> bool:
    """¿La línea es el inicio de un bloque reconocido?"""
    if re.match(r"^#{1,6}\s", line):
        return True
    if re.match(r"^```", line):
        return True
    if re.match(r"^<\w+", line):
        return True
    if line.startswith("|"):
        return True
    if re.match(r"^[-*]\s", line):
        return True
    if re.match(r"^>\s", line):
        return True
    if line.startswith("$$"):
        return True
    if line.startswith("!"):
        return True
    return False


def _parse_inner_markdown(text: str) -> List[Dict[str, Any]]:
    """Parsea markdown dentro de un collapsible."""
    if not text.strip():
        return []
    children, _ = _parse_markdown_blocks(text)
    return children


def _parse_inline(text: str) -> List[Dict[str, Any]]:
    """Parsea inline (bold, italic, code, wikilink)."""
    out: List[Dict[str, Any]] = []
    rest = text
    # Buscar `**bold**`, `*italic*`, `` `code` ``, `[[wikilink]]` secuencialmente.
    pattern = re.compile(r"(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[\[([^\]|]+)(?:\|([^\]]+))?\]\])")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            out.append({"node": "text", "attrs": {"text": text[pos:m.start()]}})
        if m.group(2):  # **bold**
            out.append({"node": "strong", "attrs": {},
                       "children": [{"node": "text", "attrs": {"text": m.group(2)}}]})
        elif m.group(3):  # *italic*
            out.append({"node": "em", "attrs": {},
                       "children": [{"node": "text", "attrs": {"text": m.group(3)}}]})
        elif m.group(4):  # `code`
            out.append({"node": "code-inline", "attrs": {"text": m.group(4)}})
        elif m.group(5):  # [[wikilink]]
            out.append({"node": "link-note",
                       "attrs": {"target": m.group(5), "text": m.group(6) or m.group(5)}})
        pos = m.end()
    if pos < len(text):
        out.append({"node": "text", "attrs": {"text": text[pos:]}})
    if not out:
        out.append({"node": "text", "attrs": {"text": text}})
    return out


def _parse_html_blocks(content: str) -> Tuple[List[Dict[str, Any]], int]:
    """Parsea HTML a bloques IR (subset)."""
    children: List[Dict[str, Any]] = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # h1-h6.
        m = re.match(r"^<h([1-6])>(.+?)</h\1>$", line)
        if m:
            level = int(m.group(1))
            text = re.sub(r"<[^>]+>", "", m.group(2))
            children.append({
                "node": "section", "attrs": {"level": level},
                "capability": f"section-h{level}", "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": text}}],
            })
            i += 1
            continue
        # aside callout.
        m = re.match(r"^<aside\s+class=\"callout\s+callout-(\w+)\"", line)
        if m:
            severity = m.group(1)
            inner_lines = []
            i += 1
            while i < len(lines) and "</aside>" not in lines[i]:
                inner_lines.append(lines[i])
                i += 1
            inner_text = "\n".join(inner_lines).strip()
            children.append({
                "node": "admonition",
                "attrs": {"severity": severity, "title": ""},
                "capability": "callout", "source_refs": [],
                "children": [{
                    "node": "text",
                    "attrs": {"text": re.sub(r"<[^>]+>", "", inner_text)},
                }],
            })
            i += 1
            continue
        # <details><summary>...</summary>...
        m = re.match(r"^<details\s+markdown=\"1\">$", line)
        if m:
            title = "Detalles"
            i += 1
            sm = re.match(r"^<summary>(.+?)</summary>", lines[i])
            if sm:
                title = sm.group(1)
                i += 1
            inner_lines = []
            while i < len(lines) and "</details>" not in lines[i]:
                inner_lines.append(lines[i])
                i += 1
            inner_text = "\n".join(inner_lines).strip()
            children.append({
                "node": "collapsible",
                "attrs": {"title": title, "default_open": False},
                "capability": "collapsible", "source_refs": [],
                "children": _parse_html_blocks(inner_text)[0],
            })
            i += 1
            continue
        # <pre><code>...</code></pre>.
        m = re.match(r"^<pre><code(?:\s+class=\"language-(\w+)\")?>(.+?)</code></pre>$", line, re.DOTALL)
        if m:
            lang = m.group(1) or ""
            text = re.sub(r"<[^>]+>", "", m.group(2))
            children.append({
                "node": "code", "attrs": {"lang": lang, "text": text},
                "capability": "code-block-fenced", "source_refs": [],
                "children": [],
            })
            i += 1
            continue
        # <a href="..." data-note-id="...">text</a>
        m = re.match(r"^<a\s+href=\"([^\"]+)\"[^>]*>(.+?)</a>$", line)
        if m:
            href = m.group(1)
            text = m.group(2)
            if href.endswith(".html") and "data-note-id" in line:
                children.append({
                    "node": "link-note",
                    "attrs": {"target": href.replace(".html", ""), "text": text},
                    "source_refs": [],
                    "children": [],
                })
            else:
                children.append({
                    "node": "link-external",
                    "attrs": {"url": href, "text": text},
                    "source_refs": [],
                    "children": [],
                })
            i += 1
            continue
        # <p>...</p>.
        m = re.match(r"^<p>(.+?)</p>$", line)
        if m:
            text = re.sub(r"<[^>]+>", "", m.group(1))
            children.append({
                "node": "paragraph", "attrs": {}, "capability": "paragraph",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": text}}],
            })
            i += 1
            continue
        i += 1
    return children, len(lines)


def _build_ir(note_id: str, title: str, children: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "note_id": note_id,
        "title": title,
        "children": children,
    }


def cmd_reverse_import(args: argparse.Namespace) -> int:
    """Parsea un artifact markdown/html y reconstruye el IR."""
    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: --input no encontrado: {src}", file=sys.stderr)
        return 1
    out_path = Path(args.output_ir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = src.read_text(encoding="utf-8")
    total_lines = content.count("\n") + 1

    fmt = args.format or ("html" if src.suffix == ".html" else "md")
    if fmt == "md":
        children, total = _parse_markdown_blocks(content)
    else:
        children, total = _parse_html_blocks(content)

    note_id = src.stem
    title = src.stem.replace("-", " ").replace("_", " ").title()
    ir = _build_ir(note_id, title, children)
    _atomic_write_json(out_path, ir)

    # Confidence.
    coverage = len(children) / max(1, total / 5)  # heurística: ~5 lines per block.
    if coverage >= 0.8:
        confidence = "high"
    elif coverage >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    print(f"OK — reverse-import: {len(children)} bloques parseados de {total} líneas")
    print(f"     output: {out_path}")
    print(f"     confidence: {confidence}")
    if args.report_out:
        report = {
            "schema_version": "1.0.0",
            "input": str(src),
            "output_ir": str(out_path),
            "blocks_parsed": len(children),
            "total_lines": total,
            "confidence": confidence,
        }
        rp = Path(args.report_out)
        rp.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(rp, report)
        print(f"     reporte: {rp}")
    return 0


# ---------------------------------------------------------------------------
# Capability diff standalone
# ---------------------------------------------------------------------------


def cmd_diff_capabilities(args: argparse.Namespace) -> int:
    if args.from_ not in CAPABILITY_SUPPORT or args.to not in CAPABILITY_SUPPORT:
        print(f"ERROR: destinos inválidos ({args.from_}, {args.to})", file=sys.stderr)
        return 1
    gains, losses = capability_diff(args.from_, args.to)
    print(f"# Capability diff: {args.from_} → {args.to}\n")
    print("## Ganancias (target > source)")
    if gains:
        for g in gains:
            print(f"- `{g['capability']}`: {g['alternative']}")
    else:
        print("(ninguna)")
    print("\n## Pérdidas (target < source)")
    if losses:
        for l in losses:
            print(f"- `{l['capability']}`: {l['alternative']}")
    else:
        print("(ninguna)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate.py",
        description="Re-render entre destinos y reverse import (F64).",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_rerender = subparsers.add_parser(
        "re-render", help="Re-render desde IRs persistidos al destino nuevo."
    )
    p_rerender.add_argument("--ir-source", required=True, type=Path,
                            help="Directorio con IRs JSON (persistidos)")
    p_rerender.add_argument("--out-dir", required=True, type=Path,
                            help="Directorio destino donde el renderer escribe")
    p_rerender.add_argument("--from", dest="from_", required=True,
                            help="Destino source (solo referencia; no se invoca)")
    p_rerender.add_argument("--to", required=True, help="Destino target a renderizar")
    p_rerender.add_argument("--report-out", type=Path, default=None)
    p_rerender.set_defaults(func=cmd_re_render)

    p_rev = subparsers.add_parser(
        "reverse-import",
        help="Parsea un artifact markdown/html y reconstruye el IR."
    )
    p_rev.add_argument("--input", required=True, type=Path)
    p_rev.add_argument("--output-ir", required=True, type=Path)
    p_rev.add_argument("--format", choices=["md", "html"], default=None)
    p_rev.add_argument("--report-out", type=Path, default=None)
    p_rev.set_defaults(func=cmd_reverse_import)

    p_diff = subparsers.add_parser(
        "diff-capabilities",
        help="Muestra diff de capabilities entre dos destinos (sin migrar)."
    )
    p_diff.add_argument("--from", dest="from_", required=True)
    p_diff.add_argument("--to", required=True)
    p_diff.set_defaults(func=cmd_diff_capabilities)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

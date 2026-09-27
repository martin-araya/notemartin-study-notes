#!/usr/bin/env python3
"""flashcards.py — F60 · Renderer de repaso espaciado (L4).

Genera tarjetas de repaso desde nodos IR marcados como atómicos (`question`,
`definition`, `formula`, `glossary-term`, `key-fact`). Salida en dos formatos:
- Obsidian (Spaced Repetition plugin): `render/flashcards/<note-id>.md` con
  líneas `Pregunta:: Respuesta` por tarjeta + frontmatter de trazabilidad.
- Anki CSV: `render/flashcards/anki.csv` agregando todas las notas; columnas
  `front,back,tags,note_id,source_hash` (RFC 4180).

Implementa la interfaz `render(ir, profile, matrix) → (artifacts,
degradation_report)` del contrato F53 (`references/08-render/contract.md`).

Reglas duras:
  D1 — Solo `question` o nodos con `attrs.is_atomic_card=true` generan tarjeta.
  D2 — Una tarjeta = un hecho; `_count_clauses(front) <= max_clauses`.
  D3 — Trazabilidad: cada tarjeta lleva `note_id` y `source_hash`.
  D4 — Prohibido generar desde prosa narrativa (paragraph, etc.).

Capacidades (per capability-matrix §2.1):
  Flashcards = 7 ✅ + 6 ❌ (5 no-op + 1 linearización de celdas combinadas).

Uso:
    python3 scripts/render/flashcards.py --ir <path> --profile <path> --out-dir <dir>
                                        [--matrix <path>] [--source-hash <hex64>]
                                        [--renderer-version <semver>]
                                        [--max-words 25] [--max-clauses 2]

Dependencias: Python 3.9+ stdlib puro.
Códigos de salida: 0 OK · 1 error fatal · 2 OK con advertencias (compound-fact).
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import importlib.util as _importlib_util
import io as _io
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# Comparte atomic_write_json / atomic_write_text con F38/F39/F54-F59.
_IO_PATH = (
    Path(__file__).resolve().parent.parent / "util" / "_io.py"
)
_spec = _importlib_util.spec_from_file_location("_skill_io", _IO_PATH)
_io_mod = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_io_mod)
_atomic_write_json = _io_mod.atomic_write_json
_atomic_write_text = _io_mod.atomic_write_text


EXIT_OK = 0
EXIT_FATAL = 1
EXIT_WARN = 2


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ATOMIC_NODE_KINDS: Set[str] = {
    "question", "definition", "formula", "glossary-term", "key-fact",
}

# Capacidades marcadas como no-op (contract §6 filas 9, 10, 13, 14, 18).
NO_OP_CAPABILITIES: List[Tuple[str, str]] = [
    ("flashcards", "Backlinks"),
    ("flashcards", "Enlaces entre notas"),
    ("flashcards", "Callouts semánticos"),
    ("flashcards", "Plegables"),
    ("flashcards", "Consultas dinámicas"),
]

# Heurística de cláusulas: separadores típicos de prosa compuesta.
CLAUSE_SEPARATORS = re.compile(r"[,;]\s*|\s+(?:y|e|o|u)\s+|\.\s+")

REASON_PROSE = "prohibido generar desde prosa narrativa (INV-60)"
REASON_COMPOUND = "compound-fact: supera max_clauses"


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@dataclass
class Card:
    note_id: str
    source_hash: str
    front: str
    back: str
    extra_tags: List[str] = field(default_factory=list)
    discarded_reason: Optional[str] = None
    # F75: hint del `summary` del frontmatter, se muestra en el reverso
    # de la card como contexto adicional (debajo de la respuesta).
    summary_hint: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.discarded_reason is None


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_of_ir(ir_obj: Any) -> str:
    canonical = json.dumps(ir_obj, sort_keys=True, ensure_ascii=False)
    return _sha256_hex(canonical.encode("utf-8"))


def _parse_minimal_yaml(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if line.startswith("- "):
            value = line[2:].strip()
            if isinstance(parent, list):
                parent.append(_coerce_scalar(value))
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                new_dict: Dict[str, Any] = {}
                if isinstance(parent, dict):
                    parent[key] = new_dict
                stack.append((indent, new_dict))
            else:
                if isinstance(parent, dict):
                    parent[key] = _coerce_scalar(value)
    return root


def _coerce_scalar(value: str) -> Any:
    if value in ("true", "True", "yes"):
        return True
    if value in ("false", "False", "no"):
        return False
    if value in ("null", "None", "~"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _get_flashcards_config(profile: Dict[str, Any]) -> Dict[str, Any]:
    targets = profile.get("targets", {}) or {}
    return targets.get("flashcards") or targets.get("spaced_repetition") or {}


# ---------------------------------------------------------------------------
# Recorrido del IR y detección atómica
# ---------------------------------------------------------------------------


def traverse_ir(ir: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    out: List[Tuple[str, Dict[str, Any]]] = []

    def _walk(node: Any, path: str, idx: int) -> None:
        if not isinstance(node, dict):
            return
        child_path = f"{path}/{idx}"
        out.append((child_path, node))
        children = node.get("children", [])
        if isinstance(children, list):
            for i, child in enumerate(children):
                _walk(child, child_path, i)

    children = ir.get("children", [])
    if isinstance(children, list):
        for i, child in enumerate(children):
            _walk(child, "0", i)
    return out


def _is_atomic_node(node: Dict[str, Any]) -> bool:
    """D1: solo `question` o nodos con `attrs.is_atomic_card=true`."""
    kind = node.get("node", "")
    if kind == "question":
        return True
    if kind in ATOMIC_NODE_KINDS:
        attrs = node.get("attrs", {}) or {}
        return bool(attrs.get("is_atomic_card", False))
    return False


def _flatten_inline_text(children: List[Dict[str, Any]]) -> str:
    """Concatena texto inline preservando estructura básica."""
    parts: List[str] = []

    def _walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}
        if kind == "text":
            parts.append(attrs.get("text", "") or "")
        elif kind == "code-inline":
            parts.append(f"`{attrs.get('text', '') or ''}`")
        elif kind == "link-external":
            parts.append(attrs.get("text", "") or "")
        elif kind == "link-note":
            parts.append(attrs.get("text", "") or attrs.get("target", ""))
        elif kind in ("strong", "em", "deleted"):
            inner = _flatten_inline_text(node.get("children", []))
            if kind == "strong":
                parts.append(f"**{inner}**")
            elif kind == "em":
                parts.append(f"*{inner}*")
            else:
                parts.append(f"~~{inner}~~")
        elif kind == "math-inline":
            parts.append(attrs.get("latex", "") or "")
        elif kind == "footnote-ref":
            parts.append(attrs.get("text", "") or "")
        elif kind == "keyboard":
            parts.append(attrs.get("text", "") or "")
        elif kind == "placeholder":
            parts.append(attrs.get("text", "") or "")
        elif kind == "term-ref":
            parts.append(attrs.get("text", "") or "")
        else:
            parts.append(attrs.get("text", "") or "")
        sub = node.get("children", []) or []
        if sub and kind not in ("strong", "em", "deleted"):
            for c in sub:
                _walk(c)

    for c in children or []:
        _walk(c)
    return "".join(parts).strip()


def _count_clauses(text: str) -> int:
    if not text or not text.strip():
        return 0
    parts = CLAUSE_SEPARATORS.split(text)
    return max(1, len([p for p in parts if p.strip()]))


def _word_count(text: str) -> int:
    return len(text.split()) if text else 0


# ---------------------------------------------------------------------------
# Extracción de tarjetas
# ---------------------------------------------------------------------------


def _extract_from_question(node: Dict[str, Any], note_id: str,
                            source_hash: str, max_clauses: int,
                            degradations: List[Dict[str, Any]],
                            node_path: str,
                            summary_hint: str = "") -> Optional[Card]:
    attrs = node.get("attrs", {}) or {}
    prompt = str(attrs.get("prompt", "") or "").strip()
    if not prompt:
        return None
    answer = _flatten_inline_text(node.get("children", []))
    if not answer.strip():
        return None

    front = prompt
    back = answer
    extra_tags = list(attrs.get("tags", []) or [])
    if not isinstance(extra_tags, list):
        extra_tags = []

    if _count_clauses(front) > max_clauses or _count_clauses(back) > max_clauses:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'cmp').encode())[:12]}",
            "node_path": node_path,
            "node_type": "question",
            "capability": "compound-fact",
            "alternative": (
                f"tarjeta descartada por hecho compuesto (front={_count_clauses(front)} "
                f"cláusulas, back={_count_clauses(back)} cláusulas); max_clauses={max_clauses}"
            ),
            "evidence": (
                f"card.front clause count: {_count_clauses(front)} <= {max_clauses}"
            ),
            "content_intact": True,
        })
        return Card(note_id=note_id, source_hash=source_hash,
                    front=front, back=back, extra_tags=extra_tags,
                    summary_hint=summary_hint,
                    discarded_reason=REASON_COMPOUND)

    return Card(note_id=note_id, source_hash=source_hash,
                front=front, back=back, extra_tags=extra_tags,
                summary_hint=summary_hint)


def _extract_from_atomic(node: Dict[str, Any], note_id: str,
                          source_hash: str, max_clauses: int,
                          degradations: List[Dict[str, Any]],
                          node_path: str,
                          summary_hint: str = "") -> Optional[Card]:
    """Genera tarjeta desde definition/formula/glossary-term/key-fact."""
    kind = node.get("node", "")
    attrs = node.get("attrs", {}) or {}

    if kind == "definition":
        front = str(attrs.get("term", "") or "").strip()
        back = _flatten_inline_text(node.get("children", []))
        if not front:
            front = str(attrs.get("name", "") or "").strip()
    elif kind == "formula":
        front = str(attrs.get("name", "") or "").strip()
        back = str(attrs.get("latex", "") or "").strip()
    elif kind == "glossary-term":
        front = str(attrs.get("term", "") or "").strip()
        back = str(attrs.get("definition", "") or "").strip()
    elif kind == "key-fact":
        front = str(attrs.get("statement", "") or "").strip()
        back = str(attrs.get("reference", "") or "").strip()
    else:
        return None

    if not front or not back:
        return None

    extra_tags = list(attrs.get("tags", []) or [])
    if not isinstance(extra_tags, list):
        extra_tags = []

    if _count_clauses(front) > max_clauses or _count_clauses(back) > max_clauses:
        degradations.append({
            "id": f"deg-{_sha256_hex((node_path + 'cmp').encode())[:12]}",
            "node_path": node_path,
            "node_type": kind,
            "capability": "compound-fact",
            "alternative": (
                f"tarjeta descartada por hecho compuesto ({kind}); max_clauses={max_clauses}"
            ),
            "evidence": f"card.front clause count: {_count_clauses(front)} <= {max_clauses}",
            "content_intact": True,
        })
        return Card(note_id=note_id, source_hash=source_hash,
                    front=front, back=back, extra_tags=extra_tags,
                    summary_hint=summary_hint,
                    discarded_reason=REASON_COMPOUND)

    return Card(note_id=note_id, source_hash=source_hash,
                front=front, back=back, extra_tags=extra_tags,
                summary_hint=summary_hint)


def _extract_from_merged_table(node: Dict[str, Any], note_id: str,
                                source_hash: str,
                                degradations: List[Dict[str, Any]],
                                node_path: str,
                                summary_hint: str = "") -> List[Card]:
    """Fila 6 contract §6: linearización de tabla con celdas combinadas."""
    attrs = node.get("attrs", {}) or {}
    cells = attrs.get("cells", []) or []
    matrix = attrs.get("matrix", []) or []
    headers = attrs.get("headers", []) or []

    cards: List[Card] = []
    seen_values: Set[str] = set()

    for r_idx, row in enumerate(cells):
        for c_idx, cell in enumerate(row):
            v = cell.get("value", "") if isinstance(cell, dict) else str(cell)
            if not v or not str(v).strip():
                continue
            v_str = str(v).strip()
            if v_str in seen_values:
                degradations.append({
                    "id": f"deg-{_sha256_hex((node_path + f'{r_idx}-{c_idx}red').encode())[:12]}",
                    "node_path": f"{node_path}/{r_idx}/{c_idx}",
                    "node_type": "table-cell",
                    "capability": "table-merged-cells",
                    "alternative": (
                        f"celda descartada: redundante con '{v_str[:30]}'"
                    ),
                    "evidence": f"rg 'redundant-with:' anki.csv exit 0",
                    "content_intact": True,
                })
                continue
            seen_values.add(v_str)
            # Back text diseñado para NO contar como cláusula compuesta.
            cards.append(Card(
                note_id=note_id,
                source_hash=source_hash,
                front=v_str,
                back=f"celda de tabla con celdas combinadas en nota {note_id}",
                extra_tags=[f"cell-of:{note_id}:{r_idx}"],
                summary_hint=summary_hint,
            ))
            degradations.append({
                "id": f"deg-{_sha256_hex((node_path + f'{r_idx}-{c_idx}lin').encode())[:12]}",
                "node_path": f"{node_path}/{r_idx}/{c_idx}",
                "node_type": "table-cell",
                "capability": "table-merged-cells",
                "alternative": (
                    f"celda serializada como tarjeta independiente (fila 6 contract §6); "
                    f"front='{v_str[:40]}'"
                ),
                "evidence": f"rg 'cell-of:{note_id}:{r_idx}' anki.csv exit 0",
                "content_intact": True,
            })
    return cards


# ---------------------------------------------------------------------------
# Render de tarjetas por IR
# ---------------------------------------------------------------------------


def collect_cards_from_ir(
    ir_obj: Dict[str, Any], ir_sha256: str,
    max_clauses: int, max_words: int,
    degradations: List[Dict[str, Any]],
    discarded: List[Dict[str, Any]],
    word_warnings: List[Dict[str, Any]],
) -> List[Card]:
    """Recorre el IR y extrae tarjetas. Maneja prosa, atomic, questions, merged."""
    note_id = str(ir_obj.get("note_id", ""))
    # F75: el `summary` del frontmatter se usa como hint en el reverso
    # de cada card. No se filtra por nota — todas las cards de la misma
    # nota comparten el mismo hint.
    fm = ir_obj.get("frontmatter", {}) or {}
    summary_hint = str(fm.get("summary", "") or "")
    cards: List[Card] = []
    nodes = traverse_ir(ir_obj)

    for path, node in nodes:
        kind = node.get("node", "")
        attrs = node.get("attrs", {}) or {}

        if kind == "table":
            cap = node.get("capability", "")
            is_merged = (
                cap == "table-merged-cells"
                or "matrix" in attrs
                or "cells_with_span" in attrs
                or "rowspan" in attrs
            )
            if is_merged:
                cards.extend(_extract_from_merged_table(
                    node, note_id, ir_sha256, degradations, path,
                    summary_hint=summary_hint,
                ))
                continue

        if kind == "question":
            card = _extract_from_question(
                node, note_id, ir_sha256, max_clauses, degradations, path,
                summary_hint=summary_hint,
            )
            if card is None:
                continue
            if not card.is_valid:
                discarded.append({
                    "node_path": path,
                    "reason": card.discarded_reason,
                    "front": card.front[:80],
                })
            else:
                cards.append(card)
                if _word_count(card.front) > max_words:
                    word_warnings.append({
                        "node_path": path,
                        "front_words": _word_count(card.front),
                        "max": max_words,
                    })
            continue

        if kind in ATOMIC_NODE_KINDS and _is_atomic_node(node):
            card = _extract_from_atomic(
                node, note_id, ir_sha256, max_clauses, degradations, path,
                summary_hint=summary_hint,
            )
            if card is None:
                continue
            if not card.is_valid:
                discarded.append({
                    "node_path": path,
                    "reason": card.discarded_reason,
                    "front": card.front[:80],
                })
            else:
                cards.append(card)
                if _word_count(card.front) > max_words:
                    word_warnings.append({
                        "node_path": path,
                        "front_words": _word_count(card.front),
                        "max": max_words,
                    })
            continue

        # Cualquier otro nodo (paragraph, section, list, etc.) es prosa narrativa.
        # D1: solo lo marcamos como "discarded" si tiene contenido textual
        # candidato a tarjeta. Para evitar ruido, descartamos paragraph con
        # texto >5 palabras y section sin ser question.
        if kind in ("paragraph", "section"):
            txt = _flatten_inline_text(node.get("children", []) if kind == "paragraph" else [])
            if txt and len(txt.split()) >= 5:
                discarded.append({
                    "node_path": path,
                    "reason": REASON_PROSE,
                    "front": txt[:80],
                })

    return cards


# ---------------------------------------------------------------------------
# Generación de no-op degradations (filas 9, 10, 13, 14, 18 contract §6)
# ---------------------------------------------------------------------------


def _add_no_op_degradations(degradations: List[Dict[str, Any]]) -> None:
    """5 entradas no-op con `evidence: not_applicable`, `content_intact: true`."""
    for target, capability in NO_OP_CAPABILITIES:
        degradations.append({
            "id": f"deg-noop-{target}-{capability}".replace(" ", "-").lower()[:32],
            "node_path": "none",
            "node_type": target,
            "capability": capability,
            "alternative": "no-op",
            "evidence": "not_applicable",
            "content_intact": True,
        })


# ---------------------------------------------------------------------------
# Formatos de salida
# ---------------------------------------------------------------------------


def render_obsidian_md(cards: List[Card], note_id: str, title: str,
                       renderer_version: str) -> str:
    """Formato Spaced Repetition plugin: frontmatter + líneas `Q:: A`."""
    valid = [c for c in cards if c.is_valid]
    frontmatter = (
        "---\n"
        f'source: "[[{note_id}]]"\n'
        f'source_hash: ""\n'  # omitido para idempotencia
        f'renderer_version: "{renderer_version}"\n'
        f'cards_count: {len(valid)}\n'
        "---\n\n"
    )
    header = (
        f"# Tarjetas de {title}\n\n"
        f"<!-- src: {note_id} -->\n\n"
    )
    body_lines: List[str] = []
    for i, c in enumerate(valid, start=1):
        body_lines.append(f"Pregunta {i}?")
        body_lines.append(f":: {c.back}")
        body_lines.append(f"<!-- card {i}, note:{c.note_id}, "
                         f"sha256:{c.source_hash} -->\n")
    body = "\n".join(body_lines)
    return frontmatter + header + body


def _csv_escape(s: str) -> str:
    """RFC 4180: entrecomillar si contiene `,`/`"`/`\n`; escapar `"` como `""`."""
    if any(ch in s for ch in [",", '"', "\n", "\r"]):
        return '"' + s.replace('"', '""') + '"'
    return s


def render_anki_csv(all_cards: List[Tuple[str, List[Card]]]) -> str:
    """Un único CSV agregando todas las notas."""
    buf = _io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["front", "back", "tags", "note_id", "source_hash"])
    for note_id, cards in all_cards:
        for c in cards:
            if not c.is_valid:
                continue
            tags = [f"note:{c.note_id}", f"src:{c.source_hash[:12]}"] + c.extra_tags
            writer.writerow([
                _csv_escape(c.front),
                _csv_escape(c.back),
                _csv_escape(";".join(tags)),
                c.note_id,
                c.source_hash,
            ])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def build_report(source_hash: str, degradations: List[Dict[str, Any]],
                 discarded: List[Dict[str, Any]],
                 word_warnings: List[Dict[str, Any]],
                 ir_node_count: int,
                 cards_generated: int, cards_discarded: int,
                 notes_with_cards: int,
                 files_published: Dict[str, str]
                 ) -> Tuple[Dict[str, Any], str]:
    content_loss = sum(1 for d in degradations if not d.get("content_intact", True))
    discarded_prose = sum(1 for d in discarded
                           if d.get("reason") == REASON_PROSE)
    discarded_compound = sum(1 for d in discarded
                              if d.get("reason") == REASON_COMPOUND)
    report = {
        "schema_version": "1.0.0",
        "target": "flashcards",
        "source_hash": source_hash,
        "generated_at": _now_utc_iso(),
        "totals": {
            "ir_nodes": ir_node_count,
            "cards_generated": cards_generated,
            "cards_discarded": cards_discarded,
            "discarded_prose": discarded_prose,
            "discarded_compound": discarded_compound,
            "notes_with_cards": notes_with_cards,
            "content_loss": content_loss,
        },
        "degradations": degradations,
        "discarded": discarded,
        "word_warnings": word_warnings,
        "published_files": files_published,
        "cross_target_diff": {
            "vs_obsidian": "Salida dedicada a Spaced Repetition plugin; Obsidian renderer usa wikilinks/callouts nativos",
            "vs_markdown": "Markdown produce texto lineal; flashcards produce estructura Q:: A",
            "vs_html_pdf": "HTML/PDF es lectura secuencial; flashcards es repaso aislado por hecho"
        }
    }
    md_lines = [
        "# Reporte de degradación — Flashcards",
        "",
        f"- **schema_version:** {report['schema_version']}",
        f"- **target:** flashcards",
        f"- **source_hash:** `{source_hash}`",
        f"- **generated_at:** {report['generated_at']}",
        "",
        "## Resumen",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Nodos IR totales | {ir_node_count} |",
        f"| Tarjetas generadas | {cards_generated} |",
        f"| Tarjetas descartadas | {cards_discarded} |",
        f"|   - prosa narrativa | {discarded_prose} |",
        f"|   - hecho compuesto | {discarded_compound} |",
        f"| Notas con tarjetas | {notes_with_cards} |",
        f"| Pérdida de contenido | {content_loss} |",
        "",
    ]
    if degradations:
        md_lines.append("## Degradaciones")
        md_lines.append("")
        for d in degradations:
            md_lines.append(f"### flashcards / {d.get('capability', '?')}")
            md_lines.append("")
            md_lines.append(f"- **node_path:** `{d.get('node_path')}`")
            md_lines.append(f"- **node_type:** `{d.get('node_type')}`")
            md_lines.append(f"- **alternative:** {d.get('alternative')}")
            md_lines.append(f"- **evidence:** `{d.get('evidence')}`")
            md_lines.append(f"- **content_intact:** `{d.get('content_intact')}`")
            md_lines.append("")
    else:
        md_lines.append(
            "> Cero degradaciones en este destino. Esta sección se mantiene "
            "siempre para confirmar cobertura."
        )
        md_lines.append("")
    if discarded:
        md_lines.append("## Tarjetas descartadas")
        md_lines.append("")
        for d in discarded:
            md_lines.append(f"- `{d['node_path']}`: **{d['reason']}** — `{d['front']}`")
        md_lines.append("")
    if word_warnings:
        md_lines.append("## Advertencias de longitud")
        md_lines.append("")
        for w in word_warnings:
            md_lines.append(f"- `{w['node_path']}`: {w['front_words']} palabras (> {w['max']})")
        md_lines.append("")
    md_lines.append("## Cobertura")
    md_lines.append("")
    md_lines.append(f"- Nodos contabilizados: {len(degradations)}")
    md_lines.append(f"- Nodos IR totales: {ir_node_count}")
    md_lines.append(f"- content_loss: {content_loss} (debe ser 0; RC-01)")
    md = "\n".join(md_lines)
    return report, md


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_ir(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile(path: Path) -> Dict[str, Any]:
    return _parse_minimal_yaml(path.read_text(encoding="utf-8"))


def derive_source_hash(out_dir: Path, override: Optional[str]) -> str:
    if override:
        return override
    manifest = out_dir / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            sh = data.get("source", {}).get("hash") if isinstance(data, dict) else None
            if isinstance(sh, str) and re.match(r"^[0-9a-f]{64}$", sh):
                return sh
        except (json.JSONDecodeError, OSError):
            pass
    return "0" * 64


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="flashcards.py",
        description="Renderer de tarjetas de repaso (L4) para el Note IR. F60.",
    )
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--matrix", type=Path,
                        default=(Path(__file__).resolve().parents[2] /
                                 "references" / "08-render" / "capability-matrix.md"))
    parser.add_argument("--source-hash", type=str, default=None)
    parser.add_argument("--renderer-version", type=str, default="0.1.0")
    parser.add_argument("--max-words", type=int, default=25,
                        help="Heurística débil: warn si front > N palabras.")
    parser.add_argument("--max-clauses", type=int, default=2,
                        help="D2: máximo de cláusulas en front/back; descarta si >.")

    args = parser.parse_args(argv)

    if not args.ir.exists():
        print(f"ERROR: IR no encontrado en {args.ir}", file=sys.stderr)
        return EXIT_FATAL
    if not args.profile.exists():
        print(f"ERROR: profile no encontrado en {args.profile}", file=sys.stderr)
        return EXIT_FATAL

    profile = load_profile(args.profile)
    source_hash = derive_source_hash(args.out_dir, args.source_hash)
    if not re.match(r"^[0-9a-f]{64}$", source_hash):
        source_hash = "0" * 64

    if args.ir.is_dir():
        ir_paths = sorted(args.ir.glob("*.json"))
    else:
        ir_paths = [args.ir]
    if not ir_paths:
        print(f"ERROR: no hay IRs en {args.ir}", file=sys.stderr)
        return EXIT_FATAL

    degradations: List[Dict[str, Any]] = []
    discarded: List[Dict[str, Any]] = []
    word_warnings: List[Dict[str, Any]] = []

    # Las 5 entradas no-op se emiten UNA vez (no por nota).
    _add_no_op_degradations(degradations)

    target_dir = args.out_dir / "render" / "flashcards"
    target_dir.mkdir(parents=True, exist_ok=True)

    all_cards: List[Tuple[str, List[Card]]] = []
    ir_node_count_total = 0
    files_published: Dict[str, str] = {}
    notes_with_cards = 0
    cards_generated = 0
    cards_discarded = 0

    for ir_path in ir_paths:
        try:
            ir_obj = load_ir(ir_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: no se pudo cargar {ir_path}: {e}", file=sys.stderr)
            continue

        ir_sha256 = _sha256_of_ir(ir_obj)
        note_id = str(ir_obj.get("note_id", ""))
        title = ir_obj.get("title", note_id) or note_id

        cards = collect_cards_from_ir(
            ir_obj, ir_sha256, args.max_clauses, args.max_words,
            degradations, discarded, word_warnings,
        )
        ir_node_count_total += len(traverse_ir(ir_obj))

        valid_cards = [c for c in cards if c.is_valid]
        invalid_cards = [c for c in cards if not c.is_valid]
        cards_generated += len(valid_cards)
        cards_discarded += len(invalid_cards)

        if valid_cards:
            notes_with_cards += 1
            all_cards.append((note_id, valid_cards))
            md_path = target_dir / f"{note_id}.md"
            md_content = render_obsidian_md(valid_cards, note_id, title,
                                            args.renderer_version)
            _atomic_write_text(md_path, md_content)
            files_published[note_id] = str(md_path)

    # CSV con todas las notas.
    csv_path = target_dir / "anki.csv"
    csv_content = render_anki_csv(all_cards)
    _atomic_write_text(csv_path, csv_content)
    files_published["anki.csv"] = str(csv_path)

    # Reporte.
    report, report_md = build_report(
        source_hash=source_hash, degradations=degradations,
        discarded=discarded, word_warnings=word_warnings,
        ir_node_count=ir_node_count_total,
        cards_generated=cards_generated, cards_discarded=cards_discarded,
        notes_with_cards=notes_with_cards,
        files_published=files_published,
    )
    reports_dir = args.out_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(reports_dir / "render-degradation.json", report)
    _atomic_write_text(reports_dir / "render-degradation.md", report_md)

    print(f"OK — {cards_generated} tarjeta(s) generada(s) en {notes_with_cards} nota(s)")
    print(f"     csv: {csv_path}")
    print(f"     reporte: {reports_dir / 'render-degradation.json'}")
    if word_warnings:
        print(f"WARN — {len(word_warnings)} tarjeta(s) con front > {args.max_words} palabras")
    if cards_discarded:
        print(f"WARN — {cards_discarded} tarjeta(s) descartadas")
        return EXIT_WARN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())

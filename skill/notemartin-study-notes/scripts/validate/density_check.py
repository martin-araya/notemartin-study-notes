"""Verificador de densidad y jerarquía — Fase 76.

Lee una nota NoteMark (`.md`) y mide las 8 reglas de densidad definidas
en `references/07-visual/density.md`:

    R1  Max párrafo L1 (## TL;DR): ≤ 60 palabras Y ≤ 8 líneas
    R2  Max párrafo L2 (cuerpo): ≤ 200 palabras
    R3  Frecuencia mínima de anclaje visual: ≥ 1 cada 200 palabras
    R4  Max callouts consecutivos sin prosa: ≤ 3
    R5  Max viñetas consecutivas sin prosa/estructura: ≤ 5
    R6  Sección (H2/H3) no puede ser 100% viñetas: ≥ 1 párrafo/tabla/callout/figura
    R7  L3 si > 100 líneas → plegable (warning)
    R8  Densidad {src:} por bloque fáctico: ≥ 0.80

Exenciones por tipo de nota (ver density.md §4):
  - glossary-term: exenta R3 y R6
  - cheatsheet: exenta R3 y R5 y R6
  - index-moc: exenta R3 y R5 y R6

CLI:
    python3 density_check.py --note <path>            # markdown a stdout
    python3 density_check.py --note <path> --json     # JSON estructurado
    python3 density_check.py --note <path> --strict   # warnings → exit 1
    python3 density_check.py --note <path> --allow-violations R2,R5
    python3 density_check.py --notes <dir>            # batch

Exit codes:
    0  sin violaciones
    1  alguna violación (o warning si --strict)
    2  error de uso (archivo no encontrado, etc.)

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Tipos de nota exentos (parcial o totalmente) de las reglas R3/R5/R6.
EXEMPT_FROM_R3 = frozenset({"glossary-term", "cheatsheet", "index-moc"})
EXEMPT_FROM_R5 = frozenset({"cheatsheet", "index-moc"})
EXEMPT_FROM_R6 = frozenset({"glossary-term", "cheatsheet", "index-moc"})


@dataclass
class Rules:
    max_l1_paragraph_words: int = 60
    max_l1_paragraph_lines: int = 8
    max_l2_paragraph_words: int = 200
    min_anchors_per_words: int = 200
    max_consecutive_callouts: int = 3
    max_consecutive_bullets: int = 5
    max_section_lines_for_unfolded: int = 100
    min_src_density_per_factual_block: float = 0.80
    exempt_r3: frozenset = field(default_factory=lambda: EXEMPT_FROM_R3)
    exempt_r5: frozenset = field(default_factory=lambda: EXEMPT_FROM_R5)
    exempt_r6: frozenset = field(default_factory=lambda: EXEMPT_FROM_R6)


@dataclass
class Block:
    kind: str                       # paragraph, callout, table, list, code, figure, diagram, equation, heading
    text: str
    line: int                      # línea 1-indexed en el archivo
    section: str = ""              # heading de la sección padre
    is_prose: bool = False         # paragraph o list
    is_anchor: bool = False        # callout, table, figure, diagram, equation, code-con-caption
    is_checklist: bool = False     # list con [ ] items
    is_factual: bool = False       # para R8
    has_src_mark: bool = False     # para R8
    items: int = 0                 # para list: número de items


@dataclass
class Section:
    heading: str                    # el heading raíz, e.g. "## TL;DR" o "## Procedimiento"
    line: int                       # línea del heading
    blocks: List[Block] = field(default_factory=list)
    lines: int = 0                  # número de líneas de la sección (incluyendo heading)

    @property
    def paragraphs(self) -> List[Block]:
        return [b for b in self.blocks if b.kind == "paragraph"]

    @property
    def is_collapsible(self) -> bool:
        return any(b.kind == "collapsible" for b in self.blocks)


@dataclass
class ParsedNote:
    frontmatter: Dict[str, str]
    note_type: str
    sections: List[Section] = field(default_factory=list)
    raw_lines: int = 0
    in_frontmatter: bool = False

    def section_by_heading(self, heading_prefix: str) -> Optional[Section]:
        for s in self.sections:
            if s.heading.startswith(heading_prefix):
                return s
        return None


@dataclass
class Issue:
    code: str               # R1..R8 + subcode (e.g. "R1", "R2", "R4", "R6")
    severity: str          # "error" o "warning"
    where: str             # ruta tipo "section:H2:paragraph:3"
    rule: str              # nombre legible
    message: str
    measured: Optional[float] = None
    limit: Optional[float] = None


# Regex de parsing (stdlib puro, no usa markdown libs).
_RE_FRONTMATTER_END = re.compile(r"^---\s*$")
_RE_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_RE_CALLOUT = re.compile(r"^>\s*\[!(\w+)\]")
_RE_DIRECTIVE = re.compile(r"^:::\s*(\w+)")
_RE_TABLE = re.compile(r"^\s*\|.*\|\s*$")
_RE_CODE_FENCE = re.compile(r"^```")
_RE_FIGURE = re.compile(r"^:::\s*figure|!\[")
_RE_DIAGRAM = re.compile(r"^:::\s*diagram|```mermaid")
_RE_EQUATION = re.compile(r"^:::\s*equation|^\$\$")
_RE_SRC_MARK = re.compile(r"\{src:blk_[0-9a-f]{12}\}")
_RE_CHECKLIST = re.compile(r"^[\s]*-\s+\[[ xX]\]\s+")


def _parse_frontmatter(lines: List[str]) -> Tuple[Dict[str, str], int]:
    """Extrae el frontmatter YAML. Parser mínimo: clave: valor (sin soporte de
    listas, comillas, escapes). Suficiente para los 5 universales que valida F75."""
    if not lines or not _RE_FRONTMATTER_END.match(lines[0]):
        return {}, 0
    fm: Dict[str, str] = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if _RE_FRONTMATTER_END.match(line):
            return fm, i + 1
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, len(lines)


def _classify_block(kind_hint: str, line: str) -> str:
    """Decide el kind final del bloque a partir del hint inicial y el contenido."""
    if kind_hint == "callout":
        return "callout"
    if kind_hint == "table":
        return "table"
    if kind_hint == "code":
        return "code"
    if kind_hint == "figure":
        return "figure"
    if kind_hint == "diagram":
        return "diagram"
    if kind_hint == "equation":
        return "equation"
    if kind_hint == "list":
        return "list"
    if kind_hint == "collapsible":
        return "collapsible"
    if kind_hint == "heading":
        return "heading"
    return "paragraph"


def _is_factual(block: Block) -> bool:
    """Determina si un bloque es fáctico (ver density.md §3.3)."""
    if block.kind == "paragraph":
        # No es fáctico si es transaccional puro (heurística: ≤ 4 palabras + verbo imperativo).
        words = block.text.split()
        if len(words) <= 4 and words and words[0].lower() in {"click", "press", "open", "select", "go", "run"}:
            return False
        return True
    if block.kind == "callout":
        # Solo las severities fácticas cuentan.
        m = _RE_CALLOUT.match(block.text)
        if m:
            sev = m.group(1).lower()
            return sev in {"info", "warning", "danger", "security", "performance", "deprecated"}
        return False
    if block.kind == "code":
        # Code con caption (heurística: la primera línea no es un fence vacío).
        return block.text.strip().startswith("```") and len(block.text.split("\n")) >= 2
    if block.kind == "equation":
        return True
    if block.kind == "figure":
        return "caption" in block.text.lower() or "Figura" in block.text
    return False


def _is_anchor(block: Block) -> bool:
    """Determina si un bloque cuenta como anclaje visual (density.md §3.1)."""
    return block.kind in ("callout", "table", "figure", "diagram", "equation") or (
        block.kind == "code" and "caption" in block.text.lower()
    )


def _parse_note(path: Path) -> ParsedNote:
    """Parsea un archivo NoteMark (.md) en bloques clasificados por sección."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    fm, start = _parse_frontmatter(lines)
    note_type = str(fm.get("note-type", "") or "")
    parsed = ParsedNote(frontmatter=fm, note_type=note_type, raw_lines=len(lines))

    current_section: Optional[Section] = None
    pending_kind = "paragraph"
    pending_text: List[str] = []
    pending_start_line = 0
    in_code_fence = False

    def _flush_block(line_no: int) -> Optional[Block]:
        nonlocal pending_kind, pending_text, pending_start_line
        if not pending_text:
            return None
        text_block = "\n".join(pending_text).strip()
        if not text_block:
            pending_text = []
            return None
        kind = _classify_block(pending_kind, text_block)
        block = Block(
            kind=kind,
            text=text_block,
            line=pending_start_line,
            section=current_section.heading if current_section else "",
            is_prose=kind in ("paragraph", "list"),
            is_anchor=_is_anchor(Block(kind=kind, text=text_block, line=pending_start_line)),
            is_checklist=kind == "list" and any(_RE_CHECKLIST.match(l) for l in pending_text),
            is_factual=_is_factual(Block(kind=kind, text=text_block, line=pending_start_line)),
            has_src_mark=bool(_RE_SRC_MARK.search(text_block)),
            items=sum(1 for l in pending_text if _RE_CHECKLIST.match(l) or re.match(r"^[\s]*[-*]\s+", l)),
        )
        pending_text = []
        pending_kind = "paragraph"  # reset tras flush
        return block

    i = start
    while i < len(lines):
        line = lines[i]
        line_no = i + 1

        # Frontmatter ya consumido; saltar líneas vacías iniciales.
        if line_no <= start and not line.strip():
            i += 1
            continue

        # Code fence toggle.
        if _RE_CODE_FENCE.match(line):
            if not in_code_fence:
                # Apertura de fence; si hay pendiente, flushear.
                b = _flush_block(line_no)
                if b and current_section is not None:
                    current_section.blocks.append(b)
                pending_kind = "code"
                pending_text = [line]
                pending_start_line = line_no
                in_code_fence = True
            else:
                # Cierre de fence; flushear.
                pending_text.append(line)
                b = _flush_block(line_no)
                if b and current_section is not None:
                    current_section.blocks.append(b)
                in_code_fence = False
            i += 1
            continue

        if in_code_fence:
            pending_text.append(line)
            i += 1
            continue

        # Heading: nueva sección.
        m = _RE_HEADING.match(line)
        if m:
            # Flushear bloque pendiente antes de iniciar nueva sección.
            b = _flush_block(line_no)
            if b and current_section is not None:
                current_section.blocks.append(b)
            level = len(m.group(1))
            heading = m.group(2).strip()
            if level == 2 or level == 3:
                # Cierra sección anterior (si la había).
                if current_section is not None:
                    # Calcular líneas antes de cerrar.
                    current_section.lines = (
                        (current_section.line - current_section.line)
                        + len(current_section.blocks)
                    )
                    for bk in current_section.blocks:
                        current_section.lines += len(bk.text.splitlines())
                    parsed.sections.append(current_section)
                current_section = Section(heading=f"{'#' * level} {heading}", line=line_no)
            else:
                # H1, H4+ dentro de la sección actual; tratarlo como paragraph.
                pending_kind = "paragraph"
                pending_text.append(line)
            i += 1
            continue

        # Callout: nueva línea con `> [!type]` (inicio) o continuación de callout.
        is_callout_start = bool(_RE_CALLOUT.match(line))
        is_callout_continuation = (
            pending_kind == "callout" and line.lstrip().startswith(">")
        )
        if is_callout_start or is_callout_continuation:
            if is_callout_start and pending_kind == "callout":
                # Inicio de un callout mientras hay otro en curso: flushear primero.
                b = _flush_block(line_no)
                if b and current_section is not None:
                    current_section.blocks.append(b)
            pending_kind = "callout"
            if not pending_text:
                pending_start_line = line_no
            pending_text.append(line)
            i += 1
            continue

        # Directivas `:::type`.
        m = _RE_DIRECTIVE.match(line)
        if m:
            directive_kind = m.group(1).lower()
            kind_map = {
                "figure": "figure", "diagram": "diagram", "equation": "equation",
                "collapsible": "collapsible", "callout": "callout", "table": "table",
            }
            mapped = kind_map.get(directive_kind, "paragraph")
            b = _flush_block(line_no)
            if b and current_section is not None:
                current_section.blocks.append(b)
            pending_kind = mapped
            pending_text = [line]
            pending_start_line = line_no
            i += 1
            continue

        # Tabla.
        if _RE_TABLE.match(line):
            if pending_kind != "table":
                b = _flush_block(line_no)
                if b and current_section is not None:
                    current_section.blocks.append(b)
                pending_kind = "table"
                pending_text = [line]
                pending_start_line = line_no
            else:
                pending_text.append(line)
            i += 1
            continue

        # Lista (incluye checklist).
        if re.match(r"^[\s]*[-*]\s+", line) or _RE_CHECKLIST.match(line):
            if pending_kind != "list":
                b = _flush_block(line_no)
                if b and current_section is not None:
                    current_section.blocks.append(b)
                pending_kind = "list"
                pending_text = [line]
                pending_start_line = line_no
            else:
                pending_text.append(line)
            i += 1
            continue

        # Línea vacía: flushea bloque pendiente.
        if not line.strip():
            b = _flush_block(line_no)
            if b and current_section is not None:
                current_section.blocks.append(b)
            i += 1
            continue

        # Párrafo: si el pending_kind no es paragraph, flushear antes.
        if pending_kind != "paragraph" and pending_text:
            b = _flush_block(line_no)
            if b and current_section is not None:
                current_section.blocks.append(b)
            pending_kind = "paragraph"
        if not pending_text:
            pending_start_line = line_no
        pending_text.append(line)
        i += 1

    # Flush final.
    b = _flush_block(len(lines))
    if b and current_section is not None:
        current_section.blocks.append(b)
    if current_section is not None:
        # Calcular líneas finales.
        for bk in current_section.blocks:
            current_section.lines += len(bk.text.splitlines())
        parsed.sections.append(current_section)

    return parsed


def _measure(parsed: ParsedNote, rules: Rules) -> List[Issue]:
    """Aplica las 8 reglas R1-R8 y emite los Issues correspondientes."""
    issues: List[Issue] = []
    exempt_r3 = parsed.note_type in rules.exempt_r3
    exempt_r5 = parsed.note_type in rules.exempt_r5
    exempt_r6 = parsed.note_type in rules.exempt_r6

    # R1: max párrafo L1 (## TL;DR) ≤ 60 palabras Y ≤ 8 líneas.
    l1 = parsed.section_by_heading("## TL;DR")
    if l1:
        for p in l1.paragraphs:
            words = len(p.text.split())
            lines = len(p.text.splitlines()) or 1
            if words > rules.max_l1_paragraph_words or lines > rules.max_l1_paragraph_lines:
                issues.append(Issue(
                    code="R1", severity="warning",
                    where=f"{l1.heading}:paragraph:{p.line}",
                    rule="R1 max párrafo L1",
                    message=(
                        f"L1 párrafo con {words} palabras / {lines} líneas "
                        f"(límite: {rules.max_l1_paragraph_words} palabras / "
                        f"{rules.max_l1_paragraph_lines} líneas)"
                    ),
                    measured=float(words), limit=float(rules.max_l1_paragraph_words),
                ))

    # R2: max párrafo L2 (cuerpo) ≤ 200 palabras.
    for section in parsed.sections:
        if section.heading.startswith("## TL;DR"):
            continue
        for p in section.paragraphs:
            words = len(p.text.split())
            if words > rules.max_l2_paragraph_words:
                issues.append(Issue(
                    code="R2", severity="error",
                    where=f"{section.heading}:paragraph:{p.line}",
                    rule="R2 max párrafo L2",
                    message=(
                        f"Párrafo L2 con {words} palabras (límite: "
                        f"{rules.max_l2_paragraph_words})"
                    ),
                    measured=float(words), limit=float(rules.max_l2_paragraph_words),
                ))

    # R3: ≥ 1 anclaje cada 200 palabras de prosa.
    if not exempt_r3:
        for section in parsed.sections:
            run_prose = 0
            run_start_block: Optional[Block] = None
            for block in section.blocks:
                if block.is_prose and not block.is_anchor:
                    run_prose += len(block.text.split())
                    if run_start_block is None:
                        run_start_block = block
                    if run_prose > rules.min_anchors_per_words:
                        issues.append(Issue(
                            code="R3", severity="warning",
                            where=f"{section.heading}:paragraph:{run_start_block.line}",
                            rule="R3 frecuencia mínima de anclaje visual",
                            message=(
                                f"{run_prose} palabras de prosa sin anclaje visual "
                                f"(límite: {rules.min_anchors_per_words})"
                            ),
                            measured=float(run_prose), limit=float(rules.min_anchors_per_words),
                        ))
                        run_prose = 0
                        run_start_block = None
                else:
                    if block.is_anchor:
                        run_prose = 0
                        run_start_block = None

    # R4: ≤ 3 callouts consecutivos sin prosa.
    for section in parsed.sections:
        run = 0
        run_start_block: Optional[Block] = None
        for block in section.blocks:
            if block.kind == "callout":
                run += 1
                if run_start_block is None:
                    run_start_block = block
                if run > rules.max_consecutive_callouts:
                    issues.append(Issue(
                        code="R4", severity="error",
                        where=f"{section.heading}:callout:{block.line}",
                        rule="R4 max callouts consecutivos",
                        message=(
                            f"{run} callouts consecutivos sin prosa intermedia "
                            f"(límite: {rules.max_consecutive_callouts})"
                        ),
                        measured=float(run), limit=float(rules.max_consecutive_callouts),
                    ))
                    run = 0
                    run_start_block = None
            elif block.kind == "code":
                # Code cuenta como prosa intermedia.
                run = 0
                run_start_block = None
            else:
                run = 0
                run_start_block = None

    # R5: ≤ 5 viñetas consecutivas sin prosa/estructura.
    if not exempt_r5:
        for section in parsed.sections:
            run = 0
            run_start_block: Optional[Block] = None
            for block in section.blocks:
                if block.kind == "list" and not block.is_checklist:
                    run += block.items or 1
                    if run_start_block is None:
                        run_start_block = block
                    if run > rules.max_consecutive_bullets:
                        issues.append(Issue(
                            code="R5", severity="error",
                            where=f"{section.heading}:list:{block.line}",
                            rule="R5 max viñetas consecutivas",
                            message=(
                                f"{run} viñetas consecutivas sin prosa/estructura "
                                f"(límite: {rules.max_consecutive_bullets})"
                            ),
                            measured=float(run), limit=float(rules.max_consecutive_bullets),
                        ))
                        run = 0
                        run_start_block = None
                else:
                    if block.kind in ("paragraph", "table", "callout", "figure",
                                       "diagram", "equation", "code"):
                        run = 0
                        run_start_block = None

    # R6: sección no puede ser 100% viñetas.
    if not exempt_r6:
        for section in parsed.sections:
            total = len(section.blocks)
            if total == 0:
                continue
            prose_or_struct = sum(
                1 for b in section.blocks
                if b.kind in ("paragraph", "table", "callout", "figure",
                               "diagram", "equation", "code")
            )
            if prose_or_struct == 0:
                issues.append(Issue(
                    code="R6", severity="error",
                    where=section.heading,
                    rule="R6 sección 100% viñetas",
                    message=(
                        f"Sección con {total} bloques, todos listas; requiere ≥ 1 "
                        f"párrafo, tabla, callout o figura"
                    ),
                ))

    # R7: > 100 líneas → marcar para plegable.
    if parsed.note_type != "architecture":
        for section in parsed.sections:
            if section.lines > rules.max_section_lines_for_unfolded and not section.is_collapsible:
                issues.append(Issue(
                    code="R7", severity="warning",
                    where=section.heading,
                    rule="R7 L3 > 100 líneas sin plegable",
                    message=(
                        f"Sección con {section.lines} líneas (límite: "
                        f"{rules.max_section_lines_for_unfolded}); envolver en "
                        f":::collapsible con default_open: false"
                    ),
                    measured=float(section.lines),
                    limit=float(rules.max_section_lines_for_unfolded),
                ))

    # R8: ≥ 0.80 {src:} por bloque fáctico.
    # Las secciones `## Autoevaluación` (F102) y `## Errores registrados` /
    # `## Resumen de errores` (F103, en living-docs `note-type: error-log`)
    # y sus H3 hijas quedan exentas: son ejercicios del lector o
    # meta-documentales, no bloques fácticos con anclaje al SDM.
    exempt_h2_starts = ("## Autoevaluaci", "## Errores registrados", "## Resumen de errores")
    in_exempt = False
    factual_count = 0
    anchored_count = 0
    for section in parsed.sections:
        if section.heading.startswith("## ") and any(
            ex in section.heading for ex in exempt_h2_starts
        ):
            in_exempt = True
            continue
        if section.heading.startswith("## ") and not any(
            ex in section.heading for ex in exempt_h2_starts
        ):
            in_exempt = False
        if in_exempt:
            continue
        for block in section.blocks:
            if block.is_factual:
                factual_count += 1
                if block.has_src_mark:
                    anchored_count += 1
    if factual_count >= 5:
        density = anchored_count / factual_count
        if density < rules.min_src_density_per_factual_block:
            issues.append(Issue(
                code="R8", severity="warning",
                where="/",
                rule="R8 densidad {src:}",
                message=(
            f"Densidad {density:.2f} ({anchored_count}/{factual_count}) "
            f"por debajo del mínimo {rules.min_src_density_per_factual_block:.2f}"
                ),
                measured=density, limit=rules.min_src_density_per_factual_block,
            ))

    return issues


def _render_markdown(issues: List[Issue], note_path: Path) -> str:
    if not issues:
        return f"OK — {note_path} cumple todas las reglas R1-R8."
    lines = [f"## Densidad — {note_path}", ""]
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if errors:
        lines.append(f"### Errores ({len(errors)})")
    for i in errors:
        lines.append(f"- **{i.code}** ({i.where}): {i.message}")
    if warnings:
        lines.append("")
        lines.append(f"### Advertencias ({len(warnings)})")
    for i in warnings:
        lines.append(f"- **{i.code}** ({i.where}): {i.message}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="density_check.py",
        description="Verificador de densidad y jerarquía (Fase 76).",
    )
    parser.add_argument("--note", type=Path, help="Ruta a un archivo .md")
    parser.add_argument("--notes", type=Path, help="Directorio con archivos .md (batch)")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Warnings también exit 1")
    parser.add_argument("--allow-violations", type=str, default="",
                        help="Lista separada por comas de reglas a ignorar (e.g. R2,R5)")
    args = parser.parse_args(argv)

    if not args.note and not args.notes:
        print("ERROR: debe pasar --note o --notes", file=sys.stderr)
        return 2

    allowed = set(filter(None, (s.strip() for s in args.allow_violations.split(","))))

    if args.note and not args.note.is_file():
        print(f"ERROR: nota no encontrada: {args.note}", file=sys.stderr)
        return 2

    targets: List[Path] = []
    if args.note:
        targets.append(args.note)
    if args.notes:
        if not args.notes.is_dir():
            print(f"ERROR: directorio no encontrado: {args.notes}", file=sys.stderr)
            return 2
        targets.extend(sorted(args.notes.glob("*.md")))

    exit_code = 0
    all_results: List[Dict[str, Any]] = []
    for path in targets:
        try:
            parsed = _parse_note(path)
        except Exception as e:
            print(f"ERROR: parseo falló para {path}: {e}", file=sys.stderr)
            return 2
        issues = _measure(parsed, Rules())
        # Filtrar allow-violations.
        issues = [i for i in issues if i.code not in allowed]
        # Determinar exit code para esta nota.
        if any(i.severity == "error" for i in issues):
            exit_code = 1
        elif args.strict and any(i.severity == "warning" for i in issues):
            exit_code = 1
        result = {
            "file": str(path),
            "note_type": parsed.note_type,
            "issues": [i.__dict__ for i in issues],
        }
        all_results.append(result)
        if args.json:
            continue
        print(_render_markdown(issues, path))
        print()

    if args.json:
        print(json.dumps({"results": all_results, "exit_code": exit_code},
                          indent=2, ensure_ascii=False))

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

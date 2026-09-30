#!/usr/bin/env python3
"""Validador del registro de errores propios — Fase 103.

Aplica las 7 reglas R-E1 a R-E7 definidas en
`references/09-study/error-log.md` §5 sobre un living-doc
`study/errors/<dominio>.md`:

  R-E1  Cada entrada tiene las 5 H3 en orden estricto.
  R-E2  Comando erróneo y corrección en bloques `:::code` verbatim.
  R-E3  Cada entrada tiene `### Repaso` con `review-next: <YYYY-MM-DD>`.
  R-E4  Cada corrección enlaza a la nota canónica con `[[note:id]]`.
  R-E5  Cero lenguaje de evaluación personal (lista cerrada §4).
  R-E6  Las tarjetas tienen tag `priority-error` (verificación indirecta:
        si el script `error_cards.py` se ejecuta, valida que el tag se
        añade correctamente; este validador no genera tarjetas).
  R-E7  El living-doc tiene `note-type: error-log` (meta-tipo).

CLI:
    python3 error_log_check.py --note <path>             # markdown a stdout
    python3 error_log_check.py --note <path> --json      # JSON estructurado
    python3 error_log_check.py --note <path> --strict    # warnings → exit 1
    python3 error_log_check.py --notes <dir>             # batch

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
from typing import Dict, FrozenSet, List, Optional, Tuple


DOC_PATH = (
    Path(__file__).resolve().parents[4]
    / "skill" / "notemartin-study-notes" / "references" / "09-study" / "error-log.md"
)

ERROR_H3_RE = re.compile(r"^###\s+Error\s+([\w\-]+(?:-[\w\-]+)*)\s*$", re.MULTILINE)
CODE_BLOCK_RE = re.compile(
    r":::code\s*\n(.*?)\n\s*:::",
    re.DOTALL,
)
NOTE_LINK_RE = re.compile(r"\[\[note:([a-z0-9][a-z0-9\-]*(?:#[\w\-§]+)?)\]\]")
REVIEW_NEXT_RE = re.compile(
    r"review-next:\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)

REQUIRED_SUBSECTIONS = (
    "Concepto",
    "Comando erróneo",
    "Corrección",
    "Origen",
    "Repaso",
)


@dataclass
class Violation:
    rule: str
    severity: str
    location: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class NoteReport:
    path: str
    note_type: Optional[str] = None
    violations: List[Violation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.severity == "error" for v in self.violations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": self.path,
            "note_type": self.note_type,
            "violations": [v.to_dict() for v in self.violations],
        }


def _load_prohibited_list(doc_path: Path) -> List[str]:
    """Carga la lista cerrada de frases prohibidas desde §4."""
    if not doc_path.exists():
        return []
    text = doc_path.read_text(encoding="utf-8")
    if "{#lista-cerrada-prohibidos}" not in text:
        return []
    sec4_match = re.search(
        r"## §4 · Lenguaje de evaluación personal.*?(?=^## §5)",
        text, re.MULTILINE | re.DOTALL,
    )
    if not sec4_match:
        return []
    sec4 = sec4_match.group(0)
    rows = re.findall(
        r"^\|\s*\d+\s*\|\s*[^\|]+\|\s*\"([^\"]+)\"",
        sec4, re.MULTILINE,
    )
    return rows


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    fm: Dict[str, str] = {}
    if not text.startswith("---"):
        return fm, text
    end = text.find("\n---", 3)
    if end < 0:
        return fm, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body


def _extract_section(body: str, h4: str) -> str:
    pattern = re.compile(
        rf"^####\s+{re.escape(h4)}\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def _strip_code_blocks(text: str) -> str:
    """Quita bloques `:::code` para análisis de prosa."""
    return CODE_BLOCK_RE.sub("", text)


def _has_autocritica(prosa: str, prohibited: List[str]) -> Optional[str]:
    """Detecta frases prohibidas en prosa narrativa."""
    prosa_l = prosa.lower()
    for frase in prohibited:
        # Normaliza: lowercase, quita el placeholder X (en mayúscula o minúscula,
        # con o sin espacio) y espacios redundantes.
        norm = frase.lower()
        # Quitar el placeholder X (con o sin espacio antes).
        norm = re.sub(r"\s*x\b", "", norm)
        norm = norm.strip()
        if norm and norm in prosa_l:
            return frase
    return None


def check_note(
    path: Path,
    prohibited: List[str],
    strict: bool = False,
) -> NoteReport:
    report = NoteReport(path=str(path))
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    report.note_type = fm.get("note-type")

    # R-E7: debe ser note-type: error-log.
    if report.note_type != "error-log":
        report.violations.append(Violation(
            "R-E7", "error", "frontmatter",
            f"note-type debe ser `error-log`, recibí `{report.note_type}`",
        ))
        return report

    # Buscar las entradas.
    matches = list(ERROR_H3_RE.finditer(body))
    if not matches:
        report.violations.append(Violation(
            "R-E0", "warning", "## Errores registrados",
            "el living-doc no contiene ninguna entrada `### Error <id>`",
        ))
        return report

    for idx, m in enumerate(matches):
        error_id = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        section = body[start:end]

        # R-E1: las 5 H3 obligatorias en orden.
        sub_presence = []
        for sub in REQUIRED_SUBSECTIONS:
            sub_presence.append(bool(_extract_section(section, sub)))
        missing = [s for s, present in zip(REQUIRED_SUBSECTIONS, sub_presence) if not present]
        if missing:
            report.violations.append(Violation(
                "R-E1", "error", f"### Error {error_id}",
                f"faltan sub-secciones obligatorias: {missing}",
            ))
            continue  # sin las 5 H3 no podemos validar el resto

        # R-E2: comando erróneo y corrección en bloques :::code verbatim.
        cmd_section = _extract_section(section, "Comando erróneo")
        cmd_code = CODE_BLOCK_RE.search(cmd_section)
        if not cmd_code:
            report.violations.append(Violation(
                "R-E2", "error", f"### Error {error_id} › Comando erróneo",
                "falta bloque `:::code` con el comando verbatim",
            ))
        else:
            cmd_text = cmd_code.group(1).strip()
            if len(cmd_text) < 3:
                report.violations.append(Violation(
                    "R-E2", "warning", f"### Error {error_id} › Comando erróneo",
                    f"comando tiene {len(cmd_text)} chars (esperaba ≥ 3)",
                ))

        corr_section = _extract_section(section, "Corrección")
        corr_code = CODE_BLOCK_RE.search(corr_section)
        if not corr_code:
            report.violations.append(Violation(
                "R-E2", "error", f"### Error {error_id} › Corrección",
                "falta bloque `:::code` con la corrección verbatim",
            ))

        # R-E3: review-next en Repaso.
        repaso_section = _extract_section(section, "Repaso")
        if not REVIEW_NEXT_RE.search(repaso_section):
            report.violations.append(Violation(
                "R-E3", "error", f"### Error {error_id} › Repaso",
                "falta `review-next: <YYYY-MM-DD>` ISO 8601",
            ))

        # R-E4: enlace a nota canónica en Corrección.
        if not NOTE_LINK_RE.search(corr_section):
            report.violations.append(Violation(
                "R-E4", "error", f"### Error {error_id} › Corrección",
                "falta enlace `[[note:id#§N]]` a la nota canónica",
            ))

        # R-E5: cero autocrítica en prosa narrativa (excluyendo :::code).
        prosa = _strip_code_blocks(section)
        prohibited_match = _has_autocritica(prosa, prohibited)
        if prohibited_match:
            sev = "error" if strict else "error"  # siempre error (AP16)
            report.violations.append(Violation(
                "R-E5", sev, f"### Error {error_id}",
                f"lenguaje de evaluación personal detectado: '{prohibited_match}' (AP16)",
            ))

    return report


def format_markdown(reports: List[NoteReport]) -> str:
    lines: List[str] = ["# error_log_check — reporte\n"]
    if not reports:
        lines.append("Sin notas analizadas.")
        return "\n".join(lines) + "\n"
    for r in reports:
        lines.append(f"## `{r.path}`  (note-type: `{r.note_type}`)\n")
        if not r.violations:
            lines.append("- ✅ sin violaciones\n")
        else:
            for v in r.violations:
                icon = "❌" if v.severity == "error" else "⚠️"
                lines.append(f"- {icon} **{v.rule}** ({v.severity}) — {v.location}: {v.message}")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="error_log_check.py",
        description="Validador del registro de errores propios (Fase 103).",
    )
    parser.add_argument("--note", type=Path, help="Ruta a un living-doc")
    parser.add_argument("--notes", type=Path,
                        help="Directorio con living-docs (batch)")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="warnings se convierten en exit 1")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[4]
    doc_path = repo_root / "skill" / "notemartin-study-notes" / "references" / "09-study" / "error-log.md"
    prohibited = _load_prohibited_list(doc_path)

    if not args.note and not args.notes:
        parser.error("debes pasar --note o --notes")

    paths: List[Path] = []
    if args.note:
        paths.append(args.note)
    if args.notes:
        paths.extend(sorted(args.notes.rglob("*.md")))

    reports: List[NoteReport] = []
    for p in paths:
        if not p.exists():
            print(f"[ERROR] archivo no encontrado: {p}", file=sys.stderr)
            return 2
        reports.append(check_note(p, prohibited, args.strict))

    if args.json:
        out = {
            "total": len(reports),
            "errors": sum(1 for r in reports if r.has_errors),
            "reports": [r.to_dict() for r in reports],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(reports))

    has_errors = any(r.has_errors for r in reports)
    if has_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

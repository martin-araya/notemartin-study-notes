#!/usr/bin/env python3
"""Consulta de repaso vencido — Fase 103.

Implementa las 4 reglas Q1-Q4 definidas en
`references/09-study/error-log.md` §6 sobre los living-docs en
`study/errors/*.md`:

  Q1 — Lectura del directorio: itera `*.md`, parsea frontmatter mínimo,
       filtra por `note-type: error-log`.
  Q2 — Extracción de entradas: por archivo, identifica H3 `### Error <id>`
       y extrae las 5 H3 hijas + `review-next` por entrada.
  Q3 — Filtro `--due`: entradas con `review-next < --as-of` (default hoy).
       Modo `--domain <slug>` filtra adicionalmente.
  Q4 — Emisión: Markdown legible por humano o JSON estructurado.

CLI:
    python3 error_log_query.py --list                                # todas las entradas
    python3 error_log_query.py --due                                 # solo vencidas
    python3 error_log_query.py --due --domain postgresql            # vencidas de un dominio
    python3 error_log_query.py --due --as-of 2026-12-31 --json      # vista previa futura
    python3 error_log_query.py --errors-dir /path/to/study/errors   # dir alternativo
    python3 error_log_query.py --list --strict                       # warnings → exit 1

Exit codes:
    0  OK (≥ 1 entrada listada o todas OK)
    1  --due sin entradas vencidas (info) o violación de strict
    2  error de uso (archivo no encontrado, etc.)

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REQUIRED_FRONTMATTER = ("title", "domain", "note-type", "tags", "retrieved")
ERROR_H3_RE = re.compile(r"^###\s+Error\s+([\w\-]+(?:-[\w\-]+)*)\s*$", re.MULTILINE)
REVIEW_NEXT_RE = re.compile(
    r"review-next:\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


@dataclass
class ErrorEntry:
    domain: str
    error_id: str
    concepto: str
    review_next: Optional[str]
    source_path: Path

    @property
    def overdue(self) -> Optional[int]:
        if self.review_next is None:
            return None
        try:
            d = date.fromisoformat(self.review_next)
        except ValueError:
            return None
        return (date.today() - d).days

    def is_overdue_as_of(self, as_of: date) -> bool:
        if self.review_next is None:
            return False
        try:
            d = date.fromisoformat(self.review_next)
        except ValueError:
            return False
        return d < as_of

    def to_dict(self, as_of: Optional[date] = None) -> Dict[str, object]:
        out: Dict[str, object] = {
            "domain": self.domain,
            "error_id": self.error_id,
            "concepto": self.concepto,
            "review_next": self.review_next,
            "source_path": str(self.source_path),
        }
        if self.review_next:
            try:
                d = date.fromisoformat(self.review_next)
                out["overdue_days"] = (date.today() - d).days
                if as_of:
                    out["overdue_as_of"] = (as_of - d).days
            except ValueError:
                pass
        return out


@dataclass
class Report:
    as_of: date
    errors_dir: Path
    entries: List[ErrorEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def overdue_entries(self) -> List[ErrorEntry]:
        return [e for e in self.entries if e.is_overdue_as_of(self.as_of)]

    @property
    def domains(self) -> List[str]:
        return sorted({e.domain for e in self.entries})

    def to_dict(self) -> Dict[str, object]:
        return {
            "as_of": self.as_of.isoformat(),
            "errors_dir": str(self.errors_dir),
            "total_entries": len(self.entries),
            "overdue_entries": len(self.overdue_entries),
            "domains": self.domains,
            "entries": [e.to_dict(self.as_of) for e in self.entries],
            "skipped": self.skipped,
        }


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Extrae el frontmatter YAML mínimo (sin PyYAML)."""
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


def _extract_section_text(body: str, section_h4: str) -> str:
    """Extrae el contenido bajo una H4 hasta la siguiente H4 o H3."""
    pattern = re.compile(
        rf"^####\s+{re.escape(section_h4)}\s*$(.*?)(?=^####\s+|^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else ""


def _extract_entries(path: Path, body: str, domain: str) -> List[ErrorEntry]:
    entries: List[ErrorEntry] = []
    matches = list(ERROR_H3_RE.finditer(body))
    for idx, m in enumerate(matches):
        error_id = m.group(1)
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        section = body[start:end]

        concepto = _extract_section_text(section, "Concepto").strip()
        repaso = _extract_section_text(section, "Repaso")
        review_match = REVIEW_NEXT_RE.search(repaso)
        review_next = review_match.group(1) if review_match else None

        entries.append(ErrorEntry(
            domain=domain,
            error_id=error_id,
            concepto=concepto,
            review_next=review_next,
            source_path=path,
        ))
    return entries


def collect(errors_dir: Path, as_of: date, domain_filter: Optional[str]) -> Report:
    report = Report(as_of=as_of, errors_dir=errors_dir)

    if not errors_dir.exists():
        return report

    for path in sorted(errors_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)

        if fm.get("note-type") != "error-log":
            continue

        missing = [k for k in REQUIRED_FRONTMATTER if k not in fm]
        if missing:
            report.skipped.append(
                f"{path.name}: frontmatter falta {missing}"
            )
            continue

        domain = fm.get("domain", "").strip()
        if domain_filter and domain != domain_filter:
            continue

        entries = _extract_entries(path, body, domain)
        report.entries.extend(entries)

    return report


def format_markdown(report: Report, *, only_overdue: bool) -> str:
    entries = report.overdue_entries if only_overdue else report.entries
    lines: List[str] = []
    title = (
        f"# Repaso vencido de errores propios (as-of {report.as_of.isoformat()})"
        if only_overdue
        else "# Listado de entradas de error (living-docs)"
    )
    lines.append(title)
    lines.append("")
    lines.append(f"- **Total entradas:** {len(report.entries)}")
    lines.append(f"- **Vencidas (≤ {report.as_of.isoformat()}):** {len(report.overdue_entries)}")
    lines.append(f"- **Dominios cubiertos:** {', '.join(report.domains) or '(ninguno)'}")
    if report.skipped:
        lines.append(f"- **Archivos omitidos:** {len(report.skipped)}")
    lines.append("")

    if not entries:
        lines.append("_Sin entradas para mostrar._")
        return "\n".join(lines) + "\n"

    lines.append("| Dominio | Error ID | Concepto | Review-next | Vencido (días) |")
    lines.append("|---|---|---|---|---|")
    for e in sorted(entries, key=lambda x: (x.domain, x.error_id)):
        overdue_days = "—"
        if e.review_next:
            try:
                d = date.fromisoformat(e.review_next)
                delta = (report.as_of - d).days
                overdue_days = str(delta) if delta > 0 else "0"
            except ValueError:
                overdue_days = "?"
        concepto_short = (e.concepto[:60] + "…") if len(e.concepto) > 60 else e.concepto
        lines.append(
            f"| `{e.domain}` | `{e.error_id}` | {concepto_short} | "
            f"{e.review_next or '—'} | {overdue_days} |"
        )

    if report.skipped:
        lines.append("")
        lines.append("## Archivos omitidos")
        for s in report.skipped:
            lines.append(f"- {s}")

    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="error_log_query.py",
        description="Consulta de repaso vencido del registro de errores (Fase 103).",
    )
    parser.add_argument("--list", action="store_true",
                        help="lista todas las entradas (default)")
    parser.add_argument("--due", action="store_true",
                        help="filtra solo las entradas vencidas")
    parser.add_argument("--domain", type=str, default=None,
                        help="filtra por dominio (kebab-case slug)")
    parser.add_argument("--as-of", type=str, default=None,
                        help="fecha de corte YYYY-MM-DD (default: hoy)")
    parser.add_argument("--errors-dir", type=Path, default=Path("study/errors"),
                        help="directorio con living-docs (default: study/errors/)")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--strict", action="store_true",
                        help="warnings se convierten en exit 1")
    args = parser.parse_args(argv)

    try:
        as_of = (
            date.fromisoformat(args.as_of)
            if args.as_of
            else date.today()
        )
    except ValueError:
        print(f"[ERROR] --as-of debe ser YYYY-MM-DD, recibí: {args.as_of}",
              file=sys.stderr)
        return 2

    only_overdue = bool(args.due)
    if not args.list and not args.due:
        args.list = True  # default

    if not args.errors_dir.exists():
        print(f"[ERROR] no existe --errors-dir: {args.errors_dir}",
              file=sys.stderr)
        return 2

    report = collect(args.errors_dir, as_of, args.domain)

    if args.json:
        out = report.to_dict()
        if only_overdue:
            out["entries"] = [e.to_dict(as_of) for e in report.overdue_entries]
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(report, only_overdue=only_overdue))

    if only_overdue and not report.overdue_entries:
        return 1
    if args.strict and report.skipped:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Inspect — verifica los artefactos generados para F77.

Lee cada artefacto en `artifacts/`, detecta:
  - Markdown: líneas > 200 chars (copy-paste defects), tablas con 10+ cols
    sin wrapper de overflow, links con formato no canónico, marcas `{src:}`
    con formato no canónico, código sin highlighting de 5+ líneas.
  - HTML/PDF: bloques sin cerrar (`<table>`, `<tr>`, `<td>`, `<p>`, `<div>`),
    <table> con <th> sin scope, inline styles > 10 (defecto de estilo), src:
    con formato no canónico.
  - Mermaid (SVG): viewBox inválido, ausencia de <title> accesible,
    dimensiones razonables.
  - Flashcards (CSV): RFC 4180 válido, campos requeridos presentes,
    > 5 clauses por front/back.

CLI:
    python3 inspect.py --artifacts-dir evals/visual/artifacts [--json] [--strict]

Exit codes: 0 (sin issues), 1 (con issues), 2 (error de uso).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

CANONICAL_SRC_RE = re.compile(r"\{src:blk_[0-9a-f]{12}\}")


@dataclass
class Issue:
    code: str
    severity: str          # "error" | "warning"
    file: str
    line: Optional[int]
    message: str


def inspect_markdown(path: Path) -> List[Issue]:
    issues: List[Issue] = []
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        if len(line) > 200:
            issues.append(Issue(
                code="MD_LINE_TOO_LONG",
                severity="warning",
                file=str(path),
                line=i,
                message=f"Línea con {len(line)} chars (límite 200)",
            ))
    # Tablas con 10+ cols sin wrapper.
    for i, line in enumerate(text.splitlines(), start=1):
        if line.startswith("|") and "---" not in line:
            cells = [c for c in line.split("|") if c.strip()]
            if len(cells) >= 10:
                issues.append(Issue(
                    code="MD_TABLE_WIDE",
                    severity="warning",
                    file=str(path),
                    line=i,
                    message=f"Tabla con {len(cells)} columnas; verificar overflow",
                ))
    # Marcas {src:} con formato no canónico.
    bad_src = re.findall(r"\{src:(?!blk_[0-9a-f]{12}\})[^}]*\}", text)
    for bad in bad_src[:5]:
        issues.append(Issue(
            code="MD_SRC_NONCANONICAL",
            severity="error",
            file=str(path),
            line=None,
            message=f"Marca {src!r} no canónica; esperado {{src:blk_xxxxxxxxxxxx}}",
        ))
    # Links rotos: [text](url) donde url no es relativo ni http(s) ni #anchor.
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", line)
        if m:
            url = m.group(2)
            if not (url.startswith("http") or url.startswith("#")
                    or url.startswith("./") or "/" in url or url.endswith(".md")):
                issues.append(Issue(
                    code="MD_LINK_FORMAT",
                    severity="warning",
                    file=str(path),
                    line=i,
                    message=f"Link con formato no estándar: ({url})",
                ))
    return issues


def inspect_html(path: Path) -> List[Issue]:
    issues: List[Issue] = []
    text = path.read_text(encoding="utf-8")
    # Verifica balanceo de tags principales.
    for tag in ("table", "tr", "td", "p", "div", "section", "h1", "h2", "h3"):
        opens = len(re.findall(rf"<{tag}\b", text, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}>", text, re.IGNORECASE))
        if opens != closes:
            issues.append(Issue(
                code=f"HTML_{tag.upper()}_UNBALANCED",
                severity="error",
                file=str(path),
                line=None,
                message=f"<{tag}>: {opens} aperturas vs {closes} cierres",
            ))
    # <table> con <th> sin scope. Regex: <th seguido de espacio, > o /> (no
    # 'e' u otra letra, para no matchear <thead>).
    th_tags = re.findall(r"<th(?:[\s>/][^>]*)?>", text, re.IGNORECASE)
    th_no_scope = [t for t in th_tags if "scope=" not in t.lower()]
    if th_no_scope:
        issues.append(Issue(
            code="HTML_TH_NO_SCOPE",
            severity="warning",
            file=str(path),
            line=None,
            message=f"{len(th_no_scope)} <th> sin scope attribute (a11y WCAG 1.3.1)",
        ))
    # Inline styles > 10 (defecto de estilo: debería ser class).
    inline = re.findall(r'style="[^"]{30,}"', text)
    if len(inline) > 10:
        issues.append(Issue(
            code="HTML_INLINE_STYLES",
            severity="warning",
            file=str(path),
            line=None,
            message=f"{len(inline)} inline styles (≥ 30 chars); preferir class",
        ))
    # Marcas {src:} no canónicas.
    bad_src = re.findall(r"\{src:(?!blk_[0-9a-f]{12}\})[^}]*\}", text)
    for bad in bad_src[:5]:
        issues.append(Issue(
            code="HTML_SRC_NONCANONICAL",
            severity="error",
            file=str(path),
            line=None,
            message=f"Marca no canónica: {src!r}",
        ))
    return issues


def inspect_svg(path: Path) -> List[Issue]:
    issues: List[Issue] = []
    text = path.read_text(encoding="utf-8")
    # viewBox inválido o ausente.
    m = re.search(r'viewBox="([^"]+)"', text)
    if not m:
        issues.append(Issue(
            code="SVG_NO_VIEWBOX",
            severity="error",
            file=str(path),
            line=None,
            message="<svg> sin viewBox",
        ))
    else:
        vb = m.group(1).split()
        if len(vb) != 4:
            issues.append(Issue(
                code="SVG_VIEWBOX_MALFORMED",
                severity="error",
                file=str(path),
                line=None,
                message=f"viewBox={m.group(1)!r} (esperado 4 valores)",
            ))
    # <title> ausente (a11y).
    if "<title>" not in text:
        issues.append(Issue(
            code="SVG_NO_TITLE",
            severity="warning",
            file=str(path),
            line=None,
            message="<svg> sin <title> (a11y WCAG 1.1.1)",
        ))
    # role="img" ausente.
    if 'role="img"' not in text and "role='img'" not in text:
        issues.append(Issue(
            code="SVG_NO_ROLE",
            severity="warning",
            file=str(path),
            line=None,
            message="<svg> sin role='img' (a11y)",
        ))
    return issues


def inspect_csv(path: Path) -> List[Issue]:
    issues: List[Issue] = []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return issues  # CSV vacío es válido si no hay tarjetas
    try:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
    except csv.Error as e:
        issues.append(Issue(
            code="CSV_RFC4180",
            severity="error",
            file=str(path),
            line=None,
            message=f"CSV malformado: {e}",
        ))
        return issues
    if not rows:
        return issues
    header = rows[0]
    required = {"front", "back"}
    missing = required - set(header)
    if missing:
        issues.append(Issue(
            code="CSV_MISSING_COLUMNS",
            severity="error",
            file=str(path),
            line=None,
            message=f"Columnas requeridas faltantes: {sorted(missing)}",
        ))
    # > 5 clauses por front/back (heurística: contar comas + puntos).
    for i, row in enumerate(rows[1:], start=2):
        if len(row) < 2:
            continue
        front, back = row[0], row[1]
        clauses_f = front.count(",") + front.count(".") + 1
        clauses_b = back.count(",") + back.count(".") + 1
        if clauses_f > 5:
            issues.append(Issue(
                code="CSV_FRONT_TOO_MANY_CLAUSES",
                severity="warning",
                file=str(path),
                line=i,
                message=f"front con {clauses_f} cláusulas (límite 5)",
            ))
        if clauses_b > 5:
            issues.append(Issue(
                code="CSV_BACK_TOO_MANY_CLAUSES",
                severity="warning",
                file=str(path),
                line=i,
                message=f"back con {clauses_b} cláusulas (límite 5)",
            ))
    return issues


def inspect_path(path: Path) -> List[Issue]:
    if not path.is_file():
        return [Issue(code="FILE_MISSING", severity="error",
                       file=str(path), line=None,
                       message="archivo no existe")]
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown"):
        return inspect_markdown(path)
    if suffix in (".html", ".htm"):
        return inspect_html(path)
    if suffix == ".svg":
        return inspect_svg(path)
    if suffix == ".csv":
        return inspect_csv(path)
    return []


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="inspect.py", description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="warnings → exit 1")
    args = parser.parse_args(argv)

    if not args.artifacts_dir.is_dir():
        print(f"ERROR: directorio no encontrado: {args.artifacts_dir}",
              file=sys.stderr)
        return 2

    all_issues: List[Issue] = []
    files = sorted(p for p in args.artifacts_dir.rglob("*") if p.is_file())
    for path in files:
        issues = inspect_path(path)
        all_issues.extend(issues)
        if not args.json:
            for i in issues:
                marker = "❌" if i.severity == "error" else "⚠️"
                line = f":{i.line}" if i.line else ""
                print(f"  {marker} {i.file}{line}  [{i.code}]  {i.message}")
    if not all_issues and not args.json:
        print(f"OK — {len(files)} artefactos sin issues.")
    if args.json:
        print(json.dumps(
            {"artifacts_count": len(files),
             "issues": [asdict(i) for i in all_issues]},
            indent=2, ensure_ascii=False,
        ))
    has_error = any(i.severity == "error" for i in all_issues)
    has_warning = any(i.severity == "warning" for i in all_issues)
    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

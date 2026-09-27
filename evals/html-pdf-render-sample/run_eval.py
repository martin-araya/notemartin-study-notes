#!/usr/bin/env python3
"""run_eval.py — eval battery del renderer HTML/PDF (F59).

10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/html-pdf-render-sample/run_eval.py [--verbose]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile


HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
HTML_PDF_PY = REPO / "skill/notemartin-study-notes/scripts/render/html_pdf.py"
FIXTURES = HERE / "fixtures"


def run_renderer(workdir: pathlib.Path, ir_arg: pathlib.Path,
                 profile: pathlib.Path, *extra: str) -> tuple:
    cmd = [
        sys.executable, str(HTML_PDF_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def render_to(workdir: pathlib.Path, ir_arg: pathlib.Path,
              profile: pathlib.Path, *extra: str) -> bool:
    """Devuelve True si el renderer terminó (exit 0 o 2)."""
    rc, _, _ = run_renderer(workdir, ir_arg, profile, *extra)
    return rc in (0, 2)


def read_html(workdir: pathlib.Path, note_id: str) -> str:
    return (workdir / "render" / "html_pdf" / f"{note_id}.html").read_text(
        encoding="utf-8"
    )


def read_report(workdir: pathlib.Path) -> dict:
    return json.loads(
        (workdir / "reports" / "render-degradation.json").read_text(encoding="utf-8")
    )


def install_weasyprint_stub():
    """Copia el stub de weasyprint al path que el renderer espera."""
    src = HERE / "scripts" / "weasyprint.py"
    target = HTML_PDF_PY.parent / "weasyprint.py"
    shutil.copy(src, target)


def uninstall_weasyprint_stub():
    target = HTML_PDF_PY.parent / "weasyprint.py"
    if target.exists():
        target.unlink()


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_self_contained(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1): HTML funciona sin conexión y sin recursos externos."""
    if not render_to(workdir / "c1", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c1", "ff0000000001")
    # Strip CSS comments (/* ... */) para evitar falsos positivos en
    # comentarios que describen qué NO usar.
    css_removed = re.sub(r"/\*.*?\*/", "", html, flags=re.DOTALL)
    bad_patterns = [
        r'<link\s+rel="stylesheet"\s+href="http',
        r'<script\s+src="http',
        r'@import\s+url\([\'"]?http',
        r'<img\s+src="http',
        r'url\(\s*[\'"]?http',
        r'url\(\s*//',
    ]
    found: list = []
    for pat in bad_patterns:
        for m in re.finditer(pat, css_removed, re.IGNORECASE):
            found.append(f"{pat} → {m.group(0)[:60]}")
    has_inline_style = bool(re.search(r"<style>", html))
    has_script = bool(re.search(r"<script", html, re.IGNORECASE))
    return (len(found) == 0 and has_inline_style and not has_script,
            f"external refs: {len(found)}; inline_style={has_inline_style}; "
            f"scripts={has_script}")


def c2_no_page_break(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): PDF no parte tablas ni código por la mitad."""
    if not render_to(workdir / "c2", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c2", "ff0000000001")
    # Extraer el bloque @media print.
    m = re.search(r"@media print\s*\{(.*?)\n\}", html, re.DOTALL)
    if not m:
        return False, "no hay bloque @media print"
    print_css = m.group(1)
    required_selectors = ["table", "pre", "code", "figure", "aside", "blockquote", "dl"]
    missing = [s for s in required_selectors
               if not re.search(rf"\b{re.escape(s)}\b[^{{}}]*\{{[^}}]*page-break-inside:\s*avoid", print_css)]
    has_page_rule = "page-break-inside: avoid" in print_css
    return (has_page_rule and len(missing) == 0,
            f"page-break-inside avoid={has_page_rule}; missing={missing}")


def c3_quotes_survive(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): las citas sobreviven."""
    if not render_to(workdir / "c3", FIXTURES / "ir-with-quotes.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c3", "ff0000000002")
    blockquotes = re.findall(r"<blockquote>", html)
    cites = re.findall(r"<cite>([^<]+)</cite>", html)
    platon = any("Platón" in c for c in cites)
    aristoteles = any("Aristóteles" in c for c in cites)
    return (len(blockquotes) >= 2 and platon and aristoteles,
            f"blockquotes={len(blockquotes)}; cites={cites}")


def c4_toc_present(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: TOC sidebar presente."""
    if not render_to(workdir / "c4", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c4", "ff0000000001")
    has_toc = bool(re.search(r'<nav\s+id="toc"', html))
    has_index = "Índice" in html or "Indice" in html or "Indice" in html
    has_layout = '<div class="layout">' in html
    return (has_toc and has_index and has_layout,
            f"toc={has_toc}, index_word={has_index}, layout={has_layout}")


def c5_diagram_svg(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: diagramas como SVG inline (criterio 1)."""
    # Sin F70: <pre class="mermaid"> (acceptable fallback).
    if not render_to(workdir / "c5", FIXTURES / "ir-with-diagram.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c5", "ff0000000005")
    has_pre_mermaid = bool(re.search(r'<pre\s+class="mermaid"', html))
    has_figure_diagram = '<figure class="diagram">' in html
    return (has_pre_mermaid or has_figure_diagram,
            f"pre_mermaid={has_pre_mermaid}, figure_diagram={has_figure_diagram}")


def c6_head_meta(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: cabecera §8 visible en <head>."""
    if not render_to(workdir / "c6", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c6", "ff0000000001")
    required = ["schema_version", "target", "note_id", "source_hash",
                "ir_sha256", "rendered_at", "renderer_version"]
    missing = [k for k in required if not re.search(rf'<meta\s+name="{k}"', html)]
    return (len(missing) == 0, f"missing meta: {missing}" if missing else "7 metas presentes")


def c7_backlinks(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: backlinks (fila 8 §6) → <aside class='backlinks'>."""
    if not render_to(workdir / "c7", FIXTURES, FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c7", "ff0000000012")
    has_aside = bool(re.search(r'<aside\s+class="backlinks"', html))
    has_link_to_a = bool(re.search(r'href="ff0000000011\.html"', html))
    return (has_aside and has_link_to_a,
            f"aside={has_aside}, link_to_a={has_link_to_a}")


def c8_queries(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: queries (fila 17 §6) → <section class='queries'>."""
    if not render_to(workdir / "c8", FIXTURES / "ir-with-query.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló"
    html = read_html(workdir / "c8", "ff0000000004")
    has_section = bool(re.search(r'<section\s+class="queries"', html))
    has_query = "TABLE field FROM notes" in html
    return (has_section and has_query,
            f"section={has_section}, query_in_html={has_query}")


def c9_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: idempotencia byte-a-byte (módulo timestamp en cabecera)."""
    wd1 = workdir / "c9-a"
    wd2 = workdir / "c9-b"
    if not render_to(wd1, FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló (a)"
    if not render_to(wd2, FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-html-pdf.yaml", "--no-pdf"):
        return False, "renderer falló (b)"
    h1 = read_html(wd1, "ff0000000001")
    h2 = read_html(wd2, "ff0000000001")
    rendered_re = re.compile(r'<meta name="rendered_at" content="[^"]+">')
    h1_norm = rendered_re.sub('<meta name="rendered_at" content="X">', h1)
    h2_norm = rendered_re.sub('<meta name="rendered_at" content="X">', h2)
    return (h1_norm == h2_norm, f"outputs idénticos: {h1_norm == h2_norm}")


def c10_pdf_graceful(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: PDF generation graceful — sin weasyprint, exit 0 con warning."""
    # Sin weasyprint.
    uninstall_weasyprint_stub()
    rc, _, _ = run_renderer(
        workdir / "c10-no-weasy", FIXTURES / "ir-single-note.json",
        FIXTURES / "profile-html-pdf.yaml",
    )
    if rc not in (0, 2):
        return False, f"renderer sin weasyprint exit={rc} (esperaba 0 o 2)"
    report = read_report(workdir / "c10-no-weasy")
    pdf_status = report.get("pdf_status", "")
    has_pdf_degradation = any(
        d.get("capability") == "pdf-export" for d in report.get("degradations", [])
    )
    html_present = (workdir / "c10-no-weasy" / "render" / "html_pdf" / "ff0000000001.html").exists()

    # Con weasyprint (mock).
    install_weasyprint_stub()
    try:
        rc2, _, err2 = run_renderer(
            workdir / "c10-weasy", FIXTURES / "ir-single-note.json",
            FIXTURES / "profile-html-pdf.yaml",
        )
        if rc2 not in (0, 2):
            return False, f"renderer con weasyprint exit={rc2}: {err2}"
        report2 = read_report(workdir / "c10-weasy")
        pdf_status2 = report2.get("pdf_status", "")
        pdf_path = workdir / "c10-weasy" / "render" / "html_pdf" / "ff0000000001.pdf"
        pdf_generated = pdf_path.exists()
    finally:
        uninstall_weasyprint_stub()

    return (pdf_status.startswith("skipped") and has_pdf_degradation and html_present
            and pdf_status2 == "generated" and pdf_generated,
            f"sin: status={pdf_status} pdf_deg={has_pdf_degradation} html={html_present}; "
            f"con: status={pdf_status2} pdf_file={pdf_generated}")


CHECKS = [
    ("C1 HTML self-contained (criterio 1)", c1_self_contained),
    ("C2 CSS @media print page-break rules (criterio 2)", c2_no_page_break),
    ("C3 Citas sobreviven (criterio 3)", c3_quotes_survive),
    ("C4 TOC sidebar presente", c4_toc_present),
    ("C5 Diagram: SVG inline o mermaid fallback", c5_diagram_svg),
    ("C6 Head <meta> §8 contract", c6_head_meta),
    ("C7 Backlinks <aside> (fila 8 §6)", c7_backlinks),
    ("C8 Queries <section> (fila 17 §6)", c8_queries),
    ("C9 Idempotencia", c9_idempotent),
    ("C10 PDF graceful: sin y con weasyprint", c10_pdf_graceful),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not HTML_PDF_PY.exists():
        print(f"ERROR: html_pdf.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="html-pdf-eval-"))
    print("=" * 70)
    print("F59 · Eval battery — Renderer HTML/PDF")
    print("=" * 70)

    passed = 0
    try:
        for name, fn in CHECKS:
            try:
                ok, detail = fn(workdir)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ok, detail = False, f"exception: {e}"
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}")
            if args.verbose or not ok:
                print(f"         {detail}")
            if ok:
                passed += 1
    finally:
        uninstall_weasyprint_stub()
        shutil.rmtree(workdir, ignore_errors=True)

    print("=" * 70)
    print(f"  Resultado: {passed}/{len(CHECKS)} verde")
    print("=" * 70)
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

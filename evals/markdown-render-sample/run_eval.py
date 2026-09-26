#!/usr/bin/env python3
"""run_eval.py — eval battery del renderer Markdown estándar (F58).

Stdlib puro. 10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/markdown-render-sample/run_eval.py [--verbose]
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
MARKDOWN_PY = REPO / "skill/notemartin-study-notes/scripts/render/markdown.py"
FIXTURES = HERE / "fixtures"


def run_renderer(workdir: pathlib.Path, ir_arg: pathlib.Path,
                 profile: pathlib.Path, *extra: str) -> tuple:
    cmd = [
        sys.executable, str(MARKDOWN_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def read_note(workdir: pathlib.Path, note_id: str) -> str:
    return (workdir / "render" / "markdown" / f"{note_id}.md").read_text(
        encoding="utf-8"
    )


def read_report(workdir: pathlib.Path) -> dict:
    return json.loads(
        (workdir / "reports" / "render-degradation.json").read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_gfm_compliant(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1): GFM-compliant para GitHub."""
    if run_renderer(workdir / "c1", FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c1", "ee0000000001")
    bad_patterns = [
        r"^:::", r":::warning", r":::note", r":::collapsible",
        r"\{src:", r"\{derived\}", r"\{external\}",
    ]
    found: list = []
    for pat in bad_patterns:
        if re.search(pat, note, re.MULTILINE):
            found.append(pat)
    has_yaml = len(re.findall(r"^---$", note, re.MULTILINE)) >= 2
    has_yaml_fields = all(re.search(rf"^{k}:", note, re.MULTILINE) for k in
                          ["schema_version", "target", "note_id", "source_hash",
                           "ir_sha256", "rendered_at", "renderer_version"])
    if not has_yaml:
        return False, "Falta frontmatter YAML"
    if not has_yaml_fields:
        return False, "Faltan campos YAML §8"
    return (len(found) == 0,
            f"raw syntax: {found}; yaml={has_yaml_fields}")


def c2_no_content_loss(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): nada se pierde; content_loss == 0 y content_intact en entries."""
    rc, _, _ = run_renderer(
        workdir / "c2", FIXTURES / "ir-with-merged-table.json",
        FIXTURES / "profile-markdown.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    report = read_report(workdir / "c2")
    if report.get("target") != "markdown":
        return False, f"target={report.get('target')} != markdown"
    if report["totals"]["content_loss"] != 0:
        return False, f"content_loss={report['totals']['content_loss']}"
    bad = [d for d in report.get("degradations", [])
           if not d.get("content_intact")]
    if bad:
        return False, f"bad entries: {bad}"
    return True, (f"content_loss=0; {len(report['degradations'])} degradaciones; "
                  f"todas content_intact=true")


def c3_relative_links(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): enlaces relativos resuelven en la estructura generada."""
    # Renderizar las 3 notas de backlinks; verificar que cada [text](<id>.md)
    # apunta a un archivo que existe en render/markdown/.
    rc, _, _ = run_renderer(
        workdir / "c3", FIXTURES, FIXTURES / "profile-markdown.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    md_dir = workdir / "c3" / "render" / "markdown"
    if not md_dir.exists():
        return False, f"no existe {md_dir}"
    rendered_files = {p.stem for p in md_dir.glob("*.md")}
    # Buscar enlaces en cada nota.
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
    broken: list = []
    for note_path in sorted(md_dir.glob("*.md")):
        text = note_path.read_text(encoding="utf-8")
        for m in pattern.finditer(text):
            target_file = m.group(2).replace("./", "").lstrip("/")
            # Strip path components.
            target_id = target_file.replace(".md", "").split("/")[-1]
            if target_id not in rendered_files:
                broken.append(f"{note_path.name} -> {m.group(2)}")
    return (len(broken) == 0,
            f"rendered_files: {sorted(rendered_files)}; "
            f"broken: {broken if broken else 'ninguno'}")


def c4_admonitions(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: admonitions con emoji + CSS class."""
    if run_renderer(workdir / "c4", FIXTURES / "ir-with-admonitions.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c4", "ee0000000002")
    # Verificar que cada admonition tenga emoji prefijo + CSS class.
    blockquotes = re.findall(r"^>\s*\[!(\w+)\]", note, re.MULTILINE)
    has_css = bool(re.search(r'\{\.callout-', note))
    # Contar emojis (cualquier emoji como prefijo del blockquote).
    pattern = re.compile(r"^>\s*\[!\w+\][^\n]*[\U0001F000-\U0001FFFF\u2600-\u27BF\u2130-\u2BFF]")
    emoji_lines = sum(1 for line in note.splitlines()
                      if pattern.match(line))
    return (len(blockquotes) >= 8 and has_css and emoji_lines >= 8,
            f"blockquotes={len(blockquotes)}; css_class={has_css}; "
            f"emoji_lines={emoji_lines}")


def c5_merged_table(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: celdas combinadas → <details> con matriz completa (fila 5 §6)."""
    if run_renderer(workdir / "c5", FIXTURES / "ir-with-merged-table.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c5", "ee0000000003")
    has_details = '<details markdown="1">' in note
    has_legend = "Estructura original" in note
    return (has_details and has_legend,
            f"details={has_details}, legend={has_legend}")


def c6_backlinks_section(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: backlinks → '## Referenciado por' (fila 7 §6)."""
    rc, _, _ = run_renderer(
        workdir / "c6", FIXTURES, FIXTURES / "profile-markdown.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    # La nota B (ee0000000012) tiene incoming de A; la nota C (ee0000000013) tiene incoming de B.
    note_b = read_note(workdir / "c6", "ee0000000012")
    note_c = read_note(workdir / "c6", "ee0000000013")
    has_b = "## Referenciado por" in note_b
    has_c = "## Referenciado por" in note_c
    has_b_link = "[ee0000000011](ee0000000011.md)" in note_b
    has_c_link = "[ee0000000012](ee0000000012.md)" in note_c
    return (has_b and has_c and has_b_link and has_c_link,
            f"B: heading={has_b}, link={has_b_link}; "
            f"C: heading={has_c}, link={has_c_link}")


def c7_properties(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: propiedades en YAML frontmatter."""
    if run_renderer(workdir / "c7", FIXTURES / "ir-with-properties.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c7", "ee0000000004")
    required = ["author", "priority"]
    missing = [k for k in required if not re.search(rf"^{k}:", note, re.MULTILINE)]
    return (len(missing) == 0, f"missing: {missing}" if missing else "2 props presentes")


def c8_queries_table(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: queries → '## Consultas habituales' (fila 16 §6)."""
    if run_renderer(workdir / "c8", FIXTURES / "ir-with-query.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c8", "ee0000000005")
    has_heading = "## Consultas habituales" in note
    has_query = "TABLE field FROM notes" in note
    return (has_heading and has_query,
            f"heading={has_heading}, query_in_output={has_query}")


def c9_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: idempotencia byte-a-byte (módulo timestamp)."""
    wd1 = workdir / "c9-a"
    wd2 = workdir / "c9-b"
    if run_renderer(wd1, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló (a)"
    if run_renderer(wd2, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-markdown.yaml")[0] != 0:
        return False, "renderer falló (b)"
    n1 = read_note(wd1, "ee0000000001")
    n2 = read_note(wd2, "ee0000000001")
    rendered_re = re.compile(r'rendered_at: "[^"]+"')
    n1_norm = rendered_re.sub("rendered_at: X", n1)
    n2_norm = rendered_re.sub("rendered_at: X", n2)
    return (n1_norm == n2_norm, f"outputs idénticos: {n1_norm == n2_norm}")


def c10_diagram_strategy(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: diagramas con imagen de respaldo si pre-render; mermaid-only si no."""
    # Sin F70.
    rc1, _, _ = run_renderer(
        workdir / "c10-nof70", FIXTURES / "ir-with-diagram.json",
        FIXTURES / "profile-markdown.yaml",
        "--pre-render-diagrams",
    )
    if rc1 != 0:
        return False, f"renderer falló (sin F70): exit={rc1}"
    note1 = read_note(workdir / "c10-nof70", "ee0000000006")
    has_mermaid1 = bool(re.search(r"^```mermaid", note1, re.MULTILINE))
    has_img1 = bool(re.search(r"!\[[^\]]*\]\([^)]+\.svg\)", note1))
    # Con F70 (copiar stub).
    f70 = MARKDOWN_PY.parent / "diagram_image.py"
    f70_stub = HERE / "scripts" / "diagram_image.py"  # si existe
    if f70_stub.exists():
        shutil.copy(f70_stub, f70)
    try:
        rc2, _, _ = run_renderer(
            workdir / "c10-f70", FIXTURES / "ir-with-diagram.json",
            FIXTURES / "profile-markdown.yaml",
            "--pre-render-diagrams",
        )
        if rc2 != 0:
            return False, f"renderer falló (con F70): exit={rc2}"
        note2 = read_note(workdir / "c10-f70", "ee0000000006")
        has_mermaid2 = bool(re.search(r"^```mermaid", note2, re.MULTILINE))
        has_img2 = bool(re.search(r"!\[[^\]]*\]\([^)]+\.svg\)", note2))
    finally:
        if f70.exists():
            f70.unlink()

    return (has_mermaid1 and not has_img1 and has_mermaid2 and has_img2,
            f"sin F70: mermaid={has_mermaid1} img={has_img1}; "
            f"con F70: mermaid={has_mermaid2} img={has_img2}")


CHECKS = [
    ("C1 GFM-compliant para GitHub (criterio 1)",
     c1_gfm_compliant),
    ("C2 Sin pérdida de contenido (criterio 2)",
     c2_no_content_loss),
    ("C3 Enlaces relativos resuelven (criterio 3)",
     c3_relative_links),
    ("C4 Admonitions con emoji + CSS class (fila 12 §6)",
     c4_admonitions),
    ("C5 Celdas combinadas (fila 5 §6)",
     c5_merged_table),
    ("C6 Backlinks (fila 7 §6)",
     c6_backlinks_section),
    ("C7 Properties en YAML",
     c7_properties),
    ("C8 Queries table (fila 16 §6)",
     c8_queries_table),
    ("C9 Idempotencia",
     c9_idempotent),
    ("C10 Diagram: mermaid + image fallback",
     c10_diagram_strategy),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not MARKDOWN_PY.exists():
        print(f"ERROR: markdown.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="markdown-eval-"))
    print("=" * 70)
    print("F58 · Eval battery — Renderer Markdown estándar")
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
        shutil.rmtree(workdir, ignore_errors=True)

    print("=" * 70)
    print(f"  Resultado: {passed}/{len(CHECKS)} verde")
    print("=" * 70)
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

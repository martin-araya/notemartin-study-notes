#!/usr/bin/env python3
"""run_eval.py — eval battery del renderer Notion import (Markdown) (F56).

Stdlib puro. 10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/notion-md-render-sample/run_eval.py [--verbose]
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
NOTION_MD_PY = REPO / "skill/notemartin-study-notes/scripts/render/notion_md.py"
FIXTURES = HERE / "fixtures"
RENDERER_SCHEMA = REPO / "evals/render-contract-sample/schema/report.schema.json"


def run_renderer(workdir: pathlib.Path, ir_arg: pathlib.Path,
                 profile: pathlib.Path, *extra: str) -> tuple:
    cmd = [
        sys.executable, str(NOTION_MD_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def read_note(workdir: pathlib.Path, note_id: str) -> str:
    return (workdir / "render" / "notion_md" / f"{note_id}.md").read_text(
        encoding="utf-8"
    )


def read_report(workdir: pathlib.Path) -> dict:
    return json.loads(
        (workdir / "reports" / "render-degradation.json").read_text(encoding="utf-8")
    )


def validate_report_schema(report: dict) -> tuple[bool, str]:
    schema = json.loads(RENDERER_SCHEMA.read_text(encoding="utf-8"))
    if report.get("target") != "notion_md":
        return False, f"target={report.get('target')} != notion_md"
    if report.get("totals", {}).get("content_loss", -1) != 0:
        return False, f"content_loss={report.get('totals', {}).get('content_loss')}"
    return True, "OK"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_no_raw_syntax(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1): sin bloques rotos ni sintaxis cruda (NoteMark residual)."""
    if run_renderer(workdir / "c1", FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c1", "cc0000000001")
    bad_patterns = [
        r"^:::",       # directivas NoteMark residuales
        r":::warning",
        r":::note",
        r":::collapsible",
        r":::tip",
        r"\{src:",    # marcas inline NoteMark residuales
        r"\{derived\}",
        r"\{external\}",
    ]
    found: list = []
    for pat in bad_patterns:
        m = re.search(pat, note, re.MULTILINE)
        if m:
            found.append(f"{pat} → {m.group(0)[:30]}")
    return (len(found) == 0, f"raw syntax found: {found}" if found else "limpio")


def c2_cross_target_warning(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): el reporte advierte qué se degradó respecto a notion_api."""
    rc, _, _ = run_renderer(
        workdir / "c2", FIXTURES / "ir-with-admonitions.json",
        FIXTURES / "profile-notion-md.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    report = read_report(workdir / "c2")
    diff = report.get("cross_target_diff", {}).get("vs_notion_api", {})
    if not diff:
        return False, "no hay cross_target_diff.vs_notion_api"
    for key in ["admonition", "property-block", "table-merged-cells", "color-semantic"]:
        if key not in diff:
            return False, f"falta {key} en cross_target_diff"
    has_vs_in_entries = all(
        "vs_notion_api" in d for d in report.get("degradations", [])
    )
    return (has_vs_in_entries,
            f"diff keys: {sorted(diff.keys())}; "
            f"vs_notion_api en entries: {has_vs_in_entries}")


def c3_no_content_loss(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): nada se pierde; content_loss == 0 y content_intact: true."""
    rc, _, _ = run_renderer(
        workdir / "c3", FIXTURES / "ir-with-admonitions.json",
        FIXTURES / "profile-notion-md.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    report = read_report(workdir / "c3")
    if report["totals"]["content_loss"] != 0:
        return False, f"content_loss={report['totals']['content_loss']}"
    bad = [d for d in report["degradations"] if not d.get("content_intact")]
    return (len(bad) == 0, f"content_loss=0; bad entries: {bad}")


def c4_yaml_header(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: cabecera YAML cumple contract §8 (7 campos)."""
    if run_renderer(workdir / "c4", FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c4", "cc0000000001")
    required = ["schema_version", "target", "note_id", "source_hash",
                "ir_sha256", "rendered_at", "renderer_version"]
    missing = [k for k in required if not re.search(rf"^{k}:", note, re.MULTILINE)]
    return (len(missing) == 0, f"missing: {missing}" if missing else "7 campos presentes")


def c5_admonition_emojis(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: admonitions con emoji prefijo en blockquote."""
    if run_renderer(workdir / "c5", FIXTURES / "ir-with-admonitions.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c5", "cc0000000002")
    # Buscar líneas que empiecen con "> " + emoji/símbolo semántico.
    # Incluye BMP (ℹ U+2139) + rangos emoji extendidos + símbolos misc.
    lines = note.splitlines()
    emoji_lines = []
    pattern = re.compile(
        r"^>\s*([\U0001F000-\U0001FFFF\u2600-\u27BF\u2130-\u2BFF])"
    )
    for line in lines:
        m = pattern.match(line)
        if m:
            emoji_lines.append(m.group(1))
    return (len(emoji_lines) >= 9,
            f"emoji blockquote lines: {len(emoji_lines)} (esperaba ≥9)")


def c6_collapsible(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: collapsibles → <details markdown='1'>."""
    if run_renderer(workdir / "c6", FIXTURES / "ir-with-collapsible.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c6", "cc0000000005")
    has_details = '<details markdown="1">' in note
    has_summary = "<summary>" in note
    return (has_details and has_summary,
            f"details={has_details}, summary={has_summary}")


def c7_merged_table(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: celdas combinadas → <details> con matriz completa."""
    if run_renderer(workdir / "c7", FIXTURES / "ir-with-merged-table.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c7", "cc0000000003")
    has_details = '<details markdown="1">' in note
    has_legend = "Estructura original" in note
    return (has_details and has_legend,
            f"details={has_details}, legend={has_legend}")


def c8_frontmatter_props(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: frontmatter YAML contiene todas las properties del IR."""
    if run_renderer(workdir / "c8", FIXTURES / "ir-with-properties.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c8", "cc0000000004")
    required = ["author", "priority", "is_published"]
    missing = [k for k in required if not re.search(rf"^{k}:", note, re.MULTILINE)]
    return (len(missing) == 0, f"missing props: {missing}" if missing else "3 props presentes")


def c9_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: idempotencia byte-a-byte (módulo timestamp)."""
    wd1 = workdir / "c9-a"
    wd2 = workdir / "c9-b"
    if run_renderer(wd1, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló (a)"
    if run_renderer(wd2, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-notion-md.yaml")[0] != 0:
        return False, "renderer falló (b)"
    n1 = read_note(wd1, "cc0000000001")
    n2 = read_note(wd2, "cc0000000001")
    rendered_re = re.compile(r'rendered_at: "[^"]+"')
    n1_norm = rendered_re.sub("rendered_at: X", n1)
    n2_norm = rendered_re.sub("rendered_at: X", n2)
    return (n1_norm == n2_norm,
            f"outputs idénticos módulo timestamp: {n1_norm == n2_norm}")


def c10_import_instructions(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: --include-import-instructions escribe IMPORT_INSTRUCTIONS.md."""
    rc, _, _ = run_renderer(
        workdir / "c10", FIXTURES / "ir-single-note.json",
        FIXTURES / "profile-notion-md.yaml",
        "--include-import-instructions",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    p = workdir / "c10" / "render" / "notion_md" / "IMPORT_INSTRUCTIONS.md"
    if not p.exists():
        return False, f"falta {p}"
    content = p.read_text(encoding="utf-8")
    has_steps = "1." in content and "2." in content and "3." in content
    has_limits = "Limitaciones conocidas" in content or "Limitaciones" in content
    return (has_steps and has_limits,
            f"steps={has_steps}, limits={has_limits}")


CHECKS = [
    ("C1 Sin sintaxis cruda (criterio 1)", c1_no_raw_syntax),
    ("C2 Reporte advierte vs notion_api (criterio 2)", c2_cross_target_warning),
    ("C3 Nada se pierde (criterio 3)", c3_no_content_loss),
    ("C4 Cabecera YAML §8", c4_yaml_header),
    ("C5 Admonitions con emoji", c5_admonition_emojis),
    ("C6 Collapsible <details>", c6_collapsible),
    ("C7 Merged table fila 3 §6", c7_merged_table),
    ("C8 Properties en frontmatter (fila 15 §6)", c8_frontmatter_props),
    ("C9 Idempotencia", c9_idempotent),
    ("C10 Instrucciones de importación", c10_import_instructions),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not NOTION_MD_PY.exists():
        print(f"ERROR: notion_md.py no encontrado", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="notion-md-eval-"))
    print("=" * 70)
    print("F56 · Eval battery — Renderer Notion import (Markdown)")
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

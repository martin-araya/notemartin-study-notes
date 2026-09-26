#!/usr/bin/env python3
"""run_eval.py — eval battery del renderer AppFlowy (F57).

Stdlib puro. 10 sub-checks. Salida: N/10 verde.

Uso:
    python3 evals/appflowy-render-sample/run_eval.py [--verbose]
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
APPFLOWY_PY = REPO / "skill/notemartin-study-notes/scripts/render/appflowy.py"
FIXTURES = HERE / "fixtures"
F70_STUB = HERE / "scripts" / "diagram_image.py"
RENDERER_SCHEMA = REPO / "evals/render-contract-sample/schema/report.schema.json"


def run_renderer(workdir: pathlib.Path, ir_arg: pathlib.Path,
                 profile: pathlib.Path, *extra: str) -> tuple:
    cmd = [
        sys.executable, str(APPFLOWY_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout, p.stderr


def read_note(workdir: pathlib.Path, note_id: str) -> str:
    return (workdir / "render" / "appflowy" / f"{note_id}.md").read_text(
        encoding="utf-8"
    )


def read_report(workdir: pathlib.Path) -> dict:
    return json.loads(
        (workdir / "reports" / "render-degradation.json").read_text(encoding="utf-8")
    )


def with_f70_stub(enabled: bool):
    """Copia el stub F70 a la ubicación esperada por el renderer."""
    target = APPFLOWY_PY.parent / "diagram_image.py"
    if enabled:
        shutil.copy(F70_STUB, target)
    elif target.exists():
        target.unlink()


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_clean_markdown(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1, parcial): Markdown limpio compatible con AppFlowy."""
    if run_renderer(workdir / "c1", FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c1", "dd0000000001")
    bad_patterns = [
        r"^:::", r":::warning", r":::note", r":::collapsible",
        r"\{src:", r"\{derived\}", r"\{external\}",
    ]
    found = []
    for pat in bad_patterns:
        if re.search(pat, note, re.MULTILINE):
            found.append(pat)
    has_yaml = len(re.findall(r"^---$", note, re.MULTILINE)) >= 2
    if not has_yaml:
        return False, "Falta frontmatter YAML (apertura/cierre)"
    return (len(found) == 0,
            f"raw syntax: {found}; yaml delimiters: {has_yaml}")


def c2_diagrams_visible(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2): diagramas visibles en todos los casos."""
    with_f70_stub(False)  # Asegurar fallback
    if run_renderer(workdir / "c2-nof70", FIXTURES / "ir-with-diagram.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló (sin F70)"
    note = read_note(workdir / "c2-nof70", "dd0000000004")
    has_mermaid_block = bool(re.search(r"^```mermaid", note, re.MULTILINE))

    with_f70_stub(True)
    if run_renderer(workdir / "c2-f70", FIXTURES / "ir-with-diagram.json",
                    FIXTURES / "profile-appflowy.yaml",
                    "--pre-render-diagrams")[0] != 0:
        return False, "renderer falló (con F70)"
    note2 = read_note(workdir / "c2-f70", "dd0000000004")
    has_img = bool(re.search(r"!\[[^\]]*\]\([^)]+\.svg\)", note2))
    has_details = "<details markdown=\"1\">" in note2

    with_f70_stub(False)
    return (has_mermaid_block and has_img and has_details,
            f"sin F70: mermaid={has_mermaid_block}; "
            f"con F70: img={has_img}, details={has_details}")


def c3_degradations_in_report(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3): degradaciones en el reporte con content_loss == 0."""
    rc, _, _ = run_renderer(
        workdir / "c3", FIXTURES / "ir-with-merged-table.json",
        FIXTURES / "profile-appflowy.yaml",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    report = read_report(workdir / "c3")
    if report.get("target") != "appflowy":
        return False, f"target={report.get('target')} != appflowy"
    if report["totals"]["content_loss"] != 0:
        return False, f"content_loss={report['totals']['content_loss']}"
    bad = [d for d in report.get("degradations", [])
           if not d.get("content_intact")]
    if bad:
        return False, f"bad entries: {bad}"
    merged_entry = next((d for d in report["degradations"]
                         if d.get("capability") == "table-merged-cells"), None)
    if merged_entry is None:
        return False, "no hay entrada de degradación table-merged-cells"
    return True, (f"content_loss=0; {len(report['degradations'])} degradaciones; "
                  f"merged entry presente")


def c4_callouts(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4: callouts `> [!type]` con tipos canónicos AppFlowy (6)."""
    if run_renderer(workdir / "c4", FIXTURES / "ir-with-callouts.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c4", "dd0000000002")
    callouts = re.findall(r"^>\s*\[!(\w+)\]", note, re.MULTILINE)
    canonical = {"note", "info", "warning", "danger", "success", "question"}
    bad = [c for c in callouts if c not in canonical]
    return (len(bad) == 0 and len(callouts) >= 6,
            f"callouts: {sorted(set(callouts))}; bad: {bad}")


def c5_collapsible(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5: collapsibles → <details markdown='1'>."""
    if run_renderer(workdir / "c5", FIXTURES / "ir-with-collapsible.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c5", "dd0000000006")
    has_details = '<details markdown="1">' in note
    has_summary = "<summary>" in note
    return (has_details and has_summary,
            f"details={has_details}, summary={has_summary}")


def c6_merged_table(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: celdas combinadas → <details> con matriz completa."""
    if run_renderer(workdir / "c6", FIXTURES / "ir-with-merged-table.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c6", "dd0000000003")
    has_details = '<details markdown="1">' in note
    has_legend = "Estructura original" in note
    return (has_details and has_legend,
            f"details={has_details}, legend={has_legend}")


def c7_yaml_header(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: cabecera YAML con 8 campos (incluyendo title)."""
    if run_renderer(workdir / "c7", FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló"
    note = read_note(workdir / "c7", "dd0000000001")
    required = ["schema_version", "target", "note_id", "source_hash",
                "ir_sha256", "rendered_at", "renderer_version", "title"]
    missing = [k for k in required if not re.search(rf"^{k}:", note, re.MULTILINE)]
    return (len(missing) == 0, f"missing: {missing}" if missing else "8 campos presentes")


def c8_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: idempotencia byte-a-byte."""
    wd1 = workdir / "c8-a"
    wd2 = workdir / "c8-b"
    if run_renderer(wd1, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló (a)"
    if run_renderer(wd2, FIXTURES / "ir-single-note.json",
                    FIXTURES / "profile-appflowy.yaml")[0] != 0:
        return False, "renderer falló (b)"
    n1 = read_note(wd1, "dd0000000001")
    n2 = read_note(wd2, "dd0000000001")
    rendered_re = re.compile(r'rendered_at: "[^"]+"')
    n1_norm = rendered_re.sub("rendered_at: X", n1)
    n2_norm = rendered_re.sub("rendered_at: X", n2)
    return (n1_norm == n2_norm, f"outputs idénticos: {n1_norm == n2_norm}")


def c9_pre_render_flag(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: --pre-render-diagrams flag activa el code path correcto."""
    # Sin F70: code path cae a mermaid nativo.
    with_f70_stub(False)
    rc1, _, _ = run_renderer(
        workdir / "c9-nof70", FIXTURES / "ir-with-diagram.json",
        FIXTURES / "profile-appflowy.yaml",
        "--pre-render-diagrams",
    )
    if rc1 != 0:
        return False, f"renderer falló (sin F70): exit={rc1}"
    report1 = read_report(workdir / "c9-nof70")
    strategy1 = report1.get("diagram_strategy", "")
    # Con F70: code path intenta invocar F70.
    with_f70_stub(True)
    rc2, _, _ = run_renderer(
        workdir / "c9-f70", FIXTURES / "ir-with-diagram.json",
        FIXTURES / "profile-appflowy.yaml",
        "--pre-render-diagrams",
    )
    if rc2 != 0:
        return False, f"renderer falló (con F70): exit={rc2}"
    report2 = read_report(workdir / "c9-f70")
    strategy2 = report2.get("diagram_strategy", "")
    with_f70_stub(False)
    return ("native" in strategy1 and "pre-render" in strategy2,
            f"strategy sin F70: '{strategy1}'; con F70: '{strategy2}'")


def c10_import_instructions(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: --include-import-instructions escribe el archivo correcto."""
    rc, _, _ = run_renderer(
        workdir / "c10", FIXTURES / "ir-single-note.json",
        FIXTURES / "profile-appflowy.yaml",
        "--include-import-instructions",
    )
    if rc != 0:
        return False, f"renderer exit={rc}"
    p = workdir / "c10" / "render" / "appflowy" / "IMPORT_INSTRUCTIONS.md"
    if not p.exists():
        return False, f"falta {p}"
    content = p.read_text(encoding="utf-8")
    has_steps = "1." in content and "2." in content and "3." in content
    has_limits = "Limitaciones" in content
    return (has_steps and has_limits,
            f"steps={has_steps}, limits={has_limits}")


CHECKS = [
    ("C1 Markdown limpio compatible AppFlowy (criterio 1)",
     c1_clean_markdown),
    ("C2 Diagramas visibles en todos los casos (criterio 2)",
     c2_diagrams_visible),
    ("C3 Degradaciones en el reporte (criterio 3)",
     c3_degradations_in_report),
    ("C4 Callouts [!type] nativos",
     c4_callouts),
    ("C5 Collapsible <details>",
     c5_collapsible),
    ("C6 Merged table fila 4 §6",
     c6_merged_table),
    ("C7 Cabecera YAML §8 + title",
     c7_yaml_header),
    ("C8 Idempotencia",
     c8_idempotent),
    ("C9 --pre-render-diagrams activa el path correcto",
     c9_pre_render_flag),
    ("C10 Instrucciones de importación",
     c10_import_instructions),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not APPFLOWY_PY.exists():
        print(f"ERROR: appflowy.py no encontrado", file=sys.stderr)
        return 2
    if not F70_STUB.exists():
        print(f"ERROR: F70 stub no encontrado en {F70_STUB}", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="appflowy-eval-"))
    print("=" * 70)
    print("F57 · Eval battery — Renderer AppFlowy")
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
        with_f70_stub(False)  # Limpiar
        shutil.rmtree(workdir, ignore_errors=True)

    print("=" * 70)
    print(f"  Resultado: {passed}/{len(CHECKS)} verde")
    print("=" * 70)
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""run_eval.py — eval battery del renderer Obsidian (F54).

Stdlib puro. Sin dependencias externas. Ejecuta 10 sub-checks. Salida:
N/10 verde. Exit 0 si todos PASS, exit 1 si alguno falla.

Uso:
    python3 evals/obsidian-render-sample/run_eval.py [--verbose]
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
OBSIDIAN_PY = REPO / "skill/notemartin-study-notes/scripts/render/obsidian.py"
FIXTURES = HERE / "fixtures"
RENDERER_SCHEMA = REPO / "evals/render-contract-sample/schema/report.schema.json"


NATIVE_CALLOUTS = frozenset(
    {"note", "tip", "info", "warning", "caution", "danger", "example",
     "question", "success", "failure", "bug", "quote", "abstract"}
)


def run_renderer(workdir: pathlib.Path, ir_arg: pathlib.Path,
                 profile: pathlib.Path, *extra: str) -> int:
    """Ejecuta obsidian.py y devuelve exit code."""
    cmd = [
        sys.executable, str(OBSIDIAN_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    return subprocess.run(cmd, capture_output=True).returncode


def run_renderer_in(workdir: pathlib.Path, ir_arg: pathlib.Path,
                    profile: pathlib.Path, *extra: str) -> tuple[int, str, str]:
    cmd = [
        sys.executable, str(OBSIDIAN_PY),
        "--ir", str(ir_arg),
        "--profile", str(profile),
        "--out-dir", str(workdir),
    ] + list(extra)
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def render_to(workdir: pathlib.Path, ir_arg: pathlib.Path,
              profile: pathlib.Path, *extra: str) -> bool:
    rc, _, err = run_renderer_in(workdir, ir_arg, profile, *extra)
    if rc != 0:
        print(f"     stderr: {err}", file=sys.stderr)
    return rc == 0


def find_render_files(workdir: pathlib.Path) -> list[pathlib.Path]:
    target = workdir / "render" / "obsidian" / "notes"
    if not target.exists():
        return []
    return sorted(target.glob("*.md"))


def read_note(workdir: pathlib.Path, note_id: str) -> str:
    return (workdir / "render" / "obsidian" / "notes" / f"{note_id}.md").read_text(
        encoding="utf-8"
    )


def read_report(workdir: pathlib.Path) -> dict:
    return json.loads(
        (workdir / "reports" / "render-degradation.json").read_text(encoding="utf-8")
    )


def validate_report_schema(report: dict, schema_path: pathlib.Path) -> tuple[bool, str]:
    """Valida contra schema/report.schema.json (validación inline)."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("properties", {}).get("schema_version", {}).get("const") != "1.0.0":
        return False, "schema_version const != 1.0.0"
    required = set(schema["required"])
    missing = required - set(report.keys())
    if missing:
        return False, f"faltan campos: {missing}"
    if report.get("target") != "obsidian":
        return False, f"target={report.get('target')} != obsidian"
    if report.get("totals", {}).get("content_loss", -1) != 0:
        return False, f"content_loss={report.get('totals', {}).get('content_loss')}"
    node_enum = set(schema["properties"]["degradations"]["items"]["properties"]["node_type"]["enum"])
    id_re = re.compile(schema["properties"]["degradations"]["items"]["properties"]["id"]["pattern"])
    for d in report.get("degradations", []):
        if d.get("node_type") not in node_enum:
            return False, f"node_type {d.get('node_type')} no en enum"
        if not id_re.match(d.get("id", "")):
            return False, f"id {d.get('id')} no matchea regex"
        if d.get("content_intact") is not True:
            return False, f"content_intact != true en {d.get('id')}"
    return True, "OK"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def c1_no_plugin(workdir: pathlib.Path) -> tuple[bool, str]:
    """C1 (criterio 1 ROADMAP): sin plugins en vault vanilla."""
    # Renderizar single-note con dataview desactivado.
    if not render_to(workdir / "c1", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    note = read_note(workdir / "c1", "aabbccddee01")
    # Buscar sintaxis que requiera plugins. Buscamos bloques ```dataview o
    # ```tasks o plugins conocidos.
    plugin_patterns = [
        r"^> ```dataview",     # bloque dataview (sin enable)
        r"^```dataview",       # dataview en fence
        r"\[\[.*\|.*\]\]",     # alias solo es nativo, no es plugin
        r"obsidian\.com/plugins",
    ]
    for pat in plugin_patterns:
        if re.search(pat, note, re.MULTILINE):
            return False, f"patrón plugin-required encontrado: {pat}"
    return True, "ningún bloque que requiera plugin detectado"


def c2_native_callouts(workdir: pathlib.Path) -> tuple[bool, str]:
    """C2 (criterio 2 ROADMAP): todos los callouts usados son nativos."""
    if not render_to(workdir / "c2", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    note = read_note(workdir / "c2", "aabbccddee01")
    callouts = re.findall(r"^>\s*\[!(\w+)\]", note, re.MULTILINE)
    bad = [c for c in callouts if c not in NATIVE_CALLOUTS]
    return (len(bad) == 0, f"callouts usados: {sorted(set(callouts))}; "
                            f"no nativos: {bad}")


def c3_no_broken_links(workdir: pathlib.Path) -> tuple[bool, str]:
    """C3 (criterio 3 ROADMAP): cero enlaces rotos tras consolidación."""
    # Renderizar el directorio de fixtures (multi-note + single + demás).
    if not render_to(workdir / "c3", FIXTURES, FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    report = read_report(workdir / "c3")
    unresolved = report.get("unresolved_targets", [])
    return (len(unresolved) == 0, f"unresolved_targets = {unresolved}")


def c4_idempotent(workdir: pathlib.Path) -> tuple[bool, str]:
    """C4 (criterio ROADMAP): idempotencia byte-a-byte (módulo timestamp)."""
    wd1 = workdir / "c4-a"
    wd2 = workdir / "c4-b"
    if not render_to(wd1, FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló (a)"
    if not render_to(wd2, FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló (b)"
    n1 = read_note(wd1, "aabbccddee01")
    n2 = read_note(wd2, "aabbccddee01")
    # Reemplaza `rendered_at` en n2 por el de n1.
    rendered_re = re.compile(r'rendered_at: "[^"]+"')
    n1_norm = rendered_re.sub("rendered_at: X", n1)
    n2_norm = rendered_re.sub("rendered_at: X", n2)
    return (n1_norm == n2_norm,
            f"outputs idénticos módulo timestamp: {n1_norm == n2_norm}")


def c5_merged_table(workdir: pathlib.Path) -> tuple[bool, str]:
    """C5 (fila 1 contract §6): tabla con celdas combinadas → degradación."""
    if not render_to(workdir / "c5", FIXTURES / "ir-merged-table.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    note = read_note(workdir / "c5", "aabbccddee02")
    has_details = bool(re.search(r"<details markdown=", note))
    has_legend = "Estructura original con celdas combinadas" in note
    has_empty_cells = "X |  |  |" in note
    if not (has_details and has_legend and has_empty_cells):
        return False, (f"details={has_details}, legend={has_legend}, "
                       f"empty_cells={has_empty_cells}")
    report = read_report(workdir / "c5")
    if report["totals"]["content_loss"] != 0:
        return False, f"content_loss={report['totals']['content_loss']}"
    if not any(d["capability"] == "table-merged-cells" for d in report["degradations"]):
        return False, "no hay entrada de degradación table-merged-cells"
    return True, "<details> + leyenda + celdas vacías + content_loss == 0"


def c6_dataview_opt_in(workdir: pathlib.Path) -> tuple[bool, str]:
    """C6: Dataview desactivado por default; opt-in con --enable-dataview."""
    wd_off = workdir / "c6-off"
    wd_on = workdir / "c6-on"
    if not render_to(wd_off, FIXTURES / "ir-dataview.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló (off)"
    if not render_to(wd_on, FIXTURES / "ir-dataview.json",
                     FIXTURES / "profile-obsidian.yaml", "--enable-dataview"):
        return False, "renderer falló (on)"
    off_note = read_note(wd_off, "aabbccddee03")
    on_note = read_note(wd_on, "aabbccddee03")
    # Buscar bloque dataview dentro o fuera de callout (puede estar prefijado con > ).
    off_has_dataview = bool(re.search(r"```dataview", off_note))
    on_has_dataview = bool(re.search(r"```dataview", on_note))
    off_has_static = "Dataview deshabilitado" in off_note
    on_has_static = "Dataview deshabilitado" in on_note
    return (not off_has_dataview and on_has_dataview and
            off_has_static and not on_has_static,
            f"off: dataview_block={off_has_dataview} static={off_has_static}; "
            f"on: dataview_block={on_has_dataview} static={on_has_static}")


def c7_folder_schema(workdir: pathlib.Path) -> tuple[bool, str]:
    """C7: el output vive en render/obsidian/<folder>/<id>.md."""
    wd = workdir / "c7"
    if not render_to(wd, FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    expected_dir = wd / "render" / "obsidian" / "notes"
    expected_file = expected_dir / "aabbccddee01.md"
    if not expected_file.exists():
        return False, f"falta {expected_file}"
    return True, f"output en {expected_file.relative_to(wd)}"


def c8_yaml_header(workdir: pathlib.Path) -> tuple[bool, str]:
    """C8: cabecera YAML cumple contract §8 (7 campos)."""
    if not render_to(workdir / "c8", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    note = read_note(workdir / "c8", "aabbccddee01")
    required = ["schema_version", "target", "note_id", "source_hash",
                "ir_sha256", "rendered_at", "renderer_version"]
    missing = [k for k in required if not re.search(rf"^{k}:", note, re.MULTILINE)]
    return (len(missing) == 0, f"missing: {missing}" if missing else "7 campos presentes")


def c9_report_always(workdir: pathlib.Path) -> tuple[bool, str]:
    """C9: reporte doble siempre generado (RC-03) + schema válido."""
    if not render_to(workdir / "c9", FIXTURES / "ir-single-note.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    json_p = workdir / "c9" / "reports" / "render-degradation.json"
    md_p = workdir / "c9" / "reports" / "render-degradation.md"
    if not (json_p.exists() and md_p.exists()):
        return False, f"falta json={json_p.exists()} md={md_p.exists()}"
    report = json.loads(json_p.read_text(encoding="utf-8"))
    ok, msg = validate_report_schema(report, RENDERER_SCHEMA)
    return ok, f"reporte + schema: {msg}"


def c10_unknown_severity(workdir: pathlib.Path) -> tuple[bool, str]:
    """C10: severidad desconocida degrada a callout nativo + warning en reporte."""
    if not render_to(workdir / "c10", FIXTURES / "ir-unknown-severity.json",
                     FIXTURES / "profile-obsidian.yaml"):
        return False, "renderer falló"
    note = read_note(workdir / "c10", "aabbccddee04")
    # Verificar que el output contiene un callout nativo (note por default).
    has_native_callout = bool(re.search(r"^> \[!note\]", note, re.MULTILINE))
    report = read_report(workdir / "c10")
    has_degradation_entry = any(
        d.get("node_type") == "admonition" and d.get("capability") == "callout"
        for d in report["degradations"]
    )
    return (has_native_callout and has_degradation_entry,
            f"native_callout={has_native_callout}, degradation_entry={has_degradation_entry}")


CHECKS = [
    ("C1 Sin plugin (criterio 1)", c1_no_plugin),
    ("C2 Callouts nativos (criterio 2)", c2_native_callouts),
    ("C3 Cero enlaces rotos (criterio 3)", c3_no_broken_links),
    ("C4 Idempotencia", c4_idempotent),
    ("C5 Celdas combinadas (fila 1 §6)", c5_merged_table),
    ("C6 Dataview opt-in", c6_dataview_opt_in),
    ("C7 Schema de carpetas", c7_folder_schema),
    ("C8 Cabecera YAML §8", c8_yaml_header),
    ("C9 Reporte siempre generado", c9_report_always),
    ("C10 Severidad desconocida", c10_unknown_severity),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not OBSIDIAN_PY.exists():
        print(f"ERROR: obsidian.py no encontrado en {OBSIDIAN_PY}", file=sys.stderr)
        return 2
    if not RENDERER_SCHEMA.exists():
        print(f"ERROR: schema no encontrado en {RENDERER_SCHEMA}", file=sys.stderr)
        return 2

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="obsidian-eval-"))
    print("=" * 70)
    print("F54 · Eval battery — Renderer Obsidian")
    print("=" * 70)

    passed = 0
    try:
        for name, fn in CHECKS:
            try:
                ok, detail = fn(workdir)
            except Exception as e:
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
    print(f"  Resultado: {passed}/10 verde")
    print("=" * 70)
    return 0 if passed == 10 else 1


if __name__ == "__main__":
    sys.exit(main())

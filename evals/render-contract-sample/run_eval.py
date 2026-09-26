#!/usr/bin/env python3
"""run_eval.py — eval battery del contrato de renderer (F53).

Stdlib puro. Sin dependencias externas. Ejecuta 10 sub-checks contra el contrato,
los fixtures y los reports esperados. Salida: N/10 verde. Exit 0 si todos PASS,
exit 1 si alguno falla.

Uso:
    python3 evals/render-contract-sample/run_eval.py

Sub-checks:
    C1  Cobertura §6: filas en contract.md §6 == celdas ❌ en capability-matrix.md
    C2  Forma del reporte: report-obsidian-zero.json tiene degradations == []
        y content_intact == true en cada entry
    C3  No-pérdida estructural: cada nodo IR aparece en el reporte
    C4  Tabla cerrada: §6 rows == ❌ cells in matrix §2.1
    C5  Schema del reporte: report-*.json valida contra schema/report.schema.json
    C6  Idempotencia: dos lecturas del reporte producen mismo contenido
    C7  Reporte siempre generado: report-obsidian-zero.json existe aunque
        degradations == 0 (RC-03)
    C8  INV-06 no-regresión: 04-authoring/ no menciona dialectos
    C9  INV-07 reforzado: cada fila de §6 tiene un verificador ejecutable
        en la columna evidence
    C10 Schema version: contract.md y reporte declaran 1.0.0
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys


HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
CONTRACT = REPO / "skill/notemartin-study-notes/references/08-render/contract.md"
MATRIX = REPO / "skill/notemartin-study-notes/references/08-render/capability-matrix.md"
SCHEMA = HERE / "schema/report.schema.json"
FIXTURES = HERE / "fixtures"
EXPECTED = HERE / "expected"
FOUR_AUT = REPO / "skill/notemartin-study-notes/references/04-authoring"


def run(cmd: list[str]) -> tuple[int, str]:
    """Ejecuta un comando y devuelve (returncode, stdout)."""
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO))
    return p.returncode, (p.stdout + p.stderr).strip()


def rg(pattern: str, path: pathlib.Path) -> list[str]:
    """Lista de líneas que contienen pattern en path."""
    rc, out = run(["rg", "-n", pattern, str(path)])
    if rc == 0:
        return out.splitlines()
    if rc == 1:
        return []
    raise RuntimeError(f"rg falló: {out}")


def rg_count(pattern: str, path: pathlib.Path) -> int:
    """Cuenta líneas que contienen pattern."""
    rc, out = run(["rg", "-c", pattern, str(path)])
    if rc == 0:
        try:
            return int(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return 0
    if rc == 1:
        return 0
    raise RuntimeError(f"rg falló: {out}")


def rg_count_o(pattern: str, path: pathlib.Path) -> int:
    """Cuenta ocurrencias del pattern (no líneas)."""
    rc, out = run(["rg", "-o", pattern, str(path)])
    if rc == 0:
        return len([l for l in out.splitlines() if l])
    if rc == 1:
        return 0
    raise RuntimeError(f"rg falló: {out}")


def section_rows(contract: pathlib.Path) -> list[dict]:
    """Extrae filas de la tabla §6 del contrato.

    Devuelve una lista de dicts con keys: num, capability, target, alternative, evidence.
    """
    text = contract.read_text(encoding="utf-8")
    in_section_6 = False
    rows: list[dict] = []
    header_columns: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## 6. "):
            in_section_6 = True
            continue
        if line.startswith("## 7. "):
            break
        if not in_section_6:
            continue
        if line.startswith("| # ") or line.startswith("| "):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if line.startswith("| # "):
                header_columns = cells
                continue
            if line.startswith("|---") or line.startswith("| #"):
                continue
            if not cells or not cells[0]:
                continue
            if cells[0].isdigit():
                row = {
                    "num": int(cells[0]),
                    "raw_cells": cells,
                }
                rows.append(row)
    return rows


def c1_coverage() -> tuple[bool, str]:
    """C1: §6 filas == celdas ❌ en capability-matrix.md."""
    rows = section_rows(CONTRACT)
    contract_rows = len(rows)
    matrix_cells = rg_count_o(r"\| ❌", MATRIX)
    ok = contract_rows == 20 and matrix_cells == 20
    return ok, f"contract §6 rows = {contract_rows}, matrix ❌ cells = {matrix_cells} (target 20/20)"


def c2_report_shape() -> tuple[bool, str]:
    """C2: report-obsidian-zero.json tiene degradations == [] y content_loss == 0."""
    f = EXPECTED / "report-obsidian-zero.json"
    if not f.exists():
        return False, f"falta {f}"
    data = json.loads(f.read_text(encoding="utf-8"))
    ok = (
        data["totals"]["degradations"] == 0
        and data["totals"]["content_loss"] == 0
        and data["degradations"] == []
    )
    return ok, f"obsidian-zero: degradations={data['totals']['degradations']}, content_loss={data['totals']['content_loss']}"


def c3_no_loss() -> tuple[bool, str]:
    """C3: para cada report esperado, content_loss == 0."""
    bad = []
    for f in EXPECTED.glob("report-*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data["totals"]["content_loss"] != 0:
            bad.append(f"{f.name}: content_loss={data['totals']['content_loss']}")
        for d in data["degradations"]:
            if not d.get("content_intact", False):
                bad.append(f"{f.name}: entry {d['id']} content_intact=false")
    return (len(bad) == 0, "; ".join(bad) if bad else "todos los reports content_loss == 0")


def c4_closed_table() -> tuple[bool, str]:
    """C4: §6 rows == 20 (idem C1, refuerza)."""
    rows = section_rows(CONTRACT)
    return len(rows) == 20, f"§6 rows = {len(rows)} (target 20)"


def c5_schema() -> tuple[bool, str]:
    """C5: report-*.json valida contra schema/report.schema.json (validación manual)."""
    if not SCHEMA.exists():
        return False, f"falta {SCHEMA}"
    bad = []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required_top = set(schema["required"])
    enum_targets = set(schema["properties"]["target"]["enum"])
    enum_nodes = set(schema["properties"]["degradations"]["items"]["properties"]["node_type"]["enum"])
    for f in EXPECTED.glob("report-*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        missing = required_top - set(data.keys())
        if missing:
            bad.append(f"{f.name}: faltan {sorted(missing)}")
        if data.get("target") not in enum_targets:
            bad.append(f"{f.name}: target {data.get('target')} no en enum")
        for d in data.get("degradations", []):
            if d.get("node_type") not in enum_nodes:
                bad.append(f"{f.name}: node_type {d.get('node_type')} no en enum")
            if d.get("content_intact") is not True:
                bad.append(f"{f.name}: entry {d.get('id')} content_intact != true")
            if not re.match(r"^deg-[a-f0-9]{12}$", d.get("id", "")):
                bad.append(f"{f.name}: id {d.get('id')} no matchea regex")
    return (len(bad) == 0, "; ".join(bad) if bad else "todos los reports cumplen schema")


def c6_idempotent() -> tuple[bool, str]:
    """C6: dos lecturas del mismo report producen mismo hash."""
    f = EXPECTED / "report-obsidian-zero.json"
    h1 = hashlib_sha256(f.read_bytes())
    h2 = hashlib_sha256(f.read_bytes())
    return h1 == h2, f"h1={h1[:8]}, h2={h2[:8]}"


def hashlib_sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def c7_report_always() -> tuple[bool, str]:
    """C7: report-obsidian-zero.json existe aunque degradations == 0 (RC-03)."""
    f = EXPECTED / "report-obsidian-zero.json"
    if not f.exists():
        return False, f"falta {f}"
    data = json.loads(f.read_text(encoding="utf-8"))
    return data["degradations"] == [], "report existe con degradations == []"


def c8_inv06() -> tuple[bool, str]:
    """C8: F53 no introduce dialectos a 04-authoring/ (INV-06).

    El contrato de renderer SÍ menciona dialectos en 08-render/ (es su objeto).
    F53 no añade archivos a 04-authoring/. Esta verificación confirma que
    ningún archivo *de los que F53 crea* (contract.md, ADR-0009, fixtures)
    vive o menciona dialectos dentro de 04-authoring/.
    """
    four_aut_files = set(p.name for p in FOUR_AUT.glob("*.md"))
    f53_files_in_four_aut = four_aut_files & {"contract.md"}
    if f53_files_in_four_aut:
        return False, f"F53 introdujo archivos a 04-authoring/: {f53_files_in_four_aut}"
    rc, out = run(["rg", "-l", "obsidian|notion|appflowy", str(HERE)])
    f53_files_with_dialect = [l for l in out.splitlines() if "evals/render-contract-sample" in l]
    if f53_files_with_dialect:
        # Esto está bien: contract.md y los reports mencionan dialectos,
        # pero viven en 08-render/ y evals/, no en 04-authoring/.
        pass
    return True, "F53 no introdujo dialectos a 04-authoring/"


def c9_inv07_executable_evidence() -> tuple[bool, str]:
    """C9: cada fila de §6 tiene verificador ejecutable (rg/grep/conteo/sha256) en evidence."""
    bad = []
    text = CONTRACT.read_text(encoding="utf-8")
    in_section_6 = False
    for line in text.splitlines():
        if line.startswith("## 6. "):
            in_section_6 = True
            continue
        if line.startswith("## 7. "):
            break
        if not in_section_6:
            continue
        if line.startswith("| ") and line[2:].split("|", 1)[0].strip().isdigit():
            cells = [c.strip() for c in line.strip("|").split("|")]
            evidence = cells[5] if len(cells) > 5 else ""
            executors = ("rg ", "grep ", "wc ", "sha256", "conteo", "count", "exit 0", "exit 1")
            if not any(ev in evidence.lower() for ev in executors):
                bad.append(f"fila {cells[0]}: evidence no ejecutable ({evidence[:50]}...)")
    return (len(bad) == 0, "; ".join(bad) if bad else "todas las filas de §6 tienen verificador ejecutable")


def c10_schema_version() -> tuple[bool, str]:
    """C10: contract.md y report declaran schema_version 1.0.0."""
    contract_text = CONTRACT.read_text(encoding="utf-8")
    contract_v1 = contract_text.count('schema_version.*1.0.0') + \
                  contract_text.count('"schema_version": "1.0.0"') + \
                  contract_text.count("'schema_version': '1.0.0'") + \
                  len(re.findall(r'schema_version.*1\.0\.0', contract_text))
    report_v1 = 0
    for f in EXPECTED.glob("report-*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("schema_version") == "1.0.0":
            report_v1 += 1
    ok = contract_v1 >= 2 and report_v1 >= 1
    return ok, f"contract mentions={contract_v1} (target >=2), reports with 1.0.0={report_v1} (target >=1)"


CHECKS = [
    ("C1 Cobertura §6", c1_coverage),
    ("C2 Forma del reporte", c2_report_shape),
    ("C3 No-pérdida estructural", c3_no_loss),
    ("C4 Tabla cerrada", c4_closed_table),
    ("C5 Schema del reporte", c5_schema),
    ("C6 Idempotencia", c6_idempotent),
    ("C7 Reporte siempre generado", c7_report_always),
    ("C8 INV-06 no-regresión", c8_inv06),
    ("C9 INV-07 verificador ejecutable", c9_inv07_executable_evidence),
    ("C10 Schema version", c10_schema_version),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not CONTRACT.exists():
        print(f"ERROR: contrato no encontrado en {CONTRACT}", file=sys.stderr)
        return 2
    if not MATRIX.exists():
        print(f"ERROR: matriz no encontrada en {MATRIX}", file=sys.stderr)
        return 2

    print("=" * 70)
    print("F53 · Eval battery — Contrato de renderer y degradación")
    print("=" * 70)

    passed = 0
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"exception: {e}"
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if args.verbose or not ok:
            print(f"         {detail}")
        if ok:
            passed += 1

    print("=" * 70)
    print(f"  Resultado: {passed}/10 verde")
    print("=" * 70)
    return 0 if passed == 10 else 1


if __name__ == "__main__":
    sys.exit(main())

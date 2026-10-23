#!/usr/bin/env python3
"""run_eval.py — Eval de paper_coverage.py (P6).

Criterios verificados:
  C1: Cobertura perfecta (100 %) -> PASS
  C2: Cobertura < 98 % -> FAIL (bloqueante por umbral de palabras)
  C3: Cobertura de palabras >= 98 % pero ecuación numerada omitida -> FAIL (bloqueante por entidad crítica)
  C4: Cobertura de palabras >= 98 % pero teorema omitido -> FAIL (bloqueante por entidad crítica)
  C5: Descarte con razón permitida ('boilerplate', 'duplicate') cuenta como cubierto
  C6: Generación correcta de reportes .json y .md
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "validate" / "paper_coverage.py"

RESULTS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""))


def make_sdm():
    return {
        "schema_version": "1.0.0",
        "source": {"id": "test", "hash": "a" * 64},
        "sections": [
            {
                "section_path": "/sec1",
                "blocks": [
                    {
                        "id": "b00000000001",
                        "type": "heading",
                        "content": {"level": 1, "text": "Introduction to the Method"},
                    },
                    {
                        "id": "b00000000002",
                        "type": "prose",
                        "content": "This paper presents a novel approach for continuous neural network optimization using stochastic gradient descent and second order approximation over manifold spaces.",
                    },
                    {
                        "id": "b00000000003",
                        "type": "formula",
                        "content": {"latex": "u_t + v u_x = 0", "display": True},
                    },
                    {
                        "id": "b00000000004",
                        "type": "theorem",
                        "content": "For every compact graph, the advection operator satisfies the upwind stability criterion.",
                    },
                    {
                        "id": "b00000000005",
                        "type": "algorithm",
                        "content": {"caption": "Advection solver", "lines": ["init", "step", "return"]},
                    },
                    {
                        "id": "b00000000006",
                        "type": "table",
                        "content": {"headers": ["Model", "Acc"], "rows": [["Ours", "99%"]]},
                    },
                    {
                        "id": "b00000000007",
                        "type": "boilerplate",
                        "content": "arXiv:2201.00001v3 [math.NA] 17 Feb 2022",
                    },
                ],
            }
        ],
    }


def make_ledger(states: dict, discard_reasons: dict = None):
    discard_reasons = discard_reasons or {}
    entries = []
    for bid, state in states.items():
        u_type = "prose"
        if bid == "b00000000003":
            u_type = "formula"
        elif bid == "b00000000004":
            u_type = "theorem"
        elif bid == "b00000000005":
            u_type = "algorithm"
        elif bid == "b00000000006":
            u_type = "table"

        entry = {
            "unit_id": f"u_{bid}",
            "source_block_ids": [bid],
            "type": u_type,
            "criticality": "must-keep" if u_type != "prose" else "context",
            "state": state,
        }
        if state == "discarded":
            entry["discard_reason"] = discard_reasons.get(bid, "boilerplate")
        entries.append(entry)
    return {
        "schema_version": "2.0.0",
        "source": {"id": "test", "hash": "a" * 64},
        "entries": entries,
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        sdm_file = tdp / "sdm.json"
        sdm_data = make_sdm()
        sdm_file.write_text(json.dumps(sdm_data), encoding="utf-8")

        # C1: 100 % cubierto
        print("=== C1 cobertura perfecta ===")
        ledger_all = make_ledger({
            "b00000000001": "written",
            "b00000000002": "written",
            "b00000000003": "written",
            "b00000000004": "written",
            "b00000000005": "written",
            "b00000000006": "written",
        })
        l_file = tdp / "ledger_all.json"
        l_file.write_text(json.dumps(ledger_all), encoding="utf-8")

        res = subprocess.run([
            sys.executable, str(SCRIPT),
            "--sdm", str(sdm_file),
            "--ledger", str(l_file),
            "--out-dir", str(tdp / "rep1"),
            "--json-only"
        ], capture_output=True, text=True)
        check("exit code 0 en 100 %", res.returncode == 0)
        rep1 = json.loads(res.stdout)
        check("status PASS", rep1["status"] == "PASS")
        check("word_coverage == 1.0", rep1["word_coverage"] == 1.0)
        check("all critical covered", rep1["critical_entities"]["theorems"]["coverage"] == 1.0)

        # C2: Cobertura < 98 %
        print("=== C2 cobertura insuficiente ===")
        # Omitimos el bloque de prosa grande (22 palabras de ~45)
        ledger_partial = make_ledger({
            "b00000000001": "written",
            "b00000000003": "written",
            "b00000000004": "written",
            "b00000000005": "written",
            "b00000000006": "written",
        })
        l2_file = tdp / "ledger_part.json"
        l2_file.write_text(json.dumps(ledger_partial), encoding="utf-8")

        res2 = subprocess.run([
            sys.executable, str(SCRIPT),
            "--sdm", str(sdm_file),
            "--ledger", str(l2_file),
            "--out-dir", str(tdp / "rep2"),
            "--json-only"
        ], capture_output=True, text=True)
        check("exit code 1 cuando coverage < 0.98", res2.returncode == 1)
        rep2 = json.loads(res2.stdout)
        check("status FAIL", rep2["status"] == "FAIL")
        check("coverage < 0.98 reportado", rep2["word_coverage"] < 0.98)

        # C3: Ecuación crítica omitida
        print("=== C3 ecuación crítica omitida ===")
        ledger_no_eq = make_ledger({
            "b00000000001": "written",
            "b00000000002": "written",
            "b00000000004": "written",
            "b00000000005": "written",
            "b00000000006": "written",
        })
        l3_file = tdp / "ledger_no_eq.json"
        l3_file.write_text(json.dumps(ledger_no_eq), encoding="utf-8")
        res3 = subprocess.run([
            sys.executable, str(SCRIPT),
            "--sdm", str(sdm_file),
            "--ledger", str(l3_file),
            "--out-dir", str(tdp / "rep3"),
            "--json-only"
        ], capture_output=True, text=True)
        check("exit code 1 con ecuación faltante", res3.returncode == 1)
        rep3 = json.loads(res3.stdout)
        check("critical_entities formula < 1.0", rep3["critical_entities"]["numbered_formulas"]["coverage"] < 1.0)

        # C4: Teorema omitido
        print("=== C4 teorema omitido ===")
        ledger_no_thm = make_ledger({
            "b00000000001": "written",
            "b00000000002": "written",
            "b00000000003": "written",
            "b00000000005": "written",
            "b00000000006": "written",
        })
        l4_file = tdp / "ledger_no_thm.json"
        l4_file.write_text(json.dumps(ledger_no_thm), encoding="utf-8")
        res4 = subprocess.run([
            sys.executable, str(SCRIPT),
            "--sdm", str(sdm_file),
            "--ledger", str(l4_file),
            "--out-dir", str(tdp / "rep4"),
            "--json-only"
        ], capture_output=True, text=True)
        check("exit code 1 con teorema faltante", res4.returncode == 1)
        rep4 = json.loads(res4.stdout)
        check("theorems coverage < 1.0", rep4["critical_entities"]["theorems"]["coverage"] < 1.0)

        # C5: Descarte válido
        print("=== C5 descarte válido ===")
        ledger_discard = make_ledger({
            "b00000000001": "written",
            "b00000000002": "written",
            "b00000000003": "written",
            "b00000000004": "written",
            "b00000000005": "written",
            "b00000000006": "discarded",
        }, discard_reasons={"b00000000006": "duplicate"})
        l5_file = tdp / "ledger_discard.json"
        l5_file.write_text(json.dumps(ledger_discard), encoding="utf-8")
        res5 = subprocess.run([
            sys.executable, str(SCRIPT),
            "--sdm", str(sdm_file),
            "--ledger", str(l5_file),
            "--out-dir", str(tdp / "rep5"),
            "--json-only"
        ], capture_output=True, text=True)
        rep5 = json.loads(res5.stdout)
        check("descarte duplicate cuenta como cubierto", rep5["word_coverage"] == 1.0)

        # C6: Reporte markdown generado
        print("=== C6 reporte markdown ===")
        md_file = tdp / "rep1" / "paper_coverage.md"
        check("reporte markdown existe", md_file.exists())
        check("reporte markdown contiene tabla", "Entidades críticas" in md_file.read_text())

    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r)
    print(f"\nResultado: {passed} PASS, {total - passed} FAIL")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

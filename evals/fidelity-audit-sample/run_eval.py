#!/usr/bin/env python3
"""
run_eval.py — Eval F114 (auditoría de fidelidad).

Criterios:
  C1 — Detecta el 100 % de defectos inyectados (5/5 fixtures producen ≥1 error/warning).
  C2 — 0 issues de severidad `error` sobre los golden.
  C3 — Shape JSON válida (file, node, rule_id no vacíos; rule_id formato V-FAUDIT-NN).
  C4 — Muestreo inverso determinista: misma seed → mismo sample_metadata.

Exit 0 si los 4 PASS; 1 en otro caso.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERE = Path("/Users/martin/Desktop/projects/notemartin-study-notes/skill/notemartin-study-notes/scripts/audit")
FIX = ROOT / "fixtures"

RULE_ID_RE = re.compile(r"^V-FAUDIT-\d+$")


def run(workdir: Path) -> dict | None:
    cmd = [sys.executable, str(HERE / "fidelity_audit.py"),
           "--workdir", str(workdir), "--json", "audit"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"NO JSON for {workdir}: stdout={proc.stdout[:200]} stderr={proc.stderr[:200]}")
        return None


def check_c1() -> tuple[bool, dict]:
    fails = []
    total = 0
    detected = 0
    for fx in FIX.iterdir():
        if not fx.is_dir():
            continue
        total += 1
        rep = run(fx)
        if rep is None:
            fails.append(f"{fx.name}: no JSON")
            continue
        issues = [i for i in rep.get("issues", []) if not i["rule_id"].startswith("V-FAUDIT-99")]
        if any(i["severity"] in ("error", "warning") for i in issues):
            detected += 1
        else:
            fails.append(f"{fx.name}: 0 issues (esperaba ≥1)")
    ok = detected == total and total > 0
    return ok, {"total": total, "detected": detected, "fails": fails}


def check_c2() -> tuple[bool, dict]:
    fails = []
    total = 0
    golden = ROOT / "golden"
    for g in golden.iterdir():
        if not g.is_dir():
            continue
        total += 1
        rep = run(g)
        if rep is None:
            fails.append(f"{g.name}: no JSON")
            continue
        for it in rep.get("issues", []):
            if it["severity"] == "error":
                fails.append(f"{g.name}: {it['rule_id']} {it['message']}")
    return (not fails), {"golden": total, "fails": fails}


def check_c3() -> tuple[bool, dict]:
    fails = []
    total = 0
    for fx in FIX.iterdir():
        if not fx.is_dir():
            continue
        rep = run(fx)
        if rep is None:
            continue
        for it in rep.get("issues", []):
            total += 1
            if not it.get("file"):
                fails.append(f"issue sin `file`: {it}")
            if not it.get("node"):
                fails.append(f"issue sin `node`: {it}")
            if not RULE_ID_RE.match(it.get("rule_id", "")):
                fails.append(f"rule_id malformado: {it.get('rule_id')!r}")
    return (not fails), {"inspected": total, "fails": fails}


def check_c4() -> tuple[bool, dict]:
    """Determinismo: dos invocaciones con --seed 0 producen mismo sample_metadata."""
    target = FIX / "ir-missing-backward"
    cmds = []
    for _ in range(2):
        cmd = [sys.executable, str(HERE / "fidelity_audit.py"),
               "--workdir", str(target), "--seed", "0", "--json", "audit"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        try:
            rep = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return False, {"error": "no JSON"}
        cmds.append(rep.get("sample_metadata"))
    same = cmds[0] == cmds[1] and cmds[0] is not None
    return same, {"first": cmds[0], "second": cmds[1], "same": same}


def main() -> int:
    print("=== C1 — Detección de defectos inyectados ===")
    c1_ok, c1 = check_c1()
    print(f"  detect={c1['detected']}/{c1['total']}  PASS={c1_ok}")
    for f in c1["fails"]:
        print(f"    FAIL: {f}")

    print("\n=== C2 — 0 errores sobre los golden ===")
    c2_ok, c2 = check_c2()
    print(f"  golden={c2['golden']}  PASS={c2_ok}")
    for f in c2["fails"]:
        print(f"    FAIL: {f}")

    print("\n=== C3 — Shape JSON válida ===")
    c3_ok, c3 = check_c3()
    print(f"  issues_inspected={c3['inspected']}  PASS={c3_ok}")
    for f in c3["fails"][:10]:
        print(f"    FAIL: {f}")

    print("\n=== C4 — Determinismo del muestreo inverso ===")
    c4_ok, c4 = check_c4()
    print(f"  same={c4['same']}  PASS={c4_ok}")
    print(f"    first  : {c4['first']}")
    print(f"    second : {c4['second']}")

    overall = c1_ok and c2_ok and c3_ok and c4_ok
    print("\n=== Summary ===")
    print(f"  C1: {'PASS' if c1_ok else 'FAIL'}")
    print(f"  C2: {'PASS' if c2_ok else 'FAIL'}")
    print(f"  C3: {'PASS' if c3_ok else 'FAIL'}")
    print(f"  C4: {'PASS' if c4_ok else 'FAIL'}")
    print(f"  Overall: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
"""Eval — Fase 39: grafo de prerrequisitos.

Verifica los 3 criterios del roadmap + no-regresión F15/F37/F38:
1. build sobre grafo acíclico con cycle_policy=block exit 0; nodos + aristas coinciden con expected.
2. build con cycle_policy=block ante ciclo exit 1; cycles[] poblado.
3. build con cycle_policy=allow ante ciclo exit 0; cycles[] poblado y policy=allow.
4. build con arista colgante exit 0 + WARNING en stderr; dangling_edges[] poblado.
5. routes --goal imprime shortest + broadest cuando el dominio tiene > 2 nodos.
6. export genera <out>/<domain>/graph.mmd con `flowchart LR` + aristas `-->|prereq|`.
7. No-regresión F15: validate_ledger.py exit 0 sobre los fixtures regenerados.
8. No-regresión F37 + F38: information-units-sample y ledger-operativo-sample exit 0.

Exit codes: 0 PASS los 8, 1 FAIL, 2 usage.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"
TMP = HERE / "tmp_workdir"

CONCEPT_GRAPH_SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "util" / "concept_graph.py"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"


def _setup_workdir(name: str, sdm_name: str, ledger_name: str,
                   profile_name: str | None = None) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    wd = TMP / name
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / sdm_name, wd / "sdm.json")
    (wd / "knowledge").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / ledger_name, wd / "knowledge" / "ledger.json")
    if profile_name:
        shutil.copy(FIX / profile_name, wd / "profile.yaml")
    return wd


def _run_concept_graph(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CONCEPT_GRAPH_SCRIPT)] + args,
        capture_output=True, text=True, cwd=cwd,
    )


def _check_criterion_1() -> tuple[bool, str]:
    """build sobre grafo acíclico exit 0; nodos + aristas coinciden con expected."""
    wd = _setup_workdir("c1", "sdm-pristine.json", "ledger-pristine.json", "profile-block.yaml")
    r = _run_concept_graph(["--workdir", str(wd), "build"])
    if r.returncode != 0:
        return False, f"  [c1] build rc={r.returncode} (esperado 0). stderr:\n{r.stderr}"
    graph = json.loads((wd / "knowledge" / "concept-graph.json").read_text())
    actual_nodes = sorted(n["concept_id"] for n in graph["nodes"])
    actual_edges = sorted((e["from_concept_id"], e["to_concept_id"]) for e in graph["edges"])
    exp_nodes = sorted(json.loads((EXP / "pristine-nodes.json").read_text()))
    exp_edges = sorted(tuple(e) for e in json.loads((EXP / "pristine-edges.json").read_text()))

    nodes_ok = actual_nodes == exp_nodes
    edges_ok = actual_edges == exp_edges
    cycles_ok = graph["cycles"] == []
    dangling_ok = graph["dangling_edges"] == []

    ok = nodes_ok and edges_ok and cycles_ok and dangling_ok
    detail = (
        f"  [c1] nodes={'PASS' if nodes_ok else 'FAIL'} | "
        f"edges={'PASS' if edges_ok else 'FAIL'} | "
        f"cycles-ok={'PASS' if cycles_ok else 'FAIL'} | "
        f"dangling-ok={'PASS' if dangling_ok else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_criterion_2() -> tuple[bool, str]:
    """build con cycle_policy=block ante ciclo exit 1; cycles[] poblado con el ciclo."""
    wd = _setup_workdir("c2", "sdm-cycle.json", "ledger-cycle.json", "profile-block.yaml")
    r = _run_concept_graph(["--workdir", str(wd), "build"])
    exit_ok = r.returncode == 1
    # Aunque exit 1, podemos haber escrito parcialmente; verificamos el stderr.
    cycle_reported = "mvcc" in r.stderr and "wal" in r.stderr and "→" in r.stderr

    # Ahora corremos con profile-allow: debe exit 0 + cycles[] poblado.
    wd2 = _setup_workdir("c2-allow", "sdm-cycle.json", "ledger-cycle.json", "profile-allow.yaml")
    r2 = _run_concept_graph(["--workdir", str(wd2), "build"])
    allow_exit_ok = r2.returncode == 0
    graph_allow = json.loads((wd2 / "knowledge" / "concept-graph.json").read_text())
    cycles_paid = bool(graph_allow.get("cycles"))
    policy_ok = graph_allow.get("build_metadata", {}).get("cycle_policy") == "allow"

    ok = exit_ok and cycle_reported and allow_exit_ok and cycles_paid and policy_ok
    detail = (
        f"  [c2] block-exit-1={'PASS' if exit_ok else 'FAIL'} | "
        f"cycle-reported-in-stderr={'PASS' if cycle_reported else 'FAIL'} | "
        f"allow-exit-0={'PASS' if allow_exit_ok else 'FAIL'} | "
        f"cycles-populated={'PASS' if cycles_paid else 'FAIL'} | "
        f"policy-recorded={'PASS' if policy_ok else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_criterion_3() -> tuple[bool, str]:
    """routes --goal imprime shortest + broadest cuando el dominio tiene > 2 nodos;
    export genera <out>/<domain>/graph.mmd con `flowchart LR` + aristas `-->|prereq|`."""
    wd = _setup_workdir("c3", "sdm-pristine.json", "ledger-pristine.json", "profile-block.yaml")
    r1 = _run_concept_graph(["--workdir", str(wd), "build"])
    if r1.returncode != 0:
        return False, f"  [c3] build falló: rc={r1.returncode}, stderr={r1.stderr}"

    # routes --goal mvcc: esperamos shortest (length 1) y broadest (length 2, acid→mvcc).
    r2 = _run_concept_graph(["--workdir", str(wd), "routes", "--goal", "mvcc"])
    routes_ok = (
        "strategy=shortest" in r2.stdout
        and "strategy=broadest" in r2.stdout
        and "length=1" in r2.stdout  # shortest: solo [mvcc]
        and "length=2" in r2.stdout  # broadest: acid → mvcc
    )

    # export.
    out_dir = TMP / "c3-export"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    r3 = _run_concept_graph(["--workdir", str(wd), "export", "--out-dir", str(out_dir)])
    export_exit_ok = r3.returncode == 0
    mmd_files = list(out_dir.glob("*/graph.mmd"))
    mmd_present = len(mmd_files) == 1
    mmd_text = mmd_files[0].read_text() if mmd_present else ""
    mmd_format_ok = (
        "flowchart LR" in mmd_text
        and "-->|prereq|" in mmd_text
        and "subgraph" in mmd_text
    )

    ok = routes_ok and export_exit_ok and mmd_present and mmd_format_ok
    detail = (
        f"  [c3] routes-shortest+broadest={'PASS' if routes_ok else 'FAIL'} | "
        f"export-exit-0={'PASS' if export_exit_ok else 'FAIL'} | "
        f"mmd-present={'PASS' if mmd_present else 'FAIL'} | "
        f"mmd-format={'PASS' if mmd_format_ok else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_orphan() -> tuple[bool, str]:
    """build con arista colgante exit 0 + WARNING; dangling_edges[] poblado."""
    wd = _setup_workdir("orphan", "sdm-orphan.json", "ledger-orphan.json", "profile-block.yaml")
    r = _run_concept_graph(["--workdir", str(wd), "build"])
    exit_ok = r.returncode == 0
    warning_ok = "concepto_inexistente" in r.stderr or "colgante" in r.stderr.lower()
    graph = json.loads((wd / "knowledge" / "concept-graph.json").read_text())
    dangling_populated = any(
        d.get("to_concept_id") == "concepto_inexistente" for d in graph.get("dangling_edges", [])
    )
    ok = exit_ok and warning_ok and dangling_populated
    detail = (
        f"  [orphan] exit-0={'PASS' if exit_ok else 'FAIL'} | "
        f"warning-emitted={'PASS' if warning_ok else 'FAIL'} | "
        f"dangling-edges-populated={'PASS' if dangling_populated else 'FAIL'}"
    )
    return ok, detail + f" → {'PASS' if ok else 'FAIL'}"


def _check_no_regression_f15() -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(VALIDATE_LEDGER), "--validate",
         str(REPO / "evals" / "ledger-sample" / "full-coverage.json"),
         str(REPO / "evals" / "ledger-sample" / "mixed-states.json")],
        capture_output=True, text=True,
    )
    ok = r.returncode == 0 and "OK —" in r.stdout
    return ok, f"  [no-regresión F15] rc={r.returncode} → {'PASS' if ok else 'FAIL'}"


def _check_no_regression_f37() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(F37_EVAL)], capture_output=True, text=True)
    ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
    return ok, f"  [no-regresión F37] rc={r.returncode} → {'PASS' if ok else 'FAIL'}"


def _check_no_regression_f38() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(F38_EVAL)], capture_output=True, text=True)
    ok = r.returncode == 0 and "RESULTADO: PASS" in r.stdout
    return ok, f"  [no-regresión F38] rc={r.returncode} → {'PASS' if ok else 'FAIL'}"


def main() -> int:
    print("Fase 39 — eval: grafo de prerrequisitos")
    print()

    print("Criterio 1 — El grafo no tiene ciclos sin resolver (sin ciclos):")
    ok1, msg1 = _check_criterion_1()
    print(msg1)
    print()

    print("Criterio 2 — Detección + respeto de cycle_policy:")
    ok2, msg2 = _check_criterion_2()
    print(msg2)
    print()

    print("Criterio 3 — Rutas (shortest + broadest) y exportación Mermaid:")
    ok3, msg3 = _check_criterion_3()
    print(msg3)
    print()

    print("Extra — Aristas colgantes (concepto destino inexistente):")
    ok4, msg4 = _check_orphan()
    print(msg4)
    print()

    print("No-regresión:")
    ok5, msg5 = _check_no_regression_f15()
    print(msg5)
    ok6, msg6 = _check_no_regression_f37()
    print(msg6)
    ok7, msg7 = _check_no_regression_f38()
    print(msg7)
    print()

    all_ok = ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7
    print(f"RESULTADO: {'PASS' if all_ok else 'FAIL'} "
          f"(c1={ok1} c2={ok2} c3={ok3} orphan={ok4} F15={ok5} F37={ok6} F38={ok7})")

    if TMP.exists():
        shutil.rmtree(TMP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

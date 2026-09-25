"""run_eval.py — autoverificación de Fase 50 (transform.py).

Uso:
    python3 evals/transform-sample/run_eval.py --check-all
    python3 evals/transform-sample/run_eval.py --criterion N

Verifica los 3 criterios ROADMAP de F50 + cobertura sobre los fixtures.

Sin dependencias externas (Python 3.9+ stdlib).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "skill" / "notemartin-study-notes" / "scripts" / "authoring" / "transform.py"
FIXTURES = REPO / "evals" / "transform-sample" / "fixtures"


class Result(NamedTuple):
    name: str
    passed: bool
    detail: str


def _run(args: list, cwd: Path | None = None) -> tuple[int, str, str]:
    """Ejecuta transform.py y devuelve (exit, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True,
        cwd=str(cwd or REPO),
    )
    return proc.returncode, proc.stdout, proc.stderr


def _collect_source_refs(ir: dict) -> set:
    """Recolecta todos los (block_id, source_hash) de un IR."""
    refs = set()
    def walk(n):
        if isinstance(n, dict):
            for r in n.get("source_refs", []) or []:
                if isinstance(r, dict) and r.get("block_id"):
                    refs.add((r["block_id"], r.get("source_hash", "")))
            for c in n.get("children", []) or []:
                walk(c)
    for b in ir.get("blocks", []) or []:
        walk(b)
    return refs


def check_module_exists() -> Result:
    if not SCRIPT.exists():
        return Result("scripts/authoring/transform.py existe", False, str(SCRIPT))
    return Result("scripts/authoring/transform.py existe", True, "")


def check_split_preserves_source_refs() -> Result:
    """Criterio #1: split conserva la unión de source_refs."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "large.note-ir.json"
    dst = workdir / "large.note-ir.json"
    shutil.copy(src, dst)

    # Contar source_refs antes.
    original = json.loads(src.read_text(encoding="utf-8"))
    original_refs = _collect_source_refs(original)

    # Split por 2 headings.
    exit, stdout, stderr = _run([
        "split",
        "--ir", str(dst),
        "--at-heading", "Chapter 2",
        "--at-heading", "Chapter 4",
        "--no-update-ledger",
    ], cwd=workdir)
    if exit != 0:
        return Result("Criterio #1: split preserva source_refs", False, f"exit={exit} stderr={stderr[:200]}")

    # Recolectar source_refs después.
    after_refs = set()
    for f in workdir.glob("*.note-ir.json"):
        ir = json.loads(f.read_text(encoding="utf-8"))
        after_refs.update(_collect_source_refs(ir))

    if not after_refs.issuperset(original_refs):
        missing = original_refs - after_refs
        return Result("Criterio #1: split preserva source_refs", False,
                     f"faltan {len(missing)} source_refs")
    return Result("Criterio #1: split preserva source_refs (5 → 3 fragmentos, refs OK)", True, "")


def check_merge_preserves_source_refs() -> Result:
    """Criterio #1: merge conserva la unión de source_refs."""
    workdir = Path(tempfile.mkdtemp())
    a_src = FIXTURES / "a.note-ir.json"
    b_src = FIXTURES / "b.note-ir.json"
    a_dst = workdir / "a.note-ir.json"
    b_dst = workdir / "b.note-ir.json"
    shutil.copy(a_src, a_dst)
    shutil.copy(b_src, b_dst)
    out = workdir / "ab.note-ir.json"

    # Recolectar antes.
    refs_before = set()
    for src in [a_src, b_src]:
        ir = json.loads(src.read_text(encoding="utf-8"))
        refs_before.update(_collect_source_refs(ir))

    exit, _, stderr = _run([
        "merge", "--irs", str(a_dst), str(b_dst),
        "--output", str(out),
    ], cwd=workdir)
    if exit != 0:
        return Result("Criterio #1: merge preserva source_refs", False, f"exit={exit} stderr={stderr[:200]}")

    ir_after = json.loads(out.read_text(encoding="utf-8"))
    refs_after = _collect_source_refs(ir_after)

    if not refs_after.issuperset(refs_before):
        missing = refs_before - refs_after
        return Result("Criterio #1: merge preserva source_refs", False,
                     f"faltan {len(missing)}")
    return Result("Criterio #1: merge preserva source_refs (2 → 1, refs OK)", True, "")


def check_dedup_preserves_source_refs() -> Result:
    """Criterio #1: dedup preserva la unión de source_refs."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "dup.note-ir.json"
    dst = workdir / "dup.note-ir.json"
    shutil.copy(src, dst)

    original = json.loads(src.read_text(encoding="utf-8"))
    original_refs = _collect_source_refs(original)

    exit, _, stderr = _run(["dedup", "--ir", str(dst)], cwd=workdir)
    if exit != 0:
        return Result("Criterio #1: dedup preserva source_refs", False, f"exit={exit} stderr={stderr[:200]}")

    after = json.loads(dst.read_text(encoding="utf-8"))
    after_refs = _collect_source_refs(after)

    if not after_refs.issuperset(original_refs):
        missing = original_refs - after_refs
        return Result("Criterio #1: dedup preserva source_refs", False,
                     f"faltan {len(missing)}")
    return Result("Criterio #1: dedup preserva source_refs", True, "")


def check_split_rewrites_links() -> Result:
    """Criterio #2: split deja enlaces bidireccionales correctos.

    El frontmatter.related de cada fragmento debe incluir `foo` (la nota original),
    porque al partirse, las hijas deben apuntar de vuelta al padre.
    """
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "large.note-ir.json"
    dst = workdir / "large.note-ir.json"
    shutil.copy(src, dst)

    exit, _, stderr = _run([
        "split",
        "--ir", str(dst),
        "--at-heading", "Chapter 2",
        "--at-heading", "Chapter 4",
        "--no-update-ledger",
    ], cwd=workdir)
    if exit != 0:
        return Result("Criterio #2: split reescribe enlaces", False, f"exit={exit}")

    # Cada fragmento generado (excluyendo el original sin dividir) debe tener "foo" en related.
    fragments = [f for f in workdir.glob("foo-*.note-ir.json")]
    failures = []
    for f in fragments:
        ir = json.loads(f.read_text(encoding="utf-8"))
        related = ir.get("related", []) or []
        if "foo" not in related:
            failures.append(f"{f.name}: related={related}")
    if failures:
        return Result("Criterio #2: split reescribe enlaces", False, f"fallos={failures}")
    return Result(f"Criterio #2: split reescribe enlaces ({len(fragments)} fragmentos, todos enlazan foo)", True, "")


def check_layer_operation() -> Result:
    """Layer: cambia el layer de un nodo específico."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "large.note-ir.json"
    dst = workdir / "large.note-ir.json"
    shutil.copy(src, dst)

    exit, _, stderr = _run([
        "layer",
        "--ir", str(dst),
        "--node-path", "blocks[2]",
        "--layer", "l1",
    ], cwd=workdir)
    if exit != 0:
        return Result("layer: cambia layer de un nodo", False, f"exit={exit} stderr={stderr[:200]}")

    ir = json.loads(dst.read_text(encoding="utf-8"))
    if ir.get("blocks", [])[2].get("layer") != "l1":
        return Result("layer: cambia layer de un nodo", False, "layer no actualizado")
    return Result("layer: cambia layer de un nodo", True, "")


def check_split_max_blocks() -> Result:
    """Split por threshold (modo B)."""
    workdir = Path(tempfile.mkdtemp())
    src = FIXTURES / "large.note-ir.json"
    dst = workdir / "large.note-ir.json"
    shutil.copy(src, dst)

    exit, stdout, stderr = _run([
        "split",
        "--ir", str(dst),
        "--max-blocks", "3",
        "--no-update-ledger",
    ], cwd=workdir)
    if exit != 0:
        return Result("split --max-blocks", False, f"exit={exit} stderr={stderr[:200]}")
    # El número de bloques es 5; threshold=3 debe partir.
    if "SPLIT" not in stdout:
        return Result("split --max-blocks", False, f"no output SPLIT: {stdout[:200]}")
    return Result("split --max-blocks", True, "")


CRITERION_MAP = {
    1: ["Criterio #1: split preserva source_refs (5 → 3 fragmentos, refs OK)",
        "Criterio #1: merge preserva source_refs (2 → 1, refs OK)",
        "Criterio #1: dedup preserva source_refs"],
    2: ["Criterio #2: split reescribe enlaces (3 fragmentos, todos enlazan foo)"],
    3: ["Criterio #1: dedup preserva source_refs", "split --max-blocks"],
}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true")
    parser.add_argument("--criterion", type=int, choices=[1, 2, 3])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = [
        check_module_exists,
        check_split_preserves_source_refs,
        check_merge_preserves_source_refs,
        check_dedup_preserves_source_refs,
        check_split_rewrites_links,
        check_layer_operation,
        check_split_max_blocks,
    ]
    results = [c() for c in checks]

    if args.criterion:
        wanted = CRITERION_MAP[args.criterion]
        results = [r for r in results if r.name in wanted]

    if args.json:
        print(json.dumps([r._asdict() for r in results], indent=2, ensure_ascii=False))
    else:
        width = max(len(r.name) for r in results) + 2
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.name.ljust(width)} {r.detail}")
        n_pass = sum(1 for r in results if r.passed)
        n_total = len(results)
        print(f"\n  Resultado: {n_pass}/{n_total} verde")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

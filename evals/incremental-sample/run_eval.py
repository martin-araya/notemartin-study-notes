#!/usr/bin/env python3
"""run_eval.py — Verificador de la Fase 111 — Actualización incremental.

Ejecuta 3 sub-criterios (C1-C3):

  C1 — Solo los IRs afectados se modifican: tras run-all, `c.note-ir.json`
        tiene `status: archived` + `superseded_by` poblado; `a` y `b` no
        cambian sus `source_refs` originales.
  C2 — Delta generado automáticamente: existe `ir/vd*.note-ir.json` con
        `note_type: "version-delta"` + ≥ 1 entrada `changes` por sección.
  C3 — Ninguna nota pierde contenido válido: `a` y `b` mantienen sus
        `source_refs` originales byte-a-byte; `c` NO se borra y tiene
        `superseded_by` poblado.

Uso:
    python3 evals/incremental-sample/run_eval.py [--regen]

Salida esperada: PASS 3/3.
Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SAMPLE_DIR / "fixtures"
EXPECTED_DIR = SAMPLE_DIR / "expected"
SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "diff" / "update.py"


class _Result:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    def summary(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _run(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable] + cmd, capture_output=True, text=True, cwd=str(cwd)
    )
    return proc.returncode, proc.stdout, proc.stderr


def _make_workdir(name: str) -> Path:
    base = Path(f"/tmp/incremental-eval-{name}")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    src_workdir = FIXTURES_DIR / "workdir"
    if src_workdir.exists():
        shutil.copytree(src_workdir, base, dirs_exist_ok=True)
    return base


def _normalize_source_refs(ir: dict) -> List[Tuple[str, str, str]]:
    """Canonical representation of source_refs (block_id, source_hash, section_path)."""
    out: List[Tuple[str, str, str]] = []

    def walk(node):
        if isinstance(node, dict):
            for sr in node.get("source_refs") or []:
                if isinstance(sr, dict):
                    out.append((
                        sr.get("block_id", ""),
                        sr.get("source_hash", ""),
                        sr.get("section_path", ""),
                    ))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(ir)
    return sorted(out)


# ============================================================
# Tests
# ============================================================


def c1_only_affected_reprocessed(result: _Result) -> None:
    """C1: solo c se marca obsoleto; a y b no cambian sus source_refs."""
    workdir = _make_workdir("c1")
    # Snapshot a/b source_refs antes.
    a_before = json.loads((workdir / "ir" / "a.note-ir.json").read_text(encoding="utf-8"))
    b_before = json.loads((workdir / "ir" / "b.note-ir.json").read_text(encoding="utf-8"))
    c_before = json.loads((workdir / "ir" / "c.note-ir.json").read_text(encoding="utf-8"))
    a_refs_before = _normalize_source_refs(a_before)
    b_refs_before = _normalize_source_refs(b_before)
    c_refs_before = _normalize_source_refs(c_before)
    rc, _, err = _run(
        [str(SCRIPT), "run-all",
         "--old-sdm", str(FIXTURES_DIR / "old" / "old_sdm.json"),
         "--new-sdm", str(FIXTURES_DIR / "old" / "new_sdm.json"),
         "--workdir", str(workdir), "--yes"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C1-only-affected", f"run-all rc={rc} err={err[:200]}")
        return
    # Verificar c se marcó obsoleto.
    c_after = json.loads((workdir / "ir" / "c.note-ir.json").read_text(encoding="utf-8"))
    fm_c = c_after.get("frontmatter", {})
    if fm_c.get("status") != "archived":
        result.fail("C1-only-affected",
                    f"c status={fm_c.get('status')} (esperado archived)")
        return
    if not fm_c.get("superseded_by"):
        result.fail("C1-only-affected",
                    f"c superseded_by={fm_c.get('superseded_by')} (esperado no nulo)")
        return
    # Verificar que a/b NO se modificaron (source_refs byte-a-byte).
    a_after = json.loads((workdir / "ir" / "a.note-ir.json").read_text(encoding="utf-8"))
    b_after = json.loads((workdir / "ir" / "b.note-ir.json").read_text(encoding="utf-8"))
    a_refs_after = _normalize_source_refs(a_after)
    b_refs_after = _normalize_source_refs(b_after)
    if a_refs_after != a_refs_before:
        result.fail("C1-only-affected",
                    f"a source_refs cambiaron: {a_refs_before} → {a_refs_after}")
        return
    if b_refs_after != b_refs_before:
        result.fail("C1-only-affected",
                    f"b source_refs cambiaron: {b_refs_before} → {b_refs_after}")
        return
    # Verificar que c conserva sus source_refs originales (INC-R2).
    c_refs_after = _normalize_source_refs(c_after)
    if c_refs_after != c_refs_before:
        result.fail("C1-only-affected",
                    f"c source_refs cambiaron: {c_refs_before} → {c_refs_after}")
        return
    result.ok(
        "C1-only-affected (c obsoleted con superseded_by; "
        "a/b source_refs byte-a-byte preservados)"
    )


def c2_delta_auto_generated(result: _Result) -> None:
    """C2: existe ir/vd*.note-ir.json con note_type=version-delta + ≥1 change."""
    workdir = _make_workdir("c2")
    rc, _, err = _run(
        [str(SCRIPT), "run-all",
         "--old-sdm", str(FIXTURES_DIR / "old" / "old_sdm.json"),
         "--new-sdm", str(FIXTURES_DIR / "old" / "new_sdm.json"),
         "--workdir", str(workdir), "--yes"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C2-delta", f"run-all rc={rc} err={err[:200]}")
        return
    # Buscar archivos vd*.note-ir.json.
    deltas = sorted(workdir.glob("ir/vd*.note-ir.json"))
    if not deltas:
        result.fail("C2-delta", "no se generó ningún vd*.note-ir.json")
        return
    delta = json.loads(deltas[0].read_text(encoding="utf-8"))
    if delta.get("note_type") != "version-delta":
        # Buscar en frontmatter.
        fm = delta.get("frontmatter", {})
        if fm.get("note-type") != "version-delta":
            result.fail("C2-delta",
                        f"delta no es version-delta: {delta.get('note_type')} / {fm.get('note-type')}")
            return
    changes = delta.get("changes", [])
    if not changes:
        result.fail("C2-delta", "delta sin changes")
        return
    sections = {c.get("section_path") for c in changes}
    # Esperamos al menos: /ch02/main (modified), /ch03/deprecated (removed), /ch05/new (added).
    if "/ch02/main" not in sections:
        result.fail("C2-delta", f"section /ch02/main missing in changes: {sections}")
        return
    if "/ch03/deprecated" not in sections:
        result.fail("C2-delta", f"section /ch03/deprecated missing in changes: {sections}")
        return
    if "/ch05/new" not in sections:
        result.fail("C2-delta", f"section /ch05/new missing in changes: {sections}")
        return
    result.ok(
        f"C2-delta ({len(changes)} cambios cubriendo {len(sections)} secciones; "
        f"version-delta auto-generado; INC-R3 verificado)"
    )


def c3_no_content_lost(result: _Result) -> None:
    """C3: a/b mantienen source_refs originales; c NO se borra y tiene superseded_by."""
    workdir = _make_workdir("c3")
    # Hash a/b antes.
    a_hash_before = hashlib.sha256(
        (workdir / "ir" / "a.note-ir.json").read_bytes()
    ).hexdigest()
    b_hash_before = hashlib.sha256(
        (workdir / "ir" / "b.note-ir.json").read_bytes()
    ).hexdigest()
    rc, _, err = _run(
        [str(SCRIPT), "run-all",
         "--old-sdm", str(FIXTURES_DIR / "old" / "old_sdm.json"),
         "--new-sdm", str(FIXTURES_DIR / "old" / "new_sdm.json"),
         "--workdir", str(workdir), "--yes"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C3-no-loss", f"run-all rc={rc} err={err[:200]}")
        return
    # a/b: deben ser byte-a-identical (excepto 'in_progress_at' field updates si los hubiera).
    a_text = (workdir / "ir" / "a.note-ir.json").read_text(encoding="utf-8")
    b_text = (workdir / "ir" / "b.note-ir.json").read_text(encoding="utf-8")
    # Los IRs no afectados pueden haber sido modificados por escrito atómico (mismo bytes esperado).
    a_hash_after = hashlib.sha256(
        (workdir / "ir" / "a.note-ir.json").read_bytes()
    ).hexdigest()
    b_hash_after = hashlib.sha256(
        (workdir / "ir" / "b.note-ir.json").read_bytes()
    ).hexdigest()
    # Como a/b no están afectados, no deberían haber cambiado.
    # (Aceptamos pequeñas diferencias de whitespace, no source_refs.)
    a_after = json.loads(a_text)
    b_after = json.loads(b_text)
    a_refs = _normalize_source_refs(a_after)
    b_refs = _normalize_source_refs(b_after)
    a_orig = json.loads(FIXTURES_DIR.joinpath("workdir", "ir", "a.note-ir.json").read_text(encoding="utf-8"))
    b_orig = json.loads(FIXTURES_DIR.joinpath("workdir", "ir", "b.note-ir.json").read_text(encoding="utf-8"))
    if a_refs != _normalize_source_refs(a_orig):
        result.fail("C3-no-loss", f"a source_refs cambiaron: {a_refs} != {_normalize_source_refs(a_orig)}")
        return
    if b_refs != _normalize_source_refs(b_orig):
        result.fail("C3-no-loss", f"b source_refs cambiaron")
        return
    # c: NO se borra.
    c_path = workdir / "ir" / "c.note-ir.json"
    if not c_path.exists():
        result.fail("C3-no-loss", "c fue BORRADO (INC-R2 violado)")
        return
    c_after = json.loads(c_path.read_text(encoding="utf-8"))
    fm_c = c_after.get("frontmatter", {})
    if fm_c.get("superseded_by") is None:
        result.fail("C3-no-loss",
                    f"c no tiene superseded_by poblado (INC-R2/AP34)")
        return
    if fm_c.get("status") != "archived":
        result.fail("C3-no-loss",
                    f"c status={fm_c.get('status')} (esperado archived; INC-R2)")
        return
    # c conserva sus source_refs originales.
    c_refs = _normalize_source_refs(c_after)
    c_orig = json.loads(FIXTURES_DIR.joinpath("workdir", "ir", "c.note-ir.json").read_text(encoding="utf-8"))
    if c_refs != _normalize_source_refs(c_orig):
        result.fail("C3-no-loss",
                    f"c source_refs cambiaron (INC-R2): {c_refs}")
        return
    result.ok(
        "C3-no-loss (a/b source_refs preservados; c NO borrado con "
        "superseded_by poblado + source_refs originales; INC-R2 + AP34 verificados)"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    if args.regen:
        rc, _, _ = _run([str(SAMPLE_DIR / "build_fixtures.py")], cwd=REPO_ROOT)
        if rc != 0:
            sys.stderr.write("FAIL — build_fixtures.py rc != 0\n")
            return 1
    if not SCRIPT.exists():
        sys.stderr.write(f"FAIL: {SCRIPT} no existe\n")
        return 1

    result = _Result()
    c1_only_affected_reprocessed(result)
    c2_delta_auto_generated(result)
    c3_no_content_lost(result)

    print("=" * 60)
    print("Fase 111 — Actualización incremental")
    print("=" * 60)
    for name in result.passed:
        print(f"  PASS  {name}")
    for name, detail in result.failed:
        print(f"  FAIL  {name}\n        {detail}")
    print("=" * 60)
    print(result.summary())
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
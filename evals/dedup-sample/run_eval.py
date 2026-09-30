#!/usr/bin/env python3
"""run_eval.py — Verificador de la Fase 108 — Deduplicación y fusión.

Ejecuta 3 sub-criterios (C1-C3):

  C1 — `apply merge` no pierde unidades: source_refs de A ∪ B ⊆ source_refs de C
        (DEDUP-R1) + frontmatter.aliases de C contiene A y B (DEDUP-R3).
  C2 — Enlaces entrantes redirigidos: tras apply merge A+B→C, los IRs del
        workdir con `[[note:A]]` o `[[note:B]]` se han reescrito a `[[note:C]]`
        (DEDUP-R2) + manifest.json::link_debt[] tiene entradas (DEDUP-R4).
  C3 — Detector encuentra duplicados inyectados: scan sobre los 5 pares
        tiene recall ≥ 4/5 contra expected/candidates.json (V3 + AP25).

Uso:
    python3 evals/dedup-sample/run_eval.py [--regen]

Salida esperada: PASS 3/3.
Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SAMPLE_DIR / "fixtures"
NOTES_DIR = FIXTURES_DIR / "notes"
EXPECTED_DIR = SAMPLE_DIR / "expected"

DETECT_SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "dedup" / "detect.py"
APPLY_SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "dedup" / "apply.py"
TRANSFORM_SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "authoring" / "transform.py"


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
    base = Path(f"/tmp/dedup-eval-{name}")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    return base


# ============================================================
# IR fixtures para C1+C2 (sintéticos, válidos para F50)
# ============================================================


def _write_ir(path: Path, ir: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ir, indent=2), encoding="utf-8")


def _build_ir_pair(workdir: Path) -> Tuple[Path, Path, Path]:
    """Crea 2 IRs (A, B) + 1 IR externo (X con [[note:A]]) para C1+C2."""
    ir_dir = workdir / "ir"
    ir_dir.mkdir(parents=True, exist_ok=True)
    sr_a = [
        {"block_id": "a00000000001", "source_hash": "h" * 64,
         "section_path": "/ch01/intro"},
        {"block_id": "a00000000002", "source_hash": "h" * 64,
         "section_path": "/ch01/body"},
    ]
    sr_b = [
        {"block_id": "b00000000001", "source_hash": "h" * 64,
         "section_path": "/ch02/intro"},
    ]
    a = {
        "schema_version": "1.0.0",
        "note_id": "note-a",
        "title": "Note A",
        "layer": "l2",
        "frontmatter": {"title": "Note A", "aliases": ["a-alias"]},
        "blocks": [
            {
                "node": "section",
                "attrs": {"level": 2, "capability": "section-h2"},
                "source_refs": [sr_a[0]],
                "children": [
                    {
                        "node": "paragraph",
                        "attrs": {"capability": "paragraph"},
                        "source_refs": [sr_a[1]],
                        "children": [
                            {"node": "text",
                             "attrs": {"text": "Content of A", "capability": "text"},
                             "source_refs": []},
                        ],
                    },
                ],
            },
        ],
    }
    b = {
        "schema_version": "1.0.0",
        "note_id": "note-b",
        "title": "Note B",
        "layer": "l2",
        "frontmatter": {"title": "Note B", "aliases": ["b-alias"]},
        "blocks": [
            {
                "node": "section",
                "attrs": {"level": 2, "capability": "section-h2",
                          "_title": "Section B"},
                "source_refs": [sr_b[0]],
                "children": [
                    {
                        "node": "paragraph",
                        "attrs": {"capability": "paragraph"},
                        "source_refs": [sr_b[0]],
                        "children": [
                            {"node": "text",
                             "attrs": {"text": "Content of B", "capability": "text"},
                             "source_refs": []},
                        ],
                    },
                ],
            },
        ],
    }
    x = {
        "schema_version": "1.0.0",
        "note_id": "note-x",
        "title": "Note X",
        "layer": "l2",
        "frontmatter": {"title": "Note X"},
        "blocks": [
            {
                "node": "paragraph",
                "attrs": {"capability": "paragraph"},
                "source_refs": [],
                "children": [
                    {"node": "text",
                     "attrs": {"text": "Refers to ", "capability": "text"},
                     "source_refs": []},
                    {"node": "link-note",
                     "attrs": {"target": "note-a", "capability": "link-note",
                                "text": "note a"},
                     "source_refs": []},
                    {"node": "text",
                     "attrs": {"text": " and ", "capability": "text"},
                     "source_refs": []},
                    {"node": "link-note",
                     "attrs": {"target": "note-b", "capability": "link-note",
                                "text": "note b"},
                     "source_refs": []},
                ],
            },
        ],
    }
    a_path = ir_dir / "note-a.note-ir.json"
    b_path = ir_dir / "note-b.note-ir.json"
    x_path = ir_dir / "note-x.note-ir.json"
    _write_ir(a_path, a)
    _write_ir(b_path, b)
    _write_ir(x_path, x)
    return a_path, b_path, x_path


# ============================================================
# Tests
# ============================================================


def c1_merge_no_loss(result: _Result) -> None:
    """C1: source_refs unión + DEDUP-R1 + DEDUP-R3 (aliases)."""
    workdir = _make_workdir("c1")
    a_path, b_path, _x = _build_ir_pair(workdir)
    out_path = workdir / "ir" / "note-merged.note-ir.json"
    rc, _, err = _run(
        [str(APPLY_SCRIPT), "merge",
         "--a", str(a_path), "--b", str(b_path),
         "--output", str(out_path),
         "--workdir", str(workdir),
         "--irs-glob", "ir/*.json",
         "--note-id", "note-merged",
         "--yes"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C1-merge-no-loss", f"apply merge rc={rc} err={err[:200]}")
        return
    if not out_path.exists():
        result.fail("C1-merge-no-loss", f"output no creado: {out_path}")
        return
    merged = json.loads(out_path.read_text(encoding="utf-8"))
    # Verificar DEDUP-R1: source_refs unión.
    def _collect_refs(ir: dict) -> set:
        out = set()

        def walk(node):
            if isinstance(node, dict):
                for sr in node.get("source_refs") or []:
                    if isinstance(sr, dict):
                        out.add((sr.get("block_id", ""), sr.get("source_hash", "")))
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(ir)
        return out
    refs_a = _collect_refs(json.loads(a_path.read_text(encoding="utf-8")))
    refs_b = _collect_refs(json.loads(b_path.read_text(encoding="utf-8")))
    refs_m = _collect_refs(merged)
    missing = (refs_a | refs_b) - refs_m
    if missing:
        result.fail("C1-merge-no-loss", f"DEDUP-R1 violado: {len(missing)} source_refs perdidos: {list(missing)[:3]}")
        return
    # Verificar DEDUP-R3: aliases contienen note-a y note-b.
    aliases = merged.get("frontmatter", {}).get("aliases", [])
    if "note-a" not in aliases or "note-b" not in aliases:
        result.fail("C1-merge-no-loss", f"DEDUP-R3 violado: aliases={aliases}")
        return
    result.ok(
        f"C1-merge-no-loss (DEDUP-R1: {len(refs_a | refs_b)} source_refs preservados; "
        f"DEDUP-R3: aliases contiene note-a + note-b)"
    )


def c2_incoming_links_redirected(result: _Result) -> None:
    """C2: tras apply merge, `[[note:note-a]]` y `[[note:note-b]]` reescritos;
    manifest.json::link_debt[] tiene 2 entradas redirected."""
    workdir = _make_workdir("c2")
    a_path, b_path, x_path = _build_ir_pair(workdir)
    out_path = workdir / "ir" / "note-merged.note-ir.json"
    rc, _, err = _run(
        [str(APPLY_SCRIPT), "merge",
         "--a", str(a_path), "--b", str(b_path),
         "--output", str(out_path),
         "--workdir", str(workdir),
         "--irs-glob", "ir/*.json",
         "--note-id", "note-merged",
         "--yes"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C2-links-redirected", f"apply merge rc={rc} err={err[:200]}")
        return
    # Verificar que el IR externo ya no contiene los old links.
    x_text = x_path.read_text(encoding="utf-8")
    if '"target": "note-a"' in x_text or '"target": "note-b"' in x_text:
        # Re-load, count occurrences.
        x_ir = json.loads(x_text)
        x_text2 = json.dumps(x_ir)
        n_a = x_text2.count('"target": "note-a"')
        n_b = x_text2.count('"target": "note-b"')
        if n_a or n_b:
            result.fail("C2-links-redirected",
                        f"DEDUP-R2 violado: note-a={n_a} refs, note-b={n_b} refs restantes")
            return
    # Verificar manifest.json.
    manifest_path = workdir / "manifest.json"
    if not manifest_path.exists():
        result.fail("C2-links-redirected", "manifest.json no creado")
        return
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    debt = manifest_data.get("link_debt", [])
    redirected = [d for d in debt if d.get("kind") == "redirected"
                   and d.get("target") == "note-merged"]
    if len(redirected) < 2:
        result.fail("C2-links-redirected",
                    f"DEDUP-R4 violado: {len(redirected)} entradas redirected (esperado ≥ 2)")
        return
    from_ids = {d["from_note"] for d in redirected}
    if not {"note-a", "note-b"}.issubset(from_ids):
        result.fail("C2-links-redirected", f"from_notes={from_ids}")
        return
    result.ok(
        f"C2-links-redirected (DEDUP-R2: 0 old links en note-x; "
        f"DEDUP-R4: {len(redirected)} entradas redirected en manifest)"
    )


def c3_detector_finds_injected(result: _Result) -> None:
    """C3: detector encuentra ≥ 4/5 pares inyectados."""
    workdir = _make_workdir("c3")
    # Copiar fixtures/notes/ + glossary.json al workdir.
    if (workdir / "notes").exists():
        shutil.rmtree(workdir / "notes")
    shutil.copytree(NOTES_DIR, workdir / "notes")
    shutil.copy(FIXTURES_DIR / "glossary.json", workdir / "glossary.json")
    # Colocar expected/candidates.json en workdir/expected/ (el verify lo lee).
    expected_dest = workdir / "expected"
    expected_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXPECTED_DIR / "candidates.json", expected_dest / "candidates.json")
    rc, _, err = _run([str(DETECT_SCRIPT), "scan",
                        "--workdir", str(workdir),
                        "--glossary", str(workdir / "glossary.json"),
                        "--json-out", str(workdir / "candidates.json")],
                       cwd=REPO_ROOT)
    if rc != 0:
        result.fail("C3-detector-finds-injected", f"scan rc={rc} err={err[:200]}")
        return
    rc, out, err = _run([str(DETECT_SCRIPT), "verify",
                          "--workdir", str(workdir)], cwd=REPO_ROOT)
    if rc != 0:
        result.fail("C3-detector-finds-injected",
                    f"verify rc={rc} out={out[:300]} err={err[:200]}")
        return
    # Verify recall ≥ 4/5.
    actual = json.loads((workdir / "candidates.json").read_text(encoding="utf-8"))
    actual_pairs = {tuple(sorted(c["pair"])) for c in actual.get("candidates", [])}
    expected_pairs = {
        tuple(sorted(c["pair"]))
        for c in json.loads((EXPECTED_DIR / "candidates.json").read_text(encoding="utf-8"))["candidates"]
    }
    hits = expected_pairs & actual_pairs
    recall = len(hits) / max(len(expected_pairs), 1)
    if recall < 0.8:
        result.fail("C3-detector-finds-injected",
                    f"recall={recall:.2f} ({len(hits)}/{len(expected_pairs)})")
        return
    result.ok(
        f"C3-detector-finds-injected (recall={recall:.2f}; "
        f"{len(hits)}/{len(expected_pairs)} pares ground-truth detectados)"
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
    # Verificar scripts disponibles.
    for script in (DETECT_SCRIPT, APPLY_SCRIPT, TRANSFORM_SCRIPT):
        if not script.exists():
            sys.stderr.write(f"FAIL: {script} no existe\n")
            return 1
    result = _Result()
    c1_merge_no_loss(result)
    c2_incoming_links_redirected(result)
    c3_detector_finds_injected(result)

    print("=" * 60)
    print("Fase 108 — Deduplicación y fusión")
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
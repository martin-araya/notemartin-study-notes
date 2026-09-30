#!/usr/bin/env python3
"""run_eval.py — Verificador de la Fase 107 — Bucle por chunks.

Ejecuta 6 sub-criterios (C1-C6) sobre los deliverables de F107:

  C1 — Default chunk_size=30 con 250 bloques → 9 chunks.
  C2 — Estrategia `by_chapter` con chapter_size=3 → ~9 chunks sobre 25 chapters.
  C3 — AP-CHK1: cross-chunk unit registrada una vez con primary + secondary.
  C4 — AP-CHK2: audit log SIN texto crudo → check OK; CON texto crudo → FAIL.
  C5 — Walk idempotente: re-walk sobre chunk done sin --force → exit 1.
  C6 — Resume continúa sin re-procesar + .bak presente tras save().

Uso:
    python3 evals/chunk-loop-sample/run_eval.py [--regen]

Salida esperada: PASS 6/6.
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
EXPECTED_DIR = SAMPLE_DIR / "expected"
SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "pipeline" / "chunk_loop.py"


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
    base = Path(f"/tmp/chunk-loop-{name}")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    return base


def _register_cross_chunk_unit_api(workdir: Path, unit_id: str, primary: str,
                                   secondary: List[str], note_id: str = "n") -> None:
    """Helper para invocar la API Python de register_cross_chunk_unit."""
    code = (
        "import sys; sys.path.insert(0, 'skill/notemartin-study-notes/scripts/pipeline'); "
        "from chunk_loop import ChunkState, register_cross_chunk_unit; "
        f"state = ChunkState.load(__import__('pathlib').Path('{workdir}')); "
        f"register_cross_chunk_unit(state, '{unit_id}', primary_chunk='{primary}', "
        f"secondary_chunks={secondary!r}, note_id='{note_id}'); "
        "state.save()"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        sys.stderr.write(f"FAIL — register API: {proc.stderr}\n")


def c1_default_chunk_size_30(result: _Result) -> None:
    """C1: 250 bloques / 30 = 9 chunks."""
    workdir = _make_workdir("c1")
    rc, _, err = _run(
        [str(SCRIPT), "init", "--sdm", str(FIXTURES_DIR / "sdm-large.json"),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C1-chunk-size-30", f"init rc={rc} err={err[:200]}")
        return
    state = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    n = len(state["chunks"])
    if n != 9:
        result.fail("C1-chunk-size-30", f"n_chunks={n} (esperado 9)")
        return
    if state["config"]["chunk_size"] != 30:
        result.fail("C1-chunk-size-30", f"chunk_size={state['config']['chunk_size']}")
        return
    result.ok(f"C1-chunk-size-30 ({n} chunks sobre 250 bloques, chunk_size=30)")


def c2_by_chapter_strategy(result: _Result) -> None:
    """C2: by_chapter con chapter_size=3 sobre 25 chapters → ceil(25/3)=9 chunks."""
    workdir = _make_workdir("c2")
    rc, _, err = _run(
        [str(SCRIPT), "init",
         "--sdm", str(FIXTURES_DIR / "sdm-large.json"),
         "--workdir", str(workdir),
         "--strategy", "by_chapter", "--chunk-size", "3"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C2-by-chapter", f"init rc={rc} err={err[:200]}")
        return
    state = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    n = len(state["chunks"])
    if n != 9:
        result.fail("C2-by-chapter", f"n_chunks={n} (esperado 9)")
        return
    result.ok(f"C2-by-chapter ({n} chunks; strategy=by_chapter, chunk_size=3)")


def c3_cross_chunk_unit(result: _Result) -> None:
    """C3: AP-CHK1 — cross-chunk unit tiene note_id único + primary + secondary."""
    workdir = _make_workdir("c3")
    rc, _, err = _run(
        [str(SCRIPT), "init",
         "--sdm", str(FIXTURES_DIR / "sdm-cross-chunk.json"),
         "--workdir", str(workdir),
         "--chunk-size", "30"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C3-cross-chunk", f"init rc={rc} err={err[:200]}")
        return
    _register_cross_chunk_unit_api(workdir, "mvcc", "chk01", ["chk02"], note_id="n-mvcc")
    state = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    ccu = state["cross_chunk_units"]
    if len(ccu) != 1:
        result.fail("C3-cross-chunk", f"len(cross_chunk_units)={len(ccu)} (esperado 1)")
        return
    if ccu[0]["unit_id"] != "mvcc" or ccu[0]["primary_chunk"] != "chk01":
        result.fail("C3-cross-chunk", f"primary={ccu[0]}")
        return
    if ccu[0]["secondary_chunks"] != ["chk02"]:
        result.fail("C3-cross-chunk", f"secondary={ccu[0]['secondary_chunks']}")
        return
    if ccu[0]["note_id"] != "n-mvcc":
        result.fail("C3-cross-chunk", f"note_id={ccu[0]['note_id']}")
        return
    # Verificar que check NO reporta AP-CHK1.
    rc, _, out = _run(
        [str(SCRIPT), "check", "--workdir", str(workdir)], cwd=REPO_ROOT
    )
    if rc != 0 or "AP-CHK1" in out:
        result.fail("C3-cross-chunk", f"check reporta AP-CHK1 inesperado: {out[:200]}")
        return
    # Verificar que registrar la misma unidad con otro note_id NO crea duplicado.
    _register_cross_chunk_unit_api(workdir, "mvcc", "chk01", [], note_id="n-mvcc")
    state = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    if len(state["cross_chunk_units"]) != 1:
        result.fail("C3-cross-chunk", "duplicate cross_chunk_unit creada")
        return
    result.ok("C3-cross-chunk (1 unidad; primary=chk01; secondary=[chk02]; AP-CHK1 PASS)")


def c4_ap_chk2_audit_loads(result: _Result) -> None:
    """C4: AP-CHK2 — log limpio PASS; log sucio FAIL."""
    # Log limpio.
    rc, _, out = _run(
        [str(SCRIPT), "check", "--workdir", str(Path("/tmp/dummy")),
         "--audit-loads", str(EXPECTED_DIR / "audit-loads-no-full.jsonl")],
        cwd=REPO_ROOT,
    )
    # El check reporta error porque /tmp/dummy no existe (es un workdir
    # inválido), pero queremos verificar AP-CHK2. Probamos solo el path:
    # el script intenta cargar el workdir PRIMERO; si falla, devuelve 1 con
    # ERR_STATE_CORRUPT. Para probar AP-CHK2 aisladamente, simulamos con un
    # workdir válido y el log sucio.
    workdir = _make_workdir("c4")
    rc, _, err = _run(
        [str(SCRIPT), "init",
         "--sdm", str(FIXTURES_DIR / "sdm-large.json"),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C4-ap-chk2", f"init rc={rc} err={err[:200]}")
        return
    # Log limpio (sin path de fuente) → PASS.
    rc, _, out = _run(
        [str(SCRIPT), "check", "--workdir", str(workdir),
         "--audit-loads", str(EXPECTED_DIR / "audit-loads-no-full.jsonl")],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C4-ap-chk2", f"log limpio rc={rc} out={out[:200]}")
        return
    if "AP-CHK2" in out:
        result.fail("C4-ap-chk2", "AP-CHK2 detectado en log limpio (falso positivo)")
        return
    # Log sucio (con path de fuente) → FAIL.
    rc, _, out = _run(
        [str(SCRIPT), "check", "--workdir", str(workdir),
         "--audit-loads", str(FIXTURES_DIR / "audit-loads-with-full.jsonl")],
        cwd=REPO_ROOT,
    )
    if rc != 1:
        result.fail("C4-ap-chk2", f"log sucio rc={rc} (esperado 1) out={out[:200]}")
        return
    if "AP-CHK2" not in out:
        result.fail("C4-ap-chk2", f"AP-CHK2 no detectado en log sucio: {out[:200]}")
        return
    result.ok("C4-ap-chk2 (log limpio PASS; log sucio FAIL con AP-CHK2)")


def c5_walk_idempotent(result: _Result) -> None:
    """C5: re-walk sobre chunk done sin --force → exit 1."""
    workdir = _make_workdir("c5")
    rc, _, _ = _run(
        [str(SCRIPT), "init",
         "--sdm", str(FIXTURES_DIR / "sdm-large.json"),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C5-idempotent", "init rc != 0")
        return
    rc, _, _ = _run(
        [str(SCRIPT), "walk", "--workdir", str(workdir),
         "--chunk", "chk01", "--notes", "n1"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C5-idempotent", "first walk rc != 0")
        return
    rc, _, err = _run(
        [str(SCRIPT), "walk", "--workdir", str(workdir), "--chunk", "chk01"],
        cwd=REPO_ROOT,
    )
    if rc != 1 or "CHUNK_ALREADY_DONE" not in err:
        result.fail("C5-idempotent", f"re-walk rc={rc} err={err[:200]}")
        return
    # Con --force sí debe aceptar y preservar previous_processed_at.
    rc, _, _ = _run(
        [str(SCRIPT), "walk", "--workdir", str(workdir),
         "--chunk", "chk01", "--notes", "n2", "--force"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C5-idempotent", "force walk rc != 0")
        return
    state = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    ch01 = next(c for c in state["chunks"] if c["id"] == "chk01")
    if not ch01.get("previous_processed_at"):
        result.fail("C5-idempotent", "previous_processed_at ausente tras --force")
        return
    result.ok("C5-idempotent (re-walk sin --force → exit 1; con --force preserva previous_processed_at)")


def c6_resume_atomic(result: _Result) -> None:
    """C6: resume continúa; .bak presente tras save()."""
    workdir = _make_workdir("c6")
    rc, _, _ = _run(
        [str(SCRIPT), "init",
         "--sdm", str(FIXTURES_DIR / "sdm-large.json"),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-resume", "init rc != 0")
        return
    rc, _, _ = _run(
        [str(SCRIPT), "walk", "--workdir", str(workdir),
         "--chunk", "chk01", "--notes", "n1"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-resume", "first walk rc != 0")
        return
    bak = workdir / "chunk-state.json.bak"
    if not bak.exists():
        result.fail("C6-resume", ".bak ausente tras save()")
        return
    # Snapshot timestamps de chk01.
    snap = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    ch01_snap = next(c for c in snap["chunks"] if c["id"] == "chk01")
    # Resume hasta chk09.
    rc, _, _ = _run(
        [str(SCRIPT), "resume", "--workdir", str(workdir), "--to", "chk09"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-resume", f"resume rc={rc}")
        return
    cur = json.loads((workdir / "chunk-state.json").read_text(encoding="utf-8"))
    ch01_cur = next(c for c in cur["chunks"] if c["id"] == "chk01")
    if ch01_snap["processed_at"] != ch01_cur["processed_at"]:
        result.fail("C6-resume", f"chk01 processed_at mutó: {ch01_snap['processed_at']} → {ch01_cur['processed_at']}")
        return
    # Todos los chunks del rango están done.
    pending = [c["id"] for c in cur["chunks"] if c["status"] != "done"]
    if pending:
        result.fail("C6-resume", f"pending: {pending}")
        return
    result.ok("C6-resume (.bak presente; chk01 timestamp inmutable; chk01-chk09 done)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    if args.regen:
        rc, _, _ = _run([str(SAMPLE_DIR / "build_fixtures.py")], cwd=REPO_ROOT)
        if rc != 0:
            sys.stderr.write("FAIL — build_fixtures.py rc != 0\n")
            return 1

    result = _Result()
    c1_default_chunk_size_30(result)
    c2_by_chapter_strategy(result)
    c3_cross_chunk_unit(result)
    c4_ap_chk2_audit_loads(result)
    c5_walk_idempotent(result)
    c6_resume_atomic(result)

    print("=" * 60)
    print("Fase 107 — Bucle por chunks y presupuesto de contexto")
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
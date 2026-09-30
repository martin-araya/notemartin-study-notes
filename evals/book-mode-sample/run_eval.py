#!/usr/bin/env python3
"""run_eval.py — Verificador de la Fase 106 — Modo obra completa.

Ejecuta 6 sub-criterios (C1-C6) sobre los deliverables de F106:

  C1 — `init` exige book_map.json antes de permitir process (BM-R1).
  C2 — AP-BM1 detecta la redefinición de MVCC en ch09 sin `[[note:mvcc]]`
        y NO detecta la nota que sí lo enlaza.
  C3 — `resume` continúa desde next_chapter sin re-procesar done;
        `started_at`/`processed_at` de los capítulos previos son inmutables.
  C4 — Consolidación N=5 se dispara tras ch05; re-ejecutar `consolidate`
        es idempotente.
  C5 — Escritura atómica: tras `save()`, existe `.bak` antes de la nueva
        escritura.
  C6 — AP-BM2..AP-BM4: fixtures negativos para mapa regenerado tras ch1
        (AP-BM2), .bak ausente (AP-BM3), re-process de done con --force
        preserva `previous_processed_at` (AP-BM4).

Uso:
    python3 evals/book-mode-sample/run_eval.py [--regen]

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
SCRIPT = REPO_ROOT / "skill" / "notemartin-study-notes" / "scripts" / "pipeline" / "book_mode.py"
SDM_FIXTURE = FIXTURES_DIR / "sdm-book.json"
NOTES_FIXTURE = FIXTURES_DIR / "notes"


class EvalResult:
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


def _run(cmd: List[str], cwd: Path, check: bool = False) -> Tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable] + cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )
    if check and proc.returncode != 0:
        sys.stderr.write(
            f"FAIL — cmd={' '.join(cmd)} exit={proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}\n"
        )
    return proc.returncode, proc.stdout, proc.stderr


def _make_workdir() -> Path:
    """Crea un workdir limpio bajo /tmp y devuelve su ruta."""
    base = Path("/tmp/book-mode-eval")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    return base


def _copy_notes_to(workdir: Path) -> None:
    """Copia la jerarquía de notas fixture al workdir."""
    target = workdir / "notes"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(NOTES_FIXTURE, target)


def c1_init_blocks_process_until_map_exists(result: EvalResult) -> None:
    """C1: mapa antes del primer capítulo (BM-R1)."""
    workdir = _make_workdir()
    # Forzar estado sin book_map.json y con started_at poblado.
    state = {
        "schema_version": "1.0.0",
        "book_id": "test-bm1",
        "source_hash": "a" * 64,
        "total_chapters": 10,
        "has_preface": True,
        "chapters": [
            {"id": f"ch{n:02d}", "title": f"Ch{n}",
             "status": "processing" if n == 1 else "pending",
             "started_at": "2026-01-01T00:00:00Z" if n == 1 else None,
             "processed_at": None, "previous_processed_at": None,
             "sdm_path": None, "notes": [], "error": None}
            for n in range(1, 12)
        ],
        "shared_concepts": {},
        "book_map_ref": "book_map.json",
        "last_consolidation_chapter": None,
        "next_consolidation_at": None,
        "index_unreliable": False,
        "config": {"consolidation_every": 5, "auto_consolidate": False},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    (workdir / "book-state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    rc, _, err = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir), "--chapter", "ch02"],
        cwd=REPO_ROOT,
    )
    if rc != 1 or "BOOK_MAP_MISSING" not in err:
        result.fail("C1-mapa-antes-ch1", f"rc={rc} err={err[:200]}")
        return
    # Crear mapa con timestamp anterior.
    book_map = {
        "schema_version": "1.0.0",
        "book_id": "test-bm1",
        "generated_at": "2025-12-31T00:00:00Z",
        "nodes": [], "edges": [], "mermaid_path": "book_map.mmd",
    }
    (workdir / "book_map.json").write_text(
        json.dumps(book_map, indent=2), encoding="utf-8"
    )
    rc, _, _ = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir), "--chapter", "ch02"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C1-mapa-antes-ch1", f"con mapa válido rc={rc}")
        return
    result.ok("C1-mapa-antes-ch1 (BM-R1 violado → exit 1; con mapa OK)")


def c2_ap_bm1_detects_redefinition(result: EvalResult) -> None:
    """C2: concepto de ch02 no redefinido en ch09."""
    workdir = _make_workdir()
    rc, _, err = _run(
        [str(SCRIPT), "init", "--sdm", str(SDM_FIXTURE),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C2-ap-bm1", f"init rc={rc} err={err[:200]}")
        return
    # Marcar ch02 y ch09 como done para que detect-ap-bm1 los incluya.
    for ch in ("ch02", "ch03", "ch09"):
        rc, _, _ = _run(
            [str(SCRIPT), "process", "--workdir", str(workdir),
             "--chapter", ch, "--notes", "x"],
            cwd=REPO_ROOT,
        )
        if rc != 0:
            result.fail("C2-ap-bm1", f"process {ch} rc={rc}")
            return
    # Registrar concepto MVCC en ch02.
    rc, _, _ = _run(
        [str(SCRIPT), "register-concept", "--workdir", str(workdir),
         "--concept-id", "mvcc", "--chapter", "ch02", "--note-id", "mvcc"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C2-ap-bm1", f"register-concept rc={rc}")
        return
    _copy_notes_to(workdir)
    # Detectar.
    rc, _, err = _run(
        [str(SCRIPT), "detect-ap-bm1", "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 1:
        result.fail("C2-ap-bm1", f"detect-ap-bm1 rc={rc} (esperado 1) err={err[:200]}")
        return
    if "mvcc" not in err or "ch09" not in err:
        result.fail("C2-ap-bm1", f"AP-BM1 no menciona mvcc/ch09 en err={err[:200]}")
        return
    # Verificar que ch03 NO es violación (tiene `[[note:mvcc]]`).
    if "ch03" in err:
        result.fail("C2-ap-bm1", "AP-BM1 detecta ch03 (falso positivo)")
        return
    result.ok("C2-ap-bm1 (1 violación en ch09; ch03 con link NO es violación)")


def c3_resume_continues_without_reprocessing(result: EvalResult) -> None:
    """C3: stop/resume. Procesa ch01-ch03, snapshot de timestamps,
    resume procesa ch04 onwards sin tocar ch01-ch03."""
    workdir = _make_workdir()
    rc, _, _ = _run(
        [str(SCRIPT), "init", "--sdm", str(SDM_FIXTURE),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C3-resume", f"init rc={rc}")
        return
    # Marcar ch01, ch02, ch03 como done secuencialmente.
    for ch in ("ch01", "ch02", "ch03"):
        rc, _, _ = _run(
            [str(SCRIPT), "process", "--workdir", str(workdir),
             "--chapter", ch, "--notes", "n"],
            cwd=REPO_ROOT,
        )
        if rc != 0:
            result.fail("C3-resume", f"process {ch} rc={rc}")
            return
    # Snapshot timestamps.
    state = json.loads((workdir / "book-state.json").read_text(encoding="utf-8"))
    snap = {ch["id"]: (ch.get("started_at"), ch.get("processed_at"))
            for ch in state["chapters"]}
    # Resume.
    rc, _, _ = _run(
        [str(SCRIPT), "resume", "--workdir", str(workdir), "--to", "ch11"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C3-resume", f"resume rc={rc}")
        return
    state = json.loads((workdir / "book-state.json").read_text(encoding="utf-8"))
    for ch in state["chapters"]:
        cid = ch["id"]
        if cid in snap and snap[cid][0] is not None:
            if ch["started_at"] != snap[cid][0] or ch["processed_at"] != snap[cid][1]:
                result.fail("C3-resume", f"{cid} timestamp mutado: {snap[cid]} → {ch['started_at']}/{ch['processed_at']}")
                return
    # Verificar que ahora todos están done.
    pending = [ch["id"] for ch in state["chapters"] if ch["status"] != "done"]
    if pending:
        result.fail("C3-resume", f"quedan pending: {pending}")
        return
    result.ok("C3-resume (timestamps inmutables; ch01-ch11 done tras resume)")


def c4_consolidation_every_5(result: EvalResult) -> None:
    """C4: consolidación N=5 idempotente."""
    workdir = _make_workdir()
    rc, _, _ = _run(
        [str(SCRIPT), "init", "--sdm", str(SDM_FIXTURE),
         "--workdir", str(workdir), "--consolidation-every", "5"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C4-consolidate", f"init rc={rc}")
        return
    for ch in ("ch01", "ch02", "ch03", "ch04", "ch05"):
        rc, _, _ = _run(
            [str(SCRIPT), "process", "--workdir", str(workdir),
             "--chapter", ch, "--notes", "n"],
            cwd=REPO_ROOT,
        )
        if rc != 0:
            result.fail("C4-consolidate", f"process {ch} rc={rc}")
            return
    rc, _, out = _run(
        [str(SCRIPT), "consolidate", "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C4-consolidate", f"consolidate rc={rc} out={out[:200]}")
        return
    state = json.loads((workdir / "book-state.json").read_text(encoding="utf-8"))
    if state["last_consolidation_chapter"] != "ch05":
        result.fail("C4-consolidate", f"last_consolidation={state['last_consolidation_chapter']}")
        return
    # Re-ejecutar es idempotente.
    snap_before = (workdir / "book-state.json").read_text(encoding="utf-8")
    rc, _, _ = _run(
        [str(SCRIPT), "consolidate", "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C4-consolidate", "segundo consolidate rc != 0")
        return
    # Re-load, comparar campos semánticos (ignorar updated_at).
    snap_after = (workdir / "book-state.json").read_text(encoding="utf-8")
    a = json.loads(snap_before); b = json.loads(snap_after)
    a.pop("updated_at", None); b.pop("updated_at", None)
    if a != b:
        result.fail("C4-consolidate", "re-consolidate no idempotente")
        return
    result.ok("C4-consolidate (N=5 → ch05; re-run idempotente)")


def c5_atomic_writes_create_bak(result: EvalResult) -> None:
    """C5: cada save() preserva .bak."""
    workdir = _make_workdir()
    rc, _, _ = _run(
        [str(SCRIPT), "init", "--sdm", str(SDM_FIXTURE),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C5-atomic", f"init rc={rc}")
        return
    # init crea el archivo por primera vez (sin .bak). La 2ª save (process)
    # debe copiar el estado anterior a .bak.
    state_path = workdir / "book-state.json"
    bak = state_path.with_suffix(state_path.suffix + ".bak")
    if bak.exists():
        result.fail("C5-atomic", f".bak inesperado tras init: {bak}")
        return
    # process actualiza y crea .bak.
    rc, _, _ = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir),
         "--chapter", "ch02", "--notes", "n"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C5-atomic", "process rc != 0")
        return
    if not bak.exists():
        result.fail("C5-atomic", ".bak ausente tras process")
        return
    bak_text = bak.read_text(encoding="utf-8")
    if "ch02" not in bak_text:
        result.fail("C5-atomic", ".bak no contiene ch02")
        return
    # El .bak debe ser DIFERENTE del state actual (snapshot anterior).
    cur_text = (workdir / "book-state.json").read_text(encoding="utf-8")
    if bak_text == cur_text:
        result.fail("C5-atomic", ".bak idéntico al state actual (no es snapshot anterior)")
        return
    bak_state = json.loads(bak_text)
    cur_state = json.loads(cur_text)
    ch02_bak = next(c for c in bak_state["chapters"] if c["id"] == "ch02")
    ch02_cur = next(c for c in cur_state["chapters"] if c["id"] == "ch02")
    # El snapshot anterior debe ser un estado anterior en la transición.
    if ch02_bak["status"] not in ("pending", "processing"):
        result.fail("C5-atomic", f".bak ch02 status={ch02_bak['status']} (esperado pending|processing)")
        return
    if ch02_cur["status"] != "done":
        result.fail("C5-atomic", f"state ch02 status={ch02_cur['status']} (esperado done)")
        return
    result.ok("C5-atomic (.bak = snapshot anterior; current = done)")


def c6_ap_bm2_bm3_bm4(result: EvalResult) -> None:
    """C6: detect AP-BM2 (mapa tras ch1), AP-BM3 (.bak ausente),
    AP-BM4 (re-process con --force preserva previous_processed_at)."""
    workdir = _make_workdir()
    rc, _, _ = _run(
        [str(SCRIPT), "init", "--sdm", str(SDM_FIXTURE),
         "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-ap-bm234", f"init rc={rc}")
        return
    # C6.1 AP-BM4: procesar ch01, luego con --force preservando previous.
    rc, _, _ = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir),
         "--chapter", "ch01", "--notes", "first"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-ap-bm234", "first process rc != 0")
        return
    rc, _, _ = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir),
         "--chapter", "ch01", "--notes", "second", "--force"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        result.fail("C6-ap-bm234", "force process rc != 0")
        return
    state = json.loads((workdir / "book-state.json").read_text(encoding="utf-8"))
    ch01 = next(c for c in state["chapters"] if c["id"] == "ch01")
    if not ch01.get("previous_processed_at"):
        result.fail("C6-ap-bm234", "previous_processed_at ausente tras --force")
        return
    # C6.2 AP-BM2: regenerar book_map.json con generated_at posterior a ch01.started_at
    book_map = json.loads((workdir / "book_map.json").read_text(encoding="utf-8"))
    book_map["generated_at"] = "2099-01-01T00:00:00Z"
    (workdir / "book_map.json").write_text(
        json.dumps(book_map, indent=2), encoding="utf-8"
    )
    rc, _, err = _run(
        [str(SCRIPT), "process", "--workdir", str(workdir),
         "--chapter", "ch02"],
        cwd=REPO_ROOT,
    )
    if rc != 1 or "BM-R1" not in err:
        result.fail("C6-ap-bm234", f"AP-BM2 no detectado rc={rc} err={err[:200]}")
        return
    # C6.3 AP-BM3: borrar .bak; check reporta WARN.
    state_path = workdir / "book-state.json"
    bak = state_path.with_suffix(state_path.suffix + ".bak")
    if bak.exists():
        bak.unlink()
    rc, _, out = _run(
        [str(SCRIPT), "check", "--workdir", str(workdir)],
        cwd=REPO_ROOT,
    )
    if "AP-BM3" not in out:
        result.fail("C6-ap-bm234", "AP-BM3 no reportado tras borrar .bak")
        return
    result.ok("C6-ap-bm234 (AP-BM2 detectado; AP-BM3 reportado; AP-BM4 previous_processed_at OK)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true",
                   help="regenerar fixtures antes de evaluar")
    args = p.parse_args()
    if args.regen:
        rc, _, _ = _run([str(SAMPLE_DIR / "build_fixtures.py")], cwd=REPO_ROOT)
        if rc != 0:
            sys.stderr.write("FAIL — build_fixtures.py rc != 0\n")
            return 1

    result = EvalResult()
    c1_init_blocks_process_until_map_exists(result)
    c2_ap_bm1_detects_redefinition(result)
    c3_resume_continues_without_reprocessing(result)
    c4_consolidation_every_5(result)
    c5_atomic_writes_create_bak(result)
    c6_ap_bm2_bm3_bm4(result)

    print("=" * 60)
    print("Fase 106 — Modo obra completa")
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
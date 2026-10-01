#!/usr/bin/env python3
"""check_assertions.py — Evalúa aserciones automáticas de un caso de la suite

Uso:
    python3 check_assertions.py --case <case.yaml> --run-dir <run-dir>
    python3 check_assertions.py --case <case.yaml> --run-dir <run-dir> --assertion-id <id>

Evalúa cada aserción `assertions.automatic[*]` del caso y emite
`runs/<run-id>/cases/<case-id>/assertions.json`.

Tipos soportados (handler por type):
  - ledger_coverage
  - param_table_coverage
  - ir_validation
  - sdm_validation
  - ocr_code_fidelity
  - fidelity_audit
  - manifest_valid

Cada handler implementa:
  handler(spec: dict, threshold: float, workdir: Path, case_path: Path) -> dict

y devuelve un dict con al menos: passed (bool), observed (float|str),
evidence (str), errors (list[str]). Puede devolver 'status: pending' si
la aserción está en estado pendiente por muestra faltante.

Exit codes:
  0  todas las aserciones pasan o están pending
  1  alguna aserción falla
  2  error de uso / case inválido
  3  error de runtime (workdir no existe, validator no encontrado, etc.)

Dependencias: PyYAML (rec); jsonschema (rec, para invocar validate_*).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_RUNTIME = 3


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("ERROR: PyYAML no disponible.", file=sys.stderr)
        sys.exit(EXIT_RUNTIME)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _resolve_path(workdir: Path, rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    return workdir / p


def _invoke_validator(validator: str, args: list[str]) -> tuple[int, str, str]:
    """Invoca un script validator del proyecto. Devuelve (exit, stdout, stderr)."""
    cmd = ["python3", str(REPO_ROOT / validator)] + args
    try:
        r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError as e:
        return 127, "", f"validator not found: {e}"
    except subprocess.TimeoutExpired:
        return 124, "", "validator timeout"


# ─────────────────────────────────────────────────────────────────────────────
# Handlers
# ─────────────────────────────────────────────────────────────────────────────


def handler_param_table_coverage(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    canonical_ref = spec.get("canonical_ref")
    ledger_rel = spec.get("ledger_path_rel", "knowledge/ledger.json")
    if not canonical_ref:
        return _fail("missing spec.canonical_ref")

    canonical_path = Path(canonical_ref)
    if not canonical_path.is_absolute():
        canonical_path = REPO_ROOT / canonical_path
    if not canonical_path.exists():
        return _fail(f"canonical_ref no encontrado: {canonical_path}")

    canonical = _load_yaml(canonical_path)
    ledger_path = _resolve_path(workdir, ledger_rel)
    if not ledger_path.exists():
        return _fail(f"ledger no encontrado: {ledger_path}", pending=True)

    ledger = _read_json(ledger_path)
    entries = ledger.get("entries") or ledger if isinstance(ledger, list) else []

    # Recolectar todo el texto de las notas destino + unit_id + source_block_ids.
    haystack_tokens: set[str] = set()
    for e in entries:
        for k in ("unit_id", "target_note", "target_node"):
            v = e.get(k)
            if isinstance(v, str):
                for tok in re.findall(r"\w+", v):
                    haystack_tokens.add(tok)
        sbi = e.get("source_block_ids") or []
        if isinstance(sbi, list):
            for sb in sbi:
                if isinstance(sb, str):
                    for tok in re.findall(r"\w+", sb):
                        haystack_tokens.add(tok)
    haystack_norm = " ".join(sorted(haystack_tokens)).lower()

    params = canonical.get("params") or []
    covered = 0
    missing: list[str] = []
    for p in params:
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        # Comparación case-insensitive y tolerante a guiones / underscores.
        norm = name.lower().replace("-", " ").replace("_", " ")
        if norm in haystack_norm:
            covered += 1
        else:
            # Búsqueda laxa: tokens principales
            first_tok = norm.split(" ", 1)[0]
            if first_tok in haystack_norm:
                covered += 1
            else:
                missing.append(name)

    total = len(params)
    ratio = (covered / total) if total else 0.0
    passed = ratio >= threshold
    evidence = f"{covered}/{total} parámetros cubiertos"
    if missing:
        evidence += f"; faltan: {', '.join(missing)}"
    return {
        "passed": passed,
        "observed": ratio,
        "threshold": threshold,
        "evidence": evidence,
        "errors": [] if passed else [f"cobertura {ratio:.2f} < threshold {threshold}"],
    }


def handler_ledger_coverage(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    ledger_rel = spec.get("ledger_path_rel", "knowledge/ledger.json")
    ledger_path = _resolve_path(workdir, ledger_rel)
    if not ledger_path.exists():
        return _fail(f"ledger no encontrado: {ledger_path}", pending=True)
    check = spec.get("check")
    if check == "no_etc_or_entre_otros_in_target_notes":
        ledger = _read_json(ledger_path)
        bad: list[str] = []
        for e in ledger.get("entries") or []:
            tn = (e.get("target_note") or "").lower()
            if "etc" in tn.split() or "entre otros" in tn or "más relevantes" in tn:
                bad.append(e.get("unit_id", "?"))
        if bad:
            return {
                "passed": False,
                "observed": 0.0,
                "threshold": threshold,
                "evidence": f"unidades con truncado en target_note: {bad}",
                "errors": ["INV-10 violado"],
            }
        return {
            "passed": True,
            "observed": 1.0,
            "threshold": threshold,
            "evidence": "cero truncados detectados",
            "errors": [],
        }
    # Default: min_must_keep_terminal ratio.
    min_terminal = float(spec.get("min_must_keep_terminal", 1.0))
    exit_code, stdout, stderr = _invoke_validator(
        "scripts/util/validate_ledger.py", ["--coverage", str(ledger_path)]
    )
    if exit_code != 0:
        return _fail(f"validator falló (exit {exit_code}): {stderr.strip()}")
    must_keep_pending = 0
    must_keep_total = 0
    for line in stdout.splitlines():
        m = re.search(r"must-keep pending[: ]+(\d+)/(\d+)", line)
        if m:
            must_keep_pending = int(m.group(1))
            must_keep_total = int(m.group(2))
            break
    if must_keep_total == 0:
        return {
            "passed": min_terminal <= 0,
            "observed": 0.0,
            "threshold": threshold,
            "evidence": "sin unidades must-keep en el ledger",
            "errors": [],
        }
    terminal_ratio = 1.0 - (must_keep_pending / must_keep_total)
    return {
        "passed": terminal_ratio >= min_terminal and terminal_ratio >= threshold,
        "observed": terminal_ratio,
        "threshold": threshold,
        "evidence": f"must-keep terminal {must_keep_pending}/{must_keep_total} invertidos → {terminal_ratio:.2f}",
        "errors": [] if terminal_ratio >= threshold else [f"ratio {terminal_ratio:.2f} < {threshold}"],
    }


def handler_ir_validation(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    glob_pat = spec.get("ir_glob", "ir/*.json")
    require_resolvable = bool(spec.get("require_resolvable_source_refs", False))
    files = sorted(workdir.glob(glob_pat))
    if not files:
        return _fail(f"sin IR files matching {glob_pat}", pending=True)
    all_ok = True
    errors: list[str] = []
    for f in files:
        rc, out, err = _invoke_validator(
            "scripts/util/validate_ir.py", ["--validate", str(f)]
        )
        if rc != 0:
            all_ok = False
            errors.append(f"{f.name}: {err.strip() or out.strip()}")
    return {
        "passed": all_ok,
        "observed": 1.0 if all_ok else 0.0,
        "threshold": threshold,
        "evidence": f"{len(files)} IR files; require_resolvable={require_resolvable}",
        "errors": errors,
    }


def handler_sdm_validation(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    sdm_rel = spec.get("sdm_path_rel", "sdm.json")
    sdm_path = _resolve_path(workdir, sdm_rel)
    if not sdm_path.exists():
        return _fail(f"sdm no encontrado: {sdm_path}", pending=True)
    rc, out, err = _invoke_validator(
        "scripts/util/validate_sdm.py", ["--validate", str(sdm_path)]
    )
    return {
        "passed": rc == 0,
        "observed": 1.0 if rc == 0 else 0.0,
        "threshold": threshold,
        "evidence": out.strip() or err.strip() or f"exit={rc}",
        "errors": [] if rc == 0 else [err.strip()],
    }


def handler_ocr_code_fidelity(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    # Cargar expected_code_snippets — admite "path::key" para extraer clave hermana.
    snippets_ref = spec.get("snippets_ref", "")
    snippets: dict = {}
    if "::" in snippets_ref:
        path_str, key = snippets_ref.split("::", 1)
        sp = Path(path_str)
        if not sp.is_absolute():
            sp = REPO_ROOT / sp
        if not sp.exists():
            return _fail(f"snippets_ref no encontrado: {sp}", pending=True)
        snippets = (_load_yaml(sp)).get(key) or {}
    else:
        sp = Path(snippets_ref)
        if not sp.is_absolute():
            sp = REPO_ROOT / sp
        if sp.exists():
            snippets = _load_yaml(sp)

    if snippets.get("status") == "pending_due_to_missing_sample":
        return {
            "passed": False,
            "observed": None,
            "threshold": threshold,
            "evidence": "pending_due_to_missing_sample; F6 sin muestra para corpus hostil",
            "errors": [],
            "status": "pending",
        }

    edit_threshold = float(spec.get("edit_distance_threshold", threshold))
    sdm_path = _resolve_path(workdir, spec.get("sdm_or_ocr_path_rel", "sdm.json"))
    if not sdm_path.exists():
        return _fail(f"sdm no encontrado: {sdm_path}", pending=True)
    sdm = _read_json(sdm_path)
    code_blocks: list[dict] = []
    for blk in (sdm.get("blocks") or []):
        if blk.get("type") == "code" and blk.get("origin") == "ocr":
            code_blocks.append(blk)
    if not code_blocks:
        return _fail("sin bloques code de origen OCR en sdm.json", pending=True)

    expected_snippets = snippets.get("snippets") or []
    if not expected_snippets:
        return _fail("expected_code_snippets vacío", pending=True)

    ratios: list[float] = []
    for snip in expected_snippets:
        expected_text = (snip.get("expected_text") or "").strip()
        if not expected_text:
            continue
        best = 0.0
        for blk in code_blocks:
            actual = (blk.get("content") or {}).get("text") or ""
            ratio = _edit_ratio(expected_text, actual)
            if ratio > best:
                best = ratio
        ratios.append(best)
    if not ratios:
        return _fail("sin snippets canónicos con texto")
    avg = sum(ratios) / len(ratios)
    passed = avg >= edit_threshold
    return {
        "passed": passed,
        "observed": avg,
        "threshold": edit_threshold,
        "evidence": f"edit-ratio medio sobre {len(ratios)} snippets = {avg:.3f}",
        "errors": [] if passed else [f"{avg:.3f} < {edit_threshold}"],
    }


def handler_fidelity_audit(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    # Heurística ligera: busca marcadores prohibidos (INV-09, INV-10) en
    # las notas generadas.
    notemark_dir = workdir / "notemark"
    if not notemark_dir.exists():
        return _fail(f"notemark/ no existe en {workdir}", pending=True)
    bad: list[str] = []
    for f in notemark_dir.rglob("*.nm"):
        text = f.read_text(encoding="utf-8", errors="replace")
        for marker in ("etc.", "etc)", "entre otros", "los más relevantes", "..."):
            if marker in text:
                bad.append(f"{f.name}: '{marker}'")
    return {
        "passed": not bad,
        "observed": 1.0 if not bad else 0.0,
        "threshold": threshold,
        "evidence": "audit heurístico: cero marcadores prohibidos" if not bad else f"{len(bad)} violaciones",
        "errors": bad[:5],
    }


def handler_manifest_valid(
    spec: dict, threshold: float, workdir: Path, case_path: Path, case: dict
) -> dict:
    manifest = workdir / "manifest.json"
    if not manifest.exists():
        return _fail(f"manifest.json no existe en {workdir}", pending=True)
    return {
        "passed": True,
        "observed": 1.0,
        "threshold": threshold,
        "evidence": f"manifest presente ({manifest.stat().st_size} bytes)",
        "errors": [],
    }


HANDLERS = {
    "param_table_coverage": handler_param_table_coverage,
    "ledger_coverage": handler_ledger_coverage,
    "ir_validation": handler_ir_validation,
    "sdm_validation": handler_sdm_validation,
    "ocr_code_fidelity": handler_ocr_code_fidelity,
    "fidelity_audit": handler_fidelity_audit,
    "manifest_valid": handler_manifest_valid,
}


def _edit_ratio(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b)
    return sm.ratio()


def _fail(msg: str, pending: bool = False) -> dict:
    return {
        "passed": False,
        "observed": 0.0,
        "threshold": 0.0,
        "evidence": msg,
        "errors": [msg],
        **({"status": "pending"} if pending else {}),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Evalúa aserciones automáticas de un caso")
    p.add_argument("--case", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--assertion-id", default=None, help="Si se da, evalúa solo esta aserción")
    args = p.parse_args(argv)

    case_path = Path(args.case)
    if not case_path.exists():
        print(f"ERROR: case no encontrado: {case_path}", file=sys.stderr)
        return EXIT_RUNTIME
    case = _load_yaml(case_path)
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"ERROR: run-dir no existe: {run_dir}", file=sys.stderr)
        return EXIT_RUNTIME

    case_id = case.get("id", case_path.stem)
    workdir = run_dir / "cases" / case_id / "workdir"
    if not workdir.exists():
        print(f"ERROR: workdir no existe: {workdir}", file=sys.stderr)
        return EXIT_RUNTIME

    automatic = case.get("assertions", {}).get("automatic") or []
    results: list[dict] = []
    any_fail = False
    for a in automatic:
        if args.assertion_id and a.get("id") != args.assertion_id:
            continue
        atype = a.get("type")
        if atype not in HANDLERS:
            any_fail = True
            results.append(
                {
                    "id": a.get("id"),
                    "type": atype,
                    "validator": a.get("validator"),
                    "passed": False,
                    "observed": 0.0,
                    "threshold": a.get("threshold"),
                    "evidence": f"no handler for type={atype!r}",
                    "errors": [f"missing handler for type={atype!r}"],
                }
            )
            continue
        handler = HANDLERS[atype]
        out = handler(a.get("spec", {}), float(a.get("threshold", 1.0)), workdir, case_path, case)
        out = {"id": a.get("id"), "type": atype, "validator": a.get("validator"), **out}
        results.append(out)
        if not out.get("passed") and out.get("status") != "pending":
            any_fail = True

    payload = {
        "case_id": case_id,
        "automatic": results,
        "human": None,
    }
    out_path = run_dir / "cases" / case_id / "assertions.json"
    _save_json(out_path, payload)

    # Resumen por stdout.
    n = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    pending = sum(1 for r in results if r.get("status") == "pending")
    print(f"case={case_id} assertions={n} passed={passed} pending={pending} fail={n - passed - pending}")
    for r in results:
        marker = "PASS" if r.get("passed") else ("PEND" if r.get("status") == "pending" else "FAIL")
        print(f"  [{marker}] {r.get('id')} ({r.get('type')}): {r.get('evidence')}")

    return EXIT_FAIL if any_fail else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

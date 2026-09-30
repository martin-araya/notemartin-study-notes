#!/usr/bin/env python3
"""
run_eval.py — Orchestrator for evals/validator-suite-sample.

Ejecuta la batería de validadores sobre los fixtures con defectos inyectados
y verifica:

  C1 — Detecta el 100 % de los defectos inyectados (cada fixture produce ≥ 1 issue).
  C2 — 0 issues de severidad `error` sobre los golden del repo.
  C3 — El 100 % de los issues emitidos por C1 tienen `file`, `node`, `rule_id`
       no vacíos y formato `V-<CAT>-NNN`.

Exit 0 si los 3 criterios PASS, 1 en otro caso.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HERE = Path("/Users/martin/Desktop/projects/notemartin-study-notes/skill/notemartin-study-notes/scripts/validate")
FIX = ROOT / "fixtures"
GOLDEN = ROOT / "golden"

RULE_ID_RE = re.compile(r"^V-[A-Z]+-\d+$")


def run_validator(script: str, args: list[str]) -> tuple[int, dict | None]:
    cmd = [sys.executable, str(HERE / script)] + args + ["--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, None


def run_on_dir(target_dir: Path, validator: str) -> dict:
    """Ejecuta un validador sobre un directorio de fixtures."""
    if validator in ("validate_profile", "validate_sdm", "validate_ledger", "validate_notemark",
                      "validate_links", "validate_images", "validate_properties",
                      "validate_tables", "validate_lengths"):
        # These validators take --notes-dir or --workdir
        # Find files matching the validator's pattern.
        if validator == "validate_profile":
            return run_validator("validate_profile.py", ["--notes-dir", str(target_dir)])[1] or {}
        if validator == "validate_sdm":
            return run_validator("validate_sdm.py", ["--notes-dir", str(target_dir)])[1] or {}
        if validator == "validate_ledger":
            return run_validator("validate_ledger.py", ["--notes-dir", str(target_dir)])[1] or {}
        if validator == "validate_notemark":
            return run_validator("validate_notemark.py", ["--notes-dir", str(target_dir)])[1] or {}
        if validator == "validate_links":
            return run_validator("validate_links.py", ["--notes-dir", str(target_dir)])[1] or {}
    return {}


def run_on_each(target_dir: Path, validator: str, exts: tuple[str, ...]) -> list[dict]:
    """Ejecuta un validador por cada archivo (cuando opera con --note)."""
    reports = []
    for p in sorted(target_dir.rglob("*")):
        if p.is_file() and p.suffix in exts:
            args = ["--note", str(p)]
            if validator == "validate_lengths":
                # Read note-type from frontmatter.
                text = p.read_text(encoding="utf-8")
                for ln in text.splitlines():
                    if ln.startswith("note-type:"):
                        args += ["--type", ln.split(":", 1)[1].strip()]
                        break
            _, report = run_validator(f"{validator}.py", args)
            if report:
                report["_target_file"] = str(p)
                reports.append(report)
    return reports


def collect_c1_fixtures() -> dict[str, list[Path]]:
    """Devuelve {validator_name: [fixture_dirs_or_files]}."""
    out: dict[str, list[Path]] = {}

    for cat in FIX.iterdir():
        if not cat.is_dir():
            continue
        for defect in cat.iterdir():
            if not defect.is_dir():
                continue
            v = CAT_TO_VALIDATOR.get(cat.name)
            if v:
                out.setdefault(v, []).append(defect)
    return out


CAT_TO_VALIDATOR = {
    "profile": "validate_profile",
    "sdm": "validate_sdm",
    "ledger": "validate_ledger",
    "notemark": "validate_notemark",
    "links": "validate_links",
    "images": "validate_images",
    "properties": "validate_properties",
    "tables": "validate_tables",
    "lengths": "validate_lengths",
    "destinations": "validate_destinations",
}

WORKDIR_VALIDATORS = {"validate_destinations"}
DIR_VALIDATORS = {"validate_profile", "validate_sdm", "validate_ledger"}


def check_c1() -> tuple[bool, dict]:
    """C1: 100% de defectos detectados."""
    fails = []
    total_targets = 0
    detected = 0

    for cat in FIX.iterdir():
        if not cat.is_dir():
            continue
        for defect in cat.iterdir():
            if not defect.is_dir():
                continue
            total_targets += 1
            v = CAT_TO_VALIDATOR.get(cat.name)
            if not v:
                continue
            script = f"{v}.py"
            if v in DIR_VALIDATORS:
                _, rep = run_validator(script, ["--notes-dir", str(defect)])
            elif v in WORKDIR_VALIDATORS:
                _, rep = run_validator(script, ["--workdir", str(defect)])
            else:
                # Per-file mode for note validators.
                files = sorted(
                    list(defect.rglob("*.nm")) + list(defect.rglob("*.md"))
                )
                rep = None
                for f in files:
                    if not f.is_file():
                        continue
                    args = ["--note", str(f)]
                    if v == "validate_lengths":
                        text = f.read_text(encoding="utf-8")
                        for ln in text.splitlines():
                            if ln.startswith("note-type:"):
                                args += ["--type", ln.split(":", 1)[1].strip()]
                                break
                    _, r = run_validator(script, args)
                    if r:
                        rep = r
                        break
            if rep is None:
                fails.append(f"{v} / {defect.name}: no JSON output")
                continue
            issues = rep.get("issues", [])
            real_issues = [i for i in issues if not i.get("rule_id", "").startswith("V-RUN-")]
            errs = [i for i in real_issues if i["severity"] == "error"]
            warns = [i for i in real_issues if i["severity"] == "warning"]
            if errs or warns:
                detected += 1
            else:
                fails.append(f"{v} / {defect.name}: 0 error/warning issues (esperaba ≥ 1)")

    ok = detected == total_targets and total_targets > 0
    return ok, {"total_targets": total_targets, "detected": detected, "fails": fails}


def check_c2() -> tuple[bool, dict]:
    """C2: 0 issues de severidad `error` sobre los golden."""
    fails = []
    total_golden = 0

    for golden in GOLDEN.iterdir():
        if not golden.is_file():
            continue
        total_golden += 1
        ext = golden.suffix
        if golden.name.startswith("valid-profile"):
            v = "validate_profile"
            args = ["--note", str(golden)]
        elif golden.name.startswith("valid-sdm"):
            v = "validate_sdm"
            args = ["--note", str(golden)]
        elif golden.name.startswith("valid-ledger"):
            v = "validate_ledger"
            args = ["--note", str(golden)]
        elif ext in (".md", ".nm"):
            for v in ("validate_properties", "validate_notemark", "validate_tables", "validate_lengths"):
                args = ["--note", str(golden)]
                if v == "validate_lengths":
                    text = golden.read_text(encoding="utf-8")
                    for ln in text.splitlines():
                        if ln.startswith("note-type:"):
                            args += ["--type", ln.split(":", 1)[1].strip()]
                            break
                _, rep = run_validator(f"{v}.py", args)
                if rep:
                    for it in rep.get("issues", []):
                        if it["severity"] == "error":
                            fails.append(f"{golden.name} / {v}: {it['rule_id']} {it['message']}")
            continue
        else:
            continue

        _, rep = run_validator(f"{v}.py", args)
        if rep:
            for it in rep.get("issues", []):
                if it["severity"] == "error":
                    fails.append(f"{golden.name} / {v}: {it['rule_id']} {it['message']}")

    return (not fails), {"golden": total_golden, "fails": fails}


def check_c3() -> tuple[bool, dict]:
    """C3: 100% de issues emitidos por C1 tienen shape válida."""
    fails = []
    total = 0

    for cat in FIX.iterdir():
        if not cat.is_dir():
            continue
        for defect in cat.iterdir():
            if not defect.is_dir():
                continue
            v = CAT_TO_VALIDATOR.get(cat.name)
            if not v:
                continue
            script = f"{v}.py"
            if v in DIR_VALIDATORS:
                _, rep = run_validator(script, ["--notes-dir", str(defect)])
            elif v in WORKDIR_VALIDATORS:
                _, rep = run_validator(script, ["--workdir", str(defect)])
            else:
                files = sorted(
                    list(defect.rglob("*.nm")) + list(defect.rglob("*.md"))
                )
                rep = None
                for f in files:
                    if not f.is_file():
                        continue
                    args = ["--note", str(f)]
                    if v == "validate_lengths":
                        text = f.read_text(encoding="utf-8")
                        for ln in text.splitlines():
                            if ln.startswith("note-type:"):
                                args += ["--type", ln.split(":", 1)[1].strip()]
                                break
                    _, r = run_validator(script, args)
                    if r:
                        rep = r
                        break
            if not rep:
                continue
            for it in rep.get("issues", []):
                total += 1
                if not it.get("file"):
                    fails.append(f"issue sin `file`: {it}")
                if not it.get("node"):
                    fails.append(f"issue sin `node`: {it}")
                rid = it.get("rule_id", "")
                if not RULE_ID_RE.match(rid):
                    fails.append(f"rule_id malformado: {rid!r}")

    return (not fails), {"issues_inspected": total, "fails": fails}


def main() -> int:
    print("=== C1 — Detección de defectos inyectados ===")
    c1_ok, c1 = check_c1()
    print(f"  detect={c1['detected']}/{c1['total_targets']}  PASS={c1_ok}")
    for f in c1["fails"]:
        print(f"    FAIL: {f}")

    print("\n=== C2 — 0 errores sobre los golden ===")
    c2_ok, c2 = check_c2()
    print(f"  golden={c2['golden']}  PASS={c2_ok}")
    for f in c2["fails"]:
        print(f"    FAIL: {f}")

    print("\n=== C3 — Shape válida (file, node, rule_id) ===")
    c3_ok, c3 = check_c3()
    print(f"  issues_inspected={c3['issues_inspected']}  PASS={c3_ok}")
    for f in c3["fails"][:10]:
        print(f"    FAIL: {f}")

    overall = c1_ok and c2_ok and c3_ok
    print("\n=== Summary ===")
    print(f"  C1: {'PASS' if c1_ok else 'FAIL'}")
    print(f"  C2: {'PASS' if c2_ok else 'FAIL'}")
    print(f"  C3: {'PASS' if c3_ok else 'FAIL'}")
    print(f"  Overall: {'PASS' if overall else 'FAIL'}")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
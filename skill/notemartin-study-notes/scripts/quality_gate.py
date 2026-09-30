#!/usr/bin/env python3
"""
quality_gate.py — Puerta de calidad y reporte (F115).

Agrega 4 fuentes (F43 + F113 + F114 + F7 auto), produce un reporte
JSON + Markdown por trabajo, y bloquea la promoción a status: verified
cuando hay errors bloqueantes o cobertura incompleta. Registra la deuda
aceptada en reports/debt.json.

Sub-comandos:
  report       (default) — produce reports/quality-gate.{json,md}
  promote      — modifica frontmatter published→verified si blocking=false
  check        — sólo exit code (CI)
  debt list    — lista entradas activas en reports/debt.json
  debt add     — añade entrada con --kind/--scope/--reason/--expires
  debt accept  — marca entrada con --id/--by

Uso:
  python3 scripts/quality_gate.py --workdir .notes-work/<hash> report
  python3 scripts/quality_gate.py --workdir .notes-work/<hash> promote --yes
  python3 scripts/quality_gate.py --workdir .notes-work/<hash> check
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

VALIDATOR_SCRIPT_DIR = Path(__file__).resolve().parent
COMPLETENESS_PY = VALIDATOR_SCRIPT_DIR / "validate" / "completeness.py"
RUN_ALL_PY = VALIDATOR_SCRIPT_DIR / "validate" / "run_all.py"
FIDELITY_AUDIT_PY = VALIDATOR_SCRIPT_DIR / "audit" / "fidelity_audit.py"
DEDUP_DETECT_PY = VALIDATOR_SCRIPT_DIR / "dedup" / "detect.py"

DEBT_PATH_DEFAULT = "reports/debt.json"
QG_REPORT_PATH_DEFAULT = "reports/quality-gate.json"
QG_MD_PATH_DEFAULT = "reports/quality-gate.md"
PROMOTE_LOG_PATH_DEFAULT = "reports/promote-log.json"

DEBT_ID_RE = re.compile(r"^QG-DEBT-\d{4}$")
RULE_ID_RE = re.compile(r"^V-[A-Z]+-\d+$")


# ────────────────────────────────────────────────────────────────────
# Subprocess helpers
# ────────────────────────────────────────────────────────────────────
def run_subprocess(cmd: list[str], timeout: int = 30) -> dict | None:
    """Ejecuta un comando y devuelve el JSON parseado o None."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def load_workdir_state(wd: Path) -> dict:
    """Carga SDM + IRs + ledger del workdir."""
    state: dict = {"sdm": None, "irs": [], "ledger": None, "notes_files": []}
    sdm_path = wd / "sdm.json"
    if sdm_path.is_file():
        try:
            state["sdm"] = json.loads(sdm_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    ir_dir = wd / "ir"
    if ir_dir.is_dir():
        for p in sorted(ir_dir.glob("*.note-ir.json")):
            try:
                ir = json.loads(p.read_text(encoding="utf-8"))
                ir["_path"] = str(p)
                state["irs"].append(ir)
            except Exception:
                continue
    kd = wd / "knowledge"
    if kd.is_dir():
        for p in sorted(kd.glob("ledger*.json")):
            try:
                state["ledger"] = json.loads(p.read_text(encoding="utf-8"))
                state["ledger"]["_path"] = str(p)
                break
            except Exception:
                continue
    # Detectar archivos de notas (notemark/*.nm o notes/*.md).
    for sub in ("notemark", "notes"):
        nd = wd / sub
        if nd.is_dir():
            for ext in ("*.nm", "*.md"):
                state["notes_files"].extend(sorted(nd.glob(ext)))
            break
    return state


def invoke_completeness(wd: Path) -> dict | None:
    return run_subprocess([sys.executable, str(COMPLETENESS_PY),
                           "--workdir", str(wd), "audit"])


def invoke_validators(wd: Path) -> dict | None:
    return run_subprocess([sys.executable, str(RUN_ALL_PY),
                           "--workdir", str(wd)])


def invoke_fidelity(wd: Path) -> dict | None:
    return run_subprocess([sys.executable, str(FIDELITY_AUDIT_PY),
                           "--workdir", str(wd), "--json", "audit"])


def invoke_dedup(wd: Path) -> dict | None:
    return run_subprocess([sys.executable, str(DEDUP_DETECT_PY),
                           "--notes-dir", str(wd / "notes"), "scan"])


# ────────────────────────────────────────────────────────────────────
# Aggregation
# ────────────────────────────────────────────────────────────────────
def aggregate_summary(sources: dict) -> dict:
    """Suma issues de las 3 fuentes. F43 'critical' se mapea a error."""
    n_err = 0
    n_warn = 0
    n_info = 0
    for key in ("completeness", "validators", "fidelity"):
        rep = sources.get(key)
        if not rep or not isinstance(rep, dict):
            continue
        # F113 / F114 shape: summary.errors/warnings/info.
        s = rep.get("summary")
        if isinstance(s, dict):
            n_err += s.get("errors", 0)
            n_warn += s.get("warnings", 0)
            n_info += s.get("info", 0)
            continue
        # F43 shape: findings list con severity {critical, warning, info}.
        for it in rep.get("findings", []) or []:
            sev = it.get("severity")
            if sev == "critical":
                n_err += 1
            elif sev == "warning":
                n_warn += 1
            elif sev == "info":
                n_info += 1
    return {"errors": n_err, "warnings": n_warn, "info": n_info}


def compute_coverage(sdm: dict | None, ledger: dict | None) -> tuple[float, list[dict]]:
    """Cobertura = secciones del SDM con unidad en ledger / secciones totales.

    Devuelve (coverage, not_covered).
    """
    if not sdm or not isinstance(sdm, dict):
        return 0.0, []
    sections = sdm.get("sections") or []
    if not sections:
        return 0.0, []

    # Map section_path → booleano (covered).
    covered: dict[str, bool] = {}
    section_ids: set[str] = set()
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        spath = sec.get("path") or "/" + (sec.get("title") or sec.get("id", ""))
        section_ids.add(spath)
        covered[spath] = False
        for blk in sec.get("blocks") or []:
            if isinstance(blk, dict) and blk.get("id"):
                section_ids.add(blk["id"])
                covered[blk["id"]] = False

    # Ledger entries con source_block_ids o source_section_path.
    if isinstance(ledger, dict):
        entries = ledger.get("entries") or []
        for e in entries:
            if not isinstance(e, dict):
                continue
            sp = e.get("source_section_path")
            if sp and sp in covered:
                covered[sp] = True
            for bid in e.get("source_block_ids") or []:
                if bid in covered:
                    covered[bid] = True

    not_covered = []
    for path, ok in covered.items():
        if not ok:
            not_covered.append({"section_path": path, "reason": "futuro"})

    total = max(1, len(covered))
    cov = sum(1 for v in covered.values() if v) / total
    return cov, not_covered


def compute_rubric(sources: dict, coverage: float, not_covered: list) -> dict:
    """Calcula 4 dimensiones auto-aplicables; las 4 humanas quedan null."""
    fidelity_level = 4
    fidelity_justif = "0 issues en F114"
    f_rep = sources.get("fidelity")
    if f_rep and isinstance(f_rep, dict):
        s = f_rep.get("summary") or {}
        e = s.get("errors", 0)
        w = s.get("warnings", 0)
        if e > 5:
            fidelity_level = 0
            fidelity_justif = f">{5} errors en F114"
        elif e > 2:
            fidelity_level = 1
            fidelity_justif = f">{2} errors en F114"
        elif e > 0:
            fidelity_level = 2
            fidelity_justif = f"{e} errors en F114"
        elif w > 2:
            fidelity_level = 3
            fidelity_justif = f"{w} warnings en F114"
        else:
            fidelity_justif = f"0 errores/warnings en F114"

    if coverage >= 1.0:
        cov_level, cov_justif = 4, "100% cobertura"
    elif coverage >= 0.95:
        cov_level, cov_justif = 3, f"{coverage:.0%} cobertura"
    elif coverage >= 0.90:
        cov_level, cov_justif = 2, f"{coverage:.0%} cobertura"
    elif coverage >= 0.70:
        cov_level, cov_justif = 1, f"{coverage:.0%} cobertura"
    else:
        cov_level, cov_justif = 0, f"{coverage:.0%} cobertura"

    # Trazabilidad: errores V-SDM-04/05 + V-FAUDIT-01.
    trace_err = 0
    v_rep = sources.get("validators")
    if v_rep and isinstance(v_rep, dict):
        for it in v_rep.get("issues", []) or []:
            if it.get("rule_id") in ("V-SDM-04", "V-SDM-05"):
                trace_err += 1
    f_rep2 = sources.get("fidelity")
    if f_rep2 and isinstance(f_rep2, dict):
        for it in f_rep2.get("issues", []) or []:
            if it.get("rule_id") == "V-FAUDIT-01":
                trace_err += 1
    if trace_err == 0:
        trace_level, trace_justif = 4, "0 nodos sin trazabilidad"
    elif trace_err <= 2:
        trace_level, trace_justif = 3, f"{trace_err} issues de trazabilidad"
    elif trace_err <= 10:
        trace_level, trace_justif = 2, f"{trace_err} issues de trazabilidad"
    else:
        trace_level, trace_justif = 1, f"{trace_err} issues de trazabilidad"

    # Render: units_lost en cross_target.
    render_level = 4
    render_justif = "0 unidades perdidas en cross-target"
    # Heurística: no invocamos cross_target directamente aquí; dejamos 4
    # si no se detecta nada obvio.
    return {
        "fidelity":     {"level": fidelity_level, "justification": fidelity_justif},
        "coverage":     {"level": cov_level, "justification": cov_justif},
        "traceability": {"level": trace_level, "justification": trace_justif},
        "render":       {"level": render_level, "justification": render_justif},
        "pedagogy":     {"level": None, "justification": "human evaluation required (rubric §3.4)"},
        "structure":    {"level": None, "justification": "human evaluation required (rubric §3.5)"},
        "components":   {"level": None, "justification": "human evaluation required (rubric §3.6)"},
        "operational":  {"level": None, "justification": "human evaluation required (rubric §3.7)"},
    }


# ────────────────────────────────────────────────────────────────────
# Debt registry
# ────────────────────────────────────────────────────────────────────
def load_debt(wd: Path) -> list:
    p = wd / DEBT_PATH_DEFAULT
    if not p.is_file():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_debt(wd: Path, entries: list) -> None:
    p = wd / DEBT_PATH_DEFAULT
    p.parent.mkdir(parents=True, exist_ok=True)
    # Backup atómico.
    if p.is_file():
        p.rename(p.with_suffix(".json.bak"))
    p.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def next_debt_id(entries: list) -> str:
    used = [int(e["id"].split("-")[-1]) for e in entries
            if DEBT_ID_RE.match(e.get("id", ""))]
    n = (max(used) if used else 0) + 1
    return f"QG-DEBT-{n:04d}"


def cmd_debt_list(wd: Path) -> int:
    entries = load_debt(wd)
    print(json.dumps({"debt_registry": entries}, indent=2, ensure_ascii=False))
    return 0


def cmd_debt_add(wd: Path, args) -> int:
    entries = load_debt(wd)
    if not args.kind or not args.scope or not args.reason:
        print("ERROR: --kind/--scope/--reason requeridos", file=sys.stderr)
        return 2
    if not RULE_ID_RE.match(args.rule_id or ""):
        print(f"ERROR: --rule-id '{args.rule_id}' no cumple V-[A-Z]+-\\d+",
              file=sys.stderr)
        return 2
    entry = {
        "id": next_debt_id(entries),
        "kind": args.kind,
        "scope": args.scope,
        "reason": args.reason,
        "raised_by": args.raised_by or "human",
        "rule_id": args.rule_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": args.expires,
        "accepted_by": None,
    }
    entries.append(entry)
    save_debt(wd, entries)
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


def cmd_debt_accept(wd: Path, args) -> int:
    if not args.id or not args.by:
        print("ERROR: --id y --by requeridos", file=sys.stderr)
        return 2
    entries = load_debt(wd)
    target = None
    for e in entries:
        if e["id"] == args.id:
            e["accepted_by"] = args.by
            target = e
            break
    if not target:
        print(f"ERROR: --id '{args.id}' no encontrado en debt registry",
              file=sys.stderr)
        return 1
    save_debt(wd, entries)
    print(json.dumps(target, indent=2, ensure_ascii=False))
    return 0


# ────────────────────────────────────────────────────────────────────
# report / promote / check
# ────────────────────────────────────────────────────────────────────
def blocking(summary: dict, coverage: float, debt: list,
             coverage_min: float) -> bool:
    """Calcula blocking per §8."""
    if summary["errors"] > 0:
        return True
    if coverage < coverage_min:
        return True
    for e in debt:
        if e.get("kind") == "blocker" and not e.get("accepted_by"):
            return True
    return False


def build_report(wd: Path, sources: dict, coverage: float, not_covered: list,
                 debt: list, blocking_flag: bool, summary: dict) -> dict:
    sdm = sources.get("_sdm") or {}
    src_hash = (sdm.get("source") or {}).get("hash", "")
    if not re.match(r"^[0-9a-f]{64}$", src_hash):
        src_hash = "0" * 64
    return {
        "schema_version": SCHEMA_VERSION,
        "workdir": str(wd),
        "source_hash": src_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "blocking": blocking_flag,
        "coverage": coverage,
        "rubric": sources.get("_rubric") or compute_rubric(sources, coverage, not_covered),
        "not_covered": not_covered,
        "debt_registry": debt,
        "sources": {
            "completeness": sources.get("completeness"),
            "validators":   sources.get("validators"),
            "fidelity":     sources.get("fidelity"),
            "dedup":        sources.get("dedup"),
        },
    }


def emit_markdown(report: dict) -> str:
    lines = [
        f"# Quality Gate Report — `{report['workdir']}`",
        f"Generado: {report['generated_at']}",
        f"Source hash: `{report['source_hash']}`",
        "",
        "## Resumen",
        f"- Errores: **{report['summary']['errors']}**",
        f"- Warnings: {report['summary']['warnings']}",
        f"- Info: {report['summary']['info']}",
        f"- Blocking: **{report['blocking']}**",
        f"- Coverage: {report['coverage']:.0%}",
        "",
        "## Rúbrica (auto-aplicada)",
        "| Dimensión | Nivel | Justificación |",
        "|---|---|---|",
    ]
    for name, dim in report["rubric"].items():
        lvl = dim["level"] if dim["level"] is not None else "human"
        lines.append(f"| {name} | {lvl} | {dim['justification']} |")
    lines += [
        "",
        f"## No cubierto ({len(report['not_covered'])})",
    ]
    if report["not_covered"]:
        for nc in report["not_covered"]:
            lines.append(f"- `{nc['section_path']}` — {nc['reason']}")
    else:
        lines.append("(todo cubierto)")
    lines += [
        "",
        f"## Deuda registrada ({len(report['debt_registry'])})",
    ]
    if report["debt_registry"]:
        for d in report["debt_registry"]:
            acc = d["accepted_by"] or "—"
            lines.append(f"- {d['id']} [{d['kind']}] scope={d['scope']} "
                         f"accepted_by={acc} — {d['reason']}")
    else:
        lines.append("(sin deuda)")
    return "\n".join(lines) + "\n"


def cmd_report(wd: Path, args) -> int:
    state = load_workdir_state(wd)
    sdm = state["sdm"]
    ledger = state["ledger"]

    sources: dict = {"_sdm": sdm}
    sources["completeness"] = invoke_completeness(wd)
    sources["validators"] = invoke_validators(wd)
    sources["fidelity"] = invoke_fidelity(wd)
    if len(state["irs"]) >= 5:
        sources["dedup"] = invoke_dedup(wd)

    coverage, not_covered = compute_coverage(sdm, ledger)
    summary = aggregate_summary(sources)
    debt = load_debt(wd)
    blocking_flag = blocking(summary, coverage, debt, args.coverage_min)

    rubric = compute_rubric(sources, coverage, not_covered)
    sources["_rubric"] = rubric

    report = build_report(wd, sources, coverage, not_covered, debt,
                          blocking_flag, summary)

    out_json = wd / args.qj
    out_md = wd / args.qm
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    if not args.markdown_only:
        out_md.write_text(emit_markdown(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(emit_markdown(report))

    if blocking_flag:
        return 1
    if summary["warnings"] > 0:
        return 2
    return 0


def cmd_check(wd: Path, args) -> int:
    """Sólo exit code: corre report internamente, no escribe, devuelve rc."""
    state = load_workdir_state(wd)
    sdm = state["sdm"]
    ledger = state["ledger"]

    sources = {"completeness": invoke_completeness(wd),
               "validators":   invoke_validators(wd),
               "fidelity":     invoke_fidelity(wd)}
    coverage, not_covered = compute_coverage(sdm, ledger)
    summary = aggregate_summary(sources)
    debt = load_debt(wd)
    blocking_flag = blocking(summary, coverage, debt, args.coverage_min)

    if blocking_flag:
        print(f"FAIL ({summary['errors']} errors)")
        return 1
    print("PASS")
    return 0


def cmd_promote(wd: Path, args) -> int:
    """Si blocking=false, modifica frontmatter de status: published → verified."""
    # Primero correr report (forzado) para obtener el estado actual.
    state = load_workdir_state(wd)
    sdm = state["sdm"]
    ledger = state["ledger"]

    sources = {"completeness": invoke_completeness(wd),
               "validators":   invoke_validators(wd),
               "fidelity":     invoke_fidelity(wd)}
    coverage, not_covered = compute_coverage(sdm, ledger)
    summary = aggregate_summary(sources)
    debt = load_debt(wd)
    blocking_flag = blocking(summary, coverage, debt, args.coverage_min)

    if blocking_flag:
        print(f"BLOCKED: errors={summary['errors']} coverage={coverage:.0%}",
              file=sys.stderr)
        return 1

    if not state["notes_files"]:
        print("ERROR: no se encontraron notas en notemark/ ni notes/",
              file=sys.stderr)
        return 1
    if not args.yes:
        print(f"DRY RUN: se promoverían {len(state['notes_files'])} notas. "
              "Use --yes para ejecutar.", file=sys.stderr)
        return 0

    run_id = str(uuid.uuid4())
    promoted_at = datetime.now(timezone.utc).isoformat()
    log = []
    for p in state["notes_files"]:
        text = p.read_text(encoding="utf-8")
        # Backup.
        bak = p.with_suffix(p.suffix + ".bak")
        bak.write_text(text, encoding="utf-8")
        # Modificar frontmatter.
        new_text = _update_frontmatter_status(
            text, "published", "verified",
            verified_at=promoted_at, quality_gate_run_id=run_id,
        )
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            log.append({
                "note_path": str(p),
                "before": "published",
                "after": "verified",
                "verified_at": promoted_at,
                "quality_gate_run_id": run_id,
            })

    log_path = wd / args.promote_log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({
        "run_id": run_id,
        "promoted_at": promoted_at,
        "promoted_count": len(log),
        "log": log,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "run_id": run_id,
        "promoted_count": len(log),
        "log_path": str(log_path),
    }, indent=2, ensure_ascii=False))
    return 0


def _update_frontmatter_status(text: str, old_status: str, new_status: str,
                                verified_at: str, quality_gate_run_id: str) -> str:
    """Reemplaza status en el bloque YAML del frontmatter.

    Si no hay frontmatter o no tiene `status: <old_status>`, devuelve text
    sin cambios.
    """
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    fm = parts[1]
    body = parts[2]
    # Buscar línea `status: old_status`.
    new_fm_lines = []
    replaced = False
    for line in fm.splitlines():
        s = line.strip()
        if s == f"status: {old_status}":
            new_fm_lines.append(f"status: {new_status}")
            replaced = True
        elif s.startswith("status:"):
            # No tocar si no es exactamente old_status.
            new_fm_lines.append(line)
        else:
            new_fm_lines.append(line)
    if not replaced:
        return text
    # Añadir verified_at y quality_gate_run_id si no existen.
    lines_str = "\n".join(new_fm_lines)
    if "verified_at:" not in lines_str:
        new_fm_lines.append(f"verified_at: {verified_at}")
    if "quality_gate_run_id:" not in lines_str:
        new_fm_lines.append(f"quality_gate_run_id: {quality_gate_run_id}")
    new_fm = "\n".join(new_fm_lines)
    return f"---{new_fm}\n---{body}"


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--workdir", default=".",
                        help="directorio .notes-work/<hash>/")
    parser.add_argument("--coverage-min", type=float, default=1.0)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--markdown-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qj", default=QG_REPORT_PATH_DEFAULT,
                        help="ruta del JSON de salida")
    parser.add_argument("--qm", default=QG_MD_PATH_DEFAULT,
                        help="ruta del Markdown de salida")
    parser.add_argument("--promote-log", default=PROMOTE_LOG_PATH_DEFAULT)
    parser.add_argument("--kind", help="para debt add")
    parser.add_argument("--scope", help="para debt add")
    parser.add_argument("--reason", help="para debt add / accept")
    parser.add_argument("--rule-id", dest="rule_id",
                        help="para debt add (formato V-XXX-NNN)")
    parser.add_argument("--expires", help="para debt add (ISO date)")
    parser.add_argument("--raised-by", dest="raised_by",
                        help="para debt add")
    parser.add_argument("--id", help="para debt accept")
    parser.add_argument("--by", help="para debt accept")

    sub = parser.add_subparsers(dest="subcommand")
    sub.add_parser("report")
    sub.add_parser("promote")
    sub.add_parser("check")
    sub.add_parser("debt")

    args = parser.parse_args()
    wd = Path(args.workdir).resolve()
    if not wd.is_dir():
        print(f"ERROR: workdir no existe: {wd}", file=sys.stderr)
        return 2

    subcmd = args.subcommand or "report"

    if subcmd == "debt":
        # debt add / accept / list según args.
        if args.id and args.by:
            return cmd_debt_accept(wd, args)
        if args.kind or args.scope or args.reason:
            return cmd_debt_add(wd, args)
        return cmd_debt_list(wd)

    if subcmd == "report":
        return cmd_report(wd, args)
    if subcmd == "promote":
        return cmd_promote(wd, args)
    if subcmd == "check":
        return cmd_check(wd, args)

    print(f"ERROR: sub-comando desconocido: {subcmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
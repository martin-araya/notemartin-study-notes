#!/usr/bin/env python3
"""
fidelity_audit.py — Auditoría semántica automatizada de fidelidad (F114).

Tres pasadas:
  1. Forward source-check  (R-FAUDIT-01) — nodos fácticos sin respaldo.
  2. Content-fidelity check (R-FAUDIT-02) — valores inventados contra SDM.
  3. Inverse sample       (R-FAUDIT-03) — bloques SDM must-keep no cubiertos.

Modos:
  --note <note-ir.json>      un IR.
  --notes-dir <dir>          carpeta de IRs.
  --workdir <dir>            autodetecta ir/ + sdm.json.

CLI:
  audit      (default) — 3 pasadas + threshold gate, salida JSON.
  report     — formato humano.
  check --strict — aborta al primer error.
  fix        — lista accionable sola.

Exit: 0 PASS, 1 FAIL (≥1 error), 2 uso, 3 error IO.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0.0"

# Nodos fácticos (deben tener source_refs si external/derived = false).
FACTUAL_NODES = {
    "paragraph", "list", "code", "table", "equation", "figure",
    "definition_list",
}

# Tipos de bloque SDM must-keep (F37).
MUST_KEEP_TYPES = {"parameter", "default", "error-code", "version-note", "syntax-rule"}

# Severidades editorial_note críticas (F35).
EDITORIAL_CRITICAL = {"deprecated", "removed", "novelty"}

ID_RE = re.compile(r"^[0-9a-f]{12}$")


# ────────────────────────────────────────────────────────────────────
# Pasada 1 — ForwardSourceCheck
# ────────────────────────────────────────────────────────────────────
class ForwardSourceCheck:
    """Detecta nodos IR fácticos con source_refs vacío y external/derived = false."""

    def __init__(self, issues: list):
        self.issues = issues

    def check(self, ir: dict, ir_path: Path) -> None:
        rel = str(ir_path)
        nid = ir.get("note_id") or ir_path.stem
        for node in ir.get("nodes") or ir.get("blocks") or []:
            if not isinstance(node, dict):
                continue
            node_type = node.get("node") or node.get("type") or ""
            if node_type not in FACTUAL_NODES:
                continue
            external = bool(node.get("external"))
            derived = bool(node.get("derived"))
            src = node.get("source_refs") or []
            if external or derived:
                continue
            if not src:
                self.issues.append({
                    "rule_id": "V-FAUDIT-01",
                    "severity": "error",
                    "message": f"nodo fáctico `{node_type}` sin source_refs",
                    "file": rel,
                    "node": f"{nid}.{node.get('id', '')}",
                    "fix_hint": "añade source_refs desde el SDM o marca external/derived",
                })


# ────────────────────────────────────────────────────────────────────
# Pasada 2 — ContentFidelityCheck
# ────────────────────────────────────────────────────────────────────
class ContentFidelityCheck:
    """Detecta valores inventados comparando contra SDM.

    Búsqueda literal: lowercase + whitespace collapsed sobre el texto
    del SDM (concatenación de todos los `content.text`).
    """

    def __init__(self, sdm_text: str, issues: list):
        self.sdm_text = sdm_text
        self.sdm_norm = _normalize(sdm_text)
        self.issues = issues

    def _in_sdm(self, value: str) -> bool:
        return _normalize(value) in self.sdm_norm

    def check(self, ir: dict, ir_path: Path) -> None:
        rel = str(ir_path)
        nid = ir.get("note_id") or ir_path.stem
        for node in ir.get("nodes") or ir.get("blocks") or []:
            if not isinstance(node, dict):
                continue
            attrs = node.get("attrs") or {}

            # V-FAUDIT-02 valor numérico sin unidad.
            val = attrs.get("value")
            if val is not None and isinstance(val, (int, float)):
                unit = attrs.get("unit")
                if unit in (None, ""):
                    self.issues.append({
                        "rule_id": "V-FAUDIT-02",
                        "severity": "warning",
                        "message": f"valor numérico {val} sin unidad",
                        "file": rel,
                        "node": f"{nid}.{node.get('id', '')}",
                        "fix_hint": "añade attrs.unit (bytes, ms, MB, etc.)",
                    })

            node_type = node.get("node") or node.get("type") or ""

            # V-FAUDIT-03 parameter.name / syntax-rule.rule inventados.
            if node_type == "parameter" or "parameter" in node_type:
                name = attrs.get("name")
                if name and not self._in_sdm(name):
                    self.issues.append({
                        "rule_id": "V-FAUDIT-03",
                        "severity": "error",
                        "message": f"parameter.name inventado: {name!r}",
                        "file": rel,
                        "node": f"{nid}.{node.get('id', '')}",
                        "fix_hint": "verifica que el nombre aparece en el SDM",
                    })
            elif "syntax" in node_type:
                rule = attrs.get("rule")
                if rule and not self._in_sdm(rule):
                    self.issues.append({
                        "rule_id": "V-FAUDIT-03",
                        "severity": "error",
                        "message": f"syntax-rule inventada: {rule[:40]!r}...",
                        "file": rel,
                        "node": f"{nid}.{node.get('id', '')}",
                        "fix_hint": "verifica que la regla aparece en el SDM",
                    })

            # V-FAUDIT-04 error-code.code inventado.
            if node_type == "error-code" or "error-code" in node_type:
                code = attrs.get("code")
                if code and not self._in_sdm(code):
                    self.issues.append({
                        "rule_id": "V-FAUDIT-04",
                        "severity": "error",
                        "message": f"error-code inventado: {code!r}",
                        "file": rel,
                        "node": f"{nid}.{node.get('id', '')}",
                        "fix_hint": "verifica que el código aparece en el SDM",
                    })

            # V-FAUDIT-05 version-note sin version_introduced/removed.
            if "version" in node_type:
                vi = attrs.get("version_introduced")
                vr = attrs.get("version_removed")
                if not vi and not vr:
                    self.issues.append({
                        "rule_id": "V-FAUDIT-05",
                        "severity": "warning",
                        "message": "version-note sin version_introduced ni version_removed",
                        "file": rel,
                        "node": f"{nid}.{node.get('id', '')}",
                        "fix_hint": "declara al menos una versión",
                    })


# ────────────────────────────────────────────────────────────────────
# Pasada 3 — InverseSampler
# ────────────────────────────────────────────────────────────────────
class InverseSampler:
    """Muestreo estratificado del SDM; verifica cobertura en IRs."""

    def __init__(self, sdm: dict, irs: list, sample_rate: float, seed: int,
                 issues: list):
        self.sdm = sdm
        self.irs = irs
        self.sample_rate = sample_rate
        self.seed = seed
        self.issues = issues
        self.sd_rng = random.Random(seed)

    def _all_block_ids_in_irs(self) -> set[str]:
        """Conjunto de block_ids referenciados por algún IR."""
        ids: set[str] = set()
        for ir in self.irs:
            for node in ir.get("nodes") or ir.get("blocks") or []:
                if not isinstance(node, dict):
                    continue
                for ref in node.get("source_refs") or []:
                    if isinstance(ref, dict):
                        bid = ref.get("block_id")
                        if bid and ID_RE.match(bid):
                            ids.add(bid)
        return ids

    def run(self) -> dict:
        must_keep_blocks = []
        editorial_blocks = []
        context_blocks = []
        sections = self.sdm.get("sections") or []
        for sec in sections:
            for blk in (sec.get("blocks") or []):
                if not isinstance(blk, dict):
                    continue
                ctype = (blk.get("content") or {}).get("type")
                severity = (blk.get("editorial_note") or {}).get("severity")
                if ctype in MUST_KEEP_TYPES:
                    must_keep_blocks.append(blk)
                elif severity in EDITORIAL_CRITICAL:
                    editorial_blocks.append(blk)
                else:
                    context_blocks.append(blk)

        sampled = list(must_keep_blocks) + list(editorial_blocks)
        if context_blocks:
            rate = self.sample_rate
            # R-FAUDIT-03: si SDM < 10 bloques, sube a 1.0.
            if len(context_blocks) < 10:
                rate = 1.0
            k = max(1, int(len(context_blocks) * rate))
            sampled += self.sd_rng.sample(context_blocks, min(k, len(context_blocks)))

        covered_ids = self._all_block_ids_in_irs()
        for blk in sampled:
            bid = blk.get("id")
            if not bid or not ID_RE.match(bid):
                continue
            if bid in covered_ids:
                continue
            ctype = (blk.get("content") or {}).get("type")
            is_must = ctype in MUST_KEEP_TYPES
            sev = "error" if is_must else "warning"
            self.issues.append({
                "rule_id": "V-FAUDIT-06",
                "severity": sev,
                "message": f"bloque SDM {ctype or 'context'} no cubierto en IR: {bid}",
                "file": str(self.sdm.get("_path") or "sdm.json"),
                "node": f"sdm.{bid}",
                "fix_hint": f"añade source_refs en algún IR con block_id={bid}",
            })

        return {
            "seed": self.seed,
            "sample_rate": self.sample_rate,
            "must_keep_sampled": len(must_keep_blocks),
            "editorial_sampled": len(editorial_blocks),
            "context_sampled": len(sampled) - len(must_keep_blocks) - len(editorial_blocks),
            "total_sampled": len(sampled),
        }


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _sdm_text(sdm: dict) -> str:
    parts: list[str] = []
    for sec in sdm.get("sections") or []:
        for blk in (sec.get("blocks") or []):
            if not isinstance(blk, dict):
                continue
            content = blk.get("content") or {}
            if isinstance(content, dict):
                t = content.get("text") or content.get("code") or ""
                if isinstance(t, str):
                    parts.append(t)
    return "\n".join(parts)


def load_workdir(wd: Path) -> tuple[dict | None, list[dict], list[Path]]:
    sdm = None
    sdm_path = wd / "sdm.json"
    if sdm_path.is_file():
        sdm = json.loads(sdm_path.read_text(encoding="utf-8"))
        if isinstance(sdm, dict):
            sdm["_path"] = str(sdm_path)
    irs: list[dict] = []
    ir_paths: list[Path] = []
    ir_dir = wd / "ir"
    if ir_dir.is_dir():
        for p in sorted(ir_dir.glob("*.note-ir.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            d["_path"] = str(p)
            irs.append(d)
            ir_paths.append(p)
    return sdm, irs, ir_paths


def collect_targets(args) -> tuple[list[Path], Path | None]:
    if args.note:
        return [Path(args.note)], None
    if args.notes_dir:
        d = Path(args.notes_dir)
        return sorted(list(d.rglob("*.note-ir.json")) + list(d.rglob("*.json"))), None
    wd = Path(args.workdir)
    _, _, ir_paths = load_workdir(wd)
    return ir_paths, wd


# ────────────────────────────────────────────────────────────────────
# Report builder (shape F113 §3.1)
# ────────────────────────────────────────────────────────────────────
def build_report(target: str, issues: list, started: datetime, duration_ms: int,
                 sample_metadata: dict | None = None) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "validator": "fidelity_audit",
        "target": target,
        "started_at": started.isoformat(),
        "duration_ms": duration_ms,
        "summary": {
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        },
        "sample_metadata": sample_metadata,
        "issues": issues,
    }


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────
def run_audit(args) -> tuple[int, dict]:
    started = datetime.now(timezone.utc)
    issues: list = []
    sdm: dict | None = None
    sdm_text = ""
    irs: list[dict] = []
    target_label = ""

    if args.workdir:
        wd = Path(args.workdir)
        sdm, irs, _ = load_workdir(wd)
        if sdm:
            sdm_text = _sdm_text(sdm)
        target_label = str(wd)
    elif args.note:
        p = Path(args.note)
        ir = json.loads(p.read_text(encoding="utf-8"))
        ir["_path"] = str(p)
        irs = [ir]
        target_label = str(p)
        if args.sdm:
            sp = Path(args.sdm)
            sdm = json.loads(sp.read_text(encoding="utf-8"))
            sdm_text = _sdm_text(sdm)
    elif args.notes_dir:
        d = Path(args.notes_dir)
        irs = []
        for p in sorted(list(d.rglob("*.note-ir.json"))):
            ir = json.loads(p.read_text(encoding="utf-8"))
            ir["_path"] = str(p)
            irs.append(ir)
        target_label = str(d)
        if args.sdm:
            sdm = json.loads(Path(args.sdm).read_text(encoding="utf-8"))
            sdm_text = _sdm_text(sdm)

    if not irs:
        issues.append({
            "rule_id": "V-FAUDIT-99",
            "severity": "info",
            "message": "no se encontraron IRs",
            "file": target_label, "node": "<root>",
        })
        return 1, build_report(target_label, issues, started, 0)

    # Pasada 1: forward source-check por IR.
    fwd = ForwardSourceCheck(issues)
    for ir in irs:
        fwd.check(ir, Path(ir["_path"]))

    # Pasada 2: content-fidelity por IR.
    if sdm_text:
        cfc = ContentFidelityCheck(sdm_text, issues)
        for ir in irs:
            cfc.check(ir, Path(ir["_path"]))
    else:
        issues.append({
            "rule_id": "V-FAUDIT-99",
            "severity": "warning",
            "message": "no hay SDM; saltando Pasada 2 (content-fidelity)",
            "file": target_label, "node": "<root>",
        })

    # Pasada 3: inverse sample.
    sample_metadata = None
    if sdm:
        sampler = InverseSampler(sdm, irs, args.sample_rate, args.seed, issues)
        sample_metadata = sampler.run()
    else:
        issues.append({
            "rule_id": "V-FAUDIT-99",
            "severity": "warning",
            "message": "no hay SDM; saltando Pasada 3 (inverse sample)",
            "file": target_label, "node": "<root>",
        })

    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    report = build_report(target_label, issues, started, duration_ms, sample_metadata)

    if args.strict and any(i["severity"] == "warning" for i in issues):
        return 1, report
    if any(i["severity"] == "error" for i in issues):
        return 1, report
    if any(i["severity"] == "warning" for i in issues):
        return 2, report
    return 0, report


def emit_text_report(report: dict) -> str:
    lines = [f"fidelity_audit — {report['target']}",
             f"summary: {report['summary']}",
             ""]
    if report.get("sample_metadata"):
        sm = report["sample_metadata"]
        lines.append(f"sample_metadata: seed={sm['seed']} rate={sm['sample_rate']} "
                     f"must_keep={sm['must_keep_sampled']} editorial={sm['editorial_sampled']} "
                     f"context={sm['context_sampled']}")
        lines.append("")
    for it in report.get("issues", []):
        lines.append(f"  [{it['severity'].upper():7}] {it['rule_id']} {it['file']} — {it['message']}")
    if not report.get("issues"):
        lines.append("  (sin issues)")
    return "\n".join(lines)


def emit_fix_report(report: dict) -> str:
    lines = [f"Lista accionable — {report['target']}", ""]
    for it in report.get("issues", []):
        lines.append(f"- {it['rule_id']} [{it['severity']}] {it['file']}:{it['node']}")
        lines.append(f"    {it['message']}")
        if it.get("fix_hint"):
            lines.append(f"    fix: {it['fix_hint']}")
    if not report.get("issues"):
        lines.append("(sin issues)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--note")
    grp.add_argument("--notes-dir")
    grp.add_argument("--workdir")
    parser.add_argument("--sdm", help="ruta explícita al sdm.json (modo --note/--notes-dir)")
    parser.add_argument("--irs-dir", help="carpeta de IRs (modo --workdir)")
    parser.add_argument("--sample-rate", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", help="ruta del JSON de salida")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 ante cualquier warning")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")

    sub = parser.add_subparsers(dest="subcommand")
    sub.add_parser("audit")
    sub.add_parser("report")
    sub.add_parser("check")
    sub.add_parser("fix")
    args = parser.parse_args()

    if not any([args.note, args.notes_dir, args.workdir]):
        print("ERROR: especifica --note, --notes-dir o --workdir", file=sys.stderr)
        return 2

    rc, report = run_audit(args)

    subcmd = args.subcommand or "audit"
    if subcmd == "report":
        print(emit_text_report(report))
    elif subcmd == "fix":
        print(emit_fix_report(report))
    else:
        # audit / check — siempre JSON cuando hay --out o --json o cuando
        # el subcomando es check. Para `audit` (default), texto humano
        # breve a menos que se pida --json.
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
        elif args.json or subcmd == "check":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            if not args.quiet:
                print(emit_text_report(report))

    return rc


if __name__ == "__main__":
    sys.exit(main())
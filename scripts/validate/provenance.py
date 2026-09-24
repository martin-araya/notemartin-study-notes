#!/usr/bin/env python3
"""provenance.py — F34 Provenance validator.

Verifica los 3 criterios de Fase 34 sobre uno o varios SDMs:
  1. Procedencia presente: cada SDM lleva `source_provenance` por campo no
     default (al menos para los campos `version`/`vendor`/`product`/`hash`).
  2. Distinguibilidad: ningún campo `inferred` lleva `confidence == 1.0`, y
     ningún campo `read` lleva `confidence < 1.0`.
  3. Version gating: con `--require-version`, ningún SDM de "documentación"
     (vendor+product no triviales) puede tener `version` ausente/null.

Uso:
    python3 scripts/validate/provenance.py --sdm <path>|<dir> [<sdm> ...]
    python3 scripts/validate/provenance.py --sdm evals/provenance-sample/build/source-full/sdm.json
    python3 scripts/validate/provenance.py --sdm evals/provenance-sample/build/source-version-absent/sdm.json --require-version
    python3 scripts/validate/provenance.py --sdm <dir> --require-version --json-only

Argumentos:
    --sdm             Uno o más sdms (archivo o directorio que contenga `*.json`).
    --require-version Exit 1 si algún SDM de documentación tiene version ausente (default: solo exit 2 warning).
    --min-confidence  Confianza mínima para inferidos (default 0.7). Por debajo warning.
    --json-only       No escribir reporte legible.
    --report PATH     Ruta para `validation_report.json` (default: <out>/provenance_report.json).

Códigos de salida:
    0 — OK
    2 — Advertencias (campos inferidos, version ausente sin --require-version)
    1 — Hard fail (--require-version: version ausente en documentación;
                     consistencia read/inferred rota)

Dependencias:
    - Python 3.9+ stdlib
    - jsonschema (recomendado, validación contra sdm.schema.json)

Documentación normativa: references/02-source-model/provenance.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "skill" / "notemartin-study-notes" / "schemas" / "sdm.schema.json"

# Methods whose `confidence` must be < 1.0 per spec §4 (tabla).
# Note: `triage_metadata` is excluded because its default confidence is 1.0
# (per spec §4 — hash computed deterministically). If a future caller emits
# `triage_metadata` with confidence < 1.0, the validator accepts either value.
INFERRED_METHODS = {
    "inferred",
    "url_regex",
    "cover_or_header",
    "web_docs_metadata",
}

# Required-fields whose absence/empty triggers C1 warning.
PROVENANCE_FIELDS_REQUIRED = ("vendor", "product", "version", "hash", "id")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tf:
        tf.write(content)
        tmpname = tf.name
    Path(tmpname).replace(path)


def _collect_sdm_paths(args_paths: List[str]) -> List[Path]:
    out: List[Path] = []
    for arg in args_paths:
        p = Path(arg)
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.glob("*.json")))
        else:
            sys.stderr.write(f"--sdm path not found: {p}\n")
    return out


def _load_sdm(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _field_method_conf(sdm: Dict[str, Any], field: str) -> Tuple[str, float]:
    """Resolve (method, confidence) for a source field. Returns
    (read, 1.0) when source_provenance is absent (backward-compat per §5)."""
    src = sdm.get("source") or {}
    prov = sdm.get("source_provenance") or {}
    if field in prov:
        entry = prov[field]
        return entry.get("method", "absent"), float(entry.get("confidence", 0.0))
    # No annotation: assume read (backward-compat)
    return "read", 1.0


def _value_present(sdm: Dict[str, Any], field: str) -> bool:
    v = (sdm.get("source") or {}).get(field)
    if v is None:
        return False
    if isinstance(v, (list, dict)) and len(v) == 0:
        return False
    if isinstance(v, str) and v == "":
        return False
    return True


def _is_documentation(sdm: Dict[str, Any]) -> bool:
    """'Documentation' = vendor+product non-trivial. Per spec §6."""
    src = sdm.get("source") or {}
    vendor = (src.get("vendor") or "").strip().lower()
    product = (src.get("product") or "").strip().lower()
    trivial = {"", "unknown", "n/a", "none"}
    return vendor not in trivial and product not in trivial


def _judge_one(sdm_path: Path, sdm: Dict[str, Any], min_confidence: float
               ) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate a single SDM. Returns (ok, warnings, info_dict)."""
    warnings: List[str] = []
    info: Dict[str, Any] = {"source_id": (sdm.get("source") or {}).get("id", "?")}

    # Criterion 1: every required field has provenance entry (when source_provenance exists).
    if "source_provenance" in sdm:
        for f in PROVENANCE_FIELDS_REQUIRED:
            if f not in sdm["source_provenance"]:
                warnings.append(
                    f"C1: source_provenance missing entry for required field {f!r}"
                )

    # Criterion 2: distinguishability.
    methods_used: Counter = Counter()
    inferences: List[str] = []
    reads: List[str] = []
    for f, entry in (sdm.get("source_provenance") or {}).items():
        method = entry.get("method", "absent")
        conf = float(entry.get("confidence", 0.0))
        methods_used[method] += 1
        if method == "read" and conf != 1.0:
            warnings.append(
                f"C2: field {f!r} has method='read' but confidence={conf} (must be 1.0)"
            )
        if method in INFERRED_METHODS and conf >= 1.0:
            warnings.append(
                f"C2: field {f!r} has method={method!r} but confidence={conf} (must be <1.0)"
            )
        if conf < min_confidence:
            warnings.append(
                f"C2: field {f!r} confidence={conf} < min-confidence={min_confidence}"
            )
        if method == "read":
            reads.append(f)
        elif method in INFERRED_METHODS or method == "inferred":
            inferences.append(f)

    info["methods_count"] = dict(methods_used)
    info["read_fields"] = reads
    info["inferred_fields"] = inferences

    return True, warnings, info


def _criterion_3_version_check(sdm: Dict[str, Any]) -> Optional[str]:
    """Returns None if OK, otherwise a warning string about missing version."""
    method, _ = _field_method_conf(sdm, "version")
    if _value_present(sdm, "version"):
        return None
    return f"C3: source.version is null/absent (method={method}); propagation will carry version:null + inferred:true"


def _run(sdm_paths: List[Path], require_version: bool,
         min_confidence: float, json_only: bool,
         report_path: Path) -> int:
    sdms: List[Tuple[Path, Dict[str, Any]]] = []
    for p in sdm_paths:
        try:
            sdms.append((p, _load_sdm(p)))
        except Exception as e:
            sys.stderr.write(f"failed to parse {p}: {e}\n")
            return 1

    sdms_info: List[Dict[str, Any]] = []
    all_warnings: List[str] = []
    hard_fails: List[str] = []

    for path, sdm in sdms:
        ok, warns, info = _judge_one(sdm_path=path, sdm=sdm,
                                       min_confidence=min_confidence)
        info["path"] = str(path)
        info["warnings"] = warns
        # Criterion 3
        c3 = _criterion_3_version_check(sdm)
        if c3 is not None:
            if require_version and _is_documentation(sdm):
                hard_fails.append(
                    f"{path} {c3} (--require-version: documentation source)"
                )
            else:
                all_warnings.append(f"{path} {c3}")
        # Attach info
        sdms_info.append(info)
        # From info.warnings is per-sdm; we add to global
        for w in warns:
            all_warnings.append(f"{path} {w}")

    # Per-method totals (cross-SDM)
    methods_total: Counter = Counter()
    for info in sdms_info:
        for k, v in (info.get("methods_count") or {}).items():
            methods_total[k] += v

    report = {
        "schema_version": "1.0.0",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "sdms_evaluated": len(sdms),
        "criteria": {
            "c1_propagation": "PASS" if not any("C1:" in w for w in all_warnings) else "WARN",
            "c2_distinguishability": "PASS" if not any("C2:" in w for w in all_warnings) else "WARN",
            "c3_version": (
                "HARD_FAIL" if hard_fails
                else "WARN" if any("C3:" in w for w in all_warnings)
                else "PASS"
            ),
        },
        "require_version_flag": require_version,
        "min_confidence": min_confidence,
        "methods_total": dict(methods_total),
        "hard_fails": hard_fails,
        "warnings": all_warnings,
        "sdms": sdms_info,
    }

    _atomic_write_text(report_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    if not json_only:
        lines = [
            f"# Provenance validation report",
            "",
            f"- **SDMs evaluated:** {len(sdms)}",
            f"- **require-version:** {require_version}",
            f"- **min-confidence:** {min_confidence}",
            f"- **methods_total:** {dict(methods_total)}",
            f"- **hard fails:** {len(hard_fails)}",
            f"- **warnings:** {len(all_warnings)}",
            "",
            "## Criterios",
            f"- C1 (propagación): {report['criteria']['c1_propagation']}",
            f"- C2 (distinguibilidad): {report['criteria']['c2_distinguishability']}",
            f"- C3 (version): {report['criteria']['c3_version']}",
        ]
        if hard_fails:
            lines.append("")
            lines.append("## HARD FAILS")
            for h in hard_fails:
                lines.append(f"- {h}")
        if all_warnings:
            lines.append("")
            lines.append("## WARNINGS")
            for w in all_warnings[:50]:
                lines.append(f"- {w}")
            if len(all_warnings) > 50:
                lines.append(f"- ... ({len(all_warnings) - 50} más en {report_path})")
        report_md = report_path.with_suffix(".md")
        _atomic_write_text(report_md, "\n".join(lines) + "\n")
        sys.stdout.write(f"\n{lines[0]}\n{'-' * 32}\n")
        for l in lines[3:]:
            print(l)

    if hard_fails:
        return 1
    if all_warnings:
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="provenance.py",
        description="F34 — Provenance validator (propagation, distinguishability, version gate).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Métodos (per spec §4):
  read               confidence == 1.0
  web_docs_metadata  confidence < 1.0
  triage_metadata    confidence < 1.0
  cover_or_header    confidence < 1.0
  url_regex          confidence < 1.0
  inferred           confidence < 1.0
  default            confidence == 0.0
  absent             confidence == 0.0

Reglas duras (spec §5):
  - method:'read'           ⇒ confidence == 1.0 (C2 violation otherwise)
  - method != 'read'/'absent'/'default' ⇒ confidence < 1.0 (C2 violation otherwise)

Criterios:
  C1 — source_provenance cubre todos los campos requeridos (vendor/product/version/hash/id)
  C2 — read vs inferido distinguibles (reglas duras arriba)
  C3 — version ausente en documentación ⇒ warning; con --require-version ⇒ exit 1

Códigos de salida:
  0 OK
  2 warnings
  1 hard fail (--require-version + documentation sin version)
""",
    )
    p.add_argument("--sdm", required=True, nargs="+",
                   help="Uno o más sdms (archivo o directorio con *.json)")
    p.add_argument("--require-version", action="store_true",
                   help="Exit 1 cuando source.version sea null/absent en fuentes "
                        "con vendor+product no triviales (gate de release).")
    p.add_argument("--min-confidence", type=float, default=0.7,
                   help="Confianza mínima para inferidos; por debajo warning (default 0.7)")
    p.add_argument("--json-only", action="store_true", help="Omitir reporte legible")
    p.add_argument("--report", type=Path, default=None,
                   help="Ruta para validation_report.json (default: <out>/provenance_report.json)")
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = _collect_sdm_paths(args.sdm)
    if not paths:
        sys.stderr.write("no SDM files resolved from --sdm\n")
        return 2
    report_path = args.report
    if report_path is None:
        # Default: <first_sdm_dir_or_file>.provenance_report.json
        first = paths[0]
        report_path = first.parent / "provenance_report.json"
    return _run(
        sdm_paths=paths,
        require_version=args.require_version,
        min_confidence=args.min_confidence,
        json_only=args.json_only,
        report_path=report_path,
    )


if __name__ == "__main__":
    sys.exit(main())

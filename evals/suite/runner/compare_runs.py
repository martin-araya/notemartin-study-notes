#!/usr/bin/env python3
"""compare_runs.py — Diff entre dos runs de la suite de evals

Uso:
    python3 compare_runs.py <run-A> <run-B> [--markdown]

Compara dos runs por case_id y por clave de aserción. Emite diff.json
junto al run-B (o a stdout en modo --markdown).

Cierre de criterio C4 del roadmap (F118): los resultados son comparables
entre iteraciones de la skill.

Detecta:
  - Cambios en skill_fingerprint.json (huella de la skill).
  - Casos aprobados / no aprobados que cambian.
  - Aserciones que pasan en un run y fallan en otro.
  - Cambios en scores humanos por dimensión.

Exit codes:
  0  diff emitido
  1  error de uso
  2  error de runtime

Dependencias: stdlib puro.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _index_run(run_dir: Path) -> dict[str, Any]:
    rep = _load(run_dir / "report.json")
    if rep:
        return {c["case_id"]: c for c in rep.get("cases", [])}
    # Si no hay report.json, reconstruir desde los cases/.
    out: dict[str, dict] = {}
    cases_dir = run_dir / "cases"
    if not cases_dir.exists():
        return out
    for cdir in sorted(cases_dir.iterdir()):
        if not cdir.is_dir():
            continue
        a = _load(cdir / "assertions.json")
        h = _load(cdir / "human.json")
        out[cdir.name] = {
            "case_id": cdir.name,
            "automatic": a.get("automatic", []) if a else [],
            "human_scores": h.get("scores", {}) if h else None,
            "approved": h.get("approved") if h else None,
        }
    return out


def _diff_summaries(a: dict, b: dict) -> dict:
    cases_a = set(a.keys())
    cases_b = set(b.keys())
    added = sorted(cases_b - cases_a)
    removed = sorted(cases_a - cases_b)
    common = sorted(cases_a & cases_b)
    changed = []
    for cid in common:
        ca = a[cid]
        cb = b[cid]
        # approved flip
        a_app = ca.get("approved")
        b_app = cb.get("approved")
        if a_app != b_app:
            changed.append({"case_id": cid, "field": "approved", "a": a_app, "b": b_app})
        # assertion deltas
        ids_a = {x["id"]: x for x in ca.get("automatic", []) or []}
        ids_b = {x["id"]: x for x in cb.get("automatic", []) or []}
        for aid in sorted(set(ids_a) | set(ids_b)):
            xa = ids_a.get(aid)
            xb = ids_b.get(aid)
            if xa and xb:
                if xa.get("passed") != xb.get("passed"):
                    changed.append(
                        {"case_id": cid, "field": f"assertion:{aid}", "a": xa.get("passed"), "b": xb.get("passed")}
                    )
        # human deltas
        ha = ca.get("human_scores") or {}
        hb = cb.get("human_scores") or {}
        for dim in sorted(set(ha) | set(hb)):
            if ha.get(dim) != hb.get(dim):
                changed.append(
                    {"case_id": cid, "field": f"human:{dim}", "a": ha.get(dim), "b": hb.get(dim)}
                )
    return {"added": added, "removed": removed, "common": common, "changed": changed}


def _render_markdown(diff: dict, fp_a: dict | None, fp_b: dict | None) -> str:
    out = ["# Diff entre runs", ""]
    if fp_a and fp_b and fp_a.get("composite_sha256") != fp_b.get("composite_sha256"):
        out.append("## Skill fingerprint cambió")
        out.append(f"- A: `{fp_a.get('composite_sha256')}`")
        out.append(f"- B: `{fp_b.get('composite_sha256')}`")
        out.append("")
    out.append("## Casos")
    if diff["added"]:
        out.append(f"- Añadidos: {', '.join(diff['added'])}")
    if diff["removed"]:
        out.append(f"- Eliminados: {', '.join(diff['removed'])}")
    if not diff["added"] and not diff["removed"]:
        out.append("- Mismos casos en ambos runs.")
    out.append("")
    if diff["changed"]:
        out.append("## Cambios")
        for c in diff["changed"]:
            out.append(f"- **{c['case_id']}** {c['field']}: `{c['a']}` → `{c['b']}`")
    else:
        out.append("Sin cambios.")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Diff entre dos runs")
    p.add_argument("run_a", help="Path a runs/<run-A>/")
    p.add_argument("run_b", help="Path a runs/<run-B>/")
    p.add_argument("--markdown", action="store_true")
    args = p.parse_args(argv)

    a_dir = Path(args.run_a)
    b_dir = Path(args.run_b)
    if not a_dir.exists() or not b_dir.exists():
        print("ERROR: run dir no existe", file=sys.stderr)
        return 2

    a_idx = _index_run(a_dir)
    b_idx = _index_run(b_dir)
    diff = _diff_summaries(a_idx, b_idx)
    fp_a = _load(a_dir / "skill_fingerprint.json")
    fp_b = _load(b_dir / "skill_fingerprint.json")

    if fp_a and fp_b and fp_a.get("composite_sha256") != fp_b.get("composite_sha256"):
        diff["skill_fingerprint_changed"] = {
            "a": fp_a.get("composite_sha256"),
            "b": fp_b.get("composite_sha256"),
        }

    out_obj = diff
    if args.markdown:
        sys.stdout.write(_render_markdown(diff, fp_a, fp_b))
    else:
        out_path = b_dir / "diff.json"
        out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"OK diff → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""apply_rubric.py — Asistente para que un humano aplique evals/rubric.md a un caso

Uso:
    python3 apply_rubric.py --case <case.yaml> --rubric <rubric.md> --out <human.json>

Genera una plantilla human.json con las 8 dimensiones y las anclas
declaradas en el caso. El humano rellena los valores 0-4 y guarda.

No usa LLM-as-judge: es estrictamente un formulario estructurado.

Exit codes:
  0  OK
  1  case inválido
  2  error de runtime

Dependencias: PyYAML (rec).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

DIMENSIONS = [
    "fidelity",
    "coverage",
    "traceability",
    "pedagogy",
    "structure",
    "components",
    "operational",
    "render-fidelity",
]

# Pesos y mínimos por perfil (de evals/rubric.md §5).
PROFILES: dict[str, dict[str, tuple[float, int]]] = {
    "study": {
        "fidelity": (0.20, 3),
        "coverage": (0.15, 3),
        "traceability": (0.10, 3),
        "pedagogy": (0.25, 2),
        "structure": (0.10, 2),
        "components": (0.05, 2),
        "operational": (0.10, 2),
        "render-fidelity": (0.05, 2),
    },
    "reference": {
        "fidelity": (0.30, 3),
        "coverage": (0.20, 3),
        "traceability": (0.20, 3),
        "pedagogy": (0.10, 2),
        "structure": (0.05, 2),
        "components": (0.10, 2),
        "operational": (0.05, 2),
        "render-fidelity": (0.00, 2),
    },
    "hybrid": {
        "fidelity": (0.25, 3),
        "coverage": (0.175, 3),
        "traceability": (0.15, 3),
        "pedagogy": (0.175, 2),
        "structure": (0.075, 2),
        "components": (0.075, 2),
        "operational": (0.075, 2),
        "render-fidelity": (0.025, 2),
    },
}


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("ERROR: PyYAML no disponible.", file=sys.stderr)
        sys.exit(2)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Genera plantilla human.json")
    p.add_argument("--case", required=True)
    p.add_argument("--rubric", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    case_path = Path(args.case)
    case = _load_yaml(case_path)
    profile = case.get("profile")
    if profile not in PROFILES:
        print(f"ERROR: profile inválido {profile!r}", file=sys.stderr)
        return 1

    anchors = (
        (case.get("assertions") or {})
        .get("human", [{}])[0]
        .get("spec", {})
        .get("anchors_used", [])
    )

    template = {
        "case_id": case.get("id", case_path.stem),
        "evaluator": "",
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "anchors_used": anchors,
        "scores": {d: None for d in DIMENSIONS},
        "profile": profile,
        "weights_and_mins": {d: {"weight": w, "min": m} for d, (w, m) in PROFILES[profile].items()},
        "approved": None,
        "notes": "",
    }
    Path(args.out).write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK plantilla → {args.out}")
    print("Rellene los valores 0-4 de cada dimensión y ejecute compute_global.py")
    print("(o hágalo a mano: global = Σ(weight × score); approved = global ≥ 2.5 AND cada dimensión ≥ min).")
    return 0


def compute_global(scores: dict[str, int], profile: str) -> tuple[float, bool, list[str]]:
    """Utilidad: dado un dict de scores y un perfil, devuelve (global, approved, violators)."""
    pw = PROFILES.get(profile)
    if not pw:
        return 0.0, False, []
    global_score = 0.0
    violators: list[str] = []
    for dim, (w, m) in pw.items():
        s = scores.get(dim)
        if s is None:
            violators.append(f"{dim}: missing")
            continue
        if s < m:
            violators.append(f"{dim}: {s} < min {m}")
        global_score += w * s
    approved = global_score >= 2.5 and not violators
    return round(global_score, 3), approved, violators


if __name__ == "__main__":
    raise SystemExit(main())

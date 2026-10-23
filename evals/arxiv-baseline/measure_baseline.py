#!/usr/bin/env python3
"""measure_baseline.py — línea base de ingesta para PDFs de arXiv (P0 del plan).

Mide, sobre un PDF nativo, los indicadores que el plan
`docs/arxiv-adaptation-plan.md` pretende mejorar, para comparar antes/después:

    ligature_fragments      fragmentos con ligaduras (ﬁ ﬂ ﬃ ﬄ ﬀ) sin normalizar
    math_glyph_fragments    fragmentos en fuentes matemáticas (CM*, MSBM, MSAM, ...)
    footnote_role_fragments fragmentos con rol `footnote` (incluye sub/superíndices mal clasificados)
    typed_blocks_missing    teoremas/pruebas/algoritmos que quedan como texto plano
    columns_per_page        columnas detectadas por layout.py en cada página
    columns_unstable        True si el nº de columnas varía entre páginas
    continuity_min/mean     continuity_score de layout.py

Uso:
    python3 evals/arxiv-baseline/measure_baseline.py --pdf <pdf> --out baseline.json
    python3 evals/arxiv-baseline/measure_baseline.py --pdf <pdf> --fragments <fragments.json> \
        --layout-summary <layout_summary.json> --out baseline.json   # reutiliza salidas previas

Códigos de salida: 0 OK, 1 error.
Dependencias: Python 3.9+ stdlib; pypdf (lo usa pdf_native.py).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[2]
INGEST = REPO / "skill" / "notemartin-study-notes" / "scripts" / "ingest"

LIGATURES = "\ufb00\ufb01\ufb02\ufb03\ufb04"
MATH_FONT_RE = re.compile(r"(CMMI|CMSY|CMEX|CMR|CMBX|MSBM|MSAM|MnSymbol|Math)", re.I)
TYPED_BLOCK_RE = re.compile(
    r"^(Theorem|Lemma|Proposition|Corollary|Definition|Remark|Claim|Proof|Algorithm)\b"
)


def _run(cmd: List[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode not in (0, 2):
        raise RuntimeError(f"{' '.join(cmd)} -> exit {res.returncode}\n{res.stderr[-500:]}")


def measure(fragments: Dict[str, Any], layout: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    frags = [f for p in fragments["pages"] for f in p["fragments"]]
    out: Dict[str, Any] = {
        "page_count": fragments.get("page_count"),
        "fragment_count": len(frags),
        "ligature_fragments": sum(1 for f in frags if any(c in f["text"] for c in LIGATURES)),
        "math_glyph_fragments": sum(1 for f in frags if MATH_FONT_RE.search(f.get("font_name", ""))),
        "footnote_role_fragments": sum(1 for f in frags if f.get("role") == "footnote"),
        "typed_blocks_missing": sum(1 for f in frags if TYPED_BLOCK_RE.match(f["text"].strip())),
    }
    if layout is not None:
        pages = layout.get("pages", [])
        cols = [p.get("column_count") for p in pages]
        scores = [p.get("continuity_score") for p in pages if p.get("continuity_score") is not None]
        out["columns_per_page"] = cols
        out["columns_unstable"] = len(set(cols)) > 1
        out["continuity_min"] = min(scores) if scores else None
        out["continuity_mean"] = round(sum(scores) / len(scores), 4) if scores else None
        out["out_of_flow_ratio"] = round(
            sum(p.get("out_of_flow_count", 0) for p in pages)
            / max(1, sum(p.get("region_count", 0) for p in pages)),
            4,
        )
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fragments", type=Path, help="fragments.json de pdf_native.py (evita re-ejecutar)")
    ap.add_argument("--layout-summary", type=Path, help="layout_summary.json de layout.py (evita re-ejecutar)")
    args = ap.parse_args(argv)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            frag_path = args.fragments
            if frag_path is None:
                _run([sys.executable, str(INGEST / "pdf_native.py"), "--source", str(args.pdf),
                      "--out-dir", f"{tmp}/native", "--json-only"])
                frag_path = Path(tmp) / "native" / "fragments.json"
            layout_path = args.layout_summary
            if layout_path is None:
                _run([sys.executable, str(INGEST / "layout.py"), "--pdf", str(args.pdf),
                      "--out-dir", f"{tmp}/layout", "--json-only"])
                layout_path = Path(tmp) / "layout" / "ingest" / "layout" / "layout_summary.json"
            fragments = json.loads(frag_path.read_text(encoding="utf-8"))
            layout = json.loads(layout_path.read_text(encoding="utf-8")) if layout_path.exists() else None
    except (RuntimeError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result = {"pdf": str(args.pdf), "metrics": measure(fragments, layout)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

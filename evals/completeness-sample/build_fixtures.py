"""Eval battery — Fase 43: auditoría de no-pérdida.

Sintetiza workdirs reproducibles (SDM + ledger) para verificar los 3 criterios:
1. Detecta una omisión inyectada deliberadamente.
2. El muestreo inverso tiene tamaño y método definidos.
3. No se puede cerrar el trabajo con la auditoría en rojo.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/completeness-sample/build_fixtures.py
    python3 evals/completeness-sample/run_eval.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"
TMP = HERE / "tmp_workdir"

COMPLETENESS = REPO / "skill" / "notemartin-study-notes" / "scripts" / "validate" / "completeness.py"
VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"
F41_EVAL = REPO / "evals" / "conflicts-sample" / "run_eval.py"
F42_EVAL = REPO / "evals" / "fidelity-sample" / "run_eval.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _setup_workdir(name: str, sdm_name: str, ledger_name: str,
                   sample_rate: float = 0.10, seed: int = 0) -> Path:
    """Crea un workdir sintético."""
    TMP.mkdir(parents=True, exist_ok=True)
    wd = TMP / name
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / sdm_name, wd / "sdm.json")
    (wd / "knowledge").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / ledger_name, wd / "knowledge" / "ledger.json")
    return wd


def _run_completeness(workdir: Path, subcommand: str = "audit", **flags) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(COMPLETENESS), "--workdir", str(workdir), subcommand]
    for k, v in flags.items():
        cmd.append(f"--{k.replace('_', '-')}")
        cmd.append(str(v))
    return subprocess.run(cmd, capture_output=True, text=True)


# -------------------------------------------------------------------
# SDM sintético bien poblado.
# -------------------------------------------------------------------

def _block(content: str | None = None, btype: str = "definition",
           section_path: str = "/ch02/config", idx: int = 0, src: str = "sdm-clean") -> dict:
    h = hashlib.sha1()
    h.update(f"{src}/{section_path}/{idx}".encode())
    bid = h.hexdigest()[:12]
    return {
        "id": bid,
        "type": btype,
        "content": content or {},
        "anchor": {"page": 1, "section_path": section_path, "bbox": None},
        "confidence": 1.0,
        "origin": "native",
    }


def sdm_clean() -> dict:
    blocks = [
        _block({"name": "shared_buffers", "description": "Tamaño del caché."},
               "parameter", "/ch02/config", 0),
        _block({"name": "shared_buffers", "value": "128 MB"},
               "default", "/ch02/config", 1),
        _block({"code": "EADDRINUSE", "message": "Puerto en uso."},
               "error-code", "/ch02/config", 2),
        _block({"text": "WARNING: este comando borra datos.", "severity": "caution"},
               "warning", "/ch02/config", 3),
        _block({"latex": "t = O(n log n)", "numbered": True, "label": "eq:1"},
               "formula", "/ch02/config", 4),
        _block({"text": "PostgreSQL es un ORDBMS."},
               "definition", "/ch02/intro", 5),
        _block({"text": "Texto introductorio sin info nueva."},
               "prose", "/ch02/intro", 6),
    ]
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64, "format": "pdf",
                   "vendor": "PGDG", "product": "PostgreSQL"},
        "sections": [
            {"section_path": "/ch02/config", "title": "Config", "blocks": blocks[:5]},
            {"section_path": "/ch02/intro", "title": "Intro", "blocks": blocks[5:]},
        ],
    }


def ledger_clean() -> dict:
    """Ledger con entries para todos los must-keep; todos en state=written."""
    blocks = sdm_clean()["sections"][0]["blocks"] + sdm_clean()["sections"][1]["blocks"]
    bid_param = blocks[0]["id"]
    bid_default = blocks[1]["id"]
    bid_error = blocks[2]["id"]
    bid_warning = blocks[3]["id"]
    bid_formula = blocks[4]["id"]
    bid_definition = blocks[5]["id"]

    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "entries": [
            {"unit_id": "u_001", "source_block_ids": [bid_param],
             "source_section_path": "/ch02/config", "type": "parameter",
             "criticality": "must-keep", "target_note": "pg", "state": "written",
             "content": blocks[0]["content"]},
            {"unit_id": "u_002", "source_block_ids": [bid_default],
             "source_section_path": "/ch02/config", "type": "default",
             "criticality": "must-keep", "target_note": "pg", "state": "written",
             "content": blocks[1]["content"]},
            {"unit_id": "u_003", "source_block_ids": [bid_error],
             "source_section_path": "/ch02/config", "type": "error-code",
             "criticality": "must-keep", "target_note": "pg", "state": "written",
             "content": blocks[2]["content"]},
            {"unit_id": "u_004", "source_block_ids": [bid_warning],
             "source_section_path": "/ch02/config", "type": "warning",
             "criticality": "must-keep", "target_note": "pg", "state": "written",
             "content": blocks[3]["content"]},
            {"unit_id": "u_005", "source_block_ids": [bid_formula],
             "source_section_path": "/ch02/config", "type": "formula",
             "criticality": "must-keep", "target_note": "pg", "state": "written",
             "content": blocks[4]["content"]},
            {"unit_id": "u_006", "source_block_ids": [bid_definition],
             "source_section_path": "/ch02/intro", "type": "definition",
             "criticality": "context", "target_note": "pg", "state": "written",
             "content": blocks[5]["content"]},
        ],
    }


def ledger_with_omission() -> dict:
    """Ledger que omite el block del error-code."""
    base = json.loads(json.dumps(ledger_clean()))
    base["entries"] = [e for e in base["entries"] if e["type"] != "error-code"]
    return base


def ledger_mutilated() -> dict:
    """Ledger con `parameter.name` mutilado (cambia 'shared_buffers' a 'sharedbuffer')."""
    base = json.loads(json.dumps(ledger_clean()))
    for e in base["entries"]:
        if e["type"] == "parameter":
            e["content"]["name"] = "sharedbuffer"  # mutilación
    return base


def ledger_pending() -> dict:
    """Ledger con un must-keep en state=pending."""
    base = json.loads(json.dumps(ledger_clean()))
    for e in base["entries"]:
        if e["type"] == "parameter":
            e["state"] = "pending"
    return base


def sdm_context_rich() -> dict:
    """SDM con muchos blocks context (prose) para verificar muestreo 10%."""
    blocks: list[dict] = []
    for i in range(50):
        blocks.append(_block({"text": f"Texto introductorio {i}."},
                             "prose", "/ch03/prose", i, src="sdm-context-rich"))
    # Añadir 2 must-keep también.
    blocks.append(_block({"name": "param_x", "description": "Otro parámetro."},
                         "parameter", "/ch03/extra", 100, src="sdm-context-rich"))
    blocks.append(_block({"name": "param_x", "value": "default"},
                         "default", "/ch03/extra", 101, src="sdm-context-rich"))
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-rich", "hash": "b" * 64, "format": "pdf",
                   "vendor": "PGDG", "product": "PostgreSQL"},
        "sections": [
            {"section_path": "/ch03/prose", "title": "Prose", "blocks": blocks[:50]},
            {"section_path": "/ch03/extra", "title": "Extra", "blocks": blocks[50:]},
        ],
    }


def ledger_context_rich_partial() -> dict:
    """Ledger que cubre los 2 must-keep pero omite algunos context."""
    sdm = sdm_context_rich()
    must_keep_ids = [sdm["sections"][1]["blocks"][0]["id"],
                     sdm["sections"][1]["blocks"][1]["id"]]
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-rich", "hash": "b" * 64},
        "entries": [
            {"unit_id": "u_r_01", "source_block_ids": [must_keep_ids[0]],
             "source_section_path": "/ch03/extra", "type": "parameter",
             "criticality": "must-keep", "target_note": "rich", "state": "written",
             "content": {"name": "param_x", "description": "Otro parámetro."}},
            {"unit_id": "u_r_02", "source_block_ids": [must_keep_ids[1]],
             "source_section_path": "/ch03/extra", "type": "default",
             "criticality": "must-keep", "target_note": "rich", "state": "written",
             "content": {"name": "param_x", "value": "default"}},
        ],
    }


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    sdm_c = sdm_clean()
    _write_json(FIX / "sdm-clean.json", sdm_c)
    _write_json(FIX / "ledger-clean.json", ledger_clean())
    _write_json(FIX / "ledger-with-omission.json", ledger_with_omission())
    _write_json(FIX / "ledger-mutilated.json", ledger_mutilated())
    _write_json(FIX / "ledger-pending.json", ledger_pending())
    _write_json(FIX / "sdm-context-rich.json", sdm_context_rich())
    _write_json(FIX / "ledger-context-rich-partial.json", ledger_context_rich_partial())

    print("fixtures: 7 archivos JSON")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Eval battery — Fase 41: contradicciones y obsolescencia.

Sintetiza fixtures reproducibles para verificar los 3 criterios del roadmap
+ reglas R1–R8 del spec + no-regresión F15/F37/F38/F39/F40:

1. Una contradicción inyectada se detecta y documenta con ambas anclas.
2. Todo contenido deprecado llega marcado.
3. El cuerpo nunca contradice la fuente sin señalarlo.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/conflicts-sample/build_fixtures.py
    python3 evals/conflicts-sample/run_eval.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _conflict(id_: str, type_: str, anchors: list[dict], description: str,
              status: str = "open", resolution: str | None = None,
              model_says: str | None = None,
              deprecation_status: str | None = None) -> dict:
    c: dict = {
        "id": id_,
        "type": type_,
        "anchors": anchors,
        "description": description,
        "status": status,
        "resolution": resolution,
        "model_says": model_says,
        "first_seen_at": _now(),
        "deprecation_status": deprecation_status,
    }
    return c


# -------------------------------------------------------------------
# Fixture: conflicts-good (3 contradicciones válidas).
# -------------------------------------------------------------------

def conflicts_good() -> dict:
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "conflicts": [
            _conflict(
                "c_001", "source-vs-source",
                [{"type": "block", "id": "a8f4ce140580"},
                 {"type": "block", "id": "b9e0d250691"}],
                "El parámetro `shared_buffers` aparece con default 128 MB en /ch02 y 64 MB en /ch07.",
                status="open",
            ),
            _conflict(
                "c_002", "source-vs-derived",
                [{"type": "block", "id": "c1d2e3f40506"},
                 {"type": "concept", "id": "mvcc"}],
                "El modelo infiere serializable snapshot isolation; la fuente no lo nombra explícitamente.",
                status="resolved",
                resolution="Cuerpo refleja la fuente; modelo_says documenta la inferencia.",
                model_says="MVCC implementa serializable snapshot isolation desde PG 9.1.",
            ),
            _conflict(
                "c_003", "deprecation-mismatch",
                [{"type": "block", "id": "d1e2f3a40506"},
                 {"type": "note", "id": "postgres-wal"}],
                "WAL aparece como current en /ch02 y como deprecated en /ch09.",
                status="open",
                deprecation_status="deprecated",
            ),
        ],
        "build_metadata": {"built_at": _now(), "conflict_count": 3},
    }


# -------------------------------------------------------------------
# Fixture: conflicts-orphan-anchor (anchor apunta a bloque inexistente).
# -------------------------------------------------------------------

def conflicts_orphan_anchor() -> dict:
    base = json.loads(json.dumps(conflicts_good()))
    base["conflicts"][0]["anchors"][1]["id"] = "deadbeef0000"  # block inexistente
    return base


# -------------------------------------------------------------------
# Fixture: conflicts-same-anchor (R3 violado: 2 anchors idénticos).
# -------------------------------------------------------------------

def conflicts_same_anchor() -> dict:
    base = json.loads(json.dumps(conflicts_good()))
    base["conflicts"][0]["anchors"] = [
        {"type": "block", "id": "a8f4ce140580"},
        {"type": "block", "id": "a8f4ce140580"},  # mismo anchor
    ]
    return base


# -------------------------------------------------------------------
# Fixture: conflicts-undocumented (criterio 1: contradicción en SDM no documentada).
# Para el eval, este fixture se inyecta manualmente; build_fixtures.py solo lo deja
# como "anchor record" para que el eval verifique el caso.
# -------------------------------------------------------------------

def conflicts_undocumented_record() -> dict:
    """Caso negativo: el SDM tiene una contradicción (block A dice X, block B dice no-X)
    pero el registry NO la incluye. El eval inyecta el fixture SDM-contradiction y
    verifica que el registry queda incompleto."""
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "conflicts": [],  # vacío: contradicción NO documentada
        "build_metadata": {"built_at": _now(), "conflict_count": 0},
    }


# -------------------------------------------------------------------
# SDM con contradicción inyectada (criterio 1).
# -------------------------------------------------------------------

def sdm_with_contradiction() -> dict:
    """SDM donde dos bloques dicen cosas distintas sobre el mismo parámetro."""
    blocks: list[dict] = []
    section = "/ch02/configuration"
    for idx, (btype, content) in enumerate([
        ("parameter", {"name": "shared_buffers", "description": "default 128 MB"}),
        ("parameter", {"name": "shared_buffers", "description": "default 64 MB"}),  # contradicción
        ("warning", {"text": "WARNING: ajuste este parámetro.", "severity": "caution"}),
        ("example", {"text": "Ejemplo de configuración."}),
    ]):
        h = __import__("hashlib").sha1()
        h.update(f"sdm-conflict/{section}/{idx}".encode())
        bid = h.hexdigest()[:12]
        blocks.append({
            "id": bid,
            "type": btype,
            "content": content,
            "anchor": {"page": 1 + idx // 2, "section_path": section, "bbox": None},
            "confidence": 1.0,
            "origin": "native",
        })
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64, "format": "pdf"},
        "sections": [{"section_path": section, "title": "Configuration", "blocks": blocks}],
    }


# -------------------------------------------------------------------
# SDM con bloque deprecated sin marker (criterio 2 violado).
# -------------------------------------------------------------------

def sdm_deprecated_unmarked() -> dict:
    blocks: list[dict] = []
    section = "/ch02/legacy"
    for idx, (btype, content) in enumerate([
        ("warning", {"text": "WARNING: este comando está deprecated.", "severity": "caution"}),  # bloque deprecado
        ("parameter", {"name": "old_param", "description": "deprecated"}),
        ("example", {"text": "ejemplo"}),
        ("prose", {"text": "intro"}),
    ]):
        h = __import__("hashlib").sha1()
        h.update(f"sdm-deprecated/{section}/{idx}".encode())
        bid = h.hexdigest()[:12]
        blocks.append({
            "id": bid,
            "type": btype,
            "content": content,
            "anchor": {"page": 1, "section_path": section, "bbox": None},
            "confidence": 1.0,
            "origin": "native",
        })
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-legacy", "hash": "b" * 64, "format": "pdf"},
        "sections": [{"section_path": section, "title": "Legacy", "blocks": blocks}],
    }


def sdm_deprecated_marked() -> dict:
    """Versión buena: cada bloque con 'deprecated' en content tiene deprecation_status poblado
    en el ledger que lo respalda."""
    base = json.loads(json.dumps(sdm_deprecated_unmarked()))
    return base


def _deprecated_block_ids() -> list[str]:
    """IDs reales de los bloques que contienen keywords deprecated en sdm-deprecated-*."""
    sdm = sdm_deprecated_unmarked()
    ids = []
    for section in sdm.get("sections", []):
        for block in section.get("blocks", []):
            content_text = json.dumps(block.get("content", {}))
            if any(kw in content_text.lower() for kw in ("deprecated", "obsolete", "removed")):
                ids.append(block["id"])
    return ids


def ledger_with_deprecation_markers() -> dict:
    """Ledger que marca cada bloque deprecated con deprecation_status='deprecated'."""
    dep_ids = _deprecated_block_ids()
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-legacy", "hash": "b" * 64},
        "entries": [
            {
                "unit_id": f"u_dep_{i:02d}",
                "source_block_ids": [bid],
                "source_section_path": "/ch02/legacy",
                "type": "warning",
                "criticality": "context",
                "target_note": None,
                "state": "discarded",
                "discard_reason": "out-of-scope-by-user",
                "deprecation_status": "deprecated",
            }
            for i, bid in enumerate(dep_ids)
        ],
        "build_metadata": {"version": "1.0", "built_at": _now()},
    }


def ledger_no_deprecation_markers() -> dict:
    """Ledger que NO marca los bloques deprecated — caso negativo para criterio 2."""
    dep_ids = _deprecated_block_ids()
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-legacy", "hash": "b" * 64},
        "entries": [
            {
                "unit_id": f"u_dep_{i:02d}",
                "source_block_ids": [bid],
                "source_section_path": "/ch02/legacy",
                "type": "warning",
                "criticality": "context",
                "target_note": None,
                "state": "discarded",
                "discard_reason": "out-of-scope-by-user",
                # deprecation_status ausente
            }
            for i, bid in enumerate(dep_ids)
        ],
        "build_metadata": {"version": "1.0", "built_at": _now()},
    }


# -------------------------------------------------------------------
# NoteMark files (criterio 3).
# -------------------------------------------------------------------

NOTEMARK_GOOD = """\
# Postgres Configuration

El parámetro `shared_buffers` controla el caché compartido.

:::contradiction id="c_001"
:::

Este parámetro acepta valores en MB.
"""

NOTEMARK_UNDOCUMENTED = """\
# Postgres Configuration

El parámetro `shared_buffers` controla el caché compartido.

:::contradiction id="c_999"
:::

Este parámetro acepta valores en MB.
"""


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    _write_json(FIX / "conflicts-good.json", conflicts_good())
    _write_json(FIX / "conflicts-orphan-anchor.json", conflicts_orphan_anchor())
    _write_json(FIX / "conflicts-same-anchor.json", conflicts_same_anchor())
    _write_json(FIX / "conflicts-undocumented.json", conflicts_undocumented_record())
    _write_json(FIX / "sdm-with-contradiction.json", sdm_with_contradiction())
    _write_json(FIX / "sdm-deprecated-unmarked.json", sdm_deprecated_unmarked())
    _write_json(FIX / "sdm-deprecated-marked.json", sdm_deprecated_marked())
    _write_json(FIX / "ledger-with-deprecation.json", ledger_with_deprecation_markers())
    _write_json(FIX / "ledger-no-deprecation.json", ledger_no_deprecation_markers())
    _write_text(FIX / "notemark-good.md", NOTEMARK_GOOD)
    _write_text(FIX / "notemark-undocumented.md", NOTEMARK_UNDOCUMENTED)

    print("fixtures: 9 archivos JSON + 2 NoteMark")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

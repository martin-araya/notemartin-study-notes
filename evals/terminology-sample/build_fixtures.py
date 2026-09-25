"""Eval battery — Fase 40: terminología y glosario acumulativo.

Sintetiza glosarios reproducibles para verificar los 3 criterios del roadmap:
1. Ningún término tiene dos definiciones canónicas.
2. Ningún alias apunta a dos términos.
3. Un término del capítulo 2 no se redefine en el 9.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/terminology-sample/build_fixtures.py
    python3 evals/terminology-sample/run_eval.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"

CANONICAL_RE = r"^[a-z0-9][a-z0-9-]{0,63}$"
ALIAS_KINDS = {"en", "es", "acronym", "plural", "variant"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _term(canonical: str, definition: str, domain: str, aliases: list[dict],
          definitions: list[dict], needs_review: bool = False,
          confusables: list[str] | None = None,
          related_concepts: list[str] | None = None) -> dict:
    t: dict = {
        "canonical": canonical,
        "definition": definition,
        "domain": domain,
        "aliases": aliases,
        "definitions": definitions,
        "needs_review": needs_review,
    }
    if confusables is not None:
        t["confusables"] = confusables
    if related_concepts is not None:
        t["related_concepts"] = related_concepts
    return t


def _def(chapter: str, definition: str, canonical: bool, status: str = "current") -> dict:
    return {
        "chapter": chapter,
        "definition": definition,
        "canonical": canonical,
        "status": status,
        "first_seen_at": _now(),
        "source_section_path": chapter,
    }


# -------------------------------------------------------------------
# Fixture: glossary-good (5 términos, todo válido).
# -------------------------------------------------------------------

def glossary_good() -> dict:
    return {
        "schema_version": "1.0.0",
        "source": {"id": "01-postgres", "vendor": "PostgreSQL Global Development Group", "product": "PostgreSQL"},
        "terms": {
            "transaccion": _term(
                "transaccion",
                "Una transacción es una unidad atómica de trabajo.",
                "postgresql",
                [{"alias": "transaction", "kind": "en"}, {"alias": "tx", "kind": "acronym"}],
                [_def("/ch01/intro", "Una transacción es una unidad atómica de trabajo.", True)],
                related_concepts=["acid", "mvcc"],
            ),
            "mvcc": _term(
                "mvcc",
                "Control de concurrencia multiversión.",
                "postgresql",
                [{"alias": "multi-version-concurrency-control", "kind": "acronym"}],
                [_def("/ch01/intro", "Control de concurrencia multiversión.", True)],
            ),
            "wal": _term(
                "wal",
                "Write-Ahead Log: registro de escritura anticipada.",
                "postgresql",
                [{"alias": "write-ahead-log", "kind": "en"}],
                [_def("/ch01/intro", "Write-Ahead Log: registro de escritura anticipada.", True)],
            ),
            "acid": _term(
                "acid",
                "Atomicidad, consistencia, aislamiento, durabilidad.",
                "postgresql",
                [{"alias": "ACID", "kind": "acronym"}],
                [_def("/ch02/transactions", "Atomicidad, consistencia, aislamiento, durabilidad.", True)],
            ),
            "vista-materializada": _term(
                "vista-materializada",
                "Una vista materializada almacena el resultado de una consulta.",
                "postgresql",
                [{"alias": "materialized view", "kind": "en"}],
                [_def("/ch01/intro", "Una vista materializada almacena el resultado de una consulta.", True)],
                confusables=["view"],
            ),
        },
        "build_metadata": {"built_at": _now(), "term_count": 5},
    }


# -------------------------------------------------------------------
# Fixture: glossary-dual-def (criterio 1 violado).
# -------------------------------------------------------------------

def glossary_dual_def() -> dict:
    base = json.loads(json.dumps(glossary_good()))
    # El término "transaccion" tiene 2 definitions con canonical=true (texto idéntico
    # para aislar criterio 1; un 2do canonical con texto distinto dispararía también
    # el criterio 3, mezclando las dos señales del eval).
    base["terms"]["transaccion"]["definitions"].append(
        _def("/ch09/late", "Una transacción es una unidad atómica de trabajo.", True)
    )
    return base


# -------------------------------------------------------------------
# Fixture: glossary-alias-collision (criterio 2 violado).
# -------------------------------------------------------------------

def glossary_alias_collision() -> dict:
    base = json.loads(json.dumps(glossary_good()))
    # "transaction" (alias de transaccion) aparece también como alias de mvcc.
    base["terms"]["mvcc"]["aliases"].append({"alias": "transaction", "kind": "variant"})
    return base


# -------------------------------------------------------------------
# Fixture: glossary-redefinition (criterio 3 violado).
# -------------------------------------------------------------------

def glossary_redefinition() -> dict:
    base = json.loads(json.dumps(glossary_good()))
    # "wal" tiene definition canónica en ch01; en ch09 aparece definition distinta
    # con canonical=false status=conflicting (y needs_review=true en el término).
    base["terms"]["wal"]["definitions"].append({
        "chapter": "/ch09/replication",
        "definition": "El WAL es el log binario que registra todas las modificaciones de la base.",
        "canonical": False,
        "status": "conflicting",
        "first_seen_at": _now(),
        "source_section_path": "/ch09/replication",
    })
    base["terms"]["wal"]["needs_review"] = True
    return base


# -------------------------------------------------------------------
# Fixture: glossary-collision-suffix (resolución correcta vía sufijo).
# -------------------------------------------------------------------

def glossary_collision_suffix() -> dict:
    base = json.loads(json.dumps(glossary_good()))
    # Añade "wal" en Oracle (mismo término, distinto vendor).
    base["terms"]["wal-oracle"] = _term(
        "wal-oracle",
        "Write-Ahead Log en Oracle (también llamado redo log).",
        "oracle",
        [],
        [_def("/oracle/ch03", "Write-Ahead Log en Oracle (también llamado redo log).", True)],
    )
    return base


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    _write_json(FIX / "glossary-good.json", glossary_good())
    _write_json(FIX / "glossary-dual-def.json", glossary_dual_def())
    _write_json(FIX / "glossary-alias-collision.json", glossary_alias_collision())
    _write_json(FIX / "glossary-redefinition.json", glossary_redefinition())
    _write_json(FIX / "glossary-collision-suffix.json", glossary_collision_suffix())

    _write_json(EXP / "good-canonicals.json",
                sorted(["transaccion", "mvcc", "wal", "acid", "vista-materializada"]))
    _write_json(EXP / "redefinition-chapters.json",
                ["/ch01/intro", "/ch09/replication"])

    print("fixtures: 5 glosarios + 2 expected")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

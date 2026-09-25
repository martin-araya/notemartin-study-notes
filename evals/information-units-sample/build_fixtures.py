"""Eval battery — Fase 37: unidades de información.

Sintetiza fixtures reproducibles (SDM sintéticos, ground-truth de criticidad,
dos extracciones independientes por fuente) para verificar los 3 criterios de
F37. Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/information-units-sample/build_fixtures.py
    python3 evals/information-units-sample/run_eval.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"

sys.path.insert(0, str(HERE))
from rules import is_must_keep  # noqa: E402

SOURCE_HASH_A = "a" * 64
SOURCE_HASH_B = "b" * 64


def _block_id(source_hash: str, section_path: str, block_index: int) -> str:
    """sha1(source.hash + section_path + str(block_index))[:12] — F13."""
    h = hashlib.sha1()
    h.update(source_hash.encode())
    h.update(section_path.encode())
    h.update(str(block_index).encode())
    return h.hexdigest()[:12]


def build_source_a() -> dict:
    """SDM sintético de 30 bloques con los 14 tipos cubiertos."""
    section = "/ch02/configuration"
    blocks: list[dict] = []
    idx = 0

    def add(type_: str, content: dict) -> None:
        nonlocal idx
        blocks.append(
            {
                "id": _block_id(SOURCE_HASH_A, section, idx),
                "type": type_,
                "content": content,
                "anchor": {"page": 10 + idx // 4, "section_path": section, "bbox": None},
                "confidence": 1.0,
                "origin": "native",
            }
        )
        idx += 1

    # prose introductorio (sin info nueva → no es unidad)
    add("prose", {"text": "Este capítulo describe los parámetros principales del servidor PostgreSQL."})

    # 6 parameters (R1 → must-keep)
    for name, desc in [
        ("shared_buffers", "Tamaño en MB del caché compartido."),
        ("work_mem", "Memoria asignada por operación de ordenamiento y hash antes de volcar a disco."),
        ("maintenance_work_mem", "Memoria usada por operaciones de mantenimiento como VACUUM."),
        ("effective_cache_size", "Estimación del tamaño del caché del sistema de archivos."),
        ("wal_buffers", "Memoria para el Write-Ahead Log antes de volcar a disco."),
        ("max_connections", "Número máximo de conexiones concurrentes al servidor."),
    ]:
        add("parameter", {"name": name, "description": desc})

    # 3 defaults (R2 → must-keep)
    for name, value in [
        ("shared_buffers", "128 MB"),
        ("max_connections", "100"),
        ("wal_buffers", "16 MB"),
    ]:
        add("default", {"name": name, "value": value})

    # 1 definition
    add("definition", {"text": "Una vista materializada es una relación almacenada que materializa el resultado de una consulta."})

    # 1 mechanism
    add("mechanism", {"text": "El WAL previene la pérdida de datos porque cada cambio se fsyncea antes del COMMIT."})

    # 1 formula (numbered=true → R5 → must-keep)
    add("formula", {"latex": "t = O(n \\log n)", "numbered": True, "label": "eq:heapsort"})

    # 1 formula (unnumbered → context)
    add("formula", {"latex": "h(x) = (ax + b) \\bmod p", "numbered": False})

    # 2 error-codes (R3 → must-keep)
    add("error-code", {"code": "EADDRINUSE", "message": "El puerto ya está en uso."})
    add("error-code", {"code": "ORA-00904", "message": "Identificador no válido en la cláusula."})

    # 2 warnings (R4 → must-keep)
    add("warning", {"text": "WARNING: este comando borra datos sin pedir confirmación.", "severity": "caution"})
    add("warning", {"text": "WARNING: una clave primaria no puede contener NULL.", "severity": "caution"})

    # 1 step
    add("step", {"ordinal": 1, "text": "Verificar el hash con `sha256sum archivo.iso`."})
    add("step", {"ordinal": 2, "text": "Montar la imagen con `mount -o loop archivo.iso /mnt`."})

    # 1 example
    add("example", {"text": "Ejemplo: SELECT pg_reload_conf(); recarga la configuración sin reiniciar."})

    # 1 constraint
    add("constraint", {"text": "Una clave primaria no puede contener NULL."})

    # 1 syntax-rule
    add("syntax-rule", {"rule": "Los identificadores válidos siguen `[a-zA-Z_][a-zA-Z0-9_]*`.", "ebnf": "<identificador> ::= [a-zA-Z_][a-zA-Z0-9_]*"})

    # 1 version-note
    add("version-note", {"text": "Desde PostgreSQL 13, wal_keep_size reemplaza a wal_keep_segments.", "version_introduced": "13"})

    # 1 tradeoff
    add("tradeoff", {"text": "Usar un índice acelera lecturas pero ralentiza escrituras."})

    # 1 cross-reference
    add("cross-reference", {"target": "/ch04/replication", "label": "Ver §4 sobre replicación."})

    # prose sin info nueva (cierra los 30 bloques)
    for _ in range(30 - len(blocks)):
        add("prose", {"text": f"Texto introductorio adicional sin unidades nuevas ({idx})."})

    return {
        "schema_version": "1.0.0",
        "source": {
            "id": "01-postgres-config",
            "hash": SOURCE_HASH_A,
            "format": "pdf",
            "vendor": "PostgreSQL Global Development Group",
            "product": "PostgreSQL",
            "language": "en",
        },
        "sections": [
            {
                "section_path": section,
                "title": "Configuration Parameters",
                "blocks": blocks,
            }
        ],
    }


def build_source_b() -> dict:
    """SDM sintético corto (12 bloques) para CI rápido."""
    section = "/ch01/intro"
    blocks: list[dict] = []
    idx = 0

    def add(type_: str, content: dict) -> None:
        nonlocal idx
        blocks.append(
            {
                "id": _block_id(SOURCE_HASH_B, section, idx),
                "type": type_,
                "content": content,
                "anchor": {"page": 1 + idx // 4, "section_path": section, "bbox": None},
                "confidence": 1.0,
                "origin": "native",
            }
        )
        idx += 1

    add("definition", {"text": "Una transacción es una unidad atómica de trabajo."})
    add("parameter", {"name": "default_transaction_isolation", "description": "Nivel de aislamiento por defecto."})
    add("default", {"name": "default_transaction_isolation", "value": "read committed"})
    add("error-code", {"code": "EIO", "message": "Error de E/S de bajo nivel."})
    add("warning", {"text": "WARNING: las transacciones largas pueden bloquear el VACUUM.", "severity": "caution"})
    add("formula", {"latex": "n = r \\cdot w", "numbered": True})
    add("example", {"text": "Ejemplo: BEGIN; COMMIT; define una transacción vacía."})
    add("mechanism", {"text": "El aislamiento se implementa mediante MVCC."})
    add("step", {"ordinal": 1, "text": "Iniciar la transacción con BEGIN."})
    add("constraint", {"text": "Una transacción no puede anidar BEGIN explícito."})
    add("tradeoff", {"text": "Mayor aislamiento reduce anomalías pero baja el rendimiento."})
    add("cross-reference", {"target": "/ch02/iso-levels"})

    return {
        "schema_version": "1.0.0",
        "source": {
            "id": "02-postgres-intro",
            "hash": SOURCE_HASH_B,
            "format": "pdf",
            "vendor": "PostgreSQL Global Development Group",
            "product": "PostgreSQL",
            "language": "en",
        },
        "sections": [
            {
                "section_path": section,
                "title": "Introduction",
                "blocks": blocks,
            }
        ],
    }


# -------------------------------------------------------------------
# Ground-truth de criticidad: aplica R1-R5 sobre el SDM.
# -------------------------------------------------------------------


def compute_ground_truth(sdm: dict) -> list[dict]:
    """Devuelve la lista de unidades must-keep según R1–R5.

    `unit_id` es determinista por bloque: `u_<block_id>`. Esto garantiza que
    dos agentes que extraen el mismo bloque obtengan el mismo `unit_id` aunque
    difieran en el orden de las unidades contextuales.
    """
    must_keep: list[dict] = []
    for section in sdm["sections"]:
        for block in section["blocks"]:
            rationale = is_must_keep(block)
            if rationale:
                must_keep.append(
                    {
                        "unit_id": f"u_{block['id']}",
                        "block_id": block["id"],
                        "type": block["type"],
                        "rationale": rationale,
                    }
                )
    return must_keep


# -------------------------------------------------------------------
# Extracciones manuales (dos agentes independientes sobre la misma fuente).
# Coinciden en must-keep al 100 %; difieren en context.
# -------------------------------------------------------------------

def build_extraction(sdm: dict, source_hash: str, agent: str) -> dict:
    """Genera una extracción que satisface R1–R5 y produce cobertura de los 14 tipos.

    `unit_id` es determinista por bloque: `u_<block_id>`. Garantiza que dos
    agentes distintos, con orden de extracción de context divergente, obtengan
    el mismo `unit_id` para el mismo bloque.
    """
    units: list[dict] = []
    for section in sdm["sections"]:
        for block in section["blocks"]:
            t = block["type"]
            rationale = is_must_keep(block)

            unit_id = f"u_{block['id']}"

            # Cualquier unidad que active regla → must-keep (ambos agentes coinciden).
            if rationale:
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "must-keep",
                        "criticality_rationale": rationale,
                        "state": "pending",
                    }
                )
                continue

            # Tipos context. Cada agente extrae un subconjunto ligeramente distinto.
            # agent A incluye `cross-reference` y `version-note`; agent B incluye
            # `formula` no numerada y `tradeoff` adicional. Cobertura de los 14
            # tipos sale entre los dos agentes.
            if t in {"definition", "mechanism", "step", "example", "constraint", "syntax-rule"}:
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "context",
                        "criticality_rationale": None,
                        "state": "pending",
                    }
                )
            elif t == "tradeoff" and agent == "B":
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "context",
                        "criticality_rationale": None,
                        "state": "pending",
                    }
                )
            elif t == "cross-reference" and agent == "A":
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "context",
                        "criticality_rationale": None,
                        "state": "pending",
                    }
                )
            elif t == "version-note" and agent == "A":
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "context",
                        "criticality_rationale": None,
                        "state": "pending",
                    }
                )
            elif t == "formula" and agent == "B":
                units.append(
                    {
                        "unit_id": unit_id,
                        "source_block_ids": [block["id"]],
                        "source_section_path": section["section_path"],
                        "type": t,
                        "content": block["content"],
                        "criticality": "context",
                        "criticality_rationale": None,
                        "state": "pending",
                    }
                )
            # prose (sin info) → no se extrae.

    return {
        "schema_version": "1.0.0",
        "source": {
            "id": sdm["source"]["id"],
            "hash": source_hash,
        },
        "agent": agent,
        "units": units,
    }


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    sdm_a = build_source_a()
    sdm_b = build_source_b()

    (FIX / "source-A.sdm.json").write_text(json.dumps(sdm_a, indent=2, ensure_ascii=False))
    (FIX / "source-B.sdm.json").write_text(json.dumps(sdm_b, indent=2, ensure_ascii=False))

    gt_a = compute_ground_truth(sdm_a)
    gt_b = compute_ground_truth(sdm_b)

    (EXP / "source-A-criticality.json").write_text(json.dumps(gt_a, indent=2))
    (EXP / "source-B-criticality.json").write_text(json.dumps(gt_b, indent=2))

    (FIX / "source-A-extraction-1.json").write_text(
        json.dumps(build_extraction(sdm_a, SOURCE_HASH_A, "A"), indent=2, ensure_ascii=False)
    )
    (FIX / "source-A-extraction-2.json").write_text(
        json.dumps(build_extraction(sdm_a, SOURCE_HASH_A, "B"), indent=2, ensure_ascii=False)
    )
    (FIX / "source-B-extraction-1.json").write_text(
        json.dumps(build_extraction(sdm_b, SOURCE_HASH_B, "A"), indent=2, ensure_ascii=False)
    )
    (FIX / "source-B-extraction-2.json").write_text(
        json.dumps(build_extraction(sdm_b, SOURCE_HASH_B, "B"), indent=2, ensure_ascii=False)
    )

    print(f"source-A: {len(sdm_a['sections'][0]['blocks'])} blocks, {len(gt_a)} must-keep")
    print(f"source-B: {len(sdm_b['sections'][0]['blocks'])} blocks, {len(gt_b)} must-keep")
    return 0


if __name__ == "__main__":
    sys.exit(main())

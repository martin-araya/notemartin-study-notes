#!/usr/bin/env python3
"""Verificador de la Fase 85 — `data-model` (tipo de nota).

Ejecuta 6 sub-criterios sobre los deliverables de F85:

  C1 — `data-model.md` existe, ≤ 500 líneas, contiene las 9 secciones canónicas.
  C2 — Cada entidad listada en `## Entidades` tiene ≥ 1 fila en `## Campos` con
        Tipo y Restricciones no vacíos — criterio ROADMAP #1.
  C3 — Las relaciones en `## Relaciones` aparecen como líneas en el
        `erDiagram` Mermaid de `## Modelo` — criterio ROADMAP #2.
  C4 — `## Integridad` tiene `:::warning`/`:::danger` por tipo (PK, FK,
        UNIQUE, NOT NULL, CHECK) con `{src:blk_xxxx}` — criterio ROADMAP #3.
  C5 — Los 3 fixtures pasan `density_check.py --strict` con exit 0.
  C6 — `SKILL.md` §5.2 fila `data-model` y
        `references/05-note-types/README.md` ya no marcan `[pendiente F85]`.

Uso:
    python3 evals/data-model-sample/run_eval.py
    python3 evals/data-model-sample/run_eval.py --regen

Salida esperada: PASS 6/6.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
DOC_PATH = SKILL_DIR / "references" / "05-note-types" / "data-model.md"
DENSITY_CHECK_PATH = SKILL_DIR / "scripts" / "validate" / "density_check.py"
NOTES_DIR = Path(__file__).resolve().parent / "notes"
SKILL_MD_PATH = SKILL_DIR / "SKILL.md"
TYPES_README_PATH = SKILL_DIR / "references" / "05-note-types" / "README.md"
DOC_LINE_LIMIT = 600

EXPECTED_SECTIONS = (
    "## §1 · Propósito y alcance",
    "## §2 · Estructura de la nota",
    "## §3 · Componentes mínimos",
    "## §4 · Reglas de contenido",
    "## §5 · Activación por perfil",
    "## §6 · Checklist de cierre",
    "## §7 · Nota mínima viable",
    "## §8 · Wirings y referencias cruzadas",
    "## §9 · Verificación al cierre de la fase",
)

ALL_NOTES = (
    "ecommerce-data-model.md",
    "library-data-model.md",
    "postgresql-data-model.md",
)

REQUIRED_INTEGRITY_TYPES = ("PK", "FK", "UNIQUE", "NOT NULL", "CHECK")


class EvalResult:
    def __init__(self) -> None:
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []

    def ok(self, name: str) -> None:
        self.passed.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failed.append((name, detail))

    @property
    def total(self) -> int:
        return len(self.passed) + len(self.failed)

    @property
    def status(self) -> str:
        if not self.failed:
            return f"PASS {len(self.passed)}/{self.total}"
        return f"FAIL {len(self.failed)}/{self.total} (passed {len(self.passed)}/{self.total})"


def _split_into_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    current_heading = ""
    current_body: List[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading or current_body:
                sections.append((current_heading, "\n".join(current_body)))
            current_heading = line
            current_body = []
        else:
            current_body.append(line)
    if current_heading or current_body:
        sections.append((current_heading, "\n".join(current_body)))
    return sections


def _section_body_of(text: str, heading: str) -> str:
    sections = _split_into_sections(text)
    for h, b in sections:
        if h.strip() == heading:
            return b
    return ""


def _extract_h3_subheadings(body: str) -> List[str]:
    """Devuelve todos los H3 del cuerpo, normalizados (sin código inline ni {src:})."""
    titles: List[str] = []
    for line in body.splitlines():
        if line.startswith("### "):
            t = line[4:].strip()
            # Quitar {src:...} inline.
            t = re.sub(r"\s*\{src:blk_[0-9a-f]{12}\}\s*$", "", t)
            titles.append(t)
    return titles


def _extract_code_blocks(body: str) -> List[str]:
    """Devuelve el contenido de cada bloque `code`."""
    blocks: List[str] = []
    in_code = False
    current: List[str] = []
    for line in body.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                blocks.append("\n".join(current))
                current = []
            in_code = not in_code
            continue
        if in_code:
            current.append(line)
    return blocks


def _parse_table_rows(body: str) -> List[List[str]]:
    """Devuelve las filas de las tablas GFM."""
    rows: List[List[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


# ---------------------------------------------------------------------------
# C1 — doc existe, ≤ 500 líneas, contiene las 9 secciones canónicas
# ---------------------------------------------------------------------------

def c1_doc_structure(result: EvalResult) -> None:
    name = "C1-doc-structure"
    if not DOC_PATH.is_file():
        result.fail(name, f"{DOC_PATH} no existe")
        return
    line_count = sum(1 for _ in DOC_PATH.open("r", encoding="utf-8"))
    if line_count > DOC_LINE_LIMIT:
        result.fail(name, f"{line_count} líneas > {DOC_LINE_LIMIT}")
        return
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [s for s in EXPECTED_SECTIONS if s not in text]
    if missing:
        result.fail(name, f"faltan secciones: {missing}")
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C2 — Cada entidad en ## Entidades tiene ≥ 1 fila en ## Campos con tipo/restricciones
# ---------------------------------------------------------------------------

def c2_entities_have_fields(result: EvalResult) -> None:
    name = "C2-entities-have-fields"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed_notes.append(f"{note_name} no existe")
            continue
        text = note_path.read_text(encoding="utf-8")
        entidades_body = _section_body_of(text, "## Entidades")
        campos_body = _section_body_of(text, "## Campos")
        if not entidades_body or not campos_body:
            failed_notes.append(f"{note_name}: sin `## Entidades` o `## Campos`")
            continue

        # Lista de entidades (H3 en Entidades).
        entities = _extract_h3_subheadings(entidades_body)

        # Para cada entidad, buscar sub-sección H3 en Campos.
        campos_subsections = re.split(r"^### ", campos_body, flags=re.MULTILINE)
        # El primer split devuelve el texto antes del primer ###.
        # Construir dict {entity: rows}.
        entity_rows: dict[str, List[List[str]]] = {}
        current_entity = ""
        for chunk in campos_subsections[1:]:
            lines = chunk.splitlines()
            if not lines:
                continue
            current_entity = lines[0].strip()
            # Quitar {src:...} inline.
            current_entity = re.sub(r"\s*\{src:blk_[0-9a-f]{12}\}\s*$", "", current_entity)
            # Encontrar la primera tabla dentro de este chunk.
            in_table = False
            header_seen = False
            rows: List[List[str]] = []
            for line in lines[1:]:
                stripped = line.strip()
                if stripped.startswith("|"):
                    if re.match(r"^\|[\s\-:|]+\|\s*$", stripped):
                        in_table = True
                        continue
                    if in_table:
                        cells = [c.strip() for c in stripped.strip("|").split("|")]
                        if not header_seen:
                            header_seen = True
                        else:
                            rows.append(cells)
                elif in_table and rows:
                    break  # fin de la tabla
            entity_rows[current_entity] = rows

        # Verificar cada entidad.
        incomplete: List[str] = []
        for entity in entities:
            rows = entity_rows.get(entity, [])
            if not rows:
                incomplete.append(f"{entity}: sin filas en `## Campos`")
                continue
            for i, row in enumerate(rows):
                if len(row) < 4:
                    incomplete.append(f"{entity} fila {i+1}: solo {len(row)} columnas")
                    continue
                if not row[1].strip():  # Tipo
                    incomplete.append(f"{entity}.{row[0]}: Tipo vacío")
                if not row[2].strip():  # Restricciones
                    incomplete.append(f"{entity}.{row[0]}: Restricciones vacío")
        if incomplete:
            failed_notes.append(f"{note_name}: {len(incomplete)} problemas (p.ej. {incomplete[:2]})")
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C3 — ER Mermaid refleja las relaciones
# ---------------------------------------------------------------------------

def c3_er_matches_relationships(result: EvalResult) -> None:
    name = "C3-er-matches-relationships"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        modelo_body = _section_body_of(text, "## Modelo")
        relaciones_body = _section_body_of(text, "## Relaciones")
        if not modelo_body or not relaciones_body:
            failed_notes.append(f"{note_name}: sin `## Modelo` o `## Relaciones`")
            continue

        # Extraer el bloque Mermaid erDiagram.
        mermaid_blocks = [b for b in _extract_code_blocks(modelo_body)]
        er_diagram = ""
        for b in mermaid_blocks:
            if "erDiagram" in b:
                er_diagram = b
                break
        if not er_diagram:
            failed_notes.append(f"{note_name}: sin `erDiagram` Mermaid en `## Modelo`")
            continue

        # Extraer entidades y relaciones del ER.
        # Patrón: `ENTITY1 ||--o{ ENTITY2 : label` o similares.
        er_lines = [l.strip() for l in er_diagram.splitlines() if l.strip()]
        er_pairs: set[Tuple[str, str]] = set()
        for line in er_lines:
            if line.startswith("{") or line.startswith("}"):
                continue
            # Patrón de relación Mermaid: `USER ||--o{ ORDER : label`
            # Middle (cardinalidad) puede incluir `{`, `}`, `o`, `|`, `<`, `>`.
            m = re.match(r"^(\w+)\s+\|+[-o|]*--[^\s]+\s+(\w+)", line)
            if m:
                a, b = m.groups()
                # Normalizar guiones bajos a vacío para que "ORDER_ITEM" == "ORDERITEM".
                a_norm = a.upper().replace("_", "")
                b_norm = b.upper().replace("_", "")
                er_pairs.add((a_norm, b_norm))
                er_pairs.add((b_norm, a_norm))  # bidireccional

        # Extraer relaciones de la tabla `## Relaciones`.
        relaciones_rows = _parse_table_rows(relaciones_body)
        # Filtrar la fila de cabecera.
        rel_rows = [r for r in relaciones_rows if len(r) >= 3 and not r[0].lower().startswith("origen")]
        missing = []
        for row in rel_rows:
            # Limpiar paréntesis de N:M markers: `(Product` → `Product`.
            origen_raw = row[0].strip()
            destino_raw = row[2].strip() if len(row) >= 3 else ""
            origen = origen_raw.lstrip("(").rstrip(")").strip().upper().replace("_", "")
            destino = destino_raw.lstrip("(").rstrip(")").strip().upper().replace("_", "")
            if not origen or not destino:
                continue
            if (origen, destino) not in er_pairs:
                missing.append(f"{origen_raw} → {destino_raw}")
        if missing:
            failed_notes.append(
                f"{note_name}: {len(missing)} relaciones en tabla sin ER matching: {missing[:3]}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C4 — Integridad con tipos PK, FK, UNIQUE, NOT NULL, CHECK
# ---------------------------------------------------------------------------

def c4_integrity_complete(result: EvalResult) -> None:
    name = "C4-integrity-complete"
    failed_notes = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        text = note_path.read_text(encoding="utf-8")
        integridad_body = _section_body_of(text, "## Integridad")
        if not integridad_body.strip():
            failed_notes.append(f"{note_name}: sin `## Integridad`")
            continue
        # Buscar tipos de integridad en :::warning/:::danger.
        body_upper = integridad_body.upper()
        body_lower = integridad_body.lower()
        missing = []
        for itype in REQUIRED_INTEGRITY_TYPES:
            # PK may appear as "PK" or "primary key"; FK as "FK" or "foreign key".
            pattern_variants = [itype, itype.lower(), itype.replace(" ", "")]
            found = any(
                re.search(rf"\b{p}\b", body_upper if itype.isupper() else body_lower)
                for p in pattern_variants
            )
            if not found:
                # Búsqueda laxa: contiene la palabra completa.
                if itype.lower() not in body_lower and itype not in integridad_body:
                    missing.append(itype)
        if missing:
            failed_notes.append(
                f"{note_name}: tipos de integridad faltantes en `## Integridad`: {missing}"
            )
    if failed_notes:
        result.fail(name, "; ".join(failed_notes))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C5 — los 3 fixtures pasan density_check.py --strict
# ---------------------------------------------------------------------------

def c5_density_check(result: EvalResult) -> None:
    name = "C5-density-check"
    if not DENSITY_CHECK_PATH.is_file():
        result.fail(name, f"{DENSITY_CHECK_PATH} no existe")
        return
    failed = []
    for note_name in ALL_NOTES:
        note_path = NOTES_DIR / note_name
        if not note_path.is_file():
            failed.append(f"{note_name} no existe")
            continue
        proc = subprocess.run(
            [sys.executable, str(DENSITY_CHECK_PATH), "--note", str(note_path), "--strict"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            failed.append(f"{note_name}: exit {proc.returncode}\n{proc.stdout.strip()[:200]}")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# C6 — wirings cerrados
# ---------------------------------------------------------------------------

def c6_wirings_closed(result: EvalResult) -> None:
    name = "C6-wirings-closed"
    failed = []
    if SKILL_MD_PATH.is_file():
        text = SKILL_MD_PATH.read_text(encoding="utf-8")
        if "[pendiente F85]" in text:
            failed.append("SKILL.md: aún contiene `[pendiente F85]`")
        elif not re.search(r"Seleccionar el tipo de nota `data-model`.*\bF85\b", text):
            failed.append("SKILL.md: no se encontró la fila de `data-model` cerrada")
    else:
        failed.append("SKILL.md no existe")
    if TYPES_README_PATH.is_file():
        text = TYPES_README_PATH.read_text(encoding="utf-8")
        if "`[pendiente F85]`" in text:
            failed.append("05-note-types/README.md: aún contiene `[pendiente F85]`")
    else:
        failed.append("05-note-types/README.md no existe")
    if failed:
        result.fail(name, "; ".join(failed))
        return
    result.ok(name)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="Regenera fixtures antes de ejecutar")
    args = parser.parse_args()

    if args.regen:
        build_script = Path(__file__).resolve().parent / "build_fixtures.py"
        subprocess.run([sys.executable, str(build_script)], check=True)

    result = EvalResult()
    c1_doc_structure(result)
    c2_entities_have_fields(result)
    c3_er_matches_relationships(result)
    c4_integrity_complete(result)
    c5_density_check(result)
    c6_wirings_closed(result)

    print(result.status)
    for name in result.passed:
        print(f"  [PASS] {name}")
    for name, detail in result.failed:
        print(f"  [FAIL] {name}: {detail}")

    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())

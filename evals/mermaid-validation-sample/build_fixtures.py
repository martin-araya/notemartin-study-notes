#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/mermaid-validation-sample/.

Genera un archivo `broken.nm` con los 20 diagramas rotos envueltos en
directivas `:::diagram` (cada uno con alt y src), y un archivo
`valid-checks.yaml` que apunta a los diagramas válidos del repo.

Uso:
    python build_fixtures.py [--out-dir evals/mermaid-validation-sample/fixtures]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "mermaid-validation-sample" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_broken_nm(out: Path) -> None:
    """Genera un archivo `broken.nm` con los 20 diagramas rotos envueltos."""
    rows = [
        ("broken-01", "S-01", "unknownDiagram\n    A --> B"),
        ("broken-02", "S-02", 'flowchart\n    A["x"] --> B["y"]'),
        ("broken-03", "S-03", 'flowchart TD\n    A["texto sin cerrar'),
        ("broken-04", "S-05", "sequenceDiagram\n    participant A as Cliente\n    A->>B"),
        ("broken-05", "S-07", 'erDiagram\n    A ??--o{ B : "test"'),
        ("broken-06", "S-08", "gantt\n    title Tareas\n    Tarea A :a1, 2026-01-01, 5d"),
        ("broken-07", "S-06", "stateDiagram-v2\n    A --> B\n    B --> C"),
        ("broken-08", "S-04", "sequenceDiagram\n    participant 1A as Uno\n    1A->>B:X"),
        ("broken-09", "P-01", "flowchart TD\n    A[Texto sin comillas]"),
        ("broken-10", "P-02", 'flowchart TD\n    Acción["X"]'),
        ("broken-11", "P-03", 'flowchart TD\n    style A fill:#ff0000\n    A["X"] --> B["Y"]'),
        ("broken-12", "P-04", 'flowchart TD\n    A["X"] --> B["Y"]\n    click A "https://example.com"'),
        ("broken-13", "P-05", "%%{init: {'theme':'dark'}}%%\nflowchart TD\n    A[\"X\"] --> B[\"Y\"]"),
        ("broken-14", "P-06", 'flowchart TD\n    A["<b><i>texto</i></b>"]'),
        ("broken-15", "L-01",
         "flowchart TD\n"
         "    N1[\"a\"] --> N2[\"b\"] --> N3[\"c\"] --> N4[\"d\"] --> N5[\"e\"] --> N6[\"f\"] --> "
         "N7[\"g\"] --> N8[\"h\"] --> N9[\"i\"] --> N10[\"j\"] --> N11[\"k\"] --> N12[\"l\"] --> "
         "N13[\"m\"] --> N14[\"n\"] --> N15[\"o\"] --> N16[\"p\"] --> N17[\"q\"] --> N18[\"r\"] --> "
         "N19[\"s\"] --> N20[\"t\"]"),
        ("broken-16", "L-04", 'flowchart TD\n    A["texto de más de 40 caracteres en una sola línea sin break"]'),
        ("broken-17", "L-05", 'flowchart TB\n    subgraph X\n        subgraph Y\n            subgraph Z\n                A["x"]\n            end\n        end\n    end'),
        ("broken-18", "L-01",
         "gantt\n    dateFormat YYYY-MM-DD\n    title Con 30 hitos\n" +
         "\n".join(f"    T{i:02d} :t{i:02d}, 2026-01-{i:02d}, 1d" for i in range(1, 31))),
        ("broken-19", "S-05", "sequenceDiagram\n    A->>B:X\n    alt Condición\n        B-->>A:Y\n    end"),
        ("broken-20", "L-06", 'flowchart TD\n    A["X"] --> B["Y"]'),
    ]

    lines: list[str] = []
    lines.append("# F67 — 20 diagramas rotos a propósito (Fase 67 criterio 1)")
    lines.append("# Cada bloque :::diagram contiene una violación específica.")
    lines.append("")
    for did, rule_id, content in rows:
        # broken-20 specifically: missing alt (accesibilidad)
        if did == "broken-20":
            lines.append(f":::diagram src=\"blk_{did}\"")
        else:
            lines.append(f':::diagram src="blk_{did}" alt="Diagrama roto {did}"')
        lines.append("```mermaid")
        lines.append(content)
        lines.append("```")
        lines.append(":::")
        lines.append("")

    write(out / "broken.nm", "\n".join(lines))


def build_valid_checks(out: Path) -> None:
    """Genera valid-checks.yaml con los diagramas válidos del repo.

    IMPORTANTE: el regex de extracción del validador captura tanto las plantillas
    (con placeholders como <entrada>) como los ejemplos reales. En el catalog, los
    bloques están intercalados: plantilla, ejemplo, plantilla, ejemplo, ...
    Para usar el ejemplo real de cada tipo, hay que saltar la plantilla previa.
    El catalog tiene 10 plantillas (índices 0,2,4,6,8,10,12,14,16,18) y 10
    ejemplos (índices 1,3,5,7,9,11,13,15,17,19) según el regex del validador.

    También se excluye T4 (índice 7) porque su ejemplo usa 'Raíz' como ID, lo que
    dispara la regla P-02 intencionalmente (el catalog lo usa para mostrar la
    violación).
    """
    portable_path = "skill/notemartin-study-notes/references/07-visual/mermaid-portable.md"
    catalog_path = "skill/notemartin-study-notes/references/07-visual/diagram-catalog.md"

    rows = [
        # 9 plantillas WP-1..WP-9 (índices 1-9 en portable, saltando el genérico idx 0)
        (portable_path, 1, "Plantilla WP-1 flowchart"),
        (portable_path, 2, "Plantilla WP-2 sequenceDiagram"),
        (portable_path, 3, "Plantilla WP-3 stateDiagram-v2"),
        (portable_path, 4, "Plantilla WP-4 erDiagram"),
        (portable_path, 5, "Plantilla WP-5 classDiagram"),
        (portable_path, 6, "Plantilla WP-6 gantt"),
        (portable_path, 7, "Plantilla WP-7 gitGraph"),
        (portable_path, 8, "Plantilla WP-8 pie"),
        (portable_path, 9, "Plantilla WP-9 subgraph"),
        # 9 ejemplos REALES del catalog (índices impares: 1,3,5,9,11,13,15,17,19)
        # (T1=1, T2=3, T3=5, T5=9, T6=11, T7=13, T8=15, T9=17, T10=19)
        # T4 (idx 7) se excluye porque su ejemplo usa 'Raíz' como ID → P-02.
        (catalog_path, 1, "T1 Sobrecarga C++"),
        (catalog_path, 3, "T2 Query PostgreSQL"),
        (catalog_path, 5, "T3 Pod Kubernetes"),
        (catalog_path, 9, "T5 Catálogo SQL"),
        (catalog_path, 11, "T6 PostgreSQL capas"),
        (catalog_path, 13, "T7 Dependencias PostgreSQL"),
        (catalog_path, 15, "T8 Cronología HTTP"),
        (catalog_path, 17, "T9 Memoria del motor BD"),
        (catalog_path, 19, "T10 expression C++"),
        # (sin entradas adicionales; 18 + 1 explícito en portable.md = 19 total).
    ]

    lines = ["# F67 — Diagramas válidos del repo (Fase 67 criterio 2).",
             "# Generado por build_fixtures.py.",
             "# Solo se incluyen los ejemplos de mermaid-portable.md y los ejemplos REALES",
             "# del catalog (saltando las plantillas con placeholders). T4 se excluye",
             "# porque su ejemplo usa 'Raíz' como ID, lo que dispara P-02 intencionalmente.",
             "diagramas_validos:"]
    for path, idx, desc in rows:
        lines += [
            f"  - path: \"{path}\"",
            f"    bloque_esperado_idx: {idx}",
            f"    descripcion: \"{desc}\"",
        ]
    write(out / "valid-checks.yaml", "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    build_broken_nm(out)
    build_valid_checks(out)
    print(f"Fixtures generadas en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

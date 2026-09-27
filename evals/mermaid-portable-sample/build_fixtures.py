#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/mermaid-portable-sample/.

Las fixtures YAML codifican lo que el catálogo debe verificar:
- whitelist.yaml: 9 tipos portables (WP-1 … WP-9).
- blacklist.yaml: 16 entradas con alternativa explícita.
- writing-rules.yaml: 6 reglas R-MP-01 … R-MP-06 con casos PASS/FAIL.
- three-dest-render.yaml: matriz 3 destinos × N constructs.
- acentos-ñ.yaml: 10+ etiquetas con acentos/ñ + veredicto.

Uso:
    python build_fixtures.py [--out-dir evals/mermaid-portable-sample/fixtures]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "mermaid-portable-sample" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_whitelist(out: Path) -> None:
    tipos = [
        ("WP-1", "flowchart", "T1, T4, T6, T7, T9, T10"),
        ("WP-2", "sequenceDiagram", "T2"),
        ("WP-3", "stateDiagram-v2", "T3"),
        ("WP-4", "erDiagram", "T5"),
        ("WP-5", "classDiagram", "(sin equivalente F65)"),
        ("WP-6", "gantt", "T8"),
        ("WP-7", "gitGraph", "(sin equivalente F65)"),
        ("WP-8", "pie", "(sin equivalente F65)"),
        ("WP-9", "flowchart con subgraph", "T4, T6"),
    ]
    lines = ["# 9 tipos portables (WP-1 … WP-9) declarados en §3.",
             "# Generado por build_fixtures.py.",
             "tipos:"]
    for wid, nombre, equiv in tipos:
        lines += [
            f"  - id: {wid}",
            f"    nombre: \"{nombre}\"",
            f"    equivalente_f65: \"{equiv}\"",
        ]
    write(out / "whitelist.yaml", "\n".join(lines) + "\n")


def build_blacklist(out: Path) -> None:
    rows = [
        ("LN-1", "pie con etiquetas >12 chars", "Tabla markdown 2 columnas (categoría | valor)", ""),
        ("LN-2", "journey", "flowchart LR con swimlanes por lanes nombradas", "F65 T7"),
        ("LN-3", "timeline (Mermaid 10+)", "gantt con section", "F65 T8"),
        ("LN-4", "mindmap", "flowchart TB jerárquico", "F65 T4"),
        ("LN-5", "radar", "Tabla con valores por dimensión", ""),
        ("LN-6", "sankey-beta", "flowchart LR con aristas etiquetadas", "F65 T7"),
        ("LN-7", "C4 / architecture-beta", "flowchart con subgraph siguiendo convención C4", "F65 T6"),
        ("LN-8", "style X fill:#hex", "classDef con nombre semántico + tokens F72", "F72"),
        ("LN-9", "click A callback, linkStyle", "Documentar enlace en prosa adyacente o nota al pie", ""),
        ("LN-10", "init con theme/themeVariables", "Tema por defecto; tema por destino si F73 aplica", "F73"),
        ("LN-11", "init con flowchart.htmlLabels: false", "Usar etiquetas sin HTML (<br/> solo si los 3 destinos lo soportan)", ""),
        ("LN-12", "HTML labels complejos (<b>, <i>, <sub>)", "Markdown inline en etiquetas (Mermaid 10+: **bold**, *italic*)", ""),
        ("LN-13", "Subgraphs anidados >2 niveles", "Partir en 2 diagramas enlazados o usar classDef", "F65 §6"),
        ("LN-14", "IDs Unicode (Acción[\"x\"])", "ASCII ID + acento en etiqueta (Accion[\"Acción\"])", ""),
        ("LN-15", "Imágenes embebidas (img://...) en nodos", "Usar :::figure separada referenciada desde el caption", "F65 §3"),
        ("LN-16", "block-beta (experimental)", "flowchart TB con subgraph", "F65 T4/T6"),
    ]
    lines = ["# Generado por build_fixtures.py.", "blacklist:"]
    for lid, construct, alternativa, wirings in rows:
        lines += [
            f"  - id: {lid}",
            f"    construct: \"{construct}\"",
            f"    alternativa: \"{alternativa}\"",
            f"    wirings: \"{wirings}\"",
        ]
    write(out / "blacklist.yaml", "\n".join(lines) + "\n")


def build_writing_rules(out: Path) -> None:
    rows = [
        ("R-MP-01", "Etiquetas siempre entrecomilladas",
         'A["texto"]', "A[texto]"),
        ("R-MP-02", "IDs ASCII; acentos en etiqueta",
         'Cliente_Nino["Cliente (niño)"]', 'Cliente_Niño["Cliente"]'),
        ("R-MP-03", "≤40 chars por línea, ≤60 con <br/>",
         'A["PostgreSQL: motor<br/>MVCC"]',
         'A["PostgreSQL motor transaccional con control de concurrencia multiversión"]'),
        ("R-MP-04", "classDef con nombre semántico; sin style literal",
         "classDef warning fill:#ff6b6b; class A warning",
         "style A fill:#ff0000"),
        ("R-MP-05", "Subgraphs anidados ≤2 niveles",
         "subgraph X con 1 nivel interno",
         "subgraph X con subgraph Y con subgraph Z (3 niveles)"),
        ("R-MP-06", "Sin click, linkStyle, init con theme",
         'A["X"] sin directivas',
         'click A "https://..."'),
    ]
    lines = ["# Generado por build_fixtures.py.", "reglas:"]
    for rid, regla, pass_, fail in rows:
        lines += [
            f"  - id: {rid}",
            f"    regla: \"{regla}\"",
            f"    pass: \"{pass_}\"",
            f"    fail: \"{fail}\"",
        ]
    write(out / "writing-rules.yaml", "\n".join(lines) + "\n")


def build_three_dest_render(out: Path) -> None:
    lines = ["# Generado por build_fixtures.py.",
             "matriz_destinos:",
             "  columnas: [\"Obsidian\", \"Notion import\", \"GitHub\"]",
             "  estados_requeridos_notion_import:",
             "    ok: 5",
             "    warning: 2",
             "    no: 5",
             "  filas:"]
    rows = [
        ("flowchart TB/LR con [], {}, (), [[]], [()]", "ok", "ok", "ok"),
        ("subgraph id con ≤2 niveles", "ok", "ok", "ok"),
        ("sequenceDiagram con participant y Note", "ok", "ok", "ok"),
        ("stateDiagram-v2 con note", "ok", "ok", "ok"),
        ("erDiagram crow's foot", "ok", "ok", "ok"),
        ("classDiagram", "ok", "ok", "ok"),
        ("gantt con section, milestone, active", "ok", "ok", "ok"),
        ("gitGraph básico", "ok", "ok", "ok"),
        ("pie con etiquetas ≤12 chars", "ok", "warning", "ok"),
        ("Etiquetas UTF-8 (acentos, ñ)", "ok", "ok", "ok"),
        ("Etiquetas HTML inline (<br/>, <b>)", "ok", "warning", "ok"),
        ("classDef <name> fill:#hex + class", "ok", "ok", "ok"),
        ("style X fill:#hex literal", "ok", "no", "ok"),
        ("click X url", "ok", "no", "ok"),
        ("%%{init:...}%%", "ok", "no", "ok"),
        ("linkStyle N stroke", "ok", "no", "ok"),
        ("Tema custom (theme: dark)", "ok", "no", "ok"),
        ("Comentarios %% ... %%", "ok", "ok", "ok"),
    ]
    for construct, obs, ni, gh in rows:
        lines += [
            f"    - construct: \"{construct}\"",
            f"      obsidian: {obs}",
            f"      notion_import: {ni}",
            f"      github: {gh}",
        ]
    write(out / "three-dest-render.yaml", "\n".join(lines) + "\n")


def build_acentos(out: Path) -> None:
    rows = [
        ("cliente_nino", "Cliente_Nino", "Cliente (niño)", True, True, True, True, True, ""),
        ("accion_acento", "Accion", "Acción con acento", True, True, True, True, True, ""),
        ("anio_2026", "Anio_2026", "Año 2026 — España", True, True, True, True, True, ""),
        ("pequeno", "Pequeno", "Pequeño en acción", True, True, True, True, True, ""),
        ("categoria_espanol", "Categoria", "Categoría en español", True, True, True, True, True, ""),
        ("descripcion", "Descripcion", "Descripción técnica", True, True, True, True, True, ""),
        ("libro_magico", "Libro_Magico", "Libro mágico", True, True, True, True, True, ""),
        ("cumpleanos", "Cumpleanos", "Cumpleaños 2026", True, True, True, True, True, ""),
        ("sin_comillas_fail", "A", "Acción", True, False, True, False, True, ""),
        ("id_con_acento_fail", "Acción", "Acción", False, True, True, False, True, ""),
        ("remplazos_ascii", "nino", "nino (remplazo ASCII)", True, True, True, True, True, "Remplazo ASCII seguro según §6.4"),
    ]
    lines = ["# Generado por build_fixtures.py.", "etiquetas:"]
    for (eid, idn, etq, ascii, com, po, pn, pg, nota) in rows:
        lines += [
            f"  - id: {eid}",
            f"    id_nodo: \"{idn}\"",
            f"    etiqueta: \"{etq}\"",
            f"    ascii_id: {str(ascii).lower()}",
            f"    comillas: {str(com).lower()}",
            f"    portable_obsidian: {str(po).lower()}",
            f"    portable_notion_import: {str(pn).lower()}",
            f"    portable_github: {str(pg).lower()}",
        ]
        if nota:
            lines.append(f"    nota: \"{nota}\"")
    write(out / "acentos-ñ.yaml", "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    build_whitelist(out)
    build_blacklist(out)
    build_writing_rules(out)
    build_three_dest_render(out)
    build_acentos(out)

    print(f"Fixtures regeneradas en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

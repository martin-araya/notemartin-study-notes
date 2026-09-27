#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/diagram-catalog-sample/.

Las fixtures YAML codifican lo que el catálogo debe verificar:
- positive-intentions.yaml: los 10 tipos con su intención primaria.
- corpus-coverage.yaml: 14 fuentes del corpus con tipo elegido y razón.
- fifteen-nodes-decision.yaml: 8 casos de tamaño con veredicto esperado.
- obligatoriedad.yaml: 5 situaciones (3 obligatorias + 2 opcionales).
- matrix-resolution.yaml: 20 intenciones no listadas en §3 con fallback.
- no-vision-examples.txt: lista negra de términos de visión por computador.

Uso:
    python build_fixtures.py [--out-dir evals/diagram-catalog-sample/fixtures]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "diagram-catalog-sample" / "fixtures"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_positive_intentions(out: Path) -> None:
    tipos = [
        ("T1", "T1 — Decisión", "flowchart", "I-1", 6),
        ("T2", "T2 — Secuencia", "sequenceDiagram", "I-2", 4),
        ("T3", "T3 — Estados", "stateDiagram-v2", "I-3", 3),
        ("T4", "T4 — Jerarquía", "flowchart", "I-4", 6),
        ("T5", "T5 — Modelo de datos", "erDiagram", "I-5", 4),
        ("T6", "T6 — Capas", "flowchart", "I-6", 4),
        ("T7", "T7 — Dependencias", "flowchart", "I-7", 5),
        ("T8", "T8 — Cronología de versiones", "gantt", "I-8", 4),
        ("T9", "T9 — Estructura de memoria", "flowchart", "I-9", 4),
        ("T10", "T10 — Gramática", "flowchart", "I-10", 4),
    ]
    lines = ["# 10 tipos canónicos del catálogo (§4) con su intención primaria.",
             "# Generado por build_fixtures.py; no editar a mano.",
             "tipos:"]
    for tid, title, mermaid, intent, min_nodes in tipos:
        lines += [
            f"  - id: {tid}",
            f"    titulo_esperado: \"{title}\"",
            f"    tipo_mermaid: \"{mermaid}\"",
            f"    intencion_primaria: \"{intent}\"",
            f"    nodos_ejemplo_min: {min_nodes}",
        ]
    write(out / "positive-intentions.yaml", "\n".join(lines) + "\n")


def build_corpus_coverage(out: Path) -> None:
    rows = [
        ("01-postgresql-chapter", "capas + flujo de una query", "T6 + T2",
         "Arquitectura por capas del motor + secuencia de una query"),
        ("02-database-internals-chapter", "estructuras internas (memoria, B-tree)", "T5 + T9 + T6",
         "Modelo ER + regiones de memoria + capas del motor"),
        ("03-rfc-7231", "gramática ABNF + estados HTTP", "T10 + T3",
         "Gramática de métodos + máquina de estados HTTP"),
        ("04-arxiv-two-column", "definiciones formales + teoremas", "sin diagrama",
         "Texto matemático denso; tabla de teoremas si hace falta resumen"),
        ("05-iso-sql-tables", "modelo de datos relacional", "T5",
         "ER explícito del catálogo"),
        ("06-kubernetes-api-ref", "jerarquía de recursos + RBAC", "T4 + T1",
         "Jerarquía de recursos + árbol de decisión RBAC"),
        ("07-docker-cli-ref", "capas del demonio + árbol de comandos", "T6 + T4",
         "Capas del demonio + jerarquía de sub-comandos"),
        ("08-conference-transcript", "línea temporal de intervenciones", "T8",
         "Cronología por bloques temáticos"),
        ("09-conference-slides", "una idea por slide", "sin diagrama",
         "Cada slide es atómica; `:::diagram` opcional por slide"),
        ("10-postgres-readme-repo", "dependencias del repo + flujo CI", "T7",
         "Grafo de módulos + estado de jobs"),
        ("11-iso-cpp-syntax", "gramática C++ + decisión de overload", "T10 + T1",
         "Sobrecarga como T1; gramática completa en F69"),
        ("12-arxiv-formulas", "derivaciones matemáticas", "sin diagrama",
         "Ecuaciones con `:::equation`; no diagrama"),
        ("13-internet-archive-scan-hostil", "estructura del libro (capítulos)", "T8",
         "Cronología de capítulos del libro hostil"),
        ("14-book-bad-numbering-hostil", "workflow de normalización", "T2",
         "Secuencia del procedimiento de reparación de numeración"),
    ]
    lines = ["# Cobertura del corpus: 14 fuentes con tipo elegido y razón no trivial.",
             "# Generado por build_fixtures.py.",
             "cobertura:"]
    for fuente, intencion, tipo, razon in rows:
        lines += [
            f"  - fuente: \"{fuente}\"",
            f"    intencion: \"{intencion}\"",
            f"    tipo: \"{tipo}\"",
            f"    razon_no_vacia: \"{razon}\"",
        ]
    write(out / "corpus-coverage.yaml", "\n".join(lines) + "\n")


def build_fifteen_nodes(out: Path) -> None:
    casos = [
        ("tiny", 5, "T1", "unico"),
        ("small", 10, "T1", "unico_subgraphs"),
        ("medium", 18, "T2", "partir"),
        ("large", 30, "T7", "tabla"),
        ("gantt_excepcion", 20, "T8", "unico"),
        ("jerarquia_excepcion", 22, "T4", "unico"),
        ("gramatica_sin_excepcion", 16, "T10", "partir"),
        ("boundary_15", 15, "T1", "partir"),
    ]
    lines = ["# Generado por build_fixtures.py.",
             "casos:"]
    for cid, nodos, tipo, verdict in casos:
        lines += [
            f"  - id: \"{cid}\"",
            f"    nodos: {nodos}",
            f"    tipo: \"{tipo}\"",
            f"    verdict: \"{verdict}\"",
        ]
    write(out / "fifteen-nodes-decision.yaml", "\n".join(lines) + "\n")


def build_obligatoriedad(out: Path) -> None:
    casos = [
        ("arq_3_componentes", "architecture", 3, 2, "obligatorio"),
        ("arq_2_componentes", "architecture", 2, 1, "opcional"),
        ("moc_6_hijos", "index-moc", 6, 5, "obligatorio"),
        ("proc_lineal", "procedure", 5, 0, "opcional"),
        ("proc_3_caminos", "procedure", 8, 3, "obligatorio"),
    ]
    lines = ["# Generado por build_fixtures.py.", "casos:"]
    for cid, tipo_nota, ent, rel, esperado in casos:
        lines += [
            f"  - id: \"{cid}\"",
            f"    tipo_nota: \"{tipo_nota}\"",
            f"    entidades: {ent}",
            f"    relaciones: {rel}",
            f"    esperado: \"{esperado}\"",
        ]
    write(out / "obligatoriedad.yaml", "\n".join(lines) + "\n")


def build_matrix_resolution(out: Path) -> None:
    rows = [
        ("receta de cocina", "sin diagrama"),
        ("lista de comandos CLI sin dependencias", "sin diagrama"),
        ("fórmula matemática única", "sin diagrama"),
        ("definición de un solo término", "sin diagrama"),
        ("tabla de comparación de 5 alternativas", "sin diagrama"),
        ("color picker con 8 hex", "sin diagrama"),
        ("flujo narrativo de un proceso sin decisiones", "sin diagrama"),
        ("árbol genealógico de un personaje", "T4"),
        ("registro de versiones de un binario", "T8"),
        ("historia de un commit en git", "T8"),
        ("mapa de calles de una ciudad", "T7"),
        ("tabla periódica de los elementos", "sin diagrama"),
        ("diagrama de clases UML", "T5"),
        ("secuencia de boot de un SO", "T2"),
        ("API REST con un endpoint y 2 parámetros", "sin diagrama"),
        ("organigrama de una empresa pequeña", "T4"),
        ("memoria virtual con paginación", "T9"),
        ("compilador: fases léxico→sintáctico→semántico", "T6"),
        ("esquema de colores RGB", "sin diagrama"),
        ("árbol de decisión de un clasificador", "T1"),
    ]
    lines = ["# Generado por build_fixtures.py.", "intenciones_fuera_de_matriz:"]
    for intent, esperado in rows:
        lines += [
            f"  - intencion: \"{intent}\"",
            f"    esperado: \"{esperado}\"",
        ]
    write(out / "matrix-resolution.yaml", "\n".join(lines) + "\n")


def build_no_vision_examples(out: Path) -> None:
    terms = [
        "CNN", "convolution", "convolutional", "RNN", "recurrent neural",
        "transformer", "YOLO", "segmentation", "object detection", "detection",
        "SLAM", "calibration", "optical flow", "GAN", "autoencoder", "ResNet",
        "VGG", "U-Net", "Mask R-CNN", "pose estimation", "depth map",
        "feature map", "kernel", "stride", "pooling", "fully connected layer",
        "semantic segmentation", "instance segmentation", "backbone",
        "encoder-decoder", "deconvolution", "upsampling", "downsampling",
        "attention head", "self-attention", "multi-head attention",
        "batch normalization", "dropout", "loss function", "gradient descent",
        "backpropagation", "inception", "mobilenet", "efficientnet",
        "token embedding", "positional encoding",
    ]
    write(out / "no-vision-examples.txt", "\n".join(terms) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR,
                        help="Directorio de salida de las fixtures.")
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    build_positive_intentions(out)
    build_corpus_coverage(out)
    build_fifteen_nodes(out)
    build_obligatoriedad(out)
    build_matrix_resolution(out)
    build_no_vision_examples(out)

    print(f"Fixtures regeneradas en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

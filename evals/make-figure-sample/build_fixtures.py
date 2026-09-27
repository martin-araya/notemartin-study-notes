#!/usr/bin/env python3
"""
Genera fixtures reproducibles para evals/make-figure-sample/.

Crea 6 specs (uno por tipo de figura) + 1 spec inválida (sin source_refs)
para verificar el criterio 3 de F70.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "evals" / "make-figure-sample" / "fixtures"


def write(path: Path, content: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")


def make_spec(figure_type: str, title: str, series: list, **kwargs) -> dict:
    return {
        "schema_version": "1.0.0",
        "figure_type": figure_type,
        "title": title,
        "theme": "light",
        "x_axis_label": kwargs.get("x_axis_label", "X"),
        "y_axis_label": kwargs.get("y_axis_label", "Y"),
        "series": series,
        "alt_text": f"Alt text auto-generado para {title}.",
        "reading_phrase": f"Frase de lectura para {title}.",
    }


def build_bar(out: Path) -> None:
    write(out / "bar.json", make_spec(
        "bar", "Rendimiento PostgreSQL vs MySQL",
        series=[
            {
                "name": "PostgreSQL 16",
                "color_token": "okabe-ito-blue",
                "source_refs": ["blk_pg_001", "blk_pg_002"],
                "data": [
                    {"category": "SELECT", "value": 12.3, "source_ref": "blk_pg_001"},
                    {"category": "INSERT", "value": 45.6, "source_ref": "blk_pg_002"},
                ],
            },
            {
                "name": "MySQL 8",
                "color_token": "okabe-ito-vermillion",
                "source_refs": ["blk_my_001"],
                "data": [
                    {"category": "SELECT", "value": 45.0, "source_ref": "blk_my_001"},
                    {"category": "INSERT", "value": 70.0, "source_ref": "blk_my_001"},
                ],
            },
        ],
    ))


def build_line(out: Path) -> None:
    write(out / "line.json", make_spec(
        "line", "Tendencia de latencia",
        x_axis_label="Mes",
        y_axis_label="Latencia (ms)",
        series=[
            {
                "name": "API A",
                "color_token": "okabe-ito-blue",
                "source_refs": ["blk_api_a_001"],
                "data": [
                    {"category": "Ene", "value": 100, "source_ref": "blk_api_a_001"},
                    {"category": "Feb", "value": 80, "source_ref": "blk_api_a_001"},
                    {"category": "Mar", "value": 60, "source_ref": "blk_api_a_001"},
                ],
            },
            {
                "name": "API B",
                "color_token": "okabe-ito-vermillion",
                "source_refs": ["blk_api_b_001"],
                "data": [
                    {"category": "Ene", "value": 90, "source_ref": "blk_api_b_001"},
                    {"category": "Feb", "value": 85, "source_ref": "blk_api_b_001"},
                    {"category": "Mar", "value": 75, "source_ref": "blk_api_b_001"},
                ],
            },
        ],
    ))


def build_heatmap(out: Path) -> None:
    write(out / "heatmap.json", make_spec(
        "heatmap", "Correlación variables",
        series=[
            {
                "name": "Correlación",
                "color_token": "okabe-ito-blue",
                "source_refs": ["blk_corr_001"],
                "data": [
                    {"category": "A,A", "value": 1.0, "source_ref": "blk_corr_001"},
                    {"category": "A,B", "value": 0.5, "source_ref": "blk_corr_001"},
                    {"category": "A,C", "value": 0.3, "source_ref": "blk_corr_001"},
                    {"category": "B,A", "value": 0.5, "source_ref": "blk_corr_001"},
                    {"category": "B,B", "value": 1.0, "source_ref": "blk_corr_001"},
                    {"category": "B,C", "value": 0.7, "source_ref": "blk_corr_001"},
                ],
            },
        ],
    ))


def build_confusion_matrix(out: Path) -> None:
    write(out / "confusion_matrix.json", make_spec(
        "confusion_matrix", "Matriz de confusión",
        series=[
            {
                "name": "Counts",
                "color_token": "okabe-ito-blue",
                "source_refs": ["blk_cm_001"],
                "data": [
                    {"category": "cat,cat", "value": 80, "source_ref": "blk_cm_001"},
                    {"category": "cat,dog", "value": 5, "source_ref": "blk_cm_001"},
                    {"category": "dog,cat", "value": 10, "source_ref": "blk_cm_001"},
                    {"category": "dog,dog", "value": 90, "source_ref": "blk_cm_001"},
                ],
            },
        ],
    ))


def build_distribution(out: Path) -> None:
    write(out / "distribution.json", make_spec(
        "distribution", "Distribución de latencia",
        x_axis_label="Latencia (ms)",
        y_axis_label="Frecuencia",
        series=[
            {
                "name": "Count",
                "color_token": "okabe-ito-blue",
                "source_refs": ["blk_dist_001"],
                "data": [
                    {"category": "0-10", "value": 5, "source_ref": "blk_dist_001"},
                    {"category": "10-20", "value": 12, "source_ref": "blk_dist_001"},
                    {"category": "20-30", "value": 25, "source_ref": "blk_dist_001"},
                    {"category": "30-40", "value": 30, "source_ref": "blk_dist_001"},
                    {"category": "40-50", "value": 18, "source_ref": "blk_dist_001"},
                    {"category": "50-60", "value": 10, "source_ref": "blk_dist_001"},
                ],
            },
        ],
    ))


def build_before_after(out: Path) -> None:
    write(out / "before_after.json", make_spec(
        "before_after", "Antes/después de optimización",
        x_axis_label="Categoría",
        y_axis_label="Tiempo (s)",
        series=[
            {
                "name": "Antes",
                "color_token": "okabe-ito-vermillion",
                "source_refs": ["blk_before_001"],
                "data": [
                    {"category": "Query 1", "value": 5.0, "source_ref": "blk_before_001"},
                    {"category": "Query 2", "value": 8.0, "source_ref": "blk_before_001"},
                    {"category": "Query 3", "value": 3.0, "source_ref": "blk_before_001"},
                ],
            },
            {
                "name": "Después",
                "color_token": "okabe-ito-bluish-green",
                "source_refs": ["blk_after_001"],
                "data": [
                    {"category": "Query 1", "value": 1.5, "source_ref": "blk_after_001"},
                    {"category": "Query 2", "value": 2.0, "source_ref": "blk_after_001"},
                    {"category": "Query 3", "value": 0.8, "source_ref": "blk_after_001"},
                ],
            },
        ],
    ))


def build_missing_refs(out: Path) -> None:
    """Spec inválida: serie sin source_refs (criterio 3 fallido)."""
    spec = make_spec(
        "bar", "Test missing refs",
        series=[
            {
                "name": "BadSeries",
                "color_token": "okabe-ito-blue",
                "source_refs": [],  # ← vacío
                "data": [
                    {"category": "A", "value": 1.0, "source_ref": ""},
                ],
            },
        ],
    )
    write(out / "missing-refs.json", spec)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    build_bar(out)
    build_line(out)
    build_heatmap(out)
    build_confusion_matrix(out)
    build_distribution(out)
    build_before_after(out)
    build_missing_refs(out)
    print(f"Fixtures generadas en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

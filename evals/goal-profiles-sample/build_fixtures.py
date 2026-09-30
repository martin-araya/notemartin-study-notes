#!/usr/bin/env python3
"""Generador de fixtures para la Fase 105 — `goal-profiles`.

Produce en `evals/goal-profiles-sample/fixtures/`:

  - `profile.yaml` con `goal_profile: hybrid` + `certification.objectives[]`
    (3 objetivos: ckad-core-1, ckad-core-2, psql-admin-1).
  - `study-paths/postgresql.json` con 3 rutas (output de F104).
  - `notemark/` con 3 notas NoteMark:
    - `pg-mvcc-concept.nm` (concept con `## Decisiones de diseño` +
      `## Explicación oral` para perfil `interview`)
    - `k8s-pods.nm` (concept con `## Objetivos oficiales` +
      `## Cobertura por objetivo` + `certification-objective: [ckad-core-1]`)
    - `nginx-quick.nm` (configuration sin secciones adicionales — perfil
      `work` no añade secciones).
  - `knowledge/note-plan.json` con las 3 notas.

Uso:
    python3 evals/goal-profiles-sample/build_fixtures.py            # genera si no existe
    python3 evals/goal-profiles-sample/build_fixtures.py --force    # regenera
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _frontmatter(**fields) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _build_profile_yaml() -> str:
    return """# Profile fixture para F105 — eval goal-profiles-sample.
# Ver references/09-study/goal-profiles.md §2.

use_case_profile: hybrid
goal_profile: hybrid

certification:
  objectives:
    - id: "ckad-core-1"
      description: "Core Concepts (13 %)"
    - id: "ckad-core-2"
      description: "Configuration (18 %)"
    - id: "psql-admin-1"
      description: "Architecture and Design (15 %)"
"""


def _build_note_plan() -> dict:
    return {
        "schema_version": "1.0.0",
        "notes": [
            {"note_id": "pg-mvcc-concept", "concept_ids": ["pg-mvcc"],
             "depends_on": [], "note-type": "concept", "domain": "postgresql"},
            {"note_id": "k8s-pods", "concept_ids": ["k8s-pod-basics"],
             "depends_on": [], "note-type": "concept", "domain": "kubernetes"},
            {"note_id": "nginx-quick", "concept_ids": ["nginx-quick"],
             "depends_on": [], "note-type": "configuration", "domain": "nginx"},
        ],
        "metadata": {
            "generated_at": "2026-09-30T00:00:00Z",
            "source": "goal-profiles-sample",
        },
    }


def _build_pg_mvcc_note() -> str:
    """Nota concept con secciones extra para `interview`."""
    fm = _frontmatter(
        title='"MVCC y snapshot isolation"',
        **{"note-type": "concept", "status": "published",
           "summary": "\"MVCC da a cada transacción un snapshot al inicio.\"",
           "reading-time-minutes": 12,
           "language": "es",
           "tags": "[type/concept, domain/postgresql, f105/goal-profiles]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "postgresql",
        }
    )
    body = "\n# MVCC y snapshot isolation\n\n"
    body += "## TL;DR\n\nMVCC da a cada transacción un snapshot al inicio.\n\n"
    body += "## Mecanismo\n\nCada fila lleva marcas `xmin` y `xmax`.\n"
    body += "{src:blk_pg_mvcc_1}\n"
    body += "\n## Decisiones de diseño\n\n"
    body += "1. **Snapshot por transacción.** Trade-off: simplicidad vs memoria por snapshot.\n"
    body += "2. **Marcas por fila.** Trade-off: espacio en heap vs index lookup.\n"
    body += "\n## Explicación oral\n\n"
    body += "Explicar MVCC a un entrevistador: 'cada transacción ve una foto fija del database al momento de empezar, sin esperar a que otras transacciones terminen. Esto evita lecturas sucias a costa de mantener múltiples versiones por fila.'\n"
    return fm + body


def _build_k8s_pods_note() -> str:
    """Nota concept con secciones extra para `certification`."""
    fm = _frontmatter(
        title='"Kubernetes Pods"',
        **{"note-type": "concept", "status": "published",
           "summary": "\"Pods son la unidad mínima de scheduling en Kubernetes.\"",
           "reading-time-minutes": 10,
           "language": "es",
           "tags": "[type/concept, domain/kubernetes, f105/goal-profiles]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "kubernetes",
           "certification-objective": "[ckad-core-1, ckad-core-2]",
        }
    )
    body = "\n# Kubernetes Pods\n\n"
    body += "## TL;DR\n\nPods son la unidad mínima de scheduling.\n\n"
    body += "## Mecanismo\n\nUn Pod encapsula uno o más contenedores con networking y storage compartido.\n"
    body += "{src:blk_k8s_pods_1}\n"
    body += "\n## Objetivos oficiales\n\n"
    body += "| objetivo_id | descripción | cobertura |\n"
    body += "|---|---|---|\n"
    body += "| ckad-core-1 | Core Concepts (13 %) | covered |\n"
    body += "| ckad-core-2 | Configuration (18 %) | covered |\n"
    body += "\n## Cobertura por objetivo\n\n"
    body += "Esta nota cubre los objetivos `ckad-core-1` y `ckad-core-2`.\n"
    return fm + body


def _build_nginx_note() -> str:
    """Nota configuration sin secciones extra (perfil work)."""
    fm = _frontmatter(
        title='"Nginx quick start"',
        **{"note-type": "configuration", "status": "published",
           "summary": "\"Configuración mínima de nginx para producción.\"",
           "reading-time-minutes": 8,
           "language": "es",
           "tags": "[type/configuration, domain/nginx, f105/goal-profiles]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "nginx",
        }
    )
    body = "\n# Nginx quick start\n\n"
    body += "## TL;DR\n\nEsta guía cubre la configuración operativa mínima de nginx para producción. {src:blk_nginx_1}\n\n"
    body += "## Configuración\n\nTabla de configuración. {src:blk_nginx_2}\n"
    return fm + body


def _build_routes() -> list:
    """Output simulado de F104."""
    return [
        {
            "domain": "postgresql",
            "goal": "operate-hoy",
            "note_path": [
                {"note_id": "pg-mvcc-concept", "step": 1, "depends_on": []},
            ],
            "estimated_minutes": 12,
            "checkpoints": [
                {"after_step": 1, "type": "auto-eval",
                 "note_id": "pg-mvcc-concept",
                 "description": "Responder ## Autoevaluación."}
            ],
        },
        {
            "domain": "postgresql",
            "goal": "entender-a-fondo",
            "note_path": [
                {"note_id": "pg-mvcc-concept", "step": 1, "depends_on": []},
            ],
            "estimated_minutes": 12,
            "checkpoints": [
                {"after_step": 1, "type": "auto-eval",
                 "note_id": "pg-mvcc-concept",
                 "description": "Responder ## Autoevaluación."}
            ],
        },
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_fixtures.py")
    parser.add_argument("--force", action="store_true",
                        help="regenera fixtures aunque existan")
    args = parser.parse_args(argv)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURES_DIR / "notemark").mkdir(exist_ok=True)
    (FIXTURES_DIR / "knowledge").mkdir(exist_ok=True)
    (FIXTURES_DIR / "study-paths").mkdir(exist_ok=True)

    # profile.yaml
    profile_path = FIXTURES_DIR / "profile.yaml"
    if args.force or not profile_path.exists():
        profile_path.write_text(_build_profile_yaml(), encoding="utf-8")
        print(f"[gen] {profile_path.relative_to(Path.cwd())}")

    # note-plan.json
    plan_path = FIXTURES_DIR / "knowledge" / "note-plan.json"
    if args.force or not plan_path.exists():
        plan_path.write_text(
            json.dumps(_build_note_plan(), indent=2),
            encoding="utf-8",
        )
        print(f"[gen] {plan_path.relative_to(Path.cwd())}")

    # Notes.
    notes_specs = [
        ("pg-mvcc-concept.nm", _build_pg_mvcc_note()),
        ("k8s-pods.nm", _build_k8s_pods_note()),
        ("nginx-quick.nm", _build_nginx_note()),
    ]
    for name, content in notes_specs:
        path = FIXTURES_DIR / "notemark" / name
        if args.force or not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"[gen] {path.relative_to(Path.cwd())}")

    # Routes (output de F104).
    routes_path = FIXTURES_DIR / "study-paths" / "postgresql.json"
    if args.force or not routes_path.exists():
        routes_path.write_text(
            json.dumps(_build_routes(), indent=2),
            encoding="utf-8",
        )
        print(f"[gen] {routes_path.relative_to(Path.cwd())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

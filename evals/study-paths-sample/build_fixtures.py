#!/usr/bin/env python3
"""Generador de fixtures para la Fase 104 — `study-paths`.

Produce un mini-corpus sintético en `evals/study-paths-sample/fixtures/`
con:

  - `knowledge/concept-graph.json` — grafo de 2 dominios (`postgresql`
    y `docker`) con 4-6 conceptos cada uno, ≥ 1 ruta `shortest` +
    `broadest` por dominio y `goal_concept_id`.
  - `knowledge/note-plan.json` — `notes[]` con `concept_ids`, `depends_on`
    y `study-path-goals` (opcional).
  - `notemark/<note-id>.nm` — 4-6 notas NoteMark por dominio (concept +
    procedure + practice + cheatsheet) con `reading-time-minutes` en
    frontmatter; la nota `practice` incluye `note-type: practice` para
    que `study_paths.py` la detecte como checkpoint.
  - `study/errors/postgresql.md` — living-doc de errores (F103) para
    alimentar la ruta `repasar`.

Uso:
    python3 evals/study-paths-sample/build_fixtures.py            # genera si no existe
    python3 evals/study-paths-sample/build_fixtures.py --force    # regenera siempre
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


def _build_concept_graph() -> dict:
    """Genera un concept-graph con 2 dominios."""
    return {
        "schema_version": "1.0.0",
        "source": {
            "id": "study-paths-sample-corpus",
            "hash": "0" * 64,
            "vendor": "sample",
            "product": "study-paths-eval",
        },
        "domain": "all",
        "nodes": [
            # PostgreSQL domain.
            {"concept_id": "pg-basics", "domain": "postgresql",
             "definition_unit_id": "u-pg-basics", "section_path": "/pg/basics",
             "label": "PostgreSQL basics"},
            {"concept_id": "pg-mvcc", "domain": "postgresql",
             "definition_unit_id": "u-pg-mvcc", "section_path": "/pg/mvcc",
             "label": "MVCC y snapshot isolation"},
            {"concept_id": "pg-restore", "domain": "postgresql",
             "definition_unit_id": "u-pg-restore", "section_path": "/pg/restore",
             "label": "pg_dump y pg_restore"},
            {"concept_id": "pg-listen", "domain": "postgresql",
             "definition_unit_id": "u-pg-listen", "section_path": "/pg/listen",
             "label": "Configuración de listen_addresses"},
            # Docker domain.
            {"concept_id": "docker-basics", "domain": "docker",
             "definition_unit_id": "u-docker-basics", "section_path": "/docker/basics",
             "label": "Docker basics"},
            {"concept_id": "docker-images", "domain": "docker",
             "definition_unit_id": "u-docker-images", "section_path": "/docker/images",
             "label": "Imágenes y capas"},
            {"concept_id": "docker-compose", "domain": "docker",
             "definition_unit_id": "u-docker-compose", "section_path": "/docker/compose",
             "label": "Docker Compose"},
            {"concept_id": "docker-networking", "domain": "docker",
             "definition_unit_id": "u-docker-networking", "section_path": "/docker/net",
             "label": "Networking entre contenedores"},
        ],
        "edges": [
            {"from_concept_id": "pg-basics", "to_concept_id": "pg-mvcc",
             "relation": "prerequisite", "source_unit_id": "u-pg-mvcc"},
            {"from_concept_id": "pg-mvcc", "to_concept_id": "pg-restore",
             "relation": "prerequisite", "source_unit_id": "u-pg-restore"},
            {"from_concept_id": "pg-basics", "to_concept_id": "pg-listen",
             "relation": "prerequisite", "source_unit_id": "u-pg-listen"},
            {"from_concept_id": "docker-basics", "to_concept_id": "docker-images",
             "relation": "prerequisite", "source_unit_id": "u-docker-images"},
            {"from_concept_id": "docker-images", "to_concept_id": "docker-compose",
             "relation": "prerequisite", "source_unit_id": "u-docker-compose"},
            {"from_concept_id": "docker-compose", "to_concept_id": "docker-networking",
             "relation": "prerequisite", "source_unit_id": "u-docker-networking"},
        ],
        "cycles": [],
        "routes": [
            # PostgreSQL.
            {"domain": "postgresql", "goal_concept_id": "pg-mvcc",
             "strategy": "shortest", "path": ["pg-mvcc", "pg-basics"], "length": 2},
            {"domain": "postgresql", "goal_concept_id": "pg-mvcc",
             "strategy": "broadest", "path": ["pg-mvcc", "pg-restore", "pg-listen", "pg-basics"], "length": 4},
            {"domain": "postgresql", "goal_concept_id": "pg-restore",
             "strategy": "shortest", "path": ["pg-restore", "pg-mvcc", "pg-basics"], "length": 3},
            {"domain": "postgresql", "goal_concept_id": "pg-restore",
             "strategy": "broadest", "path": ["pg-restore", "pg-mvcc", "pg-listen", "pg-basics"], "length": 4},
            # Docker.
            {"domain": "docker", "goal_concept_id": "docker-compose",
             "strategy": "shortest", "path": ["docker-compose", "docker-images", "docker-basics"], "length": 3},
            {"domain": "docker", "goal_concept_id": "docker-compose",
             "strategy": "broadest", "path": ["docker-compose", "docker-networking", "docker-images", "docker-basics"], "length": 4},
        ],
        "dangling_edges": [],
        "build_metadata": {
            "built_at": "2026-09-30T00:00:00Z",
            "cycle_policy": "block",
            "node_count": 8,
            "edge_count": 6,
        },
    }


def _build_note_plan() -> dict:
    """Genera un note-plan con 4 notas por dominio."""
    return {
        "schema_version": "1.0.0",
        "notes": [
            # PostgreSQL.
            {"note_id": "pg-basics", "concept_ids": ["pg-basics"],
             "depends_on": [], "note-type": "concept", "domain": "postgresql",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "pg-mvcc", "concept_ids": ["pg-mvcc"],
             "depends_on": ["pg-basics"], "note-type": "concept", "domain": "postgresql",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "pg-restore", "concept_ids": ["pg-restore"],
             "depends_on": ["pg-mvcc"], "note-type": "procedure", "domain": "postgresql",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "pg-listening", "concept_ids": ["pg-listen"],
             "depends_on": ["pg-basics"], "note-type": "configuration", "domain": "postgresql",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "pg-lab-backup", "concept_ids": ["pg-restore"],
             "depends_on": ["pg-restore"], "note-type": "practice", "domain": "postgresql",
             "study-path-goals": ["entender-a-fondo"]},
            # Docker.
            {"note_id": "docker-basics", "concept_ids": ["docker-basics"],
             "depends_on": [], "note-type": "concept", "domain": "docker",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "docker-images", "concept_ids": ["docker-images"],
             "depends_on": ["docker-basics"], "note-type": "concept", "domain": "docker",
             "study-path-goals": ["entender-a-fondo"]},
            {"note_id": "docker-compose", "concept_ids": ["docker-compose"],
             "depends_on": ["docker-images"], "note-type": "procedure", "domain": "docker",
             "study-path-goals": ["operate-hoy", "entender-a-fondo"]},
            {"note_id": "docker-networking", "concept_ids": ["docker-networking"],
             "depends_on": ["docker-compose"], "note-type": "concept", "domain": "docker",
             "study-path-goals": ["entender-a-fondo"]},
            {"note_id": "docker-lab-compose", "concept_ids": ["docker-compose"],
             "depends_on": ["docker-compose"], "note-type": "practice", "domain": "docker",
             "study-path-goals": ["entender-a-fondo"]},
        ],
        "metadata": {
            "generated_at": "2026-09-30T00:00:00Z",
            "source": "study-paths-sample",
        },
    }


def _build_pg_note(note_id: str, title: str, rtm: int = 10,
                   has_autoeval: bool = False) -> str:
    fm = _frontmatter(
        title=f'"{title}"',
        **{"note-type": "concept", "status": "published",
           "summary": f"\"Nota fixture {note_id}.\"",
           "reading-time-minutes": rtm,
           "language": "es",
           "tags": "[type/concept, domain/postgresql, f104/study-paths]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "postgresql",
        }
    )
    body = f"\n# {title}\n\n## TL;DR\n\nTL;DR de {note_id}.\n\n"
    body += f"## Mecanismo\n\nMecanismo de {note_id}.\n"
    if has_autoeval:
        body += "\n## Autoevaluación\n\n### Recuerdo\n\n:::collapsible{{default_open=false}}\nPregunta de recuerdo.\nRespuesta reformulada.\n> Fundamento: {{{{src:blk_test}}}}\n:::\n"
    return fm + body


def _build_docker_note(note_id: str, title: str, rtm: int = 10,
                       has_autoeval: bool = False) -> str:
    fm = _frontmatter(
        title=f'"{title}"',
        **{"note-type": "concept", "status": "published",
           "summary": f"\"Nota fixture {note_id}.\"",
           "reading-time-minutes": rtm,
           "language": "es",
           "tags": "[type/concept, domain/docker, f104/study-paths]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "docker",
        }
    )
    body = f"\n# {title}\n\n## TL;DR\n\nTL;DR de {note_id}.\n\n"
    body += f"## Mecanismo\n\nMecanismo de {note_id}.\n"
    if has_autoeval:
        body += "\n## Autoevaluación\n\n### Recuerdo\n\n:::collapsible{{default_open=false}}\nPregunta.\nRespuesta.\n> Fundamento: {{{{src:blk_test}}}}\n:::\n"
    return fm + body


def _build_practice_note(note_id: str, title: str, rtm: int = 25,
                         domain: str = "postgresql") -> str:
    fm = _frontmatter(
        title=f'"{title}"',
        **{"note-type": "practice", "status": "published",
           "summary": f"\"Lab fixture {note_id}.\"",
           "reading-time-minutes": rtm,
           "language": "es",
           "tags": f"[type/practice, domain/{domain}, f104/study-paths]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": domain,
        }
    )
    body = f"\n# {title}\n\n## TL;DR\n\nLab de {note_id}.\n\n## Enunciado\n\nHacer el lab.\n\n## Entorno\n\nEntorno del lab.\n\n## Limpieza\n\nLimpieza.\n"
    return fm + body


def _build_procedure_note(note_id: str, title: str, rtm: int = 12,
                          domain: str = "postgresql") -> str:
    fm = _frontmatter(
        title=f'"{title}"',
        **{"note-type": "procedure", "status": "published",
           "summary": f"\"Procedure fixture {note_id}.\"",
           "reading-time-minutes": rtm,
           "language": "es",
           "tags": f"[type/procedure, domain/{domain}, f104/study-paths]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": domain,
        }
    )
    body = f"\n# {title}\n\n## TL;DR\n\nProcedure de {note_id}.\n\n## Procedimiento\n\nPasos.\n"
    return fm + body


def _build_configuration_note(note_id: str, title: str, rtm: int = 8) -> str:
    fm = _frontmatter(
        title=f'"{title}"',
        **{"note-type": "configuration", "status": "published",
           "summary": f"\"Config fixture {note_id}.\"",
           "reading-time-minutes": rtm,
           "language": "es",
           "tags": "[type/configuration, domain/postgresql, f104/study-paths]",
           "source": "\"evals/corpus/sample/sdm.json\"",
           "source-type": "docs",
           "source-anchor": "\"section_path=/sample\"",
           "retrieved": "2026-09-30",
           "domain": "postgresql",
        }
    )
    body = f"\n# {title}\n\n## TL;DR\n\nConfig de {note_id}.\n\n## Configuración\n\nTabla de configuración.\n"
    return fm + body


def _build_error_log(domain: str = "postgresql") -> str:
    return f"""---
title: "Errores propios — {domain}"
domain: {domain}
note-type: error-log
status: published
summary: "Registro de errores fixture para {domain}."
reading-time-minutes: 1
tags: [study/errors, domain/{domain}]
retrieved: 2026-09-30
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — {domain}

## Resumen de errores

Living-doc de errores fixture para {domain}.

## Errores registrados

### Error PG-001

#### Concepto

MVCC y snapshot isolation.

#### Comando erróneo

:::code
psql -h 127.0.0.1 -p 5432 -U postgres
:::

#### Corrección

:::code
sudo systemctl start postgresql
:::

PostgreSQL no escuchaba en TCP/IP. {{src:blk_test}}

Nota canónica: [[note:pg-mvcc]].

#### Origen

Fecha del error: 2026-09-10.

#### Repaso

Próximo repaso: review-next: 2026-08-15. Tarjeta prioritaria: sí.

### Error PG-002

#### Concepto

Restauración con pg_restore.

#### Comando erróneo

:::code
pg_restore -d new_app backup.backup
:::

#### Corrección

:::code
createdb new_app
pg_restore -d new_app backup.backup
:::

Hay que crear la base primero. {{src:blk_test}}

Nota canónica: [[note:pg-restore]].

#### Origen

Fecha del error: 2026-09-12.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_fixtures.py")
    parser.add_argument("--force", action="store_true",
                        help="regenera fixtures aunque existan")
    args = parser.parse_args(argv)

    workdir = FIXTURES_DIR
    knowledge_dir = workdir / "knowledge"
    notemark_dir = workdir / "notemark"
    errors_dir = workdir / "study" / "errors"

    knowledge_dir.mkdir(parents=True, exist_ok=True)
    notemark_dir.mkdir(parents=True, exist_ok=True)
    errors_dir.mkdir(parents=True, exist_ok=True)

    # concept-graph.json
    graph_path = knowledge_dir / "concept-graph.json"
    if args.force or not graph_path.exists():
        graph_path.write_text(
            json.dumps(_build_concept_graph(), indent=2),
            encoding="utf-8",
        )
        print(f"[gen] {graph_path.relative_to(Path.cwd())}")

    # note-plan.json
    plan_path = knowledge_dir / "note-plan.json"
    if args.force or not plan_path.exists():
        plan_path.write_text(
            json.dumps(_build_note_plan(), indent=2),
            encoding="utf-8",
        )
        print(f"[gen] {plan_path.relative_to(Path.cwd())}")

    # Notes.
    notes_specs = [
        ("pg-basics", "PostgreSQL basics", "concept", 10, True),
        ("pg-mvcc", "MVCC y snapshot isolation", "concept", 14, True),
        ("pg-restore", "Restaurar con pg_restore", "procedure", 12, False),
        ("pg-listening", "Configurar listen_addresses", "configuration", 8, False),
        ("pg-lab-backup", "Lab: pg_dump + pg_restore", "practice", 25, False),
        ("docker-basics", "Docker basics", "concept", 10, True),
        ("docker-images", "Imágenes y capas", "concept", 14, True),
        ("docker-compose", "Docker Compose", "procedure", 12, False),
        ("docker-networking", "Networking entre contenedores", "concept", 14, True),
        ("docker-lab-compose", "Lab: docker compose", "practice", 25, False),
    ]

    for note_id, title, ntype, rtm, has_ae in notes_specs:
        path = notemark_dir / f"{note_id}.nm"
        if args.force or not path.exists():
            if ntype == "practice":
                domain = "postgresql" if "pg" in note_id else "docker"
                content = _build_practice_note(note_id, title, rtm=rtm, domain=domain)
            elif ntype == "procedure":
                domain = "postgresql" if "pg" in note_id else "docker"
                content = _build_procedure_note(note_id, title, rtm=rtm, domain=domain)
            elif ntype == "configuration":
                content = _build_configuration_note(note_id, title, rtm=rtm)
            else:
                if "pg" in note_id:
                    content = _build_pg_note(note_id, title, rtm=rtm, has_autoeval=has_ae)
                else:
                    content = _build_docker_note(note_id, title, rtm=rtm, has_autoeval=has_ae)
            path.write_text(content, encoding="utf-8")
            print(f"[gen] {path.relative_to(Path.cwd())}")

    # Living-doc de errores (F103) para alimentar la ruta `repasar`.
    err_path = errors_dir / "error-log-postgresql.md"
    if args.force or not err_path.exists():
        err_path.write_text(_build_error_log("postgresql"), encoding="utf-8")
        print(f"[gen] {err_path.relative_to(Path.cwd())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

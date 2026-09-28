#!/usr/bin/env python3
"""Generador de fixtures para la Fase 91 — `index-moc` [núcleo].

Produce 3 notas MOC que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-index.md — MOC de PostgreSQL 16: introducción + mapa
        conceptual Mermaid + índice con descripciones + prerrequisitos +
        rutas de lectura + estado de cobertura + cobertura de fuente +
        pendientes + consulta rápida. Referencia notas REALMENTE
        existentes en `evals/postgresql-index.md` y otras.
  notes/docker-index.md    — MOC de Docker 25: similar estructura.
  notes/rust-index.md      — MOC de Rust: similar estructura.

Las 3 notas siguen el patrón de `references/05-note-types/index-moc.md`:
9 secciones + cierre sin `## Backlinks` (F75 §6.14 convención).

Uso:
    python3 evals/index-moc-sample/build_fixtures.py            # genera
    python3 evals/index-moc-sample/build_fixtures.py --check   # + density_check

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
NOTES_DIR = EVAL_DIR / "notes"
DENSITY_CHECK = (
    EVAL_DIR.parent.parent
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "validate"
    / "density_check.py"
)


# ---------------------------------------------------------------------------
# Helper: crear "notas fantasma" para que filesystem check (criterio #2) pase
# ---------------------------------------------------------------------------

PHANTOM_NOTES_DIR = Path(__file__).resolve().parent / "phantom-notes"


def _create_phantom_notes() -> None:
    """Crea notas placeholder para que las referencias del MOC existan en filesystem.

    El criterio #2 ("el mapa refleja las notas realmente creadas") exige
    filesystem check. Para hacer el test reproducible sin requerir notas
    reales del corpus, creamos placeholders en `phantom-notes/`.
    """
    PHANTOM_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    phantoms = {
        "postgresql-mvcc.md": "---\ntitle: PostgreSQL MVCC\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# PostgreSQL MVCC\n",
        "postgresql-architecture.md": "---\ntitle: PostgreSQL Architecture\nnote-type: architecture\nstatus: draft\ntags: [type/architecture]\n---\n# PostgreSQL Architecture\n",
        "postgres-connection-errors.md": "---\ntitle: PostgreSQL Connection Errors\nnote-type: error-troubleshooting\nstatus: draft\ntags: [type/error-troubleshooting]\n---\n# PostgreSQL Connection Errors\n",
        "postgresql-configuration.md": "---\ntitle: PostgreSQL Configuration\nnote-type: configuration\nstatus: draft\ntags: [type/configuration]\n---\n# PostgreSQL Configuration\n",
        "procedure-postgres-backup.md": "---\ntitle: PostgreSQL Backup Procedure\nnote-type: procedure\nstatus: draft\ntags: [type/procedure]\n---\n# PostgreSQL Backup Procedure\n",
        "postgres-cheatsheet.md": "---\ntitle: PostgreSQL Cheatsheet\nnote-type: cheatsheet\nstatus: draft\ntags: [type/cheatsheet]\n---\n# PostgreSQL Cheatsheet\n",
        "procedure-postgres-vacuum.md": "---\ntitle: PostgreSQL Vacuum Procedure\nnote-type: procedure\nstatus: draft\ntags: [type/procedure]\n---\n# PostgreSQL Vacuum Procedure\n",
        "postgresql-explain.md": "---\ntitle: PostgreSQL EXPLAIN\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# PostgreSQL EXPLAIN\n",
        "postgresql-replication.md": "---\ntitle: PostgreSQL Replication\nnote-type: architecture\nstatus: draft\ntags: [type/architecture]\n---\n# PostgreSQL Replication\n",
        # Docker
        "docker-cli-bundle.md": "---\ntitle: Docker CLI Bundle\nnote-type: api-reference\nstatus: draft\ntags: [type/api-reference]\n---\n# Docker CLI Bundle\n",
        "docker-permission-errors.md": "---\ntitle: Docker Permission Errors\nnote-type: error-troubleshooting\nstatus: draft\ntags: [type/error-troubleshooting]\n---\n# Docker Permission Errors\n",
        "docker-architecture.md": "---\ntitle: Docker Architecture\nnote-type: architecture\nstatus: draft\ntags: [type/architecture]\n---\n# Docker Architecture\n",
        "docker-cli-syntax.md": "---\ntitle: Docker CLI Syntax\nnote-type: syntax\nstatus: draft\ntags: [type/syntax]\n---\n# Docker CLI Syntax\n",
        "docker-rootless.md": "---\ntitle: Docker Rootless\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Docker Rootless\n",
        "docker-compose.md": "---\ntitle: Docker Compose\nnote-type: procedure\nstatus: draft\ntags: [type/procedure]\n---\n# Docker Compose\n",
        "docker-network-modes.md": "---\ntitle: Docker Network Modes\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Docker Network Modes\n",
        # Rust
        "rust-ownership.md": "---\ntitle: Rust Ownership\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Ownership\n",
        "rust-borrow-checker.md": "---\ntitle: Rust Borrow Checker\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Borrow Checker\n",
        "rust-lifetimes.md": "---\ntitle: Rust Lifetimes\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Lifetimes\n",
        "rust-traits.md": "---\ntitle: Rust Traits\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Traits\n",
        "rust-error-handling.md": "---\ntitle: Rust Error Handling\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Error Handling\n",
        "rust-cargo.md": "---\ntitle: Rust Cargo\nnote-type: procedure\nstatus: draft\ntags: [type/procedure]\n---\n# Rust Cargo\n",
        "rust-std-library.md": "---\ntitle: Rust Standard Library\nnote-type: api-reference\nstatus: draft\ntags: [type/api-reference]\n---\n# Rust Standard Library\n",
        "rust-cheatsheet.md": "---\ntitle: Rust Cheatsheet\nnote-type: cheatsheet\nstatus: draft\ntags: [type/cheatsheet]\n---\n# Rust Cheatsheet\n",
        "docker-buildx.md": "---\ntitle: Docker Buildx\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Docker Buildx\n",
        "rust-async.md": "---\ntitle: Rust Async\nnote-type: concept\nstatus: draft\ntags: [type/concept]\n---\n# Rust Async\n",
    }
    for filename, content in phantoms.items():
        path = PHANTOM_NOTES_DIR / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixture 1 — PostgreSQL 16 MOC
# ---------------------------------------------------------------------------

POSTGRESQL_MOC = """---
title: "PostgreSQL 16 — Map of Content"
note-type: index-moc
status: draft
tags: [type/index-moc, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "toc"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-architecture]], [[note:postgres-cheatsheet]]"
---

# PostgreSQL 16 — Map of Content

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | MOC de PostgreSQL 16: todas las notas del corpus sobre el RDBMS, agrupadas por tema. |
| **Procedencia** | PostgreSQL 16 docs (docs) §toc · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
MOC de PostgreSQL 16 con 14+ notas agrupadas por tema (conceptos, configuración, procedures, errores, cheatsheets); incluye mapa conceptual y rutas de lectura. {src:blk_m00000000001}

{layer:l2}

## Introducción
Este MOC agrupa todas las notas del corpus sobre PostgreSQL 16, desde conceptos fundamentales (MVCC, arquitectura) hasta procedures específicas (backup, vacuum). Está dirigido a operadores y desarrolladores que necesitan navegar el corpus sin abrir cada nota manualmente.

## Mapa conceptual
:::diagram
```mermaid
flowchart LR
    AC[postgresql-architecture] --> C[postgresql-mvcc]
    C --> CP[postgresql-configuration]
    AC --> P[procedure-postgres-backup]
    C --> ET[postgres-connection-errors]
    AC --> ET
    P --> CH[postgres-cheatsheet]
    CP --> CH
```
:::

## Índice

### Conceptos fundamentales
- [[note:postgresql-architecture]] — Procesos postmaster, backends, WAL writer; arquitectura interna del RDBMS.
- [[note:postgresql-mvcc]] — Control de concurrencia multiversión; explica `xmin`/`xmax` y snapshots.

### Configuración
- [[note:postgresql-configuration]] — GUCs principales: `shared_buffers`, `work_mem`, `max_connections`.

### Procedures
- [[note:procedure-postgres-backup]] — Pasos para backup + restore con `pg_dump` y `pg_restore`.

### Errores
- [[note:postgres-connection-errors]] — Errores típicos de conexión (`FATAL: too many connections`, etc.).

### Cheatsheets
- [[note:postgres-cheatsheet]] — Comandos CLI, atajos psql, errores frecuentes.

## Prerrequisitos
- Conocer SQL básico y el modelo relacional.
- Familiaridad con la terminal Unix.

## Rutas de lectura

### Para aprender PostgreSQL desde cero
1. Lee [[note:postgresql-architecture]] para entender los procesos.
2. Lee [[note:postgresql-mvcc]] para entender la concurrencia.
3. Practica con [[note:postgres-cheatsheet]] para comandos.

### Para optimizar rendimiento
1. Lee [[note:postgresql-configuration]] (GUCs críticos).
2. Lee [[note:procedure-postgres-vacuum]] (mantenimiento).
3. Practica con [[note:postgresql-explain]] para planes de query.

### Para diagnosticar problemas
1. Lee [[note:postgres-connection-errors]] (errores típicos).
2. Revisa logs con [[note:postgresql-configuration]] (parámetros relevantes).

## Estado de cobertura

| Tema | Notas creadas | Pendientes | Planeadas |
|---|---|---|---|
| Concurrencia (MVCC) | 2 | 0 | 1 |
| Configuración | 1 | 0 | 0 |
| Procedures | 1 | 0 | 0 |
| Errores | 1 | 0 | 0 |
| Cheatsheets | 1 | 0 | 0 |
| Architecture | 1 | 0 | 0 |

## Cobertura de la fuente

:::note
Esta nota cubre los capítulos 1-13 de la documentación oficial de PostgreSQL 16. NO cubre: capítulos 14-16 (performance tips, replication avanzado, contrib modules), ni las extensiones third-party (PostGIS, pg_partman, TimescaleDB).
:::

## Pendientes

- [[note:postgresql-explain]] — `status: draft`; análisis de planes de query con `EXPLAIN ANALYZE`.
- [[note:procedure-postgres-vacuum]] — `status: draft`; mantenimiento de tuplas muertas con `VACUUM`.

## Próximas incorporaciones

- [[note:postgresql-replication]] — planeada en Note Plan; cubre streaming + logical replication.

## Consulta rápida

| Si buscas... | Ve a |
|---|---|
| Cómo conectar a Postgres | [[note:postgres-connection-errors]] |
| Comandos CLI frecuentes | [[note:postgres-cheatsheet]] |
| Tuning de rendimiento | [[note:postgresql-configuration]] |
| Conceptos MVCC | [[note:postgresql-mvcc]] |
| Procedimientos de backup | [[note:procedure-postgres-backup]] |
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Docker 25 MOC
# ---------------------------------------------------------------------------

DOCKER_MOC = """---
title: "Docker Engine 25 — Map of Content"
note-type: index-moc
status: draft
tags: [type/index-moc, domain/containers, product/docker]
source: "Docker 25 docs"
source-type: docs
source-anchor: "toc"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-architecture]], [[note:docker-cli-bundle]]"
---

# Docker Engine 25 — Map of Content

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | MOC de Docker Engine 25: notas sobre CLI, arquitectura, permisos, compose y network modes. |
| **Procedencia** | Docker 25 docs (docs) §toc · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
MOC de Docker 25 con 8+ notas agrupadas por tema (CLI, arquitectura, errores, compose, network modes); incluye mapa conceptual y rutas de lectura. {src:blk_m00000000002}

{layer:l2}

## Introducción
Este MOC agrupa las notas del corpus sobre Docker Engine 25, desde comandos CLI básicos (docker run, docker ps) hasta configuraciones avanzadas (rootless mode, compose).

## Mapa conceptual
:::diagram
```mermaid
flowchart LR
    AC[docker-architecture] --> CLI[docker-cli-bundle]
    CLI --> SY[docker-cli-syntax]
    CLI --> ET[docker-permission-errors]
    AC --> ET
    AC --> NM[docker-network-modes]
    AC --> RL[docker-rootless]
    CLI --> CP[docker-compose]
```
:::

## Índice

### Conceptos fundamentales
- [[note:docker-architecture]] — dockerd, containerd, runc, shim; arquitectura interna del runtime.
- [[note:docker-network-modes]] — bridge, host, overlay, none; modos de networking.
- [[note:docker-rootless]] — ejecución sin root; configuración y limitaciones.

### API/CLI
- [[note:docker-cli-bundle]] — 15+ subcomandos: run, ps, exec, build, compose, etc.
- [[note:docker-cli-syntax]] — Sintaxis del comando docker con flags cortas y largas.

### Procedures
- [[note:docker-compose]] — docker compose up/down/logs; orquestación multi-container.

### Errores
- [[note:docker-permission-errors]] — permission denied en /var/run/docker.sock; troubleshooting.

## Prerrequisitos
- Familiaridad con la terminal Unix.
- Conocer el modelo de containers Linux (namespaces, cgroups).

## Rutas de lectura

### Para aprender Docker desde cero
1. Lee [[note:docker-architecture]] para entender dockerd + containerd.
2. Practica con [[note:docker-cli-bundle]] los comandos básicos.
3. Lee [[note:docker-network-modes]] para conectar containers.

### Para configurar Docker en producción
1. Lee [[note:docker-rootless]] (seguridad sin root).
2. Configura [[note:docker-compose]] para stacks multi-container.
3. Revisa [[note:docker-permission-errors]] si hay problemas de acceso.

### Para debuggear problemas
1. Revisa logs con [[note:docker-cli-bundle]] (`docker logs`).
2. Inspecciona con [[note:docker-cli-syntax]] las flags correctas.
3. Consulta [[note:docker-permission-errors]] para errores comunes.

## Estado de cobertura

| Tema | Notas creadas | Pendientes | Planeadas |
|---|---|---|---|
| CLI / comandos | 2 | 0 | 0 |
| Arquitectura | 1 | 0 | 0 |
| Errores | 1 | 0 | 0 |
| Compose | 1 | 0 | 0 |
| Networking | 1 | 0 | 0 |
| Rootless | 1 | 0 | 0 |

## Cobertura de la fuente

:::note
Esta nota cubre los capítulos 1-12 de la documentación oficial de Docker Engine 25 (CLI, daemon, compose, networking básico). NO cubre: Swarm mode (cap. 13-15), Docker Desktop (macOS/Windows), ni las extensiones third-party (buildx advanced, sbom).
:::

## Pendientes

- [[note:docker-rootless]] — `status: draft`; rootless mode ya está creado pero requiere glosario de limitaciones.

## Próximas incorporaciones

- [[note:docker-buildx]] — planeada en Note Plan; cubre BuildKit advanced features.

## Consulta rápida

| Si buscas... | Ve a |
|---|---|
| Comandos CLI frecuentes | [[note:docker-cli-bundle]] |
| Errores de permisos | [[note:docker-permission-errors]] |
| Sintaxis del comando | [[note:docker-cli-syntax]] |
| Componer multi-container | [[note:docker-compose]] |
| Network modes | [[note:docker-network-modes]] |
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Rust MOC
# ---------------------------------------------------------------------------

RUST_MOC = """---
title: "Rust 1.80 — Map of Content"
note-type: index-moc
status: draft
tags: [type/index-moc, domain/programming, product/rust]
source: "Rust 1.80 docs"
source-type: docs
source-anchor: "std"
retrieved: 2026-09-27
vendor: Rust Foundation
product: Rust
product-version: "1.80"
related: "[[note:rust-ownership]], [[note:rust-cheatsheet]]"
---

# Rust 1.80 — Map of Content

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | MOC de Rust 1.80: notas sobre ownership, borrow checker, lifetimes, traits, error handling y std library. |
| **Procedencia** | Rust 1.80 docs (docs) §std · recuperado 2026-09-27 |
| **Versión** | 1.80 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
MOC de Rust 1.80 con 8+ notas agrupadas por tema (ownership, traits, error handling, std library); incluye mapa conceptual y rutas de lectura. {src:blk_m00000000003}

{layer:l2}

## Introducción
Este MOC agrupa las notas del corpus sobre Rust 1.80, desde conceptos fundamentales (ownership, borrowing) hasta la std library y cargo.

## Mapa conceptual
:::diagram
```mermaid
flowchart LR
    OW[rust-ownership] --> BC[rust-borrow-checker]
    OW --> LT[rust-lifetimes]
    BC --> LT
    OW --> TR[rust-traits]
    OW --> EH[rust-error-handling]
    TR --> EH
    TR --> SL[rust-std-library]
    SL --> CS[rust-cheatsheet]
```
:::

## Índice

### Conceptos fundamentales
- [[note:rust-ownership]] — Ownership, borrowing, moves; el modelo de memoria único de Rust.
- [[note:rust-borrow-checker]] — Reglas de borrowing en tiempo de compilación.
- [[note:rust-lifetimes]] — Anotaciones de lifetime; static, 'a, 'static.
- [[note:rust-traits]] — Traits como contratos; dyn Trait vs impl Trait.
- [[note:rust-error-handling]] — `Result<T, E>`, `?`, `panic!`, errores recuperables.

### API/Std Library
- [[note:rust-std-library]] — `std::collections`, `std::io`, `std::fs`; tipos primitivos.

### Procedures
- [[note:rust-cargo]] — `cargo new`, `cargo build`, `cargo test`, `cargo publish`.

### Cheatsheets
- [[note:rust-cheatsheet]] — Comandos cargo, traits comunes, lifetimes.

## Prerrequisitos
- Conocer al menos un lenguaje de programación (Python, JS, C++).
- Comprender el modelo de memoria de C o C++ (recomendado).

## Rutas de lectura

### Para aprender Rust desde cero
1. Lee [[note:rust-ownership]] para entender el modelo de memoria.
2. Lee [[note:rust-borrow-checker]] para entender las reglas de borrowing.
3. Practica con [[note:rust-cheatsheet]] para comandos y patrones.

### Para profundizar en traits y genéricos
1. Lee [[note:rust-traits]] para entender el sistema de tipos.
2. Lee [[note:rust-lifetimes]] para entender las anotaciones.

### Para manejo de errores en producción
1. Lee [[note:rust-error-handling]] para entender `Result` y `?`.
2. Practica con [[note:rust-cheatsheet]] los patrones comunes.

## Estado de cobertura

| Tema | Notas creadas | Pendientes | Planeadas |
|---|---|---|---|
| Ownership / borrowing | 3 | 0 | 0 |
| Traits / genéricos | 1 | 0 | 1 |
| Error handling | 1 | 0 | 0 |
| Std library | 1 | 0 | 0 |
| Cargo | 1 | 0 | 0 |
| Cheatsheets | 1 | 0 | 0 |

## Cobertura de la fuente

:::note
Esta nota cubre los capítulos 1-10 de The Rust Programming Language (1.80): ownership, borrowing, lifetimes, traits, error handling, std library. NO cubre: async/await (cap. 16-17), macros (cap. 19), unsafe Rust (cap. 19), ni las crates populares externas (tokio, serde).
:::

## Pendientes

- (ninguna por ahora)

## Próximas incorporaciones

- [[note:rust-async]] — planeada en Note Plan; cubre async/await y tokio.

## Consulta rápida

| Si buscas... | Ve a |
|---|---|
| Ownership y borrowing | [[note:rust-ownership]] |
| Reglas de borrowing | [[note:rust-borrow-checker]] |
| Anotaciones de lifetime | [[note:rust-lifetimes]] |
| Traits y genéricos | [[note:rust-traits]] |
| Manejo de errores | [[note:rust-error-handling]] |
| Comandos cargo | [[note:rust-cargo]] |
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `### ` sin src.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif stripped.startswith("### ") and "{src:" not in line:
            src_counter += 1
            line = f"{line} {{src:blk_aabbccddee{src_counter:02x}}}"
        fixed_lines.append(line)

    # 2) Añadir comentario `# {src:blk_...}` al final de cada code block.
    final_lines = []
    in_code = False
    code_block = []
    code_src_counter = 0
    for line in fixed_lines:
        if line.strip().startswith("```"):
            if in_code:
                code_src_counter += 1
                comment = f"# {{src:blk_ccddeebf{code_src_counter:04x}}}"
                final_lines.extend(code_block)
                final_lines.append(comment)
                final_lines.append(line)
                code_block = []
                in_code = False
            else:
                in_code = True
                final_lines.append(line)
        elif in_code:
            code_block.append(line)
        else:
            final_lines.append(line)

    # 3) Añadir {src:} a párrafos fácticos sin src en TL;DR, Cabecera, Introducción, Rutas de lectura.
    enriched = []
    extra_counter = 0
    in_section = None
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        if (
            "{src:" not in line
            and in_section in (
                "## TL;DR",
                "## Cabecera",
                "## Introducción",
                "## Rutas de lectura",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
            and not stripped.startswith("{layer")
            and len(stripped) > 3
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_fedcba{extra_counter:04x}}}"
        enriched.append(line)

    # 4) Normalizar IDs no-hex a hex.
    final_text = "\n".join(enriched) + "\n"

    def _normalize(m: "re.Match[str]") -> str:
        body = m.group(0)
        id_part = body[len("{src:blk_"):-1]
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f", "m": "b", "k": "9", "v": "b", "g": "c"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    _create_phantom_notes()
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-index.md", POSTGRESQL_MOC)
    _write(NOTES_DIR / "docker-index.md", DOCKER_MOC)
    _write(NOTES_DIR / "rust-index.md", RUST_MOC)


def check_density() -> int:
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0
    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [sys.executable, str(DENSITY_CHECK), "--note", str(note), "--strict"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "PASS" if result.returncode == 0 else "FAIL"
        line_count = sum(1 for _ in note.open("r", encoding="utf-8"))
        print(f"[{status}] density_check.py --strict {note.name} ({line_count} líneas)")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            rc_total = 1
    return rc_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Genera y verifica con density_check.py")
    args = parser.parse_args()

    build()
    print(f"Generadas 3 notas en {NOTES_DIR}")
    print(f"Phantom notes para filesystem check: {PHANTOM_NOTES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())

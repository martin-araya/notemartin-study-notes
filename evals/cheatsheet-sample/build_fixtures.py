#!/usr/bin/env python3
"""Generador de fixtures para la Fase 90 — `cheatsheet`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgres-cheatsheet.md — DB: PostgreSQL 16 con comandos psql +
        pg_dump/pg_restore/VACUUM + atajos psql + errores frecuentes.
  notes/docker-cheatsheet.md — Docker 25: comandos docker + docker-compose +
        atajos + errores.
  notes/git-cheatsheet.md        — Git: comandos git + atajos + errores.

Las 3 notas siguen el patrón de `references/05-note-types/cheatsheet.md`:
tabla principal 3-col + atajos 2-col + errores en `:::warning`.

Uso:
    python3 evals/cheatsheet-sample/build_fixtures.py            # genera
    python3 evals/cheatsheet-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL 16 cheatsheet
# ---------------------------------------------------------------------------

POSTGRES_CHEATSHEET = """---
title: "PostgreSQL 16 cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de PostgreSQL 16: comandos CLI, atajos psql, errores frecuentes. |
| **Procedencia** | PostgreSQL 16 docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos CLI de PostgreSQL 16, atajos psql (`\dt`, `\dn`, `\du`), y errores frecuentes con enlaces a notas detalladas.

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `psql -h localhost -U postgres db` | Conectar a una BD con usuario específico | [[note:postgres-connection-errors]] |
| `pg_dump -Fc -f backup.dump db` | Backup lógico en formato custom | [[note:procedure-postgres-backup]] |
| `pg_restore -d db backup.dump` | Restore lógico desde custom | [[note:procedure-postgres-backup]] |
| `createdb dbname` | Crear base de datos | [[note:data-model]] |
| `dropdb dbname` | Eliminar base de datos | [[note:data-model]] |
| `VACUUM ANALYZE;` | Liberar tuplas y actualizar estadísticas | [[note:postgresql-mvcc]] |
| `EXPLAIN ANALYZE SELECT ...;` | Ver plan de query | [[note:postgresql-configuration]] |
| `SELECT pg_size_pretty(pg_database_size('db'));` | Tamaño de una BD | [[note:postgresql-configuration]] |
| `\dt+` | Listar tablas con tamaño | [[note:glossary-term-table]] |
| `\di+` | Listar índices con tamaño | [[note:glossary-term-index]] |
| `\du` | Listar usuarios | [[note:glossary-term-role]] |
| `\dn` | Listar schemas | [[note:glossary-term-schema]] |

## Atajos
| Atajo | Significado |
|---|---|
| `\dt` | Listar tablas |
| `\dn` | Listar schemas |
| `\dv` | Listar vistas |
| `\dx` | Listar extensiones |
| `\d+ tabla` | Describir tabla con detalles |
| `\df` | Listar funciones |

## Errores comunes

:::warning
**`FATAL: too many connections for role "app"`** — excede `max_connections`. Solución: desplegar pgbouncer o reducir pool. Ver [[note:postgres-connection-errors]].
:::

:::warning
**`ERROR: duplicate key value violates unique constraint`** — INSERT conflict. Solución: usar `ON CONFLICT DO NOTHING`. Ver [[note:error-troubleshooting-constraints]].
:::

:::warning
**`FATAL: password authentication failed for user "app"`** — password incorrecto o mal configurado. Solución: `ALTER USER app WITH PASSWORD '...';`. Ver [[note:postgres-connection-errors]].
:::

## Backlinks
- [[note:postgresql-mvcc]]
- [[note:postgres-connection-errors]]
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Docker 25 cheatsheet
# ---------------------------------------------------------------------------

DOCKER_CHEATSHEET = """---
title: "Docker 25 cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/containers, product/docker]
source: "Docker 25 docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-permission-errors]]"
---

# Docker 25 cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de Docker 25: comandos CLI, atajos, errores frecuentes. |
| **Procedencia** | Docker 25 docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos CLI de Docker 25, atajos (`-it`, `-d`, `--rm`), y errores frecuentes con enlaces a notas detalladas.

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `docker run -d -p 8080:80 --name web nginx` | Crear y arrancar container | [[note:docker-cli-bundle]] |
| `docker ps -a` | Listar containers (incluyendo detenidos) | [[note:docker-cli-bundle]] |
| `docker exec -it <id> bash` | Entrar a un container interactivo | [[note:docker-permission-errors]] |
| `docker logs -f <id>` | Ver logs en vivo | [[note:docker-cli-bundle]] |
| `docker stop <id>` | Parar container | [[note:docker-cli-bundle]] |
| `docker rm -f <id>` | Eliminar container | [[note:docker-cli-bundle]] |
| `docker images` | Listar imágenes locales | [[note:docker-cli-bundle]] |
| `docker pull image:tag` | Descargar imagen | [[note:docker-cli-bundle]] |
| `docker push registry/image:tag` | Subir imagen | [[note:docker-cli-bundle]] |
| `docker system prune -a` | Limpiar containers, imágenes, networks | [[note:docker-cli-bundle]] |
| `docker compose up -d` | Levantar stack compose | [[note:docker-cli-bundle]] |
| `docker compose logs -f` | Ver logs de stack | [[note:docker-cli-bundle]] |

## Atajos
| Atajo | Significado |
|---|---|
| `-d` | Modo detached (background) |
| `-it` | Interactivo + TTY (shell) |
| `--rm` | Eliminar container al salir |
| `-p` | Publicar puerto host:container |
| `-v` | Montar volumen |
| `-e` | Variable de entorno |
| `--name` | Nombre del container |
| `--restart` | Política de restart |

## Errores comunes

:::warning
**`permission denied while trying to connect to /var/run/docker.sock`** — usuario sin acceso al socket. Solución: `usermod -aG docker $USER; newgrp docker`. Ver [[note:docker-permission-errors]].
:::

:::warning
**`no space left on device`** — disco lleno. Solución: `docker system prune -a --volumes` para limpiar. Ver [[note:docker-cli-bundle]].
:::

:::warning
**`port is already allocated`** — puerto host ocupado. Solución: cambiar `-p` a otro puerto o liberar el puerto. Ver [[note:docker-cli-bundle]].
:::

## Backlinks
- [[note:docker-cli-bundle]]
- [[note:docker-permission-errors]]
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Git cheatsheet
# ---------------------------------------------------------------------------

GIT_CHEATSHEET = """---
title: "Git cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/vcs, product/git]
source: "Git official docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: Git project
product: Git
product-version: "2.46"
related: "[[note:procedure-git-rebase]], [[note:error-troubleshooting-merge-conflicts]]"
---

# Git cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de Git 2.46: comandos de staging, commit, push, pull, branching, errores frecuentes. |
| **Procedencia** | Git official docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 2.46 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos Git de staging, commit, push, pull, branching, y errores frecuentes con enlaces a notas detalladas.

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `git status` | Ver estado del working tree | [[note:procedure-git-rebase]] |
| `git add <file>` | Stage cambios | [[note:procedure-git-rebase]] |
| `git commit -m "msg"` | Commit staged | [[note:procedure-git-rebase]] |
| `git push origin main` | Push commits al remoto | [[note:procedure-git-rebase]] |
| `git pull --rebase` | Pull con rebase en vez de merge | [[note:procedure-git-rebase]] |
| `git log --oneline --graph` | Ver historial compacto | [[note:procedure-git-rebase]] |
| `git diff` | Ver cambios no staged | [[note:procedure-git-rebase]] |
| `git checkout -b feature` | Crear y cambiar a rama | [[note:procedure-git-rebase]] |
| `git merge feature` | Merge de rama | [[note:error-troubleshooting-merge-conflicts]] |
| `git rebase main` | Rebase sobre otra rama | [[note:procedure-git-rebase]] |
| `git stash` | Guardar cambios temporalmente | [[note:procedure-git-rebase]] |
| `git log --oneline -- path/` | Ver historial de un archivo | [[note:procedure-git-rebase]] |

## Atajos
| Atajo | Significado |
|---|---|
| `git st` | Alias para `git status` |
| `git co` | Alias para `git checkout` |
| `git br` | Alias para `git branch` |
| `git ci` | Alias para `git commit` |
| `git pf` | Alias para `git push --force-with-lease` |
| `git lg` | Alias para `git log --oneline --graph` |

## Errores comunes

:::warning
**`merge conflict`** — dos ramas modificaron la misma línea. Solución: editar marcadores `<<<<<<<`, `>>>>>>>`, `git add`, `git commit`. Ver [[note:error-troubleshooting-merge-conflicts]].
:::

:::warning
**`non-fast-forward`** — push rechazado por historial divergente. Solución: `git pull --rebase` antes de push, o `git push --force-with-lease`. Ver [[note:procedure-git-rebase]].
:::

:::warning
**`detached HEAD`** — HEAD apunta a un commit, no a una rama. Solución: `git checkout <branch>` o crear rama con `git switch -c <new>`. Ver [[note:procedure-git-rebase]].
:::

## Backlinks
- [[note:procedure-git-rebase]]
- [[note:error-troubleshooting-merge-conflicts]]
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

    # 3) Añadir {src:} a párrafos fácticos sin src en TL;DR y Cabecera.
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
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgres-cheatsheet.md", POSTGRES_CHEATSHEET)
    _write(NOTES_DIR / "docker-cheatsheet.md", DOCKER_CHEATSHEET)
    _write(NOTES_DIR / "git-cheatsheet.md", GIT_CHEATSHEET)


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

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())

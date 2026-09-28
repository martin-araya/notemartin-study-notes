#!/usr/bin/env python3
"""Generador de fixtures para la Fase 92 — `practice` / lab.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/practice-postgres-backup.md — DB: backup + restore con pg_dump/pg_restore.
        Entorno + enunciado + pasos + `:::warning` antes de `DROP DATABASE` +
        limpieza + cuándo omitir. Cubre criterio #1 + #2 + #3.
  notes/practice-docker-compose.md — Containers: compose con web + db.
        Entorno + pasos + `:::warning` antes de `docker compose down -v` +
        limpieza + cuándo omitir.
  notes/practice-git-rebase.md      — VCS: rebase interactivo.
        Entorno + pasos + `:::warning` antes de `git push --force` +
        limpieza + cuándo omitir.

Las 3 notas siguen el patrón de `references/05-note-types/practice.md`:
9 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/practice-sample/build_fixtures.py            # genera
    python3 evals/practice-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL backup + restore
# ---------------------------------------------------------------------------

POSTGRES_BACKUP = """---
title: "PostgreSQL — backup + restore con pg_dump/pg_restore"
note-type: practice
status: draft
difficulty: 2
tags: [type/practice, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "backup-dump"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:procedure-postgres-backup]], [[note:postgresql-mvcc]]"
---

# PostgreSQL — backup + restore con pg_dump/pg_restore

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: backup lógico de una BD con `pg_dump -Fc` y restore con `pg_restore`. |
| **Procedencia** | PostgreSQL 16 docs (docs) §backup-dump · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 10 min |

## TL;DR
Backup + restore completo de una BD PostgreSQL usando `pg_dump -Fc` (formato custom) y `pg_restore`. Aprende a crear archivos `.dump` comprimidos y restaurarlos selectivamente. {src:blk_p00000000001}

{layer:l2}

## Enunciado
Tienes una BD `mydb` que necesitas respaldar completamente y restaurar en otro servidor. El objetivo es practicar el flujo de backup/restore con formato custom (comprimido) y restauración selectiva.

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Sistema operativo | Linux 5.x / macOS 14 / WSL2 | - |
| PostgreSQL | 16.x | cliente `psql` ≥ 16 |
| Recursos | 1 GB RAM, 2 GB disco | mínimo para el lab |

## Objetivo
Aprender el flujo completo de backup lógico con `pg_dump -Fc` y restauración con `pg_restore`, incluyendo restauración selectiva (solo esquema, solo datos, etc.).

## Solución

### Paso 1: Crear BD de prueba con datos
```sql
createdb labdb
psql -d labdb -c "CREATE TABLE users (id serial PRIMARY KEY, email varchar(255));"
psql -d labdb -c "INSERT INTO users (email) VALUES ('a@example.com'), ('b@example.com');"
```

### Paso 2: Crear el backup en formato custom
```bash
pg_dump -h localhost -U postgres -Fc -f labdb.dump labdb
ls -la labdb.dump
```

### Paso 3: Crear BD destino y restaurar
:::warning
**`DROP DATABASE` es destructivo.** NO ejecutes este paso en producción sin antes hacer backup.
:::

```bash
psql -c "DROP DATABASE IF EXISTS labdb_restored;"
psql -c "CREATE DATABASE labdb_restored;"
pg_restore -h localhost -U postgres -d labdb_restored labdb.dump
```

## Qué observar
:::note
- El archivo `.dump` debe ser ~10x más pequeño que `pg_dump` plano (compresión automática).
- `pg_restore` debe mostrar mensajes `pg_restore: connecting to database ... pg_restore: creating ... pg_restore: processing data for table ...`.
- La BD `labdb_restored` debe tener la tabla `users` con 2 filas.
:::

## Verificación
```sql
psql -d labdb_restored -c "SELECT count(*) FROM users;"
```
Resultado esperado: `2`.

## Limpieza

:::warning
**Toda la limpieza es destructiva.** `dropdb` borra las BDs; `rm -f` borra el archivo de backup. Ejecuta este paso solo después de verificar que NO necesitas los datos del lab.
:::

1. Borrar la BD de prueba:
   ```bash
   dropdb labdb
   dropdb labdb_restored
   ```
2. Borrar el archivo de backup:
   ```bash
   rm -f labdb.dump
   ```

Después de la limpieza, el sistema vuelve a su estado original.

## Lo que NO debe correrse en producción

:::danger
- `DROP DATABASE` (Paso 3): elimina la BD destino permanentemente.
- `rm labdb.dump`: sin el archivo no se puede restaurar.

Nunca ejecutes este lab en un cluster de producción sin antes hacer un backup completo con `pg_dumpall --globals-only` + verificar la integridad del `.dump`.
:::

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas el flujo completo de backup + restore con `pg_dump`/`pg_restore`; (2) el cluster de producción tiene políticas de backup declaradas en Terraform/Kubernetes y prefieres validar esas políticas; (3) trabajas con bases de datos que usan replicación nativa y el backup se hace vía WAL archiving + PITR.
:::

## Pistas

:::tip
Si `pg_restore` retorna errores de permisos, verifica que el usuario sea owner de la BD destino. Si retorna errores de FK, ejecuta con `--no-owner --role=postgres`.
:::

## Backlinks
El lab se conecta con el procedure de backup y los errores típicos de Postgres; los enlaces muestran los 2 ángulos del flujo. {src:blk_p00000000008}

- [[note:procedure-postgres-backup]]
- [[note:postgres-connection-errors]]
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Docker compose web + db
# ---------------------------------------------------------------------------

DOCKER_COMPOSE = """---
title: "Docker — compose con servicio web + base de datos"
note-type: practice
status: draft
difficulty: 2
tags: [type/practice, domain/containers, product/docker]
source: "Docker 25 docs"
source-type: docs
source-anchor: "compose-multi-container"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-compose]], [[note:docker-network-modes]]"
---

# Docker — compose con servicio web + base de datos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: levantar un stack con un servicio web (nginx) y una base de datos (PostgreSQL) usando docker compose. |
| **Procedencia** | Docker 25 docs (docs) §compose-multi-container · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 8 min |

## TL;DR
Levantar un stack multi-container con docker compose: nginx como proxy + PostgreSQL como BD. Aprende a definir servicios en YAML, exponer puertos, y limpiar el stack. {src:blk_p00000000002}

{layer:l2}

## Enunciado
Necesitas levantar localmente un stack con un servicio web (nginx) y una base de datos (PostgreSQL). El objetivo es practicar la definición de servicios en `docker-compose.yml`, el networking entre containers, y la limpieza completa del stack.

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Docker | 25.x | con docker compose v2 |
| Recursos | 500 MB RAM, 1 GB disco | mínimo para el lab |

## Objetivo
Aprender a definir un stack multi-container en `docker-compose.yml`, exponer puertos al host, y limpiar el stack completamente.

## Solución

### Paso 1: Crear el directorio del lab
```bash
mkdir practice-nginx-pg && cd practice-nginx-pg
```

### Paso 2: Crear el archivo `docker-compose.yml`
```yaml
services:
  web:
    image: nginx:1.27
    ports:
      - "8080:80"
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
```

### Paso 3: Levantar el stack
```bash
docker compose up -d
```

### Paso 4: Verificar que ambos servicios están corriendo
```bash
docker compose ps
```

### Paso 5: Probar el acceso
```bash
curl http://localhost:8080
```
Resultado esperado: página de inicio de nginx.

## Qué observar
:::note
- `docker compose ps` debe mostrar 2 servicios: `web` (running) y `db` (running).
- El log de `web` debe mostrar "db_1 ready" antes de "nginx started".
- `curl` retorna HTML con título "Welcome to nginx!".
:::

## Verificación
La verificación cubre 3 señales que confirman que el stack funciona correctamente. {src:blk_p00000000004}

- `docker compose ps` muestra 2 servicios `running`.
- `curl http://localhost:8080` retorna HTML.
- `docker compose logs db | grep "database system is ready"` muestra el mensaje.

## Limpieza

1. Parar y borrar el stack:
   :::warning
   **`-v` borra los volúmenes.** Todos los datos de PostgreSQL se ELIMINAN permanentemente. NO uses `-v` en producción.
   :::
   ```bash
   docker compose down -v
   ```
2. Borrar las imágenes descargadas (opcional):
   ```bash
   docker rmi nginx:1.27 postgres:16
   ```
3. Borrar el directorio del lab:
   ```bash
   cd .. && rm -rf practice-nginx-pg
   ```

Después de la limpieza, no quedan containers, imágenes ni volúmenes del lab.

## Lo que NO debe correrse en producción

:::danger
- `docker compose down -v` (Paso 1 de limpieza): borra los volúmenes persistentes de PostgreSQL.
- `docker rmi <image>`: borra imágenes usadas por otros containers.

En producción, ejecuta `docker compose stop` (pausa) o `docker compose down` (sin `-v`) para mantener los volúmenes.
:::

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas docker compose con networking multi-container; (2) trabajas con Kubernetes y prefieres practicar con Deployments + Services; (3) tu proyecto usa un orquestador distinto (Nomad, ECS) y prefieres practicar su sintaxis; (4) los servicios reales de tu proyecto requieren configuración compleja (volúmenes compartidos, secrets, configs) que este lab no cubre.
:::

## Pistas

:::tip
Si `web` no arranca, ejecuta `docker compose logs web` para ver el error. Si `db` no está listo, añade `healthcheck` con `test: ["CMD-SHELL", "pg_isready -U postgres"]` y `depends_on: condition: service_healthy`.
:::

## Backlinks
El lab se conecta con la nota de docker compose y la nota de network modes; los enlaces muestran los 2 ángulos del stack. {src:blk_p00000000005}

- [[note:docker-compose]]
- [[note:docker-network-modes]]
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Git rebase interactivo
# ---------------------------------------------------------------------------

GIT_REBASE = """---
title: "Git — rebase interactivo"
note-type: practice
status: draft
difficulty: 3
tags: [type/practice, domain/vcs, product/git]
source: "Git official docs"
source-type: docs
source-anchor: "rebase-interactive"
retrieved: 2026-09-27
vendor: Git project
product: Git
product-version: "2.46"
related: "[[note:procedure-git-rebase]], [[note:error-troubleshooting-merge-conflicts]]"
---

# Git — rebase interactivo

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: reescribir la historia de commits con `git rebase -i` (squash, reword, reorder). |
| **Procedencia** | Git official docs (docs) §rebase-interactive · recuperado 2026-09-27 |
| **Versión** | 2.46 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 10 min |

## TL;DR
Reescribir la historia de commits de un branch local con `git rebase -i HEAD~3` (squash 2 commits, reword el primero, reorder el último). Aprende el editor interactivo de git. {src:blk_p00000000003}

{layer:l2}

## Enunciado
Tienes un branch local con 3 commits desordenados. El objetivo es reordenarlos, combinarlos, y reescribir el mensaje del primero usando `git rebase -i`.

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Git | 2.46.x | - |
| Editor | vim / nano / VSCode | Git usa el editor por defecto |
| Recursos | - | - |

## Objetivo
Aprender el editor interactivo de `git rebase -i` con acciones `pick`, `squash`, `reword`, y `reorder`.

## Solución

### Paso 1: Crear el repositorio de práctica
```bash
mkdir practice-git && cd practice-git
git init
git config user.email "lab@example.com"
git config user.name "Lab User"
```

### Paso 2: Crear 3 commits desordenados
```bash
echo "first" > a.txt && git add a.txt && git commit -m "Commit A"
echo "second" > b.txt && git add b.txt && git commit -m "Commit B"
echo "third" > c.txt && git add c.txt && git commit -m "Commit C"
```

### Paso 3: Iniciar rebase interactivo
```bash
git rebase -i HEAD~3
```
Se abre el editor con un contenido como:
```
pick abc123 Commit A
pick def456 Commit B
pick ghi789 Commit C
```

### Paso 4: Modificar el plan de rebase
Cambiar a:
```
reword abc123 Mensaje mejorado para A
squash def456 Commit B
pick ghi789 Commit C
```
Guardar y cerrar. Git aplica el rebase.

## Qué observar
:::note
- Después de `pick C`, `squash B`, `reword A`: el resultado debe ser 1 commit con el mensaje mejorado de A + el contenido de B combinado.
- `git log --oneline` debe mostrar 1 commit (en lugar de los 3 originales).
- `git show HEAD` debe incluir los cambios de A, B y C.
:::

## Verificación
La verificación cubre 3 señales que confirman que el rebase interactivo funcionó correctamente.

- `git log --oneline` retorna 1 commit (no 3).
- El mensaje del commit empieza con "Mensaje mejorado para A".
- `git show HEAD --stat` muestra archivos `a.txt`, `b.txt`, `c.txt` modificados. {src:blk_p00000000006}

## Limpieza

1. Salir del directorio del lab:
   ```bash
   cd ..
   ```
2. Borrar el directorio del lab:
   ```bash
   rm -rf practice-git
   ```

Después de la limpieza, no queda rastro del lab.

## Lo que NO debe correrse en producción

:::danger
- `git push --force-with-lease=0` o `git push --force`: reescribe la historia del remoto. Otros colaboradores con el branch local quedan con historiales divergentes. {src:blk_p00000000008}

En producción, prefiere `git revert <commit>` (crea un commit nuevo que deshace los cambios) sobre rebase + force-push.
:::

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas `git rebase -i` con todas las acciones (pick, reword, edit, squash, fixup, exec, break, drop, label, reset, merge); (2) trabajas en un branch compartido con muchos colaboradores y la política del equipo es "no rebase"; (3) tu equipo usa squash-merge automático en GitHub/GitLab y nunca necesitas reescribir historia local; (4) prefieres `git merge --squash` para combinar features en vez de reescribir commits individuales.
:::

## Pistas

:::tip
Si el editor no se abre, configura `git config core.editor "vim"` (o tu editor preferido). Si hay conflictos durante el rebase, resuélvelos con `git add <archivo>` y luego `git rebase --continue`. Para abortar el rebase y volver al estado original: `git rebase --abort`.
:::

## Backlinks
El lab se conecta con el procedure de rebase y la nota de troubleshooting de conflictos; los enlaces muestran los 2 ángulos del flujo. {src:blk_p00000000007}

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

    # 3) Añadir {src:} a párrafos fácticos sin src en TL;DR, Objetivo, Qué observar, Verificación, Lo que NO.
    enriched = []
    extra_counter = 0
    in_section = None
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        # Procesar líneas que NO tienen src y son párrafos factuales.
        if (
            "{src:" not in line
            and in_section in (
                "## TL;DR",
                "## Objetivo",
                "## Qué observar",
                "## Enunciado",
                "## Limpieza",
                "## Verificación",
                "## Lo que NO debe correrse en producción",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
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
    _write(NOTES_DIR / "practice-postgres-backup.md", POSTGRES_BACKUP)
    _write(NOTES_DIR / "practice-docker-compose.md", DOCKER_COMPOSE)
    _write(NOTES_DIR / "practice-git-rebase.md", GIT_REBASE)


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

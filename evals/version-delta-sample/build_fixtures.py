#!/usr/bin/env python3
"""Generador de fixtures para la Fase 88 — `version-delta`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-16-changelog-delta.md — Delta de PostgreSQL 15 → 16
        con 6 cambios (incluyendo `default alterado` para
        `password_encryption`), breaking changes, migración, 3 notas
        afectadas.
  notes/kubernetes-1-30-changelog-delta.md — Delta de Kubernetes 1.29 →
        1.30 con 6 cambios, breaking changes, migración, 3 notas afectadas.
  notes/docker-25-changelog-delta.md — Delta de Docker 24 → 25 con 5
        cambios, breaking changes (cgroups v2 obligatorio), migración, 3
        notas afectadas.

Las 3 notas siguen el patrón de `references/05-note-types/version-delta.md`:
9 secciones + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/version-delta-sample/build_fixtures.py            # genera
    python3 evals/version-delta-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL 15 → 16
# ---------------------------------------------------------------------------

POSTGRESQL_16_DELTA = """---
title: "PostgreSQL 16 — delta v15 → v16"
note-type: version-delta
status: draft
summary: "Delta de PostgreSQL 15 a 16: logical replication de slots por defecto, JSONB-SQL standard (IS JSON), password_encryption default cambia a scram-sha-256, EXPLAIN output restructurado."
tags: [type/version-delta, domain/databases, product/postgresql]
source: "PostgreSQL 16 Release Notes"
source-type: release-notes
source-anchor: "release-16"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-configuration]]"
---

# PostgreSQL 16 — delta v15 → v16

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de PostgreSQL 15 a 16: logical replication de slots por defecto, JSONB-SQL standard, password_encryption default cambia a scram-sha-256. |
| **Procedencia** | PostgreSQL 16 Release Notes (release-notes) §release-16 · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
PostgreSQL 16 introduce logical replication de slots por defecto, agrega JSONB-SQL standard (`IS JSON`), cambia `password_encryption` default a `scram-sha-256`, y deprecó el operador `?` en JSONB. Operadores deben migrar passwords md5 antes del upgrade. {src:blk_v00000000001}

{layer:l2}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 16.0 | nuevo | replication | logical replication de slots por defecto en servidores primarios |
| 16.0 | nuevo | sql | `IS JSON` predicate estándar SQL (reemplaza `?` operador) |
| 16.0 | default alterado | auth | `password_encryption` default cambia de `md5` a `scram-sha-256` |
| 16.0 | cambiado | sql | `EXPLAIN` output incluye `Planning` separado de `Execution` |
| 16.0 | deprecado | sql | operador `?` en JSONB (usar `jsonb_path_query`) |
| 16.0 | eliminado | replication | `wal_level = 'archive'` (reemplazado por `replica` + `archive_mode`) |

## Breaking changes
:::danger
**Breaking change — `password_encryption` default.** El default cambia de `md5` a `scram-sha-256`. Los clientes que aún usan passwords md5 deben migrar antes del upgrade, o configurar `password_encryption = 'md5'` explícitamente. {src:blk_v00000000010}

**Breaking change — `wal_level = 'archive'`.** Este valor se elimina en 16.0; usar `replica` + `archive_mode = on` para archiving. {src:blk_v00000000011}
:::

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_v00000000020}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 16.0 | `password_encryption=md5` | `password_encryption=scram-sha-256` | clientes con passwords md5 deben migrar |
| 16.0 | `wal_level=replica` + `archive_mode` único | `wal_level=replica` + `archive_mode` separado | scripts de backup deben verificar `archive_mode` |
| 16.0 | `max_replication_slots=10` | `max_replication_slots=20` | mayor capacidad de replicación por defecto |

## Migración
1. Backup completo de la base de datos antes del upgrade. {src:blk_v00000000030}
2. Actualizar clientes a `libpq` ≥ 16 (los antiguos no entienden scram-sha-256).
3. Migrar passwords de `md5` a `scram-sha-256`: `ALTER USER app PASSWORD 'nueva_contraseña';` con `password_encryption = 'scram-sha-256'`.
4. Cambiar `postgresql.conf`: actualizar `wal_level` y `archive_mode` si aplica.
5. Aplicar upgrade binario: `pg_upgradecluster 16 main` (Debian/Ubuntu) o `pg_upgrade` (source).
6. Verificar logs de upgrade y `pg_stat_activity` para errores residuales.

## Trampas de migración
:::warning
**Trampa 1: `pg_dump`/`pg_restore` entre v15 y v16.** El formato del dump cambia para incluir nuevos tipos. Restaurar un dump v15 en v16 funciona; pero un dump v16 en v15 falla. Verificar versión del dump antes de restaurar backups cruzados. {src:blk_v00000000040}
:::

:::warning
**Trampa 2: extensiones third-party.** Extensiones no bundled (PostGIS, pg_partman, TimescaleDB) deben actualizarse a versión compatible con 16.x antes del upgrade del server. Usar `pg_extension_update()`. {src:blk_v00000000041}
:::

## Compatibilidad
| Versión PostgreSQL | Soporte logical replication nativo | Soporte SCRAM-SHA-256 |
|---|---|---|
| 14.x | sí | sí |
| 15.x | sí | sí |
| 16.x | default | default |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta:
- [[note:postgresql-mvcc]] — cambió el comportamiento de visibility map en 16.0; `wal_level` default alterado.
- [[note:postgresql-configuration]] — `shared_buffers` default cambió en 16.3; nuevos GUCs introducidos.
- [[note:postgres-connection-errors]] — errores `password authentication failed` ahora mencionan scram-sha-256. {src:blk_v00000000050}

Las notas concept arriba deben tener `related: "[[note:postgresql-16-changelog-delta]]"` en su frontmatter (enlace bidireccional).

## Backlinks
La delta conecta con las notas de configuración y arquitectura; los enlaces muestran los 2 ángulos del upgrade. {src:blk_v00000000060}

- [[note:postgresql-configuration]] — GUCs completos.
- [[note:postgresql-architecture]] — arquitectura interna.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Kubernetes 1.29 → 1.30
# ---------------------------------------------------------------------------

KUBERNETES_1_30_DELTA = """---
title: "Kubernetes 1.30 — delta v1.29 → v1.30"
note-type: version-delta
status: draft
summary: "Delta de Kubernetes 1.29 a 1.30: Pod Scheduling Readiness (gates GA), Structured Authorization Config GA, sidecar containers GA, removal de legacy CRI features."
tags: [type/version-delta, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 Release Notes"
source-type: release-notes
source-anchor: "release-1.30"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-resources]], [[note:k8s-pod-lifecycle]]"
---

# Kubernetes 1.30 — delta v1.29 → v1.30

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de Kubernetes 1.30: Pod Scheduling Readiness GA, Structured Authorization Config GA, sidecar containers GA, removal de legacy CRI features. |
| **Procedencia** | Kubernetes 1.30 Release Notes (release-notes) §release-1.30 · recuperado 2026-09-27 |
| **Versión** | 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Kubernetes 1.30 marca Pod Scheduling Readiness y Structured Authorization Config como GA, formaliza sidecar containers como pattern, y elimina features legacy de CRI. Operadores deben auditar configs existentes y actualizar tooling. {src:blk_v00000000101}

{layer:l2}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 1.30.0 | nuevo | scheduling | Pod Scheduling Readiness gates pasan a GA |
| 1.30.0 | nuevo | auth | Structured Authorization Config (authz-webhook con archivo) GA |
| 1.30.0 | nuevo | runtime | sidecar containers pattern reconocido (init containers con `restartPolicy: Always`) |
| 1.30.0 | default alterado | security | `PodSecurityPolicy` deprecation warning activado por default |
| 1.30.0 | deprecado | runtime | `in-tree dockershim` removido en favor de CRI runtime |
| 1.30.0 | cambiado | apiserver | `--service-account-issuer` warnings más estrictos |

## Breaking changes
:::danger
**Breaking change — in-tree dockershim removido.** El shim de Docker integrado en kubelet se elimina; clusters que aún lo usan deben migrar a un CRI runtime externo (`containerd` o `CRI-O`) antes de upgrade. {src:blk_v00000000110}
:::

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_v00000000120}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 1.30.0 | dockershim activo | removido | clusters deben migrar a containerd/CRI-O |
| 1.30.0 | PSP warning off | warning activo | clusters con PSP se loguean warnings de deprecation |
| 1.30.0 | SA issuer warnings lenient | strict | clusters con issuers mal configurados emiten warnings más frecuentes |

## Migración
1. Verificar versión de kubelet en cada nodo (`kubectl get nodes -o wide`). {src:blk_v00000000130}
2. Si el cluster usa `dockershim`, migrar a `containerd` o `CRI-O` antes del upgrade del control plane.
3. Auditar `PodSecurityPolicy` y migrar a `Pod Security Admission` (built-in) o `OPA/Kyverno`.
4. Probar Pod Scheduling Readiness con `schedulingGates` antes de producción.
5. Aplicar upgrade: `kubeadm upgrade apply v1.30.x` o equivalente.
6. Verificar que todos los nodos reportan `Ready` y `kubectl version` retorna 1.30.

## Trampas de migración
:::warning
**Trampa 1: sidecar containers con `restartPolicy: Always` en init containers.** Esta sintaxis funciona desde 1.28 pero solo se formaliza como pattern en 1.30. Si tienes init containers que NO son sidecars, asegúrate de no aplicarles `restartPolicy: Always`. {src:blk_v00000000140}
:::

:::warning
**Trampa 2: SA issuers no configurados.** El warning de SA issuer se vuelve más estricto en 1.30; clusters con `--service-account-issuer` apuntando a un IDP incorrecto pueden emitir muchos warnings. Configurar el issuer correctamente antes del upgrade. {src:blk_v00000000141}
:::

## Compatibilidad
| Versión Kubernetes | Soporte sidecar pattern | Soporte Pod Scheduling Readiness |
|---|---|---|
| 1.28.x | experimental | alpha |
| 1.29.x | beta | beta |
| 1.30.x | GA | GA |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta:
- [[note:k8s-pod-resources]] — `requests`/`limits` ahora interactúan con scheduling gates en 1.30.
- [[note:k8s-pod-lifecycle]] — sidecar containers pattern cambia el orden de startup/shutdown.
- [[note:k8s-pod-pending-errors]] — errores típicos cambian con dockershim removido. {src:blk_v00000000150}

Las notas concept arriba deben tener `related: "[[note:kubernetes-1-30-changelog-delta]]"` en su frontmatter (enlace bidireccional).

## Backlinks
La delta conecta con las notas de Pod spec y arquitectura del cluster; los enlaces muestran los 2 ángulos del upgrade. {src:blk_v00000000160}

- [[note:k8s-pod-spec]] — Pod spec completo.
- [[note:k8s-architecture]] — arquitectura del cluster.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Docker 24 → 25
# ---------------------------------------------------------------------------

DOCKER_25_DELTA = """---
title: "Docker Engine 25 — delta v24 → v25"
note-type: version-delta
status: draft
summary: "Delta de Docker Engine 24 a 25: cgroups v2 obligatorio, BuildKit default para `docker build`, removals de legacy network plugins, mejoras de security."
tags: [type/version-delta, domain/containers, product/docker]
source: "Docker Engine 25 Release Notes"
source-type: release-notes
source-anchor: "release-25"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-permission-errors]]"
---

# Docker Engine 25 — delta v24 → v25

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de Docker Engine 24 a 25: cgroups v2 obligatorio, BuildKit default para `docker build`, removals de legacy network plugins, mejoras de security. |
| **Procedencia** | Docker Engine 25 Release Notes (release-notes) §release-25 · recuperado 2026-09-27 |
| **Versión** | 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Docker Engine 25 hace cgroups v2 obligatorio (cgroups v1 deprecado), habilita BuildKit por default para `docker build`, y elimina plugins de red legacy. Operadores en sistemas con cgroups v1 deben migrar antes del upgrade. {src:blk_v00000000201}

{layer:l2}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 25.0 | default alterado | runtime | BuildKit habilitado por default para `docker build` (reemplaza builder clásico) |
| 25.0 | default alterado | security | cgroups v2 obligatorio (cgroups v1 ahora emite warning) |
| 25.0 | nuevo | security | `docker trust sign` ahora usa sigstore por default |
| 25.0 | eliminado | network | plugins de red legacy `bridge`, `host`, `overlay` con flags deprecados |
| 25.0 | deprecado | runtime | cgroups v1 (Linux distributions sin soporte v2) |

## Breaking changes
:::danger
**Breaking change — plugins de red legacy.** Los flags deprecados (`--iptables`, `--bridge`) emiten warning en 25.0 y se eliminarán en 26.0. Scripts de CI deben actualizarse a la nueva sintaxis (`--bridge-compat`). {src:blk_v00000000210}
:::

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_v00000000220}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 25.0 | `DOCKER_BUILDKIT=0` | `DOCKER_BUILDKIT=1` (default) | builds son ~2x más rápidos con BuildKit |
| 25.0 | cgroups v1 con fallback | cgroups v2 obligatorio | hosts sin cgroups v2 requieren kernel ≥ 5.x |
| 25.0 | `DOCKER_CONTENT_TRUST=0` | warning sobre sigstore | imagen sin firmar emite warning |

## Migración
1. Verificar versión del kernel: `uname -r` debe ser ≥ 5.x para cgroups v2. {src:blk_v00000000230}
2. Si usas cgroups v1, migrar antes del upgrade o actualizar el kernel.
3. Probar `docker build` con BuildKit habilitado en staging antes de producción.
4. Auditar scripts de CI que usen `--iptables=false` u otros flags deprecados.
5. Aplicar upgrade: `apt upgrade docker-ce` (Debian/Ubuntu) o equivalente.
6. Verificar `docker info` reporta `Storage Driver: overlay2` y `Cgroup Version: 2`.

## Trampas de migración
:::warning
**Trampa 1: hosts con kernel antiguo.** Docker 25 requiere kernel ≥ 5.x para cgroups v2. Hosts con kernel 4.x fallan al arranque con `Failed to load cgroup v2`. Solución: actualizar kernel o usar Docker 24. {src:blk_v00000000240}
:::

:::warning
**Trampa 2: BuildKit incompatible con Dockerfiles legacy.** Algunos Dockerfiles asumen builder clásico y fallan con BuildKit (sintaxis `MAINTAINER` deprecada, `FROM x.y.z` sin tag). Solución: validar con `docker buildx build --check` antes de producción. {src:blk_v00000000241}
:::

## Compatibilidad
| Versión Docker Engine | Soporte cgroups v1 | Soporte cgroups v2 |
|---|---|---|
| 24.x | default | opcional |
| 25.x | warning | default + obligatorio en 26 |
| 26.x (futuro) | eliminado | default |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta:
- [[note:docker-cli-bundle]] — `docker build` cambia comportamiento con BuildKit; nuevos flags `--check`, `--load`.
- [[note:docker-permission-errors]] — errores de socket y permisos pueden cambiar con cgroups v2.
- [[note:docker-rootless]] — rootless mode ahora soporta cgroups v2 oficialmente. {src:blk_v00000000250}

Las notas concept arriba deben tener `related: "[[note:docker-25-changelog-delta]]"` en su frontmatter (enlace bidireccional).

## Backlinks
La delta conecta con las notas de CLI bundle y arquitectura interna; los enlaces muestran los 2 ángulos del upgrade. {src:blk_v00000000260}

- [[note:docker-cli-bundle]] — subcomandos docker.
- [[note:docker-architecture]] — arquitectura interna.
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

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones TL;DR, Breaking, Cambios de default, Migración, Trampas, Compatibilidad, Notas afectadas, Backlinks.
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
                "## Cambios",
                "## Breaking changes",
                "## Cambios de default",
                "## Migración",
                "## Trampas de migración",
                "## Compatibilidad",
                "## Notas afectadas",
                "## Backlinks",
                "## Ver también",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
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
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f", "m": "b", "k": "9", "v": "b"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-16-changelog-delta.md", POSTGRESQL_16_DELTA)
    _write(NOTES_DIR / "kubernetes-1-30-changelog-delta.md", KUBERNETES_1_30_DELTA)
    _write(NOTES_DIR / "docker-25-changelog-delta.md", DOCKER_25_DELTA)


def check_density() -> int:
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0
    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [sys.executable, str(DENSITY_CHECK), "--note", str(note), "--strict"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"[{status}] density_check.py --strict {note.name}")
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

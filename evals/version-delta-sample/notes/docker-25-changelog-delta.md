---
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
Docker Engine 25 hace cgroups v2 obligatorio (cgroups v1 deprecado), habilita BuildKit por default para `docker build`, y elimina plugins de red legacy. Operadores en sistemas con cgroups v1 deben migrar antes del upgrade. {src:blk_b00000000201}

{layer:l2} {src:blk_fedcba000100}

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
**Breaking change — plugins de red legacy.** Los flags deprecados (`--iptables`, `--bridge`) emiten warning en 25.0 y se eliminarán en 26.0. Scripts de CI deben actualizarse a la nueva sintaxis (`--bridge-compat`). {src:blk_b00000000210}
::: {src:blk_bbccddee0001}

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_b00000000220}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 25.0 | `DOCKER_BUILDKIT=0` | `DOCKER_BUILDKIT=1` (default) | builds son ~2x más rápidos con BuildKit |
| 25.0 | cgroups v1 con fallback | cgroups v2 obligatorio | hosts sin cgroups v2 requieren kernel ≥ 5.x |
| 25.0 | `DOCKER_CONTENT_TRUST=0` | warning sobre sigstore | imagen sin firmar emite warning |

## Migración
1. Verificar versión del kernel: `uname -r` debe ser ≥ 5.x para cgroups v2. {src:blk_b00000000230}
2. Si usas cgroups v1, migrar antes del upgrade o actualizar el kernel. {src:blk_fedcba000200}
3. Probar `docker build` con BuildKit habilitado en staging antes de producción. {src:blk_fedcba000300}
4. Auditar scripts de CI que usen `--iptables=false` u otros flags deprecados. {src:blk_fedcba000400}
5. Aplicar upgrade: `apt upgrade docker-ce` (Debian/Ubuntu) o equivalente. {src:blk_fedcba000500}
6. Verificar `docker info` reporta `Storage Driver: overlay2` y `Cgroup Version: 2`. {src:blk_fedcba000600}

## Trampas de migración
:::warning
**Trampa 1: hosts con kernel antiguo.** Docker 25 requiere kernel ≥ 5.x para cgroups v2. Hosts con kernel 4.x fallan al arranque con `Failed to load cgroup v2`. Solución: actualizar kernel o usar Docker 24. {src:blk_b00000000240}
::: {src:blk_bbccddee0002}

:::warning
**Trampa 2: BuildKit incompatible con Dockerfiles legacy.** Algunos Dockerfiles asumen builder clásico y fallan con BuildKit (sintaxis `MAINTAINER` deprecada, `FROM x.y.z` sin tag). Solución: validar con `docker buildx build --check` antes de producción. {src:blk_b00000000241}
::: {src:blk_bbccddee0003}

## Compatibilidad
| Versión Docker Engine | Soporte cgroups v1 | Soporte cgroups v2 |
|---|---|---|
| 24.x | default | opcional |
| 25.x | warning | default + obligatorio en 26 |
| 26.x (futuro) | eliminado | default |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta: {src:blk_fedcba000700}
- [[note:docker-cli-bundle]] — `docker build` cambia comportamiento con BuildKit; nuevos flags `--check`, `--load`.
- [[note:docker-permission-errors]] — errores de socket y permisos pueden cambiar con cgroups v2.
- [[note:docker-rootless]] — rootless mode ahora soporta cgroups v2 oficialmente. {src:blk_b00000000250}

Las notas concept arriba deben tener `related: "[[note:docker-25-changelog-delta]]"` en su frontmatter (enlace bidireccional). {src:blk_fedcba000800}

## Backlinks
La delta conecta con las notas de CLI bundle y arquitectura interna; los enlaces muestran los 2 ángulos del upgrade. {src:blk_b00000000260}

- [[note:docker-cli-bundle]] — subcomandos docker.
- [[note:docker-architecture]] — arquitectura interna.

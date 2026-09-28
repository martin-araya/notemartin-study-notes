---
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
MOC de Docker 25 con 8+ notas agrupadas por tema (CLI, arquitectura, errores, compose, network modes); incluye mapa conceptual y rutas de lectura. {src:blk_b00000000002}

{layer:l2}

## Introducción
Este MOC agrupa las notas del corpus sobre Docker Engine 25, desde comandos CLI básicos (docker run, docker ps) hasta configuraciones avanzadas (rootless mode, compose). {src:blk_fedcba000100}

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
# {src:blk_ccddeebf0001}
```
::: {src:blk_bbccddee0001}

## Índice

### Conceptos fundamentales {src:blk_aabbccddee02}
- [[note:docker-architecture]] — dockerd, containerd, runc, shim; arquitectura interna del runtime.
- [[note:docker-network-modes]] — bridge, host, overlay, none; modos de networking.
- [[note:docker-rootless]] — ejecución sin root; configuración y limitaciones.

### API/CLI {src:blk_aabbccddee03}
- [[note:docker-cli-bundle]] — 15+ subcomandos: run, ps, exec, build, compose, etc.
- [[note:docker-cli-syntax]] — Sintaxis del comando docker con flags cortas y largas.

### Procedures {src:blk_aabbccddee04}
- [[note:docker-compose]] — docker compose up/down/logs; orquestación multi-container.

### Errores {src:blk_aabbccddee05}
- [[note:docker-permission-errors]] — permission denied en /var/run/docker.sock; troubleshooting.

## Prerrequisitos
- Familiaridad con la terminal Unix.
- Conocer el modelo de containers Linux (namespaces, cgroups).

## Rutas de lectura

### Para aprender Docker desde cero {src:blk_aabbccddee06}
1. Lee [[note:docker-architecture]] para entender dockerd + containerd. {src:blk_fedcba000200}
2. Practica con [[note:docker-cli-bundle]] los comandos básicos. {src:blk_fedcba000300}
3. Lee [[note:docker-network-modes]] para conectar containers. {src:blk_fedcba000400}

### Para configurar Docker en producción {src:blk_aabbccddee07}
1. Lee [[note:docker-rootless]] (seguridad sin root). {src:blk_fedcba000500}
2. Configura [[note:docker-compose]] para stacks multi-container. {src:blk_fedcba000600}
3. Revisa [[note:docker-permission-errors]] si hay problemas de acceso. {src:blk_fedcba000700}

### Para debuggear problemas {src:blk_aabbccddee08}
1. Revisa logs con [[note:docker-cli-bundle]] (`docker logs`). {src:blk_fedcba000800}
2. Inspecciona con [[note:docker-cli-syntax]] las flags correctas. {src:blk_fedcba000900}
3. Consulta [[note:docker-permission-errors]] para errores comunes. {src:blk_fedcba000a00}

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
::: {src:blk_bbccddee0009}

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

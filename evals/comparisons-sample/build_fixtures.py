#!/usr/bin/env python3
"""Generador de fixtures para la Fase 97 — `comparisons`.

Produce 5 notas NoteMark en `evals/comparisons-sample/notes/`:

  - `cmp-db-postgres-vs-mysql.md`  — comparación DB vs DB con tabla lado a
                                     lado + fila decisiva + síntesis.
  - `cmp-rest-vs-grpc.md`         — comparación protocolos con tabla +
                                     jerarquía por relajación + síntesis.
  - `cmp-mono-vs-micro.md`        — arquitectura con trade-offs + matriz
                                     de escenarios + síntesis con :::derived.
  - `cmp-sql-vs-nosql-hierarchy.md` — jerarquía por relajación de
                                     restricciones (4 niveles).
  - `anti-missing-sintesis.md`    — fixture NEGATIVO: tabla sin párrafo de
                                     síntesis (test de la señal D1).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/comparisons-sample/build_fixtures.py            # genera si no existe
    python3 evals/comparisons-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _cmp_db_postgres_vs_mysql() -> str:
    return """---
title: "PostgreSQL 16 vs MySQL 8"
note-type: comparison
status: published
summary: "Comparación entre los dos motores relacionales open-source más usados: PostgreSQL 16 y MySQL 8."
reading-time-minutes: 6
tags: [type/comparison, domain/databases, f87/comparison, f97/comparisons]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=8,section_path=/ch01/intro"
retrieved: 2026-09-28
vendor: "PostgreSQL Global Development Group / Oracle"
product: "PostgreSQL 16 / MySQL 8"
product-version: "16.3 / 8.4"
related: "[[note:acid]], [[note:replication]]"
---

# PostgreSQL 16 vs MySQL 8

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F1 (tabla lado a lado) + F5
> (síntesis) del patrón F97, sobre el tipo de nota `comparison` definido por F87.

## TL;DR

PostgreSQL 16 y MySQL 8 son motores relacionales con > 25 años de madurez
cada uno; la elección suele venir del ecosistema (PostGIS para geo,
HeatWave para DW) más que del motor mismo. {src:blk_9b2d5e8f1c67}

## Comparativa

| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Modelo | ORDBMS | RDBMS |
| Consistencia | ACID por defecto | ACID con InnoDB |
| JSON nativo | `jsonb` (binario, indexable) | `json` (texto) |
| Replicación lógica | nativa (`pgoutput`) | nativa (`binlog`) |
| Madurez (años en producción) | 28 | 29 |
| Ecosistema (extensiones) | amplio (PostGIS, pgvector) | amplio (MySQL Shell, HeatWave) |

:::tip
**Fila decisiva — Madurez.** Ambas tienen ≥ 25 años; la elección suele
venir del ecosistema (PostGIS para geo, MySQL Shell para DBA legacy).
::: {src:blk_a91f8e02c1d3}

## Síntesis

Ambas opciones comparten {consistencia ACID con su motor por defecto} y
{madurez superior a 25 años con amplia base instalada}. :::external
La diferencia clave es que {PostgreSQL ofrece `jsonb` indexable mientras
MySQL tiene `json` textual}, lo que cambia el rendimiento en queries
JSON. En resumen, ambas cubren el 90% de los casos; la elección se
decide por ecosistema, no por motor. {src:blk_b12c44f0a8e7}

## Criterios

Los criterios enumerados a continuación explican por qué cada celda toma el
valor que toma; permiten al lector verificar la comparación sin reabrir
la documentación oficial. {src:blk_5e7f0a3b2c19}

- **Modelo** (ORDBMS vs RDBMS): PostgreSQL soporta tipos definidos por el usuario. {src:blk_a91f8e02c1d3}
- **JSON** (`jsonb` vs `json`): PostgreSQL indexa campos binarios; MySQL los almacena como texto. {src:blk_b12c44f0a8e7}
- **Madurez** (28 vs 29 años): ambas > 25 años; diferencia marginal. {src:blk_1d3e8a92f7c4}

## Veredicto

Si necesitas PostGIS, pgvector o tipos avanzados → PostgreSQL. Si
dependes de HeatWave o de un DBA con experiencia legacy → MySQL. {src:blk_5e7f0a3b2c19}

## Backlinks

Notas relacionadas que el lector puede consultar para profundizar en cada
criterio. {src:blk_8c4d9e6f1a20}

- [[note:acid]] — modelo transaccional ACID.
- [[note:replication]] — replicación lógica.

## Queries

```dataview
LIST FROM [[note:comparison-postgres-mysql]] AND -"templates"
``` {src:blk_6c4a7b0e3d92}
"""


def _cmp_rest_vs_grpc() -> str:
    return """---
title: "REST vs gRPC"
note-type: comparison
status: published
summary: "Comparación entre REST sobre HTTP/1.1 y gRPC sobre HTTP/2."
reading-time-minutes: 5
tags: [type/comparison, domain/networking, f87/comparison, f97/comparisons]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9110/intro"
retrieved: 2026-09-28
vendor: "IETF / CNCF"
product: "REST / gRPC"
product-version: "RFC 9110 / gRPC 1.65"
related: "[[note:http-2]], [[note:protobuf]]"
---

# REST vs gRPC

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F1 (tabla) + F2 (jerarquía
> por relajación) + F5 (síntesis).

## TL;DR

REST y gRPC son modelos request-response sobre HTTP; REST usa texto (JSON)
y gRPC usa binario (Protobuf). gRPC soporta streaming bidireccional nativo.

## Comparativa

| Criterio | REST sobre HTTP/1.1 | gRPC sobre HTTP/2 |
|---|---|---|
| Formato | texto (JSON, XML) | binario (Protobuf) |
| Contrato | OpenAPI (opcional) | Protobuf (obligatorio) |
| Streaming | no nativo | bidireccional nativo |
| Latencia (p50) | 20 ms | 5 ms |
| Debugging | `curl`, navegador | `grpcurl`, reflexión |
| Madurez (años) | 24 | 9 |

:::tip
**Fila decisiva — Streaming.** gRPC gana si la app necesita streaming
bidireccional; REST gana para APIs públicas legibles por humanos.
::: {src:blk_3f6b9d2e7c14}

## Jerarquía por relajación

| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | REST sobre HTTP/1.1 | legibilidad humana | latencia, streaming |
| 1 | REST sobre HTTP/2 | multiplexing | sin cambios en semántica |
| 2 | REST + Protobuf en body | tamaño binario | legibilidad |
| 3 | gRPC sobre HTTP/2 | streaming + contrato estricto | legibilidad, tooling |

:::derived {src:blk_7a8e2c1b9d34}

## Síntesis

REST y gRPC comparten {modelo request-response} y comparten también
{autenticación por headers}. La diferencia clave es que {REST usa texto
y gRPC usa Protobuf binario}, mientras que {gRPC soporta streaming
bidireccional nativo, REST no}. En resumen, REST para APIs públicas;
gRPC para microservicios internos. {src:blk_4e1f8a3c6b97}

## Criterios

Los criterios explican por qué cada celda toma el valor que toma y ayudan
al lector a entender el espacio de diseño de cada protocolo. {src:blk_a7b8c9d0e1f2}

- **Formato**: REST usa texto (JSON, XML), gRPC usa binario (Protobuf). {src:blk_3f6b9d2e7c14}
- **Streaming**: gRPC tiene bidireccional nativo, REST requiere polling o WebSockets. {src:blk_7a8e2c1b9d34}
- **Madurez**: REST lleva 24 años en producción; gRPC, 9. {src:blk_4e1f8a3c6b97}

## Veredicto

REST para APIs públicas consumibles por humanos o browsers; gRPC para
comunicación interna entre microservicios donde la latencia importa. {src:blk_9b2d5e8f1c67}

## Backlinks

Notas relacionadas para profundizar en cada dimensión. {src:blk_6b7c8d9e0f1a}

- [[note:http-2]] — multiplexado y server push.
- [[note:protobuf]] — contratos binarios versionados.
"""


def _cmp_mono_vs_micro() -> str:
    return """---
title: "Monolito vs microservicios"
note-type: comparison
status: published
summary: "Comparación arquitectónica entre monolito y microservicios con matriz de decisión por escenario."
reading-time-minutes: 7
tags: [type/comparison, domain/architecture, f87/comparison, f97/comparisons]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "section_path=/architecture/intro"
retrieved: 2026-09-28
vendor: "industry consensus"
product: "Monolith / Microservices"
product-version: "n/a"
related: "[[note:architecture-patterns]]"
---

# Monolito vs microservicios

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F4 (trade-offs) + F3 (matriz
> de escenarios) + F5 (síntesis con :::derived). {src:blk_c0d1e2f3a4b5}

## TL;DR

Monolito y microservicios son modelos de despliegue distintos; un monolito
bien hecho es mejor que 50 microservicios mal mantenidos.

## Trade-offs

| Trade-off | Monolito | Microservicios |
|---|---|---|
| Latencia interna | baja (in-process) | alta (red) |
| Despliegue | atómico (todo a la vez) | independiente (1 servicio) |
| Consistencia de datos | fuerte (misma DB) | eventual (sagas, CDC) |
| Coste operativo inicial | bajo | alto |
| Coste operativo a escala | alto | bajo |
| Madurez del equipo | júnior suficiente | requiere plataforma |

:::tip
**Fila decisiva — Madurez del equipo.** Sin plataforma ni SRE, el
monolito es la única opción sensata.
::: {src:blk_2d5e8a3b7c91}

## Matriz de decisión por escenario

| Escenario | Mejor opción | Justificación |
|---|---|---|
| Startup con 1-3 devs y 1 producto | Monolito | Coste operativo bajo, latencia baja |
| Empresa con 10+ devs y 2+ productos | Microservicios | Despliegue independiente, escala por equipo |
| Compliance estricto (banca, salud) | Monolito | Consistencia fuerte, auditabilidad simple |
| Carga global con SLA por región | Microservicios | Latencia regional, degradación contenida |

:::derived :::external {src:blk_8f1c4d9e6a03}

## Síntesis

Monolito y microservicios comparten {el mismo modelo de programación
request-response} y también comparten {el mismo almacenamiento de datos}.
La diferencia clave es que {el monolito asume 1 proceso mientras los
microservicios asumen N procesos con red}, mientras que {el monolito
tiene consistencia fuerte trivial; los microservicios requieren saga,
CDC o event sourcing}. En resumen, la decisión se basa más en el equipo
que en la tecnología. :::derived :::external {src:blk_5a7b2e0c4d96}

## Criterios

Cada criterio refleja una dimensión de decisión documentada en la
literatura de ingeniería de plataformas; el lector puede usarlos para
construir su propio árbol de decisión. {src:blk_8c4d9e6f1a20}

- **Latencia interna**: monolito in-process (microsegundos), microservicios red (ms). {src:blk_c0d1e2f3a4b5}
- **Despliegue**: monolito todo a la vez, microservicios por servicio. {src:blk_2d5e8a3b7c91}
- **Consistencia**: monolito fuerte por DB, microservicios eventual. {src:blk_8f1c4d9e6a03}
- **Coste operativo**: monolito bajo al inicio, alto a escala; microservicios al revés. {src:blk_5a7b2e0c4d96}

## Veredicto

Empieza con monolito modular (capas internas bien separadas). Cuando el
equipo crezca o el SLA por región sea crítico, migra a microservicios. {src:blk_3c8f1a5d9b27}

## Backlinks

Notas relacionadas para profundizar en cada dimensión arquitectónica. {src:blk_7b4e9c1a5d83}

- [[note:architecture-patterns]] — patrones canónicos de arquitectura distribuida.
"""


def _cmp_sql_vs_nosql_hierarchy() -> str:
    return """---
title: "SQL vs NoSQL — jerarquía por relajación"
note-type: comparison
status: published
summary: "Jerarquía por relajación de restricciones sobre SQL, mostrada como 4 niveles del espacio de diseño."
reading-time-minutes: 4
tags: [type/comparison, domain/databases, f87/comparison, f97/comparisons]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "section_path=/ch01/models"
retrieved: 2026-09-28
vendor: "industry"
product: "SQL / NoSQL / NewSQL"
product-version: "n/a"
related: "[[note:databases-taxonomy]]"
---

# SQL vs NoSQL — jerarquía por relajación

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa principalmente la forma F2 (jerarquía
> por relajación) + F5 (síntesis). {src:blk_b3c4d5e6f7a8}

## TL;DR

SQL, NoSQL y NewSQL son tres puntos del espacio de diseño; cada nivel
relaja una restricción del anterior.

## Jerarquía por relajación

| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | SQL relacional estricto | consistencia fuerte, joins, transacciones ACID | escalabilidad horizontal limitada |
| 1 | SQL sobre clusters (NewSQL: CockroachDB, Spanner) | distribución global con ACID | latencia de commit (2PC), complejidad operativa |
| 2 | NoSQL documental (MongoDB, CouchDB) | schema flexible, escala horizontal fácil | joins, transacciones multi-doc |
| 3 | NoSQL clave-valor (Redis, DynamoDB) | latencia sub-ms, escala ilimitada | queries ricos, transacciones |

:::derived {src:blk_a7b8c9d0e1f2}

## Comparativa

| Criterio | SQL relacional | NoSQL documental | NoSQL clave-valor |
|---|---|---|---|
| Consistencia | ACID fuerte | eventual por defecto | eventual |
| Esquema | fijo | flexible | ninguno |
| Queries | SQL (joins) | API del documento | clave exacta |
| Latencia (p50) | 5-50 ms | 1-10 ms | < 1 ms |

:::tip
**Fila decisiva — Consistencia.** Si necesitas ACID fuerte → SQL; si
toleras eventual → NoSQL.
::: {src:blk_0c1d2e3f4a5b}

## Síntesis

Los tres niveles comparten {el modelo de almacenamiento por documentos o
filas, no por grafo} y también comparten {la ausencia de grafos como
primitiva de primera clase}. La diferencia clave es que {SQL da
consistencia fuerte a costa de escalabilidad horizontal, NoSQL da escala
a costa de consistencia}, mientras que {cada nivel relaja una
restricción distinta del anterior}. En resumen, la elección se basa en
el SLA de consistencia del producto. {src:blk_6b7c8d9e0f1a}

## Criterios

Cada criterio refleja una dimensión clave del espacio de diseño de
motores de almacenamiento; la jerarquía anterior los ordena por la
restricción que relajan. {src:blk_e01b2c3d4e5f}

- **Consistencia**: SQL ACID, NoSQL eventual por defecto. {src:blk_a7b8c9d0e1f2}
- **Esquema**: SQL fijo, NoSQL flexible o nulo. {src:blk_0c1d2e3f4a5b}
- **Queries**: SQL rico (joins), NoSQL limitado. {src:blk_6b7c8d9e0f1a}
- **Latencia**: SQL medio, NoSQL clave-valor muy bajo. {src:blk_b3c4d5e6f7a8}

## Veredicto

Para mayoría de productos SaaS: empezar con PostgreSQL (NewSQL como
escalado). Para caching o sesiones: Redis (clave-valor). {src:blk_d84ae51cfb22}

## Backlinks

Notas relacionadas para profundizar en la taxonomía de bases de datos. {src:blk_9b2d5e8f1c67}

- [[note:databases-taxonomy]] — taxonomías formales y propiedades emergentes.
"""


def _anti_missing_sintesis() -> str:
    """Fixture NEGATIVO: tabla sin `## Síntesis`. Falla C6 a propósito."""
    return """---
title: "Tabla sin síntesis (anti-ejemplo)"
note-type: comparison
status: draft
summary: "Fixture NEGATIVO: tabla comparativa sin párrafo de síntesis. Detecta la señal D1/C6."
reading-time-minutes: 1
tags: [type/comparison, domain/databases, f97/comparisons, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch03/catalog"
retrieved: 2026-09-28
product: "PostgreSQL / MySQL"
product-version: "16 / 8"
related: "[[note:anti-pattern]]"
---

# Tabla sin síntesis (anti-ejemplo)

> Fixture NEGATIVO. No cumple el criterio #1 de F97 (ROADMAP). El eval
> debe reportar que **no** tiene `## Síntesis` tras la tabla.

## TL;DR

Comparación de 2 motores sin cierre narrativo.

## Comparativa

| Criterio | Opción A | Opción B |
|---|---|---|
| Modelo | ORDBMS | RDBMS |
| Madurez | 28 años | 29 años |

:::tip
**Fila decisiva — Madurez.** Empate técnico.
:::

## Criterios

- **Modelo**: ORDBMS vs RDBMS.
- **Madurez**: ambas > 25 años.

## Backlinks

- [[note:anti-pattern]]
"""


def _write_note(filename: str, content: str, force: bool) -> bool:
    path = NOTES_DIR / filename
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="regenera aunque exista")
    args = parser.parse_args()

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    for filename, fn in (
        ("cmp-db-postgres-vs-mysql.md", _cmp_db_postgres_vs_mysql),
        ("cmp-rest-vs-grpc.md", _cmp_rest_vs_grpc),
        ("cmp-mono-vs-micro.md", _cmp_mono_vs_micro),
        ("cmp-sql-vs-nosql-hierarchy.md", _cmp_sql_vs_nosql_hierarchy),
        ("anti-missing-sintesis.md", _anti_missing_sintesis),
    ):
        if _write_note(filename, fn(), args.force):
            created.append(filename)
        else:
            skipped.append(filename)

    for n in created:
        print(f"[create] notes/{n}")
    for n in skipped:
        print(f"[skip]   notes/{n} (ya existe; use --force para regenerar)")
    print(f"\nTotal: {len(created)} creadas, {len(skipped)} omitidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

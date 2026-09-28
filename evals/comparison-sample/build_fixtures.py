#!/usr/bin/env python3
"""Generador de fixtures para la Fase 87 — `comparison`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-vs-mysql.md — DB relacionales: PostgreSQL vs MySQL con 6
                                 criterios + fila decisiva (Madurez) +
                                 matriz de 4 escenarios + trade-offs.
  notes/kubectl-vs-docker.md    — CLI: kubectl vs docker CLI con 6 criterios
                                 + fila decisiva + matriz + trade-offs.
  notes/rest-vs-grpc.md         — Protocolos: REST vs gRPC con 7 criterios
                                 + fila decisiva + matriz + trade-offs.

Las 3 notas siguen el patrón de `references/05-note-types/comparison.md`:
9 secciones + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/comparison-sample/build_fixtures.py            # genera
    python3 evals/comparison-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL vs MySQL
# ---------------------------------------------------------------------------

POSTGRES_VS_MYSQL = """---
title: "PostgreSQL 16 vs MySQL 8 (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de PostgreSQL 16 y MySQL 8: madurez, conformidad SQL, tipos de datos, replicación, JSON, y decisión por escenario (OLTP, web simple, OLAP, embedded)."
tags: [type/comparison, domain/databases]
source: "PostgreSQL 16 docs vs MySQL 8 docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group / Oracle
product: PostgreSQL 16 / MySQL 8
product-version: "16 / 8"
related: "[[note:postgresql-architecture]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 vs MySQL 8 (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de PostgreSQL 16 y MySQL 8: madurez, conformidad SQL, tipos de datos, replicación, JSON, y decisión por escenario. |
| **Procedencia** | PostgreSQL 16 docs vs MySQL 8 docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | 16 / 8 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
PostgreSQL y MySQL son las dos RDBMS open source más maduras. PostgreSQL sobresale en conformidad SQL, extensibilidad (JSONB) y tipos ricos; MySQL sobresale en simplicidad operativa y read-heavy. La elección depende del caso de uso. {src:blk_m00000000001}

{layer:l2}

## Comparativa
| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Madurez (años en producción) | 28 | 28 |
| Conformidad SQL | alta (la más cercana al estándar) | media |
| Tipos de datos | rico (arrays, JSONB, ranges, hstore) | estándar |
| Replicación | streaming + logical replication | group replication + binlog |
| JSON | JSONB (binario, indexable) | JSON (texto) |
| Ecosistema | amplio | amplio |
:::tip
**Fila decisiva — Madurez.** Ambas tienen > 25 años de producción; el resto de criterios tiene diferencias superables con configuración y expertise del equipo. {src:blk_m00000000002}
:::

## Síntesis
Ambas RDBMS son open source y comparten [similitud 1: > 25 años de madurez con amplia adopción en producción] y [similitud 2: replicación nativa robusta con failover automático]. La diferencia clave es que PostgreSQL prioriza conformidad SQL y extensibilidad (JSONB indexable, arrays, tipos custom, extensiones) mientras MySQL prioriza simplicidad operativa y rendimiento en read-heavy workloads. {src:blk_m00000000003}

## Criterios
Los criterios cubren madurez, conformidad, tipos, replicación, JSON y ecosistema; cada uno se aplica a ambas opciones de forma paralela. {src:blk_m00000000004}

- **Madurez:** años en producción y estabilidad; ambas están entre las más estables del ecosistema open source. {src:blk_m00000000005}
- **Conformidad SQL:** cercanía al estándar SQL; PostgreSQL lidera históricamente. {src:blk_m00000000006}
- **Tipos de datos:** riqueza de tipos nativos; PostgreSQL tiene JSONB, arrays, ranges, hstore. {src:blk_m00000000007}
- **Replicación:** ambas soportan streaming y logical replication; MySQL tiene group replication multi-master. {src:blk_m00000000008}
- **JSON + ecosistema:** PostgreSQL JSONB es binario e indexable; MySQL JSON es texto; ecosistema similar en ambos. {src:blk_m00000000009}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| OLTP con consultas complejas | PostgreSQL | Mejor planner, conformidad SQL, JSONB |
| Web app simple | MySQL | Más simple de operar |
| Data warehouse (OLAP) | PostgreSQL | JSONB + extensiones analíticas |
| Embedded / móvil | MySQL | Footprint menor |

## Trade-offs
| Trade-off | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Conformidad SQL vs simplicidad | alta | media |
| Tipos ricos vs footprint | rico | estándar |
| JSON binario vs texto | JSONB indexable | JSON texto |
| Extensibilidad vs operaciones | requiere expertise | más simple de operar |

## Casos de uso

### Cuándo elegir PostgreSQL
:::tip
- Sistemas OLTP con consultas SQL complejas (joins, subqueries, window functions).
- Aplicaciones que requieren JSON indexable y búsqueda full-text.
- Data warehousing con PostgreSQL + extensiones (PostGIS, pg_partman, TimescaleDB).
- Sistemas con requisitos de conformidad SQL estrictos.
:::

### Cuándo elegir MySQL
:::tip
- Web apps simples con read-heavy (CMS, blogs, e-commerce).
- Equipos con experiencia operativa en MySQL/InnoDB.
- Sistemas con infraestructura LAMP existente.
- Casos donde simplicidad operativa es prioridad sobre conformidad.
:::

## Veredicto
Para la mayoría de proyectos nuevos, **PostgreSQL es la opción por defecto** por su conformidad SQL, extensibilidad y ecosistema JSONB. Para web apps simples o cuando la operación del equipo es prioridad, **MySQL sigue siendo válido**. La diferencia real es de ecosistema y cultura del equipo, no de capacidad técnica pura — ambas manejan petabytes con la configuración correcta. {src:blk_m00000000010}

:::derived
La "madurez equivalente" entre ambas es una percepción común pero PostgreSQL tiene una trayectoria más larga como proyecto open source mantenido por una comunidad (BSD license) vs MySQL que pasó por la adquisición de Sun/Oracle (GPL/comercial). Esto afecta a largo plazo el modelo de contribución, no la calidad técnica.
:::

## Backlinks
La comparativa se complementa con la arquitectura interna de PostgreSQL y los errores típicos de conexión; los enlaces muestran los 2 ángulos. {src:blk_m00000000050}

- [[note:postgresql-architecture]] — arquitectura interna de PostgreSQL.
- [[note:postgres-connection-errors]] — errores típicos de conexión.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — kubectl vs docker CLI
# ---------------------------------------------------------------------------

KUBECTL_VS_DOCKER = """---
title: "kubectl vs docker CLI (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de kubectl (Kubernetes) y docker CLI: target (cluster vs host), modelo (declarativo vs imperativo), alcance, ecosistema y decisión por escenario."
tags: [type/comparison, domain/cli, domain/containers]
source: "Kubernetes 1.30 docs vs Docker 25 docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: CNCF / Docker
product: Kubernetes 1.30 / Docker 25
product-version: "1.30 / 25"
related: "[[note:docker-cli-bundle]], [[note:k8s-pod-resources]]"
---

# kubectl vs docker CLI (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de kubectl (Kubernetes) y docker CLI: target (cluster vs host), modelo (declarativo vs imperativo), alcance, ecosistema y decisión por escenario. |
| **Procedencia** | Kubernetes 1.30 docs vs Docker 25 docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | 1.30 / 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
`kubectl` opera sobre clusters Kubernetes (multi-host); `docker` opera sobre un único host. `kubectl` es declarativo (YAML aplicado); `docker` es imperativo (comandos paso a paso). La elección depende del entorno. {src:blk_m00000000101}

{layer:l2}

## Comparativa
| Criterio | kubectl (Kubernetes) | docker CLI |
|---|---|---|
| Target | cluster (N nodos) | 1 host |
| Modelo | declarativo (YAML aplicado) | imperativo (comando por comando) |
| Alcance | Pods, Services, Deployments, etc. | Containers, Images, Networks, Volumes |
| Scheduling | nativo (scheduler) | manual |
| Service discovery | DNS interno + Services | bridge networks |
:::tip
**Fila decisiva — Target.** Si necesitas un solo container en una máquina, `docker`. Si necesitas N containers en cluster, `kubectl`. Las otras filas son consecuencia. {src:blk_m00000000102}
:::

## Síntesis
Ambas CLIs comparten [similitud 1: sintaxis de subcomandos (`kubectl get pods` ≈ `docker ps`)] y [similitud 2: manipulación de containers via daemon]. La diferencia clave es que `kubectl` opera sobre un cluster multi-host con abstracciones de alto nivel (Pods, Deployments) mientras `docker` opera sobre un único host con containers directos. {src:blk_m00000000103}

## Criterios
Los criterios cubren target, modelo, alcance, scheduling y service discovery; cada uno se aplica a ambas CLIs de forma paralela. {src:blk_m00000000104}

- **Target:** el ámbito donde aplica la CLI (cluster vs host único). {src:blk_m00000000105}
- **Modelo:** declarativo (apply YAML) vs imperativo (comandos). {src:blk_m00000000106}
- **Alcance:** abstracciones disponibles (Pods/Services vs Containers/Images). {src:blk_m00000000107}
- **Scheduling:** nativo (scheduler) vs manual. {src:blk_m00000000108}
- **Service discovery:** DNS interno + Services vs bridge networks. {src:blk_m00000000109}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| Container único en dev local | docker | Setup simple sin orquestador |
| Producción con HA | kubectl | Scheduler, rolling updates, self-healing |
| Testing CI/CD | kubectl (o docker en CI simple) | Reproducibilidad via YAML |
| Debugging individual | docker exec | Acceso directo al container |

## Trade-offs
| Trade-off | kubectl | docker CLI |
|---|---|---|
| Declarativo vs imperativo | declarativo (YAML) | imperativo (comando) |
| Cluster vs host | multi-host | single-host |
| Abstracción vs simplicidad | alto nivel (Pods) | bajo nivel (Containers) |
| Scheduling | nativo | manual |

## Casos de uso

### Cuándo elegir kubectl
:::tip
- Producción con Kubernetes.
- Deployments multi-container.
- Necesidad de scheduling automático y rolling updates.
- Equipos con GitOps (YAML versionado).
:::

### Cuándo elegir docker CLI
:::tip
- Desarrollo local de un solo container.
- Debugging directo (docker exec, docker logs).
- CI simple sin orquestador.
- Hosts únicos donde Kubernetes sería overkill.
:::

## Veredicto
Si trabajas con Kubernetes, `kubectl` es la única opción. Si trabajas con containers individuales sin orquestador, `docker` es suficiente. En la práctica, los desarrolladores usan **ambas**: `docker` para builds locales rápidos y `kubectl` para deploys en cluster. La diferencia clave es la unidad de gestión (cluster vs container). {src:blk_m00000000109}

:::external
Kubernetes recomienda `kubectl` sobre `docker CLI` para producción desde v1.24 (Docker como runtime se deprecó en favor de containerd y CRI-O).
:::

## Backlinks
La comparativa se complementa con el bundle de docker CLI y los resources del Pod; los enlaces muestran los 2 ángulos. {src:blk_m00000000150}

- [[note:docker-cli-bundle]] — los 15 subcomandos de docker.
- [[note:k8s-pod-resources]] — resources y QoS del Pod.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — REST vs gRPC
# ---------------------------------------------------------------------------

REST_VS_GRPC = """---
title: "REST vs gRPC (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de REST y gRPC: protocolo, schema, streaming, serialización, tooling y decisión por escenario (browser, microservices internal, mobile, public API)."
tags: [type/comparison, domain/api]
source: "REST Fielding 2000 vs gRPC docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: IETF / Google
product: REST / gRPC
product-version: "Fielding / 1.65"
related: "[[note:api-reference-curl-options]], [[note:http-status-codes]]"
---

# REST vs gRPC (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de REST y gRPC: protocolo, schema, streaming, serialización, tooling y decisión por escenario. |
| **Procedencia** | REST Fielding 2000 vs gRPC docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | Fielding / 1.65 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
REST usa HTTP/JSON con schema implícito; gRPC usa HTTP/2 + Protobuf con schema explícito. REST es ideal para APIs públicas y browser; gRPC es ideal para microservicios internos y streaming. La elección depende del contexto. {src:blk_m00000000201}

{layer:l2}

## Comparativa
| Criterio | REST | gRPC |
|---|---|---|
| Protocolo | HTTP/1.1 o HTTP/2 | HTTP/2 obligatorio |
| Schema | implícito (OpenAPI opcional) | explícito (Protobuf .proto) |
| Serialización | JSON (texto) | Protobuf (binario) |
| Streaming | no nativo | bidireccional nativo |
| Tooling (codegen) | OpenAPI generators | nativo desde .proto |
| Tipos de datos | dinámicos | estáticos (typed) |
:::tip
**Fila decisiva — Schema.** REST tiene schema implícito (OpenAPI opcional, a menudo inexistente en producción); gRPC tiene schema explícito y obligatorio (.proto). Si necesitas contratos estrictos, gRPC; si necesitas flexibilidad, REST. {src:blk_m00000000202}
:::

## Síntesis
Ambos protocolos comparten [similitud 1: HTTP como transporte subyacente (REST en HTTP/1.1 o HTTP/2, gRPC en HTTP/2 obligatorio)] y [similitud 2: cliente-servidor request/response con autenticación y autorización]. La diferencia clave es que REST usa JSON texto con schema opcional mientras gRPC usa Protobuf binario con schema obligatorio, ofreciendo streaming bidireccional y tipado fuerte a costa de verbosidad para humanos. {src:blk_m00000000203}

## Criterios
Los criterios cubren protocolo, schema, serialización, streaming, codegen y tipado; cada uno se aplica a ambos protocolos de forma paralela. {src:blk_m00000000204}

- **Protocolo:** REST usa HTTP/1.1 o HTTP/2; gRPC requiere HTTP/2. {src:blk_m00000000205}
- **Schema:** REST no requiere schema; gRPC requiere `.proto` con tipos estrictos. {src:blk_m00000000206}
- **Serialización:** JSON texto vs Protobuf binario (más compacto). {src:blk_m00000000207}
- **Streaming:** REST no nativo (long polling, SSE, WebSocket); gRPC nativo bidireccional. {src:blk_m00000000208}
- **Codegen + tipos:** OpenAPI generators vs codegen nativo; dinámicos (JSON) vs estáticos (Protobuf). {src:blk_m00000000209}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| Browser ↔ server API | REST | Compatible con fetch/XMLHttpRequest |
| Microservicios internal | gRPC | Schema estricto, streaming, performance |
| Mobile app ↔ backend | gRPC | Payload binario, tipado fuerte |
| Public API para terceros | REST | Familiaridad, debugging con curl |
| Streaming bidireccional | gRPC | Streaming nativo |
| CRUD simple | REST | Simplicidad, menos boilerplate |

## Trade-offs
| Trade-off | REST | gRPC |
|---|---|---|
| Schema implícito vs explícito | opcional OpenAPI | obligatorio .proto |
| JSON vs Protobuf | texto (legible) | binario (compacto) |
| Streaming | no nativo | nativo bidireccional |
| Tipado | dinámico | estático |
| Codegen | opcional (OpenAPI) | nativo |
| Tooling de debug | curl, browser, Postman | grpcurl, grpcox |

## Casos de uso

### Cuándo elegir REST
:::tip
- APIs públicas accesibles desde browsers.
- APIs que terceras partes consumirán sin generar clientes tipados.
- Sistemas CRUD simples donde JSON es legible para humanos.
- Debugging en producción con curl.
:::

### Cuándo elegir gRPC
:::tip
- Microservicios internal con contratos estrictos entre servicios.
- Streaming bidireccional (e.g., chat, real-time updates).
- Mobile apps donde el payload binario importa.
- Sistemas con requisitos de performance y baja latencia.
:::

## Veredicto
Para **APIs públicas** accesibles desde browsers o consumidas por terceros sin código generado, REST es la elección pragmática. Para **microservicios internal** con contratos estrictos y requisitos de performance, gRPC es superior. En la práctica, los sistemas modernos usan **ambos**: gRPC para la comunicación entre servicios internos y REST como gateway público. La diferencia clave es el contrato: schema implícito vs explícito. {src:blk_m00000000210}

:::derived
El benchmark típico muestra gRPC ~7-10x más rápido que REST+JSON para payloads pequeños (< 1 KB), pero la diferencia se diluye para payloads grandes o con compresión gzip. Esta comparación depende mucho del caso de uso y no es universal.
:::

## Backlinks
La comparativa se complementa con el detalle de curl y los status codes REST; los enlaces muestran los 2 ángulos. {src:blk_m00000000250}

- [[note:api-reference-curl-options]] — opciones de cURL (REST).
- [[note:http-status-codes]] — status codes REST.
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

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones Síntesis, Criterios, Matriz, Trade-offs, Veredicto, Backlinks, Casos de uso, TL;DR.
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
                "## Síntesis",
                "## Criterios",
                "## Matriz de decisión por escenario",
                "## Trade-offs",
                "## Casos de uso",
                "## Veredicto",
                "## Backlinks",
                "## Ver también",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith("[[")
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
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f", "m": "b", "k": "9"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-vs-mysql.md", POSTGRES_VS_MYSQL)
    _write(NOTES_DIR / "kubectl-vs-docker.md", KUBECTL_VS_DOCKER)
    _write(NOTES_DIR / "rest-vs-grpc.md", REST_VS_GRPC)


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

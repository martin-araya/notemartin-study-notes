#!/usr/bin/env python3
"""Generador del catálogo JSON de F95 — `analogies`.

Escribe `evals/analogies-sample/catalog.json` con las 18 entradas del banco
de F95. Sirve como fuente única de verdad para los criterios algorítmicos
del eval (evita que el eval dependa de regex sobre prosa markdown).

Estructura de cada entrada:
    {
        "id": "E1",
        "name": "Cárcel / sandbox",
        "pattern_primary": "P1",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "cárcel",
        "marca": ":::derived",
        "rotura": "El preso no puede escapar físicamente; ...",
        "rotura_concreta": true,   # no contiene palabras prohibidas
        "reused_in": ["Docker --pid=host", "Kubernetes pod sandbox"]
    }

Uso:
    python3 evals/analogies-sample/build_catalog.py            # genera si no existe
    python3 evals/analogies-sample/build_catalog.py --force    # regenera siempre

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "catalog.json"

PROHIBITED_ROTURA = re.compile(
    r"\b(?:casi|m[aá]s o menos|no del todo|parcialmente|en general|aproximadamente)\b",
    re.IGNORECASE,
)


CATALOG: list[dict] = [
    {
        "id": "E1",
        "name": "Cárcel / sandbox",
        "pattern_primary": "P1",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "cárcel",
        "marca": ":::derived",
        "rotura": "El preso no puede escapar físicamente; un proceso puede hacer path traversal o exploit de kernel para salir del namespace.",
        "reused_in": ["Docker --pid=host", "Kubernetes pod sandbox"],
    },
    {
        "id": "E2",
        "name": "Caja fuerte de banco",
        "pattern_primary": "P1",
        "pattern_secondary": [],
        "target_domain": "secretos",
        "source_domain": "caja fuerte",
        "marca": ":::external",
        "rotura": "El banco tiene una llave maestra física; en Vault la llave maestra es revocable y rotada.",
        "reused_in": ["HashiCorp Vault", "AWS KMS"],
    },
    {
        "id": "E3",
        "name": "Contrato legal",
        "pattern_primary": "P2",
        "pattern_secondary": [],
        "target_domain": "apis",
        "source_domain": "contrato notarial",
        "marca": ":::external",
        "rotura": "Un contrato se firma una vez; un schema se versiona (v1, v2) y cada cliente negocia la versión por conexión.",
        "reused_in": ["gRPC docs", "Avro spec"],
    },
    {
        "id": "E4",
        "name": "Formulario de admisión",
        "pattern_primary": "P2",
        "pattern_secondary": [],
        "target_domain": "apis",
        "source_domain": "formulario de hospital",
        "marca": ":::external",
        "rotura": "Un formulario se entrega una vez; HTTP puede reintentar (idempotencia, retries) y los headers se renegocian por sesión.",
        "reused_in": ["RFC 9110", "OpenAPI spec"],
    },
    {
        "id": "E5",
        "name": "Grifo de agua",
        "pattern_primary": "P3",
        "pattern_secondary": [],
        "target_domain": "memoria",
        "source_domain": "grifo con caudal",
        "marca": ":::external",
        "rotura": "El grifo tiene caudal físico constante; la RAM es compartida por todos los procesos y se libera por GC, no por gravedad.",
        "reused_in": ["PostgreSQL shared_buffers tuning"],
    },
    {
        "id": "E6",
        "name": "Boletos de cine",
        "pattern_primary": "P3",
        "pattern_secondary": [],
        "target_domain": "redes",
        "source_domain": "boletos numerados",
        "marca": ":::external",
        "rotura": "Un boleto se destruye al usarse; un puerto TCP entra en TIME_WAIT y se reutiliza tras minutos.",
        "reused_in": ["troubleshooting ps aux | grep socket"],
    },
    {
        "id": "E7",
        "name": "Semáforo urbano",
        "pattern_primary": "P4",
        "pattern_secondary": [],
        "target_domain": "redes",
        "source_domain": "semáforo de tráfico",
        "marca": ":::derived",
        "rotura": "Un semáforo tiene ciclos fijos; un token bucket tiene refill rate configurable y se adapta al tráfico.",
        "reused_in": ["AWS API Gateway throttling", "NGINX limit_req"],
    },
    {
        "id": "E8",
        "name": "Cola de supermercado",
        "pattern_primary": "P4",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "cola de caja",
        "marca": ":::external",
        "rotura": "En el supermercado ves a la gente; en una queue TCP no ves a los paquetes hasta que llegan al head.",
        "reused_in": ["Kafka docs", "SQS docs"],
    },
    {
        "id": "E9",
        "name": "Libro contable",
        "pattern_primary": "P5",
        "pattern_secondary": [],
        "target_domain": "bases de datos",
        "source_domain": "libro contable",
        "marca": ":::external",
        "rotura": "Un libro contable se cierra al final del ejercicio; el WAL se trunca tras el checkpoint.",
        "reused_in": ["PostgreSQL §19.5", "MySQL binlog"],
    },
    {
        "id": "E10",
        "name": "Bitácora de barco",
        "pattern_primary": "P5",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "bitácora de barco",
        "marca": ":::external",
        "rotura": "La bitácora es narrativa y cualitativa; el journal es estructurado (PRIORITY, MESSAGE_ID, SYSLOG_IDENTIFIER).",
        "reused_in": ["systemd-journald docs"],
    },
    {
        "id": "E11",
        "name": "Edificio de pisos",
        "pattern_primary": "P6",
        "pattern_secondary": [],
        "target_domain": "redes",
        "source_domain": "edificio de oficinas",
        "marca": ":::external",
        "rotura": "Los pisos tienen grosor constante; las capas digitales son difusas (cross-cutting concerns como auth cruzan todas).",
        "reused_in": ["RFC 1122", "教材 de redes"],
    },
    {
        "id": "E12",
        "name": "Interruptor de luz",
        "pattern_primary": "P7",
        "pattern_secondary": [],
        "target_domain": "apis",
        "source_domain": "interruptor on/off",
        "marca": ":::external",
        "rotura": "El interruptor solo tiene 2 estados; una operación idempotente puede tener infinitos estados finales.",
        "reused_in": ["RFC 9110 §9.2.2", "Stripe API idempotency"],
    },
    {
        "id": "E13",
        "name": "Cocina con 2 cocineros",
        "pattern_primary": "P8",
        "pattern_secondary": [],
        "target_domain": "bases de datos",
        "source_domain": "cocina con 2 cocineros",
        "marca": ":::derived",
        "rotura": "Los cocineros se ven físicamente; los nodos DB no se ven hasta la replicación y la latencia de red rompe la sincronía.",
        "reused_in": ["CAP theorem", "Spanner docs"],
    },
    {
        "id": "E14",
        "name": "Barrendero nocturno",
        "pattern_primary": "P9",
        "pattern_secondary": [],
        "target_domain": "bases de datos",
        "source_domain": "barrendero nocturno",
        "marca": ":::external",
        "rotura": "El barrendero recoge todo; el GC solo lo inalcanzable (sin referencias).",
        "reused_in": ["PostgreSQL §19.10 routine vacuuming"],
    },
    {
        "id": "E15",
        "name": "Cuaderno de notas junto al libro",
        "pattern_primary": "P10",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "cuaderno de notas",
        "marca": ":::external",
        "rotura": "El cuaderno es tuyo y no se invalida; el cache expira por TTL o por eviction (LRU/LFU).",
        "reused_in": ["Redis docs", "Squid docs"],
    },
    {
        "id": "E16",
        "name": "Baño con llave",
        "pattern_primary": "P11",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "baño con cerradura",
        "marca": ":::external",
        "rotura": "El baño tiene 1 capacidad fija; un mutex protege una sección crítica arbitrariamente larga y puede haber deadlock.",
        "reused_in": ["pthread docs", "Java synchronized"],
    },
    {
        "id": "E17",
        "name": "Recepcionista de hotel",
        "pattern_primary": "P12",
        "pattern_secondary": [],
        "target_domain": "sistemas",
        "source_domain": "recepcionista de hotel",
        "marca": ":::external",
        "rotura": "La recepcionista conoce cada habitación; un load balancer solo conoce los backends registrados.",
        "reused_in": ["NGINX", "HAProxy", "Envoy docs"],
    },
    {
        "id": "E18",
        "name": "Tren con vagones",
        "pattern_primary": "P4",
        "pattern_secondary": ["P6"],
        "target_domain": "redes",
        "source_domain": "tren con vagones",
        "marca": ":::external",
        "rotura": "Los vagones van enganchados al tren; los paquetes IP se enrutan independientemente y pueden llegar por caminos distintos.",
        "reused_in": ["RFC 791", "教材 de redes"],
    },
]


def _annotate(entry: dict) -> dict:
    """Marca rotura_concreta según la regla universal §4."""
    out = dict(entry)
    out["rotura_concreta"] = not bool(PROHIBITED_ROTURA.search(entry["rotura"]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="regenera aunque exista")
    args = parser.parse_args()

    if OUTPUT.exists() and not args.force:
        print(f"[skip] {OUTPUT.name} (ya existe; use --force para regenerar)")
        return 0

    catalog = [_annotate(e) for e in CATALOG]
    OUTPUT.write_text(
        json.dumps({"version": "1.0.0", "entries": catalog}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[create] {OUTPUT.name} ({len(catalog)} entradas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

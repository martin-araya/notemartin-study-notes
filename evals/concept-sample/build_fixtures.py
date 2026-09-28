#!/usr/bin/env python3
"""Generador de fixtures para la Fase 78 — `concept`.

Produce 4 notas (2 bases + 2 variantes con `## Práctica`) y 2 perfiles que
documentan el contrato `profile.notes.types.concept`.

Las notas base NO tienen sección `## Práctica` (caso `include_practice: false`
o perfil ausente → default `false`). Las variantes SÍ la tienen (caso
`include_practice: true`).

Las 4 notas siguen el patrón de `references/05-note-types/concept.md`:
13 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/concept-sample/build_fixtures.py            # genera siempre
    python3 evals/concept-sample/build_fixtures.py --check    # regenera y verifica
    python3 evals/concept-sample/build_fixtures.py --regen    # alias de siempre

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
NOTES_DIR = EVAL_DIR / "notes"
PROFILES_DIR = EVAL_DIR / "profiles"
DENSITY_CHECK = (
    EVAL_DIR.parent.parent
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "validate"
    / "density_check.py"
)


# ---------------------------------------------------------------------------
# Notas base (sin `## Práctica`)
# ---------------------------------------------------------------------------

NOTE_DB_MVCC = """---
title: "MVCC (control de concurrencia multiversión)"
note-type: concept
status: draft
summary: "MVCC permite lecturas y escrituras concurrentes manteniendo un snapshot por transacción sin bloquear filas en disco."
tags: [type/concept, domain/databases, domain/postgres]
source: "PostgreSQL 16 — Chapter 13: Concurrency Control"
source-type: docs
source-anchor: "13.1 Introduction"
retrieved: 2026-09-27
product: "PostgreSQL"
product-version: "16"
related: "[[note:two-phase-locking]], [[note:serializable-isolation]], [[note:wal]]"
---

# MVCC (control de concurrencia multiversión)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | MVCC permite lecturas y escrituras concurrentes manteniendo un snapshot por transacción sin bloquear filas en disco. |
| **Procedencia** | PostgreSQL 16 — Chapter 13: Concurrency Control (docs) §13.1 Introduction · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
MVCC hace que cada transacción vea un snapshot consistente de la base de datos al iniciarse, sin leer los cambios que otras transacciones todavía no han confirmado. {src:blk_a91f8e02c1d3}

{layer:l2}

## Problema
Sin un mecanismo de versiones, una lectura larga bloquearía todas las escrituras sobre las filas que toca, y una escritura bloquearía todas las lecturas — degradación severa del throughput. {src:blk_b12c44f0a8e7}

## Intuición
Imagina una pizarra compartida: cada vez que alguien quiere cambiar algo, no borra la versión anterior, sino que dibuja la nueva encima. Quien lee, ve siempre la última versión **confirmada por completo** en el momento en que empezó a leer. {src:blk_1d3e8a92f7c4}

## Analogía
Como un libro con ediciones numeradas: la edición 1 no se destruye cuando aparece la edición 2. Un lector que compró la edición 1 sigue leyéndola aunque la edición 2 ya esté en las tiendas; las dos ediciones coexisten hasta que la vieja se descataloga. {src:blk_c7d3f1a025b9}

## Definición formal
Cada fila insertada recibe un `xmin` (id de transacción que la creó) y un `xmax` (id de transacción que la borró o reemplazó). Una transacción `T` ve una fila si `xmin` está confirmado y anterior a `T`, y `xmax` o no existe o es posterior a `T`. {src:blk_d84ae51cfb22}

| Variable | Significado |
|---|---|
| `xmin` | id de la transacción que insertó la fila |
| `xmax` | id de la transacción que la eliminó (NULL si vive) |
| `xid` | id de la transacción actual |

## Mecanismo
PostgreSQL implementa MVCC con `HeapTuple` visible/no visible por `xmin`/`xmax` en cada fila. Un `UPDATE` no modifica la fila: inserta una nueva versión y marca la anterior como borrada. Un `VACUUM` recicla las versiones sin referencias. {src:blk_e95bf62da133}

```mermaid
sequenceDiagram
    T1->>DB: BEGIN
    T1->>DB: UPDATE row SET v=2
    T2->>DB: SELECT v
    Note over T2: ve v=1 (snapshot pre-T1)
    T1->>DB: COMMIT
    T2->>DB: SELECT v
    Note over T2: ve v=2 (nuevo snapshot)
```

## Comparaciones
MVCC contrasta con el bloqueo pesimista tradicional en el coste de la concurrencia. {src:blk_45d7e219bf03}

| Aspecto | MVCC (PostgreSQL) | 2PL pesimista (MySQL InnoDB antiguo) |
|---|---|---|
| Lecturas concurrentes | sin bloqueos | comparten bloqueo compartido |
| Escrituras | nueva versión por fila | in-place + locks exclusivos |
| Latencia de lectura | uniforme, predecible | sensible a escrituras activas |

## Resumen
Cada fila lleva `xmin` y `xmax`; el snapshot decide visibilidad. `UPDATE` inserta versión, no modifica in-place; `VACUUM` reclama versiones huérfanas. {src:blk_46e8f32ac014}

- Cada fila lleva `xmin` y `xmax`; el snapshot decide visibilidad. {src:blk_f1c7a83b29d4}
- `UPDATE` inserta versión, no modifica in-place. {src:blk_f23a4b8e15c0}
- `VACUUM` reclama versiones huérfanas. {src:blk_b9d2e741fa6c}

## Trampas
:::warning
**Long-running transaction bloquea VACUUM.** Si una transacción `T` abierta ve versiones muertas, `VACUUM` no las puede reclamar y la tabla crece sin parar (`table bloat`). Solución: monitorizar `pg_stat_activity` y cancelar transacciones idle-in-transaction. {src:blk_8c5f2a917e44}
:::

:::warning
**`xid` wraparound.** PostgreSQL usa un contador de 32 bits para `xid`; tras ~4 mil millones de transacciones, los `xmin` antiguos parecen "del futuro". Solución: `VACUUM FREEZE` periódico; PostgreSQL 16 activa autovacuum agresiva cuando se acerca el límite. {src:blk_9d6e3b028f55}
:::

## Cuándo NO usarlo
MVCC no encaja cuando la consistencia o el espacio en disco son la prioridad absoluta; en esos casos, otros enfoques rinden mejor. {src:blk_47f9034bd125}

- Si necesitas consistencia fuerte entre réplicas síncronas → usa `[[note:synchronous-replication]]`. {src:blk_3a8c5f2d9711}
- Si necesitas evitar `table bloat` sin `VACUUM` → considera `[[note:append-only-log]]`. {src:blk_4f7b91c2e8d6}

## Límites y alternativas
MVCC asume que el coste de mantener versiones y ejecutar `VACUUM` es aceptable. Cuando no lo es, hay alternativas con trade-offs distintos. {src:blk_480a145ce236}

| Alternativa | Cubre | Trade-off |
|---|---|---|
| `[[note:two-phase-locking]]` | consistencia estricta | menos concurrencia |
| `[[note:append-only-log]]` | sin bloat | lectura más cara (compactación) |
| `[[note:optimistic-locking]]` | escrituras raras | rollback frecuente bajo contención |

## Relacionados
MVCC se complementa con el journal de transacciones y se opone al bloqueo pesimista; ambos extremos viven en el catálogo. {src:blk_491b256df347}

- `[[note:two-phase-locking]]` — el enfoque pesimista opuesto. {src:blk_5e3a8b1d7c4f}
- `[[note:wal]]` — el journal donde MVCC registra los `xid` confirmados. {src:blk_6d9c4a2f8e13}

## Backlinks
MVCC es referenciado desde notas que profundizan en niveles de aislamiento y mantenimiento. {src:blk_4a2c367e0458}

- [[note:isolation-levels]] {src:blk_71fa5c39b0e2}
- [[note:vacuum-and-autovacuum]] {src:blk_82a6b41cf1d5}

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(related, this.file.link)
SORT file.ctime DESC
```
"""


NOTE_NET_3WHS = """---
title: "Three-Way Handshake (establecimiento de conexión TCP)"
note-type: concept
status: draft
summary: "El 3WHS de TCP sincroniza ISN de cliente y servidor en 3 pasos antes de transmitir datos, garantizando que ambos extremos están listos."
tags: [type/concept, domain/networking, domain/tcp]
source: "RFC 9293 — Transmission Control Protocol"
source-type: rfc
source-anchor: "3.5 Establishing a Connection"
retrieved: 2026-09-27
product: "TCP/IP"
product-version: "RFC 9293"
related: "[[note:tcp-four-way-teardown]], [[note:tcp-fast-open]], [[note:tcp-retransmission]]"
---

# Three-Way Handshake (establecimiento de conexión TCP)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | El 3WHS de TCP sincroniza ISN de cliente y servidor en 3 pasos antes de transmitir datos, garantizando que ambos extremos están listos. |
| **Procedencia** | RFC 9293 — Transmission Control Protocol (rfc) §3.5 Establishing a Connection · recuperado 2026-09-27 |
| **Versión** | TCP/IP RFC 9293 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
TCP usa 3 segmentos (SYN, SYN-ACK, ACK) para sincronizar los números de secuencia iniciales (ISN) de cliente y servidor antes de cualquier dato. {src:blk_a01b9c7f3e22}

{layer:l2}

## Problema
Dos extremos que no se conocen deben acordar parámetros (ISN, ventana, MSS) sin saber si el otro está vivo ni qué estado tenía antes. {src:blk_b42c8d1eaa91}

## Intuición
Como una llamada telefónica: quien llama marca, el receptor descuelga y dice "diga", y quien llama responde "diga, soy yo" antes de empezar la conversación real. {src:blk_2e8b4f61d3a7}

## Analogía
Como un apretón de manos en tres tiempos: A extiende la mano, B la estrecha, A confirma con un apretón final. Sin el tercer movimiento, ninguno de los dos sabe si el otro está realmente listo. {src:blk_c7f3e0a51bcd}

## Definición formal
Tres segmentos: cliente envía SYN con ISN_C; servidor responde SYN-ACK con ISN_S y `ack = ISN_C + 1`; cliente envía ACK con `seq = ISN_C + 1` y `ack = ISN_S + 1`. Tras el ACK, ambos extremos entran en `ESTABLISHED`. {src:blk_d88a1f62c4e7}

| Campo | Significado |
|---|---|
| ISN_C | número de secuencia inicial del cliente |
| ISN_S | número de secuencia inicial del servidor |
| SYN | flag de sincronización |
| ACK | flag de acknowledgement |

## Mecanismo
Cada lado genera un ISN pseudoaleatorio (mitigación de spoofing). El servidor aloca recursos (TCB, buffers) al enviar SYN-ACK; si el ACK del cliente no llega, agota el timeout y libera. La retransmisión del SYN usa backoff exponencial. {src:blk_e95cf12a08b3}

El handshake aporta además protección frente a segmentos duplicados de conexiones anteriores: cada SYN lleva un ISN nuevo, y los segmentos con ISN antiguo son descartados por el receptor. {src:blk_6f7a8b9c0d1e}

```mermaid
sequenceDiagram
    C->>S: SYN (ISN_C)
    S->>C: SYN-ACK (ISN_S, ack=ISN_C+1)
    C->>S: ACK (seq=ISN_C+1, ack=ISN_S+1)
    Note over C,S: ESTABLISHED
```

## Comparaciones
TCP 3WHS contrasta con UDP (sin handshake) en coste y semántica. {src:blk_55e8f32ac014}

| Aspecto | TCP 3WHS | UDP (sin handshake) |
|---|---|---|
| Acuerdo previo | ISN + ventana | ninguno |
| Coste en RTT | 1 RTT extra antes de datos | 0 |
| Resistencia a spoofing | alta (ISN aleatorio) | baja |

## Resumen
3 segmentos: SYN, SYN-ACK, ACK. Cada extremo fija su ISN antes de transmitir datos; el servidor aloca recursos desde el SYN-ACK, no espera al ACK. {src:blk_56f9034bd125}

- 3 segmentos: SYN, SYN-ACK, ACK. {src:blk_f1c8a37b29d4}
- Cada extremo fija su ISN antes de transmitir datos. {src:blk_e2b4c91d8f3a}
- El servidor aloca recursos desde el SYN-ACK, no espera al ACK. {src:blk_c5a7e2369b81}

## Trampas
:::warning
**SYN flood.** Un atacante envía muchos SYN sin completar el ACK, agotando los buffers del servidor. Solución: SYN cookies (codifican ISN+estado en el ISN_S). {src:blk_7b1e4c92d3a8}
:::

:::warning
**Half-open connections.** Si un extremo se reinicia tras enviar SYN-ACK, el otro queda esperando ACK indefinidamente. Solución: TCP keepalive (RFC 9293 §3.8.4) o timeouts de aplicación. {src:blk_8c2f5da3e4b9}
:::

## Cuándo NO usarlo
El handshake de 3 pasos añade 1 RTT antes de enviar datos; cuando la latencia es crítica o el flujo confiable no es necesario, hay alternativas. {src:blk_570a145ce236}

- Latencia crítica < 1 RTT → usa `[[note:tcp-fast-open]]` (datos en el SYN). {src:blk_94d3e8a1c2f5}
- Sin necesidad de flujo confiable → usa `[[note:udp]]`. {src:blk_a1f5c72b9e3d}

## Límites y alternativas
El 3WHS añade 1 RTT antes de cualquier dato; cuando ese coste es prohibitivo, hay variantes que lo eliminan o lo absorben en el primer paquete. {src:blk_581b256df347}

| Alternativa | Cubre | Trade-off |
|---|---|---|
| `[[note:tcp-fast-open]]` | datos en el SYN | requiere cookie y soporte en el server |
| `[[note:quic]]` | handshake 1-RTT | nueva pila, no es TCP |
| `[[note:sctp]]` | multi-homing | despliegue muy inferior |

## Relacionados
El 3WHS es la mitad del ciclo de vida de una conexión TCP; su cierre y su recuperación ante pérdida son los conceptos vecinos naturales. {src:blk_592c367e0458}

- `[[note:tcp-four-way-teardown]]` — cierre en 4 segmentos. {src:blk_b7e2c814fa05}
- `[[note:tcp-retransmission]]` — recuperación tras pérdida de ACK. {src:blk_c8f3d9250b16}

## Backlinks
El 3WHS aparece referenciado en la nota que recorre los estados completos de una conexión TCP. {src:blk_5a3d478f1569}

- [[note:tcp-state-machine]] {src:blk_d4a91e6f3c82}

## Queries
```dataview
LIST
FROM "notes"
WHERE contains(related, this.file.link)
SORT file.ctime DESC
```
"""


# ---------------------------------------------------------------------------
# Variantes con `## Práctica` (perfil `include_practice: true`)
# ---------------------------------------------------------------------------

PRACTICE_DB = """

## Práctica

:::question
**¿Qué garantiza el snapshot de una transacción en MVCC?** {src:blk_0000a1b2c3d4}

Que la transacción ve la base de datos en un estado consistente al momento de su primer `SELECT` o `BEGIN`, independientemente de las escrituras concurrentes que otras transacciones hagan después. {src:blk_0000a2c3d4e5}
:::

:::question
**¿Por qué `VACUUM` es esencial para MVCC?** {src:blk_0000a3d4e5f6}

Porque `UPDATE` y `DELETE` no eliminan físicamente las filas viejas, solo marcan `xmax`. Sin `VACUUM`, la tabla crece sin parar y se reduce el rendimiento de las consultas. {src:blk_0000a4e5f607}
:::

:::question
**¿Cómo afecta `xid` wraparound al comportamiento de MVCC?** {src:blk_0000a5f60718}

PostgreSQL usa un contador de 32 bits; al llegar cerca del límite, las transacciones antiguas se ven como "del futuro" y sus filas se vuelven invisibles, perdiendo datos. Solución: `VACUUM FREEZE` periódico que marca las filas como congeladas. {src:blk_0000a6071829}
:::
"""

PRACTICE_NET = """

## Práctica

:::question
**¿Por qué son necesarios 3 segmentos y no 2 en el handshake TCP?** {src:blk_0000b1c2d3e4}

Para que ambos extremos sincronicen ISN y confirmen la recepción. Si fueran 2, un solo extremo confirmaría sin saber si el otro recibió su confirmación — no habría acuerdo mutuo de estado. {src:blk_0000b2c3d4e5}
:::

:::question
**¿Qué ataque mitiga el ISN pseudoaleatorio?** {src:blk_0000b3d4e5f6}

El ataque de predicción de secuencia: si el ISN fuera secuencial, un atacante podría inyectar paquetes asumiendo el siguiente número. Con ISN aleatorio, la suposición es inviable. {src:blk_0000b4e5f607}
:::

:::question
**¿Cuándo libera recursos el servidor tras enviar SYN-ACK?** {src:blk_0000b5f60718}

Tras el `ACK` del cliente. Si el `ACK` no llega, el servidor agota el timeout (típicamente 75 s con backoff) y libera el TCB. Esto lo hace vulnerable a SYN flood. {src:blk_0000b6071829}
:::
"""


# ---------------------------------------------------------------------------
# Perfiles (documentan el contrato; no se parsean como validación dura)
# ---------------------------------------------------------------------------

PROFILE_PRACTICE = """# Perfil de prueba F78: `include_practice: true`
# Activa la sección opcional `## Práctica` en notas `concept`.
# Este archivo documenta el contrato; el agente consumidor lo lee y aplica
# `references/05-note-types/concept.md` §5.
schema_version: "1.0.0"

notes:
  types:
    concept:
      include_practice: true
      include_limits_alternatives: true
      include_comparisons: true
      min_comparisons: 2
      min_traps: 1
"""

PROFILE_NO_PRACTICE = """# Perfil de prueba F78: `include_practice: false` (default)
# Omite la sección `## Práctica` en notas `concept`.
schema_version: "1.0.0"

notes:
  types:
    concept:
      include_practice: false
      include_limits_alternatives: true
      include_comparisons: true
      min_comparisons: 2
      min_traps: 1
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(notes_only: bool = False) -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    # Notas base sin Práctica.
    _write(NOTES_DIR / "db-mvcc.md", NOTE_DB_MVCC)
    _write(NOTES_DIR / "net-three-way-handshake.md", NOTE_NET_3WHS)

    # Variantes con Práctica (insertada antes del cierre).
    _write(
        NOTES_DIR / "db-mvcc-practice.md",
        NOTE_DB_MVCC.replace("\n## Backlinks\n", f"{PRACTICE_DB}\n## Backlinks\n"),
    )
    _write(
        NOTES_DIR / "net-three-way-handshake-practice.md",
        NOTE_NET_3WHS.replace("\n## Backlinks\n", f"{PRACTICE_NET}\n## Backlinks\n"),
    )

    if not notes_only:
        _write(PROFILES_DIR / "profile-practice.yaml", PROFILE_PRACTICE)
        _write(PROFILES_DIR / "profile-no-practice.yaml", PROFILE_NO_PRACTICE)


def check_density() -> int:
    """Re-ejecuta `density_check.py --strict` sobre las 4 notas."""
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0

    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [
            sys.executable,
            str(DENSITY_CHECK),
            "--note", str(note),
            "--strict",
        ]
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
    parser.add_argument("--check", action="store_true", help="Genera + verifica con density_check.py")
    parser.add_argument("--regen", action="store_true", help="Alias de generación (sobrescribe fixtures)")
    parser.add_argument("--notes-only", action="store_true", help="No genera perfiles, solo notas")
    args = parser.parse_args()

    build(notes_only=args.notes_only)
    print(f"Generadas 4 notas en {NOTES_DIR}")
    if not args.notes_only:
        print(f"Generados 2 perfiles en {PROFILES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generador de fixtures para la Fase 102 — `self-evaluation`.

Produce 8 notas NoteMark en `evals/self-evaluation-sample/notes/`:

  - `self-eval-good-1-concept.md`                — nota `concept` con
      recuerdo + aplicación + decisión, 3 preguntas por H3, todas con
      `{src:blk_xxxx}` o `[[note:id#§N]]`.
  - `self-eval-good-2-procedure.md`              — nota `procedure` con
      aplicación + predicción, fundamento mixto.
  - `self-eval-good-3-error-troubleshooting.md`  — nota `error-troubleshooting`
      con diagnóstico + decisión, mensaje literal preservado.
  - `self-eval-good-4-glossary-term.md`          — nota `glossary-term`
      con solo recuerdo (referencia pura), 3 preguntas.
  - `self-eval-bad-1-no-fundamento.md`           — colapsable sin línea
      `> Fundamento: …` (falla V3 / AP14).
  - `self-eval-bad-2-copiada.md`                 — respuesta es copia
      literal (falla V4 / AP13, detectable por tokens ≤ 2).
  - `self-eval-bad-3-recuerdo-en-referencia.md`  — glossary-term con
      pregunta de aplicación (falla V2 / AP15).
  - `self-eval-bad-4-index-moc-con-seccion.md`   — index-moc con
      sección ## Autoevaluación (falla V1 / V6).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/self-evaluation-sample/build_fixtures.py            # genera si no existe
    python3 evals/self-evaluation-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _frontmatter(
    title: str,
    note_type: str,
    summary: str,
    *,
    status: str = "published",
    self_eval_types: str = "",
    extra: str = "",
) -> str:
    fm = f"""---
title: "{title}"
note-type: {note_type}
status: {status}
summary: "{summary}"
reading-time-minutes: 3
language: es
tags: [type/{note_type}, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
"""
    if self_eval_types:
        fm += f"self-evaluation-types: {self_eval_types}\n"
    if extra:
        fm += extra
    return fm.rstrip() + "\n---\n"


def _good_concept() -> str:
    return (
        _frontmatter(
            "Aislamiento de transacciones en MVCC",
            "concept",
            "MVCC da a cada transacción un snapshot al inicio; las escrituras concurrentes no son visibles hasta el commit.",
            self_eval_types="[recuerdo, aplicacion, decision]",
        )
        + """

# Aislamiento de transacciones en MVCC

## TL;DR

MVCC da a cada transacción un snapshot al inicio. Cada fila lleva
dos marcas (`xmin`, `xmax`). Los lectores ven filas cuyo rango cae
dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores bloqueaban un `SELECT` largo con todas las
inserciones. Un reporte diario podía detener la carga OLTP durante
minutos. {src:blk_a91f8e02c1d3}

## Definición formal

Una transacción `T` con snapshot `S(T)` ve la fila `R` si `xmin_R < S(T)`
y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Resumen

MVCC garantiza que cada transacción observa un snapshot estable y que
las marcas de versión por fila permiten reciclar espacio con `VACUUM`
sin bloquear lectores. {src:blk_a91f8e02c1d3}

## Autoevaluación

Tipos asignados a `concept`: recuerdo, aplicación, decisión.

### Recuerdo

:::collapsible{default_open=false}
¿Qué garantiza el aislamiento snapshot en MVCC?
Cada transacción observa un estado del database consistente con el momento de su inicio; las escrituras concurrentes no son visibles hasta el commit.
> Fundamento: {src:blk_a91f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuál es el campo del header de heap tuple que marca la transacción creadora?
El campo `xmin` registra la transacción que insertó la fila; mientras la fila no se modifique, este valor permanece estable.
> Fundamento: [[note:heap-tuple-layout#header]]
:::

:::collapsible{default_open=false}
¿Qué operación recicla las versiones con `xmax < oldest_active_snapshot`?
La operación `VACUUM` marca como reutilizables los espacios ocupados por tuplas cuya versión ya no es visible para ninguna transacción activa.
> Fundamento: [[note:vacuum#recycle]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos transacciones T1 y T2 que arrancan antes de que T1 haga commit, ¿qué versión de la fila ve T2 al hacer SELECT?
La versión previa al commit de T1 (T2 sigue en su snapshot original); el commit posterior de T1 no es visible para T2.
> Fundamento: {src:blk_a91f8e02c1d3}
:::

:::collapsible{default_open=false}
Con una tabla donde el 80 % de las filas son versiones muertas, ¿qué operación recomiendas primero para liberar espacio?
Ejecutar `VACUUM (VERBOSE, ANALYZE)` para reciclar versiones y refrescar estadísticas.
> Fundamento: [[note:vacuum#recycle]]
:::

:::collapsible{default_open=false}
Si tu aplicación hace lecturas largas sobre una tabla con mucha escritura, ¿qué nivel de aislamiento evita lecturas no repetibles?
`REPEATABLE READ`: garantiza snapshot estable durante toda la transacción.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

### Decisión

:::collapsible{default_open=false}
Entre `READ COMMITTED` y `REPEATABLE READ`, ¿cuál elegirías para un reporte agregado que no puede mostrar lecturas no repetibles?
`REPEATABLE READ`: garantiza snapshot estable durante toda la transacción.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

:::collapsible{default_open=false}
¿Cuándo NO usarías MVCC y preferirías un modelo de locking pesimista?
En sistemas embebidos con memoria muy limitada donde el coste de mantener múltiples versiones por fila no compensa.
> Fundamento: [[note:storage-tradeoffs#mvcc-vs-locking]]
:::

:::collapsible{default_open=false}
Para una carga 100 % OLTP con muchas escrituras y reportes cortos, ¿prefieres MVCC por fila o MVCC por bloque?
MVCC por fila: las escrituras no invalidan lecturas de filas vecinas.
> Fundamento: [[note:storage-tradeoffs#granularity]]
:::
"""
    )


def _good_procedure() -> str:
    return (
        _frontmatter(
            "Backup lógico con pg_dump -Fc",
            "procedure",
            "Procedimiento para respaldar y restaurar una base de datos PostgreSQL con formato custom (-Fc) y pg_restore.",
            self_eval_types="[aplicacion, prediccion]",
        )
        + """

# Backup lógico con pg_dump -Fc

## TL;DR

`pg_dump -Fc` produce un archivo binario comprimido que `pg_restore`
puede aplicar selectivamente. {src:blk_b11f8e02c1d3}

## Procedimiento

### 1. Crear el backup

:::step
Ejecutar `pg_dump -Fc -d <dbname> -f <ruta.backup>`.

El flag `-Fc` selecciona el formato custom (comprimido). El archivo
resultante es binario, no legible por `cat`, y permite restauración
selectiva por tabla o esquema. {src:blk_b11f8e02c1d3}
:::

### 2. Verificar integridad

:::step
Ejecutar `pg_restore -l <ruta.backup>` para listar el contenido sin
restaurar. Confirma que las tablas esperadas están presentes. La salida
es texto plano con cabecera y líneas tipo `<id> <tipo> <nombre>`. {src:blk_b11f8e02c1d3}
:::

### 3. Restaurar

:::step
Ejecutar `pg_restore -d <dbname> <ruta.backup>` desde un objetivo
donde la base de datos destino ya existe. Para una restauración limpia
añade `-c` (drop before create) o `--clean`. {src:blk_b11f8e02c1d3}
:::

## Errores frecuentes

:::warning
`pg_restore` no crea la base de datos destino. Debes crearla primero
con `createdb` o `CREATE DATABASE`.
:::
{src:blk_b11f8e02c1d3}

## Autoevaluación

Tipos asignados a `procedure`: aplicación, predicción.

### Aplicación

:::collapsible{default_open=false}
Dados una base `app_prod` y un archivo `backup_20250929.backup`, ¿qué comando usarías para restaurar solo la tabla `orders`?
`pg_restore -d app_prod --table=orders backup_20250929.backup`.
> Fundamento: {src:blk_b11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con un backup de 50 GB en formato custom, ¿qué flag añadirías para paralelizar la restauración?
`pg_restore -j 8 ...` (donde `8` es el número de workers concurrentes; ajustar a CPUs disponibles).
> Fundamento: [[note:pg-restore-parallelism#workers]]
:::

:::collapsible{default_open=false}
Para verificar que el backup es íntegro antes de borrarlo, ¿qué comando usarías?
`pg_restore -l backup.backup` lista el contenido sin aplicar; complementa con `pg_restore --stats` para estadísticas.
> Fundamento: [[note:pg-restore-verify#listing]]
:::

### Predicción

:::collapsible{default_open=false}
¿Qué ocurre si ejecutas `pg_restore` sobre una base de datos destino que no existe?
Falla con error `FATAL: database "<name>" does not exist`; debes crearla primero.
> Fundamento: {src:blk_b11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué log esperas si el archivo de backup está corrupto en su cabecera?
`pg_restore` emite `pg_restore: error: header is not valid` y termina con exit code 1.
> Fundamento: [[note:pg-restore-errors#corrupt-header]]
:::

:::collapsible{default_open=false}
Si la base destino tiene una tabla `orders` con más filas que el backup, ¿qué sucede al restaurar con `-c` (clean)?
`pg_restore -c` borra (`DROP`) los objetos antes de crearlos; las filas extra de la tabla destino se pierden.
> Fundamento: [[note:pg-restore-flags#clean]]
:::
"""
    )


def _good_error_troubleshooting() -> str:
    return (
        _frontmatter(
            "Connection refused en PostgreSQL",
            "error-troubleshooting",
            "Causa raíz y diagnóstico cuando psql o un cliente devuelve `Connection refused` apuntando al puerto 5432.",
            self_eval_types="[diagnostico, decision]",
        )
        + """

# Connection refused en PostgreSQL

## TL;DR

El mensaje `Connection refused` indica que el puerto 5432 está cerrado
o el servidor no escucha en la interfaz esperada. {src:blk_c11f8e02c1d3}

## Síntomas

```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
```

Este mensaje literal preserva el formato exacto del cliente `psql`
cuando no puede establecer la conexión TCP/IP. {src:blk_c11f8e02c1d3}

## Causa raíz

PostgreSQL no escucha en el puerto; el servicio no está activo, o
`listen_addresses` excluye la interfaz de origen. {src:blk_c11f8e02c1d3}

## Diagnóstico

1. Verificar que el servicio esté activo: `systemctl status postgresql`.
2. Verificar el puerto: `ss -tln | grep 5432`.
3. Revisar `postgresql.conf`: `listen_addresses = '*'` o la IP esperada.
4. Comprobar `pg_hba.conf` para descartar rechazo por autenticación. {src:blk_c11f8e02c1d3}

## Solución

La corrección típica tiene tres pasos. Primero, verificar si el servicio
está activo (`systemctl status postgresql`); si está caído, iniciarlo.
Segundo, ajustar `listen_addresses` en `postgresql.conf` para incluir la
interfaz de origen. Tercero, comprobar `pg_hba.conf` si el cliente llega
al puerto pero la autenticación falla. {src:blk_c11f8e02c1d3}

## Autoevaluación

Tipos asignados a `error-troubleshooting`: diagnóstico, decisión.

### Diagnóstico

:::collapsible{default_open=false}
Si ves `Connection refused` al conectar a `localhost:5432`, ¿cuál es la causa más probable?
El puerto 5432 está cerrado: el servicio PostgreSQL no está activo o `listen_addresses` excluye `localhost`.
> Fundamento: {src:blk_c11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Por qué `psql -h localhost` falla con `Connection refused` pero `psql -h /var/run/postgresql` funciona?
La segunda forma usa el socket Unix del sistema de archivos, que no depende de la pila TCP/IP; la primera requiere que PostgreSQL esté escuchando en la interfaz de red.
> Fundamento: [[note:postgres-listen-addresses#tcp-vs-unix]]
:::

:::collapsible{default_open=false}
Si `ss -tln` no muestra el puerto 5432, ¿qué conclusión sacas?
El servidor no está aceptando conexiones TCP/IP entrantes; puede estar caído, configurado solo para socket local, o filtrado por un firewall upstream que bloquea el puerto.
> Fundamento: [[note:postgres-network-troubleshooting#listen]]
:::

### Decisión

:::collapsible{default_open=false}
Entre reiniciar el servicio y corregir `postgresql.conf`, ¿cuál haces primero si el servicio está caído?
Reiniciar el servicio primero (recupera la conexión); la corrección de `postgresql.conf` la haces en una ventana de mantenimiento.
> Fundamento: [[note:postgres-incident-response#restart-vs-config]]
:::

:::collapsible{default_open=false}
Si la aplicación se conecta vía TCP/IP y `listen_addresses = 'localhost'`, ¿prefieres ampliar a `'*'` o configurar un proxy?
Configurar un proxy (PgBouncer) con TLS y ACL; evita exponer el puerto a toda la red.
> Fundamento: [[note:postgres-security#proxy-vs-bind]]
:::

:::collapsible{default_open=false}
Cuando el `Connection refused` es intermitente y coincide con despliegues, ¿qué revisas primero?
Los logs de systemd y el journal del kernel para detectar OOM kills del proceso postgres durante picos de memoria.
> Fundamento: [[note:postgres-incident-response#oom]]
:::
"""
    )


def _good_glossary_term() -> str:
    return (
        _frontmatter(
            "Snapshot (MVCC)",
            "glossary-term",
            "Vista consistente del estado del database al inicio de una transacción.",
            self_eval_types="[recuerdo]",
        )
        + """

# Snapshot (MVCC)

Vista del database consistente al inicio de una transacción T,
determinada por el conjunto de transacciones activas en ese momento. {src:blk_d11f8e02c1d3}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 docs · concurrency control |
| **Versión** | PostgreSQL 16.3 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `13.1.2` |

## Autoevaluación

Tipos asignados a `glossary-term` (referencia pura, solo recuerdo).

### Recuerdo

:::collapsible{default_open=false}
¿Qué es un snapshot en MVCC?
Es la vista del database que observa una transacción al inicio, congelada hasta el commit o rollback.
> Fundamento: {src:blk_d11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué define el conjunto de transacciones activas que delimitan un snapshot?
Las transacciones que estaban activas en el instante del primer comando de la transacción definen la frontera: las escrituras posteriores de otras transacciones no serán visibles.
> Fundamento: [[note:mvcc-snapshot#active-set]]
:::

:::collapsible{default_open=false}
¿Un snapshot cambia durante la vida de una transacción?
No, permanece estable hasta el commit o rollback; cualquier escritura confirmada después del inicio no es visible para esa transacción.
> Fundamento: [[note:mvcc-snapshot#stability]]
:::
"""
    )


def _bad_no_fundamento() -> str:
    return (
        _frontmatter(
            "Concepto sin fundamento en autoevaluación",
            "concept",
            "Nota concept con colapsable que omite la línea de Fundamento.",
            self_eval_types="[recuerdo, aplicacion, decision]",
        )
        + """

# Concepto sin fundamento en autoevaluación

## TL;DR

Esta nota falla V3 porque un colapsable no cierra con `> Fundamento:`. {src:blk_e11f8e02c1d3}

## Definición

Concepto de prueba para verificar el validador V3 / AP14. {src:blk_e11f8e02c1d3}

## Autoevaluación

Tipos asignados: recuerdo, aplicación, decisión.

### Recuerdo

:::collapsible{default_open=false}
¿Cuál es la diferencia entre snapshot y vista materializada?
El snapshot es MVCC temporal por transacción; la vista materializada es persistente y refrescable manualmente.
:::

:::collapsible{default_open=false}
¿Qué marca indica el inicio de la transacción creadora de una fila?
`xmin`.
> Fundamento: {src:blk_e11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué operación recicla las versiones muertas?
`VACUUM`.
> Fundamento: [[note:vacuum#recycle]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos transacciones T1 y T2, ¿qué ve T2 si T1 aún no hace commit?
La versión previa al commit de T1.
> Fundamento: {src:blk_e11f8e02c1d3}
:::

:::collapsible{default_open=false}
Si tu tabla tiene 80 % de tuplas muertas, ¿qué recomiendas?
Ejecutar `VACUUM (VERBOSE, ANALYZE)`.
> Fundamento: [[note:vacuum#recycle]]
:::

:::collapsible{default_open=false}
Con lecturas largas y escrituras concurrentes, ¿qué nivel de aislamiento?
`REPEATABLE READ`.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

### Decisión

:::collapsible{default_open=false}
Entre `READ COMMITTED` y `REPEATABLE READ`, ¿cuál para reportes agregados?
`REPEATABLE READ`.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

:::collapsible{default_open=false}
¿Cuándo NO usar MVCC?
En sistemas embebidos con memoria muy limitada.
> Fundamento: [[note:storage-tradeoffs#mvcc-vs-locking]]
:::

:::collapsible{default_open=false}
Para OLTP con muchas escrituras, ¿MVCC por fila o por bloque?
MVCC por fila.
> Fundamento: [[note:storage-tradeoffs#granularity]]
:::
"""
    )


def _bad_copiada() -> str:
    return (
        _frontmatter(
            "Concepto con respuesta copiada",
            "concept",
            "Nota concept cuya respuesta es copia literal del bloque referenciado.",
            self_eval_types="[recuerdo, aplicacion, decision]",
        )
        + """

# Concepto con respuesta copiada

## TL;DR

Esta nota falla V4 (respuesta con ≤ 2 tokens no técnicos = trivial). {src:blk_f11f8e02c1d3}

## Definición

Concepto de prueba para verificar V4 / AP13. {src:blk_f11f8e02c1d3}

## Autoevaluación

### Recuerdo

:::collapsible{default_open=false}
¿Qué garantiza el aislamiento snapshot?
Snapshot.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuál es la marca de la transacción creadora?
`xmin`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué operación recicla versiones?
`VACUUM`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

### Aplicación

:::collapsible{default_open=false}
Dados T1 y T2 sin commit, ¿qué ve T2?
Versión previa.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con 80 % muertas, ¿qué operación?
`VACUUM`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con lecturas largas, ¿nivel?
`REPEATABLE READ`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

### Decisión

:::collapsible{default_open=false}
¿READ COMMITTED o REPEATABLE READ?
`REPEATABLE READ`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuándo NO usar MVCC?
Embebidos.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Fila o bloque?
Fila.
> Fundamento: {src:blk_f11f8e02c1d3}
:::
"""
    )


def _bad_recuerdo_en_referencia() -> str:
    return (
        _frontmatter(
            "Término con pregunta de aplicación (mal)",
            "glossary-term",
            "Glossary-term con sección de Aplicación: viola la regla de referencia pura.",
            self_eval_types="[recuerdo, aplicacion]",
        )
        + """

# Término con pregunta de aplicación (mal)

## TL;DR

Término que viola AP15: glossary-term es referencia pura y solo recuerdo aplica. {src:blk_g11f8e02c1d3}

## Autoevaluación

Tipos declarados (incorrectos): recuerdo, aplicación.

### Recuerdo

:::collapsible{default_open=false}
¿Qué es un snapshot?
Vista consistente al inicio de la transacción.
> Fundamento: {src:blk_g11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué define el snapshot?
El conjunto de transacciones activas al inicio.
> Fundamento: [[note:mvcc-snapshot#active-set]]
:::

:::collapsible{default_open=false}
¿Cambia el snapshot durante la transacción?
No, es estable.
> Fundamento: [[note:mvcc-snapshot#stability]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos clientes, ¿cómo configuras el snapshot isolation?
Ajustando `default_transaction_isolation = 'repeatable read'`.
> Fundamento: [[note:isolation-levels#config]]
:::

:::collapsible{default_open=false}
Con un pool de conexiones, ¿cómo preservas el snapshot?
Usando `SET TRANSACTION SNAPSHOT` al iniciar cada transacción del pool.
> Fundamento: [[note:pool-snapshots#reset]]
:::

:::collapsible{default_open=false}
Si necesitas un snapshot distribuido, ¿qué patrón aplicas?
`SET TRANSACTION SNAPSHOT '<id>'` con un id previamente exportado.
> Fundamento: [[note:distributed-snapshots#export]]
:::
"""
    )


def _bad_index_moc_con_seccion() -> str:
    return (
        _frontmatter(
            "MOC indebida con autoevaluación",
            "index-moc",
            "Index-moc con sección ## Autoevaluación: viola V6.",
            self_eval_types="[]",
        )
        + """

# MOC indebida con autoevaluación

## TL;DR

Esta MOC no debería tener autoevaluación. {src:blk_h11f8e02c1d3}

## Índice

- [[note:concept-a]]
- [[note:concept-b]]

## Autoevaluación

:::collapsible{default_open=false}
Pregunta inválida en una MOC.
> Fundamento: {src:blk_h11f8e02c1d3}
:::
"""
    )


FIXTURES = {
    "self-eval-good-1-concept.md": _good_concept,
    "self-eval-good-2-procedure.md": _good_procedure,
    "self-eval-good-3-error-troubleshooting.md": _good_error_troubleshooting,
    "self-eval-good-4-glossary-term.md": _good_glossary_term,
    "self-eval-bad-1-no-fundamento.md": _bad_no_fundamento,
    "self-eval-bad-2-copiada.md": _bad_copiada,
    "self-eval-bad-3-recuerdo-en-referencia.md": _bad_recuerdo_en_referencia,
    "self-eval-bad-4-index-moc-con-seccion.md": _bad_index_moc_con_seccion,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_fixtures.py")
    parser.add_argument("--force", action="store_true",
                        help="regenera fixtures aunque existan")
    args = parser.parse_args(argv)

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    for name, builder in FIXTURES.items():
        path = NOTES_DIR / name
        if path.exists() and not args.force:
            continue
        path.write_text(builder(), encoding="utf-8")
        print(f"[gen] {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

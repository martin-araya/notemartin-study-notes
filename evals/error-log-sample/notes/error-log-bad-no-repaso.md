---
title: "Errores propios — Sin Repaso"
domain: norepaso
note-type: error-log
status: draft
summary: "Living-doc sin `### Repaso` ni `review-next` — falla R-E3."
reading-time-minutes: 1
tags: [study/errors, domain/norepaso]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Sin Repaso

## Resumen de errores

Una entrada sin `### Repaso`.

## Errores registrados

### Error NOREP-001

#### Concepto

Snapshot isolation.

#### Comando erróneo

:::code
psql -h localhost
:::

#### Corrección

:::code
psql -h /var/run/postgresql
:::

Usar socket Unix cuando TCP/IP no está habilitado.

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-12. Contexto: configuración inicial.

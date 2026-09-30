---
title: "Errores propios — Sin enlace canónico"
domain: nofund
note-type: error-log
status: draft
summary: "Living-doc sin enlace `[[note:id]]` en `### Corrección` — falla R-E4."
reading-time-minutes: 1
tags: [study/errors, domain/nofund]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Sin enlace canónico

## Resumen de errores

Una entrada sin enlace a nota canónica.

## Errores registrados

### Error NOFUND-001

#### Concepto

PostgreSQL escucha solo en localhost por defecto.

#### Comando erróneo

:::code
psql -h 0.0.0.0 -U postgres
:::

Salida literal:

:::code
psql: error: connection to server at "0.0.0.0" failed: Connection refused
:::

#### Corrección

:::code
psql -h 127.0.0.1 -U postgres
:::

PostgreSQL por defecto solo escucha en `localhost`.

#### Origen

Fecha del error: 2026-09-10. Contexto: configurar acceso desde otra
máquina.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.

---
title: "Errores propios — Verbatim modificado"
domain: verbatim
note-type: error-log
status: draft
summary: "Living-doc con comando erróneo fuera de bloque :::code — falla R-E2."
reading-time-minutes: 1
tags: [study/errors, domain/verbatim]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Verbatim modificado

## Resumen de errores

Una entrada con comando erróneo en prosa en lugar de bloque verbatim.

## Errores registrados

### Error VERBATIM-001

#### Concepto

Error de conexión.

#### Comando erróneo

Ejecuté psql con un host incorrecto, lo cual produjo un error de
conexión rechazada.

#### Corrección

:::code
psql -h 127.0.0.1 -U postgres
:::

Usar el host correcto.

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-10. Contexto: configuración inicial.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.

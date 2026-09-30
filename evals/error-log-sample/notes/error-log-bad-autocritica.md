---
title: "Errores propios — Mal ejemplo de autocrítica"
domain: bad
note-type: error-log
status: draft
summary: "Living-doc con lenguaje de evaluación personal — debe fallar AP16."
reading-time-minutes: 1
tags: [study/errors, domain/bad]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Mal ejemplo de autocrítica

## Resumen de errores

Una entrada con autocrítica.

## Errores registrados

### Error BAD-001

#### Concepto

No entiendo MVCC, soy malo en esto.

#### Comando erróneo

:::code
SELECT * FROM orders WHERE xmin < 100;
:::

#### Corrección

:::code
SELECT * FROM orders WHERE age(xmin) < '1 hour';
:::

La función `age()` es la forma idiomática. {src:blk_x11f8e02c1d3}

Nota canónica: [[note:mvcc-basics]].

#### Origen

Fecha del error: 2026-09-15. Contexto: intentando optimizar una
consulta.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.

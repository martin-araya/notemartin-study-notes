---
title: "fork"
note-type: glossary-term
status: draft
summary: "System call POSIX que crea un proceso hijo duplicando el proceso actual."
tags: [type/glossary-term, domain/os]
source: "POSIX.1-2017 — fork(2)"
source-type: spec
source-anchor: "fork"
retrieved: 2026-09-27
related: "[[note:docker-architecture]]"
---

# fork

## TL;DR
`fork()` es una system call POSIX que crea un proceso hijo idéntico al padre mediante copia-on-write; usada por servidores y shells. {src:blk_c00000000030}

{layer:l1} {src:blk_fedcba000100}

## Definición
Llamada al sistema que duplica el proceso actual: el hijo recibe una copia del espacio de direcciones, registros y descriptores del padre; retorna 0 al hijo y el PID del hijo al padre. {src:blk_fedcba000200}

## Formas
| Idioma | Forma |
|---|---|
| Inglés | fork (system call) |
| Español | bifurcación (de proceso) |
| Sigla | fork |

## Aliases
- `fork(2)` (notación de man page)
- `vfork` (variant: el padre espera al hijo)
- `clone` (Linux: implementation genérica de fork)

## Contexto
:::tip
POSIX.1-2017; implementada en Linux, macOS, BSD. Usada por Nginx, PostgreSQL, Docker daemon, y shells. {src:blk_fedcba000300}
::: {src:blk_bbccddee0001}

## Ejemplos
:::example
`pid_t pid = fork(); if (pid == 0) { /* proceso hijo */ } else { /* proceso padre */ }` crea un proceso hijo idéntico al padre.
::: {src:blk_bbccddee0002}

## Confundibles
| Término | Diferencia |
|---|---|
| `exec` | Reemplaza el proceso actual con uno nuevo; fork lo duplica |
| `[[term:clone]]` | Linux: implementación genérica con flags; fork es un wrapper |
| `posix_spawn` | API de alto nivel que combina fork + exec |

## Notas donde aparece
- [[note:docker-architecture]]
- [[note:postgresql-architecture]]

## Backlinks
- [[note:docker-architecture]]

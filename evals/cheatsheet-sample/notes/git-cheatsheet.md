---
title: "Git cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/vcs, product/git]
source: "Git official docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: Git project
product: Git
product-version: "2.46"
related: "[[note:procedure-git-rebase]], [[note:error-troubleshooting-merge-conflicts]]"
---

# Git cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de Git 2.46: comandos de staging, commit, push, pull, branching, errores frecuentes. |
| **Procedencia** | Git official docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 2.46 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos Git de staging, commit, push, pull, branching, y errores frecuentes con enlaces a notas detalladas. {src:blk_fedcba000100}

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `git status` | Ver estado del working tree | [[note:procedure-git-rebase]] |
| `git add <file>` | Stage cambios | [[note:procedure-git-rebase]] |
| `git commit -m "msg"` | Commit staged | [[note:procedure-git-rebase]] |
| `git push origin main` | Push commits al remoto | [[note:procedure-git-rebase]] |
| `git pull --rebase` | Pull con rebase en vez de merge | [[note:procedure-git-rebase]] |
| `git log --oneline --graph` | Ver historial compacto | [[note:procedure-git-rebase]] |
| `git diff` | Ver cambios no staged | [[note:procedure-git-rebase]] |
| `git checkout -b feature` | Crear y cambiar a rama | [[note:procedure-git-rebase]] |
| `git merge feature` | Merge de rama | [[note:error-troubleshooting-merge-conflicts]] |
| `git rebase main` | Rebase sobre otra rama | [[note:procedure-git-rebase]] |
| `git stash` | Guardar cambios temporalmente | [[note:procedure-git-rebase]] |
| `git log --oneline -- path/` | Ver historial de un archivo | [[note:procedure-git-rebase]] |

## Atajos
| Atajo | Significado |
|---|---|
| `git st` | Alias para `git status` |
| `git co` | Alias para `git checkout` |
| `git br` | Alias para `git branch` |
| `git ci` | Alias para `git commit` |
| `git pf` | Alias para `git push --force-with-lease` |
| `git lg` | Alias para `git log --oneline --graph` |

## Errores comunes

:::warning
**`merge conflict`** — dos ramas modificaron la misma línea. Solución: editar marcadores `<<<<<<<`, `>>>>>>>`, `git add`, `git commit`. Ver [[note:error-troubleshooting-merge-conflicts]].
::: {src:blk_bbccddee0001}

:::warning
**`non-fast-forward`** — push rechazado por historial divergente. Solución: `git pull --rebase` antes de push, o `git push --force-with-lease`. Ver [[note:procedure-git-rebase]].
::: {src:blk_bbccddee0002}

:::warning
**`detached HEAD`** — HEAD apunta a un commit, no a una rama. Solución: `git checkout <branch>` o crear rama con `git switch -c <new>`. Ver [[note:procedure-git-rebase]].
::: {src:blk_bbccddee0003}

## Backlinks
- [[note:procedure-git-rebase]]
- [[note:error-troubleshooting-merge-conflicts]]

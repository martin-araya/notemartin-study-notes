---
title: "Git — rebase interactivo"
note-type: practice
status: draft
difficulty: 3
tags: [type/practice, domain/vcs, product/git]
source: "Git official docs"
source-type: docs
source-anchor: "rebase-interactive"
retrieved: 2026-09-27
vendor: Git project
product: Git
product-version: "2.46"
related: "[[note:procedure-git-rebase]], [[note:error-troubleshooting-merge-conflicts]]"
---

# Git — rebase interactivo

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: reescribir la historia de commits con `git rebase -i` (squash, reword, reorder). |
| **Procedencia** | Git official docs (docs) §rebase-interactive · recuperado 2026-09-27 |
| **Versión** | 2.46 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 10 min |

## TL;DR
Reescribir la historia de commits de un branch local con `git rebase -i HEAD~3` (squash 2 commits, reword el primero, reorder el último). Aprende el editor interactivo de git. {src:blk_c00000000003}

{layer:l2}

## Enunciado
Tienes un branch local con 3 commits desordenados. El objetivo es reordenarlos, combinarlos, y reescribir el mensaje del primero usando `git rebase -i`. {src:blk_fedcba000100}

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Git | 2.46.x | - |
| Editor | vim / nano / VSCode | Git usa el editor por defecto |
| Recursos | - | - |

## Objetivo
Aprender el editor interactivo de `git rebase -i` con acciones `pick`, `squash`, `reword`, y `reorder`. {src:blk_fedcba000200}

## Solución

### Paso 1: Crear el repositorio de práctica {src:blk_aabbccddee01}
```bash
mkdir practice-git && cd practice-git
git init
git config user.email "lab@example.com"
git config user.name "Lab User"
# {src:blk_ccddeebf0001}
```

### Paso 2: Crear 3 commits desordenados {src:blk_aabbccddee02}
```bash
echo "first" > a.txt && git add a.txt && git commit -m "Commit A"
echo "second" > b.txt && git add b.txt && git commit -m "Commit B"
echo "third" > c.txt && git add c.txt && git commit -m "Commit C"
# {src:blk_ccddeebf0002}
```

### Paso 3: Iniciar rebase interactivo {src:blk_aabbccddee03}
```bash
git rebase -i HEAD~3
# {src:blk_ccddeebf0003}
```
Se abre el editor con un contenido como:
```
pick abc123 Commit A
pick def456 Commit B
pick ghi789 Commit C
# {src:blk_ccddeebf0004}
```

### Paso 4: Modificar el plan de rebase {src:blk_aabbccddee04}
Cambiar a:
```
reword abc123 Mensaje mejorado para A
squash def456 Commit B
pick ghi789 Commit C
# {src:blk_ccddeebf0005}
```
Guardar y cerrar. Git aplica el rebase.

## Qué observar
:::note {src:blk_fedcba000300}
- Después de `pick C`, `squash B`, `reword A`: el resultado debe ser 1 commit con el mensaje mejorado de A + el contenido de B combinado.
- `git log --oneline` debe mostrar 1 commit (en lugar de los 3 originales).
- `git show HEAD` debe incluir los cambios de A, B y C.
::: {src:blk_bbccddee0005}

## Verificación
La verificación cubre 3 señales que confirman que el rebase interactivo funcionó correctamente. {src:blk_fedcba000400}

- `git log --oneline` retorna 1 commit (no 3).
- El mensaje del commit empieza con "Mensaje mejorado para A".
- `git show HEAD --stat` muestra archivos `a.txt`, `b.txt`, `c.txt` modificados. {src:blk_c00000000006}

## Limpieza

1. Salir del directorio del lab: {src:blk_fedcba000500}
   ```bash
   cd .. {src:blk_fedcba000600}
# {src:blk_ccddeebf0006}
   ```
2. Borrar el directorio del lab: {src:blk_fedcba000700}
   ```bash
   rm -rf practice-git {src:blk_fedcba000800}
# {src:blk_ccddeebf0007}
   ```

Después de la limpieza, no queda rastro del lab. {src:blk_fedcba000900}

## Lo que NO debe correrse en producción

:::danger {src:blk_fedcba000a00}
- `git push --force-with-lease=0` o `git push --force`: reescribe la historia del remoto. Otros colaboradores con el branch local quedan con historiales divergentes. {src:blk_c00000000008}

En producción, prefiere `git revert <commit>` (crea un commit nuevo que deshace los cambios) sobre rebase + force-push. {src:blk_fedcba000b00}
::: {src:blk_bbccddee0006}

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas `git rebase -i` con todas las acciones (pick, reword, edit, squash, fixup, exec, break, drop, label, reset, merge); (2) trabajas en un branch compartido con muchos colaboradores y la política del equipo es "no rebase"; (3) tu equipo usa squash-merge automático en GitHub/GitLab y nunca necesitas reescribir historia local; (4) prefieres `git merge --squash` para combinar features en vez de reescribir commits individuales.
::: {src:blk_bbccddee0007}

## Pistas

:::tip
Si el editor no se abre, configura `git config core.editor "vim"` (o tu editor preferido). Si hay conflictos durante el rebase, resuélvelos con `git add <archivo>` y luego `git rebase --continue`. Para abortar el rebase y volver al estado original: `git rebase --abort`.
::: {src:blk_bbccddee0008}

## Backlinks
El lab se conecta con el procedure de rebase y la nota de troubleshooting de conflictos; los enlaces muestran los 2 ángulos del flujo. {src:blk_c00000000007}

- [[note:procedure-git-rebase]]
- [[note:error-troubleshooting-merge-conflicts]]

---
title: "Verificar pods de Kubernetes con kubectl"
note-type: procedure
status: published
summary: "Procedimiento para listar y describir pods en un namespace."
reading-time-minutes: 2
tags: [type/procedure, domain/networking, f80/procedure, f99/voice-style]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch02/pods"
retrieved: 2026-09-29
product: "Kubernetes"
product-version: "1.29"
related: "[[note:kubectl-get]]"
---

# Verificar pods de Kubernetes con kubectl

Lista los pods de un namespace y describe uno concreto para diagnosticar
su estado. {src:blk_b12c44f0a8e7}

## Procedimiento

Ejecuta `kubectl get pods -n <namespace>` para listar los pods. {src:blk_1d3e8a92f7c4}
Copia el nombre del pod que quieras inspeccionar. Después ejecuta
`kubectl describe pod <nombre> -n <namespace>` para ver eventos y estado.
{src:blk_5e7f0a3b2c19}

Si el pod no aparece en la lista, comprueba el namespace con
`kubectl config view --minify --output 'jsonpath={..namespace}'`.
{src:blk_8c4d9e6f1a20}

## Limpieza

> No requiere limpieza: `kubectl get` y `kubectl describe` son operaciones
> de solo lectura. {src:blk_a7b8c9d0e1f2}

## Verificación

Verás eventos al final del output. Si hay `ImagePullBackOff`, revisa
el nombre de la imagen. Si hay `CrashLoopBackOff`, ejecuta
`kubectl logs <pod> -n <namespace>` para inspeccionar el error.
{src:blk_6b7c8d9e0f1a}

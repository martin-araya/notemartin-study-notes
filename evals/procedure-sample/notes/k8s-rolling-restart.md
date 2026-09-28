---
title: "Kubernetes — rolling restart de un Deployment"
note-type: procedure
status: draft
summary: "Reinicia los pods de un Deployment uno a uno usando kubectl rollout restart; preserva disponibilidad durante el rollout, declara explícitamente el riesgo de cascade delete con kubectl delete."
tags: [type/procedure, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — kubectl rollout"
source-type: docs
source-anchor: "kubectl-rollout"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-deployment-lifecycle]], [[note:k8s-pod-disruption-budget]]"
---

# Kubernetes — rolling restart de un Deployment

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Reinicia los pods de un Deployment uno a uno usando kubectl rollout restart; preserva disponibilidad durante el rollout, declara explícitamente el riesgo de cascade delete con kubectl delete. |
| **Procedencia** | Kubernetes 1.30 — kubectl rollout (docs) §kubectl-rollout · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 2 min |

## TL;DR
`kubectl rollout restart deployment/<name>` actualiza el annotation `kubectl.kubernetes.io/restartedAt`, lo que dispara el rollout; los pods se recrean uno a uno respetando el `Deployment` strategy y, si existe, el `PodDisruptionBudget`. La operación `kubectl delete` es destructiva y usa `:::danger`. {src:blk_c000000a01d1}

{layer:l2}

## Objetivo
Reiniciar los pods de un Deployment sin cambiar el spec del Deployment (mismo image, mismas env vars); útil tras actualizar un ConfigMap montado como volume o tras rotación de un secret. {src:blk_ddbbccddeefd}

## Aplicabilidad
El procedimiento aplica a Deployments estándar con rolling update; para StatefulSets, DaemonSets o deployments single-replica la estrategia cambia.

- **SÍ:** Deployment con `strategy.rollingUpdate`; recargar ConfigMap/Secret sin re-deploy; limpiar estado en memoria (caches, conexiones abiertas). {src:blk_c000000a01d2}
- **NO:** StatefulSet (usar `kubectl rollout restart statefulset`); DaemonSet (borrar pods uno a uno manualmente); deployments con `replicas: 1` (causa downtime total durante el recreate). {src:blk_c000000a01d3}

## Precondiciones verificadas
Antes de iniciar el restart, todas estas condiciones deben cumplirse. Cada una con su verificación ejecutable. {src:blk_c000000a01d4}

- `kubectl` con kubeconfig válido: `kubectl cluster-info` retorna URLs de master y services.
- Permisos: el usuario debe tener `patch` sobre `deployments` en el namespace del target.
- PDB si el Deployment es crítico: `kubectl get pdb -n <ns>` muestra un budget que permita la disrupción.

## Impacto y reversibilidad

| Aspecto | Detalle |
|---|---|
| Ventana de indisponibilidad | 0 con `replicas ≥ 2` y `maxUnavailable=0`; hasta `maxUnavailable` con `maxUnavailable=25%` por defecto |
| Datos afectados | Solo memoria/volúmenes efímeros de los pods; cero impacto en volúmenes persistentes |
| Rollback | `kubectl rollout undo deployment/<name>` revierte al revision anterior del spec; **no** revierte pods que ya se recrearon |

## Procedimiento

### Paso 1: Confirmar el estado actual del rollout
```bash
kubectl rollout status deployment/web -n default --timeout=10s
# {src:blk_ccddeebf0001}
```

**Salida esperada:** {src:blk_aabbccddee01}
```
deployment "web" successfully rolled out
# {src:blk_ccddeebf0002}
```

**Verificación:** exit code 0; si retorna `Waiting for rollout to finish`, **no proceder** — el rollout anterior está en curso. {src:blk_aabbccddee02}

### Paso 2: Disparar el restart
```bash
kubectl rollout restart deployment/web -n default
# {src:blk_ccddeebf0003}
```

**Verificación:** `kubectl get deployment web -n default -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/restartedAt}'` retorna un timestamp ISO 8601 reciente. {src:blk_aabbccddee03}

### Paso 3: Esperar a que el rollout complete
```bash
kubectl rollout status deployment/web -n default --timeout=5m
# {src:blk_ccddeebf0004}
```

**Verificación:** exit code 0 y `kubectl get pods -l app=web -n default` muestra todos los pods en estado `Running` con `Ready 1/1` y `RESTARTS` incrementados respecto al Paso 1. {src:blk_aabbccddee04}

### Paso 4: Verificar disponibilidad end-to-end
```bash
kubectl get pods -l app=web -n default -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -q true
# {src:blk_ccddeebf0005}
```

**Verificación:** al menos 1 pod en `Ready` durante todo el rollout (lo confirma el `Ready` final); si 0, abrir incidente (criterio: el rollout falló). {src:blk_aabbccddee05}

:::danger
**Operación alternativa destructiva — `kubectl delete pod -l app=web -n default`.** Esta acción **borra los pods inmediatamente** y deja que el Deployment los recree. Equivalente funcional a `rollout restart` pero **sin orquestación gradual**: viola `maxUnavailable` y `PodDisruptionBudget`. Solo usar si `rollout restart` falla por bug conocido y se documenta el incidente.

## Verificación final
```bash
kubectl get pods -l app=web -n default -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp {src:blk_eeeeff0008}
# {src:blk_ccddeebf0006}
```

Todos los pods deben tener `RESTARTS ≥ 1` (fresco) y `AGE` reciente (≤ 5 min desde el Paso 2). {src:blk_ddbbccddeefe}

## Errores frecuentes
:::danger
**`kubectl rollout restart` con `replicas: 1` causa downtime total.** El pod viejo se termina antes de que el nuevo esté Ready. Solución: escalar temporalmente a `replicas: 2` antes del restart, o usar `kubectl scale deployment/web --replicas=2` seguido de restart, y volver a `replicas: 1` después.
::: {src:blk_bbccddee0006}

:::warning
**Rollout que excede `--timeout=5m`.** Típicamente por image pull lento o PDB que bloquea. Diagnóstico: `kubectl describe deployment web -n default | tail -30` muestra el `Progressing=False` con el motivo (image pull back-off, PDB, etc.).
::: {src:blk_bbccddee0007}

:::warning
**`kubectl rollout undo` no revierte pods ya recreados.** Solo revierte el spec del Deployment al revision anterior; si el revision N ya tenía el bug, undo vuelve al N-1 que también lo tiene. Solución: usar `kubectl rollout history deployment/web -n default` para listar revisions antes de undo.

## Backlinks
El rolling restart es el método canónico para reiniciar pods sin downtime; los enlaces muestran el ciclo de vida del Deployment y el rol del PDB. {src:blk_c000000a01d5}

- [[note:k8s-deployment-lifecycle]] — fases del rollout: Progressing → Available.
- [[note:k8s-pod-disruption-budget]] — cómo el PDB afecta al ritmo del rollout.

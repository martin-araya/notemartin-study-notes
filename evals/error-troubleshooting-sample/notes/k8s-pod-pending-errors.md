---
title: "Kubernetes — 4 errores comunes de Pod Pending"
note-type: error-troubleshooting
status: draft
summary: "Cuatro errores que dejan un Pod en estado Pending (ImagePullBackOff, Insufficient cpu, Insufficient memory, ErrImageNeverPull) con causa raíz, diagnóstico, solución, confundibles y árbol de decisión."
tags: [type/error-troubleshooting, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod Lifecycle"
source-type: docs
source-anchor: "pod-lifecycle"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-resources]], [[note:procedure-debug-pending-pod]]"
---

# Kubernetes — 4 errores comunes de Pod Pending

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cuatro errores que dejan un Pod en estado Pending (ImagePullBackOff, Insufficient cpu, Insufficient memory, ErrImageNeverPull) con causa raíz, diagnóstico, solución, confundibles y árbol de decisión. |
| **Procedencia** | Kubernetes 1.30 — Pod Lifecycle (docs) §pod-lifecycle · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Pod Pending significa que el scheduler no puede asignarlo a un nodo. Las 4 causas más frecuentes: imagen no pullable, recursos insuficientes, taints no toleradas, y ErrImageNeverPull. Diagnosticar con `kubectl describe pod`. {src:blk_e00000000020}

{layer:l2}

## Síntomas

### Mensaje 1: ImagePullBackOff
```
Warning  Failed     5m  kubelet            Failed to pull image "myorg/api:1.0": rpc error: code = Unknown desc = Error response from daemon: pull access denied for myorg/api, repository does not exist or may require 'docker login'
Warning  Failed     5m  kubelet            Error: ErrImagePull
Warning  BackOff    5m  kubelet            Back-off pulling image "myorg/api:1.0"
# {src:blk_ccddeebf0001}
```

### Mensaje 2: Insufficient cpu
```
Warning  FailedScheduling  30s  default-scheduler  0/3 nodes are available: 3 Insufficient cpu.
# {src:blk_ccddeebf0002}
```

### Mensaje 3: Insufficient memory
```
Warning  FailedScheduling  30s  default-scheduler  0/3 nodes are available: 3 Insufficient memory.
# {src:blk_ccddeebf0003}
```

### Mensaje 4: ErrImageNeverPull
```
Warning  Failed     5m  kubelet            Failed to pull image "myorg/api:1.0": image pull policy is "Never" and the image is not present locally
# {src:blk_ccddeebf0004}
```

## Causa raíz

### Mensaje 1: ImagePullBackOff
La imagen no se puede descargar del registry. Tres causas: (a) nombre/tag incorrecto; (b) registry privado sin `imagePullSecrets`; (c) credenciales del registry expiradas o inválidas. {src:blk_e00000000021}

### Mensaje 2: Insufficient cpu
La suma de `requests.cpu` de todos los Pods supera `allocatable.cpu` del nodo. Scheduler no encuentra nodo donde colocar el Pod. {src:blk_e00000000022}

### Mensaje 3: Insufficient memory
Idem cpu pero para `requests.memory`. Distinto de OOMKilled: aquí el Pod **no llega a arrancar**; OOMKilled es post-arranque. {src:blk_e00000000023}

### Mensaje 4: ErrImageNeverPull
`imagePullPolicy: Never` (explícito o por defecto para `:latest`) y la imagen no está pre-cargada en el nodo. No es lo mismo que ImagePullBackOff: aquí no hay reintentos. {src:blk_e00000000024}

## Diagnóstico ordenado
```bash
# Paso 1: ¿Qué dice el scheduler?
kubectl describe pod <name> -n <ns> | tail -20
# {src:blk_ccddeebf0005}
```
**Verificación:** la sección `Events:` muestra el motivo exacto (ImagePullBackOff, FailedScheduling, etc.). {src:blk_aabbccddee01}

```bash
# Paso 2: ¿Hay recursos disponibles en el cluster?
kubectl describe nodes | grep -A 5 "Allocated resources"
# {src:blk_ccddeebf0006}
```
**Verificación:** si `cpu` o `memory` están al 100%, hay presión. {src:blk_aabbccddee02}

```bash
# Paso 3: ¿La imagen existe y es accesible?
docker pull myorg/api:1.0   # o: kubectl run --image=myorg/api:1.0 --rm -it --restart=Never
# {src:blk_ccddeebf0007}
```
**Verificación:** exit 0 → sí; `pull access denied` → problema de registry/auth. {src:blk_aabbccddee03}

## Solución

### Mensaje 1: ImagePullBackOff
```bash
# Verificar tag y registry
kubectl get pod <name> -o jsonpath='{.spec.containers[0].image}'
# Añadir imagePullSecret si registry privado
kubectl create secret docker-registry myregistry --docker-server=... --docker-username=... --docker-password=... -n <ns>
# {src:blk_ccddeebf0008}
```
Luego añadir `imagePullSecrets: [{name: myregistry}]` al Pod spec y reintentar.

### Mensaje 2: Insufficient cpu
:::danger
**Reducir `requests.cpu` en producción puede causar nodos saturados.** Solución conservadora: añadir nodos o escalar el cluster; no bajar requests unilateralmente.
::: {src:blk_bbccddee0004}

```bash
# Aumentar nodos (autoscaling)
kubectl scale deploy cluster-autoscaler --replicas=+1
# O reducir requests del Deployment asociado
kubectl edit deployment <name>
# {src:blk_ccddeebf0009}
```

### Mensaje 3: Insufficient memory
Idem cpu pero para memoria. Considerar primero liberar memoria de otros Pods (`kubectl delete pod` con QoS BestEffort antes), no bajar requests.

### Mensaje 4: ErrImageNeverPull
Cambiar `imagePullPolicy: Always` o pre-cargar la imagen con `docker load` en cada nodo.

## Prevención

:::tip
**Mensaje 1:** Versionar imágenes por tag inmutable (`:sha-abc123`) en vez de `:latest`; automatizar rotación de `imagePullSecrets` con `external-secrets`.
::: {src:blk_bbccddee0005}

:::tip
**Mensaje 2:** Configurar `HorizontalPodAutoscaler` con `resources.requests.cpu` conservador; `cluster-autoscaler` para nodos dinámicos.
::: {src:blk_bbccddee0006}

:::tip
**Mensaje 3:** Definir `LimitRange` por namespace para acotar requests.memory; monitorizar `kube-state-metrics` para `allocatable_memory_pressure`.
::: {src:blk_bbccddee0007}

:::tip
**Mensaje 4:** Usar `imagePullPolicy: IfNotPresent` solo en imágenes inmutables; pre-cargar en nodos con `DaemonSet` `image-cache-loader`.
::: {src:blk_bbccddee0008}

## Confundibles

| Error | Diferencia con este | Nota relacionada |
|---|---|---|
| `ImagePullBackOff` (k8s) vs `pull access denied` (Docker) | k8s: Pod Pending; Docker: comando local falla | [[note:docker-permission-errors]] |
| `Insufficient cpu` vs `Pending` sin razón clara | scheduler no muestra motivo | [[note:postgres-connection-errors]] (síntomas de "servicio no disponible") |
| `OOMKilled` (post-arranque) | container supera `limits.memory` | [[note:k8s-pod-resources]] (configuración de limits) |
| `ErrImageNeverPull` vs `ImagePullBackOff` | NeverPull: no reintentos; BackOff: reintentos con backoff | mismo tipo, comportamiento distinto |

## Árbol de diagnóstico
:::diagram
```mermaid
flowchart TD
    A[Pod Pending] --> B{¿Imagen accesible?}
    B -->|No| C{¿Pull policy Never?}
    C -->|Sí| D[ErrImageNeverPull: pre-cargar]
    C -->|No| E[ImagePullBackOff: imagePullSecrets]
    B -->|Sí| F{¿Recursos disponibles?}
    F -->|cpu| G[Insufficient cpu: añadir nodo]
    F -->|memory| H[Insufficient memory: añadir nodo]
    F -->|Sí| I{¿Taints toleradas?}
    I -->|No| J[Añadir tolerations al Pod]
    I -->|Sí| K[OK]
# {src:blk_ccddeebf000a}
```
::: {src:blk_bbccddee0009}

## Tabla índice

| Mensaje literal | Sección |
|---|---|
| `Failed to pull image ... pull access denied` | Síntomas 1 |
| `0/N nodes are available: N Insufficient cpu` | Síntomas 2 |
| `0/N nodes are available: N Insufficient memory` | Síntomas 3 |
| `image pull policy is "Never" and the image is not present locally` | Síntomas 4 |

## Backlinks
Pod Pending es uno de los estados más comunes al desplegar; los enlaces muestran las herramientas de debugging y los confundibles de otros sistemas. {src:blk_e00000000041}

- [[note:k8s-pod-resources]] — `requests` y `limits` que el scheduler evalúa.
- [[note:procedure-debug-pending-pod]] — procedure paso a paso para diagnosticar Pending.
- [[note:postgres-connection-errors]] — confundibles: errores de servicio no disponible.
- [[note:docker-permission-errors]] — confundibles: pull access denied en Docker local.

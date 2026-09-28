---
title: "Kubernetes Pod — resources (requests + limits + QoS class)"
note-type: configuration
status: draft
summary: "Configuración de resources.requests y resources.limits en Pod core/v1; clases QoS (Guaranteed, Burstable, BestEffort), combinaciones peligrosas e interacciones con node allocatable."
tags: [type/configuration, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod Resources"
source-type: docs
source-anchor: "pod-resources"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-lifecycle]], [[note:k8s-pod-disruption-budget]]"
---

# Kubernetes Pod — resources (requests + limits + QoS class)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Configuración de resources.requests y resources.limits en Pod core/v1; clases QoS (Guaranteed, Burstable, BestEffort), combinaciones peligrosas e interacciones con node allocatable. |
| **Procedencia** | Kubernetes 1.30 — Pod Resources (docs) §pod-resources · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
`spec.containers[].resources.requests` y `.limits` controlan CPU y memoria del Pod; la combinación determina la QoS class (Guaranteed / Burstable / BestEffort), que a su vez decide la prioridad de eviction. Los defaults son BestEffort (sin requests/limits) — no recomendado en producción. {src:blk_c00000000020}

{layer:l2}

## Configuración
```yaml
# Pod spec — subset canónico de resources
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:1.27
    resources:
      requests:
        cpu: "100m"       # 0.1 CPU
        memory: "64Mi"    # 64 MiB
      limits:
        cpu: "500m"       # 0.5 CPU
        memory: "256Mi"   # 256 MiB
# {src:blk_ccddeebf0001}
```

## Parámetros

### Resources
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `requests.cpu` | container | string | `unset` (BestEffort) | 1m–n CPU | n/a | sí | 1.0+ | disponibilidad: scheduler; suma de requests ≤ node allocatable |
| `requests.memory` | container | size | `unset` (BestEffort) | ≥ 0 | n/a | sí | 1.0+ | disponibilidad: scheduler; reserva para el Pod en el nodo |
| `limits.cpu` | container | string | `unset` (sin límite) | ≥ 1m | sí | no | 1.0+ | rendimiento: throttling cuando se excede |
| `limits.memory` | container | size | `unset` (sin límite) | ≥ requests.memory | sí | no | 1.0+ | disponibilidad: OOMKill cuando se excede |

### QoS class (derivada)
| Parámetro | Ámbito | Tipo | Default | Rango | Hot reload | Reinicio | Versión | Impacto |
|---|---|---|---|---|---|---|---|---|
| `qosClass` | pod (read-only) | enum | `BestEffort` | Guaranteed/Burstable/BestEffort | n/a | n/a | 1.0+ | disponibilidad: orden de eviction bajo presión de memoria; Guaranteed > Burstable > BestEffort |

## Ejemplo completo
:::example
**Pod de producción (Burstable, recomendado):** {src:blk_c00000000090}

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
  - name: app
    image: myorg/api:1.0
    resources:
      requests:
        cpu: "250m"
        memory: "256Mi"
      limits:
        cpu: "1000m"
        memory: "1Gi"
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0001}

## Combinaciones peligrosas
:::danger
**`requests.memory = 64Mi` + `limits.memory = 32Mi` (limits < requests).** Inválido: Kubernetes rechaza el Pod con `Invalid value: must be greater than or equal to memory request`. Solución: `limits.memory ≥ requests.memory`.
::: {src:blk_bbccddee0002}

:::danger
**`requests = limits` en CPU y memoria + eviction policy agresiva.** QoS = Guaranteed, lo cual es bueno, pero **sin memory requests** el Pod es BestEffort y se evicta primero. Solución: siempre definir `requests.memory`.
::: {src:blk_bbccddee0003}

:::danger
**`limits.memory = 4Gi` en node con `allocatable.memory = 2Gi`.** El scheduler acepta el Pod pero el container será OOMKilled en cuanto supere 2 Gi (el cgroup no aplica el limit, el kernel sí). Solución: monitorear `kube-state-metrics` y bajar el limit.
::: {src:blk_bbccddee0004}

## Interacciones
| Cambio | Revisar también |
|---|---|
| Subir `requests.cpu` | `node allocatable.cpu` (scheduler; suma de requests ≤ allocatable) |
| Subir `requests.memory` | `node allocatable.memory`; `kube-scheduler` densidad del nodo |
| Subir `limits.cpu` | throttling: `container_cpu_cfs_throttled_seconds_total` en Prometheus |
| Subir `limits.memory` | OOMKill: `container_oom_events_total`; `evictions` en `kube-state-metrics` |
| Cambiar QoS | `PodDisruptionBudget` (BestEffort se evicta primero), `PriorityClass` |

## Diagrama de dependencias
:::diagram
```mermaid
flowchart LR
    RCPU[requests.cpu] --> NA[node allocatable.cpu]
    RMEM[requests.memory] --> NMEM[node allocatable.memory]
    RCPU --> SCH[kube-scheduler]
    RMEM --> SCH
    LCPU[limits.cpu] --> THR[CPU throttling]
    LMEM[limits.memory] --> OOM[OOMKill]
    REQ[requests = limits] --> GUAR[QoS: Guaranteed]
    REQ2[requests < limits] --> BUR[QoS: Burstable]
    REQ3[sin requests/limits] --> BE[QoS: BestEffort]
    GUAR --> EV[eviction order]
    BUR --> EV
    BE --> EV
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0005}

## Valores comunes

| Caso | requests.cpu | requests.memory | limits.cpu | limits.memory | QoS |
|---|---|---|---|---|---|
| Producción típica | `250m` | `256Mi` | `1000m` | `1Gi` | Burstable |
| Crítico (BD, cache) | `1000m` | `2Gi` | `1000m` | `2Gi` | Guaranteed |
| BestEffort (dev only) | n/a | n/a | n/a | n/a | BestEffort |

## Troubleshooting
:::warning
**Pod en `Pending` con `Insufficient memory`.** Suma de `requests.memory` excede `allocatable.memory` del nodo. Solución: bajar requests o añadir nodos.
::: {src:blk_bbccddee0006}

:::warning
**Pod en `OOMKilled` repetidamente.** El container excede `limits.memory`. Solución: subir limit o detectar memory leak con `pprof` / `go tool trace`.
::: {src:blk_bbccddee0007}

## Backlinks
Los resources de un Pod interactúan con el scheduler y el eviction manager; los enlaces muestran el ciclo de vida y el rol del PDB. {src:blk_c00000000070}

- [[note:k8s-pod-lifecycle]] — fases del Pod y rol del QoS en eviction.
- [[note:k8s-pod-disruption-budget]] — interacción con disruption budgets.

---
title: "Kubernetes API — POST /api/v1/namespaces/{namespace}/pods"
note-type: api-reference
status: draft
summary: "Endpoint REST para crear un Pod en un namespace; campos canónicos del schema core/v1, errores HTTP, privilegios RBAC y precondiciones."
tags: [type/api-reference, domain/rest, product/kubernetes]
source: "Kubernetes 1.30 — Pod v1 API Reference"
source-type: docs
source-anchor: "core/pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-lifecycle]], [[note:k8s-rbac]]"
---

# Kubernetes API — POST /api/v1/namespaces/{namespace}/pods

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Endpoint REST para crear un Pod en un namespace; campos canónicos del schema core/v1, errores HTTP, privilegios RBAC y precondiciones. |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API Reference (docs) §core/pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
`POST /api/v1/namespaces/{namespace}/pods` crea un Pod; el body es un objeto `Pod` core/v1 con `apiVersion`, `kind`, `metadata`, `spec`; requiere `create` en `pods` del namespace y namespace existente. {src:blk_a8a00001a001}

{layer:l2} {src:blk_a1b2c3d4e500}

## Sintaxis
```http
# {src:blk_aabbccddee01}
```

Body mínimo:

```json
# {src:blk_aabbccddee02}
```

## Parámetros
| Parámetro | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `{namespace}` | string (path) | **sí** | n/a | namespace donde se crea el Pod; debe existir |
| `apiVersion` | string (body) | **sí** | n/a | siempre `"v1"` para core/v1 |
| `kind` | string (body) | **sí** | n/a | siempre `"Pod"` |
| `metadata.name` | string (body) | **sí** | n/a | nombre DNS-1123 válido (≤ 63 chars, `[a-z0-9-]`) |
| `metadata.namespace` | string (body) | no | (del path) | debe coincidir con `{namespace}` |
| `metadata.labels` | map[string]string | no | (vacío) | etiquetas clave-valor |
| `spec.containers` | array<Container> | **sí** | n/a | ≥ 1 contenedor; cada uno con `name` + `image` |
| `spec.containers[].name` | string | **sí** | n/a | nombre único dentro del Pod |
| `spec.containers[].image` | string | **sí** | n/a | imagen (registry/path:tag) |
| `spec.containers[].ports` | array<ContainerPort> | no | (vacío) | puertos `containerPort` + opcional `name`/`protocol` |
| `spec.containers[].resources` | ResourceRequirements | no | (sin límites) | `limits` y `requests` (CPU/memoria) |
| `spec.containers[].env` | array<EnvVar> | no | (de la imagen) | variables de entorno (`name` + `value` o `valueFrom`) |
| `spec.restartPolicy` | enum | no | `Always` | `Always` / `OnFailure` / `Never` |
| `spec.nodeSelector` | map[string]string | no | (vacío) | restricciones de scheduling por labels de nodo |

## Retornos
`201 Created` con el objeto `Pod` completo (incluido `metadata.uid`, `status`, `metadata.creationTimestamp`). {src:blk_a8a00001a009}

## Excepciones
| Código | Causa | Remediación |
|---|---|---|
| 400 | schema inválido o nombre no DNS-1123 | validar con `kubectl apply --dry-run=client -f pod.yaml` |
| 401 | token ausente o expirado | renovar token; verificar ServiceAccount |
| 403 | sin `create` en `pods` del namespace | crear RoleBinding con `pods/create` |
| 404 | namespace no existe | crear con `kubectl create namespace <name>` |
| 409 | ya existe un Pod con ese `metadata.name` | borrar el previo o cambiar nombre |
| 422 | `image` no pullable o `nodeSelector` sin nodos | revisar `kubectl describe pod <name>` |
| 500 | error interno del apiserver | reintentar; si persiste, abrir issue con `kubectl get events` |

## Privilegios
RBAC verb `create` sobre el recurso `pods` en el namespace del path. Equivalente YAML: `rules: - apiGroups: [""] resources: ["pods"] verbs: ["create"]`. Para ServiceAccount: `kubectl create rolebinding <name> --role=<role> --serviceaccount=<ns>:<sa>`. {src:blk_a8a00001a002}

## Precondiciones
Antes de llamar al endpoint, el clúster debe estar listo y el namespace destino debe existir; sin esto el apiserver rechaza con 404 antes de evaluar el schema. {src:blk_a8a00001a003}

- API server alcanzable (`kubectl cluster-info`).
- Namespace `{namespace}` debe existir (verificar con `kubectl get namespace {namespace}`).
- Si el Pod usa `image` privada, el `imagePullSecret` debe estar en el namespace.
- Si `spec.nodeSelector` referencia labels, los nodos deben tener esos labels.

## Ejemplos
:::example
**Mínimo:** Pod nginx de un contenedor, exposición de puerto 80. {src:blk_a8a00001a00a}

```bash
# {src:blk_aabbccddee03}
```
::: {src:blk_aabbcc0001ee}

:::example
**Realista:** Pod con límites de recursos, variables de entorno y nodeSelector. {src:blk_a8a00001a00b}

```bash
# {src:blk_aabbccddee04}
```
::: {src:blk_aabbcc0002ee}

## Gotchas
:::warning
**`metadata.namespace` en el body debe coincidir con el path.** Si difieren, el apiserver retorna 422 con `metadata.namespace: Invalid value: "..."`. Solución: omitir `metadata.namespace` y dejar que el path lo aporte. {src:blk_a8a00001a004}
::: {src:blk_aabbcc0003ee}

:::warning
**`spec.containers` vacío** falla con 422 (`spec.containers: Required value`). Solución: incluir ≥ 1 contenedor; usar `Deployment` o `Job` si necesitas 0. {src:blk_a8a00001a005}
::: {src:blk_aabbcc0004ee}

:::warning
**`image` sin tag** descarga `latest`, que puede variar entre pulls. Solución: pinear por digest (`nginx:1.27@sha256:...`) o tag inmutable. {src:blk_a8a00001a006}
::: {src:blk_aabbcc0005ee}

:::warning
**`nodeSelector` sin nodos coincidentes** deja el Pod en `Pending` indefinidamente. Solución: `kubectl describe pod <name>` muestra el evento "0/N nodes are available". {src:blk_a8a00001a007}
::: {src:blk_aabbcc0006ee}

## Backlinks
El endpoint POST Pods es referenciado desde procedure (cómo crear un Pod) y architecture (cómo escala el control plane). {src:blk_a8a00001a008}

- [[note:k8s-pod-lifecycle]] — fases Pending → Running → Succeeded/Failed.
- [[note:k8s-rbac]] — modelo de autorización del cluster.

## Queries
```dataview
# {src:blk_aabbccddee05}
```

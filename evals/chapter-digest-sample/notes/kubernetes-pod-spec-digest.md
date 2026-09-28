---
title: "Kubernetes 1.30 — Pod spec API reference (digest)"
note-type: chapter-digest
status: draft
summary: "Digest del Pod v1 API reference de Kubernetes 1.30: spec.containers, lifecycle, resources, scheduling constraints, security context, DNS policy."
tags: [type/chapter-digest, domain/kubernetes, source/kubernetes-docs]
source: "Kubernetes 1.30 — Pod v1 API reference"
source-type: docs
source-anchor: "pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
coverage: summary
related: "[[note:overview-digest]], [[note:deployment-digest]]"
---

# Kubernetes 1.30 — Pod spec API reference (digest)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Digest del Pod v1 API reference de Kubernetes 1.30: spec.containers, lifecycle, resources, scheduling constraints, security context, DNS policy. |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API reference (docs) §pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
El spec de un Pod core/v1 tiene 4 secciones obligatorias (`apiVersion`, `kind`, `metadata.name`, `spec.containers[]`) y 14+ opcionales (`priorityClassName`, `tolerations`, `affinity`, `nodeSelector`, `lifecycle`, `securityContext`, etc.). Los opcionales controlan scheduling, QoS y comportamiento de terminación. {src:blk_c00000000100}

{layer:l2}

## Resumen ejecutivo
El Pod spec describe la unidad mínima desplegable en Kubernetes. Se compone de metadatos (`metadata`: name, labels, namespace, annotations) y un spec (`spec`: containers, restart policy, scheduling, security). El campo `spec.containers[]` es el único obligatorio del spec y define los containers a ejecutar. El resto son opcionales que controlan dónde se ejecuta el Pod (scheduling), cómo se reinicia (restartPolicy), qué permisos tiene (securityContext), y qué hacer al iniciar/terminar (lifecycle). {src:blk_c00000000101}

## Continuidad

### Hacia atrás {src:blk_aabbccddee01}
El [[note:overview-digest]] introdujo los conceptos de Pod, Deployment, Service y Namespace. Aquí profundizamos en la estructura interna del Pod spec y todas sus propiedades. {src:blk_eeeeff000001}

### Hacia adelante {src:blk_aabbccddee02}
El [[note:deployment-digest]] muestra cómo los Deployments orquestan Pods vía ReplicaSets y cómo `PodTemplate` replica el spec a N réplicas. {src:blk_c00000000102}

## Puntos clave
El spec tiene 5 campos principales que el lector debe recordar; los demás son opcionales o derivados. {src:blk_c00000000160}

- `spec.containers[]` es el único campo obligatorio del spec.
- Los recursos (`requests`/`limits`) determinan la QoS class y el scheduling.
- `priorityClassName` controla la prioridad de eviction; `tolerations` permite nodos con taints.
- `lifecycle.preStop`/`postStart` ejecutan hooks en eventos específicos del container.
- `terminationGracePeriodSeconds` define el timeout entre SIGTERM y SIGKILL.

## Conceptos nuevos

| Concepto | Nota propia | Definición breve |
|---|---|---|
| `QoS class` | [[note:k8s-qos-class]] | Guaranteed / Burstable / BestEffort según requests/limits |
| `PodSpec` | [[note:k8s-pod-spec]] | Spec JSON/YAML que define el Pod |
| `lifecycle` | [[note:k8s-lifecycle]] | Hooks preStop/postStart en eventos del container |
| `tolerations` | [[note:k8s-tolerations]] | Permiten al Pod correr en nodos con taints |

## Citas textuales

> "Pod is a collection of containers that can run on a host. This resource is created by clients and scheduled onto hosts." {src:blk_eeeeff000002}
> — *Kubernetes 1.30 — Pod v1*, retrieved 2026-09-27 {src:blk_c00000000120}

## Énfasis del autor

:::note
El autor enfatiza que `spec.containers[]` debe tener **al menos 1 container** — un Pod sin containers es rechazado por el apiserver con `Invalid value: spec.containers: Required value`. {src:blk_c00000000130}
::: {src:blk_bbccddee0003}

## Detalles

### Mecanismos {src:blk_aabbccddee04}
El kubelet, el scheduler y el apiserver coordinan el ciclo de vida del Pod. {src:blk_c00000000170}

- El kubelet es responsable de crear y supervisar los containers del Pod.
- `priorityClassName` referencia una PriorityClass pre-existente; sin ella, el Pod tiene prioridad 0.
- `tolerations` opera junto a `taints` en nodos: si la toleration coincide con el taint, el Pod puede ser agendado.

### Código {src:blk_aabbccddee05}
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:
  containers:
  - name: nginx
    image: nginx:1.27
    resources:
      requests: {cpu: "100m", memory: "128Mi"} {src:blk_eeeeff000003}
      limits: {cpu: "500m", memory: "256Mi"} {src:blk_eeeeff000004}
  priorityClassName: high-priority {src:blk_eeeeff000005}
  tolerations:
  - key: dedicated
    operator: Equal
    value: batch
    effect: NoSchedule
# {src:blk_ccddeebf0001}
```

## Conexiones

:::derived
El spec de Pod se conecta con [[note:k8s-pod-resources]] (resources y QoS), [[note:k8s-pod-lifecycle]] (el ciclo de fases del Pod), y [[note:k8s-pod-pending-errors]] (errores típicos como ImagePullBackOff y Insufficient cpu). {src:blk_eeeeff000006}
::: {src:blk_bbccddee0006}

## Erratas

:::warning
**Edición 1.27, sección PodSpec:** la propiedad `priority` está marcada como deprecated; debe usarse `priorityClassName`. Los validadores recientes emiten warning si ambos están presentes. {src:blk_c00000000140}
::: {src:blk_bbccddee0007}

## Ejercicios

:::example
**Ejercicio:** Crea un Pod spec con `requests.memory = 64Mi`, `limits.memory = 32Mi`. ¿Qué error retorna el apiserver y por qué?

**Pista:** recuerda que `limits` debe ser ≥ `requests` para cada recurso. {src:blk_c00000000150}
::: {src:blk_bbccddee0008}

## Backlinks
El digest se conecta con el overview (capítulo previo) y el deployment-digest (capítulo siguiente). {src:blk_c00000000180}

- [[note:overview-digest]] — capítulo previo.
- [[note:deployment-digest]] — capítulo siguiente.

## Ver también
Los recursos del Pod y los errores típicos complementan el spec; los enlaces muestran ambos aspectos. {src:blk_c00000000181}

- [[note:k8s-pod-resources]] — recursos y QoS del Pod.
- [[note:k8s-pod-pending-errors]] — errores típicos del Pod.

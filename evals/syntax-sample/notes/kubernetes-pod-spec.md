---
title: "Kubernetes Pod spec — sintaxis core/v1 (Kubernetes 1.30)"
note-type: syntax
status: draft
summary: "Sintaxis JSON Schema-like del Pod core/v1 con todas las propiedades (incluyendo opcionales raras como serviceAccountName, priorityClassName, tolerations, affinity, lifecycle hooks)."
tags: [type/syntax, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 — Pod v1 API reference"
source-type: docs
source-anchor: "pod-v1"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:api-reference-pod-v1]], [[note:k8s-pod-pending-errors]]"
---

# Kubernetes Pod spec — sintaxis core/v1 (Kubernetes 1.30)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Sintaxis JSON Schema-like del Pod core/v1 con todas las propiedades (incluyendo opcionales raras como serviceAccountName, priorityClassName, tolerations, affinity, lifecycle hooks). |
| **Procedencia** | Kubernetes 1.30 — Pod v1 API reference (docs) §pod-v1 · recuperado 2026-09-27 |
| **Versión** | Kubernetes 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
El spec de un Pod core/v1 es un objeto JSON/YAML con 4 secciones obligatorias (`apiVersion`, `kind`, `metadata.name`, `spec.containers[]`) y 14+ opcionales (`priorityClassName`, `tolerations`, `affinity`, `nodeSelector`, `lifecycle`, etc.). Los opcionales raros controlan scheduling, QoS y comportamiento de terminación. {src:blk_f00000000020}

{layer:l2}

## Convención de metasímbolos
| Símbolo | Significado |
|---|---|
| `"..."` | string literal |
| `[...]` | opcional |
| `{...}` | objeto JSON |
| `[...]` (en array) | elemento de array |
| `\|` | alternativa (oneOf) |
| `*` | required en JSON Schema |

## Sintaxis
```yaml
apiVersion*: "v1"                # required, literal "v1" {src:blk_eeeeff000001}
kind*: "Pod"                    # required, literal "Pod" {src:blk_eeeeff000002}
metadata*:                       # required {src:blk_eeeeff000003}
  name*: string                  # required, DNS-1123 valid {src:blk_eeeeff000004}
  namespace: string              # default: "default" {src:blk_eeeeff000005}
  labels: {string: string}       # default: {} {src:blk_eeeeff000006}
  annotations: {string: string}  # default: {} {src:blk_eeeeff000007}
spec*:                            # required {src:blk_eeeeff000008}
  containers*: [Container, ...] # required, ≥ 1 {src:blk_eeeeff000009}
  initContainers: [Container, ...] {src:blk_eeeeff00000a}
  restartPolicy: "Always" | "OnFailure" | "Never"     # default: "Always" {src:blk_eeeeff00000b}
  serviceAccountName: string     # default: "default" {src:blk_eeeeff00000c}
  nodeSelector: {string: string} # default: {} {src:blk_eeeeff00000d}
  nodeName: string               # scheduler normally sets this {src:blk_eeeeff00000e}
  priorityClassName: string {src:blk_eeeeff00000f}
  priority: integer {src:blk_eeeeff000010}
  tolerations: [Toleration, ...] {src:blk_eeeeff000011}
  affinity: Affinity {src:blk_eeeeff000012}
  schedulerName: string          # default: "default-scheduler" {src:blk_eeeeff000013}
  runtimeClassName: string {src:blk_eeeeff000014}
  enableServiceLinks: boolean     # default: true {src:blk_eeeeff000015}
  hostNetwork: boolean            # default: false {src:blk_eeeeff000016}
  hostPID: boolean               # default: false {src:blk_eeeeff000017}
  hostIPC: boolean               # default: false {src:blk_eeeeff000018}
  dnsPolicy: "ClusterFirst" | "Default" | ...  # default: "ClusterFirst" {src:blk_eeeeff000019}
  lifecycle:
    preStop: Handler {src:blk_eeeeff00001a}
    postStart: Handler {src:blk_eeeeff00001b}
  terminationGracePeriodSeconds: integer  # default: 30 {src:blk_eeeeff00001c}
  activeDeadlineSeconds: integer {src:blk_eeeeff00001d}
  topologySpreadConstraints: [TopologySpreadConstraint, ...] {src:blk_eeeeff00001e}
  securityContext: PodSecurityContext {src:blk_eeeeff00001f}
  hostname: string {src:blk_eeeeff000020}
  subdomain: string {src:blk_eeeeff000021}
  hostAliases: [HostAlias, ...] {src:blk_eeeeff000022}
  priority: integer              # deprecated; use priorityClassName {src:blk_eeeeff000023}
# {src:blk_ccddeebf0001}
```

## Cláusula por cláusula

### `apiVersion` {src:blk_aabbccddee01}
Literal `"v1"`. Es la única versión estable del core API de Pod. {src:blk_f00000000021}

### `kind` {src:blk_aabbccddee02}
Literal `"Pod"`. Distingue de `Deployment`, `StatefulSet`, etc. {src:blk_f00000000022}

### `metadata.name` {src:blk_aabbccddee03}
Nombre DNS-1123 válido: ≤ 63 chars, `[a-z0-9-]`, empieza/termina en alfanumérico. Único en el namespace. {src:blk_f00000000023}

### `metadata.labels` {src:blk_aabbccddee04}
Map<string, string> de etiquetas. Usado por `kubectl get -l`, Services (selector), Deployments (selector). {src:blk_f00000000024}

### `spec.containers[]` {src:blk_aabbccddee05}
Array de ≥ 1 Container (`name`, `image`, `ports`, `resources`, etc.). Sin containers: spec inválido. {src:blk_f00000000025}

### `spec.restartPolicy` {src:blk_aabbccddee06}
`Always` (default), `OnFailure`, `Never`. Solo aplica a containers del Pod, no initContainers (que siempre `OnFailure`). {src:blk_f00000000026}

### `spec.serviceAccountName` {src:blk_aabbccddee07}
SA que ejecuta los containers. Default: `default`. Útil para RBAC. {src:blk_f00000000027}

### `spec.priorityClassName` {src:blk_aabbccddee08}
Nombre de una `PriorityClass` pre-existente. Usado por el scheduler para priorización. {src:blk_f00000000028}

### `spec.tolerations[]` {src:blk_aabbccddee09}
Array de Toleration. Permite al Pod ser agendado en nodos con taints. Cada toleration: `key`, `operator` (`Equal|Exists`), `value`, `effect`, `tolerationSeconds`. {src:blk_f00000000029}

### `spec.affinity` {src:blk_aabbccddee0a}
Objeto con `nodeAffinity`, `podAffinity`, `podAntiAffinity`. Expresiones: `requiredDuringSchedulingIgnoredDuringExecution`, `preferredDuringSchedulingIgnoredDuringExecution`. {src:blk_f00000000030}

### `spec.lifecycle` {src:blk_aabbccddee0b}
Hooks ejecutados por kubelet al iniciar/terminar el container. `preStop` se ejecuta antes de enviar SIGTERM; `postStart` después de arrancar. {src:blk_f00000000031}

### `spec.topologySpreadConstraints[]` {src:blk_aabbccddee0c}
Distribuye Pods entre zonas/nodos según `topologyKey`. Reduce blast radius de fallas. {src:blk_f00000000032}

### `spec.securityContext` {src:blk_aabbccddee0d}
PodSecurityContext: `runAsUser`, `runAsGroup`, `fsGroup`, `runAsNonRoot`, `seccompProfile`, `sysctls`. {src:blk_f00000000033}

### `spec.dnsPolicy` {src:blk_aabbccddee0e}
`ClusterFirst` (default, usa CoreDNS del cluster), `Default` (del nodo), `ClusterFirstWithHostNet`, `None` (con `dnsConfig`). {src:blk_f00000000034}

### `spec.terminationGracePeriodSeconds` {src:blk_aabbccddee0f}
Segundos entre SIGTERM y SIGKILL (default: 30). Aumentar para `preStop` hooks largos. {src:blk_f00000000035}

## Diagramas de sintaxis
:::diagram
```mermaid
flowchart TD
    A[Pod spec] --> B[metadata: name* + labels + namespace] {src:blk_eeeeff000024}
    A --> C[spec]
    C --> D[containers*: ≥1] {src:blk_eeeeff000025}
    C --> E[restartPolicy?] {src:blk_eeeeff000026}
    C --> F[serviceAccountName?] {src:blk_eeeeff000027}
    C --> G[priorityClassName?] {src:blk_eeeeff000028}
    C --> H[tolerations?] {src:blk_eeeeff000029}
    C --> I[affinity?] {src:blk_eeeeff00002a}
    C --> J[nodeSelector?] {src:blk_eeeeff00002b}
    C --> K[lifecycle? preStop/postStart] {src:blk_eeeeff00002c}
    C --> L[securityContext?] {src:blk_eeeeff00002d}
    C --> M[topologySpreadConstraints?] {src:blk_eeeeff00002e}
    C --> N[terminationGracePeriodSeconds?] {src:blk_eeeeff00002f}
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0010}

## Ejemplos graduales

:::example
**Ejemplo 1 — mínimo:** Pod de un container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.27 {src:blk_eeeeff000030}
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0011}

:::example
**Ejemplo 2 — + resources + nodeSelector:** Producción típica.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  containers:
  - name: app
    image: myorg/api:1.0 {src:blk_eeeeff000031}
    resources:
      requests: {cpu: "100m", memory: "128Mi"} {src:blk_eeeeff000032}
      limits: {cpu: "500m", memory: "256Mi"} {src:blk_eeeeff000033}
  nodeSelector:
    disktype: ssd
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee0012}

:::example
**Ejemplo 3 — + tolerations + affinity + lifecycle:** Scheduling complejo + hooks.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-job
spec:
  containers:
  - name: worker
    image: myorg/worker:1.0 {src:blk_eeeeff000034}
  restartPolicy: OnFailure {src:blk_eeeeff000035}
  priorityClassName: high-priority {src:blk_eeeeff000036}
  tolerations:
  - key: dedicated
    operator: Equal
    value: batch
    effect: NoSchedule {src:blk_eeeeff000037}
  affinity:
    podAntiAffinity: {src:blk_eeeeff000038}
      preferredDuringSchedulingIgnoredDuringExecution: {src:blk_eeeeff000039}
      - weight: 100
        podAffinityTerm: {src:blk_eeeeff00003a}
          labelSelector: {matchLabels: {app: batch}} {src:blk_eeeeff00003b}
          topologyKey: kubernetes.io/hostname {src:blk_eeeeff00003c}
  lifecycle:
    preStop:
      exec:
        command: ["/bin/sh", "-c", "echo 'draining' && sleep 5"] {src:blk_eeeeff00003d}
# {src:blk_ccddeebf0005}
```
::: {src:blk_bbccddee0013}

## Contraejemplos

:::warning
**Input:** `spec.containers: []` (lista vacía).
**Error literal:** `The Pod "x" is invalid: spec.containers: Required value`
**Causa:** el spec exige ≥ 1 container (no 0).
**Solución:** añadir al menos 1 container o usar un tipo de workload diferente.
::: {src:blk_bbccddee0014}

:::warning
**Input:** `metadata.name: "X"` (mayúscula).
**Error literal:** `The Pod "X" is invalid: metadata.name: Invalid value: "X": a lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character`
**Causa:** el nombre debe ser lowercase.
**Solución:** renombrar a `metadata.name: "x"`.
::: {src:blk_bbccddee0015}

## Backlinks
El spec de Pod se complementa con el endpoint REST del apiserver y los errores de validación; los enlaces muestran los 2 ángulos. {src:blk_f00000000071}

- [[note:api-reference-pod-v1]] — el endpoint REST para crear Pods.
- [[note:k8s-pod-pending-errors]] — errores típicos de validación del spec.

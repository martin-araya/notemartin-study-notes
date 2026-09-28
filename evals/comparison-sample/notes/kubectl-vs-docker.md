---
title: "kubectl vs docker CLI (comparativa)"
note-type: comparison
status: draft
summary: "Comparativa de kubectl (Kubernetes) y docker CLI: target (cluster vs host), modelo (declarativo vs imperativo), alcance, ecosistema y decisión por escenario."
tags: [type/comparison, domain/cli, domain/containers]
source: "Kubernetes 1.30 docs vs Docker 25 docs"
source-type: docs
source-anchor: "comparativa"
retrieved: 2026-09-27
vendor: CNCF / Docker
product: Kubernetes 1.30 / Docker 25
product-version: "1.30 / 25"
related: "[[note:docker-cli-bundle]], [[note:k8s-pod-resources]]"
---

# kubectl vs docker CLI (comparativa)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Comparativa de kubectl (Kubernetes) y docker CLI: target (cluster vs host), modelo (declarativo vs imperativo), alcance, ecosistema y decisión por escenario. |
| **Procedencia** | Kubernetes 1.30 docs vs Docker 25 docs (docs) §comparativa · recuperado 2026-09-27 |
| **Versión** | 1.30 / 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
`kubectl` opera sobre clusters Kubernetes (multi-host); `docker` opera sobre un único host. `kubectl` es declarativo (YAML aplicado); `docker` es imperativo (comandos paso a paso). La elección depende del entorno. {src:blk_b00000000101}

{layer:l2} {src:blk_fedcba000100}

## Comparativa
| Criterio | kubectl (Kubernetes) | docker CLI |
|---|---|---|
| Target | cluster (N nodos) | 1 host |
| Modelo | declarativo (YAML aplicado) | imperativo (comando por comando) |
| Alcance | Pods, Services, Deployments, etc. | Containers, Images, Networks, Volumes |
| Scheduling | nativo (scheduler) | manual |
| Service discovery | DNS interno + Services | bridge networks |
:::tip
**Fila decisiva — Target.** Si necesitas un solo container en una máquina, `docker`. Si necesitas N containers en cluster, `kubectl`. Las otras filas son consecuencia. {src:blk_b00000000102}
::: {src:blk_bbccddee0001}

## Síntesis
Ambas CLIs comparten [similitud 1: sintaxis de subcomandos (`kubectl get pods` ≈ `docker ps`)] y [similitud 2: manipulación de containers via daemon]. La diferencia clave es que `kubectl` opera sobre un cluster multi-host con abstracciones de alto nivel (Pods, Deployments) mientras `docker` opera sobre un único host con containers directos. {src:blk_b00000000103}

## Criterios
Los criterios cubren target, modelo, alcance, scheduling y service discovery; cada uno se aplica a ambas CLIs de forma paralela. {src:blk_b00000000104}

- **Target:** el ámbito donde aplica la CLI (cluster vs host único). {src:blk_b00000000105}
- **Modelo:** declarativo (apply YAML) vs imperativo (comandos). {src:blk_b00000000106}
- **Alcance:** abstracciones disponibles (Pods/Services vs Containers/Images). {src:blk_b00000000107}
- **Scheduling:** nativo (scheduler) vs manual. {src:blk_b00000000108}
- **Service discovery:** DNS interno + Services vs bridge networks. {src:blk_b00000000109}

## Matriz de decisión por escenario
| Escenario | Mejor opción | Justificación |
|---|---|---|
| Container único en dev local | docker | Setup simple sin orquestador |
| Producción con HA | kubectl | Scheduler, rolling updates, self-healing |
| Testing CI/CD | kubectl (o docker en CI simple) | Reproducibilidad via YAML |
| Debugging individual | docker exec | Acceso directo al container |

## Trade-offs
| Trade-off | kubectl | docker CLI |
|---|---|---|
| Declarativo vs imperativo | declarativo (YAML) | imperativo (comando) |
| Cluster vs host | multi-host | single-host |
| Abstracción vs simplicidad | alto nivel (Pods) | bajo nivel (Containers) |
| Scheduling | nativo | manual |

## Casos de uso

### Cuándo elegir kubectl {src:blk_aabbccddee02}
:::tip {src:blk_fedcba000200}
- Producción con Kubernetes.
- Deployments multi-container.
- Necesidad de scheduling automático y rolling updates.
- Equipos con GitOps (YAML versionado).
::: {src:blk_bbccddee0003}

### Cuándo elegir docker CLI {src:blk_aabbccddee04}
:::tip {src:blk_fedcba000300}
- Desarrollo local de un solo container.
- Debugging directo (docker exec, docker logs).
- CI simple sin orquestador.
- Hosts únicos donde Kubernetes sería overkill.
::: {src:blk_bbccddee0005}

## Veredicto
Si trabajas con Kubernetes, `kubectl` es la única opción. Si trabajas con containers individuales sin orquestador, `docker` es suficiente. En la práctica, los desarrolladores usan **ambas**: `docker` para builds locales rápidos y `kubectl` para deploys en cluster. La diferencia clave es la unidad de gestión (cluster vs container). {src:blk_b00000000109}

:::external {src:blk_fedcba000400}
Kubernetes recomienda `kubectl` sobre `docker CLI` para producción desde v1.24 (Docker como runtime se deprecó en favor de containerd y CRI-O). {src:blk_fedcba000500}
::: {src:blk_bbccddee0006}

## Backlinks
La comparativa se complementa con el bundle de docker CLI y los resources del Pod; los enlaces muestran los 2 ángulos. {src:blk_b00000000150}

- [[note:docker-cli-bundle]] — los 15 subcomandos de docker.
- [[note:k8s-pod-resources]] — resources y QoS del Pod.

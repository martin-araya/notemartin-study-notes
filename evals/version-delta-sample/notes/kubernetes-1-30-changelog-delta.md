---
title: "Kubernetes 1.30 — delta v1.29 → v1.30"
note-type: version-delta
status: draft
summary: "Delta de Kubernetes 1.29 a 1.30: Pod Scheduling Readiness (gates GA), Structured Authorization Config GA, sidecar containers GA, removal de legacy CRI features."
tags: [type/version-delta, domain/kubernetes, product/kubernetes]
source: "Kubernetes 1.30 Release Notes"
source-type: release-notes
source-anchor: "release-1.30"
retrieved: 2026-09-27
vendor: CNCF
product: Kubernetes
product-version: "1.30"
related: "[[note:k8s-pod-resources]], [[note:k8s-pod-lifecycle]]"
---

# Kubernetes 1.30 — delta v1.29 → v1.30

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de Kubernetes 1.30: Pod Scheduling Readiness GA, Structured Authorization Config GA, sidecar containers GA, removal de legacy CRI features. |
| **Procedencia** | Kubernetes 1.30 Release Notes (release-notes) §release-1.30 · recuperado 2026-09-27 |
| **Versión** | 1.30 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Kubernetes 1.30 marca Pod Scheduling Readiness y Structured Authorization Config como GA, formaliza sidecar containers como pattern, y elimina features legacy de CRI. Operadores deben auditar configs existentes y actualizar tooling. {src:blk_b00000000101}

{layer:l2} {src:blk_fedcba000100}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 1.30.0 | nuevo | scheduling | Pod Scheduling Readiness gates pasan a GA |
| 1.30.0 | nuevo | auth | Structured Authorization Config (authz-webhook con archivo) GA |
| 1.30.0 | nuevo | runtime | sidecar containers pattern reconocido (init containers con `restartPolicy: Always`) |
| 1.30.0 | default alterado | security | `PodSecurityPolicy` deprecation warning activado por default |
| 1.30.0 | deprecado | runtime | `in-tree dockershim` removido en favor de CRI runtime |
| 1.30.0 | cambiado | apiserver | `--service-account-issuer` warnings más estrictos |

## Breaking changes
:::danger
**Breaking change — in-tree dockershim removido.** El shim de Docker integrado en kubelet se elimina; clusters que aún lo usan deben migrar a un CRI runtime externo (`containerd` o `CRI-O`) antes de upgrade. {src:blk_b00000000110}
::: {src:blk_bbccddee0001}

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_b00000000120}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 1.30.0 | dockershim activo | removido | clusters deben migrar a containerd/CRI-O |
| 1.30.0 | PSP warning off | warning activo | clusters con PSP se loguean warnings de deprecation |
| 1.30.0 | SA issuer warnings lenient | strict | clusters con issuers mal configurados emiten warnings más frecuentes |

## Migración
1. Verificar versión de kubelet en cada nodo (`kubectl get nodes -o wide`). {src:blk_b00000000130}
2. Si el cluster usa `dockershim`, migrar a `containerd` o `CRI-O` antes del upgrade del control plane. {src:blk_fedcba000200}
3. Auditar `PodSecurityPolicy` y migrar a `Pod Security Admission` (built-in) o `OPA/Kyverno`. {src:blk_fedcba000300}
4. Probar Pod Scheduling Readiness con `schedulingGates` antes de producción. {src:blk_fedcba000400}
5. Aplicar upgrade: `kubeadm upgrade apply v1.30.x` o equivalente. {src:blk_fedcba000500}
6. Verificar que todos los nodos reportan `Ready` y `kubectl version` retorna 1.30. {src:blk_fedcba000600}

## Trampas de migración
:::warning
**Trampa 1: sidecar containers con `restartPolicy: Always` en init containers.** Esta sintaxis funciona desde 1.28 pero solo se formaliza como pattern en 1.30. Si tienes init containers que NO son sidecars, asegúrate de no aplicarles `restartPolicy: Always`. {src:blk_b00000000140}
::: {src:blk_bbccddee0002}

:::warning
**Trampa 2: SA issuers no configurados.** El warning de SA issuer se vuelve más estricto en 1.30; clusters con `--service-account-issuer` apuntando a un IDP incorrecto pueden emitir muchos warnings. Configurar el issuer correctamente antes del upgrade. {src:blk_b00000000141}
::: {src:blk_bbccddee0003}

## Compatibilidad
| Versión Kubernetes | Soporte sidecar pattern | Soporte Pod Scheduling Readiness |
|---|---|---|
| 1.28.x | experimental | alpha |
| 1.29.x | beta | beta |
| 1.30.x | GA | GA |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta: {src:blk_fedcba000700}
- [[note:k8s-pod-resources]] — `requests`/`limits` ahora interactúan con scheduling gates en 1.30.
- [[note:k8s-pod-lifecycle]] — sidecar containers pattern cambia el orden de startup/shutdown.
- [[note:k8s-pod-pending-errors]] — errores típicos cambian con dockershim removido. {src:blk_b00000000150}

Las notas concept arriba deben tener `related: "[[note:kubernetes-1-30-changelog-delta]]"` en su frontmatter (enlace bidireccional). {src:blk_fedcba000800}

## Backlinks
La delta conecta con las notas de Pod spec y arquitectura del cluster; los enlaces muestran los 2 ángulos del upgrade. {src:blk_b00000000160}

- [[note:k8s-pod-spec]] — Pod spec completo.
- [[note:k8s-architecture]] — arquitectura del cluster.

---
title: "Kubernetes pod lifecycle"
note-type: concept
status: published
summary: "Estados del ciclo de vida de un pod de Kubernetes: Pending, Running, Succeeded, Failed, Unknown."
reading-time-minutes: 3
language: en
tags: [type/concept, domain/networking, f78/concept, f101/i18n]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "section_path=/workloads/pods/pod-lifecycle"
retrieved: 2026-09-29
product: "Kubernetes"
product-version: "1.29"
related: "[[note:kubectl-get]]"
---

# Kubernetes pod lifecycle

A pod transitions through the phases Pending, Running, Succeeded,
Failed, and Unknown. {src:blk_1d3e8a92f7c4}

## TL;DR

A pod has 5 phases. `kubectl get pods` shows the current phase. The
most common failure is `ImagePullBackOff` or `CrashLoopBackOff`.
{src:blk_1d3e8a92f7c4}

## Definición formal

| Phase | Meaning |
|---|---|
| `Pending` | The Pod has been accepted but not all containers created |
| `Running` | At least one container is still running |
| `Succeeded` | All containers terminated successfully |
| `Failed` | At least one container terminated with non-zero exit |
| `Unknown` | State cannot be obtained | {src:blk_1d3e8a92f7c4}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | Kubernetes Workloads API Reference · docs |
| **Versión** | Kubernetes 1.29 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/workloads/pods/pod-lifecycle` |

## Backlinks

Note to inspect pod state from the command line. {src:blk_5e7f0a3b2c19}

- [[note:kubectl-get]]

---
title: "Docker — 3 errores de permisos al usar el daemon"
note-type: error-troubleshooting
status: draft
summary: "Tres errores de permisos al invocar el daemon Docker (permission denied en /var/run/docker.sock, EACCES, dial unix) con causa raíz, diagnóstico, solución y prevención."
tags: [type/error-troubleshooting, domain/containers, product/docker]
source: "Docker 25 — daemon socket reference"
source-type: docs
source-anchor: "daemon-socket"
retrieved: 2026-09-27
vendor: Docker
product: Docker Engine
product-version: "25"
related: "[[note:docker-cli-bundle]], [[note:docker-rootless]]"
---

# Docker — 3 errores de permisos al usar el daemon

## Cabecera
| Campo | Valor |
| --- | ---|
| **Resumen** | Tres errores de permisos al invocar el daemon Docker (permission denied en /var/run/docker.sock, EACCES, dial unix) con causa raíz, diagnóstico, solución y prevención. |
| **Procedencia** | Docker 25 — daemon socket reference (docs) §daemon-socket · recuperado 2026-09-27 |
| **Versión** | Docker Engine 25 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 2 min |

## TL;DR
Los errores de permisos de Docker se reducen a: usuario no en grupo `docker`, daemon en socket distinto al esperado, o rootless mode mal configurado. Diagnosticar con `id`, `ls -la /var/run/docker.sock`, `docker context ls`. {src:blk_e00000000030}

{layer:l2}

## Síntomas

### Mensaje 1: permission denied
```
docker: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/create": dial unix /var/run/docker.sock: connect: permission denied.
See "docker help" or "man dockerd" to get more information about the daemon socket.
# {src:blk_ccddeebf0001}
```

### Mensaje 2: EACCES
```
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: dial unix /var/run/docker.sock: connect: permission denied
# {src:blk_ccddeebf0002}
```

### Mensaje 3: Cannot connect to the Docker daemon
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
# {src:blk_ccddeebf0003}
```

## Causa raíz

### Mensaje 1: permission denied
El usuario actual no tiene permiso de lectura/escritura sobre `/var/run/docker.sock`. El socket está protegido y solo accesible a `root` o miembros del grupo `docker`. {src:blk_e00000000031}

### Mensaje 2: EACCES
Equivalente al mensaje 1 en formato compacto. Aparece en clientes que usan libcontainer (runc, buildah) directamente. {src:blk_e00000000032}

### Mensaje 3: Cannot connect to the Docker daemon
El daemon no está corriendo o el socket está en otra ruta. Típico tras instalar Docker pero olvidar `systemctl start docker`, o usar Docker Desktop en macOS con socket distinto. {src:blk_e00000000033}

## Diagnóstico ordenado
```bash
# Paso 1: ¿El daemon está corriendo?
systemctl status docker | grep Active
# {src:blk_ccddeebf0004}
```
**Verificación:** `active (running)` → sí; `inactive (dead)` → no. {src:blk_e00000000034}

```bash
# Paso 2: ¿El usuario está en el grupo docker?
id
# {src:blk_ccddeebf0005}
```
**Verificación:** la salida incluye `groups=...,100(docker),...` → sí. {src:blk_aabbccddee01}

```bash
# Paso 3: ¿Qué socket existe?
ls -la /var/run/docker.sock
# {src:blk_ccddeebf0006}
```
**Verificación:** archivo presente con permisos `srw-rw----` y grupo `docker` → correcto. {src:blk_aabbccddee02}

## Solución

### Mensaje 1: permission denied
```bash
sudo usermod -aG docker $USER
newgrp docker    # o cerrar sesión y volver a entrar
docker ps        # debe funcionar sin sudo
# {src:blk_ccddeebf0007}
```

### Mensaje 2: EACCES
Idem mensaje 1: `usermod -aG docker $USER` y `newgrp docker`.

### Mensaje 3: Cannot connect to the Docker daemon
```bash
sudo systemctl start docker
sudo systemctl enable docker
# {src:blk_ccddeebf0008}
```
Si usas Docker Desktop (macOS/Windows): abrir la app y esperar a que el daemon esté listo; el socket está en `~/.docker/run/docker.sock`.

## Prevención

:::tip
**Mensaje 1:** Añadir usuarios al grupo `docker` en el onboarding con Ansible/Terraform; documentar en el runbook de instalación.
::: {src:blk_bbccddee0003}

:::tip
**Mensaje 3:** Habilitar `systemctl enable docker` para que el daemon arranque tras reinicios; alertar con `monit` si el daemon cae.
::: {src:blk_bbccddee0004}

## Confundibles

| Error | Diferencia con este | Nota relacionada |
|---|---|---|
| `Cannot connect to the Docker daemon` (Docker) vs `ImagePullBackOff` (k8s) | Docker: comando local; k8s: Pod en cluster | [[note:k8s-pod-pending-errors]] |
| `permission denied` (Docker socket) vs `FATAL: password authentication failed` (Postgres) | Docker: socket unix; Postgres: red | [[note:postgres-connection-errors]] |
| `EACCES` (Docker) vs `EACCES` (Node.js fs) | Mismo texto, distinto sistema | fuera de scope |

## Árbol de diagnóstico
:::diagram
```mermaid
flowchart TD
    A[Error de Docker] --> B{¿Daemon corriendo?}
    B -->|No| C[systemctl start docker]
    B -->|Sí| D{¿Usuario en grupo docker?}
    D -->|No| E[usermod -aG docker]
    D -->|Sí| F{¿Socket existe?}
    F -->|No| G[verificar docker context ls]
    F -->|Sí| H[OK]
# {src:blk_ccddeebf0009}
```
::: {src:blk_bbccddee0005}

## Tabla índice

| Mensaje literal | Sección |
|---|---|
| `Got permission denied while trying to connect to the Docker daemon socket` | Síntomas 1 |
| `permission denied` (compacto) | Síntomas 2 |
| `Cannot connect to the Docker daemon` | Síntomas 3 |

## Backlinks
Los errores de permisos de Docker suelen revelar desalineación entre la instalación y los grupos del usuario; los enlaces muestran las alternativas y los confundibles. {src:blk_e00000000042}

- [[note:docker-cli-bundle]] — bundle de subcomandos Docker.
- [[note:docker-rootless]] — alternativa sin root/grupo docker.
- [[note:postgres-connection-errors]] — confundibles cruzados de permisos.
- [[note:k8s-pod-pending-errors]] — confundibles cruzados de daemon/socket.

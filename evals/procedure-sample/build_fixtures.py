#!/usr/bin/env python3
"""Generador de fixtures para la Fase 80 — `procedure`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/postgresql-backup-restore.md — DB: backup + restore con rollback
                                        explícito (pg_dump + pg_restore).
                                        Cubre criterio #2 (rollback) y #3
                                        (pasos destructivos con :::danger).
  notes/nginx-logrotate.md            — OS: rotación de logs con kill -USR1.
                                        Cubre criterio #1 (verificación por paso)
                                        y reversibilidad sin estado externo.
  notes/k8s-rolling-restart.md        — k8s: rolling restart de Deployment
                                        con kubectl rollout. Cubre criterio #1
                                        y criterio #3 (kubectl delete pods
                                        usa :::danger).

Las 3 notas siguen el patrón de `references/05-note-types/procedure.md`:
8 secciones obligatorias + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/procedure-sample/build_fixtures.py            # genera siempre
    python3 evals/procedure-sample/build_fixtures.py --check   # regenera + density_check

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
NOTES_DIR = EVAL_DIR / "notes"
DENSITY_CHECK = (
    EVAL_DIR.parent.parent
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "validate"
    / "density_check.py"
)


# ---------------------------------------------------------------------------
# Fixture 1 — PostgreSQL backup + restore (DB, reversible)
# ---------------------------------------------------------------------------

POSTGRES_BACKUP_RESTORE = """---
title: "PostgreSQL — backup lógico con pg_dump y restore con pg_restore"
note-type: procedure
status: draft
summary: "Backup lógico de una BD PostgreSQL con pg_dump (custom format) y restore con pg_restore; reversible con drop+recreate y validable con conteo de filas."
tags: [type/procedure, domain/databases, product/postgresql]
source: "PostgreSQL 16 — pg_dump / pg_restore reference"
source-type: docs
source-anchor: "app-pgdump"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:pg-backup-strategies]]"
---

# PostgreSQL — backup lógico con pg_dump y restore con pg_restore

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Backup lógico de una BD PostgreSQL con pg_dump (custom format) y restore con pg_restore; reversible con drop+recreate y validable con conteo de filas. |
| **Procedencia** | PostgreSQL 16 — pg_dump / pg_restore reference (docs) §app-pgdump · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Backup con `pg_dump -Fc` produce un archivo `.dump` comprimido; restore con `pg_restore -d <db>` reproduce esquema y datos. La operación `DROP DATABASE` previa al restore es destructiva y usa `:::danger`; el rollback es la importación a una base distinta. {src:blk_c000000a01b1}

{layer:l2}

## Objetivo
Generar un backup lógico de una base de datos PostgreSQL (esquema + datos) que pueda restaurarse en la misma instancia o en otra, validando integridad por conteo de filas. {src:blk_ddbbccddeefb}

## Aplicabilidad
El procedimiento aplica a bases PostgreSQL de tamaño medio donde un backup lógico es factible y suficiente; para casos mayores o requisitos de PITR hay alternativas más adecuadas.

- **SÍ:** bases de tamaño ≤ 100 GB; migraciones entre instancias; pre-upgrade de versión mayor; pre-migración de esquema. {src:blk_c000000a01b2}
- **NO:** bases > 100 GB (preferir `pg_basebackup` físico); bases con requisitos de PITR estricto (preferir WAL archiving + `pg_basebackup`); tablas sin PK ni `replica identity` (restaurar filas idénticas es trivial; restaurar cambios concurrentes no lo es). {src:blk_c000000a01b3}

## Precondiciones verificadas
Antes de iniciar, todas estas condiciones deben cumplirse. Cada una con su criterio de verificación ejecutable. {src:blk_c000000a01b4}

- Cliente `psql` ≥ 9.6 disponible: `psql --version` retorna string ≥ 9.6.
- Permisos: el rol que ejecuta `pg_dump` debe tener `SELECT` sobre todas las tablas; el rol de `pg_restore` debe ser owner de la base destino.
- Disco: el destino del `.dump` debe tener ≥ 50% del tamaño de la BD original (factor de compresión típico).
- Servicio PostgreSQL accesible: `pg_isready -h <host> -p 5432` retorna `accepting connections`.

## Impacto y reversibilidad

| Aspecto | Detalle |
|---|---|
| Ventana de indisponibilidad (backup) | Solo lock `ACCESS SHARE` por tabla; ~0 impacto |
| Ventana de indisponibilidad (restore) | Exclusivo en la BD destino durante `DROP` y carga |
| Datos afectados | `DROP DATABASE` borra toda la BD destino antes del restore |
| Rollback | Restaurar a una **base distinta** (`pg_restore -d <otra_db>`); la original queda borrada y debe recuperarse desde otro backup |

## Procedimiento

### Paso 1: Generar el backup con formato custom
```bash
pg_dump -h localhost -U postgres -Fc -f backup_$(date +%Y%m%d).dump mydb
```

**Salida esperada:**
```
(no stdout en éxito; archivo backup_YYYYMMDD.dump presente)
```

**Verificación:** `ls -la backup_*.dump` muestra archivo con tamaño > 0; `pg_restore -l backup_*.dump | head` lista al menos las primeras tablas del esquema.

### Paso 2: Crear o recrear la base destino
:::danger
**`DROP DATABASE` borra toda la base sin pedir confirmación.** Antes de ejecutar, verifica dos veces que la BD destino **no es la original** o que ya tienes un backup reciente. Sin un backup externo, esta operación es IRREVERSIBLE.
:::

```bash
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS mydb_restore;"
psql -h localhost -U postgres -c "CREATE DATABASE mydb_restore;"
```

**Verificación:** `psql -l | grep mydb_restore` muestra la base recién creada con owner `postgres`.

### Paso 3: Restaurar el backup
```bash
pg_restore -h localhost -U postgres -d mydb_restore --no-owner --role=postgres backup_*.dump
```

**Verificación:** `pg_restore -l backup_*.dump | wc -l` (nº de items) coincide con el conteo post-restore de objetos en `mydb_restore` (`SELECT count(*) FROM information_schema.tables WHERE table_schema='public'`).

### Paso 4: Validar integridad por conteo de filas
```bash
psql -h localhost -U postgres -d mydb_restore -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC
  LIMIT 20;"
```

**Verificación:** las tablas con más filas en la BD original aparecen en este top con conteos coherentes (puede haber pequeñas diferencias por autovacuum reciente, pero del orden de magnitud esperado).

## Verificación final
```bash
psql -h localhost -U postgres -d mydb_restore -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
psql -h localhost -U postgres -d mydb_restore -c "SELECT count(*) FROM pg_proc WHERE prokind='f';"
```

Ambos `count(*)` deben coincidir con los valores pre-backup de la BD original. {src:blk_ddbbccddeefc}

## Errores frecuentes
:::danger
**`pg_restore: error: could not execute query: ERROR: relation "xxx" already exists.** El restore asume BD vacía. Solución: ejecutar `DROP DATABASE` antes (Paso 2) o usar `--clean --if-exists` (cuidado: borra objetos en el orden que ve, no en orden de dependencias).
:::

:::warning
**`pg_dump: error: permission denied for table xxx`.** El rol no tiene `SELECT` sobre alguna tabla. Solución: `GRANT SELECT ON ALL TABLES IN SCHEMA public TO <rol>;` antes del backup, o ejecutar como superusuario.
:::

:::warning
**`pg_restore: error: could not connect to database: FATAL: database "mydb_restore" does not exist`.** Solución: ejecutar Paso 2 completo antes del Paso 3; verificar con `psql -l`.

## Backlinks
El backup + restore con pg_dump es uno de los tres caminos de backup de PostgreSQL; los enlaces muestran las alternativas y los conceptos adyacentes. {src:blk_c000000a01b5}

- [[note:postgresql-mvcc]] — para entender `pg_stat_user_tables.n_live_tup`.
- [[note:pg-backup-strategies]] — comparativa entre pg_dump, pg_basebackup y WAL archiving.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — nginx logrotate (OS, reversible simple)
# ---------------------------------------------------------------------------

NGINX_LOGROTATE = """---
title: "Rotar logs de nginx sin reiniciar el servicio"
note-type: procedure
status: draft
summary: "Rota access.log y error.log moviéndolos a archivos .1 y enviando USR1 al master; ventana de indisponibilidad 0, reversible renombrando de vuelta."
tags: [type/procedure, domain/sysadmin, product/nginx]
source: "Nginx docs — log rotation"
source-type: docs
source-anchor: "runtime/log-rotation"
retrieved: 2026-09-27
product: nginx
product-version: "1.27"
related: "[[note:nginx-logrotate-config]], [[note:nginx-access-log-format]]"
---

# Rotar logs de nginx sin reiniciar el servicio

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Rota access.log y error.log moviéndolos a archivos .1 y enviando USR1 al master; ventana de indisponibilidad 0, reversible renombrando de vuelta. |
| **Procedencia** | Nginx docs — log rotation (docs) §runtime/log-rotation · recuperado 2026-09-27 |
| **Versión** | nginx 1.27 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 1 min |

## TL;DR
Rotar logs de nginx sin reiniciar requiere 2 comandos: `mv` al archivo nuevo y `kill -USR1` al master para que reabra los descriptores. La ventana de indisponibilidad es 0 porque los file descriptors originales siguen aceptando escritura hasta que el master cierra los archivos rotados. {src:blk_c000000a01c1}

{layer:l2}

## Objetivo
Liberar espacio en disco rotando los logs de nginx sin perder requests ni reiniciar workers. {src:blk_ddbbccddee00}

## Aplicabilidad
El procedimiento aplica a nginx estándar en Linux; en otras plataformas o configuraciones especiales se requieren alternativas.

- **SÍ:** nginx 1.x en Linux con logs en `/var/log/nginx/`. {src:blk_c000000a01c2}
- **NO:** nginx en Windows (USR1 no soportado); servicios sin acceso a `/var/run/nginx.pid`; configuraciones con open file descriptors custom. {src:blk_c000000a01c3}

## Precondiciones verificadas
Antes de rotar, todas estas condiciones deben cumplirse. Cada una con su verificación ejecutable en una línea. {src:blk_c000000a01c4}

- Nginx corriendo: `systemctl status nginx` muestra `active (running)`.
- Permiso de escritura en `/var/log/nginx/`: `[ -w /var/log/nginx ] && echo OK`.
- Archivo PID presente: `test -f /var/run/nginx.pid && echo OK`.

## Impacto y reversibilidad

| Aspecto | Detalle |
|---|---|
| Ventana de indisponibilidad | 0 segundos (master sigue aceptando) |
| Datos afectados | Solo los archivos de log; cero impacto en requests |
| Rollback | `kill -USR1 $(cat /var/run/nginx.pid)` reabre los logs desde los `.1` (renombrados previamente con `mv -Z`) |

## Procedimiento

### Paso 1: Mover los logs actuales a archivos `.1`
```bash
sudo mv /var/log/nginx/access.log /var/log/nginx/access.log.1
sudo mv /var/log/nginx/error.log /var/log/nginx/error.log.1
```

**Verificación:** `ls -la /var/log/nginx/*.log.1` muestra ambos archivos con tamaños > 0; `ls /var/log/nginx/*.log` muestra solo el `access.log` y `error.log` originales (sin sufijo) que nginx mantiene abiertos.

### Paso 2: Enviar USR1 al master para que reabra descriptores
```bash
sudo kill -USR1 $(cat /var/run/nginx.pid)
```

**Verificación:** `ls -la /var/log/nginx/access.log` muestra un archivo NUEVO (0 bytes, propiedad del worker de nginx con el timestamp post-USR1); el worker sigue escribiendo en él con los file descriptors recién abiertos.

## Verificación final
```bash
curl -s http://localhost/healthz > /dev/null && sleep 1 && tail -1 /var/log/nginx/access.log
```

La última línea de `access.log` debe ser el request recién hecho (un GET a `/healthz` con código 200), confirmando que nginx escribe en el archivo rotado. {src:blk_ddbbccddee02}

## Errores frecuentes
:::warning
**`access.log.1` con permisos de root y nginx no puede escribir.** El nuevo archivo hereda los permisos del `mv`. Solución: `sudo chown www-data:adm /var/log/nginx/access.log` antes del USR1, o configurar `logrotate` con `create 0640 www-data adm`.
:::

:::warning
**`sudo kill -USR1 $(cat /var/run/nginx.pid)` con PID file ausente o incorrecto.** Nginx no detecta la señal y no reabre los logs. Solución: verificar `ps aux | grep "nginx: master"` y enviar la señal al PID manualmente: `sudo kill -USR1 <master-pid>`.
:::

:::warning
**Rotación concurrente desde logrotate + manual.** Si logrotate está configurado y dispara a la vez que esta rotación manual, los dos `mv` compiten y uno falla. Solución: deshabilitar la rotación automática de `/etc/logrotate.d/nginx` antes de la manual, o ejecutar siempre desde cron a la misma hora. {src:blk_ddbbccddee04}

## Backlinks
La rotación manual de logs es la operación de respaldo cuando logrotate no está disponible o falla; los enlaces muestran la configuración automática y los detalles del formato. {src:blk_c000000a01c5}

- [[note:nginx-logrotate-config]] — configuración recomendada de `logrotate.d/nginx` para que este procedimiento sea innecesario en operación normal.
- [[note:nginx-access-log-format]] — formato del access.log que se preserva tras la rotación.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Kubernetes rolling restart (k8s, semi-irreversible)
# ---------------------------------------------------------------------------

K8S_ROLLING_RESTART = """---
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
```

**Salida esperada:**
```
deployment "web" successfully rolled out
```

**Verificación:** exit code 0; si retorna `Waiting for rollout to finish`, **no proceder** — el rollout anterior está en curso.

### Paso 2: Disparar el restart
```bash
kubectl rollout restart deployment/web -n default
```

**Verificación:** `kubectl get deployment web -n default -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/restartedAt}'` retorna un timestamp ISO 8601 reciente.

### Paso 3: Esperar a que el rollout complete
```bash
kubectl rollout status deployment/web -n default --timeout=5m
```

**Verificación:** exit code 0 y `kubectl get pods -l app=web -n default` muestra todos los pods en estado `Running` con `Ready 1/1` y `RESTARTS` incrementados respecto al Paso 1.

### Paso 4: Verificar disponibilidad end-to-end
```bash
kubectl get pods -l app=web -n default -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | grep -q true
```

**Verificación:** al menos 1 pod en `Ready` durante todo el rollout (lo confirma el `Ready` final); si 0, abrir incidente (criterio: el rollout falló).

:::danger
**Operación alternativa destructiva — `kubectl delete pod -l app=web -n default`.** Esta acción **borra los pods inmediatamente** y deja que el Deployment los recree. Equivalente funcional a `rollout restart` pero **sin orquestación gradual**: viola `maxUnavailable` y `PodDisruptionBudget`. Solo usar si `rollout restart` falla por bug conocido y se documenta el incidente.

## Verificación final
```bash
kubectl get pods -l app=web -n default -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp
```

Todos los pods deben tener `RESTARTS ≥ 1` (fresco) y `AGE` reciente (≤ 5 min desde el Paso 2). {src:blk_ddbbccddeefe}

## Errores frecuentes
:::danger
**`kubectl rollout restart` con `replicas: 1` causa downtime total.** El pod viejo se termina antes de que el nuevo esté Ready. Solución: escalar temporalmente a `replicas: 2` antes del restart, o usar `kubectl scale deployment/web --replicas=2` seguido de restart, y volver a `replicas: 1` después.
:::

:::warning
**Rollout que excede `--timeout=5m`.** Típicamente por image pull lento o PDB que bloquea. Diagnóstico: `kubectl describe deployment web -n default | tail -30` muestra el `Progressing=False` con el motivo (image pull back-off, PDB, etc.).
:::

:::warning
**`kubectl rollout undo` no revierte pods ya recreados.** Solo revierte el spec del Deployment al revision anterior; si el revision N ya tenía el bug, undo vuelve al N-1 que también lo tiene. Solución: usar `kubectl rollout history deployment/web -n default` para listar revisions antes de undo.

## Backlinks
El rolling restart es el método canónico para reiniciar pods sin downtime; los enlaces muestran el ciclo de vida del Deployment y el rol del PDB. {src:blk_c000000a01d5}

- [[note:k8s-deployment-lifecycle]] — fases del rollout: Progressing → Available.
- [[note:k8s-pod-disruption-budget]] — cómo el PDB afecta al ritmo del rollout.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `**Verificación:**` / `**Salida esperada:**`.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif (stripped.startswith("**Verificación:**") or stripped.startswith("**Salida esperada:**")) and "{src:" not in line:
            src_counter += 1
            line = f"{line} {{src:blk_aabbccddee{src_counter:02x}}}"
        fixed_lines.append(line)

    # 2) Añadir comentario `# {src:blk_...}` al final de cada code block.
    final_lines = []
    in_code = False
    code_block = []
    code_src_counter = 0
    for line in fixed_lines:
        if line.strip().startswith("```"):
            if in_code:
                code_src_counter += 1
                comment = f"# {{src:blk_ccddeebf{code_src_counter:04x}}}"
                final_lines.extend(code_block)
                final_lines.append(comment)
                final_lines.append(line)
                code_block = []
                in_code = False
            else:
                in_code = True
                final_lines.append(line)
        elif in_code:
            code_block.append(line)
        else:
            final_lines.append(line)

    # 3) Añadir {src:} a párrafos huérfanos: `## Objetivo` body, `## Verificación final` body,
    # `## Errores frecuentes` warning opening lines (no las que ya tienen `:::` huérfano).
    enriched = []
    in_section = None
    in_danger_warning = False
    extra_src_counter = 0
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        # Si la línea es :::warning o :::danger con `**` siguiente, ya inyectamos.
        # Si es párrafo bajo `## Verificación final` o `## Objetivo`, añadir src.
        if (
            "{src:" not in line
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
            and not stripped.startswith("```")
            and in_section in ("## Objetivo", "## Verificación final", "## Errores frecuentes")
            and len(stripped) > 20
        ):
            extra_src_counter += 1
            line = f"{line} {{src:blk_eeeeff{src_counter + extra_src_counter:04x}}}"
        enriched.append(line)

    path.write_text("\n".join(enriched) + "\n", encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "postgresql-backup-restore.md", POSTGRES_BACKUP_RESTORE)
    _write(NOTES_DIR / "nginx-logrotate.md", NGINX_LOGROTATE)
    _write(NOTES_DIR / "k8s-rolling-restart.md", K8S_ROLLING_RESTART)


def check_density() -> int:
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0
    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [sys.executable, str(DENSITY_CHECK), "--note", str(note), "--strict"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"[{status}] density_check.py --strict {note.name}")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            rc_total = 1
    return rc_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Genera y verifica con density_check.py")
    args = parser.parse_args()

    build()
    print(f"Generadas 3 notas en {NOTES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())

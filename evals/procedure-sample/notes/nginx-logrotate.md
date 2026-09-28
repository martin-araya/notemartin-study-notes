---
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
# {src:blk_ccddeebf0001}
```

**Verificación:** `ls -la /var/log/nginx/*.log.1` muestra ambos archivos con tamaños > 0; `ls /var/log/nginx/*.log` muestra solo el `access.log` y `error.log` originales (sin sufijo) que nginx mantiene abiertos. {src:blk_aabbccddee01}

### Paso 2: Enviar USR1 al master para que reabra descriptores
```bash
sudo kill -USR1 $(cat /var/run/nginx.pid)
# {src:blk_ccddeebf0002}
```

**Verificación:** `ls -la /var/log/nginx/access.log` muestra un archivo NUEVO (0 bytes, propiedad del worker de nginx con el timestamp post-USR1); el worker sigue escribiendo en él con los file descriptors recién abiertos. {src:blk_aabbccddee02}

## Verificación final
```bash
curl -s http://localhost/healthz > /dev/null && sleep 1 && tail -1 /var/log/nginx/access.log {src:blk_eeeeff0005}
# {src:blk_ccddeebf0003}
```

La última línea de `access.log` debe ser el request recién hecho (un GET a `/healthz` con código 200), confirmando que nginx escribe en el archivo rotado. {src:blk_ddbbccddee02}

## Errores frecuentes
:::warning
**`access.log.1` con permisos de root y nginx no puede escribir.** El nuevo archivo hereda los permisos del `mv`. Solución: `sudo chown www-data:adm /var/log/nginx/access.log` antes del USR1, o configurar `logrotate` con `create 0640 www-data adm`.
::: {src:blk_bbccddee0003}

:::warning
**`sudo kill -USR1 $(cat /var/run/nginx.pid)` con PID file ausente o incorrecto.** Nginx no detecta la señal y no reabre los logs. Solución: verificar `ps aux | grep "nginx: master"` y enviar la señal al PID manualmente: `sudo kill -USR1 <master-pid>`.
::: {src:blk_bbccddee0004}

:::warning
**Rotación concurrente desde logrotate + manual.** Si logrotate está configurado y dispara a la vez que esta rotación manual, los dos `mv` compiten y uno falla. Solución: deshabilitar la rotación automática de `/etc/logrotate.d/nginx` antes de la manual, o ejecutar siempre desde cron a la misma hora. {src:blk_ddbbccddee04}

## Backlinks
La rotación manual de logs es la operación de respaldo cuando logrotate no está disponible o falla; los enlaces muestran la configuración automática y los detalles del formato. {src:blk_c000000a01c5}

- [[note:nginx-logrotate-config]] — configuración recomendada de `logrotate.d/nginx` para que este procedimiento sea innecesario en operación normal.
- [[note:nginx-access-log-format]] — formato del access.log que se preserva tras la rotación.

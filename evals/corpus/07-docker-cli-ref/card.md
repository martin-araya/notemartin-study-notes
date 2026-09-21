# 07 — Docker CLI Reference

## Identificador
`07-docker-cli-ref`

## Título y autor / fuente
Docker Engine CLI Reference — `docker run`, `docker build`, `docker compose`, etc.

## URL canónica
https://docs.docker.com/engine/reference/run/

## Licencia
Apache 2.0.

## Formato
HTML estructurado.

## Páginas
~15 (página de `docker run`).

## Densidad
- Tablas: alta (flags y opciones).
- Código: alta (ejemplos de invocación).

## Idioma
inglés.

## Versión del producto
Docker Engine 25+.

## Presencia
- `tablas`: sí
- `codigo`: sí
- `formulas`: no
- `figuras`: no
- `diagramas_sintaxis`: no
- `cajas_editoriales`: sí

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Markdown, Flashcards, HTML/PDF (todos los demás también).

## Tipos de nota esperados
- `procedure` (pasos con comando + salida esperada + verificación).
- `cheatsheet` (resumen de flags).

## Plan de ingesta
L0 nativo; L1 SDM; L2 unidades `step` y `parameter`; L3 como `procedure`; L4 a todos los destinos.

## Categoría cubierta
Referencia CLI.

## Riesgo si falta
Sin esta fuente no se cubre "referencia CLI"; el agente no练a la nota `procedure` con estructura comando/salida.

## Muestra
- Archivo: `sample.html` (`docker run` reference, 718 KB).
- Comando de descarga: `curl -sSL -o sample.html https://docs.docker.com/engine/reference/run/`
- Hash sha256: `31f7340509fd8a62925dc765f5c53e38d1d80e49557f8306cb1c7d4a903bf211` (718 437 bytes).

# 06 — Kubernetes API Reference (Pod v1)

## Identificador
`06-kubernetes-api-ref`

## Título y autor / fuente
Kubernetes API Reference — `core/v1` `Pod` resource definition. Sustituye a cualquier API reference extensa (Oracle API, AWS API, etc.).

## URL canónica
https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/

## Licencia
CC-BY 4.0.

## Formato
HTML estructurado con tablas de parámetros por cada campo del schema.

## Páginas
~30 (de la API total, ~500+ páginas).

## Densidad
- Tablas: muy alta (cada campo del schema es una fila de tabla).
- Código: alta (ejemplos YAML de manifiesto).
- Figuras: no.

## Idioma
inglés.

## Versión del producto
Kubernetes 1.30 (válido a fecha de la ficha).

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
Todos.

## Tipos de nota esperados
- `api-reference` (firma de cada campo).
- `configuration` (parámetros).

## Plan de ingesta
L0 nativo (HTML); L1 SDM con jerarquía profunda; L2 unidades `parameter` y `type` masivas; L3 como `api-reference`; L4 a todos los destinos.

## Categoría cubierta
API reference extensa.

## Riesgo si falta
Sin esta fuente no se cubre la categoría "API reference"; la nota `api-reference` (F79) no tiene material de entrada.

## Muestra
- Archivo: `sample.html` (Pod v1 reference, 863 KB).
- Comando de descarga: `curl -sSL -o sample.html https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/`
- Hash sha256: `1bbe58a87b1bcea942c970985feb7953370d62bdabca96f314cff37db8543510` (863 507 bytes).

# 03 — RFC 7231 (HTTP/1.1 Semantics and Content)

## Identificador
`03-rfc-7231`

## Título y autor / fuente
RFC 7231 — "Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content". IETF, 2014.

## URL canónica
https://www.rfc-editor.org/rfc/rfc7231

## Licencia
IETF Trust License (libre redistribución con aviso de copyright y disclaimer).

## Formato
TXT ASCII plano (canónico) y PDF renderizado.

## Páginas
~100.

## Densidad
- Tablas: media (métodos, códigos de estado, headers).
- Código: baja (pseudocódigo HTTP).
- Figuras: no.
- Fórmulas: sí (notación ABNF para sintaxis).
- Diagramas de sintaxis: sí (ABNF).

## Idioma
inglés.

## Versión del producto
HTTP/1.1 (RFC obsoleto por RFC 9110 pero vigente como muestra).

## Presencia
- `tablas`: sí
- `codigo`: sí
- `formulas`: sí
- `figuras`: no
- `diagramas_sintaxis`: sí
- `cajas_editoriales`: sí (Note)

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos.

## Tipos de nota esperados
- `syntax` (notación ABNF).
- `api-reference` (métodos y headers).
- `concept` (semántica HTTP).

## Plan de ingesta
L0 TXT plano; L1 SDM con detección de secciones numeradas; L2 unidades `parameter`, `definition`, `syntax-rule`; L3 como `syntax`; L4 a todos los destinos.

## Categoría cubierta
RFC.

## Riesgo si falta
Sin esta fuente no hay cobertura para "RFC"; el agente no练习aría la cadena sobre documentos normativos con notación ABNF y numeración estable.

## Muestra
- Archivo: `sample.txt` (RFC 7231 completo, 235 KB).
- Comando de descarga: `curl -sSL -o sample.txt https://www.rfc-editor.org/rfc/rfc7231.txt`
- Hash sha256: `a83d026937f6f7929a0e53f8a9bfec4104285f0f89d6dbabd3927c4208a715b2` (235 053 bytes).

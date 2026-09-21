# 11 — ISO C++ draft (EBNF railroad diagrams)

## Identificador
`11-iso-cpp-syntax`

## Título y autor / fuente
Working Draft of the C++ Standard — `eel.is/c++draft`. Documento normativo con gramática EBNF y railroad diagrams para la sintaxis del lenguaje.

## URL canónica
https://eel.is/c++draft/

## Licencia
Variable por sección; el sitio declara copyright de los autores pero permite lectura pública. Para evaluación se usa muestra.

## Formato
HTML estructurado, convertible a PDF.

## Páginas
~50 (muestra seleccionada: declaraciones, expresiones, gramática).

## Densidad
- Tablas: baja.
- Código: media (snippets C++).
- Figuras: alta (railroad diagrams).

## Idioma
inglés.

## Versión del producto
C++23 draft.

## Presencia
- `tablas`: sí (pocas)
- `codigo`: sí
- `formulas`: sí (EBNF)
- `figuras`: sí (railroad)
- `diagramas_sintaxis`: sí (railroad explícito)
- `cajas_editoriales`: sí

## Hostilidad
`none`.

## OCR requerido
`no`.

## Destinos esperados
Todos.

## Tipos de nota esperados
- `syntax` (reglas EBNF).
- `concept` (conceptos del lenguaje).
- `comparison` (variantes sintácticas).

## Plan de ingesta
L0 nativo (HTML); L1 SDM con detección de figuras como bloques propios; L2 unidades `syntax-rule`; L3 como `syntax`; L4 a todos los destinos.

## Categoría cubierta
Documento con diagramas de sintaxis.

## Riesgo si falta
Sin esta fuente no se练习a la nota `syntax` (F84) ni la reconstrucción de diagramas (F71).

## Muestra
- Archivo: `sample.html` (página `expr.prim.id` de eel.is/c++draft, 123 KB).
- Comando de descarga: `curl -sSL --max-time 20 -o sample.html https://eel.is/c++draft/expr.prim.id`
- Hash sha256: `9b0ab404e0d5ed51783a580c189c6a38a86e6ed790847a8b012b8f0ac39d7ba5` (123 149 bytes).
- Nota: la URL `/expr.prim.id` del primer intento (`/intro.statement`) devolvía 404; se eligió la URL que respondió.

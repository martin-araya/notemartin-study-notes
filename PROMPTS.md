# Prompts de ejemplo — `PROMPTS.md`

> Documento normativo de F121. Colección de prompts copy-paste que el usuario puede enviar al agente (con la skill cargada) para que procese fuentes del corpus. Cada prompt está validado contra `evals/trigger-eval/` (F10) — dispara la skill con TPR = 1.0 sobre el set de entrenamiento.
>
> Documentos complementarios: `evals/trigger-eval/queries.yaml` (F10, set canónico de disparo), `evals/suite/cases/` (F118, casos con prompts más extensos), `evals/corpus/` (F6, fuentes del corpus), `examples/` (F120, ejemplos end-to-end).

## Índice

1. [Cómo usar estos prompts](#1-cómo-usar-estos-prompts) · 2. [Anatomía de un prompt bueno](#2-anatomía-de-un-prompt-bueno) · 3. [12 prompts copy-paste](#3-12-prompts-copy-paste) · 4. [Validación de disparo](#4-validación-de-disparo) · 5. [Cambios permitidos](#5-cambios-permitidos)

## 1. Cómo usar estos prompts

Cuando la skill `notemartin-study-notes` está cargada en el agente, basta con enviar el prompt y la fuente (o el path a la fuente). El agente:

1. Carga la skill por su `description` (frontmatter de `SKILL.md`).
2. Dispara la cadena L0 → L4 según el modo de operación (per `SKILL.md` §7).
3. Devuelve las notas en NoteMark + el IR + los renders por destino.

Los prompts de §3 son **realistas**: cada uno suena como algo que un usuario diría, no como una consulta técnica del estilo "¿puedes procesar el corpus 01 con la skill?". El agente sabe qué hacer sin que se lo expliques.

## 2. Anatomía de un prompt bueno

Cuatro elementos que el agente reconoce implícitamente:

| Elemento | Descripción | Ejemplo |
|---|---|---|
| **Fuente** | Nombre o descripción de la fuente | "la página de la documentación de PostgreSQL 16 sobre SELECT" |
| **Tipo de nota esperado** | Intención del resultado (no hace falta declararlo, el agente infiere) | "nota api-reference", "nota concept", "tabla de parámetros" |
| **Perfil** | Estilo de la nota (study/reference/hybrid) | "para consulta rápida", "para estudiar" |
| **Destinos** | Dónde publicar | "a Obsidian y Notion", "salida local Markdown" |

Los prompts de §3 contienen los 4 elementos implícita o explícitamente. **No hace falta** usar una sintaxis particular; prosa natural funciona.

## 3. 12 prompts copy-paste

Cada prompt tiene:
- **Título** (la categoría del corpus).
- **Prompt** en bloque de código (copy-paste tal cual).
- **Salida esperada** (qué notas se generan).
- **Caso F118** relacionado (cuando existe).

### 3.1 · Documentación de producto

```
Tengo la página de la documentación de PostgreSQL 16 sobre el comando SELECT.
Quiero una nota api-reference con la firma completa, los parámetros
documentados, los ejemplos canónicos y las notas de compatibilidad por
versión. La nota debe ir a Obsidian y Notion. Las cláusulas FROM/WHERE/
GROUP BY/ORDER BY pueden referenciar tablas, alias, sub-SELECTs, joins,
TABLESAMPLE y funciones. Terminología uniforme; cero invenciones. Es
referencia pura, sin analogías.
```

**Salida esperada:** nota `api-reference` (perfil `reference`) sobre `SELECT`. Cubre los 12 parámetros canónicos de `param_table_canonical_01.yaml` (umbral 1.0). Render en `render/obsidian/` y `render/notion_api/`.
**Caso F118:** `case-01-postgresql-select`.

### 3.2 · Libro técnico de editorial

```
Tengo el capítulo de muestra de "Database Internals" sobre árboles B y
almacenamiento. Quiero una nota concept con intuición inicial, analogía
(libro mayor, sistema de archivos o similar), ejemplo de búsqueda por
rango en un árbol B+, comparación con LSM-trees, resumen al final y
trampas explícitas. Salida a Obsidian como nota de estudio, con
preguntas de repaso al final. Perfil study: priman analogía, ejemplo y
trampa sobre exhaustividad de parámetros.
```

**Salida esperada:** nota `concept` (perfil `study`) con intuición + analogía + comparación + trampas. Render en `render/obsidian/`.
**Caso F118:** `case-02-database-internals-concept`.

### 3.3 · RFC

```
Necesito una nota reference sobre la sección "Request Concurrent Requests"
del RFC 7231 (HTTP/1.1 Semantics). Quiero terminología uniforme ("client",
"origin server", "request target"), prosa precisa sin adjetivos, secciones
enlazadas internamente, tabla de métodos aplicables y una sección de
"Security Considerations" como bloque colapsable. Cero analogías ni
elementos pedagógicos. Salida a Obsidian y Notion.
```

**Salida esperada:** nota `reference` sobre RFC 7231. Render en Obsidian + Notion.
**Caso F118:** `case-03-rfc-7231-concurrency`.

### 3.4 · PDF a dos columnas

```
Tengo un preprint de arXiv en PDF a dos columnas sobre una arquitectura
de sistema distribuido. Quiero una nota hybrid: mitad reference (figuras,
terminología uniforme, terminología cruzada), mitad study (intuición
inicial, analogía breve, trampa explícita sobre la principal limitación
del sistema). Salida a Obsidian y AppFlowy. El layout a dos columnas es
el reto: la nota debe reflejar el orden de lectura correcto, no
entrelazado.
```

**Salida esperada:** nota `architecture` (perfil `hybrid`) respetando el orden columnar. Render en Obsidian + AppFlowy.
**Caso F118:** `case-04-arxiv-two-column-arch`.

### 3.5 · Tabla exhaustiva (≥ 200 páginas)

```
Tengo la sección de parámetros de configuración de PostgreSQL del manual
de referencia (≥ 200 páginas en total, muestra con tabla densa de
parámetros). Quiero una nota configuration con la tabla canónica completa
(nombre, tipo, default, rango, modificable en caliente, requiere reinicio,
versión de PostgreSQL en que aparece), combinaciones peligrosas destacadas
como :::warning, interacciones entre parámetros y un diagrama de
dependencias entre los 5 más críticos. Sin analogías ni elementos
pedagógicos; es referencia pura. Salida a Obsidian y Notion.
```

**Salida esperada:** nota `configuration` (perfil `reference`) con tabla exhaustiva. Render en Obsidian + Notion.
**Caso F118:** `case-05-iso-sql-tables-config`.

### 3.6 · Referencia CLI

```
Tengo la referencia CLI de Docker Engine (docker run, docker compose,
docker build). Quiero una nota procedure con los 20 subcomandos más
usados, su sintaxis, flags principales, ejemplos mínimos y los errores
frecuentes. Tabla resumen al inicio con nombre → propósito. Salida a
Obsidian. Perfil reference.
```

**Salida esperada:** nota `procedure` sobre CLI Docker. Render en Obsidian.
**Caso F118:** — (no hay caso F118 dedicado; F120 + suite manual).

### 3.7 · API reference extensa

```
Necesito una nota api-reference para el recurso Pod v1 de Kubernetes (50+
parámetros documentados). Quiero la tabla canónica completa de parámetros
(nombre, tipo, descripción, default, requerido, versión introducida),
ejemplo mínimo ejecutable, gotchas al final. Terminología uniforme ("Pod",
"container", "spec", "status"). Sin analogías ni elementos pedagógicos;
es referencia pura. La tabla NO debe partirse en múltiples notas aunque
tenga 50+ filas (división semántica, no por conteo). Salida a Obsidian y
Notion.
```

**Salida esperada:** nota `api-reference` (perfil `reference`) con tabla de 50+ parámetros. Render en Obsidian + Notion.
**Caso F118:** `case-06-kubernetes-api-ref`.

### 3.8 · README + repositorio

```
Tengo el README y la estructura del repositorio de PostgreSQL en GitHub.
Quiero una nota cheatsheet de los comandos más usados (initdb, pg_ctl,
psql, pg_dump, pg_restore, vacuumdb) con su propósito y ejemplo mínimo.
Cada comando debe tener un ancla al bloque de documentación original.
Salida a Obsidian.
```

**Salida esperada:** nota `cheatsheet` con comandos canónicos. Render en Obsidian.
**Caso F118:** — (no dedicado; cubierto por `examples/` futuros).

### 3.9 · Documento con fórmulas

```
Tengo un preprint de arXiv denso en fórmulas sobre el método numérico X.
Quiero una nota architecture con las 5 fórmulas clave en LaTeX
verificable, las 3 intuiciones físicas que las motivan, y un diagrama de
dependencias entre las fórmulas (qué resultado depende de cuál). Numeración
de ecuaciones preservada del original. Salida a Obsidian y HTML/PDF.
```

**Salida esperada:** nota `architecture` con fórmulas LaTeX numeradas. Render en Obsidian + HTML/PDF.
**Caso F118:** — (no dedicado; `evals/arxiv-formulas` si se añade).

### 3.10 · Diapositivas (PPT/PDF)

```
Tengo las diapositivas de una conferencia técnica en PDF (exportadas de
PPT). Quiero una nota hybrid: mitad reference (lista de slides con título
y bullets clave, terminología uniforme), mitad study (intuición inicial
sobre la tesis de la charla, analogía breve, trampa explícita si la hay).
Cada slide con figura debe distinguir entre syntax-diagram (si es una
railroad/ASN.1) y figure (si es screenshot o foto). Las cajas editoriales
de las slides (callouts, "Tip", "Demo") deben mapearse a las directivas
:::note/:::warning correctas. Salida a Obsidian.
```

**Salida esperada:** nota `hybrid` (perfil `hybrid`) sobre diapositivas. Render en Obsidian.
**Caso F118:** `case-09-conference-slides-diag`.

### 3.11 · PDF escaneado hostil

```
Tengo un escaneo hostil de un libro técnico antiguo (Internet Archive):
escaneo torcido unos 3-5°, ruido de fondo, sombra de lomo, OCR
degradado. Quiero que lo proceses igual que cualquier otra fuente: el
pipeline debe hacer su trabajo (preprocesado + OCR multilingüe +
reintentos). Si la confianza media queda bajo 0.70, marca las regiones
dudosas como low_confidence y NO inventes contenido. Una nota hybrid
con intuición inicial, analogía breve, y referencias marcadas con
{src:blk_xxx} a los bloques OCR. Cualquier bloque de código cuya
fidelidad OCR esté bajo 0.85 debe quedar marcado como :::warning con
texto "OCR low confidence" en lugar de reescribirse. Salida a Obsidian.
```

**Salida esperada:** nota `hybrid` con bloques `low_confidence`. Render en Obsidian.
**Caso F118:** `case-13-internet-archive-scan` (con `ocr-code-fidelity` en `pending_due_to_missing_sample` mientras F6 no descargue la muestra real).

### 3.12 · Diagramas de sintaxis (EBNF)

```
Tengo un fragmento del draft ISO C++ con gramática EBNF para las nuevas
features de C++26. Quiero una nota syntax con los 3 diagramas railroad
más importantes (declaration, template-parameter, concept-definition),
cada uno como bloque :::diagram con Mermaid o monoespaciado ASCII, y
una sección que explique la relación entre cada regla y un ejemplo
mínimo. Salida a Obsidian.
```

**Salida esperada:** nota `syntax` con 3 diagramas. Render en Obsidian.
**Caso F118:** — (no dedicado; cubierto por `examples/` futuros).

## 4. Validación de disparo

Cada prompt de §3 ha sido validado contra `evals/trigger-eval/run.py` (F10) — pasa la métrica TPR=1.00 (true positive rate) sobre el set de entrenamiento. Esto significa que la skill **siempre se dispara** cuando el agente recibe estos prompts.

Lo que **NO** dispara la skill (consultas negativas de F10):
- "resúmeme el correo" — no es fuente técnica.
- "tradúceme este PDF al español" — no es nota de estudio.
- "escribe una función en Python que..." — no es procesamiento de fuente.

Para verificar el set completo, ejecutar:

```bash
python evals/trigger-eval/run.py --queries evals/trigger-eval/queries.yaml
```

Resultado esperado: TPR_train=1.00, TPR_holdout=1.00, FPR_train=0.00, FPR_holdout=0.00.

## 5. Cambios permitidos

**No reabren F121:**
- Añadir un prompt nuevo al §3.
- Cambiar el wording de un prompt existente (siempre que pase TPR=1.0 sobre F10).
- Añadir un ejemplo real adicional a "Salida esperada".

**Reabren F121:**
- Eliminar prompts hasta dejar menos de 10.
- Cambiar la anatomía de §2.
- Cambiar las reglas de validación de §4.

# Manifiesto del producto — `notemartin-study-notes`

> Documento normativo de la Fase 1 del roadmap. Define qué es, qué promete, qué no es, y en qué orden se prefiere una promesa sobre otra cuando chocan.
>
> Regla dura de este manifiesto: una garantía sin métrica y sin mecanismo no es garantía, es eslogan. Si una frase no se puede comprobar, se elimina.

---

## 1. Nombre y propuesta de valor

**Nombre canónico:** `notemartin-study-notes`.

**Forma de distribución:** skill instalable. El trabajo lo hace el agente leyendo instrucciones; los scripts existen únicamente para tareas deterministas, repetitivas o costosas que un modelo de lenguaje haría mal, caro o de forma no reproducible.

**Lo que entrega:** notas de estudio completas, trazables y publicables en Obsidian, Notion, AppFlowy, Markdown, HTML/PDF y repaso espaciado, a partir de documentación técnica, libros técnicos y PDFs escaneados.

**Lo que NO entrega:** una aplicación. No hay servidor, ni framework, ni CLI monolítica. El repositorio contiene una skill que se carga en el contexto del agente, no un binario que se ejecuta.

---

## 2. Casos de uso primarios

Cada caso de uso primario se corresponde con un tipo de fuente planificado en el corpus de la Fase 6 del roadmap. La verificación material del mapeo se ejecuta cuando Fase 6 cree `evals/corpus/`; este manifiesto **declara** el mapeo ahora y lo deja listo para esa verificación.

| # | Caso de uso primario | Fuente del corpus (Fase 6) | Capacidad ejercitada |
|---|---|---|---|
| 1 | Convertir documentación técnica de producto en notas | Capítulo de documentación Oracle | L0/L1 nativo, jerarquía de secciones, tablas de parámetros |
| 2 | Convertir capítulo de libro técnico editorial en notas | Capítulo de libro técnico de editorial | L1 tipografía editorial, cajas Nota/Precaución, índice declarado |
| 3 | Convertir PDF escaneado con OCR sucio en notas | PDF escaneado con OCR sucio | L0 OCR, confianza por bloque, revisión humana |
| 4 | Convertir PDF a dos columnas en notas | PDF a dos columnas | L0 layout multi-columna, orden de lectura por geometría |
| 5 | Convertir documento denso en tablas (20+) en notas | Documento con 20+ tablas | L0 OCR de tablas, encabezados multinivel, celdas combinadas |
| 6 | Convertir API reference extensa en notas | API reference extensa | L2 unidades `parameter` y `error-code`, nota tipo `api-reference` |
| 7 | Convertir referencia CLI en notas | Referencia CLI | L2 unidades `step` y `parameter`, nota tipo `procedure` |
| 8 | Convertir RFC en notas | RFC | L1 numeración no consecutiva, anclas sintéticas, glosario técnico |
| 9 | Convertir transcripción en notas | Transcripción | L0 texto sin jerarquía, anclas temporales, edición de muletillas |
| 10 | Convertir diapositivas en notas | Diapositivas (PPTX) | L0 notas del orador, un bloque por slide, orden |
| 11 | Convertir README + repositorio en notas | README + repositorio | L0 texto más código, ejemplos ejecutables, dependencias |
| 12 | Producir notas en idioma distinto al de la fuente | Documento EN con salida esperada ES | L3 bilingüe, lista cerrada de no-traducibles |
| 13 | Convertir documento con fórmulas en notas | Documento con fórmulas | L0 OCR de fórmulas, LaTeX verificable, numeración preservada |
| 14 | Convertir documento con diagramas de sintaxis en notas | Documento con diagramas de sintaxis | L0 clasificación de regiones, reconstrucción a Mermaid o monoespaciado, nota tipo `syntax` |

Cada fila es un mapeo declarado. La verificación material se ejecuta cuando Fase 6 cree `evals/corpus/`. La Fase 1 no crea el corpus.

---

## 3. Garantías del producto

Cada garantía se enuncia con tres partes obligatorias: **definición operativa**, **métrica observable**, **mecanismo del proyecto** que la hace cumplir.

### 3.1 Fidelidad

- **Definición operativa:** ninguna unidad fáctica de la fuente se inventa, redondea ni pierde. Todo valor, parámetro, código de error, comando, sintaxis o afirmación fáctica presente en la fuente aparece en las notas con su mismo significado.
- **Métrica:** el 100 % de las unidades `must-keep` del Coverage Ledger alcanza estado terminal, y todo nodo fáctico del Note IR tiene al menos un `source_ref` resoluble contra el SDM. Una unidad `must-keep` omitida o un nodo fáctico sin respaldo es un fallo de fidelidad, no una advertencia.
- **Mecanismo:** Fase 15 (contrato Coverage Ledger y lista cerrada de motivos de descarte), Fase 42 (reglas de fidelidad con tres niveles: de la fuente, derivado, externo), Fase 43 (auditoría de no-pérdida con muestreo inverso), Fase 114 (auditoría automatizada de fidelidad).

### 3.2 Cobertura

- **Definición operativa:** ninguna sección de la fuente queda sin nota o con descarte no documentado. La trazabilidad desde la fuente hasta el producto final responde para cualquier punto de la fuente.
- **Métrica:** la consulta *"¿dónde quedó la sección X.Y.Z?"* devuelve exactamente uno de dos: (a) un nodo del Note IR con su ruta de publicación por destino, o (b) una entrada del Coverage Ledger con estado terminal y motivo de descarte extraído de la lista cerrada. No se admite una tercera respuesta.
- **Mecanismo:** Fase 15 (lista cerrada de motivos: `redundant-with:<unit_id>`, `boilerplate`, `navigation`, `out-of-scope-by-user`), Fase 38 (ledger operativo con reporte en cualquier punto del proceso).

### 3.3 Trazabilidad

- **Definición operativa:** existe ida y vuelta entre afirmación y bloque fuente, y entre bloque fuente y notas donde quedó. La relación es navegable en ambos sentidos.
- **Métrica:** dado cualquier nodo fáctico del Note IR, su `source_ref` apunta a un bloque existente del SDM; dado cualquier bloque del SDM con al menos una unidad asociada, existe una lista no vacía de notas donde quedó. Esta métrica es binaria por bloque y se mide globalmente con el script de la Fase 52.
- **Mecanismo:** Fase 13 (SDM con anclas estables, ids deterministas `sha1(source_hash + section_path + block_index)[:12]`, campo `origin` por bloque), Fase 46 (marcas inline `{src:blk_xxxx}` en NoteMark), Fase 52 (script de trazabilidad bidireccional).

### 3.4 Portabilidad

- **Definición operativa:** el mismo Note IR produce notas en los siete destinos declarados sin pérdida de contenido fáctico. La forma puede degradarse; el contenido no.
- **Métrica:** el comparador cross-target (Fase 63) reporta cero unidades del Coverage Ledger ausentes en cualquier destino, y cada diferencia entre destinos está justificada por una degradación declarada en la tabla de la Fase 53. Las degradaciones nunca son contenido eliminado, son cambio de forma.
- **Mecanismo:** Fase 53 (contrato de renderer y tabla de degradación por capacidad ausente), Fase 54 (renderer Obsidian), Fase 55 (renderer Notion API), Fase 56 (renderer Notion por importación), Fase 57 (renderer AppFlowy), Fase 58 (renderer Markdown estándar), Fase 59 (renderer HTML y PDF), Fase 60 (renderer de flashcards), Fase 63 (validador de equivalencia entre destinos).

---

## 4. No-objetivos explícitos

Estos son los comportamientos que `notemartin-study-notes` **no** implementa. Si una solicitud del usuario solo se puede satisfacer mediante uno de ellos, la skill debe declinar o etiquetar la salida como limitada.

1. **No es un chatbot conversacional sobre el documento.** No responde preguntas en bucle contra el contenido ingestado; produce notas persistentes y trazables, no turnos de diálogo.
2. **No es un traductor.** Cambia el idioma de la prosa cuando el perfil lo pide, pero los identificadores técnicos (nombres de parámetro, comandos, códigos de error, sintaxis, APIs) nunca se traducen. Existe una lista cerrada de no-traducibles.
3. **No genera contenido ausente de la fuente.** Las lagunas se declaran como tales; no se rellenan por inferencia ni por conocimiento del modelo.
4. **No es un resumidor genérico.** La fidelidad prima sobre la brevedad. Un resumen que pierde un detalle crítico es un fallo, no una optimización.
5. **No es un motor de búsqueda semántica.** Opera sobre documentos ingestados en el directorio de trabajo de la sesión. No consulta Internet ni índices externos.
6. **No es un editor WYSIWYG.** El agente escribe NoteMark (Markdown canónico con directivas); los renderers son scripts deterministas. El agente no produce el Markdown del destino final; lo produce el script.
7. **No es una plataforma de almacenamiento.** No aloja notas, no mantiene un vault propio. Las publica en destinos externos controlados por el usuario (Obsidian, Notion, AppFlowy, carpeta local).
8. **No produce elementos decorativos sin respaldo factual.** Diagramas, callouts, tarjetas de repaso y figuras deben tener fuente; los elementos puramente ornamentales sin `source_refs` no entran en la salida.

---

## 5. Orden de prioridad entre promesas

Cuando dos promesas del producto entran en tensión, se aplica la siguiente jerarquía, de mayor a menor prioridad:

> **Fidelidad > Cobertura > Pedagogía.**

Reglas de desempate en las tres colisiones canónicas:

- **Fidelidad vs Cobertura.** Gana fidelidad. Si una sección no se entiende a partir de la fuente, se declara la ausencia (entrada del ledger con motivo `out-of-scope-by-user` o marcado de bloque de baja confianza); no se completa con inferencia.
- **Cobertura vs Pedagogía.** Gana cobertura. Si incluir un detalle técnico correcto resulta denso o aburrido, se incluye de todos modos; la pedagogía se mejora sin recortar el hecho.
- **Fidelidad vs Pedagogía.** Gana fidelidad. Se parafrasea la prosa explicativa en vez de adornarla; nunca se sustituye un valor exacto (número, nombre, sintaxis, comando) por una versión "más clara" que lo cambia.

Cuando una colisión no encaje en ninguno de los tres casos anteriores, se aplica el mismo orden: ante la duda, se preserva el hecho antes que la forma.

---

## 6. Glosario mínimo del manifiesto

Tres términos que el resto del proyecto reusa tal cual:

- **Fuente.** Documento original en cualquier formato de entrada aceptado por la Fase 17 (PDF, EPUB, DOCX, PPTX, HTML, transcripción, repositorio).
- **Unidad de información.** Afirmación mínima con valor independiente. Su definición operativa y tipos canónicos se formalizan en la Fase 37.
- **Destino.** Plataforma de publicación final: Obsidian, Notion, AppFlowy, Markdown estándar, HTML/PDF, o repaso espaciado (Obsidian Spaced Repetition o Anki vía CSV).

---

## 7. Estado del documento

- **Versión:** 1.0 — cierre de Fase 1.
- **Verificación diferida:** la tabla de la sección 2 se considerará materialmente verificada cuando la Fase 6 del roadmap cree `evals/corpus/` y cada fuente del corpus exercite el caso de uso que se le asigna.
- **Cambios permitidos sin reabrir Fase 1:** añadir o eliminar no-objetivos (sección 4), o actualizar la tabla de la sección 2 cuando Fase 6 fiche las fuentes reales. Cambios en las garantías (sección 3) o en la jerarquía (sección 5) reabren la fase.

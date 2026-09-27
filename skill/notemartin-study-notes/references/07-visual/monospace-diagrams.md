# `references/07-visual/monospace-diagrams.md` — Diagramas monoespaciados

> **Propósito:** catálogo de patrones de diagramas en ASCII puro (monoespaciado) listos para copiar y pegar en notas NoteMark (`.nm`) y Markdown (`.md`). Complementa al catálogo Mermaid de F65 (`diagram-catalog.md`) y al subconjunto portable de F66 (`mermaid-portable.md`) con representaciones que no requieren motor de renderizado y se ven idénticas en **Obsidian**, **Notion import** y **GitHub/Markdown** (los 3 destinos de la intersección F66 §1.1).
>
> **Cuándo cargar:** el agente está decidiendo entre Mermaid (F65), monoespaciado (F69) o imagen pre-renderizada (F68) para una intención dada. Carga este archivo para verificar si un patrón monoespaciado sirve, especialmente cuando: (1) el diagrama cabe en ≤60 caracteres, (2) la estructura es tabular o jerárquica simple, (3) no hay Unicode en los nodos, (4) se quiere evitar la dependencia de `mmdc`.

---

## §1 · Propósito y alcance

**Gobna tres decisiones:**

1. **Cuándo preferir monoespaciado** sobre Mermaid (F65) o imagen (F68): §3 tabla de decisión.
2. **Qué patrón copy-paste** usar para una intención dada: §4-§15 con 12 patrones canónicos.
3. **Cómo verificar** que el patrón cumple los criterios de portabilidad (ancho, caracteres, destinos): §17.

**Fuera de alcance:**

- Sintaxis Mermaid portable → `mermaid-portable.md` (F66).
- Catálogo intención→tipo → `diagram-catalog.md` (F65).
- Pre-renderizado a imagen → `scripts/render/diagram_image.py` (F68).
- Reconstrucción de diagramas impresos → `reconstruction.md` (F71).
- Tokens de color / estilo visual → `tokens.md` (F72), `style-mapping.md` (F73).

---

## §2 · Convenciones

### §2.1 · Ancho máximo

- **Ancho estándar:** **60 caracteres** (conservador, cabe sin scroll en viewport estándar de Notion import).
- **Ancho máximo absoluto:** **70 caracteres** (reservado para patrones con campos anchos como árbol B). El uso de >70 chars debe documentarse como "no portable" en §3.

### §2.2 · Caracteres permitidos

Solo **ASCII puro** para máxima portabilidad:

```
+ - | : = < > v ^ ( ) , . # * [ ] espacio
```

**No se usan caracteres Unicode box-drawing** (`┌─┐│└┘├┤┬┴┼`) porque algunos destinos los renderizan con ancho diferente o los confunden con otros símbolos.

### §2.3 · Encapsulamiento en NoteMark

Cada patrón va en un bloque fenced code **sin** lenguaje específico (no ```` ```mermaid ````, solo ```` ``` ````):

```notemark
:::note
Patrón extraído de `references/07-visual/monospace-diagrams.md` §N.
:::
```
```
<contenido ASCII del patrón>
```
```

Para combinar con `:::note` admonition (F45) y `{src:blk_xxx}` cuando el patrón viene de una fuente externa.

---

## §3 · Tabla de decisión

12 criterios × 3 formatos = 36 celdas. La siguiente tabla decide qué representación usar para cada caso.

| Criterio | Mermaid (F65/F66) | Monoespaciado (F69) | Imagen (F68) |
|---|---|---|---|
| Diagrama con ≤15 nodos | ✅ | ✅ más simple | ⚠ overhead |
| Diagrama con >15 nodos | ✅ con partición | ⚠ aceptable si cabe en ancho | ✅ vectorial escalable |
| Anchura requerida > 60 chars | ✅ se adapta | ❌ se sale del viewport | ✅ se adapta |
| Ramas complejas (>5 alternativas) | ✅ decisiones con rombo | ⚠ verboso | ✅ |
| Estados con transiciones complejas | ✅ stateDiagram | ⚠ verboso | ✅ |
| Tabla de comparación con datos | ❌ mejor tabla GFM | ✅ side-by-side | ❌ |
| Layout de memoria / buffer | ⚠ verbose | ✅ claro | ⚠ requiere pre-render |
| ASCII art embebido en código fuente | ❌ | ✅ natural | ❌ |
| Jerarquías profundas (>5 niveles) | ✅ con subgraph | ❌ verboso | ✅ |
| Redes de paquetes / protocolos | ✅ | ✅ para headers simples | ✅ |
| Diagramas muy pequeños (≤3 nodos) | ⚠ overhead innecesario | ✅ más simple | ⚠ overhead |
| Diagramas que se actualizan frecuentemente | ✅ editable en texto | ✅ editable en texto | ❌ requiere regenerar |

**Regla operativa:**

1. Si el criterio dominante es "datos tabulares" o "layout de memoria/buffer" → **monoespaciado**.
2. Si el criterio dominante es "ramas complejas" o "estados" → **Mermaid**.
3. Si el destino es HTML/PDF, Notion API, AppFlowy, Flashcards y el diagrama tiene >10 nodos → **imagen pre-renderizada** (F68).
4. Si ninguno aplica, **Mermaid portable** (F66).

---

## §4 · Patrón: Layout en disco (ext2/ext3 simplificado)

**Contexto:** representar la disposición de metadatos y datos en un filesystem Unix-like.

**Ancho típico:** 32 caracteres.

````
+----------------+
|  superblock    |
|  (block #0)    |
+-------+--------+
|       |        |
| inode table    |
|       |        |
+-------+--------+
|       |        |
| data blocks    |
|       |        |
+-------+--------+
````

**Variante extendida (con grupos de cilindros):**

````
+-cyl grp 0-+-cyl grp 1-+-cyl grp 2-+
| sb |  bg  |  bg  |  bg |  bg  |  bg |
| it | data | data | data | data | data |
+----+-----+------+-----+------+-----+
````

**Notas:**

- Para variantes con más metadatos (journal, bitmap) preferir Mermaid (F65 T6 capas).
- Si el dominio es académico (Tanenbaum §4), preferir la versión extendida.

---

## §5 · Patrón: Buffer circular

**Contexto:** representar una cola FIFO con índice de lectura y escritura que dan la vuelta.

**Ancho típico:** 60 caracteres.

````
   +---+---+---+---+---+---+---+---+
   |   |   |   |   |   |   |   |   |
   +---+---+---+---+---+---+---+---+
     ^                       ^
    head                    tail
   (read)                  (write)
   
   (vacío cuando head == tail)
````

**Variante con tamaño y capacidad:**

````
   +---+---+---+---+---+---+---+---+
   |   |   |   | X | X | X |   |   |
   +---+---+---+---+---+---+---+---+
            ^           ^
           tail        head
   size=5  capacity=8  (3 vacíos)
````

**Notas:**

- Si head/tail se cruzan → buffer lleno o vacío según implementación.
- Para variantes con prioridades o múltiples colas, remitir a Mermaid (F65 T6).

---

## §6 · Patrón: Árbol B (nodo genérico)

**Contexto:** representar un nodo de árbol B con claves y punteros a hijos.

**Ancho típico:** 60 caracteres (versión compacta) / 70 (versión extendida).

````
              +-----+
              |  K  |
              +--+--+
                 |
       +---------+---------+
       |                   |
   +---+---+           +---+---+
   | K | K |  -->      | K | K |  -->
   +-|-+-+-           +-|-+-+-
    V   V             V   V
  leaf leaf         leaf leaf
````

**Variante extendida (3 niveles, con valores):**

````
              +-------+
              |   7   |
              +---+---+
                  |
        +---------+---------+
        |                   |
    +---+---+           +---+---+
    | 3 | 5 |  -->     | 9 | 12| -->
    +-|-+-+-           +-|-+-+-
     V   V             V   V
   [3,5] [5,7]       [9,12] [12,15]
````

**Notas:**

- Si el árbol tiene >5 nodos visibles, preferir Mermaid (F65 T4) o imagen (F68).
- Los `K` y `V` son placeholders: en el árbol real cada nodo contiene 2t−1 claves como máximo.

---

## §7 · Patrón: Jerarquía de memoria

**Contexto:** representar los niveles de la jerarquía de memoria (registros → caché → RAM → disco).

**Ancho típico:** 40 caracteres.

````
  Speed          Size          Cost
    +               +             +
    |               |             |
    v               v             v
+--------+      +---------+     +---------+
| regs   |      |  L1     |     |  RAM    |
+--------+      +---------+     +---------+
   |               |               |
   v               v               v
+--------+      +---------+     +---------+
|  L1    |      |  L2     |     |  Disk   |
+--------+      +---------+     +---------+
   |               |               |
   v               v               v
+--------+      +---------+     +---------+
|  L2    |      |  L3     |     |  Tape   |
+--------+      +---------+     +---------+
````

**Variante compacta (3 niveles):**

````
  regs   <->   L1   <->   L2/L3   <->   RAM   <->   Disk
  ~1 ns       ~1 ns      ~10 ns         ~100 ns      ~10 ms
````

**Notas:**

- La jerarquía canónica es 5 niveles (Tanenbaum §4). Las flechas `<->` indican que el dato puede fluir en ambos sentidos.
- Para variantes con tiempos de acceso numéricos, usar tabla GFM en lugar de monoespaciado.

---

## §8 · Patrón: Concurrencia y bloqueos

**Contexto:** representar la sincronización entre threads mediante mutex o semáforos.

**Ancho típico:** 50 caracteres.

````
Thread A   Thread B
   |           |
   v           v
+---+       +---+
|M  |       |M  |
+-+-+       +-+-+
  |   lock    |
  +-----+-----+
        v
   +---------+
   | shared  |
   | resource|
   +---------+
````

**Variante con RW lock (lectores concurrentes, escritor exclusivo):**

````
  Reader1   Reader2    Writer
    |         |          |
    v         v          v
  +-----+  +-----+    +-----+
  |  R  |  |  R  |    |  W  |
  +--+--+  +--+--+    +--+--+
     |        |          |
     +----+---+      [exclusive]
          |              |
          v              v
       +--+--+       +--+--+
       | RW | lock  | RW |
       +-----+       +-----+
````

**Notas:**

- Para variantes con monitors, condition variables, o barriers, preferir Mermaid (F65 T1).
- Si el caso incluye deadlock detection o wait-for graph, Mermaid es obligatorio.

---

## §9 · Patrón: Paquete de red (Ethernet/IP simplificado)

**Contexto:** representar la estructura de un frame Ethernet con payload IP.

**Ancho típico:** 60 caracteres.

````
+--------+--------+--------+----------------+
| dest   | src    | type   | payload        |
| MAC    | MAC    | (Ether)| (var)          |
+--------+--------+--------+----------------+
|  6B    |  6B    |  2B    | 46-1500B       |
+--------+--------+--------+----------------+
````

**Variante con OSI layers (stack vertical):**

````
  7  Application  | HTTP, DNS, SSH
  6  Presentation | TLS, MIME
  5  Session      | NetBIOS, RPC
  4  Transport    | TCP, UDP     <-- port numbers
  3  Network      | IP           <-- IP addresses
  2  Data Link    | Ethernet      <-- MAC addresses
  1  Physical     | cables, radio
````

**Notas:**

- Si se requiere representar fragmentación o flags TCP/IP, preferir Mermaid (F65 T2 secuencia).
- La variante OSI usa 7 filas; cabe en 60 chars sin problema.

---

## §10 · Patrón: Particionamiento (sharding)

**Contexto:** representar cómo se distribuyen datos entre múltiples shards por hash de clave.

**Ancho típico:** 60 caracteres.

````
+-----------+   +-----------+   +-----------+
| Shard 0   |   | Shard 1   |   | Shard 2   |
| key % 3=0 |   | key % 3=1 |   | key % 3=2 |
+-----------+   +-----------+   +-----------+
       \              |              /
        +-------------+-------------+
                      |
                +-----+-----+
                | router    |
                | hash(key) |
                +-----------+
````

**Variante con replicación (master/replica):**

````
+----------+        +----------+
| Master 0 |------->| Replica 0|
+----------+        +----------+
+----------+        +----------+
| Master 1 |------->| Replica 1|
+----------+        +----------+
+----------+        +----------+
| Master 2 |------->| Replica 2|
+----------+        +----------+
   \                  /
    +------+---------+
           |
       [clients]
````

**Notas:**

- Si se requiere representar consistencia eventual vs fuerte, Mermaid es mejor (F65 T6).
- Para variantes con Raft/Paxos, remitir a Mermaid T2 (secuencia).

---

## §11 · Patrón: Comparación lado a lado

**Contexto:** comparar dos estados, versiones o alternativas en una sola vista.

**Ancho típico:** 50 caracteres.

````
+----------+       +----------+
| Before   |       | After    |
+----------+       +----------+
| prop A   |  -->  | prop A'  |
| prop B   |       | prop B'  |
| prop C   |       | prop D   |
+----------+       +----------+
````

**Variante con tabla de 3 columnas (diff):**

````
| Aspect    | Before  | After   |
|----------+---------+---------|
| syntax    | foo()   | foo()   |
| behavior  | bar     | baz     |
| perf      | 100ms   | 10ms    |
````

**Notas:**

- Si hay >5 propiedades, preferir tabla GFM (que es texto preformado en monoespaciado igualmente).
- Para diffs con >20 líneas, usar herramienta externa (git diff).

---

## §12 · Patrón: Pipeline de instrucciones (5-stage RISC)

**Contexto:** representar las 5 etapas clásicas del pipeline MIPS/RISC-V.

**Ancho típico:** 60 caracteres.

````
  IF    ->    ID    ->    EX    ->    MEM   ->    WB
fetch     decode    execute    memory    writeback
  |          |          |          |          |
  v          v          v          v          v
instr     regs      ALU       data       reg
from      read      op        mem        file
mem                           access
````

**Variante con instrucción viajando por las etapas:**

````
  I1:  IF          ID                EX       MEM  WB
  I2:     IF          ID                EX       MEM  WB
  I3:        IF          ID                EX       MEM  WB
  I4:           IF          ID                EX       MEM  WB
  I5:              IF          ID                EX       MEM
````

**Notas:**

- Para variantes con hazard detection o forwarding, Mermaid (F65 T2 secuencia) es mejor.
- Si se quiere representar stalls o flushes, usar tabla GFM.

---

## §13 · Patrón: Cola de mensajes (producer/consumer)

**Contexto:** representar una cola de mensajes con topics, producer y consumer.

**Ancho típico:** 50 caracteres.

````
producer         broker            consumer
   |                |                  |
   v                v                  v
+------+    +-----+-----+    +------+
| msg1 |--->| topic A    |--->| sub1 |
+------+    +-----+-----+    +------+
   |         |  |  |           |
   v         v  v  v           v
+------+    +-----+-----+    +------+
| msg2 |--->| topic B    |--->| sub2 |
+------+    +-----+-----+    +------+
````

**Variante con prioridad:**

````
  +--Priority Queue--+
  |  high | med | low |
  +------+-----+-----+
     |      |     |
     v      v     v
   worker worker worker
````

**Notas:**

- Si hay >5 topics o routing complejo, Mermaid (F65 T6 capas) es mejor.

---

## §14 · Patrón: Tabla hash con chaining

**Contexto:** representar una tabla hash donde las colisiones se resuelven con listas enlazadas.

**Ancho típico:** 50 caracteres.

````
bucket[0]   bucket[1]   bucket[2]   bucket[3]
   |           |           |           |
   v           v           v           v
+---+       +---+       +---+       +---+
| K |--->|   |       | K |--->| K |
+---+   | K |--->|     +---+   | K |
        +---+   |              +---+
        | nil  |
        +-----+
````

**Variante con carga (load factor):**

````
  size=4   load=0.75   capacity=8

  [0] [1] [2] [3] [4] [5] [6] [7]
   |   |   |   |
   v   v   v   v
   K   K   K   K (colision en [3])
       |
       v
       K
````

**Notas:**

- Para variantes con open addressing (linear probing, quadratic probing), Mermaid T4 es mejor.

---

## §15 · Patrón: Pila de llamadas

**Contexto:** representar la pila de llamadas (call stack) de un programa.

**Ancho típico:** 30 caracteres.

````
+----------+
| main()   |
+----------+
   |
   v
+----------+
| foo()    |
+----------+
   |
   v
+----------+
| bar()    |
+----------+
   |
   v
+----------+
| baz()    |
+----------+
````

**Variante con variables locales:**

````
+----------+
| main()   | a=1, b=2
+----------+
   |
   v
+----------+
| foo(x)   | x=42
+----------+
   |
   v
+----------+
| bar(y)   | y=99
+----------+
   |
   v
  (return)
````

**Notas:**

- Para stacks con >10 frames, Mermaid T4 jerarquía es mejor.
- Si se quiere representar recursión o tail calls, Mermaid T1.

---

## §16 · Tabla resumen de patrones

| # | Patrón | Categoría | Dominio | Ancho típico | Cuándo preferir |
|---|---|---|---|---|---|
| 4 | Layout en disco | almacenamiento | Filesystems | 32 | Filesystems Unix-like |
| 5 | Buffer circular | memoria | Sistemas | 60 | Colas FIFO de tamaño fijo |
| 6 | Árbol B | estructura de datos | Databases | 60-70 | Árboles balanceados de búsqueda |
| 7 | Jerarquía de memoria | memoria | Sistemas | 40 | Jerarquía caches/RAM/disco |
| 8 | Concurrencia y bloqueos | concurrencia | Sistemas | 50 | Sincronización simple |
| 9 | Paquete de red | red | Redes | 60 | Headers Ethernet/IP/TCP |
| 10 | Particionamiento | distribución | Databases | 60 | Sharding / replicación simple |
| 11 | Comparación lado a lado | comparación | General | 50 | Diff / before-after |
| 12 | Pipeline de instrucciones | arquitectura | CPU | 60 | Pipeline 5-stage RISC |
| 13 | Cola de mensajes | mensajería | Distributed | 50 | Producer/consumer simple |
| 14 | Tabla hash con chaining | estructura de datos | General | 50 | Hash con colisiones |
| 15 | Pila de llamadas | memoria | Sistemas | 30 | Call stack simple |

---

## §17 · Verificación

### §17.1 · Auto-evaluación antes de cerrar la nota

Para cada patrón usado en una nota, verificar:

| Pregunta | ✓ / ✗ | Nota |
|---|---|---|
| Ancho ≤ 60 chars (estándar) o ≤ 70 con justificación | | |
| Solo caracteres ASCII permitidos (§2.2) | | |
| Decisión correcta según §3 (vs Mermaid / imagen) | | |
| Variante envuelta en bloque fenced code sin lenguaje | | |
| `:::note` con `src:blk_xxx` si viene de fuente externa | | |

### §17.2 · Verificación programática (opcional)

Si la eval battery `evals/monospace-diagrams-sample/` existe, ejecuta:

```bash
python evals/monospace-diagrams-sample/run_eval.py
```

Criterios: C1 ≥10 patrones extraídos; C2 todos los patrones ≤60 (o ≤70 con justificación); C3 tabla de decisión con 36 celdas no vacías.

---

## §18 · Cambios permitidos

**Modificaciones libres (sin reabrir la fase):**

1. Añadir **variantes** a un patrón existente en §4-§15.
2. Añadir **nuevos patrones** §4-§15 (manteniendo el formato `### Contexto / ### Ancho / ### Plantilla / ### Variantes / ### Notas`).
3. Añadir **filas a la tabla resumen** §16.
4. Añadir **filas a la tabla de decisión** §3 (manteniendo las 3 columnas y todos los criterios anteriores).
5. Corregir erratas tipográficas sin reabrir la fase.

**Reabrir la fase si:**

- Se cambia el ancho estándar (60) o máximo (70).
- Se permite Unicode box-drawing en §2.2.
- Se reduce el número de patrones por debajo de 10.
- Se eliminan filas de la tabla de decisión §3.

---

**Verificación al cierre de la fase:**

- `wc -l monospace-diagrams.md` ≤ 700 líneas.
- ≥ 10 patrones en §4-§15.
- Todas las plantillas ≤ 60 caracteres (o ≤ 70 con justificación).
- Tabla §3 con 36 celdas no vacías (12 × 3).
- Wirings colaterales aplicados (SKILL.md §5.2, 07-visual/README.md, mermaid-portable.md §10).

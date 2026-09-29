# `references/06-writing/analogies.md` — Catálogo de analogías y banco reutilizable

> Documento normativo de la **Fase 95**. Define la **taxonomía de patrones**
> de analogía (≥ 10), el **banco reutilizable** (≥ 15 entradas) y la
> **regla universal de rotura** que toda analogía debe satisfacer.
>
> F94 fija **cuándo** y **cómo** aparece `## Analogía` dentro del patrón
> de 5 etapas; F95 fija **qué** se elige. La diferencia operativa:
> cuando el agente redacta `## Analogía`, **primero** consulta este catálogo;
> si encuentra una entrada apta, la reusa; si no, inventa una nueva y la
> añade al banco.
>
> **Cuándo cargar:** antes de redactar `## Analogía` en cualquier nota
> pedagógica; cuando se revisa una nota y el revisor externo detecta que
> la analogía es débil, está mal mapeada o no declara la rotura.
>
> **Wirings:**
> - `references/06-writing/intuition-first.md` (F94) §2, §5.3, §6 D5-D6
>   — mecánica de la sección, regla A1-A3, señales D5 y D6.
> - `references/04-authoring/block-directives.md` (F45) §10.11-§10.12 —
>   `:::derived` (analogía propia basada en SDM) vs `:::external`
>   (referencia cultural/técnica ajena al SDM).
> - `references/04-authoring/inline-marks.md` (F46) — `{external}` inline.
> - `references/04-authoring/depth-layers.md` (F51) — el banco es L1
>   reutilizable; la analogía vive en L1 dentro de la nota.
> - `references/05-note-types/concept.md` (F78) §3 fila `## Analogía`.
> - `references/05-note-types/selector.md` (F93) §3 — decide si la nota
>   admite analogía o aplica la excepción `reference-pure` (F94 §4).

---

## §1 · Propósito y alcance

Tres problemas resueltos por F95:

1. **El agente reinventa analogías mediocres en cada nota.** Sin catálogo,
   el agente cae en los mismos 3 patrones (tráfico, biblioteca, cocina)
   y termina comparando bases de datos con bases de datos. F95 ofrece
   **≥ 15 entradas curadas** distribuidas en **≥ 10 patrones de sistemas**.
2. **Las analogías no declaran la rotura.** F94 §6 D5 ya exige una frase
   algorítmicamente detectable. F95 eleva esa señal a **norma del banco**:
   ninguna entrada entra sin `Rotura:` explícito, redactado con plantilla
   cerrada (no vale "casi", "no del todo", "más o menos").
3. **El agente no sabe cuándo aplicar un patrón u otro.** F95 §5 da un
   árbol de decisión de 5-7 preguntas binarias con señales léxicas
   extraíbles del SDM o del concepto.

**Cierra los 3 criterios del ROADMAP §1652-1654:**

1. _Al menos 10 patrones con ejemplo completo_ → §2 con tabla de 12 patrones.
2. _Toda analogía declara su límite_ → §4 regla universal + plantilla cerrada,
   verificada por entrada en §3 (campo `Rotura:`) y por el eval (C4).
3. _El banco tiene al menos 15 entradas_ → §3 con 18 entradas estructuradas.

**Fuera de alcance:**

- El patrón de **cuándo** aparece la analogía → F94.
- Ejemplos ejecutables con setup/cleanup → F96.
- Comparaciones y trade-offs → F97.
- Anti-patrones generales de redacción → F100.
- Idioma bilingüe y citación → F101.

---

## §2 · Taxonomía de patrones (≥ 10)

Tabla cerrada con **12 patrones**. Los 5 primeros vienen impuestos por el
ROADMAP (sistemas: contención, contrato/protocolo, recurso escaso, tráfico
y colas, libro mayor/bitácora); los 7 restantes son los que el banco y la
experiencia del dominio han revelado como recurrentes.

| # | Patrón | Idea núcleo | Dominios destino típicos | Dominios fuente típicos | Rotura canónica |
|---|---|---|---|---|---|
| **P1** | Contención | Aislar X para que no afecte a Y. | namespaces, sandboxing, cgroups, chroot, permisos `0600`. | cárcel, caja fuerte, habitación cerrada, bunker. | La analogía asume un límite físico; el límite digital se rompe por escape de kernel o path traversal. |
| **P2** | Contrato / protocolo | Dos partes acuerdan forma y orden antes de hablar. | APIs (REST, gRPC), protocolos de red (HTTP, SMTP), schemas (Protobuf, Avro), contratos legales. | contrato notarial, formulario de admisión, pedido a restaurante. | Un contrato legal se firma una vez; un protocolo se negocia cada sesión (handshake, auth). |
| **P3** | Recurso escaso | Si te pasas, no hay más; hay que soltar. | memoria RAM, file handles, puertos TCP, conexiones DB, threads, seats. | agua de grifo, dinero en caja, asientos de cine, meseros de restaurante. | El agua se acaba sin aviso; los handles los回收 el GC. La analogía no captura la liberación asíncrona. |
| **P4** | Tráfico y colas | Lo que llega antes sale antes (FIFO) o se descarta. | routers, balanceadores, message queues (Kafka, RabbitMQ), kernel runqueue, token bucket. | tráfico urbano, cola de supermercado, fila de banco. | Una cola física se ve; un buffer TCP no. El descarte es silencioso y recuperable con ACK. |
| **P5** | Libro mayor / bitácora | Cada evento se escribe en orden; nada se reescribe. | PostgreSQL WAL, Git log, `journald`, audit log, replication log, event sourcing. | libro contable, bitácora de barco, diario personal. | Un libro se cierra y se archiva; un WAL se trunca tras el checkpoint. |
| **P6** | Capas | Cada capa solo conoce a la de abajo y a la de arriba. | OSI, TCP/IP, stack de red, middleware, layered architecture. | cebolla, edificio de pisos, matrimonio entre capas (capa de presentación + lógica + datos). | Las capas físicas tienen grosor constante; las capas digitales son difusas (cross-cutting concerns). |
| **P7** | Idempotencia | Aplicar la operación N veces produce el mismo resultado que aplicarla 1. | `PUT /resource/123`, `UPSERT`, `mv` (rename), interruptores binarios. | interruptor de luz (on/off), timbre (tocar 2 veces = tocar 1), sello de tinta. | Un interruptor solo tiene 2 estados; una operación idempotente puede tener infinitos. |
| **P8** | Consistencia vs disponibilidad | Bajo partición, eliges entre ver lo mismo o estar disponible. | CAP theorem, replicación síncrona vs asíncrona, caches distribuidas. | cocina con 2 cocineros vs 1, equipo con comunicación vs sin ella. | 2 cocineros físicamente en la misma cocina se ven; 2 nodos DB no se ven hasta la replicación. |
| **P9** | Garbage collection / limpieza | Lo viejo se libera cuando ya nadie lo necesita. | `VACUUM` PostgreSQL, Java GC, logrotate, `rm -r` programado. | barrendero nocturno, recicladora, limpieza de trastos viejos. | El barrendero recoge todo; el GC solo lo que es inalcanzable (referencias). |
| **P10** | Cache / memoización | Si ya lo calculaste, no lo recalcules. | LRU, CDN, Memcached, Redis, browser cache, write-back. | cuaderno de notas junto al libro, lista de la compra repetida, pizarra. | El cuaderno se queda contigo; el cache expira por TTL o por eviction. |
| **P11** | Concurrencia / exclusión mutua | Solo uno a la vez. | mutex, semáforo, `SELECT FOR UPDATE`, transacción, lock de archivo. | baño con llave, puente de un solo carril, micrófono compartido. | El baño tiene 1 capacidad fija; un mutex protege una sección crítica arbitrariamente larga. |
| **P12** | Routing / despacho | Elige a quién enviar el paquete. | load balancer, DNS round-robin, message router, dispatch en kernel. | recepcionista de hotel, centralita telefónica, cartero con rutas. | El cartero conoce cada casa; un router solo conoce la subred siguiente. |

Cada patrón puede tener **N entradas** en el banco (§3). Una misma entrada
puede aplicar a **2-3 patrones** (ej. E18 tren con vagones → P4 + P6); la
tabla de banco §3 marca el patrón principal y los secundarios.

---

## §3 · Banco reutilizable (≥ 15 entradas)

**18 entradas estructuradas**. Cada una declara: patrón, dominios,
plantilla, marca preferida, **Rotura:** explícita, reusos conocidos,
señal de verificación. Plantilla de §7.

### E1 · Cárcel / sandbox

- **Patrón:** P1 (Contención).
- **Dominio destino:** sistemas, kernel (cgroups, namespaces, `chroot`).
- **Dominio fuente:** cárcel (celdas, muros, rejas).
- **Plantilla:** "Un proceso en un namespace es como un preso en una
  celda: solo ve lo que su celda le deja ver. El mundo exterior existe,
  pero no es accesible desde dentro."
- **Marca preferida:** `:::derived`.
- **Rotura:** El preso no puede escapar físicamente; un proceso puede
  hacer path traversal o exploit de kernel para salir del namespace.
- **Reusado en:** docs de Docker (`--pid=host`), Kubernetes (pod sandbox).
- **Señal de verificación:** D5 + D6.

### E2 · Caja fuerte de banco

- **Patrón:** P1 (Contención).
- **Dominio destino:** secretos (Vault, permisos `0600`, HSM).
- **Dominio fuente:** caja fuerte con combinación.
- **Plantilla:** "Un secreto en Vault es como una caja fuerte con
  combinación: solo quien tiene la combinación la abre; el banco entero
  no ve el contenido."
- **Marca preferida:** `:::external`.
- **Rotura:** El banco tiene una llave maestra (root); en Vault, la
  llave maestra es revocable y rotada. La analogía no captura la
  rotación de credenciales.
- **Reusado en:** HashiCorp Vault docs, AWS KMS.
- **Señal de verificación:** D5 + D6.

### E3 · Contrato legal

- **Patrón:** P2 (Contrato / protocolo).
- **Dominio destino:** APIs, schemas (Protobuf, Avro, OpenAPI).
- **Dominio fuente:** contrato notarial.
- **Plantilla:** "Un schema Protobuf es como un contrato legal: define
  qué campos van, en qué orden, de qué tipo. Las dos partes lo firman
  antes de hablar."
- **Marca preferida:** `:::external`.
- **Rotura:** Un contrato se firma una vez; un schema se versiona
  (`v1`, `v2`) y cada cliente negocia la versión en cada conexión.
- **Reusado en:** gRPC docs, Avro spec.
- **Señal de verificación:** D5 + D6.

### E4 · Formulario de admisión

- **Patrón:** P2 (Contrato / protocolo).
- **Dominio destino:** HTTP request, `kubectl apply -f`, formulario web.
- **Dominio fuente:** formulario de hospital.
- **Plantilla:** "Una petición HTTP es como un formulario de admisión
  de hospital: el cliente rellena los campos (headers, body), el
  servidor los valida y responde con un resultado estructurado."
- **Marca preferida:** `:::external`.
- **Rotura:** Un formulario se entrega una vez; HTTP puede reintentar
  (idempotencia, retries) y los headers se renegocian por sesión.
- **Reusado en:** RFC 9110, OpenAPI spec.
- **Señal de verificación:** D5 + D6.

### E5 · Grifo de agua

- **Patrón:** P3 (Recurso escaso).
- **Dominio destino:** memoria RAM, CPU, bandwidth.
- **Dominio fuente:** grifo con caudal limitado.
- **Plantilla:** "La memoria RAM es como el agua de un grifo: sale
  mientras haya presión. Cuando abres demasiados grifos a la vez, la
  presión cae y el sistema se ralentiza."
- **Marca preferida:** `:::external`.
- **Rotura:** El grifo tiene caudal físico constante; la RAM es
  compartida por todos los procesos y se libera por GC, no por gravedad.
- **Reusado en:** tuning de PostgreSQL `shared_buffers`.
- **Señal de verificación:** D5 + D6.

### E6 · Boletos de cine

- **Patrón:** P3 (Recurso escaso).
- **Dominio destino:** puertos TCP, file handles, conexiones DB.
- **Dominio fuente:** boletos numerados de cine.
- **Plantilla:** "Cada conexión al servidor consume un puerto TCP.
  Es como un boleto numerado: hay 65535 boletos, y cuando se acaban
  el servidor rechaza nuevas conexiones con `EADDRINUSE`."
- **Marca preferida:** `:::external`.
- **Rotura:** Un boleto se usa una vez y se destruye; un puerto TCP
  entra en `TIME_WAIT` y se reutiliza tras minutos.
- **Reusado en:** troubleshooting `ps aux | grep socket`.
- **Señal de verificación:** D5 + D6.

### E7 · Semáforo urbano

- **Patrón:** P4 (Tráfico y colas).
- **Dominio destino:** routers, rate limiters, token bucket, semáforos
  de concurrencia.
- **Dominio fuente:** semáforo de tráfico.
- **Plantilla:** "Un token bucket es como un semáforo: los coches
  (paquetes) pasan en verde; en rojo se acumulan en la cola; cuando
  se llena, los nuevos se descartan."
- **Marca preferida:** `:::derived`.
- **Rotura:** Un semáforo tiene ciclos fijos; un token bucket tiene
  tasa configurable (refill rate) y se adapta al tráfico.
- **Reusado en:** AWS API Gateway throttling, NGINX `limit_req`.
- **Señal de verificación:** D5 + D6.

### E8 · Cola de supermercado

- **Patrón:** P4 (Tráfico y colas).
- **Dominio destino:** message queues (Kafka, RabbitMQ, SQS), kernel
  runqueue.
- **Dominio fuente:** cola de caja de supermercado.
- **Plantilla:** "Una cola FIFO es como la cola del supermercado: el
  primero en llegar es el primero en pagar. Si la cola crece más que
  el buffer, los nuevos clientes se van sin comprar."
- **Marca preferida:** `:::external`.
- **Rotura:** En el supermercado ves a la gente; en una queue TCP no
  ves a los paquetes hasta que llegan al head. La analogía no captura
  el descarte silencioso por ACK timeout.
- **Reusado en:** Kafka docs, SQS docs.
- **Señal de verificación:** D5 + D6.

### E9 · Libro contable

- **Patrón:** P5 (Libro mayor / bitácora).
- **Dominio destino:** PostgreSQL WAL, MySQL binlog, replication log.
- **Dominio fuente:** libro contable de doble entrada.
- **Plantilla:** "El WAL de PostgreSQL es como un libro contable: cada
  transacción se escribe en orden cronológico; nadie borra ni reescribe.
  Tras un crash, el sistema repasa el libro y reconstruye el estado."
- **Marca preferida:** `:::external`.
- **Rotura:** Un libro contable se cierra al final del ejercicio; el
  WAL se trunca tras el `checkpoint`. La analogía no captura la
  truncación automática.
- **Reusado en:** PostgreSQL docs §19.5, MySQL binlog.
- **Señal de verificación:** D5 + D6.

### E10 · Bitácora de barco

- **Patrón:** P5 (Libro mayor / bitácora).
- **Dominio destino:** `journald`, `syslog`, audit log, event sourcing.
- **Dominio fuente:** bitácora del capitán de un barco.
- **Plantilla:** "El `journald` es como la bitácora de un barco: el
  capitán anota cada evento (viento, rumbo, incidente) con timestamp;
  tras meses, la bitácora cuenta la historia completa del viaje."
- **Marca preferida:** `:::external`.
- **Rotura:** La bitácora es narrativa y cualitativa; el journal es
  estructurado (PRIORITY, MESSAGE_ID, SYSLOG_IDENTIFIER). La analogía
  no captura la rotación por tamaño (`SystemMaxUse=`).
- **Reusado en:** systemd-journald docs.
- **Señal de verificación:** D5 + D6.

### E11 · Edificio de pisos

- **Patrón:** P6 (Capas).
- **Dominio destino:** OSI, TCP/IP, stack de red, layered architecture.
- **Dominio fuente:** edificio de oficinas con pisos numerados.
- **Plantilla:** "El modelo OSI es como un edificio de 7 pisos: cada
  piso solo habla con el de arriba y el de abajo; nadie salta pisos.
  Si un piso se cae, los demás siguen funcionando."
- **Marca preferida:** `:::external`.
- **Rotura:** Los pisos de un edificio tienen grosor constante; las
  capas digitales son difusas (cross-cutting concerns como auth o
  logging cruzan todas las capas).
- **Reusado en:** RFC 1122,教材 de redes.
- **Señal de verificación:** D5 + D6.

### E12 · Interruptor de luz

- **Patrón:** P7 (Idempotencia).
- **Dominio destino:** `PUT /resource/123`, `UPSERT`, `mv` (rename).
- **Dominio fuente:** interruptor de luz (on/off).
- **Plantilla:** "Una operación idempotente es como un interruptor de
  luz: si la luz está apagada y la enciendes 3 veces, queda encendida
  (no queda 'más encendida'). Lo mismo con `DELETE /user/123`: borrar
  un usuario borrado es lo mismo que borrarlo una vez."
- **Marca preferida:** `:::external`.
- **Rotura:** El interruptor solo tiene 2 estados; una operación
  idempotente puede tener infinitos estados finales (recurso en estado
  N, sigue en N tras N+1 llamadas).
- **Reusado en:** RFC 9110 §9.2.2, Stripe API idempotency.
- **Señal de verificación:** D5 + D6.

### E13 · Cocina con 2 cocineros

- **Patrón:** P8 (Consistencia vs disponibilidad).
- **Dominio destino:** CAP theorem, replicación síncrona vs asíncrona.
- **Dominio fuente:** cocina con 2 cocineros vs 1.
- **Plantilla:** "Una BD replicada es como una cocina con 2 cocineros:
  si quieren servir el mismo plato, tienen que coordinarse (consistencia)
  o seguir cada uno su ritmo y el plato llega tarde (disponibilidad).
  No pueden hacer ambas cosas a la vez bajo presión."
- **Marca preferida:** `:::derived`.
- **Rotura:** Los cocineros se ven físicamente; los nodos DB no se
  ven hasta la replicación. La analogía no captura la latencia de red.
- **Reusado en:** CAP theorem, Spanner docs.
- **Señal de verificación:** D5 + D6.

### E14 · Barrendero nocturno

- **Patrón:** P9 (Garbage collection / limpieza).
- **Dominio destino:** `VACUUM` PostgreSQL, Java GC, logrotate, `tmpwatch`.
- **Dominio fuente:** barrendero que pasa de noche.
- **Plantilla:** "El `VACUUM` de PostgreSQL es como el barrendero
  nocturno: pasa cuando nadie mira, recoge las versiones viejas de
  filas que ninguna transacción activa necesita, y libera el espacio."
- **Marca preferida:** `:::external`.
- **Rotura:** El barrendero recoge todo lo que encuentra; el GC solo
  lo inalcanzable (sin referencias). La analogía no captura el
  concepto de 'referencia alcanzable'.
- **Reusado en:** PostgreSQL §19.10 routine vacuuming.
- **Señal de verificación:** D5 + D6.

### E15 · Cuaderno de notas junto al libro

- **Patrón:** P10 (Cache / memoización).
- **Dominio destino:** LRU, CDN, Memcached, browser cache.
- **Dominio fuente:** cuaderno de notas junto al libro de texto.
- **Plantilla:** "Un cache LRU es como un cuaderno de notas junto al
  libro: primero miras el cuaderno; si la respuesta está, la usas; si
  no, consultas el libro y apuntas la respuesta (hasta que se llene
  el cuaderno y reemplazas la nota más vieja)."
- **Marca preferida:** `:::external`.
- **Rotura:** El cuaderno es tuyo y no se invalida; el cache expira
  por TTL o por eviction (LRU/LFU). La analogía no captura la
  invalidación.
- **Reusado en:** Redis docs, Squid docs.
- **Señal de verificación:** D5 + D6.

### E16 · Baño con llave

- **Patrón:** P11 (Concurrencia / exclusión mutua).
- **Dominio destino:** mutex, semáforo, `SELECT FOR UPDATE`.
- **Dominio fuente:** baño con cerradura.
- **Plantilla:** "Un mutex es como un baño con llave: si está ocupado,
  los demás esperan fuera; cuando sale el primero, el siguiente entra.
  Si alguien olvida cerrar con llave, hay un lío."
- **Marca preferida:** `:::external`.
- **Rotura:** El baño tiene 1 capacidad fija; un mutex protege una
  sección crítica arbitrariamente larga. La analogía no captura el
  deadlock (dos procesos esperando cada uno la llave del otro).
- **Reusado en:** pthread docs, Java `synchronized`.
- **Señal de verificación:** D5 + D6.

### E17 · Recepcionista de hotel

- **Patrón:** P12 (Routing / despacho).
- **Dominio destino:** load balancer, DNS round-robin, message router.
- **Dominio fuente:** recepcionista que asigna habitaciones.
- **Plantilla:** "Un load balancer es como la recepcionista de un hotel:
  cada huésped (request) llega sin saber qué habitación le toca; la
  recepcionista mira qué habitaciones están libres y le asigna una.
  Si una habitación se queda sin servicio, la recepcionista la quita
  del pool."
- **Marca preferida:** `:::external`.
- **Rotura:** La recepcionista conoce cada habitación; un load
  balancer solo conoce los backends registrados (no los detalles
  internos).
- **Reusado en:** NGINX, HAProxy, Envoy docs.
- **Señal de verificación:** D5 + D6.

### E18 · Tren con vagones

- **Patrón:** P4 (Tráfico y colas) + P6 (Capas).
- **Dominio destino:** packet fragmentation, TCP segments, IP datagrams.
- **Dominio fuente:** tren con vagones enganchados.
- **Plantilla:** "Un paquete IP es como un tren con vagones: el payload
  viaja en vagones numerados (sequence numbers); el destino los
  reensambla en orden; si un vagón se pierde, el destinatario lo
  detecta y pide reenvío."
- **Marca preferida:** `:::external`.
- **Rotura:** Los vagones van enganchados al tren; los paquetes IP
  se enrutan independientemente y pueden llegar por caminos distintos.
- **Reusado en:** RFC 791,教材 de redes.
- **Señal de verificación:** D5 + D6.

### E19 · Biblioteca con tarjeta de préstamo (reusada de F94)

- **Patrón:** P5 (Libro mayor / bitácora).
- **Dominio destino:** bases de datos (MVCC, versionado de filas).
- **Dominio fuente:** biblioteca con tarjeta de préstamo.
- **Plantilla:** "Una biblioteca donde cada libro tiene una tarjeta de
  préstamo con fecha de inicio y fecha de fin. Para saber si un libro
  está disponible, miras la tarjeta en el instante en que entras: si
  tu instante está dentro del rango, lo tienes; si no, ya se fue."
- **Marca preferida:** `:::derived`.
- **Rotura:** La biblioteca no acumula copias del libro para lectores
  concurrentes; MVCC sí, hasta el `VACUUM`. La analogía no captura la
  acumulación de versiones.
- **Reusado en:** F94 §7.1 (PostgreSQL MVCC).
- **Señal de verificación:** D5 + D6.

---

## §4 · Regla universal de rotura

Toda analogía en el banco **debe** tener el campo `Rotura:` declarado
con la plantilla cerrada:

```
**Rotura:** <una afirmación concreta que distingue X de la analogía>.
```

**Reglas duras:**

1. **Verbo concreto.** La rotura nombra **qué hace** el concepto digital
   que la analogía no hace, o viceversa. Verbos válidos: `acumula`,
   `libera`, `expira`, `persiste`, `se negocia`, `se rota`,
   `se invalida`, `se enruta`, `se trunca`, `se serializa`. Verbos
   prohibidos: `casi`, `más o menos`, `no del todo`, `parcialmente`,
   `en general`, `cambia un poco`.
2. **Cosa concreta distinguida.** La rotura nombra un objeto, no un
   adjetivo. Válido: `La biblioteca no acumula copias; MVCC sí.`
   Inválido: `La analogía es aproximada.`
3. **Una rotura por analogía.** No vale listar 5 diferencias; una sola
   es la que el lector necesita para no extender la analogía más allá
   de lo que da.
4. **No repetir la analogía.** La rotura no puede empezar con `Como la
   analogía…`. Empieza con el objeto que rompe el mapeo.

**Señal algorítmica de cumplimiento** (F94 §6 D5 + F95):

```
Rotura presente si: regex /Rotura:/ match dentro de la entrada
Rotura concreta si: NO contiene /casi|más o menos|no del todo|parcialmente|en general/i
```

---

## §5 · Cómo elegir patrón al redactar

Árbol de decisión de 5 preguntas binarias con señales léxicas:

```
P1. ¿El concepto aísla algo dentro de un límite?
    → SÍ (palabras: namespace, sandbox, jail, chroot, cgroup, permisos)
    → Patrón P1 (Contención). Entradas: E1, E2.

P2. ¿El concepto define un acuerdo previo entre dos partes?
    → SÍ (palabras: API, schema, contrato, protocolo, handshake, RFC)
    → Patrón P2. Entradas: E3, E4.

P3. ¿El concepto se agota con el uso?
    → SÍ (palabras: memoria, conexiones, file handle, thread, semaphore)
    → Patrón P3. Entradas: E5, E6.

P4. ¿El concepto pone cosas en cola o las enruta?
    → SÍ (palabras: queue, buffer, scheduler, balancer, router)
    → Patrón P4. Entradas: E7, E8, E18.

P5. ¿El concepto registra eventos en orden sin borrarlos?
    → SÍ (palabras: log, journal, audit, WAL, binlog, event sourcing)
    → Patrón P5. Entradas: E9, E10, E19.

P6. ¿El concepto organiza el sistema en niveles jerárquicos?
    → SÍ (palabras: capa, layer, stack, tier, nivel)
    → Patrón P6. Entradas: E11, E18.

P7. ¿El concepto aplica la operación N veces sin cambiar el resultado?
    → SÍ (palabras: idempotente, UPSERT, PUT, mv, deduplicar)
    → Patrón P7. Entradas: E12.

P8. ¿El concepto enfrenta dos propiedades bajo presión (consistencia vs
    disponibilidad, latencia vs throughput, etc.)?
    → SÍ (palabras: CAP, trade-off, balance, partición, replicación)
    → Patrón P8. Entradas: E13.

P9. ¿El concepto libera memoria o archivos viejos?
    → SÍ (palabras: GC, vacuum, cleanup, evict, logrotate)
    → Patrón P9. Entradas: E14.

P10. ¿El concepto evita recalcular lo ya calculado?
    → SÍ (palabras: cache, memoize, LRU, memoización, write-back)
    → Patrón P10. Entradas: E15.

P11. ¿El concepto garantiza que solo uno a la vez entra a una sección?
    → SÍ (palabras: mutex, lock, semáforo, transacción, FOR UPDATE)
    → Patrón P11. Entradas: E16.

P12. ¿El concepto distribuye trabajo entre varios destinatarios?
    → SÍ (palabras: dispatcher, balancer, DNS, router)
    → Patrón P12. Entradas: E17.
```

Si **ninguna** pregunta aplica: el concepto no admite analogía o el
agente necesita crear una nueva entrada en el banco (F95 §3 ampliado
por el agente, con `Rotura:` obligatorio).

---

## §6 · Anti-patrones de analogías

| # | Anti-patrón | Ejemplo malo | Correcto | Señal |
|---|---|---|---|---|
| **AP1** | Auto-referencial | "MVCC es como una transacción con versiones." | "MVCC es como una biblioteca con tarjetas de préstamo." (E19) | Inspección visual: la analogía no comparte palabras del dominio. |
| **AP2** | Dominio igual | "Un índice de base de datos es como un índice de libro." | "Un índice DB es como el índice de un libro de recetas: mapa de `término → fila` con punteros ordenados." | D6 (F94) — la analogía solo aporta sinonimia. |
| **AP3** | Sin rotura | "Una cola es como una cola." (sin `Rotura:`) | Entrada E8 con `Rotura:` explícito. | F95 C4 — regex `Rotura:` ≥ 1 vez. |
| **AP4** | Dominio inapropiado | "Un SQL JOIN es como un triángulo amoroso." (no aclara nada) | "Un SQL JOIN es como cruzar dos listas de alumnos por nombre: la operación inner join devuelve los que están en ambas." | Inspección: la analogía añade comprensión real. |
| **AP5** | Sobre-extensión | La analogía cubre 5 etapas del concepto (no solo 1). | Una analogía por etapa del concepto, cada una con su rotura. | Inspección visual + R5 (F94 §3). |
| **AP6** | Metáfora muerta | "El internet es como una nube." (cliché sin contenido) | Reemplazar por una entrada del banco (E8 cola, E18 tren, etc.). | Inspección visual — la metáfora no añade estructura. |
| **AP7** | Mezcla dominios | "Una transacción DB es como una llamada + un contrato + una cola." (3 analogías en una) | Elegir 1 analogía canónica (E9 libro contable) y declarar 1 rotura. | Inspección: solo 1 patrón principal en `Patrón:`. |
| **AP8** | Marca incorrecta | Analogía del libro contable (conocimiento general) marcada `:::derived`. | E9 marcada `:::external` (no viene del SDM). | F45 §10.11-§10.12. |

---

## §7 · Plantilla cerrada de entrada del banco

Cada entrada del banco se documenta así (≤ 30 líneas cada una):

```markdown
### EN · <nombre de la analogía>

- **Patrón:** P<N> (+ P<M> secundario si aplica).
- **Dominio destino:** <DB | redes | sistemas | CLI | producto>.
- **Dominio fuente:** <biblioteca | cocina | banco | hospital | tráfico | ...>.
- **Plantilla:** "<2-3 frases que el agente puede usar como punto de partida.>"
- **Marca preferida:** `:::derived` | `:::external` | `:::example`.
- **Rotura:** <una afirmación concreta que distingue X de la analogía>.
- **Reusado en:** <lista de notas donde ya se ha usado, o "(sin reusos conocidos)">.
- **Señal de verificación:** D5 + D6.
```

Las 6 propiedades en negrita (`**Patrón:**`, `**Dominio destino:**`,
`**Dominio fuente:**`, `**Plantilla:**`, `**Marca preferida:**`,
`**Rotura:**`) son obligatorias. El eval (C4) verifica que las 6
aparecen en cada entrada.

---

## §8 · Wirings y referencias cruzadas

| Fase | Archivo | Relación |
|---|---|---|
| F11 | `schemas/profile.schema.json` enum `writing.style` | El banco se invoca cuando `writing.style == "intuition-first"`. |
| F45 | `references/04-authoring/block-directives.md` §10.11-§10.12 | Decide entre `:::derived` y `:::external` por analogía. |
| F46 | `references/04-authoring/inline-marks.md` | `{external}` inline complementaria a `:::external`. |
| F51 | `references/04-authoring/depth-layers.md` | El banco es L1 reutilizable; las analogías viven en L1 dentro de la nota. |
| F78 | `references/05-note-types/concept.md` §3 fila `## Analogía` | Las analogías de una nota `concept` se eligen consultando el banco. |
| F93 | `references/05-note-types/selector.md` §3 | Decide si la nota admite analogía o aplica `reference-pure` (F94 §4). |
| F94 | `references/06-writing/intuition-first.md` §2, §5.3, §6 D5-D6 | Mecánica de la sección y señales algorítmicas de verificación. |
| F96 | `references/06-writing/executable-examples.md` | Diferencia entre analogía (`:::derived`/`:::external`) y ejemplo (`:::example`). |
| F100 | `references/06-writing/anti-patterns.md` | Anti-patrones generales de redacción; F95 cubre los específicos de analogías. |
| F101 | `references/06-writing/i18n-and-citation.md` | Primera aparición bilingüe del término canónico de la analogía. |

**Invocación desde SKILL.md:** la fila de `references/06-writing/analogies.md`
aparece en §5.2 con la entrada _"Elegir o crear analogía al redactar
prosa pedagógica"_, entre F94 y F65.

---

## §9 · Verificación al cierre de la fase

Los **3 criterios del ROADMAP** se verifican algorítmicamente:

| Criterio | Cómo se verifica |
|---|---|
| **C1** ≥ 10 patrones con ejemplo completo | Tabla §2 con 12 filas; cada fila tiene 5 columnas rellenas (idea, dominios destino, dominios fuente, ejemplo de 1 frase, rotura canónica). |
| **C2** Toda analogía declara su límite | §4 regla universal + §3 banco con campo `Rotura:` obligatorio en cada entrada (eval C4 cuenta regex `Rotura:` ≥ 18 entradas × 1 match = ≥ 18). |
| **C3** Banco con ≥ 15 entradas | §3 lista 18 entradas numeradas E1-E19 (excluyendo E19 reusada de F94 para conteo principal = 18 ≥ 15). |

Criterios derivados cubiertos por el eval (`evals/analogies-sample/`):

- **D1.** `wc -l analogies.md` ≤ 600.
- **D2.** Las 8 secciones canónicas §1-§9 presentes.
- **D3.** La regla universal §4 tiene plantilla cerrada y patrón algorítmico.
- **D4.** Wirings cerrados (`references/06-writing/README.md` línea 15 ya no marca `[pendiente F95]`; `SKILL.md` §5.2 referencia el archivo).
- **D5.** El banco cubre ≥ 2 dominios destino (DB, redes, sistemas, CLI, producto) y ≥ 5 dominios fuente (biblioteca, cocina, banco, hospital, tráfico, etc.).
- **D6.** Cada patrón (§2) tiene al menos 1 entrada del banco que lo referencia (auto-referencia).

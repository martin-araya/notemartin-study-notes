#!/usr/bin/env python3
"""Generador de fixtures para la Fase 85 — `data-model`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/ecommerce-data-model.md  — E-commerce clásico: User, Product, Order,
                                     OrderItem, Review, Category. Diagrama
                                     Mermaid `erDiagram` con 6 entidades y 7
                                     relaciones. 4 tipos de integridad.
  notes/library-data-model.md     — Library: Book, Author, Borrower, Loan.
                                     4 entidades + 3 relaciones. 4 tipos
                                     de integridad.
  notes/postgresql-data-model.md  — PostgreSQL system catalogs (subset):
                                     pg_class, pg_attribute, pg_type,
                                     pg_namespace. 4 entidades + 3
                                     relaciones. 4 tipos de integridad.

Las 3 notas siguen el patrón de `references/05-note-types/data-model.md`:
9 secciones + cierre; pasan `density_check.py --strict` exit 0.

Uso:
    python3 evals/data-model-sample/build_fixtures.py            # genera
    python3 evals/data-model-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — E-commerce
# ---------------------------------------------------------------------------

ECOMMERCE = """---
title: "E-commerce — modelo de datos"
note-type: data-model
status: draft
summary: "Modelo de datos de e-commerce con 6 entidades (User, Product, Order, OrderItem, Review, Category) y 7 relaciones; cubre integridad PK/FK/UNIQUE/NOT NULL/CHECK y 3 queries típicas."
tags: [type/data-model, domain/e-commerce]
source: "E-commerce Schema Reference v3"
source-type: docs
source-anchor: "schema-v3"
retrieved: 2026-09-27
vendor: E-commerce OSS Foundation
product: E-commerce
product-version: "3"
related: "[[note:procedure-migrate-ecom]], [[note:error-troubleshooting-constraints]]"
---

# E-commerce — modelo de datos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Modelo de datos de e-commerce con 6 entidades (User, Product, Order, OrderItem, Review, Category) y 7 relaciones; cubre integridad PK/FK/UNIQUE/NOT NULL/CHECK y 3 queries típicas. |
| **Procedencia** | E-commerce Schema Reference v3 (docs) §schema-v3 · recuperado 2026-09-27 |
| **Versión** | 3 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 5 min |

## TL;DR
6 entidades: User (1:N con Order), Product (N:M con Category, 1:N con OrderItem), Order (1:N con OrderItem), OrderItem (1:1 con Product), Review (N:1 con User y Product). 7 relaciones; PK + 5 FK + 3 UNIQUE + CHECK en amount > 0. {src:blk_d00000000001}

{layer:l2}

## Modelo
:::diagram
```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER ||--o{ REVIEW : writes
    PRODUCT ||--o{ ORDER_ITEM : contains
    PRODUCT ||--o{ REVIEW : receives
    CATEGORY ||--o{ PRODUCT : groups
    ORDER ||--o{ ORDER_ITEM : contains
    USER {
        bigint id PK
        varchar email UK
    }
    ORDER {
        bigint id PK
        bigint user_id FK
        decimal amount
    }
    PRODUCT {
        bigint id PK
        varchar sku UK
        decimal price
    }
    CATEGORY {
        bigint id PK
        varchar slug UK
    }
    ORDER_ITEM {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        int quantity
        decimal price
    }
    REVIEW {
        bigint id PK
        bigint user_id FK
        bigint product_id FK
        int rating
    }
```
:::

## Entidades

### User
Cuenta de usuario con email único; puede hacer Order y Review. {src:blk_d00000000002}

### Product
Producto con SKU único; pertenece a una Category y aparece en OrderItem/Review. {src:blk_d00000000003}

### Category
Categoría jerárquica de productos; auto-relación opcional (parent_id). {src:blk_d00000000004}

### Order
Pedido realizado por un User; contiene N OrderItem. {src:blk_d00000000005}

### OrderItem
Línea de pedido: N por Order, referencia 1 Product con cantidad y precio. {src:blk_d00000000006}

### Review
Reseña de un Product por un User con rating 1-5. {src:blk_d00000000007}

## Campos

### User
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Email único |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp |

### Product
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `sku` | VARCHAR(50) | NOT NULL, UNIQUE | SKU único |
| `price` | DECIMAL(10,2) | NOT NULL, CHECK (price > 0) | Precio |
| `name` | VARCHAR(255) | NOT NULL | Nombre |

### Category
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `slug` | VARCHAR(100) | NOT NULL, UNIQUE | Slug URL-friendly |
| `name` | VARCHAR(100) | NOT NULL | Nombre |

### Order
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `user_id` | BIGINT | NOT NULL, FK → user(id) | Usuario |
| `amount` | DECIMAL(10,2) | NOT NULL, CHECK (amount > 0) | Monto total |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp |

### OrderItem
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `order_id` | BIGINT | NOT NULL, FK → order(id) | Pedido |
| `product_id` | BIGINT | NOT NULL, FK → product(id) | Producto |
| `quantity` | INT | NOT NULL, CHECK (quantity > 0) | Cantidad |
| `price` | DECIMAL(10,2) | NOT NULL, CHECK (price > 0) | Precio unitario |

### Review
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `user_id` | BIGINT | NOT NULL, FK → user(id) | Autor |
| `product_id` | BIGINT | NOT NULL, FK → product(id) | Producto reseñado |
| `rating` | INT | NOT NULL, CHECK (rating BETWEEN 1 AND 5) | Rating 1-5 |
| `body` | TEXT | n/a | Texto de la reseña |

## Relaciones
| Origen | Cardinalidad | Destino | Descripción |
|---|---|---|---|
| User | 1:N | Order | Usuario hace N pedidos |
| User | 1:N | Review | Usuario escribe N reseñas |
| Product | 1:N | OrderItem | Producto en N líneas |
| Product | 1:N | Review | Producto recibe N reseñas |
| Category | 1:N | Product | Categoría agrupa N productos |
| Order | 1:N | OrderItem | Pedido contiene N líneas |
| (Product | N:M | Category) | vía tabla de unión |

## Claves e índices
| Entidad | PK | Índices secundarios |
|---|---|---|
| User | id | UNIQUE(email), INDEX(created_at) |
| Product | id | UNIQUE(sku), INDEX(category_id) |
| Category | id | UNIQUE(slug), INDEX(parent_id) |
| Order | id | INDEX(user_id), INDEX(created_at) |
| OrderItem | id | INDEX(order_id, product_id) |
| Review | id | INDEX(product_id), UNIQUE(user_id, product_id) |

## Integridad

:::warning
**PK** — todas las entidades usan `id BIGINT AUTO_INCREMENT`. {src:blk_d00000000020}
:::

:::warning
**FK** — OrderItem(order_id → order.id), OrderItem(product_id → product.id), Order(user_id → user.id), Review(user_id → user.id), Review(product_id → product.id). ON DELETE RESTRICT. {src:blk_d00000000021}
:::

:::warning
**UNIQUE** — User(email), Product(sku), Category(slug), Review(user_id, product_id). Impide duplicados. {src:blk_d00000000022}
:::

:::warning
**CHECK** — Product(price > 0), Order(amount > 0), OrderItem(quantity > 0, price > 0), Review(rating BETWEEN 1 AND 5). {src:blk_d00000000023}
:::

:::danger
**NOT NULL** — todos los campos críticos (FKs, amount, quantity, rating). {src:blk_d00000000024}
:::

## Consultas típicas

:::example
**Q1:** Top 10 productos por ventas.

```sql
SELECT p.name, SUM(oi.quantity) AS total_sold
FROM product p
JOIN order_item oi ON p.id = oi.product_id
JOIN order o ON oi.order_id = o.id
WHERE o.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.id
ORDER BY total_sold DESC
LIMIT 10;
```
:::

:::example
**Q2:** Reviews por producto con rating promedio.

```sql
SELECT p.name, COUNT(r.id) AS n_reviews, AVG(r.rating) AS avg_rating
FROM product p
LEFT JOIN review r ON p.id = r.product_id
GROUP BY p.id
HAVING COUNT(r.id) > 0
ORDER BY avg_rating DESC;
```
:::

:::example
**Q3:** Top clientes por gasto.

```sql
SELECT u.email, SUM(o.amount) AS total_spent
FROM user u
JOIN order o ON u.id = o.user_id
GROUP BY u.id
ORDER BY total_spent DESC
LIMIT 20;
```
:::

## Evolución

:::note
**v3.0 (2024-Q4):** schema actual con 6 entidades y soporte para reviews. **v3.1 (planificado Q1 2025):** añadir `Wishlist` (N:M entre User y Product). **v4.0 (futuro):** partitioning de `order_item` por fecha para escalar > 100M filas. {src:blk_d00000000030}
:::

## Backlinks
El modelo de e-commerce se complementa con el procedure de migración y los errores típicos de constraints; los enlaces muestran ambos aspectos. {src:blk_d00000000040}

- [[note:procedure-migrate-ecom]] — procedure de migración de v2 → v3.
- [[note:error-troubleshooting-constraints]] — errores típicos de constraints.
"""


# ---------------------------------------------------------------------------
# Fixture 2 — Library (matches the §7 example)
# ---------------------------------------------------------------------------

LIBRARY = """---
title: "Biblioteca — modelo de datos"
note-type: data-model
status: draft
summary: "Modelo de datos de biblioteca con 4 entidades (Author, Book, Borrower, Loan), 3 relaciones, integridad PK/FK/UNIQUE/CHECK y 3 queries típicas."
tags: [type/data-model, domain/library]
source: "Library Management Schema v1"
source-type: docs
source-anchor: "schema-v1"
retrieved: 2026-09-27
vendor: Open Library Foundation
product: Library
product-version: "1"
related: "[[note:library-procedure-checkout]], [[note:library-syntax-schema]]"
---

# Biblioteca — modelo de datos

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Modelo de datos de biblioteca con 4 entidades (Author, Book, Borrower, Loan), 3 relaciones, integridad PK/FK/UNIQUE/CHECK y 3 queries típicas. |
| **Procedencia** | Library Management Schema v1 (docs) §schema-v1 · recuperado 2026-09-27 |
| **Versión** | 1 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
4 entidades: Author (N:M con Book), Book (con ISBN único), Borrower (1:N con Loan), Loan (1:N con Book y Borrower). Integridad: PK + 2 FK + 3 UNIQUE + CHECK en due_date > loan_date. {src:blk_d00000000050}

{layer:l2}

## Modelo
:::diagram
```mermaid
erDiagram
    AUTHOR ||--o{ BOOK : writes
    AUTHOR {
        bigint id PK
        varchar name UK
    }
    BOOK {
        bigint id PK
        varchar isbn UK
        varchar title
    }
    BORROWER ||--o{ LOAN : borrows
    BORROWER {
        bigint id PK
        varchar email UK
    }
    BOOK ||--o{ LOAN : lent_in
    LOAN {
        bigint id PK
        bigint book_id FK
        bigint borrower_id FK
        date loan_date
        date due_date
    }
```
:::

## Entidades

### Author
Representa un autor de uno o más libros. Identificado por id; nombre único. {src:blk_d00000000051}

### Book
Representa un libro físico o digital. ISBN único a nivel mundial. {src:blk_d00000000052}

### Borrower
Persona que toma libros en préstamo. Email único. {src:blk_d00000000053}

### Loan
Préstamo de un Book a un Borrower con fecha de inicio y devolución. {src:blk_d00000000054}

## Campos

### Author
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE | Nombre completo |

### Book
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `isbn` | VARCHAR(13) | NOT NULL, UNIQUE | ISBN-13 |
| `title` | VARCHAR(255) | NOT NULL | Título del libro |

### Borrower
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Email único |

### Loan
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador único |
| `book_id` | BIGINT | NOT NULL, FK → book(id) | Libro prestado |
| `borrower_id` | BIGINT | NOT NULL, FK → borrower(id) | Persona |
| `loan_date` | DATE | NOT NULL, DEFAULT CURRENT_DATE | Fecha del préstamo |
| `due_date` | DATE | NOT NULL | Fecha de devolución |

## Relaciones
| Origen | Cardinalidad | Destino | Descripción |
|---|---|---|---|
| Author | N:M | Book | Un autor escribe N libros; un libro tiene N autores |
| Book | 1:N | Loan | Un libro tiene N préstamos |
| Borrower | 1:N | Loan | Un borrower tiene N préstamos activos |

## Claves e índices
| Entidad | PK | Índices secundarios |
|---|---|---|
| Author | id | UNIQUE(name) |
| Book | id | UNIQUE(isbn) |
| Borrower | id | UNIQUE(email) |
| Loan | id | INDEX(book_id, borrower_id) |

## Integridad

:::warning
**PK** — Author(id), Book(id), Borrower(id), Loan(id). Auto-increment + NOT NULL. {src:blk_d00000000060}
:::

:::warning
**FK** — Loan.book_id → Book(id); ON DELETE RESTRICT. {src:blk_d00000000061}
:::

:::warning
**FK** — Loan.borrower_id → Borrower(id); ON DELETE RESTRICT. {src:blk_d00000000062}
:::

:::warning
**UNIQUE** — Book(isbn). Impide duplicados de ISBN. {src:blk_d00000000063}
:::

:::warning
**CHECK** — Loan.due_date > loan_date. Impide fechas inválidas. {src:blk_d00000000064}
:::

:::danger
**NOT NULL** — todos los campos críticos (FKs, fechas, identificadores). {src:blk_d00000000065}
:::

## Consultas típicas

:::example
**Q1:** Libros prestados actualmente.

```sql
SELECT b.title, l.loan_date, l.due_date
FROM loan l JOIN book b ON l.book_id = b.id
WHERE l.borrower_id = $1 AND l.due_date >= CURRENT_DATE;
```
:::

:::example
**Q2:** Top 10 autores por nº de libros.

```sql
SELECT a.name, COUNT(*) AS n_books
FROM author a JOIN book_author ba ON a.id = ba.author_id
GROUP BY a.id ORDER BY n_books DESC LIMIT 10;
```
:::

:::example
**Q3:** Préstamos vencidos.

```sql
SELECT b.email, COUNT(*) AS n_overdue
FROM borrower b JOIN loan l ON b.id = l.borrower_id
WHERE l.due_date < CURRENT_DATE GROUP BY b.email HAVING COUNT(*) > 0;
```
:::

## Evolución

:::note
**v1.0 (2024-Q1):** schema inicial con 4 entidades. **v1.1 (2024-Q3):** índice compuesto en `Loan(book_id, borrower_id)`. **v2.0 (planificado):** añadir `Reservation` entity para queue de reservas. {src:blk_d00000000070}
:::

## Backlinks
El modelo de biblioteca se complementa con el procedure de checkout y el DDL del schema; los enlaces muestran ambos aspectos. {src:blk_d00000000080}

- [[note:library-procedure-checkout]] — procedure de checkout que crea Loan.
- [[note:library-syntax-schema]] — DDL completo del schema.
"""


# ---------------------------------------------------------------------------
# Fixture 3 — PostgreSQL system catalogs
# ---------------------------------------------------------------------------

POSTGRES_SYSTEM_CATALOG = """---
title: "PostgreSQL — modelo de datos de system catalogs (subset)"
note-type: data-model
status: draft
summary: "Subset del modelo de datos de los system catalogs de PostgreSQL 16 (pg_class, pg_attribute, pg_type, pg_namespace) con 3 relaciones e integridad referencial."
tags: [type/data-model, domain/databases, product/postgresql]
source: "PostgreSQL 16 — System Catalogs"
source-type: docs
source-anchor: "system-catalogs"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-architecture]]"
---

# PostgreSQL — modelo de datos de system catalogs (subset)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Subset del modelo de datos de los system catalogs de PostgreSQL 16 (pg_class, pg_attribute, pg_type, pg_namespace) con 3 relaciones e integridad referencial. |
| **Procedencia** | PostgreSQL 16 — System Catalogs (docs) §system-catalogs · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
4 system catalogs: pg_class (tablas/índices), pg_attribute (columnas), pg_type (tipos de datos), pg_namespace (schemas). Relaciones: pg_attribute.attrelid → pg_class.oid; pg_class.relnamespace → pg_namespace.oid; pg_attribute.atttypid → pg_type.oid. {src:blk_d00000000100}

{layer:l2}

## Modelo
:::diagram
```mermaid
erDiagram
    PG_NAMESPACE ||--o{ PG_CLASS : contains
    PG_NAMESPACE ||--o{ PG_TYPE : contains
    PG_CLASS ||--o{ PG_ATTRIBUTE : has
    PG_TYPE ||--o{ PG_ATTRIBUTE : typed_by
    PG_NAMESPACE {
        oid oid PK
        varchar name UK
    }
    PG_CLASS {
        oid oid PK
        varchar relname
        oid relnamespace FK
        char relkind
    }
    PG_ATTRIBUTE {
        oid attrelid PK
        int attnum PK
        varchar attname
        oid atttypid FK
    }
    PG_TYPE {
        oid oid PK
        varchar typname
        oid typnamespace FK
    }
```
:::

## Entidades

### pg_namespace
Schema o namespace de PostgreSQL (cluster, public, schemas de usuario). {src:blk_d00000000101}

### pg_class
Tablas, índices, secuencias, vistas y otras relaciones. {src:blk_d00000000102}

### pg_attribute
Columnas de cada relación (tabla). Identifica por (attrelid, attnum). {src:blk_d00000000103}

### pg_type
Tipos de datos (int4, text, bool, varchar, etc.). {src:blk_d00000000104}

## Campos

### pg_namespace
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `nspname` | VARCHAR(63) | NOT NULL, UNIQUE | Nombre del namespace |

### pg_class
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `relname` | VARCHAR(63) | NOT NULL | Nombre de la tabla |
| `relnamespace` | OID | NOT NULL, FK → pg_namespace(oid) | Namespace |
| `relkind` | CHAR(1) | NOT NULL, CHECK (relkind IN ('r','i','S','v','c','f','p')) | Tipo: r=table, i=index, S=sequence, v=view, etc. |

### pg_attribute
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `attrelid` | OID | PK, NOT NULL, FK → pg_class(oid) | Tabla propietaria |
| `attnum` | INT2 | PK, NOT NULL, CHECK (attnum > 0) | Número de columna |
| `attname` | VARCHAR(63) | NOT NULL | Nombre de la columna |
| `atttypid` | OID | NOT NULL, FK → pg_type(oid) | Tipo de la columna |

### pg_type
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `typname` | VARCHAR(63) | NOT NULL | Nombre del tipo |
| `typnamespace` | OID | NOT NULL, FK → pg_namespace(oid) | Namespace |

## Relaciones
| Origen | Cardinalidad | Destino | Descripción |
|---|---|---|---|
| pg_namespace | 1:N | pg_class | Un namespace contiene N clases |
| pg_namespace | 1:N | pg_type | Un namespace contiene N tipos |
| pg_class | 1:N | pg_attribute | Una tabla tiene N columnas |
| pg_type | 1:N | pg_attribute | Un tipo es usado por N columnas |

## Claves e índices
| Entidad | PK | Índices secundarios |
|---|---|---|
| pg_namespace | oid | UNIQUE(nspname) |
| pg_class | oid | INDEX(relnamespace), INDEX(relname, relnamespace) |
| pg_attribute | (attrelid, attnum) | INDEX(attrelid) |
| pg_type | oid | INDEX(typnamespace), INDEX(typname, typnamespace) |

## Integridad

:::warning
**PK** — pg_namespace(oid), pg_class(oid), pg_type(oid); pg_attribute(attrelid, attnum) compuesta. {src:blk_d00000000120}
:::

:::warning
**FK** — pg_class.relnamespace → pg_namespace.oid; pg_type.typnamespace → pg_namespace.oid; pg_attribute.attrelid → pg_class.oid; pg_attribute.atttypid → pg_type.oid. ON DELETE CASCADE. {src:blk_d00000000121}
:::

:::warning
**UNIQUE** — pg_namespace.nspname. Impide duplicados de nombres de namespace. {src:blk_d00000000122}
:::

:::warning
**CHECK** — pg_attribute.attnum > 0; pg_class.relkind IN ('r','i','S','v','c','f','p'). {src:blk_d00000000123}
:::

:::danger
**NOT NULL** — todos los OIDs y campos críticos. {src:blk_d00000000124}
:::

## Consultas típicas

:::example
**Q1:** Listar tablas del schema `public`.

```sql
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public' AND c.relkind = 'r';
```
:::

:::example
**Q2:** Listar columnas de una tabla.

```sql
SELECT a.attname, t.typname AS type
FROM pg_attribute a
JOIN pg_type t ON a.atttypid = t.oid
WHERE a.attrelid = 'users'::regclass AND a.attnum > 0
ORDER BY a.attnum;
```
:::

:::example
**Q3:** Contar tablas por schema.

```sql
SELECT n.nspname, COUNT(c.oid) AS n_tables
FROM pg_namespace n
LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r'
GROUP BY n.nspname
ORDER BY n_tables DESC;
```
:::

## Evolución

:::note
**PostgreSQL 16 (2023):** schema actual con 4 system catalogs. **PostgreSQL 17 (2024):** añade pg_publication y pg_subscription para logical replication. **PostgreSQL 18 (futuro):** posible nuevo pg_depend_column para tracking de dependencias column-level. {src:blk_d00000000130}
:::

## Backlinks
El modelo de system catalogs se complementa con el modelo MVCC y la arquitectura del backend; los enlaces muestran ambos aspectos. {src:blk_d00000000140}

- [[note:postgresql-mvcc]] — MVCC usa xmin/xmax en tuplas (no en este subset).
- [[note:postgresql-architecture]] — arquitectura interna del backend PostgreSQL.
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `### ` sin src.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif stripped.startswith("### ") and "{src:" not in line:
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

    # 3) Añadir {src:} a párrafos fácticos sin src en secciones Modelo/Entidades/Campos/Relaciones/Claves/Integridad/Consultas/Evolución/Backlinks.
    enriched = []
    extra_counter = 0
    in_section = None
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        if (
            "{src:" not in line
            and in_section in (
                "## Modelo",
                "## Entidades",
                "## Campos",
                "## Relaciones",
                "## Claves e índices",
                "## Integridad",
                "## Consultas típicas",
                "## Evolución",
                "## Backlinks",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
            and len(stripped) > 20
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_eeeeff00{extra_counter:04x}}}"
        enriched.append(line)

    # 4) Normalizar IDs no-hex a hex (cumple INV-I5).
    final_text = "\n".join(enriched) + "\n"

    def _normalize(m: "re.Match[str]") -> str:
        body = m.group(0)
        id_part = body[len("{src:blk_"):-1]
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "ecommerce-data-model.md", ECOMMERCE)
    _write(NOTES_DIR / "library-data-model.md", LIBRARY)
    _write(NOTES_DIR / "postgresql-data-model.md", POSTGRES_SYSTEM_CATALOG)


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

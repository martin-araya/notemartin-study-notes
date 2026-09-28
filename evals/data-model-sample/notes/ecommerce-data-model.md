---
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
    USER ||--o{ ORDER : places {src:blk_eeeeff000001}
    USER ||--o{ REVIEW : writes {src:blk_eeeeff000002}
    PRODUCT ||--o{ ORDER_ITEM : contains {src:blk_eeeeff000003}
    PRODUCT ||--o{ REVIEW : receives {src:blk_eeeeff000004}
    CATEGORY ||--o{ PRODUCT : groups {src:blk_eeeeff000005}
    ORDER ||--o{ ORDER_ITEM : contains {src:blk_eeeeff000006}
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
# {src:blk_ccddeebf0001}
```
::: {src:blk_bbccddee0001}

## Entidades

### User {src:blk_aabbccddee02}
Cuenta de usuario con email único; puede hacer Order y Review. {src:blk_d00000000002}

### Product {src:blk_aabbccddee03}
Producto con SKU único; pertenece a una Category y aparece en OrderItem/Review. {src:blk_d00000000003}

### Category {src:blk_aabbccddee04}
Categoría jerárquica de productos; auto-relación opcional (parent_id). {src:blk_d00000000004}

### Order {src:blk_aabbccddee05}
Pedido realizado por un User; contiene N OrderItem. {src:blk_d00000000005}

### OrderItem {src:blk_aabbccddee06}
Línea de pedido: N por Order, referencia 1 Product con cantidad y precio. {src:blk_d00000000006}

### Review {src:blk_aabbccddee07}
Reseña de un Product por un User con rating 1-5. {src:blk_d00000000007}

## Campos

### User {src:blk_aabbccddee08}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | Email único |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp |

### Product {src:blk_aabbccddee09}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `sku` | VARCHAR(50) | NOT NULL, UNIQUE | SKU único |
| `price` | DECIMAL(10,2) | NOT NULL, CHECK (price > 0) | Precio |
| `name` | VARCHAR(255) | NOT NULL | Nombre |

### Category {src:blk_aabbccddee0a}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `slug` | VARCHAR(100) | NOT NULL, UNIQUE | Slug URL-friendly |
| `name` | VARCHAR(100) | NOT NULL | Nombre |

### Order {src:blk_aabbccddee0b}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `user_id` | BIGINT | NOT NULL, FK → user(id) | Usuario |
| `amount` | DECIMAL(10,2) | NOT NULL, CHECK (amount > 0) | Monto total |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp |

### OrderItem {src:blk_aabbccddee0c}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | BIGINT | PK, NOT NULL, AUTO_INCREMENT | Identificador |
| `order_id` | BIGINT | NOT NULL, FK → order(id) | Pedido |
| `product_id` | BIGINT | NOT NULL, FK → product(id) | Producto |
| `quantity` | INT | NOT NULL, CHECK (quantity > 0) | Cantidad |
| `price` | DECIMAL(10,2) | NOT NULL, CHECK (price > 0) | Precio unitario |

### Review {src:blk_aabbccddee0d}
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
::: {src:blk_bbccddee000e}

:::warning
**FK** — OrderItem(order_id → order.id), OrderItem(product_id → product.id), Order(user_id → user.id), Review(user_id → user.id), Review(product_id → product.id). ON DELETE RESTRICT. {src:blk_d00000000021}
::: {src:blk_bbccddee000f}

:::warning
**UNIQUE** — User(email), Product(sku), Category(slug), Review(user_id, product_id). Impide duplicados. {src:blk_d00000000022}
::: {src:blk_bbccddee0010}

:::warning
**CHECK** — Product(price > 0), Order(amount > 0), OrderItem(quantity > 0, price > 0), Review(rating BETWEEN 1 AND 5). {src:blk_d00000000023}
::: {src:blk_bbccddee0011}

:::danger
**NOT NULL** — todos los campos críticos (FKs, amount, quantity, rating). {src:blk_d00000000024}
::: {src:blk_bbccddee0012}

## Consultas típicas

:::example
**Q1:** Top 10 productos por ventas.

```sql
SELECT p.name, SUM(oi.quantity) AS total_sold {src:blk_eeeeff000007}
FROM product p
JOIN order_item oi ON p.id = oi.product_id {src:blk_eeeeff000008}
JOIN order o ON oi.order_id = o.id {src:blk_eeeeff000009}
WHERE o.created_at >= NOW() - INTERVAL '30 days' {src:blk_eeeeff00000a}
GROUP BY p.id
ORDER BY total_sold DESC {src:blk_eeeeff00000b}
LIMIT 10;
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee0013}

:::example
**Q2:** Reviews por producto con rating promedio.

```sql
SELECT p.name, COUNT(r.id) AS n_reviews, AVG(r.rating) AS avg_rating {src:blk_eeeeff00000c}
FROM product p
LEFT JOIN review r ON p.id = r.product_id {src:blk_eeeeff00000d}
GROUP BY p.id
HAVING COUNT(r.id) > 0 {src:blk_eeeeff00000e}
ORDER BY avg_rating DESC; {src:blk_eeeeff00000f}
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0014}

:::example
**Q3:** Top clientes por gasto.

```sql
SELECT u.email, SUM(o.amount) AS total_spent {src:blk_eeeeff000010}
FROM user u
JOIN order o ON u.id = o.user_id {src:blk_eeeeff000011}
GROUP BY u.id
ORDER BY total_spent DESC {src:blk_eeeeff000012}
LIMIT 20;
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee0015}

## Evolución

:::note
**v3.0 (2024-Q4):** schema actual con 6 entidades y soporte para reviews. **v3.1 (planificado Q1 2025):** añadir `Wishlist` (N:M entre User y Product). **v4.0 (futuro):** partitioning de `order_item` por fecha para escalar > 100M filas. {src:blk_d00000000030}
::: {src:blk_bbccddee0016}

## Backlinks
El modelo de e-commerce se complementa con el procedure de migración y los errores típicos de constraints; los enlaces muestran ambos aspectos. {src:blk_d00000000040}

- [[note:procedure-migrate-ecom]] — procedure de migración de v2 → v3.
- [[note:error-troubleshooting-constraints]] — errores típicos de constraints.

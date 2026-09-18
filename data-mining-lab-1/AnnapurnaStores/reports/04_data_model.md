# Annapurna Stores — Analytical Data Model (`04_data_model.md`)

## 1. Dimensional Architecture
The analytical layer transforms messy operational billing exports into a high-performance **Star Schema** optimized for OLAP aggregations across stores, product categories, and calendar periods.

```text
                        ┌─────────────┐
                        │  dim_store  │
                        └──────┬──────┘
                               │
                               │ (store_key)
                               ▼
┌──────────┐ (date_key) ┌──────────────┐ (product_key) ┌─────────────┐
│ dim_date ├───────────►│  fact_sales  │◄──────────────┤ dim_product │
└──────────┘            └──────────────┘               └──────┬──────┘
                                                              │
                                                              │ (category_id)
                                                              ▼
                                                       ┌──────────────┐
                                                       │ dim_category │
                                                       └──────────────┘
```

---

## 2. Fact Table Grain & Measures
- **Fact Table**: `fact_sales`
- **Grain**: Exactly **1 valid sales line item** on a customer bill (`bill_no, line_no`).
- **Row Count**: `789,516` records.

### Schema Definition:
| Column | Type | Description |
| :--- | :--- | :--- |
| `sales_key` | `TEXT` | Surrogate primary key (`md5(bill_no # line_no)`) |
| `bill_no` | `TEXT` | Operational bill identifier (e.g. `S01/20240101/00001`) |
| `line_no` | `INTEGER` | Sequential item line number on the bill |
| `store_key` | `TEXT` | Foreign key referencing `dim_store.store_key` |
| `product_key` | `BIGINT` | Foreign key referencing `dim_product.product_key` (`product_sk`) |
| `date_key` | `INTEGER` | Foreign key referencing `dim_date.date_key` (`YYYYMMDD`) |
| `sale_date` | `DATE` | Business trading date from filename contract |
| `quantity` | `DECIMAL(12,2)` | Quantity purchased (positive for sales, negative for returns/voids) |
| `unit_price` | `DECIMAL(12,2)` | Till printed unit price |
| `historical_price` | `DECIMAL(12,2)` | Authoritative selling price from `price_revisions` effective on `sale_date` |
| `revenue` | `DECIMAL(12,2)` | Net revenue measure (`quantity * unit_price`) |
| `line_type` | `TEXT` | `SALE`, `DISCOUNT`, `RETURN`, `VOID` |
| `source_file` | `TEXT` | Lineage tracking raw export filename |
| `txn_time` | `TIMESTAMP` | Normalized ISO timestamp |

---

## 3. Dimension Specifications

### 3.1 `dim_store`
- Source: `stores` table in PostgreSQL.
- Grain: 1 row = 1 physical supermarket branch.
- Rows: 12.
- Attributes: `store_key`, `store_id`, `store_name`, `address_line`, `city`, `state`, `region`, `floor_area_sqft`, `opened_on`.

### 3.2 `dim_category`
- Source: `product_categories` table in PostgreSQL.
- Grain: 1 row = 1 product category.
- Rows: 14.
- Attributes: `category_key`, `category_id`, `category_name`, `department` (Food, Fresh, Non-Food), `gst_rate`.

### 3.3 `dim_product` (SCD Type 2 Historical Identity)
- Source: `products` table in PostgreSQL.
- Grain: 1 row = 1 unique historical product version.
- Rows: 1,224.
- Attributes: `product_key` (`product_sk`), `product_code`, `product_name`, `category_id`, `brand`, `pack_size`, `uom`, `valid_from`, `valid_to`, `is_current`.

> [!IMPORTANT]
> **Preserving Product Identity Across Reissues**:
> In June 2024, 24 retired product codes were reissued to new products. `fact_sales` resolves product identity through:
> ```sql
> ON s.product_code = p.product_code
> AND s.sale_date >= p.valid_from
> AND s.sale_date <= p.valid_to
> ```
> This guarantees zero duplicate joins and ensures transactions prior to June 1, 2024 map to the retired product and category, while transactions from June 1 onward map to the reissued product.

### 3.4 `dim_date`
- Grain: 1 row = 1 calendar day in 2024.
- Rows: 366 (leap year 2024).
- Attributes: `date_key`, `calendar_date`, `year`, `month`, `month_name`, `day`, `day_of_week`, `day_of_week_name`, `week`, `is_weekend`.

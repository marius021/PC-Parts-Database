# 🧩 PC Parts Database (Oracle SQL Project)

This project implements a relational database for a **PC components supplier** using **Oracle Database**.

## 📦 Structure

- `schema_oracle.sql` — Creates all tables, relationships and constraints.
- `prepare_raw_data.py` — Processes raw CSV datasets into a unified `products_raw.csv`.
- `etl_populate_db_v2.py` — Generates SQL inserts (`populate.sql`) from the processed data.
- `standards_mapping.csv` — Maps column names to standards (socket, form factor, etc.).
- `pcparts_erd.drawio` — Entity-Relationship Diagram for the schema.
- `output/populate.sql` — Ready-to-run SQL insert script.

## 🧰 How to Use

1. Run `prepare_raw_data.py` to unify and clean datasets.
2. Generate inserts with `etl_populate_db_v2.py`.
3. Execute `schema_oracle.sql` then `output/populate.sql` in Oracle (FREEPDB1).
4. Check the data using example queries in `quickcheck.sql` (optional).

## ⚒️ Work in Progress Status
- Implemented script to populate tables with data from different merged datasets.
- Implemented script to populate tables with a minimum ammount of data.
- 
## 📊 Example Queries

```sql
SELECT COUNT(*) FROM PRODUS;
SELECT * FROM STANDARD;

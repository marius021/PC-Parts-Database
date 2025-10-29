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
.
```
## Conceptual design
 # Main entities
- PRODUCATOR (producator_id PK): nume (unic), tara, website
- CATEGORIE (categorie_id PK): nume (unic), descriere
- STANDARD (standard_id PK): grup (ex. SOCKET_CPU,MEM_TYPE), cod (ex. AM5,DDR5), descriere
- PRODUS (produs_id PK): cod_sku (unic), denumire, garantie_luni, status, FK: categorie_id, producator_id
- PRODUS_STANDARD (PK compus): FK: produs_id, standard_id (M:N între PRODUS și STANDARD)
- DEPOZIT (depozit_id PK): nume, oras, tara (UNIQUE pe (nume,oras,tara))
- STOC (PK compus): produs_id, depozit_id, cantitate, prag_minim
- CLIENT (client_id PK): tip (B2B/B2C), nume, cod_fiscal, tara, categoria_pret
- COMANDA_VANZARE (cv_id PK): client_id (FK), data_creare, status, metoda_livrare
- CV_LINIE (cv_linie_id PK): cv_id (FK), linie_nr (UNIQUE pe (cv_id, linie_nr)), produs_id (FK), cantitate, pret_unitar, discount
- EXPEDIERE (expediere_id PK): cv_id (FK), depozit_id (FK), curier, awb, data_expediere
- RMA (rma_id PK): client_id (FK), produs_id (FK), cv_id (FK opțional), motiv, status, data_creare

# Relații cheie:
- PRODUCATOR 1–N PRODUS
- CATEGORIE 1–N PRODUS
- PRODUS M–N STANDARD prin PRODUS_STANDARD
- RODUS 1–N STOC (per DEPOZIT)
- CLIENT 1–N COMANDA_VANZARE; COMANDA_VANZARE 1–N CV_LINIE
- COMANDA_VANZARE 1–N EXPEDIERE
- CLIENT 1–N RMA; PRODUS 1–N RMA; COMANDA_VANZARE 0..1–N RMA (opțional)

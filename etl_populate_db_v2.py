import pandas as pd
from pathlib import Path
import csv

# ---------------------
# Configurare utilizator
# ---------------------
BASE = Path(r"C:\Users\Maurice\Desktop\BDDT\Proiect")
INPUT_CSV  = BASE / "products_raw.csv"
OUTPUT_SQL = BASE / "output" / "populate.sql"
MAPPING_CSV = BASE / "standards_mapping.csv"

def sql_str(x):
    if pd.isna(x):
        return "NULL"
    s = str(x).replace("'", "''")
    return f"'{s}'"

def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)

    # Curățare de bază
    for col in ["categorie","producator","status","depozit","oras_depozit","tara_depozit","denumire","cod_sku"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    df["garantie_luni"] = pd.to_numeric(df.get("garantie_luni", 24), errors="coerce").fillna(24).astype(int)
    df["status"] = df.get("status", "ACTIV").fillna("ACTIV").str.upper().where(df["status"].isin(["ACTIV","INACTIV"]), "ACTIV")

    # Dimensiuni
    dim_categorie = pd.DataFrame(sorted(df["categorie"].dropna().unique()), columns=["nume"]).query("nume != ''").reset_index(drop=True)
    dim_producator = pd.DataFrame(sorted(df["producator"].dropna().unique()), columns=["nume"]).query("nume != ''").reset_index(drop=True)
    dim_producator["tara"] = ""
    dim_producator["website"] = ""

    dim_depozit = df[["depozit","oras_depozit","tara_depozit"]].dropna(how="all").drop_duplicates()
    dim_depozit = dim_depozit[dim_depozit["depozit"].notna() & (dim_depozit["depozit"].astype(str).str.strip()!="")]

    # Citire mapping (rezistent la BOM / delimitator)
    standards_map = {}
    if MAPPING_CSV.exists():
        with open(MAPPING_CSV, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
            reader = csv.DictReader(f, dialect=dialect)
            for row in reader:
                raw_col = (row.get("raw_column") or row.get("RAW_COLUMN") or "").strip()
                grup    = (row.get("grup") or row.get("GRUP") or "").strip()
                if raw_col and grup:
                    standards_map[raw_col] = grup
    else:
        print(f"[ETL] WARNING: mapping file not found at {MAPPING_CSV}")

    print("[ETL] mapping loaded:", standards_map)
    print("[ETL] csv columns:", list(df.columns))

    # Construim STANDARD
    std_records = []
    for raw_col, grup in standards_map.items():
        if raw_col in df.columns:
            colvals = (df[raw_col].astype(str)
                       .str.strip()
                       .replace({"": None, "nan": None, "None": None})
                       .dropna())
            for cod in sorted(colvals.unique()):
                std_records.append({"grup": grup, "cod": cod})
    dim_standard = pd.DataFrame(std_records).drop_duplicates().reset_index(drop=True)

    print(f"[ETL] STANDARD rows: {len(dim_standard)}")

    # Scriem INSERT-uri
    lines = []
    lines.append("SET DEFINE OFF;")
    lines.append("SET SQLBLANKLINES ON;")

    # PRODUCATOR
    for _, r in dim_producator.iterrows():
        lines.append(f"MERGE INTO PRODUCATOR t USING (SELECT {sql_str(r.nume)} AS nume FROM dual) s "
                     f"ON (t.nume = s.nume) WHEN NOT MATCHED THEN "
                     f"INSERT (nume, tara, website) VALUES (s.nume, {sql_str(r.tara)}, {sql_str(r.website)});")

    # CATEGORIE
    for _, r in dim_categorie.iterrows():
        lines.append(f"MERGE INTO CATEGORIE t USING (SELECT {sql_str(r.nume)} AS nume FROM dual) s "
                     f"ON (t.nume = s.nume) WHEN NOT MATCHED THEN "
                     f"INSERT (nume, descriere) VALUES (s.nume, NULL);")

    # STANDARD (upsert pe (grup,cod))
    for _, r in dim_standard.iterrows():
        g = sql_str(r["grup"])
        c = sql_str(r["cod"])
        lines.append(f"""
MERGE INTO STANDARD t
USING (SELECT {g} AS grup, {c} AS cod FROM dual) s
ON (t.grup = s.grup AND t.cod = s.cod)
WHEN NOT MATCHED THEN INSERT (grup, cod) VALUES (s.grup, s.cod);
""".strip())

    # DEPOZIT
    for _, r in dim_depozit.iterrows():
        lines.append(f"""
MERGE INTO DEPOZIT t USING (SELECT {sql_str(r.depozit)} AS nume, {sql_str(r.oras_depozit)} AS oras, {sql_str(r.tara_depozit)} AS tara FROM dual) s
ON (t.nume=s.nume AND t.oras=s.oras AND t.tara=s.tara)
WHEN NOT MATCHED THEN INSERT (nume, oras, tara) VALUES (s.nume, s.oras, s.tara);
""".strip())

    # PRODUS
    for _, r in df.iterrows():
        garantie = "NULL" if pd.isna(r.garantie_luni) else str(int(r.garantie_luni))
        status = sql_str(r.status if isinstance(r.status, str) else "ACTIV")
        lines.append(f"""
MERGE INTO PRODUS t USING (SELECT {sql_str(r.cod_sku)} AS cod_sku FROM dual) s
ON (t.cod_sku = s.cod_sku)
WHEN NOT MATCHED THEN INSERT (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ({sql_str(r.cod_sku)}, {sql_str(r.denumire)},
(SELECT categorie_id FROM CATEGORIE WHERE nume={sql_str(r.categorie)}),
(SELECT producator_id FROM PRODUCATOR WHERE nume={sql_str(r.producator)}),
{garantie}, {status});
""".strip())

    # PRODUS_STANDARD (lookup pe SKU + (grup,cod))
    links = []
    for raw_col, grup in standards_map.items():
        if raw_col in df.columns:
            for _, rr in df[["cod_sku", raw_col]].dropna().iterrows():
                val = str(rr[raw_col]).strip()
                if val and val.lower() not in ("none", "nan"):
                    links.append((rr["cod_sku"], grup, val))

    seen = set()
    uniq_links = [x for x in links if not (x in seen or seen.add(x))]

    for sku, grup, cod in uniq_links:
        lines.append(f"""
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup={sql_str(grup)} AND s.cod={sql_str(cod)}
WHERE p.cod_sku={sql_str(sku)}
AND NOT EXISTS (
  SELECT 1 FROM PRODUS_STANDARD ps
  WHERE ps.produs_id=p.produs_id AND ps.standard_id=s.standard_id
);
""".strip())

    # STOC (lookup pe depozit + produs)
    if {"depozit","oras_depozit","tara_depozit","cantitate","prag_minim"}.issubset(df.columns):
        stoc = (df.dropna(subset=["cod_sku","depozit"])
                  .groupby(["cod_sku","depozit","oras_depozit","tara_depozit"], as_index=False)
                  .agg(cantitate=("cantitate","sum"), prag_minim=("prag_minim","max")))
        for _, r in stoc.iterrows():
            lines.append(f"""
INSERT INTO STOC (produs_id, depozit_id, cantitate, prag_minim)
SELECT p.produs_id, d.depozit_id, {int(r['cantitate'])}, {int(r['prag_minim'])}
FROM PRODUS p JOIN DEPOZIT d
ON d.nume={sql_str(r['depozit'])} AND d.oras={sql_str(r['oras_depozit'])} AND d.tara={sql_str(r['tara_depozit'])}
WHERE p.cod_sku={sql_str(r['cod_sku'])}
AND NOT EXISTS (
  SELECT 1 FROM STOC s WHERE s.produs_id=p.produs_id AND s.depozit_id=d.depozit_id
);
""".strip())

    # Commit final
    lines.append("COMMIT;")

    OUTPUT_SQL.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ETL] Generated {len(lines)} SQL statements -> {OUTPUT_SQL}")

if __name__ == "__main__":
    main()

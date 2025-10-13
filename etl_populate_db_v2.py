import pandas as pd
from pathlib import Path

# ---------------------
# User-configurable paths
# ---------------------
BASE = Path(r"C:\Users\Maurice\Desktop\BDDT\Proiect")
INPUT_CSV  = BASE / "products_raw.csv"          # fișierul creat de prepare_raw_data.py
OUTPUT_SQL = BASE / "output" / "populate.sql"   # unde vrei INSERT-urile
MAPPING_CSV = BASE / "standards_mapping.csv"    # mappingul pentru standarde

# Optional: a mapping file to convert raw column names into STANDARD "grup" values
# Example rows:
# raw_column,grup
# socket,SOCKET_CPU
# memory_type,MEM_TYPE
# form_factor,FORM_FACTOR_MB
# interface,INTERFATA
# storage_form,STORAGE_FORM
MAPPING_CSV = Path("/mnt/data/standards_mapping.csv")  # can be absent

# ---------------------
# Expected core columns in INPUT_CSV (others are optional):
# cod_sku, denumire, categorie, producator, garantie_luni, status,
# depozit, oras_depozit, tara_depozit, cantitate, prag_minim
#
# Any additional columns that describe standards should be mapped through MAPPING_CSV.
# ---------------------

def sql_str(x):
    if pd.isna(x): 
        return "NULL"
    s = str(x).replace("'", "''")
    return f"'{s}'"

def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing {INPUT_CSV}. Create it or point INPUT_CSV to your file.")
    df = pd.read_csv(INPUT_CSV)

    # Basic cleanup
    for col in ["categorie","producator","status","depozit","oras_depozit","tara_depozit","denumire","cod_sku"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Types
    df["garantie_luni"] = pd.to_numeric(df.get("garantie_luni", 24), errors="coerce").fillna(24).astype(int)
    df["status"] = df.get("status", "ACTIV").fillna("ACTIV").str.upper().where(df["status"].isin(["ACTIV","INACTIV"]), "ACTIV")

    # Dimension tables
    dim_categorie = pd.DataFrame(sorted(df["categorie"].dropna().unique()), columns=["nume"]).query("nume != ''").reset_index(drop=True)
    dim_categorie["categorie_id"] = dim_categorie.index + 1

    dim_producator = pd.DataFrame(sorted(df["producator"].dropna().unique()), columns=["nume"]).query("nume != ''").reset_index(drop=True)
    dim_producator["producator_id"] = dim_producator.index + 1
    dim_producator["tara"] = ""
    dim_producator["website"] = ""

    dim_depozit = df[["depozit","oras_depozit","tara_depozit"]].dropna(how="all").drop_duplicates()
    dim_depozit = dim_depozit[dim_depozit["depozit"].notna() & (dim_depozit["depozit"].astype(str).str.strip()!="")]
    if not dim_depozit.empty:
        dim_depozit = dim_depozit.reset_index(drop=True)
        dim_depozit["depozit_id"] = dim_depozit.index + 1
    else:
        dim_depozit = pd.DataFrame(columns=["depozit","oras_depozit","tara_depozit","depozit_id"])

    # Standards mapping (optional but recommended)
    standards_map = {}
    if MAPPING_CSV.exists():
        mapdf = pd.read_csv(MAPPING_CSV)
        mapdf = mapdf.dropna(subset=["raw_column","grup"])
        for _, r in mapdf.iterrows():
            standards_map[str(r["raw_column"]).strip()] = str(r["grup"]).strip()

    # Build STANDARD dimension from mapped columns
    std_records = []
    for raw_col, grup in standards_map.items():
        if raw_col in df.columns:
            colvals = df[raw_col].dropna().astype(str).str.strip()
            colvals = colvals[colvals!=""]
            for cod in sorted(colvals.unique()):
                std_records.append({"grup": grup, "cod": cod})

    dim_standard = pd.DataFrame(std_records).drop_duplicates().reset_index(drop=True)
    if not dim_standard.empty:
        dim_standard["standard_id"] = dim_standard.index + 1
    else:
        dim_standard = pd.DataFrame(columns=["grup","cod","standard_id"])

    # Assign surrogate keys
    def map_id(series, dim_df, key_col, id_col):
        m = dict(zip(dim_df[key_col], dim_df[id_col]))
        return series.map(m)

    df["categorie_id"]  = map_id(df["categorie"],  dim_categorie, "nume", "categorie_id")
    df["producator_id"] = map_id(df["producator"], dim_producator, "nume", "producator_id")

    if not dim_depozit.empty:
        df = df.merge(dim_depozit, how="left", on=["depozit","oras_depozit","tara_depozit"])

    # PRODUCT IDs
    df = df.reset_index(drop=True)
    df["produs_id"] = df.index + 1

    # Build PRODUS_STANDARD links from standards_map
    ps_links = []
    for raw_col, grup in standards_map.items():
        if raw_col in df.columns and not dim_standard.empty:
            # lookup for this group
            group_std = dim_standard[dim_standard["grup"]==grup]
            lut = dict(zip(zip([grup]*len(group_std), group_std["cod"]), group_std["standard_id"]))
            for i, val in df[raw_col].items():
                if pd.isna(val) or str(val).strip()=="":
                    continue
                key = (grup, str(val).strip())
                std_id = lut.get(key)
                if std_id:
                    ps_links.append({"produs_id": int(df.at[i,"produs_id"]), "standard_id": int(std_id)})

    if ps_links:
        ps_df = pd.DataFrame(ps_links).drop_duplicates().reset_index(drop=True)
    else:
        ps_df = pd.DataFrame(columns=["produs_id","standard_id"])

    # Write INSERTs in dependency order
    lines = []

    # PRODUCATOR
    for _, r in dim_producator.iterrows():
        lines.append(f"INSERT INTO PRODUCATOR(producator_id, nume, tara, website) VALUES ({int(r.producator_id)}, {sql_str(r.nume)}, {sql_str(r.tara)}, {sql_str(r.website)});")

    # CATEGORIE
    for _, r in dim_categorie.iterrows():
        lines.append(f"INSERT INTO CATEGORIE(categorie_id, nume, descriere) VALUES ({int(r.categorie_id)}, {sql_str(r.nume)}, NULL);")

    # STANDARD
    for _, r in dim_standard.iterrows():
        lines.append(f"INSERT INTO STANDARD(standard_id, grup, cod, descriere) VALUES ({int(r.standard_id)}, {sql_str(r.grup)}, {sql_str(r.cod)}, NULL);")

    # DEPOZIT
    for _, r in dim_depozit.iterrows():
        lines.append(f"INSERT INTO DEPOZIT(depozit_id, nume, oras, tara) VALUES ({int(r.depozit_id)}, {sql_str(r.depozit)}, {sql_str(r.oras_depozit)}, {sql_str(r.tara_depozit)});")

    # PRODUS
    for _, r in df.iterrows():
        garantie = "NULL" if pd.isna(r.garantie_luni) else str(int(r.garantie_luni))
        cat_id   = "NULL" if pd.isna(r.categorie_id) else str(int(r.categorie_id))
        prod_id  = "NULL" if pd.isna(r.producator_id) else str(int(r.producator_id))
        status   = sql_str(r.status if isinstance(r.status, str) else "ACTIV")
        lines.append(
            f"INSERT INTO PRODUS(produs_id, cod_sku, denumire, categorie_id, producator_id, garantie_luni, status) "
            f"VALUES ({int(r.produs_id)}, {sql_str(r.cod_sku)}, {sql_str(r.denumire)}, {cat_id}, {prod_id}, {garantie}, {status});"
        )

    # PRODUS_STANDARD
    for _, r in ps_df.iterrows():
        lines.append(f"INSERT INTO PRODUS_STANDARD(produs_id, standard_id) VALUES ({int(r.produs_id)}, {int(r.standard_id)});")

    # STOC
    stoc_cols = {"depozit_id","cantitate","prag_minim"}
    if stoc_cols.issubset(df.columns):
        for _, r in df.dropna(subset=["depozit_id"]).iterrows():
            cant = int(r.get("cantitate", 0)) if pd.notna(r.get("cantitate", None)) else 0
            prag = int(r.get("prag_minim", 0)) if pd.notna(r.get("prag_minim", None)) else 0
            lines.append(f"INSERT INTO STOC(produs_id, depozit_id, cantitate, prag_minim) VALUES ({int(r.produs_id)}, {int(r.depozit_id)}, {cant}, {prag});")

    OUTPUT_SQL.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {len(lines)} SQL INSERT statements -> {OUTPUT_SQL}")

if __name__ == '__main__':
    main()
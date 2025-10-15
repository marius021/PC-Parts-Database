import pandas as pd
from pathlib import Path
import re

BASE = Path(r"C:\Users\Maurice\Desktop\BDDT\Proiect")
PCPART_DIR = BASE / "raw_data" / "pc-part-dataset"   # zip GitHub extras aici (conține un subfolder 'data', dar căutăm recursiv)
KAGGLE_DIR = BASE / "raw_data" / "kaggle-pccomponents"  # zip Kaggle extras aici (pot fi mai multe CSV-uri)

OUT_CSV = BASE / "products_raw.csv"

# ---- helper: caută un singur fișier potrivit unor pattern-uri
def find_file(root: Path, patterns):
    for pat in patterns:
        matches = list(root.rglob(pat))
        if matches:
            # alegem cel mai scurt path / cel mai "plauzibil"
            matches = sorted(matches, key=lambda p: len(str(p)))
            return matches[0]
    return None

# ---- helper: citește CSV cu fallback la encodings
def read_csv_safe(path: Path):
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    # ultimul fallback, ignorăm erorile de encoding
    return pd.read_csv(path, encoding_errors="ignore")

def norm_socket(val: str | None) -> str | None:
        if not isinstance(val, str):
            return None
        v = val.strip().upper()
        # scoate cuvinte de umplutură
        v = v.replace("SOCKET", " ").replace("CPU", " ").replace("PROCESSOR", " ")
        v = re.sub(r"\(.*?\)", " ", v)         # elimină paranteze
        v = re.sub(r"[^A-Z0-9 ]", " ", v)      # caractere non-alfa
        v = re.sub(r"\s+", " ", v).strip()

        # extrage patternuri cunoscute
        if "AM5" in v:
            return "AM5"
        m = re.search(r"\bLGA\s*([0-9]{3,5})\b", v)
        if m:
            return f"LGA{m.group(1)}"
        m = re.search(r"\bAM([2-5])\b", v)     # AM4, AM3 etc.
        if m:
            return f"AM{m.group(1)}"
        return v or None
    

# ---- mapare minimă comună
def normalize_df(df, categorie_hint=None):
    df = df.copy()

    # denumire / nume produs
    name_cols = [c for c in df.columns if c.lower() in ("name", "product_name", "model", "title")]
    df["denumire"] = df[name_cols[0]] if name_cols else df.iloc[:,0].astype(str)

    # producator / brand
    brand_cols = [c for c in df.columns if c.lower() in ("brand", "manufacturer", "maker")]
    df["producator"] = df[brand_cols[0]] if brand_cols else ""

    # cod_sku: prefer id/sku/part_number; dacă nu există, derivăm
    sku_cols = [c for c in df.columns if c.lower() in ("id", "sku", "part_number", "partnumber", "pn")]
    if sku_cols:
        df["cod_sku"] = df[sku_cols[0]].astype(str)
    else:
        df["cod_sku"] = (df["producator"].astype(str).str[:6].str.upper() + "-" +
                         df["denumire"].astype(str).str.replace(r"\s+", "-", regex=True).str[:20].str.upper())

    # categorii: fie există coloană, fie venim cu hint
    cat_cols = [c for c in df.columns if c.lower() in ("category", "categorie", "type")]
    if cat_cols:
        df["categorie"] = df[cat_cols[0]].astype(str)
    else:
        df["categorie"] = categorie_hint if categorie_hint else "Unknown"

    # standarde uzuale
    def pick(*names):
        for n in names:
            if n in df.columns: 
                return df[n]
        return None

    # socket
    for c in df.columns:
        if "socket" in c.lower():
            df["socket"] = df[c].astype(str)
            break
    if "socket" not in df.columns: df["socket"] = None

    # memory type
    mem_col = pick("memory_type","memorytype","ram_type","memory")
    df["memory_type"] = mem_col.astype(str) if mem_col is not None else None

    # form factor (placi/ carcase)
    ff_candidates = [c for c in df.columns if "form" in c.lower() and "factor" in c.lower()]
    df["form_factor"] = df[ff_candidates[0]].astype(str) if ff_candidates else None

    # interface (PCIe x16 etc.)
    iface_candidates = [c for c in df.columns if "interface" in c.lower() or "bus" in c.lower()]
    df["interface"] = df[iface_candidates[0]].astype(str) if iface_candidates else None

    # storage form (M.2 2280 / 2.5 in)
    st_candidates = [c for c in df.columns if "m.2" in c.lower() or "form_factor_storage" in c.lower() or "storage_form" in c.lower()]
    df["storage_form"] = df[st_candidates[0]].astype(str) if st_candidates else None

    keep = ["cod_sku","denumire","categorie","producator","socket","memory_type","form_factor","interface","storage_form"]
    for k in keep:
        if k not in df.columns:
            df[k] = None
    return df[keep]

# ---------- 1) DOCYX (GitHub) : încercăm să citim cel puțin CPU, Motherboard, Memory
docyx_files = {
    "CPU": find_file(PCPART_DIR, ["**/cpu.csv", "**/*cpu*.csv"]),
    "Motherboard": find_file(PCPART_DIR, ["**/motherboard.csv", "**/*mobo*.csv", "**/*mother*.csv"]),
    "RAM": find_file(PCPART_DIR, ["**/memory.csv", "**/*ram*.csv", "**/*memory*.csv"]),
}
parts = []
for cat, path in docyx_files.items():
    if path and path.exists():
        df = read_csv_safe(path)
        parts.append(normalize_df(df, categorie_hint=cat))
    else:
        print(f"⚠️  Nu am găsit fișierul pentru {cat} în {PCPART_DIR} (cautat recursiv).")

# ---------- 2) KAGGLE: combinăm toate CSV-urile din director și normalizăm
kaggle_csvs = list(KAGGLE_DIR.rglob("*.csv"))
if kaggle_csvs:
    for p in kaggle_csvs:
        try:
            df = read_csv_safe(p)
            parts.append(normalize_df(df))  # lăsăm 'categorie' din fișier dacă există
        except Exception as e:
            print(f"⚠️  Nu am putut citi {p}: {e}")
else:
    print(f"⚠️  Nu am găsit CSV-uri în {KAGGLE_DIR}")

# ---------- 3) Concatenează și curăță
if not parts:
    raise SystemExit("❌ Nu am găsit niciun CSV de combinat. Verifică căile și extragerile .zip.")

merged = pd.concat(parts, ignore_index=True)
# mică curățare
for c in ["cod_sku","denumire","categorie","producator","socket","memory_type","form_factor","interface","storage_form"]:
    merged[c] = merged[c].astype(str).str.strip().replace({"nan": None, "None": None, "": None})

# completări minime
merged["status"] = "ACTIV"
merged["garantie_luni"] = 24

# exemplu de stoc default (poți edita ulterior)
merged["depozit"] = "Central"
merged["oras_depozit"] = "Bucuresti"
merged["tara_depozit"] = "RO"
merged["cantitate"] = 10
merged["prag_minim"] = 2
merged["socket"] = merged["socket"].apply(norm_socket)
# reordonează coloanele ca să fie compatibil cu ETL v2
ordered = [
    "cod_sku","denumire","categorie","producator","garantie_luni","status",
    "depozit","oras_depozit","tara_depozit","cantitate","prag_minim",
    "socket","memory_type","form_factor","interface","storage_form"
]
for col in ordered:
    if col not in merged.columns:
        merged[col] = None

merged = merged[ordered].drop_duplicates(subset=["cod_sku","denumire"], keep="first")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUT_CSV, index=False, encoding="utf-8")
print(f"✅ products_raw.csv creat: {OUT_CSV} (rows={len(merged)})")

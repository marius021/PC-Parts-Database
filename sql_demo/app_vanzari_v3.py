import tkinter as tk
from tkinter import ttk, messagebox
import oracledb

# ================= CONFIGURARE DATABASE =================
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"
DB_DSN = "localhost:1521/freepdb1"

# ================= CULORI SI STILURI =================
COLOR_PRIMARY = "#2c3e50"    # Dark Blue (Sidebar)
COLOR_ACCENT = "#3498db"     # Light Blue (Buttons/Highlights)
COLOR_SUCCESS = "#27ae60"    # Green (Save)
COLOR_DANGER = "#e74c3c"     # Red (Logout/Delete)
COLOR_BG = "#ecf0f1"         # Light Gray (Background)
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_LABEL = ("Segoe UI", 11)
FONT_TOTAL = ("Segoe UI", 24, "bold")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PC Parts Manager v2.0")
        self.geometry("900x700")
        self.configure(bg=COLOR_BG)
        
        # Configurare Stiluri Globale (TTK)
        style = ttk.Style()
        style.theme_use('clam')
        
        # Stiluri Butoane
        style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="white", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("Accent.TButton", background=[("active", "#2980b9")])
        
        style.configure("Danger.TButton", background=COLOR_DANGER, foreground="white", font=("Segoe UI", 10, "bold"), padding=10)
        style.map("Danger.TButton", background=[("active", "#c0392b")])

        # Stiluri Tab-uri
        style.configure("TNotebook", background=COLOR_BG)
        style.configure("TNotebook.Tab", padding=[15, 5], font=("Segoe UI", 11))

        # Container Principal
        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (LoginPage, AdminPage, AgentPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'refresh_data'):
            frame.refresh_data()

# ================= LOGIN PAGE (DESIGN MODERN) =================
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.configure(bg=COLOR_PRIMARY)
        
        # Centrare continut
        card = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised")
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(card, text="PC PARTS ERP", font=("Segoe UI", 28, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(0, 10))
        tk.Label(card, text="Sistem de Gestiune Integrat", font=("Segoe UI", 12), fg="gray", bg="white").pack(pady=(0, 30))
        
        ttk.Button(card, text="🔐 Autentificare ADMINISTRATOR", style="Danger.TButton", width=30,
                   command=lambda: controller.show_frame("AdminPage")).pack(pady=10)
        
        ttk.Button(card, text="💼 Autentificare AGENT VÂNZĂRI", style="Accent.TButton", width=30,
                   command=lambda: controller.show_frame("AgentPage")).pack(pady=10)

# ================= ADMIN PAGE =================

class AdminPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.configure(bg=COLOR_BG)
        self.controller = controller
        
        # Navbar
        nav = tk.Frame(self, bg=COLOR_DANGER, height=60)
        nav.pack(fill="x")
        tk.Label(nav, text="PANOU ADMIN", bg=COLOR_DANGER, fg="white", font=FONT_HEADER).pack(side="left", padx=20, pady=15)
        tk.Button(nav, text="Deconectare", bg="white", fg=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat",
                  command=lambda: controller.show_frame("LoginPage")).pack(side="right", padx=20)

        # Content
        content = tk.Frame(self, bg=COLOR_BG, padx=20, pady=20)
        content.pack(fill="both", expand=True)

        # Notebook (Tab-uri)
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Clienti
        self.tab_clienti = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_clienti, text=" 👥 Gestionare Clienți ")
        self.build_clienti_ui()

        # Tab 2: Stocuri (NOU)
        self.tab_stocuri = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_stocuri, text=" 📦 Gestiune Stocuri & Aprovizionare ")
        self.build_stocuri_ui()
        
        # Eveniment la schimbarea tab-ului (pentru refresh date)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        # Facem refresh în funcție de tab-ul activ
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 0:
            self.refresh_clienti()
        elif selected_tab == 1:
            self.refresh_stocuri()

    # ================= UI TAB STOCURI (NOU) =================
    def build_stocuri_ui(self):
        # 1. Filtre și KPI
        frm_top = tk.Frame(self.tab_stocuri, bg="white")
        frm_top.pack(fill="x", pady=(0, 10))

        tk.Label(frm_top, text="Filtrează după Depozit:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.combo_depozit = ttk.Combobox(frm_top, state="readonly", width=25)
        self.combo_depozit.pack(side="left", padx=10)
        self.combo_depozit.bind("<<ComboboxSelected>>", lambda e: self.refresh_stocuri())

        self.lbl_total_val = tk.Label(frm_top, text="Valoare Totală Stoc: 0 RON", bg="#ecf0f1", fg=COLOR_PRIMARY, font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        self.lbl_total_val.pack(side="right")

        # 2. Tabel Stocuri
        cols = ("PRODUS", "SKU", "DEPOZIT", "CANTITATE", "PRET UNITAR", "VALOARE")
        self.tree_stoc = ttk.Treeview(self.tab_stocuri, columns=cols, show="headings", height=12)
        
        for c in cols: self.tree_stoc.heading(c, text=c)
        self.tree_stoc.column("CANTITATE", width=80, anchor="center")
        self.tree_stoc.column("VALOARE", width=100, anchor="e")
        self.tree_stoc.column("DEPOZIT", width=150)
        
        self.tree_stoc.pack(fill="both", expand=True)
        
        # 3. Zona Aprovizionare (Jos)
        frm_action = tk.LabelFrame(self.tab_stocuri, text="Acțiuni Aprovizionare", bg="white", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        frm_action.pack(fill="x", pady=10)

        tk.Label(frm_action, text="Selectează un produs din tabel și introdu cantitatea de adăugat:", bg="white").pack(side="left")
        
        self.ent_add_stoc = tk.Entry(frm_action, width=10, font=("Segoe UI", 10))
        self.ent_add_stoc.pack(side="left", padx=10)
        
        ttk.Button(frm_action, text="➕ Adaugă Stoc (Intrare Marfă)", style="Accent.TButton", command=self.add_stock).pack(side="left")

    def refresh_stocuri(self):
        # Golim tabelul
        for i in self.tree_stoc.get_children(): self.tree_stoc.delete(i)
        
        conn = self.get_conn()
        if not conn: return
        cur = conn.cursor()

        # Populam Dropdown Depozite (daca e gol)
        if not self.combo_depozit['values']:
            try:
                cur.execute("SELECT nume FROM DEPOZIT")
                depos = ["Toate"] + [r[0] for r in cur]
                self.combo_depozit['values'] = depos
                self.combo_depozit.current(0)
            except: pass

        # Construim Query-ul dinamic
        sql = """
            SELECT p.denumire, p.cod_sku, d.nume, s.cantitate, s.pret_minim, (s.cantitate * s.pret_minim) as valoare, 
                   p.produs_id, d.depozit_id
            FROM STOC s
            JOIN PRODUS p ON s.produs_id = p.produs_id
            JOIN DEPOZIT d ON s.depozit_id = d.depozit_id
        """
        
        filtre = self.combo_depozit.get()
        if filtre and filtre != "Toate":
            sql += f" WHERE d.nume = '{filtre}'"
        
        sql += " ORDER BY s.cantitate ASC" # Vedem întâi produsele cu stoc mic

        total_general = 0
        try:
            cur.execute(sql)
            for row in cur:
                # row[0-5] sunt datele vizibile, row[6-7] sunt ID-urile ascunse (pentru update)
                # Formatam preturile
                pret = f"{row[4]:.2f}"
                val = f"{row[5]:.2f}"
                total_general += row[5]
                
                # Inseram in Treeview, dar salvam ID-urile in tag-ul 'values' extins sau intr-un dictionar
                # Truc: Punem ID-urile la final in values, dar nu le definim in columns, deci nu se vad, dar se pot accesa
                item_id = self.tree_stoc.insert("", "end", values=(row[0], row[1], row[2], row[3], pret, val))
                # Salvam ID-urile reale in dictionarul item-ului pentru a le folosi la update
                self.tree_stoc.set(item_id, column="#0", value=f"{row[6]}|{row[7]}") # Hack: stocam in coloana #0 ascunsa
                
                # Coloram randurile cu stoc critic (<10)
                if row[3] < 10:
                    self.tree_stoc.item(item_id, tags=('critic',))

            self.tree_stoc.tag_configure('critic', foreground='red')
            self.lbl_total_val.config(text=f"Valoare Totală Stoc: {total_general:,.2f} RON")

        except Exception as e: print(e)
        finally: conn.close()

    def add_stock(self):
        sel = self.tree_stoc.selection()
        if not sel:
            messagebox.showwarning("Atenție", "Selectează un produs din tabel pentru aprovizionare!")
            return
        
        qty_str = self.ent_add_stoc.get()
        if not qty_str.isdigit():
            messagebox.showerror("Eroare", "Introdu o cantitate validă (număr întreg)!")
            return
        
        # Recuperam ID-urile salvate. 
        # Nota: In Treeview standard e greu sa ascunzi coloane si sa iei date din ele.
        # Vom face un query rapid bazat pe numele selectat sau folosim metoda mai sigura:
        # Preluam valorile vizibile
        values = self.tree_stoc.item(sel[0])['values']
        prod_nume = values[0]
        depozit_nume = values[2]
        
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            
            # 1. Aflam ID-urile reale (SQL rapid)
            cur.execute("SELECT produs_id FROM PRODUS WHERE denumire = :1", [prod_nume])
            pid = cur.fetchone()[0]
            cur.execute("SELECT depozit_id FROM DEPOZIT WHERE nume = :1", [depozit_nume])
            did = cur.fetchone()[0]
            
            # 2. Apeleaza Procedura
            cur.callproc("ADMIN_UPDATE_STOC", [pid, did, int(qty_str)])
            conn.close()
            
            messagebox.showinfo("Succes", f"Stoc actualizat pentru {prod_nume}!\n(+{qty_str} buc)")
            self.ent_add_stoc.delete(0, tk.END)
            self.refresh_stocuri()
            
        except Exception as e:
            messagebox.showerror("Eroare DB", str(e))


    # ================= UI TAB CLIENTI (CEL VECHI) =================
    def build_clienti_ui(self):
        # Formular Adaugare
        frm_add = tk.LabelFrame(self.tab_clienti, text="Adăugare Client Nou", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        frm_add.pack(fill="x", pady=(0, 20))
        
        tk.Label(frm_add, text="Nume:", bg="white").grid(row=0, column=0, padx=5, sticky="e")
        self.ent_nume = ttk.Entry(frm_add, width=25)
        self.ent_nume.grid(row=0, column=1, padx=5)
        
        tk.Label(frm_add, text="Cod Fiscal:", bg="white").grid(row=0, column=2, padx=5, sticky="e")
        self.ent_fiscal = ttk.Entry(frm_add, width=20)
        self.ent_fiscal.grid(row=0, column=3, padx=5)
        
        tk.Label(frm_add, text="Tip:", bg="white").grid(row=0, column=4, padx=5, sticky="e")
        self.combo_tip = ttk.Combobox(frm_add, values=["B2C", "B2B"], width=5, state="readonly")
        self.combo_tip.current(0)
        self.combo_tip.grid(row=0, column=5, padx=5)

        ttk.Button(frm_add, text="+ Adaugă Client", style="Accent.TButton", command=self.add_client).grid(row=0, column=6, padx=20)

        # Tabel
        cols = ("ID", "NUME", "COD FISCAL", "TIP", "CATEGORIE PRET")
        self.tree = ttk.Treeview(self.tab_clienti, columns=cols, show="headings", height=12)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        
        sb = ttk.Scrollbar(self.tab_clienti, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscroll=sb.set)
        
        # Buton Stergere
        ttk.Button(self.tab_clienti, text="Șterge Selectat", style="Danger.TButton", command=self.delete_client).pack(pady=10, anchor="e")

    def refresh_clienti(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT client_id, nume, cod_fiscal, tip, categoria_pret FROM CLIENT ORDER BY client_id DESC")
            for row in cur: self.tree.insert("", "end", values=row)
            conn.close()
        except: pass

    # ... (Păstrează metodele add_client și delete_client exact ca înainte)
    def add_client(self):
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_CLIENT", [self.combo_tip.get(), self.ent_nume.get(), self.ent_fiscal.get(), "Romania", "Standard"])
            conn.close()
            messagebox.showinfo("Succes", "Client adăugat!")
            self.refresh_clienti()
        except Exception as e: messagebox.showerror("Eroare", str(e))

    def delete_client(self):
        sel = self.tree.selection()
        if not sel: return
        client_id = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirmare", "Ștergi clientul?"):
            try:
                conn = self.get_conn()
                cur = conn.cursor()
                cur.callproc("ADMIN_STERGE_CLIENT", [client_id])
                conn.close()
                self.refresh_clienti()
            except Exception as e: messagebox.showerror("Eroare", "Nu se poate șterge (are comenzi active)!")

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    
    def refresh_data(self):
        # Default refresh la deschidere
        self.refresh_clienti()
        
# ================= AGENT PAGE (LIVE TOTAL & UI UPDATE) =================
class AgentPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.configure(bg=COLOR_BG)
        self.controller = controller
        self.client_map = {}
        self.produs_info = {} # { 'Nume': {'id': 1, 'pret': 100, 'stoc': 10} }

        # Navbar
        nav = tk.Frame(self, bg=COLOR_ACCENT, height=60)
        nav.pack(fill="x")
        tk.Label(nav, text="MODUL VÂNZĂRI", bg=COLOR_ACCENT, fg="white", font=FONT_HEADER).pack(side="left", padx=20, pady=15)
        tk.Button(nav, text="Deconectare", bg="white", fg=COLOR_ACCENT, font=("Segoe UI", 9, "bold"), relief="flat",
                  command=lambda: controller.show_frame("LoginPage")).pack(side="right", padx=20)

        # Layout Principal: Split 60% Stanga (Formular), 40% Dreapta (Sumar)
        main = tk.Frame(self, bg=COLOR_BG, padx=20, pady=20)
        main.pack(fill="both", expand=True)

        left_frame = tk.Frame(main, bg="white", padx=20, pady=20, relief="flat")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_frame = tk.Frame(main, bg="white", padx=20, pady=20, relief="flat")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # === STANGA: INPUT ===
        tk.Label(left_frame, text="Detalii Comandă", font=("Segoe UI", 14, "bold"), bg="white", fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 20))

        # Client
        tk.Label(left_frame, text="Client:", bg="white", font=FONT_LABEL).pack(anchor="w")
        self.cb_client = ttk.Combobox(left_frame, state="readonly", font=FONT_LABEL)
        self.cb_client.pack(fill="x", pady=(0, 15))

        # Produs
        tk.Label(left_frame, text="Produs:", bg="white", font=FONT_LABEL).pack(anchor="w")
        self.cb_produs = ttk.Combobox(left_frame, state="readonly", font=FONT_LABEL)
        self.cb_produs.pack(fill="x", pady=(0, 5))
        self.cb_produs.bind("<<ComboboxSelected>>", self.on_prod_select)
        
        # Info Stoc (Mic sub produs)
        self.lbl_stoc_info = tk.Label(left_frame, text="Stoc disponibil: -", bg="white", fg="gray", font=("Segoe UI", 9))
        self.lbl_stoc_info.pack(anchor="w", pady=(0, 15))

        # Grid pentru Cantitate / Discount / Livrare
        grid_fr = tk.Frame(left_frame, bg="white")
        grid_fr.pack(fill="x", pady=10)

        tk.Label(grid_fr, text="Cantitate:", bg="white").grid(row=0, column=0, sticky="w")
        self.ent_cant = tk.Spinbox(grid_fr, from_=1, to=1000, width=10, font=FONT_LABEL, command=self.update_total)
        self.ent_cant.grid(row=1, column=0, padx=(0, 10), pady=(0, 15))
        self.ent_cant.bind("<KeyRelease>", self.update_total)

        tk.Label(grid_fr, text="Discount (%):", bg="white").grid(row=0, column=1, sticky="w")
        self.ent_disc = tk.Entry(grid_fr, width=10, font=FONT_LABEL)
        self.ent_disc.insert(0, "0")
        self.ent_disc.grid(row=1, column=1, padx=(0, 10), pady=(0, 15))
        self.ent_disc.bind("<KeyRelease>", self.update_total)

        tk.Label(left_frame, text="Metodă Livrare:", bg="white", font=FONT_LABEL).pack(anchor="w")
        self.cb_livrare = ttk.Combobox(left_frame, values=["Curier Rapid", "Ridicare Personala"], state="readonly", font=FONT_LABEL)
        self.cb_livrare.current(0)
        self.cb_livrare.pack(fill="x", pady=(0, 20))

        # === DREAPTA: SUMAR LIVE ===
        tk.Label(right_frame, text="Sumar Tranzacție", font=("Segoe UI", 14, "bold"), bg="white", fg=COLOR_PRIMARY).pack(anchor="w", pady=(0, 20))

        # Card Pret
        tk.Label(right_frame, text="Preț Unitar:", bg="white", fg="gray").pack(anchor="e")
        self.lbl_unit_price = tk.Label(right_frame, text="0.00 RON", bg="white", font=("Segoe UI", 12))
        self.lbl_unit_price.pack(anchor="e", pady=(0, 10))

        tk.Frame(right_frame, height=2, bg=COLOR_BG).pack(fill="x", pady=10) # Separator

        # Total Mare
        tk.Label(right_frame, text="TOTAL DE PLATĂ:", bg="white", font=("Segoe UI", 12, "bold")).pack(anchor="center")
        self.lbl_total = tk.Label(right_frame, text="0.00 RON", bg="white", fg=COLOR_SUCCESS, font=FONT_TOTAL)
        self.lbl_total.pack(anchor="center", pady=10)

        # Buton Salvare Mare
        ttk.Button(right_frame, text="✅ PLASEAZĂ COMANDA", style="Accent.TButton", command=self.save_order).pack(fill="x", side="bottom", pady=20)

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    def refresh_data(self):
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            
            # Clienti
            cur.execute("SELECT client_id, nume FROM CLIENT")
            self.client_map = {row[1]: row[0] for row in cur}
            self.cb_client['values'] = list(self.client_map.keys())
            
            # Produse
            sql = "SELECT p.produs_id, p.denumire, s.pret_minim, s.cantitate FROM PRODUS p JOIN STOC s ON p.produs_id = s.produs_id WHERE s.depozit_id = 1"
            cur.execute(sql)
            self.produs_info = {row[1]: {'id': row[0], 'pret': row[2], 'stoc': row[3]} for row in cur}
            self.cb_produs['values'] = list(self.produs_info.keys())
            conn.close()
        except: pass

    def on_prod_select(self, event):
        name = self.cb_produs.get()
        if name in self.produs_info:
            info = self.produs_info[name]
            self.lbl_stoc_info.config(text=f"Stoc disponibil: {info['stoc']} buc", fg="green" if info['stoc'] > 0 else "red")
            self.lbl_unit_price.config(text=f"{info['pret']:.2f} RON")
            self.update_total()

    def update_total(self, event=None):
        try:
            name = self.cb_produs.get()
            if name not in self.produs_info: return
            
            price = self.produs_info[name]['pret']
            qty = int(self.ent_cant.get())
            disc = float(self.ent_disc.get()) if self.ent_disc.get() else 0
            
            total = (price * qty) * (1 - disc/100)
            self.lbl_total.config(text=f"{total:.2f} RON")
        except:
            self.lbl_total.config(text="0.00 RON")

    def save_order(self):
        try:
            # Validari
            c_name, p_name = self.cb_client.get(), self.cb_produs.get()
            if not c_name or not p_name: return messagebox.showwarning("Atentie", "Completeaza tot!")
            
            cid = self.client_map[c_name]
            pid = self.produs_info[p_name]['id']
            qty = int(self.ent_cant.get())
            liv = self.cb_livrare.get()
            disc = float(self.ent_disc.get())

            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADAUGA_COMANDA_COMPLETA", [cid, pid, qty, liv, disc])
            conn.close()
            
            messagebox.showinfo("Succes", f"Comanda plasata!\nTotal: {self.lbl_total.cget('text')}")
            self.refresh_data() # Refresh stoc
            self.ent_cant.delete(0, tk.END); self.ent_cant.insert(0, "1")
            
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
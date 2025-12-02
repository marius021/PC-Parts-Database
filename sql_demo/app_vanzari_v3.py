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

# ================= LOGIN PAGE =================
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
        
        # Maps pentru dropdown-uri (Nume -> ID)
        self.cat_map = {}
        self.producator_map = {}

        # === 1. NAVBAR (FULL WIDTH) ===
        nav = tk.Frame(self, bg=COLOR_DANGER, height=60)
        nav.pack(side="top", fill="x")
        
        tk.Label(nav, text="PANOU ADMIN - CONTROL TOTAL", bg=COLOR_DANGER, fg="white", font=FONT_HEADER).pack(side="left", padx=20, pady=15)
        
        tk.Button(nav, text="Deconectare", bg="white", fg=COLOR_DANGER, font=("Segoe UI", 9, "bold"), relief="flat",
                  command=lambda: controller.show_frame("LoginPage")).pack(side="right", padx=20)

        # === 2. CONTAINER CENTRAL (RESPONSIVE) ===
        self.main_container = tk.Frame(self, bg=COLOR_BG)
        self.main_container.pack(fill="both", expand=True, padx=40, pady=20) 

        # Notebook
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Clienti
        self.tab_clienti = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_clienti, text=" 👥 Gestionare Clienți ")
        self.build_clienti_ui()

        # Tab 2: Produse (Catalog + Aprovizionare)
        self.tab_produse = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_produse, text=" 📦 Catalog & Aprovizionare ")
        self.build_produse_ui()

        # Tab 3: Comenzi (Status)
        self.tab_comenzi = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_comenzi, text=" 🚚 Gestionare Comenzi & Status ")
        self.build_comenzi_ui()
        
        # Eveniment Tab Change
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 0: self.refresh_clienti()
        elif selected_tab == 1: self.refresh_produse_data()
        elif selected_tab == 2: self.refresh_comenzi()

    # =========================================================================
    # TAB 3: COMENZI
    # =========================================================================
    def build_comenzi_ui(self):
        # 1. ZONA ACTIUNI (JOS) - Prioritate la Layout
        frm_actions = tk.LabelFrame(self.tab_comenzi, text="Acțiuni Comandă Selectată", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        frm_actions.pack(side="bottom", fill="x", pady=(10, 0))

        # Centrare butoane
        btn_center = tk.Frame(frm_actions, bg="white")
        btn_center.pack(anchor="center")

        ttk.Button(btn_center, text="⚙️ În Procesare", command=lambda: self.change_status("In Procesare")).pack(side="left", padx=10)
        ttk.Button(btn_center, text="✅ Confirmă: FINALIZATĂ", style="Accent.TButton", command=lambda: self.change_status("Finalizata")).pack(side="left", padx=10)
        ttk.Button(btn_center, text="❌ ANULEAZĂ COMANDA", style="Danger.TButton", command=lambda: self.change_status("Anulata")).pack(side="left", padx=10)

        # 2. ZONA FILTRE (SUS)
        frm_filter = tk.Frame(self.tab_comenzi, bg="white", pady=10)
        frm_filter.pack(side="top", fill="x")
        
        tk.Label(frm_filter, text="Filtrează Status:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 5))
        self.cb_filter_status = ttk.Combobox(frm_filter, values=["Toate", "In Asteptare", "In Procesare", "Finalizata"], state="readonly", width=15)
        self.cb_filter_status.current(0)
        self.cb_filter_status.pack(side="left", padx=5)
        self.cb_filter_status.bind("<<ComboboxSelected>>", lambda e: self.refresh_comenzi())

        ttk.Button(frm_filter, text="🔄 Refresh Tabel", command=self.refresh_comenzi).pack(side="right")

        # 3. TABEL (RESTUL SPATIULUI)
        frm_table = tk.Frame(self.tab_comenzi, bg="white")
        frm_table.pack(side="top", fill="both", expand=True)

        cols = ("ID", "CLIENT", "DATA", "LIVRARE", "TOTAL", "STATUS")
        self.tree_cmd = ttk.Treeview(frm_table, columns=cols, show="headings", selectmode="browse")
        
        for c in cols: self.tree_cmd.heading(c, text=c)
        
        # Configurare lățimi
        self.tree_cmd.column("ID", width=50, anchor="center")
        self.tree_cmd.column("CLIENT", width=150)
        self.tree_cmd.column("DATA", width=80, anchor="center")
        self.tree_cmd.column("LIVRARE", width=100)
        self.tree_cmd.column("TOTAL", width=80, anchor="e")
        self.tree_cmd.column("STATUS", width=100, anchor="center")

        sb = ttk.Scrollbar(frm_table, orient="vertical", command=self.tree_cmd.yview)
        self.tree_cmd.configure(yscroll=sb.set)
        
        self.tree_cmd.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Culori
        self.tree_cmd.tag_configure('noua', foreground='#e67e22') 
        self.tree_cmd.tag_configure('finalizata', foreground='green', font=("Segoe UI", 9, "bold")) 
        self.tree_cmd.tag_configure('procesare', foreground='#2980b9')

    def refresh_comenzi(self):
        for i in self.tree_cmd.get_children(): self.tree_cmd.delete(i)
        filtre = self.cb_filter_status.get()
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            sql = "SELECT cv_id, nume_client, data_creare, metoda_livrare, valoare_totala, status FROM V_ISTORIC_SUMAR ORDER BY cv_id DESC"
            cur.execute(sql)
            for row in cur:
                status_db = row[5]
                if filtre != "Toate" and filtre != status_db: continue

                data_fmt = row[2].strftime('%d-%m-%Y') if row[2] else ""
                bani = f"{row[4]:.2f} RON" if row[4] else "0.00 RON"
                
                tag = 'noua'
                if status_db == 'Finalizata': tag = 'finalizata'
                elif status_db == 'In Procesare': tag = 'procesare'
                elif status_db == 'Anulata': tag = ''

                self.tree_cmd.insert("", "end", values=(row[0], row[1], data_fmt, row[3], bani, status_db), tags=(tag,))
            conn.close()
        except: pass

    def change_status(self, new_status):
        sel = self.tree_cmd.selection()
        if not sel: return messagebox.showwarning("Atenție", "Selectează o comandă!")
        
        item = self.tree_cmd.item(sel[0])
        cv_id = item['values'][0]
        
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADMIN_UPDATE_STATUS_COMANDA", [cv_id, new_status])
            conn.close()
            messagebox.showinfo("Succes", f"Status actualizat: {new_status}")
            self.refresh_comenzi()
        except Exception as e: messagebox.showerror("Eroare", str(e))

    # =========================================================================
    # TAB 2: PRODUSE (CATALOG + APROVIZIONARE)
    # =========================================================================
    def build_produse_ui(self):
        main_content = tk.Frame(self.tab_produse, bg="white")
        main_content.pack(fill="both", expand=True)

        # A. Formular Adaugare (Stanga)
        frm_left = tk.LabelFrame(main_content, text="Definire Produs Nou", font=("Segoe UI", 10, "bold"), bg="white", padx=15, pady=15)
        frm_left.pack(side="left", fill="y", padx=(0, 20))

        tk.Label(frm_left, text="Denumire:", bg="white").pack(anchor="w")
        self.ent_p_nume = ttk.Entry(frm_left, width=30)
        self.ent_p_nume.pack(pady=(0, 10))

        tk.Label(frm_left, text="SKU:", bg="white").pack(anchor="w")
        self.ent_p_sku = ttk.Entry(frm_left, width=30)
        self.ent_p_sku.pack(pady=(0, 10))

        tk.Label(frm_left, text="Categorie:", bg="white").pack(anchor="w")
        self.cb_cat = ttk.Combobox(frm_left, state="readonly", width=28)
        self.cb_cat.pack(pady=(0, 10))

        tk.Label(frm_left, text="Producător:", bg="white").pack(anchor="w")
        self.cb_prod = ttk.Combobox(frm_left, state="readonly", width=28)
        self.cb_prod.pack(pady=(0, 10))

        fr_grid = tk.Frame(frm_left, bg="white")
        fr_grid.pack(fill="x", pady=5)
        tk.Label(fr_grid, text="Garanție:", bg="white").grid(row=0, column=0, sticky="w")
        self.ent_p_gar = ttk.Entry(fr_grid, width=10); self.ent_p_gar.insert(0, "24"); self.ent_p_gar.grid(row=1, column=0, padx=(0, 10))
        tk.Label(fr_grid, text="Preț (RON):", bg="white").grid(row=0, column=1, sticky="w")
        self.ent_p_pret = ttk.Entry(fr_grid, width=10); self.ent_p_pret.grid(row=1, column=1)

        ttk.Button(frm_left, text="💾 Salvează Produs", style="Accent.TButton", command=self.add_product_db).pack(pady=20, fill="x")

        # B. Lista Produse (Dreapta)
        frm_right = tk.LabelFrame(main_content, text="Produse Existente", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        frm_right.pack(side="right", fill="both", expand=True)

        cols = ("ID", "NUME", "SKU", "CATEGORIE", "PRODUCATOR")
        self.tree_prod = ttk.Treeview(frm_right, columns=cols, show="headings")
        self.tree_prod.heading("ID", text="ID"); self.tree_prod.column("ID", width=40)
        self.tree_prod.heading("NUME", text="Denumire"); self.tree_prod.column("NUME", width=120)
        self.tree_prod.heading("SKU", text="SKU"); self.tree_prod.column("SKU", width=60)
        self.tree_prod.heading("CATEGORIE", text="Categorie"); self.tree_prod.column("CATEGORIE", width=80)
        self.tree_prod.heading("PRODUCATOR", text="Brand"); self.tree_prod.column("PRODUCATOR", width=60)
        self.tree_prod.pack(fill="both", expand=True)

        # Butoane Actiuni
        btn_frame = tk.Frame(frm_right, bg="white", pady=10)
        btn_frame.pack(side="bottom", fill="x")
        
        # Stiluri Butoane Speciale
        style = ttk.Style()
        style.configure("Success.TButton", background="#27ae60", foreground="white", font=("Segoe UI", 9, "bold"))

        ttk.Button(btn_frame, text="➕ Adaugă Stoc (Intrare Marfă)", style="Success.TButton", command=self.open_restock_popup).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="📍 Vezi Distribuție Stoc", style="Accent.TButton", command=self.view_stock_distribution).pack(side="right", padx=5)

    def refresh_produse_data(self):
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            
            # Dropdowns
            cur.execute("SELECT categorie_id, nume FROM CATEGORIE")
            self.cat_map = {row[1]: row[0] for row in cur}
            self.cb_cat['values'] = list(self.cat_map.keys())

            cur.execute("SELECT producator_id, nume FROM PRODUCATOR")
            self.producator_map = {row[1]: row[0] for row in cur}
            self.cb_prod['values'] = list(self.producator_map.keys())

            # Tabel
            for i in self.tree_prod.get_children(): self.tree_prod.delete(i)
            sql = "SELECT p.produs_id, p.denumire, p.cod_sku, c.nume, pr.nume FROM PRODUS p JOIN CATEGORIE c ON p.categorie_id = c.categorie_id JOIN PRODUCATOR pr ON p.producator_id = pr.producator_id ORDER BY p.produs_id DESC"
            cur.execute(sql)
            for row in cur: self.tree_prod.insert("", "end", values=row)
            conn.close()
        except: pass

    def add_product_db(self):
        nume, sku, cat, prod, gar, pret = self.ent_p_nume.get(), self.ent_p_sku.get(), self.cb_cat.get(), self.cb_prod.get(), self.ent_p_gar.get(), self.ent_p_pret.get()
        if not all([nume, sku, cat, prod, gar, pret]): return messagebox.showwarning("Atentie", "Toate campurile sunt obligatorii")
        
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_PRODUS_NOU", [nume, sku, self.cat_map[cat], self.producator_map[prod], int(gar), float(pret)])
            conn.close()
            messagebox.showinfo("Succes", "Produs creat!")
            self.refresh_produse_data()
            self.ent_p_nume.delete(0, tk.END); self.ent_p_sku.delete(0, tk.END)
        except Exception as e: messagebox.showerror("Eroare", str(e))

    def view_stock_distribution(self):
        sel = self.tree_prod.selection()
        if not sel: return messagebox.showwarning("!", "Selectează un produs!")
        
        item = self.tree_prod.item(sel[0])
        pid, pname = item['values'][0], item['values'][1]
        
        top = tk.Toplevel(self); top.title("Distribuție Stoc"); top.geometry("400x300"); top.configure(bg="white")
        tk.Label(top, text=f"Stoc: {pname}", font=("Segoe UI", 12, "bold"), bg="white").pack(pady=10)
        
        cols = ("DEPOZIT", "ORAS", "CANTITATE")
        tree = ttk.Treeview(top, columns=cols, show="headings", height=8)
        tree.heading("DEPOZIT", text="Depozit"); tree.column("DEPOZIT", width=120)
        tree.heading("ORAS", text="Oraș"); tree.column("ORAS", width=80)
        tree.heading("CANTITATE", text="Buc", anchor="center"); tree.column("CANTITATE", width=60)
        tree.pack(fill="both", expand=True, padx=10)
        
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT d.nume, d.oras, s.cantitate FROM STOC s JOIN DEPOZIT d ON s.depozit_id = d.depozit_id WHERE s.produs_id = :1 ORDER BY s.cantitate DESC", [pid])
            total = 0
            for row in cur: 
                tree.insert("", "end", values=row)
                total += row[2]
            tk.Label(top, text=f"TOTAL: {total} buc", font=("Segoe UI", 11, "bold"), bg="#ecf0f1").pack(fill="x")
            conn.close()
        except Exception as e: messagebox.showerror("Eroare", str(e))

    def open_restock_popup(self):
        sel = self.tree_prod.selection()
        if not sel: return messagebox.showwarning("!", "Selectează un produs!")
        item = self.tree_prod.item(sel[0])
        pid, pname = item['values'][0], item['values'][1]

        top = tk.Toplevel(self); top.title("Recepție Marfă"); top.geometry("400x250"); top.configure(bg="white")
        tk.Label(top, text="Intrare Stoc", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)
        
        frm = tk.Frame(top, bg="white"); frm.pack(pady=10)
        tk.Label(frm, text="Depozit:", bg="white").grid(row=0, column=0); cb_dep = ttk.Combobox(frm, state="readonly"); cb_dep.grid(row=0, column=1)
        tk.Label(frm, text="Cantitate:", bg="white").grid(row=1, column=0); ent_q = ttk.Entry(frm); ent_q.grid(row=1, column=1)
        
        # Populare depozite
        dep_map = {}
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.execute("SELECT depozit_id, nume FROM DEPOZIT")
            for r in cur: dep_map[r[1]] = r[0]
            cb_dep['values'] = list(dep_map.keys()); cb_dep.current(0)
            conn.close()
        except: pass

        def confirm():
            try:
                conn = self.get_conn(); cur = conn.cursor()
                cur.callproc("ADMIN_APROVIZIONARE", [pid, dep_map[cb_dep.get()], int(ent_q.get())])
                conn.close()
                messagebox.showinfo("Succes", "Stoc adaugat!"); top.destroy()
            except Exception as e: messagebox.showerror("Eroare", str(e))
            
        ttk.Button(top, text="✅ Confirmă", style="Success.TButton", command=confirm).pack(pady=10)

    # =========================================================================
    # TAB 1: CLIENTI (STANDARD)
    # =========================================================================
    def build_clienti_ui(self):
        frm_add = tk.LabelFrame(self.tab_clienti, text="Adăugare Client Nou", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        frm_add.pack(fill="x", pady=(0, 20))
        
        tk.Label(frm_add, text="Nume:", bg="white").grid(row=0, column=0, padx=5, sticky="e")
        self.ent_nume = ttk.Entry(frm_add, width=25); self.ent_nume.grid(row=0, column=1, padx=5)
        
        tk.Label(frm_add, text="Cod Fiscal:", bg="white").grid(row=0, column=2, padx=5, sticky="e")
        self.ent_fiscal = ttk.Entry(frm_add, width=20); self.ent_fiscal.grid(row=0, column=3, padx=5)
        
        tk.Label(frm_add, text="Tip:", bg="white").grid(row=0, column=4, padx=5, sticky="e")
        self.combo_tip = ttk.Combobox(frm_add, values=["B2C", "B2B"], width=5, state="readonly"); self.combo_tip.current(0); self.combo_tip.grid(row=0, column=5, padx=5)

        ttk.Button(frm_add, text="+ Adaugă Client", style="Accent.TButton", command=self.add_client).grid(row=0, column=6, padx=20)

        cols = ("ID", "NUME", "COD FISCAL", "TIP", "CATEGORIE PRET")
        self.tree = ttk.Treeview(self.tab_clienti, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("ID", width=50); self.tree.pack(fill="both", expand=True, side="left")
        
        sb = ttk.Scrollbar(self.tab_clienti, orient="vertical", command=self.tree.yview); sb.pack(side="right", fill="y")
        self.tree.configure(yscroll=sb.set)
        
        ttk.Button(self.tab_clienti, text="Șterge Selectat", style="Danger.TButton", command=self.delete_client).pack(pady=10, anchor="e")

    def refresh_clienti(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.execute("SELECT client_id, nume, cod_fiscal, tip, categoria_pret FROM CLIENT ORDER BY client_id DESC")
            for row in cur: self.tree.insert("", "end", values=row)
            conn.close()
        except: pass

    def add_client(self):
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_CLIENT", [self.combo_tip.get(), self.ent_nume.get(), self.ent_fiscal.get(), "Romania", "Standard"])
            conn.close(); messagebox.showinfo("Succes", "Adaugat!"); self.refresh_clienti()
        except Exception as e: messagebox.showerror("Eroare", str(e))

    def delete_client(self):
        sel = self.tree.selection()
        if not sel: return
        cid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("?", "Stergi?"):
            try:
                conn = self.get_conn(); cur = conn.cursor()
                cur.callproc("ADMIN_STERGE_CLIENT", [cid])
                conn.close(); self.refresh_clienti()
            except: messagebox.showerror("Eroare", "Clientul are comenzi!")

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

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
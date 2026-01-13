import tkinter as tk
from tkinter import messagebox
# Inlocuim importul standard cu ttkbootstrap
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import oracledb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ================= CONFIGURARE DATABASE =================
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"
DB_DSN = "localhost:1521/freepdb1"

# ================= CLASA PRINCIPALĂ (CONTROLLER) =================
class MainApp(ttk.Window):
    def __init__(self):
        # Folosim tema "flatly" pentru aspect corporate modern
        super().__init__(themename="flatly")
        self.title("PC Parts Manager ERP v3.0")
        self.geometry("1100x750")
        
        self.container = ttk.Frame(self)
        self.container.pack(fill=BOTH, expand=YES)
        
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
        # Refresh specific pentru dashboard daca intram in Admin
        if page_name == "AdminPage":
            frame.refresh_dashboard()

# ================= LOGIN PAGE (MODERNIZAT) =================
class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        
        # Centrare cu un card
        center_frame = ttk.Frame(self)
        center_frame.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Logo / Titlu
        ttk.Label(center_frame, text="PC PARTS MANAGER", font=("Helvetica", 28, "bold"), bootstyle="primary").pack(pady=(0, 10))
        ttk.Label(center_frame, text="Enterprise Resource Planning System", font=("Helvetica", 12), bootstyle="secondary").pack(pady=(0, 40))
        
        # Butoane Login Mari
        btn_agent = ttk.Button(center_frame, text="👤 Autentificare AGENT VÂNZĂRI", bootstyle="info-outline", width=30,
                               command=lambda: controller.show_frame("AgentPage"))
        btn_agent.pack(pady=10, ipady=5)
        
        btn_admin = ttk.Button(center_frame, text="🛠️ Autentificare ADMINISTRATOR", bootstyle="danger", width=30,
                               command=lambda: controller.show_frame("AdminPage"))
        btn_admin.pack(pady=10, ipady=5)

        ttk.Label(center_frame, text="© 2025 PC Parts Corp.", font=("Arial", 8), bootstyle="secondary").pack(pady=(50, 0))

# ================= ADMIN PAGE (PROFI) =================
class AdminPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.cat_map = {}
        self.producator_map = {}

        # 1. NAVBAR
        nav = ttk.Frame(self, bootstyle="primary")
        nav.pack(side=TOP, fill=X)
        
        ttk.Label(nav, text="  PANOU ADMINISTRARE", font=("Helvetica", 14, "bold"), bootstyle="inverse-primary").pack(side=LEFT, pady=15)
        ttk.Button(nav, text="Deconectare", bootstyle="light-outline", command=lambda: controller.show_frame("LoginPage")).pack(side=RIGHT, padx=20)

        # 2. TAB CONTROL
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Taburi
        self.tab_dashboard = ttk.Frame(self.notebook, padding=20)
        self.tab_clienti = ttk.Frame(self.notebook, padding=20)
        self.tab_produse = ttk.Frame(self.notebook, padding=20)
        self.tab_comenzi = ttk.Frame(self.notebook, padding=20)

        self.notebook.add(self.tab_dashboard, text="📊 Dashboard")
        self.notebook.add(self.tab_clienti, text="👥 Clienți")
        self.notebook.add(self.tab_produse, text="📦 Catalog & Stoc")
        self.notebook.add(self.tab_comenzi, text="🚚 Comenzi")

        # Initializare UI
        self.build_dashboard_ui()
        self.build_clienti_ui()
        self.build_produse_ui()
        self.build_comenzi_ui()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0: self.refresh_dashboard()
        elif idx == 1: self.refresh_clienti()
        elif idx == 2: self.refresh_produse_data()
        elif idx == 3: self.refresh_comenzi()
    
    def get_conn(self): return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    # --- DASHBOARD ---
    def build_dashboard_ui(self):
        ttk.Label(self.tab_dashboard, text="Analiză Performanță", font=("Helvetica", 16, "bold")).pack(pady=(0, 20), anchor="w")
        self.charts_frame = ttk.Frame(self.tab_dashboard)
        self.charts_frame.pack(fill=BOTH, expand=YES)
        self.fr_left = ttk.Frame(self.charts_frame); self.fr_left.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)
        self.fr_right = ttk.Frame(self.charts_frame); self.fr_right.pack(side=RIGHT, fill=BOTH, expand=YES, padx=10)

    def refresh_dashboard(self):
        for w in self.fr_left.winfo_children(): w.destroy()
        for w in self.fr_right.winfo_children(): w.destroy()
        
        try:
            conn = self.get_conn(); cur = conn.cursor()
            
            # Pie Chart
            cur.execute("SELECT d.oras, SUM(s.cantitate * s.pret_minim) FROM STOC s JOIN DEPOZIT d ON s.depozit_id = d.depozit_id GROUP BY d.oras")
            labels, sizes = [], []
            for r in cur: 
                if r[1]: labels.append(r[0]); sizes.append(r[1])
            
            fig1, ax1 = plt.subplots(figsize=(5,4), dpi=100)
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#3498db','#e74c3c','#2ecc71'])
            ax1.set_title("Valoare Stoc / Oraș")
            FigureCanvasTkAgg(fig1, self.fr_left).get_tk_widget().pack(fill=BOTH, expand=YES)

            # Bar Chart
            cur.execute("SELECT p.denumire, SUM(s.cantitate) FROM STOC s JOIN PRODUS p ON s.produs_id = p.produs_id GROUP BY p.denumire ORDER BY SUM(s.cantitate) DESC FETCH FIRST 5 ROWS ONLY")
            prods, qtys = [], []
            for r in cur: prods.append(r[0][:10]+".."); qtys.append(r[1])
            
            fig2, ax2 = plt.subplots(figsize=(5,4), dpi=100)
            ax2.bar(prods, qtys, color='#18bc9c')
            ax2.set_title("Top 5 Produse (Cantitate)")
            FigureCanvasTkAgg(fig2, self.fr_right).get_tk_widget().pack(fill=BOTH, expand=YES)
            
            conn.close()
        except: plt.close('all')

    # --- CLIENTI ---
    def build_clienti_ui(self):
        frm_add = ttk.Labelframe(self.tab_clienti, text="Adăugare Client", padding=15)
        frm_add.pack(fill=X, pady=(0, 20))
        
        ttk.Label(frm_add, text="Nume:").grid(row=0, column=0, padx=5, sticky=E)
        self.ent_cnume = ttk.Entry(frm_add, width=30); self.ent_cnume.grid(row=0, column=1, padx=5)
        
        ttk.Label(frm_add, text="Cod Fiscal:").grid(row=0, column=2, padx=5, sticky=E)
        self.ent_cfiscal = ttk.Entry(frm_add, width=20); self.ent_cfiscal.grid(row=0, column=3, padx=5)
        
        ttk.Label(frm_add, text="Tip:").grid(row=0, column=4, padx=5, sticky=E)
        self.cb_ctip = ttk.Combobox(frm_add, values=["B2C", "B2B"], width=10, state="readonly"); self.cb_ctip.current(0); self.cb_ctip.grid(row=0, column=5, padx=5)
        
        ttk.Button(frm_add, text="Salvează", bootstyle="success", command=self.add_client).grid(row=0, column=6, padx=20)
        
        self.tr_client = ttk.Treeview(self.tab_clienti, columns=("ID","NUME","FISCAL","TIP"), show="headings", bootstyle="primary")
        for c in ("ID","NUME","FISCAL","TIP"): self.tr_client.heading(c, text=c)
        self.tr_client.pack(fill=BOTH, expand=YES)
        ttk.Button(self.tab_clienti, text="Șterge Selectat", bootstyle="danger-outline", command=self.del_client).pack(pady=10, anchor=E)

    def refresh_clienti(self):
        for i in self.tr_client.get_children(): self.tr_client.delete(i)
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.execute("SELECT client_id, nume, cod_fiscal, tip FROM CLIENT ORDER BY client_id DESC")
            for r in cur: self.tr_client.insert("", END, values=r)
            conn.close()
        except: pass

    def add_client(self):
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_CLIENT", [self.cb_ctip.get(), self.ent_cnume.get(), self.ent_cfiscal.get(), "Ro", "Std"])
            conn.close(); self.refresh_clienti(); messagebox.showinfo("OK", "Client adaugat!")
        except Exception as e: messagebox.showerror("Err", str(e))
    
    def del_client(self):
        sel = self.tr_client.selection()
        if not sel: return
        cid = self.tr_client.item(sel[0])['values'][0]
        if messagebox.askyesno("?", "Stergi?"):
            try:
                conn = self.get_conn(); cur = conn.cursor()
                cur.callproc("ADMIN_STERGE_CLIENT", [cid])
                conn.close(); self.refresh_clienti()
            except: messagebox.showerror("Err", "Are comenzi!")

    # --- PRODUSE ---
    def build_produse_ui(self):
        content = ttk.Frame(self.tab_produse); content.pack(fill=BOTH, expand=YES)
        
        # Stanga
        frm_left = ttk.Labelframe(content, text="Produs Nou", padding=15)
        frm_left.pack(side=LEFT, fill=Y, padx=(0, 10))
        
        ttk.Label(frm_left, text="Denumire:").pack(anchor=W); self.en_pname = ttk.Entry(frm_left); self.en_pname.pack(fill=X, pady=5)
        ttk.Label(frm_left, text="SKU:").pack(anchor=W); self.en_psku = ttk.Entry(frm_left); self.en_psku.pack(fill=X, pady=5)
        ttk.Label(frm_left, text="Categorie:").pack(anchor=W); self.cb_pcat = ttk.Combobox(frm_left, state="readonly"); self.cb_pcat.pack(fill=X, pady=5)
        ttk.Label(frm_left, text="Brand:").pack(anchor=W); self.cb_pbrand = ttk.Combobox(frm_left, state="readonly"); self.cb_pbrand.pack(fill=X, pady=5)
        ttk.Label(frm_left, text="Pret (RON):").pack(anchor=W); self.en_ppret = ttk.Entry(frm_left); self.en_ppret.pack(fill=X, pady=5)
        ttk.Label(frm_left, text="Garantie:").pack(anchor=W); self.en_pgar = ttk.Entry(frm_left); self.en_pgar.insert(0,"24"); self.en_pgar.pack(fill=X, pady=5)
        ttk.Button(frm_left, text="Salvează Produs", bootstyle="primary", command=self.add_prod).pack(fill=X, pady=20)
        
        # Dreapta
        frm_right = ttk.Labelframe(content, text="Catalog & Stoc", padding=10)
        frm_right.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        self.tr_prod = ttk.Treeview(frm_right, columns=("ID","NUME","SKU","CAT","BRAND"), show="headings", bootstyle="info")
        self.tr_prod.heading("ID", text="ID"); self.tr_prod.column("ID", width=40)
        self.tr_prod.heading("NUME", text="Nume"); self.tr_prod.column("NUME", width=120)
        self.tr_prod.heading("SKU", text="SKU"); self.tr_prod.column("SKU", width=80)
        self.tr_prod.heading("CAT", text="Cat"); self.tr_prod.column("CAT", width=80)
        self.tr_prod.heading("BRAND", text="Brand"); self.tr_prod.column("BRAND", width=80)
        self.tr_prod.pack(fill=BOTH, expand=YES)
        
        btns = ttk.Frame(frm_right, padding=10)
        btns.pack(fill=X)
        ttk.Button(btns, text="➕ Intrare Marfă", bootstyle="success", command=self.open_restock).pack(side=RIGHT, padx=5)
        ttk.Button(btns, text="📍 Distribuție", bootstyle="info-outline", command=self.view_dist).pack(side=RIGHT, padx=5)

    def refresh_produse_data(self):
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.execute("SELECT categorie_id, nume FROM CATEGORIE"); self.cat_map = {r[1]:r[0] for r in cur}
            self.cb_pcat['values'] = list(self.cat_map.keys())
            cur.execute("SELECT producator_id, nume FROM PRODUCATOR"); self.producator_map = {r[1]:r[0] for r in cur}
            self.cb_pbrand['values'] = list(self.producator_map.keys())
            
            for i in self.tr_prod.get_children(): self.tr_prod.delete(i)
            cur.execute("SELECT p.produs_id, p.denumire, p.cod_sku, c.nume, pr.nume FROM PRODUS p JOIN CATEGORIE c ON p.categorie_id=c.categorie_id JOIN PRODUCATOR pr ON p.producator_id=pr.producator_id ORDER BY p.produs_id DESC")
            for r in cur: self.tr_prod.insert("", END, values=r)
            conn.close()
        except: pass

    def add_prod(self):
        try:
            conn = self.get_conn(); cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_PRODUS_NOU", [self.en_pname.get(), self.en_psku.get(), self.cat_map[self.cb_pcat.get()], self.producator_map[self.cb_pbrand.get()], int(self.en_pgar.get()), float(self.en_ppret.get())])
            conn.close(); self.refresh_produse_data(); messagebox.showinfo("Ok", "Produs creat!")
        except Exception as e: messagebox.showerror("Err", str(e))

    def view_dist(self):
        sel = self.tr_prod.selection()
        if not sel: return
        pid = self.tr_prod.item(sel[0])['values'][0]
        top = ttk.Toplevel(title="Distributie Stoc"); top.geometry("400x300")
        tr = ttk.Treeview(top, columns=("DEP","ORAS","QTY"), show="headings", bootstyle="info")
        tr.heading("DEP", text="Depozit"); tr.heading("ORAS", text="Oras"); tr.heading("QTY", text="Buc")
        tr.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        try:
            conn=self.get_conn(); cur=conn.cursor()
            cur.execute("SELECT d.nume, d.oras, s.cantitate FROM STOC s JOIN DEPOZIT d ON s.depozit_id=d.depozit_id WHERE s.produs_id=:1", [pid])
            for r in cur: tr.insert("", END, values=r)
            conn.close()
        except: pass

    def open_restock(self):
        sel = self.tr_prod.selection()
        if not sel: return
        pid = self.tr_prod.item(sel[0])['values'][0]
        
        top = ttk.Toplevel(title="Receptie Marfa"); top.geometry("350x250")
        ttk.Label(top, text="Intrare Stoc", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        frm = ttk.Frame(top); frm.pack(pady=10)
        ttk.Label(frm, text="Depozit:").grid(row=0, column=0)
        cb = ttk.Combobox(frm, state="readonly"); cb.grid(row=0, column=1)
        ttk.Label(frm, text="Cantitate:").grid(row=1, column=0)
        en = ttk.Entry(frm); en.grid(row=1, column=1)
        
        dep_map = {}
        try:
            conn=self.get_conn(); cur=conn.cursor(); cur.execute("SELECT depozit_id, nume FROM DEPOZIT")
            for r in cur: dep_map[r[1]]=r[0]
            cb['values']=list(dep_map.keys()); cb.current(0); conn.close()
        except: pass

        def save():
            try:
                conn=self.get_conn(); cur=conn.cursor()
                cur.callproc("ADMIN_APROVIZIONARE", [pid, dep_map[cb.get()], int(en.get())])
                conn.close(); top.destroy(); messagebox.showinfo("Ok", "Stoc actualizat!")
            except Exception as e: messagebox.showerror("Err", str(e))
        
        ttk.Button(top, text="Confirmă", bootstyle="success", command=save).pack(pady=10)


    # --- COMENZI ---
    def build_comenzi_ui(self):
        frm_act = ttk.Labelframe(self.tab_comenzi, text="Acțiuni", padding=10)
        frm_act.pack(side=BOTTOM, fill=X, pady=10)
        
        ttk.Button(frm_act, text="În Procesare", bootstyle="secondary", command=lambda: self.ch_stat("In Procesare")).pack(side=LEFT, padx=5, expand=YES)
        ttk.Button(frm_act, text="Finalizează (+AWB)", bootstyle="success", command=lambda: self.ch_stat("Finalizata")).pack(side=LEFT, padx=5, expand=YES)
        ttk.Button(frm_act, text="Anulează", bootstyle="danger", command=lambda: self.ch_stat("Anulata")).pack(side=LEFT, padx=5, expand=YES)

        frm_filt = ttk.Frame(self.tab_comenzi, padding=10)
        frm_filt.pack(side=TOP, fill=X)
        ttk.Label(frm_filt, text="Filtru Status:").pack(side=LEFT)
        self.cb_cfilt = ttk.Combobox(frm_filt, values=["Toate","In Asteptare","In Procesare","Finalizata","Anulata"], state="readonly")
        self.cb_cfilt.current(0); self.cb_cfilt.pack(side=LEFT, padx=5)
        self.cb_cfilt.bind("<<ComboboxSelected>>", lambda e: self.refresh_comenzi())
        ttk.Button(frm_filt, text="Refresh", bootstyle="link", command=self.refresh_comenzi).pack(side=RIGHT)

        self.tr_cmd = ttk.Treeview(self.tab_comenzi, columns=("ID","CLIENT","DATA","LIV","AWB","TOT","STAT"), show="headings", bootstyle="primary")
        self.tr_cmd.heading("ID", text="ID"); self.tr_cmd.column("ID", width=50)
        self.tr_cmd.heading("CLIENT", text="Client"); self.tr_cmd.column("CLIENT", width=120)
        self.tr_cmd.heading("DATA", text="Data"); self.tr_cmd.column("DATA", width=80)
        self.tr_cmd.heading("LIV", text="Livrare"); self.tr_cmd.column("LIV", width=100)
        self.tr_cmd.heading("AWB", text="AWB"); self.tr_cmd.column("AWB", width=100)
        self.tr_cmd.heading("TOT", text="Total"); self.tr_cmd.column("TOT", width=80, anchor=E)
        self.tr_cmd.heading("STAT", text="Status"); self.tr_cmd.column("STAT", width=100)
        self.tr_cmd.pack(fill=BOTH, expand=YES)
        
        self.tr_cmd.tag_configure('anulata', foreground='gray')
        self.tr_cmd.tag_configure('finalizata', foreground='green')

    def refresh_comenzi(self):
        for i in self.tr_cmd.get_children(): self.tr_cmd.delete(i)
        flt = self.cb_cfilt.get()
        try:
            conn=self.get_conn(); cur=conn.cursor()
            cur.execute("SELECT cv_id, nume_client, data_creare, metoda_livrare, awb, valoare_totala, status FROM V_ISTORIC_SUMAR ORDER BY cv_id DESC")
            for r in cur:
                if flt != "Toate" and flt != r[6]: continue
                tag = 'anulata' if r[6]=='Anulata' else ('finalizata' if r[6]=='Finalizata' else '')
                dat = r[2].strftime('%d-%m') if r[2] else ""
                awb = r[4] if r[4] else "-"
                self.tr_cmd.insert("", END, values=(r[0], r[1], dat, r[3], awb, f"{r[5]} RON", r[6]), tags=(tag,))
            conn.close()
        except: pass

    def ch_stat(self, st):
        sel = self.tr_cmd.selection()
        if not sel: return
        cid = self.tr_cmd.item(sel[0])['values'][0]
        try:
            conn=self.get_conn(); cur=conn.cursor()
            cur.callproc("ADMIN_UPDATE_STATUS_COMANDA", [cid, st])
            conn.close(); self.refresh_comenzi(); messagebox.showinfo("Ok", f"Status: {st}")
        except Exception as e: messagebox.showerror("Err", str(e))

# ================= AGENT PAGE (PROFI) =================
class AgentPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        nav = ttk.Frame(self, bootstyle="info"); nav.pack(side=TOP, fill=X)
        ttk.Label(nav, text="  MODUL VÂNZĂRI", font=("Helvetica", 14, "bold"), bootstyle="inverse-info").pack(side=LEFT, pady=15)
        ttk.Button(nav, text="Ieșire", bootstyle="light-outline", command=lambda: controller.show_frame("LoginPage")).pack(side=RIGHT, padx=20)

        main = ttk.Frame(self, padding=20); main.pack(fill=BOTH, expand=YES)
        
        # Stanga: Formular
        frm_l = ttk.Labelframe(main, text="Vânzare Nouă", padding=20); frm_l.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))
        
        ttk.Label(frm_l, text="Client:").pack(anchor=W); self.cb_cli = ttk.Combobox(frm_l, state="readonly"); self.cb_cli.pack(fill=X, pady=5)
        ttk.Label(frm_l, text="Produs:").pack(anchor=W); self.cb_prd = ttk.Combobox(frm_l, state="readonly"); self.cb_prd.pack(fill=X, pady=5)
        self.lbl_stoc = ttk.Label(frm_l, text="Stoc: -", bootstyle="secondary"); self.lbl_stoc.pack(anchor=W)
        self.cb_prd.bind("<<ComboboxSelected>>", self.on_prod)
        
        f2 = ttk.Frame(frm_l); f2.pack(fill=X, pady=10)
        ttk.Label(f2, text="Cantitate:").pack(side=LEFT)
        self.en_qty = ttk.Entry(f2, width=8); self.en_qty.pack(side=LEFT, padx=5); self.en_qty.insert(0,"1")
        self.en_qty.bind("<KeyRelease>", self.calc)
        
        ttk.Label(frm_l, text="Livrare:").pack(anchor=W); self.cb_liv = ttk.Combobox(frm_l, values=["Ridicare Personala","Curier Rapid"], state="readonly"); self.cb_liv.current(0); self.cb_liv.pack(fill=X, pady=5)
        
        # Dreapta: Sumar
        frm_r = ttk.Labelframe(main, text="Sumar & Plată", padding=20); frm_r.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        self.lbl_total = ttk.Label(frm_r, text="0.00 RON", font=("Helvetica", 24, "bold"), bootstyle="success"); self.lbl_total.pack(pady=40)
        ttk.Button(frm_r, text="✅ PLASEAZĂ COMANDA", bootstyle="success", command=self.save).pack(fill=X, pady=20)

        self.cli_map={}; self.prd_data={}

    def get_conn(self): return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    
    def refresh_data(self):
        try:
            conn=self.get_conn(); cur=conn.cursor()
            cur.execute("SELECT client_id, nume FROM CLIENT"); self.cli_map={r[1]:r[0] for r in cur}
            self.cb_cli['values']=list(self.cli_map.keys())
            cur.execute("SELECT p.produs_id, p.denumire, s.pret_minim, s.cantitate FROM PRODUS p JOIN STOC s ON p.produs_id=s.produs_id WHERE s.depozit_id=1")
            self.prd_data={r[1]:{'id':r[0],'pr':r[2],'st':r[3]} for r in cur}
            self.cb_prd['values']=list(self.prd_data.keys())
            conn.close()
        except: pass

    def on_prod(self, e):
        d = self.prd_data.get(self.cb_prd.get())
        if d: 
            self.lbl_stoc.config(text=f"Stoc: {d['st']} buc", bootstyle="danger" if d['st']<10 else "secondary")
            self.calc()

    def calc(self, e=None):
        try:
            p = self.prd_data[self.cb_prd.get()]['pr']
            q = int(self.en_qty.get())
            self.lbl_total.config(text=f"{p*q:.2f} RON")
        except: self.lbl_total.config(text="0.00 RON")

    def save(self):
        try:
            cid = self.cli_map[self.cb_cli.get()]
            pid = self.prd_data[self.cb_prd.get()]['id']
            qty = int(self.en_qty.get())
            conn=self.get_conn(); cur=conn.cursor()
            cur.callproc("ADAUGA_COMANDA_COMPLETA", [cid, pid, qty, self.cb_liv.get(), 0])
            conn.close(); messagebox.showinfo("Succes", "Vandut!"); self.refresh_data()
        except Exception as e: messagebox.showerror("Err", str(e))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
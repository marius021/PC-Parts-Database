import tkinter as tk
from tkinter import ttk, messagebox
import oracledb

# ================= CONFIGURARE DATABASE =================
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"
DB_DSN = "localhost:1521/freepdb1"

# ================= CLASA PRINCIPALĂ (CONTROLLER) =================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PC Parts Management System")
        self.geometry("800x650")
        
        # Container pentru frame-uri
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        
        # Dicționar pentru a stoca ferestrele
        self.frames = {}
        
        # Initializam ferestrele
        for F in (LoginPage, AdminPage, AgentPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        '''Functie pentru a schimba ferestrele'''
        frame = self.frames[page_name]
        frame.tkraise()
        # Daca intram in Admin sau Agent, vrem sa facem refresh la date
        if hasattr(frame, 'refresh_data'):
            frame.refresh_data()

# ================= PAGINA DE LOGIN =================
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#2c3e50")
        
        lbl_title = tk.Label(self, text="PC PARTS MANAGER", font=("Arial", 24, "bold"), fg="white", bg="#2c3e50")
        lbl_title.pack(pady=80)
        
        # Buton Agent
        btn_agent = tk.Button(self, text="👤 Login Agent Vânzări", font=("Arial", 14), width=25, height=2,
                              command=lambda: controller.show_frame("AgentPage"))
        btn_agent.pack(pady=20)
        
        # Buton Admin
        btn_admin = tk.Button(self, text="🛠️ Login Administrator", font=("Arial", 14), width=25, height=2,
                              bg="#e74c3c", fg="white",
                              command=lambda: controller.show_frame("AdminPage"))
        btn_admin.pack(pady=20)

# ================= PAGINA ADMIN =================
class AdminPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = tk.Frame(self, bg="#e74c3c", height=50)
        header.pack(fill="x")
        tk.Label(header, text="PANOU ADMINISTRATOR", bg="#e74c3c", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(header, text="Log Out", command=lambda: controller.show_frame("LoginPage")).pack(side="right", padx=10, pady=10)

        # Tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab Clienti
        self.tab_clienti = tk.Frame(notebook)
        notebook.add(self.tab_clienti, text="Gestionare Clienți")
        self.build_clienti_ui()

    def build_clienti_ui(self):
        # Zona Adaugare
        frame_add = tk.LabelFrame(self.tab_clienti, text="Adaugă Client Nou")
        frame_add.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_add, text="Nume:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_nume = tk.Entry(frame_add, width=30)
        self.ent_nume.grid(row=0, column=1)
        
        tk.Label(frame_add, text="Cod Fiscal:").grid(row=0, column=2, padx=5)
        self.ent_fiscal = tk.Entry(frame_add)
        self.ent_fiscal.grid(row=0, column=3)
        
        tk.Label(frame_add, text="Tip:").grid(row=1, column=0, padx=5)
        self.combo_tip = ttk.Combobox(frame_add, values=["B2C", "B2B"], width=10)
        self.combo_tip.grid(row=1, column=1, sticky="w")
        self.combo_tip.current(0)

        tk.Label(frame_add, text="Țara:").grid(row=1, column=2, padx=5)
        self.ent_tara = tk.Entry(frame_add)
        self.ent_tara.insert(0, "Romania")
        self.ent_tara.grid(row=1, column=3)

        tk.Button(frame_add, text="Salvează Client", bg="green", fg="white", command=self.add_client).grid(row=1, column=4, padx=20)

        # Zona Lista & Stergere
        frame_list = tk.LabelFrame(self.tab_clienti, text="Listă Clienți (Selectează pentru ștergere)")
        frame_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("id", "nume", "fiscal", "tip")
        self.tree = ttk.Treeview(frame_list, columns=cols, show="headings")
        for col in cols: self.tree.heading(col, text=col.upper())
        self.tree.pack(side="left", fill="both", expand=True)
        
        btn_del = tk.Button(frame_list, text="🗑️ Șterge Client Selectat", bg="red", fg="white", command=self.delete_client)
        btn_del.pack(side="right", fill="y", padx=5)

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    def refresh_data(self):
        # Reincarcam lista de clienti
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT client_id, nume, cod_fiscal, tip FROM CLIENT ORDER BY client_id DESC")
            for row in cur:
                self.tree.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(e)

    def add_client(self):
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADMIN_ADAUGA_CLIENT", [
                self.combo_tip.get(),
                self.ent_nume.get(),
                self.ent_fiscal.get(),
                self.ent_tara.get(),
                "Standard" # Default
            ])
            conn.close()
            messagebox.showinfo("Succes", "Client adăugat!")
            self.refresh_data()
            self.ent_nume.delete(0, tk.END)
            self.ent_fiscal.delete(0, tk.END)
        except oracledb.DatabaseError as e:
            messagebox.showerror("Eroare", e.args[0].message)

    def delete_client(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenție", "Selectează un client din listă!")
            return
        
        client_id = self.tree.item(selected[0])['values'][0]
        
        if messagebox.askyesno("Confirmare", "Sigur vrei să ștergi clientul?"):
            try:
                conn = self.get_conn()
                cur = conn.cursor()
                cur.callproc("ADMIN_STERGE_CLIENT", [client_id])
                conn.close()
                messagebox.showinfo("Succes", "Client șters!")
                self.refresh_data()
            except oracledb.DatabaseError as e:
                # Aici prindem eroarea personalizata din PL/SQL (Client cu comenzi)
                messagebox.showerror("Eroare Ștergere", e.args[0].message)


# ================= PAGINA AGENT (Codul Anterior Adaptat) =================
class AgentPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = tk.Frame(self, bg="#2980b9", height=50)
        header.pack(fill="x")
        tk.Label(header, text="PANOU AGENT VÂNZĂRI", bg="#2980b9", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        tk.Button(header, text="Log Out", command=lambda: controller.show_frame("LoginPage")).pack(side="right", padx=10, pady=10)

        # Tab-urile vechi
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_vanzare = tk.Frame(notebook)
        self.tab_istoric = tk.Frame(notebook)
        notebook.add(self.tab_vanzare, text="🛒 Vânzare Nouă")
        notebook.add(self.tab_istoric, text="📜 Istoric Comenzi")

        # Initializare logica veche (simplificata pentru exemplu)
        self.init_vanzare_ui()
        self.init_istoric_ui()
        
        self.client_map = {}
        self.produs_map = {}

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    def refresh_data(self):
        # Functie apelata cand intram pe pagina
        self.populeaza_dropdowns()
        self.refresh_istoric()

    def init_vanzare_ui(self):
        fr = tk.Frame(self.tab_vanzare, padx=20, pady=20)
        fr.pack(fill="both")
        
        tk.Label(fr, text="Client:").grid(row=0, column=0)
        self.cb_client = ttk.Combobox(fr, width=30)
        self.cb_client.grid(row=0, column=1)
        
        tk.Label(fr, text="Produs:").grid(row=1, column=0)
        self.cb_produs = ttk.Combobox(fr, width=30)
        self.cb_produs.grid(row=1, column=1)
        
        tk.Label(fr, text="Cantitate:").grid(row=2, column=0)
        self.ent_cant = tk.Entry(fr)
        self.ent_cant.grid(row=2, column=1)
        
        tk.Button(fr, text="Vinde", bg="green", fg="white", command=self.vinde).grid(row=3, column=1, pady=10)

    def init_istoric_ui(self):
        self.tree = ttk.Treeview(self.tab_istoric, columns=("id", "client", "total"), show="headings")
        self.tree.heading("id", text="ID"); self.tree.heading("client", text="Client"); self.tree.heading("total", text="Total")
        self.tree.pack(fill="both", expand=True)

    def populeaza_dropdowns(self):
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT client_id, nume FROM CLIENT")
            self.client_map = {row[1]: row[0] for row in cur}
            self.cb_client['values'] = list(self.client_map.keys())
            
            cur.execute("SELECT produs_id, denumire FROM PRODUS")
            self.produs_map = {row[1]: row[0] for row in cur}
            self.cb_produs['values'] = list(self.produs_map.keys())
            conn.close()
        except: pass

    def refresh_istoric(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            conn = self.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT cv_id, nume_client, valoare_totala FROM V_ISTORIC_SUMAR")
            for row in cur: self.tree.insert("", "end", values=row)
            conn.close()
        except: pass

    def vinde(self):
        # Logica simplificata de apelare procedura existenta
        try:
            cid = self.client_map[self.cb_client.get()]
            pid = self.produs_map[self.cb_produs.get()]
            cant = int(self.ent_cant.get())
            
            conn = self.get_conn()
            cur = conn.cursor()
            cur.callproc("ADAUGA_COMANDA_COMPLETA", [cid, pid, cant, "Ridicare", 0])
            conn.close()
            messagebox.showinfo("Succes", "Vandut!")
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
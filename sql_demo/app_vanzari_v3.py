import tkinter as tk
from tkinter import ttk, messagebox
import oracledb

# ================= CONFIGURARE =================
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"
DB_DSN = "localhost:1521/freepdb1"

class AplicatieCompleta:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Parts Manager - Agent Vânzări")
        self.root.geometry("700x600")

        # Configurare Stil
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

        # --- SISTEMUL DE TAB-URI ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        # Creare Frame-uri pentru Tab-uri
        self.tab_vanzare = tk.Frame(self.notebook, bg="#f0f0f0")
        self.tab_istoric = tk.Frame(self.notebook, bg="#f0f0f0")

        self.notebook.add(self.tab_vanzare, text="🛒 Vânzare Nouă")
        self.notebook.add(self.tab_istoric, text="📜 Istoric Comenzi")

        # Initializare componente pentru fiecare Tab
        self.init_tab_vanzare()
        self.init_tab_istoric()

        # Incarcare Date
        self.client_map = {}
        self.produs_info = {}
        self.populeaza_date_vanzare()
        self.refresh_istoric() # Incarca istoricul la pornire

    # ==================================================
    # LOGICA TAB 1: VANZARE (Codul anterior, adaptat)
    # ==================================================
    def init_tab_vanzare(self):
        main_frame = tk.Frame(self.tab_vanzare, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Zona Detalii
        lf_detalii = tk.LabelFrame(main_frame, text="1. Client & Livrare", font=("Arial", 10, "bold"))
        lf_detalii.pack(fill="x", pady=10)

        tk.Label(lf_detalii, text="Client:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_client = ttk.Combobox(lf_detalii, width=30, state="readonly")
        self.combo_client.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(lf_detalii, text="Livrare:").grid(row=0, column=2, padx=5, pady=5)
        self.combo_livrare = ttk.Combobox(lf_detalii, width=20, state="readonly")
        self.combo_livrare['values'] = ('Curier Rapid', 'Ridicare Personala', 'Posta')
        self.combo_livrare.current(0)
        self.combo_livrare.grid(row=0, column=3, padx=5, pady=5)

        # Zona Produs
        lf_produs = tk.LabelFrame(main_frame, text="2. Produs & Calcul", font=("Arial", 10, "bold"))
        lf_produs.pack(fill="x", pady=10)

        tk.Label(lf_produs, text="Produs:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_produs = ttk.Combobox(lf_produs, width=40, state="readonly")
        self.combo_produs.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="w")
        self.combo_produs.bind("<<ComboboxSelected>>", self.actualizeaza_info_produs)

        self.lbl_stoc = tk.Label(lf_produs, text="Stoc: -", fg="gray")
        self.lbl_stoc.grid(row=0, column=4, padx=5)

        tk.Label(lf_produs, text="Cantitate:").grid(row=1, column=0, padx=5, pady=5)
        self.ent_cantitate = tk.Spinbox(lf_produs, from_=1, to=100, width=5, command=self.calculeaza_total)
        self.ent_cantitate.grid(row=1, column=1, sticky="w")
        self.ent_cantitate.bind("<KeyRelease>", self.calculeaza_total)

        tk.Label(lf_produs, text="Preț (RON):").grid(row=1, column=2, padx=5)
        self.ent_pret = tk.Entry(lf_produs, width=10, state="readonly")
        self.ent_pret.grid(row=1, column=3, sticky="w")

        tk.Label(lf_produs, text="Discount %:").grid(row=1, column=4, padx=5)
        self.ent_disc = tk.Entry(lf_produs, width=5)
        self.ent_disc.insert(0, "0")
        self.ent_disc.grid(row=1, column=5, sticky="w")
        self.ent_disc.bind("<KeyRelease>", self.calculeaza_total)

        # Zona Total & Buton
        self.lbl_total = tk.Label(main_frame, text="TOTAL: 0.00 RON", font=("Arial", 14, "bold"), fg="red")
        self.lbl_total.pack(pady=15)

        btn_save = tk.Button(main_frame, text="💾 SALVEAZĂ COMANDA", bg="#4CAF50", fg="white", 
                             font=("Arial", 11, "bold"), command=self.salveaza_comanda)
        btn_save.pack(ipadx=20, ipady=5)

    # ==================================================
    # LOGICA TAB 2: ISTORIC (NOU)
    # ==================================================
    def init_tab_istoric(self):
        frame_istoric = tk.Frame(self.tab_istoric, padx=10, pady=10)
        frame_istoric.pack(fill="both", expand=True)

        # Buton Refresh
        btn_refresh = tk.Button(frame_istoric, text="🔄 Actualizează Lista", command=self.refresh_istoric)
        btn_refresh.pack(anchor="ne", pady=5)

        # Tabel (Treeview)
        columns = ("id", "client", "data", "livrare", "total")
        self.tree = ttk.Treeview(frame_istoric, columns=columns, show="headings", height=15)
        
        # Configurare coloane
        self.tree.heading("id", text="ID Comandă")
        self.tree.column("id", width=80, anchor="center")
        
        self.tree.heading("client", text="Client")
        self.tree.column("client", width=150)
        
        self.tree.heading("data", text="Data")
        self.tree.column("data", width=100, anchor="center")
        
        self.tree.heading("livrare", text="Metodă Livrare")
        self.tree.column("livrare", width=120)

        self.tree.heading("total", text="Total (RON)")
        self.tree.column("total", width=100, anchor="e")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_istoric, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ==================================================
    # FUNCTII AJUTATOARE (Database)
    # ==================================================
    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    def populeaza_date_vanzare(self):
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Clienti
            cursor.execute("SELECT client_id, nume FROM CLIENT")
            for r in cursor: self.client_map[r[1]] = r[0]
            self.combo_client['values'] = list(self.client_map.keys())

            # Produse
            cursor.execute("SELECT p.produs_id, p.denumire, s.pret_minim, s.cantitate FROM PRODUS p JOIN STOC s ON p.produs_id = s.produs_id WHERE s.depozit_id = 1")
            for r in cursor:
                self.produs_info[r[1]] = {'id': r[0], 'pret': r[2], 'stoc': r[3]}
            self.combo_produs['values'] = list(self.produs_info.keys())
            conn.close()
        except Exception as e:
            print(e)

    def actualizeaza_info_produs(self, event):
        nume = self.combo_produs.get()
        if nume in self.produs_info:
            info = self.produs_info[nume]
            self.ent_pret.config(state="normal")
            self.ent_pret.delete(0, tk.END)
            self.ent_pret.insert(0, str(info['pret']))
            self.ent_pret.config(state="readonly")
            
            stoc = info['stoc']
            self.lbl_stoc.config(text=f"Stoc: {stoc} buc", fg="green" if stoc > 0 else "red")
            self.calculeaza_total()

    def calculeaza_total(self, event=None):
        try:
            pret = float(self.ent_pret.get())
            cant = int(self.ent_cantitate.get())
            disc = float(self.ent_disc.get())
            total = (pret * cant) * (1 - disc/100)
            self.lbl_total.config(text=f"TOTAL: {total:.2f} RON")
        except:
            pass

    def salveaza_comanda(self):
        try:
            # Preluare date
            client_nume = self.combo_client.get()
            produs_nume = self.combo_produs.get()
            
            if not client_nume or not produs_nume:
                messagebox.showwarning("Eroare", "Selectează clientul și produsul!")
                return

            client_id = self.client_map[client_nume]
            produs_id = self.produs_info[produs_nume]['id']
            cantitate = int(self.ent_cantitate.get())
            livrare = self.combo_livrare.get()
            discount = float(self.ent_disc.get())

            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Apel Procedura
            cursor.callproc("ADAUGA_COMANDA_COMPLETA", [client_id, produs_id, cantitate, livrare, discount])
            
            messagebox.showinfo("Succes", "Comanda a fost salvată!")
            
            # Refresh automat la tab-ul de istoric si la stocuri
            self.populeaza_date_vanzare()
            self.refresh_istoric()
            conn.close()
            
        except oracledb.DatabaseError as e:
            error, = e.args
            messagebox.showerror("Eroare Oracle", error.message)

    def refresh_istoric(self):
        # Golire tabel
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Select din Vederea nou creata
            cursor.execute("SELECT cv_id, nume_client, data_creare, metoda_livrare, valoare_totala FROM V_ISTORIC_SUMAR")
            
            for row in cursor:
                # Formatare data si bani
                data_fmt = row[2].strftime('%d-%m-%Y') if row[2] else ""
                bani_fmt = f"{row[4]:.2f}" if row[4] else "0.00"
                
                self.tree.insert("", "end", values=(row[0], row[1], data_fmt, row[3], bani_fmt))
                
            conn.close()
        except Exception as e:
            messagebox.showerror("Eroare Istoric", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieCompleta(root)
    root.mainloop()
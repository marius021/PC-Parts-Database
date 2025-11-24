import tkinter as tk
from tkinter import ttk, messagebox
import oracledb

# ================= CONFIGURARE =================
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"
DB_DSN = "localhost:1521/freepdb1"

class AplicatieVanzariAvansata:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Parts - Sistem Vânzări v2.0")
        self.root.geometry("600x550")

        # Stocare Date Locale
        self.client_map = {} 
        self.produs_info = {} # { 'Nume Produs': {'id': 1, 'pret': 100, 'stoc': 50} }

        # --- Titlu ---
        tk.Label(root, text="Procesare Comandă & Ofertare", font=("Segoe UI", 16, "bold"), fg="#333").pack(pady=15)

        # --- Container Principal ---
        main_frame = tk.Frame(root)
        main_frame.pack(padx=20, pady=5, fill="both", expand=True)

        # === ZONA 1: DETALII GENERALE ===
        lf_detalii = tk.LabelFrame(main_frame, text="Detalii Comandă", font=("Arial", 10, "bold"), fg="blue")
        lf_detalii.pack(fill="x", pady=10)

        # Client
        tk.Label(lf_detalii, text="Client:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.combo_client = ttk.Combobox(lf_detalii, width=35, state="readonly")
        self.combo_client.grid(row=0, column=1, padx=10, pady=10)

        # Livrare
        tk.Label(lf_detalii, text="Metodă Livrare:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.combo_livrare = ttk.Combobox(lf_detalii, width=20, state="readonly")
        self.combo_livrare['values'] = ('Curier Rapid', 'Ridicare Personala', 'Posta Romana')
        self.combo_livrare.current(0)
        self.combo_livrare.grid(row=0, column=3, padx=10, pady=10)

        # === ZONA 2: PRODUS SI CALCUL ===
        lf_produs = tk.LabelFrame(main_frame, text="Selecție Produs & Calcul", font=("Arial", 10, "bold"), fg="green")
        lf_produs.pack(fill="x", pady=10)

        # Selectare Produs
        tk.Label(lf_produs, text="Produs:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.combo_produs = ttk.Combobox(lf_produs, width=35, state="readonly")
        self.combo_produs.grid(row=0, column=1, padx=10, pady=10, columnspan=2, sticky="w")
        # Eveniment: Când alegem produsul, actualizăm prețul și stocul
        self.combo_produs.bind("<<ComboboxSelected>>", self.actualizeaza_info_produs)

        # Info Stoc (Label Informativ)
        self.lbl_info_stoc = tk.Label(lf_produs, text="Stoc: -", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_info_stoc.grid(row=0, column=3, padx=10)

        # Pret Unitar (Read Only)
        tk.Label(lf_produs, text="Preț Unitar (RON):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.lbl_pret = tk.Entry(lf_produs, width=15, state="readonly")
        self.lbl_pret.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Cantitate
        tk.Label(lf_produs, text="Cantitate:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_cantitate = tk.Spinbox(lf_produs, from_=1, to=1000, width=13, command=self.calculeaza_total)
        self.ent_cantitate.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        # Bind pentru tastatura (daca scrie manual)
        self.ent_cantitate.bind("<KeyRelease>", self.calculeaza_total)

        # Discount (Câmp NOU)
        tk.Label(lf_produs, text="Discount (%):").grid(row=2, column=2, padx=10, pady=5, sticky="e")
        self.ent_discount = tk.Entry(lf_produs, width=10)
        self.ent_discount.insert(0, "0")
        self.ent_discount.grid(row=2, column=3, padx=10, pady=5, sticky="w")
        self.ent_discount.bind("<KeyRelease>", self.calculeaza_total)

        # === ZONA 3: TOTAL ===
        frame_total = tk.Frame(main_frame, bg="#eee", bd=1, relief="sunken")
        frame_total.pack(fill="x", pady=20)
        
        tk.Label(frame_total, text="TOTAL ESTIMAT:", bg="#eee", font=("Arial", 12)).pack(side="left", padx=20, pady=10)
        self.lbl_total = tk.Label(frame_total, text="0.00 RON", bg="#eee", fg="red", font=("Arial", 14, "bold"))
        self.lbl_total.pack(side="right", padx=20, pady=10)

        # === BUTON FINAL ===
        btn_save = tk.Button(root, text="💾 SALVEAZĂ COMANDA", 
                             bg="#007ACC", fg="white", font=("Arial", 11, "bold"),
                             command=self.salveaza_comanda)
        btn_save.pack(pady=10, ipadx=20, ipady=8)

        # Initializare
        self.populeaza_date()

    def get_conn(self):
        return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

    def populeaza_date(self):
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Clienti
            cursor.execute("SELECT client_id, nume FROM CLIENT")
            for r in cursor: self.client_map[r[1]] = r[0]
            self.combo_client['values'] = list(self.client_map.keys())

            # Produse - Luăm și PREȚUL și STOCUL acum!
            # Interogam vederea sau facem join cu STOC
            sql_prod = """
                SELECT p.produs_id, p.denumire, s.pret_minim, s.cantitate 
                FROM PRODUS p 
                JOIN STOC s ON p.produs_id = s.produs_id 
                WHERE s.depozit_id = 1
            """
            cursor.execute(sql_prod)
            for r in cursor:
                # Structura: { 'Nume': {'id': 1, 'pret': 100, 'stoc': 50} }
                self.produs_info[r[1]] = {'id': r[0], 'pret': r[2], 'stoc': r[3]}
            
            self.combo_produs['values'] = list(self.produs_info.keys())
            
            conn.close()
        except Exception as e:
            messagebox.showerror("Eroare Init", str(e))

    def actualizeaza_info_produs(self, event):
        nume_p = self.combo_produs.get()
        if nume_p in self.produs_info:
            info = self.produs_info[nume_p]
            
            # Actualizare UI Pret
            self.lbl_pret.config(state="normal")
            self.lbl_pret.delete(0, tk.END)
            self.lbl_pret.insert(0, str(info['pret']))
            self.lbl_pret.config(state="readonly")

            # Actualizare UI Stoc
            stoc = info['stoc']
            self.lbl_info_stoc.config(text=f"Stoc disp: {stoc} buc", fg="green" if stoc > 0 else "red")
            
            self.calculeaza_total()

    def calculeaza_total(self, event=None):
        try:
            pret = float(self.lbl_pret.get())
            cant = int(self.ent_cantitate.get())
            disc = float(self.ent_discount.get())

            valoare = pret * cant
            valoare_finala = valoare - (valoare * disc / 100)
            
            self.lbl_total.config(text=f"{valoare_finala:.2f} RON")
        except:
            self.lbl_total.config(text="0.00 RON")

    def salveaza_comanda(self):
        try:
            # Preluare date
            nume_c = self.combo_client.get()
            nume_p = self.combo_produs.get()
            
            if not nume_c or not nume_p:
                messagebox.showwarning("Incomplet", "Alege clientul și produsul!")
                return

            id_client = self.client_map[nume_c]
            id_produs = self.produs_info[nume_p]['id']
            cantitate = int(self.ent_cantitate.get())
            livrare = self.combo_livrare.get()
            discount = float(self.ent_discount.get())

            # Conexiune DB
            conn = self.get_conn()
            cursor = conn.cursor()
            
            # Apel Procedura (acum cu 5 parametri)
            cursor.callproc("ADAUGA_COMANDA_COMPLETA", [id_client, id_produs, cantitate, livrare, discount])
            
            messagebox.showinfo("Succes", "Comanda salvată cu succes!")
            self.populeaza_date() # Reîmprospătare stocuri
            conn.close()

        except oracledb.DatabaseError as e:
            error, = e.args
            # Afișăm doar mesajul relevant din eroarea Oracle
            messagebox.showerror("Eroare Oracle", error.message)
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieVanzariAvansata(root)
    root.mainloop()
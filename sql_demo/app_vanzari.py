import tkinter as tk
from tkinter import ttk, messagebox
import oracledb

# ================= CONFIGURARE CONEXIUNE =================
# Aici punem datele utilizatorului AGENT_VANZARI creat anterior
DB_USER = "AGENT_VANZARI"
DB_PASS = "parolaagent123"  # Parola pe care ai setat-o
DB_DSN = "localhost:1521/freepdb1" # Service name-ul tau

class AplicatieVanzari:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Parts - Interfață Agent Vânzări")
        self.root.geometry("500x400")

        # Variabile pentru stocarea ID-urilor (pentru a trimite ID-ul, nu Numele la DB)
        self.client_map = {} # { 'Ion Popescu': 100 }
        self.produs_map = {} # { 'RTX 4090': 500 }

        # --- 1. Titlu ---
        lbl_titlu = tk.Label(root, text="Procesare Comandă Nouă", font=("Arial", 16, "bold"))
        lbl_titlu.pack(pady=20)

        # --- 2. Zona Formular (Grid) ---
        frame_form = tk.Frame(root)
        frame_form.pack(pady=10)

        # Selectare Client
        tk.Label(frame_form, text="Client:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.combo_client = ttk.Combobox(frame_form, width=30, state="readonly")
        self.combo_client.grid(row=0, column=1, padx=10, pady=5)

        # Selectare Produs
        tk.Label(frame_form, text="Produs:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.combo_produs = ttk.Combobox(frame_form, width=30, state="readonly")
        self.combo_produs.grid(row=1, column=1, padx=10, pady=5)

        # Cantitate
        tk.Label(frame_form, text="Cantitate:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_cantitate = tk.Entry(frame_form, width=10)
        self.ent_cantitate.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.ent_cantitate.insert(0, "1")

        # Metoda Livrare
        tk.Label(frame_form, text="Livrare:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.combo_livrare = ttk.Combobox(frame_form, width=30, state="readonly")
        self.combo_livrare['values'] = ('Curier Rapid', 'Ridicare Personala', 'Posta')
        self.combo_livrare.current(0)
        self.combo_livrare.grid(row=3, column=1, padx=10, pady=5)

        # --- 3. Buton Actionare ---
        btn_save = tk.Button(root, text="✅ FINALIZEAZĂ COMANDA", 
                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                             command=self.salveaza_comanda)
        btn_save.pack(pady=30, ipadx=10, ipady=5)

        # --- 4. Initializare Date ---
        self.populeaza_date()

    def get_db_connection(self):
        try:
            return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        except oracledb.Error as e:
            messagebox.showerror("Eroare Conexiune", f"Nu m-am putut conecta la Oracle:\n{e}")
            return None

    def populeaza_date(self):
        """Preia listele de clienti si produse din baza de date"""
        conn = self.get_db_connection()
        if not conn: return

        cursor = conn.cursor()
        
        try:
            # 1. Luam Clientii
            cursor.execute("SELECT client_id, nume FROM CLIENT")
            for row in cursor:
                c_id, c_nume = row
                self.client_map[c_nume] = c_id # Mapam Nume -> ID
            self.combo_client['values'] = list(self.client_map.keys())

            # 2. Luam Produsele (folosim Vederea pentru a vedea si stocul)
            # Nota: Trebuie sa stim ID-ul real, il luam din tabelul PRODUS sau V_OFFERTA_PRODUSE daca l-am pus acolo
            # Aici facem un join mic sau luam din produs direct pentru simplitate
            cursor.execute("SELECT produs_id, denumire FROM PRODUS")
            for row in cursor:
                p_id, p_nume = row
                self.produs_map[p_nume] = p_id
            self.combo_produs['values'] = list(self.produs_map.keys())
            
        except oracledb.Error as e:
            messagebox.showerror("Eroare Date", f"Nu am putut prelua datele:\n{e}")
        finally:
            cursor.close()
            conn.close()

    def salveaza_comanda(self):
        # 1. Validari simple
        nume_client = self.combo_client.get()
        nume_produs = self.combo_produs.get()
        str_cantitate = self.ent_cantitate.get()
        metoda_livrare = self.combo_livrare.get()

        if not all([nume_client, nume_produs, str_cantitate]):
            messagebox.showwarning("Atenție", "Toate câmpurile sunt obligatorii!")
            return

        try:
            cantitate = int(str_cantitate)
        except ValueError:
            messagebox.showerror("Eroare", "Cantitatea trebuie să fie un număr!")
            return

        # 2. Obtinem ID-urile din mapari
        id_client = self.client_map[nume_client]
        id_produs = self.produs_map[nume_produs]

        # 3. Apelam Procedura Stocata
        conn = self.get_db_connection()
        if not conn: return

        cursor = conn.cursor()
        try:
            # Apelul procedurii PL/SQL create anterior
            cursor.callproc("ADAUGA_COMANDA_COMPLETA", [id_client, id_produs, cantitate, metoda_livrare])
            
            # Daca nu da eroare, inseamna ca e OK
            messagebox.showinfo("Succes", "Comanda a fost înregistrată cu succes!\nStocul a fost actualizat.")
            
            # Resetam campurile
            self.ent_cantitate.delete(0, tk.END)
            self.ent_cantitate.insert(0, "1")

        except oracledb.Error as e:
            # Aici prindem erorile de logica (Ex: Stoc insuficient)
            error_obj = e.args[0]
            messagebox.showerror("Eroare Database", f"Tranzacția a eșuat:\n{error_obj.message}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieVanzari(root)
    root.mainloop()
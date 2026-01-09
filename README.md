# 🖥️ PC Parts Manager - Sistem Distribuit de Gestiune

![Status](https://img.shields.io/badge/Status-Work_in_Progress-yellow)
![Database](https://img.shields.io/badge/Oracle-Database_23c-red)
![Frontend](https://img.shields.io/badge/Python-Tkinter-blue)

**PC Parts Manager** este o aplicație software complexă de tip ERP (Enterprise Resource Planning) destinată gestionării unui lanț de magazine de componente IT. Sistemul este construit pe o arhitectură de **Bază de Date Distribuită**, simulând operarea în multiple puncte de lucru (București, Cluj-Napoca, Timișoara).

---

## 🚀 Funcționalități Cheie

### 1. Arhitectură Distribuită (BDD)
* **Fragmentare Orizontală:** Stocurile și comenzile sunt distribuite pe servere logice în funcție de locație (`depozit_id`).
* **Fragmentare Verticală:** Datele sensibile ale clienților (financiare) sunt separate de cele operaționale (vânzări).
* **Replicare:** Nomenclatoarele (Produse, Categorii) sunt replicate total pentru performanță maximă la interogare.

### 2. Roluri și Securitate
Aplicația implementează un sistem de autentificare securizat cu roluri distincte:
* **👨‍💼 Agent Vânzări:**
    * Procesare comenzi cu verificare stoc în timp real.
    * Vizualizare istoric vânzări proprii.
    * Calcul automat al prețului final (inclusiv discount-uri).
* **🛠️ Administrator:**
    * **Supply Chain:** Aprovizionare marfă (Intrări Stoc) folosind logica *Upsert* (Merge).
    * **Catalog:** Definire și adăugare produse noi.
    * **Logistică:** Monitorizare comenzi, schimbare status (`În Procesare` -> `Finalizată`) și **Generare Automată AWB**.
    * **Analytics:** Vizualizarea distribuției stocului pe orașe.

---

## 🛠️ Tehnologii Utilizate

* **Backend (Database):**
    * **Oracle Database** (PL/SQL).
    * Proceduri Stocate pentru logica tranzacțională (ACID).
    * Vederi (Views) pentru raportare.
    * Triggere și secvențe pentru auto-incrementare.
* **Frontend (GUI):**
    * **Python 3.x**
    * **Tkinter** (Interfață grafică modernă, responsive).
    * **ttk** (Widgets stilizate).
* **Conectivitate:**
    * Librăria `oracledb` (Thin Client).

---

## 📸 Capturi de Ecran (Screenshots)

### 1. Dashboard Administrator - Gestiune Comenzi & AWB
*Monitorizarea statusului comenzilor. Comenzile finalizate primesc automat un AWB unic.*
![Admin Dashboard](link_catre_poza_ta_cu_admin_comenzi.png)

### 2. Distribuția Stocului pe Orașe
*Vizualizarea stocului fragmentat pe depozitele din țară.*
![Distributie Stoc](link_catre_poza_ta_cu_popup_stoc.png)

### 3. Interfața Agent - Vânzare Rapidă
*Formular de vânzare cu feedback vizual pentru stoc critic.*
![Agent UI](link_catre_poza_ta_cu_agent_vanzare.png)

---

## ⚙️ Instalare și Rulare

### Cerințe Preliminare
* Python 3.10+
* Oracle Database (Local sau Cloud)
* Oracle Instant Client (opțional, depinde de setup)

### Pasul 1: Configurare Bază de Date
Rulează scripturile din folderul `/sql` în ordinea următoare folosind SQL Developer:
1.  `01_create_tables.sql` - Crearea structurii.
2.  `02_populate_data.sql` - Inserarea datelor de test.
3.  `03_procedures.sql` - Compilarea procedurilor stocate (`ADMIN_APROVIZIONARE`, `ADAUGA_COMANDA`, etc.).

### Pasul 2: Configurare Python
```bash
# Clonează repository-ul
git clone [https://github.com/userul-tau/pc-parts-manager.git](https://github.com/userul-tau/pc-parts-manager.git)

pip install oracledb

-- to be implemented

S-a implementat o varianta mai simpla, functionala, cu interfata pentru Admin si pentru Agentul de vanzari.
-- IMBUNATATIRI ( TO BE TESTED )
* De adaugat filtru pentru comenzile anulate
* Dezvoltare UI/UX - eventual extensie
* Evntuale idei pentru implementarea unei aplicatii stand alone pe pc? java?
* Dezvoltare idei pentru o aplicatie de mobil? Flutter/Android Studio?
* Populare DATABASE cu mai multe entry-uri [script python care ia datele dintr-un dataset si le insereaza in databse]
  

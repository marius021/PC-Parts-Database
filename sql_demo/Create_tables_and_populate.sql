-- In prima etapa, vom creea tabelele parinte 
-- CATEGORIE
CREATE TABLE CATEGORIE (
    categorie_id NUMBER PRIMARY KEY,
    nume VARCHAR(100) UNIQUE,
    descriere VARCHAR2(255)
);

-- PRODUCATOR
CREATE TABLE PRODUCATOR (
    producator_id NUMBER PRIMARY KEY,
    nume VARCHAR2(100),
    website VARCHAR2(100)
);

-- DEPOZIT
CREATE TABLE DEPOZIT (
    depozit_id NUMBER PRIMARY KEY,
    nume VARCHAR2(100),
    oras VARCHAR2(100),
    tara VARCHAR2(50)
);

--client
CREATE TABLE CLIENT ( 
    client_id NUMBER PRIMARY KEY,
    tip_client VARCHAR2(50),
    nume VARCHAR2(100),
    cnp_client VARCHAR(50),
    cod_fiscal VARCHAR2(50) UNIQUE,
    categorie_pret VARCHAR2(50)
);

--STANDARD
CREATE TABLE STANDARD (
    standard_id NUMBER PRIMARY KEY,
    cod VARCHAR2(50) UNIQUE,
    grup VARCHAR2(100),
    describe VARCHAR2(255)
);

-- creeam tabelele "child" cu FK

-- PRODUS (depinde de CATEGORIE, PRODUCATOR)
CREATE TABLE PRODUS (
    produs_id NUMBER PRIMARY KEY,
    nume VARCHAR2(255),
    cod_sku VARCHAR2(100) UNIQUE,
    descriere CLOB,
    categorie_id NUMBER REFERENCES CATEGORIE(categorie_id),
    producator_id NUMBER REFERENCES PRODUCATOR(producator_id),
    garantie_luni NUMBER,
    status VARCHAR2(50)
);
-- comanda_vanzare ( depinde de CLIENT )
CREATE TABLE COMANDA_VANZARE (
    cv_id NUMBER PRIMARY KEY,
    client_id NUMBER REFERENCES CLIENT(client_id),
    data_comanda DATE DEFAULT SYSDATE,
    status VARCHAR2(50),
    metoda_livrare VARCHAR2(100),
    adresa_livrare VARCHAR2(500)
);

-- STOC (depinde de PRODUS, DEPOZIT)
-- aceasta este o tabela asociativa cu cheie primara compusa

CREATE TABLE STOC (
    produs_id NUMBER REFERENCES PRODUS(produs_id),
    depozit_id NUMBER REFERENCES DEPOZIT(depozit_id),
    cantitate NUMBER,
    pret_minim NUMBER(10, 2),
    PRIMARY KEY (produs_id, depozit_id)
);

-- PRODUS_STANDARD ( depinde de PRODUS, STANDARD)
-- O alta tavela asociativa

CREATE TABLE PRODUS_STANDARD (
    produs_id NUMBER REFERENCES PRODUS(produs_id),
    standard_id NUMBER REFERENCES STANDARD(standard_id),
    mentiuni_leg VARCHAR2(255),
    PRIMARY KEY (produs_id, standard_id)
);

--RMA (Retur) (depinde de CLIENT, PRODUS)
CREATE TABLE RMA (
    rma_id NUMBER PRIMARY KEY,
    client_id NUMBER REFERENCES CLIENT(client_id),
    produs_id NUMBER REFERENCES PRODUS(produs_id),
    cv_id NUMBER, -- poate fi FK la COMANDA_VANZARE, de adaugat ulterior
    status VARCHAR2(50),
    data_solicitare DATE,
    data_rezolvare DATE
);

-- EXPEDIERE (depinde de COMANDA_VANZARE, DEPOZIT)
CREATE TABLE EXPEDIERE (
    expediere_id NUMBER PRIMARY KEY,
    cv_id NUMBER REFERENCES COMANDA_VANZARE(cv_id),
    depozit_id NUMBER REFERENCES DEPOZIT(depozit_id),
    awb VARCHAR2(100),
    curier VARCHAR2(100),
    data_expedierii DATE
);

-- CV_LINIE (Linii Comanda) (depinde de COMANDA_VANZARE, PRODUS)
CREATE TABLE CV_LINE (
    cv_id NUMBER REFERENCES COMANDA_VANZARE(cv_id),
    linie_nr NUMBER,
    produs_id NUMBER REFERENCES PRODUS(produs_id),
    cantitate NUMBER,
    pret_unitar NUMBER(10, 2),
    discount NUMBER(5, 2),
    PRIMARY KEY (cv_id, linie_nr) -- cheie primara compusa
);

-- Inserare Date Părinte
INSERT INTO CATEGORIE VALUES (1, 'Placi Video', 'GPU pentru gaming si workstation');
INSERT INTO PRODUCATOR VALUES (1, 'ASUS', 'asus.com');
INSERT INTO DEPOZIT VALUES (1, 'Depozit Bucuresti', 'Bucuresti', 'Romania');
INSERT INTO CLIENT VALUES (101, 'B2C', 'Ion Ionut', 'CNP122', 'Romania', 'Standard');

-- Inserare Produse
INSERT INTO PRODUS VALUES (500, 'RTX4090-OC', 'GeForce RTX 4090', 1, 1, 36, 'Activ');

-- Inserare Stoc si Comanda
INSERT INTO STOC VALUES (500, 1, 10, 2);
INSERT INTO COMANDA_VANZARE VALUES (1001, 100, SYSDATE, 'Noua', 'Curier Rapid');
INSERT INTO CV_LINIE VALUES (1001, 1, 500, 1, 9500, 0);


-- =============================================
-- 1. POPULARE CATEGORII (ID 10 -> 16)
-- =============================================

INSERT INTO CATEGORIE VALUES (10, 'Procesoare', 'CPU Intel si AMD pentru Desktop/Server');
INSERT INTO CATEGORIE VALUES (11, 'Placi de Baza', 'Format ATX, mATX, ITX');
INSERT INTO CATEGORIE VALUES (12, 'Memorii RAM', 'DDR4 si DDR5');
INSERT INTO CATEGORIE VALUES (13, 'Stocare SSD', 'NVMe M.2 si SATA');
INSERT INTO CATEGORIE VALUES (14, 'Surse', 'Alimentare PC certificare Gold/Platinum');
INSERT INTO CATEGORIE VALUES (15, 'Carcase', 'Tower, Mini Tower cu RGB');
INSERT INTO CATEGORIE VALUES (16, 'Periferice', 'Mouse, Tastaturi, Casti');

-- =============================================
-- 2. POPULARE PRODUCATORI (ID 10 -> 16)
-- =============================================
INSERT INTO PRODUCATOR VALUES (10, 'AMD', 'SUA', 'amd.com');
INSERT INTO PRODUCATOR VALUES (11, 'NVIDIA', 'SUA', 'nvidia.com');
INSERT INTO PRODUCATOR VALUES (12, 'Corsair', 'SUA', 'corsair.com');
INSERT INTO PRODUCATOR VALUES (13, 'Samsung', 'Coreea de Sud', 'samsung.com');
INSERT INTO PRODUCATOR VALUES (14, 'Seasonic', 'Taiwan', 'seasonic.com');
INSERT INTO PRODUCATOR VALUES (15, 'Logitech', 'Elvetia', 'logitech.com');
INSERT INTO PRODUCATOR VALUES (16, 'Gigabyte', 'Taiwan', 'gigabyte.com');

-- =============================================
-- 3. POPULARE CLIENTI (ID 101 -> 108)
-- =============================================
INSERT INTO CLIENT VALUES (101, 'B2C', 'Maria Ionescu', 'CNP2900101', 'Romania', 'Standard');
INSERT INTO CLIENT VALUES (102, 'B2B', 'SC Tech Solutions SRL', 'RO882233', 'Romania', 'VIP');
INSERT INTO CLIENT VALUES (103, 'B2C', 'Andrei Radu', 'CNP1890505', 'Romania', 'Standard');
INSERT INTO CLIENT VALUES (104, 'B2B', 'Cabinet Avocat Popa', 'RO991122', 'Romania', 'Business');
INSERT INTO CLIENT VALUES (105, 'B2C', 'Elena Dumitrescu', 'CNP2951212', 'Romania', 'Standard');
INSERT INTO CLIENT VALUES (106, 'B2B', 'IT Garage Services', 'RO445566', 'Romania', 'VIP');
INSERT INTO CLIENT VALUES (107, 'B2C', 'George Vasile', 'CNP1920303', 'Romania', 'Standard');
INSERT INTO CLIENT VALUES (108, 'B2C', 'Ana Stan', 'CNP2980808', 'Romania', 'Standard');

-- =============================================
-- 4. POPULARE DEPOZITE SUPLIMENTARE (ID 2, 3)
-- =============================================
-- Aveai deja ID 1 (Bucuresti). Adaugam Cluj si Timisoara.
INSERT INTO DEPOZIT VALUES (2, 'Depozit Cluj-Napoca', 'Cluj-Napoca', 'Romania');
INSERT INTO DEPOZIT VALUES (3, 'Depozit Timisoara', 'Timisoara', 'Romania');

-- =============================================
-- 5. POPULARE PRODUSE (ID 1000 -> 1009)
-- =============================================
-- Nota: Folosim ID-urile de Categorie si Producator create mai sus
-- Produs 1000: CPU AMD
INSERT INTO PRODUS VALUES (1000, 'RYZEN7-7800X3D', 'AMD Ryzen 7 7800X3D Gaming', 10, 10, 36, 'Activ');
-- Produs 1001: GPU Gigabyte
INSERT INTO PRODUS VALUES (1001, 'RTX4070-GIGA', 'Gigabyte GeForce RTX 4070 Windforce', 1, 16, 36, 'Activ');
-- Produs 1002: RAM Corsair
INSERT INTO PRODUS VALUES (1002, 'CMK32GX5M2B', 'Corsair Vengeance 32GB DDR5 6000MHz', 12, 12, 99, 'Activ');
-- Produs 1003: SSD Samsung
INSERT INTO PRODUS VALUES (1003, 'MZ-V8P1T0BW', 'Samsung 980 PRO 1TB NVMe M.2', 13, 13, 60, 'Activ');
-- Produs 1004: Sursa Seasonic
INSERT INTO PRODUS VALUES (1004, 'FOCUS-GX-850', 'Seasonic Focus GX, 80+ Gold, 850W', 14, 14, 120, 'Activ');
-- Produs 1005: Mouse Logitech
INSERT INTO PRODUS VALUES (1005, 'MX-MASTER-3S', 'Logitech MX Master 3S Performance', 16, 15, 24, 'Activ');
-- Produs 1006: Placa baza Gigabyte
INSERT INTO PRODUS VALUES (1006, 'Z790-AORUS', 'Gigabyte Z790 AORUS ELITE AX', 11, 16, 36, 'Activ');
-- Produs 1007: SSD Samsung 2TB
INSERT INTO PRODUS VALUES (1007, 'MZ-V8P2T0BW', 'Samsung 990 PRO 2TB NVMe', 13, 13, 60, 'Activ');
-- Produs 1008: CPU Intel (Presupunand ca aveai Intel la ID 1 in datele vechi, sau folosim Producator nou daca cream)
-- Folosim producator 1 (Intel) din datele tale vechi sau adaugam unul nou daca nu exista.
-- Punem pe cat 10 (Procesoare)
INSERT INTO PRODUS VALUES (1008, 'I5-13600K', 'Intel Core i5-13600K Raptor Lake', 10, 1, 36, 'Activ'); -- ID 1 (Intel) exista deja
-- Produs 1009: Carcasa Corsair
INSERT INTO PRODUS VALUES (1009, '4000D-AIR', 'Corsair 4000D Airflow Black', 15, 12, 24, 'Activ');


-- =============================================
-- 6. POPULARE STOCURI (Legatura Produs - Depozit)
-- =============================================
-- Este CRITIC să avem stocuri pentru ca aplicația Python să poată vinde produse.
-- Punem stocuri in Depozit 1 (Central) si cateva in Depozit 2 (Cluj)

-- Stocuri Depozit 1 (Bucuresti)
INSERT INTO STOC VALUES (1000, 1, 50, 2100.00);  -- Ryzen 7
INSERT INTO STOC VALUES (1001, 1, 20, 3200.00);  -- RTX 4070
INSERT INTO STOC VALUES (1002, 1, 100, 650.00);  -- RAM
INSERT INTO STOC VALUES (1003, 1, 80, 450.00);   -- SSD 1TB
INSERT INTO STOC VALUES (1004, 1, 30, 750.00);   -- Sursa
INSERT INTO STOC VALUES (1005, 1, 60, 550.00);   -- Mouse
INSERT INTO STOC VALUES (1006, 1, 15, 1400.00);  -- Placa baza
INSERT INTO STOC VALUES (1009, 1, 25, 500.00);   -- Carcasa

-- Stocuri Depozit 2 (Cluj) - Fragmentare Orizontala :)
INSERT INTO STOC VALUES (1000, 2, 10, 2150.00);  -- Ryzen la Cluj (pret usor diferit poate)
INSERT INTO STOC VALUES (1003, 2, 20, 460.00);   -- SSD la Cluj
INSERT INTO STOC VALUES (1005, 2, 15, 560.00);   -- Mouse la Cluj



COMMIT; -- Salvează datele



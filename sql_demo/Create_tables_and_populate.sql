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

COMMIT; -- Salvează datele

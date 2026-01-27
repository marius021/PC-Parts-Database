CREATE OR REPLACE VIEW pcparts.V_ISTORIC_SUMAR AS
SELECT 
    cv.cv_id,
    c.nume AS nume_client,
    cv.data_creare,
    cv.metoda_livrare,
    cv.status,
    -- Calculam suma totală a liniilor comenzii
    (SELECT SUM(l.cantitate * l.pret_unitar * (1 - l.discount/100)) 
     FROM pcparts.CV_LINIE l 
     WHERE l.cv_id = cv.cv_id) AS valoare_totala
FROM pcparts.COMANDA_VANZARE cv
JOIN pcparts.CLIENT c ON cv.client_id = c.client_id
ORDER BY cv.cv_id DESC;

-- 2. Dăm drepturi Agentului să vadă acest istoric
GRANT SELECT ON pcparts.V_ISTORIC_SUMAR TO AGENT_VANZARI;

-- 3. Creăm sinonimul public
CREATE OR REPLACE PUBLIC SYNONYM V_ISTORIC_SUMAR FOR pcparts.V_ISTORIC_SUMAR;


-- === IMPLEMENTARE INTERFATA ADMINISTRATOR ===

-- 1. Procedura de ADĂUGARE CLIENT
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_ADAUGA_CLIENT (
    p_tip IN VARCHAR2,
    p_nume IN VARCHAR2,
    p_cod_fiscal IN VARCHAR2,
    p_tara IN VARCHAR2,
    p_cat_pret IN VARCHAR2
) AS
    v_new_id NUMBER;
BEGIN
    SELECT NVL(MAX(client_id), 100) + 1 INTO v_new_id FROM pcparts.CLIENT;
    
    INSERT INTO pcparts.CLIENT (client_id, tip, nume, cod_fiscal, tara, categoria_pret)
    VALUES (v_new_id, p_tip, p_nume, p_cod_fiscal, p_tara, p_cat_pret);
    
    COMMIT;
END;
/

-- 2. Procedura de ȘTERGERE CLIENT
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_STERGE_CLIENT (
    p_client_id IN NUMBER
) AS
BEGIN
    DELETE FROM pcparts.CLIENT WHERE client_id = p_client_id;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        -- Eroarea ORA-02292 apare dacă clientul are comenzi (Foreign Key)
        RAISE_APPLICATION_ERROR(-20002, 'Nu se poate șterge: Clientul are comenzi active!');
END;
/

-- 3. Acordare Drepturi și Sinonime
GRANT EXECUTE ON pcparts.ADMIN_ADAUGA_CLIENT TO AGENT_VANZARI;
GRANT EXECUTE ON pcparts.ADMIN_STERGE_CLIENT TO AGENT_VANZARI;

-- Drepturi directe pentru a popula listele în Admin
GRANT SELECT ON pcparts.CLIENT TO AGENT_VANZARI; 

CREATE OR REPLACE PUBLIC SYNONYM ADMIN_ADAUGA_CLIENT FOR pcparts.ADMIN_ADAUGA_CLIENT;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_STERGE_CLIENT FOR pcparts.ADMIN_STERGE_CLIENT;

-- Adaugă prefixul "pcparts." pentru a fi siguri unde se creează
CREATE OR REPLACE PROCEDURE pcparts.ADAUGA_COMANDA_COMPLETA (
    p_client_id IN NUMBER,
    p_produs_id IN NUMBER,
    p_cantitate IN NUMBER,
    p_metoda_livrare IN VARCHAR2
) AS
    v_stoc_existent NUMBER;
    v_pret_unitar NUMBER;
    v_noul_cv_id NUMBER;
    e_stoc_insuficient EXCEPTION;
BEGIN
    -- 1. Verificăm Stocul
    SELECT cantitate, pret_minim INTO v_stoc_existent, v_pret_unitar
    FROM pcparts.STOC  -- Specificăm și aici pcparts pentru siguranță
    WHERE produs_id = p_produs_id AND depozit_id = 1; 

    IF v_stoc_existent < p_cantitate THEN
        RAISE e_stoc_insuficient;
    END IF;

    -- 2. Generăm ID nou
    SELECT NVL(MAX(cv_id), 202400) + 1 INTO v_noul_cv_id FROM pcparts.COMANDA_VANZARE;

    -- 3. Inserăm Comanda
    INSERT INTO pcparts.COMANDA_VANZARE (cv_id, client_id, data_creare, status, metoda_livrare)
    VALUES (v_noul_cv_id, p_client_id, SYSDATE, 'In Asteptare', p_metoda_livrare);

    -- 4. Inserăm Linia
    INSERT INTO pcparts.CV_LINIE (cv_id, linie_nr, produs_id, cantitate, pret_unitar, discount)
    VALUES (v_noul_cv_id, 1, p_produs_id, p_cantitate, v_pret_unitar, 0);

    -- 5. Actualizăm Stocul
    UPDATE pcparts.STOC 
    SET cantitate = cantitate - p_cantitate
    WHERE produs_id = p_produs_id AND depozit_id = 1;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Comanda ' || v_noul_cv_id || ' a fost creata cu succes!');

EXCEPTION
    WHEN e_stoc_insuficient THEN
        ROLLBACK;
        DBMS_OUTPUT.PUT_LINE('EROARE: Stoc insuficient!');
    WHEN OTHERS THEN
        ROLLBACK;
        DBMS_OUTPUT.PUT_LINE('EROARE TEHNICA: ' || SQLERRM);
END;
/

-- 1. Acum Oracle va găsi procedura în pcparts
GRANT EXECUTE ON pcparts.ADAUGA_COMANDA_COMPLETA TO AGENT_VANZARI;

-- 2. Refacem sinonimul public ca să fie sigur corect
DROP PUBLIC SYNONYM ADAUGA_COMANDA_COMPLETA; -- Doar dacă exista deja
CREATE PUBLIC SYNONYM ADAUGA_COMANDA_COMPLETA FOR pcparts.ADAUGA_COMANDA_COMPLETA;

-- =============== IMPLEMENTARE Discount(%) si campuri Read-Only ==================

CREATE OR REPLACE PROCEDURE pcparts.ADAUGA_COMANDA_COMPLETA (
    p_client_id IN NUMBER,        -- Atenție la virgula de aici
    p_produs_id IN NUMBER,        -- Și aici
    p_cantitate IN NUMBER,        -- Și aici
    p_metoda_livrare IN VARCHAR2, -- Și aici
    p_discount IN NUMBER          -- Aici NU se pune virgulă (e ultimul)
) AS
    v_stoc_existent NUMBER;
    v_pret_unitar NUMBER;
    v_noul_cv_id NUMBER;
    e_stoc_insuficient EXCEPTION;
BEGIN
    -- 1. Verificăm Stocul și Prețul
    -- Folosim alias 's' pentru tabelul STOC ca să fie clar
    SELECT s.cantitate, s.pret_minim INTO v_stoc_existent, v_pret_unitar
    FROM pcparts.STOC s
    WHERE s.produs_id = p_produs_id AND s.depozit_id = 1;

    -- Validare stoc
    IF v_stoc_existent < p_cantitate THEN
        RAISE e_stoc_insuficient;
    END IF;

    -- 2. Generăm ID nou pentru comandă
    SELECT NVL(MAX(cv_id), 202400) + 1 INTO v_noul_cv_id FROM pcparts.COMANDA_VANZARE;

    -- 3. Inserăm Comanda (Header)
    INSERT INTO pcparts.COMANDA_VANZARE (cv_id, client_id, data_creare, status, metoda_livrare)
    VALUES (v_noul_cv_id, p_client_id, SYSDATE, 'In Asteptare', p_metoda_livrare);

    -- 4. Inserăm Linia Comenzii (Detaliile)
    -- Aici folosim parametrii p_produs_id și p_discount
    INSERT INTO pcparts.CV_LINIE (cv_id, linie_nr, produs_id, cantitate, pret_unitar, discount)
    VALUES (v_noul_cv_id, 1, p_produs_id, p_cantitate, v_pret_unitar, p_discount);

    -- 5. Actualizăm Stocul
    UPDATE pcparts.STOC 
    SET cantitate = cantitate - p_cantitate
    WHERE produs_id = p_produs_id AND depozit_id = 1;

    -- Confirmăm totul
    COMMIT;
    
    DBMS_OUTPUT.PUT_LINE('Comanda ' || v_noul_cv_id || ' a fost creata cu succes!');

EXCEPTION
    WHEN e_stoc_insuficient THEN
        ROLLBACK;
        -- Aruncăm o eroare care poate fi prinsă de Python (cod 20001)
        RAISE_APPLICATION_ERROR(-20001, 'Stoc insuficient! Disponibil: ' || v_stoc_existent);
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE; -- Trimitem eroarea mai departe către Python
END;
/

GRANT EXECUTE ON pcparts.ADAUGA_COMANDA_COMPLETA TO AGENT_VANZARI;



-- ====== IMPLEMENTARE ISTORIC COMENZI ====================


-- 1. Creăm o vedere care calculează TOTALUL per comandă
CREATE OR REPLACE VIEW pcparts.V_ISTORIC_SUMAR AS
SELECT 
    cv.cv_id,
    c.nume AS nume_client,
    cv.data_creare,
    cv.metoda_livrare,
    cv.status,
    -- Calculam suma totală a liniilor comenzii
    (SELECT SUM(l.cantitate * l.pret_unitar * (1 - l.discount/100)) 
     FROM pcparts.CV_LINIE l 
     WHERE l.cv_id = cv.cv_id) AS valoare_totala
FROM pcparts.COMANDA_VANZARE cv
JOIN pcparts.CLIENT c ON cv.client_id = c.client_id
ORDER BY cv.cv_id DESC;

-- 2. Dăm drepturi Agentului să vadă acest istoric
GRANT SELECT ON pcparts.V_ISTORIC_SUMAR TO AGENT_VANZARI;

-- 3. Creăm sinonimul public
CREATE OR REPLACE PUBLIC SYNONYM V_ISTORIC_SUMAR FOR pcparts.V_ISTORIC_SUMAR;


-- === IMPLEMENTARE INTERFATA ADMINISTRATOR ===

-- 1. Procedura de ADĂUGARE CLIENT
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_ADAUGA_CLIENT (
    p_tip IN VARCHAR2,
    p_nume IN VARCHAR2,
    p_cod_fiscal IN VARCHAR2,
    p_tara IN VARCHAR2,
    p_cat_pret IN VARCHAR2
) AS
    v_new_id NUMBER;
BEGIN
    SELECT NVL(MAX(client_id), 100) + 1 INTO v_new_id FROM pcparts.CLIENT;
    
    INSERT INTO pcparts.CLIENT (client_id, tip, nume, cod_fiscal, tara, categoria_pret)
    VALUES (v_new_id, p_tip, p_nume, p_cod_fiscal, p_tara, p_cat_pret);
    
    COMMIT;
END;
/

-- 2. Procedura de ȘTERGERE CLIENT
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_STERGE_CLIENT (
    p_client_id IN NUMBER
) AS
BEGIN
    DELETE FROM pcparts.CLIENT WHERE client_id = p_client_id;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        -- Eroarea ORA-02292 apare dacă clientul are comenzi (Foreign Key)
        RAISE_APPLICATION_ERROR(-20002, 'Nu se poate șterge: Clientul are comenzi active!');
END;
/

-- 3. Acordare Drepturi și Sinonime
GRANT EXECUTE ON pcparts.ADMIN_ADAUGA_CLIENT TO AGENT_VANZARI;
GRANT EXECUTE ON pcparts.ADMIN_STERGE_CLIENT TO AGENT_VANZARI;

-- Drepturi directe pentru a popula listele în Admin
GRANT SELECT ON pcparts.CLIENT TO AGENT_VANZARI; 

CREATE OR REPLACE PUBLIC SYNONYM ADMIN_ADAUGA_CLIENT FOR pcparts.ADMIN_ADAUGA_CLIENT;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_STERGE_CLIENT FOR pcparts.ADMIN_STERGE_CLIENT;

-- === IMPLEMENTARE ADAUGARE PRODUS DE CATRE ADMIN ===

CREATE OR REPLACE PROCEDURE pcparts.ADMIN_ADAUGA_PRODUS_NOU(
    p_nume IN VARCHAR2,
    p_sku IN VARCHAR2,
    p_categorie_id IN NUMBER,
    p_producator_id IN NUMBER,
    p_garantie IN NUMBER,
    p_pret_initial IN NUMBER
) AS
    v_new_id NUMBER;
 BEGIN
    -- 1. Generam ID nou pentru Produs
    SELECT NVL(MAX(produs_id), 1000) + 1 INTO v_new_id FROM pcparts.PRODUS;
    
 -- 2. Inserăm în tabelul PRODUS
    INSERT INTO pcparts.PRODUS (produs_id, cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
    VALUES (v_new_id, p_sku, p_nume, p_categorie_id, p_producator_id, p_garantie, 'Activ');
    
    -- 3. Inițializăm stocul (0 bucăți) în Depozitul Central (1), ca să aibă un preț
    INSERT INTO pcparts.STOC (produs_id, depozit_id, cantitate, pret_minim)
    VALUES (v_new_id, 1, 0, p_pret_initial);
    
    COMMIT;
END;
/

-- Acordăm drepturi
GRANT EXECUTE ON pcparts.ADMIN_ADAUGA_PRODUS_NOU TO AGENT_VANZARI;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_ADAUGA_PRODUS_NOU FOR pcparts.ADMIN_ADAUGA_PRODUS_NOU;

-- Avem nevoie să citim categoriile și producătorii pentru dropdown-uri
GRANT SELECT ON pcparts.CATEGORIE TO AGENT_VANZARI;
GRANT SELECT ON pcparts.PRODUCATOR TO AGENT_VANZARI;
CREATE OR REPLACE PUBLIC SYNONYM CATEGORIE FOR pcparts.CATEGORIE;
CREATE OR REPLACE PUBLIC SYNONYM PRODUCATOR FOR pcparts.PRODUCATOR;

-- === IMPLEMENTARE PROCEDURA DE ACTUALIZARE STATUS ===

CREATE OR REPLACE PROCEDURE pcparts.ADMIN_UPDATE_STATUS_COMANDA (
    p_cv_id IN NUMBER,
    p_status_nou IN VARCHAR2
) AS
BEGIN
    UPDATE pcparts.COMANDA_VANZARE
    SET status = p_status_nou
    WHERE cv_id = p_cv_id;
    
    COMMIT;
END;
/

-- Acordare drepturi
GRANT EXECUTE ON pcparts.ADMIN_UPDATE_STATUS_COMANDA TO AGENT_VANZARI;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_UPDATE_STATUS_COMANDA FOR pcparts.ADMIN_UPDATE_STATUS_COMANDA;

-- Ne asiguram ca vederea V_ISTORIC_SUMAR include si statusul ( am creat anterior, se verifica)
CREATE OR REPLACE VIEW pcparts.V_ISTORIC_SUMAR AS
SELECT
    cv.cv_id,
    c.nume AS nume_client,
    cv.data_creare,
    cv.metoda_livrare,
    cv.status,
    (SELECT SUM(l.cantitate * l.pret_unitar * (1 - l.discount/100))
     FROM pcparts.CV_LINIE l
     WHERE l.cv_id = cv.cv_id) AS valoare_totala
FROM pcparts.COMANDA_VANZARE cv
JOIN pcparts.CLIENT c ON cv.client_id = c.client_id
ORDER BY cv.cv_id DESC;

-- Refresh drepturi pe vedere
GRANT SELECT ON pcparts.V_ISTORIC_SUMAR TO AGENT_VANZARI;


-- === PROCEDURA "SMART" DE APROVIZIONARE
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_APROVIZIONARE (
    p_produs_id IN NUMBER,
    p_depozit_id IN NUMBER,
    p_cantitate IN NUMBER
) AS
    v_pret_existent NUMBER;
BEGIN
    -- Cautăm un preț existent pentru acest produs (ca să nu punem preț 0 dacă e depozit nou)
    -- Luăm prețul din orice alt depozit (ex: București)
    BEGIN
        SELECT pret_minim INTO v_pret_existent
        FROM pcparts.STOC WHERE produs_id = p_produs_id AND ROWNUM = 1;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN v_pret_existent := 0;
    END;
    
    -- MERGE: Update sau Insert intr-o singura comanda
    MERGE INTO pcparts.STOC s
    USING DUAL ON (s.produs_id = p_produs_id AND s.depozit_id = p_depozit_id)
    WHEN MATCHED THEN
        UPDATE SET s.cantitate = s.cantitate + p_cantitate
    WHEN NOT MATCHED THEN
        INSERT (produs_id, depozit_id, cantitate, pret_minim)
        VALUES (p_produs_id, p_depozit_id, p_cantitate, v_pret_existent);
        
    COMMIT;
END;
/

-- Acordare Drepturi
GRANT EXECUTE ON pcparts.ADMIN_APROVIZIONARE TO AGENT_VANZARI;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_APROVIZIONARE FOR pcparts.ADMIN_APROVIZIONARE;

-- IMPLEMENTARE LOGICA PENTRU AWB
-- 1. Adăugăm coloana AWB în tabelul de comenzi (dacă nu există deja)
ALTER TABLE pcparts.COMANDA_VANZARE ADD awb VARCHAR2(50);

-- 2. Actualizăm Vederea (View) pentru a include și coloana AWB
CREATE OR REPLACE VIEW pcparts.V_ISTORIC_SUMAR AS
SELECT 
    cv.cv_id,
    c.nume AS nume_client,
    cv.data_creare,
    cv.metoda_livrare,
    cv.status,
    cv.awb,  -- Am adăugat coloana AWB
    (SELECT SUM(l.cantitate * l.pret_unitar * (1 - l.discount/100)) 
     FROM pcparts.CV_LINIE l 
     WHERE l.cv_id = cv.cv_id) AS valoare_totala
FROM pcparts.COMANDA_VANZARE cv
JOIN pcparts.CLIENT c ON cv.client_id = c.client_id
ORDER BY cv.cv_id DESC;

-- 3. Modificăm Procedura de Status pentru a Genera AWB-ul automat
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_UPDATE_STATUS_COMANDA (
    p_cv_id IN NUMBER,
    p_status_nou IN VARCHAR2
) AS
    v_livrare VARCHAR2(100);
    v_awb_nou VARCHAR2(50);
BEGIN
    -- Aflăm metoda de livrare pentru comanda respectivă
    SELECT metoda_livrare INTO v_livrare 
    FROM pcparts.COMANDA_VANZARE WHERE cv_id = p_cv_id;

    -- Dacă statusul devine 'Finalizata' și NU e ridicare personală, generăm AWB
    IF p_status_nou = 'Finalizata' AND v_livrare != 'Ridicare Personala' THEN
        -- Generăm un AWB random format din: RO + Anul curent + 6 cifre aleatoare
        -- Exemplu: RO2025884921
        v_awb_nou := 'RO' || TO_CHAR(SYSDATE, 'YYYY') || TRUNC(DBMS_RANDOM.VALUE(100000, 999999));
        
        UPDATE pcparts.COMANDA_VANZARE
        SET status = p_status_nou, awb = v_awb_nou
        WHERE cv_id = p_cv_id;
    ELSE
        -- Dacă e ridicare personală sau alt status, doar actualizăm statusul (fără AWB)
        UPDATE pcparts.COMANDA_VANZARE
        SET status = p_status_nou
        WHERE cv_id = p_cv_id;
    END IF;
    
    COMMIT;
END;
/

-- QUICK FIX AWB
--Există deja un AWB generat pentru comanda asta?".
    --Dacă DA -> Păstrează-l pe cel vechi.
    --Dacă NU (e NULL) -> Generează unul nou.

    CREATE OR REPLACE PROCEDURE pcparts.ADMIN_UPDATE_STATUS_COMANDA (
    p_cv_id IN NUMBER,
    P_status_nou IN VARCHAR2
) AS
v_livrare VARCHAR2(100);
    v_awb_existent VARCHAR2(50); -- Variabilă pentru a ține minte AWB-ul actual
    v_awb_nou VARCHAR2(50);
BEGIN
    -- 1. Citim Metoda de livrare ȘI AWB-ul existent
    SELECT metoda_livrare, awb INTO v_livrare, v_awb_existent
    FROM pcparts.COMANDA_VANZARE 
    WHERE cv_id = p_cv_id;

    -- 2. Logica de generare
    IF p_status_nou = 'Finalizata' AND v_livrare != 'Ridicare Personala' THEN
        
        -- VERIFICAREA CHEIE: Generăm doar dacă NU există deja unul!
        IF v_awb_existent IS NULL THEN
            -- Generare AWB Nou
            v_awb_nou := 'RO' || TO_CHAR(SYSDATE, 'YYYY') || TRUNC(DBMS_RANDOM.VALUE(100000, 999999));
            
            UPDATE pcparts.COMANDA_VANZARE
            SET status = p_status_nou, awb = v_awb_nou
            WHERE cv_id = p_cv_id;
        ELSE
            -- Dacă există deja AWB, actualizăm doar statusul, lăsăm AWB-ul vechi
            UPDATE pcparts.COMANDA_VANZARE
            SET status = p_status_nou
            WHERE cv_id = p_cv_id;
        END IF;

    ELSE
        -- Pentru orice alt status sau Ridicare Personală, doar actualizăm statusul
        UPDATE pcparts.COMANDA_VANZARE
        SET status = p_status_nou
        WHERE cv_id = p_cv_id;
    END IF;
    
    COMMIT;
END;
/

-- implementare logica sql pentru sistemul de audit (logs)

-- 1. Crearea tabelului de Audit
CREATE TABLE pcparts.AUDIT_LOG (
    audit_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    nume_utilizator VARCHAR2(50),
    tip_actiune VARCHAR2(20),  -- INSERT, UPDATE, DELETE
    tabela_afectata VARCHAR2(30),
    detalii VARCHAR2(400),  -- CE S-A MODIFICAT ( PRET VECHI -> PRET NOU)
    data_actiune DATE DEFAULT SYSDATE
);

-- 2. Crearea Trigger-ului pentru monitorizare STOC (Pret si Cantitate)
CREATE OR REPLACE TRIGGER pcparts.TRG_AUDIT_STOC
AFTER UPDATE OF pret_minim, cantitate ON pcparts.STOC
FOR EACH ROW
DECLARE
    v_user VARCHAR2(50);
    v_produs VARCHAR2(100);
BEGIN
    --AFLAM cine face modificarea ( in cazul nostru, userul conectat la DB)
    SELECT USER INTO v_user FROM DUAL;
    
    --aflam numele produsului pentru claritate
    SELECT denumire INTO v_produs FROM pcparts.PRODUS WHERE produs_id = :OLD.produs_id;
    
    -- Cazul 1: Modificare Preț
    IF :OLD.pret_minim != :NEW.pret_minim THEN
        INSERT INTO pcparts.AUDIT_LOG (nume_utilizator, tip_actiune, tabela_afectata, detalii)
        VALUES (v_user, 'UPDATE PRET', 'STOC', 
                'Produs: ' || v_produs || ' | Pret vechi: ' || :OLD.pret_minim || ' -> Pret nou: ' || :NEW.pret_minim);
    END IF;

    -- Cazul 2: Modificare Cantitate (Intrare/Iesire stoc)
    IF :OLD.cantitate != :NEW.cantitate THEN
        INSERT INTO pcparts.AUDIT_LOG (nume_utilizator, tip_actiune, tabela_afectata, detalii)
        VALUES (v_user, 'UPDATE STOC', 'STOC', 
                'Produs: ' || v_produs || ' | Cantitate veche: ' || :OLD.cantitate || ' -> Cantitate noua: ' || :NEW.cantitate);
    END IF;
END;
/

-- 3. Acordare drepturi
GRANT SELECT ON pcparts.AUDIT_LOG TO AGENT_VANZARI;

-- Implementare logica pentur RMA 

-- 1. Ștergem tabelul vechi și constrângerile lui
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE pcparts.RMA CASCADE CONSTRAINTS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF; -- Ignorăm eroarea dacă tabelul nu există
END;
/

-- 2. Re-creăm tabelul RMA cu structura corectă (inclusiv data_deschidere)
CREATE TABLE pcparts.RMA (
    rma_id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    cv_id NUMBER REFERENCES pcparts.COMANDA_VANZARE(cv_id),
    produs_id NUMBER REFERENCES pcparts.PRODUS(produs_id),
    motiv VARCHAR2(200),
    status VARCHAR2(20) DEFAULT 'Deschis', -- Deschis, Aprobat, Respins
    data_deschidere DATE DEFAULT SYSDATE,
    data_rezolvare DATE
);

-- 3. Re-compilăm procedura (acum va găsi coloana data_deschidere)
CREATE OR REPLACE PROCEDURE pcparts.ADMIN_CREAZA_RMA (
    p_cv_id IN NUMBER,
    p_produs_id IN NUMBER,
    p_motiv IN VARCHAR2
) IS
BEGIN
    INSERT INTO pcparts.RMA (cv_id, produs_id, motiv, status, data_deschidere)
    VALUES (p_cv_id, p_produs_id, p_motiv, 'Deschis', SYSDATE);
    COMMIT;
END;
/

-- 4. Re-creăm vederea (View)
CREATE OR REPLACE VIEW pcparts.V_RMA_LIST AS
SELECT 
    r.rma_id,
    r.cv_id,
    p.denumire AS produs,
    c.nume AS client,
    r.motiv,
    r.status,
    r.data_deschidere
FROM pcparts.RMA r
JOIN pcparts.COMANDA_VANZARE cv ON r.cv_id = cv.cv_id
JOIN pcparts.CLIENT c ON cv.client_id = c.client_id
JOIN pcparts.PRODUS p ON r.produs_id = p.produs_id
ORDER BY r.rma_id DESC;

-- 5. Refacem drepturile și sinonimele
GRANT SELECT ON pcparts.V_RMA_LIST TO AGENT_VANZARI;
GRANT EXECUTE ON pcparts.ADMIN_CREAZA_RMA TO AGENT_VANZARI;

CREATE OR REPLACE PUBLIC SYNONYM V_RMA_LIST FOR pcparts.V_RMA_LIST;
CREATE OR REPLACE PUBLIC SYNONYM ADMIN_CREAZA_RMA FOR pcparts.ADMIN_CREAZA_RMA;

-- Verificare finală
SELECT * FROM V_RMA_LIST;
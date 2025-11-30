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

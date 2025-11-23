-- 1. crearea utilizatorului
CREATE USER AGENT_VANZARI IDENTIFIED BY parolaagent123;
GRANT CREATE SESSION TO AGENT_VANZARI;
GRANT UNLIMITED TABLESPACE TO AGENT_VANZARI;
GRANT UPDATE ON STOC TO AGENT_VANZARI;
COMMIT;


-- Creăm SINONIMELE CORECTE (care arată spre pcparts)
CREATE PUBLIC SYNONYM CATEGORIE FOR pcparts.CATEGORIE;
CREATE PUBLIC SYNONYM PRODUCATOR FOR pcparts.PRODUCATOR;
CREATE PUBLIC SYNONYM DEPOZIT FOR pcparts.DEPOZIT;
CREATE PUBLIC SYNONYM CLIENT FOR pcparts.CLIENT;
CREATE PUBLIC SYNONYM STANDARD FOR pcparts.STANDARD;
CREATE PUBLIC SYNONYM PRODUS FOR pcparts.PRODUS;
CREATE PUBLIC SYNONYM STOC FOR pcparts.STOC;
CREATE PUBLIC SYNONYM PRODUS_STANDARD FOR pcparts.PRODUS_STANDARD;
CREATE PUBLIC SYNONYM COMANDA_VANZARE FOR pcparts.COMANDA_VANZARE;
CREATE PUBLIC SYNONYM CV_LINIE FOR pcparts.CV_LINIE;
CREATE PUBLIC SYNONYM EXPEDIERE FOR pcparts.EXPEDIERE;
CREATE PUBLIC SYNONYM RMA FOR pcparts.RMA;
CREATE PUBLIC SYNONYM V_OFFERTA_PRODUSE FOR pcparts.V_OFFERTA_PRODUSE;
CREATE PUBLIC SYNONYM V_COMENZI_CLIENTI FOR pcparts.V_COMENZI_CLIENTI;

-- procedura ADAUGA_COMANDA_COMPLETA

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
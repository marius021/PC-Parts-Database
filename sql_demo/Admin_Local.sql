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
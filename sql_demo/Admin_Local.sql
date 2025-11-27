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
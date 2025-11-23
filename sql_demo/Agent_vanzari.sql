-- == SIMULARE TRANZACTIE: COMANDA NOUA ==

-- 1. identificam clientul ( aplicatia ar face asta automat in backend )
-- presupunem ca agentul a selectat clientul cu ID 100
DEFINE v_client_id = 100;

-- 2. Cream antetul comenzii ( INSERT in COMANDA_VANZARE)
-- se genereaaza un id nou ( in practica se folosesc secvente, aici punem manual un id: 202401)
INSERT INTO COMANDA_VANZARE (cv_id, client_id, data_creare, status, metoda_livrare)
VALUES (202401, &v_client_id, SYSDATE, 'In Asteptare', 'Ridicare Personala');

-- 3. Adaugam linia de comanda ( Produsul 500, Cantitate 2 )
-- agentul alege produsul 500
INSERT INTO CV_LINIE ( cv_id, linie_nr, produs_id, cantitate, pret_unitar, discount)
VALUES (202401, 1, 500, 2, 9500, 0);

-- 4. ACTUALIZARE STOC (PAS CRITIC!)
-- in momentul in care se vinde un produs, stocul trebuie sa scada
UPDATE STOC
SET cantitate = cantitate - 2
WHERE produs_id = 500 AND depozit_id = 1; -- presupunem depozitul 1

-- 5. Validare finala
COMMIT;


-- === VERIFICARE REZULTAT ===
PROMPT Situatia dupa comanda:
SELECT * FROM COMANDA_VANZARE WHERE cv_id = 202401;
SELECT * FROM CV_LINIE WHERE cv_id = 202401;
SELECT produs_id, cantitate AS stoc_ramas FROM STOC WHERE produs_id = 500;


SET SERVEROUTPUT ON;
BEGIN
    ADAUGA_COMANDA_COMPLETA(100, 500, 2, 'Curier Rapid');
END;
/

SELECT * FROM STOC;
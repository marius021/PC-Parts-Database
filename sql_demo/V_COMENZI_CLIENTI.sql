CREATE OR REPLACE VIEW V_COMENZI_CLIENTI AS
SELECT
    cv.cv_id AS numar_comanda,
    cl.nume AS nume_client,
    cl.tip AS tip_client,
    cv.data_creare,
    cv.status,
    cv.metoda_livrare
FROM COMANDA_VANZARE cv
JOIN CLIENT cl ON cv.client_id = cl.client_id;

-- VERIFICAM vederile

-- afisam catalogul simplificat
SELECT * FROM v_oferta_produse;

-- afisam comenzile intr-un format citibil
SELECT * FROM v_comenzi_clienti;
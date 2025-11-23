CREATE OR REPLACE VIEW V_OFERTA_PRODUSE AS
SELECT 
    p.cod_sku,
    p.denumire AS produs,
    c.nume AS categorie,
    pr.nume AS producator, 
    p.garantie_luni,
    p.status
FROM PRODUS p
JOIN CATEGORIE c ON p.categorie_id = c.categorie_id
JOIN PRODUCATOR pr ON p.producator_id = pr.producator_id;
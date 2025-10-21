SET DEFINE OFF;
SET SQLBLANKLINES ON;

-- 1) Stoc critic (dacă nu l-ai creat deja în verify_data.sql)
CREATE OR REPLACE VIEW vw_stoc_critic AS
SELECT p.denumire, d.nume AS depozit, s.cantitate, s.prag_minim
FROM STOC s
JOIN PRODUS p  ON p.produs_id = s.produs_id
JOIN DEPOZIT d ON d.depozit_id = s.depozit_id
WHERE s.cantitate < s.prag_minim;

-- 2) Standardele agregate pe produs (utile la listări)
CREATE OR REPLACE VIEW vw_produs_standarde AS
SELECT p.produs_id, p.cod_sku, p.denumire,
       LISTAGG(s.grup||':'||s.cod, ', ') WITHIN GROUP (ORDER BY s.grup, s.cod) AS standarde
FROM PRODUS p
LEFT JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
LEFT JOIN STANDARD s ON s.standard_id = ps.standard_id
GROUP BY p.produs_id, p.cod_sku, p.denumire;

-- 3) Sumă stoc pe categorie
CREATE OR REPLACE VIEW vw_stoc_pe_categorie AS
SELECT c.nume AS categorie, SUM(s.cantitate) AS total_cantitate
FROM STOC s
JOIN PRODUS p ON p.produs_id = s.produs_id
JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
GROUP BY c.nume;

COMMIT;

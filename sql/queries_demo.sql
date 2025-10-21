SET DEFINE OFF;
SET SQLBLANKLINES ON;

PROMPT === Overview ===
-- Produse pe categorie
SELECT c.nume AS categorie, COUNT(*) AS produse
FROM PRODUS p JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
GROUP BY c.nume ORDER BY produse DESC;

-- Grupuri de standarde și câte valori are fiecare
SELECT TRIM(grup) AS grup, COUNT(*) nr_standard
FROM STANDARD
GROUP BY TRIM(grup)
ORDER BY 1;

-- Câte legături există pe fiecare grup
SELECT TRIM(s.grup) AS grup, COUNT(*) nr_legaturi
FROM PRODUS_STANDARD ps
JOIN STANDARD s ON s.standard_id = ps.standard_id
GROUP BY TRIM(s.grup)
ORDER BY 1;

PROMPT === Compatibilitate ===
-- 1) Toate plăcile compatibile cu un CPU dat (după SKU CPU) via SOCKET_CPU
--    Înlocuiește :cpu_sku cu SKU-ul tău (ex. 'AMD-R5-7600')
WITH cpu_socket AS (
  SELECT s.cod AS socket
  FROM PRODUS p
  JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
  JOIN STANDARD s ON s.standard_id = ps.standard_id
  JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
  WHERE p.cod_sku = 'AMD-R5-7600'  -- <- schimbă aici rapid dacă vrei
    AND UPPER(s.grup) = 'SOCKET_CPU'
)
SELECT p.cod_sku, p.denumire
FROM PRODUS p
JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
JOIN STANDARD s ON s.standard_id = ps.standard_id
WHERE UPPER(c.nume) IN ('MOTHERBOARD','MOBO','MAINBOARD')
  AND UPPER(s.grup) = 'SOCKET_CPU'
  AND UPPER(s.cod) IN (SELECT UPPER(socket) FROM cpu_socket)
ORDER BY p.denumire;

-- 2) RAM compatibil cu o placă (plăcile au MEM_TYPE, găsim RAM cu același tip)
--    Schimbă SKU-ul plăcii la nevoie (ex. 'ASUS-B650-PLUS')
WITH board_mem AS (
  SELECT s.cod AS mem_type
  FROM PRODUS p
  JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
  JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
  JOIN STANDARD s ON s.standard_id = ps.standard_id
  WHERE p.cod_sku = 'ASUS-B650-PLUS'
    AND UPPER(s.grup) = 'MEM_TYPE'
)
SELECT p.cod_sku, p.denumire
FROM PRODUS p
JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
JOIN STANDARD s ON s.standard_id = ps.standard_id
WHERE UPPER(c.nume) = 'RAM'
  AND UPPER(s.grup) = 'MEM_TYPE'
  AND UPPER(s.cod) IN (SELECT UPPER(mem_type) FROM board_mem);

-- 3) Carcase compatibile cu o placă (FORM_FACTOR_MB)
WITH board_ff AS (
  SELECT s.cod AS ff
  FROM PRODUS p
  JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
  JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
  JOIN STANDARD s ON s.standard_id = ps.standard_id
  WHERE p.cod_sku = 'ASUS-B650-PLUS'
    AND UPPER(s.grup) = 'FORM_FACTOR_MB'
)
SELECT p.cod_sku, p.denumire
FROM PRODUS p
JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
JOIN STANDARD s ON s.standard_id = ps.standard_id
WHERE UPPER(c.nume) = 'CASE'
  AND UPPER(s.grup) = 'FORM_FACTOR_MB'
  AND UPPER(s.cod) IN (SELECT UPPER(ff) FROM board_ff);

PROMPT === Stoc & rapoarte ===
-- Top stoc pe categorie
SELECT * FROM vw_stoc_pe_categorie ORDER BY total_cantitate DESC;

-- Stoc critic
SELECT * FROM vw_stoc_critic;

-- Produse fără înregistrări de stoc
SELECT p.cod_sku, p.denumire
FROM PRODUS p
WHERE NOT EXISTS (SELECT 1 FROM STOC s WHERE s.produs_id = p.produs_id);

PROMPT === Calitate date ===
-- SKU duplicate (ar trebui 0)
SELECT cod_sku, COUNT(*) cnt
FROM PRODUS
GROUP BY cod_sku
HAVING COUNT(*) > 1;

-- Produse fără standarde mapate (ideal cât mai puține)
SELECT COUNT(*) AS produse_fara_standard
FROM PRODUS p
WHERE NOT EXISTS (SELECT 1 FROM PRODUS_STANDARD ps WHERE ps.produs_id = p.produs_id);

-- Distribuție standarde pe categorii (socket exemplu)
SELECT c.nume AS categorie, s.cod AS socket, COUNT(*) nr
FROM PRODUS p
JOIN CATEGORIE c ON c.categorie_id = p.categorie_id
JOIN PRODUS_STANDARD ps ON ps.produs_id = p.produs_id
JOIN STANDARD s ON s.standard_id = ps.standard_id
WHERE s.grup = 'SOCKET_CPU'
GROUP BY c.nume, s.cod
ORDER BY c.nume, s.cod;

PROMPT === Mini-CRUD (SQL-only) ===
-- Inserare produs nou + legare la standarde fără ID-uri manuale
-- (Exemplu: un RAM DDR5)
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('KINGSTON-D5-32', 'Kingston Fury 32GB DDR5 (2x16)',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='RAM'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Kingston'),
  36,'ACTIV');

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5'
WHERE p.cod_sku='KINGSTON-D5-32';

-- Actualizare/creare stoc pentru produsul nou
INSERT INTO STOC (produs_id, depozit_id, cantitate, prag_minim)
SELECT p.produs_id, d.depozit_id, 5, 1
FROM PRODUS p JOIN DEPOZIT d
ON d.nume='Central' AND d.oras='Bucuresti' AND d.tara='RO'
WHERE p.cod_sku='KINGSTON-D5-32'
AND NOT EXISTS (
  SELECT 1 FROM STOC s WHERE s.produs_id=p.produs_id AND s.depozit_id=d.depozit_id
);

COMMIT;

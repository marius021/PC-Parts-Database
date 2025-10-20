SET DEFINE OFF;
SET SQLBLANKLINES ON;

----------------------------------------------------------------
-- 1) MASTER: PRODUCATOR, CATEGORIE, STANDARD
----------------------------------------------------------------
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('AMD','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Intel','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('ASUS','TW',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('MSI','TW',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Kingston','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Samsung','KR',NULL);

INSERT INTO CATEGORIE (nume, descriere) VALUES ('CPU',NULL);
INSERT INTO CATEGORIE (nume, descriere) VALUES ('Motherboard',NULL);
INSERT INTO CATEGORIE (nume, descriere) VALUES ('RAM',NULL);
INSERT INTO CATEGORIE (nume, descriere) VALUES ('Storage',NULL);

-- standarde folosite în demo (dacă le ai deja, UQ va preveni duplicatele)
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('SOCKET_CPU','AM5','AMD AM5 socket');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('SOCKET_CPU','LGA1700','Intel LGA1700 socket');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('MEM_TYPE','DDR5','DDR5 memory');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('MEM_TYPE','DDR4','DDR4 memory');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('FORM_FACTOR_MB','ATX','ATX motherboard');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('FORM_FACTOR_MB','mATX','Micro-ATX motherboard');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('STORAGE_FORM','M.2 2280','M.2 2280 NVMe/SATA');

----------------------------------------------------------------
-- 2) PRODUS (folosim sub-selecturi ca să nu setăm ID-uri manual)
----------------------------------------------------------------
-- CPU AMD AM5
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'AMD-R5-7600',
  'Ryzen 5 7600',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='CPU'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='AMD'),
  36, 'ACTIV'
);

-- CPU Intel LGA1700
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'INTEL-i5-12400',
  'Core i5-12400',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='CPU'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Intel'),
  36, 'ACTIV'
);

-- Motherboard AM5 ATX
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'ASUS-B650-PLUS',
  'ASUS TUF GAMING B650-PLUS',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Motherboard'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='ASUS'),
  36, 'ACTIV'
);

-- Motherboard LGA1700 mATX
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'MSI-B660M-MORTAR',
  'MSI MAG B660M MORTAR',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Motherboard'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='MSI'),
  36, 'ACTIV'
);

-- RAM DDR5
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'KINGSTON-FURY-16G-D5',
  'Kingston Fury Beast 16GB DDR5 (2x8)',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='RAM'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Kingston'),
  36, 'ACTIV'
);

-- SSD M.2 2280
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES (
  'SAMSUNG-980-1TB',
  'Samsung 980 1TB M.2 NVMe',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Storage'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Samsung'),
  36, 'ACTIV'
);

----------------------------------------------------------------
-- 3) PRODUS_STANDARD (legăm produsele de standarde prin lookup pe text)
----------------------------------------------------------------
-- CPU ↔ SOCKET & MEM
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='AM5'
WHERE p.cod_sku='AMD-R5-7600';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5'
WHERE p.cod_sku='AMD-R5-7600';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='LGA1700'
WHERE p.cod_sku='INTEL-i5-12400';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR4'
WHERE p.cod_sku='INTEL-i5-12400';

-- Motherboard ↔ SOCKET, MEM, FORM_FACTOR
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='AM5'
WHERE p.cod_sku='ASUS-B650-PLUS';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5'
WHERE p.cod_sku='ASUS-B650-PLUS';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='FORM_FACTOR_MB' AND s.cod='ATX'
WHERE p.cod_sku='ASUS-B650-PLUS';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='LGA1700'
WHERE p.cod_sku='MSI-B660M-MORTAR';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR4'
WHERE p.cod_sku='MSI-B660M-MORTAR';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='FORM_FACTOR_MB' AND s.cod='mATX'
WHERE p.cod_sku='MSI-B660M-MORTAR';

-- RAM DDR5
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5'
WHERE p.cod_sku='KINGSTON-FURY-16G-D5';

-- SSD M.2 2280
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id
FROM PRODUS p JOIN STANDARD s ON s.grup='STORAGE_FORM' AND s.cod='M.2 2280'
WHERE p.cod_sku='SAMSUNG-980-1TB';

----------------------------------------------------------------
-- 4) INVENTORY: DEPOZIT + STOC
----------------------------------------------------------------
INSERT INTO DEPOZIT (nume, oras, tara) VALUES ('Central','Bucuresti','RO');

-- stoc prin lookup pe SKU + depozit
INSERT INTO STOC (produs_id, depozit_id, cantitate, prag_minim)
SELECT p.produs_id, d.depozit_id, 20, 5
FROM PRODUS p CROSS JOIN DEPOZIT d
WHERE p.cod_sku IN ('AMD-R5-7600','INTEL-i5-12400','ASUS-B650-PLUS','MSI-B660M-MORTAR','KINGSTON-FURY-16G-D5','SAMSUNG-980-1TB')
  AND d.nume='Central' AND d.oras='Bucuresti' AND d.tara='RO';

----------------------------------------------------------------
-- 5) CLIENT + COMANDA + LINIi
----------------------------------------------------------------
INSERT INTO CLIENT (tip, nume, cod_fiscal, tara, categoria_pret)
VALUES ('B2C','Ion Popescu',NULL,'RO',NULL);

INSERT INTO COMANDA_VANZARE (client_id, status, metoda_livrare)
VALUES ( (SELECT client_id FROM CLIENT WHERE nume='Ion Popescu'), 'APROBATA', 'Curier' );

-- adaugă 2 linii (CPU AM5 + placa AM5)
INSERT INTO CV_LINIE (cv_id, linie_nr, produs_id, cantitate, pret_unitar, discount)
SELECT cv.cv_id, 1, p.produs_id, 1, 999.99, 0
FROM COMANDA_VANZARE cv JOIN PRODUS p ON p.cod_sku='AMD-R5-7600'
WHERE cv.client_id = (SELECT client_id FROM CLIENT WHERE nume='Ion Popescu')
  AND ROWNUM=1;

INSERT INTO CV_LINIE (cv_id, linie_nr, produs_id, cantitate, pret_unitar, discount)
SELECT cv.cv_id, 2, p.produs_id, 1, 899.99, 0
FROM COMANDA_VANZARE cv JOIN PRODUS p ON p.cod_sku='ASUS-B650-PLUS'
WHERE cv.client_id = (SELECT client_id FROM CLIENT WHERE nume='Ion Popescu')
  AND ROWNUM=1;

----------------------------------------------------------------
-- 6) (opțional) EXPEDIERE + RMA
----------------------------------------------------------------
INSERT INTO EXPEDIERE (cv_id, depozit_id, curier, awb)
SELECT cv.cv_id, d.depozit_id, 'FanCourier', 'AWB-0001'
FROM COMANDA_VANZARE cv CROSS JOIN DEPOZIT d
WHERE d.nume='Central' AND d.oras='Bucuresti' AND ROWNUM=1;

-- RMA deschis pentru SSD (exemplu)
INSERT INTO RMA (client_id, produs_id, cv_id, motiv, status)
SELECT c.client_id, p.produs_id, cv.cv_id, 'Defect in 7 zile', 'DESCHIS'
FROM CLIENT c, PRODUS p, COMANDA_VANZARE cv
WHERE c.nume='Ion Popescu' AND p.cod_sku='SAMSUNG-980-1TB' AND ROWNUM=1;

COMMIT;

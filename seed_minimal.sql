SET DEFINE OFF;
SET SQLBLANKLINES ON;

------------------------------------------------------------
-- 1) MASTER: PRODUCATOR, CATEGORIE, STANDARD (lookup-uri)
------------------------------------------------------------
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('AMD','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Intel','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('ASUS','TW',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('MSI','TW',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Kingston','US',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Samsung','KR',NULL);
INSERT INTO PRODUCATOR (nume, tara, website) VALUES ('Gigabyte','TW',NULL);

INSERT INTO CATEGORIE (nume) VALUES ('CPU');
INSERT INTO CATEGORIE (nume) VALUES ('Motherboard');
INSERT INTO CATEGORIE (nume) VALUES ('RAM');
INSERT INTO CATEGORIE (nume) VALUES ('Storage');
INSERT INTO CATEGORIE (nume) VALUES ('GPU');
INSERT INTO CATEGORIE (nume) VALUES ('Case');

-- standarde minime
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('SOCKET_CPU','AM5','AMD AM5 socket');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('SOCKET_CPU','LGA1700','Intel LGA1700 socket');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('MEM_TYPE','DDR5','DDR5 memory');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('MEM_TYPE','DDR4','DDR4 memory');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('FORM_FACTOR_MB','ATX','ATX motherboard');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('FORM_FACTOR_MB','mATX','Micro-ATX motherboard');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('STORAGE_FORM','M.2 2280','M.2 2280 NVMe/SATA');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('STORAGE_FORM','2.5"','2.5-inch SATA');
INSERT INTO STANDARD (grup, cod, descriere) VALUES ('INTERFATA','PCIe x16','PCI Express x16 slot');

COMMIT;

------------------------------------------------------------
-- 2) PRODUS (max ~10 produse)
------------------------------------------------------------
-- 2x CPU
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('AMD-R5-7600','Ryzen 5 7600',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='CPU'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='AMD'),
  36,'ACTIV');

INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('INTEL-i5-12400','Core i5-12400',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='CPU'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Intel'),
  36,'ACTIV');

-- 2x Motherboard
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('ASUS-B650-PLUS','ASUS TUF GAMING B650-PLUS',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Motherboard'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='ASUS'),
  36,'ACTIV');

INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('MSI-B660M-MORTAR','MSI MAG B660M MORTAR',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Motherboard'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='MSI'),
  36,'ACTIV');

-- 2x RAM
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('KINGSTON-D5-16','Kingston Fury 16GB DDR5 (2x8)',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='RAM'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Kingston'),
  36,'ACTIV');

INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('KINGSTON-D4-16','Kingston HyperX 16GB DDR4 (2x8)',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='RAM'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Kingston'),
  36,'ACTIV');

-- 2x Storage
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('SAMSUNG-980-1TB','Samsung 980 1TB M.2 NVMe',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Storage'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Samsung'),
  36,'ACTIV');

INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('SAMSUNG-870-1TB','Samsung 870 EVO 1TB 2.5"',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Storage'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Samsung'),
  36,'ACTIV');

-- 1x GPU
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('GIGABYTE-RTX4060','Gigabyte RTX 4060',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='GPU'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='Gigabyte'),
  36,'ACTIV');

-- 1x Case
INSERT INTO PRODUS (cod_sku, denumire, categorie_id, producator_id, garantie_luni, status)
VALUES ('ASUS-CASE-ATX','ASUS Prime Case ATX',
  (SELECT categorie_id FROM CATEGORIE WHERE nume='Case'),
  (SELECT producator_id FROM PRODUCATOR WHERE nume='ASUS'),
  24,'ACTIV');

COMMIT;

------------------------------------------------------------
-- 3) PRODUS_STANDARD (legături prin lookup pe text)
------------------------------------------------------------
-- CPU sockets + memory
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='AM5' WHERE p.cod_sku='AMD-R5-7600';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5' WHERE p.cod_sku='AMD-R5-7600';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='LGA1700' WHERE p.cod_sku='INTEL-i5-12400';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR4' WHERE p.cod_sku='INTEL-i5-12400';

-- Motherboard sockets + mem + form factor
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='AM5' WHERE p.cod_sku='ASUS-B650-PLUS';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5' WHERE p.cod_sku='ASUS-B650-PLUS';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='FORM_FACTOR_MB' AND s.cod='ATX' WHERE p.cod_sku='ASUS-B650-PLUS';

INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='SOCKET_CPU' AND s.cod='LGA1700' WHERE p.cod_sku='MSI-B660M-MORTAR';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR4' WHERE p.cod_sku='MSI-B660M-MORTAR';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='FORM_FACTOR_MB' AND s.cod='mATX' WHERE p.cod_sku='MSI-B660M-MORTAR';

-- RAM types
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR5' WHERE p.cod_sku='KINGSTON-D5-16';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='MEM_TYPE' AND s.cod='DDR4' WHERE p.cod_sku='KINGSTON-D4-16';

-- Storage forms
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='STORAGE_FORM' AND s.cod='M.2 2280' WHERE p.cod_sku='SAMSUNG-980-1TB';
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='STORAGE_FORM' AND s.cod='2.5"' WHERE p.cod_sku='SAMSUNG-870-1TB';

-- GPU interface
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='INTERFATA' AND s.cod='PCIe x16' WHERE p.cod_sku='GIGABYTE-RTX4060';

-- Case form factor (suport plăci ATX)
INSERT INTO PRODUS_STANDARD (produs_id, standard_id)
SELECT p.produs_id, s.standard_id FROM PRODUS p JOIN STANDARD s ON s.grup='FORM_FACTOR_MB' AND s.cod='ATX' WHERE p.cod_sku='ASUS-CASE-ATX';

COMMIT;

------------------------------------------------------------
-- 4) DEPOZIT + STOC (lookup pe SKU + depozit)
------------------------------------------------------------
INSERT INTO DEPOZIT (nume, oras, tara) VALUES ('Central','Bucuresti','RO');

INSERT INTO STOC (produs_id, depozit_id, cantitate, prag_minim)
SELECT p.produs_id, d.depozit_id, 10, 2
FROM PRODUS p JOIN DEPOZIT d ON d.nume='Central' AND d.oras='Bucuresti' AND d.tara='RO';

COMMIT;

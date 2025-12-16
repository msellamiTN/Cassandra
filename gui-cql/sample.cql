----------------------------------------------Lab 1- CQLSH Manipulation ------------------------------------------------------ 
--------------#####################################################################################--------------------------- 

--------------########Creation d'un keyspace#################--------------
CREATE KEYSPACE IF NOT EXISTS Covid19
WITH REPLICATION={'class':'SimpleStrategy','replication_factor':3};
 
--------------########Creation d'une table#################--------------
CREATE TABLE Covid19.countries (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, confirmed INT, deaths INT, recovred INT,  active INT,
primary key (idCountry )
);

--------------########Creation d'un index#################--------------
CREATE INDEX covid_country ON Covid19.countries  (country);

--------------########Insertion de données avec SQL#################--------------
INSERT INTO covid19.countries (idcountry, country, date, longitude, latitude, confirmed, deaths,recovred, active)  
VALUES (1, 'France', '2020-11-19', 46.23219, 46.23219, 2086288, 47127, 147569, 1891592);

--------------########selection de données#################--------------
select * from covid19.countries;

--------------########Insertion de données avec JSON#################--------------
INSERT INTO covid19.countries JSON '{
"idcountry" : 1, "country" : "France", "date" : "2020-11-19",
"longitude":46.23219, "latitude" : 46.23219, "confirmed" : 2086288, "deaths" : 47227,  "recovred" : 147569, "active" : 1891592}';
--------------########selection de données#################--------------   

SELECT * FROM Covid19.countries WHERE idcountry = 1;

--------------########update de données avec TIMESTAMP#################--------------

UPDATE Covid19.Countries  
SET recovred = 147900  WHERE idcountry = 1;

--------------########selection de données  #################--------------
SELECT * FROM Covid19.countries WHERE idcountry = 1;

--------------########Récupérer la date de modification :#################--------------

SELECT writetime(country), writetime(confirmed), writetime(recovred)
FROM Covid19.Countries  WHERE   idcountry = 1;

--------------######## Selection de données #################--------------
SELECT * FROM Covid19.countries WHERE idcountry = 1;

--------------########  supprimer une valeur définie un instant T #################--------------
DELETE country FROM Covid19.Countries USING TIMESTAMP 1605818828690000
WHERE idcountry = 1;

--------------########gérer des données volatiles : TTL #################--------------

UPDATE Covid19.Countries USING TTL 3600
SET recovred=147900 WHERE idcountry = 1;

--------------######## Selection de données #################--------------
SELECT * FROM Covid19.countries WHERE idcountry = 1;
--utf-8
----------------------------------------------Lab 2- CQLSH Imbrication ------------------------------------------------------ 
--------------#####################################################################################--------------------------- 

--------------########use d'un keyspace existant#################--------------
use Covid19;

--------------########create table with tuple <  > ##################-------------------
CREATE TABLE Covid19.countries_tuple (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, 
Covid tuple< date,INT,  INT,  INT,   INT>,
primary key (idCountry )
);
----##Insertion 
 
INSERT INTO covid19.countries_tuple (idcountry, country, date, longitude, latitude,Covid)  
VALUES (1, 'France', '2020-11-19',46.23219, 46.23219, ('2020-11-19', 2086288,47127, 147569, 1891592));
---##update 
UPDATE covid19.countries_tuple  
SET Covid =('2020-11-20', 2086288,47127, 147569, 1891592)   WHERE idcountry = 1;
---##delete 
DELETE Covid FROM covid19.countries_tuple WHERE idcountry = 1;


---##select

SELECT country,Covid FROM Covid19.countries_tuple WHERE idcountry = 1;
--------------########create table with set <  > ##################-------------------
CREATE TABLE Covid19.countries_set (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, 
Covid set<INT>,
primary key (idCountry )
);
----##Insertion 
--insertion juste les cas confirmes
INSERT INTO covid19.countries_set (idcountry, country, date, longitude, latitude,Covid)  
VALUES (1, 'France', '2020-11-19',46.23219, 46.23219, { 2086288});
--selection
SELECT Covid FROM Covid19.countries_set WHERE idcountry = 1;
--update avec deaths, recovred et active avec  la UPDATE commande et de l'opérateur d'addition (+).
UPDATE covid19.countries_set  
SET Covid =Covid+{47127, 147569, 1891592}   WHERE idcountry = 1;
--Supprimez un élément d'un ensemble à l'aide de l'opérateur de soustraction (-).
UPDATE covid19.countries_set  
SET Covid =Covid-{47127, 147569, 1891592}   WHERE idcountry = 1;
--Supprimez tous les éléments d'un ensemble à l'aide de l'instruction UPDATE ou DELETE
UPDATE covid19.countries_set  
SET Covid =Covid-{}   WHERE idcountry = 1;
-- Supprimez avec delete
DELETE Covid FROM covid19.countries_set WHERE idcountry = 1;

--------------########create table with map <  > ##################-------------------
CREATE TABLE Covid19.countries_map (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, 
Covid map<date,text>,
primary key (idCountry )
);

--insertion juste les cas confirmes
INSERT INTO covid19.countries_map (idcountry, country, date, longitude, latitude,Covid)  
VALUES (1, 'France', '2020-11-19',46.23219, 46.23219,
	{
	'2020-11-19':'confirmed:2086288,deaths:47227,recovred:147569,active:1891592',
	'2020-11-20':'confirmed:2086288,deaths:47227,recovred:147569,active:1891592'	
	});
--selection
SELECT Covid FROM Covid19.countries_map WHERE idcountry = 1;
--update avec deaths, recovred et active avec  la UPDATE commande et de l'opérateur d'addition (+).
UPDATE covid19.countries_map  
SET Covid =Covid+{'2020-11-21':'confirmed:2086288,deaths:47227,recovred:147569,active:1891592'}   WHERE idcountry = 1;
--Ajoutez un élément à une position particulière en utilisant la position d'index de la liste entre crochets
UPDATE covid19.countries_map  
SET Covid['2020-11-21']='confirmed:2089288,deaths:47227,recovred:147969,active:1891992'   WHERE idcountry = 1;
 
-- Supprimez avec delete
DELETE Covid['2020-11-21'] FROM covid19.countries_map WHERE idcountry = 1;

--------------########create table with list <  > ##################-------------------
CREATE TABLE Covid19.countries_list (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, 
Covid list<INT>,
primary key (idCountry )
);
--insertion juste les cas confirmes
INSERT INTO covid19.countries_list (idcountry, country, date, longitude, latitude,Covid)  
VALUES (1, 'France', '2020-11-19',46.23219, 46.23219, [2086288]);
--selection
SELECT Covid FROM Covid19.countries_list WHERE idcountry = 1;
--update avec deaths, recovred et active avec  la UPDATE commande et de l'opérateur d'addition (+).
UPDATE covid19.countries_list  
SET Covid =Covid+[47127, 147569, 1891592]   WHERE idcountry = 1;
--Ajoutez un élément à une position particulière en utilisant la position d'index de la liste entre crochets
UPDATE covid19.countries_list  
SET Covid[0]=20862882   WHERE idcountry = 1;
 
-- Supprimez avec delete
DELETE Covid[0] FROM covid19.countries_set WHERE idcountry = 1;
--------------########create table with type <  > ##################-------------------

--Creez un type défini par l'utilisateur émme covid_info .
CREATE TYPE Covid19.CovidType (
  date date,
  confirmed INT,
  deaths INT,
  recovred INT,
  active INT
);

CREATE TABLE Covid19.countries_type (
idcountry INT, country TEXT, date DATE,  longitude DOUBLE,  latitude DOUBLE, 
covid FROZEN<CovidType>,
primary key (idCountry )
);


--insertion juste les cas confirmes
INSERT INTO covid19.countries_type
 (idcountry, country, date, longitude, latitude,Covid)  
VALUES (1, 'France', '2020-11-19',46.23219, 46.23219,
	{
	 date  : '2020-11-19',
	 confirmed  : 2086288,
	  deaths  : 47227,
	  recovred  : 147569,
	   active  : 1891592
	  }
);
--selection


SELECT Covid.confirmed,Covid.active  FROM Covid19.countries_type WHERE idcountry = 1;
--update avec deaths, recovred et active avec  la UPDATE commande et de l'opérateur d'addition (+).
UPDATE covid19.countries_type  
SET covid ={
	 date  : '2020-11-20',
	 confirmed  : 2086288,
	  deaths  : 47227,
	  recovred  : 147569,
	   active  : 1891592
	  } 
	   WHERE idcountry = 1;
  
 
-- Supprimez avec delete
DELETE Covid  FROM covid19.countries_set WHERE idcountry = 1;



 
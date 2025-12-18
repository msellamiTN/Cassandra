# Fleet Tracing IoT - Guide de Mise en Œuvre Complet

## 📋 Résumé Exécutif

Ce projet demande l'implémentation d'une plateforme complète de suivi de flotte avec trois composants majeurs :
- **Volet 1** : Pipeline ETL (Python) pour l'ingestion et transformation des données
- **Volet 2** : Cluster Cassandra Multi-Datacenter pour le stockage résilient
- **Volet 3** : Dashboard interactif pour la visualisation et l'analyse

**Durée estimée** : 1 jour (7 heures)  
**Ressources requises** : Docker, Python 3.11+, Cassandra 4.1+

---

## 🏗️ Phase 1 : Configuration de l'Environnement (1-2 jours)

### 1.1 Structure du Projet

```bash
fleet-tracing-project/
├── docker-compose.yml
├── .env
├── README.md
├── RAPPORT.md
│
├── cassandra/
│   ├── init-scripts/
│   │   └── 01-create-schema.cql
│   └── config/
│       └── cassandra.yaml (optionnel)
│
├── etl/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── etl_pipeline.py
│   ├── data_generator.py
│   ├── cassandra_writer.py
│   ├── config.py
│   └── tests/
│       └── test_etl.py
│
├── dashboard/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   ├── pages/
│   │   ├── realtime.py
│   │   ├── analytics.py
│   │   └── alerts.py
│   └── utils/
│       └── cassandra_client.py
│
├── data/
│   └── sample_telemetry.csv
│
└── docs/
    ├── architecture.md
    ├── cassandra-modeling.md
    └── user-guide.md
```

### 1.2 Préparation de docker-compose.yml

Points clés à respecter :
- Configuration des 4 nœuds Cassandra (DC1: 2 nœuds, DC2: 2 nœuds)
- Seed nodes pour la découverte inter-DC
- Health checks robustes
- Dépendances entre services (Cassandra → ETL → Dashboard)
- Network bridge isolé pour la communication intra-cluster

### 1.3 Script d'Initialisation Cassandra

Le fichier `01-create-schema.cql` doit créer :

**Keyspace** :
```sql
CREATE KEYSPACE fleet_iot
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 2,
  'dc2': 2
}
AND durable_writes = true;
```

**Cinq tables essentielles** :

1. **devices_by_fleet** : Listing des véhicules par flotte
   - PK: `(fleet_id)`, CC: `device_id`
   - Requête : Lister tous les véhicules d'une flotte

2. **latest_telemetry_by_device** : Dernier état connu
   - PK: `device_id`
   - Requête : Position/état actuels pour le dashboard live

3. **telemetry_by_device_day** : Historique journalier
   - PK: `(device_id, day)`, CC: `ts DESC`
   - TTL: 30 jours
   - Requête : Trajet d'un jour avec bucketing temporal

4. **alerts_by_fleet_day** : Alertes structurées
   - PK: `(fleet_id, day, severity)`, CC: `ts DESC, device_id`
   - Requête : Filtrer par sévérité et date

5. **fleet_analytics_by_day** : Agrégations précalculées
   - PK: `(fleet_id, day)`, CC: `hour`
   - Requête : Stats horaires d'une flotte

### 1.4 Vérification du Cluster

```bash
# Démarrer le cluster
docker compose up -d

# Attendre la convergence (5-10 min)
docker compose logs cassandra-dc1-node1

# Vérifier le statut
docker exec -it cassandra-dc1-node1 nodetool status

# Résultat attendu : UN (Up/Normal) pour les 4 nœuds
# Datacenter: dc1 (2 nœuds - 50% chacun)
# Datacenter: dc2 (2 nœuds - 50% chacun)
```

**Checkpoint ✅** : Tous les services marqués "healthy"

---

## 🔄 Phase 2 : Pipeline ETL (2-3 H)

### 2.1 Configuration (config.py)

```python
# Variables d'environnement
CASSANDRA_HOSTS = os.getenv('CASSANDRA_HOSTS', 'localhost').split(',')
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'fleet_iot')
CASSANDRA_DC = os.getenv('CASSANDRA_DC', 'dc1')

# Paramètres de performance
BATCH_SIZE = 100
ASYNC_CONCURRENCY = 50  # Requêtes async en parallèle
WRITE_TIMEOUT = 30  # secondes

# Monitoring
METRICS_INTERVAL = 60  # Afficher les stats tous les 60s
```

### 2.2 Writer Cassandra (cassandra_writer.py)

Points critiques à implémenter :

**1. Connexion MDC**
```python
from cassandra.cluster import Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy

profile = ExecutionProfile(
    load_balancing_policy=TokenAwarePolicy(
        DCAwareRoundRobinPolicy(local_dc='dc1')
    )
)
cluster = Cluster(contact_points, execution_profiles={'default': profile})
```

**2. Prepared Statements** (impératif pour la performance)
```python
self.insert_latest = session.prepare("""
    INSERT INTO latest_telemetry_by_device 
    (device_id, last_ts, lat, lon, speed_kmh, battery_pct, temp_c)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""")
```

**3. Modes d'insertion**

- **Batch** : Pour les insertions groupées (historique)
  - Avantage : Une seule requête pour N records
  - Risque : Taille max 65K (limitation Cassandra)
  
- **Asynchrone** : Pour les flux temps réel
  - Avantage : Non-bloquant, throughput maximal
  - Implémentation : `session.execute_async()` + gestion des futures

**4. Gestion d'erreurs et retry**
```python
try:
    future = session.execute_async(stmt, params)
    future.result(timeout=30)
except WriteTimeout:
    # Retry avec backoff exponentiel
except InvalidRequest:
    # Erreur de schéma - à logger et ignorer
```

### 2.3 Générateur de Données (data_generator.py)

**Données réalistes** :
- GPS : Coordonnées centrées sur une zone (ex: Île-de-France)
- Vitesse : 0-130 km/h (distribution réaliste selon heure)
- Batterie : 20-100% (dégradation linéaire dans la journée)
- Température : 15-35°C (variation saisonnière)
- Zone : Classification discrète (zone_a, zone_b, zone_c)

**Temporal coherence** :
```python
# Générer des séries cohérentes (pas de sauts temporels abruptes)
for device in devices:
    timestamp = base_time
    for i in range(num_points):
        record = {
            'device_id': device,
            'timestamp': timestamp,
            'lat': previous_lat + random.gauss(0, 0.001),  # Petit déplacement
            'speed_kmh': random.uniform(previous_speed - 5, previous_speed + 5),
            ...
        }
        previous_lat = record['lat']
        previous_speed = record['speed_kmh']
        timestamp -= timedelta(seconds=30)
```

### 2.4 Pipeline Principal (etl_pipeline.py)

**Deux modes d'exécution** :

**Mode 1 : Batch (Historique)**
```
Objectif : Charger 50k+ records rapidement
Stratégie :
  - Générer 50 batches de 1000 records
  - Chaque batch = 1 sec (rate limiting)
  - Durée totale : 50-60 secondes
  - Mesurer : latence P50/P95, throughput
```

**Mode 2 : Streaming (Temps réel)**
```
Objectif : Simuler un flux continu
Stratégie :
  - Générer 10 records/itération (1 par device)
  - Délai inter-itération : 5 secondes
  - Asynchrone : Ne pas bloquer sur write
  - Durée : 10 minutes (test)
```

### 2.5 Monitoring et Métriques

À implémenter dans l'ETL :

```python
class ETLMetrics:
    def __init__(self):
        self.records_written = 0
        self.errors = 0
        self.start_time = time.time()
    
    def update(self, num_records, duration):
        throughput = num_records / duration  # records/sec
        avg_latency = duration / num_records * 1000  # ms
        
    def report(self):
        elapsed = time.time() - self.start_time
        throughput = self.records_written / elapsed
        print(f"Throughput: {throughput:.0f} rec/s | Errors: {self.errors}")
```

### 2.6 Tests de Charge

Benchmarks attendus :

| Mode | Taille | Durée | Throughput | Latence P99 |
|------|--------|-------|-----------|------------|
| Batch | 100 records | 1-2s | 50-100 rec/s | <100ms |
| Streaming | 100 records | 10-20s | 5-10 rec/s | <200ms |

**Test de résilience** :
```bash
# Pendant le chargement ETL :
docker stop cassandra-dc1-node2

# L'ETL doit continuer (replication_factor=2)
# Puis redémarrer le nœud
docker start cassandra-dc1-node2
nodetool repair
```

**Livrables** :
- ✅ Code ETL complet et fonctionnel
- ✅ 50k+ records insérés avec logs
- ✅ Rapport: latence P50/P95/P99, throughput, overhead

---

## 📊 Phase 3 : Dashboard (2-3 H)

### 3.1 Client Cassandra (utils/cassandra_client.py)

**Méthodes essentielles** :

```python
def get_latest_telemetry(device_id):
    # O(1) - Partition key lookup
    # Retourne : position, vitesse, batterie, temp actuels

def get_device_history(device_id, day, limit=500):
    # O(log N) - Range query sur timestamp
    # Retourne : DataFrame avec tous les points du jour

def get_fleet_latest_all(fleet_id):
    # Listera d'abord les devices (devices_by_fleet)
    # Puis requête get_latest_telemetry pour chacun
    # ⚠️ N requêtes → optimiser avec cache

def get_fleet_alerts(fleet_id, day, severity=None):
    # Récupère alertes filtrées par sévérité
    # Si severity=ALL → requête 3 severities différentes

def get_fleet_analytics(fleet_id, day):
    # Stats agrégées par heure
```

**Optimisations** :

1. **Caching** (optionnel mais recommandé)
```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_latest_cached(device_id):
    result = get_latest_telemetry(device_id)
    # Invalider après 30 secondes
    return result
```

2. **Pagination pour gros volumes**
```python
def get_device_history_paginated(device_id, day, page_size=100):
    query = """
        SELECT * FROM telemetry_by_device_day
        WHERE device_id = %s AND day = %s
        LIMIT %s
    """
    # Utiliser paging_state pour pagination
```

3. **Requêtes optimisées**
```python
# ❌ Anti-pattern : SELECT * suivi de filtrage en Python
results = session.execute("SELECT * FROM ...")
filtered = [r for r in results if r.speed > 50]

# ✅ Correct : Filtrage côté requête
results = session.execute("""
    SELECT * FROM telemetry_by_device_day
    WHERE device_id = %s AND day = %s AND ts > ?
""")
```

### 3.2 Page Real-Time (pages/realtime.py)

**Composants** :

1. **Sélection flotte (Sidebar)**
   - Input text pour fleet_id
   - Sélecteur de date

2. **Métriques KPI (haut)**
   ```python
   col1, col2, col3, col4 = st.columns(4)
   col1.metric("Active Devices", 47)
   col2.metric("Avg Speed", "42 km/h")
   col3.metric("Avg Battery", "78%")
   col4.metric("Critical Alerts", 2)
   ```

3. **Carte interactive (centre)**
   ```python
   import plotly.express as px
   fig = px.scatter_mapbox(
       devices_df,
       lat='lat', lon='lon',
       hover_name='device_id',
       color='speed_kmh',  # Colorer par vitesse
       zoom=10,
       mapbox_style="open-street-map"
   )
   st.plotly_chart(fig, use_container_width=True)
   ```

4. **Tableau des devices (bas)**
   - Colonnes : device_id, position, vitesse, batterie, température
   - Tri/filtrage activés

### 3.3 Page Analytics (pages/analytics.py)

**Graphiques temporels** :

1. **Vitesse dans le temps**
   ```python
   fig = px.line(
       history_df, x='ts', y='speed_kmh',
       title='Speed Evolution',
       range_y=[0, 150]
   )
   ```

2. **Batterie dans le temps**
   ```python
   fig = px.line(
       history_df, x='ts', y='battery_pct',
       title='Battery Level'
   )
   ```

3. **Température et humidité**
   ```python
   fig = px.scatter(
       history_df, x='ts', y='temp_c',
       title='Temperature Trend'
   )
   ```

**Comparaisons** :

```python
# Comparer N devices sur même métrique
multi_device_data = pd.concat([
    get_device_history(d, selected_date)
    for d in selected_devices
])

fig = px.line(
    multi_device_data, x='ts', y='speed_kmh',
    color='device_id',
    title='Multi-Device Comparison'
)
```

### 3.4 Page Alerts (pages/alerts.py)

**Filtres** :
- Sévérité (HIGH, MEDIUM, LOW, ALL)
- Plage de dates
- Type d'alerte

**Visualisations** :

1. **Compteurs par sévérité**
   ```python
   alerts_df['severity'].value_counts()
   # Afficher en KPI
   ```

2. **Timeline visuelle**
   ```python
   fig = px.scatter(
       alerts_df,
       x='ts', y='device_id',
       color='severity',
       color_discrete_map={'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'yellow'},
       size='severity',
       title='Alerts Timeline'
   )
   ```

3. **Table des alertes**
   - Colonné cliquable pour détails
   - Lien vers le device concerné

### 3.5 Livrables Dashboard

- ✅ App Streamlit démarrée sur http://localhost:8501
- ✅ 3 pages fonctionnelles
- ✅ Requêtes CQL documentées
- ✅ Captures d'écran des pages

---

## 🔐 Phase 4 : Optimisations & Résilience (1-2 H)

### 4.1 Tuning de Performance

**Identifier les slow queries** :

```python
# Activer le tracing
stmt = SimpleStatement(query)
stmt.trace = True
result = session.execute(stmt)
print(result.trace)

# Lire le tracing
for event in result.trace.events:
    print(f"{event.description}")
```

**Problèmes communs et solutions** :

| Problème | Cause | Solution |
|----------|-------|----------|
| Latence élevée sur `get_latest_all()` | N requêtes séquentielles | Ajouter cache ou parallel requests |
| Requête sur colonne non-clé | Full scan | Ajouter index secondaire (sparingly) |
| Memory OOM sur gros range | Pagination absente | Implémenter `fetch_size()` |

### 4.2 Tests de Résilience

**Scénario 1 : Perte d'un nœud**

```bash
# Phase 1 : Chargement en cours
docker compose up etl-pipeline

# Phase 2 : Kill un nœud pendant le chargement
docker stop cassandra-dc1-node2

# Phase 3 : Vérifier que
#  - ETL continue (quorum toujours atteint)
#  - Dashboard reste accessible
#  - Pas de perte de données (RF=2)

# Phase 4 : Redémarrer et réparer
docker start cassandra-dc1-node2
docker exec cassandra-dc1-node2 nodetool repair
```

**Scénario 2 : Perte d'un datacenter**

```bash
# Arrêter tous les nœuds dc2
docker stop cassandra-dc2-node1 cassandra-dc2-node2

# Vérifier que le système continue
# Données disponibles avec RF=2 en dc1

# Redémarrer
docker start cassandra-dc2-node1 cassandra-dc2-node2
```

### 4.3 Documentation Technique

**À inclure dans RAPPORT.pdf** :

1. **Architecture décisionnelle**
   - Diagramme : DataSources → ETL → Cassandra → Dashboard
   - Justification de chaque table
   - Stratégie de partitionnement

2. **Modélisation NoSQL**
   - Query-first design : pour chaque requête → table appropriée
   - Denormalization : répétition délibérée (normal en NoSQL)
   - Clustering strategy : tri des données

3. **Résilience**
   - Replica factor : 2 par DC (4 copies totales)
   - Quorum reads/writes : garantit cohérence
   - Tests de failover documentés

4. **Performance**
   - Benchmarks : throughput (rec/s), latence (ms)
   - Comparaison batch vs async
   - Impact du cache

5. **Captures d'écran**
   - Real-time page avec 10+ devices
   - Analytics page avec graphiques temporels
   - Alerts page avec timeline

---

## 📦 Rendu Final

### Structure du Livrable

```
fleet-tracing-project.zip
├── README.md (instructions déploiement)
├── RAPPORT.pdf (5-10 pages)
├── docker-compose.yml
├── .env.example
│
├── cassandra/
│   └── init-scripts/01-create-schema.cql
├── etl/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── etl_pipeline.py
│   ├── cassandra_writer.py
│   ├── data_generator.py
│   ├── config.py
│   └── tests/test_etl.py
├── dashboard/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   ├── pages/ (realtime.py, analytics.py, alerts.py)
│   └── utils/cassandra_client.py
│
├── docs/
│   ├── architecture.md
│   ├── cassandra-modeling.md
│   └── user-guide.md
│
└── screenshots/
    ├── realtime-page.png
    ├── analytics-page.png
    └── alerts-page.png
```

### Contenu du RAPPORT.pdf

1. **Page de couverture** : Titre, auteur, date
2. **Executive Summary** : 1 page avec résumé et résultats clés
3. **Architecture Technique** : 2 pages avec diagrammes
4. **Modélisation de Données** : 2 pages (justification des tables)
5. **Performance & Résilience** : 2 pages (benchmarks, tests failover)
6. **Guide d'Utilisation** : 1 page (démarrer le système)
7. **Annexes** : Screenshots, logs de test

### Commandes de Déploiement

```bash
# 1. Initialiser
git clone <repo>
cd fleet-tracing-project
cp .env.example .env

# 2. Démarrer
docker compose up -d

# 3. Vérifier
docker compose logs cassandra-dc1-node1
docker exec cassandra-dc1-node1 nodetool status

# 4. Accéder au dashboard
# http://localhost:8501

# 5. Arrêter
docker compose down
```

### Checklist de Validation

- [ ] Tous les 4 nœuds Cassandra "UP/Normal"
- [ ] 50k+ records chargés en ETL (logs visibles)
- [ ] Dashboard accessible et affichant des données
- [ ] Real-Time page avec carte et KPI
- [ ] Analytics page avec graphiques temporels
- [ ] Alerts page avec filtres
- [ ] Test failover réussi (stop/start nœud)
- [ ] RAPPORT.pdf complété
- [ ] README.md avec instructions claires

---

 

## 💡 Conseils Clés

1. **Commencer simple** : Faire fonctionner le cluster avant d'ajouter la complexité
2. **Tester fréquemment** : Vérifier à chaque étape que les données circulent
3. **Documenter en cours** : Prendre des screenshots au fur et à mesure
4. **Automatiser les tests** : Scripts bash pour vérifier la convergence du cluster
5. **Git** : Commiter régulièrement (une commit par livrable)

---

## 🔗 Ressources Essentielles

- [Cassandra Data Modeling](https://cassandra.apache.org/doc/latest/developing/cql/)
- [Python Driver API](https://docs.datastax.com/en/developer/python-driver/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

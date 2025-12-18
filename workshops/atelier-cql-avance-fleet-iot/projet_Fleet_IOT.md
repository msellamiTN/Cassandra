Projet à Rendre : Système Fleet Tracing IoT avec ETL et Dashboard
Contexte du Projet
Vous intégrez une équipe Data/IoT chargée de développer une solution complète de suivi de flotte en temps réel. Le projet comprend trois composants majeurs :

Pipeline ETL : Ingestion et transformation des données de télémétrie via Python
Cluster Cassandra Multi-Datacenter (MDC) : Stockage distribué haute performance
Dashboard Analytics : Visualisation temps réel et historique des données

Votre mission : concevoir, implémenter et déployer l'ensemble de la stack avec Docker Compose.

Architecture Globale du Système
┌─────────────────────────────────────────────────────────────────┐
│                    FLEET TRACING PLATFORM                       │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   DATA SOURCES   │
                    │  (IoT Devices)   │
                    └────────┬─────────┘
                             │
                             ▼
          ┌──────────────────────────────────┐
          │         VOLET 1 : ETL            │
          │  ┌────────────────────────────┐  │
          │  │   Python ETL Pipeline      │  │
          │  │  - cassandra-driver        │  │
          │  │  - pandas / data cleaning  │  │
          │  │  - batch / streaming       │  │
          │  └────────────┬───────────────┘  │
          └───────────────┼──────────────────┘
                          │
                          ▼
          ┌────────────────────────────────────┐
          │    CASSANDRA MDC CLUSTER           │
          │  ┌──────────────┬──────────────┐   │
          │  │  DC1 (dc1)   │  DC2 (dc2)   │   │
          │  │  - node1     │  - node3     │   │
          │  │  - node2     │  - node4     │   │
          │  └──────────────┴──────────────┘   │
          │  Replication: {'dc1': 2, 'dc2': 2} │
          └────────────────┬───────────────────┘
                           │
                           ▼
          ┌──────────────────────────────────┐
          │      VOLET 2 : DASHBOARD         │
          │  ┌────────────────────────────┐  │
          │  │   Streamlit / Dash / Flask │  │
          │  │  - Real-time monitoring    │  │
          │  │  - Historical analytics    │  │
          │  │  - Alerts visualization    │  │
          │  └────────────────────────────┘  │
          └──────────────────────────────────┘

Objectifs Pédagogiques
Volet 1 : ETL Python-Cassandra

Maîtriser le driver cassandra-driver (Python)
Implémenter des stratégies d'insertion (batch, async)
Gérer la préparation des données (bucketing temporel, dé-duplication)
Monitorer les performances (latence, throughput)

Volet 2 : Dashboard Analytics

Construire des visualisations temps réel à partir de Cassandra
Optimiser les requêtes CQL pour l'analytique
Implémenter des agrégations côté application
Gérer la pagination et les requêtes lourdes

Volet 3 : Déploiement Docker Compose

Orchestrer un cluster Cassandra multi-datacenter
Configurer la réplication inter-datacenter
Gérer les dépendances entre services
Implémenter health checks et restart policies


Architecture Technique Détaillée
Modèle de Données Cassandra
┌─────────────────────────────────────────────────────────────┐
│                   KEYSPACE: fleet_iot                       │
│   Replication: NetworkTopologyStrategy                      │
│   {'dc1': 2, 'dc2': 2}                                      │
└─────────────────────────────────────────────────────────────┘

TABLE 1: devices_by_fleet
┌──────────────────────────────────────────┐
│ PK: (fleet_id)                           │
│ CC: device_id                            │
│ Colonnes: model, activated_at, status    │
│ Usage: Liste des devices par flotte      │
└──────────────────────────────────────────┘

TABLE 2: latest_telemetry_by_device
┌──────────────────────────────────────────┐
│ PK: (device_id)                          │
│ CC: -                                    │
│ Colonnes: last_ts, lat, lon, speed_kmh,  │
│          battery_pct, temp_c             │
│ Usage: État actuel (dashboard temps réel)│
└──────────────────────────────────────────┘

TABLE 3: telemetry_by_device_day
┌──────────────────────────────────────────┐
│ PK: (device_id, day)                     │
│ CC: ts DESC                              │
│ Colonnes: lat, lon, speed_kmh,           │
│          battery_pct, temp_c, zone       │
│ Usage: Historique journalier             │
│ TTL: 30 jours                            │
└──────────────────────────────────────────┘

TABLE 4: alerts_by_fleet_day
┌──────────────────────────────────────────┐
│ PK: (fleet_id, day, severity)            │
│ CC: ts DESC, device_id                   │
│ Colonnes: alert_type, message, resolved  │
│ Usage: Alerting et monitoring            │
└──────────────────────────────────────────┘

TABLE 5: fleet_analytics_by_day
┌──────────────────────────────────────────┐
│ PK: (fleet_id, day)                      │
│ CC: hour                                 │
│ Colonnes: total_distance_km,             │
│          avg_speed_kmh, alerts_count,    │
│          active_devices_count            │
│ Usage: Agrégations pré-calculées         │
└──────────────────────────────────────────┘

Structure du Projet
fleet-tracing-project/
├── docker-compose.yml
├── README.md
├── .env
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
│   └── config.py
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
└── data/
    └── sample_telemetry.csv

VOLET 1 : Pipeline ETL Python-Cassandra
Architecture du Pipeline ETL
┌─────────────────────────────────────────────────────────────┐
│                     ETL PIPELINE                            │
└─────────────────────────────────────────────────────────────┘

    EXTRACT                TRANSFORM              LOAD
       │                       │                    │
       ▼                       ▼                    ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│ Data Sources │      │  Validation  │     │  Cassandra   │
│              │─────▶│  Enrichment  │────▶│   Writer     │
│ - CSV files  │      │  Bucketing   │     │              │
│ - IoT API    │      │  Aggregation │     │ - Batch      │
│ - Kafka      │      └──────────────┘     │ - Async      │
└──────────────┘                           │ - Prepared   │
                                           └──────────────┘
Composants à Implémenter
1.1 Configuration Cassandra (cassandra_writer.py)
pythonfrom cassandra.cluster import Cluster, ExecutionProfile
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.query import BatchStatement, PreparedStatement
from datetime import datetime, date
import logging

class CassandraWriter:
    def __init__(self, contact_points, keyspace, datacenter='dc1'):
        """
        Initialize Cassandra connection with MDC support
        
        Args:
            contact_points: List of Cassandra node IPs
            keyspace: Target keyspace
            datacenter: Preferred datacenter for reads
        """
        # Configuration de la politique de load balancing
        profile = ExecutionProfile(
            load_balancing_policy=TokenAwarePolicy(
                DCAwareRoundRobinPolicy(local_dc=datacenter)
            )
        )
        
        self.cluster = Cluster(
            contact_points=contact_points,
            execution_profiles={'default': profile},
            protocol_version=4
        )
        self.session = self.cluster.connect(keyspace)
        self.logger = logging.getLogger(__name__)
        
        # Prepared statements pour performance
        self._prepare_statements()
    
    def _prepare_statements(self):
        """Prepare CQL statements pour réutilisation"""
        self.insert_latest = self.session.prepare("""
            INSERT INTO latest_telemetry_by_device 
            (device_id, last_ts, lat, lon, speed_kmh, battery_pct, temp_c)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        self.insert_history = self.session.prepare("""
            INSERT INTO telemetry_by_device_day 
            (device_id, day, ts, lat, lon, speed_kmh, battery_pct, temp_c, zone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            USING TTL 2592000
        """)
        
        self.insert_alert = self.session.prepare("""
            INSERT INTO alerts_by_fleet_day 
            (fleet_id, day, severity, ts, device_id, alert_type, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
    
    def write_telemetry_batch(self, telemetry_records):
        """
        Écriture par batch de données de télémétrie
        
        Args:
            telemetry_records: List de dicts avec les données
        """
        batch = BatchStatement()
        
        for record in telemetry_records:
            device_id = record['device_id']
            ts = record['timestamp']
            day = ts.date()
            
            # Latest state (UPSERT automatique)
            batch.add(self.insert_latest, (
                device_id, ts, 
                record['lat'], record['lon'],
                record['speed_kmh'], record['battery_pct'],
                record['temp_c']
            ))
            
            # Historical data avec bucketing journalier
            batch.add(self.insert_history, (
                device_id, day, ts,
                record['lat'], record['lon'],
                record['speed_kmh'], record['battery_pct'],
                record['temp_c'], record.get('zone', 'unknown')
            ))
        
        try:
            self.session.execute(batch)
            self.logger.info(f"Batch de {len(telemetry_records)} records inséré")
        except Exception as e:
            self.logger.error(f"Erreur batch insert: {e}")
            raise
    
    def write_telemetry_async(self, telemetry_records):
        """
        Écriture asynchrone pour haute performance
        """
        futures = []
        
        for record in telemetry_records:
            # Insertion asynchrone
            future = self.session.execute_async(
                self.insert_latest,
                (record['device_id'], record['timestamp'], ...)
            )
            futures.append(future)
        
        # Attendre toutes les insertions
        for future in futures:
            try:
                future.result()
            except Exception as e:
                self.logger.error(f"Async insert failed: {e}")
    
    def close(self):
        """Fermeture propre de la connexion"""
        self.cluster.shutdown()
1.2 Générateur de Données (data_generator.py)
pythonimport random
from datetime import datetime, timedelta
import pandas as pd

class FleetDataGenerator:
    def __init__(self, num_devices=10, fleet_id='fleet-001'):
        self.num_devices = num_devices
        self.fleet_id = fleet_id
        self.devices = [f'device-{i:03d}' for i in range(num_devices)]
    
    def generate_telemetry_batch(self, num_records=100):
        """
        Génère un batch de données de télémétrie
        
        Returns:
            List de dicts avec les données simulées
        """
        records = []
        base_time = datetime.now()
        
        for i in range(num_records):
            device_id = random.choice(self.devices)
            timestamp = base_time - timedelta(seconds=i*10)
            
            record = {
                'device_id': device_id,
                'fleet_id': self.fleet_id,
                'timestamp': timestamp,
                'lat': 48.8566 + random.uniform(-0.1, 0.1),
                'lon': 2.3522 + random.uniform(-0.1, 0.1),
                'speed_kmh': random.uniform(0, 120),
                'battery_pct': random.randint(20, 100),
                'temp_c': random.uniform(15, 30),
                'zone': random.choice(['zone_a', 'zone_b', 'zone_c'])
            }
            records.append(record)
        
        return records
    
    def generate_alert(self, device_id, severity='HIGH'):
        """Génère une alerte pour un device"""
        return {
            'fleet_id': self.fleet_id,
            'device_id': device_id,
            'day': date.today(),
            'severity': severity,
            'timestamp': datetime.now(),
            'alert_type': random.choice(['battery_low', 'speed_limit', 'temperature']),
            'message': f'Alert for {device_id}'
        }
1.3 Pipeline Principal (etl_pipeline.py)
pythonimport time
import logging
from data_generator import FleetDataGenerator
from cassandra_writer import CassandraWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.generator = FleetDataGenerator(num_devices=50)
        self.writer = CassandraWriter(
            contact_points=['cassandra-node1', 'cassandra-node2'],
            keyspace='fleet_iot',
            datacenter='dc1'
        )
    
    def run_batch_load(self, num_batches=10, batch_size=100):
        """
        Chargement par batch (historique)
        """
        logger.info("Démarrage du chargement batch...")
        
        for i in range(num_batches):
            # Génération des données
            records = self.generator.generate_telemetry_batch(batch_size)
            
            # Écriture dans Cassandra
            start_time = time.time()
            self.writer.write_telemetry_batch(records)
            duration = time.time() - start_time
            
            logger.info(f"Batch {i+1}/{num_batches} - {batch_size} records en {duration:.2f}s")
            time.sleep(1)  # Rate limiting
    
    def run_streaming_simulation(self, duration_seconds=300):
        """
        Simulation de streaming temps réel
        """
        logger.info("Démarrage du streaming simulation...")
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            # Génération d'1 record par device
            records = self.generator.generate_telemetry_batch(10)
            
            # Écriture asynchrone
            self.writer.write_telemetry_async(records)
            
            time.sleep(5)  # Fréquence d'envoi: 5 secondes
    
    def cleanup(self):
        self.writer.close()

if __name__ == '__main__':
    pipeline = ETLPipeline()
    
    try:
        # Phase 1: Chargement historique
        pipeline.run_batch_load(num_batches=50, batch_size=200)
        
        # Phase 2: Simulation streaming
        pipeline.run_streaming_simulation(duration_seconds=600)
    
    finally:
        pipeline.cleanup()
```

### Livrables Volet 1

- [ ] `cassandra_writer.py` avec gestion MDC
- [ ] `data_generator.py` avec données réalistes
- [ ] `etl_pipeline.py` avec modes batch et streaming
- [ ] `requirements.txt` avec dépendances
- [ ] Dockerfile pour l'ETL
- [ ] Tests unitaires pour les composants critiques

---

## VOLET 2 : Dashboard Analytics

### Architecture du Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│                  DASHBOARD ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Real-Time View  │     │  Analytics View  │     │   Alerts View    │
│                  │     │                  │     │                  │
│ - Map devices    │     │ - Fleet stats    │     │ - Critical       │
│ - Latest status  │     │ - Trends charts  │     │ - Warnings       │
│ - Live metrics   │     │ - Comparisons    │     │ - Timeline       │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                      ┌───────────────────────┐
                      │  Cassandra Client     │
                      │  - Query optimizer    │
                      │  - Caching layer      │
                      │  - Pagination         │
                      └───────────┬───────────┘
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │   Cassandra Cluster   │
                      └───────────────────────┘
Composants à Implémenter
2.1 Client Cassandra (utils/cassandra_client.py)
pythonfrom cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, date
import pandas as pd

class DashboardCassandraClient:
    def __init__(self, contact_points, keyspace):
        self.cluster = Cluster(contact_points)
        self.session = self.cluster.connect(keyspace)
    
    def get_latest_telemetry(self, device_id):
        """
        Récupère l'état actuel d'un device (O(1) lookup)
        """
        query = """
            SELECT * FROM latest_telemetry_by_device 
            WHERE device_id = %s
        """
        result = self.session.execute(query, (device_id,))
        return result.one()._asdict() if result else None
    
    def get_device_history(self, device_id, day, limit=100):
        """
        Récupère l'historique journalier d'un device
        """
        query = """
            SELECT ts, lat, lon, speed_kmh, battery_pct, temp_c
            FROM telemetry_by_device_day
            WHERE device_id = %s AND day = %s
            LIMIT %s
        """
        rows = self.session.execute(query, (device_id, day, limit))
        return pd.DataFrame(list(rows))
    
    def get_fleet_alerts(self, fleet_id, day, severity=None):
        """
        Récupère les alertes d'une flotte
        """
        if severity:
            query = """
                SELECT * FROM alerts_by_fleet_day
                WHERE fleet_id = %s AND day = %s AND severity = %s
            """
            params = (fleet_id, day, severity)
        else:
            # Note: Nécessite une table supplémentaire sans severity dans PK
            # ou scan de toutes les severities
            severities = ['HIGH', 'MEDIUM', 'LOW']
            all_alerts = []
            for sev in severities:
                query = """
                    SELECT * FROM alerts_by_fleet_day
                    WHERE fleet_id = %s AND day = %s AND severity = %s
                """
                rows = self.session.execute(query, (fleet_id, day, sev))
                all_alerts.extend(list(rows))
            return pd.DataFrame(all_alerts)
        
        rows = self.session.execute(query, params)
        return pd.DataFrame(list(rows))
    
    def get_fleet_analytics(self, fleet_id, day):
        """
        Récupère les analytics agrégées
        """
        query = """
            SELECT * FROM fleet_analytics_by_day
            WHERE fleet_id = %s AND day = %s
        """
        rows = self.session.execute(query, (fleet_id, day))
        return pd.DataFrame(list(rows))
    
    def get_all_devices_latest(self, fleet_id):
        """
        Récupère l'état actuel de tous les devices d'une flotte
        
        Note: Nécessite d'abord lister les devices, puis requêter chacun
        """
        # Étape 1: Lister les devices
        query1 = """
            SELECT device_id FROM devices_by_fleet
            WHERE fleet_id = %s
        """
        device_rows = self.session.execute(query1, (fleet_id,))
        device_ids = [row.device_id for row in device_rows]
        
        # Étape 2: Récupérer l'état de chaque device
        all_states = []
        for device_id in device_ids:
            state = self.get_latest_telemetry(device_id)
            if state:
                all_states.append(state)
        
        return pd.DataFrame(all_states)
    
    def close(self):
        self.cluster.shutdown()
2.2 Application Streamlit (app.py)
pythonimport streamlit as st
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from utils.cassandra_client import DashboardCassandraClient

# Configuration
st.set_page_config(
    page_title="Fleet Tracing Dashboard",
    page_icon="🚛",
    layout="wide"
)

# Connexion Cassandra
@st.cache_resource
def get_cassandra_client():
    return DashboardCassandraClient(
        contact_points=['cassandra-node1'],
        keyspace='fleet_iot'
    )

client = get_cassandra_client()

# Sidebar
st.sidebar.title("🚛 Fleet Tracing")
fleet_id = st.sidebar.text_input("Fleet ID", "fleet-001")
selected_date = st.sidebar.date_input("Date", date.today())

# Navigation
page = st.sidebar.radio("Navigation", ["Real-Time", "Analytics", "Alerts"])

# PAGE 1: Real-Time Monitoring
if page == "Real-Time":
    st.title("📍 Real-Time Fleet Monitoring")
    
    # Récupération des données
    devices_data = client.get_all_devices_latest(fleet_id)
    
    if not devices_data.empty:
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Active Devices", len(devices_data))
        col2.metric("Avg Speed", f"{devices_data['speed_kmh'].mean():.1f} km/h")
        col3.metric("Avg Battery", f"{devices_data['battery_pct'].mean():.0f}%")
        col4.metric("Avg Temp", f"{devices_data['temp_c'].mean():.1f}°C")
        
        # Carte des devices
        st.subheader("Fleet Map")
        fig = px.scatter_mapbox(
            devices_data,
            lat='lat',
            lon='lon',
            hover_name='device_id',
            hover_data=['speed_kmh', 'battery_pct'],
            color='speed_kmh',
            size='speed_kmh',
            color_continuous_scale='Viridis',
            zoom=10,
            height=500
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
        
        # Table des devices
        st.subheader("Devices Status")
        st.dataframe(devices_data, use_container_width=True)
    else:
        st.warning("No devices found for this fleet")

# PAGE 2: Analytics
elif page == "Analytics":
    st.title("📊 Fleet Analytics")
    
    # Sélection du device
    device_id = st.selectbox("Select Device", [f"device-{i:03d}" for i in range(10)])
    
    # Récupération de l'historique
    history_df = client.get_device_history(device_id, selected_date, limit=500)
    
    if not history_df.empty:
        # Graphique de vitesse
        fig_speed = px.line(
            history_df, 
            x='ts', 
            y='speed_kmh',
            title='Speed Evolution',
            labels={'speed_kmh': 'Speed (km/h)', 'ts': 'Time'}
        )
        st.plotly_chart(fig_speed, use_container_width=True)
        
        # Graphique de batterie
        fig_battery = px.line(
            history_df,
            x='ts',
            y='battery_pct',
            title='Battery Level',
            labels={'battery_pct': 'Battery (%)', 'ts': 'Time'}
        )
        st.plotly_chart(fig_battery, use_container_width=True)
        
        # Statistiques
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Max Speed", f"{history_df['speed_kmh'].max():.1f} km/h")
            st.metric("Min Battery", f"{history_df['battery_pct'].min()}%")
        with col2:
            st.metric("Avg Speed", f"{history_df['speed_kmh'].mean():.1f} km/h")
            st.metric("Avg Temp", f"{history_df['temp_c'].mean():.1f}°C")
    else:
        st.info("No data available for this device on this date")

# PAGE 3: Alerts
elif page == "Alerts":
    st.title("⚠️ Fleet Alerts")
    
    # Filtres
    severity_filter = st.selectbox("Severity", ["ALL", "HIGH", "MEDIUM", "LOW"])
    
    # Récupération des alertes
    if severity_filter == "ALL":
        alerts_df = client.get_fleet_alerts(fleet_id, selected_date)
    else:
        alerts_df = client.get_fleet_alerts(fleet_id, selected_date, severity_filter)
    
    if not alerts_df.empty:
        # Compteurs par sévérité
        severity_counts = alerts_df['severity'].value_counts()
        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 HIGH", severity_counts.get('HIGH', 0))
        col2.metric("🟡 MEDIUM", severity_counts.get('MEDIUM', 0))
        col3.metric("🟢 LOW", severity_counts.get('LOW', 0))
        
        # Timeline des alertes
        fig = px.scatter(
            alerts_df,
            x='ts',
            y='device_id',
            color='severity',
            size='severity',
            hover_data=['alert_type', 'message'],
            title='Alerts Timeline',
            color_discrete_map={'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'green'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Table des alertes
        st.dataframe(alerts_df.sort_values('ts', ascending=False), use_container_width=True)
    else:
        st.success("No alerts for this date 🎉")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Dashboard v1.0 - Cassandra MDC Backend")
Livrables Volet 2

 app.py avec 3 pages fonctionnelles
 cassandra_client.py avec requêtes optimisées
 Visualisations interactives (Plotly/Matplotlib)
 Gestion de la pagination pour grandes données
 Dockerfile pour le dashboard
 Documentation des requêtes CQL utilisées


VOLET 3 : Déploiement Docker Compose
docker-compose.yml
yamlversion: '3.8'

services:
  # ==================== CASSANDRA MDC CLUSTER ====================
  
  # Datacenter 1 - Node 1
  cassandra-dc1-node1:
    image: cassandra:4.1
    container_name: cassandra-dc1-node1
    hostname: cassandra-dc1-node1
    networks:
      - fleet-network
    ports:
      - "9042:9042"
    environment:
      - CASSANDRA_CLUSTER_NAME=FleetCluster
      - CASSANDRA_DC=dc1
      - CASSANDRA_RACK=rack1
      - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
      - CASSANDRA_SEEDS=cassandra-dc1-node1,cassandra-dc2-node1
    volumes:
      - cassandra-dc1-node1-data:/var/lib/cassandra
      - ./cassandra/init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "cqlsh", "-e", "describe keyspaces"]
      interval: 30Continuer23:21s
timeout: 10s
retries: 5
Datacenter 1 - Node 2
cassandra-dc1-node2:
image: cassandra:4.1
container_name: cassandra-dc1-node2
hostname: cassandra-dc1-node2
networks:
- fleet-network
environment:
- CASSANDRA_CLUSTER_NAME=FleetCluster
- CASSANDRA_DC=dc1
- CASSANDRA_RACK=rack1
- CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
- CASSANDRA_SEEDS=cassandra-dc1-node1,cassandra-dc2-node1
volumes:
- cassandra-dc1-node2-data:/var/lib/cassandra
depends_on:
cassandra-dc1-node1:
condition: service_healthy
healthcheck:
test: ["CMD", "cqlsh", "-e", "describe keyspaces"]
interval: 30s
timeout: 10s
retries: 5
Datacenter 2 - Node 1
cassandra-dc2-node1:
image: cassandra:4.1
container_name: cassandra-dc2-node1
hostname: cassandra-dc2-node1
networks:
- fleet-network
environment:
- CASSANDRA_CLUSTER_NAME=FleetCluster
- CASSANDRA_DC=dc2
- CASSANDRA_RACK=rack1
- CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
- CASSANDRA_SEEDS=cassandra-dc1-node1,cassandra-dc2-node1
volumes:
- cassandra-dc2-node1-data:/var/lib/cassandra
depends_on:
cassandra-dc1-node1:
condition: service_healthy
healthcheck:
test: ["CMD", "cqlsh", "-e", "describe keyspaces"]
interval: 30s
timeout: 10s
retries: 5
Datacenter 2 - Node 2
cassandra-dc2-node2:
image: cassandra:4.1
container_name: cassandra-dc2-node2
hostname: cassandra-dc2-node2
networks:
- fleet-network
environment:
- CASSANDRA_CLUSTER_NAME=FleetCluster
- CASSANDRA_DC=dc2
- CASSANDRA_RACK=rack1
- CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
- CASSANDRA_SEEDS=cassandra-dc1-node1,cassandra-dc2-node1
volumes:
- cassandra-dc2-node2-data:/var/lib/cassandra
depends_on:
cassandra-dc2-node1:
condition: service_healthy
healthcheck:
test: ["CMD", "cqlsh", "-e", "describe keyspaces"]
interval: 30s
timeout: 10s
retries: 5
==================== ETL SERVICE ====================
etl-pipeline:
build:
context: ./etl
dockerfile: Dockerfile
container_name: fleet-etl
networks:
- fleet-network
environment:
- CASSANDRA_HOSTS=cassandra-dc1-node1,cassandra-dc1-node2
- CASSANDRA_KEYSPACE=fleet_iot
- CASSANDRA_DC=dc1
- ETL_MODE=streaming  # batch | streaming
- LOG_LEVEL=INFO
depends_on:
cassandra-dc1-node1:
condition: service_healthy
cassandra-dc1-node2:
condition: service_healthy
restart: unless-stopped
volumes:
- ./data:/app/data
==================== DASHBOARD SERVICE ====================
dashboard:
build:
context: ./dashboard
dockerfile: Dockerfile
container_name: fleet-dashboard
networks:
- fleet-network
ports:
- "8501:8501"
environment:
- CASSANDRA_HOSTS=cassandra-dc1-node1
- CASSANDRA_KEYSPACE=fleet_iot
depends_on:
cassandra-dc1-node1:
condition: service_healthy
etl-pipeline:
condition: service_started
restart: unless-stopped
healthcheck:
test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
interval: 30s
timeout: 10s
retries: 3
==================== CASSANDRA WEB UI (Optional) ====================
cassandra-web:
image: ipushc/cassandra-web
container_name: cassandra-web-ui
networks:
- fleet-network
ports:
- "8889:3000"
environment:
- CASSANDRA_HOST=cassandra-dc1-node1
- CASSANDRA_PORT=9042
- CASSANDRA_USER=cassandra
- CASSANDRA_PASSWORD=cassandra
depends_on:
cassandra-dc1-node1:
condition: service_healthy
networks:
fleet-network:
driver: bridge
volumes:
cassandra-dc1-node1-data:
cassandra-dc1-node2-data:
cassandra-dc2-node1-data:
cassandra-dc2-node2-data:

### Scripts d'Initialisation

#### `cassandra/init-scripts/01-create-schema.cql`
```sql
-- Création du keyspace avec réplication MDC
CREATE KEYSPACE IF NOT EXISTS fleet_iot
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 2,
  'dc2': 2
}
AND durable_writes = true;

USE fleet_iot;

-- Table 1: Devices par flotte
CREATE TABLE IF NOT EXISTS devices_by_fleet (
  fleet_id text,
  device_id text,
  model text,
  activated_at timestamp,
  status text,
  PRIMARY KEY ((fleet_id), device_id)
) WITH COMMENT = 'Liste des devices par flotte';

-- Table 2: État actuel des devices
CREATE TABLE IF NOT EXISTS latest_telemetry_by_device (
  device_id text PRIMARY KEY,
  last_ts timestamp,
  lat double,
  lon double,
  speed_kmh double,
  battery_pct int,
  temp_c double
) WITH COMMENT = 'Dernier état connu de chaque device';

-- Table 3: Historique journalier
CREATE TABLE IF NOT EXISTS telemetry_by_device_day (
  device_id text,
  day date,
  ts timestamp,
  lat double,
  lon double,
  speed_kmh double,
  battery_pct int,
  temp_c double,
  zone text,
  PRIMARY KEY ((device_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND COMMENT = 'Historique de télémétrie avec bucketing journalier'
  AND default_time_to_live = 2592000;  -- 30 jours

-- Table 4: Alertes par flotte/jour/sévérité
CREATE TABLE IF NOT EXISTS alerts_by_fleet_day (
  fleet_id text,
  day date,
  severity text,
  ts timestamp,
  device_id text,
  alert_type text,
  message text,
  resolved boolean,
  PRIMARY KEY ((fleet_id, day, severity), ts, device_id)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND COMMENT = 'Alertes avec filtrage par sévérité';

-- Table 5: Analytics agrégées
CREATE TABLE IF NOT EXISTS fleet_analytics_by_day (
  fleet_id text,
  day date,
  hour int,
  total_distance_km double,
  avg_speed_kmh double,
  alerts_count int,
  active_devices_count int,
  PRIMARY KEY ((fleet_id, day), hour)
) WITH COMMENT = 'Métriques agrégées par heure';

-- Insertion de données de test
INSERT INTO devices_by_fleet (fleet_id, device_id, model, activated_at, status)
VALUES ('fleet-001', 'device-001', 'GPS-X200', toTimestamp(now()), 'active');

INSERT INTO devices_by_fleet (fleet_id, device_id, model, activated_at, status)
VALUES ('fleet-001', 'device-002', 'GPS-X200', toTimestamp(now()), 'active');
```

### Dockerfiles

#### `etl/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Script de démarrage
CMD ["python", "etl_pipeline.py"]
```

#### `etl/requirements.txt`
```txt
cassandra-driver==3.28.0
pandas==2.1.0
python-dateutil==2.8.2
```

#### `dashboard/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Exposition du port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Démarrage de Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### `dashboard/requirements.txt`
```txt
streamlit==1.28.0
cassandra-driver==3.28.0
pandas==2.1.0
plotly==5.17.0
```

---

## Travail à Réaliser

### Phase 1 : Configuration de l'environnement (1h)

1. **Initialiser le projet**
   - Créer la structure de dossiers
   - Configurer `docker-compose.yml`
   - Créer les scripts d'initialisation Cassandra

2. **Démarrer le cluster**
```bash
   docker compose up -d
```

3. **Vérifier le cluster MDC**
```bash
   docker exec -it cassandra-dc1-node1 nodetool status
```
   
   Résultat attendu :
Datacenter: dc1
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address     Load       Tokens  Owns    Host ID   Rack
UN  172.18.0.2  X KB       256     50.0%   xxx-xxx   rack1
UN  172.18.0.3  X KB       256     50.0%   xxx-xxx   rack1
Datacenter: dc2
UN  172.18.0.4  X KB       256     50.0%   xxx-xxx   rack1
UN  172.18.0.5  X KB       256     50.0%   xxx-xxx   rack1

**Checkpoint ✅** : Tous les services sont "healthy"

---

### Phase 2 : Implémentation de l'ETL (3h)

#### Tâche 2.1 : Writer Cassandra

- [ ] Implémenter `CassandraWriter` avec:
  - Connexion au cluster MDC
  - Prepared statements
  - Méthode batch
  - Méthode asynchrone
  - Gestion d'erreurs

#### Tâche 2.2 : Générateur de données

- [ ] Créer `FleetDataGenerator` qui génère:
  - Données de télémétrie réalistes
  - Alertes basées sur seuils
  - Distribution temporelle cohérente

#### Tâche 2.3 : Pipeline ETL

- [ ] Implémenter les modes:
  - **Batch** : Chargement historique (10k+ records)
  - **Streaming** : Simulation temps réel (1 record/5s)
- [ ] Ajouter monitoring:
  - Latence d'insertion
  - Throughput (records/s)
  - Taux d'erreur

#### Tâche 2.4 : Tests de charge

- [ ] Benchmark du pipeline:
  - Mesurer le throughput maximum
  - Identifier les goulots d'étranglement
  - Tester la résilience (kill un nœud)

**Livrables** :
- Code ETL complet et fonctionnel
- Rapport de performance (latence P50/P95/P99)
- Log d'exécution avec 50k+ records insérés

---

### Phase 3 : Développement du Dashboard (3h)

#### Tâche 3.1 : Client Cassandra

- [ ] Implémenter toutes les méthodes de lecture
- [ ] Ajouter un système de cache (optionnel)
- [ ] Optimiser les requêtes multi-partitions

#### Tâche 3.2 : Page Real-Time

- [ ] Carte interactive avec position des devices
- [ ] Métriques en temps réel (vitesse, batterie, etc.)
- [ ] Tableau de bord avec filtres

#### Tâche 3.3 : Page Analytics

- [ ] Graphiques temporels (vitesse, température)
- [ ] Comparaisons entre devices
- [ ] Statistiques agrégées

#### Tâche 3.4 : Page Alerts

- [ ] Liste des alertes avec filtres
- [ ] Timeline visuelle
- [ ] Compteurs par sévérité

**Livrables** :
- Dashboard fonctionnel accessible sur http://localhost:8501
- Captures d'écran des 3 pages
- Documentation des requêtes CQL utilisées

---

### Phase 4 : Optimisations et Tests (2h)

#### Tâche 4.1 : Performance tuning

- [ ] Analyser les slow queries avec `TRACING ON`
- [ ] Optimiser les requêtes problématiques
- [ ] Implémenter pagination pour grandes datasets

#### Tâche 4.2 : Tests de résilience

- [ ] Tester la tolérance aux pannes:
```bash
  # Arrêter un nœud
  docker stop cassandra-dc1-node2
  
  # Vérifier que l'ETL et le dashboard fonctionnent toujours
  
  # Redémarrer le nœud
  docker start cassandra-dc1-node2
```

#### Tâche 4.3 : Documentation

- [ ] README.md avec instructions de déploiement
- [ ] Schéma d'architecture (diagrammes)
- [ ] Guide d'utilisation du dashboard
- [ ] Rapport d'analyse des performances

**Livrables** :
- Documentation complète
- Rapport de tests de résilience
- Recommandations d'amélioration

---

## Critères d'Évaluation

| Critère | Points | Détails |
|---------|--------|---------|
| **ETL Pipeline** | 30% | Fonctionnalité, performance, gestion d'erreurs |
| **Dashboard** | 25% | UI/UX, visualisations, requêtes optimisées |
| **Modèle Cassandra** | 20% | Schéma query-first, absence d'anti-patterns |
| **Déploiement Docker** | 15% | Configuration MDC, orchestration, healthchecks |
| **Tests & Résilience** | 10% | Tests de charge, tolérance aux pannes |

---

## Bonus (Points supplémentaires)

- [ ] Ajouter une API REST (FastAPI) entre Cassandra et le dashboard
- [ ] Implémenter un système de cache (Redis)
- [ ] Créer des alertes en temps réel (Kafka + Consumer)
- [ ] Ajouter des tests unitaires (pytest)
- [ ] Implémenter monitoring avec Prometheus + Grafana
- [ ] Géo-fencing: alertes automatiques si device sort d'une zone

---

## Ressources

### Documentation Officielle
- [Cassandra Documentation](https://cassandra.apache.org/doc/latest/)
- [Python Driver](https://docs.datastax.com/en/developer/python-driver/latest/)
- [Streamlit Docs](https://docs.streamlit.io/)

### Tutoriels Recommandés
- [Cassandra Data Modeling](https://www.datastax.com/learn/data-modeling-by-example)
- [Multi-Datacenter Replication](https://cassandra.apache.org/doc/latest/architecture/dynamo.html#multi-datacenter-replication)

---

## Planning Suggéré

| Jour | Activités |
|------|-----------|
| J1 | Setup environnement + ETL basique |
| J2 | ETL avancé + Tests de charge |
| J3 | Dashboard Real-Time + Analytics |
| J4 | Alerts + Optimisations + Tests résilience |
| J5 | Documentation + Présentation |

---

## Rendu Final

### Structure du livrable
fleet-tracing-project.zip
├── README.md
├── RAPPORT.pdf
├── docker-compose.yml
├── cassandra/
├── etl/
├── dashboard/
├── screenshots/
│   ├── realtime-page.png
│   ├── analytics-page.png
│   └── alerts-page.png
└── docs/
├── architecture.png
├── performance-report.pdf
└── user-guide.md

### Présentation (15 min)

1. **Démonstration live** (7 min)
   - Démarrage du système
   - ETL en action
   - Navigation dans le dashboard

2. **Architecture technique** (5 min)
   - Schéma du système
   - Choix de modélisation Cassandra
   - Stratégies d'optimisation

3. **Résultats & Perspectives** (3 min)
   - Métriques de performance
   - Défis rencontrés
   - Améliorations futures

---

**Bon courage ! 🚀**

*Date de rendu : [À définir]*  
*Contact : [Votre email]*
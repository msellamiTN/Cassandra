# 🐳 CQL Web Editor - Docker Workshop

Ce projet permet de lancer un **éditeur CQL web personnalisé** avec **Apache Cassandra** en utilisant **Docker Compose**.

👉 Solution **clé en main**, compatible **Windows, Linux et macOS (y compris Apple Silicon M1/M2/M3)**.

---

## 🎯 Objectifs

- Démarrer rapidement un éditeur CQL web sans dépendances locales
- Éviter les problèmes Java / ARM / Rosetta
- Fournir un environnement reproductible pour **TP, formations et démonstrations**

---

## 📦 Prérequis

- Docker **20+**
- Docker Compose **v2**
- Ports libres :
  - `8889` (CQL Web Editor UI)
  - `9042` (Cassandra)

Vérification :

```bash
docker --version
docker compose version
```

---

## 📁 Structure du projet

```text
.
├── docker-compose.yml
├── README.md
├── cql-scripts/
│   ├── README.md
│   └── sample.cql
└── gui-cql/
    ├── Dockerfile
    ├── main.py
    ├── requirements.txt
    ├── sample.cql
    └── templates/
        └── index.html
```

---

## ⬇️ Récupération du projet (Git)

Cloner le dépôt Git officiel de l’atelier :

```bash
git clone https://github.com/msellamiTN/Cassandra.git
cd Cassandra
```

---

## ▶️ Démarrage rapide

Dans le dossier du projet :

```bash
docker compose up -d --build
```

Vérifier l’état des services :

```bash
docker compose ps
```

Suivre les logs de l'éditeur CQL :

```bash
docker compose logs -f cql-gui
```

---

## 🌐 Accès à l'éditeur CQL Web

Ouvrir un navigateur :

```
http://localhost:8889
```

---

## 🔌 Configuration de la connexion Cassandra (dans l'interface web)

1. Ouvrir l'onglet **Configuration**
2. Renseigner (valeurs par défaut déjà configurées) :

| Champ | Valeur |
|------|-------|
| Hosts | cassandra |
| Port | 9042 |
| Username | (vide) |
| Password | (vide) |
| Keyspace | (optionnel) |

3. **Test Connection**
4. **Save**

---

## 🧪 Test rapide (CQL)

Créer un notebook CQL et exécuter :

```sql
CREATE KEYSPACE demo
WITH replication = {'class':'SimpleStrategy','replication_factor':1};

USE demo;

CREATE TABLE users (
  id UUID PRIMARY KEY,
  name text,
  email text
);

INSERT INTO users (id, name, email)
VALUES (uuid(), 'Alice', 'alice@mail.com');

SELECT * FROM users;
```

---
## 📝 Gestion des scripts CQL

L'interface web permet de sauvegarder et charger des scripts CQL :

- **Sauvegarder** : Utilisez le bouton "Save Script" pour enregistrer votre code CQL
- **Charger** : Utilisez le bouton "Load Script" pour ouvrir un script existant
- **Scripts stockés** : Les fichiers sont sauvegardés dans le dossier `cql-scripts/` du projet
- **Persistance** : Les scripts sont conservés même après redémarrage des conteneurs

---
## 🛑 Arrêt de l’environnement

```bash
docker compose down
```

Arrêt + suppression des volumes :

```bash
docker compose down -v
```

---

## 🧠 Notes importantes

- L'application web est construite avec **FastAPI** et utilise le driver Python Cassandra
- L'interface permet l'exécution de requêtes CQL multiples (séparées par des points-virgules)
- Les résultats des SELECT sont affichés dans des tableaux HTML
- Navigation possible dans les keyspaces et tables via l'interface
- **Gestion des scripts** : Sauvegarde et chargement de scripts CQL dans le dossier monté

---

## 🚀 Extensions possibles

- Connexion **Astra DB** (Secure Connect Bundle)
- Atelier **CQL avancé**
- Comparaison avec outils modernes (Astra UI, cqlsh, notebooks)
- Intégration Kafka / Spark (legacy DSE)

---

## 📜 Licence

L'utilisation d'Apache Cassandra est soumise aux conditions de licence Apache 2.0.

---

👨‍🏫 *Document prêt pour atelier académique ou formation professionnelle.*


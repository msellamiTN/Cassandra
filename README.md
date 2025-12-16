# 🐳 DataStax Studio 6.8.32 – Docker Workshop

Ce projet permet de lancer **DataStax Studio 6.8.32** avec **Apache Cassandra** en utilisant **Docker Compose**.

👉 Solution **clé en main**, compatible **Windows, Linux et macOS (y compris Apple Silicon M1/M2/M3)**.

---

## 🎯 Objectifs

- Démarrer rapidement DataStax Studio sans dépendances locales
- Éviter les problèmes Java / ARM / Rosetta
- Fournir un environnement reproductible pour **TP, formations et démonstrations**

---

## 📦 Prérequis

- Docker **20+**
- Docker Compose **v2**
- Ports libres :
  - `9091` (Studio UI)
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
└── README.md
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
docker compose up -d
```

Vérifier l’état des services :

```bash
docker compose ps
```

Suivre les logs de Studio :

```bash
docker logs -f datastax-studio
```

---

## 🌐 Accès à DataStax Studio

Ouvrir un navigateur :

```
http://localhost:9091
```

---

## 🔌 Connexion à Cassandra (dans Studio)

1. Ouvrir **Connections → Add connection**
2. Renseigner :

| Champ | Valeur |
|------|-------|
| Name | Local Cassandra |
| Host | cassandra |
| Port | 9042 |
| Auth | None |
| Datacenter | dc1 |

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

- DataStax Studio 6.x est **EOL (End Of Life)**
- L’image est exécutée en **linux/amd64** pour compatibilité Apple Silicon
- Usage recommandé : **formation, exploration, legacy**

---

## 🚀 Extensions possibles

- Connexion **Astra DB** (Secure Connect Bundle)
- Atelier **CQL avancé**
- Comparaison avec outils modernes (Astra UI, cqlsh, notebooks)
- Intégration Kafka / Spark (legacy DSE)

---

## 📜 Licence

L’utilisation de DataStax Studio est soumise aux conditions de licence DataStax.

---

👨‍🏫 *Document prêt pour atelier académique ou formation professionnelle.*


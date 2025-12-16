## CQL-gui – Éditeur CQL Web pour Cassandra

Cette application fournit une **interface Web simple** (FastAPI) pour exécuter des requêtes **CQL** sur un cluster **Apache Cassandra**.

- **Backend** : `FastAPI` + `cassandra-driver`
- **Frontend** : page HTML unique (`templates/index.html`) avec un éditeur CQL basique
- **Déploiement** : exécutable directement en Python ou via un conteneur Docker

---

### 1. Prérequis

- Python ≥ 3.10
- Accès à un cluster **Cassandra** (local ou distant)
- (Optionnel) Docker / Docker Compose pour le déploiement conteneurisé

---

### 2. Installation locale (sans Docker)

Depuis le dossier `CQL-gui` :

```bash
pip install -r requirements.txt
```

Variables d’environnement possibles pour la connexion Cassandra :

- `CASSANDRA_HOSTS` : liste d’hôtes séparés par des virgules (par défaut `cassandra`)
- `CASSANDRA_PORT` : port CQL, par défaut `9042`
- `CASSANDRA_USER` : utilisateur (optionnel)
- `CASSANDRA_PASSWORD` : mot de passe (optionnel)
- `CASSANDRA_KEYSPACE` : keyspace par défaut (optionnel)

Exemple sous PowerShell :

```powershell
$env:CASSANDRA_HOSTS="127.0.0.1"
$env:CASSANDRA_PORT="9042"
$env:CASSANDRA_KEYSPACE="mon_keyspace"
uvicorn main:app --reload
```

Lancement du serveur :

```bash
uvicorn main:app --reload
```

Ouvrir ensuite le navigateur sur :

```text
http://127.0.0.1:8000
```

---

### 3. Utilisation de l’interface Web

Sur la page principale :

- Saisir une requête CQL dans la zone de texte, par exemple :
  - `SELECT * FROM system.local;`
  - `INSERT INTO ...`
- Cliquer sur **Exécuter** (ou utiliser `Ctrl+Enter`).
- Les résultats :
  - Pour un `SELECT`, un **tableau** est affiché avec les colonnes et lignes retournées.
  - Pour les autres requêtes (INSERT/UPDATE/DELETE/DDL), un message de succès est affiché.

En cas d’erreur (Cassandra, syntaxe CQL, connexion), le message d’erreur est affiché sous l’éditeur.

---

### 4. Exécution avec Docker

Depuis le dossier `CQL-gui` :

```bash
docker build -t cql-gui .
docker run --rm -p 8000:8000 `
  -e CASSANDRA_HOSTS=host_cassandra `
  -e CASSANDRA_PORT=9042 `
  -e CASSANDRA_KEYSPACE=mon_keyspace `
  cql-gui
```

Adapter `host_cassandra` pour pointer vers ton cluster (par ex. `host.docker.internal` si Cassandra tourne sur la machine hôte).

Accès à l’interface :

```text
http://localhost:8000
```

---

### 5. Points d’entrée API (si tu veux intégrer ailleurs)

- `GET /`  
  Renvoie la page HTML de l’éditeur CQL.

- `POST /execute`  
  Corps JSON :
  ```json
  { "query": "SELECT * FROM system.local;" }
  ```
  Réponse JSON :
  - Succès SELECT :
    ```json
    {
      "success": true,
      "type": "select",
      "columns": ["col1", "col2"],
      "rows": [
        { "col1": "val1", "col2": "val2" }
      ]
    }
    ```
  - Succès autre requête :
    ```json
    {
      "success": true,
      "type": "other",
      "message": "Requête exécutée avec succès."
    }
    ```
  - Erreur :
    ```json
    {
      "success": false,
      "error": "message d’erreur..."
    }
    ```

---

### 6. Personnalisation

- Tu peux modifier le style de l’interface dans `templates/index.html`.
- Pour un éditeur plus avancé (coloration syntaxique CQL), tu peux intégrer **CodeMirror** ou **Monaco Editor** dans la même page et garder les mêmes endpoints `/execute`.



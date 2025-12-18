# Atelier étudiant — CQL avancé — Fleet Tracing (IoT) — 4h

## Énoncé

Tu rejoins une équipe Data/IoT qui doit construire un backend Cassandra pour le **suivi de flotte** (bus/camions). Les données de télémétrie arrivent en continu, et l’application doit servir des lectures rapides (dernier état, historique du jour, alertes).

Ton travail : **concevoir le modèle Cassandra “query‑first”** (1 table par requête) et valider tes choix par des requêtes CQL.

## Objectifs

- Modéliser **query‑first** (Cassandra) : 1 table par besoin de lecture
- Savoir choisir :
  - Partition key vs clustering columns
  - Bucketing temporel (jour) pour éviter les partitions infinies
  - Table “latest state” pour des lectures très fréquentes
  - Table dédiée pour l’alerting
- Identifier et corriger les anti‑patterns :
  - `ALLOW FILTERING`
  - partitions trop grosses / hot partitions
  - TTL / tombstones
  - BATCH et LWT (quand éviter / quand justifier)

## Prérequis

- Docker + Docker Compose v2
- Ports libres :
  - `8889` (UI CQL)
  - `9042` (Cassandra)
  - `8888` (Jupyter)

## Mise en place (à faire)

1. Démarrer l’environnement (depuis la racine du repo)

```bash
docker compose up -d --build
```

1. Ouvrir les interfaces

- UI CQL : <http://localhost:8889>
- Jupyter : <http://localhost:8888> (token = `my-token`)

1. Checkpoint ✅ — Les services sont prêts

```bash
docker compose ps
```

Attendu : Cassandra est “healthy” et Jupyter/UI sont “Up”.

## Supports

- Notebook **Étudiant** : `Atelier_Fleet_IoT_Student.ipynb`
- Notebook **Formateur** : `Atelier_Fleet_IoT_Instructor.ipynb`

## Travail demandé (pas à pas)

### T1 — Lire les besoins (User Stories)

Dans le notebook étudiant, relève les requêtes attendues :

- Lire le **dernier point** pour un device
- Lire l’**historique du jour** pour un device (du plus récent au plus ancien)
- Lire les **alertes** d’une flotte pour une journée, filtrées par sévérité
- Lire une vue “flotte/jour” (analytics / agrégations simples côté client)

Livrable : une liste courte “US → requête CQL” (même en pseudo‑CQL).

### T2 — Proposer le schéma (1 table par requête)

1. Dessine pour chaque table :

- la partition key
- les clustering columns (+ ordre)
- une justification en 2–3 lignes

1. Implémente le schéma en CQL (dans l’UI CQL ou via le notebook).

Checkpoint ✅ : tu peux créer les tables sans erreur, et `DESCRIBE TABLE <table>;` correspond à ton design.

### T3 — Insérer un mini jeu de données

Insère quelques devices et points de télémétrie (au moins 2 devices, sur 1 journée) + au moins 1 alerte.

Checkpoint ✅ : tes requêtes de lecture retournent bien des lignes.

### T4 — Valider les performances “logiques” (requêtes autorisées)

Exécute les requêtes principales **sans** `ALLOW FILTERING`.

Question : quelles colonnes doivent absolument apparaître dans la clause `WHERE` pour que la lecture reste “Cassandra‑friendly” ?

### T5 — Anti‑patterns et corrections

1. Construis volontairement une requête qui te pousse à utiliser `ALLOW FILTERING`.
1. Explique pourquoi c’est un problème (partition scan, latence, charge).
1. Propose un redesign (nouvelle table) qui supprime `ALLOW FILTERING`.

Livrable : 1 anti‑pattern + 1 correction (schéma + requête).

## Bonus (si tu avances vite)

- Ajouter TTL sur une table (et expliquer l’impact : tombstones, compaction).
- Expliquer quand un `BATCH` est acceptable (ou non) dans ton cas.

## Rendu attendu

- Le notebook étudiant complété
- Le schéma final (tables) + 3–5 requêtes de validation

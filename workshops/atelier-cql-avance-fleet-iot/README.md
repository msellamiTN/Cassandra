# Atelier CQL avancé — Fleet Tracing (IoT) — 4h

Ce dossier contient les supports pour un atelier **Cassandra/CQL avancé** sur un cas d’usage réaliste de **Fleet Tracking / IoT**.

## Objectifs

- Modéliser **query-first** (Cassandra): 1 table par besoin de lecture
- Comprendre et pratiquer:
  - Partition key vs clustering columns
  - Bucketing temporel (jour / tranche) pour éviter les partitions infinies
  - Tables "latest state" pour des lectures ultra fréquentes
  - Tables dédiées pour alerting et filtres métier
- Voir les **pitfalls** et leurs corrections:
  - `ALLOW FILTERING`
  - partitions trop grosses / hot partitions
  - TTL / tombstones
  - BATCH et LWT: quand et pourquoi (avec prudence)

## Pré-requis

- Docker + Docker Compose v2
- Ports libres:
  - `8889` (UI CQL)
  - `9042` (Cassandra)
  - `8888` (Jupyter)

## Démarrage

Depuis la racine du repo:

```bash
docker compose up -d --build
```

Accès:

- UI CQL: http://localhost:8889
- Jupyter: http://localhost:8888 (token = `my-token`)

## Supports

- **Notebook Étudiant**: `Atelier_Fleet_IoT_Student.ipynb`
- **Notebook Formateur** (corrigé + explications): `Atelier_Fleet_IoT_Instructor.ipynb`

## Conseils d’animation (4h)

- **H1 (A)**: US1/US2 → `latest_telemetry_by_device` + `telemetry_by_device_day` (clés, ordering, ranges)
- **H2 (A)**: US3/US4 → `alerts_by_fleet_day` (+ option zone/bucket)
- **H3 (B)**: anti-patterns → table naïve + `ALLOW FILTERING` → redesign `telemetry_by_fleet_day`
- **H4 (B)**: TTL/tombstones + BATCH/LWT + checklist finale

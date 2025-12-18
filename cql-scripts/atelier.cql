CREATE KEYSPACE IF NOT EXISTS atelier
WITH REPLICATION = {'class': 'NetworkTopologyStrategy', 'dc1': 2, 'dc2': 2}
AND durable_writes = true;

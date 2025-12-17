# CQL Scripts Directory

This directory contains CQL (Cassandra Query Language) scripts that are mounted into the CQL Web Editor container.

## Usage

- Place your `.cql` files in this directory
- They will be accessible from within the container at `/app/cql-scripts`
- The web interface can load and execute these scripts
- Files are persisted on the host machine

## Example

See `sample.cql` for example CQL commands including:
- Keyspace creation
- Table creation
- Data insertion and selection
- Index creation
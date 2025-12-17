# Cassandra CQL GUI - AI Agent Instructions

## Project Overview
This is a Docker Compose project providing a web-based CQL editor for Apache Cassandra. It consists of:
- **Cassandra 4.1** database service (port 9042)
- **FastAPI web app** (`gui-cql/`) serving a CQL editor interface (port 8889)

The web app allows users to configure Cassandra connections, browse keyspaces/tables, and execute CQL queries with results displayed in tables.

## Architecture
- **Backend**: FastAPI with Cassandra Python driver
- **Frontend**: Jinja2 templates with CodeMirror editor and vanilla JavaScript
- **Data Flow**: Web UI → FastAPI endpoints → Cassandra driver → Cassandra DB
- **Connection Management**: Global cluster/session objects initialized on startup, reconnectable via API

## Key Components
- `main.py`: FastAPI app with endpoints for config, status, keyspaces, tables, and query execution
- `templates/index.html`: Single-page app with tabs for configuration and query editor
- `docker-compose.yml`: Orchestrates Cassandra and web app services
- `sample.cql`: Example CQL commands for testing

## Developer Workflows
### Local Development
```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f cql-gui

# Access web UI
open http://localhost:8889

# Stop services
docker compose down
```

### Adding New Features
- Extend FastAPI endpoints in `main.py` (follow existing patterns with error handling)
- Update HTML/JS in `templates/index.html` for UI changes
- Add environment variables to `docker-compose.yml` and `main.py` for new config options

## Code Patterns
### Cassandra Connection
- Use environment variables for initial config (CASSANDRA_HOSTS, CASSANDRA_PORT, etc.)
- Implement reconnect logic in `reconnect_cassandra()` function
- Check `is_session_active()` before operations

### Query Execution
- Parse multi-statement queries with `split_queries()` (handles semicolons and strings)
- Remove CQL comments with `remove_comments()` before parsing
- Return structured results: columns + rows for SELECT, success message for DDL/DML

### API Design
- GET `/api/config`: Return current connection config and status
- POST `/api/config`: Update and test connection
- GET `/api/status`: Cluster metadata and connection health
- GET `/api/keyspaces`: List available keyspaces
- GET `/api/keyspaces/{name}/tables`: List tables with column metadata
- POST `/execute`: Execute CQL query/queries

### Error Handling
- Use HTTPException for API errors with descriptive messages
- Return JSON with `success: false` and `error` field for query failures
- Handle connection failures gracefully in UI

### UI Patterns
- Tab-based interface with JavaScript show/hide logic
- CodeMirror for CQL editing with Monokai theme
- AJAX calls to `/execute` with loading indicators
- Display results in HTML tables with column headers

## Dependencies
- **FastAPI**: Web framework
- **cassandra-driver**: Database connectivity
- **Jinja2**: Template rendering
- **uvicorn**: ASGI server
- **CodeMirror**: In-browser code editor (via CDN)

## Testing
- Use `sample.cql` for manual testing of CQL operations
- Test connection reconfiguration via UI
- Verify multi-query execution (semicolon-separated)

## Deployment
- Built as Docker image from `gui-cql/Dockerfile`
- Depends on healthy Cassandra service
- Exposed on port 8889 internally, mapped to host port 8889</content>
<parameter name="filePath">d:\Formation\Wevops\ABData-Fitec\Cassandra\Cassandra\.github\copilot-instructions.md
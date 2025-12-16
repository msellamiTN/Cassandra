import os
from typing import Any, Dict, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


# -------------------------------
# Configuration Cassandra
# -------------------------------
CASSANDRA_CONTACT_POINTS = os.getenv("CASSANDRA_HOSTS", "cassandra").split(",")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USER = os.getenv("CASSANDRA_USER", "")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "")

app = FastAPI(title="CQL Web Editor")

# Static & templates
if not os.path.isdir("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class CqlRequest(BaseModel):
    query: str


cluster: Cluster | None = None
session = None


@app.on_event("startup")
def on_startup() -> None:
    global cluster, session

    if CASSANDRA_USER and CASSANDRA_PASSWORD:
        auth = PlainTextAuthProvider(
            username=CASSANDRA_USER,
            password=CASSANDRA_PASSWORD,
        )
        cluster = Cluster(
            contact_points=CASSANDRA_CONTACT_POINTS,
            port=CASSANDRA_PORT,
            auth_provider=auth,
        )
    else:
        cluster = Cluster(
            contact_points=CASSANDRA_CONTACT_POINTS,
            port=CASSANDRA_PORT,
        )

    session = cluster.connect()
    if CASSANDRA_KEYSPACE:
        session.set_keyspace(CASSANDRA_KEYSPACE)


@app.on_event("shutdown")
def on_shutdown() -> None:
    global cluster, session
    if session:
        session.shutdown()
    if cluster:
        cluster.shutdown()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.post("/execute")
async def execute_cql(payload: CqlRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="La requête CQL est vide.")

    try:
        result = session.execute(payload.query)

        if result.column_names:
            rows: List[Dict[str, Any]] = [dict(row._asdict()) for row in result]
            return {
                "success": True,
                "type": "select",
                "columns": result.column_names,
                "rows": rows,
            }
        else:
            return {
                "success": True,
                "type": "other",
                "message": "Requête exécutée avec succès.",
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }



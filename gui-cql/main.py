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


class ConfigRequest(BaseModel):
    hosts: str
    port: int
    username: str = ""
    password: str = ""
    keyspace: str = ""


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


def reconnect_cassandra(hosts: str, port: int, username: str = "", password: str = "", keyspace: str = "") -> None:
    """Ferme la connexion existante et se reconnecte avec les nouveaux paramètres."""
    global cluster, session
    
    if session:
        try:
            session.shutdown()
        except:
            pass
    if cluster:
        try:
            cluster.shutdown()
        except:
            pass
    
    contact_points = [h.strip() for h in hosts.split(",") if h.strip()]
    if not contact_points:
        raise ValueError("Au moins un hôte doit être spécifié.")
    
    if username and password:
        auth = PlainTextAuthProvider(username=username, password=password)
        cluster = Cluster(contact_points=contact_points, port=port, auth_provider=auth)
    else:
        cluster = Cluster(contact_points=contact_points, port=port)
    
    session = cluster.connect()
    if keyspace:
        session.set_keyspace(keyspace)


@app.get("/api/config")
async def get_config():
    """Retourne la configuration actuelle et l'état de connexion."""
    global cluster, session
    return {
        "hosts": ",".join(CASSANDRA_CONTACT_POINTS),
        "port": CASSANDRA_PORT,
        "username": CASSANDRA_USER,
        "keyspace": CASSANDRA_KEYSPACE,
        "connected": session is not None and not session.is_shutdown if session else False,
    }


@app.post("/api/config")
async def update_config(payload: ConfigRequest):
    """Met à jour la configuration et teste la connexion."""
    try:
        reconnect_cassandra(
            hosts=payload.hosts,
            port=payload.port,
            username=payload.username,
            password=payload.password,
            keyspace=payload.keyspace,
        )
        return {"message": "Connexion réussie au cluster Cassandra."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de connexion : {str(e)}")


@app.post("/execute")
async def execute_cql(payload: CqlRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="La requête CQL est vide.")

    if not session or session.is_shutdown:
        raise HTTPException(status_code=503, detail="Pas de connexion active à Cassandra. Veuillez configurer le cluster d'abord.")

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



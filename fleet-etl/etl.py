import os
import random
import time
from datetime import date, datetime, timezone

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


CASSANDRA_CONTACT_POINTS = _env_list("CASSANDRA_HOSTS", "cassandra,cassandra-dc2-1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USER = os.getenv("CASSANDRA_USER", "")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "atelier")

FLEETS = _env_list("ETL_FLEETS", "FLEET_PARIS,FLEET_LYON")
DEVICES_PER_FLEET = int(os.getenv("ETL_DEVICES_PER_FLEET", "5"))
INTERVAL_MS = int(os.getenv("ETL_INTERVAL_MS", "500"))
ALERT_PROB = float(os.getenv("ETL_ALERT_PROB", "0.03"))


def _connect():
    if CASSANDRA_USER and CASSANDRA_PASSWORD:
        auth = PlainTextAuthProvider(username=CASSANDRA_USER, password=CASSANDRA_PASSWORD)
        cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT, auth_provider=auth)
    else:
        cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT)
    session = cluster.connect()
    return cluster, session


def _ensure_keyspace(session):
    session.execute(
        f"CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE} WITH REPLICATION = {{'class':'NetworkTopologyStrategy','dc1':2,'dc2':2}} AND durable_writes = true"
    )


def _ensure_tables(session):
    session.execute(f"USE {CASSANDRA_KEYSPACE}")

    session.execute(
        "CREATE TABLE IF NOT EXISTS devices_by_fleet (fleet_id text, device_id text, model text, activated_at timestamp, PRIMARY KEY ((fleet_id), device_id))"
    )

    session.execute(
        "CREATE TABLE IF NOT EXISTS latest_telemetry_by_device (device_id text PRIMARY KEY, last_ts timestamp, lat double, lon double, speed_kmh double, battery_pct int, temp_c double)"
    )

    session.execute(
        "CREATE TABLE IF NOT EXISTS telemetry_by_device_day (device_id text, day date, ts timestamp, lat double, lon double, speed_kmh double, battery_pct int, temp_c double, zone text, PRIMARY KEY ((device_id, day), ts)) WITH CLUSTERING ORDER BY (ts DESC)"
    )

    session.execute(
        "CREATE TABLE IF NOT EXISTS alerts_by_fleet_day (fleet_id text, day date, severity text, ts timestamp, device_id text, alert_type text, message text, PRIMARY KEY ((fleet_id, day, severity), ts, device_id)) WITH CLUSTERING ORDER BY (ts DESC)"
    )

    session.execute(
        "CREATE TABLE IF NOT EXISTS telemetry_by_fleet_day (fleet_id text, day date, ts timestamp, device_id text, lat double, lon double, speed_kmh double, battery_pct int, temp_c double, zone text, PRIMARY KEY ((fleet_id, day), ts, device_id)) WITH CLUSTERING ORDER BY (ts DESC)"
    )


def _fleet_center(fleet_id: str) -> tuple[float, float]:
    if fleet_id == "FLEET_PARIS":
        return 48.8566, 2.3522
    if fleet_id == "FLEET_LYON":
        return 45.7640, 4.8357
    return 46.2276, 2.2137


def _device_prefix(fleet_id: str) -> str:
    if fleet_id == "FLEET_PARIS":
        return "BUS"
    if fleet_id == "FLEET_LYON":
        return "TRUCK"
    return "VEH"


def _build_devices() -> dict[str, list[str]]:
    m: dict[str, list[str]] = {}
    for fleet in FLEETS:
        prefix = _device_prefix(fleet)
        m[fleet] = [f"{prefix}-{i:03d}" for i in range(1, DEVICES_PER_FLEET + 1)]
    return m


def main():
    random.seed(int(os.getenv("ETL_SEED", "0")) or None)

    cluster, session = _connect()
    try:
        _ensure_keyspace(session)
        _ensure_tables(session)

        session.execute(f"USE {CASSANDRA_KEYSPACE}")

        ins_device = session.prepare(
            "INSERT INTO devices_by_fleet (fleet_id, device_id, model, activated_at) VALUES (?, ?, ?, ?)"
        )
        ins_latest = session.prepare(
            "INSERT INTO latest_telemetry_by_device (device_id, last_ts, lat, lon, speed_kmh, battery_pct, temp_c) VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        ins_tel_dev = session.prepare(
            "INSERT INTO telemetry_by_device_day (device_id, day, ts, lat, lon, speed_kmh, battery_pct, temp_c, zone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        ins_tel_fleet = session.prepare(
            "INSERT INTO telemetry_by_fleet_day (fleet_id, day, ts, device_id, lat, lon, speed_kmh, battery_pct, temp_c, zone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        ins_alert = session.prepare(
            "INSERT INTO alerts_by_fleet_day (fleet_id, day, severity, ts, device_id, alert_type, message) VALUES (?, ?, ?, ?, ?, ?, ?)"
        )

        devices_by_fleet = _build_devices()
        state: dict[str, dict[str, float]] = {}

        now = datetime.now(timezone.utc)
        for fleet_id, devs in devices_by_fleet.items():
            for device_id in devs:
                lat0, lon0 = _fleet_center(fleet_id)
                state[device_id] = {
                    "lat": lat0 + random.uniform(-0.02, 0.02),
                    "lon": lon0 + random.uniform(-0.02, 0.02),
                    "battery": float(random.randint(60, 100)),
                }
                session.execute(ins_device, (fleet_id, device_id, "GPS-TX-1", now))

        while True:
            fleet_id = random.choice(FLEETS)
            device_id = random.choice(devices_by_fleet[fleet_id])

            ts = datetime.now(timezone.utc)
            day = date.fromisoformat(ts.date().isoformat())

            s = state[device_id]
            s["lat"] = float(s["lat"]) + random.uniform(-0.0015, 0.0015)
            s["lon"] = float(s["lon"]) + random.uniform(-0.0015, 0.0015)
            s["battery"] = max(0.0, float(s["battery"]) - random.uniform(0.0, 0.05))

            speed = max(0.0, random.gauss(35.0, 12.0))
            temp_c = random.gauss(28.0, 4.0)
            if random.random() < 0.01:
                temp_c += random.uniform(10.0, 20.0)

            zone = "PARIS-A" if fleet_id == "FLEET_PARIS" else "LYON-A"

            session.execute(ins_tel_dev, (device_id, day, ts, s["lat"], s["lon"], speed, int(s["battery"]), temp_c, zone))
            session.execute(ins_tel_fleet, (fleet_id, day, ts, device_id, s["lat"], s["lon"], speed, int(s["battery"]), temp_c, zone))
            session.execute(ins_latest, (device_id, ts, s["lat"], s["lon"], speed, int(s["battery"]), temp_c))

            if temp_c >= 40.0 or random.random() < ALERT_PROB:
                severity = "HIGH" if temp_c >= 40.0 else random.choice(["LOW", "MED", "HIGH"])
                alert_type = "TEMP_HIGH" if temp_c >= 40.0 else "GEOFENCE"
                message = "Température > 40C" if temp_c >= 40.0 else "Anomalie détectée"
                session.execute(ins_alert, (fleet_id, day, severity, ts, device_id, alert_type, message))

            time.sleep(max(0.05, INTERVAL_MS / 1000.0))
    finally:
        try:
            session.shutdown()
        except Exception:
            pass
        try:
            cluster.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()

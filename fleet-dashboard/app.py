import os
from datetime import date

import gradio as gr
import pandas as pd
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


CASSANDRA_CONTACT_POINTS = _env_list("CASSANDRA_HOSTS", "cassandra")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_USER = os.getenv("CASSANDRA_USER", "")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "atelier")


_cluster: Cluster | None = None
_session = None


def _connect() -> None:
    global _cluster, _session

    if _session is not None:
        try:
            _session.shutdown()
        except Exception:
            pass
        _session = None

    if _cluster is not None:
        try:
            _cluster.shutdown()
        except Exception:
            pass
        _cluster = None

    if CASSANDRA_USER and CASSANDRA_PASSWORD:
        auth = PlainTextAuthProvider(username=CASSANDRA_USER, password=CASSANDRA_PASSWORD)
        _cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT, auth_provider=auth)
    else:
        _cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT)

    _session = _cluster.connect()
    if CASSANDRA_KEYSPACE:
        _session.set_keyspace(CASSANDRA_KEYSPACE)


def _ensure_session():
    if _session is None:
        _connect()
    return _session


def _rows_to_df(rows) -> pd.DataFrame:
    rows = list(rows)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r._asdict()) for r in rows])


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except Exception as exc:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD") from exc


def load_devices(fleet_id: str):
    try:
        session = _ensure_session()
        if not fleet_id.strip():
            return pd.DataFrame(), gr.update(choices=[], value=None), "fleet_id is required"

        rs = session.execute(
            "SELECT device_id, model, activated_at FROM devices_by_fleet WHERE fleet_id=%s",
            (fleet_id.strip(),),
        )
        df = _rows_to_df(rs)
        device_ids = df["device_id"].tolist() if "device_id" in df.columns else []
        return df, gr.update(choices=device_ids, value=(device_ids[0] if device_ids else None)), ""
    except Exception as exc:
        return pd.DataFrame(), gr.update(choices=[], value=None), str(exc)


def load_latest(device_id: str):
    try:
        session = _ensure_session()
        if not device_id.strip():
            return pd.DataFrame(), "device_id is required"

        rs = session.execute(
            "SELECT device_id, last_ts, lat, lon, speed_kmh, battery_pct, temp_c FROM latest_telemetry_by_device WHERE device_id=%s",
            (device_id.strip(),),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def load_alerts(fleet_id: str, day_str: str, severity: str):
    try:
        session = _ensure_session()
        if not fleet_id.strip():
            return pd.DataFrame(), "fleet_id is required"

        if not day_str.strip():
            return pd.DataFrame(), "day is required"

        day_value = _parse_iso_date(day_str)

        rs = session.execute(
            "SELECT ts, device_id, alert_type, message FROM alerts_by_fleet_day WHERE fleet_id=%s AND day=%s AND severity=%s LIMIT 200",
            (fleet_id.strip(), day_value, severity),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def load_telemetry(device_id: str, day_str: str, limit: int):
    try:
        session = _ensure_session()
        if not device_id.strip():
            return pd.DataFrame(), "device_id is required"
        if not day_str.strip():
            return pd.DataFrame(), "day is required"

        day_value = _parse_iso_date(day_str)
        limit_value = int(limit)
        if limit_value < 1:
            limit_value = 1
        if limit_value > 500:
            limit_value = 500

        rs = session.execute(
            f"SELECT ts, lat, lon, speed_kmh, battery_pct, temp_c, zone FROM telemetry_by_device_day WHERE device_id=%s AND day=%s LIMIT {limit_value}",
            (device_id.strip(), day_value),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


with gr.Blocks(title="Fleet IoT Dashboard") as demo:
    gr.Markdown("# Fleet IoT Dashboard\nConnects to Cassandra and provides simple views for the Fleet Tracking workshop.")

    conn = gr.Textbox(
        label="Connection",
        value=f"hosts={','.join(CASSANDRA_CONTACT_POINTS)} port={CASSANDRA_PORT} keyspace={CASSANDRA_KEYSPACE}",
        interactive=False,
    )

    with gr.Tabs():
        with gr.Tab("Devices"):
            fleet_id = gr.Textbox(label="fleet_id", value="FLEET_PARIS")
            btn_devices = gr.Button("Load devices")
            devices_df = gr.Dataframe(label="devices_by_fleet")
            devices_err = gr.Textbox(label="error", interactive=False)

        with gr.Tab("Latest"):
            device_id = gr.Dropdown(label="device_id", choices=[])
            btn_latest = gr.Button("Load latest")
            latest_df = gr.Dataframe(label="latest_telemetry_by_device")
            latest_err = gr.Textbox(label="error", interactive=False)

        with gr.Tab("Alerts"):
            alerts_fleet_id = gr.Textbox(label="fleet_id", value="FLEET_PARIS")
            alerts_day = gr.Textbox(label="day (YYYY-MM-DD)", value=str(date.today()))
            alerts_sev = gr.Dropdown(label="severity", choices=["LOW", "MED", "HIGH"], value="HIGH")
            btn_alerts = gr.Button("Load alerts")
            alerts_df = gr.Dataframe(label="alerts_by_fleet_day")
            alerts_err = gr.Textbox(label="error", interactive=False)

        with gr.Tab("Telemetry"):
            tel_device_id = gr.Textbox(label="device_id", value="BUS-001")
            tel_day = gr.Textbox(label="day (YYYY-MM-DD)", value=str(date.today()))
            tel_limit = gr.Slider(label="limit", minimum=1, maximum=500, value=50, step=1)
            btn_tel = gr.Button("Load telemetry")
            tel_df = gr.Dataframe(label="telemetry_by_device_day")
            tel_err = gr.Textbox(label="error", interactive=False)

    btn_devices.click(load_devices, inputs=[fleet_id], outputs=[devices_df, device_id, devices_err])
    btn_latest.click(load_latest, inputs=[device_id], outputs=[latest_df, latest_err])
    btn_alerts.click(load_alerts, inputs=[alerts_fleet_id, alerts_day, alerts_sev], outputs=[alerts_df, alerts_err])
    btn_tel.click(load_telemetry, inputs=[tel_device_id, tel_day, tel_limit], outputs=[tel_df, tel_err])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))

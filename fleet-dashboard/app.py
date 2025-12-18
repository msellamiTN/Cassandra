import os
import re
from datetime import date

import pandas as pd
import streamlit as st
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


_IDENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _qualify_table(table_name: str) -> str:
    ks = (CASSANDRA_KEYSPACE or "").strip()
    if not ks:
        return table_name
    if not _IDENT_RE.match(ks) or not _IDENT_RE.match(table_name):
        raise ValueError("Invalid keyspace/table identifier")
    return f"{ks}.{table_name}"


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


@st.cache_resource(show_spinner=False)
def _ensure_session_cached():
    _connect()
    return _ensure_session()


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
        session = _ensure_session_cached()
        if not fleet_id.strip():
            return pd.DataFrame(), "fleet_id is required"

        rs = session.execute(
            f"SELECT device_id, model, activated_at FROM {_qualify_table('devices_by_fleet')} WHERE fleet_id=%s",
            (fleet_id.strip(),),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def load_latest(device_id: str):
    try:
        session = _ensure_session_cached()
        if not device_id.strip():
            return pd.DataFrame(), "device_id is required"

        rs = session.execute(
            f"SELECT device_id, last_ts, lat, lon, speed_kmh, battery_pct, temp_c FROM {_qualify_table('latest_telemetry_by_device')} WHERE device_id=%s",
            (device_id.strip(),),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def load_alerts(fleet_id: str, day_str: str, severity: str):
    try:
        session = _ensure_session_cached()
        if not fleet_id.strip():
            return pd.DataFrame(), "fleet_id is required"

        if not day_str.strip():
            return pd.DataFrame(), "day is required"

        day_value = _parse_iso_date(day_str)

        rs = session.execute(
            f"SELECT ts, device_id, alert_type, message FROM {_qualify_table('alerts_by_fleet_day')} WHERE fleet_id=%s AND day=%s AND severity=%s LIMIT 200",
            (fleet_id.strip(), day_value, severity),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def load_telemetry(device_id: str, day_str: str, limit: int):
    try:
        session = _ensure_session_cached()
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
            f"SELECT ts, lat, lon, speed_kmh, battery_pct, temp_c, zone FROM {_qualify_table('telemetry_by_device_day')} WHERE device_id=%s AND day=%s LIMIT {limit_value}",
            (device_id.strip(), day_value),
        )
        df = _rows_to_df(rs)
        return df, ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


st.set_page_config(page_title="Fleet IoT Dashboard", layout="wide")

st.title("Fleet IoT Dashboard")

with st.sidebar:
    st.subheader("Connection")
    st.code(
        f"hosts={','.join(CASSANDRA_CONTACT_POINTS)}\nport={CASSANDRA_PORT}\nkeyspace={CASSANDRA_KEYSPACE}",
        language="text",
    )

tabs = st.tabs(["Devices", "Latest", "Alerts", "Telemetry"])

with tabs[0]:
    st.subheader("Devices by fleet")
    fleet_id = st.text_input("fleet_id", value="FLEET_PARIS")
    if st.button("Load devices", key="load_devices"):
        df, err = load_devices(fleet_id)
        if err:
            st.error(err)
        else:
            st.session_state["device_ids"] = (
                df["device_id"].dropna().astype(str).tolist() if "device_id" in df.columns else []
            )
            st.dataframe(df, use_container_width=True)

with tabs[1]:
    st.subheader("Latest telemetry")
    device_ids = st.session_state.get("device_ids", [])
    default_device = device_ids[0] if device_ids else ""
    device_id = st.text_input("device_id", value=default_device)
    if st.button("Load latest", key="load_latest"):
        df, err = load_latest(device_id)
        if err:
            st.error(err)
        else:
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                row = df.iloc[0]
                c1, c2, c3 = st.columns(3)
                c1.metric("Speed (km/h)", str(row.get("speed_kmh", "")))
                c2.metric("Battery (%)", str(row.get("battery_pct", "")))
                c3.metric("Temp (°C)", str(row.get("temp_c", "")))
                if "lat" in df.columns and "lon" in df.columns:
                    map_df = df[["lat", "lon"]].copy()
                    map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
                    map_df["lon"] = pd.to_numeric(map_df["lon"], errors="coerce")
                    st.map(map_df.dropna(), use_container_width=True)

with tabs[2]:
    st.subheader("Alerts")
    alerts_fleet_id = st.text_input("fleet_id", value="FLEET_PARIS", key="alerts_fleet_id")
    alerts_day = st.date_input("day", value=date.today(), key="alerts_day")
    alerts_sev = st.selectbox("severity", options=["LOW", "MED", "HIGH"], index=2, key="alerts_sev")
    if st.button("Load alerts", key="load_alerts"):
        df, err = load_alerts(alerts_fleet_id, alerts_day.isoformat(), alerts_sev)
        if err:
            st.error(err)
        else:
            st.dataframe(df, use_container_width=True)
            if not df.empty and "alert_type" in df.columns:
                st.bar_chart(df["alert_type"].value_counts(), use_container_width=True)

with tabs[3]:
    st.subheader("Telemetry")
    tel_device_id = st.text_input("device_id", value="BUS-001", key="tel_device_id")
    tel_day = st.date_input("day", value=date.today(), key="tel_day")
    tel_limit = st.slider("limit", min_value=1, max_value=500, value=50, step=1, key="tel_limit")
    if st.button("Load telemetry", key="load_telemetry"):
        df, err = load_telemetry(tel_device_id, tel_day.isoformat(), int(tel_limit))
        if err:
            st.error(err)
        else:
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                if "ts" in df.columns:
                    df_plot = df.copy()
                    df_plot["ts"] = pd.to_datetime(df_plot["ts"], errors="coerce")
                    df_plot = df_plot.dropna(subset=["ts"]).sort_values("ts")
                    df_plot = df_plot.set_index("ts")
                    for col in ["speed_kmh", "battery_pct", "temp_c"]:
                        if col in df_plot.columns:
                            numeric_series = pd.to_numeric(df_plot[col], errors="coerce")
                            st.line_chart(numeric_series.to_frame(name=col), use_container_width=True)
                if "lat" in df.columns and "lon" in df.columns:
                    map_df = df[["lat", "lon"]].copy()
                    map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
                    map_df["lon"] = pd.to_numeric(map_df["lon"], errors="coerce")
                    st.map(map_df.dropna(), use_container_width=True)

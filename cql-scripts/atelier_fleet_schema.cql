USE atelier;

CREATE TABLE IF NOT EXISTS devices_by_fleet (
  fleet_id text,
  device_id text,
  model text,
  activated_at timestamp,
  PRIMARY KEY ((fleet_id), device_id)
);

CREATE TABLE IF NOT EXISTS latest_telemetry_by_device (
  device_id text PRIMARY KEY,
  last_ts timestamp,
  lat double,
  lon double,
  speed_kmh double,
  battery_pct int,
  temp_c double
);

CREATE TABLE IF NOT EXISTS telemetry_by_device_day (
  device_id text,
  day date,
  ts timestamp,
  lat double,
  lon double,
  speed_kmh double,
  battery_pct int,
  temp_c double,
  zone text,
  PRIMARY KEY ((device_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS alerts_by_fleet_day (
  fleet_id text,
  day date,
  severity text,
  ts timestamp,
  device_id text,
  alert_type text,
  message text,
  PRIMARY KEY ((fleet_id, day, severity), ts, device_id)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS telemetry_by_fleet_day (
  fleet_id text,
  day date,
  ts timestamp,
  device_id text,
  lat double,
  lon double,
  speed_kmh double,
  battery_pct int,
  temp_c double,
  zone text,
  PRIMARY KEY ((fleet_id, day), ts, device_id)
) WITH CLUSTERING ORDER BY (ts DESC);

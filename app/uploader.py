# app/uploader.py
import json
import os
import requests
from datetime import datetime
from dateutil import tz

API_URL = "https://h2-api-z7sq.onrender.com/api/GreenSensorData"
LOCAL_TZ = tz.gettz("Asia/Ho_Chi_Minh")

def _to_utc_z(ts_str: str) -> str:
    """
    Nhận chuỗi ISO (có hoặc không timezone). Nếu không có TZ thì coi là giờ VN.
    Trả về ISO UTC với 'Z'.
    """
    # đã có 'Z' hoặc offset?
    try:
        if ts_str.endswith("Z") or "+" in ts_str or "-" in ts_str[10:]:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.astimezone(tz.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"
    except Exception:
        pass
    # không có tz: coi là local VN
    dt_naive = datetime.fromisoformat(ts_str)
    dt_local = dt_naive.replace(tzinfo=LOCAL_TZ)
    dt_utc = dt_local.astimezone(tz.UTC)
    return dt_utc.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"

def _map_payload(internal: dict) -> dict:
    env = internal.get("env", {}) or {}
    soil = internal.get("soil", {}) or {}
    co2  = internal.get("co2", {}) or {}

    # clamp UV âm nếu sensor nhả rác
    uv = env.get("uv_mw_cm2")
    if isinstance(uv, (int, float)) and uv < 0:
        uv = 0.0

    outward = {
        "deviceId": internal.get("device_id"),
        "timestamp": _to_utc_z(internal.get("ts")),
        "environment": {
            "temperatureC": env.get("temp_c"),
            "humidityPct": env.get("rh_pct"),
            "pressureHpa": env.get("pressure_hpa"),
            "lux": env.get("lux"),
            "uvMwCm2": uv,
            "altitudeM": env.get("alt_m"),
        },
        "co2": {
            "ppm": co2.get("ppm")
        },
        "soil": {
            "temperatureC": soil.get("temp_c"),
            "humidityPct": soil.get("hum_pct"),
            "ecUSCm": soil.get("ec_uS_cm"),
            "ph": soil.get("ph"),
            "n": soil.get("n_mgkg"),
            "p": soil.get("p_mgkg"),
            "k": soil.get("k_mgkg"),
            "saltMgL": soil.get("salt_mgL"),
        }
    }
    return outward

def post_dict(internal_payload: dict, timeout=15):
    body = _map_payload(internal_payload)
    resp = requests.post(API_URL, json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.status_code, resp.text

def post_file(json_path: str, timeout=15):
    """Đọc file JSON nội bộ (schema của ông), map sang schema server, rồi POST."""
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return post_dict(raw, timeout=timeout)

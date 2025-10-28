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
    soil = internal.get("soil")  # có thể là None hoặc dict
    co2  = internal.get("co2", {}) or {}
    gpio = internal.get("gpio")  # trạng thái GPIO devices (optional)

    # Hàm helper để đảm bảo giá trị số hợp lệ
    def safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    
    def safe_int(val, default=0):
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    # Clamp UV âm nếu sensor nhả rác
    uv = safe_float(env.get("uv_mw_cm2"))
    if uv < 0:
        uv = 0.0

    outward = {
        "deviceId": internal.get("device_id") or "UNKNOWN",
        "timestamp": _to_utc_z(internal.get("ts")),
        "environment": {
            "temperatureC": safe_float(env.get("temp_c")),
            "humidityPct": safe_float(env.get("rh_pct")),
            "pressureHpa": safe_float(env.get("pressure_hpa")),
            "lux": safe_float(env.get("lux")),
            "uvMwCm2": uv,
            "altitudeM": safe_float(env.get("alt_m")),
        },
        "co2": {
            "ppm": safe_float(co2.get("ppm"))
        },
    }
    
    # Chỉ thêm soil nếu có dữ liệu thật
    if soil and isinstance(soil, dict):
        outward["soil"] = {
            "temperatureC": safe_float(soil.get("temp_c")),
            "humidityPct": safe_float(soil.get("hum_pct")),
            "ecUSCm": safe_float(soil.get("ec_uS_cm")),
            "ph": safe_float(soil.get("ph")),
            "n": safe_float(soil.get("n_mgkg")),
            "p": safe_float(soil.get("p_mgkg")),
            "k": safe_float(soil.get("k_mgkg")),
            "saltMgL": safe_float(soil.get("salt_mgL")),
        }
    else:
        # Nếu không có soil, gửi giá trị mặc định
        outward["soil"] = {
            "temperatureC": 0.0,
            "humidityPct": 0.0,
            "ecUSCm": 0.0,
            "ph": 0.0,
            "n": 0.0,
            "p": 0.0,
            "k": 0.0,
            "saltMgL": 0.0,
        }
    
    # Thêm GPIO devices nếu có
    if gpio and isinstance(gpio, dict):
        devices = []
        for device_name, is_on in gpio.items():
            devices.append({
                "name": device_name,
                "state": "ON" if is_on else "OFF"
            })
        outward["devices"] = devices
    
    return outward

def post_dict(internal_payload: dict, timeout=15):
    body = _map_payload(internal_payload)
    
    # Debug: In ra body sẽ gửi (có thể comment sau khi chạy ổn)
    print("[DEBUG] Sending payload:")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    
    resp = requests.post(API_URL, json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.status_code, resp.text

def post_file(json_path: str, timeout=15):
    """Đọc file JSON nội bộ (schema của ông), map sang schema server, rồi POST."""
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return post_dict(raw, timeout=timeout)

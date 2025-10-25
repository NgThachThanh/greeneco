# app/json_export.py
import os, json, time
from datetime import datetime
from app.sen0501_i2c import Sen0501
from app.sen0220_uart import Sen0220
from app.es_soil7 import ESSoil7

def _iso_now():
    return datetime.now().isoformat(timespec="seconds")

def collect_all(cfg):
    """Đọc cả ENV, CO2, SOIL rồi trả dict JSON-ready."""
    s1 = Sen0501(bus=cfg["sen0501"]["i2c_bus"], addr=int(cfg["sen0501"]["address"]))
    s2 = Sen0220(port=cfg["sen0220"]["port"], baud=cfg["sen0220"]["baud"])
    soil = ESSoil7(port=cfg["soil7"]["port"], slave=cfg["soil7"]["slave"],
                   baud=cfg["soil7"]["baud"], timeout=cfg["soil7"]["timeout"],
                   inter_byte_timeout=cfg["soil7"]["inter_byte_timeout"])

    a = s1.read()
    b = s2.read()
    try:
        c = soil.read()
    except Exception:
        c = None

    data = {
        "ts": _iso_now(),
        "device_id": cfg.get("device_id") or None,
        "env": {
            "temp_c": a.get("temp_c"),
            "rh_pct": a.get("rh_pct"),
            "pressure_hpa": a.get("hpa"),
            "lux": a.get("lux"),
            "uv_mw_cm2": a.get("uv_mw_cm2"),
            "alt_m": a.get("alt_m"),
        },
        "co2": {"ppm": b.get("co2_ppm")},
        "soil": None if c is None else {
            "temp_c": c.get("temp_C"),
            "hum_pct": c.get("hum_%"),
            "ec_uS_cm": c.get("ec_uS_cm"),
            "ph": c.get("pH"),
            "n_mgkg": c.get("N_mgkg"),
            "p_mgkg": c.get("P_mgkg"),
            "k_mgkg": c.get("K_mgkg"),
            "salt_mgL": c.get("salt_mgL"),
        },
    }
    return data

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

# tools/roundtrip_check.py
import json
import time
import requests
from datetime import datetime, timezone

API_BASE = "https://h2-api-z7sq.onrender.com/api/GreenSensorData"
DEVICE_ID = "H2-001"  # đổi nếu cần

def post_sample():
    payload = {
        "deviceId": DEVICE_ID,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "environment": {
            "temperatureC": 27.14,
            "humidityPct": 61.52,
            "pressureHpa": 1007.0,
            "lux": 275.34,
            "uvMwCm2": 0.0,
            "altitudeM": 66.7
        },
        "co2": {"ppm": 735},
        "soil": {
            "temperatureC": 27.1,
            "humidityPct": 0.0,
            "ecUSCm": 0.0,
            "ph": 3.0,
            "n": 0.0,
            "p": 0.0,
            "k": 0.0,
            "saltMgL": 0.0
        }
    }
    r = requests.post(API_BASE, json=payload, timeout=15)
    print("[POST] status:", r.status_code)
    try:
        print("[POST] body:", r.json())
    except Exception:
        print("[POST] text:", r.text)
    r.raise_for_status()
    return payload["timestamp"]

def get_latest(page=1, page_size=10):
    params = {"deviceId": DEVICE_ID, "page": page, "pageSize": page_size}
    r = requests.get(API_BASE, params=params, timeout=15)
    print("[GET] status:", r.status_code)
    data = r.json()
    preview = json.dumps(data, ensure_ascii=False)[:800]
    print("[GET] preview:", preview, "..." if len(preview) == 800 else "")
    r.raise_for_status()
    return data

def coerce_items(data):
    """
    Chuẩn hóa mọi kiểu trả về thành list các items.
    - Nếu API trả list -> trả luôn.
    - Nếu trả dict và có "items"/"data" -> lấy trường đó.
    - Nếu dict chứa 1 record -> bọc thành list.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "data", "results", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # fallback: có thể là 1 record đơn lẻ
        return [data]
    return []

def main():
    ts = post_sample()
    time.sleep(1.5)  # đề phòng backend ghi trễ
    data = get_latest(page=1, page_size=10)
    items = coerce_items(data)

    # In gọn record đầu cho dễ nhìn
    if items:
        print("[GET] first item:", json.dumps(items[0], ensure_ascii=False, indent=2)[:1200])

    # Tìm record vừa post theo timestamp chính xác
    found = any(str(it.get("timestamp", "")) == ts for it in items)
    if found:
        print("[CHECK] Found newly posted record ✅")
    else:
        # Thử nới tìm kiếm bằng pageSize lớn hơn nếu chưa thấy
        print("[CHECK] Not found in first page. Thử lại với pageSize=50...")
        data2 = get_latest(page=1, page_size=50)
        items2 = coerce_items(data2)
        found2 = any(str(it.get("timestamp", "")) == ts for it in items2)
        if found2:
            print("[CHECK] Found with bigger pageSize ✅")
        else:
            # In vài timestamp để đối chiếu mắt thường
            print("[DEBUG] Recent timestamps:",
                  [it.get("timestamp") for it in items2[:10]])

if __name__ == "__main__":
    main()

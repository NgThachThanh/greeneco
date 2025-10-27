# app/uploader_greenimage.py
import requests, os, time
from typing import Optional

class HttpError(RuntimeError): pass

def upload_green_image(base_url: str, image_path: str, device_id: str,
                       token: Optional[str] = None, timeout_sec: int = 20, max_retries: int = 3):
    url = base_url.rstrip("/") + "/api/GreenImage/upload"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for attempt in range(1, max_retries + 1):
        with open(image_path, "rb") as f:
            files = {"formFile": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"deviceId": device_id}
            try:
                r = requests.post(url, headers=headers, files=files, data=data, timeout=timeout_sec)
                if r.status_code in (200, 201):
                    return r.json()
                raise HttpError(f"HTTP {r.status_code}: {r.text[:300]}")
            except Exception:
                if attempt == max_retries:
                    raise
                time.sleep(2 ** attempt)

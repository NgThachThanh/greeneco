# GPIO Control API Documentation

## Endpoint: POST `/api/iot/control`

Điều khiển các thiết bị GPIO (relay) trên Raspberry Pi.

---

## 1. Format Request (Khuyến nghị)

### Request Body:
```json
{
  "deviceId": "H2-RASPI-01",
  "component": "pump",
  "state": "on"
}
```

### Parameters:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deviceId` | string | No | ID của thiết bị Raspberry Pi (để tracking) |
| `component` | string | **Yes** | Tên thiết bị: `pump`, `fan1`, `fan2`, `light` |
| `state` | string | **Yes** | Trạng thái: `on`, `off`, hoặc `toggle` |

### Valid Components:
- `pump` - Bơm nước
- `fan1` - Quạt 1
- `fan2` - Quạt 2  
- `light` - Đèn

### Valid States:
- `on` - Bật thiết bị
- `off` - Tắt thiết bị
- `toggle` - Đảo trạng thái (ON ↔ OFF)

---

## 2. Response Format

### Success Response (200 OK):
```json
{
  "status": "OK",
  "deviceId": "H2-RASPI-01",
  "component": "pump",
  "state": "on",
  "pin": 13,
  "message": "pump turned on"
}
```

### Error Response (400 Bad Request):
```json
{
  "status": "FAILED",
  "deviceId": "H2-RASPI-01",
  "component": "invalid_device",
  "error": "Failed to control 'invalid_device'. Valid components: ['fan1', 'fan2', 'pump', 'light']"
}
```

### Missing Parameters (400):
```json
{
  "status": "FAILED",
  "error": "Missing component or state"
}
```

### Invalid State (400):
```json
{
  "status": "FAILED",
  "error": "Invalid state: abc. Use 'on', 'off', or 'toggle'"
}
```

---

## 3. Example Requests

### cURL Examples:

#### Bật pump:
```bash
curl -X POST http://localhost:5000/api/iot/control \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "H2-RASPI-01",
    "component": "pump",
    "state": "on"
  }'
```

#### Tắt fan1:
```bash
curl -X POST http://localhost:5000/api/iot/control \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "H2-RASPI-01",
    "component": "fan1",
    "state": "off"
  }'
```

#### Toggle light:
```bash
curl -X POST http://localhost:5000/api/iot/control \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "H2-RASPI-01",
    "component": "light",
    "state": "toggle"
  }'
```

### Python Example:
```python
import requests

url = "http://localhost:5000/api/iot/control"
payload = {
    "deviceId": "H2-RASPI-01",
    "component": "pump",
    "state": "on"
}

response = requests.post(url, json=payload)
print(response.json())
```

### JavaScript Example:
```javascript
fetch('http://localhost:5000/api/iot/control', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    deviceId: 'H2-RASPI-01',
    component: 'pump',
    state: 'on'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## 4. Get Status

### Endpoint: GET `/api/iot/status`

Lấy trạng thái hiện tại của tất cả thiết bị.

#### Request:
```bash
curl http://localhost:5000/api/iot/status
```

#### Response:
```json
{
  "status": "OK",
  "backend": "RPi.GPIO v0.7.1",
  "devices": [
    {
      "name": "fan1",
      "state": "OFF",
      "pin": 5
    },
    {
      "name": "fan2",
      "state": "OFF",
      "pin": 6
    },
    {
      "name": "pump",
      "state": "ON",
      "pin": 13
    },
    {
      "name": "light",
      "state": "OFF",
      "pin": 19
    }
  ]
}
```

---

## 5. Legacy Format (Tương thích ngược)

API vẫn hỗ trợ format cũ:

### Single Device:
```json
{
  "device": "pump",
  "action": "on"
}
```

### Multiple Devices:
```json
{
  "devices": [
    {"device": "fan1", "action": "on"},
    {"device": "pump", "action": "off"}
  ]
}
```

### All Devices:
```json
{
  "action": "all_on"
}
```
hoặc
```json
{
  "action": "all_off"
}
```

---

## 6. Component Aliases

API hỗ trợ nhiều cách gọi tên thiết bị:

| Component | Aliases |
|-----------|---------|
| `fan1` | `1`, `fan 1`, `quat1`, `quạt1`, `q1` |
| `fan2` | `2`, `fan 2`, `quat2`, `quạt2`, `q2` |
| `pump` | `3`, `bom`, `bơm` |
| `light` | `4`, `den`, `đèn`, `lamp` |

Ví dụ:
```json
{"deviceId": "H2-RASPI-01", "component": "bơm", "state": "on"}
```
Sẽ điều khiển pump (vì "bơm" là alias của "pump")

---

## 7. GPIO Pin Mapping

| Component | BCM GPIO | Physical Pin | Active |
|-----------|----------|--------------|--------|
| fan1 | GPIO 5 | 29 | LOW |
| fan2 | GPIO 6 | 31 | LOW |
| pump | GPIO 13 | 33 | LOW |
| light | GPIO 19 | 35 | LOW |

**Lưu ý**: Tất cả relay đều ACTIVE_LOW (LOW = ON, HIGH = OFF)

---

## 8. Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 500 | Internal Server Error |
| 503 | GPIO not available |

---

## 9. Testing

### Start Flask App:
```bash
cd ~/greeneco
python3 app/app.py
```

Server sẽ chạy tại: `http://0.0.0.0:5000`

### Run Test Script:
```bash
python3 test_gpio_api.py
```

### Manual Test với curl:
```bash
# Test bật pump
curl -X POST http://localhost:5000/api/iot/control \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"H2-RASPI-01","component":"pump","state":"on"}'

# Kiểm tra status
curl http://localhost:5000/api/iot/status

# Test tắt pump
curl -X POST http://localhost:5000/api/iot/control \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"H2-RASPI-01","component":"pump","state":"off"}'
```

---

## 10. Production Deployment

### Chạy với Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app.app:app
```

### Chạy với systemd:
Tạo file `/etc/systemd/system/greeneco-api.service`:
```ini
[Unit]
Description=GreenEco GPIO Control API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/greeneco
Environment="PATH=/home/pi/greeneco/venv/bin"
ExecStart=/home/pi/greeneco/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable và start:
```bash
sudo systemctl enable greeneco-api
sudo systemctl start greeneco-api
sudo systemctl status greeneco-api
```

---

## 11. Security Notes

⚠️ **QUAN TRỌNG**:

1. **Không expose ra Internet** mà không có authentication
2. Sử dụng trong mạng local hoặc VPN
3. Thêm API key/token authentication nếu cần public
4. Rate limiting để tránh spam requests
5. HTTPS nếu truyền qua mạng không tin cậy

---

## 12. Troubleshooting

### GPIO not available (503):
```bash
# Kiểm tra RPi.GPIO
python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"

# Install nếu thiếu
pip install RPi.GPIO
```

### Permission denied:
```bash
# Thêm user vào gpio group
sudo usermod -a -G gpio $USER

# Reboot
sudo reboot
```

### Device not found (400):
Kiểm tra tên component có đúng không. Valid: `pump`, `fan1`, `fan2`, `light`

---

## Support

Xem thêm:
- `GPIO_MAPPING.md` - Chi tiết phân bổ GPIO
- `test_gpio_api.py` - Test script đầy đủ
- `app/gpio_controller.py` - Source code GPIO control

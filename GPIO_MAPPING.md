# GPIO PIN MAPPING - GREENECO PROJECT

## Tổng quan phân bổ GPIO

Bảng này liệt kê TẤT CẢ các GPIO đang được sử dụng để tránh xung đột.

## 1. UART Communication (Sensors)

| Device | Port | BCM GPIO | Physical Pin | Function | Notes |
|--------|------|----------|--------------|----------|-------|
| **SEN0220** (CO2) | `/dev/ttyAMA0` | GPIO 14 | 8 | TXD0 | UART0 - Mặc định |
| | | GPIO 15 | 10 | RXD0 | |
| **SEN0501** (Env) | `/dev/ttyAMA1` | GPIO 0 | 27 | TXD2 (ID_SD) | UART2 - Cần enable |
| | | GPIO 1 | 28 | RXD2 (ID_SC) | ⚠️ Xung đột với HAT EEPROM nếu có |

**Config cần thiết trong `/boot/config.txt`:**
```
dtoverlay=uart2
```

## 2. GPIO Control (Relay - Active LOW)

| Device | BCM GPIO | Physical Pin | State | Notes |
|--------|----------|--------------|-------|-------|
| **Fan 1** | GPIO 5 | 29 | ACTIVE_LOW | Relay module |
| **Fan 2** | GPIO 6 | 31 | ACTIVE_LOW | Relay module |
| **Pump** | GPIO 13 | 33 | ACTIVE_LOW | Relay module |
| **Light** | GPIO 19 | 35 | ACTIVE_LOW | Relay module |

## 3. I2C Communication (Nếu cần)

| Device | BCM GPIO | Physical Pin | Function | Notes |
|--------|----------|--------------|----------|-------|
| **I2C Bus 1** | GPIO 2 | 3 | SDA1 | Không dùng nếu SEN0501 chuyển UART |
| | GPIO 3 | 5 | SCL1 | |

## 4. Các GPIO KHÔNG SỬ DỤNG (Có thể dùng mở rộng)

| BCM GPIO | Physical Pin | Alt Function | Recommendation |
|----------|--------------|--------------|----------------|
| GPIO 4 | 7 | GPCLK0 | ✅ Free |
| GPIO 7 | 26 | SPI0_CE1 | ✅ Free (nếu không dùng SPI) |
| GPIO 8 | 24 | SPI0_CE0 | ⚠️ SPI (nếu cần) |
| GPIO 9 | 21 | SPI0_MISO | ⚠️ SPI (nếu cần) |
| GPIO 10 | 19 | SPI0_MOSI | ⚠️ SPI (nếu cần) |
| GPIO 11 | 23 | SPI0_SCLK | ⚠️ SPI (nếu cần) |
| GPIO 12 | 32 | PWM0 | ✅ Free |
| GPIO 16 | 36 | - | ✅ Free |
| GPIO 17 | 11 | - | ✅ Free |
| GPIO 18 | 12 | PWM0 | ✅ Free |
| GPIO 20 | 38 | - | ✅ Free |
| GPIO 21 | 40 | - | ✅ Free |
| GPIO 22 | 15 | - | ✅ Free |
| GPIO 23 | 16 | - | ✅ Free |
| GPIO 24 | 18 | - | ✅ Free |
| GPIO 25 | 22 | - | ✅ Free |
| GPIO 26 | 37 | - | ✅ Free |
| GPIO 27 | 13 | - | ✅ Free |

## 5. Giải pháp thay thế nếu GPIO 0/1 bị xung đột

### Option A: USB-to-UART Adapter (KHUYẾN NGHỊ)
```
USB Adapter (CP2102/CH340/FT232)
├─ TX → RX của SEN0501
├─ RX → TX của SEN0501
├─ VCC → 3.3V/5V
└─ GND → GND

Port: /dev/ttyUSB1 hoặc /dev/ttyUSB2
```

**Ưu điểm:**
- ✅ Không xung đột GPIO
- ✅ Dễ debug (có thể rút ra test riêng)
- ✅ Không cần config dtoverlay

**Cập nhật config:**
```yaml
sen0501:
  mode: "uart"
  port: "/dev/ttyUSB1"  # Thay vì /dev/ttyAMA1
  baud: 9600
```

### Option B: UART4 (GPIO 8/9) - Nếu không dùng SPI
```
dtoverlay=uart4

GPIO 8 (pin 24) → RX của SEN0501
GPIO 9 (pin 21) → TX của SEN0501
Port: /dev/ttyAMA2
```

⚠️ **Lưu ý**: Xung đột với SPI0 nếu dùng SPI devices

### Option C: Software Serial (GPIO tự do)
Dùng library như `pyserial` với GPIO thường (không phải UART hardware).
⚠️ Không ổn định với baud rate cao, không khuyến nghị.

## 6. Kiểm tra xung đột

### Script kiểm tra GPIO đang dùng:
```bash
# Xem tất cả GPIO exports
ls -la /sys/class/gpio/

# Xem UART ports
ls -l /dev/ttyAMA* /dev/ttyUSB*

# Xem dtoverlay đang load
dtoverlay -l
```

### Kiểm tra trong Python:
```python
# app/check_gpio.py
import RPi.GPIO as GPIO

# Danh sách GPIO đang dùng
USED_GPIOS = {
    0: "SEN0501 UART TX",
    1: "SEN0501 UART RX",
    5: "Fan1 Relay",
    6: "Fan2 Relay",
    13: "Pump Relay",
    14: "SEN0220 UART TX",
    15: "SEN0220 UART RX",
    19: "Light Relay",
}

print("GPIO được phân bổ:")
for gpio, desc in USED_GPIOS.items():
    print(f"  GPIO {gpio:2d} (pin {gpio_to_physical(gpio):2d}) - {desc}")
```

## 7. Khuyến nghị cuối cùng

### Nếu KHÔNG có HAT với EEPROM:
✅ **Dùng GPIO 0/1 (UART2)** - theo cấu hình hiện tại

### Nếu CÓ HAT với EEPROM:
✅ **Dùng USB-to-UART adapter** - an toàn nhất

### Nếu cần nhiều UART:
- UART0 → SEN0220 (đã có)
- USB1 → SEN0501 (qua adapter)
- USB0 → ES-Soil7 (đã có)

## 8. Tóm tắt

```
┌─────────────────────────────────────────────────┐
│  GREENECO GPIO ALLOCATION                       │
├─────────────────────────────────────────────────┤
│  UART Sensors:                                  │
│    • SEN0220:  GPIO 14/15  (UART0)              │
│    • SEN0501:  GPIO 0/1    (UART2) ⚠️           │
│                                                  │
│  GPIO Control (Relays):                         │
│    • Fan 1:    GPIO 5      (ACTIVE_LOW)         │
│    • Fan 2:    GPIO 6      (ACTIVE_LOW)         │
│    • Pump:     GPIO 13     (ACTIVE_LOW)         │
│    • Light:    GPIO 19     (ACTIVE_LOW)         │
│                                                  │
│  ⚠️  XUNG ĐỘT ĐÃ TRÁNH:                         │
│      UART không dùng GPIO 5, 6, 13, 19          │
│                                                  │
│  💡 GIẢI PHÁP AN TOÀN:                          │
│      Dùng USB-to-UART adapter cho SEN0501       │
└─────────────────────────────────────────────────┘
```

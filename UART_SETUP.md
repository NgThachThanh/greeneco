# Hướng dẫn chuyển SEN0501 sang chế độ UART

## Tổng quan
SEN0501 hiện được chuyển sang chế độ UART thay vì I2C do vấn đề không đọc được dữ liệu.

## Phân bổ chân UART

### SEN0220 (CO2 Sensor) - KHÔNG THAY ĐỔI
- **Port**: `/dev/ttyAMA0` (UART0)
- **TX**: GPIO 14 (Physical pin 8)
- **RX**: GPIO 15 (Physical pin 10)

### SEN0501 (Environmental Sensor) - MỚI
- **Port**: `/dev/ttyAMA1` (UART2)
- **TX từ Pi**: GPIO 0 (Physical pin 27, ID_SD) → RX của SEN0501
- **RX từ Pi**: GPIO 1 (Physical pin 28, ID_SC) → TX của SEN0501

⚠️ **LƯU Ý**: Đã tránh xung đột với GPIO control (GPIO 5, 6, 13, 19 đang dùng cho relay)

## Sơ đồ đấu nối SEN0501

```
Raspberry Pi              SEN0501 (UART Mode)
─────────────────         ───────────────────
GPIO 0 (pin 27)   ──────► RX
GPIO 1 (pin 28)   ◄────── TX
3.3V or 5V        ──────► VCC
GND               ──────► GND
```

## Các bước cấu hình trên Raspberry Pi

### 1. Enable UART2 trong `/boot/config.txt`

Thêm dòng này vào cuối file `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

Thêm vào cuối file:
```
# Enable UART2 for SEN0501 (GPIO 0/1 - tránh xung đột với GPIO control)
dtoverlay=uart2
```

Hoặc dùng lệnh:
```bash
echo "dtoverlay=uart2" | sudo tee -a /boot/config.txt
```

### 2. Reboot Raspberry Pi

```bash
sudo reboot
```

### 3. Kiểm tra UART ports

Sau khi reboot, kiểm tra xem `/dev/ttyAMA1` đã xuất hiện chưa:

```bash
ls -l /dev/ttyAMA*
```

Bạn sẽ thấy:
- `/dev/ttyAMA0` - cho SEN0220
- `/dev/ttyAMA1` - cho SEN0501 (mới)

### 4. Kiểm tra permissions

```bash
sudo chmod 666 /dev/ttyAMA1
# Hoặc thêm user vào group dialout
sudo usermod -a -G dialout $USER
```

### 5. Cấu hình trong settings.yml

File `config/settings.yml` đã được cập nhật:

```yaml
sen0501:
  mode: "uart"              # Đổi thành "i2c" nếu muốn quay lại I2C
  # UART settings
  port: "/dev/ttyAMA1"      # UART5 - GPIO 12/13
  baud: 9600
  read_hz: 1
```

## Chuyển đổi giữa I2C và UART

Để chuyển đổi mode, chỉ cần sửa trong `config/settings.yml`:

### Chế độ UART (hiện tại):
```yaml
sen0501:
  mode: "uart"
  port: "/dev/ttyAMA1"
  baud: 9600
  read_hz: 1
```

### Chế độ I2C (nếu cần quay lại):
```yaml
sen0501:
  mode: "i2c"
  i2c_bus: 1
  address: 0x22
  read_hz: 1
```

## Test SEN0501 UART

Chạy trực tiếp file để test:

```bash
cd ~/greeneco
python3 app/sen0501_uart.py
```

Hoặc test trong main:

```bash
python3 app/main.py --once-0501
```

## Lưu ý quan trọng

### 1. GPIO 0/1 và EEPROM ID
**LƯU Ý**: GPIO 0/1 (ID_SD/ID_SC) thường dùng cho HAT EEPROM trên Raspberry Pi:
- Nếu bạn **KHÔNG** dùng HAT có EEPROM → **AN TOÀN** dùng GPIO 0/1 cho UART
- Nếu bạn **CÓ** dùng HAT có EEPROM → Cân nhắc dùng **USB-to-UART adapter** thay thế

**Giải pháp thay thế** (nếu lo xung đột):
- Dùng USB-to-UART adapter (CH340, CP2102, FT232) → `/dev/ttyUSB1`
- Dùng UART4 (GPIO 8/9) - nhưng cần kiểm tra xung đột SPI

### 2. Đổi jumper/switch trên SEN0501
**QUAN TRỌNG**: Sensor SEN0501 phải được chuyển sang chế độ UART bằng cách:
- Kiểm tra datasheet của SEN0501
- Có thể cần đổi jumper hoặc switch trên module
- Một số module cần hàn hoặc cắt đường mạch để chuyển từ I2C sang UART

### 3. Baud rate
Mặc định dùng 9600. Nếu không đọc được, thử các baud rate khác:
- 9600 (thông dụng)
- 19200
- 38400
- 115200

Sửa trong `config/settings.yml`:
```yaml
sen0501:
  baud: 115200  # Thử baud rate khác
```

### 4. Protocol/Command bytes
File `sen0501_uart.py` hiện dùng command bytes giả định:
```python
CMD_READ_ALL = bytes([0xFF, 0x01, 0x78, 0x00, 0x00, 0x00, 0x00, 0x00, 0x87])
```

**Bạn CẦN kiểm tra datasheet SEN0501 UART mode** để lấy:
- Command bytes chính xác
- Response format
- Checksum algorithm
- Data parsing

### 5. Voltage level
- Raspberry Pi GPIO dùng 3.3V logic
- Nếu SEN0501 dùng 5V logic, cần level shifter để bảo vệ Pi

## Troubleshooting

### Không thấy /dev/ttyAMA1
```bash
# Kiểm tra dtoverlay đã load chưa
dtoverlay -l | grep uart

# Xem log kernel
dmesg | grep tty
```

### Permission denied
```bash
sudo chmod 666 /dev/ttyAMA1
sudo usermod -a -G dialout $USER
# Logout và login lại
```

### Không đọc được data
1. Kiểm tra wiring (TX↔RX phải chéo)
2. Kiểm tra baud rate
3. Kiểm tra command bytes theo datasheet
4. Dùng logic analyzer hoặc oscilloscope để xem tín hiệu
5. Test bằng minicom/screen:
   ```bash
   sudo apt-get install minicom
   minicom -D /dev/ttyAMA1 -b 9600
   ```

## Tham khảo GPIO Pins (BCM numbering)

### UART Sensors:
| BCM GPIO | Physical Pin | Chức năng             | Thiết bị |
|----------|-------------|-----------------------|----------|
| GPIO 14  | 8           | TXD0 (UART0)          | SEN0220  |
| GPIO 15  | 10          | RXD0 (UART0)          | SEN0220  |
| GPIO 0   | 27          | TXD2 (UART2, ID_SD)   | SEN0501  |
| GPIO 1   | 28          | RXD2 (UART2, ID_SC)   | SEN0501  |

### GPIO Control (Relay):
| BCM GPIO | Physical Pin | Thiết bị     | Trạng thái |
|----------|-------------|--------------|------------|
| GPIO 5   | 29          | Fan 1        | ACTIVE_LOW |
| GPIO 6   | 31          | Fan 2        | ACTIVE_LOW |
| GPIO 13  | 33          | Pump         | ACTIVE_LOW |
| GPIO 19  | 35          | Light        | ACTIVE_LOW |

⚠️ **Đã tránh xung đột**: UART không dùng GPIO 5, 6, 13, 19

## Liên hệ
Nếu cần hỗ trợ thêm, hãy cung cấp:
1. Datasheet SEN0501 UART mode
2. Output của `dmesg | grep tty`
3. Output test command

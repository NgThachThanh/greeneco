# app/sen0501_uart.py
# -*- coding: utf-8 -*-
"""
SEN0501 Environmental Sensor - UART Mode
Sử dụng UART2 trên Raspberry Pi (GPIO 0/1) - TRÁNH XUNG ĐỘT VỚI GPIO CONTROL
Port: /dev/ttyAMA1 (cần enable uart2 trong /boot/config.txt)

Wiring:
  SEN0501 RX -> GPIO 0 (pin 27, BCM 0, ID_SD) - TXD của Pi
  SEN0501 TX -> GPIO 1 (pin 28, BCM 1, ID_SC) - RXD của Pi
  VCC -> 3.3V hoặc 5V
  GND -> GND

LƯU Ý: GPIO 0/1 thường dùng cho EEPROM ID, nhưng an toàn nếu không dùng HAT có EEPROM.
       Nếu vẫn lo xung đột, có thể dùng USB-to-UART adapter thay thế.
"""
import serial
import time
import struct

class Sen0501UART:
    """
    Wrapper cho SEN0501 ở chế độ UART.
    
    Giao thức Modbus RTU hoặc custom protocol (tùy datasheet SEN0501).
    Hiện tại implement dạng query-response cơ bản.
    
    read() trả dict:
      {
        "temp_c": float|None,
        "rh_pct": float|None,
        "lux": float|None,
        "uv_mw_cm2": float|None,
        "hpa": float|None,
        "alt_m": None  # UART mode có thể không hỗ trợ altitude
      }
    """
    
    # Command để đọc tất cả sensors (cần xem datasheet SEN0501 UART protocol)
    # Đây là ví dụ giả định, bạn cần điều chỉnh theo datasheet thực tế
    CMD_READ_ALL = bytes([0xFF, 0x01, 0x78, 0x00, 0x00, 0x00, 0x00, 0x00, 0x87])
    
    def __init__(self, port="/dev/ttyAMA1", baud=9600, timeout=1.0):
        """
        Args:
            port: UART port (default /dev/ttyAMA1 cho UART2)
            baud: Baud rate (thường là 9600 hoặc 115200)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baud = baud
        self.ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )
        time.sleep(0.1)  # Wait for serial to stabilize
        
    def _calculate_checksum(self, data):
        """Tính checksum (tùy protocol của SEN0501)."""
        return (0xFF - (sum(data) & 0xFF) + 1) & 0xFF
    
    def _validate_response(self, resp):
        """Kiểm tra response có hợp lệ không."""
        if len(resp) < 9:
            return False
        # Thêm logic validate checksum nếu cần
        return True
    
    def read(self):
        """
        Đọc tất cả các sensors từ SEN0501 qua UART.
        
        Returns:
            dict với các keys: temp_c, rh_pct, lux, uv_mw_cm2, hpa, alt_m
        """
        try:
            # Clear buffer
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Gửi command đọc
            self.ser.write(self.CMD_READ_ALL)
            self.ser.flush()
            
            # Đợi response (độ dài tùy protocol, giả sử 25 bytes)
            time.sleep(0.1)
            resp = self.ser.read(25)
            
            if not self._validate_response(resp):
                return self._null_reading()
            
            # Parse response theo datasheet SEN0501 UART
            # Đây là ví dụ giả định cấu trúc:
            # Byte 0-1: Header (0xFF 0x78)
            # Byte 2-3: Temperature (int16, /100)
            # Byte 4-5: Humidity (uint16, /100)
            # Byte 6-9: Lux (uint32)
            # Byte 10-11: UV (uint16, /100)
            # Byte 12-15: Pressure (uint32, /100)
            # Byte 16-24: reserved/checksum
            
            if len(resp) >= 25:
                temp_raw = struct.unpack('>h', resp[2:4])[0]  # signed int16, big-endian
                hum_raw = struct.unpack('>H', resp[4:6])[0]   # unsigned int16
                lux_raw = struct.unpack('>I', resp[6:10])[0]  # unsigned int32
                uv_raw = struct.unpack('>H', resp[10:12])[0]  # unsigned int16
                hpa_raw = struct.unpack('>I', resp[12:16])[0] # unsigned int32
                
                return {
                    "temp_c": temp_raw / 100.0,
                    "rh_pct": hum_raw / 100.0,
                    "lux": float(lux_raw),
                    "uv_mw_cm2": uv_raw / 100.0,
                    "hpa": hpa_raw / 100.0,
                    "alt_m": None,  # UART mode không hỗ trợ altitude
                }
            else:
                return self._null_reading()
                
        except Exception as e:
            print(f"[SEN0501-UART] Lỗi đọc: {e}")
            return self._null_reading()
    
    def _null_reading(self):
        """Trả về reading null khi có lỗi."""
        return {
            "temp_c": None,
            "rh_pct": None,
            "lux": None,
            "uv_mw_cm2": None,
            "hpa": None,
            "alt_m": None,
        }
    
    def stream(self, hz=1):
        """Generator để stream data liên tục."""
        dt = 1.0 / max(1, int(hz))
        while True:
            yield self.read()
            time.sleep(dt)
    
    def close(self):
        """Đóng serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def __del__(self):
        """Cleanup khi object bị destroy."""
        self.close()


# Test code
if __name__ == "__main__":
    print("=== SEN0501 UART Mode Test ===")
    print("Port: /dev/ttyAMA1 (UART2, GPIO 0/1)")
    print("Wiring:")
    print("  SEN0501 RX -> GPIO 0 (pin 27, ID_SD)")
    print("  SEN0501 TX -> GPIO 1 (pin 28, ID_SC)")
    print("  VCC -> 3.3V/5V")
    print("  GND -> GND")
    print("")
    
    try:
        sensor = Sen0501UART(port="/dev/ttyAMA1", baud=9600)
        print("Đọc 5 lần...")
        for i in range(5):
            data = sensor.read()
            print(f"[{i+1}] Temp: {data['temp_c']}°C, "
                  f"RH: {data['rh_pct']}%, "
                  f"Lux: {data['lux']}, "
                  f"UV: {data['uv_mw_cm2']} mW/cm², "
                  f"Pressure: {data['hpa']} hPa")
            time.sleep(1)
        sensor.close()
    except Exception as e:
        print(f"Lỗi: {e}")
        print("\nĐảm bảo đã:")
        print("1. Enable UART2 trong /boot/config.txt:")
        print("   dtoverlay=uart2")
        print("2. Reboot Pi")
        print("3. Kiểm tra port tồn tại: ls -l /dev/ttyAMA*")

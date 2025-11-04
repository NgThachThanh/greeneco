#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test nhanh để kiểm tra cả 2 sensor SEN0501 (UART) và SEN0220 (UART)
"""
import time
import sys

def test_sen0501_uart():
    """Test SEN0501 ở chế độ UART."""
    print("="*60)
    print("TEST SEN0501 - UART MODE")
    print("="*60)
    print("Port: /dev/ttyAMA1 (UART2)")
    print("GPIO: TX=0 (pin 27), RX=1 (pin 28)")
    print("⚠️  Tránh xung đột với GPIO control (5,6,13,19)")
    print("")
    
    try:
        from app.sen0501_uart import Sen0501UART
        sensor = Sen0501UART(port="/dev/ttyAMA1", baud=9600)
        
        print("Đọc 3 lần...")
        for i in range(3):
            data = sensor.read()
            print(f"[{i+1}] Temp: {data['temp_c']}°C, "
                  f"RH: {data['rh_pct']}%, "
                  f"Lux: {data['lux']}, "
                  f"UV: {data['uv_mw_cm2']} mW/cm², "
                  f"Pressure: {data['hpa']} hPa")
            time.sleep(1)
        
        sensor.close()
        print("✓ SEN0501 UART test hoàn thành\n")
        return True
        
    except Exception as e:
        print(f"✗ Lỗi SEN0501 UART: {e}\n")
        return False

def test_sen0220_uart():
    """Test SEN0220 CO2 sensor."""
    print("="*60)
    print("TEST SEN0220 - CO2 SENSOR")
    print("="*60)
    print("Port: /dev/ttyAMA0 (UART0)")
    print("GPIO: TX=14 (pin 8), RX=15 (pin 10)")
    print("")
    
    try:
        from app.sen0220_uart import Sen0220
        sensor = Sen0220(port="/dev/ttyAMA0", baud=9600)
        
        print("Đọc 3 lần...")
        for i in range(3):
            data = sensor.read()
            print(f"[{i+1}] CO2: {data['co2_ppm']} ppm")
            time.sleep(1)
        
        print("✓ SEN0220 test hoàn thành\n")
        return True
        
    except Exception as e:
        print(f"✗ Lỗi SEN0220: {e}\n")
        return False

def check_uart_ports():
    """Kiểm tra các UART ports có tồn tại không."""
    print("="*60)
    print("KIỂM TRA UART PORTS")
    print("="*60)
    
    import os
    ports = [
        ("/dev/ttyAMA0", "SEN0220 (CO2)"),
        ("/dev/ttyAMA1", "SEN0501 (Environmental)"),
    ]
    
    all_ok = True
    for port, desc in ports:
        if os.path.exists(port):
            print(f"✓ {port} - {desc} - TỒN TẠI")
        else:
            print(f"✗ {port} - {desc} - KHÔNG TỒN TẠI")
            all_ok = False
    
    print("")
    
    if not all_ok:
        print("HƯỚNG DẪN SỬA LỖI:")
        print("1. Enable UART trong /boot/config.txt:")
        print("   sudo nano /boot/config.txt")
        print("   Thêm: dtoverlay=uart5")
        print("2. Reboot: sudo reboot")
        print("3. Kiểm tra lại: ls -l /dev/ttyAMA*")
        print("")
    
    return all_ok

def main():
    """Main test function."""
    print("\n" + "="*60)
    print("  GREENECO - UART SENSORS TEST")
    print("="*60 + "\n")
    
    # Kiểm tra ports trước
    ports_ok = check_uart_ports()
    
    if not ports_ok:
        print("⚠ Một số UART ports không tồn tại!")
        print("  Xem hướng dẫn ở trên để fix.\n")
        return
    
    # Test từng sensor
    results = []
    
    print("\n")
    sen0220_ok = test_sen0220_uart()
    results.append(("SEN0220 (CO2)", sen0220_ok))
    
    print("\n")
    sen0501_ok = test_sen0501_uart()
    results.append(("SEN0501 (Environmental)", sen0501_ok))
    
    # Tổng kết
    print("="*60)
    print("KẾT QUẢ TEST")
    print("="*60)
    for name, ok in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{status} - {name}")
    print("="*60)
    
    all_pass = all(ok for _, ok in results)
    if all_pass:
        print("\n🎉 Tất cả sensors hoạt động tốt!")
    else:
        print("\n⚠ Một số sensors có vấn đề, kiểm tra lại wiring và config.")
    print("")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest bị ngắt bởi user.")
        sys.exit(0)

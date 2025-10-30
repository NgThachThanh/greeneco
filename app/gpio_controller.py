# app/gpio_controller.py
"""
Module điều khiển các thiết bị qua GPIO (relay/transistor).
Mỗi thiết bị được map với một GPIO pin cụ thể.
"""
import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Fallback cho môi trường dev không có RPi
    GPIO = None
    print("[Warning] RPi.GPIO not available. Using mock mode.")

# Định nghĩa các thiết bị và GPIO pin tương ứng (BCM numbering)
DEVICES = {
    "fan1": 5,    # pin 29 (GPIO5)
    "fan2": 6,    # pin 31 (GPIO6)
    "pump": 13,   # pin 33 (GPIO13)
    "light": 19   # pin 35 (GPIO19)
}

# Đa số module relay phổ biến là ACTIVE-LOW: kéo chân IN xuống LOW sẽ kích relay (ON)
# Với ACTIVE_LOW=True: ON -> output LOW, OFF -> output HIGH
ACTIVE_LOW = {
    "fan1": True,
    "fan2": True,
    "pump": True,
    "light": True,
}

# Trạng thái hiện tại của các thiết bị
_device_states = {dev: False for dev in DEVICES}

def init_gpio():
    """Khởi tạo GPIO mode và setup các pin output."""
    if GPIO is None:
        print("[GPIO] Mock mode - skipping GPIO setup")
        return
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for device, pin in DEVICES.items():
            # OFF mặc định theo cực tính ACTIVE_LOW
            off_level = GPIO.HIGH if ACTIVE_LOW.get(device, False) else GPIO.LOW
            GPIO.setup(pin, GPIO.OUT, initial=off_level)
            _device_states[device] = False  # OFF

        print("[GPIO] Initialized successfully:", list(DEVICES.keys()))
    except Exception as e:
        print(f"[GPIO] Init error: {e}")

def cleanup_gpio():
    """Dọn dẹp GPIO khi thoát chương trình."""
    if GPIO is None:
        return
    try:
        # Đưa tất cả về OFF trước khi nhả GPIO để tránh relay kêu tạch
        for device, pin in DEVICES.items():
            try:
                off_level = GPIO.HIGH if ACTIVE_LOW.get(device, False) else GPIO.LOW
                GPIO.output(pin, off_level)
            except Exception:
                pass
        GPIO.cleanup()
        print("[GPIO] Cleaned up")
    except Exception as e:
        print(f"[GPIO] Cleanup error: {e}")

def set_device(device_name: str, state: bool):
    """
    Bật/tắt một thiết bị.
    
    Args:
        device_name: Tên thiết bị (fan1, fan2, pump, light)
        state: True = ON, False = OFF
    
    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    if device_name not in DEVICES:
        print(f"[GPIO] Device '{device_name}' not found. Available: {list(DEVICES.keys())}")
        return False
    
    pin = DEVICES[device_name]
    
    if GPIO is None:
        print(f"[GPIO Mock] Set {device_name} (pin {pin}) to {'ON' if state else 'OFF'}")
        _device_states[device_name] = state
        return True
    
    try:
        # Tính mức tín hiệu theo cực tính
        if ACTIVE_LOW.get(device_name, False):
            # Relay active-low: ON -> LOW, OFF -> HIGH
            level = GPIO.LOW if state else GPIO.HIGH
        else:
            # Active-high
            level = GPIO.HIGH if state else GPIO.LOW

        GPIO.output(pin, level)
        _device_states[device_name] = state
        status = "ON" if state else "OFF"
        try:
            actual = GPIO.input(pin)
            print(f"[GPIO] {device_name} (GPIO{pin}) -> {status} (level={actual}, active_low={ACTIVE_LOW.get(device_name, False)})")
        except Exception:
            print(f"[GPIO] {device_name} (GPIO{pin}) -> {status}")
        return True
    except Exception as e:
        print(f"[GPIO] Error setting {device_name}: {e}")
        return False

def get_device_state(device_name: str) -> bool:
    """
    Lấy trạng thái hiện tại của một thiết bị.
    
    Args:
        device_name: Tên thiết bị
    
    Returns:
        bool: True nếu đang ON, False nếu OFF hoặc không tồn tại
    """
    return _device_states.get(device_name, False)

def get_all_states() -> dict:
    """
    Lấy trạng thái tất cả thiết bị.
    
    Returns:
        dict: {device_name: bool}
    """
    return _device_states.copy()

def turn_on(device_name: str):
    """Bật thiết bị (shortcut)."""
    return set_device(device_name, True)

def turn_off(device_name: str):
    """Tắt thiết bị (shortcut)."""
    return set_device(device_name, False)

def toggle_device(device_name: str):
    """Đảo trạng thái thiết bị (ON <-> OFF)."""
    current = get_device_state(device_name)
    return set_device(device_name, not current)

def turn_all_off():
    """Tắt tất cả thiết bị."""
    for device in DEVICES:
        set_device(device, False)
    print("[GPIO] All devices turned OFF")

def turn_all_on():
    """Bật tất cả thiết bị."""
    for device in DEVICES:
        set_device(device, True)
    print("[GPIO] All devices turned ON")

# Demo/test function
if __name__ == "__main__":
    print("=== GPIO Controller Test ===")
    init_gpio()
    
    try:
        # Test từng thiết bị
        for device in DEVICES:
            print(f"\nTesting {device}...")
            turn_on(device)
            time.sleep(1)
            print(f"State: {get_device_state(device)}")
            turn_off(device)
            time.sleep(0.5)
        
        # Test all on/off
        print("\nTurn all ON...")
        turn_all_on()
        print("States:", get_all_states())
        time.sleep(2)
        
        print("\nTurn all OFF...")
        turn_all_off()
        print("States:", get_all_states())
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        cleanup_gpio()

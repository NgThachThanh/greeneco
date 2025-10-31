# app/gpio_controller.py
"""
Module điều khiển các thiết bị qua GPIO (relay/transistor).
Mỗi thiết bị được map với một GPIO pin cụ thể.
"""
import time
from typing import Optional
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

# Alias/biệt danh chấp nhận khi người dùng nhập, không phân biệt hoa thường
# Hỗ trợ số thứ tự 1-4, tiếng Việt cơ bản và biến thể có khoảng trắng
ALIASES = {
    "1": "fan1", "fan 1": "fan1", "quat1": "fan1", "quạt1": "fan1", "q1": "fan1",
    "2": "fan2", "fan 2": "fan2", "quat2": "fan2", "quạt2": "fan2", "q2": "fan2",
    "3": "pump",  "bom": "pump",  "bơm": "pump",
    "4": "light", "den": "light", "đèn": "light", "lamp": "light",
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

def normalize_device_name(name: str) -> Optional[str]:
    """Chuẩn hóa tên thiết bị về key trong DEVICES.

    Chấp nhận: hoa/thường, có khoảng trắng, alias và số thứ tự.
    Trả về None nếu không tìm thấy.
    """
    if not isinstance(name, str):
        return None
    key = name.strip().lower()
    if key in DEVICES:
        return key
    # bỏ khoảng trắng để bắt các biến thể như "fan 1"
    key_nospace = key.replace(" ", "")
    if key_nospace in DEVICES:
        return key_nospace
    # alias trực tiếp
    if key in ALIASES:
        return ALIASES[key]
    if key_nospace in ALIASES:
        return ALIASES[key_nospace]
    return None

def init_gpio():
    """Khởi tạo GPIO mode và setup các pin output."""
    if GPIO is None:
        print("[GPIO] Backend: MOCK (RPi.GPIO không sẵn có) - bỏ qua setup phần cứng")
        return
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for device, pin in DEVICES.items():
            # OFF mặc định theo cực tính ACTIVE_LOW
            off_level = GPIO.HIGH if ACTIVE_LOW.get(device, False) else GPIO.LOW
            GPIO.setup(pin, GPIO.OUT, initial=off_level)
            _device_states[device] = False  # OFF
        try:
            ver = getattr(GPIO, "__version__", "unknown")
        except Exception:
            ver = "unknown"
        print(f"[GPIO] Backend: RPi.GPIO v{ver}")
        print("[GPIO] Initialized successfully:", list(DEVICES.keys()))
    except Exception as e:
        print(f"[GPIO] Init error: {e}")

def backend_info() -> str:
    """Trả về thông tin backend GPIO hiện dùng."""
    if GPIO is None:
        return "MOCK"
    try:
        ver = getattr(GPIO, "__version__", "unknown")
    except Exception:
        ver = "unknown"
    return f"RPi.GPIO v{ver}"

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
    resolved = normalize_device_name(device_name)
    if not resolved:
        print(f"[GPIO] Device '{device_name}' không hợp lệ. Hợp lệ: {list(DEVICES.keys())}")
        return False
    device_name = resolved
    pin = DEVICES[device_name]
    
    if GPIO is None:
        print(f"[GPIO Mock] Set {device_name} (pin {pin}) to {'ON' if state else 'OFF'}")
        _device_states[device_name] = state
        return True
    
    try:
        # Đảm bảo cấu hình pin là OUTPUT (phòng khi bị tiến trình khác thay đổi)
        try:
            GPIO.setup(pin, GPIO.OUT)
        except Exception:
            pass

        # Tính mức tín hiệu theo cực tính
        if ACTIVE_LOW.get(device_name, False):
            # Relay active-low: ON -> LOW, OFF -> HIGH
            level = GPIO.LOW if state else GPIO.HIGH
        else:
            # Active-high
            level = GPIO.HIGH if state else GPIO.LOW

        GPIO.output(pin, level)
        # nhỏ giọt thời gian ngắn để phần cứng kịp đáp ứng trước khi đọc lại
        try:
            time.sleep(0.02)
        except Exception:
            pass
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
    resolved = normalize_device_name(device_name)
    if not resolved:
        return False
    return _device_states.get(resolved, False)

def get_all_states() -> dict:
    """
    Lấy trạng thái tất cả thiết bị.
    
    Returns:
        dict: {device_name: bool}
    """
    return _device_states.copy()

def is_on(device_name: str) -> bool:
    """Trả về True nếu thiết bị đang ON (dựa trên mức GPIO thực nếu có)."""
    resolved = normalize_device_name(device_name)
    if not resolved:
        return False
    if GPIO is None:
        return bool(_device_states.get(resolved, False))
    try:
        pin = DEVICES[resolved]
        level = GPIO.input(pin)
        if ACTIVE_LOW.get(resolved, False):
            return level == GPIO.LOW
        else:
            return level == GPIO.HIGH
    except Exception:
        return bool(_device_states.get(resolved, False))

def get_display_status(device_name: str) -> str:
    """Chuẩn hóa nhãn hiển thị "ON"/"OFF" theo trạng thái thực tế phần cứng.

    - Nếu đọc được GPIO: suy ra ON/OFF theo cực tính ACTIVE_LOW
    - Nếu không: fallback về trạng thái logic đã lưu
    """
    return "ON" if is_on(device_name) else "OFF"

def get_polarity(device_name: str) -> Optional[bool]:
    """Lấy cực tính hiện tại: True=active-low, False=active-high."""
    resolved = normalize_device_name(device_name)
    if not resolved:
        return None
    return bool(ACTIVE_LOW.get(resolved, False))

def _apply_output_for_state(device_name: str):
    """Ghi lại mức pin theo trạng thái logic hiện tại và cực tính mới."""
    if GPIO is None:
        return
    resolved = normalize_device_name(device_name)
    if not resolved:
        return
    pin = DEVICES[resolved]
    state = _device_states.get(resolved, False)
    try:
        GPIO.setup(pin, GPIO.OUT)
        if ACTIVE_LOW.get(resolved, False):
            level = GPIO.LOW if state else GPIO.HIGH
        else:
            level = GPIO.HIGH if state else GPIO.LOW
        GPIO.output(pin, level)
    except Exception:
        pass

def set_polarity(device_name: str, active_low: bool) -> bool:
    """Đặt cực tính cho 1 thiết bị và áp mức pin theo trạng thái hiện tại.

    active_low=True: ON -> LOW, OFF -> HIGH
    active_low=False: ON -> HIGH, OFF -> LOW
    """
    resolved = normalize_device_name(device_name)
    if not resolved:
        print(f"[GPIO] Device '{device_name}' không hợp lệ. Hợp lệ: {list(DEVICES.keys())}")
        return False
    ACTIVE_LOW[resolved] = bool(active_low)
    _apply_output_for_state(resolved)
    mode = "active-low" if active_low else "active-high"
    print(f"[GPIO] Đã đặt cực tính {resolved}: {mode}")
    return True

def toggle_polarity(device_name: str) -> bool:
    """Đảo cực tính active-low/active-high cho 1 thiết bị."""
    resolved = normalize_device_name(device_name)
    if not resolved:
        print(f"[GPIO] Device '{device_name}' không hợp lệ. Hợp lệ: {list(DEVICES.keys())}")
        return False
    cur = bool(ACTIVE_LOW.get(resolved, False))
    return set_polarity(resolved, not cur)

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

def diagnose_device(device_name: str, cycles: int = 2, delay: float = 0.5):
    """Chẩn đoán nhanh 1 thiết bị: đọc/ghi mức pin nhiều lần và in thông tin.

    - In cực tính active_low
    - Ghi HIGH/LOW trực tiếp và đọc lại mức GPIO
    - Thử ON/OFF theo logic set_device
    """
    resolved = normalize_device_name(device_name)
    if not resolved:
        print(f"[GPIO] Device '{device_name}' không hợp lệ. Hợp lệ: {list(DEVICES.keys())}")
        return False

    pin = DEVICES[resolved]
    al = ACTIVE_LOW.get(resolved, False)
    print(f"[GPIO DIAG] {device_name}: GPIO{pin}, active_low={al}")

    if GPIO is None:
        print("[GPIO DIAG] Mock mode (không có RPi.GPIO)")
        return False

    try:
        # Đảm bảo pin là output
        GPIO.setup(pin, GPIO.OUT)
        func = GPIO.gpio_function(pin)
        print(f"[GPIO DIAG] Function={func} (GPIO.BCM OUT is {GPIO.OUT})")

        for i in range(cycles):
            # Ghi HIGH trực tiếp
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(delay)
            lv_h = GPIO.input(pin)
            print(f"  Cycle {i+1}: direct HIGH -> level={lv_h}")

            # Ghi LOW trực tiếp
            GPIO.output(pin, GPIO.LOW)
            time.sleep(delay)
            lv_l = GPIO.input(pin)
            print(f"  Cycle {i+1}: direct LOW  -> level={lv_l}")

            # Theo logic thiết bị
            set_device(resolved, True)
            time.sleep(delay)
            lv_on = GPIO.input(pin)
            print(f"  Cycle {i+1}: logic  ON   -> level={lv_on}")

            set_device(resolved, False)
            time.sleep(delay)
            lv_off = GPIO.input(pin)
            print(f"  Cycle {i+1}: logic  OFF  -> level={lv_off}")

        print("[GPIO DIAG] Done. Nếu level thay đổi đúng nhưng relay vẫn sai, khả năng do phần cứng:")
        print("  - Module relay low-level trigger 5V: mức HIGH 3.3V có thể vẫn kéo LED opto sáng -> luôn ON")
        print("  - Giải pháp: cấp 3.3V cho phần input (nếu module hỗ trợ), dùng JD-VCC tách cuộn relay, hoặc thêm transistor/ULN2003")
        return True
    except Exception as e:
        print(f"[GPIO DIAG] Error: {e}")
        return False

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

# file: door_servo.py
from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

# Thông số hay dùng cho đa số servo SG90/MG9xx. Có thể phải tinh chỉnh 2 con số này.
MIN_PW = 0.5/1000   # 0.5 ms
MAX_PW = 2.5/1000   # 2.5 ms

# Nếu servo quay ngược ý muốn, set INVERT=True
INVERT = False

factory = LGPIOFactory()

# GPIO18 = pin 12 trên header
servo = AngularServo(
    pin=18,
    min_angle=-90, max_angle=90,
    min_pulse_width=MIN_PW, max_pulse_width=MAX_PW,
    pin_factory=factory,
    initial_angle=0,
)

def open_door(angle=80):
    """Mở cửa: quay tới +angle độ."""
    a = angle if not INVERT else -angle
    servo.angle = a
    # giữ vài trăm ms để servo đến vị trí rồi thả lỏng để bớt rung/đốt pin
    sleep(0.6)
    servo.detach()

def close_door(angle=80):
    """Đóng cửa: quay về -angle độ."""
    a = -angle if not INVERT else angle
    servo.angle = a
    sleep(0.6)
    servo.detach()

def vent_mid():
    """Mở nửa chừng cho đỡ ngộp."""
    servo.angle = 0 if not INVERT else 0
    sleep(0.6)
    servo.detach()

if __name__ == "__main__":
    # Demo nhanh: mở -> giữa -> đóng
    open_door(80)
    sleep(1)
    vent_mid()
    sleep(1)
    close_door(80)

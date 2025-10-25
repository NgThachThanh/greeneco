from gpiozero import Servo
from time import sleep
from gpiozero.pins.lgpio import LGPIOFactory

# sử dụng lgpio để tương thích với Raspberry Pi 5
factory = LGPIOFactory()
servo = Servo(18, pin_factory=factory, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

while True:
    servo.min()   # 0 độ
    sleep(1)
    servo.mid()   # 90 độ
    sleep(1)
    servo.max()   # 180 độ
    sleep(1)

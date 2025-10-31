# test_gpio.py
import gpiod, time

CHIP = "/dev/gpiochip0"   # đổi nếu gpiodetect báo chip khác
PIN  = 5

chip = gpiod.Chip(CHIP)
cfg  = gpiod.LineSettings(direction=gpiod.LineDirection.OUTPUT)

with chip.request_lines(config={PIN: cfg}) as req:
    print("ON 2s")
    req.set_values({PIN: 1})   # nếu relay active-low thì 1 = OFF
    time.sleep(2)
    print("OFF")
    req.set_values({PIN: 0})

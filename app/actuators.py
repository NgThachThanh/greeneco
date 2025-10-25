# Sau này thay bằng logic thật: gpiozero LED/OutputDevice, relay, v.v.
class Actuators:
    def __init__(self, rules=None):
        self.rules = rules or []
    def apply(self, snapshot: dict):
        # snapshot: {"co2_ppm":..., "temp_c":..., ...}
        pass

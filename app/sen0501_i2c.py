# app/sen0501_i2c.py
import math, inspect, time

# DFRobot lib có thể đặt tên I2C hoặc IIC
try:
    from DFRobot_Environmental_Sensor import DFRobot_Environmental_Sensor_I2C as EnvI2C
except ImportError:
    from DFRobot_Environmental_Sensor import DFRobot_Environmental_Sensor_IIC as EnvI2C

class Sen0501:
    """
    Wrapper gọn cho DFRobot SEN0501 (I2C).
    API lib của bạn (so theo getters đã in ra):
      - get_temperature(unist)    # unist: 0 = °C
      - get_humidity()
      - get_luminousintensity()
      - get_atmosphere_pressure(soc)  # truyền 0
      - get_elevation()
      - get_ultraviolet_intensity(soc)  # truyền 0
    """

    def __init__(self, bus=1, addr=0x22):
        self.sensor = EnvI2C(bus, addr)
        self.sensor.begin()

        # bind đúng hàm theo lib thực tế
        self._get_temp = getattr(self.sensor, "get_temperature")
        self._get_humi = getattr(self.sensor, "get_humidity")
        self._get_lux  = getattr(self.sensor, "get_luminousintensity")
        self._get_pres = getattr(self.sensor, "get_atmosphere_pressure")
        self._get_alt  = getattr(self.sensor, "get_elevation")
        self._get_uv   = getattr(self.sensor, "get_ultraviolet_intensity")

    def read(self):
        """Đọc một lần, trả dict số float. Nếu lỗi trả nan."""
        try:    t = self._get_temp(0)          # 0 = Celsius
        except: t = math.nan
        try:    h = self._get_humi()
        except: h = math.nan
        try:    uv = self._get_uv(0)           # pass 0 cho soc
        except: uv = math.nan
        try:    lx = self._get_lux()
        except: lx = math.nan
        try:    p  = self._get_pres(0)         # pass 0 cho soc
        except: p  = math.nan
        try:    alt= self._get_alt()
        except: alt= math.nan

        return {
            "temp_c": float(t),
            "rh_pct": float(h),
            "uv_mw_cm2": float(uv),
            "lux": float(lx),
            "hpa": float(p),
            "alt_m": float(alt),
        }

    def stream(self, hz=1):
        dt = 1.0 / max(1, int(hz))
        while True:
            yield self.read()
            time.sleep(dt)

# Cho phép test nhanh file này độc lập
if __name__ == "__main__":
    s = Sen0501()
    print(s.read())

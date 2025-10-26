# app/sen0501_i2c.py
# -*- coding: utf-8 -*-
import time
import math

# Thử nhiều cách import driver DFRobot cho SEN0501, tuyệt đối KHÔNG import thẳng ở top-level như bản cũ
EnvI2C = None
_import_errors = []

def _try_import(path, cls):
    try:
        mod = __import__(path, fromlist=[cls])
        return getattr(mod, cls)
    except Exception as e:
        _import_errors.append((f"{path}.{cls}", f"{type(e).__name__}: {e}"))
        return None

# 1) Ưu tiên bản driver đặt trong app/ nếu có
if EnvI2C is None:
    EnvI2C = _try_import("app.DFRobot_Environmental_Sensor", "DFRobot_Environmental_Sensor_I2C")
if EnvI2C is None:
    EnvI2C = _try_import("app.DFRobot_Environmental_Sensor", "DFRobot_Environmental_Sensor_IIC")

# 2) Thử package top-level đã cài qua pip
if EnvI2C is None:
    EnvI2C = _try_import("DFRobot_Environmental_Sensor", "DFRobot_Environmental_Sensor_I2C")
if EnvI2C is None:
    EnvI2C = _try_import("DFRobot_Environmental_Sensor", "DFRobot_Environmental_Sensor_IIC")

# 3) Một số fork dùng tên viết thường
if EnvI2C is None:
    EnvI2C = _try_import("dfrobot_environmental_sensor", "DFRobot_Environmental_Sensor_I2C")

class _DummySEN0501:
    """Fallback để app không chết khi thiếu driver/sensor."""
    def __init__(self, *args, **kwargs):
        pass
    def begin(self):
        return True
    def read_all(self):
        return {
            "temp_c": None,
            "rh_pct": None,
            "lux": None,
            "uv_mw_cm2": None,
            "hpa": None,
            "alt_m": None,
        }

class Sen0501:
    """
    Wrapper gọn cho DFRobot SEN0501 (I2C).

    read() trả dict:
      {
        "temp_c": float|None,
        "rh_pct": float|None,
        "lux": float|None,
        "uv_mw_cm2": float|None,
        "hpa": float|None,
        "alt_m": float|None
      }
    """
    def __init__(self, bus=1, addr=0x22, allow_dummy=True):
        self._dummy_mode = False
        if EnvI2C is None:
            if allow_dummy:
                self.sensor = _DummySEN0501()
                self._dummy_mode = True
            else:
                lines = [
                    "Không tìm thấy driver DFRobot cho SEN0501.",
                    "Cài 1 trong các gói vào đúng virtualenv:",
                    "  pip install DFRobot_Environmental_Sensor",
                    "  hoặc pip install git+https://github.com/DFRobot/DFRobot_Environmental_Sensor_Python.git",
                    "Đã thử import các đường dẫn sau mà thất bại:"
                ]
                for name, err in _import_errors:
                    lines.append(f"  - {name} -> {err}")
                raise ImportError("\n".join(lines))
        else:
            self.sensor = EnvI2C(bus, addr)
            if hasattr(self.sensor, "begin"):
                try:
                    self.sensor.begin()
                except Exception:
                    pass

    def _safe_get(self, fn, *args):
        try:
            return fn(*args)
        except Exception:
            return None

    def read(self):
        if self._dummy_mode:
            return self.sensor.read_all()

        get_temp = getattr(self.sensor, "get_temperature", None)
        get_rh   = getattr(self.sensor, "get_humidity", None)
        get_lux  = getattr(self.sensor, "get_luminousintensity", None)
        get_uv   = getattr(self.sensor, "get_ultraviolet_intensity", None)
        get_hpa  = getattr(self.sensor, "get_atmosphere_pressure", None)
        get_alt  = getattr(self.sensor, "get_elevation", None)

        t  = self._safe_get(get_temp, 0) if callable(get_temp) else None
        h  = self._safe_get(get_rh)      if callable(get_rh)   else None
        lx = self._safe_get(get_lux)     if callable(get_lux)  else None
        uv = self._safe_get(get_uv, 0)   if callable(get_uv)   else None
        p  = self._safe_get(get_hpa)     if callable(get_hpa)  else None
        alt= self._safe_get(get_alt)     if callable(get_alt)  else None

        def f(x):
            try:
                return float(x)
            except Exception:
                return None

        return {
            "temp_c": f(t),
            "rh_pct": f(h),
            "lux": f(lx),
            "uv_mw_cm2": f(uv),
            "hpa": f(p),
            "alt_m": f(alt),
        }

    def stream(self, hz=1):
        dt = 1.0 / max(1, int(hz))
        while True:
            yield self.read()
            time.sleep(dt)

if __name__ == "__main__":
    s = Sen0501()
    print(s.read())

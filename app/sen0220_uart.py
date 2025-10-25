# app/sen0220_uart.py
import serial, time

REQ = bytes([0xFF,0x01,0x86,0,0,0,0,0,0x79])

def _ok(f: bytes) -> bool:
    if len(f) != 9 or f[0] != 0xFF or f[1] != 0x86: 
        return False
    calc = (0xFF - (sum(f[1:8]) & 0xFF) + 1) & 0xFF
    return f[8] == calc

class Sen0220:
    def __init__(self, port="/dev/ttyAMA0", baud=9600):
        self.ser = serial.Serial(port, baud, bytesize=8, parity="N", stopbits=1, timeout=0.25)

    def read(self):
        self.ser.reset_input_buffer()
        self.ser.write(REQ); self.ser.flush()
        resp = self.ser.read(9)
        if _ok(resp):
            return {"co2_ppm": resp[2]*256 + resp[3], "raw": resp}
        return {"co2_ppm": None, "raw": resp}

    def stream(self, hz=1):
        dt = 1.0 / max(1, int(hz))
        while True:
            yield self.read()
            time.sleep(dt)

# Chỉ chạy test khi gọi trực tiếp file này, KHÔNG khi import
if __name__ == "__main__":
    s = Sen0220()
    for _ in range(5):
        x = s.read()
        print("CO2 =", x["co2_ppm"], "ppm", " raw=", x["raw"].hex(' '))
        time.sleep(1)

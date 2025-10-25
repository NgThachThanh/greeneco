# app/es_soil7.py
import time
import minimalmodbus, serial

# Map 0x0000..0x0007 theo bảng bạn chốt
REG_START = 0x0000
REG_COUNT = 8
FIELDS = [
    ("temp_C",   0.1),   # 0x0000
    ("hum_%",    0.1),   # 0x0001
    ("ec_uS_cm", 1.0),   # 0x0002
    ("pH",       0.01),  # 0x0003
    ("N_mgkg",   1.0),   # 0x0004
    ("P_mgkg",   1.0),   # 0x0005
    ("K_mgkg",   1.0),   # 0x0006
    ("salt_mgL", 1.0),   # 0x0007
]

class ESSoil7:
    def __init__(self, port="/dev/ttyUSB0", slave=1, baud=9600,
                 timeout=2.0, inter_byte_timeout=0.15):
        self.port   = port
        self.slave  = slave
        self.baud   = baud
        self.timeout = timeout
        self.ibt     = inter_byte_timeout
        self._inst_obj = None   # <- KHÔNG trùng tên hàm nữa

    def _create_inst(self):
        inst = minimalmodbus.Instrument(self.port, self.slave, minimalmodbus.MODE_RTU)
        s = inst.serial
        s.baudrate = self.baud
        s.bytesize = 8
        s.parity   = serial.PARITY_NONE  # 8N1
        s.stopbits = 1
        s.timeout  = self.timeout
        s.inter_byte_timeout = self.ibt
        inst.clear_buffers_before_each_transaction = True
        inst.close_port_after_each_call = True
        return inst

    def _get_inst(self):
        if self._inst_obj is None:
            self._inst_obj = self._create_inst()
        return self._inst_obj

    def read_raw(self):
        """Trả list 8 U16 theo thứ tự 0x0000..0x0007; thử block, fail thì từng ô."""
        m = self._get_inst()
        try:
            return m.read_registers(REG_START, REG_COUNT, functioncode=3)
        except Exception:
            vals = []
            for i in range(REG_COUNT):
                vals.append(m.read_register(REG_START + i, 0, functioncode=3))
                time.sleep(0.08)
            return vals

    def read(self):
        raw = self.read_raw()
        return {name: raw[i] * scale for i, (name, scale) in enumerate(FIELDS)}

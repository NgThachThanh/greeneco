# app/dashboard.py
import time, shutil, math, sys
import select as _select
from app.sen0501_i2c import Sen0501
from app.sen0220_uart import Sen0220
from app.es_soil7 import ESSoil7

def _fmt(x, unit="", nd=2):
    try:
        v = float(x)
        if math.isnan(v):
            return "nan"
        return f"{v:.{nd}f}{unit}"
    except Exception:
        return "nan"

def _panel_lines_env(a, b):
    co2 = "nan" if b.get("co2_ppm") is None else str(int(b["co2_ppm"]))
    return [
        "┌ KHÔNG KHÍ (ENV) ─────────────",
        f"  Nhiệt độ không khí     : {_fmt(a['temp_c'],'°C')}",
        f"  Độ ẩm không khí        : {_fmt(a['rh_pct'],'%')}",
        f"  Áp suất khí quyển      : {_fmt(a['hpa'],' hPa',1)}",
        f"  Ánh sáng (lux)         : {_fmt(a['lux'],'',1)}",
        f"  Tia UV                 : {_fmt(a['uv_mw_cm2'],' mW/cm²',3)}",
        f"  Độ cao ước tính        : {_fmt(a['alt_m'],' m',1)}",
        f"  CO₂                    : {co2} ppm",
        "└──────────────────────────────",
    ]

def _panel_lines_soil(c):
    if c is None:
        return [
            "┌ ĐẤT (SOIL) ───────────────────",
            "  Nhiệt độ đất          : nan",
            "  Độ ẩm đất             : nan",
            "  Độ dẫn điện đất (EC)  : nan",
            "  Độ pH đất             : nan",
            "  Đạm (N)               : nan",
            "  Lân (P)               : nan",
            "  Kali (K)              : nan",
            "  Muối trong đất        : nan",
            "└──────────────────────────────",
        ]
    return [
        "┌ ĐẤT (SOIL) ───────────────────",
        f"  Nhiệt độ đất          : {_fmt(c['temp_C'],'°C')}",
        f"  Độ ẩm đất             : {_fmt(c['hum_%'],'%')}",
        f"  Độ dẫn điện đất (EC)  : {_fmt(c['ec_uS_cm'],' µS/cm',0)}",
        f"  Độ pH đất             : {_fmt(c['pH'],'',2)}",
        f"  Đạm (N)               : {_fmt(c['N_mgkg'],' mg/kg',0)}",
        f"  Lân (P)               : {_fmt(c['P_mgkg'],' mg/kg',0)}",
        f"  Kali (K)              : {_fmt(c['K_mgkg'],' mg/kg',0)}",
        f"  Muối trong đất        : {_fmt(c['salt_mgL'],' mg/L',0)}",
        "└──────────────────────────────",
    ]

def _side_by_side(left_lines, right_lines, total_cols, sep="  │  "):
    sep_w = len(sep)
    panel_w = max(34, (total_cols - sep_w) // 2)
    L = [l.ljust(panel_w)[:panel_w] for l in left_lines]
    R = [r.ljust(panel_w)[:panel_w] for r in right_lines]
    n = max(len(L), len(R))
    L += [" " * panel_w] * (n - len(L))
    R += [" " * panel_w] * (n - len(R))
    return [L[i] + sep + R[i] for i in range(n)]

def run(cfg):
    s1 = Sen0501(bus=cfg["sen0501"]["i2c_bus"], addr=int(cfg["sen0501"]["address"]))
    s2 = Sen0220(port=cfg["sen0220"]["port"], baud=cfg["sen0220"]["baud"])
    soil = ESSoil7(port=cfg["soil7"]["port"], slave=cfg["soil7"]["slave"],
                   baud=cfg["soil7"]["baud"], timeout=cfg["soil7"]["timeout"],
                   inter_byte_timeout=cfg["soil7"]["inter_byte_timeout"])

    hz = max(1, int(cfg["sen0501"].get("read_hz", 1)))
    dt = 1.0 / hz

    print("Realtime dashboard. Nhấn q để thoát (hoặc Ctrl+C).")
    time.sleep(0.3)

    # Thiết lập đọc phím không chặn nếu có TTY
    kb_enabled = False
    fd = None; _termios = None; _tty = None; old_attr = None
    try:
        import termios as _termios, tty as _tty
        fd = sys.stdin.fileno()
        old_attr = _termios.tcgetattr(fd)
        _tty.setcbreak(fd)
        kb_enabled = True
    except Exception:
        kb_enabled = False

    try:
        warn_once = False
        while True:
            a = s1.read()
            b = s2.read()
            c = None
            try:
                c = soil.read()
            except Exception as e:
                if not warn_once:
                    print("Soil read error:", e, file=sys.stderr)
                    warn_once = True

            cols = shutil.get_terminal_size((100, 24)).columns
            title = "GreenEco Live"
            bar = "─" * max(0, cols - len(title) - 1)

            env_lines = _panel_lines_env(a, b)
            soil_lines = _panel_lines_soil(c)

            sys.stdout.write("\x1b[2J\x1b[H")
            if cols >= 90:
                sys.stdout.write(f"{title} {bar}\n")
                lines = _side_by_side(env_lines, soil_lines, cols)
                sys.stdout.write("\n".join(lines) + "\n")
            else:
                sys.stdout.write(f"{title}\n")
                sys.stdout.write("\n".join(env_lines) + "\n\n")
                sys.stdout.write("\n".join(soil_lines) + "\n")
            sys.stdout.flush()

            # Kiểm tra phím 'q' để thoát
            if kb_enabled:
                try:
                    if _select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1)
                        if ch and ch.lower() == 'q':
                            break
                except Exception:
                    pass
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        # Khôi phục chế độ terminal nếu đã bật cbreak
        try:
            if kb_enabled and old_attr is not None:
                _termios.tcsetattr(fd, _termios.TCSADRAIN, old_attr)
        except Exception:
            pass

#!/usr/bin/env python3
import time, csv, os, sys, json
from datetime import datetime
from app.config import load_config
from app.camera_preview import run as run_cam
from app.sen0501_i2c import Sen0501
from app.sen0220_uart import Sen0220
from app.es_soil7 import ESSoil7
from app.dashboard import run as run_dashboard
from app.json_export import collect_all, write_json, append_jsonl
from app.uploader import post_file
from app.cam_capture_cli import capture_jpeg_cli
from app.uploader_greenimage import upload_green_image

# Cấu hình cho upload ảnh lên Render
IMAGE_UPLOAD_CFG = {
    "api_base": "https://h2-api-z7sq.onrender.com",
    "device_id": "CAM-01",
    "img_dir": os.path.expanduser("~/greeneco_out/images"),
    "auth_token": None,  # nếu server yêu cầu thì nhét vào
}

# GPIO control sẽ được import lazy để tránh lỗi trên máy không có RPi.GPIO
_gpio_initialized = False

def read_once_0501(cfg):
    s = Sen0501(bus=cfg["sen0501"]["i2c_bus"], addr=int(cfg["sen0501"]["address"]))
    print(s.read())

def stream_co2(cfg):
    s = Sen0220(port=cfg["sen0220"]["port"], baud=cfg["sen0220"]["baud"])
    hz = max(1, int(cfg["sen0220"].get("read_hz", 1)))
    dt = 1.0 / hz
    print("Streaming CO2. Nhấn q để dừng (hoặc Ctrl+C).")
    fd = None; old_attr = None; kb_enabled = False
    try:
        # Thiết lập đọc phím không chặn trên Linux/TTY
        import sys as _sys
        import select as _select
        try:
            import termios as _termios, tty as _tty
            fd = _sys.stdin.fileno()
            old_attr = _termios.tcgetattr(fd)
            _tty.setcbreak(fd)
            kb_enabled = True
        except Exception:
            kb_enabled = False

        while True:
            # Kiểm tra phím 'q' để thoát
            if kb_enabled:
                try:
                    if _select.select([_sys.stdin], [], [], 0)[0]:
                        ch = _sys.stdin.read(1)
                        if ch and ch.lower() == 'q':
                            break
                except Exception:
                    pass
            print(s.read())
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        # Khôi phục chế độ terminal
        try:
            if kb_enabled and old_attr is not None:
                _termios.tcsetattr(fd, _termios.TCSADRAIN, old_attr)
        except Exception:
            pass

def read_once_soil(cfg):
    soil = ESSoil7(port=cfg["soil7"]["port"], slave=cfg["soil7"]["slave"],
                   baud=cfg["soil7"]["baud"], timeout=cfg["soil7"]["timeout"],
                   inter_byte_timeout=cfg["soil7"]["inter_byte_timeout"])
    print(soil.read())

def log_soil(cfg):
    soil = ESSoil7(port=cfg["soil7"]["port"], slave=cfg["soil7"]["slave"],
                   baud=cfg["soil7"]["baud"], timeout=cfg["soil7"]["timeout"],
                   inter_byte_timeout=cfg["soil7"]["inter_byte_timeout"])
    path = cfg["soil7"]["csv_path"]
    hz = max(1, int(cfg["soil7"].get("read_hz", 1)))
    dt = 1.0 / hz
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts","temp_C","hum_%","ec_uS_cm","pH","N_mgkg","P_mgkg","K_mgkg","salt_mgL"])
        while True:
            try:
                d = soil.read()
                ts = datetime.now().isoformat(timespec="seconds")
                w.writerow([ts, d["temp_C"], d["hum_%"], d["ec_uS_cm"], d["pH"],
                            d["N_mgkg"], d["P_mgkg"], d["K_mgkg"], d["salt_mgL"]])
                f.flush()
                print(ts, d)
            except Exception as e:
                print("Soil read error:", e, file=sys.stderr)
            time.sleep(dt)

def combined_log_all(cfg):
    s1 = Sen0501(bus=cfg["sen0501"]["i2c_bus"], addr=int(cfg["sen0501"]["address"]))
    s2 = Sen0220(port=cfg["sen0220"]["port"], baud=cfg["sen0220"]["baud"])
    soil = ESSoil7(port=cfg["soil7"]["port"], slave=cfg["soil7"]["slave"],
                   baud=cfg["soil7"]["baud"], timeout=cfg["soil7"]["timeout"],
                   inter_byte_timeout=cfg["soil7"]["inter_byte_timeout"])
    path = cfg["logging"]["output"]
    hz = max(1, int(cfg["logging"].get("interval_hz", 1)))
    dt = 1.0 / hz
    print(f"Ghi log tổng hợp vào: {path} @ {hz} Hz. Nhấn q để dừng (hoặc Ctrl+C).")

    # Thiết lập đọc phím không chặn nếu có TTY
    fd = None; old_attr = None; kb_enabled = False
    try:
        import sys as _sys
        import select as _select
        try:
            import termios as _termios, tty as _tty
            fd = _sys.stdin.fileno()
            old_attr = _termios.tcgetattr(fd)
            _tty.setcbreak(fd)
            kb_enabled = True
        except Exception:
            kb_enabled = False

        os.makedirs(os.path.dirname(path), exist_ok=True)
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts","temp_c","rh_pct","lux","uv_mw_cm2","hpa","alt_m",
                            "co2_ppm",
                            "soil_temp_C","soil_hum_%","soil_ec_uS_cm","soil_pH","soil_N","soil_P","soil_K","soil_salt_mgL"])
            try:
                while True:
                    # Kiểm tra phím 'q' để thoát
                    if kb_enabled:
                        try:
                            if _select.select([_sys.stdin], [], [], 0)[0]:
                                ch = _sys.stdin.read(1)
                                if ch and ch.lower() == 'q':
                                    break
                        except Exception:
                            pass

                    try:
                        a = s1.read()
                        b = s2.read()
                        c = soil.read()
                        ts = datetime.now().isoformat(timespec="seconds")
                        row = [ts, a["temp_c"], a["rh_pct"], a["lux"], a["uv_mw_cm2"], a["hpa"], a["alt_m"],
                               b["co2_ppm"],
                               c["temp_C"], c["hum_%"], c["ec_uS_cm"], c["pH"], c["N_mgkg"], c["P_mgkg"], c["K_mgkg"], c["salt_mgL"]]
                        print(row)
                        w.writerow(row); f.flush()
                    except Exception as e:
                        print("Combined read error:", e, file=sys.stderr)
                    time.sleep(dt)
            except KeyboardInterrupt:
                pass
    finally:
        # Khôi phục chế độ terminal
        try:
            if kb_enabled and old_attr is not None:
                _termios.tcsetattr(fd, _termios.TCSADRAIN, old_attr)
        except Exception:
            pass

def export_json_once(cfg):
    data = collect_all(cfg)
    path = cfg["export"]["json_path"]
    write_json(path, data)
    print(f"Đã ghi snapshot JSON vào: {path}")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def stream_jsonl(cfg):
    path = cfg["export"]["jsonl_path"]
    hz = max(1, int(cfg["logging"].get("interval_hz", 1)))
    dt = 1.0 / hz
    print(f"Ghi JSONL liên tục vào: {path} @ {hz} Hz. Nhấn q để dừng (hoặc Ctrl+C).")
    fd = None; old_attr = None; kb_enabled = False
    try:
        # Thiết lập đọc phím không chặn trên Linux/TTY
        import sys as _sys
        import select as _select
        try:
            import termios as _termios, tty as _tty
            fd = _sys.stdin.fileno()
            old_attr = _termios.tcgetattr(fd)
            _tty.setcbreak(fd)
            kb_enabled = True
        except Exception:
            kb_enabled = False

        while True:
            # Kiểm tra phím 'q' để thoát
            if kb_enabled:
                try:
                    if _select.select([_sys.stdin], [], [], 0)[0]:
                        ch = _sys.stdin.read(1)
                        if ch and ch.lower() == 'q':
                            break
                except Exception:
                    pass

            data = collect_all(cfg)
            append_jsonl(path, data)
            # in gọn cho biết sống
            print(data["ts"], "ENV.T=", data["env"]["temp_c"], "CO2=", data["co2"]["ppm"],
                  "SOIL.pH=", None if data["soil"] is None else data["soil"]["ph"])
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        # Khôi phục chế độ terminal
        try:
            if kb_enabled and old_attr is not None:
                _termios.tcsetattr(fd, _termios.TCSADRAIN, old_attr)
        except Exception:
            pass

def servo_menu(cfg=None):
    """Menu điều khiển servo cửa: mở/đóng/giữa/đặt góc.
    Import chậm để tránh side-effect trên máy không có GPIO.
    """
    try:
        from app import servo as door_servo
    except Exception as e:
        print("Không thể import servo module:", e)
        return

    while True:
        print("\n=== Servo Control ===")
        print("1) Mở cửa (open_door, +angle)")
        print("2) Đóng cửa (close_door, -angle)")
        print("3) Về giữa (vent_mid)")
        print("4) Đặt góc tùy ý (-90..90)")
        print("5) Thoát menu servo")
        ch = input("Chọn: ").strip()
        if ch == "1":
            try:
                door_servo.open_door()
                print("Đã mở cửa (mặc định +80°)")
            except Exception as e:
                print("Lỗi open_door:", e)
        elif ch == "2":
            try:
                door_servo.close_door()
                print("Đã đóng cửa (mặc định -80°)")
            except Exception as e:
                print("Lỗi close_door:", e)
        elif ch == "3":
            try:
                door_servo.vent_mid()
                print("Đã đưa về giữa (0°)")
            except Exception as e:
                print("Lỗi vent_mid:", e)
        elif ch == "4":
            try:
                s = input("Nhập góc (-90..90): ").strip()
                angle = float(s)
                if angle < -90: angle = -90
                if angle > 90: angle = 90
                door_servo.servo.angle = angle
                time.sleep(0.6)
                try:
                    door_servo.servo.detach()
                except Exception:
                    pass
                print(f"Đã đặt góc {angle}°")
            except Exception as e:
                print("Lỗi đặt góc:", e)
        elif ch == "5":
            break
        else:
            print("Lựa chọn không hợp lệ.")

def gpio_control_menu(cfg=None):
    """Menu điều khiển GPIO devices: fan, pump, light."""
    global _gpio_initialized
    
    try:
        from app import gpio_controller as gpio
    except Exception as e:
        print(f"Không thể import GPIO module: {e}")
        return
    
    # Khởi tạo GPIO lần đầu
    if not _gpio_initialized:
        gpio.init_gpio()
        _gpio_initialized = True
    
    while True:
        states = gpio.get_all_states()
        print("\n=== GPIO Control ===")
        print("Trạng thái hiện tại:")
        for dev, state in states.items():
            pin = gpio.DEVICES[dev]
            status = "ON" if state else "OFF"
            print(f"  {dev:8} (pin {pin:2}) -> {status}")
        
        print("\nTùy chọn:")
        print("1) Bật thiết bị")
        print("2) Tắt thiết bị")
        print("3) Đảo trạng thái (toggle)")
        print("4) Bật tất cả")
        print("5) Tắt tất cả")
        print("6) Gửi trạng thái lên server")
        print("7) Thoát menu GPIO")
        
        ch = input("Chọn: ").strip()
        
        if ch == "1":
            dev = input("Tên thiết bị (fan1/fan2/pump/light): ").strip()
            gpio.turn_on(dev)
        elif ch == "2":
            dev = input("Tên thiết bị (fan1/fan2/pump/light): ").strip()
            gpio.turn_off(dev)
        elif ch == "3":
            dev = input("Tên thiết bị (fan1/fan2/pump/light): ").strip()
            gpio.toggle_device(dev)
        elif ch == "4":
            gpio.turn_all_on()
        elif ch == "5":
            gpio.turn_all_off()
        elif ch == "6":
            try:
                # Gửi kèm với sensor data
                from app.json_export import collect_all
                from app.uploader import post_dict
                
                print("Đang đọc sensors và GPIO...")
                data = collect_all(cfg, include_gpio=True)
                
                print("Đang gửi lên server...")
                code, text = post_dict(data)
                print(f"[Upload] POST OK: {code}")
                print(text)
            except Exception as e:
                print(f"[Upload] Lỗi: {e}")
                import traceback
                traceback.print_exc()
        elif ch == "7":
            break
        else:
            print("Lựa chọn không hợp lệ.")

def menu_upload_image_once():
    """Chụp ảnh từ camera và gửi lên server Render."""
    try:
        os.makedirs(IMAGE_UPLOAD_CFG["img_dir"], exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        img_path = os.path.join(IMAGE_UPLOAD_CFG["img_dir"], f"{ts}.jpg")
        
        print(f"[Camera] Đang chụp ảnh lưu vào: {img_path}")
        img_path, _ = capture_jpeg_cli(img_path, width=1280, height=720, quality=80)
        print(f"[Camera] Đã chụp thành công: {img_path}")
        
        print(f"[Upload] Đang gửi ảnh lên {IMAGE_UPLOAD_CFG['api_base']}...")
        resp = upload_green_image(
            IMAGE_UPLOAD_CFG["api_base"], 
            img_path, 
            IMAGE_UPLOAD_CFG["device_id"], 
            token=IMAGE_UPLOAD_CFG["auth_token"]
        )
        print("[Upload] Thành công! Response:", resp)
    except Exception as e:
        print(f"[Lỗi] Không thể chụp/gửi ảnh: {e}", file=sys.stderr)

def upload_snapshot(cfg=None):
    """
    Đọc sensors + GPIO và gửi lên server (không qua file).
    """
    try:
        from app.json_export import collect_all
        from app.uploader import post_dict
        
        print("[Upload] Đang đọc sensors và GPIO...")
        data = collect_all(cfg, include_gpio=True)
        
        print("[Upload] Đang gửi lên server...")
        code, text = post_dict(data)
        print(f"[Upload] POST OK: {code}")
        print(text)
    except Exception as e:
        print(f"[Upload] LỖI: {e}")
        import traceback
        traceback.print_exc()

def main_menu():
    cfg = load_config("config/settings.yml")
    while True:
        print("\n=== GreenEco Menu ===")
        print("1) Camera preview")
        print("2) Đọc SEN0501 1 lần")
        print("3) Stream CO2 SEN0220")
        print("4) Ghi log tổng hợp (ENV + CO2 + SOIL)")
        print("5) Live dashboard (realtime)")
        print("6) Đọc Soil 7-in-1 1 lần")
        print("7) Ghi log Soil 7-in-1")
        print("8) Thoát")
        print("9) Xuất 1 file JSON (snapshot)")
        print("10) Ghi JSONL liên tục (để upload)")
        print("11) Gửi snapshot lên server")
        print("12) Điều khiển Servo (mở/đóng/giữa/góc)")
        print("13) Chụp & gửi ảnh (Render)")
        print("14) Điều khiển GPIO (Fan/Pump/Light)")

        choice = input("Chọn: ").strip()
        if   choice == "1":
            try:
                cam_cfg = cfg.get("camera", {})
                res = tuple(cam_cfg.get("resolution", (1280, 720)))
                run_cam(res)
            except Exception as e:
                print(f"Lỗi camera preview: {e}")
        elif choice == "2": read_once_0501(cfg)
        elif choice == "3": stream_co2(cfg)
        elif choice == "4": combined_log_all(cfg)
        elif choice == "5": run_dashboard(cfg)
        elif choice == "6": read_once_soil(cfg)
        elif choice == "7": log_soil(cfg)
        elif choice == "8": break
        elif choice == "9": export_json_once(cfg)
        elif choice == "10": stream_jsonl(cfg)
        elif choice == "11": upload_snapshot(cfg)
        elif choice == "12": servo_menu(cfg)
        elif choice == "13": menu_upload_image_once()
        elif choice == "14": gpio_control_menu(cfg)
        else:
            print("Lựa chọn không hợp lệ.")

if __name__ == "__main__":
    main_menu()

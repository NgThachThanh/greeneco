# app/camera_preview.py
from picamera2 import Picamera2, Preview
import cv2
import os
import time
import shutil
import subprocess
import contextlib

def run(res=(1280, 720)):
    def _fallback_cli():
        cmd = None
        if shutil.which("rpicam-hello"):
            cmd = ["rpicam-hello", "-t", "0"]
        elif shutil.which("libcamera-hello"):
            cmd = ["libcamera-hello", "-t", "0"]
        if cmd is None:
            print("Không tìm thấy rpicam-hello/libcamera-hello để fallback.")
            return
        print("Fallback CLI preview (Ctrl+C để thoát):", " ".join(cmd))
        try:
            subprocess.run(cmd, check=False)
        except KeyboardInterrupt:
            pass

    # 1) Kiểm tra GUI trước, nếu không có thì gọi CLI ngay, tránh mở camera sớm gây "in use"
    highgui_ok = True
    try:
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            highgui_ok = False
        else:
            cv2.namedWindow("__probe__")
            cv2.destroyWindow("__probe__")
    except Exception:
        highgui_ok = False

    if not highgui_ok:
        print("OpenCV GUI không khả dụng. Dùng CLI preview (rpicam-hello/libcamera-hello)...")
        _fallback_cli()
        return

    # 2) Có GUI: chạy đường OpenCV
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": (1280, 720)}))

    try:
        cam.start()
        print("Preview running. Nhấn q để thoát.")
        while True:
            frame = cam.capture_array()
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif frame.ndim == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imshow("Greenhouse Camera (Pi 5)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        msg = str(e).lower()
        print(f"Camera preview lỗi: {e}")
        # Đảm bảo giải phóng camera trước khi fallback
        with contextlib.suppress(Exception):
            cam.stop()
        with contextlib.suppress(Exception):
            cam.close()
        # Xung đột event loop → dùng CLI luôn
        if "event loop" in msg:
            print("Gặp xung đột event loop. Chuyển sang CLI preview cho ổn định...")
            _fallback_cli()
        else:
            # Lỗi khác → ưu tiên CLI thay vì DRM để tránh xung đột EGL
            print("Chuyển sang CLI preview để ổn định...")
            _fallback_cli()
    finally:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        with contextlib.suppress(Exception):
            cam.stop()
        with contextlib.suppress(Exception):
            cam.close()

# Cho chạy độc lập khi bạn test file này riêng
if __name__ == "__main__":
    run()

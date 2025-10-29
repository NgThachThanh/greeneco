# app/camera_preview.py
from picamera2 import Picamera2, Preview
import cv2
import os
import time

def run(res=(1280, 720)):
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": (1280, 720)}))
    cam.start()

    # Kiểm tra nhanh xem OpenCV HighGUI có khả dụng (có DISPLAY/Wayland và tạo window được) không
    highgui_ok = True
    try:
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            highgui_ok = False
        else:
            cv2.namedWindow("__probe__")
            cv2.destroyWindow("__probe__")
    except Exception:
        highgui_ok = False

    # Nếu không dùng được OpenCV GUI (ví dụ chạy qua SSH không có DISPLAY), fallback sang DRM preview
    if not highgui_ok:
        print("OpenCV GUI không khả dụng. Dùng Picamera2 DRM preview (Ctrl+C để thoát)...")
        try:
            cam.start_preview(Preview.DRM)
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            cam.stop()
        return

    print("Preview running. Nhấn q để thoát.")
    try:
        while True:
            frame = cam.capture_array()
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif frame.ndim == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            cv2.imshow("Greenhouse Camera (Pi 5)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        cam.stop()

# Cho chạy độc lập khi bạn test file này riêng
if __name__ == "__main__":
    run()

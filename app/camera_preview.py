# app/camera_preview.py
# -*- coding: utf-8 -*-

def run(resolution=(1280, 720), backend="auto"):
    """
    Camera preview an toàn và đúng màu:
      - Nếu Picamera2 + OpenCV HighGUI OK: hiển thị bằng cv2.imshow
        + Chuyển RGBA/XRGB/XBGR -> BGR hoặc RGB -> BGR để đúng màu.
      - Nếu Picamera2 có nhưng HighGUI không OK: dùng Picamera2 Preview (QTGL),
        nếu QTGL lỗi do event loop/Qt/EGL thì fallback sang DRM; nếu vẫn lỗi thì chạy không preview.
      - Nếu không có Picamera2 nhưng HighGUI OK: fallback USB cam (/dev/video0).
      - Nếu không có gì: có thể dùng CLI preview qua rpicam-hello (backend='cli').
    Nhấn 'q' để thoát (với OpenCV), hoặc Ctrl+C khi dùng QTGL/DRM/CLI.
    """
    # Import TRONG hàm để menu không crash nếu thiếu lib
    picam = None
    Preview = None
    cv2 = None
    try:
        from picamera2 import Picamera2, Preview as _Preview
        picam = Picamera2
        Preview = _Preview
    except Exception:
        picam = None
        Preview = None

    try:
        import cv2 as _cv2
        cv2 = _cv2
    except Exception:
        cv2 = None

    def _highgui_ready(cv2_mod):
        if cv2_mod is None:
            return False
        # Nới lỏng kiểm tra: chỉ cần tạo/huỷ được 1 window là coi như OK
        try:
            cv2_mod.namedWindow("___probe___")
            cv2_mod.destroyWindow("___probe___")
            return True
        except Exception:
            return False

    highgui_ok = _highgui_ready(cv2)

    # Cho phép người dùng ép backend cụ thể
    backend = (backend or "auto").lower()

    # Nhánh 1: Có Picamera2
    if picam is not None:
        cam = picam()
        try:
            w, h = resolution
        except Exception:
            w, h = (1280, 720)

        cam.configure(cam.create_preview_configuration(main={"size": (int(w), int(h))}))
        cam.start()

        # Ép dùng OpenCV nếu backend = 'opencv'
        if backend == "opencv" and not highgui_ok:
            print("Backend yêu cầu 'opencv' nhưng OpenCV HighGUI không khả dụng -> bỏ qua yêu cầu.")

        if highgui_ok and (backend in ("auto", "opencv")):
            print("Camera preview. Nhấn q để thoát.")
            try:
                while True:
                    frame = cam.capture_array()  # thường là 4 kênh RGBA/XRGB/XBGR
                    # ĐÚNG MÀU: chuyển về BGR trước khi imshow
                    if frame is not None and frame.ndim == 3:
                        c = frame.shape[2]
                        if c == 4:
                            # RGBA -> BGR (an toàn cho các layout RGBA/XRGB/XBGR do driver trả)
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                        elif c == 3:
                            # RGB -> BGR
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imshow("Greenhouse Camera (Pi 5)", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            finally:
                cam.stop()
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
            return

        # Không có HighGUI hoặc người dùng yêu cầu qtgl/drm: dùng preview gốc
        if Preview is None:
            cam.stop()
            raise RuntimeError(
                "Picamera2 có nhưng không có backend Preview và cũng không có OpenCV HighGUI.\n"
                "Cài một trong các lựa chọn:\n"
                "  - sudo apt-get install -y python3-picamera2 libcamera-apps\n"
                "  - sudo apt-get install -y python3-opencv (OpenCV có GUI)\n"
                "  - hoặc build lại OpenCV với GTK/Qt"
            )

        preferred_order = []
        if backend == "qtgl":
            preferred_order = ["qtgl", "drm"]
        elif backend == "drm":
            preferred_order = ["drm", "qtgl"]
        else:
            preferred_order = ["qtgl", "drm"]  # auto

        print("Picamera2 native preview. Nhấn Ctrl+C để thoát.")
        try:
            import time
            last_error = None
            for mode in preferred_order:
                try:
                    if mode == "qtgl":
                        cam.start_preview(Preview.QTGL)
                    elif mode == "drm":
                        cam.start_preview(Preview.DRM)
                    print(f"Đang dùng preview: {mode.upper()} (Ctrl+C để thoát)")
                    while True:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Preview {mode.upper()} không khả dụng: {e}")
                    last_error = e
                    # Thử mode kế tiếp
                    continue
            # Nếu tới đây là cả hai đều lỗi
            print(f"Không dùng được QTGL/DRM ({last_error}). Chạy không preview (Ctrl+C để dừng)...")
            try:
                while True:
                    time.sleep(0.25)
            except KeyboardInterrupt:
                pass
        except KeyboardInterrupt:
            pass
        finally:
            cam.stop()
        return

    # Nhánh 2: Không có Picamera2
    if highgui_ok and (backend in ("auto", "usb", "opencv")):
        # Fallback USB cam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError(
                "Không mở được camera USB (/dev/video0). "
                "Nếu bạn dùng camera Pi, hãy cài Picamera2: sudo apt-get install -y python3-picamera2 libcamera-apps"
            )
        print("USB camera preview (nhấn q để thoát).")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                cv2.imshow("USB Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
        return

    # Nhánh 3: CLI preview qua rpicam-hello nếu được yêu cầu, hoặc fallback cuối
    if backend in ("cli", "rpicam", "auto"):
        try:
            import subprocess, shutil, signal, time
            cmd = None
            # Ưu tiên rpicam-hello (mới); nếu không có, thử libcamera-hello (cũ)
            if shutil.which("rpicam-hello"):
                cmd = ["rpicam-hello", "-t", "0"]  # 0 = không giới hạn thời gian
            elif shutil.which("libcamera-hello"):
                cmd = ["libcamera-hello", "-t", "0"]
            if cmd is not None:
                print("CLI preview (rpicam-hello/libcamera-hello). Nhấn Ctrl+C để thoát.")
                proc = subprocess.Popen(cmd)
                try:
                    proc.wait()
                except KeyboardInterrupt:
                    pass
                finally:
                    try:
                        proc.terminate()
                        # Đợi một chút để tiến trình thoát gọn gàng
                        for _ in range(5):
                            if proc.poll() is not None:
                                break
                            time.sleep(0.1)
                        if proc.poll() is None:
                            proc.kill()
                    except Exception:
                        pass
                return
        except Exception as e:
            # Bỏ qua để rơi xuống thông báo hướng dẫn
            print(f"CLI preview không khả dụng: {e}")

    # Không còn lựa chọn
    raise RuntimeError(
        "Không có backend preview khả dụng.\n"
        "Bạn có thể:\n"
        "  - Dùng Picamera2: sudo apt-get install -y python3-picamera2 libcamera-apps\n"
        "  - Dùng OpenCV có GUI: sudo apt-get install -y python3-opencv\n"
        "  - Hoặc dùng CLI: sudo apt-get install -y libcamera-apps (rpicam-hello/libcamera-hello)\n"
    )

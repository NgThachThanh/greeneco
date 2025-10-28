# app/camera_preview.py
# -*- coding: utf-8 -*-

def run(resolution=(1280, 720)):
    """
    Camera preview an toàn và đúng màu:
      - Nếu Picamera2 + OpenCV HighGUI OK: hiển thị bằng cv2.imshow
        + Chuyển RGBA/XRGB/XBGR -> BGR hoặc RGB -> BGR để đúng màu.
            - Nếu Picamera2 có nhưng HighGUI không OK: dùng Picamera2 Preview (QTGL),
                nếu QTGL lỗi do event loop/Qt/EGL thì fallback sang DRM; nếu vẫn lỗi thì chạy không preview.
      - Nếu không có Picamera2 nhưng HighGUI OK: fallback USB cam (/dev/video0).
      - Nếu không có gì: báo lỗi gợi ý cài đặt.
    Nhấn 'q' để thoát (với OpenCV), hoặc Ctrl+C khi dùng QTGL.
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
        try:
            info = cv2_mod.getBuildInformation()
            ok = ("GUI:" in info and ("GTK" in info or "QT" in info or "Win32" in info))
            if not ok:
                return False
            cv2_mod.namedWindow("___probe___")
            cv2_mod.destroyWindow("___probe___")
            return True
        except Exception:
            return False

    highgui_ok = _highgui_ready(cv2)

    # Nhánh 1: Có Picamera2
    if picam is not None:
        cam = picam()
        try:
            w, h = resolution
        except Exception:
            w, h = (1280, 720)

        cam.configure(cam.create_preview_configuration(main={"size": (int(w), int(h))}))
        cam.start()

        if highgui_ok:
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

        # Không có HighGUI: dùng preview gốc QTGL
        if Preview is None:
            cam.stop()
            raise RuntimeError(
                "Picamera2 có nhưng không có backend Preview và cũng không có OpenCV HighGUI.\n"
                "Cài một trong các lựa chọn:\n"
                "  - sudo apt-get install -y python3-picamera2 libcamera-apps\n"
                "  - sudo apt-get install -y python3-opencv (OpenCV có GUI)\n"
                "  - hoặc build lại OpenCV với GTK/Qt"
            )

        print("Picamera2 native preview (QTGL). Nhấn Ctrl+C để thoát.")
        try:
            try:
                # Thử QTGL trước
                cam.start_preview(Preview.QTGL)
                import time
                while True:
                    time.sleep(0.1)
            except Exception as e:
                # Một số môi trường gặp lỗi: "An event loop is already running" hoặc vấn đề Qt/EGL.
                msg = (str(e) or "").lower()
                print(f"QTGL preview không khả dụng ({e}). Thử fallback DRM...")
                try:
                    cam.start_preview(Preview.DRM)
                    import time
                    while True:
                        time.sleep(0.1)
                except Exception as e2:
                    # DRM cũng lỗi -> chạy không preview, vẫn giữ camera hoạt động để kiểm tra.
                    print(f"DRM preview cũng không khả dụng ({e2}). Chạy không preview (Ctrl+C để dừng)...")
                    import time
                    try:
                        while True:
                            # Giữ vòng lặp, có thể thăm dò frame nếu cần
                            time.sleep(0.25)
                    except KeyboardInterrupt:
                        pass
        except KeyboardInterrupt:
            pass
        finally:
            cam.stop()
        return

    # Nhánh 2: Không có Picamera2
    if highgui_ok:
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

    # Không còn lựa chọn
    raise RuntimeError(
        "Không có Picamera2 và OpenCV HighGUI không khả dụng.\n"
        "Cài 1 trong các lựa chọn sau để xem preview:\n"
        "  1) Picamera2 native preview: sudo apt-get install -y python3-picamera2 libcamera-apps\n"
        "  2) OpenCV có GUI: sudo apt-get install -y python3-opencv\n"
        "  3) Hoặc build lại OpenCV với GTK/Qt theo hướng dẫn của OpenCV"
    )

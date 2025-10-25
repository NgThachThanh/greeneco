# app/camera_preview.py
from picamera2 import Picamera2
import cv2

def run(res=(1280, 720)):
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": tuple(res)}))
    cam.start()
    print("Camera preview. Nhấn q để thoát.")
    try:
        while True:
            frame = cam.capture_array()
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif frame.ndim == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("GreenEco Preview", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cv2.destroyAllWindows()
        cam.stop()

# Cho chạy độc lập khi bạn test file này riêng
if __name__ == "__main__":
    run()

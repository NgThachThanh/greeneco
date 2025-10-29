#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script chẩn đoán chi tiết vấn đề camera
Chạy trên Raspberry Pi để xem lỗi cụ thể
"""

import sys
import subprocess
import shlex

def check_camera_busy():
    """Kiểm tra xem thiết bị camera có đang bị process khác giữ không"""
    print("=" * 50)
    print("KIỂM TRA CAMERA BỊ CHIẾM DỤNG")
    print("=" * 50)

    devices = [
        "/dev/media0", "/dev/media1", "/dev/media2",
        "/dev/video0", "/dev/video1",
    ]
    found = False
    for dev in devices:
        try:
            # fuser hiển thị PID nào đang mở thiết bị
            res = subprocess.run(["fuser", dev], capture_output=True, text=True)
            pids = res.stdout.strip()
            if pids:
                found = True
                print(f"Thiết bị {dev} đang bị giữ bởi PID: {pids}")
        except FileNotFoundError:
            # fuser có thể chưa cài đặt
            pass
        except Exception as e:
            pass

    if not found:
        print("Không thấy process nào chiếm dụng trực tiếp /dev/media* hoặc /dev/video*.")
    else:
        print("\nGợi ý giải phóng:")
        print("  - Kiểm tra tiến trình: ps aux | grep -E 'libcamera|rpicam|picamera2|python|motion' ")
        print("  - Dừng tiến trình đó: kill -9 <PID>")
        print("  - Hoặc reboot nếu chưa rõ tiến trình nào giữ.")
    print()

def check_imports():
    """Kiểm tra các thư viện có import được không"""
    print("=" * 50)
    print("KIỂM TRA IMPORTS")
    print("=" * 50)
    
    # Check picamera2
    try:
        from picamera2 import Picamera2
        print("✓ picamera2: OK")
        try:
            print(f"  Version: {Picamera2.__version__ if hasattr(Picamera2, '__version__') else 'unknown'}")
        except:
            pass
    except ImportError as e:
        print(f"✗ picamera2: FAILED - {e}")
        print("  → Cài: sudo apt-get install -y python3-picamera2")
        return False
    except Exception as e:
        print(f"✗ picamera2: ERROR - {e}")
        return False
    
    # Check cv2
    try:
        import cv2
        print(f"✓ cv2: OK (version {cv2.__version__})")
        
        # Check GUI support
        try:
            cv2.namedWindow("test")
            cv2.destroyWindow("test")
            print("  ✓ GUI support: OK")
        except Exception as e:
            print(f"  ✗ GUI support: FAILED - {e}")
            print("    → Cài: sudo apt-get install -y python3-opencv libqt5gui5")
            return False
            
    except ImportError as e:
        print(f"✗ cv2: FAILED - {e}")
        print("  → Cài: sudo apt-get install -y python3-opencv")
        return False
    except Exception as e:
        print(f"✗ cv2: ERROR - {e}")
        return False
    
    print()
    return True

def check_camera_device():
    """Kiểm tra camera hardware"""
    print("=" * 50)
    print("KIỂM TRA CAMERA HARDWARE")
    print("=" * 50)
    
    import subprocess
    
    # Check với vcgencmd
    try:
        result = subprocess.run(['vcgencmd', 'get_camera'], 
                              capture_output=True, text=True, timeout=5)
        print(f"vcgencmd get_camera: {result.stdout.strip()}")
        
        if "detected=1" in result.stdout:
            print("✓ Camera được phát hiện bởi system")
        else:
            print("✗ Camera KHÔNG được phát hiện")
            print("  → Enable camera: sudo raspi-config → Interface Options → Camera")
            return False
    except FileNotFoundError:
        print("⚠ vcgencmd không tìm thấy (không phải Raspberry Pi?)")
    except Exception as e:
        print(f"⚠ Không check được vcgencmd: {e}")
    
    # Check libcamera
    try:
        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ libcamera có thể list cameras")
            print(f"  Cameras:\n{result.stdout}")
        else:
            print(f"✗ libcamera-hello failed: {result.stderr}")
    except FileNotFoundError:
        # Try rpicam-hello
        try:
            result = subprocess.run(['rpicam-hello', '--list-cameras'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ rpicam có thể list cameras")
                print(f"  Cameras:\n{result.stdout}")
            else:
                print(f"✗ rpicam-hello failed: {result.stderr}")
        except FileNotFoundError:
            print("⚠ libcamera-apps chưa cài")
            print("  → Cài: sudo apt-get install -y libcamera-apps")
    except Exception as e:
        print(f"⚠ Không test được libcamera: {e}")
    
    print()
    return True

def test_picamera2():
    """Test Picamera2 có khởi tạo được không"""
    print("=" * 50)
    print("TEST PICAMERA2")
    print("=" * 50)
    
    try:
        from picamera2 import Picamera2
        print("Đang khởi tạo Picamera2...")
        
        cam = Picamera2()
        print("✓ Khởi tạo thành công")
        
        print("Đang configure camera...")
        config = cam.create_preview_configuration(main={"size": (1280, 720)})
        cam.configure(config)
        print("✓ Configure thành công")
        
        print("Đang start camera...")
        cam.start()
        print("✓ Start thành công")
        
        print("Đang capture 1 frame...")
        frame = cam.capture_array()
        print(f"✓ Capture thành công: shape={frame.shape}, dtype={frame.dtype}")
        
        cam.stop()
        print("✓ Stop thành công")
        
        print("\n✓✓✓ PICAMERA2 HOẠT ĐỘNG BÌNH THƯỜNG ✓✓✓")
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ LỖI: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def test_full_preview():
    """Test preview với OpenCV"""
    print("=" * 50)
    print("TEST FULL PREVIEW (10 frames)")
    print("=" * 50)
    
    try:
        from picamera2 import Picamera2
        import cv2
        
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(main={"size": (1280, 720)}))
        cam.start()
        print("✓ Camera started")
        
        print("Đang capture và hiển thị 10 frames...")
        for i in range(10):
            frame = cam.capture_array()
            
            # Convert color
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            elif frame.ndim == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            cv2.imshow("Test Preview", frame)
            key = cv2.waitKey(100)
            
            print(f"  Frame {i+1}/10 OK", end='\r')
            
            if key & 0xFF == ord('q'):
                print("\n  User pressed 'q'")
                break
        
        print("\n✓ Capture và display thành công")
        
        cv2.destroyAllWindows()
        cam.stop()
        
        print("\n✓✓✓ FULL PREVIEW TEST THÀNH CÔNG ✓✓✓")
        print("    → Code của bạn PHẢI hoạt động!")
        return True
        
    except Exception as e:
        print(f"\n✗✗✗ LỖI: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print()

def main():
    print("\n")
    print("█" * 52)
    print("█  CHẨN ĐOÁN CAMERA - RASPBERRY PI                 █")
    print("█" * 52)
    print()
    
    # Step 1: Check imports
    if not check_imports():
        print("\n⚠ Cài đặt các package còn thiếu rồi chạy lại script này")
        return 1
    
    # Step 2: Check hardware
    check_camera_device()
    check_camera_busy()
    
    # Step 3: Test Picamera2
    if not test_picamera2():
        print("\n⚠ Picamera2 không hoạt động. Kiểm tra:")
        print("   1. Camera đã được enable chưa (raspi-config)")
        print("   2. Dây cáp camera cắm chặt chưa")
        print("   3. Thử reboot: sudo reboot")
        return 1
    
    # Step 4: Test full preview
    if not test_full_preview():
        print("\n⚠ Preview không hoạt động. Có thể:")
        print("   1. Chạy qua SSH không có DISPLAY")
        print("   2. OpenCV GUI không được cài đầy đủ")
        return 1
    
    print("=" * 50)
    print("KẾT LUẬN: MỌI THỨ HOẠT ĐỘNG BÌNH THƯỜNG!")
    print("=" * 50)
    print("Code camera_preview.py của bạn PHẢI chạy được.")
    print("Nếu vẫn lỗi, chụp màn hình lỗi và gửi lại.")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

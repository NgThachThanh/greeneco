#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test nhanh để kiểm tra OpenCV GUI có hoạt động không
"""

def test_opencv_gui():
    print("=== Test OpenCV GUI ===")
    
    # Test 1: Import cv2
    try:
        import cv2
        print("✓ Import cv2 thành công")
        print(f"  OpenCV version: {cv2.__version__}")
    except Exception as e:
        print(f"✗ Không import được cv2: {e}")
        return False
    
    # Test 2: Kiểm tra build info
    try:
        info = cv2.getBuildInformation()
        print("\n--- Build Information (trích đoạn) ---")
        for line in info.split('\n'):
            if any(keyword in line for keyword in ['GUI', 'GTK', 'QT', 'Win32', 'Cocoa', 'Video I/O']):
                print(f"  {line}")
    except Exception as e:
        print(f"  Không lấy được build info: {e}")
    
    # Test 3: Thử tạo window
    try:
        print("\n--- Test tạo window ---")
        cv2.namedWindow("Test Window")
        print("✓ Tạo window thành công")
        cv2.destroyWindow("Test Window")
        print("✓ Đóng window thành công")
    except Exception as e:
        print(f"✗ Lỗi khi tạo window: {e}")
        return False
    
    # Test 4: Thử mở camera và hiển thị
    print("\n--- Test mở camera ---")
    try:
        # Thử mở camera (0 = camera mặc định)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Không mở được camera (có thể không có camera USB hoặc cần Picamera2)")
            cap.release()
        else:
            print("✓ Mở camera thành công")
            print("  Đang hiển thị 30 frames... (sẽ tự động đóng sau vài giây)")
            
            for i in range(30):
                ret, frame = cap.read()
                if ret:
                    cv2.imshow("Camera Test", frame)
                    if cv2.waitKey(100) & 0xFF == ord('q'):
                        print("  Người dùng bấm 'q' để thoát")
                        break
                else:
                    print(f"  Không đọc được frame {i}")
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            print("✓ Test camera hoàn tất")
    except Exception as e:
        print(f"✗ Lỗi khi test camera: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== Test hoàn tất ===")
    return True

if __name__ == "__main__":
    test_opencv_gui()

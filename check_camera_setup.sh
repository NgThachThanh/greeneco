#!/bin/bash
# Script kiểm tra và sửa cấu hình camera sau khi flash SD card mới

echo "=== Kiểm tra Camera Setup trên Raspberry Pi ==="
echo ""

# 1. Kiểm tra camera có được enable không
echo "1. Kiểm tra camera interface..."
if vcgencmd get_camera | grep -q "detected=1"; then
    echo "   ✓ Camera được phát hiện"
else
    echo "   ✗ Camera KHÔNG được phát hiện"
    echo "   → Chạy: sudo raspi-config"
    echo "   → Interface Options → Camera → Enable"
fi
echo ""

# 2. Kiểm tra libcamera
echo "2. Kiểm tra libcamera..."
if command -v libcamera-hello &> /dev/null || command -v rpicam-hello &> /dev/null; then
    echo "   ✓ libcamera tools đã cài"
    if command -v rpicam-hello &> /dev/null; then
        echo "   → Test camera: rpicam-hello -t 2000"
    else
        echo "   → Test camera: libcamera-hello -t 2000"
    fi
else
    echo "   ✗ libcamera tools chưa cài"
    echo "   → Cài: sudo apt-get install -y libcamera-apps"
fi
echo ""

# 3. Kiểm tra Python packages
echo "3. Kiểm tra Python packages..."

# Picamera2
if python3 -c "import picamera2" 2>/dev/null; then
    echo "   ✓ picamera2 đã cài"
else
    echo "   ✗ picamera2 chưa cài"
    echo "   → Cài: sudo apt-get install -y python3-picamera2"
fi

# OpenCV
if python3 -c "import cv2; print('   OpenCV version:', cv2.__version__)" 2>/dev/null; then
    echo "   ✓ opencv đã cài"
else
    echo "   ✗ opencv chưa cài"
    echo "   → Cài: sudo apt-get install -y python3-opencv"
fi
echo ""

# 4. Kiểm tra user có trong video group không
echo "4. Kiểm tra user permissions..."
if groups | grep -q video; then
    echo "   ✓ User trong video group"
else
    echo "   ✗ User KHÔNG trong video group"
    echo "   → Chạy: sudo usermod -aG video $USER"
    echo "   → Sau đó logout và login lại"
fi
echo ""

# 5. Test nhanh camera
echo "5. Test camera nhanh..."
echo "   Chạy lệnh này để test camera:"
if command -v rpicam-hello &> /dev/null; then
    echo "   → rpicam-hello -t 2000"
elif command -v libcamera-hello &> /dev/null; then
    echo "   → libcamera-hello -t 2000"
else
    echo "   → (Cần cài libcamera-apps trước)"
fi
echo ""

echo "=== Cài đặt đầy đủ (nếu cần) ==="
echo "Chạy các lệnh sau trên Raspberry Pi:"
echo ""
echo "sudo apt-get update"
echo "sudo apt-get install -y python3-picamera2 python3-opencv libcamera-apps"
echo "sudo usermod -aG video \$USER"
echo ""
echo "Sau đó logout/login lại và test:"
echo "rpicam-hello -t 2000"
echo "python3 app/camera_preview.py"

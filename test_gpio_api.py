#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script cho GPIO control API endpoint
Format mới: {"deviceId": "...", "component": "...", "state": "..."}
"""
import requests
import json
import time

# Cấu hình
API_URL = "http://localhost:5000/api/iot/control"
DEVICE_ID = "H2-RASPI-01"

def test_control(component, state):
    """Test điều khiển một component với state."""
    payload = {
        "deviceId": DEVICE_ID,
        "component": component,
        "state": state
    }
    
    print(f"\n{'='*60}")
    print(f"TEST: {component} -> {state}")
    print(f"{'='*60}")
    print(f"Request URL: {API_URL}")
    print(f"Request Body: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            return True
        else:
            print("❌ FAILED")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def test_invalid_requests():
    """Test các request không hợp lệ."""
    print(f"\n{'='*60}")
    print("TEST: Invalid Requests")
    print(f"{'='*60}")
    
    # Test 1: Missing state
    print("\n1. Missing state:")
    payload = {"deviceId": DEVICE_ID, "component": "pump"}
    response = requests.post(API_URL, json=payload)
    print(f"Status: {response.status_code}, Response: {response.json()}")
    
    # Test 2: Invalid state
    print("\n2. Invalid state:")
    payload = {"deviceId": DEVICE_ID, "component": "pump", "state": "invalid"}
    response = requests.post(API_URL, json=payload)
    print(f"Status: {response.status_code}, Response: {response.json()}")
    
    # Test 3: Invalid component
    print("\n3. Invalid component:")
    payload = {"deviceId": DEVICE_ID, "component": "invalid_device", "state": "on"}
    response = requests.post(API_URL, json=payload)
    print(f"Status: {response.status_code}, Response: {response.json()}")

def get_status():
    """Lấy trạng thái hiện tại của tất cả devices."""
    url = "http://localhost:5000/api/iot/status"
    try:
        response = requests.get(url, timeout=5)
        print(f"\n{'='*60}")
        print("CURRENT STATUS")
        print(f"{'='*60}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error getting status: {e}")

def main():
    """Main test function."""
    print("\n" + "="*60)
    print("  GPIO CONTROL API TEST")
    print("  Format: {deviceId, component, state}")
    print("="*60)
    
    # Kiểm tra server có chạy không
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"✅ Server is running: {response.json()}")
    except Exception as e:
        print(f"❌ Server not running! Start Flask app first.")
        print(f"   Error: {e}")
        return
    
    # Lấy status ban đầu
    get_status()
    
    input("\nPress Enter to start tests...")
    
    # Test các components
    components = ["pump", "fan1", "fan2", "light"]
    
    print("\n" + "="*60)
    print("TEST 1: Turn ON all components")
    print("="*60)
    for comp in components:
        test_control(comp, "on")
        time.sleep(1)
    
    get_status()
    time.sleep(2)
    
    print("\n" + "="*60)
    print("TEST 2: Turn OFF all components")
    print("="*60)
    for comp in components:
        test_control(comp, "off")
        time.sleep(1)
    
    get_status()
    time.sleep(2)
    
    print("\n" + "="*60)
    print("TEST 3: Toggle pump multiple times")
    print("="*60)
    for i in range(3):
        test_control("pump", "toggle")
        time.sleep(1)
    
    get_status()
    
    # Test invalid requests
    test_invalid_requests()
    
    # Final status
    get_status()
    
    print("\n" + "="*60)
    print("  TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")

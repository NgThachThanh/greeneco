from flask import Flask, jsonify, request

app = Flask(__name__)

# Import GPIO controller và khởi tạo
try:
    from app import gpio_controller as gpio
    gpio.init_gpio()
    print("[Flask] GPIO initialized successfully")
except Exception as e:
    print(f"[Flask] GPIO init error: {e}")
    gpio = None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"msg": "GreenEco API alive"})

@app.route("/api/iot/status", methods=["GET"])
def status():
    """GET: Trả về trạng thái tất cả thiết bị GPIO"""
    if gpio is None:
        return jsonify({"error": "GPIO not available"}), 503
    
    try:
        states = gpio.get_all_states()
        devices = []
        for device_name, is_on in states.items():
            devices.append({
                "name": device_name,
                "state": "ON" if is_on else "OFF",
                "pin": gpio.DEVICES.get(device_name)
            })
        
        return jsonify({
            "status": "OK",
            "backend": gpio.backend_info(),
            "devices": devices
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/iot/control", methods=["POST"])
def control():
    """
    POST: Điều khiển GPIO theo body:
    
    Format mới (khuyến nghị):
    {
        "deviceId": "H2-RASPI-01",
        "component": "pump",    // "fan1", "fan2", "pump", "light"
        "state": "on"           // "on", "off", "toggle"
    }
    
    Format cũ (vẫn hỗ trợ):
    {
        "device": "fan1",
        "action": "on"
    }
    
    Hoặc điều khiển nhiều thiết bị:
    {
        "devices": [
            {"device": "fan1", "action": "on"},
            {"device": "pump", "action": "off"}
        ]
    }
    
    Hoặc điều khiển tất cả:
    {
        "action": "all_on"    // "all_on" hoặc "all_off"
    }
    """
    if gpio is None:
        return jsonify({"error": "GPIO not available"}), 503
    
    data = request.get_json(silent=True) or {}
    results = []
    
    try:
        # ===== FORMAT MỚI: deviceId + component + state =====
        if "component" in data and "state" in data:
            device_id = data.get("deviceId", "unknown")
            component = data.get("component")
            state = data.get("state", "").lower()
            
            if not component or not state:
                return jsonify({
                    "status": "FAILED",
                    "error": "Missing component or state"
                }), 400
            
            # Normalize state: "on"/"off"/"toggle"
            if state not in ["on", "off", "toggle"]:
                return jsonify({
                    "status": "FAILED",
                    "error": f"Invalid state: {state}. Use 'on', 'off', or 'toggle'"
                }), 400
            
            success = False
            if state == "on":
                success = gpio.turn_on(component)
            elif state == "off":
                success = gpio.turn_off(component)
            elif state == "toggle":
                success = gpio.toggle_device(component)
            
            if not success:
                return jsonify({
                    "status": "FAILED",
                    "deviceId": device_id,
                    "component": component,
                    "error": f"Failed to control '{component}'. Valid components: {list(gpio.DEVICES.keys())}"
                }), 400
            
            # Lấy trạng thái hiện tại sau khi điều khiển
            current_state = gpio.get_device_state(component)
            
            return jsonify({
                "status": "OK",
                "deviceId": device_id,
                "component": component,
                "state": "on" if current_state else "off",
                "pin": gpio.DEVICES.get(gpio.normalize_device_name(component)),
                "message": f"{component} turned {state}"
            }), 200
        
        # ===== FORMAT CŨ: Giữ lại để tương thích ngược =====
        # Trường hợp 1: Điều khiển tất cả
        elif "action" in data and data["action"] in ["all_on", "all_off"]:
            if data["action"] == "all_on":
                gpio.turn_all_on()
                results.append({"action": "all_on", "status": "OK"})
            else:
                gpio.turn_all_off()
                results.append({"action": "all_off", "status": "OK"})
        
        # Trường hợp 2: Điều khiển nhiều thiết bị
        elif "devices" in data and isinstance(data["devices"], list):
            for item in data["devices"]:
                device = item.get("device")
                action = item.get("action", "").lower()
                
                if not device or not action:
                    results.append({"device": device, "error": "Missing device or action"})
                    continue
                
                success = False
                if action == "on":
                    success = gpio.turn_on(device)
                elif action == "off":
                    success = gpio.turn_off(device)
                elif action == "toggle":
                    success = gpio.toggle_device(device)
                else:
                    results.append({"device": device, "error": f"Invalid action: {action}"})
                    continue
                
                results.append({
                    "device": device,
                    "action": action,
                    "status": "OK" if success else "FAILED"
                })

        # Trường hợp 3: Điều khiển một thiết bị (format cũ)
        elif "device" in data:
            device = data.get("device")
            action = data.get("action", "").lower()
            
            if not action:
                return jsonify({"error": "Missing action"}), 400
            
            success = False
            if action == "on":
                success = gpio.turn_on(device)
            elif action == "off":
                success = gpio.turn_off(device)
            elif action == "toggle":
                success = gpio.toggle_device(device)
            else:
                return jsonify({"error": f"Invalid action: {action}"}), 400
            
            results.append({
                "device": device,
                "action": action,
                "status": "OK" if success else "FAILED"
            })
        
        else:
            return jsonify({
                "error": "Invalid request body. Use format: {\"deviceId\": \"...\", \"component\": \"pump\", \"state\": \"on\"}"
            }), 400
        
        # Trả về trạng thái mới sau khi điều khiển
        states = gpio.get_all_states()
        devices = []
        for device_name, is_on in states.items():
            devices.append({
                "name": device_name,
                "state": "ON" if is_on else "OFF"
            })
        
        return jsonify({
            "status": "OK",
            "results": results,
            "current_states": devices
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

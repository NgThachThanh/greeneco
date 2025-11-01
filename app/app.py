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
    
    Body mẫu:
    {
        "device": "fan1",     // hoặc "fan2", "pump", "light", "1", "2", "3", "4"
        "action": "on"        // "on", "off", "toggle"
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
        # Trường hợp 1: Điều khiển tất cả
        if "action" in data and data["action"] in ["all_on", "all_off"]:
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
        
        # Trường hợp 3: Điều khiển 1 thiết bị
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
            return jsonify({"error": "Invalid request body"}), 400
        
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

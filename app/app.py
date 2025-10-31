from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"msg": "GreenEco API alive"})

@app.route("/api/iot/control", methods=["POST"])
def control():
    data = request.get_json(silent=True) or {}
    return jsonify({"echo": data, "status": "OK"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

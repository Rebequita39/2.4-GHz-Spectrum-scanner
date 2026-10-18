import sys, json, threading, time
import serial
from flask import Flask, Response, send_from_directory

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = 115200

app = Flask(__name__, static_folder="static")
state = {"seq": 0, "values": [0] * 126}

def serial_reader():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line.startswith("D,"):
            continue  # ignore boot messages / noise
        try:
            vals = [int(v) for v in line.split(",")[1:]]
        except ValueError:
            continue
        if len(vals) == 126:
            state["values"] = vals
            state["seq"] += 1

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)
    
@app.route("/stream")
def stream():
    def gen():
        last = -1
        while True:
            if state["seq"] != last:
                last = state["seq"]
                yield f"data: {json.dumps(state['values'])}\n\n"
            time.sleep(0.03)
    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, threaded=True)
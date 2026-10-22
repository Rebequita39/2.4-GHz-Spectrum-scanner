import sys, json, threading, time
from collections import deque
import serial
from flask import Flask, Response, send_from_directory, jsonify

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = 115200

app = Flask(__name__, static_folder="static")

state = {
    "seq": 0,
    "values": [0] * 126,
    "serial_ok": False,     # serial port is open
    "radio_ok": None,       # None = unknown, True/False from ESP messages
    "last_rx": 0.0,         # time of last valid sweep
    "sweeps": 0,
    "bad_lines": 0,
    "last_msg": "",         # last non-data line from the ESP (boot text, errors)
    "error": "",            # last serial error
}
stamps = deque(maxlen=10)   # timestamps of recent sweeps, for sweep rate
started = time.time()

def serial_reader():
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            state["serial_ok"] = True
            state["error"] = ""
            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                if not line.startswith("D,"):
                    state["last_msg"] = line[:80]
                    if "Radio not responding" in line:
                        state["radio_ok"] = False
                    continue
                try:
                    vals = [int(v) for v in line.split(",")[1:]]
                except ValueError:
                    state["bad_lines"] += 1
                    continue
                if len(vals) != 126:
                    state["bad_lines"] += 1
                    continue
                state["values"] = vals
                state["seq"] += 1
                state["sweeps"] += 1
                state["radio_ok"] = True
                state["last_rx"] = time.time()
                stamps.append(state["last_rx"])
        except (serial.SerialException, OSError) as e:
            state["serial_ok"] = False
            state["error"] = str(e)[:80]
            time.sleep(2)   # retry until the board is plugged back in

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/status")
def status():
    now = time.time()
    rate = 0.0
    if len(stamps) >= 2 and stamps[-1] > stamps[0]:
        rate = (len(stamps) - 1) / (stamps[-1] - stamps[0])
    return jsonify({
        "port": PORT,
        "baud": BAUD,
        "serial_ok": state["serial_ok"],
        "radio_ok": state["radio_ok"],
        "age": (now - state["last_rx"]) if state["last_rx"] else None,
        "rate": round(rate, 2),
        "sweeps": state["sweeps"],
        "bad_lines": state["bad_lines"],
        "last_msg": state["last_msg"],
        "error": state["error"],
        "uptime": int(now - started),
    })

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

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    threading.Thread(target=serial_reader, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, threaded=True)
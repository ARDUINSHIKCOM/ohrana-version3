from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ===== НАСТРОЙКИ =====
NTFY_TOPIC = "ohrana-version3-trevoga"
SERVER_URL = "https://ohrana-version3.onrender.com"

# ===== СОСТОЯНИЕ =====
guard_on = False
sensors = {"light": 0, "leak": 0, "temp": 0, "hum": 0}

# ===== ОТПРАВКА В NTFY =====
def send_ntfy(title, message, priority="default", actions=None):
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": "rotating_light" if priority == "urgent" else "bell"
    }
    if actions:
        headers["Actions"] = actions
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
                      data=message.encode(),
                      headers=headers, timeout=5)
    except Exception as e:
        print("ntfy error:", e)

# ===== ПРИЁМ ДАННЫХ ОТ ESP32 =====
@app.route('/esp32/set', methods=['POST'])
def esp32_set():
    global guard_on, sensors
    data = request.json
    for k in ["light", "leak", "temp", "hum"]:
        if k in data:
            sensors[k] = data[k]

    if guard_on:
        if sensors["light"] > 1000:
            send_ntfy("🚨 ТРЕВОГА: СВЕТ!",
                      "Датчик света сработал! Охрана включена.",
                      "urgent")
        if sensors["leak"] > 100:
            send_ntfy("🚨 ТРЕВОГА: ПРОТЕЧКА!",
                      "Датчик протечки сработал!",
                      "urgent")

    return jsonify({"ok": True, "guard": guard_on})

@app.route('/esp32/get', methods=['GET'])
def esp32_get():
    return jsonify({"guard": guard_on})

# ===== КНОПКИ В NTFY =====
@app.route('/send_buttons', methods=['GET'])
def send_buttons():
    actions = (
        f"view, Включить охрану, {SERVER_URL}/guard_on, method=POST; "
        f"view, Выключить охрану, {SERVER_URL}/guard_off, method=POST"
    )
    send_ntfy("Управление охраной", "Нажмите кнопку:", "default", actions)
    return "OK"

# ===== ОБРАБОТКА КНОПОК =====
@app.route('/guard_on', methods=['POST'])
def guard_on_route():
    global guard_on
    guard_on = True
    send_ntfy("✅ Охрана включена", "Система под охраной.")
    return "OK"

@app.route('/guard_off', methods=['POST'])
def guard_off_route():
    global guard_on
    guard_on = False
    send_ntfy("🔓 Охрана выключена", "Система снята с охраны.")
    return "OK"

# ===== ПРОВЕРКА =====
@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

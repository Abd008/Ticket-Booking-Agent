from flask import Flask, render_template, request
import subprocess
import json

app = Flask(__name__)

# ---------------------------
# HOME
# ---------------------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------------------
# START AGENT
# ---------------------------
@app.route('/start', methods=['POST'])
def start():

    data = request.form

    config = {
        "from_station": data.get("from_station"),
        "to_station": data.get("to_station"),
        "date": data.get("date"),
        "train_number": data.get("train_number"),
        "travel_class": data.get("travel_class"),
    }

    subprocess.Popen([
        "python",
        "main.py",
        json.dumps(config)
    ])

    return "Agent started!"


# ---------------------------
# 🔥 ADD THIS HERE
# ---------------------------
@app.route('/logs')
def get_logs():
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
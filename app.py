from flask import Flask, render_template, request, redirect, send_from_directory
import json
import os

app = Flask(__name__)
DATA_FILE = "fridge.json"

# JSON読み込み
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# JSON保存
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    items = load_data()
    return render_template("index.html", items=items)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]

    data = load_data()
    data.append({"name": name, "qty": qty})
    save_data(data)

    return redirect("/")

@app.route("/delete/<int:index>")
def delete(index):
    data = load_data()
    if 0 <= index < len(data):
        del data[index]
        save_data(data)
    return redirect("/")

# PWA: manifest.json を配信
@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

# PWA: service-worker.js を配信
@app.route('/service-worker.js')
def sw():
    return send_from_directory('.', 'service-worker.js')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

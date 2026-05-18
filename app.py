from flask import Flask, render_template, request, redirect, send_from_directory
import json
import os
import requests
import schedule
import time
import threading
from datetime import datetime


#Telegramで通知するための関数
TOKEN = "8508528245:AAE68UTWteJePaC3qcmEBHCLCRmmRxvHdow"
CHAT_ID = ["8738323888","8932879014"]  # 通知を送りたいユーザーのIDをリストで指定

def send_telegram(message):
    for chat_id in CHAT_ID:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)


# 賞味期限をチェックしてTelegramに通知する関数
def check_expiration_and_notify():
    with open("foods.json", "r", encoding="utf-8") as f:
        foods = json.load(f)
        
    today = datetime.now().date()
    messages = []

    for item in foods:
        exp = datetime.strptime(item["exp"], "%Y-%m-%d").date()
        days_left = (exp - today).days

        if 0 <= days_left <= 2:
            messages.append(f"⚠️ {item['name']} はよ食べや！（残り {days_left} 日）")

    if messages:
        send_telegram("\n".join(messages))

# ★ 毎日定刻に実行
schedule.every().day.at("10:00").do(check_expiration_and_notify)

# ★ スケジューラーを別スレッドで動かす
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()


# -------------------------
# Flask アプリ本体
# -------------------------

app = Flask(__name__)
DATA_FILE = "foods.json"

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
    items.sort(key=lambda x: datetime.strptime(x["exp"], "%Y-%m-%d"))

    # 今日の日付
    today = datetime.today().date()

    # 各食品に「期限切れフラグ」を追加
    for item in items:
        exp_date = datetime.strptime(item["exp"], "%Y-%m-%d").date()
        
        # 期限切れ判定
        item["expired"] = exp_date < today
        item["days_left"] = (exp_date - today).days
        item["near"] = 0 <= item["days_left"] <= 3


    return render_template("index.html", items=items)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    qty = request.form["qty"]
    unit = request.form["unit"]
    exp = request.form["exp"]  

    data = load_data()

     # 新しいIDを発行（最大ID+1）
    new_id = max([item.get("id", 0) for item in data], default=0) + 1

    data.append({"id": new_id, "name": name, "qty": qty, "unit": unit, "exp": exp})
   
    save_data(data)
    return redirect("/")

@app.route("/delete/<int:item_id>")
def delete(item_id):
    data = load_data()
    data = [item for item in data if item["id"] != item_id]
    save_data(data)
    return redirect("/")


@app.route("/edit/<int:item_id>")
def edit(item_id):
    data = load_data()
    item = next((x for x in data if x["id"] == item_id), None)
    return render_template("edit.html", item=item)


@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    data = load_data()

    for item in data:
        if item["id"] == item_id:
            item["name"] = request.form["name"]
            item["qty"] = request.form["qty"]
            item["unit"] = request.form["unit"]
            item["exp"] = request.form["exp"]

    save_data(data)
    return redirect("/")

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')
       

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)




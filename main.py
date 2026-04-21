import subprocess
import threading
from flask import Flask
import time
import os

app = Flask(__name__)

# 🔥 Ruta para mantener activo Render
@app.route('/')
def home():
    return "BOT ACTIVO 🔥"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# correr servidor web
threading.Thread(target=run_web).start()

# correr tus bots
subprocess.Popen(["python", "bot_ui.py"])
subprocess.Popen(["python", "auto.py"])

# mantener vivo
while True:
    time.sleep(60)

import os
import json
import asyncio
import re
import unicodedata
import difflib
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# TOKEN SEGURO
# =========================
TOKEN = os.getenv("8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY")

if not TOKEN or ":" not in TOKEN:
    raise Exception("❌ TOKEN INVALIDO O NO CARGADO DESDE RAILWAY")

CONFIG = "config_data.json"

# =========================
# JSON
# =========================
def load():
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        data = {"programacion": [], "canales": [], "contenido": []}
        save(data)
        return data

def save(data):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# =========================
# TEXTO
# =========================
def clean(t):
    t = t.lower()
    t = unicodedata.normalize('NFD', t)
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')

dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

def fix_day(d):
    m = difflib.get_close_matches(clean(d), dias_validos, n=1, cutoff=0.6)
    return m[0] if m else None

def parse_hour(h):
    h = h.lower().replace(" ", "")
    try:
        if "am" in h or "pm" in h:
            t = datetime.strptime(h, "%I:%M%p") if ":" in h else datetime.strptime(h, "%I%p")
            return t.strftime("%H:%M")
        else:
            hh, mm = map(int, h.split(":"))
            return f"{hh:02d}:{mm:02d}"
    except:
        return None

# =========================
# MENU
# =========================
def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["📋 Activos", "🚀 Activar"]
    ], resize_keyboard=True)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 BOT ACTIVO", reply_markup=menu())

# =========================
# HANDLER
# =========================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load()
    msg = update.message
    raw = msg.text or msg.caption or ""
    t = clean(raw)

    try:

        # ===== GUARDAR =====
        if context.user_data.get("modo") == "guardar":

            if t == "guardar":
                temp = context.user_data.get("temp", [])

                if not temp:
                    await msg.reply_text("❌ Nada guardado")
                    return

                data["contenido"] = temp
                save(data)
                context.user_data.clear()

                await msg.reply_text("✅ Mensaje guardado")
                return

            context.user_data.setdefault("temp", [])
            context.user_data["temp"].append({
                "chat_id": msg.chat_id,
                "message_id": msg.message_id
            })

            await msg.reply_text("📦 Guardado")
            return

        if "mensaje" in t:
            context.user_data["modo"] = "guardar"
            context.user_data["temp"] = []
            await msg.reply_text("📩 Envía contenido y luego escribe guardar")
            return

        # ===== PANEL =====
        if "panel" in t:
            await msg.reply_text(f"📊 Canales: {len(data['canales'])}\n⏰ Horarios: {len(data['programacion'])}")
            return

        # ===== CANALES =====
        if "canales" in t:
            await msg.reply_text("Envía ID canal (-100...)")
            return

        if raw.startswith("-100"):
            cid = int(raw)
            if cid not in data["canales"]:
                data["canales"].append(cid)
                save(data)
            await msg.reply_text("✅ Canal agregado")
            return

        # ===== HORARIOS =====
        if "horarios" in t:
            if not data["programacion"]:
                await msg.reply_text("⚠️ Ejemplo:\nlunes 5pm\nlunes,viernes 6pm")
                return

            txt = "⏰ HORARIOS:\n\n"
            for i, p in enumerate(data["programacion"], 1):
                txt += f"{i}. {p['dias']} ⏰ {p['horas']}\n"

            await msg.reply_text(txt)
            return

        # ===== ACTIVOS =====
        if "activos" in t:
            activos = [p for p in data["programacion"] if p.get("activo", True)]

            if not activos:
                await msg.reply_text("⚫ Sin activos")
            else:
                txt = ""
                for p in activos:
                    txt += f"{p['dias']} {p['horas']}\n"
                await msg.reply_text(txt)
            return

        if "activar" in t:
            await msg.reply_text("🚀 AUTO ACTIVADO")
            return

        # ===== CREAR HORARIO =====
        if re.match(r"^[a-z, ]+\s+\d", t):

            dias_txt, horas_txt = re.match(r"(.+?)\s+(.+)", t).groups()

            dias = [fix_day(d) for d in dias_txt.split(",")]
            horas = [parse_hour(h) for h in horas_txt.split(",")]

            dias = [d for d in dias if d]
            horas = [h for h in horas if h]

            if not dias or not horas:
                await msg.reply_text("❌ Formato inválido")
                return

            data["programacion"].append({
                "dias": dias,
                "horas": horas,
                "activo": True
            })

            save(data)
            await msg.reply_text("✅ Programado")
            return

        await msg.reply_text("❌ No válido")

    except Exception as e:
        print("ERROR:", e)
        await msg.reply_text("⚠️ Error")

# =========================
# AUTO ENVÍO
# =========================
ultimo = {}

async def auto(app):
    print("🔥 AUTO RUNNING")

    while True:
        try:
            data = load()
            now = datetime.now()

            if not data["contenido"]:
                await asyncio.sleep(10)
                continue

            mapa = {
                "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
                "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
            }

            hoy = mapa[now.strftime("%A").lower()]

            for p in data["programacion"]:
                if hoy not in p["dias"]:
                    continue

                for h in p["horas"]:
                    if now.strftime("%H:%M") == h:

                        key = f"{hoy}-{h}"
                        if ultimo.get(key) == now.date():
                            continue

                        for m in data["contenido"]:
                            for c in data["canales"]:
                                await app.bot.copy_message(
                                    chat_id=c,
                                    from_chat_id=m["chat_id"],
                                    message_id=m["message_id"]
                                )

                        print("✅ ENVIADO")
                        ultimo[key] = now.date()

        except Exception as e:
            print("AUTO ERROR:", e)

        await asyncio.sleep(20)

# =========================
# RUN
# =========================
def main():

    print("TOKEN:", TOKEN)  # 🔥 DEBUG

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handler))

    app.job_queue.run_once(lambda ctx: asyncio.create_task(auto(app)), 5)

    print("🔥 BOT CORRIENDO")
    app.run_polling()

if __name__ == "__main__":
    main()

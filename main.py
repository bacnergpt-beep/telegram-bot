from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import json, unicodedata, re, difflib, asyncio
from datetime import datetime

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

# =========================
# DATA
# =========================
def load():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, dict):
                raise Exception()

            data.setdefault("programacion", [])
            data.setdefault("canales", [])
            data.setdefault("contenido", [])

            return data
    except:
        return {
            "programacion": [],
            "canales": [],
            "contenido": []
        }

def save(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# =========================
# HELPERS
# =========================
def clean(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

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
# BOT
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 BOT FUNCIONANDO", reply_markup=menu())

# =========================
# HANDLER
# =========================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load()
    msg = update.message

    raw = msg.text or msg.caption or ""
    t = clean(raw)

    try:

        # ===== GUARDAR MENSAJES =====
        if context.user_data.get("mode") == "save":

            if t == "guardar":
                msgs = context.user_data.get("temp", [])

                if not msgs:
                    await msg.reply_text("❌ No hay mensajes")
                    return

                data["contenido"] = msgs
                save(data)

                context.user_data.clear()

                await msg.reply_text(f"✅ Guardados {len(msgs)} mensajes")
                return

            context.user_data.setdefault("temp", [])

            context.user_data["temp"].append({
                "chat_id": msg.chat_id,
                "message_id": msg.message_id
            })

            await msg.reply_text(f"📦 Guardado ({len(context.user_data['temp'])})")
            return

        # ===== ACTIVAR GUARDADO =====
        if "mensaje" in t:
            context.user_data["mode"] = "save"
            context.user_data["temp"] = []
            await msg.reply_text("📩 Envía contenido y luego escribe 'guardar'")
            return

        # ===== PANEL =====
        if "panel" in t:
            await msg.reply_text(
                f"📊 PANEL\n\nCanales: {len(data['canales'])}\nHorarios: {len(data['programacion'])}"
            )
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

            prog = data.get("programacion", [])

            if not prog:
                await msg.reply_text("⚠️ No hay horarios\nEj:\nlunes 5pm")
                return

            txt = "⏰ HORARIOS:\n\n"

            for i, p in enumerate(prog, 1):
                dias = ", ".join(p.get("dias", []))
                horas = ", ".join(p.get("horas", []))
                txt += f"{i}. {dias} ⏰ {horas}\n"

            await msg.reply_text(txt)
            return

        # ===== ACTIVOS =====
        if "activos" in t:
            activos = [p for p in data.get("programacion", []) if p.get("activo", True)]

            if not activos:
                await msg.reply_text("⚫ No hay activos")
            else:
                txt = ""
                for p in activos:
                    txt += f"{p['dias']} - {p['horas']}\n"
                await msg.reply_text(txt)
            return

        # ===== ACTIVAR =====
        if "activar" in t:
            await msg.reply_text("🚀 AUTO ACTIVADO")
            return

        # ===== AGREGAR HORARIO =====
        if re.match(r"^[a-z, ]+\s+\d", t):

            match = re.match(r"(.+?)\s+(.+)$", t)
            dias_txt, horas_txt = match.groups()

            dias = [fix_day(d) for d in dias_txt.split(",")]
            horas = [parse_hour(h) for h in horas_txt.split(",")]

            dias = [d for d in dias if d]
            horas = [h for h in horas if h]

            if not dias or not horas:
                await msg.reply_text("❌ Error formato")
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
ultimo_envio = {}

async def auto_envio(app):

    print("🔥 AUTO INICIADO")

    while True:
        try:
            now = datetime.now()
            data = load()

            contenidos = data.get("contenido", [])
            if not contenidos:
                await asyncio.sleep(10)
                continue

            dias_map = {
                "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
                "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
            }

            dia_actual = dias_map[now.strftime("%A").lower()]

            for prog in data.get("programacion", []):

                if dia_actual not in prog["dias"]:
                    continue

                for hora in prog["horas"]:

                    if now.strftime("%H:%M") == hora:

                        clave = f"{dia_actual}-{hora}"

                        if ultimo_envio.get(clave) == now.date():
                            continue

                        for m in contenidos:
                            for canal in data.get("canales", []):
                                await app.bot.copy_message(
                                    chat_id=canal,
                                    from_chat_id=m["chat_id"],
                                    message_id=m["message_id"]
                                )

                        print("✅ ENVIADO")
                        ultimo_envio[clave] = now.date()

        except Exception as e:
            print("ERROR AUTO:", e)

        await asyncio.sleep(20)

# =========================
# RUN
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, handler))

async def post_init(app):
    asyncio.create_task(auto_envio(app))

app.post_init = post_init

print("🔥 BOT LISTO")

app.run_polling()

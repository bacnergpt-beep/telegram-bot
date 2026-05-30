from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import json, unicodedata, re, difflib
from datetime import datetime

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

data = {"programacion": [], "canales": [], "contenido": {}}

# -------- utils --------
def limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip()

def guardar():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def cargar():
    global data
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except:
        guardar()

# -------- hora --------
def parse_hora(h):
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

# -------- días inteligentes --------
dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

def corregir_dia(d):
    d = limpiar(d)
    match = difflib.get_close_matches(d, dias_validos, n=1, cutoff=0.6)
    return match[0] if match else None

# -------- menú --------
def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["📋 Activos", "🚀 Activar"]
    ], resize_keyboard=True)

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cargar()
    await update.message.reply_text("🚀 BOT FUNCIONANDO", reply_markup=menu())

# -------- lógica --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()

    raw = update.message.text or ""
    t = limpiar(raw)

    try:

        # PANEL
        if "panel" in t:
            await update.message.reply_text(
                f"📊 PANEL\n\n"
                f"📢 Canales: {len(data['canales'])}\n"
                f"⏰ Horarios: {len(data['programacion'])}"
            )

        # CANALES
        elif "canales" in t:
            await update.message.reply_text("📢 Envía ID canal\nEj: -100123456")

        elif raw.strip().startswith("-100"):
            cid = int(raw.strip())
            if cid not in data["canales"]:
                data["canales"].append(cid)
                guardar()
            await update.message.reply_text("✅ Canal agregado")

        # MENSAJE
        elif "mensaje" in t:
            context.user_data["modo"] = "esperando_contenido"
            await update.message.reply_text("📩 Envía el mensaje a guardar")

        elif context.user_data.get("modo") == "esperando_contenido":

            data["contenido"] = {
                "chat_id": update.message.chat_id,
                "message_id": update.message.message_id
            }

            guardar()

            # 🔥 FIX IMPORTANTE
            context.user_data.clear()

            await update.message.reply_text("✅ Mensaje guardado correctamente")

        # HORARIOS
        elif "horarios" in t:

            if not data["programacion"]:
                await update.message.reply_text(
                    "⏰ CONFIGURAR\n\n"
                    "Ejemplos:\n"
                    "lunes 5pm\n"
                    "lunes,viernes 6pm\n"
                    "lunes 9am,2pm,8pm"
                )
            else:
                txt = "⏰ HORARIOS:\n\n"
                for i, p in enumerate(data["programacion"], 1):
                    estado = "🟢" if p.get("activo", True) else "🔴"
                    txt += f"{i}. {', '.join(p['dias'])}\n"
                    txt += f"🕒 {', '.join(p['horas'])} {estado}\n\n"

                txt += "🗑 del:1 | ⏸ off:1 | ▶️ on:1"
                await update.message.reply_text(txt)

        # ACTIVOS
        elif "activos" in t:
            activos = [p for p in data["programacion"] if p.get("activo", True)]

            if not activos:
                await update.message.reply_text("⚫ No hay activos")
            else:
                txt = "📋 ACTIVOS:\n\n"
                for p in activos:
                    txt += f"{', '.join(p['dias'])}\n"
                    txt += f"🕒 {', '.join(p['horas'])}\n\n"
                await update.message.reply_text(txt)

        # BORRAR
        elif t.startswith("del:"):
            i = int(t.replace("del:", "")) - 1
            data["programacion"].pop(i)
            guardar()
            await update.message.reply_text("🗑 Eliminado")

        # PAUSAR
        elif t.startswith("off:"):
            i = int(t.replace("off:", "")) - 1
            data["programacion"][i]["activo"] = False
            guardar()
            await update.message.reply_text("🔴 Pausado")

        # ACTIVAR
        elif t.startswith("on:"):
            i = int(t.replace("on:", "")) - 1
            data["programacion"][i]["activo"] = True
            guardar()
            await update.message.reply_text("🟢 Activado")

        # PANEL COMPLETO
        elif t.startswith(".panel"):
            await update.message.reply_text(
                "📘 PANEL\n\n"
                "Agregar: lunes 5pm\n"
                "Ver: horarios\n"
                "Activos: activos\n"
                "Eliminar: del:1\n"
                "Pausar: off:1\n"
                "Activar: on:1"
            )

        # AGREGAR HORARIOS
        elif re.match(r".+\s+.+", t):

            match = re.match(r"(.+?)\s+(.+)$", t)
            dias_txt = match.group(1)
            horas_txt = match.group(2)

            dias = dias_txt.split(",")
            horas_lista = horas_txt.split(",")

            dias_final = []
            for d in dias:
                c = corregir_dia(d)
                if c:
                    dias_final.append(c)

            horas_final = []
            for h in horas_lista:
                ph = parse_hora(h)
                if ph:
                    horas_final.append(ph)

            if not dias_final or not horas_final:
                await update.message.reply_text("❌ Error en formato")
                return

            data["programacion"].append({
                "dias": dias_final,
                "horas": horas_final,
                "activo": True
            })

            guardar()
            await update.message.reply_text("✅ Programado")

        elif "activar" in t:
            await update.message.reply_text("🚀 AUTO ACTIVO")

        else:
            await update.message.reply_text("❌ No válido")

    except Exception as e:
        print("ERROR:", e)
        await update.message.reply_text("⚠️ Error")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texto))

print("🔥 BOT 100% FUNCIONAL")
app.run_polling()

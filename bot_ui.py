from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, asyncio, unicodedata, re

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
OWNER_ID = 7752782654
CONFIG_PATH = "config_data.json"

usuarios_autorizados = [OWNER_ID]

data = {"canales": [], "programacion": [], "contenido": {}}

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

def parse_hora(h):
    h = h.lower().replace(" ", "")
    try:
        from datetime import datetime
        if "am" in h or "pm" in h:
            t = datetime.strptime(h, "%I:%M%p") if ":" in h else datetime.strptime(h, "%I%p")
            return t.strftime("%H:%M")
        else:
            hh, mm = map(int, h.split(":"))
            return f"{hh:02d}:{mm:02d}"
    except:
        return None

def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["🚀 Activar"]
    ], resize_keyboard=True)

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cargar()
    await update.message.reply_text("🚀 BOT PRO ACTIVO", reply_markup=menu())

# -------- lógica --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()
    data.setdefault("programacion", [])

    raw = update.message.text or ""
    t = limpiar(raw)

    msg = await update.message.reply_text("⏳")
    await asyncio.sleep(0.1)

    dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

    try:

        # PANEL
        if "panel" in t:
            await msg.edit_text(
                f"📊 PANEL\n\n"
                f"📢 Canales: {len(data['canales'])}\n"
                f"⏰ Horarios: {len(data['programacion'])}\n"
                f"⚡ Estado: ACTIVO"
            )

        # CANALES
        elif "canales" in t:
            await msg.edit_text("📢 Envía ID canal\nEj: -100123456")

        elif raw.strip().startswith("-100"):
            cid = int(raw.strip())
            if cid not in data["canales"]:
                data["canales"].append(cid)
                guardar()
            await msg.edit_text("✅ Canal agregado")

        # MENSAJE
        elif "mensaje" in t:
            context.user_data["modo"] = True
            await msg.edit_text("📩 Envía mensaje")

        elif context.user_data.get("modo"):
            data["contenido"] = {
                "chat_id": update.message.chat_id,
                "message_id": update.message.message_id
            }
            guardar()
            context.user_data["modo"] = False
            await msg.edit_text("✅ Guardado")

        # HORARIOS (CON GUÍA)
        elif "horarios" in t:

            prog = data["programacion"]

            if not prog:
                await msg.edit_text(
                    "⏰ CONFIGURAR HORARIOS\n\n"
                    "📌 Ejemplos:\n"
                    "lunes 5pm\n"
                    "lunes,viernes 6pm\n"
                    "lunes,martes 9am,2pm,8pm\n"
                    "domingo 17:20\n\n"
                    "✍️ Escribe uno para empezar"
                )

            else:
                txt = "⏰ HORARIOS:\n\n"

                for i, p in enumerate(prog, 1):
                    estado = "🟢" if p.get("activo", True) else "🔴"

                    txt += f"{i}. {', '.join(p['dias'])}\n"
                    txt += f"   🕒 {', '.join(p['horas'])} {estado}\n\n"

                txt += "➕ lunes 5pm\n🗑 del:1\n⏸ off:1\n▶️ on:1"
                await msg.edit_text(txt)

        # ELIMINAR
        elif t.startswith("del:"):
            i = int(t.replace("del:", "")) - 1
            data["programacion"].pop(i)
            guardar()
            await msg.edit_text("🗑 Eliminado")

        # PAUSAR
        elif t.startswith("off:"):
            i = int(t.replace("off:", "")) - 1
            data["programacion"][i]["activo"] = False
            guardar()
            await msg.edit_text("🔴 Pausado")

        # ACTIVAR
        elif t.startswith("on:"):
            i = int(t.replace("on:", "")) - 1
            data["programacion"][i]["activo"] = True
            guardar()
            await msg.edit_text("🟢 Activado")

        # AGREGAR HORARIOS PRO
        elif any(d in t for d in dias_validos):

            match = re.match(r"(.+?)\s+(.+)$", t)

            dias_txt = match.group(1)
            horas_txt = match.group(2)

            dias = [d.strip().replace(",", "") for d in dias_txt.split(",")]
            horas_lista = [h.strip() for h in horas_txt.split(",")]

            dias_final = [d for d in dias if d in dias_validos]

            horas_final = []
            for h in horas_lista:
                ph = parse_hora(h)
                if ph:
                    horas_final.append(ph)

            data["programacion"].append({
                "dias": dias_final,
                "horas": horas_final,
                "activo": True
            })

            guardar()
            await msg.edit_text("✅ Programado correctamente")

        elif "activar" in t:
            await msg.edit_text("🚀 AUTO ACTIVO")

        else:
            await msg.edit_text("❌ Comando inválido")

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("⚠️ Error")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))

print("BOT PRO LISTO")
app.run_polling()

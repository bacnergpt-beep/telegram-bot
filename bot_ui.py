from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, asyncio, unicodedata

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
OWNER_ID = 7752782654
CONFIG_PATH = "config_data.json"

usuarios_autorizados = [OWNER_ID]

data = {
    "canales": [],
    "programacion": [],
    "contenido": {}
}

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

def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["🚀 Activar"]
    ], resize_keyboard=True)

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in usuarios_autorizados:
        return
    cargar()
    await update.message.reply_text("🚀 BOT ACTIVO", reply_markup=menu())

# -------- lógica --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()

    data.setdefault("programacion", [])
    data.setdefault("canales", [])
    data.setdefault("contenido", {})

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
            await msg.edit_text("Envía ID canal\nEj: -100123456")

        elif raw.strip().startswith("-100"):
            cid = int(raw.strip())
            if cid not in data["canales"]:
                data["canales"].append(cid)
                guardar()
            await msg.edit_text("✅ Canal agregado")

        # MENSAJE
        elif "mensaje" in t:
            context.user_data["modo"] = True
            await msg.edit_text("Envía mensaje")

        elif context.user_data.get("modo"):
            data["contenido"] = {
                "chat_id": update.message.chat_id,
                "message_id": update.message.message_id
            }
            guardar()
            context.user_data["modo"] = False
            await msg.edit_text("✅ Mensaje guardado")

        # VER HORARIOS
        elif "horarios" in t:
            prog = data["programacion"]

            if not prog:
                await msg.edit_text("❌ No hay horarios")
            else:
                txt = "⏰ HORARIOS:\n\n"
                for i, p in enumerate(prog, 1):
                    txt += f"{i}. {','.join(p['dias'])} {p['hora']}\n"

                txt += "\n➕ lunes,viernes 16:30\n🗑 del:1"
                await msg.edit_text(txt)

        # ELIMINAR
        elif t.startswith("del:"):
            i = int(t.replace("del:", "")) - 1
            if 0 <= i < len(data["programacion"]):
                data["programacion"].pop(i)
                guardar()
                await msg.edit_text("🗑 Eliminado")

        # AGREGAR PROGRAMACIÓN
        elif any(d in t for d in dias_validos):

            try:
                partes = t.split()
                dias = partes[0].split(",")
                hora = partes[1]

                data["programacion"].append({
                    "dias": dias,
                    "hora": hora,
                    "activo": True
                })

                guardar()
                await msg.edit_text("✅ Programado")

            except:
                await msg.edit_text("❌ Usa: lunes,viernes 16:30")

        elif "activar" in t:
            await msg.edit_text("🚀 AUTO CORRIENDO")

        else:
            await msg.edit_text("❌ Comando inválido")

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("⚠️ Error")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))

print("BOT LISTO")
app.run_polling()

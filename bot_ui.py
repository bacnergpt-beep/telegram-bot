from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, asyncio, re, unicodedata
from datetime import datetime

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
OWNER_ID = 7752782654
CONFIG_PATH = "config_data.json"

usuarios_autorizados = [OWNER_ID]

data = {
    "canales": [],
    "eventos": [],
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
        ["📊 Dashboard", "📢 Canales"],
        ["📩 Mensaje", "📅 Eventos"],
        ["🚀 Activar"]
    ], resize_keyboard=True)

def parse_evento(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d %H:%M")
    except:
        return None

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in usuarios_autorizados:
        await update.message.reply_text("⛔ No tienes acceso")
        return
    cargar()
    await update.message.reply_text("🚀 BOT PRO LISTO", reply_markup=menu())

# -------- lógica --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in usuarios_autorizados:
        await update.message.reply_text("⛔ No tienes acceso")
        return

    raw = update.message.text or ""
    t = limpiar(raw)

    msg = await update.message.reply_text("⏳")
    await asyncio.sleep(0.2)

    dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

    # DASHBOARD
    if "dashboard" in t:
        total = len(data["eventos"])
        activos = len([e for e in data["eventos"] if e.get("activo", True)])
        await msg.edit_text(
            f"📊 PANEL\n\n"
            f"📢 Canales: {len(data['canales'])}\n"
            f"📅 Eventos: {total}\n"
            f"🟢 Activos: {activos}"
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
        context.user_data["modo_mensaje"] = True
        await msg.edit_text("📩 Envía mensaje")

    elif context.user_data.get("modo_mensaje"):
        data["contenido"] = {
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id
        }
        guardar()
        context.user_data["modo_mensaje"] = False
        await msg.edit_text("✅ Guardado")

    # EVENTOS LISTA
    elif "eventos" in t:
        if not data["eventos"]:
            await msg.edit_text("❌ No hay eventos")
        else:
            txt = "📅 EVENTOS:\n\n"
            for i, e in enumerate(data["eventos"], 1):
                estado = "🟢" if e.get("activo", True) else "🔴"
                if e.get("tipo") == "repetitivo":
                    txt += f"{i}. 🔁 {e['dia']} {e['hora']} {estado}\n"
                else:
                    txt += f"{i}. {e['fecha']} {e['hora']} {estado}\n"

            txt += "\n➕ 2026-03-15 16:30\n🔁 lunes 08:00\n🗑 del:1\n✏️ edit:1 2026-03-20 18:00"
            await msg.edit_text(txt)

    # ELIMINAR
    elif t.startswith("del:"):
        i = int(t.replace("del:", "")) - 1
        if 0 <= i < len(data["eventos"]):
            eliminado = data["eventos"].pop(i)
            guardar()
            await msg.edit_text("🗑 Eliminado")

    # EDITAR
    elif t.startswith("edit:"):
        try:
            partes = raw.split()
            i = int(partes[0].replace("edit:", "")) - 1
            fecha = partes[1]
            hora = partes[2]

            data["eventos"][i]["fecha"] = fecha
            data["eventos"][i]["hora"] = hora
            guardar()

            await msg.edit_text("✏️ Editado")
        except:
            await msg.edit_text("❌ Formato inválido")

    # EVENTO NORMAL
    else:
        evento = parse_evento(raw)
        if evento:
            data["eventos"].append({
                "fecha": evento.strftime("%Y-%m-%d"),
                "hora": evento.strftime("%H:%M"),
                "activo": True
            })
            guardar()
            await msg.edit_text("✅ Evento agregado")

        # REPETITIVO
        elif any(d in t for d in dias_validos):
            partes = t.split()
            if len(partes) == 2:
                data["eventos"].append({
                    "tipo": "repetitivo",
                    "dia": partes[0],
                    "hora": partes[1],
                    "activo": True
                })
                guardar()
                await msg.edit_text("🔁 Repetición agregada")

        elif "activar" in t:
            await msg.edit_text("🚀 AUTO CORRIENDO")

        else:
            await msg.edit_text("❌ No válido")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))

print("BOT LISTO")
app.run_polling()

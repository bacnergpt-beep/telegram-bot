from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, asyncio, unicodedata
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
        data = {"canales": [], "eventos": [], "contenido": {}}
        guardar()

def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "📅 Eventos"],
        ["🚀 Activar"]
    ], resize_keyboard=True)

def parse_evento(texto):
    try:
        texto = texto.strip()
        f, h = texto.split()
        y,m,d = map(int, f.split("-"))
        hh,mm = map(int, h.split(":"))
        return datetime(y,m,d,hh,mm)
    except:
        return None

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in usuarios_autorizados:
        await update.message.reply_text("⛔ Acceso denegado")
        return
    cargar()
    await update.message.reply_text("🚀 BOT PRO ACTIVO", reply_markup=menu())

# -------- lógica --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()

    if "eventos" not in data:
        data["eventos"] = []

    user_id = update.effective_user.id

    if user_id not in usuarios_autorizados:
        return

    raw = update.message.text or ""
    t = limpiar(raw)

    msg = await update.message.reply_text("⏳")
    await asyncio.sleep(0.1)

    dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

    try:

        # 🎨 PANEL PRO
        if "panel" in t or "dashboard" in t:
            total = len(data["eventos"])
            activos = len([e for e in data["eventos"] if e.get("activo", True)])

            await msg.edit_text(
                f"📊 PANEL PRO\n\n"
                f"🔵 Canales: {len(data['canales'])}\n"
                f"🟡 Eventos: {total}\n"
                f"🟢 Activos: {activos}\n"
                f"🔴 Inactivos: {total - activos}\n\n"
                f"⚡ Estado: OPERATIVO"
            )

        # 📢 CANALES
        elif "canales" in t:
            await msg.edit_text("📢 Envía ID canal\nEj: -100123456")

        elif raw.strip().startswith("-100"):
            cid = int(raw.strip())
            if cid not in data["canales"]:
                data["canales"].append(cid)
                guardar()
            await msg.edit_text("🟢 Canal agregado")

        # 📩 MENSAJE
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
            await msg.edit_text("🟢 Mensaje guardado")

        # 📅 EVENTOS
        elif "eventos" in t:
            if not data["eventos"]:
                await msg.edit_text("⚫ No hay eventos")
            else:
                txt = "📅 EVENTOS\n\n"
                for i, e in enumerate(data["eventos"], 1):
                    estado = "🟢" if e.get("activo", True) else "🔴"

                    if e.get("tipo") == "repetitivo":
                        txt += f"{i}. 🔁 {e['dia']} {e['hora']} {estado}\n"
                    else:
                        txt += f"{i}. 📆 {e['fecha']} {e['hora']} {estado}\n"

                txt += "\n➕ 2026-03-15 16:30\n🔁 lunes 08:00\n🗑 del:1\n✏️ edit:1 2026-03-20 18:00"
                await msg.edit_text(txt)

        # 🗑 ELIMINAR
        elif t.startswith("del:"):
            i = int(t.replace("del:", "")) - 1
            if 0 <= i < len(data["eventos"]):
                data["eventos"].pop(i)
                guardar()
                await msg.edit_text("🔴 Evento eliminado")

        # ✏️ EDITAR
        elif t.startswith("edit:"):
            partes = raw.split()
            i = int(partes[0].replace("edit:", "")) - 1
            data["eventos"][i]["fecha"] = partes[1]
            data["eventos"][i]["hora"] = partes[2]
            guardar()
            await msg.edit_text("🟡 Evento editado")

        # ➕ EVENTO
        else:
            evento = parse_evento(raw)

            if evento:
                data["eventos"].append({
                    "fecha": evento.strftime("%Y-%m-%d"),
                    "hora": evento.strftime("%H:%M"),
                    "activo": True
                })
                guardar()
                await msg.edit_text("🟢 Evento agregado")

            elif any(d in t for d in dias_validos):
                partes = t.split()
                data["eventos"].append({
                    "tipo": "repetitivo",
                    "dia": partes[0],
                    "hora": partes[1],
                    "activo": True
                })
                guardar()
                await msg.edit_text("🟢 Repetición agregada")

            elif "activar" in t:
                await msg.edit_text("🚀 AUTO EN MARCHA")

            else:
                await msg.edit_text("❌ Comando inválido")

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("⚠️ Error interno")
        
# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))

print("BOT PRO LISTO")
app.run_polling()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json, asyncio, re, unicodedata

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
OWNER_ID = 7752782654
CONFIG_PATH = r"C:\Users\BACNER\Desktop\config_data.json"

# 🔐 usuarios permitidos
usuarios_autorizados = [OWNER_ID]

data = {
    "canales": [],
    "horas": [],   # [{"hora":"16:30","activo":True}]
    "dias": [],
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
        json.dump(data, f)

def cargar():
    global data
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except:
        guardar()

def parse_hora(t):
    m = re.search(r'(\d{1,2})[:h\s]?(\d{2})?', t)
    if not m:
        return None
    h = int(m.group(1))
    mi = int(m.group(2)) if m.group(2) else 0
    if "pm" in t and h < 12: h += 12
    if "am" in t and h == 12: h = 0
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return f"{h:02d}:{mi:02d}"
    return None

def menu():
    return ReplyKeyboardMarkup([
        ["📊 Dashboard", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["📅 Días", "🚀 Activar"]
    ], resize_keyboard=True)

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

    # 🔐 acceso
    if user_id not in usuarios_autorizados:
        await update.message.reply_text("⛔ No tienes acceso")
        return

    raw = update.message.text or ""
    t = limpiar(raw)

    msg = await update.message.reply_text("⏳")
    await asyncio.sleep(0.2)

    dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

    # -------- ADMIN USUARIOS --------
    if t.startswith("add:") and user_id == OWNER_ID:
        try:
            uid = int(t.replace("add:", ""))
            if uid not in usuarios_autorizados:
                usuarios_autorizados.append(uid)
            await msg.edit_text(f"✅ Usuario agregado: {uid}")
        except:
            await msg.edit_text("❌ Error")

    elif t.startswith("deluser:") and user_id == OWNER_ID:
        try:
            uid = int(t.replace("deluser:", ""))
            if uid in usuarios_autorizados and uid != OWNER_ID:
                usuarios_autorizados.remove(uid)
                await msg.edit_text(f"🗑 Eliminado: {uid}")
            else:
                await msg.edit_text("❌ No válido")
        except:
            await msg.edit_text("❌ Error")

    elif t == "users" and user_id == OWNER_ID:
        await msg.edit_text("👥 Usuarios:\n" + "\n".join(map(str, usuarios_autorizados)))

    # -------- DASHBOARD --------
    elif "dashboard" in t:
        await msg.edit_text(
            f"📊 Canales: {len(data['canales'])}\n"
            f"⏰ Horarios: {len(data['horas'])}\n"
            f"📅 Días: {len(data['dias'])}"
        )

    # -------- CANALES --------
    elif "canales" in t:
        await msg.edit_text("📢 Envía el ID del canal o grupo\nEjemplo:\n-1001234567890")

    elif raw.strip().startswith("-100"):
        try:
            cid = int(raw.strip())
            if cid not in data["canales"]:
                data["canales"].append(cid)
                guardar()
            await msg.edit_text("✅ Canal agregado")
        except:
            await msg.edit_text("❌ ID inválido")

    # -------- MENSAJE EXACTO (copy_message) --------
    elif "mensaje" in t:
        context.user_data["modo_mensaje"] = True
        await msg.edit_text("📩 Reenvía o envía el mensaje (se guardará EXACTO)")

    elif context.user_data.get("modo_mensaje"):
        data["contenido"] = {
            "tipo": "copy",
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id
        }
        guardar()
        context.user_data["modo_mensaje"] = False
        await msg.edit_text("✅ Guardado (modo exacto/premium)")

    # -------- HORARIOS (multi ON/OFF) --------
    elif "horarios" in t:
        if data["horas"]:
            txt = "⏰ Horarios:\n"
            for i, h in enumerate(data["horas"], 1):
                estado = "🟢" if h.get("activo", True) else "🔴"
                txt += f"{i}. {h.get('hora')} {estado}\n"
            txt += "\n➕ Envía hora\n🗑 del:1\n🔄 on:1 / off:1"
            await msg.edit_text(txt)
        else:
            await msg.edit_text("No hay horarios\nEnvía una hora (ej: 16:30)")

    elif t.startswith("del:"):
        try:
            i = int(t.replace("del:", "").strip()) - 1
            if 0 <= i < len(data["horas"]):
                eliminado = data["horas"].pop(i)
                guardar()
                await msg.edit_text(f"🗑 Eliminado: {eliminado['hora']}")
            else:
                await msg.edit_text("❌ Número inválido")
        except:
            await msg.edit_text("❌ Usa del:1")

    elif t.startswith("on:"):
        try:
            i = int(t.replace("on:", "").strip()) - 1
            data["horas"][i]["activo"] = True
            guardar()
            await msg.edit_text("🟢 Activado")
        except:
            await msg.edit_text("❌ Error")

    elif t.startswith("off:"):
        try:
            i = int(t.replace("off:", "").strip()) - 1
            data["horas"][i]["activo"] = False
            guardar()
            await msg.edit_text("🔴 Desactivado")
        except:
            await msg.edit_text("❌ Error")

    # -------- HORAS (agregar) --------
    else:
        hora = parse_hora(t)
        if hora:
            data["horas"].append({"hora": hora, "activo": True})
            guardar()
            await msg.edit_text(f"✅ Hora agregada: {hora}")

        # -------- DÍAS --------
        elif "dia" in t:
            lista = ", ".join(data["dias"]) if data["dias"] else "Sin días"
            await msg.edit_text(f"📅 Días actuales:\n{lista}\n\nEj: lunes,viernes")

        elif any(d in t for d in dias_validos):
            lista = re.split('[, ]+', t)
            dias = [d for d in lista if d in dias_validos]
            if dias:
                data["dias"] = list(set(dias))
                guardar()
                await msg.edit_text(f"✅ Días: {', '.join(data['dias'])}")
            else:
                await msg.edit_text("❌ Día inválido")

        # -------- ACTIVAR (informativo) --------
        elif "activar" in t:
            await msg.edit_text("🚀 SISTEMA ACTIVADO (auto.py debe estar corriendo)")

        else:
            await msg.edit_text("❌ No válido")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))

print("🔐 BOT UI PRO LISTO")
app.run_polling()

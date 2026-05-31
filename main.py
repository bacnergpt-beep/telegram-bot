import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔥 PON TU TOKEN AQUÍ (SIN ESPACIOS)
TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"

CONFIG = "config_data.json"

# =========================
# CARGAR DATOS
# =========================
def load_data():
    if not os.path.exists(CONFIG):
        return {"programacion": [], "canales": [], "contenido": []}
    with open(CONFIG, "r") as f:
        return json.load(f)

# =========================
# GUARDAR DATOS
# =========================
def save_data(data):
    with open(CONFIG, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 BOT ACTIVO")

# =========================
# PANEL
# =========================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        f"📊 PANEL\n\nCanales: {len(data['canales'])}\nHorarios: {len(data['programacion'])}"
    )

# =========================
# GUARDAR MENSAJE (REENVIADO)
# =========================
async def guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Responde al mensaje a guardar")
        return

    data = load_data()
    msg = update.message.reply_to_message

    contenido = {
        "text": msg.text or msg.caption,
        "file_id": None
    }

    # detectar imagen
    if msg.photo:
        contenido["file_id"] = msg.photo[-1].file_id

    data["contenido"].append(contenido)
    save_data(data)

    await update.message.reply_text("✅ Guardado correctamente")

# =========================
# HORARIOS
# =========================
async def horarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data["programacion"]:
        await update.message.reply_text("❌ No hay horarios")
        return

    msg = "⏰ HORARIOS:\n"
    for h in data["programacion"]:
        msg += f"\n{h}"

    await update.message.reply_text(msg)

# =========================
# ACTIVOS
# =========================
async def activos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data["programacion"]:
        await update.message.reply_text("❌ No hay activos")
        return

    msg = "📋 ACTIVOS:\n"
    for h in data["programacion"]:
        msg += f"\n{h}"

    await update.message.reply_text(msg)

# =========================
# MAIN
# =========================
def main():
    print("🔥 Iniciando bot...")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("guardar", guardar))
    app.add_handler(CommandHandler("horarios", horarios))
    app.add_handler(CommandHandler("activos", activos))

    print("✅ Bot corriendo")
    app.run_polling()

if __name__ == "__main__":
    main()

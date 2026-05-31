import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY")

if not TOKEN:
    raise ValueError("TOKEN no encontrado")

CONFIG = "config_data.json"

def load_data():
    if not os.path.exists(CONFIG):
        return {"programacion": [], "canales": [], "contenido": []}
    with open(CONFIG, "r") as f:
        return json.load(f)

def save_data(data):
    with open(CONFIG, "w") as f:
        json.dump(data, f, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot funcionando correctamente")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        f"📊 PANEL\n\nCanales: {len(data['canales'])}\nHorarios: {len(data['programacion'])}"
    )

async def guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Responde al mensaje")
        return

    data = load_data()
    msg = update.message.reply_to_message

    contenido = {
        "text": msg.text or msg.caption,
        "file_id": None
    }

    if msg.photo:
        contenido["file_id"] = msg.photo[-1].file_id

    data["contenido"].append(contenido)
    save_data(data)

    await update.message.reply_text("✅ Guardado")

async def horarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data["programacion"]:
        await update.message.reply_text("❌ No hay horarios")
        return

    msg = "⏰ HORARIOS:\n"
    for h in data["programacion"]:
        msg += f"\n{h}"

    await update.message.reply_text(msg)

async def activos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data["programacion"]:
        await update.message.reply_text("❌ No hay activos")
        return

    msg = "📋 ACTIVOS:\n"
    for h in data["programacion"]:
        msg += f"\n{h}"

    await update.message.reply_text(msg)

def main():
    print("Iniciando bot...")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("guardar", guardar))
    app.add_handler(CommandHandler("horarios", horarios))
    app.add_handler(CommandHandler("activos", activos))

    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()

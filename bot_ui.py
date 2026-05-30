from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

import json

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

data = {"programacion": [], "contenido": {}, "canales": []}

# -------- utils --------
def cargar():
    global data
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except:
        guardar()

def guardar():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# -------- MENÚ PRINCIPAL --------
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📊 Panel", callback_data="panel")],
        [InlineKeyboardButton("⏰ Horarios", callback_data="horarios")],
        [InlineKeyboardButton("📋 Activos", callback_data="activos")]
    ]

    await update.message.reply_text(
        "🏠 MENÚ PRINCIPAL",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cargar()
    await menu_principal(update, context)

# -------- SUBMENÚ HORARIOS --------
async def menu_horarios(query):

    keyboard = [
        [InlineKeyboardButton("➕ Agregar", callback_data="add")],
        [InlineKeyboardButton("📋 Ver", callback_data="ver")],
        [InlineKeyboardButton("⬅️ Volver", callback_data="main")]
    ]

    await query.edit_message_text(
        "⏰ HORARIOS",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- CALLBACK CENTRAL --------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data_cb = query.data

    # VOLVER
    if data_cb == "main":
        keyboard = [
            [InlineKeyboardButton("📊 Panel", callback_data="panel")],
            [InlineKeyboardButton("⏰ Horarios", callback_data="horarios")],
            [InlineKeyboardButton("📋 Activos", callback_data="activos")]
        ]

        await query.edit_message_text(
            "🏠 MENÚ PRINCIPAL",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # PANEL
    elif data_cb == "panel":
        await query.edit_message_text(
            f"📊 PANEL\n\n"
            f"📢 Canales: {len(data['canales'])}\n"
            f"⏰ Horarios: {len(data['programacion'])}"
        )

    # HORARIOS
    elif data_cb == "horarios":
        await menu_horarios(query)

    # VER HORARIOS
    elif data_cb == "ver":

        if not data["programacion"]:
            txt = "⚫ No hay horarios"
        else:
            txt = "📋 HORARIOS:\n\n"

            for i, p in enumerate(data["programacion"], 1):
                txt += f"{i}. {', '.join(p['dias'])}\n"
                txt += f"🕒 {', '.join(p['horas'])}\n\n"

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="horarios")]]

        await query.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ACTIVOS
    elif data_cb == "activos":

        activos = [p for p in data["programacion"] if p.get("activo", True)]

        if not activos:
            txt = "⚫ No hay activos"
        else:
            txt = "📋 ACTIVOS:\n\n"
            for p in activos:
                txt += f"{', '.join(p['dias'])}\n"
                txt += f"🕒 {', '.join(p['horas'])}\n\n"

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="main")]]

        await query.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # AGREGAR HORARIO (PASO 1)
    elif data_cb == "add":

        context.user_data["dias"] = []
        context.user_data["horas"] = []

        keyboard = [
            [InlineKeyboardButton("L", callback_data="d_lunes"),
             InlineKeyboardButton("M", callback_data="d_martes"),
             InlineKeyboardButton("X", callback_data="d_miercoles")],

            [InlineKeyboardButton("J", callback_data="d_jueves"),
             InlineKeyboardButton("V", callback_data="d_viernes"),
             InlineKeyboardButton("S", callback_data="d_sabado")],

            [InlineKeyboardButton("D", callback_data="d_domingo")],

            [InlineKeyboardButton("⏰ Horas", callback_data="hora")],
            [InlineKeyboardButton("✅ Guardar", callback_data="save")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="horarios")]
        ]

        await query.edit_message_text(
            "📅 Selecciona días",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SELECCIONAR DÍAS
    elif data_cb.startswith("d_"):
        dia = data_cb.replace("d_", "")
        context.user_data["dias"].append(dia)
        await query.answer(f"✔ {dia}")

    # MENÚ HORAS
    elif data_cb == "hora":

        keyboard = [
            [InlineKeyboardButton("09:00", callback_data="h_09:00"),
             InlineKeyboardButton("14:00", callback_data="h_14:00")],
            [InlineKeyboardButton("20:00", callback_data="h_20:00")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="add")]
        ]

        await query.edit_message_text(
            "⏰ Selecciona horas",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SELECCIONAR HORAS
    elif data_cb.startswith("h_"):
        hora = data_cb.replace("h_", "")
        context.user_data["horas"].append(hora)
        await query.answer(f"✔ {hora}")

    # GUARDAR
    elif data_cb == "save":

        dias = context.user_data.get("dias", [])
        horas = context.user_data.get("horas", [])

        if not dias or not horas:
            await query.edit_message_text("❌ Falta seleccionar datos")
            return

        data["programacion"].append({
            "dias": dias,
            "horas": horas,
            "activo": True
        })

        guardar()

        await query.edit_message_text("✅ Guardado correctamente")

# -------- RUN --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callbacks))

print("🔥 BOT APP REAL")
app.run_polling()

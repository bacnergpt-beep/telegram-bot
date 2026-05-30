from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import json, unicodedata, re, difflib

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

data = {"programacion": []}

# -------- utils --------
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

def limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip()

# -------- MENÚ PRINCIPAL --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()

    keyboard = [
        [InlineKeyboardButton("📊 Panel", callback_data="panel")],
        [InlineKeyboardButton("⏰ Horarios", callback_data="horarios")],
        [InlineKeyboardButton("📋 Activos", callback_data="activos")]
    ]

    await update.message.reply_text(
        "🚀 BOT PRO",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- CALLBACKS --------
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    cargar()

    data_cb = query.data

    # PANEL
    if data_cb == "panel":

        await query.edit_message_text(
            f"📊 PANEL\n\n"
            f"⏰ Horarios: {len(data['programacion'])}\n"
            f"⚡ Estado: ACTIVO",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Volver", callback_data="main")]
            ])
        )

    # MENÚ PRINCIPAL
    elif data_cb == "main":
        await start(update, context)

    # HORARIOS MENU
    elif data_cb == "horarios":

        keyboard = [
            [InlineKeyboardButton("➕ Agregar", callback_data="add")],
            [InlineKeyboardButton("📋 Ver", callback_data="ver")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="main")]
        ]

        await query.edit_message_text(
            "⏰ HORARIOS",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # VER HORARIOS
    elif data_cb == "ver":

        if not data["programacion"]:
            txt = "⚫ No hay horarios"
        else:
            txt = "📋 HORARIOS:\n\n"

            for i, p in enumerate(data["programacion"], 1):
                estado = "🟢" if p.get("activo", True) else "🔴"
                txt += f"{i}. {', '.join(p['dias'])}\n"
                txt += f"🕒 {', '.join(p['horas'])} {estado}\n\n"

        await query.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Volver", callback_data="horarios")]
            ])
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

        await query.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Volver", callback_data="main")]
            ])
        )

    # AGREGAR
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

            [InlineKeyboardButton("⏰ Hora", callback_data="hora")],
            [InlineKeyboardButton("✅ Guardar", callback_data="save")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="horarios")]
        ]

        await query.edit_message_text(
            "📅 Selecciona días",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SELECCIÓN DÍA
    elif data_cb.startswith("d_"):
        dia = data_cb.replace("d_", "")

        context.user_data.setdefault("dias", [])

        if dia not in context.user_data["dias"]:
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
            "⏰ Selecciona hora",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # SELECCIÓN HORA
    elif data_cb.startswith("h_"):
        hora = data_cb.replace("h_", "")

        context.user_data.setdefault("horas", [])

        if hora not in context.user_data["horas"]:
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

# -------- TEXTO (OPCIONAL INTELIGENTE) --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()

    raw = update.message.text or ""
    t = limpiar(raw)

    dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

    if any(d in t for d in dias_validos):

        match = re.match(r"(.+?)\s+(.+)$", t)

        dias_txt = match.group(1)
        horas_txt = match.group(2)

        dias = [d.strip() for d in dias_txt.split(",")]
        horas = [h.strip() for h in horas_txt.split(",")]

        data["programacion"].append({
            "dias": dias,
            "horas": horas,
            "activo": True
        })

        guardar()

        await update.message.reply_text("✅ Programado")

# -------- RUN --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callbacks))
app.add_handler(MessageHandler(filters.TEXT, texto))

print("🔥 BOT APP PRO")
app.run_polling()

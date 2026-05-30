from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

import json, asyncio, unicodedata, re, difflib

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

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
    from datetime import datetime
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

dias_validos = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]

def corregir_dia(d):
    match = difflib.get_close_matches(d, dias_validos, n=1, cutoff=0.6)
    return match[0] if match else None

# -------- menu --------
def menu():
    return ReplyKeyboardMarkup([
        ["📊 Panel", "📢 Canales"],
        ["📩 Mensaje", "⏰ Horarios"],
        ["📋 Activos", "🎛️ Visual"],
        ["🚀 Activar"]
    ], resize_keyboard=True)

# -------- start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cargar()
    await update.message.reply_text("🚀 BOT PRO", reply_markup=menu())

# -------- BOTONES VISUALES --------
async def visual(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("Lunes", callback_data="dia_lunes"),
         InlineKeyboardButton("Martes", callback_data="dia_martes")],

        [InlineKeyboardButton("Miércoles", callback_data="dia_miercoles"),
         InlineKeyboardButton("Jueves", callback_data="dia_jueves")],

        [InlineKeyboardButton("Viernes", callback_data="dia_viernes"),
         InlineKeyboardButton("Sábado", callback_data="dia_sabado")],

        [InlineKeyboardButton("Domingo", callback_data="dia_domingo")],

        [InlineKeyboardButton("⏰ Elegir hora", callback_data="hora")],
        [InlineKeyboardButton("✅ Guardar", callback_data="guardar")]
    ]

    context.user_data["dias_temp"] = []
    context.user_data["horas_temp"] = []

    await update.message.reply_text(
        "🎛️ MODO VISUAL\nSelecciona días:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- CALLBACK --------
async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data_cb = query.data

    if data_cb.startswith("dia_"):
        dia = data_cb.replace("dia_", "")

        context.user_data.setdefault("dias_temp", [])

        if dia not in context.user_data["dias_temp"]:
            context.user_data["dias_temp"].append(dia)

        await query.edit_message_text(f"📅 Días: {context.user_data['dias_temp']}")

    elif data_cb == "hora":

        keyboard = [
            [InlineKeyboardButton("09:00", callback_data="h_09:00"),
             InlineKeyboardButton("14:00", callback_data="h_14:00")],
            [InlineKeyboardButton("20:00", callback_data="h_20:00")]
        ]

        await query.edit_message_text(
            "⏰ Selecciona hora:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data_cb.startswith("h_"):
        hora = data_cb.replace("h_", "")

        context.user_data.setdefault("horas_temp", [])

        if hora not in context.user_data["horas_temp"]:
            context.user_data["horas_temp"].append(hora)

        await query.edit_message_text(f"⏰ Horas: {context.user_data['horas_temp']}")

    elif data_cb == "guardar":

        dias = context.user_data.get("dias_temp", [])
        horas = context.user_data.get("horas_temp", [])

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

# -------- lógica principal --------
async def texto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cargar()
    raw = update.message.text or ""
    t = limpiar(raw)

    msg = await update.message.reply_text("⏳")
    await asyncio.sleep(0.1)

    try:

        if "visual" in t:
            await visual(update, context)

        elif "activos" in t:
            activos = [p for p in data["programacion"] if p.get("activo", True)]

            txt = "📋 ACTIVOS\n\n"
            for p in activos:
                txt += f"{', '.join(p['dias'])}\n🕒 {', '.join(p['horas'])}\n\n"

            await msg.edit_text(txt)

        elif "horarios" in t:

            prog = data["programacion"]

            if not prog:
                await msg.edit_text(
                    "📌 Ejemplo:\n"
                    "lunes,viernes 5pm\n"
                    "lunes 9am,2pm,8pm"
                )
            else:
                txt = "⏰ HORARIOS:\n\n"

                for i, p in enumerate(prog, 1):
                    estado = "🟢" if p.get("activo", True) else "🔴"
                    txt += f"{i}. {', '.join(p['dias'])}\n"
                    txt += f"   🕒 {', '.join(p['horas'])} {estado}\n\n"

                await msg.edit_text(txt)

        elif t.startswith(".panel"):

            await msg.edit_text(
                "📘 PANEL\n\n"
                "Agregar horario:\nlunes 5pm\n"
                "Ver horarios: horarios\n"
                "Ver activos: activos\n"
                "Eliminar: del:1\n"
                "Pausar: off:1\n"
                "Activar: on:1"
            )

        elif t.startswith("del:"):
            i = int(t.replace("del:", "")) - 1
            data["programacion"].pop(i)
            guardar()
            await msg.edit_text("🗑 Eliminado")

        elif t.startswith("off:"):
            i = int(t.replace("off:", "")) - 1
            data["programacion"][i]["activo"] = False
            guardar()
            await msg.edit_text("🔴 Pausado")

        elif t.startswith("on:"):
            i = int(t.replace("on:", "")) - 1
            data["programacion"][i]["activo"] = True
            guardar()
            await msg.edit_text("🟢 Activado")

        elif any(d in t for d in dias_validos):

            match = re.match(r"(.+?)\s+(.+)$", t)

            dias_txt = match.group(1)
            horas_txt = match.group(2)

            dias = dias_txt.split(",")
            horas_lista = horas_txt.split(",")

            dias_final = []
            for d in dias:
                c = corregir_dia(d.strip())
                if c:
                    dias_final.append(c)

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
            await msg.edit_text("✅ Programado")

        else:
            await msg.edit_text("❌ No válido")

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("⚠️ Error")

# -------- run --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, texto))
app.add_handler(CallbackQueryHandler(botones))

print("🔥 BOT ULTRA PRO")
app.run_polling()

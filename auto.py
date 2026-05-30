import json, asyncio
from datetime import datetime
from telegram import Bot
import pytz

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

bot = Bot(token=TOKEN)
tz = pytz.timezone("America/Lima")

ejecutados = set()

dias_map = {
    "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
    "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
}

async def main():
    print("🔥 AUTO PRO CORRIENDO")

    while True:
        try:
            now = datetime.now(tz)

            dia_en = now.strftime("%A").lower()
            dia_actual = dias_map.get(dia_en, dia_en)

            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)

            contenido = data.get("contenido")
            if not contenido:
                await asyncio.sleep(2)
                continue

            for evento in data.get("eventos", []):

                if not evento.get("activo", True):
                    continue

                # EVENTO NORMAL
                if evento.get("fecha"):
                    dt_evento = datetime.strptime(
                        f"{evento['fecha']} {evento['hora']}",
                        "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=tz)

                    clave = f"{evento['fecha']}_{evento['hora']}"

                # EVENTO REPETITIVO
                elif evento.get("tipo") == "repetitivo":

                    if evento["dia"] != dia_actual:
                        continue

                    dt_evento = datetime.strptime(
                        evento["hora"],
                        "%H:%M"
                    ).replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=tz
                    )

                    clave = f"{evento['dia']}_{evento['hora']}_{now.strftime('%Y-%m-%d')}"

                else:
                    continue

                diferencia = abs((now - dt_evento).total_seconds())

                if diferencia <= 60 and clave not in ejecutados:

                    for canal in data.get("canales", []):
                        try:
                            await bot.copy_message(
                                chat_id=canal,
                                from_chat_id=contenido["chat_id"],
                                message_id=contenido["message_id"]
                            )
                            print("✅ enviado a", canal)

                        except Exception as e:
                            print("❌ error:", e)

                    ejecutados.add(clave)

        except Exception as e:
            print("❌ ERROR:", e)

        await asyncio.sleep(2)

asyncio.run(main())

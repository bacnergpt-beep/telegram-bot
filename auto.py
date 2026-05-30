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
    print("🔥 AUTO FUNCIONANDO")

    while True:
        try:
            now = datetime.now(tz)

            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)

            contenido = data.get("contenido")
            if not contenido:
                await asyncio.sleep(2)
                continue

            dia_en = now.strftime("%A").lower()
            dia_actual = dias_map.get(dia_en, dia_en)

            for prog in data.get("programacion", []):

                if not prog.get("activo", True):
                    continue

                if dia_actual not in prog["dias"]:
                    continue

                for hora in prog["horas"]:

                    dt = datetime.strptime(hora, "%H:%M").replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=tz
                    )

                    diff = abs((now - dt).total_seconds())

                    clave = f"{dia_actual}_{hora}_{now.strftime('%Y-%m-%d')}"

                    if diff <= 60 and clave not in ejecutados:

                        for canal in data.get("canales", []):
                            await bot.copy_message(
                                chat_id=canal,
                                from_chat_id=contenido["chat_id"],
                                message_id=contenido["message_id"]
                            )
                            print("✅ enviado:", canal)

                        ejecutados.add(clave)

        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(2)

asyncio.run(main())

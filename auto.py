import json, asyncio
from datetime import datetime
from telegram import Bot
import pytz

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = "config_data.json"

bot = Bot(token=TOKEN)
tz = pytz.timezone("America/Lima")

# evitar duplicados
ultimo_envio = {}

async def main():
    print("🔥 AUTO FUNCIONANDO BIEN")

    while True:
        try:
            now = datetime.now(tz)

            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)

            contenidos = data.get("contenido", [])
            if not contenidos:
                await asyncio.sleep(5)
                continue

            dias_map = {
                "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
                "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
            }

            dia_actual = dias_map[now.strftime("%A").lower()]

            for prog in data.get("programacion", []):

                if not prog.get("activo", True):
                    continue

                if dia_actual not in prog["dias"]:
                    continue

                for hora in prog["horas"]:

                    # hora objetivo
                    dt = datetime.strptime(hora, "%H:%M").replace(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                        tzinfo=tz
                    )

                    diferencia = (now - dt).total_seconds()

                    # 🔥 ventana de 5 minutos
                    if 0 <= diferencia <= 300:

                        clave = f"{dia_actual}-{hora}"

                        # evitar repetir
                        if ultimo_envio.get(clave) == now.date():
                            continue

                        for msg in contenidos:
                            for canal in data.get("canales", []):
                                await bot.copy_message(
                                    chat_id=canal,
                                    from_chat_id=msg["chat_id"],
                                    message_id=msg["message_id"]
                                )

                        print(f"✅ enviado {hora}")

                        ultimo_envio[clave] = now.date()

        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(10)

asyncio.run(main())

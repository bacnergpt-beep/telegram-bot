import json, asyncio
from datetime import datetime
from telegram import Bot

TOKEN = "8711981791:AAHJ3hSl0lLWAffHRJu5AOZzMBiTAD4f2BY"
CONFIG_PATH = r"C:\Users\BACNER\Desktop\config_data.json"

bot = Bot(token=TOKEN)
ultima = None

dias_map = {
    "monday": "lunes",
    "tuesday": "martes",
    "wednesday": "miercoles",
    "thursday": "jueves",
    "friday": "viernes",
    "saturday": "sabado",
    "sunday": "domingo"
}

async def main():
    global ultima
    print("AUTO PRO FUNCIONANDO 🔥")

    while True:
        try:
            now = datetime.now()
            hora = now.strftime("%H:%M")

            dia_en = now.strftime("%A").lower()
            dia_actual = dias_map.get(dia_en, dia_en)

            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)

            contenido = data.get("contenido")
            if not contenido:
                await asyncio.sleep(2)
                continue

            for h in data.get("horas", []):
                # compatibilidad (por si algo quedó viejo)
                if isinstance(h, dict):
                    hora_conf = h.get("hora")
                    activo = h.get("activo", True)
                else:
                    hora_conf = h
                    activo = True

                if not hora_conf:
                    continue

                if activo and hora_conf == hora and hora != ultima:

                    # validar días
                    dias = data.get("dias", [])
                    if not dias or dia_actual in dias:

                        for canal in data.get("canales", []):
                            try:
                                if contenido.get("tipo") == "copy":
                                    await bot.copy_message(
                                        chat_id=canal,
                                        from_chat_id=contenido.get("chat_id"),
                                        message_id=contenido.get("message_id")
                                    )
                                else:
                                    # fallback simple
                                    await bot.send_message(
                                        chat_id=canal,
                                        text="Contenido no válido"
                                    )

                                print("✅ enviado a", canal)

                            except Exception as e:
                                print("❌ error:", e)

                        ultima = hora

        except Exception as e:
            print("❌ ERROR:", e)

        await asyncio.sleep(2)

asyncio.run(main())

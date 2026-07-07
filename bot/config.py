import os

# Token endi kodda ochiq yozilmaydi — muhit o'zgaruvchisidan o'qiladi.
# Render'da: Environment bo'limiga BOT_TOKEN nomi bilan qo'shasiz.
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError(
        "BOT_TOKEN topilmadi! Muhit o'zgaruvchisiga tokenni belgilang."
    )

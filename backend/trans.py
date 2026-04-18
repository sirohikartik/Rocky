# trans.py
import asyncio
from googletrans import Translator

async def translate_all(words):
    translator = Translator()
    tasks = [translator.translate(w, src='hi', dest='en') for w in words]
    results = await asyncio.gather(*tasks)
    return [r.text for r in results]

async def translate_sentence(text):
    translator = Translator()
    result = await translator.translate(text, src='hi', dest='en')  # ✅ await here
    return result.text

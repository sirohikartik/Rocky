import asyncio
from googletrans import Translator

async def translate_all(words):
    translator = Translator()
    tasks = [translator.translate(w, src='hi', dest='en') for w in words]
    results = await asyncio.gather(*tasks)
    return [r.text for r in results]




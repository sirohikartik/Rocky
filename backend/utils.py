# utils.py
from trans import translate_all

def get_soul(soul_path: str) -> str:
    with open(soul_path, "r", encoding="utf-8") as f:
        return f.read()


async def build_prompt(sentence: str, vocab: list[str], soul_path: str, lang: str = "eng") -> str:
    soul = get_soul(soul_path)

    if lang == "hi":
        translated = (await translate_all([sentence]))[0]
    else:
        translated = sentence

    prompt = f"""
{soul}

--- INPUT SENTENCE ---
Original ({lang}): {sentence}
Translated (en): {translated}

--- AVAILABLE VOCAB ---
You MUST only use words from this list:
{", ".join(vocab)}

--- TASK ---
Using ONLY the given vocabulary, generate a grammatically correct ISL sentence.
Do NOT introduce new words.
Do NOT explain anything.
Only output the final ISL word sequence.
"""
    return prompt

from fastapi import FastAPI
from pydantic import BaseModel
import ollama
import json
import re

from utils import build_prompt  

app = FastAPI()

class Input(BaseModel):
    sentence: str
    lang: str


def extract_json(text: str):
    text = text.strip()

    # remove markdown ```json ... ```
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```", "", text)

    # extract first {...} block (safety)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in output")

    json_str = match.group(0)

    return json.loads(json_str)


@app.post("/go")
async def go(s: Input):
    vocab = ["ME", "WATER", "WANT", "YOU", "HELP"]

    prompt = await build_prompt(
        sentence=s.sentence,
        vocab=vocab,
        soul_path="soul.md",
        lang=s.lang
    )

    response = ollama.chat(
        model="gemma3:27b-cloud",
        messages=[
            {
                "role": "system",
                "content": "You are an ISL generator. Follow all rules strictly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw_output = response["message"]["content"]

    try:
        parsed = extract_json(raw_output)
    except Exception as e:
        parsed = {"isl_sentence": [], "error": str(e), "raw": raw_output}

    return {
        "input": s.sentence,
        "output": parsed
    }

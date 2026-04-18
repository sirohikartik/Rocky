import re
from fastapi import FastAPI
from pydantic import BaseModel
import ollama

from utils import build_prompt
from lookup import EmbeddingEngine, EmbeddingModel
from trans import translate_sentence  # NEW

app = FastAPI()

# -------- INPUT --------
class Input(BaseModel):
    sentence: str
    lang: str


# -------- STOPWORDS --------
STOPWORDS = {
    "is", "am", "are", "was", "were",
    "the", "a", "an",
    "to", "of", "and", "in", "on", "at"
}


# -------- JSON CLEANER --------
import json
def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")

    return json.loads(match.group(0))


# -------- WORD RESOLVER --------
def resolve_words(words, engine, model):
    resolved = []

    for w in words:
        # skip stopwords
        if w in STOPWORDS:
            continue

        # exact match
        result = engine.lookup(w)
        if result:
            resolved.append(result["word"].upper())
            continue

        # similarity fallback
        vec = model.encode(w)
        sims = engine.find_similar(vec, top_k=1)

        if sims:
            resolved.append(sims[0]["word"].upper())

    return list(set(resolved))


# -------- ROTATION FETCH --------
def words_to_rotations(words, engine):
    rotations = []

    for w in words:
        idx = engine.word_to_index.get(w.lower())
        if idx is None:
            continue

        rotations.append(engine.rotations[idx])

    return rotations


# -------- LOAD ONCE (IMPORTANT) --------
engine = EmbeddingEngine("updated_file.csv")
model = EmbeddingModel()


# -------- MAIN ENDPOINT --------
@app.post("/main")
async def main(s: Input):

    # 1. translate FULL sentence if Hindi
    if s.lang == "hi":
        translated_sentence = await translate_sentence(s.sentence)
    else:
        translated_sentence = s.sentence

    # 2. tokenize
    words = re.findall(r"\w+", translated_sentence)

    # 3. normalize
    words = [w.lower() for w in words]

    # 4. resolve vocab
    vocab = resolve_words(words, engine, model)

    if not vocab:
        return {"error": "No valid vocab generated"}

    # 5. build prompt
    prompt = await build_prompt(
        sentence=translated_sentence,
        vocab=vocab,
        soul_path="soul.md",
        lang="en"
    )

    # 6. LLM call
    response = ollama.chat(
        model="gemma3:27b-cloud",
        messages=[
            {"role": "system", "content": "You are an ISL generator. Follow rules strictly."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_output = response["message"]["content"]

    try:
        parsed = extract_json(raw_output)
        isl_words = parsed.get("isl_sentence", [])
    except Exception as e:
        return {
            "error": "LLM parsing failed",
            "raw": raw_output,
            "details": str(e)
        }

    # 7. map to rotations
    isl_words = [i.lower() for i in isl_words]
    rotations = words_to_rotations(isl_words, engine)

    return {
        "input": s.sentence,
        "translated_sentence": translated_sentence,
        "resolved_vocab": vocab,
        "isl_words": isl_words,
        "rotations": rotations
    }

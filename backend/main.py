import re
import os
import json
import uuid
import asyncio
import logging
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama

# New MoviePy 2.0+ import style
from moviepy import VideoFileClip, concatenate_videoclips

from utils import build_prompt
from lookup import EmbeddingEngine, EmbeddingModel
from trans import translate_sentence

# --- LOGGING CONFIGURATION ---
# Fixed: logging.StreamHandler() instead of StreamFormatter()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ISL_Backend")

app = FastAPI()

# --- CORS CONFIG ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
VIDEO_ROOT = "isl_one_per_class"

# --- INPUT MODEL ---
class Input(BaseModel):
    sentence: str
    lang: str

# --- STOPWORDS ---
STOPWORDS = {
    "is", "am", "are", "was", "were",
    "the", "a", "an",
    "to", "of", "and", "in", "on", "at"
}

# --- HELPERS ---

def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in LLM response")
    return json.loads(match.group(0))

def resolve_words(words, engine, model):
    resolved = []
    seen = set()
    logger.info(f"🔍 Checking dictionary for words: {words}")

    for w in words:
        if w in STOPWORDS:
            continue

        result = engine.lookup(w)
        word_found = None
        
        if result:
            word_found = result["word"].upper()
            logger.info(f"✅ Exact match found: {w} -> {word_found}")
        else:
            vec = model.encode(w)
            sims = engine.find_similar(vec, top_k=1)
            if sims:
                word_found = sims[0]["word"].upper()
                logger.info(f"🔸 No exact match for '{w}'. Closest similarity: {word_found}")

        if word_found and word_found not in seen:
            resolved.append(word_found)
            seen.add(word_found)

    return resolved

def merge_videos(words):
    clips = []
    output_path = f"temp_{uuid.uuid4().hex}.mp4"
    logger.info(f"🎬 Merging sequence: {words}")

    try:
        for w in words:
            folder = os.path.join(VIDEO_ROOT, w)
            if not os.path.exists(folder):
                logger.warning(f"⚠️ Missing signs for: {w}")
                continue

            files = [f for f in os.listdir(folder) if f.lower().endswith((".mov", ".mp4"))]
            if not files:
                continue

            path = os.path.join(folder, files[0])
            logger.info(f"🎥 Attaching clip: {path}")
            clip = VideoFileClip(path)
            clips.append(clip)

        if not clips:
            logger.error("🛑 No clips found to merge.")
            return None

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio=False,
            fps=24,
            logger=None 
        )
        return output_path

    except Exception as e:
        logger.error(f"🚨 Video Error: {e}")
        return None
    finally:
        for clip in clips:
            try:
                clip.close()
            except:
                pass

# --- LOAD MODELS ---
logger.info("⚙️ Initializing EmbeddingEngine & BERT Model...")
engine = EmbeddingEngine("updated_file.csv")
model = EmbeddingModel()
logger.info("🚀 All systems online. Ready for Whisper input.")

# --- MAIN ENDPOINT ---

@app.post("/main")
async def main(s: Input, background_tasks: BackgroundTasks):
    request_id = uuid.uuid4().hex[:6]
    logger.info(f"--- [NEW REQUEST {request_id}] ---")
    logger.info(f"🎤 Input: '{s.sentence}' | Lang: {s.lang}")

    # 1. Translation Layer
    if s.lang == "hi":
        logger.info("🇮🇳 Translating from Hindi...")
        translated_sentence = await translate_sentence(s.sentence)
        logger.info(f"✨ Translated Text: {translated_sentence}")
    else:
        translated_sentence = s.sentence

    # 2. Tokenization
    words = re.findall(r"\w+", translated_sentence.lower())

    # 3. Resolve vocab
    vocab = resolve_words(words, engine, model)
    if not vocab:
        return {"error": "No valid ISL vocab found"}

    # 4. Prompt Construction
    prompt = await build_prompt(
        sentence=translated_sentence,
        vocab=vocab,
        soul_path="soul.md",
        lang="en"
    )

    # 5. Async LLM Call
    try:
        logger.info("🧠 Requesting ISL Grammar from LLM...")
        client = ollama.AsyncClient()
        response = await client.chat(
            model="gemma3:27b-cloud",
            messages=[
                {"role": "system", "content": "You are an ISL generator. Follow rules strictly."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_output = response["message"]["content"]
    except Exception as e:
        logger.error(f"❌ Ollama link broken: {e}")
        return {"error": "Ollama connection failed", "details": str(e)}

    # 6. Parse LLM output
    try:
        parsed = extract_json(raw_output)
        isl_words = parsed.get("isl_sentence", [])
        logger.info(f"🎯 Final Sign Order: {isl_words}")
    except Exception as e:
        logger.error(f"❌ Failed to parse LLM JSON: {raw_output}")
        return {"error": "LLM parsing failed", "details": str(e)}

    isl_words_lower = [w.lower() for w in isl_words]

    # 7. Video Merging
    merged_video_path = await asyncio.to_thread(merge_videos, isl_words_lower)

    if not merged_video_path or not os.path.exists(merged_video_path):
        return {"error": "Video generation failed"}

    # 8. Return file and delete after sending
    background_tasks.add_task(os.remove, merged_video_path)
    logger.info(f"--- [COMPLETED {request_id}] ---")
    
    return FileResponse(
        merged_video_path,
        media_type="video/mp4",
        filename="isl_output.mp4"
    )

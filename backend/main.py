import re
import os
import json
import uuid
import asyncio
import logging
import subprocess
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
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:5173",
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
STOPWORDS = {"is", "am", "are", "was", "were", "the", "a", "an", "to", "of", "and", "in", "on", "at"}

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
        if w in STOPWORDS: continue
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
                logger.info(f"🔸 Similarity match: {w} -> {word_found}")
        if word_found and word_found not in seen:
            resolved.append(word_found)
            seen.add(word_found)
    return resolved

def get_rotations_for_sequence(words, engine):
    """
    Helper to fetch the numerical rotation data/frames 
    for the 3D avatar from the loaded engine.
    """
    all_rotations = []
    logger.info(f"🔄 Fetching rotation frames for: {words}")
    
    for w in words:
        result = engine.lookup(w.lower())
        if result and "rotations" in result and result["rotations"]:
            all_rotations.extend(result["rotations"])
        else:
            logger.warning(f"⚠️ No rotation data found for: {w}")
            
    return all_rotations

def merge_videos(words):
    clips = []
    output_path = f"temp_{uuid.uuid4().hex}.mp4"
    try:
        for w in words:
            folder = os.path.join(VIDEO_ROOT, w)
            if not os.path.exists(folder): continue
            files = [f for f in os.listdir(folder) if f.lower().endswith((".mov", ".mp4"))]
            if not files: continue
            path = os.path.join(folder, files[0])
            clips.append(VideoFileClip(path))
        if not clips: return None
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output_path, codec="libx264", audio=False, fps=24, logger=None)
        return output_path
    except Exception as e:
        logger.error(f"🚨 Video Error: {e}")
        return None
    finally:
        for clip in clips:
            try: clip.close()
            except: pass

# --- LOAD MODELS ---
engine = EmbeddingEngine("updated_file.csv")
model = EmbeddingModel()

# --- ENDPOINTS ---

@app.post("/rotation")
async def rotation_endpoint(s: Input):
    """
    Processes speech/text and returns the raw 3D rotation 
    data for the MediaPipe/Avatar frontend.
    """
    request_id = uuid.uuid4().hex[:6]
    logger.info(f"--- [ROTATION REQUEST {request_id}] ---")
    
    # 1. Translation
    translated_sentence = await translate_sentence(s.sentence) if s.lang == "hi" else s.sentence

    # 2. Tokenization & Resolution
    words = re.findall(r"\w+", translated_sentence.lower())
    vocab = resolve_words(words, engine, model)
    if not vocab: return {"error": "No valid ISL vocab found"}

    # 3. LLM Processing
    prompt = await build_prompt(sentence=translated_sentence, vocab=vocab, soul_path="soul.md", lang="en")
    
    try:
        client = ollama.AsyncClient()
        response = await client.chat(
            model="gemma3:27b-cloud",
            messages=[
                {"role": "system", "content": "You are an ISL generator. Return JSON with 'isl_sentence' key."},
                {"role": "user", "content": prompt}
            ]
        )
        parsed = extract_json(response["message"]["content"])
        isl_words = parsed.get("isl_sentence", [])
    except Exception as e:
        logger.error(f"❌ LLM/Parsing Error: {e}")
        return {"error": "Processing failed"}

    # 4. Get Rotations
    rotations = get_rotations_for_sequence(isl_words, engine)
    
    logger.info(f"--- [COMPLETED ROTATION {request_id}] ---")
    return {
        "isl_sentence": isl_words,
        "rotations": rotations
    }

@app.post("/main")
async def main_endpoint(s: Input, background_tasks: BackgroundTasks):
    """
    Returns the stitched MP4 video file.
    """
    request_id = uuid.uuid4().hex[:6]
    logger.info(f"--- [VIDEO REQUEST {request_id}] ---")
    
    translated_sentence = await translate_sentence(s.sentence) if s.lang == "hi" else s.sentence
    words = re.findall(r"\w+", translated_sentence.lower())
    vocab = resolve_words(words, engine, model)
    if not vocab: return {"error": "No valid ISL vocab found"}

    prompt = await build_prompt(sentence=translated_sentence, vocab=vocab, soul_path="soul.md", lang="en")
    
    try:
        client = ollama.AsyncClient()
        response = await client.chat(
            model="gemma3:27b-cloud",
            messages=[{"role": "system", "content": "You are an ISL generator."}, {"role": "user", "content": prompt}]
        )
        parsed = extract_json(response["message"]["content"])
        isl_words = [w.lower() for w in parsed.get("isl_sentence", [])]
    except Exception as e:
        return {"error": "Processing failed"}

    merged_video_path = await asyncio.to_thread(merge_videos, isl_words)
    if not merged_video_path: return {"error": "Video generation failed"}

    temp_json_path = merged_video_path.replace(".mp4", "_rotations.json")
    solver_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend_solver.cjs"))
    
    try:
        # Spawn the node solver dynamically on the fused video
        logger.info(f"--- [SPAWNING SOLVER: {solver_script}] ---")
        await asyncio.to_thread(
            subprocess.run,
            ["node", solver_script, merged_video_path, temp_json_path],
            check=True
        )
        
        # Ingest the generated keyframes JSON array
        with open(temp_json_path, "r") as f:
            rotations = json.load(f)
            
    except Exception as e:
        logger.error(f"Solver script execution failed: {e}")
        rotations = []
        
    finally:
        # Aggressively delete temporary heavy pipeline files
        try:
            if os.path.exists(merged_video_path):
                os.remove(merged_video_path)
            if os.path.exists(temp_json_path):
                os.remove(temp_json_path)
        except Exception:
            pass

    logger.info(f"--- [COMPLETED DYNAMIC VIDEO SOLVING {request_id}] ---")
    return {
        "isl_sentence": isl_words,
        "rotations": rotations
    }

import pandas as pd
import json

# ---- PATHS ----
CSV_PATH = r"D:\hack helix\ISL_dataset\isl_word_embeddings.csv"
JSON_PATH = r"D:\hack helix\ISL_dataset\isl_rig_v2_final_all76.json"
OUTPUT_PATH = r"D:\hack helix\ISL_dataset\updated_file.csv"

# ---- LOAD ----
df = pd.read_csv(CSV_PATH)

with open(JSON_PATH, "r") as f:
    rotations_data = json.load(f)

# ---- OPTIONAL: normalize keys (VERY IMPORTANT) ----
rotations_data = {k.lower(): v for k, v in rotations_data.items()}
df["word"] = df["word"].str.lower()

# ---- MAP FUNCTION ----
def get_rotation(word):
    return json.dumps(rotations_data.get(word, None))

# ---- APPLY ----
df["rotations"] = df["word"].apply(get_rotation)

# ---- SAVE ----
df.to_csv(OUTPUT_PATH, index=False)

print("✅ Rotations mapped correctly!")
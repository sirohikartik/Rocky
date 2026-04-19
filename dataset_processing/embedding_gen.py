import os
import pandas as pd
import json
import zipfile
from sentence_transformers import SentenceTransformer

def generate_isl_word_embeddings(root_dir, output_folder, output_filename):
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    words_set = set()
    
    # 1. Iterate over all zip files in the root_dir
    if not os.path.exists(root_dir):
        print(f"Directory {root_dir} does not exist.")
        return
        
    zip_files = [f for f in os.listdir(root_dir) if f.endswith('.zip')]
    if not zip_files:
        print(f"No zip files found in {root_dir}.")
        return

    print(f"Found {len(zip_files)} zip files. Extracting word folder names...")

    for zip_filename in zip_files:
        zip_path = os.path.join(root_dir, zip_filename)
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # We expect structures like TopLevel/WordFolder/
                for name in z.namelist():
                    if name.endswith('/'):
                        parts = name.strip('/').split('/')
                        if len(parts) == 2:
                            # parts[0] is TopLevel (e.g., 'Adjectives')
                            # parts[1] is WordFolder (e.g., '1. loud')
                            words_set.add(parts[1])
        except zipfile.BadZipFile:
            print(f"Skipping invalid or incomplete zip file: {zip_filename}")

    folder_names = sorted(list(words_set))
    
    if not folder_names:
        print("No word folders found inside the zip files.")
        return

    # 2. Setup output paths and read existing data
    os.makedirs(output_folder, exist_ok=True)
    output_csv = os.path.join(output_folder, output_filename)

    processed_words = set()
    start_id = 1000
    
    if os.path.exists(output_csv):
        try:
            existing_df = pd.read_csv(output_csv)
            if not existing_df.empty and 'word' in existing_df.columns:
                processed_words = set(existing_df['word'].astype(str).tolist())
            if not existing_df.empty and 'word_id' in existing_df.columns:
                start_id = int(existing_df['word_id'].max()) + 1
        except Exception as e:
            print(f"Could not read existing CSV: {e}")

    # Filter out already processed words
    folder_names = [w for w in folder_names if w not in processed_words]

    if not folder_names:
        print("All words have already been processed.")
        return

    print(f"Found {len(folder_names)} new classes/words to process. Generating embeddings...")

    data = []
    for index, word in enumerate(folder_names):
        # Generate the vector embedding
        embedding = model.encode(word).tolist()
        
        data.append({
            'word_id': start_id + index,
            'word': word,
            'vector_embedding': json.dumps(embedding)
        })
        
        if (index + 1) % 10 == 0:
            print(f"Processed {index + 1}/{len(folder_names)} new words...")

    # 3. Save to a single CSV file (append if it exists)
    df = pd.DataFrame(data)
    if os.path.exists(output_csv):
        df.to_csv(output_csv, mode='a', header=False, index=False)
    else:
        df.to_csv(output_csv, index=False)
        
    print(f"\nSuccess! Added {len(df)} entries to {output_csv}.")

# --- USAGE ---
# Provide the absolute path or relative path to ISL_dataset
root_path = r'd:\hack helix\ISL_dataset' 
output_folder = 'generated_csv'
output_filename = 'isl_word_embeddings.csv'
generate_isl_word_embeddings(root_path, output_folder, output_filename)
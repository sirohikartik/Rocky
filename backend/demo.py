import csv
import json

INPUT_FILE = "isl_word_embeddings.csv"
OUTPUT_FILE = "isl_word_embeddings_with_rotations.csv"


# simple dummy rotation generator
def generate_dummy_rotations():
    return [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6]
    ]


def main():
    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # ensure column exists
        if "bone_rotations" not in fieldnames:
            fieldnames.append("bone_rotations")

        for row in reader:
            # assign dummy rotation JSON
            row["bone_rotations"] = json.dumps(generate_dummy_rotations())
            rows.append(row)

    # write new CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Done! New file: {OUTPUT_FILE}")


import csv

def get_words_from_csv(csv_path):
    words = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            word = row["word"].strip()
            words.append(word)

    return words

if __name__ == "__main__":
    print(get_words_from_csv("isl_word_embeddings_with_rotations.csv"))

import requests

URL = "http://127.0.0.1:8000/main"

test_cases = [
    # ---------------- OLD TESTS ----------------

    # Hinglish (5)
    {"sentence": "आज weather good", "lang": "hi"},
    {"sentence": "कल night cold", "lang": "hi"},
    {"sentence": "आज morning hot", "lang": "hi"},
    {"sentence": "कल dog loud", "lang": "hi"},
    {"sentence": "आज shirt new", "lang": "hi"},

    # English (3)
    {"sentence": "today dog big", "lang": "en"},
    {"sentence": "tomorrow night cold", "lang": "en"},
    {"sentence": "morning bird fast", "lang": "en"},

    # Pure Hindi (2)
    {"sentence": "आज अच्छा", "lang": "hi"},
    {"sentence": "कल ठंडा", "lang": "hi"},


    # ---------------- NEW BETTER TESTS ----------------

    # Hinglish (5)
    {"sentence": "आज morning weather hot", "lang": "hi"},
    {"sentence": "कल night dog loud", "lang": "hi"},
    {"sentence": "आज shirt new good", "lang": "hi"},
    {"sentence": "कल weather cold", "lang": "hi"},
    {"sentence": "आज bird fast", "lang": "hi"},

    # English (3)
    {"sentence": "today morning weather hot", "lang": "en"},
    {"sentence": "tomorrow night dog loud", "lang": "en"},
    {"sentence": "yesterday weather cold", "lang": "en"},

    # Pure Hindi (2)
    {"sentence": "आज मौसम गर्म", "lang": "hi"},
    {"sentence": "कल मौसम ठंडा", "lang": "hi"},


    # ---------------- FUTURE-READY (WITH VERBS ETC.) ----------------
    # These may partially fail NOW but useful once vocab expands

    {"sentence": "I want water today", "lang": "en"},
    {"sentence": "मैं पानी चाहता हूँ", "lang": "hi"},
    {"sentence": "you drink water tomorrow", "lang": "en"},
    {"sentence": "कल मैं दूध खरीद", "lang": "hi"},
]


def run_tests():
    print("🚀 Running ISL Pipeline Tests\n")

    for i, test in enumerate(test_cases, 1):
        print(f"--- Test {i} ---")
        print("Input:", test["sentence"])

        try:
            res = requests.post(URL, json=test)
            data = res.json()

            print("Translated:", data.get("translated_sentence"))
            print("Vocab:", data.get("resolved_vocab"))
            print("ISL:", data.get("isl_words"))
            print("Rotations count:", len(data.get("rotations", [])))

        except Exception as e:
            print("❌ Error:", e)

        print("\n")


if __name__ == "__main__":
    run_tests()

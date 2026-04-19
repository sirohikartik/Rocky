import yt_dlp
import os
import glob
from moviepy import VideoFileClip

# --- 1. CONFIGURATION ---
# Add your Numbers URL where indicated below
video_configs = [
    {
        "name": "alphabets",
        "url": "https://www.youtube.com/watch?v=qcdivQfA41Y",
        "segments": [
            ("02:10", "02:14", "A"), ("02:14", "02:18", "B"), ("02:18", "02:23", "C"),

    ("02:23", "02:27", "D"), ("02:27", "02:35", "E"), ("02:35", "02:40", "F"), ("02:58", "03:01", "G"), ("03:01", "03:09", "H"),

    ("03:09", "03:12", "I"), ("03:19", "03:21", "J"), ("03:31", "03:35", "K"),

    ("03:43", "03:47", "L"), ("04:03", "04:06", "M"), ("04:06", "04:10", "N"),

    ("04:10", "04:14", "O"), ("04:14", "04:17", "P"), ("04:17", "04:20", "Q"),

    ("04:25", "04:28", "R"), ("04:31", "04:34", "S"), ("04:42", "04:45", "T"),

    ("04:51", "04:55", "U"), ("04:55", "04:59", "V"), ("04:59", "05:04", "W"),

    ("05:04", "05:07", "X"), ("05:07", "05:10", "Y"), ("05:19", "05:22", "Z")
        ]
    },
    {
        "name": "numbers",
        "url": "https://www.youtube.com/watch?v=vnH2BmcSRMA",  # <--- PASTE YOUR NUMBERS YOUTUBE URL HERE
        "segments": [
            ("00:31", "00:35", "1"), ("00:35", "00:38", "2"), ("00:38", "00:42", "3"),
            ("00:42", "00:45", "4"), ("00:45", "00:54", "5"), ("00:54", "01:00", "6"),
            ("01:00", "01:05", "7"), ("01:05", "01:07", "8"), ("01:07", "01:10", "9"),
            ("01:10", "01:15", "10")
        ]
    }
]

DOWNLOAD_DIR = './raw_downloads'
BASE_DATASET_DIR = './dataset'

# --- 2. HELPERS ---
def to_sec(time_str):
    """Converts 'min:sec' to total seconds float."""
    try:
        m, s = time_str.split(':')
        return int(m) * 60 + float(s)
    except ValueError:
        return float(time_str)

def download_video(url, name):
    """Downloads video using yt-dlp and returns the path."""
    out_path = os.path.join(DOWNLOAD_DIR, f"{name}_raw.mp4")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': out_path,
        'overwrites': True,
        'quiet': True
    }
    print(f"Downloading {name} video...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return out_path

# --- 3. MAIN LOOP ---
if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    for config in video_configs:
        if "INSERT" in config["url"] or not config["url"]:
            print(f"\n[!] Skipping {config['name']}: No URL provided.")
            continue

        print(f"\n=== STARTING {config['name'].upper()} PROCESS ===")
        
        try:
            raw_video = download_video(config["url"], config["name"])
        except Exception as e:
            print(f"Download failed: {e}")
            continue

        # Open the video once for all segments in this config
        with VideoFileClip(raw_video) as video:
            for start_str, end_str, label in config["segments"]:
                output_dir = os.path.join(BASE_DATASET_DIR, label)
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"{label}_1.mp4")

                start_s = to_sec(start_str)
                end_s = to_sec(end_str)

                print(f"  > Processing {label} ({start_str} to {end_str})...")
                
                try:
                    # In MoviePy 2.x, 'subclip' is 'subclipped'
                    clip = video.subclipped(start_s, end_s)
                    
                    # Re-encoding ensures playability and keyframe alignment
                    clip.write_videofile(
                        output_file, 
                        codec="libx264", 
                        audio_codec="aac",
                        temp_audiofile=os.path.join(DOWNLOAD_DIR, 'temp-audio.m4a'),
                        remove_temp=True,
                        logger=None # Set to 'bar' if you want to see progress
                    )
                except Exception as e:
                    print(f"    Error clipping {label}: {e}")

    print("\n[SUCCESS] All clips extracted and re-encoded for MediaPipe.")
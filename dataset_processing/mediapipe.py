import cv2
import mediapipe as mp
import json
import numpy as np

# --- 1. YOUR BONE MAPPING ---
BONE_MAPPING = {
    "mediapipe_face_landmarks": {
    "_note": "refineFaceLandmarks:true required for 468 landmarks",
    "jaw_open":        { "landmarks": [13, 14], "bones": ["jaw", "chin", "chin.001"] },
    "lip_top_left":    { "landmarks": [61, 78], "bones": ["lip.T.L", "lip.T.L.001"] },
    "lip_bottom_left": { "landmarks": [84, 95], "bones": ["lip.B.L", "lip.B.L.001"] },
    "lip_top_right":   { "landmarks": [291, 308], "bones": ["lip.T.R", "lip.T.R.001"] },
    "lip_bottom_right":{ "landmarks": [314, 324], "bones": ["lip.B.R", "lip.B.R.001"] },
    "left_eye_top_lid":   { "landmarks": [159, 160, 161], "bones": ["lid.T.L", "lid.T.L.001", "lid.T.L.002", "lid.T.L.003"] },
    "left_eye_bottom_lid":{ "landmarks": [145, 144, 163], "bones": ["lid.B.L", "lid.B.L.001", "lid.B.L.002", "lid.B.L.003"] },
    "right_eye_top_lid":  { "landmarks": [386, 385, 384], "bones": ["lid.T.R", "lid.T.R.001", "lid.T.R.002", "lid.T.R.003"] },
    "right_eye_bottom_lid":{"landmarks": [374, 373, 380], "bones": ["lid.B.R", "lid.B.R.001", "lid.B.R.002", "lid.B.R.003"] },
    "left_eye_center":    { "landmarks": [468], "bones": ["eye.L"] },
    "right_eye_center":   { "landmarks": [473], "bones": ["eye.R"] },
    "left_brow_bottom":   { "landmarks": [46, 52, 53, 55], "bones": ["brow.B.L", "brow.B.L.001", "brow.B.L.002", "brow.B.L.003"] },
    "left_brow_top":      { "landmarks": [65, 66, 70, 107], "bones": ["brow.T.L", "brow.T.L.001", "brow.T.L.002", "brow.T.L.003"] },
    "right_brow_bottom":  { "landmarks": [276, 282, 283, 285], "bones": ["brow.B.R", "brow.B.R.001", "brow.B.R.002", "brow.B.R.003"] },
    "right_brow_top":     { "landmarks": [295, 296, 300, 334], "bones": ["brow.T.R", "brow.T.R.001", "brow.T.R.002", "brow.T.R.003"] },
    "nose_tip":           { "landmarks": [1, 2, 5], "bones": ["nose", "nose.001", "nose.002"] },
    "nose_bridge":        { "landmarks": [6, 168, 197], "bones": ["nose.003", "nose.004"] },
    "nose_left_ala":      { "landmarks": [64, 98, 115], "bones": ["nose.L", "nose.L.001"] },
    "nose_right_ala":     { "landmarks": [294, 327, 344], "bones": ["nose.R", "nose.R.001"] },
    "left_cheek_bottom":  { "landmarks": [147, 187, 207], "bones": ["cheek.B.L", "cheek.B.L.001"] },
    "left_cheek_top":     { "landmarks": [116, 123], "bones": ["cheek.T.L", "cheek.T.L.001"] },
    "right_cheek_bottom": { "landmarks": [376, 411, 436], "bones": ["cheek.B.R", "cheek.B.R.001"] },
    "right_cheek_top":    { "landmarks": [345, 352], "bones": ["cheek.T.R", "cheek.T.R.001"] },
    "left_forehead":      { "landmarks": [21, 54, 103], "bones": ["forehead.L", "forehead.L.001", "forehead.L.002"] },
    "right_forehead":     { "landmarks": [251, 284, 332], "bones": ["forehead.R", "forehead.R.001", "forehead.R.002"] },
    "left_temple":        { "landmarks": [234, 139], "bones": ["temple.L"] },
    "right_temple":       { "landmarks": [454, 368], "bones": ["temple.R"] },
    "jaw_left":           { "landmarks": [172, 136, 150], "bones": ["jaw.L", "jaw.L.001", "chin.L"] },
    "jaw_right":          { "landmarks": [397, 365, 379], "bones": ["jaw.R", "jaw.R.001", "chin.R"] },
    "left_ear":           { "landmarks": [234, 227, 137], "bones": ["ear.L", "ear.L.001", "ear.L.002", "ear.L.003", "ear.L.004"] },
    "right_ear":          { "landmarks": [454, 447, 366], "bones": ["ear.R", "ear.R.001", "ear.R.002", "ear.R.003", "ear.R.004"] }
  },
    "mediapipe_hands_landmarks": {
    "_note": "21 landmarks per hand: 0=wrist, 1-4=thumb, 5-8=index, 9-12=middle, 13-16=ring, 17-20=pinky",
    "LEFT": {
      "0_wrist":       "hand.L",
      "1_thumb_mcp":   "thumb.01.L",
      "2_thumb_ip":    "thumb.02.L",
      "3_thumb_tip":   "thumb.03.L",
      "4_thumb_tip":   "thumb.03.L",
      "5_index_mcp":   "palm.01.L",
      "6_index_pip":   "f_index.01.L",
      "7_index_dip":   "f_index.02.L",
      "8_index_tip":   "f_index.03.L",
      "9_middle_mcp":  "palm.02.L",
      "10_middle_pip": "f_middle.01.L",
      "11_middle_dip": "f_middle.02.L",
      "12_middle_tip": "f_middle.03.L",
      "13_ring_mcp":   "palm.03.L",
      "14_ring_pip":   "f_ring.01.L",
      "15_ring_dip":   "f_ring.02.L",
      "16_ring_tip":   "f_ring.03.L",
      "17_pinky_mcp":  "palm.04.L",
      "18_pinky_pip":  "f_pinky.01.L",
      "19_pinky_dip":  "f_pinky.02.L",
      "20_pinky_tip":  "f_pinky.03.L"
    },
    "RIGHT": {
      "0_wrist":       "hand.R",
      "1_thumb_mcp":   "thumb.01.R",
      "2_thumb_ip":    "thumb.02.R",
      "3_thumb_tip":   "thumb.03.R",
      "4_thumb_tip":   "thumb.03.R",
      "5_index_mcp":   "palm.01.R",
      "6_index_pip":   "f_index.01.R",
      "7_index_dip":   "f_index.02.R",
      "8_index_tip":   "f_index.03.R",
      "9_middle_mcp":  "palm.02.R",
      "10_middle_pip": "f_middle.01.R",
      "11_middle_dip": "f_middle.02.R",
      "12_middle_tip": "f_middle.03.R",
      "13_ring_mcp":   "palm.03.R",
      "14_ring_pip":   "f_ring.01.R",
      "15_ring_dip":   "f_ring.02.R",
      "16_ring_tip":   "f_ring.03.R",
      "17_pinky_mcp":  "palm.04.R",
      "18_pinky_pip":  "f_pinky.01.R",
      "19_pinky_dip":  "f_pinky.02.R",
      "20_pinky_tip":  "f_pinky.03.R"
    }
  },
    "mediapipe_pose_landmarks": {
    "_note": "Use poseWorldLandmarks (metric, world space) for bone rotations",
    "11_left_shoulder":  "shoulder.L",
    "12_right_shoulder": "shoulder.R",
    "13_left_elbow":     "forearm.L",
    "14_right_elbow":    "forearm.R",
    "15_left_wrist":     "hand.L",
    "16_right_wrist":    "hand.R",
    "23_left_hip":       "pelvis.L",
    "24_right_hip":      "pelvis.R",
    "25_left_knee":      "shin.L",
    "26_right_knee":     "shin.R",
    "27_left_ankle":     "foot.L",
    "28_right_ankle":    "foot.R",
    "31_left_foot_index":"toe.L",
    "32_right_foot_index":"toe.R",
    "spine_interpolated": ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
  }
}

# --- 2. EXTRACTION LOGIC ---
def get_centroid(landmarks, indices):
    pts = [[landmarks[i].x, landmarks[i].y, landmarks[i].z] for i in indices if i < len(landmarks)]
    return np.mean(pts, axis=0).tolist() if pts else [0, 0, 0]

def extract_rig_frame(results):
    frame_map = {}

    # Face Mapping
    if results.face_landmarks:
        face = results.face_landmarks.landmark
        for group, info in BONE_MAPPING["mediapipe_face_landmarks"].items():
            coord = get_centroid(face, info["landmarks"])
            for bone_name in info["bones"]:
                frame_map[bone_name] = coord

    # Hand Mapping (Left & Right)
    for side, res in [("LEFT", results.left_hand_landmarks), ("RIGHT", results.right_hand_landmarks)]:
        if res:
            for key, bone_name in BONE_MAPPING["mediapipe_hands_landmarks"][side].items():
                idx = int(key.split('_')[0])
                frame_map[bone_name] = [res.landmark[idx].x, res.landmark[idx].y, res.landmark[idx].z]

    # Pose & Spine Interpolation
    if results.pose_landmarks:
        pose = results.pose_landmarks.landmark
        # Direct Pose Mapping
        for key, bone_name in BONE_MAPPING["mediapipe_pose_landmarks"].items():
            if "_" in key and key[0].isdigit():
                idx = int(key.split('_')[0])
                frame_map[bone_name] = [pose[idx].x, pose[idx].y, pose[idx].z]

        # Spine Interpolation (Shoulders to Hips)
        mid_hip = np.mean([[pose[23].x, pose[23].y, pose[23].z], [pose[24].x, pose[24].y, pose[24].z]], axis=0)
        mid_shoulder = np.mean([[pose[11].x, pose[11].y, pose[11].z], [pose[12].x, pose[12].y, pose[12].z]], axis=0)
        
        spine_list = BONE_MAPPING["mediapipe_pose_landmarks"]["spine_interpolated"]
        for i, bone_name in enumerate(spine_list):
            alpha = (i + 1) / (len(spine_list) + 1)
            frame_map[bone_name] = (mid_hip * (1 - alpha) + mid_shoulder * alpha).tolist()

    return frame_map

# --- 3. TEST RUN ON SINGLE VIDEO ---
def test_pipeline(video_path):
    mp_holistic = mp.solutions.holistic
    cap = cv2.VideoCapture(video_path)
    
    video_data = []
    print(f"Starting extraction for: {video_path}")

    with mp_holistic.Holistic(static_image_mode=False, min_detection_confidence=0.5) as holistic:
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # MediaPipe processing
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(image)
            
            # Extract mapped data
            mapped_frame = extract_rig_frame(results)
            video_data.append(mapped_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"Processed {frame_count} frames...")

    cap.release()
    
    # Preview the data for the first frame
    if video_data:
        print("\n--- TEST SUCCESSFUL ---")
        print(f"Total Frames: {len(video_data)}")
        print("First Frame Bone Data Sample (shoulder.L):", video_data[0].get("shoulder.L"))
        
        # Save to a small test JSON to check structure
        with open("test_bone_data.json", "w") as f:
            json.dump(video_data, f)
        print("Full sequence saved to 'test_bone_data.json' for review.")
    else:
        print("No data extracted. Check video path or lighting.")

# --- EXECUTION ---
# REPLACE THIS WITH YOUR VIDEO PATH
test_pipeline("D:/hack helix/Rocky/test_video.mp4")
# gestures.py
import math
import numpy as np

# MediaPipe landmark indices for fingers
TIP_IDS = {
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20
}
PIP_IDS = {
    "thumb": 3,
    "index": 6,
    "middle": 10,
    "ring": 14,
    "pinky": 18
}
MCP_IDS = {
    "thumb": 2,
    "index": 5,
    "middle": 9,
    "ring": 13,
    "pinky": 17
}

def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def fingers_up(landmarks, handedness='Right'):
    # returns dict of finger_name -> True if finger extended
    # landmarks: list of (x,y,z) normalized
    states = {}
    # For index, middle, ring, pinky: compare tip.y and pip.y (y smaller => finger up in camera coordinates)
    for finger in ["index", "middle", "ring", "pinky"]:
        tip = landmarks[TIP_IDS[finger]]
        pip = landmarks[PIP_IDS[finger]]
        states[finger] = tip[1] < pip[1]  # tip.y < pip.y => extended (camera coords)
    # Thumb: check relative x coordinate depending on hand orientation
    thumb_tip = landmarks[TIP_IDS["thumb"]]
    thumb_mcp = landmarks[MCP_IDS["thumb"]]
    # handedness param could be 'Right' or 'Left' (MediaPipe gives label). If unknown, assume Right.
    if handedness == 'Left':
        states["thumb"] = thumb_tip[0] > thumb_mcp[0]
    else:
        states["thumb"] = thumb_tip[0] < thumb_mcp[0]
    return states

def is_open_palm(landmarks, handedness='Right'):
    s = fingers_up(landmarks, handedness)
    # open palm if all fingers are up (including thumb)
    return all(s.get(f, False) for f in ["thumb", "index", "middle", "ring", "pinky"])

def is_fist(landmarks, handedness='Right'):
    s = fingers_up(landmarks, handedness)
    # fist if all fingers are down
    return not any(s.get(f, False) for f in ["thumb", "index", "middle", "ring", "pinky"])

def is_point(landmarks, handedness='Right'):
    s = fingers_up(landmarks, handedness)
    # point when only index is up (others down)
    return s.get("index", False) and not any(s.get(f, False) for f in ["middle", "ring", "pinky", "thumb"])

def is_ok(landmarks, handedness='Right', threshold=0.06):
    # OK when thumb tip close to index tip, distance relative to palm size
    index_tip = landmarks[TIP_IDS["index"]]
    thumb_tip = landmarks[TIP_IDS["thumb"]]
    wrist = landmarks[0]
    # Use normalized distance: divide by shoulder/palm scale (distance wrist to middle_mcp)
    palm_scale = _distance(wrist, landmarks[MCP_IDS["middle"]]) + 1e-6
    d = _distance(index_tip, thumb_tip) / palm_scale
    return d < threshold

# high level mapping convenience
def classify(landmarks, handedness='Right'):
    # landmarks is a list of (x,y,z)
    if landmarks is None:
        return None
    if is_open_palm(landmarks, handedness):
        return "open_palm"
    if is_fist(landmarks, handedness):
        return "fist"
    if is_point(landmarks, handedness):
        return "point"
    if is_ok(landmarks, handedness):
        return "ok"
    return None

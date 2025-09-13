# main.py
import cv2
import mediapipe as mp
import time
import collections
import numpy as np
from gestures import classify
from utils import load_config, perform_action

def landmarks_to_list(hand_landmarks):
    # convert mp landmarks to list of (x,y,z)
    return [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]

def main():
    cfg = load_config("config.json")
    g2a = cfg.get("gesture_to_action", {})
    actions = cfg.get("actions", {})
    gs = cfg.get("gesture_settings", {})
    video_cfg = cfg.get("video", {})

    cam_idx = video_cfg.get("camera_index", 0)
    flip = video_cfg.get("flip_horizontal", True)
    fw = video_cfg.get("frame_width", 1280)
    fh = video_cfg.get("frame_height", 720)

    min_frames = gs.get("min_frames_for_gesture", 5)
    cooldown = gs.get("cooldown_seconds", 1.0)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, fw)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, fh)

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=gs.get("detection_confidence", 0.6),
        min_tracking_confidence=gs.get("tracking_confidence", 0.5)
    )

    gesture_window = collections.deque(maxlen=min_frames)
    last_trigger_time = 0
    last_gesture = None

    print("[HushHands] Starting. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[HushHands] Failed to grab frame")
            break
        if flip:
            frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        current_gesture = None
        hand_label = 'Right'
        if results.multi_hand_landmarks:
            # take first hand
            h_landmarks = results.multi_hand_landmarks[0]
            if results.multi_handedness:
                hand_label = results.multi_handedness[0].classification[0].label
            lm_list = landmarks_to_list(h_landmarks)
            current_gesture = classify(lm_list, hand_label)
            # draw landmarks
            mp_draw.draw_landmarks(frame, h_landmarks, mp_hands.HAND_CONNECTIONS)
            if current_gesture:
                cv2.putText(frame, current_gesture, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        else:
            current_gesture = None

        # smoothing
        gesture_window.append(current_gesture)
        # decide majority gesture in the window (ignore None)
        counts = {}
        for g in gesture_window:
            if g is None:
                continue
            counts[g] = counts.get(g, 0) + 1
        majority_gesture = None
        if counts:
            majority_gesture = max(counts, key=counts.get)
            # ensure it appears in enough frames (>= half the window)
            if counts[majority_gesture] < (min_frames // 2 + 1):
                majority_gesture = None

        # trigger if new gesture and cooldown passed
        now = time.time()
        if majority_gesture and majority_gesture != last_gesture and (now - last_trigger_time) > cooldown:
            last_trigger_time = now
            last_gesture = majority_gesture
            mapped = g2a.get(majority_gesture)
            print(f"[HushHands] Detected gesture: {majority_gesture} -> {mapped}")
            if mapped:
                perform_action(mapped, actions)

        # Visual helper
        if last_gesture:
            cv2.putText(frame, f"Last: {last_gesture}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2, cv2.LINE_AA)

        cv2.imshow("HushHands", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
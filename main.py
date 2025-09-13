import cv2
import mediapipe as mp
import time
import json
import os
import math
from collections import deque
import pyautogui
from pynput.keyboard import Controller, Key
import pyperclip

# Optional: active window detection
try:
    import pygetwindow as gw
except Exception:
    gw = None

# ------------------------------ Config ------------------------------
CONFIG_PATH = "hushhands_config.json"

DEFAULT_CONFIG = {
    "camera_index": 0,
    "frame_width": 1280,
    "frame_height": 720,
    "gesture_debounce_ms": 500,
    "smoothing": 5,
    "pointer_radius": 12,
    "draw_color_bgr": [0, 0, 255],
    "stroke_thickness": 3,
    "quick_messages": ["On my way", "Can you repeat?", "I agree"],
    "mappings": {
        "prev_slide": "thumb_only",
        "next_slide": "pinky_only",
        "pointer": "index_and_middle",
        "draw": "index_only",
        "undo": "middle_three",
        "clear": "five_open",
        "mute_toggle": "pinch_thumb_index",
        "send_quick_msg": "thumb_and_pinky",
        "toggle_gesture_mode": "palm_and_fist"
    },
    "platform_shortcuts": {
        "slides_next_key": "right",
        "slides_prev_key": "left",
        "mute_toggle_key_generic": "ctrl+shift+m"
    }
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception as e:
            print("Failed to load config, using default:", e)
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

config = load_config()
kb = Controller()
_last_action_time = {}

def can_do(action):
    now = time.time() * 1000
    last = _last_action_time.get(action, 0)
    if now - last > config['gesture_debounce_ms']:
        _last_action_time[action] = now
        return True
    return False

# ------------------------------ Hand utilities ------------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

FINGER_TIPS = {'thumb':4,'index':8,'middle':12,'ring':16,'pinky':20}
FINGER_PIPS = {'thumb':2,'index':6,'middle':10,'ring':14,'pinky':18}

def fingers_up(hand_landmarks, handedness='Right'):
    lm = hand_landmarks.landmark
    res = {}
    if handedness == 'Right':
        res['thumb'] = lm[FINGER_TIPS['thumb']].x < lm[FINGER_PIPS['thumb']].x
    else:
        res['thumb'] = lm[FINGER_TIPS['thumb']].x > lm[FINGER_PIPS['thumb']].x
    for f in ['index','middle','ring','pinky']:
        res[f] = lm[FINGER_TIPS[f]].y < lm[FINGER_PIPS[f]].y
    return res

def distance(a,b):
    return math.hypot(a.x-b.x,a.y-b.y)

# ------------------------------ Gesture Detection ------------------------------
class GestureDetector:
    def __init__(self):
        self.hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.6)

    def process(self, frame_rgb):
        return self.hands.process(frame_rgb)

    def interpret(self, results):
        gestures = set()
        payload = {}
        if not results.multi_hand_landmarks:
            return gestures, payload
        hands = results.multi_hand_landmarks
        handedness_list = results.multi_handedness
        up_list=[]
        for idx, hand in enumerate(hands):
            handedness='Right'
            if handedness_list:
                try:
                    handedness = handedness_list[idx].classification[0].label
                except:
                    pass
            up_list.append(fingers_up(hand,handedness))
        hand=hands[0]
        up=up_list[0]
        payload['fingers_up']=up

        # Standard gestures
        if up['thumb'] and not any([up['index'],up['middle'],up['ring'],up['pinky']]): gestures.add('thumb_only')
        if up['pinky'] and not any([up['thumb'],up['index'],up['middle'],up['ring']]): gestures.add('pinky_only')
        if up['index'] and up['middle'] and not any([up['ring'],up['pinky']]): gestures.add('index_and_middle')
        if up['index'] and not any([up['middle'],up['ring'],up['pinky']]) and not up['thumb']: gestures.add('index_only')
        if up['middle'] and up['ring'] and up['pinky'] and not up['index']: gestures.add('middle_three')
        if all(up.values()): gestures.add('five_open')
        tip_thumb = hand.landmark[FINGER_TIPS['thumb']]
        tip_index = hand.landmark[FINGER_TIPS['index']]
        if distance(tip_thumb,tip_index)<0.04: gestures.add('pinch_thumb_index')
        if up['thumb'] and up['pinky'] and not any([up['index'],up['middle'],up['ring']]): gestures.add('thumb_and_pinky')

        # Palm + fist toggle
        if len(hands)==2:
            up2 = up_list[1]
            if (all(up.values()) and not any(up2.values())) or (all(up2.values()) and not any(up.values())):
                gestures.add('palm_and_fist')

        # coords for pointer/draw
        coords=None
        # Draw pointer/draw if index finger is up (more forgiving)
        if up['index']:
            coords=(hand.landmark[FINGER_TIPS['index']].x, hand.landmark[FINGER_TIPS['index']].y)
            if not up['thumb']:
                gestures.add('index_only')

        payload['coords']=coords
        return gestures,payload

# ------------------------------ Annotation Layer ------------------------------
class AnnotationLayer:
    def __init__(self,width,height):
        self.width=width
        self.height=height
        self.strokes=[]
        self.current=[]
    def start_stroke(self,x,y): self.current=[(x,y)]
    def add_point(self,x,y): self.current.append((x,y))
    def end_stroke(self):
        if self.current: self.strokes.append(self.current)
        self.current=[]
    def undo(self): 
        if self.strokes: self.strokes.pop()
    def clear(self): self.strokes=[]; self.current=[]
    def draw_on(self,img):
        for stroke in self.strokes:
            for i in range(1,len(stroke)):
                x1,y1=stroke[i-1]
                x2,y2=stroke[i]
                cv2.line(img,(int(x1),int(y1)),(int(x2),int(y2)),tuple(config['draw_color_bgr']),config['stroke_thickness'])
        if self.current:
            for i in range(1,len(self.current)):
                x1,y1=self.current[i-1]
                x2,y2=self.current[i]
                cv2.line(img,(int(x1),int(y1)),(int(x2),int(y2)),tuple(config['draw_color_bgr']),config['stroke_thickness'])

# ------------------------------ Active window ------------------------------
def get_active_window():
    if gw is None: return None
    try:
        w=gw.getActiveWindow()
        if w: return w.title
    except:
        return None
    return None

# ------------------------------ Actions ------------------------------
def press_key(keyname):
    try: pyautogui.press(keyname)
    except:
        try:
            if len(keyname)==1: kb.press(keyname); kb.release(keyname)
            else:
                if keyname.lower()=='left': kb.press(Key.left); kb.release(Key.left)
                elif keyname.lower()=='right': kb.press(Key.right); kb.release(Key.right)
        except: pass

def toggle_mute():
    s1=config['platform_shortcuts'].get('mute_toggle_key_generic')
    if s1:
        try: pyautogui.hotkey(*s1.split('+'))
        except: pass

def send_quick_message(index=0):
    msgs=config.get('quick_messages',[])
    if not msgs: return
    i=index%len(msgs)
    msg=msgs[i]
    pyperclip.copy(msg)
    try: pyautogui.hotkey('ctrl','v'); pyautogui.press('enter')
    except:
        try: pyautogui.hotkey('command','v'); pyautogui.press('enter')
        except: pass

# ------------------------------ Main Loop ------------------------------
def main():
    cap = cv2.VideoCapture(config['camera_index'])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['frame_width'])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['frame_height'])
    detector = GestureDetector()
    annot = AnnotationLayer(config['frame_width'], config['frame_height'])

    quick_msg_idx = 0
    drawing_mode = False
    pointer_mode = False
    gesture_mode = True
    smoothed_coords = deque(maxlen=config['smoothing'])
    mouse_down = False  # for actual drawing on slide

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(frame_rgb)
        gestures, payload = detector.interpret(results)

        # Toggle Gesture Mode
        if 'palm_and_fist' in gestures and can_do('toggle_gesture_mode'):
            gesture_mode = not gesture_mode

        active_window = get_active_window() or ""
        is_ppt = 'powerpoint' in active_window.lower() or 'slide' in active_window.lower()

        # ----------------- Gesture Mode OFF → Camera Cursor + Draw on Slide -----------------
        if not gesture_mode and is_ppt:
            overlay = frame.copy()
            cv2.putText(overlay, "Camera Cursor Mode - Draw on Slide Enabled", (50,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
            if payload.get('coords'):
                cx = int(payload['coords'][0] * pyautogui.size().width)
                cy = int(payload['coords'][1] * pyautogui.size().height)
                pyautogui.moveTo(cx, cy, duration=0.01)

                # Draw gesture → mouse down/drag
                if mapping.get('draw') in gestures:
                    if not mouse_down:
                        pyautogui.mouseDown()
                        mouse_down = True
                else:
                    if mouse_down:
                        pyautogui.mouseUp()
                        mouse_down = False

            cv2.imshow('HushHands - Live', overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: break
            continue  # skip HushHands logic

        # ----------------- Gesture Mode ON → HushHands features -----------------
        context = 'presentation' if any(k.lower() in (active_window.lower() if active_window else '') 
                                       for k in ['powerpoint','slide','google meet','present']) else 'generic'
        mapping = config['mappings']

        # Slide controls
        if mapping.get('next_slide') in gestures and can_do('next_slide'):
            press_key(config['platform_shortcuts'].get('slides_next_key','right'))
        if mapping.get('prev_slide') in gestures and can_do('prev_slide'):
            press_key(config['platform_shortcuts'].get('slides_prev_key','left'))

        pointer_mode = mapping.get('pointer') in gestures

        # Drawing logic in OpenCV overlay (still works)
        if mapping.get('draw') in gestures and payload.get('coords'):
            cx = int(payload['coords'][0] * w)
            cy = int(payload['coords'][1] * h)
            smoothed_coords.append((cx, cy))
            avgx = int(sum([p[0] for p in smoothed_coords])/len(smoothed_coords))
            avgy = int(sum([p[1] for p in smoothed_coords])/len(smoothed_coords))
            if not drawing_mode:
                drawing_mode = True
                annot.start_stroke(avgx, avgy)
            else:
                annot.add_point(avgx, avgy)
        else:
            if drawing_mode:
                drawing_mode = False
                annot.end_stroke()

        if mapping.get('undo') in gestures and can_do('undo'):
            annot.undo()
        if mapping.get('clear') in gestures and can_do('clear'):
            annot.clear()
        if mapping.get('mute_toggle') in gestures and can_do('mute_toggle'):
            toggle_mute()
        if mapping.get('send_quick_msg') in gestures and can_do('send_quick_msg'):
            send_quick_message(quick_msg_idx)
            quick_msg_idx += 1

        overlay = frame.copy()
        annot.draw_on(overlay)

        # Gesture Mode indicator
        cv2.circle(overlay,(30,30),15,(0,255,0) if gesture_mode else (0,0,255),-1)
        cv2.putText(overlay,"Gesture Mode ON" if gesture_mode else "Gesture Mode OFF",(50,37),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0) if gesture_mode else (0,0,255),2)

        # Pointer
        if pointer_mode and payload.get('coords'):
            px = int(payload['coords'][0]*w)
            py = int(payload['coords'][1]*h)
            cv2.circle(overlay,(px,py),config['pointer_radius'],(0,255,255),-1)
            cv2.circle(overlay,(px,py),config['pointer_radius']+6,(0,0,0),2)

        # Mini feed
        mini = cv2.resize(frame,(240,135))
        overlay[10:10+135, w-10-240:w-10] = mini
        cv2.rectangle(overlay, (w-10-240-2,8), (w-10+2,8+135+2), (200,200,200),1)

        cv2.imshow('HushHands - Live', overlay)
        key = cv2.waitKey(1) & 0xFF
        if key == 27: break
        elif key == ord('c'): annot.clear()
        elif key == ord('u'): annot.undo()

    cap.release()
    cv2.destroyAllWindows()
    
if __name__=='__main__':
    main()

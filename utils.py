# utils.py
import json
import time
import pyautogui

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def perform_action(action, actions_map):
    """
    action: string like "next_slide"
    actions_map: actions dict from config
    """
    if action not in actions_map:
        print(f"[HushHands] Unknown action: {action}")
        return
    a = actions_map[action]
    t = a.get("type")
    try:
        if t == "key":
            # simple single key or list
            keys = a.get("keys", [])
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                # sequential presses
                for k in keys:
                    pyautogui.press(k)
        elif t == "hotkey":
            keys = a.get("keys", [])
            # pyautogui.hotkey expects separate args
            pyautogui.hotkey(*keys)
        elif t == "type_text":
            txt = a.get("text", "")
            pyautogui.typewrite(txt)
        elif t == "click":
            pos = a.get("pos", None)
            if pos:
                pyautogui.click(pos[0], pos[1])
            else:
                pyautogui.click()
        else:
            print(f"[HushHands] Action type not implemented: {t}")
    except Exception as e:
        print("[HushHands] Failed to perform action:", e)

# utils.py
import json
import time
import pyautogui

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def perform_action(action, actions_map):
    """
    action: string like "next_slide"
    actions_map: actions dict from config
    """
    if action not in actions_map:
        print(f"[HushHands] Unknown action: {action}")
        return
    a = actions_map[action]
    t = a.get("type")
    try:
        if t == "key":
            # simple single key or list
            keys = a.get("keys", [])
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                # sequential presses
                for k in keys:
                    pyautogui.press(k)
        elif t == "hotkey":
            keys = a.get("keys", [])
            # pyautogui.hotkey expects separate args
            pyautogui.hotkey(*keys)
        elif t == "type_text":
            txt = a.get("text", "")
            pyautogui.typewrite(txt)
        elif t == "click":
            pos = a.get("pos", None)
            if pos:
                pyautogui.click(pos[0], pos[1])
            else:
                pyautogui.click()
        else:
            print(f"[HushHands] Action type not implemented: {t}")
    except Exception as e:
        print("[HushHands] Failed to perform action:", e)


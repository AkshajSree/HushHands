# HushHands: Webcam-Based Mindful Gesture Control

## **Introduction & Problem Statement:**  
Research shows that even with thorough technical preparation, unpredictable factors like **stress**, **cognitive overload**, and **input device issues** (such as keyboard malfunction or accidental mispress) can lead to mistakes during high-stakes online presentations. These factors disrupt performance, causing users to miss key actions, make navigation errors, or even lose track of critical talking points—especially under pressure.  
**HushHands** addresses the lack of accessible, accurate, and user-friendly gesture-based presentation control systems by leveraging real-time hand gesture recognition to enable intuitive, hands-free interaction, reduce cognitive distractions, and improve overall presentation effectiveness.

## **Research & Motivation:**  
**HushHands** addresses three core challenges faced during digital interactions:  
- **Digital Distractions**  
- **Cognitive Overload** (intrinsic, extraneous, and germane load)  
- **Lack of Mindfulness**

1. **Digital Distractions**  
   Frequent device switching (keyboard, mouse, touchpad) and irrelevant pop-ups (e.g., MS Teams chats) disrupt flow during presentations and meetings.  
   → HushHands reduces interruptions by replacing device switching with natural gestures.

2. **Cognitive Overload**  
   Cognitive load theory identifies three types of load:  
   - *Intrinsic Load:* Simplified with intuitive gestures (Palm, Fist, Point, OK).  
   - *Extraneous Load:* Reduced by eliminating device switching and clutter.  
   - *Germane Load:* Enhanced with mindful breaks that refresh focus.  
   → HushHands minimizes overload and supports engagement.

3. **Lack of Mindfulness**  
   Constant multitasking reduces presence, concentration, and well-being.  
   → HushHands integrates mindful breaks and focus prompts to encourage relaxation and resilience.

**References:**  
- Cognitive Load Theory (Sweller, 1988).
- *Silencing Distractions: The Art of Uninterrupted Public Speaking*.

## **How do we address these problems?**
- Slide navigation using intuitive gestures:
1. Start HushHands.
2. Thumb → Next slide (Slides/PowerPoint).  
3. Pinky → Previous slide.
4. Rapid gestures → Mindfulness overlay (10s breathing).
5. Index- drawing on the slide
6. Middle 3 fingers- Undo
7. Palm (5 fingers open)- clear all
8. Peace (2 fingers up) - quick message
9. Index + middle fingers- virtual pointer
10. Mute / unmute using simple hand gestures

- Minimal UI to confirm gesture recognition without distraction.
- Mindfulness features such as break reminder, focus mode activation, and positive reinforcement
- Seamless integration with popular presentation and video conferencing platforms.

These features collectively create a flexible, natural, and mindful gesture-based interface to improve digital interaction and presentation control.

## **Tech Stack**
Programming Language: Python
Computer Vision: OpenCV
For video capture, frame processing, and drawing overlays.

Hand Landmark Detection: MediaPipe Hands
Real-time hand pose estimation providing 21 hand landmarks per detected hand.

Gesture Classification: Custom Python logic
Utilizes MediaPipe landmarks converted to feature vectors to classify gestures.

Configuration Management: JSON configuration files
For flexible gesture-action mapping, camera settings, and gesture detection parameters.

Action Automation: Python commands and third-party libraries
To trigger system or application-specific actions like slide navigation, muting, or sending quick messages.

User Interface: OpenCV window overlays
Provides live camera feed, gesture feedback, and minimal UI for user confirmation.

Development Environment:
Cross-platform support on Windows, Linux, and macOS with Python 3.x.

Optional Dependencies:
Additional libraries for specific integrations such as keyboard/mouse emulation (e.g., pyautogui), audio feedback, or messaging APIs

## **Accessibility**
- HushHands is built with openness and community collaboration in mind, ensuring that everyone who wants to improve their digital interaction experience can implement it in the comfort of their own computers
- This openness encourages continuous improvement and innovation, making HushHands a living project that evolves through contributions from a diverse, global user base.

## **User guide**
1. Setup your environment:
Ensure your computer has a webcam connected or built-in.
Install Python 3.x and required libraries (OpenCV, MediaPipe, NumPy, etc.).
Download or clone the HushHands repository.
2. Run the Application:
Launch the main script (main.py) using Python.
Allow access to your webcam if prompted.
3. Position Your Hand:
Place your dominant hand clearly in front of the webcam.
Ensure good lighting and a clean background for optimal detection.

## **Customization**
1. Modify config.json to map gestures to your preferred actions.
2. Adjust camera settings like resolution and flip options for better detection.
3. Add new gestures by extending the classification logic

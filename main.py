import cv2
import time
import os
import threading
import requests
import numpy as np
from ultralytics import YOLO
from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ================= TELEGRAM =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(msg, image_path=None, video_path=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not set in .env file")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
            timeout=5
        )

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                    files={"photo": img},
                    data={"chat_id": TELEGRAM_CHAT_ID},
                    timeout=5
                )

        if video_path and os.path.exists(video_path):
            with open(video_path, "rb") as vid:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo",
                    files={"video": vid},
                    data={"chat_id": TELEGRAM_CHAT_ID},
                    timeout=10
                )
    except Exception as e:
        print("Telegram Error:", e)

# ================= CONFIG =================
KNOWN_FOLDER   = "known_faces"
UNKNOWN_FOLDER = "unknown_faces"
SAVE_FOLDER    = "evidence"

os.makedirs(KNOWN_FOLDER,   exist_ok=True)
os.makedirs(UNKNOWN_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER,    exist_ok=True)

# ================= GLOBAL STATE =================
camera_on      = True
alerts_on      = True
latest_frame   = None
latest_alert   = {"status": "SAFE"}
last_alert_time = 0
COOLDOWN       = 15   # seconds between alerts

known_encodings = []
known_names     = []

# ================= VIDEO RECORD =================
is_recording    = False
video_writer    = None
video_file      = None
frames_recorded = 0
MAX_FRAMES      = 120  # ~6 seconds at 20fps

# ================= PERFORMANCE =================
frame_count = 0

# ================= SOUND ALERT =================
def play_alert_sound():
    """
    Cross-platform alert sound.
    On Windows: uses winsound.
    On Linux/Mac: uses terminal bell.
    """
    try:
        import winsound
        winsound.Beep(1000, 500)
    except ImportError:
        print("\a")  # Terminal bell for Linux/Mac

# ================= FACE RECOGNITION (Optional) =================
# To enable face recognition:
# 1. Install: pip install face_recognition cmake dlib
# 2. Uncomment the code blocks below

# def load_faces():
#     global known_encodings, known_names
#     known_encodings, known_names = [], []
#     for file in os.listdir(KNOWN_FOLDER):
#         path = os.path.join(KNOWN_FOLDER, file)
#         try:
#             import face_recognition
#             img = face_recognition.load_image_file(path)
#             enc = face_recognition.face_encodings(img)
#             if enc:
#                 known_encodings.append(enc[0])
#                 known_names.append(os.path.splitext(file)[0])
#         except:
#             pass
#     print("✅ Loaded faces:", known_names)

# load_faces()

# ================= FLASK SERVER =================
app = Flask(__name__)

@app.route("/status")
def status():
    return jsonify({"alert": latest_alert})

@app.route("/stream")
def stream():
    """Live MJPEG stream — open in browser: http://localhost:5000/stream"""
    def generate():
        while True:
            if latest_frame is None:
                continue
            _, buffer = cv2.imencode('.jpg', latest_frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

threading.Thread(
    target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False),
    daemon=True
).start()

print("🌐 Flask server started → http://localhost:5000")
send_telegram_alert("✅ Sentinel AI Started 🚀")

# ================= LOAD AI MODEL =================
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
print(f"🤖 Loading model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

# ================= CAMERA INIT =================
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("❌ Camera not detected. Check CAMERA_INDEX in .env")
    exit()

print("📷 Camera started")
prev_positions = {}

# ================= MAIN LOOP =================
print("🚀 Sentinel AI is running. Press ESC to quit.")

while True:
    frame_count += 1

    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (480, 360))
    latest_frame = frame.copy()

    # Skip every other frame for better performance
    if frame_count % 2 != 0:
        continue

    intruder  = False
    behavior  = "NORMAL"
    face_name = "Unknown"

    # ================= PERSON DETECTION =================
    results = model(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            # Class 0 = person in COCO dataset
            if int(box.cls[0]) != 0:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            pid = f"{cx}_{cy}"

            # Behavior analysis based on movement speed
            if pid in prev_positions:
                dx    = abs(cx - prev_positions[pid][0])
                dy    = abs(cy - prev_positions[pid][1])
                speed = dx + dy

                if speed > 40:
                    behavior = "RUNNING"
                elif speed > 20:
                    behavior = "SUSPICIOUS"

            prev_positions[pid] = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, behavior, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            intruder = True

    # ================= FACE RECOGNITION (Optional) =================
    # Uncomment to enable face recognition after installing dependencies

    # import face_recognition
    # rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # faces = face_recognition.face_locations(rgb, model="hog")
    # encs  = face_recognition.face_encodings(rgb, faces)

    # for (top, right, bottom, left), enc in zip(faces, encs):
    #     matches = face_recognition.compare_faces(known_encodings, enc)
    #     if True in matches:
    #         idx       = matches.index(True)
    #         face_name = known_names[idx]
    #         color     = (0, 255, 0)
    #     else:
    #         color    = (0, 0, 255)
    #         intruder = True
    #     cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    #     cv2.putText(frame, face_name, (left, top - 10),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # ================= ALERT TRIGGER =================
    now = time.time()

    if intruder and alerts_on and (now - last_alert_time > COOLDOWN):
        msg = (
            f"🚨 Intruder Alert!\n"
            f"Face: {face_name}\n"
            f"Behavior: {behavior}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Save screenshot
        img_path = os.path.join(SAVE_FOLDER, f"alert_{int(now)}.jpg")
        cv2.imwrite(img_path, frame)

        # Start recording video
        video_file  = os.path.join(SAVE_FOLDER, f"event_{int(now)}.mp4")
        video_writer = cv2.VideoWriter(
            video_file,
            cv2.VideoWriter_fourcc(*'mp4v'),
            20,
            (480, 360)
        )
        is_recording    = True
        frames_recorded = 0

        # Send Telegram alert in background thread
        threading.Thread(
            target=send_telegram_alert,
            args=(msg, img_path, None)
        ).start()

        # Play alert sound
        threading.Thread(target=play_alert_sound, daemon=True).start()

        last_alert_time = now
        print(f"🚨 ALERT TRIGGERED — {time.strftime('%H:%M:%S')} | Behavior: {behavior}")

    # ================= VIDEO RECORDING =================
    if is_recording:
        video_writer.write(frame)
        frames_recorded += 1

        if frames_recorded >= MAX_FRAMES:
            is_recording = False
            video_writer.release()
            print(f"🎥 Video saved: {video_file}")

            threading.Thread(
                target=send_telegram_alert,
                args=("🎥 Video Recorded", None, video_file)
            ).start()

    # ================= UI OVERLAY =================
    status_text  = "⚠ INTRUDER" if intruder else "✔ SAFE"
    status_color = (0, 0, 255) if intruder else (0, 255, 0)

    cv2.putText(frame, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(frame, time.strftime('%H:%M:%S'), (380, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Sentinel AI", frame)

    if cv2.waitKey(1) == 27:  # ESC to quit
        print("👋 Exiting Sentinel AI...")
        break

# ================= CLEANUP =================
cap.release()
if is_recording and video_writer:
    video_writer.release()
cv2.destroyAllWindows()
print("✅ Sentinel AI stopped.")

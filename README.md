# 🛡️ Sentinel AI — Smart Security System

An AI-powered real-time security system using YOLOv8 for person detection, Telegram alerts, live video streaming, and automatic video recording.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Detection** | YOLOv8 detects people in real-time |
| 🏃 **Behavior Analysis** | Classifies movement as NORMAL / SUSPICIOUS / RUNNING |
| 📱 **Telegram Alerts** | Sends instant alerts with screenshot to your phone |
| 🎥 **Auto Recording** | Records 6-second video clip on every alert |
| 🌐 **Live Stream** | Browser-accessible MJPEG stream at `http://localhost:5000/stream` |
| 🔔 **Sound Alert** | Plays beep when intruder is detected |
| 👤 **Face Recognition** | Optional — identify known vs unknown faces |
| 🔒 **Privacy Safe** | All credentials stored in `.env` file (never in code) |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/sentinel-ai.git
cd sentinel-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Download YOLOv8 model
```bash
# Auto-downloads on first run, or manually:
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### 4. Set up your credentials
```bash
cp .env.example .env
```
Edit `.env` and fill in your values:
```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
CAMERA_INDEX=0
MODEL_PATH=yolov8n.pt
```

### 5. Run
```bash
python main.py
```

---

## 📱 Telegram Setup

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow steps → copy the **token**
3. Search **@userinfobot** → send any message → copy your **chat ID**
4. Paste both into your `.env` file

---

## 📁 Project Structure

```
sentinel-ai/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Your credentials (NOT committed)
├── .gitignore           # Git ignore rules
├── yolov8n.pt           # AI model (NOT committed, download separately)
├── known_faces/         # Add photos of known people here
├── unknown_faces/       # Unknown face captures saved here
└── evidence/            # Alert screenshots & videos saved here
```

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/status` | GET | Returns current alert status as JSON |
| `/stream` | GET | Live MJPEG video stream |

---

## 👤 Optional: Face Recognition

To enable face recognition:

1. Install extra dependencies:
```bash
pip install cmake dlib face_recognition
```

2. Add photos of known people to `known_faces/`:
   - Name each file as the person's name: `john.jpg`, `alice.png`

3. Uncomment the face recognition blocks in `main.py`

---

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_TOKEN` | — | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | — | Your Telegram chat ID |
| `CAMERA_INDEX` | `0` | Webcam index (0 = default) |
| `MODEL_PATH` | `yolov8n.pt` | Path to YOLO model |

---

## 📋 Requirements

- Python 3.8+
- Webcam
- Windows / Linux / macOS

---

## ⚠️ Privacy Notice

- Evidence footage is stored **locally only** in `evidence/`
- Telegram alerts contain screenshots — only sent to **your own** Telegram chat
- **Never commit `.env`** — it contains your private credentials
- Known faces data is **excluded from git** by `.gitignore`

---

## 📄 License

MIT License — free to use and modify.

---

## 🙏 Credits

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [Flask](https://flask.palletsprojects.com/)

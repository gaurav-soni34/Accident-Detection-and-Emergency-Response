# AI-Based Accident Detection and Emergency Response

This project uses Python, OpenCV, and a webcam feed to detect sudden high motion as a basic accident trigger.  
When a trigger is detected, the system starts an emergency response flow:

- Sends an email alert through Gmail SMTP (if configured)
- Plays an alarm sound (or Windows beep fallback)
- Shows real-time status in the video stream

## What This Project Includes

- `app.py` - main OpenCV-based detector and emergency trigger
- `streamlit_app.py` - Streamlit UI version for local use
- `requirements.txt` - Python dependencies

## Features

- Real-time webcam monitoring
- Motion detection using frame differencing:
  - grayscale conversion
  - Gaussian blur for noise reduction
  - absolute frame difference + binary threshold
- Status overlay on video:
  - `SAFE`
  - `ACCIDENT DETECTED`
- Emergency trigger with cooldown protection:
  - Email alert via Gmail SMTP
  - Audible alert (`alert.wav` if available, otherwise beep)
- Configurable thresholds and camera settings via CLI

## Requirements

- Python 3.9+ recommended
- Webcam connected and accessible
- Windows/macOS/Linux (tested best on Windows because of beep fallback)

## Quick Setup

1. Open terminal in this folder.
2. (Recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configure Email Alerts (Optional)

Open `app.py` and set:

- `GMAIL_SENDER_EMAIL`
- `GMAIL_APP_PASSWORD` (Google App Password, not your normal Gmail password)
- `GMAIL_RECEIVER_EMAIL`

If these values are missing or placeholders, the app skips email and still runs sound alerts.

## Run the OpenCV Version

```bash
python app.py
```

Press `q` to close the OpenCV window.

### Useful CLI Options

```bash
python app.py --camera-index 0 --width 640 --height 480 --motion-threshold 5000 --diff-threshold 25 --cooldown-seconds 30
```

- `--camera-index`: webcam index (use `1`, `2`, etc. if needed)
- `--motion-threshold`: changed-pixel trigger limit
- `--diff-threshold`: per-pixel difference sensitivity
- `--cooldown-seconds`: minimum time between emergency triggers

## Run the Streamlit Version

```bash
streamlit run streamlit_app.py
```

- Start webcam from the app UI
- Tune thresholds from sidebar controls

## Streamlit Cloud Note

Deploying webcam apps on Streamlit Cloud is limited because the cloud server does not have direct access to your local webcam.

For reliable webcam detection:

- Run Streamlit locally, or
- Use a browser/WebRTC-based camera component and forward frames to backend logic

## Troubleshooting

- **Webcam not opening**
  - Check camera permission in OS settings
  - Try another `--camera-index`
  - Close apps already using the camera

- **Too many false alerts**
  - Increase `--motion-threshold`
  - Increase `--diff-threshold`
  - Improve lighting stability and camera placement

- **No sound on alert**
  - Add `alert.wav` in project root
  - Ensure speakers are enabled

- **Email alert fails**
  - Verify Gmail sender, app password, and receiver values
  - Ensure 2-step verification is enabled on Gmail account before creating App Password

## Important Security Note

Do not commit real email credentials or app passwords in source code.  
Use environment variables or a local secret config file excluded from version control.

## Future Improvements

- Replace motion-only trigger with model-based accident detection (for example YOLO)
- Add fall detection using pose estimation
- Add GPS/location payload in emergency alerts
- Log alert events to file/database for audit and analysis


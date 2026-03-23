import argparse
import os
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np

import smtplib
from email.mime.text import MIMEText

try:
 
    from playsound import playsound
except Exception:  # pragma: no cover
    playsound = None  # type: ignore


GMAIL_SENDER_EMAIL = "gauravsoni1967@gmail.com"
GMAIL_APP_PASSWORD = "dmupygxzayotouob"
GMAIL_RECEIVER_EMAIL = "gauravsoni5003@gmail.com"

EMAIL_SUBJECT = "Emergency Alert: Possible Accident at MP Nagar Checkpoint"
EMAIL_MESSAGE = """Emergency Alert

A possible accident has been detected near MP Nagar Checkpoint, Bhopal.

Location: MP Nagar Checkpoint, Bhopal
Time: Immediate attention required

The system has identified unusual motion activity that may indicate a road accident or emergency situation.

Action Required:
Please respond promptly and take appropriate action. Contact emergency services if necessary.

This alert has been generated automatically by the Accident Detection System.

Regards,
AI Emergency Monitoring System
"""

ALERT_SOUND_PATH = "alert.wav"

# -----------------------------
# Motion detection
# -----------------------------
MOTION_THRESHOLD_DEFAULT = 5000       
DIFF_THRESHOLD_DEFAULT = 25          # threshold 
COOLDOWN_SECONDS_DEFAULT = 30


def detect_motion(
    prev_gray: Optional[np.ndarray],
    gray: np.ndarray,
    motion_threshold: int = MOTION_THRESHOLD_DEFAULT,
    diff_threshold: int = DIFF_THRESHOLD_DEFAULT,
) -> Tuple[int, bool]:
    """
    Detect sudden high motion using frame differencing.

    Returns:
      (motion_intensity, triggered)
    """
    if prev_gray is None:
        return 0, False

    # grayscale frames
    diff = cv2.absdiff(prev_gray, gray)

    
    _, thresh = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)

    
    motion_intensity = int(cv2.countNonZero(thresh))
    triggered = motion_intensity >= motion_threshold

    return motion_intensity, triggered


def send_email_alert() -> None:
    """
    Send emergency email alert via Gmail SMTP.

    Uses smtplib + email.mime.text as requested.
    Prints success or error messages to the console for debugging.
    """
    # Skip sending if placeholders were not updated.
    if (
        not GMAIL_SENDER_EMAIL
        or "YOUR_GMAIL_SENDER_EMAIL" in GMAIL_SENDER_EMAIL
        or not GMAIL_APP_PASSWORD
        or "YOUR_GMAIL_APP_PASSWORD" in GMAIL_APP_PASSWORD
        or not GMAIL_RECEIVER_EMAIL
        or "YOUR_RECEIVER_EMAIL" in GMAIL_RECEIVER_EMAIL
    ):
        print("Email not configured: set GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, GMAIL_RECEIVER_EMAIL.")
        return

    msg = MIMEText(EMAIL_MESSAGE)
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = GMAIL_SENDER_EMAIL
    msg["To"] = GMAIL_RECEIVER_EMAIL

    try:
        # Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER_EMAIL, [GMAIL_RECEIVER_EMAIL], msg.as_string())

        print("Email alert sent successfully.")
    except Exception as exc:
        print(f"Email alert failed: {exc}")


def _play_alert_sound() -> None:
    """
    Play an alert sound.
    - If `alert.wav` exists and `playsound` is available, play it.
    - Otherwise, use a Windows beep (std library).
    """
    # playsound path-based approach (optional)
    if playsound is not None and os.path.exists(ALERT_SOUND_PATH):
        try:
            playsound(ALERT_SOUND_PATH)
            return
        except Exception:
            # Continue to beep fallback
            pass

    # Windows beep fallback
    try:
        import winsound  # type: ignore

        for _ in range(3):
            winsound.Beep(1000, 350)
            time.sleep(0.05)
    except Exception:
        print("Sound unavailable on this system.")


def agent_call(reason: str = "Accident detected. Please call emergency services.", motion_intensity: Optional[int] = None) -> None:
    """
    Emergency response agent:
    - Send Email alert using Gmail SMTP
    - Play alert sound
    """
    print(reason)
    if motion_intensity is not None:
        print(f"(Motion intensity: {motion_intensity})")

    # Best-effort email + always play an audible alert.
    send_email_alert()

    print("Calling Ambulance...")
    _play_alert_sound()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-Based Accident Detection & Emergency Response System")
    parser.add_argument("--camera-index", type=int, default=0, help="Webcam index for OpenCV (default: 0)")
    parser.add_argument("--width", type=int, default=640, help="Camera capture width")
    parser.add_argument("--height", type=int, default=480, help="Camera capture height")
    parser.add_argument("--motion-threshold", type=int, default=MOTION_THRESHOLD_DEFAULT, help="Changed-pixels threshold")
    parser.add_argument("--diff-threshold", type=int, default=DIFF_THRESHOLD_DEFAULT, help="Frame differencing threshold")
    parser.add_argument("--cooldown-seconds", type=int, default=COOLDOWN_SECONDS_DEFAULT, help="Cooldown to prevent repeated calls")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        print("Could not open webcam. Check camera permissions and camera index.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    prev_gray: Optional[np.ndarray] = None
    last_call_time = 0.0
    prev_triggered = False

    cv2.namedWindow("Accident Detection", cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        motion_intensity, triggered = detect_motion(
            prev_gray=prev_gray,
            gray=gray,
            motion_threshold=args.motion_threshold,
            diff_threshold=args.diff_threshold,
        )
        prev_gray = gray

        status_text = "ACCIDENT DETECTED" if triggered else "SAFE"
        color = (0, 0, 255) if triggered else (0, 255, 0)

        # Overlay status
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"Motion intensity: {motion_intensity}", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Threshold: {args.motion_threshold}", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

        now = time.time()
        if triggered and (not prev_triggered) and (now - last_call_time) >= args.cooldown_seconds:
            last_call_time = now

            
            threading.Thread(
                target=agent_call,
                kwargs={
                    "reason": "Accident detected. Please call emergency services.",
                    "motion_intensity": motion_intensity,
                },
                daemon=True,
            ).start()
        prev_triggered = triggered

        cv2.imshow("Accident Detection", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


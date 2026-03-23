import time
import threading

import cv2
import streamlit as st

import app as accident_app


def main() -> None:
    st.set_page_config(page_title="Accident Detection", layout="wide")
    st.title("AI-Based Accident Detection & Emergency Response System")

    st.sidebar.header("Settings")
    camera_index = st.sidebar.number_input("Camera Index", min_value=0, max_value=5, value=0, step=1)
    motion_threshold = st.sidebar.slider("Motion Threshold (changed pixels)", min_value=0, max_value=50000, value=5000, step=100)
    diff_threshold = st.sidebar.slider("Frame Diff Threshold", min_value=0, max_value=60, value=25, step=1)
    cooldown_seconds = st.sidebar.slider("Call Cooldown (seconds)", min_value=10, max_value=120, value=30, step=1)

    if "running" not in st.session_state:
        st.session_state.running = False
    if "cap" not in st.session_state:
        st.session_state.cap = None
    if "prev_gray" not in st.session_state:
        st.session_state.prev_gray = None
    if "last_call_time" not in st.session_state:
        st.session_state.last_call_time = 0.0

    st.session_state.alert_text = st.session_state.get("alert_text", "")

    col_start, col_stop = st.columns(2)
    with col_start:
        start_clicked = st.button("Start Webcam", type="primary")
    with col_stop:
        stop_clicked = st.button("Stop Webcam")

    if start_clicked:
        st.session_state.running = True
        st.session_state.prev_gray = None
        st.session_state.last_call_time = 0.0

        # Create or re-create the capture device
        if st.session_state.cap is None or not st.session_state.cap.isOpened():
            st.session_state.cap = cv2.VideoCapture(int(camera_index))

        if not st.session_state.cap.isOpened():
            st.error("Could not open webcam. Check permissions and camera index.")
            st.session_state.running = False

    if stop_clicked:
        st.session_state.running = False
        if st.session_state.cap is not None:
            try:
                st.session_state.cap.release()
            except Exception:
                pass
        st.session_state.cap = None
        st.session_state.prev_gray = None
        st.session_state.alert_text = ""

    frame_slot = st.empty()
    status_slot = st.empty()
    intensity_slot = st.empty()
    alert_slot = st.empty()

    if st.session_state.running and st.session_state.cap is not None:
        cap = st.session_state.cap

        # Process frames until user presses Stop (Streamlit reruns on button click, canceling this loop).
        while st.session_state.running:
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to read from webcam.")
                st.session_state.running = False
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            motion_intensity, triggered = accident_app.detect_motion(
                prev_gray=st.session_state.prev_gray,
                gray=gray,
                motion_threshold=int(motion_threshold),
                diff_threshold=int(diff_threshold),
            )
            st.session_state.prev_gray = gray

            status = "ACCIDENT DETECTED" if triggered else "SAFE"
            status_color = "red" if triggered else "green"
            status_slot.markdown(
                f"**Status:** <span style='color:{status_color}; font-size: 22px;'>{status}</span>",
                unsafe_allow_html=True,
            )
            intensity_slot.metric("Motion intensity", int(motion_intensity))

            # Alert message + emergency call (cooldown protected)
            now = time.time()
            if triggered and (now - st.session_state.last_call_time) >= cooldown_seconds:
                st.session_state.last_call_time = now
                st.session_state.alert_text = "Accident detected! Sending alert..."
                alert_slot.warning(st.session_state.alert_text)

                threading.Thread(
                    target=accident_app.agent_call,
                    kwargs={
                        "reason": "Accident detected. Please call emergency services.",
                        "motion_intensity": int(motion_intensity),
                    },
                    daemon=True,
                ).start()

            if not triggered:
                st.session_state.alert_text = ""
                alert_slot.empty()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_slot.image(frame_rgb, channels="RGB")

            time.sleep(0.03)


if __name__ == "__main__":
    main()


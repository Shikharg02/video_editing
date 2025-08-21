import streamlit as st
from moviepy import VideoFileClip, CompositeVideoClip, TextClip
import tempfile
import os
import gc
import time
from io import BytesIO

st.set_page_config(page_title="Video Timer Overlay", layout="centered")
st.title("⏱️ MoviePy Video Timer Overlay")

# Sidebar controls
st.sidebar.header("Timer Settings")

mode = st.sidebar.radio("Position Mode", ["Absolute (top/bottom, left/right)", "Relative (%)"])
if mode == "Absolute (top/bottom, left/right)":
    vpos = st.sidebar.selectbox("Vertical", ["top", "bottom"])
    hpos = st.sidebar.selectbox("Horizontal", ["left", "right"])
    pos, relative = (hpos, vpos), False
else:
    x = st.sidebar.slider("Horizontal %", 0, 100, 0)
    y = st.sidebar.slider("Vertical %", 0, 100, 90)
    pos, relative = (x / 100, y / 100), True

font_size = st.sidebar.selectbox("Font Size", [24, 36, 48, 60, 72], 2)
font_color = st.sidebar.color_picker("Font Color", "#FFFFFF")
bg_opt = st.sidebar.selectbox("Background", ["Transparent", "White", "Black", "Red", "Green", "Blue"])
bg_color = None if bg_opt == "Transparent" else bg_opt.lower()
w, h = map(int, st.sidebar.selectbox("Box Size", ["300x60", "400x80", "500x100", "600x120"], 0).split("x"))
interval = {"Every Second": 1, "Every 5 Seconds": 5, "Every 10 Seconds": 10, "Every Minute": 60}[
    st.sidebar.selectbox("Update Interval", list({"Every Second": 1, "Every 5 Seconds": 5,
                                                  "Every 10 Seconds": 10, "Every Minute": 60}.keys()), 0)
]

def timer_clip(t):
    h_, rem = divmod(int(t), 3600)
    m_, s_ = divmod(rem, 60)
    timer_text = f"{h_:02d}:{m_:02d}:{s_:02d}"
    return (
        TextClip(
            text=timer_text,
            font=None,
            font_size=font_size,
            color=font_color,
            bg_color=bg_color,
            method="caption",
            size=(w, h),
            duration=interval
        )
        .with_start(t)
        .with_position(pos, relative=relative)
    )

def overlay_timer_on_video(inp_path: str) -> BytesIO:
    """Return processed video in BytesIO, temp files always cleaned."""
    # Create truly unused output path to avoid handle issues on Windows
    fd, out_path = tempfile.mkstemp(suffix=".mp4"); os.close(fd)

    # Process video
    video = VideoFileClip(inp_path)
    times = range(0, int(video.duration), interval)
    comp = CompositeVideoClip([video] + [timer_clip(t) for t in times])
    comp.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=video.fps)
    comp.close()
    video.close()
    gc.collect()
    time.sleep(0.2)

    # Read to memory
    with open(out_path, "rb") as f:
        buf = BytesIO(f.read())

    # Robust attempt to delete output temp file (retry if needed)
    for _ in range(10):
        try:
            os.remove(out_path)
            break
        except PermissionError:
            time.sleep(0.1)
    else:
        st.warning("Could not delete temp output file (still in use). OS will clean up later.")

    return buf

uploaded = st.file_uploader("Upload video", ["mp4", "avi", "mov", "mkv"])
if uploaded:
    # Save upload to temp, close handle immediately!
    inp_fd, inp_path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(inp_fd, "wb") as f: f.write(uploaded.read())
    st.video(inp_path)  # Optional preview

    if st.button("Generate Video with Timer"):
        with st.spinner("Processing…"):
            video_bytes = overlay_timer_on_video(inp_path)
        # Clean input (output already deleted in overlay function)
        for _ in range(10):
            try:
                os.remove(inp_path)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            st.warning("Could not delete temp input file (still in use). OS will clean up later.")

        st.success("Done! Download below ⬇️")
        st.download_button(
            "Download Edited Video",
            video_bytes,
            file_name="video_with_timer.mp4",
            mime="video/mp4"
        )

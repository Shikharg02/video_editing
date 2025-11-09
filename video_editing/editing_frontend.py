import streamlit as st
from moviepy import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.MultiplySpeed import MultiplySpeed

import tempfile
import os
import gc
import time
from io import BytesIO

st.set_page_config(page_title="Video Timer Overlay Editor", layout="centered")
st.title("⏱️ MoviePy Video Timer Overlay")

st.sidebar.header("Feature Selection")
add_timer = st.sidebar.selectbox("Add Timer Overlay?", ["Yes", "No"]) == "Yes"

# Only show timer options if enabled:
if add_timer:
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
else:
    overlay_interval = None # For clarity

add_fastforward = st.sidebar.header("Fast Forward (Speed/Duration)?", ["None", "1x", "1.5x", "2x", "3x", "4x", "Custom Duration"])
if add_fastforward == "Custom Duration":
    user_final_duration = st.sidebar.number_input(
        "Final video duration (seconds):",
        min_value=1, max_value=100000, value=30
    )
    set_custom_duration = True
elif add_fastforward == "None" or add_fastforward == "1x":
    set_custom_duration = False
    speed_factor = 1.0
    user_final_duration = None
else:
    set_custom_duration = False
    speed_factor = float(add_fastforward.replace("x", ""))

def timer_clip(t, txt, interval, pos, relative, font_size, font_color, bg_color, w, h):
    return (
        TextClip(text=txt, font=None, font_size=font_size, color=font_color,
                 bg_color=bg_color, method="caption", size=(w, h), duration=interval)
        .with_start(t)
        .with_position(pos, relative=relative)
    )

def overlay_timer_on_video(inp_path: str) -> BytesIO:
    fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    video = VideoFileClip(inp_path)
    orig_duration = video.duration

    # === Fast Forwarding / Custom Duration ===
    if set_custom_duration and user_final_duration:
        video = MultiplySpeed(final_duration=user_final_duration).apply(video)
        factor = orig_duration / user_final_duration
        final_duration = user_final_duration
    elif not set_custom_duration and (add_fastforward != "None" and add_fastforward != "1x"):
        video = MultiplySpeed(factor=speed_factor).apply(video)
        factor = speed_factor
        final_duration = orig_duration / speed_factor
    else:
        factor = 1.0
        final_duration = orig_duration

    # === Timer Overlay Logic ===
    timer_clips = []
    if add_timer:
        interval_on_fast = 0.01  # 10 ms update interval for super smooth timer
        times = []
        t = 0.0
        while t < final_duration:
            times.append(t)
            t += interval_on_fast
        if not times or times[-1] < final_duration:
            times.append(final_duration)
        for t in times:
            shown_timer_val = t * factor
            h_, rem = divmod(int(shown_timer_val), 3600)
            m_, s_ = divmod(rem, 60)
            if interval_on_fast < 1:
                # Show decimal fractions if needed
                txt = f"{h_:02d}:{m_:02d}:{s_:02d}"
            else:
                txt = f"{h_:02d}:{m_:02d}:{s_:02d}"
            timer_clips.append(
                timer_clip(
                    t, txt, interval=interval_on_fast,
                    pos=pos, relative=relative, font_size=font_size,
                    font_color=font_color, bg_color=bg_color, w=w, h=h
                )
            )

    # Compose final video
    clips = [video] + timer_clips if timer_clips else [video]
    comp = CompositeVideoClip(clips)
    comp.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=video.fps)

    comp.close()
    video.close()
    gc.collect()
    time.sleep(0.2)
    with open(out_path, "rb") as f:
        buf = BytesIO(f.read())
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
    inp_fd, inp_path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(inp_fd, "wb") as f: f.write(uploaded.read())
    st.video(inp_path)

    if st.button("Generate Video"):
        with st.spinner("Processing…"):
            video_bytes = overlay_timer_on_video(inp_path)
        # Clean input file
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

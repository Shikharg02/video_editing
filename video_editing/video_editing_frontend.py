import gc
import os
import tempfile
import time
from io import BytesIO

import streamlit as st
from moviepy import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.MultiplySpeed import MultiplySpeed

st.set_page_config(page_title="Video Timer Overlay Editor", layout="centered")
st.title("⏱️ MoviePy Video Timer Overlay")

st.sidebar.header("Feature Selection")
add_timer = st.sidebar.selectbox("Add Timer Overlay", ["Yes", "No"]) == "Yes"

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
    overlay_interval = None  # For clarity

st.sidebar.header("Fast Forward")
add_fastforward = st.sidebar.selectbox("Choose", ["None", "1x", "1.5x", "2x", "3x", "4x", "Custom Duration"])

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


def _format_hms(total_seconds: float) -> str:
    """
    Format seconds -> HH:MM:SS.
    """
    if total_seconds < 0:
        total_seconds = 0.0
    total_int = int(total_seconds)
    h = total_int // 3600
    m = (total_int % 3600) // 60
    s = total_int % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def timer_clip(t, txt, interval, pos, relative, font_size, font_color, bg_color, w, h):
    """
    Create a TextClip that already has duration set (so we don't call set_duration later).
    """
    tc = TextClip(
        text=txt,
        font=None,
        font_size=font_size,
        color=font_color,
        bg_color=bg_color,
        method="caption",
        size=(w, h),
        duration=interval
    )
    return tc.with_start(t).with_position(pos, relative=relative)


def overlay_timer_on_video(inp_path: str) -> BytesIO:
    fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    try:
        video = VideoFileClip(inp_path)
        orig_duration = video.duration if video.duration and video.duration > 0 else 0.0

        # === Fast Forwarding / Custom Duration ===
        if set_custom_duration and user_final_duration:
            video = MultiplySpeed(final_duration=user_final_duration).apply(video)
            factor = orig_duration / user_final_duration if user_final_duration else 1.0
            final_duration = user_final_duration
        elif not set_custom_duration and (add_fastforward != "None" and add_fastforward != "1x"):
            video = MultiplySpeed(factor=speed_factor).apply(video)
            factor = speed_factor
            final_duration = orig_duration / speed_factor if speed_factor != 0 else orig_duration
        else:
            factor = 1.0
            final_duration = orig_duration

        # Protect against weird durations
        if final_duration <= 0:
            final_duration = orig_duration or 0.1
            factor = 1.0

        # === Timer Overlay Logic ===
        timer_clips = []
        if add_timer:
            # Timer overlay frequency reduced for much less memory/CPU usage
            fps = int(round(video.fps)) if video.fps else 24
            interval_on_fast = max(0.5, 1.0 / max(1, fps))

            times = []
            t = 0.0
            max_frames = int(min(final_duration / interval_on_fast, 5000))
            frame_count = 0
            while frame_count < max_frames and t < final_duration - 1e-8:
                times.append(t)
                frame_count += 1
                t = frame_count * interval_on_fast

            if not times or times[-1] + 1e-8 < final_duration:
                times.append(final_duration)

            for t in times:
                shown_timer_val = t * factor
                txt = _format_hms(shown_timer_val)
                tc = timer_clip(
                    t, txt, interval=interval_on_fast,
                    pos=pos, relative=relative, font_size=font_size,
                    font_color=font_color, bg_color=bg_color, w=w, h=h
                )
                timer_clips.append(tc)

        clips = [video] + timer_clips if timer_clips else [video]
        comp = CompositeVideoClip(clips)
        # Use video's fps to write
        write_fps = int(round(video.fps)) if video.fps else 24

        try:
            comp.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=write_fps)
        except Exception as e:
            st.error(f"Video encoding error: {e}")
            raise

        try:
            comp.close()
        except Exception:
            pass
        try:
            video.close()
        except Exception:
            pass
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
    except Exception as e:
        # === FIX: Ensure resource cleanup on any crash ===
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except Exception:
            pass
        raise e

uploaded = st.file_uploader("Upload video", ["mp4", "avi", "mov", "mkv"])
if uploaded:
    inp_fd, inp_path = tempfile.mkstemp(suffix=".mp4")
    with os.fdopen(inp_fd, "wb") as f:
        f.write(uploaded.read())
    st.video(inp_path)

    if st.button("Generate Video"):
        with st.spinner("Processing…"):
            try:
                video_bytes = overlay_timer_on_video(inp_path)
            except Exception as e:
                st.error(f"Processing failed: {str(e)}")  # FIXED: show clear error for all platforms
                video_bytes = None

        for _ in range(10):
            try:
                os.remove(inp_path)
                break
            except PermissionError:
                time.sleep(0.1)
        else:
            st.warning("Could not delete temp input file (still in use). OS will clean up later.")

        if video_bytes:
            st.success("Done! Download below ⬇️")
            st.download_button(
                "Download Edited Video",
                video_bytes,
                file_name="video_with_timer.mp4",
                mime="video/mp4"
            )
else:
    st.info("Upload a video to start.")

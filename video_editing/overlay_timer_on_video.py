"""
MoviePy is a Python module for video editing that enables complex operations such as compositing, transformations,
text/image overlays, audio editing, and exporting in various formats—all via a concise and Pythonic API.

Core features used in this script:
- Video loading and reading using VideoFileClip.
- Minute-interval timer overlays using TextClip for dynamic, transparent text creation.
- Non-destructive compositing of clips using CompositeVideoClip.
- Exporting the edited video with codec and audio settings preserved.

Requires: moviepy>=2.2, Python 3.10+
Documentation: https://zulko.github.io/moviepy/

Example usage:
    $ python this_script.py

This script does NOT change frame rate, codec, or duration of the original video except for adding the visible
on-screen timer overlay.

Installation:
pip install moviepy
"""
from moviepy import VideoFileClip, CompositeVideoClip, TextClip


def create_timer_clip(start_time):
    """
    Create a timer TextClip representing elapsed hours and minutes.

    Args:
        start_time (int): Time offset in seconds for when this timer should appear.

    Returns:
        TextClip: Configured text overlay for the timer.
    """
    hours, remaining_secs = divmod(int(start_time), 3600)       # Extract hours and remainder seconds
    minutes = remaining_secs // 60                              # Get whole minutes from remainder
    seconds = remaining_secs % 60                               # Get seconds
    timer_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"     # Format timer as HH:MM:SS

    return (
        TextClip(
            text=timer_text,
            font=None,          # Use default system font
            font_size=48,
            color="white",      # timer_text color
            bg_color=None,      # Transparent background; "white", "black" e.t.c.
            method="caption",
            size=(300, 60),     # width and height of caption; adjust as you need
            duration=1         # Each timer clip appears for 1 seconds
        )
        .with_start(start_time)
        .with_position((0, 0.9), relative=True)  # Place near bottom-left, slightly above the edge
        # with_position((left %age, right %age), relative=True)
        # can also use with_position(("left", "bottom"))
    )


def overlay_timer_on_video(input_video_path, output_video_path):
    """
    Overlay a minute-updating timer on the original video and export the result.

    Args:
        input_video_path (str): Path to the input video file.
    """
    video = VideoFileClip(input_video_path)
    total_duration = int(video.duration)
    timer_intervals = range(0, total_duration, 1)  # Timer updates every minute(1s interval)

    timer_clips = [create_timer_clip(t) for t in timer_intervals]
    composite = CompositeVideoClip([video] + timer_clips)

    composite.write_videofile(
        output_video_path,
        codec="libx264",
        audio_codec="aac",
        fps=video.fps
    )


if __name__ == "__main__":
    # Uncomment below for standalone TextClip PNG test:
    # test_clip = TextClip(
    #     text="00:00",
    #     font=None,
    #     font_size=48,
    #     color="white",
    #     bg_color="black",
    #     method="caption",
    #     size=(300, 60),
    #     duration=60
    # )
    # test_clip.save_frame("test_text_clip.png")

    # Input video file path
    input_video_path = "Imagine for 1 Minute.mp4"
    output_video_path = "Imagine.mp4"
    overlay_timer_on_video(input_video_path, output_video_path)

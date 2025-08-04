# 🎬 MoviePy Video Timer Overlay

Overlay a live timer (**HH:MM:SS**) on any video using Python—automatically, flexibly, and with zero manual editing!

This script leverages the [MoviePy](https://zulko.github.io/moviepy/) library to perform open-source, programmatic video editing:
- **No manual timeline dragging**
- **No external editors**
- **100% code controlled**

---

## ✨ Features

- **Universal Timer Overlay:** Add a timer (minutes, seconds, or both) to *any* video.
- **Transparent, Customizable Text:** Set font size, color, and position for your overlay.
- **Easy Format Tweaks:** Show hours/minutes/seconds—configure as you wish in a single line.
- **Non-Destructive:** Keeps your original video & audio intact.
- **Beginner-Friendly:** Clearly commented Python code.

---

## 🚀 Getting Started

### 1️⃣ Install Requirements
- pip install moviepy


---

## 🖼 Example

| **Original Video** |

<img src = "https://github.com/Shikharg02/video_editing/blob/master/video_editing/original_video.png" width = "600px" height = "400px">


| **Video with Timer Overlay** |

<img src = "https://github.com/Shikharg02/video_editing/blob/master/video_editing/overlay_timer_on_video.png" width = "600px" height = "400px">


---

## 🛠 Customization

- **Timer Frequency:**  
  Edit the timer interval in `range(0, total_duration, 60)` — change `60` to `1` for seconds, or customize as needed.
- **Overlay Style:**  
  Change font, color, or background in the `TextClip` arguments.
- **Position:**  
  Adjust `.with_position((0, 0.9), relative=True)` for precise control (e.g., left, right, center, or any percentage).

---

## 📚 References

- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- *Tested with Python 3.10+*

---

## 💡 Why?
A timer overlay is invaluable for educational, productivity, fitness, tutorial, and presentation videos—any context where viewers benefit from tracking elapsed or remaining time.

---

**Enjoy, share, and contribute!**  
For questions or improvements, please open an Issue or Pull Request.

---

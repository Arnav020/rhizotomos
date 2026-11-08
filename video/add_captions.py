"""Burn styled captions into the pitch video. Timing: each segment's narration starts 0.3 s in and
sentences are timed in proportion to their length within the segment's audio duration."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from make_video import SCRIPT, B, V, dur  # noqa: E402


def ts(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


events, t0 = [], 0.0
for name, text in SCRIPT:
    audio = dur(B / f"{name}.wav")
    seg = dur(B / f"seg_{name}.mp4")
    chunks = []
    for s in re.split(r"(?<=[.?!])\s+", text):
        words = s.split()
        while len(words) > 14:  # keep each caption to two short lines
            cut = 12
            chunks.append(" ".join(words[:cut])); words = words[cut:]
        chunks.append(" ".join(words))
    total = sum(len(c) for c in chunks)
    t = t0 + 0.3
    for c in chunks:
        d = audio * len(c) / total
        events.append((t, t + d - 0.05, c))
        t += d
    t0 += seg

ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Segoe UI Semibold,40,&H00E6EFF4,&H00E6EFF4,&H00111111,&HD0111111,0,0,0,0,100,100,0,0,3,18,0,2,260,260,64,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ass += "".join(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{c}\n" for a, b, c in events)
(B / "captions.ass").write_text(ass, encoding="utf-8")
src, out = V / "Rhizotomos_pitch.mp4", V / "Rhizotomos_pitch_captioned.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", "ass=captions.ass",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "copy", str(out)], check=True, cwd=B)
print("captioned:", out, len(events), "captions")

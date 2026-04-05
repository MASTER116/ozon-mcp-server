#!/usr/bin/env python3
"""
Convert asciicast v2 (.cast) to animated GIF using Pillow.

Usage:
    python scripts/cast_to_gif.py [demo.cast] [demo.gif]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Colors (Dracula-inspired terminal theme)
COLORS = {
    "bg": (40, 42, 54),
    "fg": (248, 248, 242),
    "black": (40, 42, 54),
    "red": (255, 85, 85),
    "green": (80, 250, 123),
    "yellow": (241, 250, 140),
    "blue": (98, 114, 164),
    "magenta": (255, 121, 198),
    "cyan": (139, 233, 253),
    "white": (248, 248, 242),
    "bright_white": (255, 255, 255),
    "dim": (150, 150, 160),
}

ANSI_MAP = {
    "32": "green",
    "33": "yellow",
    "36": "cyan",
    "97": "bright_white",
    "2": "dim",
    "0": "fg",
}


def parse_ansi(text: str) -> list[tuple[str, str]]:
    """Parse ANSI-colored text into (text, color_name) segments."""
    segments: list[tuple[str, str]] = []
    current_color = "fg"
    parts = re.split(r"\033\[([0-9;]+)m", text)

    i = 0
    while i < len(parts):
        if i % 2 == 0:
            # Text content
            clean = parts[i]
            if clean:
                segments.append((clean, current_color))
        else:
            # ANSI code
            codes = parts[i].split(";")
            for code in codes:
                if code in ANSI_MAP:
                    current_color = ANSI_MAP[code]
                elif code == "1":
                    pass  # bold — keep current color
        i += 1

    return segments


def render_frame(
    lines: list[str],
    width: int,
    height: int,
    font: ImageFont.FreeTypeFont,
    char_w: int,
    char_h: int,
) -> Image.Image:
    """Render terminal lines to an image."""
    padding = 16
    title_bar = 36
    img_w = width * char_w + padding * 2
    img_h = height * char_h + padding * 2 + title_bar

    img = Image.new("RGB", (img_w, img_h), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, img_w, title_bar], fill=(30, 32, 44))
    # Window buttons
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([12 + i * 22, 10, 26 + i * 22, 24], fill=color)
    # Title text
    draw.text((img_w // 2 - 100, 8), "Ozon Seller MCP Server", fill=COLORS["dim"], font=font)

    # Terminal content
    y = title_bar + padding
    for line in lines[-height:]:
        x = padding
        segments = parse_ansi(line)
        for text, color_name in segments:
            color = COLORS.get(color_name, COLORS["fg"])
            draw.text((x, y), text, fill=color, font=font)
            x += len(text) * char_w
        y += char_h

    return img


def main() -> None:
    cast_path = sys.argv[1] if len(sys.argv) > 1 else "demo.cast"
    gif_path = sys.argv[2] if len(sys.argv) > 2 else "demo.gif"

    # Load cast file
    with open(cast_path, encoding="utf-8") as f:
        lines_raw = f.readlines()

    header = json.loads(lines_raw[0])
    events = [json.loads(line) for line in lines_raw[1:]]

    cols = header.get("width", 100)
    rows = header.get("height", 35)

    # Load monospace font
    try:
        font = ImageFont.truetype("consola.ttf", 14)
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
        except OSError:
            font = ImageFont.load_default()

    char_w = 8
    char_h = 18

    # Build frames by grouping events
    terminal_lines: list[str] = []
    current_text = ""
    frames: list[tuple[Image.Image, int]] = []  # (image, duration_ms)

    # Group events into frames (every ~0.3s or on newline)
    frame_events: list[list[tuple[float, str]]] = []
    current_group: list[tuple[float, str]] = []
    last_ts = 0.0

    for ts, etype, data in events:
        if etype != "o":
            continue
        if ts - last_ts > 0.25 and current_group:
            frame_events.append(current_group)
            current_group = []
        current_group.append((ts, data))
        last_ts = ts

    if current_group:
        frame_events.append(current_group)

    # Render each frame group
    for i, group in enumerate(frame_events):
        for ts, data in group:
            for char in data:
                if char == "\r":
                    continue
                elif char == "\n":
                    terminal_lines.append(current_text)
                    current_text = ""
                else:
                    current_text += char

        # Add current partial line
        display_lines = terminal_lines.copy()
        if current_text:
            display_lines.append(current_text)

        frame_img = render_frame(display_lines, cols, rows, font, char_w, char_h)

        # Duration: time until next group (or 2s for last frame)
        if i < len(frame_events) - 1:
            next_ts = frame_events[i + 1][0][0]
            duration_ms = max(int((next_ts - group[-1][0]) * 1000), 50)
        else:
            duration_ms = 3000

        # Cap max frame duration
        duration_ms = min(duration_ms, 2000)

        frames.append((frame_img, duration_ms))
        sys.stdout.write(f"\rRendering frame {i + 1}/{len(frame_events)}...")
        sys.stdout.flush()

    print(f"\nSaving GIF ({len(frames)} frames)...")

    # Save as animated GIF
    if frames:
        images = [f[0] for f in frames]
        durations = [f[1] for f in frames]
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=0,
            optimize=True,
        )

        size_mb = Path(gif_path).stat().st_size / (1024 * 1024)
        print(f"Done! {gif_path} ({size_mb:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    main()

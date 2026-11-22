#!/usr/bin/env python3
"""Build static/assets/demo-preview.gif from the captured UI screenshots.

    python3 scripts/make_preview.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "assets"
FRAME_SIZE = (960, 602)
CAPTIONS = [
    "BEEJAK · REVENUE LEDGER · LIVE KPIs",
    "LIVE A4 SPLIT STUDIO · GST + UPI QR",
    "BEEJAK PAY SANDBOX · INSTANT PAID STAMP",
]
FILES = ["screenshot-dashboard.png", "screenshot-builder.png", "screenshot-checkout.png"]


def load_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build() -> None:
    font = load_font(19)
    small = load_font(13)
    frames = []
    for filename, caption in zip(FILES, CAPTIONS):
        source = ASSETS / filename
        if not source.exists():
            raise SystemExit(f"Missing screenshot: {source}")
        original = Image.open(source).convert("RGB")
        for step in range(4):
            zoom = 1.0 + step * 0.02
            width, height = original.size
            crop_w, crop_h = int(width / zoom), int(height / zoom)
            left = int((width - crop_w) * (step / 8))
            top = int((height - crop_h) * (step / 10))
            cropped = original.crop((left, top, left + crop_w, top + crop_h))
            frame = ImageOps.fit(cropped, FRAME_SIZE, method=Image.Resampling.LANCZOS)

            overlay = Image.new("RGBA", FRAME_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            draw.rectangle((0, 0, FRAME_SIZE[0], 48), fill=(7, 11, 20, 226))
            draw.rectangle((0, FRAME_SIZE[1] - 42, FRAME_SIZE[0], FRAME_SIZE[1]), fill=(7, 11, 20, 226))
            draw.text((18, 12), caption, font=font, fill=(16, 185, 129, 255))
            draw.text((18, FRAME_SIZE[1] - 31),
                      "Raj Gautam • Jaunpur, UP  |  github.com/Rg100152",
                      font=small, fill=(200, 212, 230, 255))
            frames.append(Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB"))

    output = ASSETS / "demo-preview.gif"
    frames[0].save(
        output, save_all=True, append_images=frames[1:],
        duration=[600] + [230] * (len(frames) - 1), loop=0, optimize=True,
    )
    print(f"Wrote {output} ({len(frames)} frames)")


if __name__ == "__main__":
    build()

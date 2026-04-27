"""Rebuild icon.ico from assets/app_icon.png (run from repo root: python scripts/make_icon.py)."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "app_icon.png"
OUT = ROOT / "icon.ico"


def main():
    im = Image.open(SRC).convert("RGBA")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [im.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
    imgs[0].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=imgs[1:],
    )
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

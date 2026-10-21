# -*- coding: utf-8 -*-
"""maak_icoon.py - maakt de iconen voor DraveRace uit assets/logo.png.

Levert:
  assets/logo_t.png - zilveren draak op transparant (voor splash/titel op donker)
  assets/logo.ico   - app-icoon (donkere tegel + staalblauwe rand + zilveren draak)
  assets/app.ico    - zelfde icoon (alias, voor de PyInstaller-spec)
Alleen Pillow nodig.
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

BG_TILE = (22, 22, 27, 255)     # donkere paneelkleur
BORDER = (111, 163, 214, 255)   # staalblauw accent
SILVER = (216, 216, 222, 255)   # zilveren draak


def _load_logo():
    p = os.path.join(ASSETS, "logo.png")
    return Image.open(p).convert("RGBA")


def _silver_dragon(src, size):
    """Maak een nette zilveren draak op transparant: dekkende lijnen, licht
    verdikt zodat het stevig oogt (geen vage streepjes), netjes bijgesneden."""
    import numpy as np
    from PIL import ImageFilter
    # eerst de buitenrand van de bron wegsnijden (daar zit een dun kaderlijntje)
    w0, h0 = src.size
    m = int(min(w0, h0) * 0.07)
    src = src.crop((m, m, w0 - m, h0 - m))
    g = src.convert("L")
    arr = np.asarray(g).astype(np.float32)
    # donker -> dekkend; lichte achtergrond/vage kaderlijnen -> weg
    thr = 190.0
    alpha = np.clip((thr - arr) / thr * 255.0 * 2.2, 0.0, 255.0).astype("uint8")
    a_img = Image.fromarray(alpha, mode="L")
    # iets verdikken + zachte randen voor een stevige, strakke look
    a_img = a_img.filter(ImageFilter.MaxFilter(3))
    a_img = a_img.filter(ImageFilter.GaussianBlur(0.6))
    alpha = np.asarray(a_img)
    h, w = alpha.shape
    out = np.zeros((h, w, 4), dtype="uint8")
    out[..., 0] = SILVER[0]
    out[..., 1] = SILVER[1]
    out[..., 2] = SILVER[2]
    out[..., 3] = alpha
    out_img = Image.fromarray(out, "RGBA")
    # bijsnijden op de duidelijke draak (negeer hele zwakke pixels)
    mask = Image.fromarray((alpha > 50).astype("uint8") * 255, "L")
    bbox = mask.getbbox()
    if bbox:
        out_img = out_img.crop(bbox)
    out_img = out_img.resize((size, size), Image.LANCZOS)
    return out_img


def _rounded_tile(size, radius_frac=0.18):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(size * radius_frac)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=BG_TILE)
    bw = max(2, size // 22)
    d.rounded_rectangle([bw // 2, bw // 2, size - 1 - bw // 2, size - 1 - bw // 2],
                        radius=r, outline=BORDER, width=bw)
    return im


def main():
    os.makedirs(ASSETS, exist_ok=True)
    src = _load_logo()

    # 1) zilveren draak op transparant (splash)
    drag = _silver_dragon(src, 512)
    drag.save(os.path.join(ASSETS, "logo_t.png"))
    print("Geschreven: assets/logo_t.png")

    # 2) app-icoon (meerdere resoluties)
    sizes = [256, 128, 64, 48, 32, 16]
    frames = []
    for s in sizes:
        tile = _rounded_tile(s)
        inner = int(s * 0.7)
        d = _silver_dragon(src, inner)
        off = (s - inner) // 2
        tile.alpha_composite(d, (off, off))
        frames.append(tile)
    ico_path = os.path.join(ASSETS, "logo.ico")
    frames[0].save(ico_path, format="ICO",
                   sizes=[(s, s) for s in sizes])
    print("Geschreven: assets/logo.ico")
    frames[0].save(os.path.join(ASSETS, "app.ico"), format="ICO",
                   sizes=[(s, s) for s in sizes])
    print("Geschreven: assets/app.ico")

    # PNG-versie van het icoon voor het spelvenster (titelbalk)
    frames[0].save(os.path.join(ASSETS, "app_icon.png"))
    print("Geschreven: assets/app_icon.png")


if __name__ == "__main__":
    main()

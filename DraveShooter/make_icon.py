# -*- coding: utf-8 -*-
"""Icoon voor DraveShooter (kruisvizier + doel) met Pillow -> geldig ICO."""
import os
from PIL import Image, ImageDraw

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def draw(sz):
    k = sz / 256.0
    im = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, sz - 1, sz - 1], int(46 * k),
                        fill=(34, 26, 48, 255), outline=(150, 90, 60, 255),
                        width=int(6 * k))
    cx = cy = int(128 * k)
    # doel (ringen)
    for r, c in [(78, (230, 90, 80)), (54, (245, 245, 245)),
                 (30, (230, 90, 80)), (12, (245, 245, 245))]:
        rr = int(r * k)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=c + (255,))
    # kruisvizier
    g = (90, 230, 130, 255)
    wq = int(7 * k)
    for (x0, y0, x1, y1) in [(cx - int(105 * k), cy - wq, cx - int(40 * k), cy + wq),
                             (cx + int(40 * k), cy - wq, cx + int(105 * k), cy + wq),
                             (cx - wq, cy - int(105 * k), cx + wq, cy - int(40 * k)),
                             (cx - wq, cy + int(40 * k), cx + wq, cy + int(105 * k))]:
        d.rectangle([x0, y0, x1, y1], fill=g)
    return im


for n in (256, 64):
    draw(n).save(os.path.join(ASSETS, "icon-%d.png" % n))
draw(256).save(os.path.join(ASSETS, "icon.ico"), format="ICO", sizes=SIZES)
print("icons done")

# -*- coding: utf-8 -*-
"""Maakt het icoon voor DraveJump (vrolijke mascotte) met Pillow -> geldig ICO."""
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
                        fill=(80, 140, 210, 255), outline=(40, 80, 140, 255),
                        width=int(6 * k))
    body = (245, 140, 60, 255)
    # body
    d.ellipse([int(70 * k), int(120 * k), int(186 * k), int(220 * k)], fill=body)
    # head
    d.ellipse([int(74 * k), int(50 * k), int(182 * k), int(150 * k)], fill=body)
    # ears
    d.ellipse([int(60 * k), int(56 * k), int(96 * k), int(92 * k)], fill=body)
    d.ellipse([int(160 * k), int(56 * k), int(196 * k), int(92 * k)], fill=body)
    # eyes
    for ex in (108, 148):
        d.ellipse([int((ex - 16) * k), int(78 * k), int((ex + 16) * k),
                   int(110 * k)], fill=(255, 255, 255, 255))
        d.ellipse([int((ex - 6) * k), int(90 * k), int((ex + 8) * k),
                   int(108 * k)], fill=(20, 20, 30, 255))
    # snout
    d.ellipse([int(116 * k), int(110 * k), int(140 * k), int(130 * k)],
              fill=(230, 110, 40, 255))
    return im


for n in (256, 64):
    draw(n).save(os.path.join(ASSETS, "icon-%d.png" % n))
draw(256).save(os.path.join(ASSETS, "icon.ico"), format="ICO", sizes=SIZES)
print("icons done")

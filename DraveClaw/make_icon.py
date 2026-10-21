# -*- coding: utf-8 -*-
"""Maakt het icoon voor DraveClaw (een grijpklauw)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

pygame.init()
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)


def draw(sz):
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    k = sz / 256.0
    pygame.draw.rect(s, (18, 22, 38), (0, 0, sz, sz), border_radius=int(46 * k))
    pygame.draw.rect(s, (50, 90, 130), (0, 0, sz, sz), int(6 * k),
                     border_radius=int(46 * k))
    cx = int(128 * k)
    # kabel
    pygame.draw.rect(s, (150, 155, 165), (cx - int(5 * k), int(34 * k),
                                          int(10 * k), int(60 * k)))
    # body
    pygame.draw.rect(s, (210, 215, 225), (cx - int(34 * k), int(90 * k),
                                          int(68 * k), int(30 * k)),
                     border_radius=int(8 * k))
    # drie vingers
    col = (180, 188, 200)
    pygame.draw.polygon(s, col, [(cx - int(28 * k), int(118 * k)),
                                 (cx - int(60 * k), int(180 * k)),
                                 (cx - int(44 * k), int(186 * k)),
                                 (cx - int(16 * k), int(120 * k))])
    pygame.draw.polygon(s, col, [(cx + int(28 * k), int(118 * k)),
                                 (cx + int(60 * k), int(180 * k)),
                                 (cx + int(44 * k), int(186 * k)),
                                 (cx + int(16 * k), int(120 * k))])
    pygame.draw.rect(s, col, (cx - int(8 * k), int(118 * k),
                              int(16 * k), int(74 * k)),
                     border_radius=int(4 * k))
    # prijs (bal)
    pygame.draw.circle(s, (240, 200, 60), (cx, int(196 * k)), int(20 * k))
    pygame.draw.circle(s, (150, 120, 20), (cx, int(196 * k)), int(20 * k),
                       int(3 * k))
    return s


for n in (256, 64):
    pygame.image.save(draw(n), os.path.join(ASSETS, "icon-%d.png" % n))
try:
    pygame.image.save(draw(256), os.path.join(ASSETS, "icon.ico"))
except Exception:
    pass
print("icons done")

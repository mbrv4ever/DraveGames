# -*- coding: utf-8 -*-
"""Maakt het icoon voor DraveMission (agent + codestuk op donker paneel)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

pygame.init()
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)


def draw(sz):
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    k = sz / 256.0
    # afgeronde donkere achtergrond
    pygame.draw.rect(s, (16, 20, 34), (0, 0, sz, sz),
                     border_radius=int(46 * k))
    pygame.draw.rect(s, (40, 48, 72), (0, 0, sz, sz), int(6 * k),
                     border_radius=int(46 * k))
    # vloer + platform (complex-sfeer)
    pygame.draw.rect(s, (54, 60, 82), (int(28 * k), int(196 * k),
                                       int(200 * k), int(20 * k)))
    pygame.draw.rect(s, (46, 52, 74), (int(132 * k), int(120 * k),
                                       int(96 * k), int(12 * k)))
    # agent
    ax, ay = int(86 * k), int(120 * k)
    pygame.draw.rect(s, (28, 38, 66), (ax + int(7 * k), ay + int(56 * k),
                                       int(10 * k), int(24 * k)))
    pygame.draw.rect(s, (28, 38, 66), (ax + int(27 * k), ay + int(56 * k),
                                       int(10 * k), int(24 * k)))
    pygame.draw.rect(s, (90, 150, 230), (ax + int(6 * k), ay + int(22 * k),
                                         int(34 * k), int(38 * k)),
                     border_radius=int(6 * k))
    pygame.draw.circle(s, (238, 214, 190),
                       (ax + int(23 * k), ay + int(12 * k)), int(13 * k))
    pygame.draw.rect(s, (18, 26, 52), (ax + int(13 * k), ay + int(8 * k),
                                       int(22 * k), int(8 * k)))
    # codestuk (geel)
    pygame.draw.rect(s, (240, 200, 60), (int(168 * k), int(150 * k),
                                         int(44 * k), int(44 * k)),
                     border_radius=int(6 * k))
    pygame.draw.rect(s, (120, 96, 20), (int(168 * k), int(150 * k),
                                        int(44 * k), int(44 * k)),
                     int(4 * k), border_radius=int(6 * k))
    pygame.draw.line(s, (120, 96, 20), (int(190 * k), int(150 * k)),
                     (int(190 * k), int(194 * k)), int(3 * k))
    return s


for n in (256, 64):
    pygame.image.save(draw(n), os.path.join(ASSETS, "icon-%d.png" % n))

ico = draw(256)
sizes = [16, 24, 32, 48, 64, 128, 256]
imgs = [pygame.transform.smoothscale(ico, (z, z)) for z in sizes]
try:
    pygame.image.save(imgs[-1], os.path.join(ASSETS, "icon.ico"))
except Exception:
    pass
print("icons done")

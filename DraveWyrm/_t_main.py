# -*- coding: utf-8 -*-
"""DraveWyrm - een 2D side-scroller waarin jij de Dravenlock-draak bent.

Vlieg met de pijltjestoetsen, adem vuur met de spatiebalk. Verschroei dorpen,
ontwijk pijlen van boogschutters, versla vijandelijke draken en verzamel goud.
Tweetalig NL/EN, procedurele audio, portable (alles in de app-map). Donationware.

Besturing: pijltjes = vliegen, spatie = vuur, P = pauze, Enter = start/opnieuw.
"""
import json
import locale
import math
import os
import random
import struct
import sys
import webbrowser
from array import array

import pygame

try:
    from pygame import gfxdraw
    HAS_GFX = True
except Exception:
    HAS_GFX = False

# ---------------------------------------------------------------- basis / paden
W, H = 960, 600
FPS = 60
GROUND_Y = H - 66
SR = 22050                      # audio sample rate


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def cache_dir():
    d = os.path.join(app_dir(), "cache")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _lang():
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _lang()
TX = {
    "title": {"nl": "DraveWyrm", "en": "DraveWyrm"},
    "sub": {"nl": "De draak van Dravenlock", "en": "The dragon of Dravenlock"},
    "start": {"nl": "Enter = start", "en": "Enter = start"},
    "ctrl": {"nl": "Pijltjes = vliegen    Spatie = vuur    P = pauze",
             "en": "Arrows = fly    Space = fire    P = pause"},
    "donate": {"nl": "D = doneren", "en": "D = donate"},
    "info": {"nl": "I = info", "en": "I = info"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "gold": {"nl": "Goud", "en": "Gold"},
    "dist": {"nl": "Afstand", "en": "Distance"},
    "level": {"nl": "Niveau", "en": "Level"},
    "best": {"nl": "Record", "en": "Best"},
    "paused": {"nl": "Pauze", "en": "Paused"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "gameover": {"nl": "Neergehaald!", "en": "Shot down!"},
    "retry": {"nl": "Enter = opnieuw", "en": "Enter = retry"},
    "menu": {"nl": "Esc = menu", "en": "Esc = menu"},
    "boss": {"nl": "Vijandelijke draak!", "en": "Enemy dragon!"},
    "levelup": {"nl": "Niveau %d", "en": "Level %d"},
    "info_txt": {
        "nl": "DraveWyrm - jij bent de Dravenlock-draak. Verschroei dorpen, "
              "ontwijk pijlen en versla vijandelijke draken.\n\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl",
        "en": "DraveWyrm - you are the Dravenlock dragon. Torch villages, "
              "dodge arrows and defeat enemy dragons.\n\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl"},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"

# --------------------------------------------------------------------- kleuren
SKY_TOP = (28, 20, 44)
SKY_BOT = (58, 40, 92)
PURPLE = (128, 94, 205)
PURPLE_D = (88, 62, 150)
PURPLE_L = (170, 140, 232)
BELLY = (206, 190, 240)
HORN = (238, 232, 250)
EYE = (255, 208, 66)
GOLDC = (255, 205, 70)
REDDR = (206, 78, 78)
REDDR_D = (150, 48, 52)
REDBELLY = (240, 196, 176)

# omgevingen per niveau: lucht (boven,onder), bergen (ver,dichtbij),
# grond (vlak, rand), grondlijn
BIOMES = [
    {"name": "dorp",    "sky": ((28, 20, 44), (58, 40, 92)),
     "mtn": ((46, 34, 70), (60, 44, 90)),
     "gnd": ((44, 32, 26), (66, 48, 36)), "line": (54, 40, 30)},
    {"name": "bergen",  "sky": ((24, 30, 54), (64, 78, 118)),
     "mtn": ((40, 50, 82), (58, 72, 108)),
     "gnd": ((40, 44, 52), (62, 68, 80)), "line": (52, 58, 70)},
    {"name": "kasteel", "sky": ((30, 28, 42), (74, 68, 92)),
     "mtn": ((52, 48, 66), (72, 66, 88)),
     "gnd": ((48, 44, 52), (72, 66, 76)), "line": (60, 54, 66)},
    {"name": "vulkaan", "sky": ((44, 18, 20), (104, 48, 30)),
     "mtn": ((64, 28, 26), (96, 46, 34)),
     "gnd": ((48, 26, 22), (78, 40, 28)), "line": (66, 34, 24)},
]

# power-up-kleuren
PU_COLORS = {"shield": (90, 180, 255), "triple": (255, 140, 50),
             "heart": (232, 80, 110), "magnet": (255, 205, 70)}


# --------------------------------------------------------- teken-hulpjes (glad)
def poly(surf, pts, color):
    ipts = [(int(round(x)), int(round(y))) for x, y in pts]
    if HAS_GFX and len(ipts) >= 3:
        try:
            gfxdraw.filled_polygon(surf, ipts, color)
            gfxdraw.aapolygon(surf, ipts, color)
            return
        except Exception:
            pass
    pygame.draw.polygon(surf, color, ipts)


def circ(surf, x, y, r, color):
    x, y, r = int(x), int(y), int(r)
    if HAS_GFX and r > 0:
        try:
            gfxdraw.filled_circle(surf, x, y, r, color)
            gfxdraw.aacircle(surf, x, y, r, color)
            return
        except Exception:
            pass
    pygame.draw.circle(surf, color, (x, y), r)


def _wing(surf, shoulder, flap, main, bone, facing=1):
    """Membraanvleugel; flap in -1..1 (omhoog..omlaag)."""
    sx, sy = shoulder
    tipx = sx - facing * 40
    tipy = sy - 30 * flap
    midx = sx - facing * 20
    midy = sy + 8 - 14 * flap
    low = (sx - facing * 6, sy + 22)
    pts = [(sx, sy), (tipx, tipy), (midx, midy), low]
    poly(surf, pts, main)
    # vleugelbotten
    for tx, ty in ((tipx, tipy), (midx, midy)):
        pygame.draw.line(surf, bone, (int(sx), int(sy)), (int(tx), int(ty)), 2)


def make_dragon(flap_phase, mouth_open, scale=1.0, facing=1,
                body=PURPLE, bodyd=PURPLE_D, bodyl=PURPLE_L, belly=BELLY):
    """Teken een draak (standaard naar rechts). Geeft een Surface met alpha."""
    ww, hh = 116, 92
    s = pygame.Surface((ww, hh), pygame.SRCALPHA)
    flap = math.sin(flap_phase)
    cx, cy = 62, 46

    # verre vleugel (achter het lichaam, tegenfase -> diepte)
    _wing(s, (cx - 4, cy - 6), -flap * 0.9,
          (bodyd[0], bodyd[1], bodyd[2], 210), bodyd, facing)

    # staart (krullend, met spade-punt)
    tx, ty = cx - 30, cy + 6
    for i in range(9):
        t = i / 8.0
        rx = tx - i * 6
        ry = ty + math.sin(t * 3.0) * 9
        circ(s, rx, ry, 9 - i * 0.8, body)
    spade = [(tx - 54, ty + 2), (tx - 70, ty - 8),
             (tx - 66, ty + 6), (tx - 70, ty + 18)]
    poly(s, spade, bodyl)

    # achterpoot
    poly(s, [(cx - 8, cy + 16), (cx - 2, cy + 30), (cx - 12, cy + 30)], bodyd)

    # lichaam
    poly(s, [(cx - 26, cy), (cx - 6, cy - 16), (cx + 20, cy - 12),
             (cx + 30, cy + 4), (cx + 16, cy + 20), (cx - 16, cy + 18)], body)
    # buikplaten
    poly(s, [(cx - 12, cy + 12), (cx + 16, cy + 14), (cx + 8, cy + 20),
             (cx - 12, cy + 18)], belly)

    # rugstekels
    for i in range(5):
        bx = cx - 18 + i * 9
        by = cy - 12 - (2 if i in (1, 2, 3) else 0)
        poly(s, [(bx, by), (bx + 6, by), (bx + 3, by - 9)], bodyl)

    # voorpoot
    poly(s, [(cx + 8, cy + 16), (cx + 16, cy + 30), (cx + 4, cy + 30)], bodyd)

    # nek + kop
    neck = [(cx + 18, cy - 8), (cx + 30, cy - 22), (cx + 40, cy - 18),
            (cx + 30, cy - 2)]
    poly(s, neck, body)
    hx, hy = cx + 40, cy - 22
    # horens
    poly(s, [(hx - 2, hy - 4), (hx + 4, hy - 4), (hx - 6, hy - 18)], HORN)
    poly(s, [(hx + 4, hy - 3), (hx + 10, hy - 3), (hx + 2, hy - 16)], HORN)
    # kop
    poly(s, [(hx - 6, hy + 2), (hx + 16, hy - 4), (hx + 24, hy + 4),
             (hx + 14, hy + 10), (hx - 4, hy + 10)], body)
    # snuit / kaak
    jaw = 6 if mouth_open else 1
    poly(s, [(hx + 16, hy + 2), (hx + 30, hy + 2), (hx + 22, hy + 8)], bodyl)
    poly(s, [(hx + 16, hy + 8), (hx + 28, hy + 8 + jaw),
             (hx + 16, hy + 10 + jaw)], bodyd)
    # oog
    circ(s, hx + 6, hy + 3, 3, (20, 16, 30))
    circ(s, hx + 6, hy + 3, 2, EYE)

    # nabije vleugel (voor het lichaam)
    _wing(s, (cx + 2, cy - 8), flap,
          (body[0], body[1], body[2], 235), bodyl, facing)

    if facing == -1:
        s = pygame.transform.flip(s, True, False)
    if scale != 1.0:
        s = pygame.transform.smoothscale(
            s, (int(ww * scale), int(hh * scale)))
    return s


def make_bat(flap_phase):
    """Kleine vliegende vijand (wyvern-silhouet)."""
    s = pygame.Surface((52, 34), pygame.SRCALPHA)
    flap = math.sin(flap_phase)
    col = (60, 48, 82)
    coll = (92, 78, 120)
    circ(s, 30, 18, 8, col)                 # lijf
    poly(s, [(36, 16), (46, 12), (42, 20)], coll)   # kop
    _wing(s, (28, 14), flap, (coll[0], coll[1], coll[2], 230), col, 1)
    _wing(s, (24, 14), flap, (col[0], col[1], col[2], 230), col, -1)
    circ(s, 40, 15, 1, EYE)
    return s


def make_hut(burning=False):
    s = pygame.Surface((60, 60), pygame.SRCALPHA)
    wall = (120, 92, 66)
    roof = (86, 58, 44)
    pygame.draw.rect(s, wall, (10, 28, 40, 30))
    poly(s, [(6, 30), (30, 12), (54, 30)], roof)
    pygame.draw.rect(s, (58, 40, 30), (26, 42, 12, 16))   # deur
    pygame.draw.rect(s, (150, 180, 210), (14, 34, 8, 8))  # raam
    return s


# ---------------------------------------------------------------- audio (synth)
def _env(i, n, atk=0.01, rel=0.3):
    a = int(n * atk) or 1
    r = int(n * rel) or 1
    if i < a:
        return i / a
    if i > n - r:
        return max(0.0, (n - i) / r)
    return 1.0


def tone(freq, ms, vol=0.4, wave="sine"):
    n = int(SR * ms / 1000)
    buf = array("h")
    for i in range(n):
        t = i / SR
        if wave == "square":
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave == "saw":
            v = 2.0 * ((freq * t) % 1.0) - 1.0
        elif wave == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * freq * t)
        buf.append(int(max(-1, min(1, v)) * _env(i, n) * vol * 32767))
    return buf


def mix(*bufs):
    n = max(len(b) for b in bufs)
    out = [0] * n
    for b in bufs:
        for i, s in enumerate(b):
            out[i] += s
    res = array("h", (int(max(-32767, min(32767, v))) for v in out))
    return res


def make_sound(buf):
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


class Audio:
    def __init__(self):
        self.ok = pygame.mixer.get_init() is not None
        self.snd = {}
        if not self.ok:
            return
        self.snd["fire"] = make_sound(tone(90, 260, 0.35, "noise"))
        self.snd["flap"] = make_sound(tone(70, 120, 0.3, "sine"))
        self.snd["coin"] = make_sound(mix(tone(880, 70, 0.3),
                                          tone(1320, 90, 0.25)))
        self.snd["hit"] = make_sound(mix(tone(200, 200, 0.4, "saw"),
                                         tone(120, 220, 0.3, "square")))
        self.snd["burn"] = make_sound(tone(140, 220, 0.3, "noise"))
        self.snd["boss"] = make_sound(mix(tone(160, 400, 0.4, "square"),
                                          tone(80, 420, 0.35, "saw")))
        self.snd["win"] = make_sound(mix(tone(660, 120, 0.3),
                                         tone(990, 160, 0.3)))
        self._music()

    def _music(self):
        # donkere loop: bas + arpeggio in a-mineur
        base = [220, 262, 330, 262, 196, 247, 294, 247]
        parts = []
        for f in base:
            parts.append(mix(tone(f, 240, 0.16, "saw"),
                             tone(f / 2, 240, 0.14, "sine"),
                             tone(f * 2, 240, 0.07, "square")))
        loop = array("h")
        for p in parts:
            loop.extend(p)
        self.music = make_sound(loop)

    def play(self, k):
        s = self.snd.get(k)
        if s:
            try:
                s.play()
            except Exception:
                pass

    def start_music(self):
        if getattr(self, "music", None):
            try:
                self.music.play(loops=-1)
            except Exception:
                pass


# ---------------------------------------------------------------- game-objecten
class Arrow:
    def __init__(self, x, y, tx, ty):
        self.x, self.y = x, y
        a = math.atan2(ty - y, tx - x)
        sp = 7.0
        self.vx = math.cos(a) * sp
        self.vy = math.sin(a) * sp
        self.dead = False

    def update(self, scroll):
        self.x += self.vx - scroll
        self.y += self.vy
        if self.x < -20 or self.y > H or self.y < -20:
            self.dead = True

    def draw(self, sc):
        a = math.atan2(self.vy, self.vx)
        ex = self.x + math.cos(a) * 14
        ey = self.y + math.sin(a) * 14
        pygame.draw.line(sc, (230, 220, 210), (self.x, self.y), (ex, ey), 3)
        pygame.draw.circle(sc, (120, 120, 130), (int(ex), int(ey)), 3)

    def rect(self):
        return pygame.Rect(self.x - 4, self.y - 4, 12, 12)


class Fireball:
    def __init__(self, x, y, tx, ty):
        self.x, self.y = x, y
        a = math.atan2(ty - y, tx - x)
        self.vx = math.cos(a) * 5.0
        self.vy = math.sin(a) * 5.0
        self.dead = False
        self.r = 9

    def update(self, scroll):
        self.x += self.vx - scroll
        self.y += self.vy
        if self.x < -30 or self.y > H + 30 or self.y < -30:
            self.dead = True

    def draw(self, sc):
        circ(sc, self.x, self.y, self.r + 2, (255, 150, 40))
        circ(sc, self.x, self.y, self.r - 2, (255, 230, 120))

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r,
                           self.r * 2, self.r * 2)


class Archer:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.cool = random.randint(50, 110)
        self.dead = False
        self.hp = 1
        self.burn = 0

    def update(self, scroll, player, arrows):
        self.x -= scroll
        if self.x < -40:
            self.dead = True
        if self.burn > 0:
            self.burn -= 1
            if self.burn == 0:
                self.dead = True
            return
        self.cool -= 1
        if self.cool <= 0 and 60 < self.x < W - 20:
            self.cool = random.randint(80, 150)
            arrows.append(Arrow(self.x, self.y - 24, player.x, player.y))

    def draw(self, sc):
        bx, by = int(self.x), int(self.y)
        if self.burn > 0:
            _draw_flames(sc, bx, by - 20, 14)
        pygame.draw.rect(sc, (70, 90, 60), (bx - 5, by - 22, 10, 20))  # lijf
        circ(sc, bx, by - 26, 5, (225, 195, 165))                      # hoofd
        pygame.draw.arc(sc, (90, 70, 50),
                        (bx + 2, by - 30, 14, 20), -1.2, 1.2, 2)       # boog

    def rect(self):
        return pygame.Rect(self.x - 8, self.y - 32, 16, 32)


class Hut:
    def __init__(self, x, img):
        self.x = x
        self.y = GROUND_Y
        self.img = img
        self.dead = False
        self.burn = 0
        self.scored = False

    def update(self, scroll):
        self.x -= scroll
        if self.x < -70:
            self.dead = True
        if self.burn > 0:
            self.burn -= 1
            if self.burn == 0:
                self.dead = True

    def draw(self, sc):
        sc.blit(self.img, (int(self.x - 30), int(self.y - 58)))
        if self.burn > 0:
            _draw_flames(sc, int(self.x), int(self.y - 40), 22)

    def rect(self):
        return pygame.Rect(self.x - 22, self.y - 40, 44, 40)


class Bird:
    def __init__(self, x):
        self.x = x
        self.y = random.randint(80, GROUND_Y - 120)
        self.base = self.y
        self.t = random.uniform(0, 6)
        self.dead = False
        self.burn = 0

    def update(self, scroll, frames):
        self.x -= scroll + 1.4
        self.t += 0.05
        self.y = self.base + math.sin(self.t) * 34
        if self.x < -40:
            self.dead = True
        if self.burn > 0:
            self.burn -= 1
            if self.burn == 0:
                self.dead = True

    def draw(self, sc, frames):
        f = frames[int(self.t * 6) % len(frames)]
        sc.blit(f, (int(self.x - 26), int(self.y - 17)))
        if self.burn > 0:
            _draw_flames(sc, int(self.x), int(self.y), 12)

    def rect(self):
        return pygame.Rect(self.x - 16, self.y - 12, 32, 24)


class Coin:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t = random.uniform(0, 6)
        self.dead = False

    def update(self, scroll):
        self.x -= scroll
        self.t += 0.12
        if self.x < -20:
            self.dead = True

    def draw(self, sc):
        r = 8 + int(math.sin(self.t) * 2)
        circ(sc, self.x, self.y, r, GOLDC)
        circ(sc, self.x, self.y, r - 3, (255, 235, 150))

    def rect(self):
        return pygame.Rect(self.x - 10, self.y - 10, 20, 20)


class Boss:
    def __init__(self, level, frames):
        self.frames = frames
        self.x = W + 120
        self.y = 170
        self.t = random.uniform(0, 6)
        self.hp = 8 + level * 4
        self.maxhp = self.hp
        self.cool = 90
        self.dead = False
        self.hurt = 0
        self.enter = True

    def update(self, scroll, player, fireballs):
        if self.enter:
            self.x -= 3
            if self.x <= W - 340:
                self.enter = False
        self.t += 0.05
        self.y = 170 + math.sin(self.t) * 80
        if self.hurt > 0:
            self.hurt -= 1
        if not self.enter:
            self.cool -= 1
            if self.cool <= 0:
                self.cool = random.randint(55, 90)
                for dy in (-24, 0, 24):
                    fireballs.append(
                        Fireball(self.x - 40, self.y, player.x, player.y + dy))

    def draw(self, sc):
        f = self.frames[int(self.t * 5) % len(self.frames)]
        if self.hurt > 0 and self.hurt % 2 == 0:
            f = f.copy()
            f.fill((90, 20, 20, 0), special_flags=pygame.BLEND_RGBA_ADD)
        sc.blit(f, (int(self.x - f.get_width() // 2),
                    int(self.y - f.get_height() // 2)))

    def rect(self):
        return pygame.Rect(self.x - 48, self.y - 34, 96, 68)


def _draw_flames(sc, x, y, size):
    for _ in range(4):
        fx = x + random.randint(-size // 2, size // 2)
        fy = y - random.randint(0, size)
        r = random.randint(4, size // 2 + 3)
        col = random.choice([(255, 140, 40), (255, 200, 70), (240, 90, 30)])
        circ(sc, fx, fy, r, col)


class FireP:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random.uniform(6, 11)
        self.vy = random.uniform(-1.6, 1.6)
        self.life = random.randint(16, 26)
        self.r = random.randint(6, 12)

    def update(self, scroll):
        self.x += self.vx - scroll * 0.4
        self.y += self.vy
        self.life -= 1
        self.r *= 0.94

    def draw(self, sc):
        if self.life <= 0:
            return
        c = (255, 210, 90) if self.life > 14 else (240, 110, 40)
        circ(sc, self.x, self.y, self.r, c)


class PowerUp:
    def __init__(self, x, y, kind):
        self.x, self.y = float(x), float(y)
        self.kind = kind
        self.t = random.uniform(0, 6)
        self.dead = False

    def update(self, scroll):
        self.x -= scroll * 0.7
        self.y = min(GROUND_Y - 20, self.y + 0.6)   # zweeft zachtjes omlaag
        self.t += 0.12
        if self.x < -24:
            self.dead = True

    def draw(self, sc):
        y = self.y + math.sin(self.t) * 4
        col = PU_COLORS.get(self.kind, (255, 255, 255))
        circ(sc, self.x, y, 14, (18, 14, 26))
        circ(sc, self.x, y, 12, col)
        x, yy = int(self.x), int(y)
        wht = (255, 255, 255)
        if self.kind == "shield":
            poly(sc, [(x - 6, yy - 6), (x + 6, yy - 6), (x + 6, yy + 1),
                      (x, yy + 7), (x - 6, yy + 1)], wht)
        elif self.kind == "triple":
            for dy in (-5, 0, 5):
                pygame.draw.line(sc, wht, (x - 5, yy + dy), (x + 6, yy + dy), 2)
        elif self.kind == "heart":
            circ(sc, x - 3, yy - 2, 3, wht)
            circ(sc, x + 3, yy - 2, 3, wht)
            poly(sc, [(x - 6, yy - 1), (x + 6, yy - 1), (x, yy + 7)], wht)
        elif self.kind == "magnet":
            pygame.draw.arc(sc, wht, (x - 7, yy - 7, 14, 14), 0.4, 2.7, 4)
            pygame.draw.line(sc, wht, (x - 6, yy + 2), (x - 6, yy + 7), 3)
            pygame.draw.line(sc, wht, (x + 6, yy + 2), (x + 6, yy + 7), 3)

    def rect(self):
        return pygame.Rect(self.x - 14, self.y - 14, 28, 28)


class Boulder:
    def __init__(self, x, y, tx, ty):
        self.x, self.y = float(x), float(y)
        self.g = 0.4
        t = 34.0
        self.vx = (tx - x) / t
        self.vy = (ty - y) / t - 0.5 * self.g * t
        self.dead = False
        self.r = 13
        self.rot = 0.0

    def update(self, scroll):
        self.x += self.vx - scroll
        self.vy += self.g
        self.y += self.vy
        self.rot += 0.2
        if self.y > H + 40 or self.x < -40:
            self.dead = True

    def draw(self, sc):
        circ(sc, self.x, self.y, self.r, (96, 86, 78))
        circ(sc, self.x - 4, self.y - 4, 4, (128, 118, 108))

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r,
                           self.r * 2, self.r * 2)


class Catapult:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.cool = random.randint(80, 140)
        self.dead = False
        self.burn = 0

    def update(self, scroll, player, boulders):
        self.x -= scroll
        if self.x < -50:
            self.dead = True
        if self.burn > 0:
            self.burn -= 1
            if self.burn == 0:
                self.dead = True
            return
        self.cool -= 1
        if self.cool <= 0 and 90 < self.x < W - 10:
            self.cool = random.randint(130, 200)
            boulders.append(Boulder(self.x, self.y - 30, player.x, player.y))

    def draw(self, sc):
        bx, by = int(self.x), int(self.y)
        if self.burn > 0:
            _draw_flames(sc, bx, by - 22, 22)
        pygame.draw.rect(sc, (92, 66, 44), (bx - 18, by - 16, 36, 14))
        pygame.draw.line(sc, (70, 50, 34), (bx - 10, by - 14),
                         (bx + 14, by - 34), 5)
        circ(sc, bx + 14, by - 34, 6, (58, 42, 30))
        circ(sc, bx - 12, by - 2, 6, (48, 36, 26))
        circ(sc, bx + 12, by - 2, 6, (48, 36, 26))

    def rect(self):
        return pygame.Rect(self.x - 20, self.y - 36, 40, 36)


class Bolt:
    def __init__(self, x, y, tx, ty):
        a = math.atan2(ty - y, tx - x)
        s = 4.6
        self.x, self.y = x, y
        self.vx = math.cos(a) * s
        self.vy = math.sin(a) * s
        self.dead = False
        self.t = 0.0

    def update(self, scroll):
        self.x += self.vx - scroll
        self.y += self.vy
        self.t += 0.3
        if self.x < -30 or self.y < -30 or self.y > H + 30:
            self.dead = True

    def draw(self, sc):
        r = 7 + int(math.sin(self.t) * 2)
        circ(sc, self.x, self.y, r, (150, 90, 220))
        circ(sc, self.x, self.y, max(1, r - 3), (214, 186, 250))

    def rect(self):
        return pygame.Rect(self.x - 8, self.y - 8, 16, 16)


class Mage:
    def __init__(self, x):
        self.x = x
        self.y = random.randint(90, GROUND_Y - 170)
        self.base = self.y
        self.t = random.uniform(0, 6)
        self.cool = random.randint(70, 120)
        self.dead = False
        self.burn = 0

    def update(self, scroll, player, bolts):
        self.x -= scroll + 0.8
        self.t += 0.04
        self.y = self.base + math.sin(self.t) * 24
        if self.x < -40:
            self.dead = True
        if self.burn > 0:
            self.burn -= 1
            if self.burn == 0:
                self.dead = True
            return
        self.cool -= 1
        if self.cool <= 0 and 80 < self.x < W - 20:
            self.cool = random.randint(100, 160)
            bolts.append(Bolt(self.x, self.y, player.x, player.y))

    def draw(self, sc):
        bx, by = int(self.x), int(self.y)
        if self.burn > 0:
            _draw_flames(sc, bx, by, 14)
        poly(sc, [(bx - 12, by + 16), (bx + 12, by + 16),
                  (bx + 6, by - 6), (bx - 6, by - 6)], (82, 62, 142))
        circ(sc, bx, by - 12, 7, (228, 198, 168))
        poly(sc, [(bx - 9, by - 8), (bx + 9, by - 8), (bx, by - 24)],
             (60, 44, 112))
        pygame.draw.line(sc, (120, 90, 60), (bx + 10, by + 14),
                         (bx + 16, by - 14), 3)
        circ(sc, bx + 16, by - 16, 4, (206, 156, 255))

    def rect(self):
        return pygame.Rect(self.x - 13, self.y - 18, 26, 36)


class Player:
    def __init__(self, frames_closed, frames_open):
        self.fc = frames_closed
        self.fo = frames_open
        self.x = 210.0
        self.y = H / 2
        self.vx = 0.0
        self.vy = 0.0
        self.phase = 0.0
        self.hp = 5
        self.maxhp = 5
        self.inv = 0
        self.breathing = False
        self.fuel = 100.0
        self.shield_t = 0     # onkwetsbaarheid
        self.triple_t = 0     # drievoudig vuur
        self.magnet_t = 0     # goud-magneet

    def update(self, keys):
        ax = ay = 0.0
        if keys[pygame.K_UP]:
            ay -= 0.6
        if keys[pygame.K_DOWN]:
            ay += 0.6
        if keys[pygame.K_LEFT]:
            ax -= 0.5
        if keys[pygame.K_RIGHT]:
            ax += 0.5
        self.vy = (self.vy + ay) * 0.9
        self.vx = (self.vx + ax) * 0.9
        self.y += self.vy
        self.x += self.vx
        self.y = max(40, min(GROUND_Y - 20, self.y))
        self.x = max(70, min(460, self.x))
        self.phase += 0.25
        if self.inv > 0:
            self.inv -= 1
        for a in ("shield_t", "triple_t", "magnet_t"):
            if getattr(self, a) > 0:
                setattr(self, a, getattr(self, a) - 1)
        # vuur
        self.breathing = keys[pygame.K_SPACE] and self.fuel > 0
        if self.breathing:
            self.fuel = max(0, self.fuel - 1.4)
        else:
            self.fuel = min(100, self.fuel + 0.6)

    def mouth(self):
        return self.x + 52, self.y - 16

    def draw(self, sc):
        if self.inv > 0 and self.inv % 6 < 3:
            return
        frames = self.fo if self.breathing else self.fc
        f = frames[int(self.phase) % len(frames)]
        sc.blit(f, (int(self.x - f.get_width() // 2),
                    int(self.y - f.get_height() // 2)))

    def rect(self):
        return pygame.Rect(self.x - 30, self.y - 20, 60, 40)


# ---------------------------------------------------------------------- de game
class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.quit()
            pygame.mixer.init(SR, -16, 1, 512)
        except Exception:
            pass
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(T("title"))
        ic = os.path.join(app_dir(), "assets", "icon.ico")
        if os.path.exists(ic):
            try:
                pygame.display.set_icon(pygame.image.load(ic))
            except Exception:
                pass
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arialrounded,arial", 60, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("arial", 20, bold=True)
        self._prerender()
        self.audio = Audio()
        self.best = self._load_best()
        self.state = "menu"
        self.reset()
        self.audio.start_music()

    def _prerender(self):
        self.dc = [make_dragon(i / 6 * math.tau, False) for i in range(6)]
        self.do = [make_dragon(i / 6 * math.tau, True) for i in range(6)]
        self.bird_f = [make_bat(i / 4 * math.tau) for i in range(4)]
        self.boss_f = [make_dragon(i / 5 * math.tau, True, 1.8, -1,
                                   REDDR, REDDR_D, (240, 150, 150), REDBELLY)
                       for i in range(5)]
        self.hut_img = make_hut()

    def _make_bg(self, biome):
        top, bot = biome["sky"]
        mtn1, mtn2 = biome["mtn"]
        s = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            s.fill((int(top[0] + (bot[0] - top[0]) * t),
                    int(top[1] + (bot[1] - top[1]) * t),
                    int(top[2] + (bot[2] - top[2]) * t)),
                   (0, y, W, 1))
        # verre bergen
        for layer, col, base in ((0, mtn1, GROUND_Y - 40),
                                 (1, mtn2, GROUND_Y - 10)):
            pts = [(0, H)]
            x = 0
            random.seed(layer + 5 + biome["name"].__hash__() % 97)
            while x <= W:
                pts.append((x, base - random.randint(20, 90)))
                x += random.randint(60, 130)
            pts.append((W, H))
            poly(s, pts, col)
        random.seed()
        return s

    def _set_biome(self):
        b = BIOMES[(self.level - 1) % len(BIOMES)]
        self.biome = b
        self.bg = self._make_bg(b)
        self.ground_col = b["gnd"][0]
        self.ground_top = b["gnd"][1]
        self.ground_line = b["line"]

    def _load_best(self):
        try:
            with open(os.path.join(cache_dir(), "score.json")) as f:
                return int(json.load(f).get("best", 0))
        except Exception:
            return 0

    def _save_best(self):
        try:
            with open(os.path.join(cache_dir(), "score.json"), "w") as f:
                json.dump({"best": self.best}, f)
        except Exception:
            pass

    def reset(self):
        self.player = Player(self.dc, self.do)
        self.arrows = []
        self.fireballs = []
        self.archers = []
        self.huts = []
        self.birds = []
        self.coins = []
        self.fire = []
        self.powerups = []
        self.catapults = []
        self.boulders = []
        self.mages = []
        self.bolts = []
        self.boss = None
        self.scroll = 3.0
        self.dist = 0
        self.gold = 0
        self.level = 1
        self.combo = 0
        self.combo_t = 0
        self.spawn = 0
        self.groundx = 0.0
        self.shake = 0
        self.msg = ""
        self.msgt = 0
        self.next_boss = 1400
        self._set_biome()

    # --------------------------------------------------------------- spelloop
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                if e.type == pygame.KEYDOWN:
                    self._key(e.key)
            if self.state == "play":
                self._update()
            self._draw()
            self.clock.tick(FPS)

    def _key(self, k):
        if k == pygame.K_i:
            self._info()
            return
        if k == pygame.K_d:
            try:
                webbrowser.open(DONATE)
            except Exception:
                pass
            return
        if self.state == "menu":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self._quit()
        elif self.state == "play":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "pause"
        elif self.state == "pause":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"
        elif self.state == "over":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def _info(self):
        # eenvoudige info-overlay tot een toets
        self._draw()
        box = pygame.Surface((640, 220), pygame.SRCALPHA)
        box.fill((20, 16, 30, 235))
        pygame.draw.rect(box, PURPLE_L, box.get_rect(), 2, border_radius=10)
        y = 22
        for line in T("info_txt").split("\n"):
            box.blit(self.small.render(line, True, (230, 224, 245)), (24, y))
            y += 28
        self.screen.blit(box, (W // 2 - 320, H // 2 - 110))
        pygame.display.flip()
        wait = True
        while wait:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    wait = False
            self.clock.tick(30)

    def _quit(self):
        self._save_best()
        pygame.quit()
        sys.exit()

    # --------------------------------------------------------------- update
    def _update(self):
        p = self.player
        keys = pygame.key.get_pressed()
        p.update(keys)
        if p.breathing and pygame.time.get_ticks() % 2 == 0:
            mx, my = p.mouth()
            self.fire.append(FireP(mx, my))
            if p.triple_t > 0:
                f1 = FireP(mx, my)
                f1.vy -= 3.4
                f2 = FireP(mx, my)
                f2.vy += 3.4
                self.fire.extend([f1, f2])
            if random.random() < 0.06:
                self.audio.play("fire")

        self.scroll = 3.0 + self.level * 0.4
        self.dist += self.scroll
        self.groundx = (self.groundx - self.scroll) % 48

        # spawnen (niet tijdens baas)
        if self.boss is None:
            self.spawn -= 1
            if self.spawn <= 0:
                self.spawn = max(24, 60 - self.level * 3)
                self._spawn()
            if self.dist >= self.next_boss:
                self.boss = Boss(self.level, self.boss_f)
                self.audio.play("boss")
                self.msg, self.msgt = T("boss"), 90

        # updates
        for a in self.arrows:
            a.update(self.scroll)
        for fb in self.fireballs:
            fb.update(self.scroll)
        for ar in self.archers:
            ar.update(self.scroll, p, self.arrows)
        for h in self.huts:
            h.update(self.scroll)
        for b in self.birds:
            b.update(self.scroll, self.bird_f)
        for c in self.coins:
            c.update(self.scroll)
        for ct in self.catapults:
            ct.update(self.scroll, p, self.boulders)
        for bo in self.boulders:
            bo.update(self.scroll)
        for mg in self.mages:
            mg.update(self.scroll, p, self.bolts)
        for bl in self.bolts:
            bl.update(self.scroll)
        for pu in self.powerups:
            pu.update(self.scroll)
        for f in self.fire:
            f.update(self.scroll)
        self.fire = [f for f in self.fire if f.life > 0]

        # goud-magneet: trek munten naar de draak
        if p.magnet_t > 0:
            for c in self.coins:
                dx, dy 
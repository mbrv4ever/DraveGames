# -*- coding: utf-8 -*-
"""rainbow.py - DraveRainbow, een Rainbow-Islands-spel van Dravenlock Games.

Klim omhoog van eiland naar eiland door REGENBOGEN te maken: een regenboog is een
boog waar je op staat en overheen klimt, en die vijanden verslaat als je hem op
ze maakt (ze laten dan fruit vallen voor punten). Onderin komt het water omhoog en
jaagt je op - blijf dus klimmen tot de top!

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke HUD; procedurele muziek en geluiden (sfx.py); gesproken intro
(neuvoice) in een apart splashvenster. Volledig draagbaar: alles in een map
"DraveRainbow-data" naast het programma.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import webbrowser

import pygame

try:
    import sfx as sfxmod
except Exception:  # pragma: no cover
    sfxmod = None
try:
    import tts as ttsmod
except Exception:  # pragma: no cover
    ttsmod = None

APP_NAME = "DraveRainbow"
APP_VERSION = "0.1.2"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 46
VIEW_H = HEIGHT - HUD_H

# fysica (pixels/seconde)
GRAVITY = 2100.0
JUMP_V = -780.0
MOVE_SPEED = 260.0
MAX_FALL = 980.0
PW, PH = 26, 34            # speler
PLAT_T = 16               # platformdikte
N_LEVELS = 5

# regenboog
ARC_N = 9
RB_LIFE = 3.4
RB_COOL = 0.45
RB_MAX = 3
RB_BW, RB_BH = 26, 16     # blokgrootte

# donker Dravenlock-palet
BG = (14, 14, 17)
PANEL = (22, 22, 27)
PANEL2 = (28, 28, 34)
LINE = (44, 44, 52)
TEXT = (224, 224, 228)
MUTED = (140, 140, 150)
ACCENT = (111, 163, 214)
GOLD = (212, 175, 90)
GOED = (127, 176, 105)
WARN = (214, 138, 111)
RED = (200, 70, 70)
PURPLE = (150, 110, 200)
SKY_TOP = (74, 142, 214)
SKY_BOT = (158, 206, 240)
CLOUD_COL = (255, 255, 255)
PLAT_COL = (96, 74, 52)
PLAT_TOP = (132, 104, 72)
WATER = (38, 98, 186)
RAINBOW_COLS = [(214, 92, 92), (214, 150, 90), (212, 200, 90),
                (127, 176, 105), (111, 163, 214), (150, 110, 200), (200, 120, 190)]


# ----------------------------------------------------------------------------
def config_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveRainbow-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveRainbow-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "highscore": 0,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        tmp = CONFIG_PATH + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, CONFIG_PATH)
    except Exception:
        pass


_LANG = "nl"


def detect_os_lang():
    try:
        import locale
        loc = (locale.getdefaultlocale()[0] or "").lower()
        return "nl" if loc.startswith("nl") else "en"
    except Exception:
        return "nl"


def set_lang(l):
    global _LANG
    _LANG = "nl" if l == "nl" else "en"


TR = {
    "made_by": {"nl": "Gemaakt door Dravenlock Games", "en": "Made by Dravenlock Games"},
    "donatie": {"nl": "Donatie", "en": "Donate"},
    "speel": {"nl": "Spelen", "en": "Play"},
    "gids": {"nl": "Hoe te spelen", "en": "How to play"},
    "instellingen": {"nl": "Instellingen", "en": "Settings"},
    "terug": {"nl": "Terug", "en": "Back"},
    "geluid": {"nl": "Geluid", "en": "Sound"},
    "muziek": {"nl": "Muziek", "en": "Music"},
    "stem": {"nl": "Stem", "en": "Voice"},
    "volume": {"nl": "Volume", "en": "Volume"},
    "taal": {"nl": "Taal", "en": "Language"},
    "aan": {"nl": "aan", "en": "on"},
    "uit": {"nl": "uit", "en": "off"},
    "auto": {"nl": "OS", "en": "OS"},
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "hervat": {"nl": "Hervatten", "en": "Resume"},
    "hoofdmenu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "opnieuw": {"nl": "Opnieuw", "en": "Retry"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "leven": {"nl": "Levens", "en": "Lives"},
    "eiland": {"nl": "Eiland", "en": "Island"},
    "eiland_klaar": {"nl": "Eiland gehaald!", "en": "Island cleared!"},
    "gameover": {"nl": "Game over", "en": "Game over"},
    "gewonnen": {"nl": "Alle eilanden gehaald!", "en": "All islands cleared!"},
    "volgende": {"nl": "Volgende eiland", "en": "Next island"},
    "uitleg1": {"nl": "Pijltjes links/rechts: lopen. Omhoog of W: springen.", "en": "Arrows left/right: walk. Up or W: jump."},
    "uitleg2": {"nl": "Spatie: maak een regenboog voor je.", "en": "Space: make a rainbow in front of you."},
    "uitleg3": {"nl": "Sta en klim op je regenbogen om hoger te komen.", "en": "Stand and climb on your rainbows to get higher."},
    "uitleg4": {"nl": "Maak een regenboog op een vijand om hem te verslaan.", "en": "Make a rainbow on an enemy to defeat it."},
    "uitleg5": {"nl": "Het water komt omhoog - blijf klimmen naar de top!", "en": "The water is rising - keep climbing to the top!"},
}


def t(key):
    e = TR.get(key, {})
    return e.get(_LANG, e.get("nl", key))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, x):
    return a + (b - a) * x


def mix(c1, c2, x):
    return (int(lerp(c1[0], c2[0], x)), int(lerp(c1[1], c2[1], x)), int(lerp(c1[2], c2[2], x)))


def draw_heart(surf, cx, cy, r, color):
    rr = max(3, int(r))
    pygame.draw.circle(surf, color, (int(cx - rr * 0.5), int(cy - rr * 0.3)), int(rr * 0.6))
    pygame.draw.circle(surf, color, (int(cx + rr * 0.5), int(cy - rr * 0.3)), int(rr * 0.6))
    pygame.draw.polygon(surf, color, [(int(cx - rr * 1.02), int(cy - rr * 0.1)),
                                      (int(cx + rr * 1.02), int(cy - rr * 0.1)),
                                      (int(cx), int(cy + rr * 1.05))])


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def load_window_icon():
    for name in ("assets/app_icon.png", "assets/logo_t.png", "assets/logo.png"):
        try:
            return pygame.transform.smoothscale(pygame.image.load(resource_path(name)), (32, 32))
        except Exception:
            continue
    return None


# arc-offsets (kijkrichting rechts), blokmiddelpunten t.o.v. de speler
def arc_offsets(facing):
    span = 170.0
    peak = 78.0
    pts = []
    for i in range(ARC_N):
        fx = 22 + i * (span / (ARC_N - 1))
        fy = -peak * math.sin(math.pi * i / (ARC_N - 1)) - 4
        pts.append((fx * facing, fy))
    return pts


# ----------------------------------------------------------------------------
class Button:
    def __init__(self, label, rect, action, kind="normal"):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.action = action
        self.kind = kind

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, font, hot=False, focus=False):
        r = self.rect
        base = PANEL2
        if self.kind == "primary":
            base = mix(ACCENT, BG, 0.55)
        elif self.kind == "back":
            base = PANEL
        bg = mix(base, (255, 255, 255), 0.10) if (hot or focus) else base
        pygame.draw.rect(surf, bg, r, border_radius=10)
        pygame.draw.rect(surf, ACCENT if (hot or focus) else LINE, r,
                         width=3 if (hot or focus) else 2, border_radius=10)
        col = TEXT if not (hot or focus) else (245, 245, 248)
        if self.kind == "donate":
            draw_heart(surf, r.left + 26, r.centery, 11, WARN if not (hot or focus) else (235, 120, 110))
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(midleft=(r.left + 46, r.centery)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


# ----------------------------------------------------------------------------
class Enemy:
    def __init__(self, cx, bottom, left, right, seed=0):
        self.w, self.h = 28, 26
        self.x = cx - self.w / 2
        self.y = bottom - self.h
        self.left = left
        self.right = right - self.w
        self.vx = 60.0 * (1 if (seed % 2 == 0) else -1)
        self.dead = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt):
        self.x += self.vx * dt
        if self.x < self.left:
            self.x = self.left
            self.vx = abs(self.vx)
        elif self.x > self.right:
            self.x = self.right
            self.vx = -abs(self.vx)


class Item:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.vy = -120.0
        self.kind = kind          # 'fruit' | 'diamond'
        self.w = self.h = 20
        self.dead = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt, plats):
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        oldb = self.y + self.h / 2
        self.y += self.vy * dt
        newb = self.y + self.h / 2
        if self.vy >= 0:
            for (px, py, pw) in plats:
                if oldb <= py + 4 and newb >= py and px - 6 <= self.x <= px + pw + 6:
                    self.y = py - self.h / 2
                    self.vy = 0
                    break


class Rainbow:
    def __init__(self, px, py, facing):
        self.blocks = []          # lijst rects (wereld)
        for (dx, dy) in arc_offsets(facing):
            self.blocks.append(pygame.Rect(int(px + dx - RB_BW / 2), int(py + dy - RB_BH / 2), RB_BW, RB_BH))
        self.life = RB_LIFE
        self.max_life = RB_LIFE

    def update(self, dt):
        self.life -= dt

    @property
    def dead(self):
        return self.life <= 0


# ----------------------------------------------------------------------------
def build_level(level):
    rng = random.Random(1000 + level)
    world_h = 2300 + level * 280
    plats = []                                  # (x, y, w)
    plats.append((0, world_h - 30, WIDTH))      # bodem
    y = world_h - 150
    prev_x = WIDTH // 2
    while y > 220:
        nseg = rng.choice([1, 1, 2])
        for s in range(nseg):
            w = rng.randint(130, 250)
            # zorg dat er overlap is met een bereikbare x t.o.v. de vorige rij
            if s == 0:
                x = int(clamp(prev_x - w / 2 + rng.randint(-120, 120), 0, WIDTH - w))
            else:
                x = rng.randint(0, WIDTH - w)
            plats.append((x, y, w))
            if s == 0:
                prev_x = x + w // 2
        y -= rng.randint(96, 124)
    goal_y = 140
    gx = WIDTH // 2 - 100
    plats.append((gx, goal_y, 200))
    goal_idx = len(plats) - 1
    # vijanden op sommige platforms (niet bodem/doel)
    enemies = []
    for i, (x, py, w) in enumerate(plats[1:-1], start=1):
        if py < world_h - 220 and w >= 130 and rng.random() < 0.55:
            enemies.append(Enemy(x + w * 0.5, py, x, x + w, seed=i))
    # zwevende diamanten om te verzamelen
    items = []
    for (x, py, w) in plats[1:-1]:
        if rng.random() < 0.3:
            it = Item(x + w * 0.5, py - 36, "diamond")
            it.vy = 0
            items.append(it)
    return {"world_h": world_h, "plats": plats, "goal_idx": goal_idx,
            "goal": (WIDTH // 2, goal_y), "enemies": enemies, "items": items,
            "start": (WIDTH // 2 - PW // 2, world_h - 30 - PH),
            "water_rate": 16 + level * 4}


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app, level):
        self.app = app
        self.level = level
        self.score = app.run_score
        self.lives = app.run_lives
        self.finished = False
        self.result = None
        self.load_level()

    def load_level(self):
        d = build_level(self.level)
        self.world_h = d["world_h"]
        self.plats = d["plats"]
        self.goal_idx = d["goal_idx"]
        self.goal_plat = self.plats[self.goal_idx]
        self.goal = d["goal"]
        self.enemies = d["enemies"]
        self.items = d["items"]
        self.water_rate = d["water_rate"]
        self.px, self.py = d["start"]
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.rainbows = []
        self.rb_cool = 0.0
        self.water_y = self.world_h + 50
        self.cam_y = 0.0
        self.invuln = 1.0
        self.dead_t = 0.0
        self.alive = True
        self.jump_held = False
        self.safe = (self.px, self.py)
        self.want_jump = False
        self.want_fire = False
        # parallax-wolken (verspreid over de hele hoogte, vaste opzet per eiland)
        crng = random.Random(7000 + self.level)
        self.clouds = []
        n_cloud = int(self.world_h / 260) + 4
        for _ in range(n_cloud):
            self.clouds.append((crng.randint(0, WIDTH), crng.randint(-40, self.world_h),
                                crng.uniform(0.7, 1.5)))
        self.cloud_t = 0.0

    @property
    def prect(self):
        return pygame.Rect(int(self.px), int(self.py), PW, PH)

    def do_jump(self):
        self.want_jump = True

    def do_fire(self):
        self.want_fire = True

    def _fire_rainbow(self):
        if self.rb_cool > 0:
            return
        self.rb_cool = RB_COOL
        rb = Rainbow(self.px + PW / 2, self.py + PH * 0.4, self.facing)
        self.rainbows.append(rb)
        if len(self.rainbows) > RB_MAX:
            self.rainbows.pop(0)
        if self.app.sfx:
            self.app.sfx.play("rainbow")
        self._rainbow_hits(rb)

    def _rainbow_hits(self, rb):
        for e in self.enemies:
            if e.dead:
                continue
            for b in rb.blocks:
                if b.colliderect(e.rect):
                    e.dead = True
                    self.score += 100
                    self.items.append(Item(e.x + e.w / 2, e.y, "fruit"))
                    if self.app.sfx:
                        self.app.sfx.play("pop")
                    break

    def _platform_tops(self):
        tops = list(self.plats)
        for rb in self.rainbows:
            for b in rb.blocks:
                tops.append((b.x, b.y, b.w))
        return tops

    def update(self, dt):
        self.cloud_t += dt
        if self.finished:
            return
        if not self.alive:
            self.dead_t += dt
            if self.dead_t > 0.7:
                self._respawn()
            return
        self.rb_cool = max(0.0, self.rb_cool - dt)
        self.invuln = max(0.0, self.invuln - dt)
        if self.want_fire:
            self._fire_rainbow()
        self.want_fire = False

        # horizontaal
        self.px += self.vx * dt
        self.px = clamp(self.px, 0, WIDTH - PW)

        # springen
        if self.want_jump and self.on_ground:
            self.vy = JUMP_V
            self.on_ground = False
            if self.app.sfx:
                self.app.sfx.play("jump")
        self.want_jump = False
        if not self.jump_held and self.vy < 0:
            self.vy = max(self.vy, JUMP_V * 0.32)

        # verticaal + eenrichtingsplatforms
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        oldb = self.py + PH
        self.py += self.vy * dt
        newb = self.py + PH
        self.on_ground = False
        if self.vy >= 0:
            cx0, cx1 = self.px, self.px + PW
            for (x, py, w) in self._platform_tops():
                if oldb <= py + 6 and newb >= py and cx1 > x + 2 and cx0 < x + w - 2:
                    self.py = py - PH
                    self.vy = 0
                    self.on_ground = True
                    break
        # veilige plek onthouden (op echt platform)
        if self.on_ground:
            for (x, py, w) in self.plats:
                if abs((self.py + PH) - py) < 2 and x - 2 < self.px + PW / 2 < x + w + 2:
                    self.safe = (self.px, self.py)
                    break

        # regenbogen verouderen + blijven vijanden poppen
        for rb in self.rainbows:
            rb.update(dt)
            self._rainbow_hits(rb)
        self.rainbows = [rb for rb in self.rainbows if not rb.dead]

        # vijanden
        for e in self.enemies:
            if not e.dead:
                e.update(dt)
                if self.invuln <= 0 and e.rect.colliderect(self.prect):
                    self._die()
                    return
        self.enemies = [e for e in self.enemies if not e.dead]

        # items
        for it in self.items:
            it.update(dt, self.plats)
            if it.rect.colliderect(self.prect):
                it.dead = True
                self.score += 50 if it.kind == "fruit" else 80
                if self.app.sfx:
                    self.app.sfx.play("item")
        self.items = [it for it in self.items if not it.dead and it.y < self.world_h + 40]

        # water stijgt
        self.water_y -= self.water_rate * dt
        if self.py + PH > self.water_y:
            self._die(drown=True)
            return

        # doel bereikt?
        gx, gpy, gw = self.goal_plat
        if self.on_ground and abs((self.py + PH) - gpy) < 3 and gx - 2 < self.px + PW / 2 < gx + gw + 2:
            self._clear()

        # camera
        target = clamp(self.py - VIEW_H * 0.62, 0, max(0, self.world_h - VIEW_H))
        self.cam_y += (target - self.cam_y) * min(1.0, dt * 6)

    def _die(self, drown=False):
        if not self.alive:
            return
        self.alive = False
        self.dead_t = 0.0
        if self.app.sfx:
            self.app.sfx.play("splash" if drown else "death")

    def _respawn(self):
        self.lives -= 1
        self.app.run_score = self.score
        if self.lives <= 0:
            self.finished = True
            self.result = "dead"
            if self.score > self.app.cfg.get("highscore", 0):
                self.app.cfg["highscore"] = self.score
                save_config(self.app.cfg)
            return
        self.app.run_lives = self.lives
        self.px, self.py = self.safe
        self.vx = self.vy = 0.0
        self.alive = True
        self.invuln = 1.6
        self.water_y = min(self.world_h + 50, self.py + PH + VIEW_H * 0.7)
        self.rainbows = []

    def _clear(self):
        if self.finished:
            return
        self.score += 500 + self.level * 100
        self.app.run_score = self.score
        self.app.run_lives = self.lives
        if self.score > self.app.cfg.get("highscore", 0):
            self.app.cfg["highscore"] = self.score
            save_config(self.app.cfg)
        if self.app.sfx:
            self.app.sfx.play("clear")
        self.finished = True
        self.result = "win" if self.level + 1 >= N_LEVELS else "clear"

    # ---------- tekenen ----------
    def _draw_cloud(self, surf, x, y, sc):
        w = int(120 * sc)
        h = int(54 * sc)
        cl = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        col = (CLOUD_COL[0], CLOUD_COL[1], CLOUD_COL[2], 200)
        puffs = [(0.28, 0.62, 0.30), (0.5, 0.45, 0.38), (0.72, 0.62, 0.30), (0.5, 0.7, 0.26)]
        for (fx, fy, fr) in puffs:
            pygame.draw.circle(cl, col, (int(10 + fx * w), int(10 + fy * h)), int(fr * h * 1.5))
        surf.blit(cl, (x - 10, y - 10))

    def _sy(self, wy):
        return int(wy - self.cam_y) + HUD_H

    def draw(self, surf):
        # lucht-gradient
        for i in range(0, VIEW_H, 4):
            c = mix(SKY_TOP, SKY_BOT, i / VIEW_H)
            pygame.draw.rect(surf, c, (0, HUD_H + i, WIDTH, 4))
        # parallax-wolken (langzamer dan de platforms = diepte) + zachte drift
        for (cx, cy, sc) in self.clouds:
            sy = int(cy - self.cam_y * 0.55) + HUD_H
            if sy < HUD_H - 50 or sy > HEIGHT + 50:
                continue
            sx = int((cx + self.cloud_t * (5 + sc * 5)) % (WIDTH + 200)) - 100
            self._draw_cloud(surf, sx, sy, sc)
        # platforms
        for i, (x, py, w) in enumerate(self.plats):
            sy = self._sy(py)
            if sy < HUD_H - PLAT_T or sy > HEIGHT:
                continue
            goal = (i == self.goal_idx)
            pygame.draw.rect(surf, mix(GOED, PLAT_COL, 0.5) if goal else PLAT_COL, (x, sy, w, PLAT_T))
            pygame.draw.rect(surf, GOED if goal else PLAT_TOP, (x, sy, w, 5))
            if goal:
                # vlag op het doel
                fx = x + w // 2
                pygame.draw.line(surf, TEXT, (fx, sy), (fx, sy - 36), 3)
                pygame.draw.polygon(surf, GOLD, [(fx, sy - 36), (fx + 26, sy - 28), (fx, sy - 20)])
        # regenbogen
        for rb in self.rainbows:
            a = clamp(rb.life / 0.6, 0, 1)
            for bi, b in enumerate(rb.blocks):
                sy = self._sy(b.y)
                col = RAINBOW_COLS[bi % len(RAINBOW_COLS)]
                if a < 1:
                    col = mix(BG, col, a)
                pygame.draw.rect(surf, col, (b.x, sy, b.w, b.h), border_radius=5)
                pygame.draw.rect(surf, mix(col, (255, 255, 255), 0.3), (b.x, sy, b.w, 4), border_radius=3)
        # items
        for it in self.items:
            sy = self._sy(it.y)
            if it.kind == "diamond":
                s = 9
                pts = [(it.x, sy - s), (it.x + s * 0.75, sy), (it.x, sy + s), (it.x - s * 0.75, sy)]
                pygame.draw.polygon(surf, ACCENT, pts)
                pygame.draw.polygon(surf, (230, 240, 250), pts, 2)
            else:
                pygame.draw.circle(surf, WARN, (int(it.x), sy), 9)
                pygame.draw.circle(surf, GOED, (int(it.x + 2), sy - 9), 3)
        # vijanden
        for e in self.enemies:
            sy = self._sy(e.y)
            pygame.draw.rect(surf, PURPLE, (int(e.x), sy, e.w, e.h), border_radius=7)
            ex = 6 if e.vx > 0 else -6
            pygame.draw.circle(surf, (255, 255, 255), (int(e.x + e.w / 2 - 5 + ex * 0.3), sy + 9), 4)
            pygame.draw.circle(surf, (255, 255, 255), (int(e.x + e.w / 2 + 5 + ex * 0.3), sy + 9), 4)
            pygame.draw.circle(surf, (20, 20, 24), (int(e.x + e.w / 2 - 5 + ex * 0.5), sy + 9), 2)
            pygame.draw.circle(surf, (20, 20, 24), (int(e.x + e.w / 2 + 5 + ex * 0.5), sy + 9), 2)
        # speler
        if self.alive and (self.invuln <= 0 or int(self.invuln * 12) % 2 == 0):
            self._draw_player(surf)
        # water
        wsy = self._sy(self.water_y)
        if wsy < HEIGHT:
            ov = pygame.Surface((WIDTH, HEIGHT - max(HUD_H, wsy)), pygame.SRCALPHA)
            ov.fill((WATER[0], WATER[1], WATER[2], 150))
            surf.blit(ov, (0, max(HUD_H, wsy)))
            for x in range(0, WIDTH, 16):
                yy = wsy + int(3 * math.sin(x * 0.06 + self.cam_y * 0.05))
                pygame.draw.circle(surf, mix(WATER, (255, 255, 255), 0.3), (x, yy), 2)

    def _draw_player(self, surf):
        f = self.facing
        sx = int(self.px)
        sy = self._sy(self.py)
        cx = sx + PW // 2
        skin = (236, 198, 168)
        shirt = (111, 163, 214)
        # benen
        pygame.draw.rect(surf, (60, 60, 70), (cx - 7, sy + 26, 5, 8), border_radius=2)
        pygame.draw.rect(surf, (60, 60, 70), (cx + 2, sy + 26, 5, 8), border_radius=2)
        # romp
        pygame.draw.rect(surf, shirt, (sx + 4, sy + 14, PW - 8, 14), border_radius=4)
        # hoofd
        hx = cx + f
        pygame.draw.circle(surf, skin, (hx, sy + 9), 8)
        pygame.draw.circle(surf, (176, 128, 96), (hx, sy + 9), 8, 2)
        for s in (-3, 3):
            pygame.draw.circle(surf, (255, 255, 255), (hx + s + f * 2, sy + 8), 2)
            pygame.draw.circle(surf, (24, 24, 28), (hx + s + f * 2 + f, sy + 8), 1)


# ----------------------------------------------------------------------------
def t_made_by():
    return t("made_by")


def run_splash(tts):
    SW, SH = 580, 420
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    icon = load_window_icon()
    if icon is not None:
        pygame.display.set_icon(icon)
    try:
        win = pygame.display.set_mode((SW, SH), pygame.NOFRAME)
    except Exception:
        win = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption(APP_NAME)
    if icon is not None:
        pygame.display.set_icon(icon)
    try:
        logo = pygame.image.load(resource_path("assets/logo_t.png")).convert_alpha()
    except Exception:
        try:
            logo = pygame.image.load(resource_path("assets/logo.png")).convert_alpha()
        except Exception:
            logo = None
    f_title = pygame.font.Font(None, 66)
    f_sub = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()
    cfg = load_config()
    set_lang(cfg.get("lang") or detect_os_lang())
    voice_on = cfg.get("voice", True)
    logo_img = pygame.transform.smoothscale(logo, (230, 230)) if logo else None
    title_img = f_title.render(APP_NAME, True, ACCENT)
    sub_img = f_sub.render(t_made_by(), True, MUTED)
    t0 = 0.0
    spoke = False
    proceed = True
    skipped = False
    speak_time = None
    use_voice = bool(tts and voice_on)
    while True:
        dt = min(clock.tick(60) / 1000.0, 1 / 30.0)
        t0 += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                proceed = False
                skipped = True
            elif e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                skipped = True
        if t0 >= 1.5 and not spoke:
            spoke = True
            if use_voice:
                tts.speak("%s. %s" % (APP_NAME, t_made_by()))
                speak_time = t0
        win.fill(BG)
        pygame.draw.rect(win, PANEL, (0, 0, SW, SH))
        pygame.draw.rect(win, ACCENT, (0, 0, SW, SH), width=2)

        def fade(start, dur):
            return int(clamp((t0 - start) / dur, 0.0, 1.0) * 255)

        if logo_img is not None:
            logo_img.set_alpha(fade(0.0, 0.7))
            win.blit(logo_img, logo_img.get_rect(center=(SW // 2, 150)))
        title_img.set_alpha(fade(0.55, 0.5))
        win.blit(title_img, title_img.get_rect(center=(SW // 2, 312)))
        sub_img.set_alpha(fade(1.0, 0.5))
        win.blit(sub_img, sub_img.get_rect(center=(SW // 2, 362)))
        pygame.display.flip()
        if skipped:
            break
        if use_voice:
            if spoke and not tts.busy() and t0 > (speak_time or 0) + 0.3:
                break
            if spoke and t0 > (speak_time or 0) + 16:
                break
        else:
            if t0 >= 3.0:
                break
    return proceed


# ----------------------------------------------------------------------------
class App:
    def __init__(self, screen, tts=None, start_state="title"):
        self.screen = screen
        self.cfg = load_config()
        set_lang(self.cfg.get("lang") or detect_os_lang())
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = start_state
        self.t_state = 0.0

        self.font_xl = pygame.font.Font(None, 72)
        self.font_l = pygame.font.Font(None, 50)
        self.font_m = pygame.font.Font(None, 32)
        self.font_s = pygame.font.Font(None, 26)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.game = None
        self.run_score = 0
        self.run_lives = 3
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)

        self.voice_on = self.cfg.get("voice", True)
        self.tts = tts
        if self.tts is None and ttsmod is not None:
            self.tts = ttsmod.Tts(voice=self.cfg.get("voice_name", "M1"), data_dir=config_dir())
        if self.tts is not None:
            self.tts.enabled = self.voice_on

        try:
            _ic = load_window_icon()
            if _ic is not None:
                pygame.display.set_icon(_ic)
        except Exception:
            pass
        try:
            self.logo = pygame.image.load(resource_path("assets/logo_t.png")).convert_alpha()
        except Exception:
            self.logo = None

    def music_for_state(self):
        if not self.sfx:
            return
        if self.state in ("title", "settings", "help", "gameover", "victory", "levelclear"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            self.sfx.start_music("play1" if (self.game and self.game.level % 2 == 0) else "play2")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        self.music_for_state()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30.0)
            self.t_state += dt
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                self.on_key(e.key)
            elif e.type == pygame.MOUSEMOTION:
                self.mouse = e.pos
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.on_click(e.pos, e.button)

    def _action(self, a):
        if a is None:
            return
        if self.sfx:
            self.sfx.play("click")
        if a == "play":
            self.run_score = 0
            self.run_lives = 3
            self.start_game(0)
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "back_title":
            self.set_state("title")
        elif a == "resume":
            self.set_state("play")
        elif a == "pause":
            self.set_state("pause")
        elif a == "retry":
            self.run_score = 0
            self.run_lives = 3
            self.start_game(0)
        elif a == "to_title":
            self.set_state("title")
        elif a == "next_level":
            self.start_game(self.game.level + 1)
        elif a == "toggle_sound":
            self.cfg["sound"] = not self.cfg.get("sound", True)
            if self.sfx:
                self.sfx.set_enabled(self.cfg["sound"])
            save_config(self.cfg)
        elif a == "toggle_music":
            self.cfg["music"] = not self.cfg.get("music", True)
            save_config(self.cfg)
            self.music_for_state()
        elif a == "toggle_voice":
            self.voice_on = not self.voice_on
            self.cfg["voice"] = self.voice_on
            if self.tts:
                self.tts.enabled = self.voice_on
            save_config(self.cfg)
        elif a == "vol_down":
            self.cfg["volume"] = clamp(self.cfg.get("volume", 0.8) - 0.1, 0, 1)
            if self.sfx:
                self.sfx.set_volume(self.cfg["volume"])
            save_config(self.cfg)
        elif a == "vol_up":
            self.cfg["volume"] = clamp(self.cfg.get("volume", 0.8) + 0.1, 0, 1)
            if self.sfx:
                self.sfx.set_volume(self.cfg["volume"])
            save_config(self.cfg)
        elif a == "cycle_lang":
            cur = self.cfg.get("lang", "")
            nxt = {"": "nl", "nl": "en", "en": ""}[cur]
            self.cfg["lang"] = nxt
            set_lang(nxt or detect_os_lang())
            save_config(self.cfg)
        elif a == "donate":
            try:
                webbrowser.open(DONATIE)
            except Exception:
                pass

    def _back_for_state(self):
        return {"help": "back_title", "settings": "back_title", "pause": "resume",
                "gameover": "to_title", "victory": "to_title", "levelclear": "to_title"}.get(self.state)

    def on_key(self, key):
        if self.state == "play":
            g = self.game
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            elif key in (pygame.K_UP, pygame.K_w, pygame.K_z):
                g.do_jump()
            elif key == pygame.K_SPACE:
                g.do_fire()
            return
        if self.state == "levelclear" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("next_level"); return
        if self.state in ("gameover", "victory") and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("retry" if self.state == "gameover" else "to_title"); return
        if key == pygame.K_ESCAPE:
            self._action(self._back_for_state())
            return
        if not self.buttons:
            return
        if key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            self.focus = (self.focus - 1) % len(self.buttons)
            if self.sfx:
                self.sfx.play("click")
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            self.focus = (self.focus + 1) % len(self.buttons)
            if self.sfx:
                self.sfx.play("click")
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.focus = clamp(self.focus, 0, len(self.buttons) - 1)
            self._action(self.buttons[self.focus].action)

    def on_click(self, pos, button):
        if button != 1:
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    def start_game(self, level):
        level = clamp(level, 0, N_LEVELS - 1)
        self.game = Game(self, level)
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            keys = pygame.key.get_pressed()
            vx = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                vx -= MOVE_SPEED
                self.game.facing = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                vx += MOVE_SPEED
                self.game.facing = 1
            self.game.vx = vx
            self.game.jump_held = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]
            self.game.update(dt)
            if self.game.finished and self.t_state > 0.3:
                if self.game.result == "dead":
                    self.set_state("gameover")
                elif self.game.result == "win":
                    self.set_state("victory")
                else:
                    self.set_state("levelclear")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st in ("play", "pause"):
            s.fill(BG)
            self.game.draw(s)
            self._draw_hud(s)
            if st == "pause":
                self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "levelclear":
            s.fill(BG)
            self.game.draw(s)
            self._overlay(s, t("eiland_klaar"), ["%s %d" % (t("score"), self.game.score)],
                          [(t("volgende"), "next_level"), (t("hoofdmenu"), "to_title")], color=GOED)
        elif st == "gameover":
            s.fill(BG)
            self.game.draw(s)
            self._overlay(s, t("gameover"),
                          ["%s %d   %s %d" % (t("score"), self.game.score, t("best"), self.cfg.get("highscore", 0))],
                          [(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")], color=WARN)
        elif st == "victory":
            self._draw_victory(s)
        self._draw_buttons(s)

    def _text(self, surf, txt, font, color, cx, y, center=True):
        img = font.render(txt, True, color)
        r = img.get_rect()
        if center:
            r.center = (cx, y)
        else:
            r.topleft = (cx, y)
        surf.blit(img, r)
        return r

    def _add_button(self, label, rect, action, kind="normal"):
        self.buttons.append(Button(label, rect, action, kind=kind))

    def _add_donate(self):
        self._add_button(t("donatie"), (WIDTH - 190, 14, 172, 46), "donate", kind="donate")

    def _stack(self, items, top, w=380, h=64, gap=18, kinds=None):
        x = WIDTH // 2 - w // 2
        y = top
        for i, (label, action) in enumerate(items):
            kind = kinds[i] if (kinds and i < len(kinds)) else "normal"
            self._add_button(label, (x, y, w, h), action, kind=kind)
            y += h + gap

    def _draw_buttons(self, s):
        if not self.buttons:
            return
        if self.focus >= len(self.buttons):
            self.focus = 0
        play_like = self.state in ("play", "pause", "gameover", "levelclear", "victory")
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, hot=b.hit(self.mouse), focus=(i == self.focus and not play_like))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=210, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "%s: %d" % (t("best"), self.cfg.get("highscore", 0)),
                   self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 70)
        y = 160
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_s, TEXT, WIDTH // 2, y)
            y += 46
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 56), "back_title", kind="back")
        self._add_donate()

    def _draw_settings(self, s):
        s.fill(BG)
        self._text(s, t("instellingen"), self.font_l, ACCENT, WIDTH // 2, 56)
        on = lambda b: t("aan") if b else t("uit")
        lang = {"": t("auto"), "nl": "Nederlands", "en": "English"}[self.cfg.get("lang", "")]
        w = 460
        x = WIDTH // 2 - w // 2
        y = 130
        self._add_button("%s: %s" % (t("geluid"), on(self.cfg.get("sound", True))), (x, y, w, 54), "toggle_sound"); y += 66
        self._add_button("%s: %s" % (t("muziek"), on(self.cfg.get("music", True))), (x, y, w, 54), "toggle_music"); y += 66
        self._add_button("%s: %s" % (t("stem"), on(self.voice_on)), (x, y, w, 54), "toggle_voice"); y += 66
        self._text(s, "%s: %d%%" % (t("volume"), int(self.cfg.get("volume", 0.8) * 100)),
                   self.font_m, TEXT, WIDTH // 2, y + 27)
        self._add_button("-", (x, y, 70, 54), "vol_down")
        self._add_button("+", (x + w - 70, y, 70, 54), "vol_up"); y += 66
        self._add_button("%s: %s" % (t("taal"), lang), (x, y, w, 54), "cycle_lang")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 70, 220, 52), "back_title", kind="back")
        self._add_donate()

    def _draw_hud(self, s):
        g = self.game
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, HUD_H))
        pygame.draw.line(s, LINE, (0, HUD_H), (WIDTH, HUD_H), 2)
        self._text(s, "%s %d" % (t("eiland"), g.level + 1), self.font_m, ACCENT, 20, HUD_H // 2, center=False)
        self._text(s, "%s %d" % (t("score"), g.score), self.font_m, GOLD, 200, HUD_H // 2, center=False)
        # hoogte-balk
        prog = clamp(1 - (g.py - g.goal[1]) / max(1, g.world_h - g.goal[1]), 0, 1)
        pygame.draw.rect(s, PANEL2, (430, HUD_H // 2 - 8, 180, 16), border_radius=8)
        pygame.draw.rect(s, GOED, (430, HUD_H // 2 - 8, int(180 * prog), 16), border_radius=8)
        for i in range(max(0, g.lives)):
            draw_heart(s, 720 + i * 28, HUD_H // 2, 9, RED)
        if self.state == "play":
            self._add_button(t("pauze"), (WIDTH - 120, 7, 104, 32), "pause", kind="back")

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 160)
        y = 250
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 44
        if buttons_def:
            self._stack(buttons_def, top=max(y + 10, 320), w=360, h=64, gap=18,
                        kinds=["primary"] + ["normal"] * (len(buttons_def) - 1))

    def _draw_victory(self, s):
        s.fill(BG)
        if self.logo:
            lg = pygame.transform.smoothscale(self.logo, (150, 150))
            s.blit(lg, (WIDTH // 2 - 75, 50))
        self._text(s, t("gewonnen"), self.font_xl, GOLD, WIDTH // 2, 240)
        self._text(s, "%s %d" % (t("score"), self.game.score), self.font_l, TEXT, WIDTH // 2, 305)
        self._stack([(t("hoofdmenu"), "to_title")], top=370, w=360, h=64, gap=18, kinds=["primary"])


# ----------------------------------------------------------------------------
def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    icon = load_window_icon()
    if icon is not None:
        pygame.display.set_icon(icon)
    tts = None
    if ttsmod is not None:
        cfg0 = load_config()
        tts = ttsmod.Tts(voice=cfg0.get("voice_name", "M1"), data_dir=config_dir())
        tts.enabled = cfg0.get("voice", True)
    if not run_splash(tts):
        pygame.quit()
        return
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    if icon is not None:
        pygame.display.set_icon(icon)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(APP_NAME)
    if icon is not None:
        pygame.display.set_icon(icon)
    app = App(screen, tts=tts, start_state="title")
    app.music_for_state()
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()

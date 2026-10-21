# -*- coding: utf-8 -*-
"""arrow.py - DraveArrow, een boogschutter-spel van Dravenlock Games.

Richt met de muis of met de pijltjestoetsen (hoek) en de spatiebalk (kracht).
De pijl volgt een echte boog door de zwaartekracht, met wind in latere rondes.
Een stippellijn toont de baan (handig bij slecht zicht). Drie modi:
- Schietbaan: raak alle schietschijven (roos = meeste punten).
- Precisie:   kleine doelen, weinig pijlen, veel wind.
- Verdediging: schiet vijanden neer voor ze je bereiken; draak als eindbaas.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke HUD; procedurele muziek en geluiden (sfx.py); gesproken intro
(neuvoice) in een apart splashvenster.
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

APP_NAME = "DraveArrow"
APP_VERSION = "0.1.4"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
GROUND_Y = HEIGHT - 70
GRAVITY = 650.0            # px/s^2 (vlakkere, verder reikende baan)
ARROW_MIN_SPEED = 700.0
ARROW_MAX_SPEED = 1350.0
CHARGE_TIME = 0.9          # s tot volle kracht

# ---- donker Dravenlock-palet ----
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
SKY_TOP = (24, 28, 40)
SKY_BOT = (40, 46, 62)
GROUND = (38, 44, 34)


# ----------------------------------------------------------------------------
# Config + taal
# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script),
    nooit in systeemmappen zoals %APPDATA%. Veel mensen hebben een kleine
    C-schijf en willen daar geen overbodige data."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveArrow-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        # alleen als de map naast de .exe niet beschrijfbaar is (zeldzaam):
        # tijdelijke map, zodat het spel niet crasht
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveArrow-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "mode": "schietbaan", "trajectory": True,
    "best_schietbaan": 0, "best_precisie": 0, "best_verdediging": 0, "highscore": 0,
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
    "onder": {"nl": "Een boogschutter-spel van Dravenlock Games",
              "en": "An archery game by Dravenlock Games"},
    "made_by": {"nl": "Gemaakt door Dravenlock Games", "en": "Made by Dravenlock Games"},
    "donatie": {"nl": "Donatie", "en": "Donate"},
    "speel": {"nl": "Spelen", "en": "Play"},
    "gids": {"nl": "Hoe te spelen", "en": "How to play"},
    "instellingen": {"nl": "Instellingen", "en": "Settings"},
    "terug": {"nl": "Terug", "en": "Back"},
    "start": {"nl": "Start", "en": "Start"},
    "kies_modus": {"nl": "Kies modus", "en": "Choose mode"},
    "modus": {"nl": "Modus", "en": "Mode"},
    "schietbaan": {"nl": "Schietbaan", "en": "Range"},
    "precisie": {"nl": "Precisie", "en": "Precision"},
    "verdediging": {"nl": "Verdediging", "en": "Defense"},
    "doel_schietbaan": {"nl": "Raak alle schijven; de roos geeft de meeste punten.",
                        "en": "Hit every target; the bullseye scores most."},
    "doel_precisie": {"nl": "Kleine doelen, weinig pijlen, veel wind.",
                     "en": "Tiny targets, few arrows, lots of wind."},
    "doel_verdediging": {"nl": "Schiet vijanden neer voor ze je bereiken.",
                        "en": "Shoot enemies before they reach you."},
    "geluid": {"nl": "Geluid", "en": "Sound"},
    "muziek": {"nl": "Muziek", "en": "Music"},
    "stem": {"nl": "Stem", "en": "Voice"},
    "volume": {"nl": "Volume", "en": "Volume"},
    "taal": {"nl": "Taal", "en": "Language"},
    "baan_lijn": {"nl": "Baanlijn", "en": "Aim line"},
    "aan": {"nl": "aan", "en": "on"},
    "uit": {"nl": "uit", "en": "off"},
    "auto": {"nl": "OS", "en": "OS"},
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "hervat": {"nl": "Hervatten", "en": "Resume"},
    "hoofdmenu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "opnieuw": {"nl": "Opnieuw", "en": "Retry"},
    "volgende": {"nl": "Volgende ronde", "en": "Next round"},
    "ronde": {"nl": "Ronde", "en": "Round"},
    "golf": {"nl": "Golf", "en": "Wave"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "pijlen": {"nl": "Pijlen", "en": "Arrows"},
    "pijlen_mee": {"nl": "Pijlen mee", "en": "Arrows carried"},
    "leven": {"nl": "Leven", "en": "HP"},
    "wind": {"nl": "Wind", "en": "Wind"},
    "kracht": {"nl": "Kracht", "en": "Power"},
    "klaar": {"nl": "Ronde gehaald!", "en": "Round cleared!"},
    "gewonnen": {"nl": "Gewonnen!", "en": "You win!"},
    "verloren": {"nl": "Verloren", "en": "Game over"},
    "richten_muis": {"nl": "Richten: beweeg de muis", "en": "Aim: move the mouse"},
    "schiet_muis": {"nl": "Schieten: houd muisknop vast en laat los",
                    "en": "Shoot: hold mouse button, release"},
    "richten_t": {"nl": "Of: pijl omhoog/omlaag = hoek", "en": "Or: Up/Down = angle"},
    "schiet_t": {"nl": "Spatie vasthouden = spannen, loslaten = schieten",
                 "en": "Hold Space = draw, release = shoot"},
    "pauze_t": {"nl": "Esc of P = pauze", "en": "Esc or P = pause"},
    "klik_start": {"nl": "Druk Enter of klik om te starten",
                   "en": "Press Enter or click to start"},
}


def t(key):
    e = TR.get(key, {})
    return e.get(_LANG, e.get("nl", key))


# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# Knop
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
        pygame.draw.rect(surf, bg, r, border_radius=12)
        pygame.draw.rect(surf, ACCENT if (hot or focus) else LINE, r,
                         width=3 if (hot or focus) else 2, border_radius=12)
        col = TEXT if not (hot or focus) else (245, 245, 248)
        if self.kind == "donate":
            draw_heart(surf, r.left + 26, r.centery, 11, WARN if not (hot or focus) else (235, 120, 110))
            surf.blit(font.render(self.label, True, col),
                      font.render(self.label, True, col).get_rect(midleft=(r.left + 46, r.centery)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


# ----------------------------------------------------------------------------
# Entiteiten
# ----------------------------------------------------------------------------
class Arrow:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.stuck = 0.0

    def tip(self):
        return self.x, self.y

    def update(self, dt, wind):
        if not self.alive:
            return
        self.vy += GRAVITY * dt
        self.vx += wind * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x > WIDTH + 60 or self.x < -60 or self.y > GROUND_Y:
            self.alive = False

    def angle(self):
        return math.atan2(self.vy, self.vx)


class Target:
    def __init__(self, x, y, outer, move=0.0, span=0.0):
        self.x = x
        self.y = y
        self.outer = outer
        self.base_y = y
        self.move = move          # snelheid op/neer
        self.span = span          # amplitude
        self.phase = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt, t):
        if self.span > 0:
            self.y = self.base_y + math.sin(t * self.move + self.phase) * self.span

    def score_for(self, px, py):
        d = math.hypot(px - self.x, py - self.y)
        if d > self.outer:
            return None
        f = d / self.outer
        if f < 0.2:
            return 100
        if f < 0.45:
            return 60
        if f < 0.7:
            return 30
        return 10


class Enemy:
    def __init__(self, x, y, kind, hp, speed, flying=False):
        self.x = x
        self.y = y
        self.base_y = y
        self.kind = kind
        self.hp = hp
        self.speed = speed
        self.flying = flying
        self.phase = random.uniform(0, math.tau)
        self.alive = True
        self.reached = False
        self.r = 26 if kind != "dragon" else 60

    def update(self, dt, t):
        self.x -= self.speed * dt
        if self.flying:
            self.y = self.base_y + math.sin(t * 3 + self.phase) * 26


class Pop:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.t = 0.0


# ----------------------------------------------------------------------------
# Sprites
# ----------------------------------------------------------------------------
def draw_archer(surf, x, y, angle, charge):
    # lijf
    pygame.draw.rect(surf, mix(ACCENT, BG, 0.3), (x - 8, y - 42, 16, 42), border_radius=6)
    pygame.draw.circle(surf, (224, 200, 170), (x, y - 50), 10)   # hoofd
    pygame.draw.circle(surf, mix(GOED, BG, 0.2), (x, y - 57), 12, width=3)  # kap
    # boog (gebogen) op aim-hoek
    bx, by = x + 5, y - 38
    a = angle
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    span = 24
    bend = 5 + charge * 9
    p_top = (bx + px * span, by + py * span)
    p_bot = (bx - px * span, by - py * span)
    p_mid = (bx + ux * bend, by + uy * bend)
    pygame.draw.lines(surf, GOLD, False, [p_top, p_mid, p_bot], 3)
    # pees
    draw = charge * 13
    nock = (bx - ux * draw, by - uy * draw)
    pygame.draw.line(surf, (210, 210, 215), p_top, nock, 2)
    pygame.draw.line(surf, (210, 210, 215), p_bot, nock, 2)
    # pijl op de pees (als je spant)
    if charge > 0.02:
        tip = (bx + ux * 24, by + uy * 24)
        pygame.draw.line(surf, (220, 220, 225), nock, tip, 3)


def draw_arrow(surf, ax, ay, ang):
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    tail = (ax - ux * 30, ay - uy * 30)
    pygame.draw.line(surf, (225, 225, 230), tail, (ax, ay), 3)
    pygame.draw.polygon(surf, GOLD, [(ax, ay), (ax - ux * 10 + px * 5, ay - uy * 10 + py * 5),
                                     (ax - ux * 10 - px * 5, ay - uy * 10 - py * 5)])
    # veren
    pygame.draw.line(surf, WARN, tail, (tail[0] + px * 6 - ux * 4, tail[1] + py * 6 - uy * 4), 2)
    pygame.draw.line(surf, WARN, tail, (tail[0] - px * 6 - ux * 4, tail[1] - py * 6 - uy * 4), 2)


def draw_target(surf, tg):
    x, y, o = int(tg.x), int(tg.y), int(tg.outer)
    pygame.draw.circle(surf, (235, 235, 238), (x, y), o)
    pygame.draw.circle(surf, (40, 40, 48), (x, y), o, 2)
    pygame.draw.circle(surf, ACCENT, (x, y), int(o * 0.7))
    pygame.draw.circle(surf, RED, (x, y), int(o * 0.45))
    pygame.draw.circle(surf, GOLD, (x, y), int(o * 0.2))
    pygame.draw.circle(surf, (60, 50, 20), (x, y), max(2, int(o * 0.06)))


def draw_enemy(surf, e):
    x, y = int(e.x), int(e.y)
    if e.kind == "dragon":
        draw_dragon(surf, x, y)
        return
    col = {"goblin": GOED, "skelet": (210, 210, 215), "vleermuis": PURPLE}.get(e.kind, GOED)
    if e.kind == "vleermuis":
        pygame.draw.circle(surf, col, (x, y), 12)
        pygame.draw.polygon(surf, col, [(x - 12, y), (x - 26, y - 8), (x - 18, y + 6)])
        pygame.draw.polygon(surf, col, [(x + 12, y), (x + 26, y - 8), (x + 18, y + 6)])
    else:
        pygame.draw.rect(surf, col, (x - 13, y - 18, 26, 36), border_radius=6)
        pygame.draw.circle(surf, mix(col, (255, 255, 255), 0.2), (x, y - 24), 11)
        if e.kind == "skelet":
            pygame.draw.circle(surf, (30, 30, 36), (x - 4, y - 25), 2)
            pygame.draw.circle(surf, (30, 30, 36), (x + 4, y - 25), 2)
    # mini hp-streepje
    if e.hp > 1:
        pygame.draw.rect(surf, (0, 0, 0), (x - 14, y - 34, 28, 5))
        pygame.draw.rect(surf, GOED, (x - 14, y - 34, int(28 * min(1, e.hp / 3.0)), 5))


def draw_dragon(surf, x, y):
    pygame.draw.ellipse(surf, mix(RED, BG, 0.1), (x - 55, y - 34, 110, 68))
    pygame.draw.polygon(surf, mix(RED, BG, 0.25), [(x - 40, y - 30), (x - 80, y - 60), (x - 30, y - 14)])
    pygame.draw.polygon(surf, mix(RED, BG, 0.25), [(x + 40, y - 30), (x + 80, y - 60), (x + 30, y - 14)])
    pygame.draw.circle(surf, (40, 16, 16), (x - 50, y - 6), 20)
    pygame.draw.polygon(surf, GOLD, [(x - 70, y - 10), (x - 62, y - 16), (x - 60, y - 4)])
    pygame.draw.circle(surf, GOLD, (x - 56, y - 12), 4)


# ----------------------------------------------------------------------------
# Spel
# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app, mode, level):
        self.app = app
        self.mode = mode
        self.level = level
        self.rng = random.Random(700 + level * 13)
        self.ax = 120
        self.ay = GROUND_Y
        self.angle = -0.6        # rad (omhoog naar rechts)
        self.charge = 0.0
        self.charging = False
        self.arrow = None
        self.shot_cd = 0.0
        self.t = 0.0
        self.score = 0
        self.finished = False
        self.result = None
        self.message = ""
        self.pops = []
        self.targets = []
        self.enemies = []
        self.spawn_queue = []
        self.spawn_t = 0.0
        self.wind = 0.0
        self.hp = 5
        self.arrows = 99
        self.carry_bonus = 0
        self.arrows_start = 0
        self.hurt_flash = 0.0
        self.boss = None
        self._setup()

    def _setup(self):
        rng = self.rng
        lv = self.level
        if self.mode in ("schietbaan", "precisie"):
            small = self.mode == "precisie"
            # geleidelijker: wind en bewegende doelen pas vanaf ronde 3,
            # en milder dan eerst
            self.wind = (rng.uniform(-1, 1) * (40 + lv * 16)) if lv >= 3 else 0.0
            n = (2 + lv // 2) if small else (2 + lv)
            for _ in range(n):
                tx = rng.uniform(WIDTH * 0.42, WIDTH - 80)
                ty = rng.uniform(170, GROUND_Y - 70)
                outer = rng.uniform(22, 32) if small else rng.uniform(36, 54)
                moving = (lv >= 3 and rng.random() < (0.5 if small else 0.35))
                self.targets.append(Target(tx, ty, outer,
                                           move=rng.uniform(1.0, 2.0) if moving else 0,
                                           span=rng.uniform(40, 100) if moving else 0))
            # ruimere basis + overgebleven pijlen uit de vorige ronde meenemen
            spare = 2 if small else 4
            carry = max(0, min(getattr(self.app, "carry_arrows", 0), 12))
            self.arrows = len(self.targets) + spare + carry
            self.carry_bonus = carry
            self.arrows_start = self.arrows
        else:  # verdediging
            self.wind = (rng.uniform(-1, 1) * (40 + lv * 15)) if lv >= 3 else 0.0
            self.hp = 5
            self.arrows = 99
            boss_wave = 6
            if lv >= boss_wave:
                self.boss = Enemy(WIDTH - 90, GROUND_Y - 90, "dragon", 24 + lv * 2, 24, flying=True)
                self.enemies.append(self.boss)
            count = 4 + lv * 2
            for i in range(count):
                kind = rng.choice(["goblin", "goblin", "skelet"] + (["vleermuis"] if lv >= 2 else []))
                flying = kind == "vleermuis"
                hp = 1 + (1 if (kind == "skelet" and lv >= 3) else 0)
                spd = (40 + lv * 8) * rng.uniform(0.85, 1.15)
                y = (GROUND_Y - 18) if not flying else rng.uniform(160, GROUND_Y - 140)
                self.spawn_queue.append((i * rng.uniform(0.9, 1.6) + 0.5,
                                         Enemy(WIDTH + 40, y, kind, hp, spd, flying)))

    # ---------- invoer ----------
    def aim_to(self, mx, my):
        a = math.atan2(my - (self.ay - 40), mx - (self.ax + 6))
        self.angle = clamp(a, -1.55, 0.25)

    def adjust_angle(self, d):
        self.angle = clamp(self.angle + d, -1.55, 0.25)

    def start_charge(self):
        if self.arrow is None and self.shot_cd <= 0 and self.arrows > 0:
            self.charging = True
            if self.app.sfx:
                self.app.sfx.start_draw()

    def release(self):
        if not self.charging:
            return
        self.charging = False
        if self.app.sfx:
            self.app.sfx.stop_draw()
        if self.arrow is not None or self.arrows <= 0:
            self.charge = 0.0
            return
        speed = lerp(ARROW_MIN_SPEED, ARROW_MAX_SPEED, self.charge)
        if self.charge < 0.05:
            self.charge = 0.0
            return
        vx = math.cos(self.angle) * speed
        vy = math.sin(self.angle) * speed
        self.arrow = Arrow(self.ax + 6 + math.cos(self.angle) * 30,
                           self.ay - 40 + math.sin(self.angle) * 30, vx, vy)
        self.arrows -= 1
        self.charge = 0.0
        self.shot_cd = 0.15
        if self.app.sfx:
            self.app.sfx.play("shoot")

    # ---------- update ----------
    def update(self, dt, keys):
        if self.finished:
            return
        self.t += dt
        self.shot_cd = max(0, self.shot_cd - dt)
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self.charging:
            self.charge = clamp(self.charge + dt / CHARGE_TIME, 0, 1)

        # toetsen-richten
        if keys.get("up"):
            self.adjust_angle(-1.4 * dt)
        if keys.get("down"):
            self.adjust_angle(1.4 * dt)

        for tg in self.targets:
            tg.update(dt, self.t)

        # spawn vijanden
        if self.mode == "verdediging":
            self.spawn_t += dt
            due = [e for (tm, e) in self.spawn_queue if tm <= self.spawn_t]
            self.spawn_queue = [(tm, e) for (tm, e) in self.spawn_queue if tm > self.spawn_t]
            for e in due:
                self.enemies.append(e)
            for e in self.enemies:
                e.update(dt, self.t)
                if e.x <= self.ax + 20 and not e.reached and e.alive:
                    e.reached = True
                    e.alive = False
                    if e is self.boss:
                        self.hp = 0
                    else:
                        self.hp -= 1
                    self.hurt_flash = 0.5
                    self.pops.append(Pop(self.ax + 30, self.ay - 70, "-1", RED))
                    if self.app.sfx:
                        self.app.sfx.play("hurt")
            self.enemies = [e for e in self.enemies if e.alive]

        # pijl
        if self.arrow is not None:
            self.arrow.update(dt, self.wind)
            self._collisions()
            if not self.arrow.alive:
                if self.app.sfx and self.arrow.y >= GROUND_Y:
                    self.app.sfx.play("thunk")
                self.arrow = None
        self.targets = [tg for tg in self.targets if tg.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        # pop-ups
        for p in self.pops:
            p.t += dt
            p.y -= 30 * dt
        self.pops = [p for p in self.pops if p.t < 1.0]

        self._check_end()

    def _collisions(self):
        ar = self.arrow
        px, py = ar.tip()
        # doelen
        for tg in self.targets:
            if not tg.alive:
                continue
            sc = tg.score_for(px, py)
            if sc is not None:
                tg.alive = False
                self.score += sc
                self.pops.append(Pop(tg.x, tg.y, "+%d" % sc, GOLD if sc >= 100 else TEXT))
                ar.alive = False
                if self.app.sfx:
                    self.app.sfx.play("bull" if sc >= 100 else "ring")
                return
        self.targets = [t for t in self.targets if t.alive]
        # vijanden
        for e in self.enemies:
            if not e.alive:
                continue
            if math.hypot(px - e.x, py - e.y) <= e.r:
                e.hp -= 1
                ar.alive = False
                if e.hp <= 0:
                    e.alive = False
                    pts = 200 if e is self.boss else 25
                    self.score += pts
                    self.pops.append(Pop(e.x, e.y, "+%d" % pts, GOLD))
                    if self.app.sfx:
                        self.app.sfx.play("roar" if e is self.boss else "hit")
                else:
                    if self.app.sfx:
                        self.app.sfx.play("hit")
                self.enemies = [en for en in self.enemies if en.alive]
                return

    def _check_end(self):
        if self.mode in ("schietbaan", "precisie"):
            if not self.targets:
                self._win()
            elif self.arrows <= 0 and self.arrow is None:
                self._lose(t("verloren"))
        else:
            if self.hp <= 0:
                self._lose(t("verloren"))
            elif not self.spawn_queue and not self.enemies:
                self._win()

    def _win(self):
        if self.finished:
            return
        self.finished = True
        self.result = "win"
        self.message = t("klaar")
        if self.app.sfx:
            self.app.sfx.stop_draw()
            self.app.sfx.play("clear")

    def _lose(self, msg):
        if self.finished:
            return
        self.finished = True
        self.result = "lose"
        self.message = msg
        if self.app.sfx:
            self.app.sfx.stop_draw()
            self.app.sfx.play("defeat")

    # ---------- baanvoorspelling ----------
    def trajectory(self):
        pts = []
        pw = self.charge if self.charging else 0.78
        speed = lerp(ARROW_MIN_SPEED, ARROW_MAX_SPEED, pw)
        x = self.ax + 6 + math.cos(self.angle) * 30
        y = self.ay - 40 + math.sin(self.angle) * 30
        vx = math.cos(self.angle) * speed
        vy = math.sin(self.angle) * speed
        dt = 1 / 60.0
        for i in range(220):
            vy += GRAVITY * dt
            vx += self.wind * dt
            x += vx * dt
            y += vy * dt
            if y > GROUND_Y or x > WIDTH or x < 0:
                break
            if i % 3 == 0:
                pts.append((int(x), int(y)))
        return pts

    # ---------- tekenen ----------
    def draw(self, surf):
        # lucht + grond
        for i in range(0, HEIGHT, 4):
            c = mix(SKY_TOP, SKY_BOT, i / HEIGHT)
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        pygame.draw.rect(surf, GROUND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(surf, mix(GROUND, (0, 0, 0), 0.3), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        # doelen
        for tg in self.targets:
            # paaltje
            pygame.draw.line(surf, (80, 64, 40), (int(tg.x), int(tg.y + tg.outer)),
                             (int(tg.x), GROUND_Y), 4)
            draw_target(surf, tg)
        # vijanden
        for e in self.enemies:
            draw_enemy(surf, e)
            if e is self.boss:
                pygame.draw.rect(surf, (0, 0, 0), (WIDTH // 2 - 160, 64, 320, 16))
                pygame.draw.rect(surf, RED, (WIDTH // 2 - 160, 64,
                                             int(320 * clamp(e.hp / (24 + self.level * 2), 0, 1)), 16))

        # baanlijn (stippels)
        if self.app.cfg.get("trajectory", True) and self.arrow is None:
            for (px, py) in self.trajectory():
                pygame.draw.circle(surf, (180, 200, 220), (px, py), 2)

        # boogschutter
        draw_archer(surf, self.ax, self.ay, self.angle, self.charge)
        # pijl in de lucht
        if self.arrow is not None:
            draw_arrow(surf, self.arrow.x, self.arrow.y, self.arrow.angle())

        # pop-ups
        for p in self.pops:
            a = int(clamp(1 - p.t, 0, 1) * 255)
            img = self.app.font_s.render(p.text, True, p.color)
            img.set_alpha(a)
            surf.blit(img, img.get_rect(center=(int(p.x), int(p.y))))

        # rode flits als een vijand je bereikt (duidelijke schade)
        if self.hurt_flash > 0:
            f = self.hurt_flash / 0.5
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            edge = int(60 * f)
            for k in range(edge):
                al = int(120 * f * (1 - k / max(1, edge)))
                pygame.draw.rect(ov, (200, 40, 40, al), (k, k, WIDTH - 2 * k, HEIGHT - 2 * k), 1)
            surf.blit(ov, (0, 0))


# ----------------------------------------------------------------------------
# Splash (apart venster)
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

    f_title = pygame.font.Font(None, 84)
    f_sub = pygame.font.Font(None, 34)
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
    FADE_END = 1.5
    MIN_TIME = 3.0
    MAX_AFTER = 16.0
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
        if t0 >= FADE_END and not spoke:
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
        win.blit(title_img, title_img.get_rect(center=(SW // 2, 310)))
        sub_img.set_alpha(fade(1.0, 0.5))
        win.blit(sub_img, sub_img.get_rect(center=(SW // 2, 362)))
        pygame.display.flip()

        if skipped:
            break
        if use_voice:
            if spoke and not tts.busy() and t0 > (speak_time or 0) + 0.3:
                break
            if spoke and t0 > (speak_time or 0) + MAX_AFTER:
                break
        else:
            if t0 >= MIN_TIME:
                break
    return proceed


# ----------------------------------------------------------------------------
# App
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

        self.font_xl = pygame.font.Font(None, 84)
        self.font_l = pygame.font.Font(None, 56)
        self.font_m = pygame.font.Font(None, 38)
        self.font_s = pygame.font.Font(None, 28)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.mode = self.cfg.get("mode", "schietbaan")
        self.level = 1
        self.game = None
        self.carry_arrows = 0
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)
        self.keys = {"up": False, "down": False}

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

    # ---------- muziek ----------
    def music_for_state(self):
        if not self.sfx:
            return
        if self.state in ("title", "modeselect", "settings", "help"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            if self.mode == "verdediging" and self.game and self.game.boss:
                self.sfx.start_music("boss")
            else:
                self.sfx.start_music("play1" if self.level % 2 else "play2")
        elif self.state in ("roundclear", "victory"):
            self.sfx.start_music("victory")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        self.music_for_state()

    # ---------- loop ----------
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
                self.on_key_down(e.key)
            elif e.type == pygame.KEYUP:
                self.on_key_up(e.key)
            elif e.type == pygame.MOUSEMOTION:
                self.mouse = e.pos
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.on_mouse_down(e.pos, e.button)
            elif e.type == pygame.MOUSEBUTTONUP:
                self.on_mouse_up(e.pos, e.button)

    # ---------- acties ----------
    def _action(self, a):
        if a is None:
            return
        if self.sfx:
            self.sfx.play("click")
        if a == "play":
            self.set_state("modeselect")
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "mode_prev":
            self._cycle_mode(-1)
        elif a == "mode_next":
            self._cycle_mode(1)
        elif a == "start":
            if self.sfx:
                self.sfx.play("select")
            self.start_game(1)
        elif a == "back_title":
            self.set_state("title")
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
        elif a == "toggle_traj":
            self.cfg["trajectory"] = not self.cfg.get("trajectory", True)
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
        elif a == "pause":
            self.set_state("pause")
        elif a == "resume":
            self.set_state("play")
        elif a == "to_title":
            if self.sfx:
                self.sfx.stop_draw()
            self.set_state("title")
        elif a == "next_round":
            self.start_game(self.level + 1)
        elif a == "retry":
            self.start_game(1)
        elif a == "donate":
            try:
                webbrowser.open(DONATIE)
            except Exception:
                pass

    def _cycle_mode(self, d):
        order = ["schietbaan", "precisie", "verdediging"]
        i = (order.index(self.mode) + d) % len(order)
        self.mode = order[i]
        if self.sfx:
            self.sfx.play("click")

    def _back_for_state(self):
        return {"modeselect": "back_title", "help": "back_title", "settings": "back_title",
                "pause": "resume", "roundclear": "to_title", "gameover": "to_title",
                "victory": "to_title"}.get(self.state)

    # ---------- toetsen ----------
    def on_key_down(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            elif key in (pygame.K_UP, pygame.K_w):
                self.keys["up"] = True
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.keys["down"] = True
            elif key == pygame.K_SPACE:
                if self.game:
                    self.game.start_charge()
            return
        if key == pygame.K_ESCAPE:
            self._action(self._back_for_state())
            return
        if self.state == "modeselect" and key in (pygame.K_LEFT, pygame.K_a):
            self._action("mode_prev"); return
        if self.state == "modeselect" and key in (pygame.K_RIGHT, pygame.K_d):
            self._action("mode_next"); return
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

    def on_key_up(self, key):
        if self.state == "play":
            if key in (pygame.K_UP, pygame.K_w):
                self.keys["up"] = False
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.keys["down"] = False
            elif key == pygame.K_SPACE:
                if self.game:
                    self.game.release()

    def on_mouse_down(self, pos, button):
        if self.state == "play" and button == 1:
            if self.game:
                self.game.aim_to(*pos)
                self.game.start_charge()
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    def on_mouse_up(self, pos, button):
        if self.state == "play" and button == 1 and self.game:
            self.game.release()

    # ---------- spel ----------
    def start_game(self, level):
        self.level = level
        if level <= 1:
            self.carry_arrows = 0
        self.cfg["mode"] = self.mode
        save_config(self.cfg)
        self.game = Game(self, self.mode, level)
        self.countdown = 0.0
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            if self.state == "play" and self.mouse and pygame.mouse.get_focused():
                self.game.aim_to(*self.mouse)
            self.game.update(dt, self.keys)
            if self.game.finished:
                self._finish()

    def _finish(self):
        g = self.game
        if g.result == "win":
            if g.score > self.cfg.get("highscore", 0):
                self.cfg["highscore"] = g.score
            key = "best_" + self.mode
            if self.level > self.cfg.get(key, 0):
                self.cfg[key] = self.level
            save_config(self.cfg)
            # overgebleven pijlen meenemen naar de volgende ronde
            if self.mode in ("schietbaan", "precisie"):
                self.carry_arrows = max(0, g.arrows)
            last = {"schietbaan": 8, "precisie": 6, "verdediging": 6}.get(self.mode, 8)
            if self.level >= last:
                self.set_state("victory")
            else:
                self.set_state("roundclear")
        else:
            self.set_state("gameover")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "modeselect":
            self._draw_modeselect(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st == "play":
            self.game.draw(s)
            self._draw_hud(s)
        elif st == "pause":
            self.game.draw(s)
            self._draw_hud(s)
            self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "roundclear":
            self.game.draw(s)
            lines = ["%s %d   %s %d" % (t("score"), self.game.score, t("ronde"), self.level)]
            if self.mode in ("schietbaan", "precisie") and self.carry_arrows > 0:
                lines.append("%s: +%d" % (t("pijlen_mee"), self.carry_arrows))
            self._overlay(s, t("klaar"), lines,
                          [(t("volgende"), "next_round"), (t("hoofdmenu"), "to_title")], color=GOED)
        elif st == "gameover":
            self.game.draw(s)
            self._overlay(s, self.game.message or t("verloren"),
                          ["%s %d" % (t("score"), self.game.score)],
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
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, hot=b.hit(self.mouse), focus=(i == self.focus))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=200, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "%s: %d" % (t("best") + " " + t("score"), self.cfg.get("highscore", 0)),
                   self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_modeselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_modus"), self.font_l, ACCENT, WIDTH // 2, 56)
        names = {"schietbaan": t("schietbaan"), "precisie": t("precisie"), "verdediging": t("verdediging")}
        doel = {"schietbaan": t("doel_schietbaan"), "precisie": t("doel_precisie"),
                "verdediging": t("doel_verdediging")}
        self._add_button("< %s >" % names[self.mode], (WIDTH // 2 - 230, 150, 460, 70),
                         "mode_next", kind="primary")
        self._text(s, doel[self.mode], self.font_s, MUTED, WIDTH // 2, 250)
        # mini-uitleg richten
        self._text(s, t("richten_muis"), self.font_s, TEXT, WIDTH // 2, 320)
        self._text(s, t("schiet_muis"), self.font_s, TEXT, WIDTH // 2, 350)
        self._add_button(t("start"), (WIDTH // 2 - 200, HEIGHT - 110, 200, 64), "start", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 + 10, HEIGHT - 110, 190, 64), "back_title", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 48)
        lines = [t("richten_muis"), t("schiet_muis"), t("richten_t"), t("schiet_t"),
                 t("pauze_t"), "", t("doel_schietbaan"), t("doel_precisie"), t("doel_verdediging")]
        y = 120
        for ln in lines:
            self._text(s, ln, self.font_s if ln else self.font_s, TEXT, WIDTH // 2, y)
            y += 42
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 60), "back_title", kind="back")
        self._add_donate()

    def _draw_settings(self, s):
        s.fill(BG)
        self._text(s, t("instellingen"), self.font_l, ACCENT, WIDTH // 2, 48)
        on = lambda b: t("aan") if b else t("uit")
        lang = {"": t("auto"), "nl": "Nederlands", "en": "English"}[self.cfg.get("lang", "")]
        w = 460
        x = WIDTH // 2 - w // 2
        y = 116
        self._add_button("%s: %s" % (t("geluid"), on(self.cfg.get("sound", True))), (x, y, w, 52), "toggle_sound"); y += 64
        self._add_button("%s: %s" % (t("muziek"), on(self.cfg.get("music", True))), (x, y, w, 52), "toggle_music"); y += 64
        self._add_button("%s: %s" % (t("stem"), on(self.voice_on)), (x, y, w, 52), "toggle_voice"); y += 64
        self._add_button("%s: %s" % (t("baan_lijn"), on(self.cfg.get("trajectory", True))), (x, y, w, 52), "toggle_traj"); y += 64
        self._text(s, "%s: %d%%" % (t("volume"), int(self.cfg.get("volume", 0.8) * 100)),
                   self.font_m, TEXT, WIDTH // 2, y + 26)
        self._add_button("-", (x, y, 70, 52), "vol_down")
        self._add_button("+", (x + w - 70, y, 70, 52), "vol_up"); y += 64
        self._add_button("%s: %s" % (t("taal"), lang), (x, y, w, 52), "cycle_lang")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 72, 220, 52), "back_title", kind="back")
        self._add_donate()

    def _draw_hud(self, s):
        g = self.game
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, 50))
        self._text(s, "%s %d" % (t("score"), g.score), self.font_m, TEXT, 110, 25)
        rk = t("golf") if self.mode == "verdediging" else t("ronde")
        self._text(s, "%s %d" % (rk, self.level), self.font_m, ACCENT, WIDTH // 2 - 40, 25)
        if self.mode == "verdediging":
            hp_col = RED if (g.hurt_flash > 0 or g.hp <= 2) else GOED
            self._text(s, "%s %d" % (t("leven"), max(0, g.hp)), self.font_m,
                       hp_col, WIDTH - 130, 25)
        else:
            self._text(s, "%s %d" % (t("pijlen"), g.arrows), self.font_m, GOLD, WIDTH - 130, 25)
        # wind
        if abs(g.wind) > 1:
            wx = WIDTH // 2 + 120
            d = 1 if g.wind > 0 else -1
            self._text(s, t("wind"), self.font_s, MUTED, wx, 18, center=False)
            n = int(clamp(abs(g.wind) / 60, 1, 4))
            for k in range(n):
                xx = wx + 6 + k * 14
                pygame.draw.polygon(s, ACCENT, [(xx, 36), (xx + d * 10, 32), (xx, 28)])
        # krachtmeter
        pygame.draw.rect(s, PANEL2, (20, HEIGHT - 28, 220, 16), border_radius=6)
        pygame.draw.rect(s, mix(GOED, RED, g.charge), (20, HEIGHT - 28, int(220 * g.charge), 16), border_radius=6)
        self._text(s, t("kracht"), self.font_s, MUTED, 60, HEIGHT - 44)
        self._add_button(t("pauze"), (WIDTH - 130, 56, 110, 40), "pause", kind="back")

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 160)
        y = 250
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 48
        if buttons_def:
            self._stack(buttons_def, top=max(y + 10, 320), w=360, h=64, gap=18,
                        kinds=["primary"] + ["normal"] * (len(buttons_def) - 1))

    def _draw_victory(self, s):
        s.fill(BG)
        if self.logo:
            lg = pygame.transform.smoothscale(self.logo, (150, 150))
            s.blit(lg, (WIDTH // 2 - 75, 50))
        self._text(s, t("gewonnen"), self.font_xl, GOLD, WIDTH // 2, 240)
        self._text(s, "%s %d" % (t("score"), self.cfg.get("highscore", 0)), self.font_l, TEXT, WIDTH // 2, 310)
        self._stack([(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                    top=380, w=360, h=64, gap=18, kinds=["primary", "normal"])


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

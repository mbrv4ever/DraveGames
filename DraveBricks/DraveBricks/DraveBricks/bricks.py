# -*- coding: utf-8 -*-
"""bricks.py - DraveBricks, een Breakout/Arkanoid van Dravenlock Games.

Beweeg de peddel (muis of pijltjes), kaats de bal omhoog en sla alle stenen
kapot. Sommige stenen zijn steviger (meerdere klappen) of onverwoestbaar.
Power-ups vallen uit stenen; vang ze met de peddel:
  Breed  - bredere peddel        Multi  - splitst in drie ballen
  Traag  - langzamere bal        Plak   - bal blijft plakken (los met spatie)
  Laser  - peddel schiet         Vuur   - bal gaat dwars door stenen
  Leven  - extra leven
Verlies de bal onderaan en je raakt een leven kwijt. Maak alle levels leeg om te
winnen.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke HUD; procedurele muziek en geluiden (sfx.py); gesproken intro
(neuvoice) in een apart splashvenster. Volledig draagbaar: alles wordt bewaard
in een map "DraveBricks-data" naast het programma.
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

APP_NAME = "DraveBricks"
APP_VERSION = "0.1.0"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 44
WALL = 16
FIELD_L = WALL
FIELD_R = WIDTH - WALL
FIELD_T = HUD_H + 8
PADDLE_Y = HEIGHT - 40
PADDLE_W = 120
PADDLE_H = 16
BALL_R = 8
BASE_SPEED = 360.0

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

HP_COLORS = {1: ACCENT, 2: GOED, 3: WARN, 4: PURPLE}
STEEL = (110, 114, 124)

# power-ups: kleur + letter
POWERS = {
    "breed": {"color": GOED, "letter": "B"},
    "multi": {"color": ACCENT, "letter": "3"},
    "traag": {"color": PURPLE, "letter": "T"},
    "plak":  {"color": GOLD, "letter": "P"},
    "laser": {"color": WARN, "letter": "L"},
    "vuur":  {"color": RED, "letter": "V"},
    "leven": {"color": RED, "letter": "+"},
}
POWER_WEIGHTS = [("breed", 20), ("multi", 16), ("traag", 12), ("plak", 12),
                 ("laser", 14), ("vuur", 12), ("leven", 6)]

COLS = 11
BRICK_W = (FIELD_R - FIELD_L) // COLS
BRICK_H = 26
BRICK_TOP = FIELD_T + 30

# levels: '.'=leeg 1/2/3=stevigheid '#'=onverwoestbaar
LEVELS = [
    [
        "...........",
        "11111111111",
        "11111111111",
        "...........",
    ],
    [
        "2.2.2.2.2.2",
        "1.1.1.1.1.1",
        "2.2.2.2.2.2",
        "1.1.1.1.1.1",
    ],
    [
        "...#...#...",
        "11111111111",
        "22222222222",
        "11111111111",
        "...#...#...",
    ],
    [
        "33333333333",
        "2.........2",
        "2..11111..2",
        "2.........2",
        "22222222222",
    ],
    [
        "1.2.3.2.1.2",
        "2.3.1.3.2.3",
        "3.1.2.1.3.1",
        "2.3.1.3.2.3",
        "1.2.3.2.1.2",
    ],
    [
        "#.2.2.2.2.#",
        ".3.3.3.3.3.",
        "2.2.2.2.2.2",
        ".3.3.3.3.3.",
        "#.2.2.2.2.#",
        "11111111111",
    ],
    [
        "33333333333",
        "3#3#3#3#3#3",
        "33333333333",
        "2222222222 ".replace(" ", "2"),
        "1111111111 ".replace(" ", "1"),
    ],
    [
        "#3#3#3#3#3#",
        "3333333333 ".replace(" ", "3"),
        "#2#2#2#2#2#",
        "2222222222 ".replace(" ", "2"),
        "#3#3#3#3#3#",
        "33333333333",
    ],
]


# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveBricks-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveBricks-data")
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
    "onder": {"nl": "Een Breakout van Dravenlock Games", "en": "A Breakout by Dravenlock Games"},
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
    "level": {"nl": "Level", "en": "Level"},
    "gewonnen": {"nl": "Alle levels gehaald!", "en": "All levels cleared!"},
    "verloren": {"nl": "Game over", "en": "Game over"},
    "level_klaar": {"nl": "Level gehaald!", "en": "Level cleared!"},
    "volgende": {"nl": "Volgende level", "en": "Next level"},
    "lanceer": {"nl": "Klik of spatie om de bal te lanceren", "en": "Click or space to launch"},
    "uitleg1": {"nl": "Beweeg de peddel met de muis of pijltjes.", "en": "Move the paddle with mouse or arrows."},
    "uitleg2": {"nl": "Spatie of klik: lanceer de bal / schiet laser.", "en": "Space or click: launch ball / fire laser."},
    "uitleg3": {"nl": "Sla alle stenen kapot; '#' is onverwoestbaar.", "en": "Break all bricks; '#' is indestructible."},
    "uitleg4": {"nl": "Vang vallende power-ups op met de peddel.", "en": "Catch falling power-ups with the paddle."},
    "uitleg5": {"nl": "Verlies de bal = een leven kwijt. Esc/P = pauze.", "en": "Lose the ball = lose a life. Esc/P = pause."},
    "pu_breed": {"nl": "Breed: bredere peddel", "en": "Wide: bigger paddle"},
    "pu_multi": {"nl": "Multi: drie ballen", "en": "Multi: three balls"},
    "pu_traag": {"nl": "Traag: langzamere bal", "en": "Slow: slower ball"},
    "pu_plak": {"nl": "Plak: bal blijft plakken", "en": "Sticky: ball sticks"},
    "pu_laser": {"nl": "Laser: peddel schiet", "en": "Laser: paddle shoots"},
    "pu_vuur": {"nl": "Vuur: bal gaat door stenen", "en": "Fire: ball pierces bricks"},
    "pu_leven": {"nl": "Leven: extra leven", "en": "Life: extra life"},
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
class Ball:
    def __init__(self, x, y, vx, vy, stuck=False, offset=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.stuck = stuck
        self.offset = offset

    def speed(self):
        return math.hypot(self.vx, self.vy)


class Brick:
    def __init__(self, col, row, hp, unbreak=False):
        self.x = FIELD_L + col * BRICK_W
        self.y = BRICK_TOP + row * BRICK_H
        self.w = BRICK_W - 2
        self.h = BRICK_H - 2
        self.hp = hp
        self.max_hp = hp
        self.unbreak = unbreak
        self.alive = True
        self.flash = 0.0

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


class PowerUp:
    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind
        self.alive = True


class Laser:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app, level=0):
        self.app = app
        self.level = level
        self.score = 0
        self.lives = 3
        self.balls = []
        self.bricks = []
        self.powerups = []
        self.lasers = []
        self.paddle_w = PADDLE_W
        self.paddle_x = WIDTH // 2
        self.wide_t = 0.0
        self.slow_t = 0.0
        self.fire_t = 0.0
        self.laser_t = 0.0
        self.sticky = False
        self.laser_cd = 0.0
        self.finished = False
        self.result = None
        self.level_done = False
        self.flash_msg = ""
        self.msg_t = 0.0
        self.load_level(level)

    def base_speed(self):
        return BASE_SPEED + self.level * 18

    def load_level(self, idx):
        self.bricks = []
        rows = LEVELS[idx % len(LEVELS)]
        for r, line in enumerate(rows):
            for c, ch in enumerate(line[:COLS]):
                if ch == ".":
                    continue
                if ch == "#":
                    self.bricks.append(Brick(c, r, 1, unbreak=True))
                elif ch in "1234":
                    self.bricks.append(Brick(c, r, int(ch)))
        self.balls = []
        self.powerups = []
        self.lasers = []
        self.paddle_w = PADDLE_W
        self.wide_t = self.slow_t = self.fire_t = self.laser_t = 0.0
        self.sticky = False
        self.level_done = False
        self._new_ball()

    def _new_ball(self):
        b = Ball(self.paddle_x, PADDLE_Y - BALL_R - 2, 0, 0, stuck=True, offset=0)
        self.balls.append(b)

    def launch(self):
        fired = False
        for b in self.balls:
            if b.stuck:
                sp = self.base_speed() * (0.7 if self.slow_t > 0 else 1.0)
                ang = math.radians(-90 + random.uniform(-20, 20))
                b.vx = math.cos(ang) * sp
                b.vy = math.sin(ang) * sp
                b.stuck = False
                fired = True
        if fired and self.app.sfx:
            self.app.sfx.play("paddle")
        elif self.laser_t > 0 and self.laser_cd <= 0:
            self.lasers.append(Laser(self.paddle_x - self.paddle_w * 0.4, PADDLE_Y))
            self.lasers.append(Laser(self.paddle_x + self.paddle_w * 0.4, PADDLE_Y))
            self.laser_cd = 0.22
            if self.app.sfx:
                self.app.sfx.play("laser")

    def set_paddle(self, x):
        half = self.paddle_w / 2
        self.paddle_x = clamp(x, FIELD_L + half, FIELD_R - half)

    def _flash(self, m):
        self.flash_msg = m
        self.msg_t = 1.4

    # ---------- update ----------
    def update(self, dt, keys):
        if self.finished or self.level_done:
            return
        for k in ("wide_t", "slow_t", "fire_t", "laser_t"):
            setattr(self, k, max(0.0, getattr(self, k) - dt))
        if self.wide_t <= 0 and self.paddle_w != PADDLE_W:
            self.paddle_w = PADDLE_W
            self.set_paddle(self.paddle_x)
        self.laser_cd = max(0.0, self.laser_cd - dt)
        self.msg_t = max(0.0, self.msg_t - dt)
        # peddel met toetsen
        if keys.get("left"):
            self.set_paddle(self.paddle_x - 560 * dt)
        if keys.get("right"):
            self.set_paddle(self.paddle_x + 560 * dt)
        # ballen
        for b in self.balls:
            if b.stuck:
                b.x = self.paddle_x + b.offset
                b.y = PADDLE_Y - BALL_R - 2
                continue
            self._move_ball(b, dt)
        self.balls = [b for b in self.balls if b.y - BALL_R < HEIGHT + 20]
        if not self.balls:
            self._lose_life()
            return
        # power-ups vallen
        for p in self.powerups:
            p.y += 150 * dt
            if (PADDLE_Y - 12 <= p.y <= PADDLE_Y + 18 and
                    abs(p.x - self.paddle_x) <= self.paddle_w / 2 + 10):
                p.alive = False
                self._apply_power(p.kind)
            elif p.y > HEIGHT + 20:
                p.alive = False
        self.powerups = [p for p in self.powerups if p.alive]
        # lasers
        for l in self.lasers:
            l.y -= 620 * dt
            if l.y < FIELD_T:
                l.alive = False
            else:
                for br in self.bricks:
                    if br.alive and br.rect().collidepoint(l.x, l.y):
                        l.alive = False
                        if not br.unbreak:
                            self._damage(br, 1)
                        break
        self.lasers = [l for l in self.lasers if l.alive]
        # level klaar?
        if not any(br.alive and not br.unbreak for br in self.bricks):
            self._level_clear()

    def _move_ball(self, b, dt):
        sp_cap = 640
        speed = b.speed()
        if speed > sp_cap:
            b.vx *= sp_cap / speed
            b.vy *= sp_cap / speed
        steps = max(1, int(b.speed() * dt / 6) + 1)
        sdt = dt / steps
        for _ in range(steps):
            b.x += b.vx * sdt
            b.y += b.vy * sdt
            # muren
            if b.x - BALL_R < FIELD_L:
                b.x = FIELD_L + BALL_R
                b.vx = abs(b.vx)
                self._bounce()
            elif b.x + BALL_R > FIELD_R:
                b.x = FIELD_R - BALL_R
                b.vx = -abs(b.vx)
                self._bounce()
            if b.y - BALL_R < FIELD_T:
                b.y = FIELD_T + BALL_R
                b.vy = abs(b.vy)
                self._bounce()
            # peddel
            if (b.vy > 0 and PADDLE_Y - BALL_R <= b.y <= PADDLE_Y + PADDLE_H and
                    abs(b.x - self.paddle_x) <= self.paddle_w / 2 + BALL_R):
                if self.sticky:
                    b.stuck = True
                    b.offset = clamp(b.x - self.paddle_x, -self.paddle_w / 2, self.paddle_w / 2)
                    b.vx = b.vy = 0
                else:
                    off = (b.x - self.paddle_x) / (self.paddle_w / 2)
                    ang = math.radians(-90 + clamp(off, -1, 1) * 60)
                    sp = max(self.base_speed() * (0.7 if self.slow_t > 0 else 1.0), b.speed())
                    b.vx = math.cos(ang) * sp
                    b.vy = math.sin(ang) * sp
                    b.y = PADDLE_Y - BALL_R - 1
                    self._fix_ball(b)
                    if self.app.sfx:
                        self.app.sfx.play("paddle")
                return
            # stenen
            if self._ball_bricks(b):
                if self.fire_t <= 0:
                    return

    def _ball_bricks(self, b):
        hit = False
        for br in self.bricks:
            if not br.alive:
                continue
            r = br.rect()
            if (r.left - BALL_R <= b.x <= r.right + BALL_R and
                    r.top - BALL_R <= b.y <= r.bottom + BALL_R):
                # bepaal kaatsas via dichtstbijzijnde rand
                if self.fire_t > 0 and not br.unbreak:
                    self._damage(br, 1)
                    hit = True
                    continue
                dx = b.x - clamp(b.x, r.left, r.right)
                dy = b.y - clamp(b.y, r.top, r.bottom)
                if abs(dx) > abs(dy):
                    b.vx = abs(b.vx) if b.x > r.centerx else -abs(b.vx)
                else:
                    b.vy = abs(b.vy) if b.y > r.centery else -abs(b.vy)
                if br.unbreak:
                    br.flash = 0.12
                    if self.app.sfx:
                        self.app.sfx.play("ping")
                else:
                    self._damage(br, 1)
                self._fix_ball(b)
                return True
        return hit

    def _damage(self, br, dmg):
        br.hp -= dmg
        br.flash = 0.1
        if br.hp <= 0:
            br.alive = False
            self.score += 10 * br.max_hp
            if random.random() < 0.2:
                kinds = [k for (k, w) in POWER_WEIGHTS for _ in range(w)]
                self.powerups.append(PowerUp(br.x + br.w / 2, br.y + br.h / 2, random.choice(kinds)))
            if self.app.sfx:
                self.app.sfx.play("brick")
        else:
            if self.app.sfx:
                self.app.sfx.play("ping")

    def _bounce(self):
        if self.app.sfx:
            self.app.sfx.play("bounce")

    def _fix_ball(self, b):
        sp = b.speed()
        if sp < 1:
            return
        min_vy = 0.34 * sp
        if abs(b.vy) < min_vy:
            b.vy = math.copysign(min_vy, b.vy if b.vy != 0 else -1)
        min_vx = 0.22 * sp
        if abs(b.vx) < min_vx:
            b.vx = math.copysign(min_vx, b.vx if b.vx != 0 else random.choice([-1, 1]))
        cur = math.hypot(b.vx, b.vy)
        b.vx *= sp / cur
        b.vy *= sp / cur

    def _bounce_brick(self):
        pass

    def _apply_power(self, kind):
        if self.app.sfx:
            self.app.sfx.play("power")
        self.score += 25
        if kind == "breed":
            self.paddle_w = PADDLE_W * 1.6
            self.wide_t = 12.0
            self.set_paddle(self.paddle_x)
        elif kind == "traag":
            self.slow_t = 9.0
            for b in self.balls:
                if not b.stuck:
                    sp = b.speed()
                    tsp = self.base_speed() * 0.7
                    if sp > tsp:
                        b.vx *= tsp / sp
                        b.vy *= tsp / sp
        elif kind == "plak":
            self.sticky = True
            self._flash(t("pu_plak"))
        elif kind == "laser":
            self.laser_t = 11.0
        elif kind == "vuur":
            self.fire_t = 8.0
        elif kind == "leven":
            self.lives += 1
            if self.app.sfx:
                self.app.sfx.play("life")
        elif kind == "multi":
            extra = []
            for b in list(self.balls):
                if b.stuck or len(self.balls) + len(extra) >= 6:
                    continue
                for da in (-26, 26):
                    sp = b.speed() or self.base_speed()
                    ang = math.atan2(b.vy, b.vx) + math.radians(da)
                    extra.append(Ball(b.x, b.y, math.cos(ang) * sp, math.sin(ang) * sp))
            self.balls.extend(extra)
            if not extra and self.balls:
                self._flash(t("pu_multi"))

    def _lose_life(self):
        self.lives -= 1
        if self.app.sfx:
            self.app.sfx.play("lose")
        if self.lives <= 0:
            self.finished = True
            self.result = "lose"
            if self.score > self.app.cfg.get("highscore", 0):
                self.app.cfg["highscore"] = self.score
                save_config(self.app.cfg)
            if self.app.sfx:
                self.app.sfx.play("defeat")
            return
        # reset peddel + bal
        self.paddle_w = PADDLE_W
        self.wide_t = self.slow_t = self.fire_t = self.laser_t = 0.0
        self.sticky = False
        self.powerups = []
        self.lasers = []
        self._new_ball()

    def _level_clear(self):
        if self.level_done:
            return
        self.level_done = True
        self.score += 100
        if self.app.sfx:
            self.app.sfx.play("clear")
        if self.level + 1 >= len(LEVELS):
            self.finished = True
            self.result = "win"
            if self.score > self.app.cfg.get("highscore", 0):
                self.app.cfg["highscore"] = self.score
                save_config(self.app.cfg)
            if self.app.sfx:
                self.app.sfx.play("victory")

    def next_level(self):
        self.level += 1
        self.load_level(self.level)

    # ---------- tekenen ----------
    def draw(self, surf):
        # speelveld
        pygame.draw.rect(surf, (18, 18, 23), (FIELD_L, FIELD_T, FIELD_R - FIELD_L, HEIGHT - FIELD_T))
        pygame.draw.rect(surf, LINE, (FIELD_L - 2, FIELD_T - 2, FIELD_R - FIELD_L + 4, HEIGHT - FIELD_T + 4), 2)
        # stenen
        for br in self.bricks:
            if not br.alive:
                continue
            if br.unbreak:
                col = STEEL
            else:
                col = HP_COLORS.get(br.hp, ACCENT)
            if br.flash > 0:
                col = mix(col, (255, 255, 255), 0.5)
                br.flash = max(0.0, br.flash - 1 / FPS)
            pygame.draw.rect(surf, col, (br.x, br.y, br.w, br.h), border_radius=4)
            pygame.draw.rect(surf, mix(col, (0, 0, 0), 0.35), (br.x, br.y, br.w, br.h), 2, border_radius=4)
            pygame.draw.rect(surf, mix(col, (255, 255, 255), 0.18), (br.x + 3, br.y + 3, br.w - 6, 4), border_radius=2)
        # power-ups
        for p in self.powerups:
            info = POWERS[p.kind]
            pygame.draw.rect(surf, mix(info["color"], BG, 0.2), (p.x - 16, p.y - 10, 32, 20), border_radius=5)
            pygame.draw.rect(surf, info["color"], (p.x - 16, p.y - 10, 32, 20), 2, border_radius=5)
            img = self.app.font_s.render(info["letter"], True, (245, 245, 248))
            surf.blit(img, img.get_rect(center=(int(p.x), int(p.y))))
        # lasers
        for l in self.lasers:
            pygame.draw.rect(surf, WARN, (int(l.x) - 2, int(l.y) - 12, 4, 14))
        # peddel
        glow = self.laser_t > 0
        pcol = mix(ACCENT, WARN, 0.5) if glow else ACCENT
        px = int(self.paddle_x - self.paddle_w / 2)
        pygame.draw.rect(surf, mix(pcol, BG, 0.25), (px, PADDLE_Y, int(self.paddle_w), PADDLE_H), border_radius=8)
        pygame.draw.rect(surf, pcol, (px, PADDLE_Y, int(self.paddle_w), PADDLE_H), 2, border_radius=8)
        if self.sticky:
            pygame.draw.rect(surf, GOLD, (px, PADDLE_Y, int(self.paddle_w), 4), border_radius=2)
        if glow:
            pygame.draw.circle(surf, WARN, (px + 8, PADDLE_Y + 2), 3)
            pygame.draw.circle(surf, WARN, (px + int(self.paddle_w) - 8, PADDLE_Y + 2), 3)
        # ballen
        for b in self.balls:
            col = RED if self.fire_t > 0 else (240, 240, 245)
            pygame.draw.circle(surf, col, (int(b.x), int(b.y)), BALL_R)
            pygame.draw.circle(surf, mix(col, (0, 0, 0), 0.3), (int(b.x), int(b.y)), BALL_R, 1)
        # melding
        if self.msg_t > 0:
            img = self.app.font_s.render(self.flash_msg, True, GOLD)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, FIELD_T + 16)))


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
    f_title = pygame.font.Font(None, 80)
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

        self.font_xl = pygame.font.Font(None, 80)
        self.font_l = pygame.font.Font(None, 54)
        self.font_m = pygame.font.Font(None, 36)
        self.font_s = pygame.font.Font(None, 26)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.game = None
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)
        self.keys = {"left": False, "right": False}

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
                self.on_key_down(e.key)
            elif e.type == pygame.KEYUP:
                self.on_key_up(e.key)
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
            self.start_game()
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
            self.start_game()
        elif a == "to_title":
            self.set_state("title")
        elif a == "next_level":
            if self.game:
                self.game.next_level()
                self.set_state("play")
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
                "gameover": "to_title", "victory": "to_title"}.get(self.state)

    def on_key_down(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.keys["left"] = True
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.keys["right"] = True
            elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if self.game:
                    self.game.launch()
            return
        if self.state == "levelclear" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("next_level"); return
        if self.state in ("gameover", "victory") and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("retry"); return
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

    def on_key_up(self, key):
        if key in (pygame.K_LEFT, pygame.K_a):
            self.keys["left"] = False
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.keys["right"] = False

    def on_click(self, pos, button):
        if button != 1:
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return
        if self.state == "play" and self.game:
            self.game.launch()

    def start_game(self):
        self.game = Game(self, 0)
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            if self.mouse and pygame.mouse.get_focused():
                self.game.set_paddle(self.mouse[0])
            self.game.update(dt, self.keys)
            if self.game.finished and self.t_state > 0.5:
                self.set_state("victory" if self.game.result == "win" else "gameover")
            elif self.game.level_done and not self.game.finished and self.t_state > 0.3:
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
            if st == "play" and self.game.balls and all(b.stuck for b in self.game.balls):
                self._hint(s, t("lanceer"))
            if st == "pause":
                self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "levelclear":
            s.fill(BG)
            self.game.draw(s)
            self._overlay(s, t("level_klaar"),
                          ["%s %d" % (t("score"), self.game.score)],
                          [(t("volgende"), "next_level"), (t("hoofdmenu"), "to_title")], color=GOED)
        elif st == "gameover":
            s.fill(BG)
            self.game.draw(s)
            self._overlay(s, t("verloren"),
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

    def _hint(self, s, txt):
        img = self.font_m.render(txt, True, TEXT)
        bg = pygame.Surface((img.get_width() + 40, img.get_height() + 18), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        s.blit(bg, bg.get_rect(center=(WIDTH // 2, HEIGHT - 120)))
        s.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT - 120)))

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
        play_like = self.state in ("play", "pause")
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
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 48)
        y = 110
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_s, TEXT, WIDTH // 2, y)
            y += 36
        y += 4
        # power-up legenda in twee kolommen
        items = ["pu_breed", "pu_multi", "pu_traag", "pu_plak", "pu_laser", "pu_vuur", "pu_leven"]
        col_x = [WIDTH // 2 - 220, WIDTH // 2 + 20]
        for i, k in enumerate(items):
            key = k.split("_", 1)[1]
            info = POWERS[key]
            cx = col_x[i % 2]
            yy = y + (i // 2) * 34
            pygame.draw.rect(s, info["color"], (cx, yy - 10, 24, 20), border_radius=4)
            im = self.font_s.render(info["letter"], True, (20, 20, 24))
            s.blit(im, im.get_rect(center=(cx + 12, yy)))
            self._text(s, t(k), self.font_s, TEXT, cx + 34, yy, center=False)
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 64, 220, 50), "back_title", kind="back")
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
        self._text(s, "%s %d" % (t("score"), g.score), self.font_m, TEXT, 90, HUD_H // 2)
        self._text(s, "%s %d / %d" % (t("level"), g.level + 1, len(LEVELS)), self.font_m, ACCENT, WIDTH // 2 - 30, HUD_H // 2)
        # levens als hartjes
        for i in range(g.lives):
            draw_heart(s, WIDTH - 230 + i * 30, HUD_H // 2, 10, RED)
        if self.state == "play":
            self._add_button(t("pauze"), (WIDTH - 120, 6, 104, 34), "pause", kind="back")

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 165)
        y = 255
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 46
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
        self._stack([(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                    top=370, w=360, h=64, gap=18, kinds=["primary", "normal"])


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

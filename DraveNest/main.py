# -*- coding: utf-8 -*-
"""DraveNest - verdedig je drakennest (Dravenlock).

Jij bent een draak boven op de toren en bewaakt je eieren. Ridders,
schilddragers, bruten en boogschutters klimmen omhoog. Richt met de MUIS en
verschroei ze voordat ze het nest bereiken. Overleef zoveel mogelijk golven,
koop upgrades en houd je eieren heel.

Besturing: MUIS = richten, muisknop of SPATIE = vuur ademen, Enter = verder,
P = pauze, Esc = terug. Tweetalig NL/EN, procedurele audio, portable.
Donationware.
"""
import json
import locale
import math
import os
import random
import sys
import webbrowser
from array import array

import pygame

try:
    from pygame import gfxdraw
    HAS_GFX = True
except Exception:
    HAS_GFX = False

W, H = 960, 640
FPS = 60
SR = 22050
MOUTH = (W // 2, 150)         # vaste positie van de drakenmond (richtpunt)
NEST_TOP = 196               # y waarop vijanden het nest bereiken
FIRE_RANGE = 375             # vuur reikt niet tot de spawn -> je moet ze hoger pakken

BG_TOP = (26, 20, 40)
BG_BOT = (52, 40, 78)
PURPLE = (128, 94, 205)
PURPLE_L = (176, 150, 236)
PURPLE_D = (74, 58, 110)
BELLY = (206, 190, 240)
HORN = (238, 232, 250)
EYE = (255, 208, 66)
INK = (230, 224, 245)
GOLDC = (255, 205, 70)
STONE = (86, 78, 100)
STONE_D = (60, 54, 76)
IRON = (150, 150, 165)
IRON_D = (96, 96, 112)


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
    "title": {"nl": "DraveNest", "en": "DraveNest"},
    "sub": {"nl": "Verdedig je drakennest", "en": "Defend your dragon nest"},
    "start": {"nl": "Enter = start", "en": "Enter = start"},
    "ctrl": {"nl": "Muis = richten    Klik/spatie = vuur    P = pauze",
             "en": "Mouse = aim    Click/space = fire    P = pause"},
    "donate": {"nl": "D = doneren", "en": "D = donate"},
    "info": {"nl": "I = info", "en": "I = info"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "gold": {"nl": "Goud", "en": "Gold"},
    "wave": {"nl": "Golf", "en": "Wave"},
    "nest": {"nl": "Nest", "en": "Nest"},
    "best": {"nl": "Record (golf)", "en": "Best (wave)"},
    "wave_done": {"nl": "Golf %d overleefd!", "en": "Wave %d survived!"},
    "shop": {"nl": "Winkel - koop upgrades", "en": "Shop - buy upgrades"},
    "next_wave": {"nl": "Enter = volgende golf", "en": "Enter = next wave"},
    "up_power": {"nl": "Sterker vuur", "en": "Stronger fire"},
    "up_wide": {"nl": "Brede vuuradem", "en": "Wide breath"},
    "up_fuel": {"nl": "Sneller opladen", "en": "Faster recharge"},
    "up_repair": {"nl": "Nest herstellen (+30)", "en": "Repair nest (+30)"},
    "lvl": {"nl": "niv.", "en": "lvl"},
    "maxed": {"nl": "MAX", "en": "MAX"},
    "buy": {"nl": "Kopen", "en": "Buy"},
    "close": {"nl": "Enter = door", "en": "Enter = go"},
    "paused": {"nl": "Pauze", "en": "Paused"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "gameover": {"nl": "Je nest is gevallen!", "en": "Your nest has fallen!"},
    "reached": {"nl": "%d golven overleefd", "en": "Survived %d waves"},
    "retry": {"nl": "Enter = opnieuw", "en": "Enter = retry"},
    "menu": {"nl": "Esc = menu", "en": "Esc = menu"},
    "info_txt": {
        "nl": "DraveNest - richt met de muis en verschroei de klimmende "
              "vijanden voordat ze je eieren bereiken.\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl",
        "en": "DraveNest - aim with the mouse and torch the climbing enemies "
              "before they reach your eggs.\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl"},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"


# ------------------------------------------------------------- teken-hulpjes
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


def make_dragon(facing=1):
    """Perchende draak (kop omhoog), kijkt links of rechts."""
    ww, hh = 150, 150
    s = pygame.Surface((ww, hh), pygame.SRCALPHA)
    cx, cy = 75, 96
    # gevouwen vleugel achter
    poly(s, [(cx - 6, cy - 20), (cx - 54, cy - 54), (cx - 30, cy + 8),
             (cx - 6, cy)], PURPLE_D)
    # staart krullend
    for i in range(7):
        circ(s, cx - 24 - i * 7, cy + 20 + math.sin(i) * 6, 8 - i * 0.7, PURPLE)
    # lichaam
    poly(s, [(cx - 26, cy + 26), (cx - 20, cy - 16), (cx + 18, cy - 18),
             (cx + 30, cy + 12), (cx + 16, cy + 34), (cx - 20, cy + 34)],
         PURPLE)
    poly(s, [(cx - 8, cy + 12), (cx + 16, cy + 12), (cx + 8, cy + 30),
             (cx - 8, cy + 28)], BELLY)
    # rugstekels
    for i in range(4):
        bx = cx - 14 + i * 10
        poly(s, [(bx, cy - 14), (bx + 7, cy - 14), (bx + 3, cy - 24)], PURPLE_L)
    # nek + kop omhoog
    poly(s, [(cx + 6, cy - 10), (cx + 26, cy - 44), (cx + 40, cy - 40),
             (cx + 22, cy - 4)], PURPLE)
    hx, hy = cx + 34, cy - 46
    poly(s, [(hx - 2, hy - 2), (hx + 4, hy - 2), (hx - 6, hy - 18)], HORN)
    poly(s, [(hx + 4, hy - 1), (hx + 10, hy - 1), (hx + 2, hy - 15)], HORN)
    poly(s, [(hx - 8, hy + 2), (hx + 14, hy - 4), (hx + 22, hy + 4),
             (hx + 6, hy + 12), (hx - 6, hy + 10)], PURPLE)
    poly(s, [(hx + 14, hy + 0), (hx + 30, hy + 2), (hx + 20, hy + 8)], PURPLE_L)
    circ(s, hx + 4, hy + 2, 3, (20, 16, 30))
    circ(s, hx + 4, hy + 2, 2, EYE)
    if facing == -1:
        s = pygame.transform.flip(s, True, False)
    return s


# stats per vijandtype: hp, speed, dmg, kleur, radius
EKIND = {
    "grunt":  {"hp": 2.6, "spd": 1.15, "dmg": 8,  "col": (150, 120, 90), "r": 15},
    "shield": {"hp": 6.5, "spd": 0.85, "dmg": 12, "col": (120, 130, 150), "r": 16},
    "brute":  {"hp": 13.0, "spd": 0.60, "dmg": 22, "col": (110, 80, 80), "r": 20},
    "archer": {"hp": 2.2, "spd": 1.00, "dmg": 6,  "col": (110, 140, 100), "r": 14},
}


class Enemy:
    def __init__(self, lane_x, kind):
        self.x = lane_x
        self.y = H + random.randint(0, 40)
        self.kind = kind
        st = EKIND[kind]
        self.hp = st["hp"]
        self.maxhp = st["hp"]
        self.spd = st["spd"]
        self.dmg = st["dmg"]
        self.col = st["col"]
        self.r = st["r"]
        self.dead = False
        self.reached = False
        self.wob = random.uniform(0, 6)
        self.stop_y = random.randint(300, 380) if kind == "archer" else NEST_TOP
        self.cool = random.randint(40, 90)
        self.hurt = 0

    def update(self, scroll_speed, arrows):
        self.wob += 0.08
        if self.y > self.stop_y:
            self.y -= self.spd * scroll_speed
        else:
            if self.kind == "archer":
                self.cool -= 1
                if self.cool <= 0:
                    self.cool = random.randint(70, 120)
                    arrows.append(Arrow(self.x, self.y))
            else:
                self.reached = True
        if self.hurt > 0:
            self.hurt -= 1

    def draw(self, sc):
        x = self.x + math.sin(self.wob) * 6
        y = self.y
        col = self.col if self.hurt == 0 else (255, 180, 120)
        # lijf
        circ(sc, x, y, self.r, col)
        # hoofd/helm
        circ(sc, x, y - self.r, self.r - 5, (215, 190, 160))
        if self.kind == "shield":
            poly(sc, [(x - 16, y - 4), (x - 8, y - 16), (x - 8, y + 12)],
                 (170, 175, 190))
        if self.kind == "brute":
            pygame.draw.rect(sc, IRON_D, (x - 4, y - self.r - 22, 8, 20))  # bijl
            poly(sc, [(x - 12, y - self.r - 22), (x + 12, y - self.r - 22),
                      (x, y - self.r - 34)], IRON)
        if self.kind == "archer":
            pygame.draw.arc(sc, (90, 70, 50),
                            (int(x + 4), int(y - 12), 16, 24), -1.2, 1.2, 3)
        # hp-balkje
        if self.hp < self.maxhp:
            w = 30
            pygame.draw.rect(sc, (40, 20, 24),
                             (x - w // 2, y - self.r - 12, w, 4))
            pygame.draw.rect(sc, (220, 90, 90),
                             (x - w // 2, y - self.r - 12,
                              int(w * self.hp / self.maxhp), 4))

    def pos(self):
        return (self.x + math.sin(self.wob) * 6, self.y)


class Arrow:
    def __init__(self, x, y):
        a = math.atan2(MOUTH[1] - y, MOUTH[0] - x)
        sp = 4.6
        self.x, self.y = x, y
        self.vx = math.cos(a) * sp
        self.vy = math.sin(a) * sp
        self.dead = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.y < NEST_TOP - 10:
            self.dead = True
            return "hit"
        if self.x < -20 or self.x > W + 20 or self.y > H + 20:
            self.dead = True
        return None

    def draw(self, sc):
        a = math.atan2(self.vy, self.vx)
        ex = self.x + math.cos(a) * 12
        ey = self.y + math.sin(a) * 12
        pygame.draw.line(sc, (230, 220, 210), (self.x, self.y), (ex, ey), 3)


class FireP:
    def __init__(self, x, y, ang, spread):
        a = ang + random.uniform(-spread, spread)
        sp = random.uniform(7, 12)
        self.x, self.y = x, y
        self.vx = math.cos(a) * sp
        self.vy = math.sin(a) * sp
        self.life = random.randint(12, 22)
        self.r = random.randint(5, 11)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.r *= 0.93

    def draw(self, sc):
        if self.life <= 0:
            return
        c = (255, 210, 90) if self.life > 12 else (240, 110, 40)
        circ(sc, self.x, self.y, self.r, c)


# ---------------------------------------------------------------- audio
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


def mixbuf(*bufs):
    n = max(len(b) for b in bufs)
    out = [0] * n
    for b in bufs:
        for i, s in enumerate(b):
            out[i] += s
    return array("h", (int(max(-32767, min(32767, v))) for v in out))


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
        self.snd["fire"] = make_sound(tone(90, 200, 0.28, "noise"))
        self.snd["burn"] = make_sound(tone(150, 200, 0.3, "noise"))
        self.snd["hit"] = make_sound(tone(180, 220, 0.34, "saw"))
        self.snd["wave"] = make_sound(mixbuf(tone(520, 140, 0.3),
                                             tone(780, 180, 0.28)))
        self.snd["buy"] = make_sound(mixbuf(tone(520, 80, 0.3),
                                            tone(780, 110, 0.26)))
        self.snd["gold"] = make_sound(mixbuf(tone(880, 60, 0.26),
                                             tone(1200, 80, 0.22)))
        self._music()

    def _music(self):
        base = [147, 175, 196, 175, 131, 165, 196, 165]
        loop = array("h")
        for f in base:
            loop.extend(mixbuf(tone(f, 300, 0.13, "saw"),
                               tone(f * 2, 300, 0.06, "square")))
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


class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label

    def draw(self, sc, font, hot=False):
        col = (74, 60, 110) if not hot else (104, 84, 150)
        pygame.draw.rect(sc, col, self.rect, border_radius=10)
        pygame.draw.rect(sc, PURPLE_L, self.rect, 2, border_radius=10)
        r = font.render(self.label, True, INK)
        sc.blit(r, (self.rect.centerx - r.get_width() // 2,
                    self.rect.centery - r.get_height() // 2))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


# --------------------------------------------------------------------- de game
LANES = [W // 2 - 150, W // 2 - 60, W // 2 + 60, W // 2 + 150]


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
        pygame.mouse.set_visible(False)
        ic = os.path.join(app_dir(), "assets", "icon.ico")
        if os.path.exists(ic):
            try:
                pygame.display.set_icon(pygame.image.load(ic))
            except Exception:
                pass
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arialrounded,arial", 56, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("arial", 21, bold=True)
        self.tiny = pygame.font.SysFont("arial", 17, bold=True)
        self.audio = Audio()
        self.drg_r = make_dragon(1)
        self.drg_l = make_dragon(-1)
        self.bg = self._make_bg()
        self.best = self._load_best()
        self.up = {"power": 0, "wide": 0, "fuel": 0}
        self.state = "menu"
        self.shop_buttons = {}
        self.reset()
        self.audio.start_music()

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

    def _make_bg(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            s.fill((int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * y / H),
                    int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * y / H),
                    int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * y / H)),
                   (0, y, W, 1))
        # maan
        circ(s, 150, 110, 50, (70, 60, 96))
        circ(s, 150, 110, 46, (86, 76, 116))
        # toren (brede stenen kolom in het midden)
        tw = 330
        tx = W // 2 - tw // 2
        pygame.draw.rect(s, STONE_D, (tx, 210, tw, H - 210))
        pygame.draw.rect(s, STONE, (tx + 10, 210, tw - 20, H - 210))
        for by in range(230, H, 46):
            pygame.draw.line(s, STONE_D, (tx + 10, by), (tx + tw - 10, by), 3)
        for i in range(1, 7):
            xx = tx + 10 + (tw - 20) * i / 7
            pygame.draw.line(s, (52, 46, 66), (xx, 210), (xx, H), 2)
        # kantelen bovenaan
        for i in range(6):
            cxx = tx + 8 + i * 56
            pygame.draw.rect(s, STONE, (cxx, 188, 34, 26))
        return s

    def reset(self):
        self.enemies = []
        self.arrows = []
        self.fire = []
        self.gold = 0
        self.wave = 0
        self.nest = 100.0
        self.fuel = 100.0
        self.firing = False
        self.aim = -math.pi / 2
        self.phase = "shop"        # begin met korte winkel/uitleg -> volgende golf
        self.to_spawn = []
        self.spawn_t = 0
        self.msg = ""
        self.msgt = 0
        self._prep_wave()
        self.phase = "shop"

    def _prep_wave(self):
        self.wave += 1
        n = 5 + self.wave * 2
        kinds = ["grunt"] * n
        for i in range(n):
            r = random.random()
            if self.wave >= 2 and r < 0.24:
                kinds[i] = "archer"
            elif self.wave >= 2 and r < 0.44:
                kinds[i] = "shield"
            elif self.wave >= 3 and r < 0.58:
                kinds[i] = "brute"
        random.shuffle(kinds)
        self.to_spawn = kinds
        self.spawn_t = 34

    # ---------- loop ----------
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    self._key(e.key)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._mousedown(e.pos)
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    self.firing = False
            if self.state == "play":
                self._update()
            self._draw()
            self.clock.tick(FPS)

    def _quit(self):
        if self.wave - 1 > self.best:
            self.best = self.wave - 1
        self._save_best()
        pygame.quit()
        sys.exit()

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
            if k == pygame.K_p:
                self.state = "pause"
            elif k == pygame.K_ESCAPE:
                self.state = "pause"
            elif k == pygame.K_SPACE:
                if self.phase == "wave":
                    self.firing = True
            elif k == pygame.K_RETURN and self.phase == "shop":
                self.phase = "wave"
                self.audio.play("wave")
        elif self.state == "pause":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"
        elif self.state == "over":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def _mousedown(self, pos):
        if self.state == "menu":
            self.reset()
            self.state = "play"
            return
        if self.state != "play":
            return
        if self.phase == "shop":
            for key, btn in self.shop_buttons.items():
                if btn.hit(pos):
                    self._buy(key)
                    return
            return
        if self.phase == "wave":
            self.firing = True

    def _keyup_space(self):
        self.firing = False

    def _buy(self, key):
        if key == "repair":
            c = 40
            if self.gold >= c and self.nest < 100:
                self.gold -= c
                self.nest = min(100, self.nest + 30)
                self.audio.play("buy")
            return
        if self.up[key] >= 4:
            return
        c = 50 + self.up[key] * 70
        if self.gold >= c:
            self.gold -= c
            self.up[key] += 1
            self.audio.play("buy")

    # ---------- update ----------
    def _fire_params(self):
        power = 0.14 + self.up["power"] * 0.06
        spread = 0.22 + self.up["wide"] * 0.06
        cone = 0.20 + self.up["wide"] * 0.05
        recharge = 0.42 + self.up["fuel"] * 0.32
        return power, spread, cone, recharge

    def _update(self):
        if self.phase == "shop":
            return
        mx, my = pygame.mouse.get_pos()
        self.aim = math.atan2(my - MOUTH[1], mx - MOUTH[0])
        power, spread, cone, recharge = self._fire_params()

        keys = pygame.key.get_pressed()
        want = self.firing or keys[pygame.K_SPACE]
        if want and self.fuel > 0:
            self.fuel = max(0, self.fuel - 1.5)
            for _ in range(2):
                self.fire.append(FireP(MOUTH[0], MOUTH[1], self.aim, spread))
            if random.random() < 0.08:
                self.audio.play("fire")
            # schade in de kegel
            for e in self.enemies:
                ex, ey = e.pos()
                d = math.hypot(ex - MOUTH[0], ey - MOUTH[1])
                if d < FIRE_RANGE:
                    ea = math.atan2(ey - MOUTH[1], ex - MOUTH[0])
                    da = abs((ea - self.aim + math.pi) % (2 * math.pi) - math.pi)
                    if da < cone:
                        dmg = power * (0.5 if e.kind == "shield" else 1.0)
                        e.hp -= dmg
                        e.hurt = 3
                        if e.hp <= 0 and not e.dead:
                            e.dead = True
                            self.gold += {"grunt": 5, "archer": 6,
                                          "shield": 9, "brute": 14}[e.kind]
                            self.audio.play("burn")
        else:
            self.fuel = min(100, self.fuel + recharge)

        # spawnen
        if self.to_spawn:
            self.spawn_t -= 1
            if self.spawn_t <= 0:
                self.spawn_t = max(12, 40 - self.wave * 3)
                kind = self.to_spawn.pop()
                e = Enemy(random.choice(LANES), kind)
                m = 1 + (self.wave - 1) * 0.07     # taaier per golf
                e.hp *= m
                e.maxhp *= m
                self.enemies.append(e)

        for e in self.enemies:
            e.update(1.0, self.arrows)
            if e.reached:
                e.dead = True
                self.nest -= e.dmg
                self.audio.play("hit")
        for a in list(self.arrows):
            r = a.update()
            if r == "hit":
                self.nest -= 5
                self.audio.play("hit")
        for f in self.fire:
            f.update()
        self.fire = [f for f in self.fire if f.life > 0]
        self.enemies = [e for e in self.enemies if not e.dead]
        self.arrows = [a for a in self.arrows if not a.dead]

        if self.nest <= 0:
            self.nest = 0
            if self.wave > self.best:
                self.best = self.wave
                self._save_best()
            self.state = "over"

        # golf klaar?
        if not self.to_spawn and not self.enemies and self.phase == "wave":
            self.gold += 20 + self.wave * 5
            self.msg = T("wave_done") % self.wave
            self.msgt = 120
            self._prep_wave()
            self.phase = "shop"

        if self.msgt > 0:
            self.msgt -= 1

    # ---------- teken ----------
    def _draw(self):
        sc = self.screen
        sc.blit(self.bg, (0, 0))
        if self.state == "menu":
            self._menu(sc)
            pygame.display.flip()
            return
        self._draw_nest(sc)
        for e in sorted(self.enemies, key=lambda e: e.y, reverse=True):
            e.draw(sc)
        for a in self.arrows:
            a.draw(sc)
        for f in self.fire:
            f.draw(sc)
        self._draw_dragon(sc)
        self._hud(sc)
        if self.phase == "wave" or self.state in ("pause",):
            self._crosshair(sc)
        if self.phase == "shop" and self.state == "play":
            self._draw_shop(sc)
        if self.msgt > 0:
            r = self.mid.render(self.msg, True, PURPLE_L)
            sc.blit(r, (W // 2 - r.get_width() // 2, 250))
        if self.state == "pause":
            self._overlay(sc, T("paused"), T("resume"))
        elif self.state == "over":
            self._overlay(sc, T("gameover"), T("reached") % (self.wave - 1))
        pygame.display.flip()

    def _draw_nest(self, sc):
        # nest met eieren bovenop de toren
        pygame.draw.ellipse(sc, (92, 68, 44), (W // 2 - 70, 150, 140, 46))
        for i, dx in enumerate((-30, 0, 30)):
            circ(sc, W // 2 + dx, 168, 15, (235, 225, 205))
            circ(sc, W // 2 + dx - 4, 164, 5, (255, 250, 240))

    def _draw_dragon(self, sc):
        mx = pygame.mouse.get_pos()[0]
        img = self.drg_l if mx < MOUTH[0] else self.drg_r
        sc.blit(img, (MOUTH[0] - img.get_width() // 2,
                      MOUTH[1] - img.get_height() // 2 - 20))

    def _crosshair(self, sc):
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(sc, PURPLE_L, (mx, my), 14, 2)
        pygame.draw.line(sc, PURPLE_L, (mx - 20, my), (mx - 6, my), 2)
        pygame.draw.line(sc, PURPLE_L, (mx + 6, my), (mx + 20, my), 2)
        pygame.draw.line(sc, PURPLE_L, (mx, my - 20), (mx, my - 6), 2)
        pygame.draw.line(sc, PURPLE_L, (mx, my + 6), (mx, my + 20), 2)

    def _hud(self, sc):
        g = self.mid.render("%s: %d" % (T("gold"), self.gold), True, GOLDC)
        sc.blit(g, (20, 16))
        w = self.small.render("%s %d   %s: %d" %
                              (T("wave"), self.wave, T("best"), self.best),
                              True, INK)
        sc.blit(w, (20, 54))
        # nest-balk
        nb = self.small.render(T("nest"), True, INK)
        sc.blit(nb, (W - 250, 16))
        pygame.draw.rect(sc, (40, 24, 30), (W - 250, 42, 230, 16),
                         border_radius=8)
        pygame.draw.rect(sc, (90, 210, 120),
                         (W - 250, 42, int(230 * self.nest / 100), 16),
                         border_radius=8)
        # brandstof
        pygame.draw.rect(sc, (40, 30, 50), (W - 250, 66, 230, 12),
                         border_radius=6)
        pygame.draw.rect(sc, (255, 150, 50),
                         (W - 250, 66, int(230 * self.fuel / 100), 12),
                         border_radius=6)

    def _draw_shop(self, sc):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 190))
        sc.blit(o, (0, 0))
        self._center(sc, T("shop"), self.big, PURPLE_L, -220)
        self._center(sc, "%s: %d" % (T("gold"), self.gold), self.mid,
                     GOLDC, -155)
        rows = [("power", T("up_power")), ("wide", T("up_wide")),
                ("fuel", T("up_fuel")), ("repair", T("up_repair"))]
        self.shop_buttons = {}
        y = 210
        for key, name in rows:
            if key == "repair":
                r = self.small.render(name, True, INK)
                sc.blit(r, (210, y + 10))
                btn = Button(650, y, 130, 40, "%s 40" % T("buy"))
            else:
                lvl = self.up[key]
                r = self.small.render("%s  (%s %d/4)" % (name, T("lvl"), lvl),
                                      True, INK)
                sc.blit(r, (210, y + 10))
                if lvl >= 4:
                    b = self.small.render(T("maxed"), True, (150, 150, 160))
                    sc.blit(b, (660, y + 10))
                    y += 62
                    continue
                btn = Button(650, y, 130, 40,
                             "%s %d" % (T("buy"), 50 + lvl * 70))
            btn.draw(sc, self.tiny, btn.hit(pygame.mouse.get_pos()))
            self.shop_buttons[key] = btn
            y += 62
        self._center(sc, "%s %d - %s" %
                     (T("wave"), self.wave, T("next_wave")),
                     self.small, INK, 210)
        # muis zichtbaar in winkel
        mx, my = pygame.mouse.get_pos()
        circ(sc, mx, my, 6, PURPLE_L)

    def _center(self, sc, txt, font, col, dy=0):
        r = font.render(txt, True, col)
        sc.blit(r, (W // 2 - r.get_width() // 2, H // 2 + dy))

    def _overlay(self, sc, title, sub):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 180))
        sc.blit(o, (0, 0))
        self._center(sc, title, self.big, (240, 130, 130), -50)
        self._center(sc, sub, self.mid, INK, 20)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 70)
        self._center(sc, T("menu"), self.small, (170, 160, 190), 104)
        mx, my = pygame.mouse.get_pos()
        circ(sc, mx, my, 6, PURPLE_L)

    def _menu(self, sc):
        sc.blit(self.drg_r, (W // 2 - 60, 150))
        self._draw_nest_menu(sc)
        self._center(sc, T("title"), self.big, PURPLE_L, -200)
        self._center(sc, T("sub"), self.mid, (200, 190, 225), -140)
        self._center(sc, T("start"), self.mid, GOLDC, 130)
        self._center(sc, T("ctrl"), self.small, INK, 180)
        self._center(sc, "%s    %s    %s" %
                     (T("donate"), T("info"), T("quit")),
                     self.small, (170, 160, 195), 216)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 252)
        mx, my = pygame.mouse.get_pos()
        circ(sc, mx, my, 6, PURPLE_L)

    def _draw_nest_menu(self, sc):
        pygame.draw.ellipse(sc, (92, 68, 44), (W // 2 - 60, 250, 120, 40))
        for dx in (-24, 0, 24):
            circ(sc, W // 2 + dx, 264, 13, (235, 225, 205))

    def _info(self):
        self._draw()
        box = pygame.Surface((640, 190), pygame.SRCALPHA)
        box.fill((20, 16, 30, 240))
        pygame.draw.rect(box, PURPLE_L, box.get_rect(), 2, border_radius=10)
        y = 24
        for line in T("info_txt").split("\n"):
            box.blit(self.small.render(line, True, INK), (24, y))
            y += 30
        self.screen.blit(box, (W // 2 - 320, H // 2 - 95))
        pygame.display.flip()
        wait = True
        while wait:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    wait = False
            self.clock.tick(30)


def main():
    Game().run()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""DraveDelver - een grot-mijnbouw-avontuur (Dravenlock).

Jij bent een gravend draakje. Graaf met de PIJLTJES steeds dieper de grot in,
verzamel edelstenen (dieper = waardevoller), beheer je lantaarn-olie en ontwijk
tunnelwormen. Ga terug naar de oppervlakte om je buit te verkopen, bij te tanken
en upgrades te kopen. Hoe diep durf jij te gaan?

Besturing: PIJLTJES = graven/bewegen, Enter = winkel (aan de oppervlakte),
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

TS = 40                       # tegelgrootte
COLS = 22
W, H = COLS * TS, 640         # 880 x 640
FPS = 60
SR = 22050

BG_TOP = (24, 18, 36)
BG_BOT = (44, 32, 62)
PURPLE = (128, 94, 205)
PURPLE_L = (176, 150, 236)
INK = (232, 226, 246)
GOLDC = (255, 205, 70)
DIRT = (96, 68, 46)
DIRT_D = (72, 50, 34)
ROCK = (96, 96, 112)
ROCK_D = (70, 70, 86)
SKY = (70, 92, 130)
GRASS = (86, 140, 78)

GEM_TIERS = [
    ((120, 210, 240), 8),     # kwarts (blauw)
    ((120, 240, 150), 16),    # smaragd (groen)
    ((240, 150, 210), 30),    # amethist (roze)
    ((255, 180, 70), 55),     # amber/goud
    ((255, 90, 90), 90),      # robijn (rood, diep)
]


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
    "title": {"nl": "DraveDelver", "en": "DraveDelver"},
    "sub": {"nl": "Graaf naar de diepte", "en": "Dig into the deep"},
    "start": {"nl": "Enter = start", "en": "Enter = start"},
    "ctrl": {"nl": "Pijltjes = graven    Enter = winkel (boven)    P = pauze",
             "en": "Arrows = dig    Enter = shop (surface)    P = pause"},
    "donate": {"nl": "D = doneren", "en": "D = donate"},
    "info": {"nl": "I = info", "en": "I = info"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "gold": {"nl": "Goud", "en": "Gold"},
    "depth": {"nl": "Diepte", "en": "Depth"},
    "best": {"nl": "Diepterecord", "en": "Best depth"},
    "bag": {"nl": "Buit", "en": "Loot"},
    "oil": {"nl": "Olie", "en": "Oil"},
    "sold": {"nl": "Verkocht: +%d goud", "en": "Sold: +%d gold"},
    "surface": {"nl": "Oppervlakte - Enter = winkel",
                "en": "Surface - Enter = shop"},
    "shop": {"nl": "Winkel", "en": "Shop"},
    "up_pick": {"nl": "Pikhouweel (hardere rots)",
                "en": "Pickaxe (harder rock)"},
    "up_lamp": {"nl": "Lantaarn (groter licht)", "en": "Lantern (bigger light)"},
    "up_oil": {"nl": "Olievat (meer olie)", "en": "Oil tank (more oil)"},
    "up_armor": {"nl": "Harnas (+1 hart)", "en": "Armor (+1 heart)"},
    "up_heal": {"nl": "Genees volledig", "en": "Heal fully"},
    "lvl": {"nl": "niv.", "en": "lvl"},
    "maxed": {"nl": "MAX", "en": "MAX"},
    "buy": {"nl": "Kopen", "en": "Buy"},
    "close": {"nl": "Esc = sluiten", "en": "Esc = close"},
    "paused": {"nl": "Pauze", "en": "Paused"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "gameover": {"nl": "Je bezweek in de grot!", "en": "You perished below!"},
    "reached": {"nl": "Diepte %d bereikt", "en": "Reached depth %d"},
    "retry": {"nl": "Enter = opnieuw", "en": "Enter = retry"},
    "menu": {"nl": "Esc = menu", "en": "Esc = menu"},
    "info_txt": {
        "nl": "DraveDelver - graaf diep, verzamel edelstenen en kom levend "
              "terug boven om te verkopen en upgraden. Let op je olie!\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl",
        "en": "DraveDelver - dig deep, collect gems and return alive to sell "
              "and upgrade. Watch your oil!\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl"},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"


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


def make_miner():
    """Klein gravend draakje met helmlamp."""
    s = pygame.Surface((TS, TS), pygame.SRCALPHA)
    c = TS // 2
    # lijf
    circ(s, c, c + 4, 13, PURPLE)
    circ(s, c, c + 4, 13, PURPLE)
    # buik
    circ(s, c, c + 8, 7, (200, 185, 235))
    # kop
    circ(s, c, c - 6, 10, PURPLE)
    # horens
    poly(s, [(c - 8, c - 12), (c - 4, c - 12), (c - 10, c - 20)], (235, 230, 248))
    poly(s, [(c + 4, c - 12), (c + 8, c - 12), (c + 10, c - 20)], (235, 230, 248))
    # ogen
    circ(s, c - 4, c - 6, 2, (20, 16, 30))
    circ(s, c + 4, c - 6, 2, (20, 16, 30))
    # helm + lamp
    pygame.draw.arc(s, (60, 54, 76), (c - 11, c - 18, 22, 20), 0.2, 2.9, 4)
    circ(s, c, c - 15, 4, (255, 240, 160))
    return s


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
        self.snd["dig"] = make_sound(tone(120, 70, 0.22, "noise"))
        self.snd["rock"] = make_sound(tone(90, 110, 0.28, "square"))
        self.snd["gem"] = make_sound(mixbuf(tone(880, 70, 0.3),
                                            tone(1320, 100, 0.26)))
        self.snd["hit"] = make_sound(tone(170, 220, 0.34, "saw"))
        self.snd["sell"] = make_sound(mixbuf(tone(660, 90, 0.3),
                                             tone(990, 120, 0.26),
                                             tone(1320, 150, 0.22)))
        self.snd["buy"] = make_sound(mixbuf(tone(520, 80, 0.3),
                                            tone(780, 110, 0.24)))
        self._music()

    def _music(self):
        base = [110, 131, 147, 131, 98, 123, 147, 123]
        loop = array("h")
        for f in base:
            loop.extend(mixbuf(tone(f, 320, 0.13, "saw"),
                               tone(f * 3, 320, 0.04, "sine")))
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


class Worm:
    def __init__(self, col, row):
        self.x = float(col)
        self.y = float(row)
        self.trail = [(self.x, self.y)] * 5
        self.hurtcd = 0

    def update(self, pcol, prow):
        dx, dy = pcol - self.x, prow - self.y
        d = math.hypot(dx, dy) or 1
        sp = 0.03
        self.x += dx / d * sp
        self.y += dy / d * sp
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        if self.hurtcd > 0:
            self.hurtcd -= 1


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
        self.big = pygame.font.SysFont("arialrounded,arial", 54, bold=True)
        self.mid = pygame.font.SysFont("arial", 28, bold=True)
        self.small = pygame.font.SysFont("arial", 20, bold=True)
        self.tiny = pygame.font.SysFont("arial", 16, bold=True)
        self.audio = Audio()
        self.miner = make_miner()
        self.light = self._make_light(340)
        self.best = self._load_best()
        self.state = "menu"
        self.shop_open = False
        self.shop_buttons = {}
        self.reset()
        self.audio.start_music()

    def _make_light(self, R):
        m = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        for r in range(R, 0, -2):
            a = int(235 * (1 - r / R) ** 1.6)
            pygame.draw.circle(m, (0, 0, 0, a), (R, R), r)
        return m

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
        self.grid = {}
        self.gem = {}
        self.seed = random.randint(1, 999999)
        self.pcol = COLS // 2
        self.prow = 0
        self.cam = 0.0
        self.gold = 0
        self.bag = 0
        self.maxdepth = 0
        self.hp = 5
        self.maxhp = 5
        self.inv = 0
        self.oil = 100.0
        self.up = {"pick": 0, "lamp": 0, "oil": 0}
        self.move_cd = 0
        self.worms = []
        self.parts = []
        self.msg = ""
        self.msgt = 0
        self.shop_open = False

    # ---------- wereld ----------
    def _gen(self, col, row):
        key = (col, row)
        if key in self.grid:
            return self.grid[key]
        if row <= 0:
            self.grid[key] = "."
            return "."
        rng = random.Random(hash((col, row, self.seed)) & 0xffffffff)
        rock_p = min(0.34, 0.05 + row * 0.006)
        gem_p = 0.05 + min(0.09, row * 0.0016)
        v = rng.random()
        if v < 0.05:
            t = "."                       # holte
        elif v < 0.05 + rock_p:
            t = "R"
            self.gem[key] = 1 + row // 14  # rots-hardheid
        elif v < 0.05 + rock_p + gem_p:
            t = "G"
            tier = min(4, rng.randint(0, 1) + row // 12)
            self.gem[key] = tier
        else:
            t = "D"
        self.grid[key] = t
        return t

    def _dig_or_move(self, dx, dy):
        nc, nr = self.pcol + dx, self.prow + dy
        if nc < 0 or nc >= COLS or nr < -3:
            return
        t = self._gen(nc, nr)
        if t == "R":
            hard = self.gem.get((nc, nr), 1)
            if self.up["pick"] + 1 < hard:
                self.audio.play("rock")
                self.move_cd = 10
                return                    # te hard
            self.grid[(nc, nr)] = "."
            self._spark(nc, nr, ROCK)
            self.audio.play("rock")
            self.move_cd = max(8, 22 - self.up["pick"] * 3)
        elif t == "D":
            self.grid[(nc, nr)] = "."
            self._spark(nc, nr, DIRT)
            self.audio.play("dig")
            self.move_cd = 11
        elif t == "G":
            tier = self.gem.get((nc, nr), 0)
            self.bag += GEM_TIERS[tier][1]
            self.grid[(nc, nr)] = "."
            self._spark(nc, nr, GEM_TIERS[tier][0])
            self.audio.play("gem")
            self.move_cd = 11
        else:
            self.move_cd = 6
        self.pcol, self.prow = nc, nr
        if nr > self.maxdepth:
            self.maxdepth = nr
        # kans op worm dieper
        if nr > 6 and len(self.worms) < 3 and random.random() < 0.04:
            side = random.choice([-4, -3, 3, 4])
            self.worms.append(Worm(max(0, min(COLS - 1, nc + side)), nr + 2))

    def _spark(self, col, row, col_rgb):
        px = col * TS + TS // 2
        py = row * TS + TS // 2
        for _ in range(6):
            self.parts.append([px, py, random.uniform(-3, 3),
                               random.uniform(-3, 1), random.randint(8, 16),
                               col_rgb])

    # ---------- loop ----------
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    self._key(e.key)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self._click(e.pos)
            if self.state == "play" and not self.shop_open:
                self._update()
            self._draw()
            self.clock.tick(FPS)

    def _quit(self):
        if self.maxdepth > self.best:
            self.best = self.maxdepth
        self._save_best()
        pygame.quit()
        sys.exit()

    def _key(self, k):
        if k == pygame.K_i:
            self._info()
            return
        if k == pygame.K_d and self.state != "play":
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
            if self.shop_open:
                if k == pygame.K_ESCAPE:
                    self.shop_open = False
                return
            if k == pygame.K_p:
                self.state = "pause"
            elif k == pygame.K_ESCAPE:
                self.state = "pause"
            elif k == pygame.K_RETURN and self.prow <= 0:
                self.shop_open = True
        elif self.state == "pause":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"
        elif self.state == "over":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def _click(self, pos):
        if self.state == "menu":
            self.reset()
            self.state = "play"
            return
        if self.state == "play" and self.shop_open:
            for key, btn in self.shop_buttons.items():
                if btn.hit(pos):
                    self._buy(key)
                    return

    def _buy(self, key):
        if key == "heal":
            if self.gold >= 30 and self.hp < self.maxhp:
                self.gold -= 30
                self.hp = self.maxhp
                self.audio.play("buy")
            return
        if key == "armor":
            if self.maxhp >= 9:
                return
            c = 60 + (self.maxhp - 5) * 60
            if self.gold >= c:
                self.gold -= c
                self.maxhp += 1
                self.hp += 1
                self.audio.play("buy")
            return
        if self.up[key] >= 4:
            return
        c = 40 + self.up[key] * 65
        if self.gold >= c:
            self.gold -= c
            self.up[key] += 1
            self.audio.play("buy")

    # ---------- update ----------
    def _update(self):
        keys = pygame.key.get_pressed()
        if self.move_cd > 0:
            self.move_cd -= 1
        else:
            if keys[pygame.K_DOWN]:
                self._dig_or_move(0, 1)
            elif keys[pygame.K_UP]:
                self._dig_or_move(0, -1)
            elif keys[pygame.K_LEFT]:
                self._dig_or_move(-1, 0)
            elif keys[pygame.K_RIGHT]:
                self._dig_or_move(1, 0)

        # camera volgt speler (verticaal)
        target = self.prow * TS - H * 0.45
        self.cam += (target - self.cam) * 0.12

        # olie brandt op onder de grond
        if self.prow > 0:
            self.oil = max(0, self.oil - (0.05 - self.up["oil"] * 0.007))
        # aan de oppervlakte: verkopen + bijtanken
        if self.prow <= 0:
            if self.bag > 0:
                self.gold += self.bag
                self.msg = T("sold") % self.bag
                self.msgt = 90
                self.bag = 0
                self.audio.play("sell")
            self.oil = 100.0

        if self.inv > 0:
            self.inv -= 1

        # wormen
        for wmr in self.worms:
            wmr.update(self.pcol, self.prow)
            d = math.hypot(wmr.x - self.pcol, wmr.y - self.prow)
            if d < 0.7 and self.inv == 0:
                self.hp -= 1
                self.inv = 70
                self.audio.play("hit")
                # worm terugduwen
                ang = math.atan2(wmr.y - self.prow, wmr.x - self.pcol)
                wmr.x += math.cos(ang) * 2.2
                wmr.y += math.sin(ang) * 2.2
        self.worms = [w for w in self.worms
                      if abs(w.y - self.prow) < 20 and abs(w.x - self.pcol) < 20]

        # deeltjes
        for p in self.parts:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.3
            p[4] -= 1
        self.parts = [p for p in self.parts if p[4] > 0]

        # verstikken/dood
        if self.oil <= 0 and self.prow > 0 and random.random() < 0.01:
            # in het donker: kleine kans op verdwalen-schade
            if self.inv == 0:
                self.hp -= 1
                self.inv = 90
                self.audio.play("hit")
        if self.hp <= 0:
            if self.maxdepth > self.best:
                self.best = self.maxdepth
                self._save_best()
            self.state = "over"

        if self.msgt > 0:
            self.msgt -= 1

    # ---------- teken ----------
    def _draw(self):
        sc = self.screen
        if self.state == "menu":
            self._menu(sc)
            pygame.display.flip()
            return
        # lucht-gradient bovenin, donker eronder
        for y in range(H):
            world_y = y + self.cam
            if world_y < 0:
                col = SKY
            else:
                col = (18, 14, 24)
            sc.fill(col, (0, y, W, 1))

        r0 = int(self.cam // TS) - 1
        r1 = r0 + H // TS + 3
        for row in range(r0, r1):
            for col in range(COLS):
                self._draw_tile(sc, col, row)
        # deeltjes
        for p in self.parts:
            circ(sc, p[0] - 0, p[1] - self.cam, max(1, p[4] // 4), p[5])
        # wormen
        for wmr in self.worms:
            self._draw_worm(sc, wmr)
        # speler
        if not (self.inv > 0 and self.inv % 6 < 3):
            sc.blit(self.miner, (self.pcol * TS,
                                 int(self.prow * TS - self.cam)))
        # licht
        self._draw_light(sc)
        self._hud(sc)
        if self.prow <= 0 and not self.shop_open and self.state == "play":
            t = self.small.render(T("surface"), True, GOLDC)
            sc.blit(t, (W // 2 - t.get_width() // 2, 90))
        if self.msgt > 0:
            r = self.small.render(self.msg, True, (120, 255, 150))
            sc.blit(r, (W // 2 - r.get_width() // 2, 120))
        if self.shop_open:
            self._draw_shop(sc)
        elif self.state == "pause":
            self._overlay(sc, T("paused"), T("resume"))
        elif self.state == "over":
            self._overlay(sc, T("gameover"), T("reached") % self.maxdepth)
        pygame.display.flip()

    def _draw_tile(self, sc, col, row):
        t = self._gen(col, row)
        x = col * TS
        y = int(row * TS - self.cam)
        if row <= 0:
            if row == 0:
                pygame.draw.rect(sc, GRASS, (x, y, TS, 8))
                pygame.draw.rect(sc, DIRT_D, (x, y + 8, TS, TS - 8))
                if col in (COLS // 2 - 1, COLS // 2, COLS // 2 + 1) and row == 0:
                    pass
            return
        if t == "D":
            pygame.draw.rect(sc, DIRT, (x, y, TS, TS))
            pygame.draw.rect(sc, DIRT_D, (x, y, TS, TS), 1)
            random.seed(col * 31 + row * 17)
            for _ in range(3):
                circ(sc, x + random.randint(6, TS - 6),
                     y + random.randint(6, TS - 6), 2, DIRT_D)
            random.seed()
        elif t == "R":
            pygame.draw.rect(sc, ROCK, (x, y, TS, TS))
            pygame.draw.rect(sc, ROCK_D, (x, y, TS, TS), 2)
            hard = self.gem.get((col, row), 1)
            if hard > 1:
                circ(sc, x + TS // 2, y + TS // 2, 4, (140, 140, 160))
        elif t == "G":
            pygame.draw.rect(sc, DIRT, (x, y, TS, TS))
            tier = self.gem.get((col, row), 0)
            gc = GEM_TIERS[tier][0]
            cx, cy = x + TS // 2, y + TS // 2
            poly(sc, [(cx, cy - 10), (cx + 9, cy), (cx, cy + 10),
                      (cx - 9, cy)], gc)
            circ(sc, cx - 3, cy - 3, 2, (255, 255, 255))
        # '.' = leeg: niets (donker)

    def _draw_worm(self, sc, wmr):
        for i, (tx, ty) in enumerate(wmr.trail):
            r = 6 + i
            circ(sc, tx * TS + TS // 2, ty * TS + TS // 2 - self.cam, r,
                 (150, 90, 120) if i < len(wmr.trail) - 1 else (190, 110, 140))
        hx = wmr.x * TS + TS // 2
        hy = wmr.y * TS + TS // 2 - self.cam
        circ(sc, hx, hy, 11, (200, 120, 150))
        circ(sc, hx - 3, hy - 2, 2, (30, 20, 30))
        circ(sc, hx + 3, hy - 2, 2, (30, 20, 30))

    def _draw_light(self, sc):
        R = 205 + self.up["lamp"] * 40
        R = int(R * (0.52 + 0.48 * self.oil / 100))
        shadow = pygame.Surface((W, H), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 232))
        light = pygame.transform.smoothscale(self.light, (R * 2, R * 2))
        px = self.pcol * TS + TS // 2
        py = int(self.prow * TS - self.cam) + TS // 2
        shadow.blit(light, (px - R, py - R),
                    special_flags=pygame.BLEND_RGBA_SUB)
        sc.blit(shadow, (0, 0))

    def _hud(self, sc):
        for i in range(self.maxhp):
            c = (220, 70, 90) if i < self.hp else (70, 55, 70)
            self._heart(sc, 22 + i * 26, 26, c)
        g = self.small.render("%s: %d" % (T("gold"), self.gold), True, GOLDC)
        sc.blit(g, (22, 44))
        b = self.small.render("%s: %d" % (T("bag"), self.bag), True,
                              (150, 230, 255))
        sc.blit(b, (22, 70))
        d = self.small.render("%s: %d   %s: %d" %
                              (T("depth"), self.maxdepth, T("best"), self.best),
                              True, INK)
        sc.blit(d, (W - d.get_width() - 20, 20))
        # olie
        pygame.draw.rect(sc, (40, 34, 26), (W - 220, 50, 200, 14),
                         border_radius=7)
        oc = (255, 200, 80) if self.oil > 25 else (255, 90, 60)
        pygame.draw.rect(sc, oc, (W - 220, 50, int(200 * self.oil / 100), 14),
                         border_radius=7)
        ot = self.tiny.render(T("oil"), True, INK)
        sc.blit(ot, (W - 220, 66))

    def _heart(self, sc, x, y, c):
        circ(sc, x - 4, y, 5, c)
        circ(sc, x + 4, y, 5, c)
        poly(sc, [(x - 9, y + 1), (x + 9, y + 1), (x, y + 11)], c)

    def _draw_shop(self, sc):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 210))
        sc.blit(o, (0, 0))
        self._center(sc, T("shop"), self.big, PURPLE_L, -230)
        self._center(sc, "%s: %d" % (T("gold"), self.gold), self.mid,
                     GOLDC, -170)
        rows = [("pick", T("up_pick")), ("lamp", T("up_lamp")),
                ("oil", T("up_oil")), ("armor", T("up_armor")),
                ("heal", T("up_heal"))]
        self.shop_buttons = {}
        y = 190
        for key, name in rows:
            label = name
            if key in self.up:
                label = "%s  (%s %d/4)" % (name, T("lvl"), self.up[key])
            r = self.small.render(label, True, INK)
            sc.blit(r, (150, y + 10))
            cost, maxed = self._shop_cost(key)
            if maxed:
                b = self.small.render(T("maxed"), True, (150, 150, 160))
                sc.blit(b, (700, y + 10))
            else:
                btn = Button(680, y, 130, 40, "%s %d" % (T("buy"), cost))
                btn.draw(sc, self.tiny, btn.hit(pygame.mouse.get_pos()))
                self.shop_buttons[key] = btn
            y += 58
        self._center(sc, T("close"), self.small, PURPLE_L, 210)

    def _shop_cost(self, key):
        if key == "heal":
            return 30, self.hp >= self.maxhp
        if key == "armor":
            return 60 + (self.maxhp - 5) * 60, self.maxhp >= 9
        return 40 + self.up[key] * 65, self.up[key] >= 4

    def _center(self, sc, txt, font, col, dy=0):
        r = font.render(txt, True, col)
        sc.blit(r, (W // 2 - r.get_width() // 2, H // 2 + dy))

    def _overlay(self, sc, title, sub):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 180))
        sc.blit(o, (0, 0))
        self._center(sc, title, self.big, (240, 130, 130), -50)
        self._center(sc, sub, self.mid, INK, 16)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 64)
        self._center(sc, T("menu"), self.small, (170, 160, 190), 98)

    def _menu(self, sc):
        for y in range(H):
            sc.fill((int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * y / H),
                     int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * y / H),
                     int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * y / H)),
                    (0, y, W, 1))
        big = pygame.transform.smoothscale(self.miner, (96, 96))
        sc.blit(big, (W // 2 - 48, 150))
        for i, (gc, _v) in enumerate(GEM_TIERS):
            cx = W // 2 - 100 + i * 50
            poly(sc, [(cx, 300), (cx + 9, 310), (cx, 320), (cx - 9, 310)], gc)
        self._center(sc, T("title"), self.big, PURPLE_L, -190)
        self._center(sc, T("sub"), self.mid, (200, 190, 225), -130)
        self._center(sc, T("start"), self.mid, GOLDC, 120)
        self._center(sc, T("ctrl"), self.small, INK, 170)
        self._center(sc, "%s    %s    %s" %
                     (T("donate"), T("info"), T("quit")),
                     self.small, (170, 160, 195), 206)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 242)

    def _info(self):
        self._draw()
        box = pygame.Surface((660, 190), pygame.SRCALPHA)
        box.fill((20, 16, 30, 240))
        pygame.draw.rect(box, PURPLE_L, box.get_rect(), 2, border_radius=10)
        y = 24
        for line in T("info_txt").split("\n"):
            box.blit(self.small.render(line, True, INK), (24, y))
            y += 30
        self.screen.blit(box, (W // 2 - 330, H // 2 - 95))
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

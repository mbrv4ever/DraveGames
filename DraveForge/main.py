# -*- coding: utf-8 -*-
"""DraveForge - een gezellige smid-game van Dravenlock.

Een klant komt met een bestelling. Jij verhit het metaal tot de juiste gloed,
hamert het op het ritme en koelt het op het juiste moment af. Hoe beter je
timing, hoe mooier het wapen en hoe meer goud. Koop upgrades en word de beste
draken-smid.

Besturing: MUIS (of SPATIE) om te timen, Enter = verder, P = pauze, Esc = terug.
Tweetalig NL/EN, procedurele audio, portable (alles in de app-map). Donationware.
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

W, H = 960, 600
FPS = 60
SR = 22050

# ---- kleuren (Dravenlock donker-paars) ----
BG_TOP = (26, 20, 38)
BG_BOT = (44, 32, 64)
PURPLE = (128, 94, 205)
PURPLE_L = (176, 150, 236)
PURPLE_D = (74, 58, 110)
INK = (230, 224, 245)
GOLDC = (255, 205, 70)
STONE = (70, 62, 84)
STONE_D = (50, 44, 64)
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
    "title": {"nl": "DraveForge", "en": "DraveForge"},
    "sub": {"nl": "De smederij van Dravenlock", "en": "The Dravenlock forge"},
    "start": {"nl": "Enter = start", "en": "Enter = start"},
    "ctrl": {"nl": "Muis of spatie = timen    Enter = verder    P = pauze",
             "en": "Mouse or space = time it    Enter = next    P = pause"},
    "donate": {"nl": "D = doneren", "en": "D = donate"},
    "info": {"nl": "I = info", "en": "I = info"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "gold": {"nl": "Goud", "en": "Gold"},
    "day": {"nl": "Dag", "en": "Day"},
    "best": {"nl": "Record", "en": "Best"},
    "order": {"nl": "Bestelling:", "en": "Order:"},
    "click_start": {"nl": "Klik of Enter om te beginnen",
                    "en": "Click or Enter to begin"},
    "shop_btn": {"nl": "Winkel", "en": "Shop"},
    "heat": {"nl": "Verhit tot de groene gloed - klik!",
             "en": "Heat to the green glow - click!"},
    "hammer": {"nl": "Hamer op het ritme - klik in de zone!",
               "en": "Hammer to the beat - click in the zone!"},
    "quench": {"nl": "Koel af op het juiste moment - klik!",
               "en": "Quench at the right moment - click!"},
    "hits_left": {"nl": "Slagen", "en": "Hits"},
    "perfect": {"nl": "Perfect!", "en": "Perfect!"},
    "good": {"nl": "Goed", "en": "Good"},
    "miss": {"nl": "Mis", "en": "Miss"},
    "too_cold": {"nl": "Te koud", "en": "Too cold"},
    "too_hot": {"nl": "Verbrand!", "en": "Burnt!"},
    "result": {"nl": "Resultaat", "en": "Result"},
    "quality": {"nl": "Kwaliteit", "en": "Quality"},
    "paid": {"nl": "Betaald", "en": "Paid"},
    "cont": {"nl": "Enter = volgende klant", "en": "Enter = next customer"},
    "q0": {"nl": "Slecht", "en": "Poor"},
    "q1": {"nl": "Redelijk", "en": "Fair"},
    "q2": {"nl": "Goed", "en": "Good"},
    "q3": {"nl": "Prachtig", "en": "Fine"},
    "q4": {"nl": "Meesterwerk!", "en": "Masterwork!"},
    "shop": {"nl": "Smid-winkel", "en": "Smith's shop"},
    "up_hammer": {"nl": "Betere hamer (grotere zone)",
                  "en": "Better hammer (bigger zone)"},
    "up_forge": {"nl": "Hetere oven (bredere gloed)",
                 "en": "Hotter forge (wider glow)"},
    "up_quench": {"nl": "Koelvat (grotere zone)",
                  "en": "Quench tank (bigger zone)"},
    "up_tip": {"nl": "Reputatie (meer fooi)", "en": "Reputation (more tips)"},
    "lvl": {"nl": "niv.", "en": "lvl"},
    "maxed": {"nl": "MAX", "en": "MAX"},
    "buy": {"nl": "Kopen", "en": "Buy"},
    "close": {"nl": "Klaar (Esc)", "en": "Done (Esc)"},
    "paused": {"nl": "Pauze", "en": "Paused"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "sword": {"nl": "Zwaard", "en": "Sword"},
    "shield": {"nl": "Schild", "en": "Shield"},
    "dagger": {"nl": "Dolk", "en": "Dagger"},
    "axe": {"nl": "Bijl", "en": "Axe"},
    "info_txt": {
        "nl": "DraveForge - smeed wapens op timing en word de beste smid.\n"
              "Muis/spatie om te timen. Donationware - https://paypal.me/roger076"
              "\nservice@dravenlock.nl",
        "en": "DraveForge - forge weapons on timing and become the best smith.\n"
              "Mouse/space to time. Donationware - https://paypal.me/roger076"
              "\nservice@dravenlock.nl"},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"
ITEMS = ["sword", "shield", "dagger", "axe"]
BASE_PAY = {"sword": 42, "shield": 36, "dagger": 26, "axe": 48}


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


def _mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def draw_item(kind, quality, glow=0.0, scale=1.0):
    """Teken een wapen. quality 0..1 bepaalt glans/deuken; glow 0..1 = gloeiend."""
    s = pygame.Surface((160, 160), pygame.SRCALPHA)
    cool = IRON
    hot = _mix((255, 90, 30), (255, 240, 150), min(1, glow))
    metal = _mix(cool, hot, glow)
    edge = _mix((210, 210, 225), (255, 250, 200), glow)
    q = quality
    if kind == "sword":
        poly(s, [(80, 20), (90, 40), (86, 110), (80, 120), (74, 110),
                 (70, 40)], metal)
        poly(s, [(80, 20), (86, 40), (82, 108), (80, 116)], edge)
        pygame.draw.rect(s, (110, 82, 54), (66, 118, 28, 8))       # pareerstang
        pygame.draw.rect(s, (90, 66, 44), (75, 126, 10, 22))       # greep
        circ(s, 80, 150, 6, GOLDC)                                 # knop
    elif kind == "shield":
        poly(s, [(80, 26), (120, 44), (114, 100), (80, 134),
                 (46, 100), (40, 44)], metal)
        poly(s, [(80, 40), (104, 52), (100, 92), (80, 112),
                 (60, 92), (56, 52)], _mix(metal, PURPLE_D, 0.5))
        circ(s, 80, 78, 10, edge)
    elif kind == "dagger":
        poly(s, [(80, 34), (88, 50), (84, 104), (80, 112), (76, 104),
                 (72, 50)], metal)
        poly(s, [(80, 34), (85, 50), (82, 102), (80, 110)], edge)
        pygame.draw.rect(s, (110, 82, 54), (70, 110, 20, 6))
        pygame.draw.rect(s, (90, 66, 44), (76, 116, 8, 20))
    elif kind == "axe":
        pygame.draw.rect(s, (96, 70, 46), (78, 30, 8, 110))        # steel
        poly(s, [(86, 40), (128, 34), (120, 74), (86, 72)], metal)  # blad
        poly(s, [(120, 40), (128, 36), (122, 68), (116, 66)], edge)
    # deuken bij lage kwaliteit
    if q < 0.55:
        random.seed(int(q * 1000) + 7)
        for _ in range(int((0.55 - q) * 10)):
            dx = random.randint(60, 100)
            dy = random.randint(40, 110)
            circ(s, dx, dy, 2, (40, 40, 50))
        random.seed()
    # glans bij hoge kwaliteit
    if q > 0.8 and glow < 0.3:
        for _ in range(int((q - 0.8) * 30)):
            sx = random.randint(66, 96)
            sy = random.randint(30, 110)
            circ(s, sx, sy, 1, (255, 255, 255))
    if scale != 1.0:
        s = pygame.transform.smoothscale(
            s, (int(160 * scale), int(160 * scale)))
    return s


def draw_customer(idx):
    """Klein klant-personage (variatie in kleur/type)."""
    s = pygame.Surface((120, 160), pygame.SRCALPHA)
    palettes = [((150, 90, 90), (210, 180, 150)),   # dorpeling rood
                ((90, 120, 150), (210, 180, 150)),   # blauw
                ((110, 140, 90), (210, 180, 150)),   # groen
                ((120, 120, 130), (210, 185, 155))]  # ridder grijs
    robe, skin = palettes[idx % len(palettes)]
    knight = idx % len(palettes) == 3
    poly(s, [(40, 150), (80, 150), (74, 84), (46, 84)], robe)     # gewaad
    circ(s, 60, 70, 16, skin)                                     # hoofd
    if knight:
        pygame.draw.arc(s, IRON, (44, 54, 32, 34), 0.2, 2.9, 5)   # helm
        pygame.draw.rect(s, IRON, (44, 66, 32, 6))
    else:
        poly(s, [(44, 60), (76, 60), (60, 40)], (90, 66, 44))     # kap/haar
    circ(s, 54, 70, 2, (30, 24, 34))
    circ(s, 66, 70, 2, (30, 24, 34))
    poly(s, [(46, 92), (40, 120), (48, 120), (52, 94)], robe)     # arm
    return s


# --------------------------------------------------------------- audio (synth)
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
        self.snd["clang"] = make_sound(mixbuf(tone(680, 120, 0.35, "square"),
                                              tone(1020, 90, 0.2)))
        self.snd["perfect"] = make_sound(mixbuf(tone(880, 90, 0.3),
                                                tone(1320, 120, 0.28)))
        self.snd["miss"] = make_sound(tone(150, 160, 0.3, "saw"))
        self.snd["heat"] = make_sound(tone(120, 300, 0.25, "noise"))
        self.snd["quench"] = make_sound(tone(300, 360, 0.3, "noise"))
        self.snd["cash"] = make_sound(mixbuf(tone(720, 90, 0.3),
                                             tone(960, 120, 0.28),
                                             tone(1200, 150, 0.24)))
        self.snd["buy"] = make_sound(mixbuf(tone(520, 80, 0.3),
                                            tone(780, 110, 0.26)))
        self._music()

    def _music(self):
        base = [196, 247, 294, 247, 175, 220, 262, 220]
        loop = array("h")
        for f in base:
            loop.extend(mixbuf(tone(f, 300, 0.12, "saw"),
                               tone(f / 2, 300, 0.12, "sine")))
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


# --------------------------------------------------------------------- knop
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
        self.big = pygame.font.SysFont("arialrounded,arial", 58, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("arial", 21, bold=True)
        self.tiny = pygame.font.SysFont("arial", 17, bold=True)
        self.audio = Audio()
        self.bg = self._make_bg()
        self.best = self._load_best()
        # upgrades: hamer, oven, koelvat, reputatie (0..4)
        self.up = {"hammer": 0, "forge": 0, "quench": 0, "tip": 0}
        self.gold = 0
        self.day = 1
        self.served = 0
        self.state = "menu"
        self.hammer_anim = 0.0
        self.sparks = []
        self.msg = ""
        self.msgt = 0
        self.shop_btn = Button(W - 150, 20, 130, 44, T("shop_btn"))
        self.shop_buttons = {}
        self._new_customer()
        self.audio.start_music()

    # ---------- opslag ----------
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

    # ---------- achtergrond ----------
    def _make_bg(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            s.fill(_mix(BG_TOP, BG_BOT, y / H), (0, y, W, 1))
        # stenen vloer
        pygame.draw.rect(s, (40, 34, 50), (0, H - 90, W, 90))
        for x in range(0, W, 64):
            pygame.draw.line(s, (30, 26, 40), (x, H - 90), (x, H), 2)
        pygame.draw.line(s, (54, 46, 66), (0, H - 90), (W, H - 90), 3)
        # oven links (stenen boog)
        pygame.draw.rect(s, STONE, (40, 200, 200, 300))
        pygame.draw.rect(s, STONE_D, (70, 250, 140, 250))
        pygame.draw.arc(s, STONE_D, (70, 210, 140, 120), 0, math.pi, 40)
        return s

    def _forge_fire(self, sc):
        cx, cy = 140, 380
        for _ in range(10):
            fx = cx + random.randint(-40, 40)
            fy = cy - random.randint(0, 70)
            r = random.randint(6, 20)
            col = random.choice([(255, 140, 40), (255, 200, 70),
                                 (240, 90, 30), (255, 170, 50)])
            circ(sc, fx, fy, r, col)
        glow = pygame.Surface((200, 200), pygame.SRCALPHA)
        circ(glow, 100, 100, 90, (255, 140, 40, 40))
        sc.blit(glow, (cx - 100, cy - 110))

    # ---------- klant / bestelling ----------
    def _new_customer(self):
        self.order = random.choice(ITEMS)
        self.cust = random.randint(0, 3)
        self.cust_img = draw_customer(self.cust)
        self.item_icon = draw_item(self.order, 0.85, 0.0, 0.6)
        self.phase = "order"
        self.heat_q = self.quench_q = 0.0
        self.hits = []
        self.hit_target = 5
        self.heat_v = 0.0
        self.heat_dir = 1
        self.mark = 0.0
        self.mark_dir = 1
        self.cool_v = 100.0
        self.item_quality = 0.0
        self.pay = 0

    # ---------- zones (met upgrades / dag) ----------
    def _heat_band(self):
        half = 8 + self.up["forge"] * 3
        return 70 - half, 70 + half        # ideaal rond 70

    def _hammer_half(self):
        return 0.09 + self.up["hammer"] * 0.028

    def _quench_zone(self):
        half = 7 + self.up["quench"] * 3
        return 45 - half, 45 + half        # ideaal rond 45 (van 100->0)

    def _speed(self):
        return 1.0 + (self.day - 1) * 0.06

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
            if self.state == "play":
                self._update()
            self._draw()
            self.clock.tick(FPS)

    def _quit(self):
        if self.gold > self.best:
            self.best = self.gold
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
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self._quit()
        elif self.state == "play":
            if k in (pygame.K_p,):
                self.state = "pause"
            elif k == pygame.K_ESCAPE:
                if self.phase == "shop":
                    self.phase = "order"
                else:
                    self.state = "pause"
            elif k == pygame.K_SPACE:
                self._action()
            elif k == pygame.K_RETURN:
                self._advance()
        elif self.state == "pause":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"

    def _click(self, pos):
        if self.state == "menu":
            self.state = "play"
            return
        if self.state != "play":
            return
        if self.phase == "order":
            if self.shop_btn.hit(pos):
                self.phase = "shop"
                return
            self.phase = "heat"
            return
        if self.phase == "shop":
            for key, btn in self.shop_buttons.items():
                if btn.hit(pos):
                    self._buy(key)
                    return
            return
        if self.phase == "result":
            self._advance()
            return
        self._action()

    # ---------- de smeed-actie (timing) ----------
    def _action(self):
        if self.phase == "heat":
            lo, hi = self._heat_band()
            v = self.heat_v
            if v < lo - 12:
                self.heat_q = 0.15
                self._flash(T("too_cold"), (150, 180, 255))
            elif v > hi + 12:
                self.heat_q = 0.1
                self._flash(T("too_hot"), (255, 120, 60))
            else:
                d = abs(v - 70) / (hi - 70 + 12)
                self.heat_q = max(0.3, 1.0 - d)
                self._flash(T("perfect") if self.heat_q > 0.85
                            else T("good"),
                            (120, 255, 140) if self.heat_q > 0.85
                            else GOLDC)
            self.audio.play("heat")
            self.phase = "hammer"
        elif self.phase == "hammer":
            half = self._hammer_half()
            d = abs(self.mark - 0.5)
            if d <= half * 0.4:
                q = 1.0
                self._flash(T("perfect"), (120, 255, 140))
                self.audio.play("perfect")
            elif d <= half:
                q = 0.7
                self._flash(T("good"), GOLDC)
                self.audio.play("clang")
            else:
                q = 0.15
                self._flash(T("miss"), (255, 120, 120))
                self.audio.play("miss")
            self.hits.append(q)
            self._swing()
            if len(self.hits) >= self.hit_target:
                self.phase = "quench"
                self.cool_v = 100.0
        elif self.phase == "quench":
            lo, hi = self._quench_zone()
            v = self.cool_v
            if lo <= v <= hi:
                self.quench_q = 1.0
                self._flash(T("perfect"), (120, 255, 140))
            elif lo - 12 <= v <= hi + 12:
                self.quench_q = 0.6
                self._flash(T("good"), GOLDC)
            else:
                self.quench_q = 0.2
                self._flash(T("miss"), (255, 120, 120))
            self.audio.play("quench")
            self._finish()

    def _finish(self):
        hammer_q = sum(self.hits) / len(self.hits) if self.hits else 0
        total = 0.34 * self.heat_q + 0.46 * hammer_q + 0.20 * self.quench_q
        self.item_quality = total
        base = BASE_PAY[self.order]
        tip = 1.0 + self.up["tip"] * 0.12
        self.pay = int(base * (0.35 + 1.15 * total) * tip)
        self.gold += self.pay
        if self.gold > self.best:
            self.best = self.gold
        self.served += 1
        if self.served % 5 == 0:
            self.day += 1
        self.result_item = draw_item(self.order, total, 0.0, 1.0)
        self.audio.play("cash")
        self.phase = "result"

    def _advance(self):
        if self.phase == "result":
            self._new_customer()
        elif self.phase == "order":
            self.phase = "heat"

    def _swing(self):
        self.hammer_anim = 1.0
        for _ in range(10):
            self.sparks.append([480, 430, random.uniform(-4, 4),
                                random.uniform(-6, -1), random.randint(10, 20)])

    def _flash(self, txt, col):
        self.msg = txt
        self.msg_col = col
        self.msgt = 45

    # ---------- winkel ----------
    def _cost(self, key):
        return 60 + self.up[key] * 90

    def _buy(self, key):
        if self.up[key] >= 4:
            return
        c = self._cost(key)
        if self.gold >= c:
            self.gold -= c
            self.up[key] += 1
            self.audio.play("buy")

    # ---------- update ----------
    def _update(self):
        sp = self._speed()
        if self.phase == "heat":
            self.heat_v += self.heat_dir * 1.4 * sp
            if self.heat_v >= 100:
                self.heat_v, self.heat_dir = 100, -1
            elif self.heat_v <= 0:
                self.heat_v, self.heat_dir = 0, 1
        elif self.phase == "hammer":
            self.mark += self.mark_dir * 0.02 * sp
            if self.mark >= 1:
                self.mark, self.mark_dir = 1, -1
            elif self.mark <= 0:
                self.mark, self.mark_dir = 0, 1
        elif self.phase == "quench":
            self.cool_v -= 1.1 * sp
            if self.cool_v <= 0:
                self.cool_v = 0
                self.quench_q = 0.15
                self._finish()
        if self.hammer_anim > 0:
            self.hammer_anim = max(0, self.hammer_anim - 0.12)
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[3] += 0.5
            s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        if self.msgt > 0:
            self.msgt -= 1

    # ---------- teken ----------
    def _draw(self):
        sc = self.screen
        sc.blit(self.bg, (0, 0))
        if self.state != "menu":
            self._forge_fire(sc)
            self._draw_anvil(sc)
        if self.state == "menu":
            self._menu(sc)
        elif self.state in ("play", "pause"):
            self._draw_play(sc)
            if self.state == "pause":
                self._overlay(sc, T("paused"), T("resume"))
        pygame.display.flip()

    def _draw_anvil(self, sc):
        # aambeeld
        pygame.draw.rect(sc, STONE_D, (430, 470, 100, 40))
        poly(sc, [(420, 430), (560, 430), (540, 470), (440, 470)], IRON_D)
        poly(sc, [(560, 430), (600, 424), (592, 444), (556, 448)], IRON_D)
        pygame.draw.rect(sc, IRON, (420, 424, 140, 10))

    def _draw_hammer(self, sc):
        # hamer die neerkomt tijdens hameren
        base_ang = -0.5 - self.hammer_anim * 0.9
        px, py = 500, 350
        hx = px + math.cos(base_ang) * 70
        hy = py + math.sin(base_ang) * 70
        pygame.draw.line(sc, (110, 82, 54), (px, py), (hx, hy), 8)
        head = pygame.Surface((44, 26), pygame.SRCALPHA)
        pygame.draw.rect(head, IRON, (0, 0, 44, 26), border_radius=4)
        pygame.draw.rect(head, IRON_D, (0, 0, 44, 26), 2, border_radius=4)
        head = pygame.transform.rotate(head, -math.degrees(base_ang))
        sc.blit(head, (hx - head.get_width() // 2, hy - head.get_height() // 2))

    def _draw_play(self, sc):
        # goud / dag / record
        g = self.mid.render("%s: %d" % (T("gold"), self.gold), True, GOLDC)
        sc.blit(g, (20, 18))
        d = self.small.render("%s %d   %s: %d" %
                              (T("day"), self.day, T("best"), self.best),
                              True, INK)
        sc.blit(d, (20, 58))

        glow = 0.0
        if self.phase in ("heat",):
            glow = max(0, min(1, self.heat_v / 100))
        elif self.phase in ("hammer",):
            glow = 0.7
        elif self.phase == "quench":
            glow = self.cool_v / 100 * 0.9
        # werkstuk op het aambeeld
        if self.phase in ("heat", "hammer", "quench"):
            it = draw_item(self.order, 0.6, glow, 0.7)
            sc.blit(it, (480 - it.get_width() // 2, 360))
        if self.phase == "hammer":
            self._draw_hammer(sc)
        for s in self.sparks:
            circ(sc, s[0], s[1], max(1, s[4] // 5), (255, 210, 90))

        if self.phase == "order":
            self._draw_order(sc)
        elif self.phase == "heat":
            self._draw_heat(sc)
        elif self.phase == "hammer":
            self._draw_hammer_ui(sc)
        elif self.phase == "quench":
            self._draw_quench(sc)
        elif self.phase == "result":
            self._draw_result(sc)
        elif self.phase == "shop":
            self._draw_shop(sc)

        if self.msgt > 0 and self.phase in ("heat", "hammer", "quench"):
            r = self.mid.render(self.msg, True, self.msg_col)
            sc.blit(r, (480 - r.get_width() // 2, 300))

    def _draw_order(self, sc):
        sc.blit(self.cust_img, (720, 300))
        # tekstballon
        pygame.draw.rect(sc, (245, 242, 250), (610, 250, 240, 90),
                         border_radius=14)
        poly(sc, [(700, 338), (720, 338), (712, 360)], (245, 242, 250))
        o = self.small.render(T("order"), True, (40, 30, 60))
        sc.blit(o, (628, 262))
        nm = self.small.render(T(self.order), True, (90, 60, 150))
        sc.blit(nm, (628, 290))
        sc.blit(self.item_icon, (770, 250))
        self.shop_btn.draw(sc, self.small,
                           self.shop_btn.hit(pygame.mouse.get_pos()))
        t = self.small.render(T("click_start"), True, PURPLE_L)
        sc.blit(t, (480 - t.get_width() // 2, 250))

    def _bar(self, sc, x, y, w, h, frac, col, band=None):
        pygame.draw.rect(sc, (30, 24, 40), (x, y, w, h), border_radius=8)
        if band:
            bl, bh = band
            pygame.draw.rect(sc, (60, 150, 80),
                             (x + w * bl / 100, y, w * (bh - bl) / 100, h),
                             border_radius=4)
        mx = x + w * frac
        pygame.draw.rect(sc, col, (mx - 4, y - 6, 8, h + 12), border_radius=4)
        pygame.draw.rect(sc, PURPLE_L, (x, y, w, h), 2, border_radius=8)

    def _draw_heat(self, sc):
        self._title(sc, T("heat"))
        lo, hi = self._heat_band()
        self._bar(sc, 230, 150, 500, 30, self.heat_v / 100,
                  (255, 160, 60), (lo, hi))

    def _draw_hammer_ui(self, sc):
        self._title(sc, T("hammer"))
        half = self._hammer_half()
        self._bar(sc, 230, 150, 500, 30, self.mark, PURPLE_L,
                  ((0.5 - half) * 100, (0.5 + half) * 100))
        h = self.small.render("%s: %d/%d" % (T("hits_left"), len(self.hits),
                                             self.hit_target), True, INK)
        sc.blit(h, (480 - h.get_width() // 2, 195))

    def _draw_quench(self, sc):
        self._title(sc, T("quench"))
        lo, hi = self._quench_zone()
        self._bar(sc, 230, 150, 500, 30, self.cool_v / 100,
                  (120, 200, 255), (lo, hi))

    def _title(self, sc, txt):
        r = self.mid.render(txt, True, INK)
        sc.blit(r, (480 - r.get_width() // 2, 105))

    def _draw_result(self, sc):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 150))
        sc.blit(o, (0, 0))
        self._center(sc, T("result"), self.big, PURPLE_L, -200)
        sc.blit(self.result_item, (480 - 80, 150))
        ql = min(4, int(self.item_quality * 5))
        label = T("q%d" % ql)
        col = (120, 255, 140) if ql >= 3 else (GOLDC if ql >= 2
                                               else (230, 160, 160))
        self._center(sc, "%s: %s" % (T("quality"), label), self.mid, col, 70)
        self._center(sc, "%s: %d %s" % (T("paid"), self.pay, "🪙"),
                     self.mid, GOLDC, 120)
        self._center(sc, T("cont"), self.small, INK, 180)

    def _draw_shop(self, sc):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 200))
        sc.blit(o, (0, 0))
        self._center(sc, T("shop"), self.big, PURPLE_L, -220)
        self._center(sc, "%s: %d" % (T("gold"), self.gold), self.mid,
                     GOLDC, -150)
        items = [("hammer", T("up_hammer")), ("forge", T("up_forge")),
                 ("quench", T("up_quench")), ("tip", T("up_tip"))]
        self.shop_buttons = {}
        y = 210
        for key, name in items:
            lvl = self.up[key]
            r = self.small.render("%s  (%s %d/4)" % (name, T("lvl"), lvl),
                                  True, INK)
            sc.blit(r, (200, y + 10))
            if lvl >= 4:
                b = self.small.render(T("maxed"), True, (150, 150, 160))
                sc.blit(b, (660, y + 10))
            else:
                btn = Button(660, y, 120, 40,
                             "%s %d" % (T("buy"), self._cost(key)))
                btn.draw(sc, self.tiny, btn.hit(pygame.mouse.get_pos()))
                self.shop_buttons[key] = btn
            y += 64
        self._center(sc, T("close"), self.small, PURPLE_L, 210)

    def _center(self, sc, txt, font, col, dy=0):
        r = font.render(txt, True, col)
        sc.blit(r, (W // 2 - r.get_width() // 2, H // 2 + dy))

    def _overlay(self, sc, title, sub):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 170))
        sc.blit(o, (0, 0))
        self._center(sc, title, self.big, PURPLE_L, -40)
        self._center(sc, sub, self.mid, INK, 30)

    def _menu(self, sc):
        icon = draw_item("sword", 0.95, 0.0, 1.3)
        sc.blit(icon, (W // 2 - 104, 120))
        icon2 = draw_item("axe", 0.9, 0.0, 1.0)
        sc.blit(icon2, (W // 2 + 30, 150))
        self._center(sc, T("title"), self.big, PURPLE_L, -190)
        self._center(sc, T("sub"), self.mid, (200, 190, 225), -130)
        self._center(sc, T("start"), self.mid, GOLDC, 150)
        self._center(sc, T("ctrl"), self.small, INK, 200)
        self._center(sc, "%s    %s    %s" %
                     (T("donate"), T("info"), T("quit")),
                     self.small, (170, 160, 195), 236)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 272)

    def _info(self):
        self._draw()
        box = pygame.Surface((640, 200), pygame.SRCALPHA)
        box.fill((20, 16, 30, 240))
        pygame.draw.rect(box, PURPLE_L, box.get_rect(), 2, border_radius=10)
        y = 24
        for line in T("info_txt").split("\n"):
            box.blit(self.small.render(line, True, INK), (24, y))
            y += 30
        self.screen.blit(box, (W // 2 - 320, H // 2 - 100))
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

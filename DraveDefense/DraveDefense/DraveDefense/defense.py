# -*- coding: utf-8 -*-
"""defense.py - DraveDefense, een D&D-tower-defense van Dravenlock Games.

Vijanden (goblins, skeletten, orks) lopen over een pad naar je kasteel. Bouw
torens op de open plekken om ze tegen te houden: een boogschutter (snel,
goedkoop), een magier (krachtig, met splash) en een vorsttoren (vertraagt).
Elke verslagen vijand levert goud op om bij te bouwen of te upgraden. De golven
worden zwaarder; in de laatste golf verschijnt een draak als eindbaas. Bereikt
een vijand het kasteel, dan kost dat een leven; zijn al je levens op, dan verlies je.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke knoppen/HUD; procedurele muziek en geluiden (sfx.py); gesproken
intro (neuvoice) in een apart splashvenster. Volledig draagbaar: alles wordt
bewaard in een map "DraveDefense-data" naast het programma.
"""
from __future__ import annotations

import json
import math
import os
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

APP_NAME = "DraveDefense"
APP_VERSION = "0.2.0"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 80
TILE = 60
COLS = 16
ROWS = 8
FIELD_Y = HUD_H

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
GRASS = (32, 40, 32)
GRASS2 = (28, 35, 28)
PATH_COL = (66, 56, 44)
PATH_EDGE = (52, 44, 34)

# pad als reeks rastercellen (kolom, rij)
PATH_CELLS = [
    (0, 1), (1, 1), (2, 1), (3, 1),
    (3, 2), (3, 3),
    (4, 3), (5, 3), (6, 3),
    (6, 4), (6, 5),
    (7, 5), (8, 5), (9, 5),
    (9, 4), (9, 3), (9, 2),
    (10, 2), (11, 2), (12, 2),
    (12, 3), (12, 4), (12, 5),
    (13, 5), (14, 5), (15, 5),
]
PATH_SET = set(PATH_CELLS)


def cell_center(col, row):
    return (col * TILE + TILE // 2, FIELD_Y + row * TILE + TILE // 2)


WAYPOINTS = [cell_center(c, r) for (c, r) in PATH_CELLS]
BASE_PX = cell_center(*PATH_CELLS[-1])

TOWERS = {
    "boog":  {"naam_nl": "Boogschutter", "naam_en": "Archer", "cost": 55, "color": GOED,
              "range": 138, "dmg": 9, "rate": 0.55, "kind": "arrow"},
    "magie": {"naam_nl": "Magier", "naam_en": "Mage", "cost": 95, "color": PURPLE,
              "range": 122, "dmg": 20, "rate": 1.15, "kind": "magic", "splash": 46},
    "vorst": {"naam_nl": "Vorsttoren", "naam_en": "Frost", "cost": 75, "color": ACCENT,
              "range": 118, "dmg": 5, "rate": 0.85, "kind": "frost", "slow": 0.45, "slow_t": 1.5},
}
TOWER_ORDER = ["boog", "magie", "vorst"]

ENEMIES = {
    "goblin": {"hp": 26, "speed": 72, "gold": 6, "r": 13, "color": GOED},
    "skelet": {"hp": 46, "speed": 58, "gold": 9, "r": 13, "color": (210, 210, 215)},
    "ork":    {"hp": 108, "speed": 44, "gold": 16, "r": 17, "color": WARN},
    "draak":  {"hp": 900, "speed": 40, "gold": 120, "r": 26, "color": RED},
}

LAST_WAVE = 8
START_GOLD = 220
START_LIVES = 20


def make_wave(w):
    """Lijst (kind, aantal, tussentijd) voor golf w."""
    if w >= LAST_WAVE:
        return [("ork", 6, 0.9), ("skelet", 8, 0.5), ("draak", 1, 0.0)]
    plan = []
    plan.append(("goblin", 6 + w * 2, max(0.35, 0.7 - w * 0.04)))
    if w >= 2:
        plan.append(("skelet", 2 + w, 0.6))
    if w >= 4:
        plan.append(("ork", w - 2, 1.0))
    return plan


def wave_hp_mult(w):
    return 1.0 + 0.13 * (w - 1)


# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveDefense-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveDefense-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "best_wave": 0,
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
    "onder": {"nl": "Een tower-defense van Dravenlock Games", "en": "A tower-defense by Dravenlock Games"},
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
    "goud": {"nl": "Goud", "en": "Gold"},
    "leven": {"nl": "Leven", "en": "Lives"},
    "golf": {"nl": "Golf", "en": "Wave"},
    "start_golf": {"nl": "Start golf", "en": "Start wave"},
    "bouw": {"nl": "Bouw", "en": "Build"},
    "upgrade": {"nl": "Upgrade", "en": "Upgrade"},
    "verplaats": {"nl": "Verplaats", "en": "Move"},
    "verplaats_hint": {"nl": "Klik een open veld om de toren te verplaatsen (Esc = stop)",
                       "en": "Click an open spot to move the tower (Esc = cancel)"},
    "verkoop": {"nl": "Verkoop", "en": "Sell"},
    "max": {"nl": "Max", "en": "Max"},
    "te_duur": {"nl": "Te weinig goud", "en": "Not enough gold"},
    "gewonnen": {"nl": "Kasteel behouden!", "en": "Castle held!"},
    "verloren": {"nl": "Kasteel gevallen", "en": "Castle fell"},
    "niveau": {"nl": "Niveau", "en": "Level"},
    "uitleg1": {"nl": "Klik op een open plek om een toren te bouwen.", "en": "Click an open spot to build a tower."},
    "uitleg2": {"nl": "Klik op een toren om te upgraden of verkopen.", "en": "Click a tower to upgrade or sell."},
    "uitleg3": {"nl": "Druk op 'Start golf' als je klaar bent.", "en": "Press 'Start wave' when ready."},
    "uitleg4": {"nl": "Verslagen vijanden geven goud.", "en": "Defeated enemies give gold."},
    "uitleg5": {"nl": "Laat niets je kasteel bereiken. Esc/P = pauze.", "en": "Let nothing reach your castle. Esc/P = pause."},
}


def t(key):
    e = TR.get(key, {})
    return e.get(_LANG, e.get("nl", key))


def tower_name(key):
    return TOWERS[key]["naam_nl"] if _LANG == "nl" else TOWERS[key]["naam_en"]


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


def draw_coin(surf, cx, cy, r):
    pygame.draw.circle(surf, GOLD, (int(cx), int(cy)), r)
    pygame.draw.circle(surf, mix(GOLD, (0, 0, 0), 0.3), (int(cx), int(cy)), r, 2)


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
    def __init__(self, label, rect, action, kind="normal", enabled=True, sub=None):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.action = action
        self.kind = kind
        self.enabled = enabled
        self.sub = sub

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, font, font_s=None, hot=False, focus=False):
        r = self.rect
        base = PANEL2
        if self.kind == "primary":
            base = mix(ACCENT, BG, 0.55)
        elif self.kind == "back":
            base = PANEL
        if not self.enabled:
            base = mix(PANEL, BG, 0.4)
        bg = mix(base, (255, 255, 255), 0.10) if (hot or focus) and self.enabled else base
        pygame.draw.rect(surf, bg, r, border_radius=10)
        edge = ACCENT if (hot or focus) and self.enabled else LINE
        pygame.draw.rect(surf, edge, r, width=3 if (hot or focus) else 2, border_radius=10)
        col = TEXT if self.enabled else MUTED
        if (hot or focus) and self.enabled:
            col = (245, 245, 248)
        if self.kind == "donate":
            draw_heart(surf, r.left + 26, r.centery, 11, WARN if not (hot or focus) else (235, 120, 110))
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(midleft=(r.left + 46, r.centery)))
        elif self.sub and font_s:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=(r.centerx, r.centery - 10)))
            img2 = font_s.render(self.sub, True, GOLD if self.enabled else MUTED)
            surf.blit(img2, img2.get_rect(center=(r.centerx, r.centery + 14)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


# ----------------------------------------------------------------------------
class Enemy:
    def __init__(self, kind, hp_mult=1.0):
        d = ENEMIES[kind]
        self.kind = kind
        self.max_hp = d["hp"] * hp_mult
        self.hp = self.max_hp
        self.speed = d["speed"]
        self.gold = d["gold"]
        self.r = d["r"]
        self.color = d["color"]
        self.wp = 0
        self.x, self.y = WAYPOINTS[0]
        self.alive = True
        self.reached = False
        self.slow_t = 0.0
        self.slow_f = 0.0
        self.hurt_t = 0.0

    def cur_speed(self):
        return self.speed * (1.0 - self.slow_f) if self.slow_t > 0 else self.speed

    def update(self, dt):
        self.slow_t = max(0.0, self.slow_t - dt)
        if self.slow_t <= 0:
            self.slow_f = 0.0
        self.hurt_t = max(0.0, self.hurt_t - dt)
        if self.wp + 1 >= len(WAYPOINTS):
            self.reached = True
            self.alive = False
            return
        tx, ty = WAYPOINTS[self.wp + 1]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = self.cur_speed() * dt
        if dist <= step:
            self.x, self.y = tx, ty
            self.wp += 1
        else:
            self.x += dx / dist * step
            self.y += dy / dist * step

    def progress(self):
        # hoe ver langs het pad (voor targeting "eerste")
        return self.wp + (0.0 if self.wp + 1 >= len(WAYPOINTS) else
                          math.hypot(self.x - WAYPOINTS[self.wp][0], self.y - WAYPOINTS[self.wp][1]) / TILE)

    def hit(self, dmg):
        self.hp -= dmg
        self.hurt_t = 0.08
        if self.hp <= 0:
            self.alive = False

    def apply_slow(self, f, t):
        if f >= self.slow_f or self.slow_t <= 0:
            self.slow_f = f
        self.slow_t = max(self.slow_t, t)


class Tower:
    def __init__(self, cell, kind):
        self.cell = cell
        self.kind = kind
        self.level = 1
        self.cd = 0.0
        self.x, self.y = cell_center(*cell)
        self.invested = TOWERS[kind]["cost"]
        self.angle = -math.pi / 2

    def stat(self, name):
        base = TOWERS[self.kind][name]
        if name in ("dmg", "range"):
            return base * (1.0 + 0.45 * (self.level - 1))
        if name == "rate":
            return base * (1.0 - 0.18 * (self.level - 1))
        return base

    def upgrade_cost(self):
        return int(TOWERS[self.kind]["cost"] * (0.8 + 0.5 * self.level))

    def sell_value(self):
        return int(self.invested * 0.6)


class Projectile:
    def __init__(self, x, y, target, dmg, kind, splash=0, slow=0.0, slow_t=0.0):
        self.x = x
        self.y = y
        self.target = target
        self.dmg = dmg
        self.kind = kind
        self.splash = splash
        self.slow = slow
        self.slow_t = slow_t
        self.alive = True
        self.speed = 520 if kind == "arrow" else 380

    def update(self, dt, enemies):
        if not self.target or not self.target.alive:
            self.alive = False
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step + self.target.r:
            self._impact(enemies)
            self.alive = False
        else:
            self.x += dx / dist * step
            self.y += dy / dist * step

    def _impact(self, enemies):
        if self.splash > 0:
            for e in enemies:
                if e.alive and math.hypot(e.x - self.target.x, e.y - self.target.y) <= self.splash:
                    e.hit(self.dmg)
        else:
            self.target.hit(self.dmg)
        if self.slow > 0:
            tgts = [self.target]
            if self.splash > 0:
                tgts = [e for e in enemies if e.alive and
                        math.hypot(e.x - self.target.x, e.y - self.target.y) <= self.splash]
            for e in tgts:
                e.apply_slow(self.slow, self.slow_t)


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app):
        self.app = app
        self.gold = START_GOLD
        self.lives = START_LIVES
        self.wave = 0
        self.enemies = []
        self.towers = {}        # cell -> Tower
        self.projectiles = []
        self.spawn_queue = []   # (kind, time)
        self.spawn_t = 0.0
        self.wave_active = False
        self.finished = False
        self.result = None
        self.hurt_flash = 0.0
        self.msg = ""
        self.msg_t = 0.0

    def buildable(self, cell):
        c, r = cell
        return (0 <= c < COLS and 0 <= r < ROWS and cell not in PATH_SET and cell not in self.towers)

    def cell_at(self, px, py):
        if py < FIELD_Y:
            return None
        c = px // TILE
        r = (py - FIELD_Y) // TILE
        if 0 <= c < COLS and 0 <= r < ROWS:
            return (int(c), int(r))
        return None

    def can_start_wave(self):
        return not self.wave_active and self.wave < LAST_WAVE and not self.finished

    def start_wave(self):
        if not self.can_start_wave():
            return
        self.wave += 1
        plan = make_wave(self.wave)
        tlist = []
        tt = 0.0
        for (kind, count, gap) in plan:
            for i in range(count):
                tlist.append((kind, tt))
                tt += gap
            tt += 0.6
        self.spawn_queue = tlist
        self.spawn_t = 0.0
        self.wave_active = True
        if self.app.sfx:
            self.app.sfx.play("wave")

    def build(self, cell, kind):
        cost = TOWERS[kind]["cost"]
        if not self.buildable(cell):
            return False
        if self.gold < cost:
            self._flash_msg(t("te_duur"))
            if self.app.sfx:
                self.app.sfx.play("error")
            return False
        self.gold -= cost
        self.towers[cell] = Tower(cell, kind)
        if self.app.sfx:
            self.app.sfx.play("build")
        return True

    def upgrade(self, cell):
        tw = self.towers.get(cell)
        if not tw or tw.level >= 3:
            return False
        cost = tw.upgrade_cost()
        if self.gold < cost:
            self._flash_msg(t("te_duur"))
            if self.app.sfx:
                self.app.sfx.play("error")
            return False
        self.gold -= cost
        tw.invested += cost
        tw.level += 1
        if self.app.sfx:
            self.app.sfx.play("upgrade")
        return True

    def sell(self, cell):
        tw = self.towers.get(cell)
        if not tw:
            return False
        self.gold += tw.sell_value()
        del self.towers[cell]
        if self.app.sfx:
            self.app.sfx.play("coin")
        return True

    def move_tower(self, old_cell, new_cell):
        tw = self.towers.get(old_cell)
        if not tw or not self.buildable(new_cell):
            return False
        del self.towers[old_cell]
        tw.cell = new_cell
        tw.x, tw.y = cell_center(*new_cell)
        tw.cd = max(tw.cd, 0.2)
        self.towers[new_cell] = tw
        if self.app.sfx:
            self.app.sfx.play("build")
        return True

    def _flash_msg(self, m):
        self.msg = m
        self.msg_t = 1.4

    def update(self, dt):
        if self.finished:
            return
        self.hurt_flash = max(0.0, self.hurt_flash - dt)
        self.msg_t = max(0.0, self.msg_t - dt)
        # spawnen
        if self.wave_active:
            self.spawn_t += dt
            due = [s for s in self.spawn_queue if s[1] <= self.spawn_t]
            if due:
                hm = wave_hp_mult(self.wave)
                for (kind, _) in due:
                    self.enemies.append(Enemy(kind, hm))
                self.spawn_queue = [s for s in self.spawn_queue if s[1] > self.spawn_t]
        # vijanden
        for e in self.enemies:
            e.update(dt)
            if e.reached:
                self.lives -= 1
                self.hurt_flash = 0.45
                if self.app.sfx:
                    self.app.sfx.play("leak")
        self.enemies = [e for e in self.enemies if e.alive]
        # torens schieten
        for tw in self.towers.values():
            tw.cd = max(0.0, tw.cd - dt)
            rng = tw.stat("range")
            target = None
            best = -1
            for e in self.enemies:
                if not e.alive:
                    continue
                if math.hypot(e.x - tw.x, e.y - tw.y) <= rng:
                    p = e.progress()
                    if p > best:
                        best = p
                        target = e
            if target:
                tw.angle = math.atan2(target.y - tw.y, target.x - tw.x)
                if tw.cd <= 0:
                    tw.cd = tw.stat("rate")
                    self._fire(tw, target)
        # projectielen
        for p in self.projectiles:
            p.update(dt, self.enemies)
        self.projectiles = [p for p in self.projectiles if p.alive]
        # dode vijanden -> goud
        dead_gold = 0
        survivors = []
        for e in self.enemies:
            if not e.alive and not e.reached:
                dead_gold += e.gold
            else:
                survivors.append(e)
        # (enemies al gefilterd hierboven; dit pad vangt sterfte deze frame)
        # einde golf
        if self.wave_active and not self.spawn_queue and not self.enemies:
            self.wave_active = False
            self.gold += 20 + self.wave * 5
            if self.wave >= LAST_WAVE:
                self._win()
        if self.lives <= 0 and not self.finished:
            self._lose()

    def _fire(self, tw, target):
        info = TOWERS[tw.kind]
        dmg = tw.stat("dmg")
        if tw.kind == "boog":
            self.projectiles.append(Projectile(tw.x, tw.y, target, dmg, "arrow"))
            if self.app.sfx:
                self.app.sfx.play("shoot")
        elif tw.kind == "magie":
            self.projectiles.append(Projectile(tw.x, tw.y, target, dmg, "magic", splash=info["splash"]))
            if self.app.sfx:
                self.app.sfx.play("magic")
        else:  # vorst
            self.projectiles.append(Projectile(tw.x, tw.y, target, dmg, "frost",
                                               slow=info["slow"], slow_t=info["slow_t"]))
            if self.app.sfx:
                self.app.sfx.play("frost")

    def _win(self):
        if self.finished:
            return
        self.finished = True
        self.result = "win"
        if self.wave > self.app.cfg.get("best_wave", 0):
            self.app.cfg["best_wave"] = self.wave
            save_config(self.app.cfg)
        if self.app.sfx:
            self.app.sfx.play("victory")

    def _lose(self):
        if self.finished:
            return
        self.finished = True
        self.result = "lose"
        if self.wave - 1 > self.app.cfg.get("best_wave", 0):
            self.app.cfg["best_wave"] = max(0, self.wave - 1)
            save_config(self.app.cfg)
        if self.app.sfx:
            self.app.sfx.play("defeat")

    # ---------- tekenen ----------
    def draw(self, surf, sel_cell=None, hover_cell=None):
        # grasveld (schaakbord)
        for r in range(ROWS):
            for c in range(COLS):
                col = GRASS if (c + r) % 2 == 0 else GRASS2
                pygame.draw.rect(surf, col, (c * TILE, FIELD_Y + r * TILE, TILE, TILE))
        # pad
        for (c, r) in PATH_CELLS:
            x, y = c * TILE, FIELD_Y + r * TILE
            pygame.draw.rect(surf, PATH_COL, (x, y, TILE, TILE))
        for (c, r) in PATH_CELLS:
            x, y = c * TILE, FIELD_Y + r * TILE
            pygame.draw.rect(surf, PATH_EDGE, (x, y, TILE, TILE), 1)
        # kasteel aan het eind
        bx, by = BASE_PX
        pygame.draw.rect(surf, mix(ACCENT, BG, 0.3), (bx - 22, by - 22, 44, 44), border_radius=4)
        for dx in (-22, -6, 10):
            pygame.draw.rect(surf, mix(ACCENT, BG, 0.1), (bx + dx, by - 30, 12, 12))
        pygame.draw.rect(surf, GOLD, (bx - 6, by - 4, 12, 18))

        # markeer buildable hover / selectie
        if hover_cell and self.buildable(hover_cell):
            hx, hy = hover_cell[0] * TILE, FIELD_Y + hover_cell[1] * TILE
            pygame.draw.rect(surf, mix(GOED, BG, 0.4), (hx, hy, TILE, TILE), 3)
        if sel_cell:
            sx, sy = sel_cell[0] * TILE, FIELD_Y + sel_cell[1] * TILE
            pygame.draw.rect(surf, ACCENT, (sx, sy, TILE, TILE), 3)
            tw = self.towers.get(sel_cell)
            rng = tw.stat("range") if tw else TOWERS[self.app.sel_build]["range"] if self.app.sel_build else 0
            if rng:
                cx, cy = cell_center(*sel_cell)
                ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(ring, (111, 163, 214, 40), (cx, cy), int(rng))
                pygame.draw.circle(ring, (111, 163, 214, 120), (cx, cy), int(rng), 2)
                surf.blit(ring, (0, 0))

        # torens
        for tw in self.towers.values():
            self._draw_tower(surf, tw)
        # vijanden
        for e in self.enemies:
            self._draw_enemy(surf, e)
        # projectielen
        for p in self.projectiles:
            self._draw_proj(surf, p)
        # rode flits bij verlies van leven
        if self.hurt_flash > 0:
            f = self.hurt_flash / 0.45
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for k in range(int(40 * f)):
                al = int(110 * f * (1 - k / max(1, int(40 * f))))
                pygame.draw.rect(ov, (200, 40, 40, al), (k, k, WIDTH - 2 * k, HEIGHT - 2 * k), 1)
            surf.blit(ov, (0, 0))

    def _draw_tower(self, surf, tw):
        x, y = int(tw.x), int(tw.y)
        col = TOWERS[tw.kind]["color"]
        pygame.draw.rect(surf, mix(col, BG, 0.4), (x - 20, y - 20, 40, 40), border_radius=6)
        pygame.draw.rect(surf, col, (x - 20, y - 20, 40, 40), 2, border_radius=6)
        # loop richting doel
        ux, uy = math.cos(tw.angle), math.sin(tw.angle)
        pygame.draw.line(surf, mix(col, (255, 255, 255), 0.3), (x, y), (x + ux * 18, y + uy * 18), 5)
        pygame.draw.circle(surf, col, (x, y), 9)
        # niveau-pips
        for i in range(tw.level):
            pygame.draw.circle(surf, GOLD, (x - 14 + i * 9, y + 14), 3)

    def _draw_enemy(self, surf, e):
        x, y = int(e.x), int(e.y)
        col = e.color if e.hurt_t <= 0 else (255, 255, 255)
        if e.kind == "draak":
            pygame.draw.ellipse(surf, mix(col, BG, 0.05), (x - 26, y - 16, 52, 32))
            pygame.draw.polygon(surf, mix(col, BG, 0.25), [(x - 16, y - 12), (x - 36, y - 30), (x - 8, y - 6)])
            pygame.draw.polygon(surf, mix(col, BG, 0.25), [(x + 16, y - 12), (x + 36, y - 30), (x + 8, y - 6)])
            pygame.draw.circle(surf, GOLD, (x + 18, y - 4), 3)
        else:
            pygame.draw.circle(surf, col, (x, y), e.r)
            pygame.draw.circle(surf, mix(col, (0, 0, 0), 0.3), (x, y), e.r, 2)
            if e.kind == "ork":
                pygame.draw.circle(surf, RED, (x - 4, y - 3), 2)
                pygame.draw.circle(surf, RED, (x + 4, y - 3), 2)
        if e.slow_t > 0:
            pygame.draw.circle(surf, (140, 200, 240), (x, y), e.r + 3, 1)
        # hp-balk
        w = e.r * 2
        pygame.draw.rect(surf, (0, 0, 0), (x - w // 2, y - e.r - 9, w, 5))
        pygame.draw.rect(surf, GOED, (x - w // 2, y - e.r - 9, int(w * clamp(e.hp / e.max_hp, 0, 1)), 5))

    def _draw_proj(self, surf, p):
        x, y = int(p.x), int(p.y)
        if p.kind == "arrow":
            pygame.draw.circle(surf, GOLD, (x, y), 4)
        elif p.kind == "magic":
            pygame.draw.circle(surf, PURPLE, (x, y), 7)
            pygame.draw.circle(surf, (210, 180, 240), (x, y), 7, 1)
        else:
            pygame.draw.circle(surf, ACCENT, (x, y), 5)
            pygame.draw.circle(surf, (200, 230, 250), (x, y), 5, 1)


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
    f_title = pygame.font.Font(None, 76)
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
        self.sel_cell = None        # geselecteerde cel (toren of bouwmenu)
        self.menu = None            # None | "build" | "tower"
        self.sel_build = None       # voor range-preview tijdens bouwmenu
        self.moving = None          # cel van de toren die verplaatst wordt

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
        if self.state in ("title", "settings", "help", "gameover", "victory"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            if self.game and self.game.wave >= LAST_WAVE and self.game.wave_active:
                self.sfx.start_music("boss")
            else:
                self.sfx.start_music("play")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        if s != "play":
            self.menu = None
            self.sel_cell = None
            self.sel_build = None
            self.moving = None
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

    # ---------- acties ----------
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
        elif a == "start_wave":
            if self.game:
                self.game.start_wave()
                self.music_for_state()
        elif a and a.startswith("build_"):
            kind = a.split("_", 1)[1]
            if self.game and self.sel_cell:
                if self.game.build(self.sel_cell, kind):
                    self.menu = None
                    self.sel_cell = None
                    self.sel_build = None
        elif a == "upgrade":
            if self.game and self.sel_cell:
                self.game.upgrade(self.sel_cell)
        elif a == "move_start":
            if self.game and self.sel_cell in self.game.towers:
                self.moving = self.sel_cell
                self.menu = None
                self.sel_cell = None
                self.sel_build = None
        elif a == "sell":
            if self.game and self.sel_cell:
                self.game.sell(self.sel_cell)
                self.menu = None
                self.sel_cell = None
        elif a == "close_menu":
            self.menu = None
            self.sel_cell = None
            self.sel_build = None
            self.moving = None
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

    def on_key(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                if self.moving:
                    self.moving = None
                elif self.menu:
                    self._action("close_menu")
                else:
                    self._action("pause")
            elif key == pygame.K_SPACE:
                self._action("start_wave")
            return
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
        # eerst knoppen (HUD/menu/overlay)
        for b in self.buttons:
            if b.hit(pos) and b.enabled:
                self._action(b.action)
                return
        if self.state == "play" and not self.game.finished:
            cell = self.game.cell_at(*pos)
            # verplaats-modus: volgende klik plaatst de toren
            if self.moving is not None:
                if cell is not None and self.game.buildable(cell):
                    self.game.move_tower(self.moving, cell)
                    self.moving = None
                elif cell == self.moving:
                    self.moving = None  # zelfde plek -> annuleer
                else:
                    self.moving = None  # ongeldige plek -> annuleer
                return
            if cell is None:
                self._action("close_menu")
                return
            if cell in self.game.towers:
                self.sel_cell = cell
                self.menu = "tower"
                self.sel_build = None
                if self.sfx:
                    self.sfx.play("select")
            elif self.game.buildable(cell):
                self.sel_cell = cell
                self.menu = "build"
                self.sel_build = "boog"
                if self.sfx:
                    self.sfx.play("select")
            else:
                self._action("close_menu")

    # ---------- spel ----------
    def start_game(self):
        self.game = Game(self)
        self.sel_cell = None
        self.menu = None
        self.sel_build = None
        self.moving = None
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            self.game.update(dt)
            if self.game.finished and self.t_state > 0.6:
                self.set_state("victory" if self.game.result == "win" else "gameover")

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
            hover = self.game.cell_at(*self.mouse) if st == "play" else None
            self.game.draw(s, sel_cell=self.sel_cell, hover_cell=hover)
            self._draw_hud(s)
            if st == "play" and self.moving is not None:
                self._draw_move_overlay(s, hover)
            if self.menu == "build":
                self._draw_build_menu(s)
            elif self.menu == "tower":
                self._draw_tower_menu(s)
            if st == "pause":
                self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "gameover":
            self.game.draw(s)
            self._overlay(s, t("verloren"),
                          ["%s %d" % (t("golf"), max(0, self.game.wave - 1))],
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

    def _add_button(self, label, rect, action, kind="normal", enabled=True, sub=None):
        self.buttons.append(Button(label, rect, action, kind=kind, enabled=enabled, sub=sub))

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
            b.draw(s, self.font_m, self.font_s, hot=b.hit(self.mouse), focus=(i == self.focus and self.state not in ("play", "pause")))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=210, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "%s %d / %d" % (t("golf"), self.cfg.get("best_wave", 0), LAST_WAVE),
                   self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 54)
        y = 120
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_s, TEXT, WIDTH // 2, y)
            y += 40
        # torenoverzicht
        y += 6
        for key in TOWER_ORDER:
            info = TOWERS[key]
            line = "%s - %d goud" % (tower_name(key), info["cost"])
            self._text(s, line, self.font_s, info["color"], WIDTH // 2, y)
            y += 34
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 70, 220, 54), "back_title", kind="back")
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
        draw_coin(s, 30, 30, 12)
        self._text(s, "%d" % g.gold, self.font_m, GOLD, 50, 30, center=False)
        draw_heart(s, 180, 30, 12, RED if g.lives <= 5 else WARN)
        self._text(s, "%d" % g.lives, self.font_m, TEXT if g.lives > 5 else RED, 200, 30, center=False)
        self._text(s, "%s %d / %d" % (t("golf"), g.wave, LAST_WAVE), self.font_m, ACCENT, 320, 30, center=False)
        # start golf knop
        if g.can_start_wave():
            self._add_button(t("start_golf"), (WIDTH // 2 - 10, 18, 190, 46), "start_wave", kind="primary")
        elif g.wave_active:
            self._text(s, "...", self.font_m, MUTED, WIDTH // 2 + 70, 30)
        self._add_button(t("pauze"), (WIDTH - 130, 18, 110, 46), "pause", kind="back")
        # foutmelding
        if g.msg_t > 0:
            img = self.font_s.render(g.msg, True, WARN)
            s.blit(img, img.get_rect(center=(WIDTH // 2 + 80, HUD_H + 18)))

    def _draw_build_menu(self, s):
        # paneel onder de geselecteerde cel
        cx, cy = cell_center(*self.sel_cell)
        pw, ph = 250, 170
        px = clamp(cx - pw // 2, 8, WIDTH - pw - 8)
        py = clamp(cy + 34, HUD_H + 8, HEIGHT - ph - 8)
        pygame.draw.rect(s, PANEL, (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(s, ACCENT, (px, py, pw, ph), 2, border_radius=10)
        self._text(s, t("bouw"), self.font_s, MUTED, px + pw // 2, py + 16)
        yy = py + 34
        for key in TOWER_ORDER:
            info = TOWERS[key]
            can = self.game.gold >= info["cost"]
            self._add_button(tower_name(key), (px + 12, yy, pw - 24, 38), "build_" + key,
                             enabled=can, sub="%d %s" % (info["cost"], t("goud").lower()))
            yy += 44
        # hover -> range preview
        for b in self.buttons:
            if b.action and b.action.startswith("build_") and b.hit(self.mouse):
                self.sel_build = b.action.split("_", 1)[1]

    def _draw_tower_menu(self, s):
        tw = self.game.towers.get(self.sel_cell)
        if not tw:
            self.menu = None
            return
        cx, cy = cell_center(*self.sel_cell)
        pw, ph = 250, 196
        px = clamp(cx - pw // 2, 8, WIDTH - pw - 8)
        py = clamp(cy + 34, HUD_H + 8, HEIGHT - ph - 8)
        pygame.draw.rect(s, PANEL, (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(s, ACCENT, (px, py, pw, ph), 2, border_radius=10)
        self._text(s, "%s  %s %d" % (tower_name(tw.kind), t("niveau"), tw.level),
                   self.font_s, TOWERS[tw.kind]["color"], px + pw // 2, py + 16)
        if tw.level >= 3:
            self._add_button(t("max"), (px + 12, py + 34, pw - 24, 38), None, enabled=False)
        else:
            can = self.game.gold >= tw.upgrade_cost()
            self._add_button(t("upgrade"), (px + 12, py + 34, pw - 24, 38), "upgrade",
                             enabled=can, sub="%d %s" % (tw.upgrade_cost(), t("goud").lower()))
        self._add_button(t("verplaats"), (px + 12, py + 80, pw - 24, 38), "move_start")
        self._add_button("%s (+%d)" % (t("verkoop"), tw.sell_value()),
                         (px + 12, py + 126, pw - 24, 38), "sell", kind="back")

    def _draw_move_overlay(self, s, hover):
        tw = self.game.towers.get(self.moving)
        if not tw:
            self.moving = None
            return
        # gemarkeerde toren die je verplaatst
        mx, my = self.moving[0] * TILE, FIELD_Y + self.moving[1] * TILE
        pulse = 2 + int(abs(math.sin(self.t_state * 5)) * 2)
        pygame.draw.rect(s, GOLD, (mx, my, TILE, TILE), pulse)
        # doelcel onder de cursor
        if hover is not None:
            hx, hy = hover[0] * TILE, FIELD_Y + hover[1] * TILE
            ok = self.game.buildable(hover) or hover == self.moving
            col = GOED if ok else RED
            pygame.draw.rect(s, col, (hx, hy, TILE, TILE), 3)
            if ok:
                cx, cy = cell_center(*hover)
                ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                rng = int(tw.stat("range"))
                pygame.draw.circle(ring, (111, 163, 214, 40), (cx, cy), rng)
                pygame.draw.circle(ring, (111, 163, 214, 120), (cx, cy), rng, 2)
                s.blit(ring, (0, 0))
        # hint-balk
        hint = t("verplaats_hint")
        img = self.font_s.render(hint, True, TEXT)
        bg = pygame.Surface((img.get_width() + 30, img.get_height() + 14), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 175))
        s.blit(bg, bg.get_rect(center=(WIDTH // 2, HEIGHT - 26)))
        s.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT - 26)))

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 160)
        y = 250
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
        self._text(s, "%s %d / %d" % (t("golf"), LAST_WAVE, LAST_WAVE), self.font_m, TEXT, WIDTH // 2, 300)
        self._stack([(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                    top=360, w=360, h=64, gap=18, kinds=["primary", "normal"])


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

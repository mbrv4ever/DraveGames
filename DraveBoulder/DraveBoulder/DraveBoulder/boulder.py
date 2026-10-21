# -*- coding: utf-8 -*-
"""boulder.py - DraveBoulder, een Boulder Dash van Dravenlock Games.

Rockford graaft door de aarde, verzamelt diamanten en ontwijkt vallende rotsen.
Een rots of diamant valt zodra de grond eronder weg is en rolt van ronde dingen
af. Verzamel genoeg diamanten en de uitgang opent; bereik hem voor de tijd om is.
Pas op voor vuurvliegjes en vlinders (dodelijk bij aanraking) - laat er een rots
op vallen: vlinders veranderen dan in diamanten. Een amoebe groeit; sluit hem in
met rotsen en hij wordt diamant. De toverwand verandert vallende rotsen in
diamanten.

16 grotten (A-P), elk in 5 moeilijkheidsgraden = 80 levels. NL-basis met
OS-taaldetectie en Engels; donker Dravenlock-palet, grote en contrastrijke HUD;
procedurele muziek en geluiden (sfx.py); gesproken intro (neuvoice) in een apart
splashvenster. Volledig draagbaar: alles in een map "DraveBoulder-data" naast het
programma.
"""
from __future__ import annotations

import json
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

APP_NAME = "DraveBoulder"
APP_VERSION = "0.1.2"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 46
TILE = 40
TICK = 0.11            # speltick (zwaartekracht/vijanden)
VIEW_C = WIDTH // TILE          # zichtbare kolommen
VIEW_R = (HEIGHT - HUD_H) // TILE

# grot-afmeting (incl. stalen rand)
CW, CH = 40, 22

# celtypes
EMPTY, DIRT, STEEL, ROCK, DIAMOND, EXIT, AMOEBA, MAGIC, LAVA, SLIME, GROWWALL = range(11)
SLIME_PERM = 0.18      # kans per tick dat iets door slijm zakt

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
DIRT_COL = (78, 56, 38)
DIRT_COL2 = (66, 47, 32)
STEEL_COL = (96, 100, 110)
ROCK_COL = (150, 150, 158)

DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]


# 16 grotten: thema-parameters (vaste seed -> vaste opzet). need/time = basis (diff 1).
CAVES = [
    # letter, seed, rocks, diamonds, fireflies, butterflies, amoeba, magic, need, time, dval, lava_w, slime, grow
    ("A", 101, 24, 30, 0, 0, False, False, 10, 150, 10, 0, False, False),
    ("B", 102, 44, 32, 0, 0, False, False, 12, 150, 10, 0, False, False),
    ("C", 103, 40, 34, 2, 0, False, False, 14, 150, 10, 0, False, False),
    ("D", 104, 38, 20, 0, 4, False, False, 14, 150, 12, 0, False, False),
    ("E", 105, 50, 34, 4, 0, False, False, 14, 140, 10, 5, False, False),
    ("F", 106, 60, 40, 0, 0, False, False, 18, 140, 12, 7, False, False),
    ("G", 107, 28, 30, 0, 0, True, False, 12, 160, 12, 0, False, False),
    ("H", 108, 44, 22, 0, 3, False, True, 14, 150, 14, 0, False, False),
    ("I", 109, 54, 34, 4, 2, False, False, 18, 140, 12, 0, True, False),
    ("J", 110, 62, 34, 6, 0, False, False, 16, 130, 10, 7, False, False),
    ("K", 111, 46, 26, 2, 4, False, False, 18, 140, 14, 0, False, True),
    ("L", 112, 40, 30, 0, 0, True, True, 14, 150, 14, 0, False, False),
    ("M", 113, 66, 40, 4, 2, False, False, 22, 130, 12, 9, False, False),
    ("N", 114, 56, 30, 6, 4, False, False, 20, 130, 12, 0, True, True),
    ("O", 115, 50, 28, 2, 4, True, False, 18, 140, 14, 0, False, True),
    ("P", 116, 62, 34, 4, 4, False, True, 22, 130, 14, 9, False, False),
]
N_CAVES = len(CAVES)
N_DIFF = 5
AMOEBA_MAX = 180


def cave_need(idx, diff):
    c = CAVES[idx]
    return c[8] + (diff - 1) * 2


def cave_time(idx, diff):
    c = CAVES[idx]
    return max(80, c[9] - (diff - 1) * 10)


# ----------------------------------------------------------------------------
def config_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveBoulder-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveBoulder-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "highscore": 0, "max_cave": 0,
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
    "kies_grot": {"nl": "Kies grot en niveau", "en": "Choose cave and level"},
    "grot": {"nl": "Grot", "en": "Cave"},
    "niveau": {"nl": "Niveau", "en": "Level"},
    "start": {"nl": "Start", "en": "Start"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "tijd": {"nl": "Tijd", "en": "Time"},
    "leven": {"nl": "Levens", "en": "Lives"},
    "nodig": {"nl": "Nodig", "en": "Need"},
    "grot_klaar": {"nl": "Grot gehaald!", "en": "Cave cleared!"},
    "gameover": {"nl": "Game over", "en": "Game over"},
    "gewonnen": {"nl": "Alle grotten gehaald!", "en": "All caves cleared!"},
    "volgende": {"nl": "Volgende grot", "en": "Next cave"},
    "uitleg1": {"nl": "Pijltjes: graven en lopen door de aarde.", "en": "Arrows: dig and walk through the earth."},
    "uitleg2": {"nl": "Verzamel genoeg diamanten; dan opent de uitgang.", "en": "Collect enough diamonds; the exit opens."},
    "uitleg3": {"nl": "Rotsen vallen als de grond eronder weg is. Pas op!", "en": "Rocks fall when the earth below is gone. Watch out!"},
    "uitleg4": {"nl": "Duw rotsen opzij; laat ze op vlinders vallen voor diamanten.", "en": "Push rocks; drop them on butterflies for diamonds."},
    "uitleg5": {"nl": "Houd Shift in om te graven zonder te lopen. Esc/P = pauze.", "en": "Hold Shift to dig without moving. Esc/P = pause."},
    "uitleg6": {"nl": "Pas op: lava is dodelijk; slijm laat rotsen erdoor; muren groeien.", "en": "Beware: lava is deadly; slime drips rocks through; walls grow."},
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
def generate_cave(idx):
    """Bouw een vaste, herhaalbare grot uit de thema-parameters."""
    (letter, seed, n_rock, n_dia, n_fire, n_butt, has_amoeba, has_magic,
     need, tlim, dval, lava_w, has_slime, has_grow) = CAVES[idx]
    rng = random.Random(seed)
    grid = [[DIRT] * CW for _ in range(CH)]
    # stalen rand
    for x in range(CW):
        grid[0][x] = STEEL
        grid[CH - 1][x] = STEEL
    for y in range(CH):
        grid[y][0] = STEEL
        grid[y][CW - 1] = STEEL
    # speler-start (linksboven), maak een klein veilig vak vrij
    psx, psy = 2, 2
    for dy in range(0, 2):
        for dx in range(0, 3):
            if 1 <= psx + dx < CW - 1 and 1 <= psy + dy < CH - 1:
                grid[psy + dy][psx + dx] = EMPTY

    def free_interior():
        return (rng.randint(2, CW - 3), rng.randint(2, CH - 3))

    # lava-poel (onderin, weg van de start) - met een leeg vakje erboven
    if lava_w > 0:
        lx = rng.randint(8, CW - 6 - lava_w)
        ly = rng.randint(CH - 6, CH - 3)
        for x in range(lx, min(CW - 1, lx + lava_w)):
            grid[ly][x] = LAVA
            if grid[ly - 1][x] == DIRT:
                grid[ly - 1][x] = EMPTY
    # slijmlijn (horizontaal, midden-onder, met ruimte eronder)
    if has_slime:
        sy = rng.randint(CH // 2, CH - 5)
        for x in range(5, CW - 5):
            grid[sy][x] = SLIME
            if grid[sy + 1][x] == DIRT:
                grid[sy + 1][x] = EMPTY
    # groeiende-muur-kiemen (een paar losse cellen die uitgroeien)
    if has_grow:
        for _ in range(2):
            gx, gy = rng.randint(6, CW - 7), rng.randint(5, CH - 6)
            if abs(gx - psx) + abs(gy - psy) > 6:
                grid[gy][gx] = GROWWALL
                if grid[gy][gx - 1] == DIRT:
                    grid[gy][gx - 1] = EMPTY
                if grid[gy][gx + 1] == DIRT:
                    grid[gy][gx + 1] = EMPTY

    # diamanten in de aarde
    placed = 0
    tries = 0
    while placed < n_dia and tries < n_dia * 40:
        tries += 1
        x, y = free_interior()
        if abs(x - psx) + abs(y - psy) < 3:
            continue
        if grid[y][x] == DIRT:
            grid[y][x] = DIAMOND
            placed += 1
    # rotsen
    placed = 0
    tries = 0
    while placed < n_rock and tries < n_rock * 40:
        tries += 1
        x, y = free_interior()
        if abs(x - psx) + abs(y - psy) < 3:
            continue
        if grid[y][x] in (DIRT, EMPTY):
            grid[y][x] = ROCK
            placed += 1
    # amoebe-kiem
    amoeba = set()
    if has_amoeba:
        ax, ay = rng.randint(6, CW - 7), rng.randint(6, CH - 7)
        grid[ay][ax] = AMOEBA
        amoeba.add((ax, ay))
    # toverwand (horizontale lijn ergens in het midden-onder)
    if has_magic:
        my = rng.randint(CH // 2, CH - 5)
        for x in range(4, CW - 4):
            grid[my][x] = MAGIC
        # ruimte eronder vrijmaken zodat transmutatie zichtbaar is
        for x in range(4, CW - 4):
            if grid[my + 1][x] == DIRT:
                grid[my + 1][x] = EMPTY

    # vijanden in een vrij 3x3-vakje
    enemies = {}

    def place_enemy(kind):
        for _ in range(120):
            x, y = rng.randint(3, CW - 4), rng.randint(3, CH - 4)
            if abs(x - psx) + abs(y - psy) < 6:
                continue
            ok = all(grid[y + dy][x + dx] in (DIRT, EMPTY)
                     for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            if ok:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        grid[y + dy][x + dx] = EMPTY
                enemies[(x, y)] = [kind, 2]   # kind 'f'/'b', richting omlaag
                return
    for _ in range(n_fire):
        place_enemy("f")
    for _ in range(n_butt):
        place_enemy("b")

    # uitgang rechtsonder in de stalen rand
    ex, ey = CW - 2, CH - 2
    grid[ey][ex] = EXIT
    growwall = set((x, y) for y in range(CH) for x in range(CW) if grid[y][x] == GROWWALL)

    # tel beschikbare diamanten (incl. potentieel uit vlinders: 9 elk)
    avail = sum(row.count(DIAMOND) for row in grid) + n_butt * 9
    need = min(need, max(1, avail - 2))
    return {
        "grid": grid, "px": psx, "py": psy, "enemies": enemies, "amoeba": amoeba,
        "growwall": growwall, "exit": (ex, ey), "need": need, "time": tlim,
        "dval": dval, "letter": letter,
    }


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
class Game:
    def __init__(self, app, cave_idx, diff):
        self.app = app
        self.cave_idx = cave_idx
        self.diff = diff
        self.score = app.run_score
        self.lives = app.run_lives
        self.finished = False
        self.result = None         # "clear" | "dead" | "win"
        self.load_cave()

    def load_cave(self):
        c = generate_cave(self.cave_idx)
        self.grid = c["grid"]
        self.px, self.py = c["px"], c["py"]
        self.enemies = dict(c["enemies"])
        self.amoeba = set(c["amoeba"])
        self.growwall = set(c.get("growwall", set()))
        self.exit = c["exit"]
        self.need = cave_need(self.cave_idx, self.diff)
        self.need = min(self.need, max(1, sum(r.count(DIAMOND) for r in self.grid) + len([1 for e in self.enemies.values() if e[0] == "b"]) * 9 - 1))
        self.dval = c["dval"]
        self.time_left = float(cave_time(self.cave_idx, self.diff))
        self.collected = 0
        self.exit_open = False
        self.falling = set()
        self.move_dir = None       # (dx,dy)
        self.facing = 1            # 1 = rechts, -1 = links (kijkrichting)
        self.grab = False
        self.tick_t = 0.0
        self.dead_t = 0.0
        self.tick_alive = True
        self.amoeba_t = 0.0
        self.cam_x = 0.0
        self.cam_y = 0.0
        self._tick_count = 0

    # ---------- hulp ----------
    def enemy_at(self, x, y):
        return (x, y) in self.enemies

    def solid_round(self, c):
        return c in (ROCK, DIAMOND, STEEL)

    def passable_empty(self, x, y):
        return (0 <= x < CW and 0 <= y < CH and self.grid[y][x] == EMPTY
                and not self.enemy_at(x, y) and (x, y) != (self.px, self.py))

    # ---------- speler ----------
    def player_action(self):
        if self.move_dir is None:
            return
        dx, dy = self.move_dir
        if dx != 0:
            self.facing = 1 if dx > 0 else -1
        nx, ny = self.px + dx, self.py + dy
        if not (0 <= nx < CW and 0 <= ny < CH):
            return
        c = self.grid[ny][nx]
        if c == EXIT and self.exit_open:
            self.px, self.py = nx, ny
            self._cave_clear()
            return
        if self.enemy_at(nx, ny):
            self._explode(nx, ny)
            self._die()
            return
        if c == LAVA:
            if not self.grab:
                self.px, self.py = nx, ny
            self._die()
            return
        if c in (STEEL, MAGIC, EXIT, AMOEBA, SLIME, GROWWALL):
            return
        if c == DIRT:
            self.grid[ny][nx] = EMPTY
            if self.app.sfx:
                self.app.sfx.play("dig")
            if not self.grab:
                self.px, self.py = nx, ny
        elif c == EMPTY:
            if not self.grab:
                self.px, self.py = nx, ny
        elif c == DIAMOND:
            self.grid[ny][nx] = EMPTY
            self._collect()
            if not self.grab:
                self.px, self.py = nx, ny
        elif c == ROCK:
            if dy == 0:
                bx = nx + dx
                if 0 <= bx < CW and self.grid[ny][bx] == EMPTY and not self.enemy_at(bx, ny):
                    self.grid[ny][bx] = ROCK
                    self.grid[ny][nx] = EMPTY
                    if self.app.sfx:
                        self.app.sfx.play("push")
                    if not self.grab:
                        self.px, self.py = nx, ny

    def _collect(self):
        self.collected += 1
        self.score += self.dval
        if self.app.sfx:
            self.app.sfx.play("diamond")
        if self.collected >= self.need and not self.exit_open:
            self.exit_open = True
            if self.app.sfx:
                self.app.sfx.play("exit")

    # ---------- fysica ----------
    def physics(self):
        moved = set()
        for y in range(CH - 2, -1, -1):
            for x in range(CW):
                if (x, y) in moved:
                    continue
                c = self.grid[y][x]
                if c not in (ROCK, DIAMOND):
                    continue
                below = self.grid[y + 1][x]
                falling = (x, y) in self.falling
                # vallend op speler/vijand?
                if falling:
                    if (x, y + 1) == (self.px, self.py):
                        self._die()
                        self.falling.discard((x, y))
                        continue
                    if self.enemy_at(x, y + 1):
                        self._explode(x, y + 1)
                        continue
                if below == EMPTY and not self.enemy_at(x, y + 1) and (x, y + 1) != (self.px, self.py):
                    self.grid[y + 1][x] = c
                    self.grid[y][x] = EMPTY
                    moved.add((x, y + 1))
                    self.falling.add((x, y + 1))
                    self.falling.discard((x, y))
                elif below == LAVA:
                    # in de lava: verdwijnt (borrelt op)
                    self.grid[y][x] = EMPTY
                    self.falling.discard((x, y))
                    if self.app.sfx:
                        self.app.sfx.play("rock")
                elif below == SLIME and y + 2 < CH and self.grid[y + 2][x] == EMPTY \
                        and not self.enemy_at(x, y + 2) and (x, y + 2) != (self.px, self.py):
                    if random.random() < SLIME_PERM:
                        # zakt door het slijm
                        self.grid[y + 2][x] = c
                        self.grid[y][x] = EMPTY
                        moved.add((x, y + 2))
                        self.falling.add((x, y + 2))
                        self.falling.discard((x, y))
                    elif falling:
                        self.falling.discard((x, y))
                elif below == MAGIC and y + 2 < CH and self.grid[y + 2][x] == EMPTY \
                        and not self.enemy_at(x, y + 2) and (x, y + 2) != (self.px, self.py):
                    newc = DIAMOND if c == ROCK else ROCK
                    self.grid[y + 2][x] = newc
                    self.grid[y][x] = EMPTY
                    moved.add((x, y + 2))
                    self.falling.add((x, y + 2))
                    self.falling.discard((x, y))
                elif self.solid_round(below):
                    rolled = False
                    if (self.grid[y][x - 1] == EMPTY and self.grid[y + 1][x - 1] == EMPTY
                            and not self.enemy_at(x - 1, y) and not self.enemy_at(x - 1, y + 1)
                            and (self.px, self.py) not in ((x - 1, y), (x - 1, y + 1))):
                        self.grid[y][x - 1] = c
                        self.grid[y][x] = EMPTY
                        moved.add((x - 1, y))
                        self.falling.add((x - 1, y))
                        self.falling.discard((x, y))
                        rolled = True
                    elif (x + 1 < CW and self.grid[y][x + 1] == EMPTY and self.grid[y + 1][x + 1] == EMPTY
                          and not self.enemy_at(x + 1, y) and not self.enemy_at(x + 1, y + 1)
                          and (self.px, self.py) not in ((x + 1, y), (x + 1, y + 1))):
                        self.grid[y][x + 1] = c
                        self.grid[y][x] = EMPTY
                        moved.add((x + 1, y))
                        self.falling.add((x + 1, y))
                        self.falling.discard((x, y))
                        rolled = True
                    if not rolled and falling:
                        self.falling.discard((x, y))
                        if self.app.sfx:
                            self.app.sfx.play("rock")
                else:
                    if falling:
                        self.falling.discard((x, y))
                        if self.app.sfx:
                            self.app.sfx.play("rock")

    # ---------- vijanden ----------
    def enemies_move(self):
        # eerst: vijand naast speler -> ontploft (speler dood)
        for (x, y), (kind, d) in list(self.enemies.items()):
            if (x, y) not in self.enemies:
                continue
            for k in range(4):
                if (x + DX[k], y + DY[k]) == (self.px, self.py):
                    self._explode(x, y)
                    self._die()
                    break
        new = {}
        for (x, y), (kind, d) in list(self.enemies.items()):
            if (x, y) not in self.enemies:
                continue
            if kind == "f":
                order = [(d - 1) % 4, d, (d + 1) % 4, (d + 2) % 4]
            else:
                order = [(d + 1) % 4, d, (d - 1) % 4, (d + 2) % 4]
            moved = False
            for nd in order:
                tx, ty = x + DX[nd], y + DY[nd]
                if self.passable_empty(tx, ty) and (tx, ty) not in new:
                    new[(tx, ty)] = [kind, nd]
                    moved = True
                    break
            if not moved:
                new[(x, y)] = [kind, (d + 2) % 4]
        self.enemies = new

    # ---------- amoebe ----------
    def amoeba_grow(self):
        if not self.amoeba:
            return
        if len(self.amoeba) > AMOEBA_MAX:
            for (x, y) in self.amoeba:
                self.grid[y][x] = ROCK
            self.amoeba = set()
            return
        can_grow = False
        adds = []
        for (x, y) in self.amoeba:
            for k in range(4):
                tx, ty = x + DX[k], y + DY[k]
                if 0 <= tx < CW and 0 <= ty < CH and self.grid[ty][tx] in (EMPTY, DIRT) \
                        and (tx, ty) != (self.px, self.py):
                    can_grow = True
                    if random.random() < 0.10:
                        adds.append((tx, ty))
        if not can_grow:
            for (x, y) in self.amoeba:
                self.grid[y][x] = DIAMOND
            self.amoeba = set()
            return
        for (tx, ty) in adds:
            if self.grid[ty][tx] in (EMPTY, DIRT):
                self.grid[ty][tx] = AMOEBA
                self.amoeba.add((tx, ty))

    # ---------- groeiende muur ----------
    def grow_wall(self):
        if not self.growwall:
            return
        adds = []
        for (x, y) in self.growwall:
            for dx in (-1, 1):
                tx = x + dx
                if 0 <= tx < CW and self.grid[y][tx] == EMPTY \
                        and not self.enemy_at(tx, y) and (tx, y) != (self.px, self.py):
                    if random.random() < 0.09:
                        adds.append((tx, y))
        for (tx, ty) in adds:
            if self.grid[ty][tx] == EMPTY:
                self.grid[ty][tx] = GROWWALL
                self.growwall.add((tx, ty))

    # ---------- explosie / dood ----------
    def _explode(self, cx, cy, butterfly=None):
        if butterfly is None:
            butterfly = self.enemies.get((cx, cy), ["", 0])[0] == "b"
        if self.app.sfx:
            self.app.sfx.play("boom")
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                x, y = cx + dx, cy + dy
                if not (0 <= x < CW and 0 <= y < CH):
                    continue
                if self.grid[y][x] == STEEL or (x, y) == self.exit:
                    continue
                self.grid[y][x] = DIAMOND if butterfly else EMPTY
                self.enemies.pop((x, y), None)
                self.amoeba.discard((x, y))
                self.falling.discard((x, y))
                if (x, y) == (self.px, self.py):
                    self._die()
        self.enemies.pop((cx, cy), None)

    def _die(self):
        if self.finished or not self.tick_alive:
            return
        self.tick_alive = False
        self.dead_t = 0.0
        if self.app.sfx:
            self.app.sfx.play("death")

    def _finalize_death(self):
        self.lives -= 1
        self.app.run_score = self.score
        if self.lives <= 0:
            self.finished = True
            self.result = "dead"
            if self.score > self.app.cfg.get("highscore", 0):
                self.app.cfg["highscore"] = self.score
                save_config(self.app.cfg)
        else:
            self.app.run_lives = self.lives
            self.load_cave()

    def _cave_clear(self):
        if self.finished:
            return
        bonus = int(self.time_left) * 2
        self.score += bonus
        self.app.run_score = self.score
        self.app.run_lives = self.lives
        if self.app.sfx:
            self.app.sfx.play("clear")
        if self.cave_idx + 1 >= self.app.cfg.get("max_cave", 0):
            self.app.cfg["max_cave"] = min(N_CAVES - 1, self.cave_idx + 1)
        if self.score > self.app.cfg.get("highscore", 0):
            self.app.cfg["highscore"] = self.score
        save_config(self.app.cfg)
        self.finished = True
        self.result = "win" if self.cave_idx + 1 >= N_CAVES else "clear"

    # ---------- update ----------
    def update(self, dt):
        if self.finished:
            return
        if not self.tick_alive:
            self.dead_t += dt
            if self.dead_t > 0.8:
                self._finalize_death()
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self._die()
            return
        self.tick_t += dt
        if self.tick_t >= TICK:
            self.tick_t -= TICK
            self._tick_count += 1
            self.player_action()
            self.physics()
            if self._tick_count % 2 == 0:
                self.enemies_move()
            self.amoeba_grow()
            self.grow_wall()

    # ---------- camera + tekenen ----------
    def _update_cam(self):
        tx = (self.px + 0.5) * TILE - WIDTH / 2
        ty = (self.py + 0.5) * TILE - (HEIGHT - HUD_H) / 2
        tx = clamp(tx, 0, CW * TILE - WIDTH)
        ty = clamp(ty, 0, CH * TILE - (HEIGHT - HUD_H))
        self.cam_x += (tx - self.cam_x) * 0.2
        self.cam_y += (ty - self.cam_y) * 0.2

    def draw(self, surf):
        self._update_cam()
        ox, oy = int(self.cam_x), int(self.cam_y)
        c0 = max(0, ox // TILE)
        r0 = max(0, oy // TILE)
        c1 = min(CW, c0 + VIEW_C + 2)
        r1 = min(CH, r0 + VIEW_R + 2)
        for y in range(r0, r1):
            for x in range(c0, c1):
                sx = x * TILE - ox
                sy = y * TILE - oy + HUD_H
                self._draw_cell(surf, self.grid[y][x], sx, sy, x, y)
        # amoebe-glans is al in cell; vijanden
        for (x, y), (kind, d) in self.enemies.items():
            if c0 <= x < c1 and r0 <= y < r1:
                self._draw_enemy(surf, kind, x * TILE - ox, y * TILE - oy + HUD_H)
        # speler
        if self.tick_alive:
            self._draw_player(surf, self.px * TILE - ox, self.py * TILE - oy + HUD_H)

    def _draw_cell(self, surf, c, sx, sy, gx, gy):
        if c == EMPTY:
            return
        r = pygame.Rect(sx, sy, TILE, TILE)
        if c == DIRT:
            pygame.draw.rect(surf, DIRT_COL if (gx + gy) % 2 == 0 else DIRT_COL2, r)
            pygame.draw.line(surf, mix(DIRT_COL, (0, 0, 0), 0.3), (sx, sy), (sx + TILE, sy))
        elif c == STEEL:
            pygame.draw.rect(surf, STEEL_COL, r)
            pygame.draw.rect(surf, mix(STEEL_COL, (255, 255, 255), 0.2), (sx + 3, sy + 3, TILE - 6, 5))
            pygame.draw.rect(surf, mix(STEEL_COL, (0, 0, 0), 0.3), r, 2)
        elif c == ROCK:
            pygame.draw.circle(surf, ROCK_COL, (sx + TILE // 2, sy + TILE // 2), TILE // 2 - 3)
            pygame.draw.circle(surf, mix(ROCK_COL, (255, 255, 255), 0.3), (sx + TILE // 2 - 5, sy + TILE // 2 - 5), 5)
            pygame.draw.circle(surf, mix(ROCK_COL, (0, 0, 0), 0.35), (sx + TILE // 2, sy + TILE // 2), TILE // 2 - 3, 2)
        elif c == DIAMOND:
            cx, cy = sx + TILE // 2, sy + TILE // 2
            s = TILE // 2 - 4
            pts = [(cx, cy - s), (cx + s * 0.75, cy), (cx, cy + s), (cx - s * 0.75, cy)]
            pygame.draw.polygon(surf, ACCENT, pts)
            pygame.draw.polygon(surf, (220, 235, 250), pts, 2)
            pygame.draw.line(surf, (235, 245, 255), (cx, cy - s), (cx, cy + s), 1)
        elif c == AMOEBA:
            pygame.draw.rect(surf, mix(GOED, BG, 0.1), r, border_radius=8)
            pygame.draw.circle(surf, mix(GOED, (255, 255, 255), 0.25), (sx + 13, sy + 13), 5)
        elif c == MAGIC:
            pygame.draw.rect(surf, mix(PURPLE, BG, 0.25), r)
            for i in range(0, TILE, 8):
                pygame.draw.line(surf, PURPLE, (sx + i, sy), (sx, sy + i))
            pygame.draw.rect(surf, PURPLE, r, 2)
        elif c == LAVA:
            ph = (self._tick_count + gx * 2 + gy) % 6
            pygame.draw.rect(surf, (150, 40, 20), r)
            pygame.draw.rect(surf, (210, 90, 30), (sx, sy + 4 + (ph - 3), TILE, TILE - 8))
            pygame.draw.circle(surf, (245, 180, 60), (sx + 12, sy + 18 + (ph - 3)), 4)
            pygame.draw.circle(surf, (245, 150, 50), (sx + 28, sy + 24 - (ph - 3)), 3)
        elif c == SLIME:
            pygame.draw.rect(surf, mix((70, 120, 200), BG, 0.15), r, border_radius=6)
            pygame.draw.circle(surf, mix((120, 170, 230), (255, 255, 255), 0.2), (sx + 12, sy + 14), 4)
            pygame.draw.circle(surf, mix((120, 170, 230), (255, 255, 255), 0.1), (sx + 27, sy + 26), 3)
        elif c == GROWWALL:
            pygame.draw.rect(surf, (120, 96, 60), r)
            pygame.draw.rect(surf, mix((120, 96, 60), (255, 255, 255), 0.18), (sx + 2, sy + 2, TILE - 4, 6))
            for yy in range(sy + 4, sy + TILE, 12):
                pygame.draw.line(surf, mix((120, 96, 60), (0, 0, 0), 0.3), (sx, yy), (sx + TILE, yy))
            pygame.draw.rect(surf, mix((120, 96, 60), (0, 0, 0), 0.35), r, 2)
        elif c == EXIT:
            if self.exit_open:
                fl = (self._tick_count % 2 == 0)
                pygame.draw.rect(surf, GOED if fl else GOLD, r, border_radius=4)
                pygame.draw.rect(surf, (255, 255, 255), (sx + 8, sy + 8, TILE - 16, TILE - 16), 2)
            else:
                pygame.draw.rect(surf, STEEL_COL, r)
                pygame.draw.rect(surf, mix(STEEL_COL, (0, 0, 0), 0.3), r, 2)

    def _draw_player(self, surf, sx, sy):
        f = self.facing                       # 1 rechts, -1 links
        cx = sx + TILE // 2
        skin = (236, 198, 168)
        skin_d = (176, 128, 96)
        helmet = (208, 92, 64)
        helmet_d = (150, 60, 40)
        boot = (40, 40, 48)
        # benen/laarzen - voorste voet iets naar de kijkrichting
        pygame.draw.rect(surf, boot, (cx - 8 + (2 if f > 0 else 0), sy + 31, 6, 7), border_radius=2)
        pygame.draw.rect(surf, boot, (cx + 2 + (2 if f > 0 else 0), sy + 31, 6, 7), border_radius=2)
        # romp (overall)
        pygame.draw.rect(surf, helmet, (sx + 12, sy + 19, TILE - 24, 15), border_radius=5)
        pygame.draw.rect(surf, helmet_d, (sx + 12, sy + 19, TILE - 24, 15), 2, border_radius=5)
        # armpje aan de kijkkant
        pygame.draw.rect(surf, skin, (cx + f * 9 - 2, sy + 21, 4, 8), border_radius=2)
        # hoofd
        hx, hy = cx + f * 1, sy + 12
        pygame.draw.circle(surf, skin, (hx, hy), 9)
        pygame.draw.circle(surf, skin_d, (hx, hy), 9, 2)
        # helm-rand bovenop
        pygame.draw.rect(surf, helmet, (hx - 9, sy + 3, 18, 5), border_radius=2)
        pygame.draw.rect(surf, helmet_d, (hx - 9, sy + 3, 18, 5), 1, border_radius=2)
        # ogen - kijken naar de looprichting
        eox = f * 2
        for s in (-3, 3):
            pygame.draw.circle(surf, (255, 255, 255), (hx + s + eox, hy), 3)
            pygame.draw.circle(surf, (24, 24, 28), (hx + s + eox + f, hy), 1)

    def _draw_enemy(self, surf, kind, sx, sy):
        cx, cy = sx + TILE // 2, sy + TILE // 2
        col = WARN if kind == "f" else PURPLE
        pygame.draw.rect(surf, col, (sx + 5, sy + 5, TILE - 10, TILE - 10), border_radius=6)
        pygame.draw.circle(surf, (20, 20, 24), (cx - 5, cy - 2), 3)
        pygame.draw.circle(surf, (20, 20, 24), (cx + 5, cy - 2), 3)
        pygame.draw.rect(surf, mix(col, (255, 255, 255), 0.3), (sx + 8, sy + 8, TILE - 16, 4))


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
    f_title = pygame.font.Font(None, 72)
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

        self.font_xl = pygame.font.Font(None, 76)
        self.font_l = pygame.font.Font(None, 50)
        self.font_m = pygame.font.Font(None, 32)
        self.font_s = pygame.font.Font(None, 25)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.game = None
        self.sel_cave = 0
        self.sel_diff = 1
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
        if self.state in ("title", "settings", "help", "gameover", "victory", "caveselect", "caveclear"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            self.sfx.start_music("play1" if (self.game and self.game.cave_idx % 2 == 0) else "play2")

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
            self.set_state("caveselect")
        elif a == "start_run":
            self.run_score = 0
            self.run_lives = 3
            self.start_game(self.sel_cave, self.sel_diff)
        elif a == "cave_prev":
            self.sel_cave = (self.sel_cave - 1) % N_CAVES
        elif a == "cave_next":
            self.sel_cave = (self.sel_cave + 1) % N_CAVES
        elif a == "diff_prev":
            self.sel_diff = max(1, self.sel_diff - 1)
        elif a == "diff_next":
            self.sel_diff = min(N_DIFF, self.sel_diff + 1)
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
            self.start_game(self.sel_cave, self.sel_diff)
        elif a == "to_title":
            self.set_state("title")
        elif a == "to_caveselect":
            self.set_state("caveselect")
        elif a == "next_cave":
            self.start_game(self.game.cave_idx + 1, self.sel_diff)
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
        return {"help": "back_title", "settings": "back_title", "caveselect": "back_title",
                "pause": "resume", "gameover": "to_title", "victory": "to_title",
                "caveclear": "to_caveselect"}.get(self.state)

    def on_key(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            return
        if self.state == "caveclear" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("next_cave"); return
        if self.state in ("gameover", "victory") and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("retry" if self.state == "gameover" else "to_title"); return
        if key == pygame.K_ESCAPE:
            self._action(self._back_for_state())
            return
        if self.state == "caveselect":
            if key in (pygame.K_LEFT, pygame.K_a):
                self._action("cave_prev"); return
            if key in (pygame.K_RIGHT, pygame.K_d):
                self._action("cave_next"); return
            if key in (pygame.K_UP, pygame.K_w):
                self._action("diff_next"); return
            if key in (pygame.K_DOWN, pygame.K_s):
                self._action("diff_prev"); return
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._action("start_run"); return
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

    def start_game(self, cave_idx, diff):
        cave_idx = clamp(cave_idx, 0, N_CAVES - 1)
        self.sel_cave = cave_idx
        self.game = Game(self, cave_idx, diff)
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            keys = pygame.key.get_pressed()
            self.game.grab = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            d = None
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                d = (-1, 0)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                d = (1, 0)
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                d = (0, -1)
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                d = (0, 1)
            self.game.move_dir = d
            self.game.update(dt)
            if self.game.finished and self.t_state > 0.3:
                if self.game.result == "dead":
                    self.set_state("gameover")
                elif self.game.result == "win":
                    self.set_state("victory")
                else:
                    self.set_state("caveclear")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "caveselect":
            self._draw_caveselect(s)
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
        elif st == "caveclear":
            s.fill(BG)
            self.game.draw(s)
            self._overlay(s, t("grot_klaar"), ["%s %d" % (t("score"), self.game.score)],
                          [(t("volgende"), "next_cave"), (t("hoofdmenu"), "to_title")], color=GOED)
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
        play_like = self.state in ("play", "pause", "gameover", "caveclear", "victory")
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

    def _draw_caveselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_grot"), self.font_l, ACCENT, WIDTH // 2, 70)
        letter = CAVES[self.sel_cave][0]
        maxc = self.cfg.get("max_cave", 0)
        # grot-kiezer
        self._text(s, t("grot"), self.font_m, MUTED, WIDTH // 2, 150)
        self._add_button("<", (WIDTH // 2 - 180, 175, 60, 60), "cave_prev")
        self._text(s, "%s  (%d/%d)" % (letter, self.sel_cave + 1, N_CAVES), self.font_xl, TEXT, WIDTH // 2, 205)
        self._add_button(">", (WIDTH // 2 + 120, 175, 60, 60), "cave_next")
        if self.sel_cave > maxc:
            self._text(s, "?", self.font_s, MUTED, WIDTH // 2, 245)
        # niveau-kiezer
        self._text(s, t("niveau"), self.font_m, MUTED, WIDTH // 2, 300)
        self._add_button("<", (WIDTH // 2 - 180, 325, 60, 60), "diff_prev")
        self._text(s, "%d / %d" % (self.sel_diff, N_DIFF), self.font_xl, TEXT, WIDTH // 2, 355)
        self._add_button(">", (WIDTH // 2 + 120, 325, 60, 60), "diff_next")
        self._text(s, "%s: %d   %s: %ds" % (t("nodig"), cave_need(self.sel_cave, self.sel_diff),
                   t("tijd"), cave_time(self.sel_cave, self.sel_diff)),
                   self.font_s, GOLD, WIDTH // 2, 410)
        self._add_button(t("start"), (WIDTH // 2 - 120, 450, 240, 60), "start_run", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 60, 220, 48), "back_title", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 70)
        y = 150
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5", "uitleg6"):
            self._text(s, t(k), self.font_s, TEXT, WIDTH // 2, y)
            y += 44
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
        # diamanten
        cx = 24
        s_ = TILE // 4
        pts = [(cx, HUD_H // 2 - s_), (cx + s_ * 0.75, HUD_H // 2), (cx, HUD_H // 2 + s_), (cx - s_ * 0.75, HUD_H // 2)]
        pygame.draw.polygon(s, ACCENT, pts)
        col = GOED if g.exit_open else TEXT
        self._text(s, "%d / %d" % (g.collected, g.need), self.font_m, col, 44, HUD_H // 2, center=False)
        self._text(s, "%s %s" % (t("grot"), CAVES[g.cave_idx][0]), self.font_m, ACCENT, 200, HUD_H // 2, center=False)
        self._text(s, "%s %d" % (t("tijd"), int(g.time_left)), self.font_m,
                   RED if g.time_left < 15 else TEXT, 330, HUD_H // 2, center=False)
        self._text(s, "%s %d" % (t("score"), g.score), self.font_m, GOLD, 500, HUD_H // 2, center=False)
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

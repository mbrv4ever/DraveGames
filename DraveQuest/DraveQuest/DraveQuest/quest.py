# -*- coding: utf-8 -*-
"""
DraveQuest - een zijwaarts scrollende D&D-platformer van Dravenlock Games.

Ren door bossen, dorpen, kerkers en een kasteel; spring over kuilen en op
platforms, sla kisten kapot, schiet vijanden neer of spring erop, en versla
de eindbaas. Pijltjes = lopen, spatie = springen (ingedrukt = hoger),
F = vuren. Volledig offline; stem en geluid worden zelf gegenereerd/gedownload.
"""
import os
import sys
import json
import math
import random

import pygame

import sfx
import tts

APP_NAME = "DraveQuest"
APP_VERSION = "0.2.3"
STUDIO = "Dravenlock Games"
DONATE_URL = "paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60

# ---- natuurkunde
GRAVITY = 0.8
MAX_FALL = 18.0
MOVE_SPEED = 5.6
JUMP_V = 14.0
SHOT_SPEED = 12.0
TILE = 48

# ---- palet (Dravenlock donker)
BG = (14, 14, 17)
PANEL = (22, 22, 27)
PANEL2 = (28, 28, 34)
LINE = (44, 44, 52)
TEXT = (224, 224, 228)
MUTED = (140, 140, 150)
ACCENT = (111, 163, 214)
GOLD = (212, 175, 90)
GOOD = (127, 176, 105)
WARN = (214, 138, 111)
RED = (200, 70, 70)
PURPLE = (150, 110, 200)


# ---------------------------------------------------------------- config
def _config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "DraveQuest")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _config_path():
    return os.path.join(_config_dir(), "config.json")


def load_config():
    try:
        with open(_config_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception:
        pass


# ---------------------------------------------------------------- taal
LANG = "nl"

TR = {
    "Nieuw spel": "New game", "Gids": "Guide", "Instellingen": "Settings",
    "Taal": "Language", "Afsluiten": "Quit", "Terug": "Back", "Verder": "Continue",
    "Nederlands": "Dutch", "Engels": "English", "Aan": "On", "Uit": "Off",
    "Hervatten": "Resume", "Hoofdmenu": "Main menu", "Gepauzeerd": "Paused",
    "Opnieuw spelen": "Play again", "Hoe te spelen": "How to play",
    "Stem": "Voice", "Geluid": "Sound", "Volume": "Volume",
    "Stem installeren": "Install voice", "Bezig...": "Working...",
    "Spel voorbij": "Game over", "Je bent gevallen...": "You have fallen...",
    "Overwinning!": "Victory!", "Niveau voltooid!": "Level complete!",
    "Druk op een toets": "Press any key", "Pijltjes + Enter, of klik": "Arrows + Enter, or click",
    "Munten": "Coins", "Niveau": "Level", "Leven": "Health",
    "Welkom in het dorp!": "Welcome to the village!",
    "Checkpoint bereikt": "Checkpoint reached",
    "De baas nadert...": "The boss approaches...",
    "Doel": "Goal", "Bediening": "Controls", "Vijanden": "Enemies", "Tips": "Tips",
    "Lopen": "Move", "Springen": "Jump", "Hoger springen": "Jump higher",
    "Vuren": "Fire", "Pauze": "Pause",
    "Een D&D-platformavontuur": "A D&D platformer adventure",
    "Een spel gemaakt door": "A game made by",
    "Score": "Score", "Beste": "Best", "Eindeloos": "Endless",
    "Schild": "Shield", "Snel vuren": "Rapid fire", "Dubbele sprong": "Double jump",
    "Diepte": "Depth", "Eindeloze modus": "Endless mode",
}


def t(s):
    if LANG == "nl":
        return s
    return TR.get(s, s)


def set_lang(code):
    global LANG
    LANG = "en" if code == "en" else "nl"


def detect_lang():
    for key in ("LANG", "LANGUAGE", "LC_ALL"):
        v = os.environ.get(key, "")
        if v[:2].lower() == "nl":
            return "nl"
        if v[:2].lower() == "en":
            return "en"
    return "nl"


# ---------------------------------------------------------------- tekenen
_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("arial,dejavusans,sans", size, bold=bold)
    return _fonts[key]


def draw_text(surf, txt, x, y, size=24, color=TEXT, center=False, bold=False, shadow=True):
    f = font(size, bold)
    if shadow:
        sh = f.render(txt, True, (0, 0, 0))
        r = sh.get_rect()
        if center:
            r.center = (x + 2, y + 2)
        else:
            r.topleft = (x + 2, y + 2)
        surf.blit(sh, r)
    img = f.render(txt, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(img, r)
    return r


def round_rect(surf, rect, color, radius=10, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def wrap_text(txt, size, max_w):
    f = font(size)
    words = txt.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, rel)


def load_icon():
    for name in ("logo.png", "logo.ico"):
        p = resource_path(os.path.join("assets", name))
        if os.path.exists(p):
            try:
                return pygame.image.load(p).convert_alpha()
            except Exception:
                pass
    return None


# ---------------------------------------------------------------- sprites
def _surf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def draw_hero(facing=1, frame=0, jumping=False, glow=None):
    """Avonturier/magier in ZIJAANZICHT; tekent naar rechts, spiegelt bij links."""
    w, h = 44, 52
    s = _surf(w, h)
    skin = (224, 196, 160)
    cloak = (70, 60, 130)
    trim = (150, 120, 210)
    boot = (60, 45, 40)
    if glow == "schild":
        cloak = (60, 90, 140); trim = (120, 180, 230)
    elif glow == "snel":
        cloak = (130, 70, 60); trim = (220, 150, 110)
    bob = 0 if jumping else int(math.sin(frame * 0.4) * 2)
    # achterste mantelpunt (sleept naar links = achter)
    pygame.draw.polygon(s, cloak, [(12, 24 + bob), (9, 48), (2, 45)])
    # lijf/mantel, iets naar voren leunend
    pygame.draw.polygon(s, cloak, [(12, 20 + bob), (30, 20 + bob), (28, 48), (10, 48)])
    pygame.draw.polygon(s, trim, [(12, 20 + bob), (30, 20 + bob), (29, 28), (11, 28)])
    # benen met stap (voorste been gaat vooruit)
    if jumping:
        pygame.draw.rect(s, boot, (13, 46, 7, 6))
        pygame.draw.rect(s, boot, (25, 44, 8, 8))
    else:
        off = int(math.sin(frame * 0.4) * 4)
        pygame.draw.rect(s, boot, (13, 46 - bob, 7, 6))                       # achter
        pygame.draw.rect(s, boot, (24 + max(0, off), 46 - bob, 7, 6))         # voor
    # hoofd, naar voren (rechts) geplaatst
    hx, hy = 25, 13 + bob
    pygame.draw.circle(s, skin, (hx, hy), 8)
    # neus steekt naar voren (rechts) = duidelijke kijkrichting
    pygame.draw.polygon(s, skin, [(hx + 7, hy - 1), (hx + 12, hy + 2), (hx + 7, hy + 5)])
    # puntmuts met punt naar ACHTEREN (links)
    pygame.draw.polygon(s, cloak, [(hx - 8, hy - 3), (hx + 6, hy - 4), (hx - 16, hy - 13)])
    pygame.draw.circle(s, trim, (hx - 15, hy - 12), 2)
    # één oog vooraan (rechts)
    pygame.draw.circle(s, (255, 255, 255), (hx + 3, hy - 1), 3)
    pygame.draw.circle(s, (30, 30, 45), (hx + 4, hy - 1), 2)
    # staf vooruit gehouden (rechts)
    sx = 36
    pygame.draw.line(s, (150, 110, 70), (sx, 6), (sx, 47), 3)
    tip = ACCENT if glow is None else (120, 180, 230) if glow == "schild" else (220, 150, 110)
    pygame.draw.circle(s, tip, (sx, 6), 4)
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def draw_enemy(kind, frame=0):
    if kind == "spook":
        return draw_spook(frame)
    if kind == "slijm":
        w, h = 40, 32
        s = _surf(w, h)
        sq = int(math.sin(frame * 0.3) * 3)
        col = (110, 180, 90)
        pygame.draw.ellipse(s, col, (2, 6 + sq, 36, 26 - sq))
        pygame.draw.circle(s, (255, 255, 255), (14, 16), 4)
        pygame.draw.circle(s, (255, 255, 255), (26, 16), 4)
        pygame.draw.circle(s, (20, 20, 20), (14, 16), 2)
        pygame.draw.circle(s, (20, 20, 20), (26, 16), 2)
        return s
    if kind == "goblin":
        w, h = 38, 44
        s = _surf(w, h)
        col = (90, 140, 70)
        pygame.draw.rect(s, col, (8, 16, 22, 22), border_radius=4)
        pygame.draw.circle(s, col, (19, 12), 10)
        pygame.draw.polygon(s, col, [(9, 8), (3, 0), (13, 6)])
        pygame.draw.polygon(s, col, [(29, 8), (35, 0), (25, 6)])
        pygame.draw.circle(s, (220, 60, 60), (15, 12), 2)
        pygame.draw.circle(s, (220, 60, 60), (23, 12), 2)
        pygame.draw.rect(s, (60, 45, 40), (10, 38, 7, 6))
        pygame.draw.rect(s, (60, 45, 40), (21, 38, 7, 6))
        return s
    if kind == "vleermuis":
        w, h = 44, 28
        s = _surf(w, h)
        col = (90, 80, 120)
        flap = int(math.sin(frame * 0.5) * 6)
        pygame.draw.polygon(s, col, [(22, 14), (2, 6 + flap), (8, 18), (22, 16)])
        pygame.draw.polygon(s, col, [(22, 14), (42, 6 + flap), (36, 18), (22, 16)])
        pygame.draw.circle(s, (60, 50, 80), (22, 14), 8)
        pygame.draw.circle(s, (220, 200, 90), (19, 12), 2)
        pygame.draw.circle(s, (220, 200, 90), (25, 12), 2)
        return s
    # standaard: skelet
    w, h = 36, 46
    s = _surf(w, h)
    bone = (220, 220, 210)
    pygame.draw.circle(s, bone, (18, 12), 9)
    pygame.draw.circle(s, (20, 20, 20), (14, 12), 2)
    pygame.draw.circle(s, (20, 20, 20), (22, 12), 2)
    pygame.draw.rect(s, bone, (14, 20, 8, 20))
    for yy in range(22, 40, 5):
        pygame.draw.line(s, (40, 40, 40), (14, yy), (22, yy), 1)
    return s


def draw_spook(frame=0):
    w, h = 40, 44
    s = _surf(w, h)
    a = 150 + int(math.sin(frame * 0.2) * 40)
    col = (200, 210, 235, a)
    pygame.draw.circle(s, col, (20, 16), 14)
    pygame.draw.rect(s, col, (6, 16, 28, 18))
    for i, bx in enumerate((8, 16, 24)):
        pygame.draw.circle(s, col, (bx + 4, 34, 4), 5)
    pygame.draw.circle(s, (40, 40, 70), (15, 14), 2)
    pygame.draw.circle(s, (40, 40, 70), (25, 14), 2)
    return s


def draw_boss(frame=0):
    w, h = 120, 110
    s = _surf(w, h)
    body = (150, 60, 70)
    dark = (90, 36, 44)
    br = int(math.sin(frame * 0.2) * 4)
    pygame.draw.ellipse(s, body, (10, 30 + br, 100, 70))
    pygame.draw.ellipse(s, dark, (20, 44 + br, 80, 46))
    # kop
    pygame.draw.circle(s, body, (30, 40 + br), 24)
    pygame.draw.polygon(s, dark, [(14, 22 + br), (8, 4 + br), (24, 18 + br)])
    pygame.draw.polygon(s, dark, [(44, 22 + br), (50, 4 + br), (34, 18 + br)])
    pygame.draw.circle(s, (250, 220, 80), (24, 38 + br), 4)
    pygame.draw.circle(s, (250, 220, 80), (38, 38 + br), 4)
    pygame.draw.circle(s, (20, 10, 10), (24, 38 + br), 2)
    pygame.draw.circle(s, (20, 10, 10), (38, 38 + br), 2)
    # vleugel
    pygame.draw.polygon(s, dark, [(80, 36 + br), (118, 14 + br), (110, 56 + br)])
    return s


def draw_miniboss(frame=0):
    w, h = 64, 70
    s = _surf(w, h)
    body = (120, 100, 70)
    dark = (90, 74, 50)
    bob = int(math.sin(frame * 0.18) * 2)
    pygame.draw.rect(s, body, (12, 24 + bob, 40, 40), border_radius=6)
    pygame.draw.circle(s, body, (32, 18 + bob), 16)
    pygame.draw.polygon(s, dark, [(18, 8 + bob), (12, -2 + bob), (24, 6 + bob)])
    pygame.draw.polygon(s, dark, [(46, 8 + bob), (52, -2 + bob), (40, 6 + bob)])
    pygame.draw.circle(s, (220, 80, 60), (26, 18 + bob), 3)
    pygame.draw.circle(s, (220, 80, 60), (38, 18 + bob), 3)
    pygame.draw.rect(s, (240, 240, 230), (27, 26 + bob, 4, 5))
    pygame.draw.rect(s, (240, 240, 230), (34, 26 + bob, 4, 5))
    pygame.draw.rect(s, dark, (14, 62, 14, 8))
    pygame.draw.rect(s, dark, (36, 62, 14, 8))
    return s


def draw_crate():
    s = _surf(TILE, TILE)
    wood = (150, 110, 60)
    dark = (110, 80, 44)
    pygame.draw.rect(s, wood, (0, 0, TILE, TILE), border_radius=4)
    pygame.draw.rect(s, dark, (0, 0, TILE, TILE), 3, border_radius=4)
    pygame.draw.line(s, dark, (0, 0), (TILE, TILE), 3)
    pygame.draw.line(s, dark, (TILE, 0), (0, TILE), 3)
    return s


def draw_coin(frame=0):
    s = _surf(24, 24)
    wob = abs(int(math.sin(frame * 0.2) * 6))
    pygame.draw.ellipse(s, GOLD, (2 + wob // 2, 2, 20 - wob, 20))
    pygame.draw.ellipse(s, (255, 240, 200), (6 + wob // 2, 5, 8 - wob // 2, 14), 2)
    return s


def draw_flag():
    s = _surf(40, 80)
    pygame.draw.rect(s, (180, 180, 190), (4, 0, 4, 80))
    pygame.draw.polygon(s, GOOD, [(8, 4), (38, 14), (8, 26)])
    return s


def draw_heart(full=True):
    s = _surf(28, 26)
    col = RED if full else (60, 40, 44)
    pygame.draw.circle(s, col, (8, 9), 7)
    pygame.draw.circle(s, col, (20, 9), 7)
    pygame.draw.polygon(s, col, [(1, 11), (27, 11), (14, 25)])
    return s


def draw_tree():
    s = _surf(90, 130)
    pygame.draw.rect(s, (80, 56, 36), (40, 70, 14, 60))
    for cx, cy, r in [(45, 50, 36), (24, 64, 26), (66, 64, 26), (45, 30, 26)]:
        pygame.draw.circle(s, (40, 80, 50), (cx, cy), r)
    return s


def draw_house():
    s = _surf(150, 140)
    pygame.draw.rect(s, (90, 70, 60), (12, 60, 126, 80))
    pygame.draw.polygon(s, (120, 70, 60), [(0, 62), (75, 8), (150, 62)])
    pygame.draw.rect(s, (60, 45, 40), (60, 96, 30, 44))
    pygame.draw.rect(s, GOLD, (24, 78, 24, 24))
    pygame.draw.rect(s, GOLD, (102, 78, 24, 24))
    pygame.draw.rect(s, (40, 30, 28), (24, 78, 24, 24), 2)
    return s


def draw_sign():
    s = _surf(54, 70)
    pygame.draw.rect(s, (90, 64, 40), (24, 20, 6, 50))
    pygame.draw.rect(s, (140, 100, 60), (4, 6, 46, 26), border_radius=4)
    pygame.draw.rect(s, (80, 56, 36), (4, 6, 46, 26), 2, border_radius=4)
    return s


def draw_powerup(kind, frame=0):
    s = _surf(34, 34)
    glow = abs(int(math.sin(frame * 0.15) * 3))
    pygame.draw.circle(s, (20, 20, 26), (17, 17), 16)
    if kind == "hart":
        pygame.draw.circle(s, RED, (11, 13), 6)
        pygame.draw.circle(s, RED, (23, 13), 6)
        pygame.draw.polygon(s, RED, [(4, 15), (30, 15), (17, 30)])
    elif kind == "snel":
        pygame.draw.circle(s, WARN, (17, 17), 13 - glow)
        pygame.draw.polygon(s, (255, 230, 120), [(18, 5), (10, 19), (16, 19),
                                                 (14, 29), (24, 14), (18, 14)])
    elif kind == "schild":
        pygame.draw.circle(s, ACCENT, (17, 17), 13 - glow)
        pygame.draw.polygon(s, (200, 230, 255), [(17, 6), (27, 11), (27, 19),
                                                 (17, 29), (7, 19), (7, 11)])
    elif kind == "dubbel":
        pygame.draw.circle(s, PURPLE, (17, 17), 13 - glow)
        pygame.draw.polygon(s, (230, 210, 255), [(17, 7), (11, 16), (23, 16)])
        pygame.draw.polygon(s, (230, 210, 255), [(17, 15), (11, 24), (23, 24)])
    return s


def draw_npc(frame=0):
    w, h = 38, 50
    s = _surf(w, h)
    robe = (90, 110, 150)
    bob = int(math.sin(frame * 0.1) * 2)
    pygame.draw.polygon(s, robe, [(9, 20 + bob), (29, 20 + bob), (33, 48), (5, 48)])
    pygame.draw.circle(s, (224, 196, 160), (19, 14 + bob), 8)
    pygame.draw.polygon(s, (150, 120, 70), [(9, 16 + bob), (29, 16 + bob), (19, 2 + bob)])
    pygame.draw.circle(s, (40, 40, 50), (16, 14 + bob), 2)
    pygame.draw.circle(s, (40, 40, 50), (22, 14 + bob), 2)
    return s


def draw_fireball(frame=0):
    s = _surf(28, 22)
    f = abs(int(math.sin(frame * 0.4) * 3))
    pygame.draw.ellipse(s, (220, 90, 40), (0, 2, 26, 18))
    pygame.draw.ellipse(s, (250, 180, 70), (6, 5 + f // 2, 14, 10 - f))
    pygame.draw.polygon(s, (220, 90, 40), [(0, 6), (-8, 11), (0, 16)])
    return s


# ---------------------------------------------------------------- achtergrond
THEME_SKY = {
    "Bos":     ((60, 110, 150), (150, 190, 170)),
    "Dorp":    ((90, 130, 170), (210, 200, 170)),
    "Kerker":  ((30, 28, 44), (70, 60, 80)),
    "Kasteel": ((60, 30, 44), (120, 70, 80)),
}
THEME_HILL = {
    "Bos": (40, 80, 55), "Dorp": (70, 100, 70),
    "Kerker": (34, 30, 46), "Kasteel": (70, 40, 50),
}
THEME_GROUND = {
    "Bos": (74, 54, 36), "Dorp": (80, 64, 44),
    "Kerker": (40, 36, 46), "Kasteel": (54, 40, 46),
}
THEME_TOP = {
    "Bos": (60, 110, 64), "Dorp": (90, 130, 80),
    "Kerker": (60, 54, 70), "Kasteel": (80, 60, 70),
}


def make_sky(theme):
    top, bot = THEME_SKY.get(theme, THEME_SKY["Bos"])
    s = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        f = y / HEIGHT
        col = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
        pygame.draw.line(s, col, (0, y), (WIDTH, y))
    return s


def draw_parallax(surf, theme, cam_x):
    hill = THEME_HILL.get(theme, (40, 80, 55))
    # verre heuvels (langzaam)
    off = int(cam_x * 0.25) % 480
    base = HEIGHT - 150
    for i in range(-1, WIDTH // 240 + 2):
        bx = i * 240 - off
        pygame.draw.polygon(surf, hill,
                            [(bx, base), (bx + 120, base - 90), (bx + 240, base)])
    # middenlaag (sneller, donkerder)
    hill2 = tuple(max(0, c - 16) for c in hill)
    off2 = int(cam_x * 0.5) % 360
    base2 = HEIGHT - 110
    for i in range(-1, WIDTH // 180 + 2):
        bx = i * 180 - off2
        pygame.draw.polygon(surf, hill2,
                            [(bx, base2), (bx + 90, base2 - 70), (bx + 180, base2)])


# ---------------------------------------------------------------- niveaus
def build_level(theme, length, gaps, platforms, crates, coins, enemies, decor,
                village=None, boss=False, moving=None, powerups=None,
                npcs=None, miniboss=None):
    """Maakt een niveau-dict met vaste-grond-rechthoeken en objecten."""
    ground_y = HEIGHT - 90
    solids = []
    # grond met kuilen (gaps = lijst van (x0,x1))
    x = 0
    segs = []
    for (gx0, gx1) in gaps:
        if gx0 > x:
            segs.append((x, gx0))
        x = gx1
    if x < length:
        segs.append((x, length))
    for (x0, x1) in segs:
        solids.append(pygame.Rect(x0, ground_y, x1 - x0, HEIGHT - ground_y + 60))
    plats = []
    for (px, py, pw) in platforms:
        r = pygame.Rect(px, py, pw, 20)
        solids.append(r); plats.append(r)
    crate_rects = []
    for (cx, cy) in crates:
        cyy = (ground_y - TILE) if cy == 0 else cy
        crate_rects.append(pygame.Rect(cx, cyy, TILE, TILE))
    return dict(
        theme=theme, length=length, ground_y=ground_y,
        solids=solids, plats=plats,
        crates=[dict(rect=r, alive=True) for r in crate_rects],
        coins=[dict(x=cx, y=cy, got=False) for (cx, cy) in coins],
        enemies=[dict(x=ex, kind=k, alive=True) for (ex, k) in enemies],
        decor=decor, village=village, boss=boss,
        moving=moving or [], powerups=powerups or [],
        npcs=npcs or [], miniboss=miniboss,
        goal=length - 120,
    )


def make_levels():
    gy = HEIGHT - 90
    L = []
    # --- 1: Bos
    L.append(build_level(
        "Bos", 3600,
        gaps=[(820, 980), (1750, 1900), (2600, 2720)],
        platforms=[(560, gy - 130, 150), (1080, gy - 150, 160),
                   (1500, gy - 120, 150), (2050, gy - 160, 160),
                   (2400, gy - 120, 140), (2950, gy - 150, 170)],
        crates=[(720, 0), (1320, 0), (2250, 0), (3100, 0)],
        coins=[(600, gy - 170), (640, gy - 170), (1120, gy - 190),
               (1560, gy - 160), (2090, gy - 200), (2480, gy - 160),
               (3000, gy - 190), (3300, gy - 130)],
        enemies=[(700, "slijm"), (1200, "goblin"), (1600, "slijm"),
                 (2150, "vleermuis"), (2500, "goblin"), (3050, "slijm"),
                 (3300, "goblin")],
        decor=[(120, "tree"), (380, "tree"), (1000, "tree"), (1700, "tree"),
               (2300, "tree"), (3200, "tree"), (250, "sign")],
        moving=[(880, gy - 110, 110, 160, "x", 1.6)],
        powerups=[(1130, gy - 230, "snel"), (2480, gy - 200, "hart")],
    ))
    # --- 2: Dorp + Kerker
    L.append(build_level(
        "Dorp", 4000,
        gaps=[(1400, 1560), (2500, 2680), (3300, 3460)],
        platforms=[(700, gy - 130, 150), (1150, gy - 160, 150),
                   (1700, gy - 140, 160), (2200, gy - 170, 150),
                   (2800, gy - 140, 160), (3550, gy - 150, 170)],
        crates=[(900, 0), (1850, 0), (2350, 0), (2950, 0), (3700, 0)],
        coins=[(740, gy - 170), (1190, gy - 200), (1740, gy - 180),
               (2240, gy - 210), (2840, gy - 180), (3000, gy - 130),
               (3600, gy - 190), (3800, gy - 130)],
        enemies=[(1000, "goblin"), (1750, "skelet"), (2300, "vleermuis"),
                 (2900, "goblin"), (3200, "skelet"), (3650, "vleermuis")],
        decor=[(300, "house"), (470, "house"), (650, "sign"), (3000, "tree")],
        village=(250, 650),
        moving=[(1430, gy - 120, 110, 130, "x", 1.8),
                (2520, gy - 100, 120, 90, "y", 1.2)],
        powerups=[(1180, gy - 220, "schild"), (3580, gy - 210, "hart")],
        npcs=[(360, "Welkom, dappere reiziger! Pas op voor de kuilen verderop."),
              (540, "In de kerker dwalen spoken. Spring of schiet ze weg!")],
        miniboss=2050,
    ))
    # --- 3: Kerker
    L.append(build_level(
        "Kerker", 3800,
        gaps=[(760, 900), (1500, 1660), (2300, 2440), (3100, 3240)],
        platforms=[(520, gy - 140, 140), (1000, gy - 160, 150),
                   (1700, gy - 130, 150), (2050, gy - 170, 150),
                   (2500, gy - 140, 150), (3300, gy - 160, 160)],
        crates=[(650, 0), (1300, 0), (1950, 0), (2700, 0), (3450, 0)],
        coins=[(560, gy - 180), (1040, gy - 200), (1740, gy - 170),
               (2090, gy - 210), (2540, gy - 180), (3340, gy - 200),
               (3600, gy - 130)],
        enemies=[(700, "spook"), (1100, "skelet"), (1750, "spook"),
                 (2150, "goblin"), (2600, "spook"), (3000, "skelet"),
                 (3400, "spook")],
        decor=[(200, "sign"), (1600, "sign")],
        moving=[(770, gy - 110, 110, 150, "x", 2.0),
                (2310, gy - 120, 120, 140, "x", 2.2)],
        powerups=[(1050, gy - 230, "dubbel"), (2540, gy - 210, "hart"),
                  (3340, gy - 230, "snel")],
        miniboss=2750,
    ))
    # --- 4: Kasteel + eindbaas
    L.append(build_level(
        "Kasteel", 3200,
        gaps=[(900, 1040), (1700, 1840), (2300, 2420)],
        platforms=[(560, gy - 140, 150), (1150, gy - 160, 150),
                   (1450, gy - 120, 140), (2000, gy - 150, 160)],
        crates=[(700, 0), (1300, 0), (2100, 0)],
        coins=[(600, gy - 180), (1190, gy - 200), (1490, gy - 160),
               (2040, gy - 190), (2500, gy - 130)],
        enemies=[(800, "skelet"), (1250, "goblin"), (1900, "spook"),
                 (2350, "skelet")],
        decor=[(150, "house"), (2700, "sign")],
        powerups=[(1180, gy - 220, "schild"), (2040, gy - 230, "hart")],
        moving=[(1710, gy - 110, 110, 120, "x", 1.8)],
        boss=True,
    ))
    return L


def make_endless_level(depth):
    """Genereert een willekeurig niveau voor de eindeloze modus."""
    gy = HEIGHT - 90
    themes = ["Bos", "Dorp", "Kerker", "Kasteel"]
    theme = themes[depth % len(themes)]
    length = 2800 + min(1600, depth * 150)
    rnd = random.Random(depth * 9173 + 7)
    gaps = []
    x = 700
    while x < length - 500:
        w = rnd.randint(120, 180)
        gaps.append((x, x + w))
        x += rnd.randint(600, 900)
    platforms = []
    coins = []
    crates = []
    for px in range(450, length - 300, rnd.randint(420, 560)):
        py = gy - rnd.choice([120, 140, 160, 180])
        platforms.append((px, py, rnd.choice([140, 150, 160])))
        coins.append((px + 30, py - 40))
        if rnd.random() < 0.5:
            crates.append((px + 200, 0))
    kinds = ["slijm", "goblin", "skelet", "vleermuis", "spook"]
    maxk = min(len(kinds), 2 + depth // 2)
    enemies = []
    n_en = 5 + min(8, depth)
    for _ in range(n_en):
        ex = rnd.randint(500, length - 300)
        enemies.append((ex, rnd.choice(kinds[:maxk])))
    powerups = []
    if rnd.random() < 0.7:
        powerups.append((rnd.randint(500, length - 400), gy - 220,
                         rnd.choice(["hart", "snel", "schild", "dubbel"])))
    moving = []
    for (gx0, gx1) in gaps[:2]:
        moving.append((gx0, gy - 110, 110, (gx1 - gx0) + 40, "x", 1.8))
    decor = [(rnd.randint(200, length - 200),
              rnd.choice(["tree", "house", "sign"])) for _ in range(4)]
    mb = (length // 2) if depth >= 2 and rnd.random() < 0.5 else None
    return build_level(theme, length, gaps, platforms, crates, coins, enemies,
                       decor, moving=moving, powerups=powerups, miniboss=mb)


# ---------------------------------------------------------------- entiteiten
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 46)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.max_hp = 5
        self.hp = 5
        self.coins = 0
        self.frame = 0
        self.invuln = 0
        self.shot_cd = 0
        self.jump_held = False
        self.rapid_t = 0          # frames met snel vuren
        self.shield_t = 0         # frames met schild (onkwetsbaar)
        self.can_double = False   # dubbele sprong vrijgespeeld
        self.double_used = False

    @property
    def glow(self):
        if self.shield_t > 0:
            return "schild"
        if self.rapid_t > 0:
            return "snel"
        return None

    def update(self, keys, solids):
        target = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target -= MOVE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target += MOVE_SPEED
        if target != 0:
            self.vx += (target - self.vx) * 0.35
            self.facing = 1 if target > 0 else -1
        else:
            self.vx *= 0.7
            if abs(self.vx) < 0.3:
                self.vx = 0.0
        # zwaartekracht (lichter tijdens stijgen met spatie ingedrukt = hoger)
        g = GRAVITY
        if self.vy < 0 and self.jump_held:
            g = GRAVITY * 0.58
        self.vy = min(MAX_FALL, self.vy + g)
        # horizontaal
        self.rect.x += round(self.vx)
        for s in solids:
            if self.rect.colliderect(s):
                if self.vx > 0:
                    self.rect.right = s.left
                elif self.vx < 0:
                    self.rect.left = s.right
                self.vx = 0
        # verticaal
        self.on_ground = False
        self.rect.y += round(self.vy)
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = s.bottom
                self.vy = 0
        if abs(self.vx) > 0.5 and self.on_ground:
            self.frame += 1
        if self.on_ground:
            self.double_used = False
        if self.invuln > 0:
            self.invuln -= 1
        if self.shot_cd > 0:
            self.shot_cd -= 1
        if self.rapid_t > 0:
            self.rapid_t -= 1
        if self.shield_t > 0:
            self.shield_t -= 1
            self.invuln = max(self.invuln, 2)

    def jump(self):
        if self.on_ground:
            self.vy = -JUMP_V
            self.on_ground = False
            self.jump_held = True
            return True
        if self.can_double and not self.double_used:
            self.vy = -JUMP_V * 0.92
            self.double_used = True
            self.jump_held = True
            return True
        return False

    def release_jump(self):
        self.jump_held = False
        if self.vy < 0:
            self.vy *= 0.45


class Enemy:
    def __init__(self, x, ground_y, kind):
        self.kind = kind
        self.alive = True
        self.fly = kind in ("vleermuis", "spook")
        if self.fly:
            self.rect = pygame.Rect(x, ground_y - 160, 40, 26)
            self.base_y = ground_y - 160
        else:
            h = {"slijm": 30, "goblin": 42, "skelet": 44}.get(kind, 42)
            self.rect = pygame.Rect(x, ground_y - h, 38, h)
        self.vx = random.choice([-1.6, 1.6])
        self.vy = 0.0
        self.frame = random.randint(0, 30)
        self.t = random.random() * 6
        self.x0 = x

    def update(self, solids):
        self.frame += 1
        self.t += 0.03
        if self.fly:
            self.rect.x += int(self.vx)
            self.rect.y = int(self.base_y + math.sin(self.t * 2) * 40)
            if abs(self.rect.x - self.x0) > 180:
                self.vx = -self.vx
            return
        # lopen + zwaartekracht
        self.vy = min(MAX_FALL, self.vy + GRAVITY)
        self.rect.x += int(self.vx)
        for s in solids:
            if self.rect.colliderect(s):
                if self.vx > 0:
                    self.rect.right = s.left
                else:
                    self.rect.left = s.right
                self.vx = -self.vx
                break
        self.rect.y += int(self.vy)
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                self.vy = 0
        # draai om bij rand van platform of patrouille-grens
        if abs(self.rect.x - self.x0) > 220:
            self.vx = -self.vx
            self.x0 = self.rect.x


class Boss:
    def __init__(self, x, ground_y):
        self.rect = pygame.Rect(x, ground_y - 110, 110, 110)
        self.ground_y = ground_y
        self.max_hp = 10
        self.hp = 10
        self.vx = -2.2
        self.vy = 0.0
        self.frame = 0
        self.x0 = x
        self.hit_flash = 0
        self.fire_cd = 90

    def update(self, solids, target=None, fireballs=None):
        self.frame += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        self.vy = min(MAX_FALL, self.vy + GRAVITY)
        # af en toe springen
        if self.frame % 130 == 0:
            self.vy = -13
        self.rect.x += int(self.vx)
        if abs(self.rect.x - self.x0) > 260:
            self.vx = -self.vx
        self.rect.y += int(self.vy)
        for s in solids:
            if self.rect.colliderect(s) and self.vy > 0:
                self.rect.bottom = s.top
                self.vy = 0
        # vuuradem richting speler
        if fireballs is not None and target is not None:
            self.fire_cd -= 1
            if self.fire_cd <= 0:
                self.fire_cd = 110
                dx = target.centerx - self.rect.centerx
                vx = -5.5 if dx < 0 else 5.5
                fireballs.append(Fireball(self.rect.centerx, self.rect.centery - 10, vx))


class MiniBoss:
    """Sterkere tussenvijand halverwege een niveau."""
    def __init__(self, x, ground_y):
        self.rect = pygame.Rect(x, ground_y - 70, 64, 70)
        self.max_hp = 4
        self.hp = 4
        self.vx = random.choice([-2.0, 2.0])
        self.vy = 0.0
        self.frame = random.randint(0, 20)
        self.x0 = x
        self.hit_flash = 0
        self.alive = True

    def update(self, solids):
        self.frame += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        self.vy = min(MAX_FALL, self.vy + GRAVITY)
        self.rect.x += int(self.vx)
        hit = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vx > 0:
                    self.rect.right = s.left
                else:
                    self.rect.left = s.right
                hit = True
                break
        if hit or abs(self.rect.x - self.x0) > 200:
            self.vx = -self.vx
            self.x0 = self.rect.x
        self.rect.y += int(self.vy)
        for s in solids:
            if self.rect.colliderect(s) and self.vy > 0:
                self.rect.bottom = s.top
                self.vy = 0


class MovingPlatform:
    def __init__(self, x, y, w, span, axis, speed):
        self.rect = pygame.Rect(x, y, w, 20)
        self.x0, self.y0 = x, y
        self.span = span
        self.axis = axis
        self.speed = speed
        self.dir = 1
        self.dx = 0
        self.dy = 0

    def update(self):
        ox, oy = self.rect.x, self.rect.y
        if self.axis == "x":
            self.rect.x += int(self.speed * self.dir)
            if abs(self.rect.x - self.x0) > self.span:
                self.dir = -self.dir
        else:
            self.rect.y += int(self.speed * self.dir)
            if abs(self.rect.y - self.y0) > self.span:
                self.dir = -self.dir
        self.dx = self.rect.x - ox
        self.dy = self.rect.y - oy


class Fireball:
    def __init__(self, x, y, vx):
        self.rect = pygame.Rect(x, y, 24, 18)
        self.vx = vx
        self.frame = 0
        self.life = 150

    def update(self):
        self.rect.x += int(self.vx)
        self.frame += 1
        self.life -= 1


class Shot:
    def __init__(self, x, y, vx):
        self.rect = pygame.Rect(x, y, 16, 8)
        self.vx = vx
        self.life = 90

    def update(self):
        self.rect.x += int(self.vx)
        self.life -= 1


# ---------------------------------------------------------------- states
class State:
    def __init__(self, app):
        self.app = app

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, s):
        pass


class SplashState(State):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.spoke = False
        self.voice_done = False

    def handle(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.app.set_state(TitleState(self.app))

    def update(self, dt):
        self.t += dt
        if not self.spoke and self.t > 0.4:
            self.spoke = True
            line = (f"{APP_NAME}. " + t("Een spel gemaakt door") + f" {STUDIO}.")
            if tts.is_installed():
                tts.say(line, on_done=lambda: setattr(self, "voice_done", True))
            else:
                self.voice_done = True
        done = self.voice_done or self.t > 10
        if self.t > 4 and done:
            self.app.set_state(TitleState(self.app))

    def draw(self, s):
        s.fill(BG)
        if self.app.splash_logo:
            r = self.app.splash_logo.get_rect(center=(WIDTH // 2, 230))
            s.blit(self.app.splash_logo, r)
        draw_text(s, APP_NAME, WIDTH // 2, 400, 72, GOLD, center=True, bold=True)
        draw_text(s, t("Een D&D-platformavontuur"), WIDTH // 2, 460, 26, MUTED, center=True)
        draw_text(s, t("Een spel gemaakt door") + f" {STUDIO}",
                  WIDTH // 2, 520, 22, MUTED, center=True)


class TitleState(State):
    def __init__(self, app):
        super().__init__(app)
        self.sel = 0
        self.buttons = []
        self.bg = make_sky("Bos")
        self.camx = 0
        sfx.start_music()

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.buttons)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.buttons)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.buttons[self.sel][1]()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def update(self, dt):
        self.camx += dt * 30

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        draw_parallax(s, "Bos", self.camx)
        pygame.draw.rect(s, THEME_GROUND["Bos"], (0, HEIGHT - 90, WIDTH, 90))
        pygame.draw.rect(s, THEME_TOP["Bos"], (0, HEIGHT - 90, WIDTH, 10))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 10, 14, 120))
        s.blit(ov, (0, 0))
        if self.app.icon_big:
            r = self.app.icon_big.get_rect(center=(WIDTH // 2, 100))
            s.blit(self.app.icon_big, r)
        draw_text(s, APP_NAME, WIDTH // 2, 200, 64, GOLD, center=True, bold=True)
        draw_text(s, t("Een D&D-platformavontuur"), WIDTH // 2, 244, 21, MUTED, center=True)
        hs = t("Beste") + f": {self.app.highscore}"
        if self.app.best_depth:
            hs += "   " + t("Diepte") + f": {self.app.best_depth}"
        draw_text(s, hs, WIDTH // 2, 272, 20, GOLD, center=True)
        items = [
            (t("Nieuw spel"), lambda: self.app.start_game()),
            (t("Eindeloos"), lambda: self.app.start_endless()),
            (t("Gids"), lambda: self.app.set_state(HelpState(self.app))),
            (t("Instellingen"), lambda: self.app.set_state(SettingsState(self.app))),
            (t("Taal") + ": " + (t("Nederlands") if LANG == "nl" else t("Engels")),
             self.app.toggle_lang),
            (t("Afsluiten"), self.app.quit),
        ]
        self.buttons = []
        y = 300
        mx, my = pygame.mouse.get_pos()
        for i, (label, fn) in enumerate(items):
            rect = pygame.Rect(WIDTH // 2 - 170, y, 340, 42)
            hov = rect.collidepoint(mx, my) or i == self.sel
            round_rect(s, rect, PANEL2 if hov else PANEL, 10)
            round_rect(s, rect, ACCENT if hov else LINE, 10, 2)
            draw_text(s, label, WIDTH // 2, y + 21, 25, TEXT, center=True, bold=hov)
            self.buttons.append((rect, fn))
            y += 46
        draw_text(s, f"v{APP_VERSION}  -  {DONATE_URL}", WIDTH // 2, HEIGHT - 14, 18,
                  MUTED, center=True)


class HelpState(State):
    def __init__(self, app, return_state=None):
        super().__init__(app)
        self.return_state = return_state
        self.buttons = []

    def _back(self):
        self.app.set_state(self.return_state or TitleState(self.app))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
            self._back()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def draw(self, s):
        s.fill(BG)
        draw_text(s, t("Gids") + " - " + t("Hoe te spelen"), WIDTH // 2, 44, 44,
                  GOLD, center=True, bold=True)
        x = 90
        y = 110
        blocks = [
            (t("Doel") + ":", [
                ("ren naar rechts door elk niveau, verzamel munten en bereik de vlag;"
                 if LANG == "nl" else
                 "run right through each level, grab coins and reach the flag;"),
                ("in het laatste niveau wacht de eindbaas."
                 if LANG == "nl" else "the final level holds the boss."),
            ]),
            (t("Bediening") + ":", [
                t("Lopen") + ": " + ("pijltjes links/rechts (of A/D)"
                                     if LANG == "nl" else "left/right arrows (or A/D)"),
                t("Springen") + ": " + ("pijl omhoog (of W)"
                                        if LANG == "nl" else "up arrow (or W)"),
                t("Hoger springen") + ": " + ("pijl omhoog ingedrukt houden"
                                              if LANG == "nl" else "hold the up arrow"),
                t("Vuren") + ": " + ("spatiebalk" if LANG == "nl" else "spacebar"),
                t("Pauze") + ": Esc of P",
            ]),
            (t("Vijanden") + ":", [
                ("spring boven op een vijand om hem te verslaan, of schiet hem neer;"
                 if LANG == "nl" else
                 "stomp an enemy from above, or shoot it down;"),
                ("aanraking van opzij doet pijn. Sla kisten kapot voor munten."
                 if LANG == "nl" else
                 "side contact hurts. Smash crates for coins."),
            ]),
            (t("Tips") + ":", [
                ("val niet in de kuilen; gebruik platforms om hoger te komen."
                 if LANG == "nl" else
                 "don't fall in the pits; use platforms to climb higher."),
                ("in dorpen genees je en wordt je voortgang opgeslagen."
                 if LANG == "nl" else
                 "villages heal you and save your progress."),
            ]),
        ]
        columns = [blocks[:2], blocks[2:]]
        col_x = [70, 500]
        col_w = 400
        for ci, col in enumerate(columns):
            cx = col_x[ci]
            cy = 104
            for title, lines in col:
                draw_text(s, title, cx, cy, 26, ACCENT, bold=True)
                cy += 34
                for ln in lines:
                    for wl in wrap_text(ln, 21, col_w):
                        draw_text(s, wl, cx + 16, cy, 21, TEXT)
                        cy += 26
                cy += 14
        self.buttons = []
        back = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 56, 180, 44)
        round_rect(s, back, ACCENT, 10)
        draw_text(s, t("Terug"), back.centerx, back.centery, 26, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.buttons.append((back, self._back))


class SettingsState(State):
    def __init__(self, app, return_state=None):
        super().__init__(app)
        self.return_state = return_state
        self.buttons = []

    def _back(self):
        self.app.set_state(self.return_state or TitleState(self.app))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._back()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def _toggle_sound(self):
        on = not sfx.is_enabled()
        sfx.set_enabled(on)
        self.app.cfg["sound"] = on
        save_config(self.app.cfg)

    def _vol(self, d):
        v = max(0.0, min(1.0, sfx.get_volume() + d))
        sfx.set_volume(v)
        self.app.cfg["sound_vol"] = v
        save_config(self.app.cfg)

    def draw(self, s):
        s.fill(BG)
        draw_text(s, t("Instellingen"), WIDTH // 2, 60, 48, GOLD, center=True, bold=True)
        self.buttons = []
        y = 150
        # stem
        draw_text(s, t("Stem"), 160, y, 30, TEXT, bold=True)
        vb = pygame.Rect(420, y - 6, 150, 44)
        on = tts.is_enabled()
        round_rect(s, vb, GOOD if on else PANEL2, 10)
        round_rect(s, vb, LINE, 10, 2)
        draw_text(s, t("Aan") if on else t("Uit"), vb.centerx, vb.centery, 26,
                  (10, 10, 14) if on else TEXT, center=True, bold=True, shadow=False)
        self.buttons.append((vb, self.app.toggle_voice))
        y += 56
        draw_text(s, tts.status_text(LANG), 160, y, 20, MUTED)
        if not tts.is_installed() and not tts.is_frozen():
            ib = pygame.Rect(420, y - 6, 220, 38)
            round_rect(s, ib, ACCENT, 8)
            draw_text(s, t("Stem installeren"), ib.centerx, ib.centery, 22,
                      (10, 10, 14), center=True, bold=True, shadow=False)
            self.buttons.append((ib, tts.install))
        y += 60
        # geluid
        draw_text(s, t("Geluid"), 160, y, 30, TEXT, bold=True)
        sb = pygame.Rect(420, y - 6, 150, 44)
        son = sfx.is_enabled()
        round_rect(s, sb, GOOD if son else PANEL2, 10)
        round_rect(s, sb, LINE, 10, 2)
        draw_text(s, t("Aan") if son else t("Uit"), sb.centerx, sb.centery, 26,
                  (10, 10, 14) if son else TEXT, center=True, bold=True, shadow=False)
        self.buttons.append((sb, self._toggle_sound))
        y += 60
        draw_text(s, t("Volume"), 160, y, 30, TEXT, bold=True)
        mn = pygame.Rect(420, y - 6, 60, 44)
        pl = pygame.Rect(510, y - 6, 60, 44)
        round_rect(s, mn, PANEL2, 10); round_rect(s, mn, LINE, 10, 2)
        round_rect(s, pl, PANEL2, 10); round_rect(s, pl, LINE, 10, 2)
        draw_text(s, "-", mn.centerx, mn.centery, 34, TEXT, center=True, bold=True)
        draw_text(s, "+", pl.centerx, pl.centery, 34, TEXT, center=True, bold=True)
        draw_text(s, f"{int(sfx.get_volume() * 100)}%", 620, y + 16, 26, MUTED)
        self.buttons.append((mn, lambda: self._vol(-0.1)))
        self.buttons.append((pl, lambda: self._vol(0.1)))
        back = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 80, 180, 48)
        round_rect(s, back, ACCENT, 10)
        draw_text(s, t("Terug"), back.centerx, back.centery, 26, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.buttons.append((back, self._back))


class PlayState(State):
    def __init__(self, app, level_idx):
        super().__init__(app)
        self.level_idx = level_idx
        self.L = app.levels[level_idx]
        self.theme = self.L["theme"]
        self.sky = make_sky(self.theme)
        gy = self.L["ground_y"]
        self.player = Player(80, gy - 60)
        # dubbele sprong behouden als al vrijgespeeld in deze run
        self.player.can_double = app.run_double
        self.enemies = [Enemy(e["x"], gy, e["kind"]) for e in self.L["enemies"]]
        self.crates = [dict(rect=c["rect"].copy(), alive=True) for c in self.L["crates"]]
        self.coins = [dict(x=c["x"], y=c["y"], got=False) for c in self.L["coins"]]
        self.powerups = [dict(x=px, y=py, kind=k, got=False)
                         for (px, py, k) in self.L["powerups"]]
        self.npcs = [dict(x=nx, text=txt, said=False) for (nx, txt) in self.L["npcs"]]
        self.movers = [MovingPlatform(mx, my, mw, span, ax, sp)
                       for (mx, my, mw, span, ax, sp) in self.L["moving"]]
        self.shots = []
        self.fireballs = []
        self.boss = Boss(self.L["length"] - 500, gy) if self.L["boss"] else None
        self.miniboss = MiniBoss(self.L["miniboss"], gy) if self.L["miniboss"] else None
        self.cam_x = 0
        self.frame = 0
        self.checkpoint = 80
        self.msg = ""
        self.msg_t = 0.0
        self.bubble = ""
        self.bubble_t = 0.0
        self.village_done = False
        self.flag = draw_flag()
        self.coin_img = draw_coin()
        self.crate_img = draw_crate()
        self.heart_full = draw_heart(True)
        self.heart_empty = draw_heart(False)
        self.boss_img = draw_boss() if self.boss else None
        if app.endless:
            line = t("Niveau") + f" {level_idx + 1}"
        else:
            line = t("Niveau") + f" {level_idx + 1}"
        if tts.is_enabled():
            tts.say(line)
        sfx.start_music()

    def _solids(self):
        sol = list(self.L["solids"])
        for c in self.crates:
            if c["alive"]:
                sol.append(c["rect"])
        for m in self.movers:
            sol.append(m.rect)
        return sol

    def _flash_msg(self, txt):
        self.msg = txt
        self.msg_t = 2.2

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.app.set_state(PauseState(self.app, self))
            elif e.key in (pygame.K_UP, pygame.K_w):
                if self.player.jump():
                    sfx.play("jump2" if self.player.double_used else "jump")
            elif e.key == pygame.K_SPACE:
                self._fire()
        elif e.type == pygame.KEYUP:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.player.release_jump()

    def _fire(self):
        if self.player.shot_cd > 0:
            return
        self.player.shot_cd = 7 if self.player.rapid_t > 0 else 16
        p = self.player.rect
        x = p.right if self.player.facing > 0 else p.left - 16
        self.shots.append(Shot(x, p.centery - 4, SHOT_SPEED * self.player.facing))
        sfx.play("shoot")

    def _hurt(self, dmg=1):
        if self.player.invuln > 0 or self.player.shield_t > 0:
            return
        self.player.hp -= dmg
        self.player.invuln = 70
        self.player.vy = -8
        self.player.vx = -6 * self.player.facing
        sfx.play("hurt")
        if self.player.hp <= 0:
            self.app.end_run(False)

    def _respawn(self):
        self.player.hp -= 1
        sfx.play("hurt")
        if self.player.hp <= 0:
            self.app.end_run(False)
            return
        self.player.rect.x = self.checkpoint
        self.player.rect.y = self.L["ground_y"] - 60
        self.player.vx = self.player.vy = 0
        self.player.invuln = 60

    def update(self, dt):
        self.frame += 1
        if self.msg_t > 0:
            self.msg_t -= dt
        if self.bubble_t > 0:
            self.bubble_t -= dt
        keys = pygame.key.get_pressed()

        # bewegende platforms eerst, en speler meenemen als hij erop staat
        for m in self.movers:
            ride = (self.player.on_ground
                    and abs(self.player.rect.bottom - m.rect.top) <= 2
                    and self.player.rect.right > m.rect.left
                    and self.player.rect.left < m.rect.right)
            m.update()
            if ride:
                self.player.rect.x += m.dx
                self.player.rect.y += m.dy

        solids = self._solids()
        self.player.update(keys, solids)
        p = self.player.rect

        # dorp: genees + checkpoint
        if self.L["village"] and not self.village_done:
            vx0, vx1 = self.L["village"]
            if vx0 <= p.centerx <= vx1:
                self.village_done = True
                self.checkpoint = p.centerx
                self.player.hp = self.player.max_hp
                self._flash_msg(t("Welkom in het dorp!"))
                sfx.play("chime")

        # NPC's: praten als de speler dichtbij komt
        for npc in self.npcs:
            if not npc["said"] and abs(p.centerx - npc["x"]) < 70:
                npc["said"] = True
                self.bubble = npc["text"]
                self.bubble_t = 4.0
                sfx.play("chime")
                if tts.is_enabled():
                    tts.say(npc["text"], role="hero")

        # in een kuil gevallen
        if p.top > HEIGHT + 80:
            self._respawn()
            return

        # power-ups oppakken
        for pu in self.powerups:
            if not pu["got"] and p.colliderect(pygame.Rect(pu["x"], pu["y"], 34, 34)):
                pu["got"] = True
                k = pu["kind"]
                if k == "hart":
                    self.player.hp = min(self.player.max_hp, self.player.hp + 2)
                    self._flash_msg("+2 " + t("Leven"))
                elif k == "snel":
                    self.player.rapid_t = 60 * 10
                    self._flash_msg(t("Snel vuren!") if LANG == "nl" else "Rapid fire!")
                elif k == "schild":
                    self.player.shield_t = 60 * 8
                    self._flash_msg(t("Schild!") if LANG == "nl" else "Shield!")
                elif k == "dubbel":
                    self.player.can_double = True
                    self.app.run_double = True
                    self._flash_msg(t("Dubbele sprong!") if LANG == "nl" else "Double jump!")
                sfx.play("coin")

        # vijanden
        for en in self.enemies:
            if not en.alive:
                continue
            en.update(solids)
            if p.colliderect(en.rect):
                falling = self.player.vy > 1 and p.bottom - en.rect.top < 24
                if falling:
                    en.alive = False
                    self.player.vy = -11 if not en.fly else -9
                    self.app.score += 25
                    sfx.play("stomp")
                else:
                    self._hurt(1)

        # tussenbaas
        if self.miniboss and self.miniboss.alive:
            if p.centerx > self.miniboss.rect.x - 650:
                self.miniboss.update(solids)
                if p.colliderect(self.miniboss.rect):
                    falling = self.player.vy > 1 and p.bottom - self.miniboss.rect.top < 26
                    if falling:
                        self.miniboss.hp -= 1
                        self.miniboss.hit_flash = 8
                        self.player.vy = -11
                        sfx.play("stomp")
                    else:
                        self._hurt(1)
                if self.miniboss.hp <= 0:
                    self.miniboss.alive = False
                    self.app.score += 100
                    self._flash_msg(t("Tussenbaas verslagen!") if LANG == "nl"
                                    else "Mini-boss defeated!")
                    sfx.play("victory")

        # schoten
        for sh in self.shots:
            sh.update()
            for en in self.enemies:
                if en.alive and sh.rect.colliderect(en.rect):
                    en.alive = False
                    sh.life = 0
                    self.app.score += 25
                    sfx.play("hit")
            for c in self.crates:
                if c["alive"] and sh.rect.colliderect(c["rect"]):
                    c["alive"] = False
                    sh.life = 0
                    sfx.play("break")
                    self.coins.append(dict(x=c["rect"].x + 12, y=c["rect"].y - 6, got=False))
            if self.miniboss and self.miniboss.alive and sh.rect.colliderect(self.miniboss.rect):
                sh.life = 0
                self.miniboss.hp -= 1
                self.miniboss.hit_flash = 8
                sfx.play("hit")
                if self.miniboss.hp <= 0:
                    self.miniboss.alive = False
                    self.app.score += 100
                    sfx.play("victory")
            if self.boss and sh.rect.colliderect(self.boss.rect):
                sh.life = 0
                self.boss.hp -= 1
                self.boss.hit_flash = 8
                sfx.play("hit")
        self.shots = [s for s in self.shots if s.life > 0
                      and -60 < s.rect.x < self.L["length"] + 60]

        # vuurballen van de baas
        for fb in self.fireballs:
            fb.update()
            if p.colliderect(fb.rect):
                fb.life = 0
                self._hurt(1)
        self.fireballs = [f for f in self.fireballs if f.life > 0]

        # kist kapot stampen
        for c in self.crates:
            if c["alive"] and p.colliderect(c["rect"]) and self.player.vy > 2 \
                    and p.bottom - c["rect"].top < 22:
                c["alive"] = False
                self.player.vy = -8
                sfx.play("break")
                self.coins.append(dict(x=c["rect"].x + 12, y=c["rect"].y - 6, got=False))

        # munten
        for c in self.coins:
            if not c["got"] and p.colliderect(pygame.Rect(c["x"], c["y"], 24, 24)):
                c["got"] = True
                self.player.coins += 1
                self.app.score += 10
                sfx.play("coin")

        # eindbaas
        if self.boss:
            if p.centerx > self.boss.rect.x - 700 and self.boss.hp > 0:
                self.boss.update(solids, target=p, fireballs=self.fireballs)
                if p.colliderect(self.boss.rect):
                    self._hurt(1)
            if self.boss.hp <= 0:
                self.app.score += 300
                self.app.win_level(self.level_idx)
                return

        # camera
        target = max(0, min(self.L["length"] - WIDTH, p.centerx - WIDTH // 2))
        self.cam_x += (target - self.cam_x) * 0.15

        # doel bereikt (geen baas-niveau)
        if not self.boss and p.centerx >= self.L["goal"]:
            self.app.score += 200
            self.app.win_level(self.level_idx)


    def draw(self, s):
        cam = int(self.cam_x)
        s.blit(self.sky, (0, 0))
        draw_parallax(s, self.theme, cam)
        gy = self.L["ground_y"]
        # decor
        for (dx, kind) in self.L["decor"]:
            sx = dx - cam
            if -160 < sx < WIDTH + 160:
                if kind == "tree":
                    img = draw_tree(); s.blit(img, (sx, gy - img.get_height()))
                elif kind == "house":
                    img = draw_house(); s.blit(img, (sx, gy - img.get_height()))
                elif kind == "sign":
                    img = draw_sign(); s.blit(img, (sx, gy - img.get_height()))
        # grond
        for r in self.L["solids"]:
            rr = pygame.Rect(r.x - cam, r.y, r.w, r.h)
            if rr.right < 0 or rr.left > WIDTH:
                continue
            if r in self.L["plats"]:
                round_rect(s, rr, THEME_GROUND[self.theme], 6)
                pygame.draw.rect(s, THEME_TOP[self.theme], (rr.x, rr.y, rr.w, 6))
            else:
                pygame.draw.rect(s, THEME_GROUND[self.theme], rr)
                pygame.draw.rect(s, THEME_TOP[self.theme], (rr.x, rr.y, rr.w, 10))
        # bewegende platforms
        for m in self.movers:
            rr = pygame.Rect(m.rect.x - cam, m.rect.y, m.rect.w, m.rect.h)
            round_rect(s, rr, THEME_GROUND[self.theme], 6)
            pygame.draw.rect(s, THEME_TOP[self.theme], (rr.x, rr.y, rr.w, 6))
            pygame.draw.rect(s, GOLD, rr, 2, border_radius=6)
        # kisten
        for c in self.crates:
            if c["alive"]:
                s.blit(self.crate_img, (c["rect"].x - cam, c["rect"].y))
        # munten
        for c in self.coins:
            if not c["got"]:
                s.blit(self.coin_img, (c["x"] - cam, c["y"]))
        # power-ups
        for pu in self.powerups:
            if not pu["got"]:
                img = draw_powerup(pu["kind"], self.frame)
                s.blit(img, (pu["x"] - cam, pu["y"]))
        # NPC's
        for npc in self.npcs:
            sx = npc["x"] - cam
            if -60 < sx < WIDTH + 60:
                img = draw_npc(self.frame)
                s.blit(img, (sx - img.get_width() // 2, gy - img.get_height()))
        # vlag
        if not self.boss:
            s.blit(self.flag, (self.L["goal"] - cam, gy - 80))
        # vijanden
        for en in self.enemies:
            if en.alive:
                img = draw_enemy(en.kind, en.frame)
                s.blit(img, (en.rect.centerx - img.get_width() // 2 - cam,
                             en.rect.bottom - img.get_height()))
        # tussenbaas
        if self.miniboss and self.miniboss.alive:
            img = draw_miniboss(self.miniboss.frame)
            if self.miniboss.hit_flash > 0:
                img = img.copy()
                ov = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                ov.fill((255, 80, 80, 120))
                img.blit(ov, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            s.blit(img, (self.miniboss.rect.centerx - img.get_width() // 2 - cam,
                         self.miniboss.rect.bottom - img.get_height()))
        # baas
        if self.boss and self.boss.hp > 0:
            img = self.boss_img
            if self.boss.hit_flash > 0:
                img = img.copy()
                ov = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                ov.fill((255, 80, 80, 120))
                img.blit(ov, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            s.blit(img, (self.boss.rect.centerx - img.get_width() // 2 - cam,
                         self.boss.rect.bottom - img.get_height()))
        # schoten
        for sh in self.shots:
            r = pygame.Rect(sh.rect.x - cam, sh.rect.y, sh.rect.w, sh.rect.h)
            pygame.draw.ellipse(s, ACCENT, r)
            pygame.draw.ellipse(s, (220, 240, 255), r, 1)
        # vuurballen
        for fb in self.fireballs:
            img = draw_fireball(fb.frame)
            flip = fb.vx > 0
            im = pygame.transform.flip(img, True, False) if flip else img
            s.blit(im, (fb.rect.centerx - im.get_width() // 2 - cam,
                        fb.rect.centery - im.get_height() // 2))
        # speler
        if not (self.player.invuln > 0 and self.player.shield_t == 0
                and self.frame % 6 < 3):
            himg = draw_hero(self.player.facing, self.player.frame,
                             jumping=not self.player.on_ground, glow=self.player.glow)
            s.blit(himg, (self.player.rect.centerx - himg.get_width() // 2 - cam,
                          self.player.rect.bottom - himg.get_height()))
        self._draw_hud(s)

    def _draw_hud(self, s):
        # harten
        for i in range(self.player.max_hp):
            img = self.heart_full if i < self.player.hp else self.heart_empty
            s.blit(img, (20 + i * 32, 18))
        # munten + score
        s.blit(self.coin_img, (20, 54))
        draw_text(s, f"x {self.player.coins}", 50, 56, 26, GOLD, bold=True)
        draw_text(s, t("Score") + f": {self.app.score}", 130, 56, 24, TEXT, bold=True)
        # power-up-timers
        ty = 86
        if self.player.shield_t > 0:
            draw_text(s, t("Schild") + f" {self.player.shield_t // 60 + 1}s",
                      24, ty, 20, ACCENT, bold=True); ty += 24
        if self.player.rapid_t > 0:
            draw_text(s, (t("Snel vuren") if LANG == "nl" else "Rapid")
                      + f" {self.player.rapid_t // 60 + 1}s", 24, ty, 20, WARN, bold=True)
            ty += 24
        if self.player.can_double:
            draw_text(s, t("Dubbele sprong") if LANG == "nl" else "Double jump",
                      24, ty, 18, PURPLE, bold=True)
        draw_text(s, t("Niveau") + f" {self.level_idx + 1}"
                  + ("+" if self.app.endless else ""), WIDTH - 90, 30, 22,
                  TEXT, center=True, bold=True)
        # eindbaas-balk
        if self.boss and self.boss.hp > 0 and self.player.rect.centerx > self.boss.rect.x - 700:
            self._bar(s, self.boss.hp, self.boss.max_hp, "BAAS")
        # tussenbaas-balk
        elif self.miniboss and self.miniboss.alive and \
                self.player.rect.centerx > self.miniboss.rect.x - 650:
            self._bar(s, self.miniboss.hp, self.miniboss.max_hp,
                      "TUSSENBAAS" if LANG == "nl" else "MINI-BOSS", col=WARN)
        # pauzeknop
        pr = pygame.Rect(WIDTH - 52, 54, 34, 34)
        round_rect(s, pr, PANEL2, 8); round_rect(s, pr, LINE, 8, 2)
        pygame.draw.rect(s, TEXT, (pr.x + 10, pr.y + 9, 5, 16))
        pygame.draw.rect(s, TEXT, (pr.x + 19, pr.y + 9, 5, 16))
        self.pause_rect = pr
        # spraakballon NPC
        if self.bubble_t > 0:
            lines = wrap_text(self.bubble, 22, 600)
            bh = 20 + len(lines) * 26
            bx = WIDTH // 2 - 330
            round_rect(s, (bx, HEIGHT - 150, 660, bh), (20, 20, 28), 10)
            round_rect(s, (bx, HEIGHT - 150, 660, bh), ACCENT, 10, 2)
            for i, ln in enumerate(lines):
                draw_text(s, ln, WIDTH // 2, HEIGHT - 150 + 18 + i * 26, 22,
                          TEXT, center=True)
        # flash-bericht
        if self.msg_t > 0:
            ov = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
            ov.fill((10, 10, 14, 180))
            s.blit(ov, (0, HEIGHT // 2 - 25))
            draw_text(s, self.msg, WIDTH // 2, HEIGHT // 2, 34, GOLD, center=True, bold=True)

    def _bar(self, s, hp, maxhp, label, col=RED):
        bw = 360
        bx = WIDTH // 2 - bw // 2
        round_rect(s, (bx, 24, bw, 22), PANEL2, 8)
        frac = max(0, hp / maxhp)
        round_rect(s, (bx, 24, int(bw * frac), 22), col, 8)
        round_rect(s, (bx, 24, bw, 22), LINE, 8, 2)
        draw_text(s, label, WIDTH // 2, 35, 16, TEXT, center=True, bold=True)


class PauseState(State):
    def __init__(self, app, game_state):
        super().__init__(app)
        self.gs = game_state
        self.sel = 0
        self.buttons = []
        self.items = [
            ("Hervatten", self._resume),
            ("Instellingen", lambda: self.app.set_state(SettingsState(self.app, self))),
            ("Gids", lambda: self.app.set_state(HelpState(self.app, self))),
            ("Nieuw spel", lambda: self.app.start_game()),
            ("Hoofdmenu", lambda: self.app.set_state(TitleState(self.app))),
        ]

    def _resume(self):
        self.app.set_state(self.gs)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self._resume()
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.items)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.items)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.items[self.sel][1]()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def draw(self, s):
        self.gs.draw(s)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 8, 12, 190))
        s.blit(ov, (0, 0))
        draw_text(s, t("Gepauzeerd"), WIDTH // 2, 130, 56, GOLD, center=True, bold=True)
        self.buttons = []
        y = 230
        mx, my = pygame.mouse.get_pos()
        for i, (label, fn) in enumerate(self.items):
            rect = pygame.Rect(WIDTH // 2 - 170, y, 340, 50)
            hov = rect.collidepoint(mx, my) or i == self.sel
            round_rect(s, rect, PANEL2 if hov else PANEL, 10)
            round_rect(s, rect, ACCENT if hov else LINE, 10, 2)
            draw_text(s, t(label), WIDTH // 2, y + 25, 27, TEXT, center=True, bold=hov)
            self.buttons.append((rect, fn))
            y += 62
        draw_text(s, "Esc / P", WIDTH // 2, HEIGHT - 40, 22, MUTED, center=True)


class LevelCompleteState(State):
    def __init__(self, app, level_idx):
        super().__init__(app)
        self.level_idx = level_idx
        self.t = 0.0
        self.buttons = []
        sfx.play("victory")

    def handle(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.app.set_state(PlayState(self.app, self.level_idx + 1))

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.fill(BG)
        draw_text(s, t("Niveau voltooid!"), WIDTH // 2, 230, 60, GOLD, center=True, bold=True)
        draw_text(s, t("Verder") + " -> " + t("Niveau") + f" {self.level_idx + 2}"
                  + ("+" if self.app.endless else ""),
                  WIDTH // 2, 310, 30, TEXT, center=True)
        draw_text(s, t("Score") + f": {self.app.score}", WIDTH // 2, 360, 28,
                  ACCENT, center=True, bold=True)
        draw_text(s, t("Druk op een toets"), WIDTH // 2, HEIGHT - 60, 24, MUTED, center=True)


class VictoryState(State):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = []
        sfx.play("victory")

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.start_game()
            elif e.key == pygame.K_ESCAPE:
                self.app.set_state(TitleState(self.app))

    def draw(self, s):
        s.fill(BG)
        draw_text(s, t("Overwinning!"), WIDTH // 2, 130, 78, GOLD, center=True, bold=True)
        draw_text(s, ("Je hebt de eindbaas verslagen!" if LANG == "nl"
                      else "You defeated the boss!"), WIDTH // 2, 205, 28, TEXT, center=True)
        draw_text(s, t("Score") + f": {self.app.score}", WIDTH // 2, 260, 32,
                  ACCENT, center=True, bold=True)
        draw_text(s, t("Beste") + f": {self.app.highscore}", WIDTH // 2, 300, 24,
                  GOLD, center=True)
        if self.app.icon_big:
            r = self.app.icon_big.get_rect(center=(WIDTH // 2, 390))
            s.blit(self.app.icon_big, r)
        self.buttons = []
        bw, gap = 230, 30
        x0 = (WIDTH - (bw * 2 + gap)) // 2
        y = HEIGHT - 100
        nb = pygame.Rect(x0, y, bw, 54)
        mb = pygame.Rect(x0 + bw + gap, y, bw, 54)
        round_rect(s, nb, ACCENT, 12)
        draw_text(s, t("Opnieuw spelen"), nb.centerx, nb.centery, 25, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        round_rect(s, mb, PANEL2, 12); round_rect(s, mb, LINE, 12, 2)
        draw_text(s, t("Hoofdmenu"), mb.centerx, mb.centery, 25, TEXT, center=True, bold=True)
        self.buttons.append((nb, self.app.start_game))
        self.buttons.append((mb, lambda: self.app.set_state(TitleState(self.app))))


class GameOverState(State):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = []
        sfx.play("defeat")

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.start_game()
            elif e.key == pygame.K_ESCAPE:
                self.app.set_state(TitleState(self.app))

    def draw(self, s):
        s.fill((10, 8, 10))
        draw_text(s, t("Spel voorbij"), WIDTH // 2, 170, 72, RED, center=True, bold=True)
        draw_text(s, t("Je bent gevallen..."), WIDTH // 2, 245, 28, MUTED, center=True)
        draw_text(s, t("Score") + f": {self.app.score}", WIDTH // 2, 305, 32,
                  ACCENT, center=True, bold=True)
        sub = t("Beste") + f": {self.app.highscore}"
        if self.app.endless:
            sub += "   " + t("Diepte") + f": {self.app.depth}"
        draw_text(s, sub, WIDTH // 2, 348, 24, GOLD, center=True)
        self.buttons = []
        bw, gap = 230, 30
        x0 = (WIDTH - (bw * 2 + gap)) // 2
        y = HEIGHT - 110
        nb = pygame.Rect(x0, y, bw, 54)
        mb = pygame.Rect(x0 + bw + gap, y, bw, 54)
        round_rect(s, nb, ACCENT, 12)
        draw_text(s, t("Opnieuw spelen"), nb.centerx, nb.centery, 25, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        round_rect(s, mb, PANEL2, 12); round_rect(s, mb, LINE, 12, 2)
        draw_text(s, t("Hoofdmenu"), mb.centerx, mb.centery, 25, TEXT, center=True, bold=True)
        self.buttons.append((nb, self.app.start_game if not self.app.endless
                             else self.app.start_endless))
        self.buttons.append((mb, lambda: self.app.set_state(TitleState(self.app))))


# ---------------------------------------------------------------- app
class App:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(APP_NAME)
        pygame.key.set_repeat(0)
        self.clock = pygame.time.Clock()
        self.running = True
        self.cfg = load_config()
        set_lang(self.cfg.get("lang") or detect_lang())
        sfx.init(enabled=bool(self.cfg.get("sound", True)),
                 volume=float(self.cfg.get("sound_vol", 0.6)))
        icon = load_icon()
        if icon:
            pygame.display.set_icon(icon)
            self.icon_big = pygame.transform.smoothscale(icon, (150, 150))
            self.splash_logo = pygame.transform.smoothscale(icon, (240, 240))
        else:
            self.icon_big = None
            self.splash_logo = None
        roles_cfg = self.cfg.get("roles", {}) if isinstance(self.cfg.get("roles"), dict) else {}
        tts.start(enabled=bool(self.cfg.get("voice", False)), roles_cfg=roles_cfg)
        self.levels = make_levels()
        self.score = 0
        self.highscore = int(self.cfg.get("highscore", 0))
        self.best_depth = int(self.cfg.get("best_depth", 0))
        self.endless = False
        self.run_double = False
        self.depth = 0
        self.state = SplashState(self)

    def start_game(self):
        self.score = 0
        self.run_double = False
        self.endless = False
        self.depth = 0
        self.levels = make_levels()
        sfx.start_music()
        self.set_state(PlayState(self, 0))

    def start_endless(self):
        self.score = 0
        self.run_double = False
        self.endless = True
        self.depth = 0
        self.levels = [make_endless_level(0)]
        sfx.start_music()
        self.set_state(PlayState(self, 0))

    def _update_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
        self.cfg["highscore"] = self.highscore
        if self.endless and self.depth > self.best_depth:
            self.best_depth = self.depth
            self.cfg["best_depth"] = self.best_depth
        save_config(self.cfg)

    def win_level(self, idx):
        if self.endless:
            self.depth += 1
            self._update_highscore()
            self.levels.append(make_endless_level(self.depth))
            self.set_state(LevelCompleteState(self, idx))
        elif idx + 1 < len(self.levels) and not self.levels[idx]["boss"]:
            self.set_state(LevelCompleteState(self, idx))
        else:
            self._update_highscore()
            self.set_state(VictoryState(self))

    def end_run(self, won):
        self._update_highscore()
        self.set_state(GameOverState(self))

    def toggle_lang(self):
        set_lang("en" if LANG == "nl" else "nl")
        self.cfg["lang"] = LANG
        save_config(self.cfg)

    def toggle_voice(self):
        on = not tts.is_enabled()
        tts.set_enabled(on)
        self.cfg["voice"] = on
        save_config(self.cfg)

    def quit(self):
        self.running = False

    def set_state(self, st):
        self.state = st

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle(e)
            self.state.update(dt)
            sfx.update()
            self.state.draw(self.screen)
            pygame.display.flip()
        tts.stop()
        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()

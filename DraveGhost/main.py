# -*- coding: utf-8 -*-
"""DraveGhost - a ghost-catching arcade game (pygame).

Inspired by the classic 1984 Ghostbusters home-computer game, but with original
graphics and naming. The language follows the PC (Dutch or English) automatically.

Speel/Play:
  - City: arrow keys to drive; reach a haunted (glowing) building and press SPACE
    to start a catch.
  - Catch: move the trap left/right (arrows), hold SPACE to pull the ghost down
    into the trap. Fill the capture bar to catch it.
"""
import array
import locale
import math
import os
import random
import sys
import threading
import webbrowser

import pygame

# ---------------------------------------------------------------------------
# taal volgt de pc  /  language follows the PC
# ---------------------------------------------------------------------------
def _detect_lang():
    code = ""
    try:
        code = (locale.getdefaultlocale()[0] or "")
    except Exception:
        code = ""
    return "nl" if code.lower().startswith("nl") else "en"


LANG = _detect_lang()

TXT = {
    "sub": {"nl": "Spokenjagers", "en": "Ghost Catchers"},
    "start": {"nl": "Druk op SPATIE om te starten", "en": "Press SPACE to start"},
    "city_help": {"nl": "Pijltjes = rijden   SPATIE bij oplichtend gebouw = vangen   P = pauze",
                  "en": "Arrows = drive   SPACE at a glowing building = bust   P = pause"},
    "catch_help": {"nl": "Pijltjes = val bewegen    SPATIE (vasthouden) = geest naar beneden trekken",
                   "en": "Arrows = move trap    Hold SPACE = pull the ghost down"},
    "money": {"nl": "Geld", "en": "Money"},
    "caught": {"nl": "Gevangen", "en": "Caught"},
    "haunting": {"nl": "Spookkracht", "en": "Haunting"},
    "caught_one": {"nl": "Gevangen! +", "en": "Caught! +"},
    "escaped": {"nl": "Ontsnapt!", "en": "Escaped!"},
    "gameover": {"nl": "De stad is overspoeld door spoken!",
                 "en": "The city is overrun by ghosts!"},
    "restart": {"nl": "Druk op R om opnieuw te spelen", "en": "Press R to play again"},
    "time": {"nl": "Tijd", "en": "Time"},
    "capture": {"nl": "Vangst", "en": "Capture"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "shop_title": {"nl": "Uitrusting", "en": "Equipment"},
    "buy_trap": {"nl": "[T] Koop een val", "en": "[T] Buy a trap"},
    "refuel": {"nl": "[B] Tank helemaal bij", "en": "[F] Refuel to full"},
    "rollout": {"nl": "[Enter] De stad in!", "en": "[Enter] Roll out!"},
    "traps": {"nl": "Vallen", "en": "Traps"},
    "fuel": {"nl": "Brandstof", "en": "Fuel"},
    "hq": {"nl": "HK", "en": "HQ"},
    "no_traps": {"nl": "Geen vallen! Ga terug naar het HK (blauw).",
                 "en": "No traps! Return to HQ (blue)."},
    "shop_hint": {"nl": "Rijd naar het blauwe HK om bij te kopen.",
                  "en": "Drive to the blue HQ to restock."},
    "low_fuel": {"nl": "Brandstof bijna op!", "en": "Low fuel!"},
    "no_money": {"nl": "Niet genoeg geld", "en": "Not enough money"},
    "shop_keys": {"nl": "T = val   B = tanken   C = auto   Enter = de stad in",
                  "en": "T = trap   F = refuel   C = car   Enter = roll out"},
    "buy_car": {"nl": "[C] Auto-upgrade", "en": "[C] Car upgrade"},
    "car": {"nl": "Auto", "en": "Car"},
    "maxed": {"nl": "max", "en": "max"},
    "paused": {"nl": "GEPAUZEERD", "en": "PAUSED"},
    "resume": {"nl": "P = verder spelen", "en": "P = resume"},
    "sound": {"nl": "Geluid", "en": "Sound"},
    "off": {"nl": "uit", "en": "off"},
    "audio_hint": {"nl": "M = geluid aan/uit    - / + = volume",
                   "en": "M = sound on/off    - / + = volume"},
    "info_hint": {"nl": "I = info / donatie", "en": "I = info / donate"},
    "info_title": {"nl": "Over DraveGhost", "en": "About DraveGhost"},
    "donationware": {"nl": "Donationware - gratis te spelen.",
                     "en": "Donationware - free to play."},
    "donate_line": {"nl": "Bevalt het spel? Een donatie wordt gewaardeerd:",
                    "en": "Enjoying the game? A donation is appreciated:"},
    "donate_click": {"nl": "(klik op de link of druk op D)",
                     "en": "(click the link or press D)"},
    "contact_lbl": {"nl": "Contact", "en": "Contact"},
    "back_any": {"nl": "Druk op een toets om terug te gaan",
                 "en": "Press any key to go back"},
}


def T(key):
    d = TXT.get(key, {})
    return d.get(LANG) or d.get("en") or key


# ---------------------------------------------------------------------------
# instellingen
# ---------------------------------------------------------------------------
W, H = 960, 640
HUD = 56
FPS = 60

BG = (12, 14, 26)
ROAD = (24, 26, 38)
BUILD = (40, 46, 66)
BUILD_TOP = (54, 62, 88)
HAUNT = (84, 60, 120)
GHOST = (210, 240, 230)
GHOST_DK = (150, 190, 180)
AMBER = (240, 200, 60)
RED = (220, 70, 60)
BLUE = (90, 170, 230)
GREEN = (110, 210, 150)
TEXT = (235, 240, 250)
SUB = (150, 165, 190)

# verschillende soorten spoken: kleur, snelheid, grilligheid, beloning, vangsnelheid
GHOST_TYPES = [
    {"nl": "dwaallicht", "en": "wisp", "vorm": "wisp", "kleur": (215, 240, 232),
     "speed": 0.9, "wander": 0.9, "rmin": 600, "rmax": 1200, "cap": 1.15},
    {"nl": "slijmgeest", "en": "slime", "vorm": "blob", "kleur": (150, 220, 120),
     "speed": 1.05, "wander": 1.7, "rmin": 1000, "rmax": 1800, "cap": 1.0},
    {"nl": "schim", "en": "phantom", "vorm": "tall", "kleur": (120, 185, 245),
     "speed": 1.5, "wander": 1.2, "rmin": 1500, "rmax": 2600, "cap": 0.9},
    {"nl": "boze geest", "en": "wraith", "vorm": "wraith", "kleur": (235, 110, 92),
     "speed": 1.3, "wander": 2.1, "rmin": 2200, "rmax": 3600, "cap": 0.8},
]

CITY_COLS, CITY_ROWS = 5, 3
CITY_MARGIN, CITY_GAP = 46, 44
LANE = (122, 112, 70)        # kleur van de rijstrepen

# verschillende gebouwstijlen: muur, daklijst, raamlicht
BUILDING_PALETTES = [
    ((46, 52, 74), (62, 70, 98), (246, 201, 60)),
    ((40, 46, 66), (54, 62, 88), (120, 200, 255)),
    ((58, 48, 66), (78, 66, 90), (255, 170, 120)),
    ((44, 58, 60), (58, 78, 80), (150, 230, 180)),
    ((54, 50, 58), (72, 68, 78), (255, 230, 150)),
]

# ---------------------------------------------------------------------------
# geluid: tonen/melodieën zelf opwekken (geen losse bestanden nodig)
# ---------------------------------------------------------------------------
AUDIO_SR = 22050


def _env(i, n, sr, atk=0.01, rel=0.06):
    a = min(1.0, i / max(1, atk * sr))
    r = min(1.0, (n - i) / max(1, rel * sr))
    return min(a, r)


def _tone(freq, ms, vol=0.5, wave="sine"):
    sr = AUDIO_SR
    n = int(sr * ms / 1000)
    out = array.array("h")
    amp = 30000 * vol
    tp = 2 * math.pi
    for i in range(n):
        ph = (i * freq / sr) % 1.0
        if wave == "square":
            v = 1.0 if ph < 0.5 else -1.0
        elif wave == "saw":
            v = 2 * ph - 1
        elif wave == "tri":
            v = 4 * abs(ph - 0.5) - 1
        else:
            v = math.sin(tp * ph)
        out.append(int(v * amp * _env(i, n, sr)))
    return out


def _sweep(f0, f1, ms, vol=0.5, wave="saw"):
    sr = AUDIO_SR
    n = int(sr * ms / 1000)
    out = array.array("h")
    amp = 30000 * vol
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / max(1, n))
        ph = (ph + f / sr) % 1.0
        v = (2 * ph - 1) if wave == "saw" else math.sin(2 * math.pi * ph)
        out.append(int(v * amp * _env(i, n, sr, 0.005, 0.08)))
    return out


def _melody(notes, vol=0.4, wave="square"):
    out = array.array("h")
    for f, ms in notes:
        out.extend(_tone(f, ms, vol if f > 0 else 0.0, wave) if f > 0
                   else _tone(1, ms, 0.0))
    return out


def _mix(a, b):
    n = max(len(a), len(b))
    out = array.array("h", bytes(2 * n))
    for i in range(len(a)):
        out[i] = a[i]
    for i in range(len(b)):
        s = out[i] + b[i]
        out[i] = 32767 if s > 32767 else (-32768 if s < -32768 else s)
    return out


def _track(bars, bpm, lead_wave="tri", lead_vol=0.34, bass_vol=0.26):
    """bars: lijst van (bas-frequentie, [(toon, tellen), ...]) -> melodie + bas."""
    beat = 60000.0 / bpm
    lead = array.array("h")
    bass = array.array("h")
    for root, notes in bars:
        bb = 0
        for f, beats in notes:
            bb += beats
            lead.extend(_tone(f, beat * beats, lead_vol, lead_wave) if f > 0
                        else _tone(1, beat * beats, 0.0))
        bass.extend(_tone(root, beat * bb, bass_vol, "sine") if root > 0
                    else _tone(1, beat * bb, 0.0))
    return _mix(lead, bass)


BTYPES = ["appartement", "kantoor", "winkel", "fabriek"]

MENU, SHOP, CITY, CATCH, OVER, INFO = (
    "menu", "shop", "city", "catch", "over", "info")
DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

TRAP_PRICE = 1500
FUEL_PRICE = 500
START_MONEY = 10000
CAR_PRICE = 3000        # kosten = CAR_PRICE * huidig niveau
CAR_MAX = 3


# ---------------------------------------------------------------------------
# hulp: tekenen
# ---------------------------------------------------------------------------
def draw_ghost(surf, cx, cy, r, wob=0.0, color=GHOST):
    body = pygame.Surface((r * 2 + 4, r * 2 + 8), pygame.SRCALPHA)
    bx, by = body.get_width() / 2, r + 2
    pygame.draw.circle(body, color, (bx, by), r)
    pygame.draw.rect(body, color, (bx - r, by, r * 2, r))
    # onderkant golfjes
    n = 4
    for i in range(n):
        wx = bx - r + (i + 0.5) * (2 * r / n)
        off = 3 * math.sin(wob + i)
        pygame.draw.circle(body, color, (int(wx), int(by + r + off)), int(r / n))
    # ogen
    eo = r * 0.35
    pygame.draw.circle(body, (30, 40, 60), (int(bx - eo), int(by - r * 0.1)), max(2, int(r * 0.16)))
    pygame.draw.circle(body, (30, 40, 60), (int(bx + eo), int(by - r * 0.1)), max(2, int(r * 0.16)))
    surf.blit(body, (cx - body.get_width() / 2, cy - by))


def _eyes(s, bx, by, r, ex=0.35, ey=-0.1, white=False):
    er = max(2, int(r * 0.17))
    for sx in (-1, 1):
        cxx, cyy = int(bx + sx * r * ex), int(by + r * ey)
        if white:
            pygame.draw.circle(s, (255, 255, 255), (cxx, cyy), er + 2)
        pygame.draw.circle(s, (30, 40, 55), (cxx, cyy), er)


def _ghost_blob(surf, cx, cy, r, t, color):
    """Slijmgeest: dikke, lompe bol met een grote mond."""
    sz = int(r * 3.2)
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    bx, by = sz / 2, sz / 2
    pygame.draw.circle(s, color, (int(bx), int(by)), int(r))
    for i, (ox, oy, rr) in enumerate([(-0.7, 0.05, 0.5), (0.7, 0.05, 0.5),
                                      (0.0, 0.65, 0.6), (-0.35, -0.55, 0.45),
                                      (0.45, -0.5, 0.42)]):
        wob = 1 + 0.07 * math.sin(t + i)
        pygame.draw.circle(s, color, (int(bx + ox * r), int(by + oy * r)),
                           int(rr * r * wob))
    pygame.draw.ellipse(s, (28, 38, 36),
                        (bx - r * 0.5, by + r * 0.05, r, r * 0.75))
    _eyes(s, bx, by, r, ex=0.38, ey=-0.4, white=True)
    surf.blit(s, (cx - bx, cy - by))


def _ghost_tall(surf, cx, cy, r, t, color):
    """Schim: lang en ijl met een wapperende staart."""
    s = pygame.Surface((int(r * 3), int(r * 4.4)), pygame.SRCALPHA)
    bx, by = s.get_width() / 2, r * 1.1
    col = (color[0], color[1], color[2], 215)
    pts = [(bx - r * 0.85, by)]
    for k in range(1, 10):
        f = k / 9.0
        w = r * 0.85 * (1 - 0.78 * f)
        sway = math.sin(t * 3 + f * 6) * r * 0.5 * f
        pts.append((bx - w + sway, by + f * r * 3.0))
    for k in range(9, 0, -1):
        f = k / 9.0
        w = r * 0.85 * (1 - 0.78 * f)
        sway = math.sin(t * 3 + f * 6) * r * 0.5 * f
        pts.append((bx + w + sway, by + f * r * 3.0))
    pygame.draw.polygon(s, col, pts)
    pygame.draw.circle(s, col, (int(bx), int(by)), int(r * 0.9))
    for sx in (-1, 1):
        pygame.draw.ellipse(s, (18, 26, 42),
                            (bx + sx * r * 0.42 - r * 0.12, by - r * 0.25,
                             r * 0.24, r * 0.45))
    surf.blit(s, (cx - bx, cy - by))


def _ghost_wraith(surf, cx, cy, r, t, color):
    """Boze geest: puntige kap, gekartelde onderkant, boze wenkbrauwen."""
    sz = int(r * 3.4)
    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
    bx, by = sz / 2, sz / 2
    pygame.draw.polygon(s, color, [(bx, by - r * 1.5), (bx - r, by),
                                   (bx + r, by)])
    base = by + r * 1.0
    spikes = [(bx - r, by)]
    seg = 6
    for i in range(seg + 1):
        x = bx - r + i * (2 * r / seg)
        y = base + (r * 0.5 if i % 2 else 0)
        spikes.append((x, y))
    spikes.append((bx + r, by))
    pygame.draw.polygon(s, color, spikes)
    for sx in (-1, 1):
        pygame.draw.circle(s, (255, 240, 210),
                           (int(bx + sx * r * 0.42), int(by + r * 0.12)),
                           int(r * 0.2))
        pygame.draw.circle(s, (130, 25, 22),
                           (int(bx + sx * r * 0.42), int(by + r * 0.14)),
                           int(r * 0.1))
    bw = max(2, int(r * 0.13))
    pygame.draw.line(s, (130, 25, 22), (bx - r * 0.7, by - r * 0.18),
                     (bx - r * 0.12, by + r * 0.04), bw)
    pygame.draw.line(s, (130, 25, 22), (bx + r * 0.7, by - r * 0.18),
                     (bx + r * 0.12, by + r * 0.04), bw)
    surf.blit(s, (cx - bx, cy - by))


def draw_ghost_shape(surf, cx, cy, r, t, color, vorm):
    if vorm == "blob":
        _ghost_blob(surf, cx, cy, r, t, color)
    elif vorm == "tall":
        _ghost_tall(surf, cx, cy, r, t, color)
    elif vorm == "wraith":
        _ghost_wraith(surf, cx, cy, r, t, color)
    else:
        draw_ghost(surf, cx, cy, r, t, color)


def draw_no_ghost(surf, cx, cy, r, wob=0.0):
    """Ons 'no-ghost' logo: spookje in een rode verbodscirkel met streep."""
    draw_ghost(surf, cx, cy + r * 0.08, r * 0.62, wob)
    wdt = max(4, int(r * 0.12))
    pygame.draw.circle(surf, RED, (int(cx), int(cy)), int(r), wdt)
    a = math.radians(45)
    dx, dy = math.cos(a) * r, math.sin(a) * r
    pygame.draw.line(surf, RED, (cx - dx, cy - dy), (cx + dx, cy + dy), wdt)


def draw_beam(surf, x1, y1, x2, y2, t):
    """Een kronkelende protonstraal van (x1,y1) naar (x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    px, py = -uy, ux                      # loodrecht op de straal
    n = max(8, int(L / 10))
    glow = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    for amp, phase, col, wdt, target in (
            (16, 0.0, (90, 170, 235, 90), 11, glow),
            (11, 1.3, (150, 210, 255), 5, surf),
            (7, 2.6, (225, 245, 255), 2, surf)):
        pts = []
        for i in range(n + 1):
            f = i / n
            a = amp * math.sin(phase + t * 16 + f * 18) * (0.25 + 0.75 * f)
            pts.append((x1 + ux * L * f + px * a, y1 + uy * L * f + py * a))
        pygame.draw.lines(target, col, False, pts, wdt)
    surf.blit(glow, (0, 0))


def draw_trap_beam(surf, tx, base_y, gx, gy, t):
    """Vasthoudstraal: een lichtkolom uit de val omhoog naar de geest."""
    if base_y - gy <= 4:
        return
    puls = 0.55 + 0.45 * math.sin(t * 12)
    col = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    pygame.draw.polygon(col, (255, 225, 120, int(70 * puls)),
                        [(tx - 32, base_y), (tx + 32, base_y),
                         (gx + 20, gy), (gx - 20, gy)])
    pygame.draw.polygon(col, (255, 250, 225, int(120 * puls)),
                        [(tx - 12, base_y), (tx + 12, base_y),
                         (gx + 8, gy), (gx - 8, gy)])
    surf.blit(col, (0, 0))


def draw_car(surf, cx, cy):
    pygame.draw.rect(surf, (235, 235, 240), (cx - 16, cy - 10, 32, 20), border_radius=5)
    pygame.draw.rect(surf, (40, 50, 70), (cx - 10, cy - 7, 20, 14), border_radius=3)
    pygame.draw.circle(surf, RED, (cx + 14, cy - 6), 2)
    pygame.draw.circle(surf, RED, (cx + 14, cy + 6), 2)
    # rooflamp
    pygame.draw.rect(surf, BLUE, (cx - 4, cy - 13, 8, 4), border_radius=2)


def draw_buster(surf, x, y, face):
    """Een ghostbuster-figuurtje; voeten op y, face=+1 kijkt rechts, -1 links.
    Geeft de positie van de wand-tip terug (begin van de straal)."""
    suit = (206, 188, 150)
    # benen
    pygame.draw.rect(surf, (40, 44, 60), (x - 7, y - 20, 6, 20))
    pygame.draw.rect(surf, (40, 44, 60), (x + 1, y - 20, 6, 20))
    # proton-pack op de rug
    pygame.draw.rect(surf, (70, 74, 86), (int(x - 15 * face), y - 44, 10, 22),
                     border_radius=3)
    pygame.draw.circle(surf, (120, 200, 255), (int(x - 10 * face), y - 40), 2)
    # romp
    pygame.draw.rect(surf, suit, (x - 9, y - 44, 18, 26), border_radius=4)
    # hoofd
    pygame.draw.circle(surf, (225, 205, 170), (int(x), y - 52), 7)
    # arm + wand richting het midden
    tip = (int(x + 16 * face), y - 38)
    pygame.draw.line(surf, (60, 64, 80), (int(x + 6 * face), y - 36), tip, 4)
    pygame.draw.circle(surf, (150, 210, 255), tip, 3)
    return tip


# ---------------------------------------------------------------------------
# stad
# ---------------------------------------------------------------------------
def draw_screamer(surf, x, y, t):
    """Een figuurtje dat met de armen omhoog uit een raam schreeuwt."""
    bob = math.sin(t * 9) * 2
    yy = y + bob
    pygame.draw.rect(surf, (200, 90, 90), (x - 5, yy + 6, 10, 12), border_radius=2)
    pygame.draw.circle(surf, (235, 205, 170), (int(x), int(yy)), 6)
    pygame.draw.ellipse(surf, (40, 18, 18), (x - 2, yy + 1, 4, 5))   # open mond
    pygame.draw.line(surf, (235, 205, 170), (x - 5, yy + 8), (x - 11, yy - 4), 2)
    pygame.draw.line(surf, (235, 205, 170), (x + 5, yy + 8), (x + 11, yy - 4), 2)


def draw_catch_backdrop(surf):
    """Straat met gebouwen als achtergrond voor het vangscherm."""
    surf.fill((14, 17, 30))
    bw = 74
    x, i = 0, 0
    while x < W:
        h = 120 + (i * 53) % 150
        top = H - 90 - h
        pal = BUILDING_PALETTES[i % len(BUILDING_PALETTES)]
        wall = tuple(int(c * 0.6) for c in pal[0])
        pygame.draw.rect(surf, wall, (x, top, bw - 6, h))
        for ry in range(top + 12, H - 100, 22):
            for rx in range(x + 8, x + bw - 14, 16):
                if ((rx * 3 + ry * 5 + i * 7) // 11) % 4 == 0:
                    pygame.draw.rect(surf, pal[2], (rx, ry, 6, 9))
        x += bw
        i += 1
    pygame.draw.rect(surf, (24, 26, 38), (0, H - 90, W, 90))      # straat


class Building:
    def __init__(self, rect):
        self.rect = rect
        self.haunted = False
        self.timer = 0.0
        self.gtype = 0          # welk soort spook hier hangt
        self.style = 0          # uiterlijk (kleur/ramen)
        self.roof = 0           # dakdetail
        self.btype = "appartement"   # gebouwtype (een ervan wordt het hotel)


def build_city():
    cols, rows = CITY_COLS, CITY_ROWS
    margin, gap = CITY_MARGIN, CITY_GAP
    area_w = W - 2 * margin
    area_h = (H - HUD) - 2 * margin
    bw = (area_w - (cols - 1) * gap) / cols
    bh = (area_h - (rows - 1) * gap) / rows
    builds = []
    for r in range(rows):
        for c in range(cols):
            x = margin + c * (bw + gap)
            y = HUD + margin + r * (bh + gap)
            b = Building(pygame.Rect(int(x), int(y), int(bw), int(bh)))
            b.style = random.randrange(len(BUILDING_PALETTES))
            b.roof = random.randrange(3)
            b.btype = random.choice(BTYPES)
            builds.append(b)
    # één gebouw wordt het hotel (niet het middelste, dat is het hoofdkwartier)
    mid = len(builds) // 2
    keuzes = [i for i in range(len(builds)) if i != mid]
    builds[random.choice(keuzes)].btype = "hotel"
    return builds


# ---------------------------------------------------------------------------
# de game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(AUDIO_SR, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        pygame.display.set_caption("DraveGhost")
        self.screen = pygame.display.set_mode((W, H))
        try:
            _ic = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "assets", "icon-64.png")
            if os.path.exists(_ic):
                pygame.display.set_icon(pygame.image.load(_ic))
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 22)
        self.big = pygame.font.SysFont("Segoe UI", 54, bold=True)
        self.mid = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.small = pygame.font.SysFont("Segoe UI", 16)
        self.volume = 0.6
        self.muted = False
        self.link_rects = []
        self._init_audio()
        self.state = MENU
        self.reset()

    def reset(self):
        self.money = START_MONEY
        self.caught = 0
        self.haunting = 0.0
        self.traps = 0
        self.car_level = 1
        self.fuel_max = 100.0
        self.fuel = self.fuel_max
        self.builds = build_city()
        self.hq = self.builds[len(self.builds) // 2]   # middelste = hoofdkwartier
        self.car = [W / 2, (H + HUD) / 2]
        self.spawn_t = 2.0
        self.msg = ""
        self.msg_t = 0.0
        self.active_b = None
        self.paused = False

    # ---- geluid ----
    def _init_audio(self):
        self.audio = False
        self.snd = {}
        self.music = []
        self.mch = None
        self.bch = None
        self.beaming = False
        self._music_kind = None
        self._mi = -1
        try:
            cur = pygame.mixer.get_init()
            if not cur:
                pygame.mixer.init(AUDIO_SR, -16, 1, 512)
            elif cur[0] != AUDIO_SR or cur[2] != 1:
                pygame.mixer.quit()
                pygame.mixer.init(AUDIO_SR, -16, 1, 512)
            pygame.mixer.set_num_channels(8)
            self.mch = pygame.mixer.Channel(0)
            self.bch = pygame.mixer.Channel(1)
            self.snd["bust"] = self._snd(_melody([(330, 60), (494, 90)], 0.5, "square"))
            self.snd["catch"] = self._snd(_melody(
                [(392, 70), (523, 70), (659, 150)], 0.5, "square"))
            self.snd["escape"] = self._snd(_sweep(700, 170, 420, 0.5, "saw"))
            self.snd["struggle"] = self._snd(_tone(110, 120, 0.5, "square"))
            self.snd["beam"] = self._snd(_tone(120, 200, 0.32, "saw"))
            self.catch_music = None
            self.audio = True
            self._apply_volume()
            # muziek op de achtergrond opwekken zodat het spel meteen start
            threading.Thread(target=self._build_music, daemon=True).start()
        except Exception:
            self.audio = False

    def _build_music(self):
        """Wek de melodieën op (melodie + bas). Drie verschillende deuntjes."""
        try:
            # A mineur, rustig en eerie (stad 1)
            barsA = [
                (110, [(440, 1), (523, 1), (494, 1), (392, 1)]),
                (175, [(440, 2), (349, 2)]),
                (131, [(330, 1), (392, 1), (523, 1), (494, 1)]),
                (165, [(330, 2), (294, 1), (0, 1)]),
                (110, [(523, 1), (494, 1), (440, 1), (392, 1)]),
                (196, [(392, 1), (494, 1), (587, 1), (494, 1)]),
                (175, [(349, 2), (440, 2)]),
                (110, [(440, 2), (0, 2)]),
            ]
            # andere wending (stad 2)
            barsB = [
                (147, [(587, 1), (523, 1), (440, 1), (523, 1)]),
                (110, [(440, 2), (330, 2)]),
                (175, [(349, 1), (440, 1), (349, 1), (294, 1)]),
                (196, [(392, 2), (0, 2)]),
                (147, [(440, 1), (523, 1), (587, 1), (523, 1)]),
                (110, [(440, 2), (349, 2)]),
                (131, [(523, 1), (494, 1), (392, 1), (330, 1)]),
                (147, [(294, 2), (0, 2)]),
            ]
            # spanning tijdens het vangen (sneller)
            barsC = [
                (110, [(440, .5), (330, .5), (440, .5), (523, .5),
                       (494, .5), (392, .5), (494, .5), (587, .5)]),
                (175, [(349, .5), (440, .5), (349, .5), (523, .5),
                       (440, .5), (349, .5), (294, .5), (349, .5)]),
                (110, [(440, .5), (330, .5), (440, .5), (523, .5),
                       (494, .5), (392, .5), (494, .5), (659, .5)]),
                (165, [(330, .5), (392, .5), (494, .5), (392, .5), (330, 1), (0, 1)]),
            ]
            t0 = _track(barsA, 116, "tri")
            t1 = _track(barsB, 116, "tri")
            t2 = _track(barsC, 150, "square", 0.30)
            self.catch_music = self._snd(t2)
            self.music = [self._snd(t0), self._snd(t1)]
        except Exception:
            pass

    def _snd(self, arr):
        return pygame.mixer.Sound(buffer=arr.tobytes())

    def _apply_volume(self):
        if not self.audio:
            return
        mv = 0.0 if self.muted else self.volume
        try:
            if self.mch:
                self.mch.set_volume(mv * 0.5)
            if self.bch:
                self.bch.set_volume(mv * 0.6)
            for s in self.snd.values():
                s.set_volume(mv)
        except Exception:
            pass

    def _set_music(self, kind):
        if not self.audio or kind == self._music_kind:
            return
        try:
            if kind == "catch":
                snd = self.catch_music
            else:
                if not self.music:
                    return                 # nog niet klaar; volgende frame opnieuw
                self._mi = (self._mi + 1) % len(self.music)
                snd = self.music[self._mi]
            if snd is None:
                return
            self.mch.play(snd, loops=-1)
            self._apply_volume()
            self._music_kind = kind        # pas markeren als het écht speelt
        except Exception:
            pass

    def play_sfx(self, name):
        if self.audio and not self.muted and name in self.snd:
            try:
                self.snd[name].play()
            except Exception:
                pass

    def _beam(self, on):
        if not self.audio:
            return
        try:
            if on and not self.beaming:
                self.beaming = True
                self.bch.play(self.snd["beam"], loops=-1)
            elif not on and self.beaming:
                self.beaming = False
                self.bch.stop()
        except Exception:
            pass

    def set_volume(self, d):
        self.volume = max(0.0, min(1.0, round(self.volume + d, 2)))
        self.muted = False
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self._beam(False)
        self._apply_volume()

    # ---- stad ----
    def update_city(self, dt, keys):
        sp = (240 + 60 * (self.car_level - 1)) * dt    # snellere auto bij upgrade
        if self.fuel <= 0:
            sp *= 0.4                       # bijna geen brandstof: hij sukkelt
        moving = False
        if keys[pygame.K_LEFT]:
            self.car[0] -= sp; moving = True
        if keys[pygame.K_RIGHT]:
            self.car[0] += sp; moving = True
        if keys[pygame.K_UP]:
            self.car[1] -= sp; moving = True
        if keys[pygame.K_DOWN]:
            self.car[1] += sp; moving = True
        self.car[0] = max(16, min(W - 16, self.car[0]))
        self.car[1] = max(HUD + 12, min(H - 12, self.car[1]))
        if moving:
            self.fuel = max(0.0, self.fuel - 2.6 * dt)

        # spook spawnen (nooit op het hoofdkwartier)
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = random.uniform(3.5, 6.5)
            vrij = [b for b in self.builds if not b.haunted and b is not self.hq]
            if vrij and sum(1 for b in self.builds if b.haunted) < 5:
                nb = random.choice(vrij)
                nb.haunted = True
                nb.gtype = random.randrange(len(GHOST_TYPES))

        # haunting loopt op zolang er spoken zijn
        n = sum(1 for b in self.builds if b.haunted)
        self.haunting = min(100.0, self.haunting + n * 3.2 * dt)
        if self.haunting >= 100.0:
            self.state = OVER
            return

    def try_bust(self):
        car = pygame.Rect(self.car[0] - 16, self.car[1] - 10, 32, 20)
        if car.colliderect(self.hq.rect):
            self.state = SHOP                 # bij het HK: winkel openen
            return
        for b in self.builds:
            if b.haunted and car.colliderect(b.rect):
                if self.traps <= 0:
                    self.msg = T("no_traps")
                    self.msg_t = 2.2
                    return
                self.active_b = b
                self.play_sfx("bust")
                self.start_catch()
                return

    def draw_city(self):
        s = self.screen
        s.fill(ROAD)
        t = pygame.time.get_ticks() / 1000.0
        # straten met rijstrepen tussen de gebouwen
        cols, rows = CITY_COLS, CITY_ROWS
        for c in range(cols - 1):
            x = (self.builds[c].rect.right + self.builds[c + 1].rect.left) / 2
            yy = HUD + 4
            while yy < H:
                pygame.draw.line(s, LANE, (x, yy), (x, yy + 12), 3)
                yy += 26
        for r in range(rows - 1):
            y = (self.builds[r * cols].rect.bottom
                 + self.builds[(r + 1) * cols].rect.top) / 2
            xx = 4
            while xx < W:
                pygame.draw.line(s, LANE, (xx, y), (xx + 12, y), 3)
                xx += 26
        for b in self.builds:
            if b is self.hq:
                pygame.draw.rect(s, (38, 66, 116), b.rect, border_radius=4)
                pygame.draw.rect(s, (70, 120, 190),
                                 (b.rect.x, b.rect.y, b.rect.w, 10), border_radius=4)
                lab = self.mid.render(T("hq"), True, (205, 228, 255))
                s.blit(lab, (b.rect.centerx - lab.get_width() / 2,
                             b.rect.centery - lab.get_height() / 2))
                continue
            pal = BUILDING_PALETTES[b.style]
            pygame.draw.rect(s, pal[0], b.rect, border_radius=4)
            pygame.draw.rect(s, pal[1], (b.rect.x, b.rect.y, b.rect.w, 10),
                             border_radius=4)
            # ramen
            for ry in range(b.rect.y + 18, b.rect.bottom - 8, 20):
                for rx in range(b.rect.x + 10, b.rect.right - 8, 18):
                    on = ((rx * 3 + ry * 5 + b.style * 7) // 13) % 3 == 0
                    pygame.draw.rect(s, (pal[2] if on else (24, 28, 42)),
                                     (rx, ry, 8, 10))
            # dakdetail
            if b.roof == 1:
                pygame.draw.rect(s, (70, 74, 86),
                                 (b.rect.centerx - 9, b.rect.y - 8, 18, 8))
            elif b.roof == 2:
                pygame.draw.line(s, (95, 99, 116), (b.rect.centerx, b.rect.y),
                                 (b.rect.centerx, b.rect.y - 14), 2)
                pygame.draw.circle(s, RED, (b.rect.centerx, b.rect.y - 14), 2)
            if b.btype == "hotel":
                sg = pygame.Rect(b.rect.x + 6, b.rect.y + 4, b.rect.w - 12, 18)
                pygame.draw.rect(s, (185, 40, 40), sg, border_radius=4)
                ht = self.small.render("HOTEL", True, (255, 240, 200))
                s.blit(ht, (sg.centerx - ht.get_width() / 2, sg.y + 1))
            if b.haunted:
                glow = 120 + int(80 * math.sin(t * 4))
                pygame.draw.rect(s, (glow, 80, glow), b.rect, width=3, border_radius=4)
                gtp = GHOST_TYPES[b.gtype]
                draw_ghost_shape(s, b.rect.centerx, b.rect.y - 4, 13, t * 4,
                                 gtp["kleur"], gtp["vorm"])
                # bange bewoner schreeuwt uit een raam
                draw_screamer(s, b.rect.x + 26, b.rect.y + 46, t + b.style)
        draw_car(s, int(self.car[0]), int(self.car[1]))
        self.draw_hud()
        self.banner(T("city_help"))
        if self.msg_t > 0:
            m = self.mid.render(self.msg, True, GREEN)
            s.blit(m, (W / 2 - m.get_width() / 2, H / 2 - 20))

    # ---- vang-minigame ----
    def start_catch(self):
        self.state = CATCH
        self.gt = GHOST_TYPES[self.active_b.gtype] if self.active_b else GHOST_TYPES[0]
        self.trap_x = W / 2
        self.gx = random.uniform(W * 0.3, W * 0.7)
        self.gy = HUD + 90
        self.gvx = random.choice([-1, 1]) * 120
        self.gvy = 0
        self.cap = 0.0
        self.catch_t = 30.0
        self.struggle_t = random.uniform(0.8, 1.5)

    def update_catch(self, dt, keys):
        # val bewegen
        sp = 360 * dt
        if keys[pygame.K_LEFT]:
            self.trap_x -= sp
        if keys[pygame.K_RIGHT]:
            self.trap_x += sp
        self.trap_x = max(90, min(W - 90, self.trap_x))
        trap_y = H - 86
        gt = self.gt

        # geest dwaalt + vlucht omhoog (grilligheid per type)
        wnd = gt["wander"]
        # de geest vecht terug: af en toe een uitbraak-ruk
        self.struggle_t -= dt
        if self.struggle_t <= 0:
            self.struggle_t = random.uniform(0.45, 1.0) / wnd
            ang = random.uniform(0, 2 * math.pi)
            kick = 270 * wnd
            self.gvx += math.cos(ang) * kick
            self.gvy += math.sin(ang) * kick - 80      # graag omhoog vluchten
            self.play_sfx("struggle")
        self.gvx += random.uniform(-80, 80) * wnd * dt
        self.gvy += (random.uniform(-45, 30) * wnd - 22) * dt
        pulling = keys[pygame.K_SPACE]
        self._beam(pulling)
        if pulling:
            # straal trekt de geest naar de val toe
            dx = self.trap_x - self.gx
            dy = trap_y - self.gy
            d = max(1.0, math.hypot(dx, dy))
            self.gvx += (dx / d) * 520 * dt
            self.gvy += (dy / d) * 520 * dt
        vmax = 300 * gt["speed"]
        self.gvx = max(-vmax, min(vmax, self.gvx))
        self.gvy = max(-vmax, min(vmax, self.gvy))
        self.gx += self.gvx * dt
        self.gy += self.gvy * dt

        # de VAL grijpt de geest vast zodra hij erboven hangt
        in_zone = abs(self.gx - self.trap_x) < 44 and self.gy > H - 195
        if in_zone:
            # zwakke greep: hij rukt zich snel los; hou SPATIE vast en blijf mikken
            self.gx += (self.trap_x - self.gx) * min(1.0, 3 * dt)
            self.gy += (trap_y - self.gy) * min(1.0, 2.2 * dt)
            self.gvx *= 0.93
            self.gvy *= 0.93
            self.cap += (34 if pulling else 5) * gt["cap"] * dt
        else:
            self.cap -= 45 * dt

        # randen
        if self.gx < 40 or self.gx > W - 40:
            self.gvx *= -1
            self.gx = max(40, min(W - 40, self.gx))
        if self.gy < HUD + 40:
            self.gy = HUD + 40
            self.gvy = abs(self.gvy)
        if self.gy > H - 40:
            self.gy = H - 40
            self.gvy = -abs(self.gvy)
        self.cap = max(0.0, min(100.0, self.cap))
        if self.cap >= 100.0:
            beloning = random.randint(self.gt["rmin"], self.gt["rmax"])
            self.money += beloning
            self.caught += 1
            self.traps = max(0, self.traps - 1)    # een val verbruikt
            if self.active_b:
                self.active_b.haunted = False
            self.haunting = max(0.0, self.haunting - 8)
            self.msg = "%s%d" % (T("caught_one"), beloning)
            self.msg_t = 1.6
            self._beam(False)
            self.play_sfx("catch")
            self.state = CITY
            return

        self.catch_t -= dt
        if self.catch_t <= 0:
            # ontsnapt
            self.haunting = min(100.0, self.haunting + 6)
            self.msg = T("escaped")
            self.msg_t = 1.4
            self._beam(False)
            self.play_sfx("escape")
            self.state = CITY

    def _facade(self, b):
        """Het gebouw zelf groot als achtergrond - eigen gevel per gebouwtype."""
        s = self.screen
        t = pygame.time.get_ticks() / 1000.0
        bt = b.btype if b else "appartement"
        style = b.style if b else 0
        WALL = {"appartement": (70, 74, 100), "kantoor": (44, 56, 80),
                "winkel": (88, 72, 62), "fabriek": (100, 60, 52),
                "hotel": (98, 100, 112)}
        WIN = {"appartement": (246, 210, 120), "kantoor": (120, 200, 255),
               "winkel": (255, 220, 150), "fabriek": (205, 170, 120),
               "hotel": (250, 225, 150)}
        wall = WALL.get(bt, (70, 74, 100))
        wincol = WIN.get(bt, (246, 210, 120))
        s.fill((12, 14, 24))
        fx, fy, fw = 40, HUD + 8, W - 80
        fh = (H - 90) - fy
        pygame.draw.rect(s, wall, (fx, fy, fw, fh))
        pygame.draw.rect(s, tuple(min(255, c + 24) for c in wall), (fx, fy, fw, 14))

        lit_windows = []
        if bt == "kantoor":                      # glazen kantoor: strak raster
            cols, rows, mx, my = 8, 6, 34, 26
            gw = (fw - 2 * mx) / cols
            gh = (fh - my - 130) / rows
            ww, wh = gw * 0.76, gh * 0.66
            for r in range(rows):
                for c in range(cols):
                    wx = fx + mx + c * gw + (gw - ww) / 2
                    wy = fy + my + r * gh
                    lit = ((c + r * 2 + style) % 3) != 0
                    pygame.draw.rect(s, (wincol if lit else (28, 36, 52)),
                                     (wx, wy, ww, wh))
                    if lit:
                        lit_windows.append((wx + ww / 2, wy + wh / 2))
        elif bt == "fabriek":                    # fabriek: schoorsteen + weinig ramen
            pygame.draw.rect(s, (62, 42, 38), (fx + fw - 96, fy - 58, 32, 62))
            for k in range(3):
                pygame.draw.circle(s, (92, 92, 98),
                                   (fx + fw - 80, fy - 68 - k * 16), 8 + k * 2)
            cols, rows, mx, my = 6, 3, 54, 54
            gw = (fw - 2 * mx) / cols
            gh = (fh - my - 150) / rows
            ww, wh = gw * 0.6, gh * 0.5
            for r in range(rows):
                for c in range(cols):
                    wx = fx + mx + c * gw + (gw - ww) / 2
                    wy = fy + my + r * gh
                    lit = ((c + r + style) % 2) == 0
                    pygame.draw.rect(s, (wincol if lit else (44, 30, 28)),
                                     (wx, wy, ww, wh))
                    if lit:
                        lit_windows.append((wx + ww / 2, wy + wh / 2))
        elif bt == "winkel":                     # winkel: 2 verdiepingen + etalages
            cols, mx = 6, 44
            gw = (fw - 2 * mx) / cols
            for r in range(2):
                for c in range(cols):
                    wx = fx + mx + c * gw + 8
                    wy = fy + 34 + r * 48
                    lit = ((c + r + style) % 3) != 0
                    pygame.draw.rect(s, (wincol if lit else (42, 34, 30)),
                                     (wx, wy, gw - 16, 30))
                    if lit:
                        lit_windows.append((wx + (gw - 16) / 2, wy + 15))
            ey0 = fy + fh - 150
            pygame.draw.rect(s, (60, 130, 92), (fx + 30, ey0 - 16, fw - 60, 14))
            for c in range(3):
                ex0 = fx + 50 + c * ((fw - 100) / 3)
                pygame.draw.rect(s, (120, 150, 162),
                                 (ex0, ey0, (fw - 100) / 3 - 22, 78))
        else:                                    # appartement / hotel: nette rijen
            cols, rows, mx, my = 6, 5, 48, 26
            gw = (fw - 2 * mx) / cols
            gh = (fh - my - 150) / rows
            ww, wh = gw * 0.5, gh * 0.6
            for r in range(rows):
                for c in range(cols):
                    wx = fx + mx + c * gw + (gw - ww) / 2
                    wy = fy + my + r * gh
                    lit = ((c * 2 + r * 3 + style) % 3) != 0
                    pygame.draw.rect(s, (18, 20, 30), (wx - 4, wy - 4, ww + 8, wh + 8))
                    pygame.draw.rect(s, (wincol if lit else (30, 32, 46)),
                                     (wx, wy, ww, wh))
                    if bt == "hotel":
                        pygame.draw.arc(s, (228, 228, 236),
                                        (wx - 4, wy - 22, ww + 8, 44), 0, math.pi, 2)
                    if lit:
                        lit_windows.append((wx + ww / 2, wy + wh / 2))

        # schreeuwers in een paar verlichte ramen (vast per gebouw, wel bewegend)
        random.seed(style * 17 + len(bt))
        for pos in lit_windows:
            if random.random() < 0.16:
                draw_screamer(s, pos[0], pos[1], t + pos[0] * 0.01)
        random.seed()

        # gedeelde entree + stoep
        ex, ey = fx + fw / 2, fy + fh
        for k in range(3):
            wdt = 250 - k * 44
            pygame.draw.rect(s, (150 - k * 12, 152 - k * 12, 162 - k * 12),
                             (ex - wdt / 2, ey - 12 - k * 9, wdt, 11))
        pygame.draw.rect(s, (40, 42, 54), (ex - 46, ey - 122, 92, 122))
        pygame.draw.rect(s, (72, 76, 92), (ex - 3, ey - 122, 6, 122))
        if bt == "hotel":
            for sx in (-1, 1):
                pygame.draw.rect(s, (208, 210, 220),
                                 (ex + sx * 96 - 7, ey - 152, 14, 152))
            pygame.draw.rect(s, (188, 42, 42), (ex - 112, ey - 156, 224, 28),
                             border_radius=6)
            txt = self.mid.render("HOTEL", True, (255, 240, 200))
            s.blit(txt, (ex - txt.get_width() / 2, ey - 156 + 2))
        else:
            pygame.draw.rect(s, tuple(min(255, c + 30) for c in wall),
                             (ex - 70, ey - 138, 140, 16))
        for sx in (-1, 1):
            lx = ex + sx * 156
            pygame.draw.rect(s, (60, 60, 72), (lx - 2, ey - 74, 4, 74))
            pygame.draw.circle(s, (250, 222, 120), (int(lx), int(ey - 78)), 7)
        pygame.draw.rect(s, (60, 62, 72), (0, H - 90, W, 90))
        for px in range(0, W, 80):
            pygame.draw.line(s, (42, 44, 54), (px, H - 90), (px, H), 2)

    def draw_catch(self):
        s = self.screen
        self._facade(self.active_b)      # het gebouw zelf als achtergrond
        floor_y = H - 80
        # val tussen de twee mannetjes
        pygame.draw.rect(s, (60, 60, 70), (self.trap_x - 34, floor_y - 6, 68, 16),
                         border_radius=4)
        pygame.draw.rect(s, AMBER, (self.trap_x - 34, floor_y - 6, 68, 4))
        tt = pygame.time.get_ticks() / 1000.0
        # twee ghostbusters die met de val meebewegen
        tip_l = draw_buster(s, self.trap_x - 78, floor_y, +1)
        tip_r = draw_buster(s, self.trap_x + 78, floor_y, -1)
        # vasthoudstraal uit de val als de geest erboven hangt
        if abs(self.gx - self.trap_x) < 55 and self.gy > H - 200:
            draw_trap_beam(s, self.trap_x, floor_y - 6, self.gx, self.gy, tt)
        # kronkelende vangstralen vanuit beide wands
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            draw_beam(s, tip_l[0], tip_l[1], self.gx, self.gy, tt)
            draw_beam(s, tip_r[0], tip_r[1], self.gx, self.gy, tt + 0.5)
        draw_ghost_shape(s, int(self.gx), int(self.gy), 20,
                         pygame.time.get_ticks() / 150.0, self.gt["kleur"],
                         self.gt["vorm"])
        self.draw_hud()
        # vangst-balk
        bx, by, bw, bh = W / 2 - 140, H - 30, 280, 14
        pygame.draw.rect(s, (40, 44, 60), (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(s, GREEN, (bx, by, bw * self.cap / 100.0, bh),
                         border_radius=6)
        lab = self.small.render("%s  -  %s: %d s" %
                                (T("capture"), T("time"), max(0, int(self.catch_t))),
                                True, SUB)
        s.blit(lab, (bx, by - 20))
        self.banner(T("catch_help"))

    # ---- HUD + schermen ----
    def draw_hud(self):
        s = self.screen
        f = self.small
        pygame.draw.rect(s, (8, 10, 18), (0, 0, W, HUD))
        s.blit(f.render("%s: $%d" % (T("money"), self.money), True, AMBER), (12, 8))
        s.blit(f.render("%s: %d" % (T("caught"), self.caught), True, TEXT), (12, 30))
        s.blit(f.render("%s: %d" % (T("traps"), self.traps), True,
                        GREEN if self.traps > 0 else RED), (180, 8))
        s.blit(f.render(T("fuel"), True, SUB), (180, 30))
        fx, fw = 240, 90
        pygame.draw.rect(s, (40, 44, 60), (fx, 32, fw, 12), border_radius=6)
        fr = self.fuel / self.fuel_max if self.fuel_max else 0
        pygame.draw.rect(s, (GREEN if fr > 0.3 else RED),
                         (fx, 32, int(fw * fr), 12), border_radius=6)
        # geluid-indicator
        astr = T("off") if self.muted else ("%d%%" % int(self.volume * 100))
        s.blit(f.render(T("sound") + ": " + astr, True, SUB), (470, 8))
        # haunting-balk rechts
        hx = 690
        s.blit(f.render(T("haunting"), True, SUB), (hx, 8))
        frac = self.haunting / 100.0
        col = (int(120 + 100 * frac), 70, int(140 - 60 * frac))
        pygame.draw.rect(s, (40, 30, 50), (hx, 30, 250, 14), border_radius=7)
        pygame.draw.rect(s, col, (hx, 30, int(250 * frac), 14), border_radius=7)

    def banner(self, text):
        s = self.screen
        b = self.small.render(text + "      " + T("quit"), True, SUB)
        y = H - 52 if self.state == CITY else HUD + 6
        s.blit(b, (W / 2 - b.get_width() / 2, y))

    def draw_menu(self):
        s = self.screen
        s.fill(BG)
        for _ in range(40):
            pass
        title = self.big.render("DraveGhost", True, GHOST)
        s.blit(title, (W / 2 - title.get_width() / 2, 170))
        sub = self.mid.render(T("sub"), True, AMBER)
        s.blit(sub, (W / 2 - sub.get_width() / 2, 240))
        draw_no_ghost(s, W / 2, 360, 62, pygame.time.get_ticks() / 200.0)
        st = self.font.render(T("start"), True, TEXT)
        s.blit(st, (W / 2 - st.get_width() / 2, 440))
        hp = self.small.render(T("city_help"), True, SUB)
        s.blit(hp, (W / 2 - hp.get_width() / 2, 490))
        dw = self.small.render(T("donationware"), True, SUB)
        s.blit(dw, (W / 2 - dw.get_width() / 2, 540))
        ih = self.small.render(T("info_hint"), True, AMBER)
        s.blit(ih, (W / 2 - ih.get_width() / 2, 564))

    def _draw_link(self, text, cx, cy, font, color):
        surf = font.render(text, True, color)
        r = surf.get_rect(center=(cx, cy))
        self.screen.blit(surf, r)
        pygame.draw.line(self.screen, color, (r.left, r.bottom + 1),
                         (r.right, r.bottom + 1), 1)
        self.link_rects.append((r, DONATE))
        return r

    def draw_info(self):
        s = self.screen
        s.fill(BG)
        draw_no_ghost(s, W / 2, 130, 54, pygame.time.get_ticks() / 200.0)
        title = self.mid.render(T("info_title"), True, GHOST)
        s.blit(title, (W / 2 - title.get_width() / 2, 195))
        dwt = self.font.render(T("donationware"), True, TEXT)
        s.blit(dwt, (W / 2 - dwt.get_width() / 2, 270))
        dl = self.small.render(T("donate_line"), True, SUB)
        s.blit(dl, (W / 2 - dl.get_width() / 2, 320))
        self._draw_link(DONATE, W / 2, 356, self.font, BLUE)
        dc = self.small.render(T("donate_click"), True, SUB)
        s.blit(dc, (W / 2 - dc.get_width() / 2, 388))
        ct = self.small.render(T("contact_lbl") + ":  " + CONTACT, True, SUB)
        s.blit(ct, (W / 2 - ct.get_width() / 2, 440))
        ba = self.small.render(T("back_any"), True, AMBER)
        s.blit(ba, (W / 2 - ba.get_width() / 2, 500))
        ah = self.small.render(T("audio_hint"), True, SUB)
        s.blit(ah, (W / 2 - ah.get_width() / 2, 514))

    def draw_over(self):
        s = self.screen
        s.fill((20, 10, 14))
        t = self.big.render(T("gameover"), True, RED)
        s.blit(t, (W / 2 - t.get_width() / 2, 200))
        sc = self.mid.render("%s: $%d    %s: %d" %
                             (T("money"), self.money, T("caught"), self.caught),
                             True, TEXT)
        s.blit(sc, (W / 2 - sc.get_width() / 2, 300))
        r = self.font.render(T("restart"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, 380))

    def draw_pause(self):
        s = self.screen
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        s.blit(ov, (0, 0))
        t = self.big.render(T("paused"), True, GHOST)
        s.blit(t, (W / 2 - t.get_width() / 2, H / 2 - 50))
        r = self.font.render(T("resume"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, H / 2 + 24))

    def draw_shop(self):
        s = self.screen
        s.fill((14, 16, 30))
        title = self.big.render(T("shop_title"), True, GHOST)
        s.blit(title, (W / 2 - title.get_width() / 2, 60))
        draw_no_ghost(s, W / 2, 190, 46, pygame.time.get_ticks() / 200.0)
        money = self.mid.render("%s: $%d" % (T("money"), self.money), True, AMBER)
        s.blit(money, (W / 2 - money.get_width() / 2, 264))
        stat = self.mid.render("%s: %d    %s: %d/%d    %s: %d" %
                               (T("traps"), self.traps, T("fuel"), int(self.fuel),
                                int(self.fuel_max), T("car"), self.car_level),
                               True, TEXT)
        s.blit(stat, (W / 2 - stat.get_width() / 2, 308))
        if self.car_level >= CAR_MAX:
            car_opt = "%s   (%s)" % (T("buy_car"), T("maxed"))
        else:
            car_opt = "%s   ($%d)" % (T("buy_car"), CAR_PRICE * self.car_level)
        y = 368
        for o in ("%s   ($%d)" % (T("buy_trap"), TRAP_PRICE),
                  "%s   ($%d)" % (T("refuel"), FUEL_PRICE),
                  car_opt,
                  T("rollout")):
            r = self.font.render(o, True, TEXT)
            s.blit(r, (W / 2 - r.get_width() / 2, y))
            y += 42
        if self.msg_t > 0 and self.msg:
            m = self.small.render(self.msg, True, RED)
            s.blit(m, (W / 2 - m.get_width() / 2, y + 10))
        k = self.small.render(T("shop_keys"), True, SUB)
        s.blit(k, (W / 2 - k.get_width() / 2, H - 40))

    def buy_trap(self):
        if self.money >= TRAP_PRICE:
            self.money -= TRAP_PRICE
            self.traps += 1
        else:
            self.msg = T("no_money")
            self.msg_t = 1.6

    def buy_fuel(self):
        if self.fuel >= self.fuel_max:
            return
        if self.money >= FUEL_PRICE:
            self.money -= FUEL_PRICE
            self.fuel = self.fuel_max
        else:
            self.msg = T("no_money")
            self.msg_t = 1.6

    def buy_car(self):
        if self.car_level >= CAR_MAX:
            return
        cost = CAR_PRICE * self.car_level
        if self.money >= cost:
            self.money -= cost
            self.car_level += 1
            self.fuel_max += 50.0          # grotere tank
            self.fuel = self.fuel_max
        else:
            self.msg = T("no_money")
            self.msg_t = 1.6

    # ---- hoofdlus ----
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                    if e.key == pygame.K_p and self.state in (CITY, CATCH):
                        self.paused = not self.paused
                        if self.paused:
                            self._beam(False)
                    if e.key == pygame.K_m:
                        self.toggle_mute()
                    elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.set_volume(-0.1)
                    elif e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        self.set_volume(0.1)
                    if e.key == pygame.K_d:
                        webbrowser.open(DONATE)
                    if self.state == MENU and e.key == pygame.K_SPACE:
                        self.reset()
                        self.state = SHOP
                    elif self.state == MENU and e.key == pygame.K_i:
                        self.state = INFO
                    elif self.state == INFO:
                        self.state = MENU
                    elif self.state == SHOP:
                        if e.key == pygame.K_t:
                            self.buy_trap()
                        elif e.key in (pygame.K_f, pygame.K_b):
                            self.buy_fuel()
                        elif e.key == pygame.K_c:
                            self.buy_car()
                        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                       pygame.K_SPACE):
                            self.state = CITY
                    elif self.state == CITY and e.key == pygame.K_SPACE:
                        self.try_bust()
                    elif self.state == OVER and e.key == pygame.K_r:
                        self.reset()
                        self.state = MENU
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, url in self.link_rects:
                        if r.collidepoint(e.pos):
                            webbrowser.open(url)
                            break
            keys = pygame.key.get_pressed()
            if self.msg_t > 0:
                self.msg_t -= dt
            self._set_music("catch" if self.state == CATCH else "city")
            if not self.paused:
                if self.state == CITY:
                    self.update_city(dt, keys)
                elif self.state == CATCH:
                    self.update_catch(dt, keys)

            self.link_rects = []
            if self.state == MENU:
                self.draw_menu()
            elif self.state == INFO:
                self.draw_info()
            elif self.state == SHOP:
                self.draw_shop()
            elif self.state == CITY:
                self.draw_city()
            elif self.state == CATCH:
                self.draw_catch()
            elif self.state == OVER:
                self.draw_over()
            if self.paused and self.state in (CITY, CATCH):
                self.draw_pause()
            mp = pygame.mouse.get_pos()
            hov = any(r.collidepoint(mp) for r, _ in self.link_rects)
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if hov else pygame.SYSTEM_CURSOR_ARROW)
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()

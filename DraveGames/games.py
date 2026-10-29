# -*- coding: utf-8 -*-
"""games.py - DraveGames, sport-minigames (C64/Atari-stijl) van Dravenlock Games.

Zes events met medailles, in winter- en zomersfeer:
  - Schaatsen 500m (winter): duw ritmisch links/rechts op de maat.
  - Schansspringen (winter): timing op de afzet + balans in de lucht.
  - 100m Sprint (zomer): ram afwisselend links/rechts voor snelheid.
  - Speerwerpen (zomer): waggle-aanloop en gooi met de juiste hoek.
  - Verspringen (zomer): waggle-aanloop en zet af vlak vóór de balk.
  - 110m Horden (zomer): waggle-rennen en spring op tijd over de horden.

1-speler (medailles halen) of 2-speler om-en-om (zelfde pc). NL-basis met
OS-taaldetectie en Engels; donker Dravenlock-palet, grote contrastrijke HUD;
procedurele muziek en geluiden (sfx.py); gesproken intro (neuvoice) in een apart
splashvenster. Volledig draagbaar: alles in een map "DraveGames-data" naast het
programma.
"""
from __future__ import annotations

import json
import math
import os
import sys
import threading
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
try:
    import net as netmod
except Exception:  # pragma: no cover
    netmod = None

APP_NAME = "DraveGames"
APP_VERSION = "0.1.0"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 46

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
SILVER = (200, 200, 210)
BRONS = (190, 130, 88)
ICE = (150, 196, 232)
SNOW = (224, 232, 244)
SKY_W = (150, 188, 224)     # winterlucht
SKY_S = (120, 178, 224)     # zomerlucht
GRASS = (96, 150, 84)
TRACK = (176, 96, 72)       # sintelbaan


# ----------------------------------------------------------------------------
def config_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveGames-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveGames-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "records": {},
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    if not isinstance(cfg.get("records"), dict):
        cfg["records"] = {}
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
    "terug_menu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "verder": {"nl": "Verder", "en": "Continue"},
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "pauze_hint": {"nl": "P of Esc = pauze", "en": "P or Esc = pause"},
    "spelers": {"nl": "Aantal spelers", "en": "Players"},
    "1speler": {"nl": "1 speler", "en": "1 player"},
    "2spelers": {"nl": "2 spelers (om-en-om)", "en": "2 players (hotseat)"},
    "lan_2spelers": {"nl": "2 spelers (LAN)", "en": "2 players (LAN)"},
    "lan_titel": {"nl": "LAN-spel", "en": "LAN game"},
    "lan_host": {"nl": "Spel hosten", "en": "Host game"},
    "lan_find": {"nl": "Host zoeken op LAN", "en": "Find host on LAN"},
    "lan_manual": {"nl": "Verbinden via IP", "en": "Connect by IP"},
    "lan_wacht_speler": {"nl": "Wacht op tweede speler...", "en": "Waiting for second player..."},
    "lan_jouw_ip": {"nl": "Jouw IP", "en": "Your IP"},
    "lan_verbinden": {"nl": "Verbinden...", "en": "Connecting..."},
    "lan_zoeken": {"nl": "Zoeken op het netwerk...", "en": "Searching the network..."},
    "lan_geen_host": {"nl": "Geen host gevonden - probeer 'Verbinden via IP'", "en": "No host found - try 'Connect by IP'"},
    "lan_tip": {"nl": "Beide pc's op hetzelfde netwerk en sta DraveGames toe in de firewall.", "en": "Both PCs on the same network and allow DraveGames in the firewall."},
    "lan_tip2": {"nl": "Werkt zoeken niet? Gebruik het IP dat de host toont via 'Verbinden via IP'.", "en": "Search not working? Use the host's shown IP via 'Connect by IP'."},
    "lan_verbonden": {"nl": "Verbonden!", "en": "Connected!"},
    "lan_fout": {"nl": "Verbinding mislukt", "en": "Connection failed"},
    "lan_typ_ip": {"nl": "Typ het IP-adres van de host:", "en": "Type the host's IP address:"},
    "lan_enter": {"nl": "Enter = verbinden, Esc = terug", "en": "Enter = connect, Esc = back"},
    "lan_niet_beschikbaar": {"nl": "LAN niet beschikbaar (net.py ontbreekt)", "en": "LAN unavailable (net.py missing)"},
    "kies_event": {"nl": "Kies een onderdeel", "en": "Choose an event"},
    "toernooi": {"nl": "Toernooi (alle 4)", "en": "Tournament (all 4)"},
    "speler": {"nl": "Speler", "en": "Player"},
    "klaar_start": {"nl": "Druk op spatie om te starten", "en": "Press space to start"},
    "resultaat": {"nl": "Resultaat", "en": "Result"},
    "medaille": {"nl": "Medaille", "en": "Medal"},
    "geen": {"nl": "geen", "en": "none"},
    "goud": {"nl": "goud", "en": "gold"},
    "zilver": {"nl": "zilver", "en": "silver"},
    "brons": {"nl": "brons", "en": "bronze"},
    "record": {"nl": "Record!", "en": "Record!"},
    "medaillespiegel": {"nl": "Medaillespiegel", "en": "Medal tally"},
    "winnaar": {"nl": "Winnaar", "en": "Winner"},
    "gelijk": {"nl": "Gelijkspel", "en": "Tie"},
    "ev_skate": {"nl": "Schaatsen 500m", "en": "Speed skating 500m"},
    "ev_jump": {"nl": "Schansspringen", "en": "Ski jump"},
    "ev_sprint": {"nl": "100m Sprint", "en": "100m Sprint"},
    "ev_javelin": {"nl": "Speerwerpen", "en": "Javelin"},
    "ev_longjump": {"nl": "Verspringen", "en": "Long jump"},
    "ev_hurdles": {"nl": "110m Horden", "en": "110m Hurdles"},
    "ev_highjump": {"nl": "Hoogspringen", "en": "High jump"},
    "ev_discus": {"nl": "Discuswerpen", "en": "Discus"},
    "ev_swim": {"nl": "Zwemmen 100m", "en": "100m Swim"},
    "ev_weight": {"nl": "Gewichtheffen", "en": "Weightlifting"},
    "ev_bobsled": {"nl": "Bobslee", "en": "Bobsled"},
    "ev_slalom": {"nl": "Slalom", "en": "Slalom"},
    "ev_biathlon": {"nl": "Biatlon", "en": "Biathlon"},
    "ev_figure": {"nl": "Kunstschaatsen", "en": "Figure skating"},
    "seizoen": {"nl": "Kies seizoen", "en": "Choose season"},
    "winterspelen": {"nl": "Winterspelen", "en": "Winter Games"},
    "zomerspelen": {"nl": "Zomerspelen", "en": "Summer Games"},
    "in_skate": {"nl": "Druk om-en-om links/rechts; sneller = sneller. Op de maat (groene zones) = extra zet.",
                 "en": "Press left/right alternately; faster = faster. On the beat (green zones) = extra push."},
    "in_jump": {"nl": "Spatie bij de schanstip voor de afzet, dan pijl omhoog/omlaag voor de balans.",
                "en": "Space at the ramp tip for take-off, then up/down arrows to balance."},
    "in_sprint": {"nl": "Ram afwisselend links en rechts zo snel mogelijk!",
                  "en": "Hammer left and right alternately as fast as you can!"},
    "in_javelin": {"nl": "Ram links/rechts voor aanloop, spatie om te werpen voor de streep.",
                   "en": "Hammer left/right to run up, space to throw before the line."},
    "in_longjump": {"nl": "Ram links/rechts voor aanloop, spatie om af te zetten bij de balk.",
                    "en": "Hammer left/right to run up, space to jump at the board."},
    "in_hurdles": {"nl": "Ram links/rechts om te rennen, spatie om over de horden te springen.",
                   "en": "Hammer left/right to run, space to jump the hurdles."},
    "in_highjump": {"nl": "Ram links/rechts voor aanloop, spatie om af te zetten bij de lat.",
                    "en": "Hammer left/right to run up, space to take off at the bar."},
    "in_discus": {"nl": "Ram links/rechts voor de draai, spatie om los te laten op de juiste hoek.",
                  "en": "Hammer left/right to spin, space to release at the right angle."},
    "in_swim": {"nl": "Ram links/rechts voor je slagen; pijl omhoog om adem te halen op de boei.",
                "en": "Hammer left/right for your strokes; up arrow to breathe on the marker."},
    "in_weight": {"nl": "Spatie op het groene moment: eerst trekken, dan stoten. Twee keer goed = zwaarder.",
                  "en": "Space on the green moment: first the pull, then the jerk. Two good = heavier."},
    "in_bobsled": {"nl": "Stuur met links/rechts door de bochten; raak de wand niet, snelste tijd wint.",
                   "en": "Steer left/right through the bends; avoid the walls, fastest time wins."},
    "in_slalom": {"nl": "Stuur met links/rechts door de poortjes; een poort missen kost tijd.",
                  "en": "Steer left/right through the gates; missing a gate costs time."},
    "in_biathlon": {"nl": "Ram links/rechts om te langlaufen; bij het schieten: spatie als het kruis op de roos staat.",
                    "en": "Hammer left/right to ski; when shooting: space when the cross is on the target."},
    "in_figure": {"nl": "Druk de getoonde pijlen/toetsen op de maat in voor een hoge juryscore.",
                  "en": "Press the shown arrows/keys on time for a high judges' score."},
    "kg": {"nl": "kg", "en": "kg"},
    "punten": {"nl": "punten", "en": "points"},
    "poging": {"nl": "Poging", "en": "Attempt"},
    "beste": {"nl": "Beste", "en": "Best"},
    "ronde": {"nl": "Ronde", "en": "Round"},
    "baan": {"nl": "Baan", "en": "Lap"},
    "toernooi3": {"nl": "Toernooi (3 rondes)", "en": "Tournament (3 rounds)"},
    "toernooi1": {"nl": "Snel (1 ronde)", "en": "Quick (1 round)"},
    "lat": {"nl": "Lat", "en": "Bar"},
    "schot": {"nl": "Schot", "en": "Shot"},
    "raak2": {"nl": "RAAK", "en": "HIT"},
    "mis2": {"nl": "MIS", "en": "MISS"},
    "poort_mis": {"nl": "Poort gemist!", "en": "Gate missed!"},
    "perfect": {"nl": "PERFECT", "en": "PERFECT"},
    "goed": {"nl": "GOED", "en": "GOOD"},
    "trek": {"nl": "TREKKEN", "en": "PULL"},
    "stoot": {"nl": "STOTEN", "en": "JERK"},
    "tijd": {"nl": "Tijd", "en": "Time"},
    "afstand": {"nl": "Afstand", "en": "Distance"},
    "snelheid": {"nl": "Snelheid", "en": "Speed"},
    "ongeldig": {"nl": "Ongeldig!", "en": "Foul!"},
    "afzet": {"nl": "AFZET!", "en": "JUMP!"},
    "balans": {"nl": "Balans", "en": "Balance"},
    "werp": {"nl": "WERP!", "en": "THROW!"},
    "hoek": {"nl": "Hoek", "en": "Angle"},
    "besturing": {"nl": "Besturing", "en": "Controls"},
    "ctrl_skate_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om duwen (sneller = sneller)", "en": "Left / Right arrow (or A / D): push left-right (faster = faster)"},
    "ctrl_skate_2": {"nl": "Op de maat van de balk duwen (groene zones) = extra zet", "en": "Push on the beat of the bar (green zones) = extra push"},
    "ctrl_jump_1": {"nl": "Spatie: afzet bij de schanstip, en daarna de landing", "en": "Space: take-off at the ramp tip, then the landing"},
    "ctrl_jump_2": {"nl": "Pijl Omhoog / Omlaag: balans in de lucht (beter = verder)", "en": "Up / Down arrow: balance in the air (better = further)"},
    "ctrl_sprint_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen", "en": "Left / Right arrow (or A / D): hammer left-right"},
    "ctrl_sprint_2": {"nl": "Sneller afwisselen = sneller; stoppen = je vertraagt", "en": "Faster alternating = faster; stop = you slow down"},
    "ctrl_javelin_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen voor aanloop", "en": "Left / Right arrow (or A / D): hammer left-right for run-up"},
    "ctrl_javelin_2": {"nl": "Spatie: werpen voor de rode streep; hoek ~45 graden = verst", "en": "Space: throw before the red line; angle ~45 degrees = furthest"},
    "ctrl_longjump_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen voor aanloop", "en": "Left / Right arrow (or A / D): hammer left-right for run-up"},
    "ctrl_longjump_2": {"nl": "Spatie: afzetten vlak vóór de rode balk (eroverheen = ongeldig)", "en": "Space: jump just before the red board (over it = foul)"},
    "ctrl_hurdles_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen om te rennen", "en": "Left / Right arrow (or A / D): hammer left-right to run"},
    "ctrl_hurdles_2": {"nl": "Spatie / Pijl Omhoog: springen; horde raken = snelheids- + tijdstraf", "en": "Space / Up arrow: jump; hitting a hurdle = speed + time penalty"},
    "horde_raak": {"nl": "Geraakt", "en": "Hits"},
    "ctrl_highjump_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen voor aanloop", "en": "Left / Right arrow (or A / D): hammer left-right for run-up"},
    "ctrl_highjump_2": {"nl": "Spatie: afzetten vlak voor de lat; sneller + nette afzet = hoger", "en": "Space: take off just before the bar; faster + clean = higher"},
    "ctrl_discus_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen voor de draai", "en": "Left / Right arrow (or A / D): hammer left-right to spin"},
    "ctrl_discus_2": {"nl": "Spatie: loslaten voor de streep; hoek ~40 graden = verst", "en": "Space: release before the line; angle ~40 degrees = furthest"},
    "ctrl_swim_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om rammen voor je slagen", "en": "Left / Right arrow (or A / D): hammer left-right for strokes"},
    "ctrl_swim_2": {"nl": "Pijl Omhoog: ademhalen bij de boei (goede timing = klein zetje)", "en": "Up arrow: breathe at the marker (good timing = small boost)"},
    "ctrl_weight_1": {"nl": "Spatie: trekken op het groene moment (fase 1)", "en": "Space: pull on the green moment (phase 1)"},
    "ctrl_weight_2": {"nl": "Spatie: stoten op het groene moment (fase 2); beide goed = zwaarder", "en": "Space: jerk on the green moment (phase 2); both good = heavier"},
    "ctrl_bobsled_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): sturen door de bochten", "en": "Left / Right arrow (or A / D): steer through the bends"},
    "ctrl_bobsled_2": {"nl": "Blijf van de wanden; raken = snelheidsverlies", "en": "Keep off the walls; scraping = loss of speed"},
    "ctrl_slalom_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): sturen door de poortjes", "en": "Left / Right arrow (or A / D): steer through the gates"},
    "ctrl_slalom_2": {"nl": "Mis je een poort, dan krijg je een tijdstraf", "en": "Missing a gate gives a time penalty"},
    "ctrl_biathlon_1": {"nl": "Pijl Links / Pijl Rechts (of A / D): om-en-om langlaufen", "en": "Left / Right arrow (or A / D): ski left-right"},
    "ctrl_biathlon_2": {"nl": "Spatie: schieten als het kruis op de roos staat (mis = strafrondje)", "en": "Space: shoot when the cross is on target (miss = penalty)"},
    "ctrl_figure_1": {"nl": "Pijltjes / toetsen: druk de getoonde reeks op de maat in", "en": "Arrows / keys: press the shown sequence on time"},
    "ctrl_figure_2": {"nl": "Op tijd = meer punten; te laat of fout = combo kwijt", "en": "On time = more points; late or wrong = combo lost"},
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


def draw_medal_icon(surf, cx, cy, r, kind):
    col = {"goud": GOLD, "zilver": SILVER, "brons": BRONS}.get(kind, MUTED)
    pygame.draw.polygon(surf, ACCENT, [(cx - 7, cy - r), (cx - 2, cy - 2), (cx - 12, cy - 2)])
    pygame.draw.polygon(surf, RED, [(cx + 7, cy - r), (cx + 2, cy - 2), (cx + 12, cy - 2)])
    pygame.draw.circle(surf, col, (cx, cy + 4), r)
    pygame.draw.circle(surf, mix(col, (0, 0, 0), 0.3), (cx, cy + 4), r, 2)
    pygame.draw.circle(surf, mix(col, (255, 255, 255), 0.4), (cx - r // 3, cy + 4 - r // 3), max(2, r // 4))


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


def compute_medal(value, gold, silver, bronze, lower_better):
    if lower_better:
        if value <= gold:
            return "goud"
        if value <= silver:
            return "zilver"
        if value <= bronze:
            return "brons"
    else:
        if value >= gold:
            return "goud"
        if value >= silver:
            return "zilver"
        if value >= bronze:
            return "brons"
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


def draw_athlete(surf, x, y, lean, phase, col, scale=1.0):
    """Eenvoudig zijaanzicht-figuurtje; phase animeert de benen, lean kantelt."""
    s = scale
    skin = (236, 198, 168)
    head = (int(x + lean * 8), int(y - 30 * s))
    pygame.draw.line(surf, col, (x, y), (x + lean * 8, y - 26 * s), int(6 * s))
    pygame.draw.circle(surf, skin, head, int(6 * s))
    # benen
    sw = math.sin(phase) * 9 * s
    pygame.draw.line(surf, col, (x, y), (x - sw, y + 16 * s), int(5 * s))
    pygame.draw.line(surf, col, (x, y), (x + sw, y + 16 * s), int(5 * s))
    # arm
    aw = math.cos(phase) * 8 * s
    pygame.draw.line(surf, col, (x + lean * 5, y - 16 * s), (x + aw + lean * 5, y - 6 * s), int(4 * s))


# ============================================================================
# EVENTS
# ============================================================================
class Event:
    name_key = ""
    instr_key = ""
    unit = "s"
    lower_better = True
    winter = True
    MED = (0, 0, 0)         # (goud, zilver, brons)
    attempts = 1           # aantal pogingen (veld-onderdelen: 3, beste telt)

    def __init__(self, app):
        self.app = app
        self.reset()

    def reset(self):
        self.done = False
        self.value = 0.0
        self.t = 0.0
        self.countdown = 3.0
        self.started = False

    def sfx(self, n):
        if self.app.sfx:
            self.app.sfx.play(n)

    def medal(self):
        g, s, b = self.MED
        return compute_medal(self.value, g, s, b, self.lower_better)

    def value_text(self):
        if self.unit == "s":
            return "%.2f s" % self.value
        if self.unit == "p":
            return "%.0f %s" % (self.value, t("punten"))
        if self.unit == "kg":
            return "%.0f kg" % self.value
        return "%.2f m" % self.value

    def tick_countdown(self, dt):
        if self.started:
            return True
        self.countdown -= dt
        if self.countdown <= 0:
            self.started = True
            self.sfx("start")
            return True
        return False

    def on_key(self, key):
        pass

    def update(self, dt, keys):
        pass

    def draw_world(self, surf):
        pass

    def draw(self, surf):
        self.draw_world(surf)
        if not self.started:
            n = max(1, int(math.ceil(self.countdown)))
            f = pygame.font.Font(None, 200)
            img = f.render(str(n), True, GOLD)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


def _bg_sky(surf, winter):
    top = SKY_W if winter else SKY_S
    bot = SNOW if winter else GRASS
    for i in range(HUD_H, HEIGHT, 4):
        c = mix(top, bot, (i - HUD_H) / (HEIGHT - HUD_H))
        pygame.draw.rect(surf, c, (0, i, WIDTH, 4))


class Sprint(Event):
    name_key = "ev_sprint"
    instr_key = "in_sprint"
    unit = "s"
    lower_better = True
    winter = False
    MED = (9.5, 12.5, 16.0)
    DIST = 100.0
    CAP = 16.0

    def reset(self):
        super().reset()
        self.speed = 0.0
        self.dist = 0.0
        self.last_side = 0
        self.phase = 0.0

    def on_key(self, key):
        if not self.started or self.done:
            return
        side = 0
        if key in (pygame.K_LEFT, pygame.K_a):
            side = -1
        elif key in (pygame.K_RIGHT, pygame.K_d):
            side = 1
        if side and side != self.last_side:
            self.last_side = side
            self.speed = min(self.CAP, self.speed + 0.62)
            self.sfx("step")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        # proportionele wrijving: hoe sneller je heen-en-weer wisselt,
        # hoe hoger je snelheid oploopt (C64-waggle-gevoel)
        self.speed = max(0.0, self.speed - (self.speed * 0.42 + 0.6) * dt)
        self.dist += self.speed * dt
        self.phase += self.speed * dt * 1.6
        if self.dist >= self.DIST:
            self.done = True
            self.value = self.t
            self.sfx("cheer")

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 150
        frac = clamp(self.speed / self.CAP, 0.0, 1.0)
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        for lane in range(1, 5):
            pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.22), (0, gy + lane * 22), (WIDTH, gy + lane * 22), 1)
        # snel scrollende streepjes voor het vaartgevoel
        spacing = 64
        off = int((self.dist * 28) % spacing)
        for k in range(-1, WIDTH // spacing + 2):
            x = k * spacing - off
            pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.5), (x, gy + 46), (x + 26, gy + 46), 5)
        # afstandsmarkeringen (elke 10 m)
        ff = pygame.font.Font(None, 24)
        for m in range(0, 101, 10):
            mx = int((m - self.dist) * 16 + 150)
            if -30 < mx < WIDTH + 30:
                pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.6), (mx, gy), (mx, gy + 13), 2)
                surf.blit(ff.render("%d" % m, True, mix(TRACK, (255, 255, 255), 0.75)), (mx - 7, gy + 15))
        # vaartlijnen bij hoge snelheid
        if frac > 0.2:
            for i in range(int(frac * 9)):
                ly = HUD_H + 30 + (i * 71) % (gy - HUD_H - 70)
                lx = WIDTH + 160 - int(self.dist * 80 + i * 130) % (WIDTH + 160)
                ln = int(30 + 70 * frac)
                pygame.draw.line(surf, (255, 255, 255), (lx, ly), (lx + ln, ly), 2)
        # loper (beweegt en bobt mee met de snelheid)
        runx = 150 + int(frac * 50)
        bob = int(math.sin(self.phase * 2) * (2 + 4 * frac))
        draw_athlete(surf, runx, gy + 8 - bob, 0.5 + 0.35 * frac, self.phase, ACCENT, 1.5)
        # HUD
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%.1f m" % self.dist, True, TEXT), (24, HUD_H + 14))
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 54))
        pygame.draw.rect(surf, PANEL2, (24, HUD_H + 100, 240, 20), border_radius=8)
        pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 100, int(240 * frac), 20), border_radius=8)
        surf.blit(pygame.font.Font(None, 26).render("%.1f m/s" % self.speed, True, TEXT), (276, HUD_H + 101))


class Skate(Event):
    name_key = "ev_skate"
    instr_key = "in_skate"
    unit = "s"
    lower_better = True
    winter = True
    MED = (34.0, 44.0, 56.0)
    DIST = 500.0
    CAP = 18.0
    LAP_LEN = 100.0           # 500 m = 5 ronden op de baan

    def reset(self):
        super().reset()
        self.speed = 5.0
        self.dist = 0.0
        self.swing = 0.0          # 0..1 pendel-fase
        self.expect = -1          # verwachte kant: -1 links, 1 rechts
        self.last_side = 1
        self.glide = 0.0          # 0..1 schaatsslag-animatie
        self.push_side = 1
        self.flash = 0.0
        self.lap = 0
        self.lap_flash = 0.0

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        self.swing = (self.swing + dt * 1.2) % 1.0
        self.expect = -1 if self.swing < 0.5 else 1
        # proportionele wrijving: blijf om-en-om duwen om snelheid te houden
        self.speed = max(2.0, self.speed - (self.speed * 0.34 + 0.5) * dt)
        self.dist += self.speed * dt
        self.glide = (self.glide + self.speed * dt * 0.16) % 1.0
        self.flash = max(0.0, self.flash - dt * 3)
        self.lap_flash = max(0.0, self.lap_flash - dt * 2)
        lap_now = min(int(self.dist / self.LAP_LEN), int(self.DIST / self.LAP_LEN) - 1)
        if lap_now > self.lap:
            self.lap = lap_now
            self.lap_flash = 1.0
            self.sfx("step")
        if self.dist >= self.DIST:
            self.done = True
            self.value = self.t
            self.sfx("cheer")

    def on_key(self, key):
        if not self.started or self.done:
            return
        side = 0
        if key in (pygame.K_LEFT, pygame.K_a):
            side = -1
        elif key in (pygame.K_RIGHT, pygame.K_d):
            side = 1
        if not side or side == self.last_side:
            return                       # moet afwisselen
        self.last_side = side
        self.push_side = side
        # basis-duw (altijd responsief) + ritmebonus in de groene zone
        in_zone = (side == self.expect)
        edge = abs(self.swing - (0.25 if side < 0 else 0.75))
        bonus = max(0.0, 1.0 - edge / 0.22) if in_zone else 0.0
        self.speed = min(self.CAP, self.speed + 0.85 + 0.9 * bonus)
        if bonus > 0.4:
            self.flash = 1.0
        self.sfx("push")

    def draw_world(self, surf):
        _bg_sky(surf, True)
        gy = HEIGHT - 150
        frac = clamp(self.speed / self.CAP, 0.0, 1.0)
        pygame.draw.rect(surf, ICE, (0, gy, WIDTH, HEIGHT - gy))
        # snel scrollende ijsstrepen (vaartgevoel)
        spacing = 84
        off = int((self.dist * 20) % spacing)
        for k in range(-1, WIDTH // spacing + 2):
            x = k * spacing - off
            pygame.draw.line(surf, mix(ICE, (255, 255, 255), 0.55), (x, gy + 52), (x + 40, gy + 52), 3)
        # afstandsmarkeringen (elke 100 m)
        ff = pygame.font.Font(None, 24)
        for m in range(0, 501, 100):
            mx = int((m - self.dist) * 1.5 + 170)
            if -40 < mx < WIDTH + 40:
                pygame.draw.line(surf, mix(ICE, (255, 255, 255), 0.7), (mx, gy), (mx, gy + 14), 2)
                surf.blit(ff.render("%d" % m, True, mix(ICE, (60, 60, 80), 0.7)), (mx - 10, gy + 16))
        # vaartlijnen bij hoge snelheid
        if frac > 0.25:
            for i in range(int(frac * 8)):
                ly = HUD_H + 30 + (i * 73) % (gy - HUD_H - 70)
                lx = WIDTH + 160 - int(self.dist * 70 + i * 150) % (WIDTH + 160)
                pygame.draw.line(surf, (255, 255, 255), (lx, ly), (lx + int(24 + 60 * frac), ly), 2)
        # de schaatser: voorovergebogen, lange glij-afzet opzij
        sx = 178
        stride = math.sin(self.glide * 2 * math.pi)
        skin = (236, 198, 168)
        hipx, hipy = sx, gy - 20
        shx, shy = sx + 22, gy - 38
        # duwbeen (ver naar achter-onder), pulseert met de slag
        ext = 16 + int(20 * (0.5 + 0.5 * stride))
        pbx, pby = hipx - ext, gy + 2
        pygame.draw.line(surf, PURPLE, (hipx, hipy), (pbx, pby), 6)
        pygame.draw.line(surf, ACCENT, (pbx - 9, pby), (pbx + 7, pby), 4)
        # glijbeen (onder/voor het lichaam)
        gbx = sx + 12 + int(8 * (0.5 - 0.5 * stride))
        pygame.draw.line(surf, PURPLE, (hipx, hipy), (gbx, gy), 6)
        pygame.draw.line(surf, ACCENT, (gbx - 9, gy), (gbx + 9, gy), 4)
        # romp (sterke voorovergebogen lijn) + hoofd
        pygame.draw.line(surf, PURPLE, (hipx, hipy), (shx, shy), 9)
        pygame.draw.circle(surf, skin, (shx + 9, shy - 7), 7)
        # arm zwaait laag mee
        ax, ay = shx + int(16 * stride), shy + 12
        pygame.draw.line(surf, PURPLE, (shx, shy + 2), (ax, ay), 5)
        # HUD
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%.0f m" % self.dist, True, TEXT), (24, HUD_H + 14))
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 54))
        pygame.draw.rect(surf, PANEL2, (24, HUD_H + 100, 240, 20), border_radius=8)
        pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 100, int(240 * frac), 20), border_radius=8)
        surf.blit(pygame.font.Font(None, 26).render("%.1f m/s" % self.speed, True, TEXT), (276, HUD_H + 101))
        # ronde-teller
        total_laps = int(self.DIST / self.LAP_LEN)
        surf.blit(f.render("%s %d/%d" % (t("ronde"), self.lap + 1, total_laps), True, ACCENT), (WIDTH - 200, HUD_H + 14))
        if self.lap_flash > 0:
            big = pygame.font.Font(None, 60)
            img = big.render("%s %d!" % (t("ronde"), self.lap + 1), True, GOLD)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 120)))
        # ritme-pendel (groene zones = bonus)
        bx, by, bw = WIDTH // 2 - 150, HEIGHT - 60, 300
        pygame.draw.rect(surf, PANEL2, (bx, by, bw, 26), border_radius=12)
        pygame.draw.rect(surf, mix(GOED, BG, 0.3), (bx + int(bw * 0.16), by, int(bw * 0.18), 26), border_radius=8)
        pygame.draw.rect(surf, mix(GOED, BG, 0.3), (bx + int(bw * 0.66), by, int(bw * 0.18), 26), border_radius=8)
        px = bx + int(bw * self.swing)
        pygame.draw.circle(surf, GOLD if self.flash > 0 else TEXT, (px, by + 13), 12)
        ff2 = pygame.font.Font(None, 28)
        surf.blit(ff2.render("L", True, TEXT), (bx + int(bw * 0.22), by - 24))
        surf.blit(ff2.render("R", True, TEXT), (bx + int(bw * 0.72), by - 24))


class SkiJump(Event):
    name_key = "ev_jump"
    instr_key = "in_jump"
    unit = "m"
    lower_better = False
    winter = True
    MED = (98.0, 82.0, 66.0)

    def reset(self):
        super().reset()
        self.phase = "ramp"       # ramp -> flight -> land -> done
        self.marker = 0.0
        self.power = 0.0
        self.lean = 0.5
        self.target = 0.62
        self.lean_acc = 0.0
        self.lean_n = 0
        self.flight_t = 0.0
        self.land_marker = 0.0
        self.land_bonus = 0.0
        self.slide = 0.0

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        if self.phase == "ramp":
            self.marker += dt * 0.62
            self.slide += dt
            if self.marker >= 1.0:
                # te laat: zwakke afzet
                self.power = 0.15
                self._to_flight()
        elif self.phase == "flight":
            self.flight_t += dt
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.lean = clamp(self.lean + dt * 0.9, 0, 1)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.lean = clamp(self.lean - dt * 0.9, 0, 1)
            self.lean_acc += (1.0 - abs(self.lean - self.target) / 0.5)
            self.lean_n += 1
            if self.flight_t >= 2.6:
                self.phase = "land"
                self.land_marker = 0.0
        elif self.phase == "land":
            self.land_marker += dt * 0.7
            if self.land_marker >= 1.0:
                self.land_bonus = 0.0
                self._finish()

    def _to_flight(self):
        self.phase = "flight"
        self.sfx("launch")

    def on_key(self, key):
        if not self.started or self.done:
            return
        if key == pygame.K_SPACE:
            if self.phase == "ramp":
                # beste afzet vlak bij de tip (0.86)
                self.power = clamp(1.0 - abs(self.marker - 0.86) * 3.2, 0.0, 1.0)
                self._to_flight()
            elif self.phase == "land":
                self.land_bonus = clamp(1.0 - abs(self.land_marker - 0.8) * 3.5, 0.0, 1.0)
                self.sfx("land")
                self._finish()

    def _finish(self):
        lean_q = (self.lean_acc / self.lean_n) if self.lean_n else 0.0
        lean_q = clamp(lean_q, 0.0, 1.0)
        self.value = 42.0 + self.power * 42.0 + lean_q * 30.0 + self.land_bonus * 8.0
        self.done = True
        self.sfx("cheer")

    def draw_world(self, surf):
        _bg_sky(surf, True)
        # schans (zijaanzicht)
        pygame.draw.polygon(surf, SNOW, [(0, HEIGHT), (0, 240), (360, 470), (520, 470), (WIDTH, HEIGHT)])
        pygame.draw.line(surf, mix(SNOW, ACCENT, 0.4), (0, 240), (360, 470), 4)
        f = pygame.font.Font(None, 40)
        ff = pygame.font.Font(None, 30)
        if self.phase == "ramp":
            sx = int(lerp(40, 350, self.marker))
            sy = int(lerp(250, 460, self.marker))
            draw_athlete(surf, sx, sy, 0.8, 0.0, PURPLE, 1.3)
            self._timing_bar(surf, self.marker, 0.86)
            surf.blit(ff.render(t("afzet"), True, GOLD), (WIDTH // 2 - 40, HEIGHT - 96))
        elif self.phase == "flight":
            prog = clamp(self.flight_t / 2.6, 0, 1)
            sx = int(lerp(360, WIDTH - 120, prog))
            sy = int(lerp(460, 330 + (1 - self.power) * 120, prog) - math.sin(prog * math.pi) * 90)
            draw_athlete(surf, sx, sy, lerp(-0.2, 1.0, self.lean), 0.0, PURPLE, 1.3)
            # balans-meter
            bx, by, bw = WIDTH // 2 - 140, HEIGHT - 70, 280
            pygame.draw.rect(surf, PANEL2, (bx, by, bw, 24), border_radius=10)
            pygame.draw.rect(surf, mix(GOED, BG, 0.2),
                             (bx + int(bw * (self.target - 0.1)), by, int(bw * 0.2), 24), border_radius=8)
            pygame.draw.circle(surf, GOLD, (bx + int(bw * self.lean), by + 12), 11)
            surf.blit(ff.render(t("balans"), True, TEXT), (bx, by - 26))
        elif self.phase == "land":
            draw_athlete(surf, WIDTH - 120, 470, 0.2, 0.0, PURPLE, 1.3)
            self._timing_bar(surf, self.land_marker, 0.8)
        surf.blit(f.render("%.0f m" % (42.0 + self.power * 42.0), True, GOLD), (24, HUD_H + 14))

    def _timing_bar(self, surf, marker, sweet):
        bx, by, bw = WIDTH // 2 - 150, HEIGHT - 64, 300
        pygame.draw.rect(surf, PANEL2, (bx, by, bw, 26), border_radius=12)
        pygame.draw.rect(surf, mix(GOED, BG, 0.2), (bx + int(bw * (sweet - 0.09)), by, int(bw * 0.18), 26), border_radius=8)
        pygame.draw.circle(surf, GOLD, (bx + int(bw * clamp(marker, 0, 1)), by + 13), 12)


class Javelin(Event):
    name_key = "ev_javelin"
    instr_key = "in_javelin"
    unit = "m"
    lower_better = False
    winter = False
    MED = (82.0, 66.0, 50.0)
    RUNWAY = 100.0
    CAP = 12.0
    attempts = 3

    def reset(self):
        super().reset()
        self.speed = 0.0
        self.pos = 0.0
        self.last_side = 0
        self.phase = "run"        # run -> fly -> done
        self.angle_t = 0.0
        self.anim = 0.0           # loop-fase voor bob/animatie
        self.foul = False
        self.fly_t = 0.0
        self.fly_x = 0.0
        self.fly_y = 0.0
        self.vx = self.vy = 0.0

    def on_key(self, key):
        if not self.started or self.done:
            return
        if self.phase == "run":
            side = 0
            if key in (pygame.K_LEFT, pygame.K_a):
                side = -1
            elif key in (pygame.K_RIGHT, pygame.K_d):
                side = 1
            # C64-waggle: om-en-om duwen; sneller wisselen = hogere aanloop
            if side and side != self.last_side:
                self.last_side = side
                self.speed = min(self.CAP, self.speed + 0.62)
                self.sfx("step")
            if key == pygame.K_SPACE:
                self._throw()

    def _throw(self):
        if self.pos > self.RUNWAY:
            self.foul = True
            self.done = True
            self.value = 0.0
            self.sfx("bad")
            return
        ang = math.radians(20 + 50 * (0.5 + 0.5 * math.sin(self.angle_t * 3.0)))
        v = 8.0 + self.speed * 2.3
        self.vx = v * math.cos(ang)
        self.vy = v * math.sin(ang)
        self.phase = "fly"
        self.sfx("launch")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        if self.phase == "run":
            self.angle_t += dt
            # proportionele wrijving (C64-waggle): blijf om-en-om duwen
            self.speed = max(0.0, self.speed - (self.speed * 0.42 + 0.6) * dt)
            self.pos += self.speed * dt
            self.anim += self.speed * dt * 1.6
            if self.pos > self.RUNWAY + 6:
                self.foul = True
                self.done = True
                self.value = 0.0
                self.sfx("bad")
        elif self.phase == "fly":
            self.fly_t += dt
            self.vy -= 9.8 * dt * 1.4
            self.fly_x += self.vx * dt
            self.fly_y += self.vy * dt
            if self.fly_y <= 0 and self.fly_t > 0.05:
                self.value = self.fly_x
                self.done = True
                self.sfx("cheer")

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 140
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        f = pygame.font.Font(None, 40)
        ff = pygame.font.Font(None, 30)
        if self.phase == "run":
            frac = clamp(self.speed / self.CAP, 0.0, 1.0)
            # snel scrollende streepjes voor het vaartgevoel
            spacing = 64
            off = int((self.pos * 28) % spacing)
            for k in range(-1, WIDTH // spacing + 2):
                x = k * spacing - off
                pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.5), (x, gy + 40), (x + 26, gy + 40), 5)
            # vaartlijnen bij hoge snelheid
            if frac > 0.2:
                for i in range(int(frac * 9)):
                    ly = HUD_H + 30 + (i * 71) % (gy - HUD_H - 70)
                    lx = WIDTH + 160 - int(self.pos * 80 + i * 130) % (WIDTH + 160)
                    ln = int(30 + 70 * frac)
                    pygame.draw.line(surf, (255, 255, 255), (lx, ly), (lx + ln, ly), 2)
            foul_x = 120 + int((self.RUNWAY - self.pos) * 3.0)
            foul_x = min(foul_x, WIDTH - 30)
            pygame.draw.line(surf, RED, (foul_x, gy - 60), (foul_x, gy), 4)
            bob = int(math.sin(self.anim * 2) * (2 + 4 * frac))
            draw_athlete(surf, 120, gy + 6 - bob, 0.4 + 0.25 * frac, self.anim, GOED, 1.4)
            # snelheid + hoekmeter
            pygame.draw.rect(surf, PANEL2, (24, HUD_H + 90, 220, 18), border_radius=8)
            pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 90, int(220 * frac), 18), border_radius=8)
            surf.blit(ff.render("%.1f m/s" % self.speed, True, TEXT), (252, HUD_H + 88))
            ang = 20 + 50 * (0.5 + 0.5 * math.sin(self.angle_t * 3.0))
            ax, ay = WIDTH - 150, gy - 10
            ex = ax + int(70 * math.cos(math.radians(ang)))
            ey = ay - int(70 * math.sin(math.radians(ang)))
            pygame.draw.arc(surf, MUTED, (ax - 70, ay - 70, 140, 140), 0, math.pi / 2, 2)
            pygame.draw.line(surf, GOLD, (ax, ay), (ex, ey), 4)
            surf.blit(ff.render("%s: %d" % (t("hoek"), int(ang)), True, GOLD), (WIDTH - 200, gy - 110))
            surf.blit(ff.render(t("werp"), True, GOLD), (WIDTH // 2 - 40, HEIGHT - 60))
        elif self.phase == "fly":
            sx = 130 + int(self.fly_x * 6.0)
            sy = gy - int(self.fly_y * 6.0)
            ang = math.atan2(self.vy, self.vx)
            ex = sx + int(26 * math.cos(ang))
            ey = sy - int(26 * math.sin(ang))
            pygame.draw.line(surf, GOLD, (sx, sy), (ex, ey), 4)
            surf.blit(f.render("%.1f m" % self.fly_x, True, GOLD), (WIDTH // 2 - 50, 120))
        if self.foul:
            surf.blit(f.render(t("ongeldig"), True, RED), (WIDTH // 2 - 60, HEIGHT // 2))
        surf.blit(f.render("%.0f m" % (self.value if self.done else self.fly_x), True, GOLD), (24, HUD_H + 14))


class LongJump(Event):
    name_key = "ev_longjump"
    instr_key = "in_longjump"
    unit = "m"
    lower_better = False
    winter = False
    MED = (8.0, 6.5, 5.0)
    RUNWAY = 45.0
    CAP = 12.0
    attempts = 3

    def reset(self):
        super().reset()
        self.speed = 0.0
        self.pos = 0.0
        self.last_side = 0
        self.phase = "run"        # run -> fly -> done
        self.anim = 0.0
        self.foul = False
        self.takeoff_q = 0.0      # 0..1 kwaliteit van de afzet
        self.jump_dist = 0.0
        self.fly_t = 0.0
        self.fly_dur = 1.0
        self.fly_x = 0.0

    def on_key(self, key):
        if not self.started or self.done:
            return
        if self.phase == "run":
            side = 0
            if key in (pygame.K_LEFT, pygame.K_a):
                side = -1
            elif key in (pygame.K_RIGHT, pygame.K_d):
                side = 1
            # C64-waggle: om-en-om rammen voor de aanloop
            if side and side != self.last_side:
                self.last_side = side
                self.speed = min(self.CAP, self.speed + 0.62)
                self.sfx("step")
            if key == pygame.K_SPACE:
                self._jump()

    def _jump(self):
        if self.pos > self.RUNWAY:
            self.foul = True
            self.done = True
            self.value = 0.0
            self.sfx("bad")
            return
        d = self.RUNWAY - self.pos            # afstand tot de balk
        self.takeoff_q = clamp(1.0 - d / 6.0, 0.0, 1.0)  # binnen 6 m = goede afzet
        self.jump_dist = (self.speed / self.CAP) * 9.0 * (0.55 + 0.45 * self.takeoff_q)
        self.value = self.jump_dist
        self.fly_dur = 0.5 + self.jump_dist * 0.08
        self.phase = "fly"
        self.sfx("launch")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        if self.phase == "run":
            # proportionele wrijving (C64-waggle): blijf om-en-om rammen
            self.speed = max(0.0, self.speed - (self.speed * 0.42 + 0.6) * dt)
            self.pos += self.speed * dt
            self.anim += self.speed * dt * 1.6
            if self.pos > self.RUNWAY + 6:
                self.foul = True
                self.done = True
                self.value = 0.0
                self.sfx("bad")
        elif self.phase == "fly":
            self.fly_t += dt
            self.fly_x = self.jump_dist * clamp(self.fly_t / self.fly_dur, 0.0, 1.0)
            if self.fly_t >= self.fly_dur:
                self.done = True
                self.sfx("cheer")

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 140
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        f = pygame.font.Font(None, 40)
        ff = pygame.font.Font(None, 30)
        if self.phase == "run":
            frac = clamp(self.speed / self.CAP, 0.0, 1.0)
            # snel scrollende streepjes voor het vaartgevoel
            spacing = 64
            off = int((self.pos * 28) % spacing)
            for k in range(-1, WIDTH // spacing + 2):
                x = k * spacing - off
                pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.5), (x, gy + 40), (x + 26, gy + 40), 5)
            # vaartlijnen bij hoge snelheid
            if frac > 0.2:
                for i in range(int(frac * 9)):
                    ly = HUD_H + 30 + (i * 71) % (gy - HUD_H - 70)
                    lx = WIDTH + 160 - int(self.pos * 80 + i * 130) % (WIDTH + 160)
                    ln = int(30 + 70 * frac)
                    pygame.draw.line(surf, (255, 255, 255), (lx, ly), (lx + ln, ly), 2)
            # de afzetbalk komt in beeld; groene zone = goede afzet (laatste 6 m)
            bx = 150 + int((self.RUNWAY - self.pos) * 12)
            zx = 150 + int((self.RUNWAY - 6 - self.pos) * 12)
            if bx > 0 and zx < WIDTH:
                z0 = max(0, zx)
                z1 = min(WIDTH, bx)
                if z1 > z0:
                    pygame.draw.rect(surf, mix(GOED, TRACK, 0.35), (z0, gy, z1 - z0, 10))
            if 0 < bx < WIDTH:
                pygame.draw.line(surf, RED, (bx, gy - 50), (bx, gy), 5)
            # loper (bobt mee met de snelheid)
            bob = int(math.sin(self.anim * 2) * (2 + 4 * frac))
            draw_athlete(surf, 150, gy + 6 - bob, 0.4 + 0.25 * frac, self.anim, ACCENT, 1.4)
            # snelheidsbalk + m/s
            pygame.draw.rect(surf, PANEL2, (24, HUD_H + 90, 220, 18), border_radius=8)
            pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 90, int(220 * frac), 18), border_radius=8)
            surf.blit(ff.render("%.1f m/s" % self.speed, True, TEXT), (252, HUD_H + 88))
            surf.blit(ff.render(t("afzet"), True, GOLD), (WIDTH // 2 - 40, HEIGHT - 60))
            surf.blit(f.render("%.1f m" % self.pos, True, TEXT), (24, HUD_H + 14))
        elif self.phase == "fly":
            fr = clamp(self.fly_t / self.fly_dur, 0.0, 1.0)
            bx = 150
            land_x = min(WIDTH - 40, bx + int(self.jump_dist * 22))
            # zandbak na de balk
            pygame.draw.rect(surf, mix(GOLD, TRACK, 0.5), (bx, gy, land_x - bx + 30, HEIGHT - gy))
            pygame.draw.line(surf, RED, (bx, gy - 50), (bx, gy), 5)
            ax = bx + int((land_x - bx) * fr)
            ah = math.sin(math.pi * fr) * (40 + self.jump_dist * 8)
            draw_athlete(surf, ax, gy + 6 - int(ah), 0.6, self.anim + fr * 6, ACCENT, 1.4)
            surf.blit(f.render("%.2f m" % self.value, True, GOLD), (WIDTH // 2 - 50, 120))
        if self.foul:
            surf.blit(f.render(t("ongeldig"), True, RED), (WIDTH // 2 - 60, HEIGHT // 2))
        surf.blit(f.render("%.2f m" % self.value, True, GOLD), (24, HUD_H + 54))


class Hurdles(Event):
    name_key = "ev_hurdles"
    instr_key = "in_hurdles"
    unit = "s"
    lower_better = True
    winter = False
    MED = (12.5, 15.5, 19.0)
    DIST = 110.0
    CAP = 16.0
    JUMP_DUR = 0.45
    SCALE = 16        # pixels per meter in beeld

    def reset(self):
        super().reset()
        self.speed = 0.0
        self.dist = 0.0
        self.last_side = 0
        self.anim = 0.0
        self.jumping = False
        self.jump_t = 0.0
        self.hits = 0
        # 10 horden: eerste op 13.72 m, dan elke 9.14 m (atletiek-maten)
        self.hurdles = [13.72 + 9.14 * i for i in range(10)]
        self.next_h = 0

    def _airborne(self):
        return self.jumping and self.jump_t < self.JUMP_DUR

    def on_key(self, key):
        if not self.started or self.done:
            return
        side = 0
        if key in (pygame.K_LEFT, pygame.K_a):
            side = -1
        elif key in (pygame.K_RIGHT, pygame.K_d):
            side = 1
        if side and side != self.last_side:
            self.last_side = side
            self.speed = min(self.CAP, self.speed + 0.62)
            self.sfx("step")
        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and not self.jumping:
            self.jumping = True
            self.jump_t = 0.0
            self.sfx("launch")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        # proportionele wrijving (C64-waggle)
        self.speed = max(0.0, self.speed - (self.speed * 0.42 + 0.6) * dt)
        self.dist += self.speed * dt
        self.anim += self.speed * dt * 1.6
        if self.jumping:
            self.jump_t += dt
            if self.jump_t >= self.JUMP_DUR:
                self.jumping = False
        # horde-controle: passeer je een horde zonder te springen -> raak
        while self.next_h < len(self.hurdles) and self.dist >= self.hurdles[self.next_h]:
            if not self._airborne():
                self.hits += 1
                self.speed *= 0.45
                self.t += 0.5          # tijdstraf
                self.jumping = False
                self.sfx("bad")
            self.next_h += 1
        if self.dist >= self.DIST:
            self.done = True
            self.value = self.t
            self.sfx("cheer")

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 150
        frac = clamp(self.speed / self.CAP, 0.0, 1.0)
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        for lane in range(1, 5):
            pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.22), (0, gy + lane * 22), (WIDTH, gy + lane * 22), 1)
        # snel scrollende streepjes
        spacing = 64
        off = int((self.dist * 28) % spacing)
        for k in range(-1, WIDTH // spacing + 2):
            x = k * spacing - off
            pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.5), (x, gy + 46), (x + 26, gy + 46), 5)
        # vaartlijnen
        if frac > 0.2:
            for i in range(int(frac * 9)):
                ly = HUD_H + 30 + (i * 71) % (gy - HUD_H - 70)
                lx = WIDTH + 160 - int(self.dist * 80 + i * 130) % (WIDTH + 160)
                ln = int(30 + 70 * frac)
                pygame.draw.line(surf, (255, 255, 255), (lx, ly), (lx + ln, ly), 2)
        # horden tekenen (vanaf de huidige positie)
        for i, H in enumerate(self.hurdles):
            hx = 150 + int((H - self.dist) * self.SCALE)
            if -20 < hx < WIDTH + 20:
                col = MUTED if i < self.next_h else GOLD
                pygame.draw.line(surf, col, (hx, gy), (hx, gy - 34), 3)
                pygame.draw.line(surf, col, (hx + 10, gy), (hx + 10, gy - 34), 3)
                pygame.draw.line(surf, mix(col, (255, 255, 255), 0.4), (hx - 3, gy - 34), (hx + 13, gy - 34), 4)
        # finishlijn
        fx = 150 + int((self.DIST - self.dist) * self.SCALE)
        if -20 < fx < WIDTH + 20:
            for j in range(0, 40, 8):
                pygame.draw.rect(surf, (255, 255, 255), (fx, gy - 40 + j, 6, 4))
        # loper met sprong-boog
        jump_h = 0
        if self._airborne():
            jump_h = int(math.sin(math.pi * (self.jump_t / self.JUMP_DUR)) * 46)
        bob = 0 if jump_h else int(math.sin(self.anim * 2) * (2 + 4 * frac))
        draw_athlete(surf, 150, gy + 8 - bob - jump_h, 0.5 + 0.35 * frac, self.anim, ACCENT, 1.5)
        # HUD
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%.1f m" % self.dist, True, TEXT), (24, HUD_H + 14))
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 54))
        pygame.draw.rect(surf, PANEL2, (24, HUD_H + 100, 240, 20), border_radius=8)
        pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 100, int(240 * frac), 20), border_radius=8)
        surf.blit(pygame.font.Font(None, 26).render("%.1f m/s" % self.speed, True, TEXT), (276, HUD_H + 101))
        if self.hits:
            surf.blit(pygame.font.Font(None, 26).render("%s: %d" % (t("horde_raak"), self.hits), True, WARN), (WIDTH - 170, HUD_H + 16))


class HighJump(LongJump):
    name_key = "ev_highjump"
    instr_key = "in_highjump"
    unit = "m"
    MED = (2.10, 1.85, 1.55)
    RUNWAY = 40.0
    CAP = 12.0

    def _jump(self):
        if self.pos > self.RUNWAY:
            self.foul = True; self.done = True; self.value = 0.0; self.sfx("bad"); return
        d = self.RUNWAY - self.pos
        self.takeoff_q = clamp(1.0 - d / 5.0, 0.0, 1.0)
        self.jump_dist = (self.speed / self.CAP) * 2.45 * (0.55 + 0.45 * self.takeoff_q)
        self.value = self.jump_dist
        self.fly_dur = 0.75
        self.phase = "fly"
        self.sfx("launch")

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 140
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        f = pygame.font.Font(None, 40)
        ff = pygame.font.Font(None, 30)
        ppm = 120  # pixels per meter hoogte in beeld
        if self.phase == "run":
            frac = clamp(self.speed / self.CAP, 0.0, 1.0)
            spacing = 64
            off = int((self.pos * 28) % spacing)
            for k in range(-1, WIDTH // spacing + 2):
                x = k * spacing - off
                pygame.draw.line(surf, mix(TRACK, (255, 255, 255), 0.5), (x, gy + 40), (x + 26, gy + 40), 5)
            bx = 150 + int((self.RUNWAY - self.pos) * 12)
            zx = 150 + int((self.RUNWAY - 5 - self.pos) * 12)
            if bx > 0 and zx < WIDTH and bx > zx:
                pygame.draw.rect(surf, mix(GOED, TRACK, 0.35), (max(0, zx), gy, min(WIDTH, bx) - max(0, zx), 10))
            if 0 < bx < WIDTH:
                bh = 130
                pygame.draw.line(surf, MUTED, (bx, gy), (bx, gy - bh), 4)
                pygame.draw.line(surf, MUTED, (bx + 44, gy), (bx + 44, gy - bh), 4)
                pygame.draw.line(surf, GOLD, (bx, gy - bh), (bx + 44, gy - bh), 4)
                # mat achter de lat
                pygame.draw.rect(surf, mix(ACCENT, TRACK, 0.5), (bx + 50, gy - 24, 90, 24))
            bob = int(math.sin(self.anim * 2) * (2 + 4 * frac))
            draw_athlete(surf, 150, gy + 6 - bob, 0.4 + 0.25 * frac, self.anim, ACCENT, 1.4)
            pygame.draw.rect(surf, PANEL2, (24, HUD_H + 90, 220, 18), border_radius=8)
            pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 90, int(220 * frac), 18), border_radius=8)
            surf.blit(ff.render("%.1f m/s" % self.speed, True, TEXT), (252, HUD_H + 88))
            surf.blit(ff.render(t("afzet"), True, GOLD), (WIDTH // 2 - 40, HEIGHT - 60))
        elif self.phase == "fly":
            fr = clamp(self.fly_t / self.fly_dur, 0.0, 1.0)
            bx = 170
            bar_y = gy - int(self.jump_dist * ppm)
            pygame.draw.line(surf, MUTED, (bx + 50, gy), (bx + 50, bar_y), 4)
            pygame.draw.line(surf, GOLD, (bx + 20, bar_y), (bx + 80, bar_y), 4)
            pygame.draw.rect(surf, mix(ACCENT, TRACK, 0.5), (bx + 86, gy - 24, 90, 24))
            peak = self.jump_dist * ppm + 30
            ax = bx + int(fr * 110)
            ah = math.sin(math.pi * fr) * peak
            draw_athlete(surf, ax, gy + 6 - int(ah), 0.6, self.anim + fr * 6, ACCENT, 1.4)
            surf.blit(f.render("%.2f m" % self.value, True, GOLD), (WIDTH // 2 - 50, 120))
        if self.foul:
            surf.blit(f.render(t("ongeldig"), True, RED), (WIDTH // 2 - 60, HEIGHT // 2))
        surf.blit(f.render("%s: %.2f m" % (t("lat"), self.value), True, GOLD), (24, HUD_H + 14))


class Discus(Javelin):
    name_key = "ev_discus"
    instr_key = "in_discus"
    MED = (65.0, 52.0, 40.0)
    RUNWAY = 20.0

    def _throw(self):
        if self.pos > self.RUNWAY:
            self.foul = True; self.done = True; self.value = 0.0; self.sfx("bad"); return
        ang = math.radians(15 + 45 * (0.5 + 0.5 * math.sin(self.angle_t * 3.0)))
        v = 7.0 + self.speed * 2.2
        self.vx = v * math.cos(ang)
        self.vy = v * math.sin(ang)
        self.phase = "fly"
        self.sfx("launch")


class Swim(Sprint):
    name_key = "ev_swim"
    instr_key = "in_swim"
    MED = (12.5, 16.0, 21.0)
    DIST = 100.0
    CAP = 11.0
    BREATH_INT = 2.2
    LAP_LEN = 50.0           # 2 banen van 50 m = heen en terug

    def reset(self):
        super().reset()
        self.breath_t = 0.0
        self.breath_open = False
        self.breath_win = 0.0
        self.breaths = 0
        self.lap = 0
        self.turn_flash = 0.0

    def on_key(self, key):
        super().on_key(key)
        if self.started and not self.done and key in (pygame.K_UP, pygame.K_w):
            if self.breath_open:
                self.speed = min(self.CAP, self.speed + 0.7)
                self.breaths += 1
                self.breath_open = False
                self.sfx("step")

    def update(self, dt, keys):
        if self.started and not self.done:
            self.breath_t += dt
            if self.breath_t >= self.BREATH_INT:
                self.breath_t = 0.0
                self.breath_open = True
                self.breath_win = 0.0
            if self.breath_open:
                self.breath_win += dt
                if self.breath_win > 0.7:
                    self.breath_open = False
            self.turn_flash = max(0.0, self.turn_flash - dt)
        super().update(dt, keys)
        # keerpunt bij elke 50 m
        lap_now = min(int(self.dist / self.LAP_LEN), int(self.DIST / self.LAP_LEN) - 1)
        if lap_now > self.lap:
            self.lap = lap_now
            self.turn_flash = 0.8
            self.sfx("step")

    def draw_world(self, surf):
        water = (38, 92, 150)
        for i in range(HUD_H, HEIGHT, 4):
            c = mix((30, 70, 120), (52, 120, 184), (i - HUD_H) / (HEIGHT - HUD_H))
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        frac = clamp(self.speed / self.CAP, 0.0, 1.0)
        # baanlijnen + golfjes die meescrollen
        for lane in range(1, 5):
            ly = HUD_H + lane * ((HEIGHT - HUD_H) // 5)
            pygame.draw.line(surf, mix(water, (255, 255, 255), 0.25), (0, ly), (WIDTH, ly), 2)
        face = 1 if self.lap % 2 == 0 else -1
        spacing = 60
        off = int((self.dist * 24) % spacing)
        for k in range(-1, WIDTH // spacing + 2):
            x = k * spacing - off * face   # terugbaan = achtergrond andere kant op
            for ly in range(HUD_H + 40, HEIGHT - 20, 70):
                pygame.draw.arc(surf, mix(water, (255, 255, 255), 0.4), (x, ly, 22, 14), 0, math.pi, 2)
        # baan + richting: even baan = heen (hoofd rechts), oneven = terug (hoofd links)
        total_laps = int(self.DIST / self.LAP_LEN)
        sy = HEIGHT // 2 + 40 + int(math.sin(self.phase * 2) * 3)
        sx = WIDTH // 2 + (1 if face >= 0 else -1) * int(frac * 30)   # blijft in beeld, schuift mee met richting
        self._draw_swimmer(surf, sx, sy, face)
        # ademhaling-boei
        if self.breath_open:
            self._text_blit(surf, "ADEM!", GOLD, WIDTH // 2, 90)
            pygame.draw.circle(surf, GOLD, (WIDTH // 2, 130), 12)
        # keerpunt-flits
        if self.turn_flash > 0:
            self._text_blit(surf, "KEER!", GOLD, WIDTH // 2, HEIGHT // 2 - 60)
        # HUD
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%s %d/%d" % (t("baan"), self.lap + 1, total_laps), True, ACCENT), (WIDTH - 200, HUD_H + 14))
        surf.blit(f.render("%.1f m" % self.dist, True, TEXT), (24, HUD_H + 14))
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 54))
        pygame.draw.rect(surf, PANEL2, (24, HUD_H + 100, 240, 20), border_radius=8)
        pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 100, int(240 * frac), 20), border_radius=8)
        surf.blit(pygame.font.Font(None, 26).render("%.1f m/s" % self.speed, True, TEXT), (276, HUD_H + 101))

    def _text_blit(self, surf, txt, color, cx, cy):
        ff = pygame.font.Font(None, 44)
        img = ff.render(txt, True, color)
        surf.blit(img, img.get_rect(center=(cx, cy)))

    def _draw_swimmer(self, surf, sx, sy, face=1):
        # face = 1 (kijkt naar rechts, heenweg) of -1 (gespiegeld, terugweg)
        body = (240, 220, 120)
        skin = (236, 198, 168)
        cap = (90, 150, 210)
        ph = self.phase
        F = 1 if face >= 0 else -1
        def X(ox):
            return sx + F * ox
        # getapeerde romp: schouders (voorkant) breed, heupen (achter) smal
        body_pts = [(X(20), sy - 6), (X(20), sy + 6), (X(-24), sy + 3), (X(-24), sy - 3)]
        pygame.draw.polygon(surf, body, body_pts)
        # twee benen met scissor-flutterkick (tegengesteld = natuurlijk)
        k = math.sin(ph * 3.2) * 7
        pygame.draw.line(surf, body, (X(-24), sy - 2), (X(-50), sy - 4 - k), 5)
        pygame.draw.line(surf, body, (X(-24), sy + 2), (X(-50), sy + 4 + k), 5)
        pygame.draw.line(surf, skin, (X(-50), sy - 4 - k), (X(-56), sy - 4 - k), 4)  # voet
        pygame.draw.line(surf, skin, (X(-50), sy + 4 + k), (X(-56), sy + 4 + k), 4)
        # twee armen draaien als molens, precies in tegenfase
        a = ph * 2.4
        shx, shy = X(10), sy - 2
        for arm in (0, math.pi):
            ang = a + arm
            ex = shx + F * int(math.cos(ang) * 22)
            ey = shy - int(math.sin(ang) * 24)
            acol = mix(skin, (255, 255, 255), 0.3) if math.sin(ang) > 0 else mix(skin, body, 0.4)
            pygame.draw.line(surf, acol, (shx, shy), (ex, ey), 5)
            pygame.draw.circle(surf, acol, (ex, ey), 3)
        # hoofd (iets gedraaid om te ademen) + badmuts
        hx, hy = X(26), sy - 3
        pygame.draw.circle(surf, skin, (hx, hy), 7)
        pygame.draw.circle(surf, cap, (hx + F, hy - 3), 6)
        # boeggolfje + spatten vooraan
        pygame.draw.arc(surf, (255, 255, 255), (min(X(-4), X(20)), sy + 2, 24, 12), 0.2, math.pi - 0.2, 2)
        if (ph % 1.0) < 0.5:
            pygame.draw.circle(surf, (255, 255, 255), (X(-58), sy + 4 + k), 2)


class WeightLift(Event):
    name_key = "ev_weight"
    instr_key = "in_weight"
    unit = "kg"
    lower_better = False
    winter = False
    MED = (150.0, 120.0, 90.0)
    attempts = 3

    def reset(self):
        super().reset()
        self.phase = "pull"      # pull -> jerk -> done
        self.marker = 0.0
        self.osc = 2.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.phase_t = 0.0
        self.flash = 0.0

    def _marker_val(self):
        return 0.5 + 0.5 * math.sin(self.marker)

    def _quality(self):
        return clamp((self._marker_val() - 0.5) * 2.0, 0.0, 1.0)

    def on_key(self, key):
        if not self.started or self.done:
            return
        if key == pygame.K_SPACE:
            self.flash = 0.3
            if self.phase == "pull":
                self.q1 = self._quality()
                self.phase = "jerk"
                self.phase_t = 0.0
                self.osc = 2.7
                self.sfx("step")
            elif self.phase == "jerk":
                self.q2 = self._quality()
                self._finish()

    def _finish(self):
        self.value = float(round(60.0 + 90.0 * (0.5 * self.q1 + 0.5 * self.q2)))
        self.done = True
        self.sfx("cheer" if self.medal() else "good")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        self.phase_t += dt
        self.marker += self.osc * dt
        self.flash = max(0.0, self.flash - dt * 3)
        if self.phase_t > 8.0:   # auto-lock zodat het nooit blijft hangen
            if self.phase == "pull":
                self.q1 = self._quality(); self.phase = "jerk"; self.phase_t = 0.0; self.osc = 2.7
            else:
                self.q2 = self._quality(); self._finish()

    def draw_world(self, surf):
        _bg_sky(surf, False)
        gy = HEIGHT - 120
        pygame.draw.rect(surf, TRACK, (0, gy, WIDTH, HEIGHT - gy))
        ff = pygame.font.Font(None, 32)
        f2 = pygame.font.Font(None, 44)
        bx = WIDTH // 2 - 30
        by = 110
        bw = 60
        bh = 300
        pygame.draw.rect(surf, PANEL2, (bx, by, bw, bh), border_radius=8)
        gz = int(bh * 0.18)
        pygame.draw.rect(surf, mix(GOED, PANEL2, 0.35), (bx, by, bw, gz), border_radius=8)
        v = self._marker_val()
        my = by + int((1.0 - v) * bh)
        col = GOLD if self.flash > 0 else WARN
        pygame.draw.rect(surf, col, (bx - 14, my - 6, bw + 28, 12), border_radius=4)
        label = t("trek") if self.phase == "pull" else t("stoot")
        img = ff.render(label, True, ACCENT)
        surf.blit(img, img.get_rect(center=(WIDTH // 2, 70)))
        draw_athlete(surf, WIDTH // 2 + 220, gy + 6, 0.2, 0.0, ACCENT, 1.7)
        surf.blit(f2.render("%d kg" % int(self.value), True, GOLD), (24, HUD_H + 14))
        # voortgang van de eerste lock
        c1 = GOED if self.phase != "pull" else MUTED
        surf.blit(ff.render("1: %d%%" % int(self.q1 * 100), True, c1), (24, HUD_H + 54))


class _Downhill(Event):
    """Gedeelde basis voor bobslee/slalom: afdaling met sturen (ingedrukte toetsen)."""
    unit = "s"
    lower_better = True
    winter = True
    DIST = 150.0
    TW = 115          # halve baanbreedte in px
    STEER = 260.0     # px/s
    PPM = 7.0         # pixels per meter (voor diepte in beeld)
    VMAX = 34.0

    def reset(self):
        super().reset()
        self.d = 0.0
        self.px = 0.0
        self.speed = 16.0
        self.scr = 0.0

    def _center(self, dist):
        return math.sin(dist * 0.045) * 95.0

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.px -= self.STEER * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.px += self.STEER * dt
        self.scr = max(0.0, self.scr - dt * 3)
        self._advance(dt)
        if self.d >= self.DIST:
            self.done = True
            self.value = self.t
            self.sfx("cheer")

    def _advance(self, dt):
        self.speed = min(self.VMAX, self.speed + 6.0 * dt)
        self.d += self.speed * dt

    def _draw_track(self, surf, gate_at=None):
        cx = WIDTH // 2
        sled_y = HEIGHT - 130
        top = HUD_H + 10
        # baanranden (van veraf naar dichtbij)
        prev = None
        for y in range(top, sled_y + 1, 10):
            dd = self.d + (sled_y - y) * self.PPM / 8.0
            c = cx + int(self._center(dd))
            scale = 0.5 + 0.5 * (y - top) / (sled_y - top)
            hw = int(self.TW * scale)
            left = (c - hw, y)
            right = (c + hw, y)
            if prev:
                pygame.draw.line(surf, mix(SNOW, (255, 255, 255), 0.5), prev[0], left, 3)
                pygame.draw.line(surf, mix(SNOW, (255, 255, 255), 0.5), prev[1], right, 3)
                pygame.draw.polygon(surf, mix(SNOW, ACCENT, 0.12), [prev[0], left, right, prev[1]])
            prev = (left, right)


class Bobsled(_Downhill):
    name_key = "ev_bobsled"
    instr_key = "in_bobsled"
    MED = (5.6, 7.5, 11.0)

    def reset(self):
        super().reset()
        self.hits = 0

    def _advance(self, dt):
        self.speed = min(self.VMAX, self.speed + 7.0 * dt)
        c = self._center(self.d)
        if self.px < c - self.TW:
            self.px = c - self.TW; self.speed *= 0.90; self.scr = 0.4; self.hits += 1; self.sfx("bad")
        elif self.px > c + self.TW:
            self.px = c + self.TW; self.speed *= 0.90; self.scr = 0.4; self.hits += 1; self.sfx("bad")
        self.d += self.speed * dt

    def draw_world(self, surf):
        for i in range(HUD_H, HEIGHT, 4):
            c = mix(SKY_W, SNOW, (i - HUD_H) / (HEIGHT - HUD_H))
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        self._draw_track(surf)
        cx = WIDTH // 2
        sled_y = HEIGHT - 130
        sx = cx + int(self.px)
        col = RED if self.scr > 0 else ACCENT
        pygame.draw.rect(surf, col, (sx - 12, sled_y - 24, 24, 44), border_radius=6)
        pygame.draw.circle(surf, (236, 198, 168), (sx, sled_y - 30), 7)
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 14))
        surf.blit(f.render("%.0f%%" % (100 * self.d / self.DIST), True, TEXT), (24, HUD_H + 54))


class Slalom(_Downhill):
    name_key = "ev_slalom"
    instr_key = "in_slalom"
    MED = (6.5, 8.5, 12.0)
    DIST = 150.0

    def reset(self):
        super().reset()
        self.gates = [(18.0 + 13.0 * i, (1 if i % 2 == 0 else -1)) for i in range(10)]
        self.next_g = 0
        self.misses = 0

    def _advance(self, dt):
        self.speed = min(30.0, self.speed + 5.0 * dt)
        self.d += self.speed * dt
        while self.next_g < len(self.gates) and self.d >= self.gates[self.next_g][0]:
            gd, side = self.gates[self.next_g]
            target = self._center(gd) + side * 55
            if abs(self.px - target) > 48:
                self.misses += 1
                self.t += 0.8
                self.scr = 0.4
                self.sfx("bad")
            self.next_g += 1

    def draw_world(self, surf):
        for i in range(HUD_H, HEIGHT, 4):
            c = mix(SKY_W, SNOW, (i - HUD_H) / (HEIGHT - HUD_H))
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        self._draw_track(surf)
        cx = WIDTH // 2
        sled_y = HEIGHT - 130
        # poortjes die in beeld zijn
        for gd, side in self.gates:
            dy = (gd - self.d)
            if 0 <= dy < 60:
                y = sled_y - int(dy / self.PPM * 8.0)
                if HUD_H < y < sled_y:
                    gx = cx + int(self._center(gd) + side * 55)
                    pcol = RED if side > 0 else ACCENT
                    pygame.draw.line(surf, pcol, (gx - 18, y), (gx - 18, y - 26), 4)
                    pygame.draw.line(surf, pcol, (gx + 18, y), (gx + 18, y - 26), 4)
        sx = cx + int(self.px)
        col = RED if self.scr > 0 else GOLD
        draw_athlete(surf, sx, sled_y, 0.0, self.t * 6, col, 1.2)
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 14))
        if self.misses:
            surf.blit(pygame.font.Font(None, 28).render("%s: %d" % (t("poort_mis"), self.misses), True, WARN),
                      (WIDTH - 210, HUD_H + 16))


class Biathlon(Event):
    name_key = "ev_biathlon"
    instr_key = "in_biathlon"
    unit = "s"
    lower_better = True
    winter = True
    MED = (18.0, 24.0, 32.0)
    SKI_DIST = 45.0           # per ski-ronde
    CAP = 14.0
    ROUNDS = 2               # 2x (langlaufen + 5 schoten), zoals echte biatlon

    def reset(self):
        super().reset()
        self.phase = "ski"       # ski -> shoot -> (volgende ronde) -> done
        self.round = 0
        self.speed = 0.0
        self.dist = 0.0
        self.last_side = 0
        self.anim = 0.0
        self.aim_t = 0.0
        self.shots = 5
        self.misses = 0
        self.flash = ""
        self.flash_t = 0.0

    def on_key(self, key):
        if not self.started or self.done:
            return
        if self.phase == "ski":
            side = 0
            if key in (pygame.K_LEFT, pygame.K_a):
                side = -1
            elif key in (pygame.K_RIGHT, pygame.K_d):
                side = 1
            if side and side != self.last_side:
                self.last_side = side
                self.speed = min(self.CAP, self.speed + 0.62)
                self.sfx("step")
        elif self.phase == "shoot":
            if key == pygame.K_SPACE and self.shots > 0:
                cross = math.sin(self.aim_t * 2.4)
                if abs(cross) < 0.18:
                    self.flash = t("raak2")
                    self.sfx("step")
                else:
                    self.misses += 1
                    self.t += 3.0      # strafrondje
                    self.flash = t("mis2")
                    self.sfx("bad")
                self.flash_t = 0.6
                self.shots -= 1
                if self.shots <= 0:
                    if self.round < self.ROUNDS - 1:
                        self.round += 1
                        self.phase = "ski"
                        self.dist = 0.0
                        self.speed = 0.0
                        self.last_side = 0
                    else:
                        self.done = True
                        self.value = self.t
                        self.sfx("cheer")

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        self.flash_t = max(0.0, self.flash_t - dt)
        if self.phase == "ski":
            self.speed = max(0.0, self.speed - (self.speed * 0.42 + 0.6) * dt)
            self.dist += self.speed * dt
            self.anim += self.speed * dt * 1.6
            if self.dist >= self.SKI_DIST:
                self.phase = "shoot"
                self.shots = 5
                self.aim_t = 0.0
        elif self.phase == "shoot":
            self.aim_t += dt

    def draw_world(self, surf):
        for i in range(HUD_H, HEIGHT, 4):
            c = mix(SKY_W, SNOW, (i - HUD_H) / (HEIGHT - HUD_H))
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        gy = HEIGHT - 150
        f = pygame.font.Font(None, 40)
        ff = pygame.font.Font(None, 30)
        if self.phase == "ski":
            frac = clamp(self.speed / self.CAP, 0.0, 1.0)
            pygame.draw.rect(surf, mix(SNOW, (255, 255, 255), 0.3), (0, gy, WIDTH, HEIGHT - gy))
            spacing = 64
            off = int((self.dist * 28) % spacing)
            for k in range(-1, WIDTH // spacing + 2):
                x = k * spacing - off
                pygame.draw.line(surf, mix(SNOW, ACCENT, 0.3), (x, gy + 44), (x + 26, gy + 44), 4)
            bob = int(math.sin(self.anim * 2) * (2 + 4 * frac))
            draw_athlete(surf, 150, gy + 6 - bob, 0.45 + 0.3 * frac, self.anim, ACCENT, 1.4)
            pygame.draw.rect(surf, PANEL2, (24, HUD_H + 90, 220, 18), border_radius=8)
            pygame.draw.rect(surf, GOLD if frac > 0.85 else GOED, (24, HUD_H + 90, int(220 * frac), 18), border_radius=8)
            surf.blit(ff.render("%.0f / %.0f m" % (self.dist, self.SKI_DIST), True, TEXT), (252, HUD_H + 88))
        else:
            # schietbaan: doelwit + bewegend kruis
            cxp = WIDTH // 2
            ty = HEIGHT // 2
            pygame.draw.circle(surf, PANEL2, (cxp, ty), 70)
            pygame.draw.circle(surf, mix(GOED, PANEL2, 0.4), (cxp, ty), 40)
            pygame.draw.circle(surf, GOLD, (cxp, ty), 16)
            cross = math.sin(self.aim_t * 2.4)
            xx = cxp + int(cross * 130)
            pygame.draw.line(surf, RED, (xx - 14, ty), (xx + 14, ty), 3)
            pygame.draw.line(surf, RED, (xx, ty - 14), (xx, ty + 14), 3)
            self._mid(surf, "%s %d" % (t("schot"), 5 - self.shots + 1) if self.shots else t("schot"), ACCENT, ty - 110, 30)
            if self.flash_t > 0:
                self._mid(surf, self.flash, GOLD if self.flash == t("raak2") else WARN, ty + 110, 40)
        surf.blit(f.render("%.2f s" % self.t, True, GOLD), (24, HUD_H + 14))
        surf.blit(ff.render("%s %d/%d" % (t("ronde"), self.round + 1, self.ROUNDS), True, ACCENT), (24, HUD_H + 54))
        if self.misses:
            surf.blit(ff.render("%s: %d" % (t("mis2"), self.misses), True, WARN), (WIDTH - 170, HUD_H + 16))

    def _mid(self, surf, txt, color, y, size):
        ff = pygame.font.Font(None, size)
        img = ff.render(txt, True, color)
        surf.blit(img, img.get_rect(center=(WIDTH // 2, y)))


class FigureSkating(Event):
    name_key = "ev_figure"
    instr_key = "in_figure"
    unit = "p"
    lower_better = False
    winter = True
    MED = (900.0, 650.0, 400.0)
    WINDOW = 0.45            # timing-venster (s)

    _KEYS = [
        (pygame.K_LEFT, "L"), (pygame.K_RIGHT, "R"),
        (pygame.K_UP, "U"), (pygame.K_DOWN, "D"),
    ]

    def reset(self):
        super().reset()
        self.value = 0.0
        self.combo = 0
        self.best_combo = 0
        self.cur = 0
        self.flash = ""
        self.flash_t = 0.0
        # vaste reeks van 14 moves (deterministisch, eerlijk voor 2 spelers)
        seq = [0, 1, 2, 3, 1, 0, 3, 2, 0, 1, 2, 1, 3, 0]
        self.moves = [(self._KEYS[k][0], self._KEYS[k][1], 1.2 + 0.8 * i) for i, k in enumerate(seq)]

    def _expected(self):
        if 0 <= self.cur < len(self.moves):
            return self.moves[self.cur]
        return None

    def on_key(self, key):
        if not self.started or self.done:
            return
        m = self._expected()
        if m is None:
            return
        ekey, _lbl, due = m
        if key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            if key == ekey and abs(self.t - due) <= self.WINDOW:
                closeness = 1.0 - abs(self.t - due) / self.WINDOW
                self.combo += 1
                self.best_combo = max(self.best_combo, self.combo)
                self.value += 40 + 60 * closeness + self.combo * 4
                self.flash = t("perfect") if closeness > 0.7 else t("goed")
                self.sfx("step")
                self.cur += 1
            else:
                self.combo = 0
                self.flash = t("mis2")
                self.sfx("bad")
            self.flash_t = 0.4

    def update(self, dt, keys):
        if self.done:
            return
        if not self.tick_countdown(dt):
            return
        self.t += dt
        self.flash_t = max(0.0, self.flash_t - dt)
        m = self._expected()
        if m is not None and self.t > m[2] + self.WINDOW:
            # gemist
            self.combo = 0
            self.cur += 1
        if self.cur >= len(self.moves):
            self.done = True
            self.value = float(round(self.value))
            self.sfx("cheer" if self.medal() else "good")

    def draw_world(self, surf):
        for i in range(HUD_H, HEIGHT, 4):
            c = mix(SKY_W, mix(ACCENT, SNOW, 0.5), (i - HUD_H) / (HEIGHT - HUD_H))
            pygame.draw.rect(surf, c, (0, i, WIDTH, 4))
        cx = WIDTH // 2
        cy = HEIGHT // 2
        # schaatser draait mee
        draw_athlete(surf, cx, cy + 80, math.sin(self.t * 3) * 0.4, self.t * 5, GOLD, 1.6)
        m = self._expected()
        if m is not None:
            _k, lbl, due = m
            arrow = {"L": "<", "R": ">", "U": "^", "D": "v"}.get(lbl, lbl)
            # timing-ring krimpt naar het juiste moment
            dtq = clamp(abs(self.t - due) / 1.0, 0.0, 1.0)
            r = int(30 + 60 * dtq)
            col = GOED if abs(self.t - due) <= self.WINDOW else MUTED
            pygame.draw.circle(surf, col, (cx, cy - 40), r, 3)
            bf = pygame.font.Font(None, 90)
            img = bf.render(arrow, True, GOLD)
            surf.blit(img, img.get_rect(center=(cx, cy - 40)))
        f = pygame.font.Font(None, 40)
        surf.blit(f.render("%d %s" % (int(self.value), t("punten")), True, GOLD), (24, HUD_H + 14))
        if self.combo > 1:
            surf.blit(pygame.font.Font(None, 30).render("combo x%d" % self.combo, True, ACCENT), (24, HUD_H + 54))
        if self.flash_t > 0:
            ff = pygame.font.Font(None, 48)
            col = GOLD if self.flash in (t("perfect"), t("goed")) else WARN
            img = ff.render(self.flash, True, col)
            surf.blit(img, img.get_rect(center=(cx, cy + 150)))


EVENT_CLASSES = [Skate, SkiJump, Bobsled, Slalom, Biathlon, FigureSkating,
                 Sprint, Javelin, LongJump, Hurdles, HighJump, Discus, Swim, WeightLift]


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

        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)

        self.players = 1
        self.paused = False
        self.attempt = 0           # huidige poging (veld-onderdelen)
        self.best_value = None     # beste resultaat over de pogingen
        self.season = "summer"     # "winter" of "summer"
        self.help_season = "winter"
        self.lan = None            # net.NetPeer als LAN actief is
        self.lan_role = 0          # 0 = host (speler 1), 1 = client (speler 2)
        self.lan_status = ""       # statusregel op lobby-/wachtscherm
        self.lan_ip_text = ""      # ingetypt IP bij handmatig verbinden
        self.lan_hosts = []        # gevonden hosts bij discovery
        self.queue = []            # lijst van event-indices
        self.qpos = 0
        self.q_roundlen = 0        # onderdelen per ronde (toernooi met rondes)
        self.cur_player = 0
        self.ev = None
        self.results = {}          # (player, qpos) -> value
        self.last_value = None
        self.last_medal = None
        self.last_record = False

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
        if self.state == "play":
            self.sfx.start_music("play")
        elif self.state == "tally":
            self.sfx.start_music("victory")
        else:
            self.sfx.start_music("menu")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        self.paused = False
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

    # ---------- flow ----------
    def start_queue(self, indices):
        self.queue = list(indices)
        self.qpos = 0
        self.cur_player = 0
        self.results = {}
        self.begin_announce()

    def begin_announce(self):
        self.ev = EVENT_CLASSES[self.queue[self.qpos]](self)
        self.set_state("announce")

    def begin_play(self):
        self.ev.reset()
        self.attempt = 0
        self.best_value = None
        self.set_state("play")

    def _register_attempt(self):
        """Houd het beste resultaat over de pogingen bij (geldig = >0)."""
        v = self.ev.value
        if self.best_value is None:
            self.best_value = v
        elif self.ev.lower_better:
            if v > 0 and (self.best_value <= 0 or v < self.best_value):
                self.best_value = v
        else:
            self.best_value = max(self.best_value, v)

    def finish_event(self):
        idx = self.queue[self.qpos]
        self.value_into_results(idx)
        self.set_state("result")

    def value_into_results(self, idx):
        # sleutel op qpos zodat herhaalde onderdelen (toernooi-rondes) niet overschrijven
        self.results[(self.cur_player, self.qpos)] = self.ev.value
        self.last_value = self.ev.value
        self.last_medal = self.ev.medal()
        # record bijhouden (alleen 1 speler en niet ongeldig)
        rec = self.cfg["records"].get(str(idx))
        self.last_record = False
        ev = self.ev
        valid = ev.value > 0 or ev.unit == "s"
        if valid:
            better = (rec is None) or (ev.value < rec if ev.lower_better else ev.value > rec)
            if better:
                self.cfg["records"][str(idx)] = ev.value
                self.last_record = True
                save_config(self.cfg)

    def after_result(self):
        if self.players == 2 and self.cur_player == 0:
            self.cur_player = 1
            self.ev.reset()
            self.set_state("announce")
            return
        # volgende event
        self.cur_player = 0
        self.qpos += 1
        if self.qpos >= len(self.queue):
            self.set_state("tally")
        else:
            self.begin_announce()

    # ---------- seizoen ----------
    def _season_indices(self, season=None):
        season = season or self.season
        want = (season == "winter")
        return [i for i, ec in enumerate(EVENT_CLASSES) if ec.winter == want]

    # ---------- LAN ----------
    def _lan_close(self):
        if self.lan:
            try:
                self.lan.close()
            except Exception:
                pass
        self.lan = None

    def _lan_ip_key(self, key):
        if key == pygame.K_ESCAPE:
            self.set_state("lan_lobby")
            return
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._action("lan_connect")
            return
        if key == pygame.K_BACKSPACE:
            self.lan_ip_text = self.lan_ip_text[:-1]
            return
        if len(self.lan_ip_text) >= 21:
            return
        digit_map = {
            pygame.K_0: "0", pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
            pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7",
            pygame.K_8: "8", pygame.K_9: "9",
            pygame.K_KP0: "0", pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3",
            pygame.K_KP4: "4", pygame.K_KP5: "5", pygame.K_KP6: "6", pygame.K_KP7: "7",
            pygame.K_KP8: "8", pygame.K_KP9: "9",
            pygame.K_PERIOD: ".", pygame.K_KP_PERIOD: ".",
        }
        ch = digit_map.get(key)
        if ch:
            self.lan_ip_text += ch

    def _lan_discover(self):
        """Zoekt op de achtergrond naar hosts; joint de eerste of meldt 'niets'."""
        hosts = []
        try:
            hosts = netmod.NetPeer.discover()
        except Exception:
            hosts = []
        self.lan_hosts = hosts
        if hosts:
            self._lan_join(hosts[0])
        else:
            self.lan_status = t("lan_geen_host")

    def _lan_join(self, ip):
        if netmod is None:
            return
        self._lan_close()
        self.lan = netmod.NetPeer()
        self.lan_role = 1
        self.players = 2
        self.lan.join(ip)
        self.lan_status = t("lan_verbinden")
        self.set_state("lan_wait")

    # ---------- input ----------
    def _action(self, a):
        if a is None:
            return
        if self.sfx:
            self.sfx.play("click")
        if a == "play":
            self.set_state("modeselect")
        elif a == "p1":
            self.players = 1
            self.set_state("seasonselect")
        elif a == "p2":
            self.players = 2
            self.set_state("seasonselect")
        elif a == "season_winter":
            self.season = "winter"
            self.set_state("eventselect")
        elif a == "season_summer":
            self.season = "summer"
            self.set_state("eventselect")
        elif a == "to_seasonselect":
            self.set_state("seasonselect")
        elif a == "help_winter":
            self.help_season = "winter"
        elif a == "help_summer":
            self.help_season = "summer"
        elif a == "p_lan":
            if netmod is None:
                self.lan_status = t("lan_niet_beschikbaar")
                self.set_state("lan_lobby")
            else:
                self.lan_status = ""
                self.set_state("lan_lobby")
        elif a == "lan_host":
            if netmod is not None:
                self._lan_close()
                self.lan = netmod.NetPeer()
                self.lan_role = 0
                self.players = 2
                self.lan.host()
                self.lan_status = "%s: %s" % (t("lan_jouw_ip"), netmod.local_ip())
                self.set_state("lan_wait")
        elif a == "lan_find":
            if netmod is not None:
                self.lan_status = t("lan_zoeken")
                threading.Thread(target=self._lan_discover, daemon=True).start()
        elif a == "lan_manual":
            self.lan_ip_text = ""
            self.set_state("lan_ip")
        elif a == "lan_connect":
            ip = self.lan_ip_text.strip()
            if ip:
                self._lan_join(ip)
        elif a == "lan_manual_back":
            self.set_state("lan_lobby")
        elif a == "lan_cancel":
            self._lan_close()
            self.set_state("modeselect")
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "back_title":
            self.set_state("title")
        elif a == "to_modeselect":
            self.set_state("modeselect")
        elif a == "to_eventselect":
            self.set_state("eventselect")
        elif a.startswith("ev_"):
            self.q_roundlen = 0
            self.start_queue([int(a[3:])])
        elif a == "tournament":
            idxs = self._season_indices()
            self.q_roundlen = len(idxs)
            self.start_queue(idxs)
        elif a == "tournament3":
            idxs = self._season_indices()
            self.q_roundlen = len(idxs)
            self.start_queue(idxs * 3)
        elif a == "start_play":
            self.begin_play()
        elif a == "pause":
            self.paused = True
        elif a == "resume":
            self.paused = False
        elif a == "quit_to_menu":
            self.paused = False
            self.set_state("title")
        elif a == "result_next":
            self.after_result()
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

    def _nav_keys(self, key):
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

    def on_key(self, key):
        if self.state == "play" and self.ev:
            if self.paused:
                if key in (pygame.K_ESCAPE, pygame.K_p):
                    self._action("resume")
                else:
                    self._nav_keys(key)
                return
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
                return
            self.ev.on_key(key)
            return
        if self.state == "lan_ip":
            self._lan_ip_key(key)
            return
        if self.state in ("lan_lobby", "lan_wait") and key == pygame.K_ESCAPE:
            self._action("lan_cancel")
            return
        if self.state == "announce" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("start_play"); return
        if self.state == "result" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("result_next"); return
        if self.state == "tally" and key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            self._action("back_title"); return
        if key == pygame.K_ESCAPE:
            back = {"modeselect": "back_title", "seasonselect": "to_modeselect",
                    "eventselect": "to_seasonselect",
                    "help": "back_title", "settings": "back_title"}.get(self.state)
            self._action(back)
            return
        self._nav_keys(key)

    def on_click(self, pos, button):
        if button != 1:
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    def update(self, dt):
        if self.state == "play" and self.ev:
            if self.paused:
                return
            keys = pygame.key.get_pressed()
            self.ev.update(dt, keys)
            if self.ev.done and self.t_state > 0.2:
                natt = getattr(self.ev, "attempts", 1)
                if natt > 1:
                    self._register_attempt()
                    self.attempt += 1
                    if self.attempt < natt:
                        if self.sfx:
                            self.sfx.play("good")
                        self.ev.reset()
                        self.ev.started = True   # geen aftellen tussen pogingen
                        self.ev.countdown = 0.0
                        self.t_state = 0.0
                        return
                    self.ev.value = self.best_value if self.best_value is not None else 0.0
                if self.sfx:
                    self.sfx.play("medal" if self.ev.medal() else "good")
                self.finish_event()
        elif self.state == "lan_wait" and self.lan:
            if self.lan.error and not self.lan.connected:
                self.lan_status = "%s: %s" % (t("lan_fout"), self.lan.error)
            elif self.lan.connected:
                self.lan.poll()  # fase 1: inbox legen; fase 2 verwerkt berichten
                self.lan_status = "%s  (%s)" % (t("lan_verbonden"), self.lan.peer_ip or "")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "modeselect":
            self._draw_modeselect(s)
        elif st == "seasonselect":
            self._draw_seasonselect(s)
        elif st == "lan_lobby":
            self._draw_lan_lobby(s)
        elif st == "lan_ip":
            self._draw_lan_ip(s)
        elif st == "lan_wait":
            self._draw_lan_wait(s)
        elif st == "eventselect":
            self._draw_eventselect(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st == "announce":
            self._draw_announce(s)
        elif st == "play":
            s.fill(BG)
            self.ev.draw(s)
            self._draw_hud(s)
            if self.paused:
                self._draw_pause(s)
        elif st == "result":
            self._draw_result(s)
        elif st == "tally":
            self._draw_tally(s)
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

    def _stack(self, items, top, w=420, h=64, gap=16, kinds=None):
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
        no_focus = self.state == "play" and not self.paused
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, hot=b.hit(self.mouse), focus=(i == self.focus and not no_focus))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=200, w=420, h=64, gap=18, kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "winter & zomer - %d onderdelen, medailles" % len(EVENT_CLASSES), self.font_s, MUTED, WIDTH // 2, HEIGHT - 44)
        self._text(s, "Contact: " + CONTACT, self.font_s, MUTED, WIDTH // 2, HEIGHT - 22)

    def _draw_modeselect(self, s):
        s.fill(BG)
        self._text(s, t("spelers"), self.font_l, ACCENT, WIDTH // 2, 90)
        self._stack([(t("1speler"), "p1"), (t("2spelers"), "p2"), (t("lan_2spelers"), "p_lan")],
                    top=170, w=440, h=66, gap=18, kinds=["primary", "normal", "normal"])
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 76, 220, 52), "back_title", kind="back")
        self._add_donate()

    def _draw_seasonselect(self, s):
        s.fill(BG)
        self._text(s, t("seizoen"), self.font_l, ACCENT, WIDTH // 2, 110)
        nw = len(self._season_indices("winter"))
        ns = len(self._season_indices("summer"))
        self._add_button("%s  (%d)" % (t("winterspelen"), nw), (WIDTH // 2 - 220, 210, 460, 72), "season_winter", kind="primary")
        self._add_button("%s  (%d)" % (t("zomerspelen"), ns), (WIDTH // 2 - 220, 300, 460, 72), "season_summer", kind="normal")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 52), "to_modeselect", kind="back")
        self._add_donate()

    def _draw_lan_lobby(self, s):
        s.fill(BG)
        self._text(s, t("lan_titel"), self.font_l, ACCENT, WIDTH // 2, 90)
        if netmod is None:
            self._text(s, t("lan_niet_beschikbaar"), self.font_s, WARN, WIDTH // 2, 170)
            self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 52), "lan_cancel", kind="back")
            self._add_donate()
            return
        self._stack([(t("lan_host"), "lan_host"), (t("lan_find"), "lan_find"),
                     (t("lan_manual"), "lan_manual")],
                    top=170, w=460, h=64, gap=18, kinds=["primary", "normal", "normal"])
        if self.lan_status:
            self._text(s, self.lan_status, self.font_s, MUTED, WIDTH // 2, 400)
        self._text(s, t("lan_tip"), self.font_s, MUTED, WIDTH // 2, 440)
        self._text(s, t("lan_tip2"), self.font_s, MUTED, WIDTH // 2, 464)
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 52), "lan_cancel", kind="back")
        self._add_donate()

    def _draw_lan_ip(self, s):
        s.fill(BG)
        self._text(s, t("lan_manual"), self.font_l, ACCENT, WIDTH // 2, 110)
        self._text(s, t("lan_typ_ip"), self.font_m, TEXT, WIDTH // 2, 200)
        box = pygame.Rect(WIDTH // 2 - 200, 240, 400, 56)
        pygame.draw.rect(s, PANEL2, box, border_radius=10)
        pygame.draw.rect(s, ACCENT, box, width=2, border_radius=10)
        shown = self.lan_ip_text + ("_" if (self.t_state % 1.0) < 0.5 else "")
        self._text(s, shown or " ", self.font_m, GOLD, WIDTH // 2, box.centery)
        self._text(s, t("lan_enter"), self.font_s, MUTED, WIDTH // 2, 320)
        self._add_button(t("lan_verbinden"), (WIDTH // 2 - 120, 360, 240, 54), "lan_connect", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 52), "lan_manual_back", kind="back")
        self._add_donate()

    def _draw_lan_wait(self, s):
        s.fill(BG)
        self._text(s, t("lan_titel"), self.font_l, ACCENT, WIDTH // 2, 110)
        if self.lan and self.lan.connected:
            head = t("lan_verbonden")
            col = GOED
        elif self.lan_role == 0:
            head = t("lan_wacht_speler")
            col = GOLD
        else:
            head = t("lan_verbinden")
            col = GOLD
        self._text(s, head, self.font_m, col, WIDTH // 2, 210)
        if self.lan_status:
            self._text(s, self.lan_status, self.font_m, TEXT, WIDTH // 2, 270)
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 90, 220, 52), "lan_cancel", kind="back")
        self._add_donate()

    def _draw_eventselect(self, s):
        s.fill(BG)
        title = t("winterspelen") if self.season == "winter" else t("zomerspelen")
        self._text(s, title, self.font_l, ACCENT, WIDTH // 2, 48)
        idxs = self._season_indices()
        n = len(idxs)
        x = WIDTH // 2 - 230
        y = 92
        rows = (n + 1) // 2
        for j, i in enumerate(idxs):
            col = (x if j % 2 == 0 else x + 240)
            row = j // 2
            self._add_button(t(EVENT_CLASSES[i].name_key), (col, y + row * 60, 220, 50), "ev_%d" % i)
        ty = y + rows * 60 + 6
        self._add_button(t("toernooi3"), (x, ty, 224, 48), "tournament3", kind="primary")
        self._add_button(t("toernooi1"), (x + 236, ty, 224, 48), "tournament", kind="normal")
        # records van dit seizoen
        yy = ty + 64
        for i in idxs:
            rec = self.cfg["records"].get(str(i))
            if rec is not None and yy < HEIGHT - 70:
                self._text(s, "%s: %.2f %s" % (t(EVENT_CLASSES[i].name_key), rec, EVENT_CLASSES[i].unit),
                           self.font_s, GOLD, WIDTH // 2, yy)
                yy += 22
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 52, 220, 42), "to_seasonselect", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 40)
        wkind = "primary" if self.help_season == "winter" else "normal"
        skind = "primary" if self.help_season == "summer" else "normal"
        self._add_button(t("winterspelen"), (WIDTH // 2 - 230, 76, 220, 44), "help_winter", kind=wkind)
        self._add_button(t("zomerspelen"), (WIDTH // 2 + 10, 76, 220, 44), "help_summer", kind=skind)
        idxs = self._season_indices(self.help_season)
        top = 140
        bottom = HEIGHT - 70
        step = max(48, min(86, (bottom - top) // max(1, len(idxs))))
        y = top
        for i in idxs:
            ec = EVENT_CLASSES[i]
            pref = ec.name_key.replace("ev_", "ctrl_")
            self._text(s, t(ec.name_key), self.font_m, GOLD, WIDTH // 2, y)
            self._text(s, t(pref + "_1"), self.font_s, TEXT, WIDTH // 2, y + 24)
            if step >= 70:
                self._text(s, t(pref + "_2"), self.font_s, MUTED, WIDTH // 2, y + 46)
            y += step
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 56, 220, 44), "back_title", kind="back")
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

    def _draw_announce(self, s):
        ec = EVENT_CLASSES[self.queue[self.qpos]]
        if ec.winter:
            _bg_sky(s, True)
        else:
            _bg_sky(s, False)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        s.blit(ov, (0, 0))
        self._text(s, t(ec.name_key), self.font_xl, GOLD, WIDTH // 2, 170)
        if self.players == 2:
            self._text(s, "%s %d" % (t("speler"), self.cur_player + 1), self.font_l, ACCENT, WIDTH // 2, 250)
        pref = ec.name_key.replace("ev_", "ctrl_")
        self._text(s, t(ec.instr_key), self.font_s, MUTED, WIDTH // 2, 286)
        self._text(s, t("besturing"), self.font_m, ACCENT, WIDTH // 2, 324)
        self._text(s, t(pref + "_1"), self.font_s, TEXT, WIDTH // 2, 360)
        self._text(s, t(pref + "_2"), self.font_s, TEXT, WIDTH // 2, 390)
        self._text(s, t("klaar_start"), self.font_m, GOED, WIDTH // 2, 432)
        self._add_button(t("verder"), (WIDTH // 2 - 120, 466, 240, 56), "start_play", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 54, 220, 46), "to_eventselect", kind="back")

    def _draw_hud(self, s):
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, HUD_H))
        pygame.draw.line(s, LINE, (0, HUD_H), (WIDTH, HUD_H), 2)
        ec = EVENT_CLASSES[self.queue[self.qpos]]
        self._text(s, t(ec.name_key), self.font_m, ACCENT, 20, HUD_H // 2, center=False)
        if self.q_roundlen and len(self.queue) // self.q_roundlen > 1:
            rnd = self.qpos // self.q_roundlen + 1
            tot = len(self.queue) // self.q_roundlen
            self._text(s, "%s %d/%d" % (t("ronde"), rnd, tot), self.font_s, ACCENT, WIDTH - 320, HUD_H // 2, center=False)
        natt = getattr(self.ev, "attempts", 1)
        if natt > 1:
            txt = "%s %d/%d" % (t("poging"), min(self.attempt + 1, natt), natt)
            if self.best_value:
                txt += "   %s: %.2f %s" % (t("beste"), self.best_value, self.ev.unit)
            self._text(s, txt, self.font_s, GOLD, WIDTH // 2, HUD_H // 2)
        else:
            self._text(s, t("pauze_hint"), self.font_s, MUTED, WIDTH // 2, HUD_H // 2)
        if self.players == 2:
            self._text(s, "%s %d" % (t("speler"), self.cur_player + 1), self.font_m, GOLD,
                       WIDTH - 150, HUD_H // 2, center=False)

    def _draw_pause(self, s):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        s.blit(ov, (0, 0))
        self._text(s, t("pauze"), self.font_xl, GOLD, WIDTH // 2, 200)
        self._add_button(t("verder"), (WIDTH // 2 - 140, 300, 280, 60), "resume", kind="primary")
        self._add_button(t("terug_menu"), (WIDTH // 2 - 140, 374, 280, 60), "quit_to_menu", kind="back")

    def _draw_result(self, s):
        ec = EVENT_CLASSES[self.queue[self.qpos]]
        if ec.winter:
            _bg_sky(s, True)
        else:
            _bg_sky(s, False)
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        s.blit(ov, (0, 0))
        self._text(s, t("resultaat"), self.font_l, ACCENT, WIDTH // 2, 90)
        if self.players == 2:
            self._text(s, "%s %d" % (t("speler"), self.cur_player + 1), self.font_m, TEXT, WIDTH // 2, 140)
        valid = (self.last_value and self.last_value > 0) or ec.unit == "s"
        self._text(s, self.ev.value_text() if valid else t("ongeldig"),
                   self.font_xl, GOLD, WIDTH // 2, 210)
        med = self.last_medal
        if med:
            draw_medal_icon(s, WIDTH // 2 - 90, 300, 28, med)
            self._text(s, t(med), self.font_l, {"goud": GOLD, "zilver": SILVER, "brons": BRONS}[med],
                       WIDTH // 2 + 30, 300)
        else:
            self._text(s, "%s: %s" % (t("medaille"), t("geen")), self.font_m, MUTED, WIDTH // 2, 300)
        if self.last_record:
            self._text(s, t("record"), self.font_m, GOED, WIDTH // 2, 350)
        self._add_button(t("verder"), (WIDTH // 2 - 120, 430, 240, 60), "result_next", kind="primary")

    def _draw_tally(self, s):
        s.fill(BG)
        self._text(s, t("medaillespiegel"), self.font_l, ACCENT, WIDTH // 2, 60)
        # tel medailles per speler
        counts = {0: {"goud": 0, "zilver": 0, "brons": 0}, 1: {"goud": 0, "zilver": 0, "brons": 0}}
        for (pl, qp), val in self.results.items():
            if qp >= len(self.queue):
                continue
            ec = EVENT_CLASSES[self.queue[qp]]
            m = compute_medal(val, ec.MED[0], ec.MED[1], ec.MED[2], ec.lower_better)
            if m:
                counts[pl][m] += 1
        y = 130
        for pl in range(self.players):
            self._text(s, "%s %d" % (t("speler"), pl + 1) if self.players == 2 else t("1speler"),
                       self.font_m, TEXT, WIDTH // 2, y, center=True)
            cx = WIDTH // 2 - 130
            for mi, mk in enumerate(("goud", "zilver", "brons")):
                draw_medal_icon(s, cx + mi * 110, y + 44, 18, mk)
                self._text(s, "x %d" % counts[pl][mk], self.font_m, TEXT, cx + mi * 110 + 30, y + 44, center=False)
            y += 110
        # winnaar bij 2 spelers (op goud, dan zilver, dan brons)
        if self.players == 2:
            def score(pl):
                return counts[pl]["goud"] * 100 + counts[pl]["zilver"] * 10 + counts[pl]["brons"]
            s0, s1 = score(0), score(1)
            if s0 == s1:
                msg = t("gelijk")
            else:
                msg = "%s: %s %d" % (t("winnaar"), t("speler"), 1 if s0 > s1 else 2)
            self._text(s, msg, self.font_l, GOLD, WIDTH // 2, y + 10)
        self._add_button(t("terug_menu"), (WIDTH // 2 - 120, HEIGHT - 80, 240, 56), "back_title", kind="primary")


# ----------------------------------------------------------------------------
def main():
    # Windows: eigen taakbalk-identiteit, anders toont de taakbalk het Python-icoon
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dravenlock.DraveGames")
        except Exception:
            pass
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
# v0.1.x - 5 onderdelen (incl. Verspringen, waggle-aanloop)

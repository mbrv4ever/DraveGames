# -*- coding: utf-8 -*-
"""race.py - DraveRace, een retro racer van Dravenlock Games.

Twee camera's (achter de auto in pseudo-3D, en bovenaanzicht) en twee
race-soorten (ronde-race en achtervolging/tijdrit). Keuze uit meerdere auto's,
obstakels en tegenstanders op de weg, en flink wat rondes die steeds zwaarder
worden. Procedurele muziek en geluiden (sfx.py). NL-basis met OS-taaldetectie
en Engels; donker Dravenlock-palet, grote en contrastrijke HUD.

Besturing: pijl links/rechts = sturen, pijl omhoog = gas, pijl omlaag = rem,
spatie = nitro, Esc/P = pauze.
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

APP_NAME = "DraveRace"
APP_VERSION = "0.2.7"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

# ----------------------------------------------------------------------------
# Scherm
# ----------------------------------------------------------------------------
WIDTH, HEIGHT = 960, 600
FPS = 60

# ----------------------------------------------------------------------------
# Donker Dravenlock-palet
# ----------------------------------------------------------------------------
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

# ----------------------------------------------------------------------------
# Wereld / pseudo-3D
# ----------------------------------------------------------------------------
SEG_LEN = 200            # wereldlengte per wegsegment
ROAD_W = 2000            # halve wegbreedte (wereld-eenheden)
CAM_HEIGHT = 1500        # camerahoogte
CAM_DEPTH = 0.84         # ~ field of view
DRAW_DIST = 260          # aantal zichtbare segmenten (pseudo-3D)

# ----------------------------------------------------------------------------
# Configuratie en taal
# ----------------------------------------------------------------------------
def config_dir() -> str:
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script),
    nooit in systeemmappen zoals %APPDATA%. Veel mensen hebben een kleine
    C-schijf en willen daar geen overbodige data."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveRace-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveRace-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")

DEFAULT_CONFIG = {
    "lang": "",
    "sound": True,
    "music": True,
    "volume": 0.8,
    "car": 0,
    "camera": "achter",     # "achter" of "boven"
    "mode": "ronde",        # "ronde" of "achtervolging"
    "best_ronde": 0,        # hoogste gehaalde ronde-stage
    "best_chase": 0,
    "highscore": 0,
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg: dict):
    try:
        tmp = CONFIG_PATH + ".part"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, CONFIG_PATH)
    except Exception:
        pass


_LANG = "nl"


def detect_os_lang() -> str:
    try:
        import locale
        loc = (locale.getdefaultlocale()[0] or "").lower()
        if loc.startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def set_lang(l):
    global _LANG
    _LANG = "nl" if l == "nl" else "en"


TR = {
    "titel": {"nl": "DraveRace", "en": "DraveRace"},
    "onder": {"nl": "Een retro racer van Dravenlock Games",
              "en": "A retro racer by Dravenlock Games"},
    "made_by": {"nl": "Gemaakt door Dravenlock Games",
                "en": "Made by Dravenlock Games"},
    "donatie": {"nl": "Donatie", "en": "Donate"},
    "start": {"nl": "Start", "en": "Start"},
    "speel": {"nl": "Spelen", "en": "Play"},
    "kies_auto": {"nl": "Kies auto", "en": "Choose car"},
    "kies_modus": {"nl": "Kies modus", "en": "Choose mode"},
    "camera": {"nl": "Camera", "en": "Camera"},
    "cam_achter": {"nl": "Achter de auto", "en": "Behind the car"},
    "cam_boven": {"nl": "Bovenaanzicht", "en": "Top-down"},
    "modus": {"nl": "Modus", "en": "Mode"},
    "ronde_race": {"nl": "Ronde-race", "en": "Lap race"},
    "achtervolging": {"nl": "Achtervolging", "en": "Chase"},
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
    "volgende": {"nl": "Volgende ronde", "en": "Next round"},
    "ronde": {"nl": "Ronde", "en": "Round"},
    "lap": {"nl": "Rondje", "en": "Lap"},
    "snelheid": {"nl": "km/u", "en": "km/h"},
    "tijd": {"nl": "Tijd", "en": "Time"},
    "plek": {"nl": "Plek", "en": "Pos"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "kloof": {"nl": "Kloof", "en": "Gap"},
    "klaar_ronde": {"nl": "Ronde gehaald!", "en": "Round cleared!"},
    "gewonnen": {"nl": "Gewonnen!", "en": "You win!"},
    "verloren": {"nl": "Verloren", "en": "Game over"},
    "tijd_op": {"nl": "Tijd op!", "en": "Time up!"},
    "ingehaald": {"nl": "Rivaal ingehaald!", "en": "Rival caught!"},
    "sturen": {"nl": "Pijl links/rechts: sturen", "en": "Left/Right: steer"},
    "gas": {"nl": "Pijl omhoog: gas", "en": "Up: accelerate"},
    "rem": {"nl": "Pijl omlaag: rem", "en": "Down: brake"},
    "nitro": {"nl": "Spatie: nitro", "en": "Space: nitro"},
    "pauze_t": {"nl": "Esc of P: pauze", "en": "Esc or P: pause"},
    "klik_start": {"nl": "Druk op Enter of klik om te starten",
                   "en": "Press Enter or click to start"},
    "doel_ronde": {"nl": "Rijd alle rondjes en eindig vooraan.",
                   "en": "Drive all laps and finish in front."},
    "doel_chase": {"nl": "Haal de rivaal in voor de tijd op is.",
                   "en": "Catch the rival before time runs out."},
    "rondjes": {"nl": "Rondjes", "en": "Laps"},
    "stat_top": {"nl": "Top", "en": "Top"},
    "stat_acc": {"nl": "Acc", "en": "Acc"},
    "stat_grip": {"nl": "Grip", "en": "Grip"},
}


def t(key):
    e = TR.get(key, {})
    return e.get(_LANG, e.get("nl", key))


# ----------------------------------------------------------------------------
# Auto's
# ----------------------------------------------------------------------------
class Car:
    def __init__(self, name_nl, name_en, color, top, acc, grip):
        self.name_nl = name_nl
        self.name_en = name_en
        self.color = color
        self.top = top      # 0..1 (relatieve topsnelheid)
        self.acc = acc      # 0..1 (versnelling)
        self.grip = grip    # 0..1 (houvast/sturen)

    def name(self):
        return self.name_nl if _LANG == "nl" else self.name_en


CARS = [
    Car("Bliksem", "Bolt", ACCENT, 0.95, 0.7, 0.7),
    Car("Vuur", "Blaze", WARN, 1.0, 0.6, 0.6),
    Car("Smaragd", "Emerald", GOED, 0.8, 0.85, 0.85),
    Car("Schaduw", "Shadow", PURPLE, 0.88, 0.75, 0.8),
]

# wereld-topsnelheid (eenheden/sec) bij top=1.0
MAX_WORLD_SPEED = 12000.0


# ----------------------------------------------------------------------------
# Hulp
# ----------------------------------------------------------------------------
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t_):
    return a + (b - a) * t_


def mix(c1, c2, t_):
    return (int(lerp(c1[0], c2[0], t_)),
            int(lerp(c1[1], c2[1], t_)),
            int(lerp(c1[2], c2[2], t_)))


def draw_heart(surf, cx, cy, r, color):
    """Teken een eenvoudig hartje gecentreerd op (cx, cy)."""
    rr = max(3, int(r))
    pygame.draw.circle(surf, color, (int(cx - rr * 0.5), int(cy - rr * 0.3)), int(rr * 0.6))
    pygame.draw.circle(surf, color, (int(cx + rr * 0.5), int(cy - rr * 0.3)), int(rr * 0.6))
    pts = [(int(cx - rr * 1.02), int(cy - rr * 0.1)),
           (int(cx + rr * 1.02), int(cy - rr * 0.1)),
           (int(cx), int(cy + rr * 1.05))]
    pygame.draw.polygon(surf, color, pts)


# ----------------------------------------------------------------------------
# Baan (segmenten met bocht); gesloten lus
# ----------------------------------------------------------------------------
class Segment:
    __slots__ = ("index", "curve", "color_i")

    def __init__(self, index, curve, color_i):
        self.index = index
        self.curve = curve
        self.color_i = color_i


def build_track(stage, rng):
    """Bouw een gesloten baan; hogere stage = meer/scherpere bochten en langer."""
    segs = []
    idx = [0]

    def add(n, curve):
        for _ in range(n):
            segs.append(Segment(idx[0], curve, (idx[0] // 4) % 2))
            idx[0] += 1

    def ease(n, target):
        # geleidelijk in- en uitlopen van een bocht
        for k in range(n):
            c = target * math.sin((k / max(1, n)) * math.pi)
            segs.append(Segment(idx[0], c, (idx[0] // 4) % 2))
            idx[0] += 1

    base_len = 120 + stage * 12
    sharp = 1.6 + stage * 0.5
    add(40, 0)
    blocks = 6 + stage
    for _ in range(blocks):
        add(rng.randint(15, 30), 0)
        d = rng.choice([-1, 1])
        ease(rng.randint(25, 45), d * rng.uniform(1.0, sharp))
    add(30, 0)
    # pad iets uitlijnen voor de lus (cosmetisch; lus telt op afstand)
    while len(segs) < base_len:
        add(10, 0)
    # herindex
    for i, s in enumerate(segs):
        s.index = i
        s.color_i = (i // 4) % 2
    return segs


# ----------------------------------------------------------------------------
# Sprites (procedureel)
# ----------------------------------------------------------------------------
def car_back_surface(color, w=200):
    """Achteraanzicht van een auto (voor pseudo-3D)."""
    h = int(w * 0.7)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(int(w * 0.12), int(h * 0.28), int(w * 0.76), int(h * 0.58))
    pygame.draw.rect(s, mix(color, (0, 0, 0), 0.15), body, border_radius=int(w * 0.06))
    # dak/ruit
    roof = pygame.Rect(int(w * 0.22), int(h * 0.1), int(w * 0.56), int(h * 0.3))
    pygame.draw.rect(s, mix(color, (0, 0, 0), 0.35), roof, border_radius=int(w * 0.05))
    win = pygame.Rect(int(w * 0.27), int(h * 0.15), int(w * 0.46), int(h * 0.18))
    pygame.draw.rect(s, (30, 34, 44), win, border_radius=int(w * 0.03))
    # wielen
    pygame.draw.rect(s, (20, 20, 24), (int(w * 0.06), int(h * 0.62), int(w * 0.16), int(h * 0.3)),
                     border_radius=4)
    pygame.draw.rect(s, (20, 20, 24), (int(w * 0.78), int(h * 0.62), int(w * 0.16), int(h * 0.3)),
                     border_radius=4)
    # achterlichten
    pygame.draw.rect(s, RED, (int(w * 0.15), int(h * 0.5), int(w * 0.14), int(h * 0.1)),
                     border_radius=3)
    pygame.draw.rect(s, RED, (int(w * 0.71), int(h * 0.5), int(w * 0.14), int(h * 0.1)),
                     border_radius=3)
    return s


def car_top_surface(color, w=46):
    """Bovenaanzicht van een auto (voor top-down camera). Wijst naar boven."""
    h = int(w * 1.9)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(int(w * 0.1), int(h * 0.06), int(w * 0.8), int(h * 0.88))
    pygame.draw.rect(s, color, body, border_radius=int(w * 0.28))
    # ruiten
    pygame.draw.rect(s, (28, 32, 42), (int(w * 0.2), int(h * 0.16), int(w * 0.6), int(h * 0.18)),
                     border_radius=int(w * 0.15))
    pygame.draw.rect(s, (28, 32, 42), (int(w * 0.2), int(h * 0.5), int(w * 0.6), int(h * 0.22)),
                     border_radius=int(w * 0.15))
    # wielen
    for wx in (int(-w * 0.02), int(w * 0.86)):
        pygame.draw.rect(s, (18, 18, 22), (wx, int(h * 0.2), int(w * 0.16), int(h * 0.18)),
                         border_radius=3)
        pygame.draw.rect(s, (18, 18, 22), (wx, int(h * 0.66), int(w * 0.16), int(h * 0.18)),
                         border_radius=3)
    return s


def obstacle_surface(kind, w=70):
    s = pygame.Surface((w, w), pygame.SRCALPHA)
    if kind == "cone":
        pygame.draw.polygon(s, (230, 130, 40),
                            [(w // 2, int(w * 0.1)), (int(w * 0.78), int(w * 0.9)),
                             (int(w * 0.22), int(w * 0.9))])
        pygame.draw.rect(s, (240, 240, 240),
                         (int(w * 0.32), int(w * 0.45), int(w * 0.36), int(w * 0.12)))
    elif kind == "oil":
        pygame.draw.ellipse(s, (24, 24, 30), (int(w * 0.05), int(w * 0.3), int(w * 0.9), int(w * 0.5)))
        pygame.draw.ellipse(s, (60, 60, 80), (int(w * 0.2), int(w * 0.4), int(w * 0.4), int(w * 0.2)))
    elif kind == "rock":
        pygame.draw.polygon(s, (120, 120, 128),
                            [(int(w * 0.2), int(w * 0.8)), (int(w * 0.1), int(w * 0.45)),
                             (int(w * 0.4), int(w * 0.18)), (int(w * 0.75), int(w * 0.25)),
                             (int(w * 0.9), int(w * 0.6)), (int(w * 0.7), int(w * 0.85))])
    else:  # barrier
        pygame.draw.rect(s, (210, 210, 215), (0, int(w * 0.4), w, int(w * 0.2)))
        for i in range(0, w, int(w * 0.25) or 1):
            pygame.draw.polygon(s, (200, 60, 60),
                                [(i, int(w * 0.4)), (i + int(w * 0.12), int(w * 0.4)),
                                 (i, int(w * 0.6))])
    return s


# ----------------------------------------------------------------------------
# Entiteiten
# ----------------------------------------------------------------------------
class Opponent:
    def __init__(self, distance, lateral, speed, color, rival=False):
        self.distance = distance
        self.lateral = lateral
        self.speed = speed
        self.color = color
        self.rival = rival
        self.hit_cd = 0.0


class Obstacle:
    def __init__(self, distance, lateral, kind):
        self.distance = distance
        self.lateral = lateral
        self.kind = kind
        self.hit = False


# ----------------------------------------------------------------------------
# Race-toestand
# ----------------------------------------------------------------------------
class Race:
    def __init__(self, app, car, mode, camera, stage):
        self.app = app
        self.car = car
        self.mode = mode          # "ronde" / "achtervolging"
        self.camera = camera      # "achter" / "boven"
        self.stage = stage
        self.rng = random.Random(1000 + stage * 7)

        self.segs = build_track(stage, self.rng)
        self.N = len(self.segs)
        self.track_len = self.N * SEG_LEN

        self.position = 0.0
        self.player_x = 0.0
        self.speed = 0.0
        self.max_speed = MAX_WORLD_SPEED * (0.75 + 0.25 * car.top) * (1.0 + 0.05 * stage)
        self.accel = MAX_WORLD_SPEED * (0.35 + 0.4 * car.acc)
        self.grip = 0.6 + 0.4 * car.grip

        self.nitro = 1.0
        self.nitro_active = False
        self.steer_wobble = 0.0    # door olie
        self.shake = 0.0
        self.view_angle = 0.0      # hoek waarmee de auto meedraait (bovenaanzicht)
        self.last_steer = 0.0

        self.lap = 1
        self.laps_target = 2 + stage         # rondjes nemen toe
        self.time_left = 0.0
        self.elapsed = 0.0
        self.score = 0
        self.finished = False
        self.result = None        # "win"/"lose"
        self.message = ""

        self.opponents = []
        self.obstacles = []
        self._spawn(stage)

        # camerabeelden / sprites
        self.spr_player_back = car_back_surface(car.color)
        self.spr_player_top = car_top_surface(car.color)
        self._opp_back = {}
        self._opp_top = {}
        self._obs_surf = {k: obstacle_surface(k) for k in ("cone", "oil", "rock", "barrier")}

        if self.mode == "achtervolging":
            self.time_left = max(18.0, 30.0 - stage * 1.5)

    # ---------- opbouw ----------
    def _opp_surfaces(self, color):
        key = tuple(color)
        if key not in self._opp_back:
            self._opp_back[key] = car_back_surface(color)
            self._opp_top[key] = car_top_surface(color)
        return self._opp_back[key], self._opp_top[key]

    def _spawn(self, stage):
        rng = self.rng
        n_obs = 8 + stage * 4
        kinds = ["cone", "cone", "oil", "rock", "barrier"]
        for _ in range(n_obs):
            d = rng.uniform(SEG_LEN * 12, self.track_len - SEG_LEN * 4)
            lat = rng.uniform(-0.7, 0.7)
            self.obstacles.append(Obstacle(d, lat, rng.choice(kinds)))

        if self.mode == "ronde":
            n_opp = 3 + min(5, stage)
            for i in range(n_opp):
                d = rng.uniform(SEG_LEN * 5, self.track_len * 0.9)
                lat = rng.uniform(-0.6, 0.6)
                spd = self.max_speed * rng.uniform(0.7, 0.86) * (1 + 0.03 * stage)
                col = rng.choice([ACCENT, WARN, GOED, PURPLE, GOLD])
                self.opponents.append(Opponent(d, lat, spd, col))
        else:
            # rivaal vooruit + wat verkeer
            gap = SEG_LEN * (16 + stage * 2)
            spd = self.max_speed * (0.82 + 0.02 * stage)
            self.rival = Opponent(gap, 0.0, spd, GOLD, rival=True)
            self.opponents.append(self.rival)
            for _ in range(2 + stage // 2):
                d = self.rng.uniform(SEG_LEN * 6, self.track_len * 0.8)
                lat = self.rng.uniform(-0.6, 0.6)
                self.opponents.append(
                    Opponent(d, lat, self.max_speed * 0.7, ACCENT))

    # ---------- baan-helpers ----------
    def seg_at(self, dist):
        i = int((dist % self.track_len) // SEG_LEN) % self.N
        return self.segs[i]

    # ---------- update ----------
    def update(self, dt, keys):
        if self.finished:
            return
        self.elapsed += dt

        steer_in = 0.0
        if keys["left"]:
            steer_in -= 1.0
        if keys["right"]:
            steer_in += 1.0

        # gas / rem
        if keys["up"]:
            self.speed += self.accel * dt
        elif keys["down"]:
            self.speed -= self.accel * 1.8 * dt
        else:
            self.speed -= self.accel * 0.35 * dt   # motorrem

        # nitro
        self.nitro_active = keys["space"] and self.nitro > 0.02
        top = self.max_speed
        if self.nitro_active:
            top *= 1.35
            self.nitro = clamp(self.nitro - dt * 0.5, 0, 1)
            if self.app.sfx and random.random() < 0.04:
                pass
        else:
            self.nitro = clamp(self.nitro + dt * 0.15, 0, 1)

        offroad = abs(self.player_x) > 1.0
        if offroad:
            top *= 0.45
            self.speed -= self.accel * 0.6 * dt
            self.shake = min(8, self.shake + 40 * dt)
            if random.random() < 0.05 and self.app.sfx:
                self.app.sfx.play("skid")
        else:
            self.shake = max(0, self.shake - 30 * dt)

        self.speed = clamp(self.speed, 0, top)

        # sturen (sneller = gevoeliger), beperkt door grip
        spd_pct = self.speed / self.max_speed if self.max_speed else 0
        dx = steer_in * dt * (1.4 + 1.2 * self.grip) * (0.4 + 0.6 * spd_pct)
        # olie-wobble
        if self.steer_wobble > 0:
            dx += math.sin(self.elapsed * 18) * 0.9 * dt
            self.steer_wobble = max(0, self.steer_wobble - dt)
        self.player_x += dx

        # middelpuntvliedende kracht in bochten
        cur = self.seg_at(self.position).curve
        self.player_x -= cur * spd_pct * spd_pct * dt * 0.9
        self.player_x = clamp(self.player_x, -2.0, 2.0)

        # hoek waarmee de auto meedraait (sturen + komende bocht)
        cur_ahead = self.seg_at(self.position + SEG_LEN * 4).curve
        self.last_steer = steer_in
        target_angle = clamp(steer_in * 20.0 + cur_ahead * 16.0 * (0.4 + spd_pct),
                             -34.0, 34.0)
        self.view_angle += (target_angle - self.view_angle) * min(1.0, dt * 7.0)

        # vooruit
        prev = self.position
        self.position += self.speed * dt
        # ronde tellen (gesloten lus)
        if self.position >= self.track_len:
            self.position -= self.track_len
            self._on_lap()

        # motorgeluid
        if self.app.sfx:
            self.app.sfx.set_engine(spd_pct * (1.2 if self.nitro_active else 1.0))

        # tegenstanders
        for o in self.opponents:
            o.distance = (o.distance + o.speed * dt) % self.track_len
            o.hit_cd = max(0, o.hit_cd - dt)
            # lichte koerscorrectie naar midden
            o.lateral *= (1 - 0.2 * dt)

        self._collisions(dt)

        # modus-logica
        if self.mode == "achtervolging":
            self.time_left -= dt
            gap = (self.rival.distance - self.position) % self.track_len
            if gap < SEG_LEN * 2.5 or gap > self.track_len - SEG_LEN:
                self._win(t("ingehaald"))
            elif self.time_left <= 0:
                self.time_left = 0
                self._lose(t("tijd_op"))

        # score
        self.score = int(self.elapsed * 10 + self.lap * 200 + spd_pct * 5)

    def _on_lap(self):
        if self.mode == "ronde":
            self.lap += 1
            if self.app.sfx:
                self.app.sfx.play("lap")
            if self.lap > self.laps_target:
                self._win(t("klaar_ronde"))

    def _collisions(self, dt):
        # obstakels
        for ob in self.obstacles:
            if ob.hit:
                continue
            dz = (ob.distance - self.position) % self.track_len
            if dz < 320 or dz > self.track_len - 120:
                if abs(self.player_x - ob.lateral) < 0.34:
                    ob.hit = True
                    self._hit_obstacle(ob.kind)
        # tegenstanders
        for o in self.opponents:
            if o.hit_cd > 0:
                continue
            dz = (o.distance - self.position) % self.track_len
            near = dz < 280 or dz > self.track_len - 160
            if near and abs(self.player_x - o.lateral) < 0.32:
                o.hit_cd = 1.2
                self.speed *= 0.6
                push = 0.4 if self.player_x < o.lateral else -0.4
                self.player_x += push
                o.lateral -= push * 0.5
                self.shake = 8
                if self.app.sfx:
                    self.app.sfx.play("crash")

    def _hit_obstacle(self, kind):
        if self.app.sfx:
            self.app.sfx.play("crash" if kind in ("rock", "barrier") else "skid")
        if kind == "cone":
            self.speed *= 0.85
        elif kind == "oil":
            self.steer_wobble = 1.2
            self.speed *= 0.95
        elif kind == "rock":
            self.speed *= 0.45
            self.shake = 8
        else:  # barrier
            self.speed *= 0.35
            self.shake = 10

    def _win(self, msg):
        if self.finished:
            return
        self.finished = True
        self.result = "win"
        self.message = msg
        if self.app.sfx:
            self.app.sfx.play("victory")

    def _lose(self, msg):
        if self.finished:
            return
        self.finished = True
        self.result = "lose"
        self.message = msg
        if self.app.sfx:
            self.app.sfx.play("defeat")

    # ---------- projectie (pseudo-3D) ----------
    def _project(self, wx, wz, cam_x):
        scale = CAM_DEPTH / max(1.0, wz)
        sx = int(WIDTH / 2 + scale * (wx - cam_x) * WIDTH / 2)
        sy = int(HEIGHT / 2 - scale * (0 - CAM_HEIGHT) * HEIGHT / 2)
        sw = int(scale * ROAD_W * WIDTH / 2)
        return sx, sy, sw, scale

    def draw(self, surf):
        if self.camera == "boven":
            self._draw_topdown(surf)
        else:
            self._draw_pseudo3d(surf)

    # ---------- pseudo-3D ----------
    def _draw_pseudo3d(self, surf):
        # lucht
        surf.fill((18, 20, 28))
        pygame.draw.rect(surf, (24, 28, 40), (0, 0, WIDTH, HEIGHT // 2))
        # verre heuvels
        pygame.draw.ellipse(surf, (30, 36, 50), (-100, HEIGHT // 2 - 80, 500, 160))
        pygame.draw.ellipse(surf, (28, 34, 46), (WIDTH - 400, HEIGHT // 2 - 60, 500, 140))

        base = int(self.position // SEG_LEN) % self.N
        offset = self.position - (self.position // SEG_LEN) * SEG_LEN
        cam_x = self.player_x * ROAD_W

        x = 0.0
        dx = 0.0
        quads = []
        clip = HEIGHT
        for n in range(DRAW_DIST):
            i = (base + n) % self.N
            seg = self.segs[i]
            z_near = (n * SEG_LEN) - offset
            z_far = z_near + SEG_LEN
            if z_far < 1:
                dx += seg.curve
                x += dx
                continue
            x_near = x
            dx += seg.curve
            x += dx
            x_far = x
            znear = max(1.0, z_near)
            zfar = max(1.0, z_far)
            sxn, syn, swn, scn = self._project(x_near * ROAD_W * 0.0009, znear, cam_x)
            sxf, syf, swf, scf = self._project(x_far * ROAD_W * 0.0009, zfar, cam_x)
            quads.append((n, seg, sxn, syn, swn, sxf, syf, swf))

        # van ver naar dichtbij tekenen (schilder-algoritme)
        for (n, seg, sxn, syn, swn, sxf, syf, swf) in reversed(quads):
            if syn <= syf:
                continue
            dark = seg.color_i == 0
            grass = (34, 44, 30) if dark else (40, 52, 36)
            road = (52, 52, 58) if dark else (60, 60, 66)
            rumble = (210, 210, 215) if dark else (200, 70, 70)
            # gras (volle breedte)
            pygame.draw.polygon(surf, grass,
                                [(0, syf), (WIDTH, syf), (WIDTH, syn), (0, syn)])
            # rumble (iets breder dan weg)
            rw_n = int(swn * 1.12)
            rw_f = int(swf * 1.12)
            pygame.draw.polygon(surf, rumble,
                                [(sxf - rw_f, syf), (sxf + rw_f, syf),
                                 (sxn + rw_n, syn), (sxn - rw_n, syn)])
            # weg
            pygame.draw.polygon(surf, road,
                                [(sxf - swf, syf), (sxf + swf, syf),
                                 (sxn + swn, syn), (sxn - swn, syn)])
            # middenstreep (stippel)
            if (seg.index // 3) % 2 == 0 and swf > 2:
                lw_n = max(1, swn // 22)
                lw_f = max(1, swf // 22)
                pygame.draw.polygon(surf, (220, 200, 120),
                                    [(sxf - lw_f, syf), (sxf + lw_f, syf),
                                     (sxn + lw_n, syn), (sxn - lw_n, syn)])

        # sprites (obstakels + tegenstanders), ver -> dichtbij
        sprites = []
        for ob in self.obstacles:
            dz = (ob.distance - self.position) % self.track_len
            if dz < DRAW_DIST * SEG_LEN:
                sprites.append((dz, "obs", ob))
        for o in self.opponents:
            dz = (o.distance - self.position) % self.track_len
            if dz < DRAW_DIST * SEG_LEN:
                sprites.append((dz, "opp", o))
        sprites.sort(key=lambda e: -e[0])
        for dz, kind, ent in sprites:
            self._draw_sprite_3d(surf, dz, kind, ent, cam_x)

        # speler-auto onderaan
        sw = 220
        simg = pygame.transform.smoothscale(self.spr_player_back, (sw, int(sw * 0.7)))
        steer_shift = int(clamp(self.player_x, -1.2, 1.2) * 30)
        sh = int(self.shake * math.sin(self.elapsed * 40))
        surf.blit(simg, (WIDTH // 2 - sw // 2 + steer_shift, HEIGHT - simg.get_height() - 10 + sh))

    def _draw_sprite_3d(self, surf, dz, kind, ent, cam_x):
        z = max(1.0, dz)
        scale = CAM_DEPTH / z
        # centrale x van de weg op die afstand benaderen via curve-integratie is duur;
        # we plaatsen sprites relatief t.o.v. wegmidden met hun laterale offset
        base = int(self.position // SEG_LEN)
        # benader curve-offset cumulatief
        sx = int(WIDTH / 2 + scale * (ent.lateral * ROAD_W - cam_x) * WIDTH / 2)
        sy = int(HEIGHT / 2 - scale * (0 - CAM_HEIGHT) * HEIGHT / 2)
        if kind == "obs":
            img = self._obs_surf[ent.kind]
            size = clamp(int(scale * 90000), 6, 240)
            im = pygame.transform.smoothscale(img, (size, size))
            surf.blit(im, (sx - size // 2, sy - size))
        else:
            back, _top = self._opp_surfaces(ent.color)
            size = clamp(int(scale * 200000), 8, 280)
            im = pygame.transform.smoothscale(back, (size, int(size * 0.7)))
            surf.blit(im, (sx - size // 2, sy - im.get_height()))

    # ---------- top-down ----------
    def _draw_topdown(self, surf):
        surf.fill((30, 40, 30))
        view = 46
        seg_px = HEIGHT / float(view - 8)
        half = 130
        cx = WIDTH / 2.0
        base = int(self.position // SEG_LEN) % self.N
        offset = self.position - (self.position // SEG_LEN) * SEG_LEN
        off_pct = offset / SEG_LEN
        # ruwe centerlijn (centers[0] = 0); enkele integratie = rustig slingeren
        raw = []
        x = 0.0
        for n in range(view):
            raw.append(x)
            seg = self.segs[(base + n) % self.N]
            x += seg.curve * 5.0
        # anker: speler altijd in beeldmidden, de weg schuift eronder door
        shift = cx - self.player_x * half
        centers = []
        for n in range(view):
            seg = self.segs[(base + n) % self.N]
            xc = shift + clamp(raw[n], -WIDTH, WIDTH)
            y = HEIGHT - 80 - (n - off_pct) * seg_px
            centers.append((xc, y, seg))
        # weg als band
        left = [(c[0] - half, c[1]) for c in centers]
        right = [(c[0] + half, c[1]) for c in centers]
        poly = left + right[::-1]
        if len(poly) >= 3:
            pygame.draw.polygon(surf, (54, 54, 60), poly)
        # randen + middenstreep
        for (cxk, yk, seg) in centers:
            col = (200, 70, 70) if (seg.color_i == 0) else (210, 210, 215)
            pygame.draw.circle(surf, col, (int(cxk - half), int(yk)), 3)
            pygame.draw.circle(surf, col, (int(cxk + half), int(yk)), 3)
            if (seg.index // 3) % 2 == 0:
                pygame.draw.circle(surf, (220, 200, 120), (int(cxk), int(yk)), 3)

        def center_at(rel_seg):
            idx = int(clamp(rel_seg, 0, view - 1))
            return centers[idx]

        # obstakels + tegenstanders
        for ob in self.obstacles:
            dz = (ob.distance - self.position) % self.track_len
            rel = dz / SEG_LEN + off_pct
            if 0 <= rel < view - 1:
                cxk, yk, _s = center_at(rel)
                im = pygame.transform.smoothscale(self._obs_surf[ob.kind], (38, 38))
                surf.blit(im, (int(cxk + ob.lateral * half) - 19, int(yk) - 19))
        for o in self.opponents:
            dz = (o.distance - self.position) % self.track_len
            rel = dz / SEG_LEN + off_pct
            if 0 <= rel < view - 1:
                cxk, yk, seg = center_at(rel)
                _b, top = self._opp_surfaces(o.color)
                # tegenstander draait mee met de bocht ter plaatse
                ang = clamp(seg.curve * 16.0, -34, 34)
                rot = pygame.transform.rotate(top, -ang)
                surf.blit(rot, rot.get_rect(center=(int(cxk + o.lateral * half), int(yk))))
        # speler: altijd in beeldmidden, draait mee met sturen/bocht
        py = HEIGHT - 80
        px = cx
        sh = int(self.shake * math.sin(self.elapsed * 40))
        rot = pygame.transform.rotate(self.spr_player_top, -self.view_angle)
        surf.blit(rot, rot.get_rect(center=(int(px) + sh, int(py))))


# ----------------------------------------------------------------------------
# App / states
# ----------------------------------------------------------------------------
class Button:
    """Klikbare, toetsenbord-navigeerbare knop (groot en contrastrijk)."""
    def __init__(self, label, rect, action, big=False, kind="normal"):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.action = action
        self.big = big
        self.kind = kind          # "normal", "back", "primary"

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
        border = ACCENT if (hot or focus) else LINE
        pygame.draw.rect(surf, border, r, width=3 if (hot or focus) else 2,
                         border_radius=12)
        col = TEXT if not (hot or focus) else (245, 245, 248)
        if self.kind == "donate":
            heart_col = WARN if not (hot or focus) else (235, 120, 110)
            draw_heart(surf, r.left + 26, r.centery, 11, heart_col)
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(midleft=(r.left + 46, r.centery)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


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

        self.car_i = int(self.cfg.get("car", 0)) % len(CARS)
        self.camera = self.cfg.get("camera", "achter")
        self.mode = self.cfg.get("mode", "ronde")
        self.stage = 1
        self.race = None
        self.keys = {"left": False, "right": False, "up": False, "down": False, "space": False}

        # knoppen / navigatie
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)

        # gesproken stem (mofasa) via neuvoice - hergebruik die van de splash
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
            try:
                self.logo = pygame.image.load(resource_path("assets/logo.png")).convert_alpha()
            except Exception:
                self.logo = None

    # ---------- muziek per state ----------
    def music_for_state(self):
        if not self.sfx:
            return
        if self.state in ("title", "carselect", "modeselect", "settings", "help"):
            self.sfx.start_music("menu")
        elif self.state == "race":
            if self.race and self.race.mode == "achtervolging":
                self.sfx.start_music("chase")
            else:
                tr = ["race1", "race2", "race3"][(self.stage - 1) % 3]
                self.sfx.start_music(tr)
        elif self.state in ("stageclear", "victory"):
            self.sfx.start_music("victory")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        self.music_for_state()

    # ---------- hoofdloop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 30.0)
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
            elif e.type == pygame.KEYUP:
                self._set_key(e.key, False)
            elif e.type == pygame.MOUSEMOTION:
                self.mouse = e.pos
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.on_click(e.pos)

    def _set_key(self, key, val):
        if key in (pygame.K_LEFT, pygame.K_a):
            self.keys["left"] = val
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.keys["right"] = val
        elif key in (pygame.K_UP, pygame.K_w):
            self.keys["up"] = val
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.keys["down"] = val
        elif key == pygame.K_SPACE:
            self.keys["space"] = val

    # ---------- centrale actie-afhandeling ----------
    def _action(self, a):
        if a is None:
            return
        self._click_sound()
        if a == "play":
            self.set_state("carselect")
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "car_prev":
            self.car_i = (self.car_i - 1) % len(CARS)
        elif a == "car_next":
            self.car_i = (self.car_i + 1) % len(CARS)
        elif a == "to_mode":
            self._sel_sound(); self.set_state("modeselect")
        elif a == "mode_toggle":
            self.mode = "achtervolging" if self.mode == "ronde" else "ronde"
        elif a == "cam_toggle":
            self.camera = "boven" if self.camera == "achter" else "achter"
        elif a == "start":
            self._sel_sound(); self.start_race(1)
        elif a == "back_title":
            self.set_state("title")
        elif a == "back_car":
            self.set_state("carselect")
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
                if self.voice_on:
                    self.tts.warmup()
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
            self.set_state("race")
        elif a == "to_title":
            if self.sfx:
                self.sfx.set_engine(0)
            self.set_state("title")
        elif a == "next_round":
            self.start_race(self.stage + 1)
        elif a == "retry":
            self.start_race(1)
        elif a == "donate":
            try:
                webbrowser.open(DONATIE)
            except Exception:
                pass

    def _back_action_for_state(self):
        return {
            "carselect": "back_title",
            "modeselect": "back_car",
            "help": "back_title",
            "settings": "back_title",
            "pause": "resume",
            "stageclear": "to_title",
            "gameover": "to_title",
            "victory": "to_title",
        }.get(self.state)

    def on_key(self, key):
        self._set_key(key, True)
        # in de race: pauzeren
        if self.state == "race":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            return
        # extra gemaksnavigatie in auto-keuze
        if self.state == "carselect":
            if key in (pygame.K_LEFT, pygame.K_a):
                self._action("car_prev"); return
            if key in (pygame.K_RIGHT, pygame.K_d):
                self._action("car_next"); return
        # menu-/overlay-navigatie via focus
        if key == pygame.K_ESCAPE:
            self._action(self._back_action_for_state())
            return
        focusables = [b for b in self.buttons]
        if not focusables:
            return
        if key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            self.focus = (self.focus - 1) % len(focusables)
            self._click_sound()
        elif key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            self.focus = (self.focus + 1) % len(focusables)
            self._click_sound()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.focus = clamp(self.focus, 0, len(focusables) - 1)
            self._action(focusables[self.focus].action)

    def on_click(self, pos):
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    def _click_sound(self):
        if self.sfx:
            self.sfx.play("click")

    def _sel_sound(self):
        if self.sfx:
            self.sfx.play("select")

    # ---------- race besturing ----------
    def start_race(self, stage):
        self.stage = stage
        self.cfg["car"] = self.car_i
        self.cfg["camera"] = self.camera
        self.cfg["mode"] = self.mode
        save_config(self.cfg)
        self.race = Race(self, CARS[self.car_i], self.mode, self.camera, stage)
        self.countdown = 3.2
        self.set_state("race")

    def update(self, dt):
        if self.state == "race" and self.race:
            if getattr(self, "countdown", 0) > 0:
                old = self.countdown
                self.countdown -= dt
                if int(old) != int(self.countdown) and self.countdown > 0:
                    if self.sfx:
                        self.sfx.play("beep")
                if self.countdown <= 0 and self.sfx:
                    self.sfx.play("go")
                return
            self.race.update(dt, self.keys)
            if self.race.finished:
                self._finish_race()

    def _finish_race(self):
        r = self.race
        if r.result == "win":
            # score/best bijwerken
            if r.score > self.cfg.get("highscore", 0):
                self.cfg["highscore"] = r.score
            key = "best_ronde" if r.mode == "ronde" else "best_chase"
            if self.stage > self.cfg.get(key, 0):
                self.cfg[key] = self.stage
            save_config(self.cfg)
            if self.stage >= 12:
                self.set_state("victory")
            else:
                self.set_state("stageclear")
        else:
            if self.sfx:
                self.sfx.set_engine(0)
            self.set_state("gameover")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "carselect":
            self._draw_carselect(s)
        elif st == "modeselect":
            self._draw_modeselect(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st == "race":
            self.race.draw(s)
            self._draw_hud(s, with_pause=getattr(self, "countdown", 0) <= 0)
            if getattr(self, "countdown", 0) > 0:
                self._draw_countdown(s)
        elif st == "pause":
            self.race.draw(s)
            self._draw_hud(s, with_pause=False)
            self._overlay(s, t("pauze"), [],
                          [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "stageclear":
            self.race.draw(s)
            self._overlay(s, t("klaar_ronde"),
                          ["%s %d   %s %d" % (t("score"), self.race.score,
                                              t("ronde"), self.stage)],
                          [(t("volgende"), "next_round"), (t("hoofdmenu"), "to_title")],
                          color=GOED)
        elif st == "gameover":
            self.race.draw(s)
            self._overlay(s, self.race.message or t("verloren"),
                          ["%s %d" % (t("score"), self.race.score)],
                          [(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                          color=WARN)
        elif st == "victory":
            self._draw_victory(s)
        # knoppen tekenen (met hover/focus)
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

    # ---------- knop-infrastructuur ----------
    def _add_button(self, label, rect, action, kind="normal"):
        b = Button(label, rect, action, kind=kind)
        self.buttons.append(b)
        return b

    def _add_donate(self):
        """Donatieknop (hartje) rechtsboven, zoals in de andere Drave-apps."""
        self._add_button(t("donatie"), (WIDTH - 190, 14, 172, 46), "donate", kind="donate")

    def _stack(self, items, top, w=360, h=64, gap=18, kinds=None):
        """Verticale, gecentreerde stapel knoppen. items = [(label, action)]."""
        x = WIDTH // 2 - w // 2
        y = top
        for i, (label, action) in enumerate(items):
            kind = "normal"
            if kinds and i < len(kinds):
                kind = kinds[i]
            self._add_button(label, (x, y, w, h), action, kind=kind)
            y += h + gap

    def _draw_buttons(self, s):
        if not self.buttons:
            return
        if self.focus >= len(self.buttons):
            self.focus = 0
        for i, b in enumerate(self.buttons):
            hot = b.hit(self.mouse)
            focus = (i == self.focus)
            font = self.font_m
            b.draw(s, font, hot=hot, focus=focus)

    # ---------- schermen ----------
    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"),
                     (t("gids"), "help"),
                     (t("instellingen"), "settings")],
                    top=200, w=380, h=66, gap=20,
                    kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "%s %s: %d    %s: %d" % (t("best"), t("ronde_race"),
                                               self.cfg.get("best_ronde", 0),
                                               t("achtervolging"),
                                               self.cfg.get("best_chase", 0)),
                   self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_carselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_auto"), self.font_l, ACCENT, WIDTH // 2, 56)
        car = CARS[self.car_i]
        prev = pygame.transform.smoothscale(car_back_surface(car.color), (300, 210))
        s.blit(prev, (WIDTH // 2 - 150, 110))
        self._text(s, car.name(), self.font_l, TEXT, WIDTH // 2, 350)
        # stat-balken
        bars = [(t("stat_top"), car.top), (t("stat_acc"), car.acc), (t("stat_grip"), car.grip)]
        bx = WIDTH // 2 - 150
        by = 390
        for name, val in bars:
            self._text(s, name, self.font_s, MUTED, bx, by + 8, center=False)
            pygame.draw.rect(s, PANEL2, (bx + 80, by, 220, 20), border_radius=6)
            pygame.draw.rect(s, car.color, (bx + 80, by, int(220 * val), 20), border_radius=6)
            by += 30
        # pijl-knoppen
        self._add_button("<", (WIDTH // 2 - 250, 170, 80, 90), "car_prev")
        self._add_button(">", (WIDTH // 2 + 170, 170, 80, 90), "car_next")
        # kiezen / terug
        self._add_button(t("speel"), (WIDTH // 2 - 200, HEIGHT - 86, 200, 60),
                         "to_mode", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 + 10, HEIGHT - 86, 190, 60),
                         "back_title", kind="back")
        self._add_donate()

    def _draw_modeselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_modus"), self.font_l, ACCENT, WIDTH // 2, 56)
        mname = t("ronde_race") if self.mode == "ronde" else t("achtervolging")
        cname = t("cam_achter") if self.camera == "achter" else t("cam_boven")
        doel = t("doel_ronde") if self.mode == "ronde" else t("doel_chase")
        self._add_button("%s: %s" % (t("modus"), mname),
                         (WIDTH // 2 - 230, 140, 460, 64), "mode_toggle")
        self._text(s, doel, self.font_s, MUTED, WIDTH // 2, 224)
        self._add_button("%s: %s" % (t("camera"), cname),
                         (WIDTH // 2 - 230, 268, 460, 64), "cam_toggle")
        self._add_button(t("start"), (WIDTH // 2 - 200, HEIGHT - 110, 200, 64),
                         "start", kind="primary")
        self._add_button(t("terug"), (WIDTH // 2 + 10, HEIGHT - 110, 190, 64),
                         "back_car", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 48)
        lines = [t("sturen"), t("gas"), t("rem"), t("nitro"), t("pauze_t"), "",
                 t("doel_ronde"), t("doel_chase")]
        y = 120
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 46
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 84, 220, 60),
                         "back_title", kind="back")
        self._add_donate()

    def _draw_settings(self, s):
        s.fill(BG)
        self._text(s, t("instellingen"), self.font_l, ACCENT, WIDTH // 2, 48)
        snd = t("aan") if self.cfg.get("sound", True) else t("uit")
        mus = t("aan") if self.cfg.get("music", True) else t("uit")
        voice = t("aan") if self.voice_on else t("uit")
        lang = {"": t("auto"), "nl": "Nederlands", "en": "English"}[self.cfg.get("lang", "")]
        vol = int(self.cfg.get("volume", 0.8) * 100)
        w = 460
        x = WIDTH // 2 - w // 2
        y = 120
        self._add_button("%s: %s" % (t("geluid"), snd), (x, y, w, 56), "toggle_sound")
        y += 70
        self._add_button("%s: %s" % (t("muziek"), mus), (x, y, w, 56), "toggle_music")
        y += 70
        self._add_button("%s: %s" % (t("stem"), voice), (x, y, w, 56), "toggle_voice")
        y += 70
        # volume met - en +
        self._text(s, "%s: %d%%" % (t("volume"), vol), self.font_m, TEXT, WIDTH // 2, y + 28)
        self._add_button("-", (x, y, 70, 56), "vol_down")
        self._add_button("+", (x + w - 70, y, 70, 56), "vol_up")
        y += 70
        self._add_button("%s: %s" % (t("taal"), lang), (x, y, w, 56), "cycle_lang")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 76, 220, 56),
                         "back_title", kind="back")
        self._add_donate()

    def _draw_countdown(self, s):
        c = self.countdown
        n = int(math.ceil(c))
        txt = str(n) if c > 0.25 else "GO"
        if n <= 0:
            txt = "GO"
        col = GOED if txt == "GO" else GOLD
        self._text(s, txt, self.font_xl, col, WIDTH // 2, HEIGHT // 2)

    def _draw_hud(self, s, with_pause=True):
        r = self.race
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, 52))
        kmh = int(r.speed / MAX_WORLD_SPEED * 320)
        self._text(s, "%d %s" % (kmh, t("snelheid")), self.font_m, TEXT, 90, 26)
        self._text(s, "%s %d" % (t("ronde"), self.stage), self.font_m, ACCENT, WIDTH // 2 - 60, 26)
        if r.mode == "ronde":
            self._text(s, "%s %d/%d" % (t("lap"), min(r.lap, r.laps_target), r.laps_target),
                       self.font_m, GOLD, WIDTH - 200, 26)
        else:
            self._text(s, "%s %d" % (t("tijd"), int(r.time_left)),
                       self.font_m, WARN if r.time_left < 6 else GOLD, WIDTH - 200, 26)
        # nitrobalk
        pygame.draw.rect(s, PANEL2, (20, HEIGHT - 26, 200, 14), border_radius=6)
        pygame.draw.rect(s, GOED, (20, HEIGHT - 26, int(200 * r.nitro), 14), border_radius=6)
        self._text(s, "NITRO", self.font_s, MUTED, 110, HEIGHT - 40)
        if r.mode == "achtervolging":
            gap = (r.rival.distance - r.position) % r.track_len
            self._text(s, "%s %dm" % (t("kloof"), int(gap / 30)),
                       self.font_m, GOLD, WIDTH // 2 + 120, HEIGHT - 28)
        # zichtbare pauzeknop
        if with_pause:
            self._add_button(t("pauze"), (WIDTH - 130, 60, 110, 44), "pause", kind="back")

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
        self._text(s, "%s %d" % (t("score"), self.cfg.get("highscore", 0)),
                   self.font_l, TEXT, WIDTH // 2, 310)
        self._stack([(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                    top=380, w=360, h=64, gap=18, kinds=["primary", "normal"])


# ----------------------------------------------------------------------------
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def load_window_icon():
    """Laad een net venster-icoon (32x32) zonder convert (mag voor set_mode)."""
    for name in ("assets/app_icon.png", "assets/logo_t.png", "assets/logo.png"):
        try:
            img = pygame.image.load(resource_path(name))
            return pygame.transform.smoothscale(img, (32, 32))
        except Exception:
            continue
    return None


def run_splash(tts):
    """Toon een apart, randloos splashvenster met logo + titel + 'Gemaakt door
    Dravenlock Games' en de gesproken intro (mofasa). Sluit daarna en geeft
    True terug als het spel mag starten (False bij sluiten)."""
    SW, SH = 580, 420
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    # icoon ZETTEN VOOR set_mode (anders pakt Windows het standaard-logo)
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

    # logo en teksten EENMALIG voorbereiden (vloeiende fade, geen herschaling)
    logo_img = None
    if logo:
        lw = 230
        logo_img = pygame.transform.smoothscale(logo, (lw, lw))
    title_img = f_title.render(APP_NAME, True, ACCENT)
    sub_img = f_sub.render(t_made_by(), True, MUTED)

    t = 0.0
    spoke = False
    proceed = True
    skipped = False
    speak_time = None
    FADE_END = 1.5
    MIN_TIME = 3.0          # minimale splashduur als er geen stem is
    MAX_AFTER = 16.0        # bovengrens nadat de stem is gestart
    use_voice = bool(tts and voice_on)
    while True:
        dt = min(clock.tick(60) / 1000.0, 1 / 30.0)
        t += dt
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                proceed = False
                skipped = True
            elif e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                skipped = True
        # stem pas NA de fade laden en spreken (titel + gemaakt door)
        if t >= FADE_END and not spoke:
            spoke = True
            if use_voice:
                tts.speak("%s. %s" % (APP_NAME, t_made_by()))
                speak_time = t

        win.fill(BG)
        pygame.draw.rect(win, PANEL, (0, 0, SW, SH))
        pygame.draw.rect(win, ACCENT, (0, 0, SW, SH), width=2)

        def fade(start, dur):
            return int(clamp((t - start) / dur, 0.0, 1.0) * 255)

        if logo_img is not None:
            logo_img.set_alpha(fade(0.0, 0.7))
            win.blit(logo_img, logo_img.get_rect(center=(SW // 2, 150)))
        title_img.set_alpha(fade(0.55, 0.5))
        win.blit(title_img, title_img.get_rect(center=(SW // 2, 310)))
        sub_img.set_alpha(fade(1.0, 0.5))
        win.blit(sub_img, sub_img.get_rect(center=(SW // 2, 362)))
        pygame.display.flip()

        # stopcondities
        if skipped:
            break
        if use_voice:
            # wachten tot de stem klaar is met laden/spreken (met bovengrens)
            if spoke and not tts.busy() and t > (speak_time or 0) + 0.3:
                break
            if spoke and t > (speak_time or 0) + MAX_AFTER:
                break
        else:
            if t >= MIN_TIME:
                break
    return proceed


def t_made_by():
    return t("made_by")


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    # venster-icoon alvast klaarzetten (voor het eerste set_mode)
    icon = load_window_icon()
    if icon is not None:
        pygame.display.set_icon(icon)

    # gedeelde stem: pas NA de fade laden (anders hapert de fade)
    tts = None
    if ttsmod is not None:
        cfg0 = load_config()
        tts = ttsmod.Tts(voice=cfg0.get("voice_name", "M1"), data_dir=config_dir())
        tts.enabled = cfg0.get("voice", True)

    # 1) splash als apart venster (laadt en spreekt de stem na de fade)
    proceed = run_splash(tts)
    if not proceed:
        pygame.quit()
        return

    # 2) hoofdvenster - icoon ZETTEN VOOR set_mode, en nogmaals erna
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

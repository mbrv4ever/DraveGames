# -*- coding: utf-8 -*-
"""DraveMission - infiltrate the complex, find the codes, escape (pygame).

Inspired by the 1984 classic Impossible Mission, but with original graphics and
naming. The language follows the PC (Dutch or English) automatically.
Donationware.

Speel/Play:
  - Arrow keys = walk left/right
  - Space = jump (somersault over robots)
  - Up/Down = ride a lift when you stand on it
  - S = search furniture (hold)  -> find code fragments and bonuses
  - Collect all code fragments, then search the master terminal to escape.
  - Touching a robot zaps you and costs time. Don't run out of time!
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
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _detect_lang()

TXT = {
    "sub": {"nl": "Infiltreer het complex", "en": "Infiltrate the complex"},
    "intro": {"nl": "Welkom, agent. De deuren zijn achter je vergrendeld.",
              "en": "Welcome, agent. The doors have locked behind you."},
    "start": {"nl": "Druk op SPATIE om te starten", "en": "Press SPACE to start"},
    "ctrl_menu": {"nl": "Pijltjes = lopen   Spatie = springen   "
                        "Lift = ↑/↓   S = doorzoeken",
                  "en": "Arrows = walk   Space = jump   "
                        "Lift = ↑/↓   S = search"},
    "time": {"nl": "Tijd", "en": "Time"},
    "codes": {"nl": "Codes", "en": "Codes"},
    "room": {"nl": "Sector", "en": "Sector"},
    "found_piece": {"nl": "Codestuk gevonden!", "en": "Code fragment found!"},
    "snooze": {"nl": "Robots tijdelijk uitgeschakeld!",
               "en": "Robots disabled for a while!"},
    "gain_time": {"nl": "Bonustijd!", "en": "Bonus time!"},
    "empty": {"nl": "Niets bruikbaars...", "en": "Nothing useful..."},
    "need_all": {"nl": "Eerst alle codestukken verzamelen!",
                 "en": "Collect all code fragments first!"},
    "terminal_ready": {"nl": "Doorzoek de hoofdterminal om te ontsnappen!",
                       "en": "Search the master terminal to escape!"},
    "searching": {"nl": "Doorzoeken...", "en": "Searching..."},
    "win_title": {"nl": "Missie geslaagd!", "en": "Mission complete!"},
    "win_sub": {"nl": "Je bent ontsnapt met alle codes.",
                "en": "You escaped with every code."},
    "over_title": {"nl": "Tijd op!", "en": "Out of time!"},
    "over_sub": {"nl": "De missie is mislukt.", "en": "The mission failed."},
    "restart": {"nl": "Druk op R om opnieuw te spelen", "en": "Press R to play again"},
    "paused": {"nl": "GEPAUZEERD", "en": "PAUSED"},
    "resume": {"nl": "P = verder spelen", "en": "P = resume"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "sound": {"nl": "Geluid", "en": "Sound"},
    "off": {"nl": "uit", "en": "off"},
    "audio_hint": {"nl": "M = geluid aan/uit    - / + = volume",
                   "en": "M = sound on/off    - / + = volume"},
    "info_hint": {"nl": "I = info / donatie", "en": "I = info / donate"},
    "info_title": {"nl": "Over DraveMission", "en": "About DraveMission"},
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
# instellingen / settings
# ---------------------------------------------------------------------------
W, H = 960, 600
HUD = 52
FPS = 60
AUDIO_SR = 22050

DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

MENU, PLAY, OVER, WIN, INFO = "menu", "play", "over", "win", "info"

# physics
WALK = 3.4
GRAV = 0.6
JUMP = -11.6
LIFTSPD = 3.2
SEARCH_TIME = 1.8
START_TIME = 300.0
DEATH_PEN = 25.0

# colors
BG = (10, 12, 20)
WALLDK = (18, 22, 34)
FLOORC = (54, 60, 82)
FLOORTOP = (86, 96, 128)
PLATC = (46, 52, 74)
PLATTOP = (120, 130, 170)
SHAFTC = (16, 18, 30)
RAILC = (60, 66, 96)
LIFTC = (150, 200, 240)
AGENT = (90, 150, 230)
ROBOT = (210, 90, 70)
ROBOT2 = (240, 150, 60)
EYEC = (255, 240, 120)
FURN = (120, 100, 70)
FURN2 = (150, 130, 95)
TERMC = (90, 210, 150)
TEXT = (235, 240, 250)
SUB = (150, 165, 190)
AMBER = (240, 200, 60)
GREEN = (110, 210, 150)
BLUE = (110, 180, 240)
RED = (225, 90, 80)

# room geometry
FLOOR_TOP = H - 24
P_A = pygame.Rect(220, H - 150, 250, 14)   # slot a (low, left)
P_B = pygame.Rect(490, H - 270, 250, 14)   # slot b (mid, right)
P_C = pygame.Rect(220, H - 390, 250, 14)   # slot c (high, left)
SHAFT_X, SHAFT_W = 445, 70
LIFT_MINY = P_C.top
LIFT_MAXY = FLOOR_TOP

TOTAL_PIECES = 8


def _res(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


# ---------------------------------------------------------------------------
# audio helpers (procedureel, geen numpy)
# ---------------------------------------------------------------------------
def _tone(freq, ms, vol=0.5, wave="sine"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    buf = array.array("h", bytes(2 * n))
    atk = max(1, int(0.008 * AUDIO_SR))
    rel = max(1, int(0.06 * AUDIO_SR))
    ph = 0.0
    step = freq / AUDIO_SR
    for i in range(n):
        ph += step
        x = ph - math.floor(ph)
        if wave == "sine":
            s = math.sin(2 * math.pi * x)
        elif wave == "square":
            s = 1.0 if x < 0.5 else -1.0
        elif wave == "tri":
            s = 4 * abs(x - 0.5) - 1
        elif wave == "saw":
            s = 2 * x - 1
        elif wave == "noise":
            s = random.uniform(-1, 1)
        else:
            s = math.sin(2 * math.pi * x)
        e = 1.0
        if i < atk:
            e = i / atk
        elif i > n - rel:
            e = max(0.0, (n - i) / rel)
        buf[i] = int(max(-1.0, min(1.0, s * e * vol)) * 32767)
    return buf


def _sweep(f0, f1, ms, vol=0.5, wave="saw"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    buf = array.array("h", bytes(2 * n))
    rel = max(1, int(0.05 * AUDIO_SR))
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        ph += f / AUDIO_SR
        x = ph - math.floor(ph)
        if wave == "square":
            s = 1.0 if x < 0.5 else -1.0
        elif wave == "saw":
            s = 2 * x - 1
        elif wave == "noise":
            s = random.uniform(-1, 1)
        else:
            s = math.sin(2 * math.pi * x)
        e = 1.0 if i < n - rel else max(0.0, (n - i) / rel)
        buf[i] = int(max(-1.0, min(1.0, s * e * vol)) * 32767)
    return buf


def _seq(parts):
    out = array.array("h")
    for p in parts:
        out += p
    return out


def _mix(a, b):
    n = min(len(a), len(b))
    out = array.array("h", bytes(2 * n))
    for i in range(n):
        v = a[i] + b[i]
        out[i] = max(-32768, min(32767, v))
    return out


def _build_music():
    bpm = 122
    beat = 60000 / bpm / 2.0   # eighth notes
    scale = [220, 247, 262, 294, 330, 349, 392, 440]
    bass = [110, 110, 98, 98, 110, 110, 87, 98,
            110, 110, 131, 123, 110, 98, 82, 98]
    melA = [0, 2, 4, 2, 5, 4, 2, 0, 4, 5, 7, 5, 4, 2, 0, 2]
    melB = [4, 4, 5, 7, 4, 2, 0, 2, 5, 4, 2, 4, 0, 0, 2, 4]
    bb = array.array("h")
    mm = array.array("h")
    for k in range(16):
        bb += _tone(bass[k], beat, 0.34, "tri")
        mm += _tone(scale[melA[k] % len(scale)], beat, 0.20, "square")
    for k in range(16):
        bb += _tone(bass[k], beat, 0.34, "tri")
        mm += _tone(scale[melB[k] % len(scale)], beat, 0.20, "square")
    n = min(len(bb), len(mm))
    return pygame.mixer.Sound(buffer=_mix(bb[:n], mm[:n]))


# ---------------------------------------------------------------------------
# rooms
# ---------------------------------------------------------------------------
def _furn_on(plat, kind, content):
    # meubel aan de liftkant van het platform (= waar je afstapt)
    if plat.centerx < SHAFT_X:          # platform links van schacht -> rechterrand
        fx = plat.right - 60
    else:                               # platform rechts van schacht -> linkerrand
        fx = plat.left + 12
    r = pygame.Rect(fx, plat.top - 38, 48, 38)
    return {"rect": r, "kind": kind, "content": content,
            "searched": False, "found": False, "prog": 0.0}


def _furn_floor(cx, kind, content):
    r = pygame.Rect(cx - 26, FLOOR_TOP - 42, 52, 42)
    return {"rect": r, "kind": kind, "content": content,
            "searched": False, "found": False, "prog": 0.0}


def _robot(spec, plats):
    kind = spec[0]
    if kind == "f":          # floor patrol
        _, x0, x1, spd = spec
        y = FLOOR_TOP - 34
        mid = float((x0 + x1) // 2)
        return {"kind": "patrol", "x": mid, "y": float(y),
                "w": 30, "h": 34, "vx": spd, "x0": x0, "x1": x1,
                "sx": mid, "sy": float(y), "sv": spd}
    if kind in ("a", "b", "c"):    # platform patrol (alleen ver van de liftkant)
        p = {"a": plats[0], "b": plats[1], "c": plats[2]}[kind]
        spd = spec[1]
        y = p.top - 34
        if p.centerx < SHAFT_X:        # links platform -> robot patrouilleert links
            x0 = p.left + 8
            x1 = p.right - 150
        else:                          # rechts platform -> robot patrouilleert rechts
            x0 = p.left + 120
            x1 = p.right - 30
        mid = float((x0 + x1) // 2)
        return {"kind": "patrol", "x": mid, "y": float(y),
                "w": 30, "h": 34, "vx": spd, "x0": x0, "x1": x1,
                "sx": mid, "sy": float(y), "sv": spd}
    # floater
    _, y, spd = spec
    return {"kind": "float", "x": float(random.randint(120, 820)), "y": float(y),
            "w": 30, "h": 30, "vx": spd, "x0": 30, "x1": W - 60,
            "sx": float(random.randint(120, 820)), "sy": float(y), "sv": spd}


def _room(contents, robot_specs, terminal=False):
    plats = [P_A.copy(), P_B.copy(), P_C.copy()]
    furn = []
    for slot, (kind, content) in contents.items():
        p = {"a": plats[0], "b": plats[1], "c": plats[2]}[slot]
        furn.append(_furn_on(p, kind, content))
    if terminal:
        furn.append(_furn_floor(W // 2 + 150, "terminal", "exit"))
    robots = [_robot(s, plats) for s in robot_specs]
    lift = {"x": SHAFT_X, "w": SHAFT_W, "y": float(LIFT_MAXY),
            "miny": LIFT_MINY, "maxy": LIFT_MAXY}
    return {"plats": plats, "furn": furn, "robots": robots, "lift": lift}


def build_rooms():
    rooms = []
    # sector 1
    rooms.append(_room(
        {"a": ("computer", "piece"), "b": ("cabinet", "snooze"),
         "c": ("computer", "empty")},
        [("f", 520, 900, 1.9)]))
    # sector 2
    rooms.append(_room(
        {"a": ("computer", "piece"), "b": ("cabinet", "time"),
         "c": ("computer", "piece")},
        [("f", 520, 900, 2.0), ("b", 1.9)]))
    # sector 3
    rooms.append(_room(
        {"a": ("cabinet", "snooze"), "b": ("computer", "piece"),
         "c": ("computer", "piece")},
        [("a", 2.0), ("c", 2.0)]))
    # sector 4
    rooms.append(_room(
        {"a": ("computer", "piece"), "b": ("cabinet", "empty"),
         "c": ("computer", "time")},
        [("f", 60, 430, 2.1), ("b", 2.0), ("float", 270, 1.4)]))
    # sector 5
    rooms.append(_room(
        {"a": ("computer", "piece"), "b": ("computer", "piece"),
         "c": ("cabinet", "snooze")},
        [("a", 2.1), ("c", 2.1), ("f", 520, 900, 2.1)]))
    # sector 6 (terminal)
    rooms.append(_room(
        {"a": ("cabinet", "time"), "b": ("computer", "empty"),
         "c": ("computer", "empty")},
        [("f", 60, 430, 2.0), ("float", 300, 1.5)], terminal=True))
    return rooms


# ---------------------------------------------------------------------------
class Agent:
    def __init__(self):
        self.w = 22
        self.h = 38
        self.x = 40.0
        self.y = float(FLOOR_TOP - self.h)
        self.vx = 0.0
        self.vy = 0.0
        self.face = 1
        self.on_ground = True
        self.on_lift = None

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


class Game:
    def __init__(self):
        pygame.mixer.pre_init(AUDIO_SR, -16, 1, 512)
        pygame.init()
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(AUDIO_SR, -16, 1, 512)
        except Exception:
            pass
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("DraveMission")
        try:
            ic = pygame.image.load(_res("assets", "icon-64.png"))
            pygame.display.set_icon(ic)
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("Segoe UI", 56, bold=True)
        self.mid = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 22)
        self.small = pygame.font.SysFont("Segoe UI", 16)
        self.agent_surf = self._make_agent_surface()

        self.volume = 0.6
        self.muted = False
        self.link_rects = []
        self.flip_angle = 0.0
        self.state = MENU
        self._init_audio()
        self.reset()

    # ---- audio ----
    def _init_audio(self):
        self.audio_ok = pygame.mixer.get_init() is not None
        self.sfx = {}
        self.music = None
        self._mch = None
        self._music_on = False
        if self.audio_ok:
            threading.Thread(target=self._build_audio, daemon=True).start()

    def _build_audio(self):
        try:
            sfx = {
                "jump": pygame.mixer.Sound(_sweep(300, 720, 150, 0.4, "square")),
                "found": pygame.mixer.Sound(_seq([
                    _tone(660, 90, 0.4, "square"),
                    _tone(990, 150, 0.4, "square")])),
                "search": pygame.mixer.Sound(_tone(430, 45, 0.22, "square")),
                "bonus": pygame.mixer.Sound(_seq([
                    _tone(523, 70, 0.4, "square"),
                    _tone(659, 70, 0.4, "square"),
                    _tone(784, 130, 0.4, "square")])),
                "zap": pygame.mixer.Sound(_sweep(760, 90, 280, 0.5, "saw")),
                "win": pygame.mixer.Sound(_seq([
                    _tone(523, 120, 0.4), _tone(659, 120, 0.4),
                    _tone(784, 120, 0.4), _tone(1047, 280, 0.45)])),
            }
            music = _build_music()
            self.sfx = sfx
            self.music = music
            self._apply_volume()
            if self._music_on:
                self._start_music()
        except Exception:
            pass

    def _start_music(self):
        if not self.music:
            return
        try:
            self._mch = self.music.play(-1)
            self._apply_volume()
        except Exception:
            self._mch = None

    def _music(self, on):
        self._music_on = on
        if on:
            if self.music and (self._mch is None or not self._mch.get_busy()):
                self._start_music()
        else:
            if self._mch:
                try:
                    self._mch.stop()
                except Exception:
                    pass
            self._mch = None

    def _apply_volume(self):
        v = 0.0 if self.muted else self.volume
        for s in self.sfx.values():
            try:
                s.set_volume(v)
            except Exception:
                pass
        if self.music:
            try:
                self.music.set_volume(v * 0.55)
            except Exception:
                pass

    def set_volume(self, d):
        self.volume = max(0.0, min(1.0, self.volume + d))
        if self.volume > 0:
            self.muted = False
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    def play_sfx(self, name):
        if self.muted:
            return
        s = self.sfx.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    # ---- agent sprite ----
    def _make_agent_surface(self):
        s = pygame.Surface((26, 42), pygame.SRCALPHA)
        pygame.draw.rect(s, (28, 38, 66), (7, 28, 5, 12))
        pygame.draw.rect(s, (28, 38, 66), (14, 28, 5, 12))
        pygame.draw.rect(s, AGENT, (5, 12, 16, 18), border_radius=3)
        pygame.draw.circle(s, (238, 214, 190), (13, 8), 6)
        pygame.draw.rect(s, (18, 26, 52), (8, 6, 11, 4))
        return s

    # ---- game state ----
    def reset(self):
        self.rooms = build_rooms()
        self.room_i = 0
        self.agent = Agent()
        self.pieces = 0
        self.time_left = START_TIME
        self.snooze_t = 0.0
        self.invuln_t = 2.0
        self.searching = None
        self.search_t = 0.0
        self.paused = False
        self.msg = ""
        self.msg_t = 0.0

    @property
    def room(self):
        return self.rooms[self.room_i]

    def flash(self, text):
        self.msg = text
        self.msg_t = 2.2

    def load_room(self, i, entry):
        self.room_i = i
        a = self.agent
        if entry == "left":
            a.x = float(W - a.w - 6)
        elif entry == "right":
            a.x = 6.0
        else:
            a.x = 40.0
        a.y = float(FLOOR_TOP - a.h)
        a.vy = 0.0
        a.on_ground = True
        a.on_lift = None
        self.invuln_t = 2.0
        self.searching = None
        self.search_t = 0.0
        for r in self.room["robots"]:
            r["x"] = r["sx"]
            r["y"] = r["sy"]
            r["vx"] = abs(r["sv"])
        self.room["lift"]["y"] = float(LIFT_MAXY)

    def do_jump(self):
        a = self.agent
        if a.on_ground:
            a.vy = JUMP
            a.on_ground = False
            a.on_lift = None
            self.play_sfx("jump")

    def zapped(self):
        self.time_left -= DEATH_PEN
        self.play_sfx("zap")
        self.load_room(self.room_i, "start")

    # ---- update ----
    def update_play(self, dt, keys):
        a = self.agent
        room = self.room

        # horizontal intent
        ax = 0
        if keys[pygame.K_LEFT]:
            ax -= 1
            a.face = -1
        if keys[pygame.K_RIGHT]:
            ax += 1
            a.face = 1
        a.vx = ax * WALK

        # lift riding (uses on_lift from last frame)
        rode = False
        L = a.on_lift
        # stap automatisch op de lift als je boven de schacht staat en ↑/↓ drukt
        if L is None and a.on_ground and (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            lf = room["lift"]
            cx = a.x + a.w / 2
            feet = a.y + a.h
            if lf["x"] <= cx <= lf["x"] + lf["w"] and \
                    lf["miny"] - 4 <= feet <= lf["maxy"] + 4:
                lf["y"] = max(lf["miny"], min(lf["maxy"], feet))
                a.on_lift = lf
                L = lf
        if L is not None:
            dy = 0.0
            if keys[pygame.K_UP]:
                dy = -LIFTSPD
            elif keys[pygame.K_DOWN]:
                dy = LIFTSPD
            newy = max(L["miny"], min(L["maxy"], L["y"] + dy))
            L["y"] = newy
            a.y = newy - a.h
            a.vy = 0.0
            a.on_ground = True
            rode = True
            # walked off the lift horizontally?
            if not (a.x + a.w > L["x"] and a.x < L["x"] + L["w"]):
                rode = False
                a.on_lift = None

        # move horizontal
        a.x += a.vx

        # room transitions / walls
        if a.x < -2:
            if self.room_i > 0:
                self.load_room(self.room_i - 1, "left")
                return
            a.x = 0.0
        elif a.x + a.w > W + 2:
            if self.room_i < len(self.rooms) - 1:
                self.load_room(self.room_i + 1, "right")
                return
            a.x = float(W - a.w)

        # vertical
        if not rode:
            a.vy += GRAV
            if a.vy > 16:
                a.vy = 16
            a.y += a.vy
            feet = a.y + a.h
            prev_feet = feet - a.vy
            landed = None
            lift_now = None
            solids = list(room["plats"]) + [pygame.Rect(0, FLOOR_TOP, W, 24)]
            if a.vy >= 0:
                for p in solids:
                    if a.x + a.w > p.left + 2 and a.x < p.right - 2:
                        if prev_feet <= p.top + 2 and feet >= p.top:
                            landed = p.top
                            break
                lf = room["lift"]
                if (a.x + a.w > lf["x"] and a.x < lf["x"] + lf["w"]
                        and prev_feet <= lf["y"] + 2 and feet >= lf["y"]):
                    landed = lf["y"]
                    lift_now = lf
            if landed is not None:
                a.y = landed - a.h
                a.vy = 0.0
                a.on_ground = True
                a.on_lift = lift_now
            else:
                a.on_ground = False
                a.on_lift = None

        # somersault spin
        if not a.on_ground:
            self.flip_angle = (self.flip_angle - 16 * a.face) % 360
        else:
            self.flip_angle = 0.0

        # search furniture
        target = None
        if a.on_ground and a.on_lift is None:
            ar = a.rect
            for f in room["furn"]:
                if f["searched"]:
                    continue
                fr = f["rect"]
                if ar.right > fr.left and ar.left < fr.right and \
                        abs((a.y + a.h) - (FLOOR_TOP if fr.bottom >= FLOOR_TOP
                                           else fr.bottom)) < 6:
                    target = f
                    break
        if keys[pygame.K_s] and target is not None:
            self.searching = target
            prev = target["prog"]
            target["prog"] += dt          # voortgang blijft bewaard
            if int(target["prog"] * 6) != int(prev * 6):
                self.play_sfx("search")
            if target["prog"] >= SEARCH_TIME:
                self._reveal(target)
                self.searching = None
        else:
            self.searching = None

        # robots
        if self.invuln_t > 0:
            self.invuln_t -= dt
        if self.snooze_t > 0:
            self.snooze_t -= dt
        else:
            ar = a.rect
            hit = False
            for r in room["robots"]:
                if r["kind"] == "patrol":
                    r["x"] += r["vx"]
                    if r["x"] < r["x0"]:
                        r["x"] = float(r["x0"])
                        r["vx"] = abs(r["vx"])
                    elif r["x"] > r["x1"]:
                        r["x"] = float(r["x1"])
                        r["vx"] = -abs(r["vx"])
                else:  # float toward agent
                    sp = abs(r["sv"])
                    if a.x + 4 > r["x"]:
                        r["x"] += sp
                    elif a.x - 4 < r["x"]:
                        r["x"] -= sp
                    ty = a.y
                    if ty > r["y"]:
                        r["y"] += sp * 0.7
                    elif ty < r["y"]:
                        r["y"] -= sp * 0.7
                    r["x"] = max(r["x0"], min(r["x1"], r["x"]))
                    r["y"] = max(HUD + 10, min(FLOOR_TOP - r["h"], r["y"]))
                rr = pygame.Rect(int(r["x"]), int(r["y"]), r["w"], r["h"])
                if self.invuln_t <= 0 and ar.colliderect(rr.inflate(2, 2)):
                    hit = True
            if hit:
                self.zapped()
                return

        # time
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.state = OVER
            self._music(False)
        if self.msg_t > 0:
            self.msg_t -= dt

    def _reveal(self, f):
        f["searched"] = True
        f["found"] = True
        c = f["content"]
        if c == "exit":
            if self.pieces >= TOTAL_PIECES:
                self.state = WIN
                self.play_sfx("win")
                self._music(False)
            else:
                f["searched"] = False
                f["found"] = False
                f["prog"] = 0.0
                self.flash(T("need_all"))
            return
        if c == "piece":
            self.pieces += 1
            self.play_sfx("found")
            if self.pieces >= TOTAL_PIECES:
                self.flash(T("terminal_ready"))
            else:
                self.flash(T("found_piece"))
        elif c == "snooze":
            self.snooze_t = 10.0
            self.play_sfx("bonus")
            self.flash(T("snooze"))
        elif c == "time":
            self.time_left += 30
            self.play_sfx("bonus")
            self.flash(T("gain_time"))
        else:
            self.flash(T("empty"))

    # ---- drawing ----
    def _draw_link(self, text, cx, cy, font, color):
        surf = font.render(text, True, color)
        r = surf.get_rect(center=(cx, cy))
        self.screen.blit(surf, r)
        pygame.draw.line(self.screen, color, (r.left, r.bottom + 1),
                         (r.right, r.bottom + 1), 1)
        self.link_rects.append((r, DONATE))
        return r

    def _draw_furn(self, f):
        s = self.screen
        r = f["rect"]
        if f["kind"] == "terminal":
            col = TERMC if self.pieces >= TOTAL_PIECES else (70, 110, 95)
            pygame.draw.rect(s, (40, 50, 60), r, border_radius=4)
            pygame.draw.rect(s, col, (r.x + 6, r.y + 6, r.w - 12, 20),
                             border_radius=3)
            for i in range(3):
                pygame.draw.line(s, (20, 30, 30),
                                 (r.x + 10, r.y + 11 + i * 5),
                                 (r.right - 10, r.y + 11 + i * 5), 1)
            return
        body = FURN if f["kind"] == "computer" else FURN2
        pygame.draw.rect(s, body, r, border_radius=3)
        pygame.draw.rect(s, (30, 34, 50), r, 2, border_radius=3)
        if f["kind"] == "computer":
            scr = (90, 200, 160) if not f["searched"] else (60, 70, 80)
            pygame.draw.rect(s, scr, (r.x + 8, r.y + 6, r.w - 16, 16),
                             border_radius=2)
        else:
            pygame.draw.line(s, (30, 34, 50), (r.centerx, r.y + 4),
                             (r.centerx, r.bottom - 4), 2)
        if f["searched"] and f["content"] != "exit":
            mark = self.small.render("✓", True, GREEN)
            s.blit(mark, (r.centerx - 6, r.y - 18))

    def _draw_robot(self, r):
        s = self.screen
        dim = self.snooze_t > 0
        body = (90, 100, 110) if dim else (ROBOT2 if r["kind"] == "float" else ROBOT)
        rect = pygame.Rect(int(r["x"]), int(r["y"]), r["w"], r["h"])
        if r["kind"] == "float":
            pygame.draw.circle(s, body, rect.center, r["w"] // 2)
            pygame.draw.circle(s, (30, 20, 20), rect.center, r["w"] // 2, 2)
            eye = (40, 40, 40) if dim else EYEC
            pygame.draw.circle(s, eye, (rect.centerx, rect.centery - 2), 4)
        else:
            pygame.draw.rect(s, body, rect, border_radius=4)
            pygame.draw.rect(s, (30, 20, 20), rect, 2, border_radius=4)
            eye = (40, 40, 40) if dim else EYEC
            ex = rect.centerx + (6 if r["vx"] >= 0 else -6)
            pygame.draw.circle(s, eye, (ex, rect.y + 12), 4)
            pygame.draw.rect(s, (40, 30, 30), (rect.x + 6, rect.bottom - 6,
                                               rect.w - 12, 4))
        if not dim:
            t = pygame.time.get_ticks() / 120.0
            rad = r["w"] // 2 + 4 + int(2 * math.sin(t))
            aura = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (255, 230, 120, 40), (rad + 1, rad + 1), rad)
            s.blit(aura, (rect.centerx - rad - 1, rect.centery - rad - 1))

    def _draw_agent(self):
        a = self.agent
        if self.invuln_t > 0 and int(self.invuln_t * 12) % 2 == 0:
            return
        surf = self.agent_surf
        if a.face < 0:
            surf = pygame.transform.flip(surf, True, False)
        if not a.on_ground:
            rot = pygame.transform.rotate(surf, self.flip_angle)
            rr = rot.get_rect(center=(int(a.x + a.w / 2), int(a.y + a.h / 2)))
            self.screen.blit(rot, rr)
        else:
            self.screen.blit(surf, (int(a.x - 2), int(a.y - 4)))
        if self.searching is not None:
            w = 50
            px = a.x + a.w / 2 - w / 2
            py = a.y - 16
            pygame.draw.rect(self.screen, (40, 50, 70), (px, py, w, 7),
                             border_radius=3)
            fillw = int(w * min(1.0, self.searching["prog"] / SEARCH_TIME))
            pygame.draw.rect(self.screen, GREEN, (px, py, fillw, 7),
                             border_radius=3)

    def draw_play(self):
        s = self.screen
        room = self.room
        s.fill(BG)
        # back wall
        pygame.draw.rect(s, WALLDK, (0, HUD, W, H - HUD))
        # lift shaft
        lf = room["lift"]
        pygame.draw.rect(s, SHAFTC, (lf["x"], HUD, lf["w"], H - HUD))
        pygame.draw.line(s, RAILC, (lf["x"] + 6, HUD), (lf["x"] + 6, H), 2)
        pygame.draw.line(s, RAILC, (lf["x"] + lf["w"] - 6, HUD),
                         (lf["x"] + lf["w"] - 6, H), 2)
        # platforms
        for p in room["plats"]:
            pygame.draw.rect(s, PLATC, p)
            pygame.draw.line(s, PLATTOP, (p.left, p.top), (p.right, p.top), 2)
        # floor
        pygame.draw.rect(s, FLOORC, (0, FLOOR_TOP, W, 24))
        pygame.draw.line(s, FLOORTOP, (0, FLOOR_TOP), (W, FLOOR_TOP), 2)
        # lift platform
        pygame.draw.rect(s, LIFTC, (lf["x"] + 4, int(lf["y"]), lf["w"] - 8, 8),
                         border_radius=3)
        # furniture
        for f in room["furn"]:
            self._draw_furn(f)
        # robots
        for r in room["robots"]:
            self._draw_robot(r)
        # agent
        self._draw_agent()
        self.draw_hud()
        if self.msg_t > 0 and self.msg:
            mb = self.font.render(self.msg, True, AMBER)
            bg = pygame.Surface((mb.get_width() + 24, mb.get_height() + 10),
                                pygame.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            s.blit(bg, (W / 2 - bg.get_width() / 2, HUD + 14))
            s.blit(mb, (W / 2 - mb.get_width() / 2, HUD + 19))

    def draw_hud(self):
        s = self.screen
        pygame.draw.rect(s, (8, 10, 18), (0, 0, W, HUD))
        pygame.draw.line(s, (40, 46, 66), (0, HUD), (W, HUD), 2)
        mins = int(self.time_left) // 60
        secs = int(self.time_left) % 60
        tcol = RED if self.time_left < 30 else TEXT
        tt = self.mid.render("%s %d:%02d" % (T("time"), mins, secs), True, tcol)
        s.blit(tt, (16, 10))
        pc = self.font.render("%s %d/%d" % (T("codes"), self.pieces, TOTAL_PIECES),
                              True, AMBER)
        s.blit(pc, (W / 2 - pc.get_width() / 2, 14))
        rm = self.font.render("%s %d/%d" % (T("room"), self.room_i + 1,
                                            len(self.rooms)), True, SUB)
        s.blit(rm, (W - rm.get_width() - 16, 14))
        if self.snooze_t > 0:
            sn = self.small.render("ZZZ %0.0f" % self.snooze_t, True, GREEN)
            s.blit(sn, (W - sn.get_width() - 16, 34))

    def draw_pause(self):
        s = self.screen
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        s.blit(ov, (0, 0))
        t = self.big.render(T("paused"), True, TEXT)
        s.blit(t, (W / 2 - t.get_width() / 2, H / 2 - 70))
        r = self.font.render(T("resume"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, H / 2 + 4))
        a = self.small.render(T("audio_hint"), True, SUB)
        s.blit(a, (W / 2 - a.get_width() / 2, H / 2 + 40))

    def draw_menu(self):
        s = self.screen
        s.fill(BG)
        for i in range(0, W, 40):
            pygame.draw.line(s, (16, 20, 32), (i, 0), (i, H), 1)
        title = self.big.render("DraveMission", True, AGENT)
        s.blit(title, (W / 2 - title.get_width() / 2, 120))
        sub = self.mid.render(T("sub"), True, AMBER)
        s.blit(sub, (W / 2 - sub.get_width() / 2, 196))
        intro = self.font.render(T("intro"), True, SUB)
        s.blit(intro, (W / 2 - intro.get_width() / 2, 256))
        st = self.font.render(T("start"), True, TEXT)
        s.blit(st, (W / 2 - st.get_width() / 2, 340))
        ct = self.small.render(T("ctrl_menu"), True, SUB)
        s.blit(ct, (W / 2 - ct.get_width() / 2, 392))
        dw = self.small.render(T("donationware"), True, SUB)
        s.blit(dw, (W / 2 - dw.get_width() / 2, 470))
        ih = self.small.render(T("info_hint") + "    " + T("quit"), True, AMBER)
        s.blit(ih, (W / 2 - ih.get_width() / 2, 496))

    def draw_info(self):
        s = self.screen
        s.fill(BG)
        title = self.mid.render(T("info_title"), True, AGENT)
        s.blit(title, (W / 2 - title.get_width() / 2, 150))
        dwt = self.font.render(T("donationware"), True, TEXT)
        s.blit(dwt, (W / 2 - dwt.get_width() / 2, 230))
        dl = self.small.render(T("donate_line"), True, SUB)
        s.blit(dl, (W / 2 - dl.get_width() / 2, 286))
        self._draw_link(DONATE, W / 2, 324, self.font, BLUE)
        dc = self.small.render(T("donate_click"), True, SUB)
        s.blit(dc, (W / 2 - dc.get_width() / 2, 356))
        ctc = self.small.render(T("contact_lbl") + ":  " + CONTACT, True, SUB)
        s.blit(ctc, (W / 2 - ctc.get_width() / 2, 410))
        ba = self.small.render(T("back_any"), True, AMBER)
        s.blit(ba, (W / 2 - ba.get_width() / 2, 480))

    def _end_screen(self, title_txt, sub_txt, tcol):
        s = self.screen
        s.fill(BG)
        t = self.big.render(title_txt, True, tcol)
        s.blit(t, (W / 2 - t.get_width() / 2, 170))
        sb = self.mid.render(sub_txt, True, TEXT)
        s.blit(sb, (W / 2 - sb.get_width() / 2, 256))
        sc = self.font.render("%s %d/%d" % (T("codes"), self.pieces,
                                            TOTAL_PIECES), True, AMBER)
        s.blit(sc, (W / 2 - sc.get_width() / 2, 318))
        r = self.font.render(T("restart"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, 380))
        dl = self.small.render(T("donate_line"), True, SUB)
        s.blit(dl, (W / 2 - dl.get_width() / 2, 444))
        self._draw_link(DONATE, W / 2, 478, self.font, BLUE)

    def draw_over(self):
        self._end_screen(T("over_title"), T("over_sub"), RED)

    def draw_win(self):
        self._end_screen(T("win_title"), T("win_sub"), GREEN)

    # ---- main loop ----
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if dt > 0.05:
                dt = 0.05
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                    if e.key == pygame.K_m:
                        self.toggle_mute()
                    elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.set_volume(-0.1)
                    elif e.key in (pygame.K_EQUALS, pygame.K_PLUS,
                                   pygame.K_KP_PLUS):
                        self.set_volume(0.1)
                    if e.key == pygame.K_d:
                        webbrowser.open(DONATE)
                    if self.state == MENU:
                        if e.key == pygame.K_SPACE:
                            self.reset()
                            self.state = PLAY
                            self._music(True)
                        elif e.key == pygame.K_i:
                            self.state = INFO
                    elif self.state == INFO:
                        self.state = MENU
                    elif self.state == PLAY:
                        if e.key == pygame.K_p:
                            self.paused = not self.paused
                        elif e.key == pygame.K_SPACE and not self.paused:
                            self.do_jump()
                    elif self.state in (OVER, WIN) and e.key == pygame.K_r:
                        self.state = MENU
                        self._music(False)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, url in self.link_rects:
                        if r.collidepoint(e.pos):
                            webbrowser.open(url)
                            break

            keys = pygame.key.get_pressed()
            if self.state == PLAY and not self.paused:
                self.update_play(dt, keys)

            self.link_rects = []
            if self.state == MENU:
                self.draw_menu()
            elif self.state == INFO:
                self.draw_info()
            elif self.state == PLAY:
                self.draw_play()
                if self.paused:
                    self.draw_pause()
            elif self.state == OVER:
                self.draw_over()
            elif self.state == WIN:
                self.draw_win()

            mp = pygame.mouse.get_pos()
            hov = any(r.collidepoint(mp) for r, _ in self.link_rects)
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if hov else pygame.SYSTEM_CURSOR_ARROW)
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()

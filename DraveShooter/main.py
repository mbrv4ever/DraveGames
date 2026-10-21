# -*- coding: utf-8 -*-
"""DraveShooter - een vrolijke cartoon-FPS (Panda3D).

Schiet op robots, aliens/UFO's en slijmmonsters in een arena. Besturing met
richt-hulp: lopen + muis kijken in rustig tempo, en het vizier 'lockt'
automatisch op de dichtstbijzijnde vijand bij je kruis. Cartoonachtig en
onschuldig. Taal volgt de pc (NL/EN). Donationware. Portable.

Speel/Play:
  - WASD / pijltjes: lopen    Muis: kijken    Linkermuis / Spatie: schieten
  - 1 Levels  2 Survival  3 Oefenbaan   P pauze  I info  M geluid  Esc menu/quit
"""
import array
import locale
import math
import os
import random
import sys
import threading
import wave
import webbrowser

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-title DraveShooter")
loadPrcFileData("", "win-size 1000 680")
loadPrcFileData("", "framebuffer-multisample 1")
loadPrcFileData("", "multisamples 4")
loadPrcFileData("", "sync-video 1")

_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "assets", "icon.ico")
if os.path.exists(_ICON):
    loadPrcFileData("", "icon-filename %s" % _ICON.replace("\\", "/"))

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton, DirectFrame
from panda3d.core import (AmbientLight, DirectionalLight, Vec3, Vec4, Point3,
                          ClockObject, TextNode, NodePath, GeomNode, Geom,
                          GeomVertexFormat, GeomVertexData, GeomVertexWriter,
                          GeomTriangles, Filename, WindowProperties)

globalClock = ClockObject.getGlobalClock()


def _lang():
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _lang()

TXT = {
    "sub": {"nl": "Cartoon-arena-shooter", "en": "Cartoon arena shooter"},
    "m_levels": {"nl": "1  Levels", "en": "1  Levels"},
    "m_surv": {"nl": "2  Survival (golven)", "en": "2  Survival (waves)"},
    "m_prac": {"nl": "3  Oefenbaan (doelen)", "en": "3  Practice (targets)"},
    "ctrl": {"nl": "Alleen de muis: klik om te schieten",
             "en": "Mouse only: click to shoot"},
    "aim_help": {"nl": "Het vizier draait vanzelf naar de dichtstbijzijnde "
                       "vijand; jij hoeft alleen te klikken.",
                 "en": "The sight turns to the nearest enemy by itself; you only "
                       "need to click."},
    "health": {"nl": "Leven", "en": "Health"},
    "score": {"nl": "Score", "en": "Score"},
    "level": {"nl": "Level", "en": "Level"},
    "wave": {"nl": "Golf", "en": "Wave"},
    "left": {"nl": "Over", "en": "Left"},
    "practice": {"nl": "Oefenbaan - raak de doelen!", "en": "Practice - hit the targets!"},
    "level_done": {"nl": "Level gehaald!", "en": "Level complete!"},
    "wave_done": {"nl": "Golf overleefd!", "en": "Wave survived!"},
    "win_title": {"nl": "Alle levels gehaald!", "en": "All levels cleared!"},
    "over_title": {"nl": "Je bent verslagen!", "en": "You're down!"},
    "restart": {"nl": "Druk op R voor het menu", "en": "Press R for the menu"},
    "paused": {"nl": "GEPAUZEERD (P = verder)", "en": "PAUSED (P = resume)"},
    "menu_hint": {"nl": "Klik op een knop om te starten", "en": "Click a button to start"},
    "sound_off": {"nl": "geluid uit", "en": "sound off"},
    "info_hint": {"nl": "I = info / donatie", "en": "I = info / donate"},
    "info_title": {"nl": "Over DraveShooter", "en": "About DraveShooter"},
    "donationware": {"nl": "Donationware - gratis te spelen.",
                     "en": "Donationware - free to play."},
    "donate_line": {"nl": "Bevalt het? Een donatie wordt gewaardeerd:",
                    "en": "Enjoying it? A donation is appreciated:"},
    "contact": {"nl": "Contact", "en": "Contact"},
    "back": {"nl": "Druk op I om terug te gaan", "en": "Press I to go back"},
    "click_play": {"nl": "Klik in het venster om te spelen", "en": "Click the window to play"},
}


def T(k):
    d = TXT.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"
AUDIO_SR = 22050

ARENA = 22.0
EYE = 1.7
MOVE = 6.5
SENS = 0.13
AIM_CONE = math.radians(15)
RANGE = 70.0
FIRE_CD = 0.14

MENU, PLAY, OVER, WIN, INFO = "menu", "play", "over", "win", "info"
LEVELS, SURVIVAL, PRACTICE = "levels", "survival", "practice"


# ---------------------------------------------------------------------------
def _cube_node():
    fmt = GeomVertexFormat.getV3n3()
    vd = GeomVertexData("c", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vd, "vertex")
    nw = GeomVertexWriter(vd, "normal")
    F = [((1, 0, 0), [(.5, -.5, -.5), (.5, .5, -.5), (.5, .5, .5), (.5, -.5, .5)]),
         ((-1, 0, 0), [(-.5, .5, -.5), (-.5, -.5, -.5), (-.5, -.5, .5), (-.5, .5, .5)]),
         ((0, 1, 0), [(.5, .5, -.5), (-.5, .5, -.5), (-.5, .5, .5), (.5, .5, .5)]),
         ((0, -1, 0), [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, -.5, .5), (-.5, -.5, .5)]),
         ((0, 0, 1), [(-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]),
         ((0, 0, -1), [(-.5, .5, -.5), (.5, .5, -.5), (.5, -.5, -.5), (-.5, -.5, -.5)])]
    t = GeomTriangles(Geom.UHStatic)
    i = 0
    for n, vs in F:
        for v in vs:
            vw.addData3(*v)
            nw.addData3(*n)
        t.addVertices(i, i + 1, i + 2)
        t.addVertices(i, i + 2, i + 3)
        i += 4
    g = Geom(vd)
    g.addPrimitive(t)
    nd = GeomNode("c")
    nd.addGeom(g)
    return nd


def _sphere_node(sl=16, st=11):
    fmt = GeomVertexFormat.getV3n3()
    vd = GeomVertexData("s", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vd, "vertex")
    nw = GeomVertexWriter(vd, "normal")
    for i in range(st + 1):
        la = math.pi * (i / st) - math.pi / 2
        for j in range(sl + 1):
            lo = 2 * math.pi * (j / sl)
            x = math.cos(la) * math.cos(lo)
            y = math.cos(la) * math.sin(lo)
            z = math.sin(la)
            vw.addData3(x, y, z)
            nw.addData3(x, y, z)
    t = GeomTriangles(Geom.UHStatic)
    row = sl + 1
    for i in range(st):
        for j in range(sl):
            a = i * row + j
            t.addVertices(a, a + row, a + 1)
            t.addVertices(a + 1, a + row, a + row + 1)
    g = Geom(vd)
    g.addPrimitive(t)
    nd = GeomNode("s")
    nd.addGeom(g)
    return nd


# ---------------------------------------------------------------------------
# audio
# ---------------------------------------------------------------------------
def _tone(f, ms, vol=0.5, w="sine"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    b = array.array("h", bytes(2 * n))
    atk = max(1, int(0.006 * AUDIO_SR))
    rel = max(1, int(0.05 * AUDIO_SR))
    ph = 0.0
    for i in range(n):
        ph += f / AUDIO_SR
        x = ph - math.floor(ph)
        if w == "square":
            s = 1.0 if x < 0.5 else -1.0
        elif w == "tri":
            s = 4 * abs(x - 0.5) - 1
        elif w == "saw":
            s = 2 * x - 1
        elif w == "noise":
            s = random.uniform(-1, 1)
        else:
            s = math.sin(2 * math.pi * x)
        e = 1.0
        if i < atk:
            e = i / atk
        elif i > n - rel:
            e = max(0.0, (n - i) / rel)
        b[i] = int(max(-1.0, min(1.0, s * e * vol)) * 32767)
    return b


def _sweep(f0, f1, ms, vol=0.5, w="saw"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    b = array.array("h", bytes(2 * n))
    rel = max(1, int(0.04 * AUDIO_SR))
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        ph += f / AUDIO_SR
        x = ph - math.floor(ph)
        s = (random.uniform(-1, 1) if w == "noise"
             else (1.0 if x < 0.5 else -1.0) if w == "square" else 2 * x - 1)
        e = 1.0 if i < n - rel else max(0.0, (n - i) / rel)
        b[i] = int(max(-1.0, min(1.0, s * e * vol)) * 32767)
    return b


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


def _music():
    bpm = 138
    beat = 60000 / bpm / 2.0
    scale = [220, 247, 262, 294, 330, 349, 392, 440]
    bass = [110, 110, 98, 110, 131, 110, 98, 82,
            110, 110, 123, 110, 147, 131, 110, 98]
    mel = [0, 0, 3, 4, 2, 0, 4, 2, 5, 4, 2, 0, 4, 5, 7, 4]
    bb = array.array("h")
    mm = array.array("h")
    for k in range(16):
        bb += _tone(bass[k], beat, 0.28, "saw")
        mm += _tone(scale[mel[k] % len(scale)], beat, 0.16, "square")
    n = min(len(bb), len(mm))
    return _mix(bb[:n], mm[:n])


def _write_wav(path, buf):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(AUDIO_SR)
        w.writeframes(buf.tobytes())


def build_audio(folder):
    gens = {
        "music": _music,
        "shoot": lambda: _sweep(900, 300, 110, 0.4, "square"),
        "hit": lambda: _tone(300, 50, 0.4, "square"),
        "kill": lambda: _seq([_tone(520, 60, .4, "square"),
                              _tone(330, 110, .4, "saw")]),
        "hurt": lambda: _sweep(400, 120, 220, 0.45, "saw"),
        "wave": lambda: _seq([_tone(523, 90, .4), _tone(784, 160, .45)]),
    }
    out = {}
    for name, gen in gens.items():
        p = os.path.join(folder, name + ".wav")
        if not os.path.exists(p):
            try:
                _write_wav(p, gen())
            except Exception:
                continue
        if os.path.exists(p):
            out[name] = p
    return out


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# enemy kinds -> stats
KINDS = {
    "robot": {"hp": 3, "speed": 2.4, "hz": 1.0, "col": (0.85, 0.4, 0.35)},
    "alien": {"hp": 2, "speed": 3.2, "hz": 2.4, "col": (0.6, 0.9, 0.5)},
    "slime": {"hp": 2, "speed": 2.0, "hz": 0.6, "col": (0.5, 0.85, 0.95)},
    "target": {"hp": 1, "speed": 0.0, "hz": 1.4, "col": (0.95, 0.85, 0.3)},
}


# ---------------------------------------------------------------------------
class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.has_win = self.win is not None
        self.render.setTwoSided(True)
        self.cube = NodePath(_cube_node())
        self.sphere = NodePath(_sphere_node())
        self._setup_lights()
        if self.has_win:
            self.setBackgroundColor(0.20, 0.16, 0.28)
            self.render.setShaderAuto()
            self.disableMouse()
            self.camLens.setFov(78)   # breder gezichtsveld (minder ingezoomd)

        self.enemies = []
        self.fx = []
        self._build_arena()
        if self.has_win:
            self._build_gun()

        self.mode = LEVELS
        self.state = MENU
        self.paused = False
        self.px, self.py = 0.0, 0.0
        self.heading, self.pitch = 0.0, 0.0
        self.sens = SENS
        self.hp = 100.0
        self.score = 0
        self.level = 1
        self.wave = 1
        self.fire_t = 0.0
        self.hurt_t = 0.0
        self.msg = ""
        self.msg_t = 0.0
        self.locked = None
        self.mouse_ok = False
        self.keys = {"w": False, "s": False, "a": False, "d": False,
                     "shoot": False}

        self.volume = 0.6
        self.muted = False
        self.sounds = {}
        self.music = None
        self._init_audio()

        if self.has_win:
            self._build_gui()
            self._bind()
            self.taskMgr.add(self.update, "update")
            self._apply_state()

    # ---- scene ----
    def _setup_lights(self):
        a = AmbientLight("a")
        a.setColor(Vec4(0.55, 0.55, 0.62, 1))
        self.render.setLight(self.render.attachNewNode(a))
        d = DirectionalLight("d")
        d.setColor(Vec4(0.9, 0.88, 0.8, 1))
        dn = self.render.attachNewNode(d)
        dn.setHpr(-35, -60, 0)
        self.render.setLight(dn)

    def _box(self, parent, sx, sy, sz, col, pos=(0, 0, 0)):
        np = self.cube.copyTo(parent)
        np.setScale(sx, sy, sz)
        np.setPos(*pos)
        np.setColor(*col, 1)
        return np

    def _ball(self, parent, sc, col, pos=(0, 0, 0)):
        np = self.sphere.copyTo(parent)
        if isinstance(sc, (tuple, list)):
            np.setScale(*sc)
        else:
            np.setScale(sc)
        np.setPos(*pos)
        np.setColor(col[0], col[1], col[2], 1)
        return np

    def _build_arena(self):
        self._box(self.render, ARENA * 2 + 4, ARENA * 2 + 4, 1,
                  (0.30, 0.46, 0.34), (0, 0, -0.5))
        # tegels-accent
        for gx in range(-2, 3):
            self._box(self.render, 0.2, ARENA * 2, 0.02,
                      (0.26, 0.40, 0.30), (gx * 9, 0, 0.02))
            self._box(self.render, ARENA * 2, 0.2, 0.02,
                      (0.26, 0.40, 0.30), (0, gx * 9, 0.02))
        wcol = (0.42, 0.36, 0.52)
        for (sx, sy, x, y) in [(ARENA * 2 + 4, 1, 0, ARENA + 2),
                               (ARENA * 2 + 4, 1, 0, -ARENA - 2),
                               (1, ARENA * 2 + 4, ARENA + 2, 0),
                               (1, ARENA * 2 + 4, -ARENA - 2, 0)]:
            self._box(self.render, sx, sy, 4, wcol, (x, y, 1.5))
        # dekkingsblokken
        self.cover = []
        for (x, y) in [(8, 6), (-7, 9), (10, -8), (-9, -7), (0, 12), (-12, 0)]:
            self._box(self.render, 2.4, 2.4, 2.2, (0.5, 0.45, 0.6),
                      (x, y, 1.0))
            self.cover.append((x, y, 1.4))
        # lucht
        self._grad_quad([(-90, 70, -30), (90, 70, -30), (90, 70, 80),
                         (-90, 70, 80)],
                        [(0.5, 0.4, 0.6, 1), (0.5, 0.4, 0.6, 1),
                         (0.16, 0.13, 0.24, 1), (0.16, 0.13, 0.24, 1)])

    def _grad_quad(self, corners, colors):
        fmt = GeomVertexFormat.getV3c4()
        vd = GeomVertexData("q", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vd, "vertex")
        cw = GeomVertexWriter(vd, "color")
        for c, col in zip(corners, colors):
            vw.addData3(*c)
            cw.addData4(*col)
        t = GeomTriangles(Geom.UHStatic)
        t.addVertices(0, 1, 2)
        t.addVertices(0, 2, 3)
        g = Geom(vd)
        g.addPrimitive(t)
        nd = GeomNode("q")
        nd.addGeom(g)
        np = self.render.attachNewNode(nd)
        np.setLightOff()
        np.setShaderOff()
        np.setBin("background", 0)
        np.setDepthWrite(False)
        return np

    def _build_gun(self):
        # herkenbaar geweer met lange loop die naar voren wijst
        self.gun = self.camera.attachNewNode("gun")
        self.gun.setPos(0.32, 1.1, -0.46)
        self.gun.setScale(1.3)
        body = (0.16, 0.17, 0.21)
        steel = (0.10, 0.11, 0.14)
        self._box(self.gun, 0.18, 0.55, 0.22, body, (0, 0.05, 0))     # body
        self._box(self.gun, 0.09, 1.3, 0.09, steel, (0, 0.95, 0.05))  # loop
        self._box(self.gun, 0.10, 0.18, 0.30, body, (0, -0.18, -0.22))  # greep
        self._box(self.gun, 0.025, 0.05, 0.13, (0.3, 0.32, 0.4),
                  (0, 1.45, 0.14))                                    # korrel
        self.muzzle = self._box(self.gun, 0.13, 0.13, 0.13,
                                (1.0, 0.88, 0.3), (0, 1.6, 0.05))     # vuurflits
        self.muzzle.setLightOff()
        self.muzzle.hide()
        self.gun_rest = self.gun.getPos()

    # ---- enemies ----
    def make_enemy(self, kind, x, y):
        st = KINDS[kind]
        np = self.render.attachNewNode(kind)
        col = st["col"]
        if kind == "robot":
            self._box(np, 1.0, 0.7, 1.0, col, (0, 0, 0.65))            # romp
            self._box(np, 0.7, 0.04, 0.4, (0.95, 0.95, 0.5), (0, -0.36, 0.7))
            self._box(np, 0.22, 0.22, 0.7, col, (-0.62, 0, 0.7))       # arm L
            self._box(np, 0.22, 0.22, 0.7, col, (0.62, 0, 0.7))        # arm R
            self._box(np, 0.34, 0.5, 0.3, (0.3, 0.3, 0.34), (-0.27, 0, 0.15))
            self._box(np, 0.34, 0.5, 0.3, (0.3, 0.3, 0.34), (0.27, 0, 0.15))
            self._box(np, 0.66, 0.6, 0.5, (0.78, 0.36, 0.33), (0, 0, 1.45))
            self._box(np, 0.5, 0.05, 0.16, (0.08, 0.08, 0.12), (0, -0.31, 1.5))
            self._ball(np, 0.08, (1, 0.9, 0.3), (-0.15, -0.34, 1.5)).setLightOff()
            self._ball(np, 0.08, (1, 0.9, 0.3), (0.15, -0.34, 1.5)).setLightOff()
            self._box(np, 0.04, 0.04, 0.3, (0.3, 0.3, 0.34), (0, 0, 1.85))
            self._ball(np, 0.1, (1, 0.35, 0.3), (0, 0, 2.05)).setLightOff()
        elif kind == "alien":
            self._ball(np, (1.4, 1.4, 0.3), (0.55, 0.57, 0.64), (0, 0, 0))
            self._ball(np, (0.85, 0.85, 0.2), (0.38, 0.4, 0.46), (0, 0, -0.14))
            for ang in (0, 72, 144, 216, 288):
                rad = math.radians(ang)
                self._ball(np, 0.09, (1, 0.85, 0.4),
                           (math.cos(rad) * 0.95, math.sin(rad) * 0.95,
                            -0.12)).setLightOff()
            self._ball(np, (0.6, 0.6, 0.55), (0.8, 0.9, 1.0), (0, 0, 0.3))
            self._ball(np, 0.34, col, (0, 0, 0.42))
            self._ball(np, 0.12, (1, 1, 1), (0.13, -0.24, 0.5))
            self._ball(np, 0.06, (0.1, 0.1, 0.15), (0.15, -0.33, 0.5)).setLightOff()
            self._ball(np, 0.12, (1, 1, 1), (-0.13, -0.24, 0.5))
            self._ball(np, 0.06, (0.1, 0.1, 0.15), (-0.15, -0.33, 0.5)).setLightOff()
        elif kind == "slime":
            self._ball(np, (1.0, 1.0, 0.85), col, (0, 0, 0.55))
            self._ball(np, (0.45, 0.4, 0.3), (0.85, 0.95, 1.0), (-0.25, -0.2, 0.85))
            self._ball(np, 0.16, (1, 1, 1), (0.22, -0.45, 0.7))
            self._ball(np, 0.08, (0.1, 0.1, 0.2), (0.26, -0.55, 0.7)).setLightOff()
            self._ball(np, 0.16, (1, 1, 1), (-0.22, -0.45, 0.7))
            self._ball(np, 0.08, (0.1, 0.1, 0.2), (-0.26, -0.55, 0.7)).setLightOff()
            self._box(np, 0.3, 0.04, 0.06, (0.15, 0.1, 0.2), (0, -0.5, 0.45))
            self._ball(np, 0.13, col, (0.5, 0.18, 0.12))
        else:  # target
            self._box(np, 0.2, 0.2, 1.4, (0.5, 0.4, 0.3), (0, 0, 0.7))
            self._ball(np, (0.9, 0.18, 0.9), (0.95, 0.95, 0.95), (0, -0.05, 1.4))
            self._ball(np, (0.6, 0.2, 0.6), (0.9, 0.2, 0.2), (0, -0.1, 1.4))
            self._ball(np, (0.25, 0.22, 0.25), (0.98, 0.98, 0.98), (0, -0.14, 1.4))
        np.setScale(1.4)   # groter = beter zichtbaar
        e = {"kind": kind, "np": np, "x": float(x), "y": float(y),
             "hp": st["hp"], "speed": st["speed"], "hz": st["hz"] * 1.4,
             "atk": 0.0, "phase": random.uniform(0, 6.28)}
        self._place(e, 0.0)
        self.enemies.append(e)
        return e

    def _place(self, e, t):
        z = 0.0
        if e["kind"] == "alien":
            z = e["hz"] + 0.3 * math.sin(t * 2 + e["phase"]) - 0.5
        elif e["kind"] == "slime":
            z = abs(math.sin(t * 3 + e["phase"])) * 0.5 - 0.2
        e["np"].setPos(e["x"], e["y"], z)
        e["hitz"] = (e["hz"])

    def clear_enemies(self):
        for e in self.enemies:
            e["np"].removeNode()
        self.enemies = []

    def _ring_pos(self):
        ang = random.uniform(0, 6.28)
        r = ARENA - 2
        return math.cos(ang) * r, math.sin(ang) * r

    def spawn_level(self, lv):
        self.clear_enemies()
        n = 3 + lv
        kinds = ["robot", "alien", "slime"]
        for _ in range(n):
            x, y = self._ring_pos()
            self.make_enemy(random.choice(kinds), x, y)

    def spawn_wave(self, wv):
        self.clear_enemies()
        n = 3 + wv * 2
        kinds = ["robot", "alien", "slime"]
        for _ in range(n):
            x, y = self._ring_pos()
            k = random.choice(kinds)
            e = self.make_enemy(k, x, y)
            e["speed"] *= (1 + wv * 0.06)

    def spawn_targets(self):
        self.clear_enemies()
        for _ in range(6):
            x = random.uniform(-ARENA + 4, ARENA - 4)
            y = random.uniform(4, ARENA - 4)
            self.make_enemy("target", x, y)

    # ---- audio ----
    def _audio_dir(self):
        d = os.path.join(app_dir(), "cache")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d

    def _init_audio(self):
        threading.Thread(target=self._load_audio, daemon=True).start()

    def _load_audio(self):
        try:
            files = build_audio(self._audio_dir())
            snd = {}
            for name, path in files.items():
                if name == "music":
                    continue
                try:
                    snd[name] = self.loader.loadSfx(Filename.fromOsSpecific(path))
                except Exception:
                    pass
            mus = None
            if "music" in files:
                try:
                    mus = self.loader.loadSfx(
                        Filename.fromOsSpecific(files["music"]))
                    if mus:
                        mus.setLoop(True)
                except Exception:
                    mus = None
            self.sounds = snd
            self.music = mus
            self._apply_volume()
            if self.state == PLAY and self.music and not self.muted:
                self.music.play()
        except Exception:
            pass

    def _apply_volume(self):
        v = 0.0 if self.muted else self.volume
        for s in self.sounds.values():
            try:
                s.setVolume(v)
            except Exception:
                pass
        if self.music:
            try:
                self.music.setVolume(v * 0.45)
            except Exception:
                pass

    def sfx(self, n):
        if self.muted:
            return
        s = self.sounds.get(n)
        if s:
            try:
                s.play()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()
        if self.music:
            try:
                self.music.stop() if self.muted else (
                    self.music.play() if self.state == PLAY else None)
            except Exception:
                pass

    # ---- gui ----
    def _build_gui(self):
        self.hud = OnscreenText(text="", pos=(-1.30, 0.88), scale=0.06,
                                fg=(1, 1, 1, 1), align=TextNode.ALeft,
                                mayChange=True, shadow=(0, 0, 0, .6))
        self.hint = OnscreenText(text="", pos=(0, -0.90), scale=0.05,
                                 fg=(1, 1, 0.7, 1), align=TextNode.ACenter,
                                 mayChange=True, shadow=(0, 0, 0, .6))
        self.ch_v = DirectFrame(frameColor=(1, 1, 1, 0.9),
                                frameSize=(-0.004, 0.004, -0.03, 0.03))
        self.ch_h = DirectFrame(frameColor=(1, 1, 1, 0.9),
                                frameSize=(-0.03, 0.03, -0.004, 0.004))
        DirectButton(text=DONATE, scale=0.04, pos=(0, 0, -0.97), relief=None,
                     text_fg=(0.5, 0.8, 1, 1),
                     command=lambda: webbrowser.open(DONATE))
        self.menu = DirectFrame(frameColor=(0.08, 0.07, 0.12, 0.85),
                                frameSize=(-2, 2, -1, 1))
        OnscreenText(text="DraveShooter", parent=self.menu, pos=(0, 0.6),
                     scale=0.2, fg=(1, 0.7, 0.4, 1))
        OnscreenText(text=T("sub"), parent=self.menu, pos=(0, 0.4),
                     scale=0.07, fg=(0.9, 0.95, 1, 1))
        modes = [("m_levels", LEVELS), ("m_surv", SURVIVAL), ("m_prac", PRACTICE)]
        for i, (key, mode) in enumerate(modes):
            DirectButton(text=T(key), parent=self.menu, pos=(0, 0, 0.16 - i * 0.15),
                         scale=0.08, text_fg=(1, 1, 1, 1),
                         frameColor=(0.22, 0.24, 0.38, 1), relief="raised",
                         pad=(0.5, 0.28), command=self.start, extraArgs=[mode])
        OnscreenText(text=T("ctrl"), parent=self.menu, pos=(0, -0.35),
                     scale=0.045, fg=(0.8, 0.85, 1, 1))
        OnscreenText(text=T("aim_help"), parent=self.menu, pos=(0, -0.45),
                     scale=0.045, fg=(0.7, 0.9, 0.7, 1))
        OnscreenText(text=T("donationware") + "   " + T("info_hint"),
                     parent=self.menu, pos=(0, -0.6), scale=0.045,
                     fg=(0.8, 0.85, 1, 1))
        self.infop = DirectFrame(frameColor=(0.08, 0.07, 0.12, 0.92),
                                 frameSize=(-2, 2, -1, 1))
        OnscreenText(text=T("info_title"), parent=self.infop, pos=(0, 0.5),
                     scale=0.1, fg=(1, 0.7, 0.4, 1))
        OnscreenText(text=T("donationware"), parent=self.infop, pos=(0, 0.3),
                     scale=0.07, fg=(1, 1, 1, 1))
        OnscreenText(text=T("donate_line"), parent=self.infop, pos=(0, 0.13),
                     scale=0.05, fg=(0.8, 0.85, 1, 1))
        DirectButton(text=DONATE, parent=self.infop, scale=0.06, pos=(0, 0, -0.02),
                     relief=None, text_fg=(0.5, 0.8, 1, 1),
                     command=lambda: webbrowser.open(DONATE))
        OnscreenText(text=T("contact") + ":  " + CONTACT, parent=self.infop,
                     pos=(0, -0.22), scale=0.05, fg=(0.8, 0.85, 1, 1))
        OnscreenText(text=T("back"), parent=self.infop, pos=(0, -0.45),
                     scale=0.05, fg=(1, 0.8, 0.4, 1))

    def _apply_state(self):
        if not self.has_win:
            return
        self.menu.hide()
        self.infop.hide()
        self.ch_v.hide()
        self.ch_h.hide()
        if self.state == MENU:
            self.menu.show()
            self._release_mouse()
        elif self.state == INFO:
            self.infop.show()
            self._release_mouse()
        elif self.state == PLAY:
            self.ch_v.show()
            self.ch_h.show()

    # ---- input ----
    def _bind(self):
        b = {"w": "w", "arrow_up": "w", "s": "s", "arrow_down": "s",
             "a": "a", "arrow_left": "a", "d": "d", "arrow_right": "d"}
        for k, slot in b.items():
            self.accept(k, self._key, [slot, True])
            self.accept(k + "-up", self._key, [slot, False])
        self.accept("space", self._key, ["shoot", True])
        self.accept("space-up", self._key, ["shoot", False])
        self.accept("mouse1", self._key, ["shoot", True])
        self.accept("mouse1-up", self._key, ["shoot", False])
        self.accept("1", self.start, [LEVELS])
        self.accept("2", self.start, [SURVIVAL])
        self.accept("3", self.start, [PRACTICE])
        self.accept("p", self.toggle_pause)
        self.accept("i", self.toggle_info)
        self.accept("m", self.toggle_mute)
        self.accept("r", self.to_menu)
        self.accept("[", self.adj_sens, [-0.03])
        self.accept("]", self.adj_sens, [0.03])
        self.accept("escape", self.on_escape)

    def _key(self, slot, val):
        self.keys[slot] = val

    def adj_sens(self, d):
        self.sens = max(0.05, min(0.4, self.sens + d))
        self.flash("Muis %d%%" % int(self.sens / SENS * 100))

    def on_escape(self):
        if self.state == PLAY:
            self.to_menu()
        else:
            self.userExit()

    def start(self, mode):
        if self.state not in (MENU,):
            return
        self.mode = mode
        self.state = PLAY
        self.hp = 100.0
        self.score = 0
        self.level = 1
        self.wave = 1
        self.px, self.py = 0.0, 0.0
        self.heading = 0.0
        self.pitch = 0.0
        if mode == LEVELS:
            self.spawn_level(self.level)
        elif mode == SURVIVAL:
            self.spawn_wave(self.wave)
        else:
            self.spawn_targets()
        self._apply_state()
        self._grab_mouse()
        if self.music and not self.muted:
            try:
                self.music.play()
            except Exception:
                pass

    def to_menu(self):
        self.state = MENU
        self.clear_enemies()
        self._apply_state()

    def toggle_pause(self):
        if self.state == PLAY:
            self.paused = not self.paused
            if self.paused:
                self._release_mouse()
            else:
                self._grab_mouse()

    def toggle_info(self):
        if self.state == INFO:
            self.state = self._prev
        else:
            self._prev = self.state
            self.state = INFO
        self._apply_state()

    def flash(self, t):
        self.msg = t
        self.msg_t = 1.6

    # ---- mouse ----
    def _grab_mouse(self):
        if not self.has_win or not hasattr(self.win, "requestProperties"):
            return
        p = WindowProperties()
        p.setCursorHidden(True)
        p.setMouseMode(WindowProperties.M_confined)
        self.win.requestProperties(p)
        self.mouse_ok = False

    def _release_mouse(self):
        if not self.has_win or not hasattr(self.win, "requestProperties"):
            return
        p = WindowProperties()
        p.setCursorHidden(False)
        p.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(p)
        self.mouse_ok = False

    def _mouselook(self):
        if not self.win.hasPointer(0):
            return
        md = self.win.getPointer(0)
        x, y = md.getX(), md.getY()
        cx = self.win.getXSize() // 2
        cy = self.win.getYSize() // 2
        if self.mouse_ok:
            self.heading -= (x - cx) * self.sens
            self.pitch -= (y - cy) * self.sens
            self.pitch = max(-70, min(70, self.pitch))
        if self.win.movePointer(0, cx, cy):
            self.mouse_ok = True

    # ---- combat ----
    def _forward(self):
        h = math.radians(self.heading)
        p = math.radians(self.pitch)
        return Vec3(-math.sin(h) * math.cos(p),
                    math.cos(h) * math.cos(p), math.sin(p))

    @staticmethod
    def _approach_angle(cur, target, maxstep):
        diff = (target - cur + 180) % 360 - 180
        if diff > maxstep:
            diff = maxstep
        elif diff < -maxstep:
            diff = -maxstep
        return cur + diff

    def _auto_aim(self, dt):
        # draai het vizier soepel naar de dichtstbijzijnde vijand
        best = None
        bd = 1e18
        for e in self.enemies:
            d = (e["x"] - self.px) ** 2 + (e["y"] - self.py) ** 2
            if d < bd:
                bd = d
                best = e
        if not best:
            return
        dx = best["x"] - self.px
        dy = best["y"] - self.py
        dist = math.hypot(dx, dy) or 1.0
        des_h = math.degrees(math.atan2(-dx, dy))
        des_p = math.degrees(math.atan2(best["hitz"] - EYE, dist))
        turn = 260 * dt
        self.heading = self._approach_angle(self.heading, des_h, turn)
        dp = des_p - self.pitch
        self.pitch += max(-turn, min(turn, dp))

    def aim_target(self):
        cam = Vec3(self.px, self.py, EYE)
        fwd = self._forward()
        best = None
        bestang = AIM_CONE
        for e in self.enemies:
            d = Vec3(e["x"] - cam.x, e["y"] - cam.y, e["hitz"] - cam.z)
            dist = d.length()
            if dist < 0.1 or dist > RANGE:
                continue
            dn = d / dist
            dot = max(-1.0, min(1.0, fwd.dot(dn)))
            ang = math.acos(dot)
            if ang < bestang:
                bestang = ang
                best = e
        return best

    def fire(self):
        self.fire_t = FIRE_CD
        self.sfx("shoot")
        if self.has_win:
            self.muzzle.show()
            self._muz_t = 0.05
            self.gun.setY(self.gun_rest.y - 0.18)
        t = self.aim_target()
        if t:
            t["hp"] -= 1
            self.sfx("hit")
            self._spark(t["x"], t["y"], t["hitz"])
            if t["hp"] <= 0:
                self._kill(t)
            return True
        return False

    def _kill(self, e):
        self.score += {"robot": 30, "alien": 25, "slime": 20,
                       "target": 15}[e["kind"]]
        self.sfx("kill")
        self._spark(e["x"], e["y"], e["hitz"], big=True)
        e["np"].removeNode()
        self.enemies.remove(e)
        if self.mode == PRACTICE:
            x = random.uniform(-ARENA + 4, ARENA - 4)
            y = random.uniform(4, ARENA - 4)
            self.make_enemy("target", x, y)

    def _spark(self, x, y, z, big=False):
        if not self.has_win:
            return
        s = self._ball(self.render, 0.5 if big else 0.3, (1, 0.85, 0.3),
                       (x, y, z))
        s.setLightOff()
        self.fx.append({"np": s, "t": 0.18})

    # ---- update ----
    def update(self, task):
        try:
            return self._update_inner(task)
        except Exception:
            self._log_error()
            return task.cont

    def _log_error(self):
        import traceback
        try:
            d = os.path.join(app_dir(), "cache")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "error.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc() + "\n")
        except Exception:
            pass

    def _update_inner(self, task):
        dt = globalClock.getDt()
        if dt > 0.05:
            dt = 0.05
        if self.state == PLAY and not self.paused:
            self._mouselook()
            self._step(dt)
        self._update_fx(dt)
        if self.has_win:
            self.camera.setPos(self.px, self.py, EYE)
            self.camera.setHpr(self.heading, self.pitch, 0)
        if self.msg_t > 0:
            self.msg_t -= dt
        self._hud()
        return task.cont

    def _step(self, dt):
        # jij richt zelf met de muis (zie _mouselook); hier rest van de logica
        # schieten
        if self.fire_t > 0:
            self.fire_t -= dt
        if self.keys["shoot"] and self.fire_t <= 0:
            self.fire()
        if getattr(self, "_muz_t", 0) > 0:
            self._muz_t -= dt
            if self._muz_t <= 0 and self.has_win:
                self.muzzle.hide()
                self.gun.setY(self.gun_rest.y)
        # vijanden
        self.hurt_t += dt
        t = task = globalClock.getFrameTime()
        for e in list(self.enemies):
            if e["kind"] != "target":
                d = Vec3(self.px - e["x"], self.py - e["y"], 0)
                dist = d.length()
                stop = 4.0 if e["kind"] == "alien" else 2.8
                if dist > stop:
                    d.normalize()
                    e["x"] += d.x * e["speed"] * dt
                    e["y"] += d.y * e["speed"] * dt
                e["atk"] -= dt
                if dist < stop + 0.8 and e["atk"] <= 0:
                    e["atk"] = 1.2
                    self.hp -= 8
                    self.hurt_t = 0.0
                    self.sfx("hurt")
            self._place(e, t)
        # leven-regen (vergevingsgezind)
        if self.hurt_t > 2.5 and self.hp < 100:
            self.hp = min(100, self.hp + 6 * dt)
        if self.hp <= 0:
            self.hp = 0
            self.state = OVER
            self._release_mouse()
            if self.music:
                try:
                    self.music.stop()
                except Exception:
                    pass
            return
        # lock-indicator
        self.locked = self.aim_target()
        # modus-voortgang
        if not self.enemies and self.mode != PRACTICE:
            self._cleared()

    def _cleared(self):
        if self.mode == LEVELS:
            if self.level >= 5:
                self.state = WIN
                self._release_mouse()
                return
            self.level += 1
            self.flash(T("level_done"))
            self.sfx("wave")
            self.spawn_level(self.level)
        else:
            self.wave += 1
            self.score += 50
            self.flash(T("wave_done"))
            self.sfx("wave")
            self.spawn_wave(self.wave)

    def _update_fx(self, dt):
        for f in list(self.fx):
            f["t"] -= dt
            if f["t"] <= 0:
                f["np"].removeNode()
                self.fx.remove(f)

    def _hud(self):
        if not self.has_win:
            return
        if self.state == PLAY:
            line = "%s: %d    %s: %d" % (T("health"), int(self.hp),
                                        T("score"), self.score)
            if self.mode == LEVELS:
                line += "    %s: %d/5    %s: %d" % (T("level"), self.level,
                                                   T("left"), len(self.enemies))
            elif self.mode == SURVIVAL:
                line += "    %s: %d    %s: %d" % (T("wave"), self.wave,
                                                 T("left"), len(self.enemies))
            self.hud.setText(line + ("  (%s)" % T("sound_off") if self.muted
                                     else ""))
            if self.msg_t > 0:
                self.hint.setText(self.msg)
            elif self.paused:
                self.hint.setText(T("paused"))
            elif self.mode == PRACTICE:
                self.hint.setText(T("practice"))
            else:
                self.hint.setText("")
            lock = self.locked is not None
            c = (1, 0.3, 0.3, 0.95) if lock else (1, 1, 1, 0.9)
            self.ch_v["frameColor"] = c
            self.ch_h["frameColor"] = c
        elif self.state == OVER:
            self.hud.setText("%s: %d" % (T("score"), self.score))
            self.hint.setText(T("over_title") + " - " + T("restart"))
        elif self.state == WIN:
            self.hud.setText("%s: %d" % (T("score"), self.score))
            self.hint.setText(T("win_title") + " - " + T("restart"))
        else:
            self.hud.setText("")
            self.hint.setText(T("menu_hint"))


if __name__ == "__main__":
    Game().run()

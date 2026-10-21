# -*- coding: utf-8 -*-
"""DraveClaw - a 3D claw machine (Panda3D + Bullet physics).

Move the claw over the prize pile, drop it, and try to grab a prize and
deliver it to the chute. Language follows the PC (Dutch/English). Donationware.

Speel/Play:
  - Arrow keys: move the claw (left/right/forward/back)
  - Space: drop the claw and try to grab
  - P pause   I info/donate   M sound   - / + volume   Esc quit
"""
import array
import locale
import math
import os
import sys
import threading
import wave
import webbrowser

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-title DraveClaw")
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
                          GeomTriangles, CardMaker, TransparencyAttrib,
                          TransformState, Filename)
from panda3d.bullet import (BulletWorld, BulletRigidBodyNode, BulletBoxShape,
                            BulletPlaneShape, BulletSphereShape)

import random

globalClock = ClockObject.getGlobalClock()


# ---------------------------------------------------------------------------
# taal volgt de pc / language follows the PC
# ---------------------------------------------------------------------------
def _detect_lang():
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _detect_lang()

TXT = {
    "title": {"nl": "DraveClaw", "en": "DraveClaw"},
    "sub": {"nl": "De grijpautomaat", "en": "The claw machine"},
    "start": {"nl": "Druk op SPATIE om te spelen", "en": "Press SPACE to play"},
    "ctrl": {"nl": "Pijltjes = klauw bewegen    Spatie = grijpen",
             "en": "Arrows = move claw    Space = grab"},
    "credits": {"nl": "Beurten", "en": "Credits"},
    "prizes": {"nl": "Prijzen", "en": "Prizes"},
    "aim": {"nl": "Mik met de pijltjes, druk SPATIE om te grijpen",
            "en": "Aim with the arrows, press SPACE to grab"},
    "grabbing": {"nl": "Grijpen...", "en": "Grabbing..."},
    "win_prize": {"nl": "Gewonnen! Prijs in de koker!",
                  "en": "Win! Prize in the chute!"},
    "missed": {"nl": "Net mis... probeer opnieuw", "en": "So close... try again"},
    "got_it": {"nl": "Hebbes! Breng naar de koker", "en": "Got it! Bring it to the chute"},
    "no_credits": {"nl": "Geen beurten meer!", "en": "Out of credits!"},
    "gameover": {"nl": "Einde - druk op R om opnieuw te spelen",
                 "en": "Game over - press R to play again"},
    "paused": {"nl": "GEPAUZEERD  (P = verder)", "en": "PAUSED  (P = resume)"},
    "sound_off": {"nl": "Geluid uit", "en": "Sound off"},
    "info_hint": {"nl": "I = info / donatie", "en": "I = info / donate"},
    "info_title": {"nl": "Over DraveClaw", "en": "About DraveClaw"},
    "donationware": {"nl": "Donationware - gratis te spelen.",
                     "en": "Donationware - free to play."},
    "donate_line": {"nl": "Bevalt het? Een donatie wordt gewaardeerd:",
                    "en": "Enjoying it? A donation is appreciated:"},
    "contact": {"nl": "Contact", "en": "Contact"},
    "back": {"nl": "Druk op I om terug te gaan", "en": "Press I to go back"},
}


def T(key):
    d = TXT.get(key, {})
    return d.get(LANG) or d.get("en") or key


DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

# playfield
BX, BY = 3.4, 3.4            # interior half-extent
TOPZ = 8.5                   # claw rest height
GRABZ = 1.4                  # claw lowest height
HOMEX, HOMEY = -2.7, -2.7    # chute corner
GRIP_RADIUS = 1.05
BASE_GRIP = 0.72
N_PRIZES = 26
HOLE_X1 = -1.9               # binnenrand van het chute-gat (hoek links-voor)
HOLE_Y1 = -1.9

MENU, PLAY, OVER, INFO = "menu", "play", "over", "info"


# ---------------------------------------------------------------------------
# geometry helper: a flat-coloured unit cube
# ---------------------------------------------------------------------------
def _cube_node():
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cube", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    faces = [
        ((1, 0, 0), [(.5, -.5, -.5), (.5, .5, -.5), (.5, .5, .5), (.5, -.5, .5)]),
        ((-1, 0, 0), [(-.5, .5, -.5), (-.5, -.5, -.5), (-.5, -.5, .5), (-.5, .5, .5)]),
        ((0, 1, 0), [(.5, .5, -.5), (-.5, .5, -.5), (-.5, .5, .5), (.5, .5, .5)]),
        ((0, -1, 0), [(-.5, -.5, -.5), (.5, -.5, -.5), (.5, -.5, .5), (-.5, -.5, .5)]),
        ((0, 0, 1), [(-.5, -.5, .5), (.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5)]),
        ((0, 0, -1), [(-.5, .5, -.5), (.5, .5, -.5), (.5, -.5, -.5), (-.5, -.5, -.5)]),
    ]
    tris = GeomTriangles(Geom.UHStatic)
    i = 0
    for n, verts in faces:
        for v in verts:
            vw.addData3(*v)
            nw.addData3(*n)
        tris.addVertices(i, i + 1, i + 2)
        tris.addVertices(i, i + 2, i + 3)
        i += 4
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("cube")
    node.addGeom(geom)
    return node


def _sphere_node(slices=16, stacks=12):
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("sphere", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    for i in range(stacks + 1):
        lat = math.pi * (i / stacks) - math.pi / 2
        for j in range(slices + 1):
            lon = 2 * math.pi * (j / slices)
            x = math.cos(lat) * math.cos(lon)
            y = math.cos(lat) * math.sin(lon)
            z = math.sin(lat)
            vw.addData3(x, y, z)
            nw.addData3(x, y, z)
    tris = GeomTriangles(Geom.UHStatic)
    row = slices + 1
    for i in range(stacks):
        for j in range(slices):
            a = i * row + j
            tris.addVertices(a, a + row, a + 1)
            tris.addVertices(a + 1, a + row, a + row + 1)
    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode("sphere")
    node.addGeom(geom)
    return node


# ---------------------------------------------------------------------------
# procedural audio -> WAV files (loaded by Panda3D)
# ---------------------------------------------------------------------------
AUDIO_SR = 22050


def _tone(freq, ms, vol=0.5, wave_t="sine"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    buf = array.array("h", bytes(2 * n))
    atk = max(1, int(0.008 * AUDIO_SR))
    rel = max(1, int(0.06 * AUDIO_SR))
    ph = 0.0
    step = freq / AUDIO_SR
    for i in range(n):
        ph += step
        x = ph - math.floor(ph)
        if wave_t == "square":
            s = 1.0 if x < 0.5 else -1.0
        elif wave_t == "tri":
            s = 4 * abs(x - 0.5) - 1
        elif wave_t == "saw":
            s = 2 * x - 1
        elif wave_t == "noise":
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


def _sweep(f0, f1, ms, vol=0.5, wave_t="saw"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    buf = array.array("h", bytes(2 * n))
    rel = max(1, int(0.05 * AUDIO_SR))
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        ph += f / AUDIO_SR
        x = ph - math.floor(ph)
        if wave_t == "square":
            s = 1.0 if x < 0.5 else -1.0
        elif wave_t == "noise":
            s = random.uniform(-1, 1)
        else:
            s = 2 * x - 1
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


def _music_buf():
    bpm = 108
    beat = 60000 / bpm / 2.0
    scale = [262, 294, 330, 349, 392, 440, 494, 523]
    bass = [131, 131, 147, 147, 165, 147, 131, 98,
            131, 131, 147, 147, 165, 175, 196, 175]
    mel = [4, 2, 0, 2, 4, 4, 4, 2, 2, 2, 4, 7, 7, 5, 4, 2]
    bb = array.array("h")
    mm = array.array("h")
    for k in range(16):
        bb += _tone(bass[k], beat, 0.30, "tri")
        mm += _tone(scale[mel[k] % len(scale)], beat, 0.18, "square")
    n = min(len(bb), len(mm))
    return _mix(bb[:n], mm[:n])


def _write_wav(path, buf):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(AUDIO_SR)
        w.writeframes(buf.tobytes())


def build_audio_files(folder):
    # luie generators: alleen aanmaken als het bestand nog niet bestaat (hergebruik)
    gens = {
        "music": _music_buf,
        "move": lambda: _tone(330, 60, 0.25, "square"),
        "drop": lambda: _sweep(700, 200, 360, 0.4, "saw"),
        "close": lambda: _seq([_tone(200, 60, 0.4, "square"),
                               _tone(150, 90, 0.4, "square")]),
        "win": lambda: _seq([_tone(523, 110, .4), _tone(659, 110, .4),
                             _tone(784, 110, .4), _tone(1047, 240, .45)]),
        "miss": lambda: _sweep(400, 120, 300, 0.4, "saw"),
        "lift": lambda: _sweep(200, 500, 300, 0.3, "square"),
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


# ---------------------------------------------------------------------------
class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.has_win = self.win is not None
        self.render.setTwoSided(True)
        self._setup_lights()
        if self.has_win:
            self.setBackgroundColor(0.07, 0.06, 0.14)
            self.render.setShaderAuto()
            self.disableMouse()
            self.camera.setPos(0, -17, 9.5)
            self.camera.lookAt(0, 0, 3.2)

        # physics
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -16))
        self.cube_tmpl = NodePath(_cube_node())
        self.sphere_tmpl = NodePath(_sphere_node())

        self.grip = 0.0
        self._build_cabinet()
        self.prizes = []
        self._build_prizes()
        self._build_claw()
        self._settle()
        if self.has_win:
            self._build_room()

        # state
        self.state = MENU
        self.paused = False
        self.credits = 12
        self.won = 0
        self.phase = "idle"
        self.grip = 0.0
        self.held = None
        self.msg = ""
        self.msg_t = 0.0
        self.base_grip = BASE_GRIP
        self.keymap = {"l": False, "r": False, "f": False, "b": False}

        # audio
        self.volume = 0.6
        self.muted = False
        self.sounds = {}
        self.music = None
        self._init_audio()

        if self.has_win:
            self._build_gui()
            self._bind_keys()
            self.taskMgr.add(self.update, "update")
            self._apply_state()

    # ---- scene ----
    def _setup_lights(self):
        amb = AmbientLight("amb")
        amb.setColor(Vec4(0.52, 0.52, 0.60, 1))
        self.render.setLight(self.render.attachNewNode(amb))
        key = DirectionalLight("key")
        key.setColor(Vec4(0.95, 0.92, 0.82, 1))
        knp = self.render.attachNewNode(key)
        knp.setHpr(-35, -55, 0)
        self.render.setLight(knp)
        fill = DirectionalLight("fill")
        fill.setColor(Vec4(0.35, 0.40, 0.55, 1))
        fnp = self.render.attachNewNode(fill)
        fnp.setHpr(150, -25, 0)
        self.render.setLight(fnp)

    def _box(self, parent, sx, sy, sz, color, pos=(0, 0, 0)):
        np = self.cube_tmpl.copyTo(parent)
        np.setScale(sx, sy, sz)
        np.setPos(*pos)
        np.setColor(*color)
        return np

    def _build_cabinet(self):
        # vloer MET een gat in de hoek (links-voor) + schacht + opvangbak eronder
        # gat = x[-BX..HOLE_X1] x y[-BY..HOLE_Y1]  (1.5 x 1.5, midden op -2.65,-2.65)
        struct = BulletRigidBodyNode("struct")

        def add_col(hx, hy, hz, cx, cy, cz):
            struct.addShape(BulletBoxShape(Vec3(hx, hy, hz)),
                            TransformState.makePos(Point3(cx, cy, cz)))

        floor_c = (0.20, 0.22, 0.30)
        # vloerdeel A: achter het gat (y van -1.9 tot 3.4), volledige breedte
        add_col(3.4, 2.65, 0.15, 0.0, 0.75, -0.15)
        self._box(self.render, 6.8, 5.3, 0.3, floor_c, (0.0, 0.75, -0.15))
        # vloerdeel B: rechts van het gat (x van -1.9 tot 3.4, y van -3.4 tot -1.9)
        add_col(2.65, 0.75, 0.15, 0.75, -2.65, -0.15)
        self._box(self.render, 5.3, 1.5, 0.3, floor_c, (0.75, -2.65, -0.15))
        # schachtwanden (binnenste twee zijden van het gat)
        add_col(0.05, 0.75, 1.1, -1.9, -2.65, -1.1)
        self._box(self.render, 0.1, 1.5, 2.2, (0.16, 0.17, 0.24), (-1.9, -2.65, -1.1))
        add_col(0.75, 0.05, 1.1, -2.65, -1.9, -1.1)
        self._box(self.render, 1.5, 0.1, 2.2, (0.16, 0.17, 0.24), (-2.65, -1.9, -1.1))
        # bodem van de opvangbak (toy valt hier zichtbaar in)
        add_col(0.75, 0.75, 0.15, -2.65, -2.65, -2.35)
        self._box(self.render, 1.5, 1.5, 0.3, (0.20, 0.55, 0.50), (-2.65, -2.65, -2.35))
        self.render.attachNewNode(struct)
        self.world.attachRigidBody(struct)
        # donkere rand rond het gat (zodat het als een gat leest)
        self._box(self.render, 1.6, 0.09, 0.12, (0.05, 0.06, 0.09), (-2.65, -1.9, 0.02))
        self._box(self.render, 0.09, 1.6, 0.12, (0.05, 0.06, 0.09), (-1.9, -2.65, 0.02))
        # invisible physics walls (inward-facing planes contain the prizes)
        walls = BulletRigidBodyNode("walls")
        walls.addShape(BulletPlaneShape(Vec3(-1, 0, 0), -BX))   # x <= BX
        walls.addShape(BulletPlaneShape(Vec3(1, 0, 0), -BX))    # x >= -BX
        walls.addShape(BulletPlaneShape(Vec3(0, -1, 0), -BY))   # y <= BY
        walls.addShape(BulletPlaneShape(Vec3(0, 1, 0), -BY))    # y >= -BY
        self.render.attachNewNode(walls)
        self.world.attachRigidBody(walls)
        # glass walls (visual, transparent)
        glass = (0.6, 0.8, 0.95, 0.12)
        h = TOPZ + 1.5
        for (sx, sy, x, y) in [(0.08, BY * 2, BX, 0), (0.08, BY * 2, -BX, 0),
                               (BX * 2, 0.08, 0, BY), (BX * 2, 0.08, 0, -BY)]:
            w = self._box(self.render, sx, sy, h, glass, (x, y, h / 2 - 0.3))
            w.setTransparency(TransparencyAttrib.MAlpha)
        # frame edges (dark posts)
        for x in (BX, -BX):
            for y in (BY, -BY):
                self._box(self.render, 0.16, 0.16, h, (0.12, 0.13, 0.18),
                          (x, y, h / 2 - 0.3))

    def _sphere(self, parent, scale, col, pos=(0, 0, 0)):
        np = self.sphere_tmpl.copyTo(parent)
        if isinstance(scale, (tuple, list)):
            np.setScale(*scale)
        else:
            np.setScale(scale)
        np.setPos(*pos)
        np.setColor(col[0], col[1], col[2], 1)
        return np

    def _teddy(self, root, c):
        acc = tuple(min(1.0, x * 1.25 + 0.16) for x in c)
        dark = (0.10, 0.08, 0.08)
        self._sphere(root, (0.40, 0.36, 0.40), c, (0, 0, 0))          # body
        self._sphere(root, (0.27, 0.20, 0.27), acc, (0, -0.16, -0.02))  # belly
        self._sphere(root, 0.28, c, (0, -0.04, 0.46))                 # head
        self._sphere(root, 0.12, c, (-0.20, 0, 0.64))
        self._sphere(root, 0.12, c, (0.20, 0, 0.64))                  # ears
        self._sphere(root, 0.06, acc, (-0.20, -0.07, 0.64))
        self._sphere(root, 0.06, acc, (0.20, -0.07, 0.64))           # inner ears
        self._sphere(root, 0.13, acc, (0, -0.26, 0.40))              # muzzle
        self._sphere(root, 0.045, dark, (-0.10, -0.24, 0.52))
        self._sphere(root, 0.045, dark, (0.10, -0.24, 0.52))        # eyes
        self._sphere(root, 0.05, dark, (0, -0.34, 0.42))            # nose
        self._sphere(root, 0.15, c, (-0.42, 0, 0.04))
        self._sphere(root, 0.15, c, (0.42, 0, 0.04))                # arms
        self._sphere(root, 0.17, c, (-0.20, 0, -0.40))
        self._sphere(root, 0.17, c, (0.20, 0, -0.40))               # legs
        self._sphere(root, 0.10, acc, (-0.20, -0.12, -0.50))
        self._sphere(root, 0.10, acc, (0.20, -0.12, -0.50))         # feet

    def _bunny(self, root, c):
        acc = tuple(min(1.0, x * 1.2 + 0.20) for x in c)
        pink = (0.96, 0.70, 0.78)
        dark = (0.10, 0.08, 0.08)
        self._sphere(root, (0.34, 0.32, 0.42), c, (0, 0, 0))         # body
        self._sphere(root, (0.24, 0.18, 0.24), acc, (0, -0.16, 0.0))  # belly
        self._sphere(root, 0.26, c, (0, -0.04, 0.48))                # head
        self._sphere(root, (0.10, 0.10, 0.30), c, (-0.13, 0, 0.86))
        self._sphere(root, (0.10, 0.10, 0.30), c, (0.13, 0, 0.86))   # tall ears
        self._sphere(root, (0.05, 0.05, 0.22), pink, (-0.13, -0.07, 0.86))
        self._sphere(root, (0.05, 0.05, 0.22), pink, (0.13, -0.07, 0.86))
        self._sphere(root, 0.045, dark, (-0.10, -0.22, 0.54))
        self._sphere(root, 0.045, dark, (0.10, -0.22, 0.54))        # eyes
        self._sphere(root, 0.04, pink, (0, -0.30, 0.46))            # nose
        self._sphere(root, 0.13, c, (-0.34, 0, -0.02))
        self._sphere(root, 0.13, c, (0.34, 0, -0.02))               # arms
        self._sphere(root, 0.16, c, (-0.18, 0, -0.42))
        self._sphere(root, 0.16, c, (0.18, 0, -0.42))               # legs
        self._sphere(root, 0.12, acc, (0, 0.30, -0.30))             # tail

    def _ball(self, root, c):
        self._sphere(root, 0.5, c, (0, 0, 0))
        self._sphere(root, (0.515, 0.515, 0.12), (0.98, 0.98, 0.98), (0, 0, 0))

    def _make_toy(self, parent, kind, col, s):
        root = parent.attachNewNode("toy")
        if kind == "teddy":
            self._teddy(root, col)
        elif kind == "bunny":
            self._bunny(root, col)
        else:
            self._ball(root, col)
        root.setScale(s)
        return root

    def _build_prizes(self):
        kinds = ["teddy", "bunny", "ball", "teddy", "ball", "teddy"]
        palette = [(0.92, 0.36, 0.42), (0.36, 0.66, 0.95), (0.45, 0.82, 0.50),
                   (0.97, 0.78, 0.32), (0.78, 0.50, 0.92), (0.97, 0.60, 0.36),
                   (0.95, 0.55, 0.70), (0.40, 0.80, 0.78)]
        for i in range(N_PRIZES):
            s = random.uniform(0.62, 0.85)
            kind = random.choice(kinds)
            col = palette[i % len(palette)]
            node = BulletRigidBodyNode("prize%d" % i)
            node.setMass(0.35)
            node.setFriction(0.9)
            node.addShape(BulletSphereShape(s * 0.5))
            np = self.render.attachNewNode(node)
            # spawn niet boven het chute-gat (anders vallen ze er meteen in)
            while True:
                px = random.uniform(-BX + 1, BX - 1)
                py = random.uniform(-BY + 1, BY - 1)
                if not (px < HOLE_X1 + 0.4 and py < HOLE_Y1 + 0.4):
                    break
            np.setPos(px, py, 1.2 + i * 0.45)
            np.setHpr(random.uniform(0, 360), 0, 0)
            vis = self._make_toy(np, kind, col, s)
            self.world.attachRigidBody(node)
            self.prizes.append({"node": node, "np": np, "vis": vis,
                                "held": False, "won": False, "size": s})

    def _grad_quad(self, corners, colors):
        fmt = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData("q", fmt, Geom.UHStatic)
        vw = GeomVertexWriter(vdata, "vertex")
        cw = GeomVertexWriter(vdata, "color")
        for c, col in zip(corners, colors):
            vw.addData3(*c)
            cw.addData4(*col)
        tris = GeomTriangles(Geom.UHStatic)
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode("grad")
        node.addGeom(geom)
        np = self.render.attachNewNode(node)
        np.setLightOff()
        np.setShaderOff()
        np.setTwoSided(True)
        return np

    def _build_room(self):
        # gradient backdrop behind the machine
        self._grad_quad(
            [(-36, 15, -14), (36, 15, -14), (36, 15, 34), (-36, 15, 34)],
            [(0.34, 0.16, 0.40, 1), (0.20, 0.12, 0.44, 1),
             (0.05, 0.05, 0.14, 1), (0.05, 0.05, 0.14, 1)])
        # carpet floor extending outward
        self._grad_quad(
            [(-36, -22, -0.31), (36, -22, -0.31), (36, 22, -0.31), (-36, 22, -0.31)],
            [(0.20, 0.10, 0.15, 1)] * 4)
        # neon corner posts + top sign (bright, unlit)
        for x in (BX, -BX):
            for y in (BY, -BY):
                n = self._box(self.render, 0.07, 0.07, TOPZ + 1.8,
                              (0.30, 0.85, 1.0), (x, y, (TOPZ + 1.8) / 2 - 0.3))
                n.setLightOff()
                n.setShaderOff()
        sign = self._box(self.render, BX * 2 + 0.5, 0.35, 1.0,
                         (0.98, 0.30, 0.48), (0, 0, TOPZ + 1.7))
        sign.setLightOff()
        sign.setShaderOff()

    def _build_claw(self):
        # kinematic palm
        node = BulletRigidBodyNode("claw")
        node.setMass(0.0)
        node.setKinematic(True)
        node.addShape(BulletBoxShape(Vec3(0.45, 0.45, 0.18)))
        self.claw_np = self.render.attachNewNode(node)
        self.claw_np.setPos(0, 0, TOPZ)
        self.world.attachRigidBody(node)
        self.claw_body = node
        metal = (0.80, 0.82, 0.88)
        metal2 = (0.62, 0.64, 0.72)
        dark = (0.40, 0.42, 0.50)
        # kabel omhoog + bolle metalen kop (hub)
        self._box(self.claw_np, 0.14, 0.14, 2.6, metal2, (0, 0, 1.5))
        self._sphere(self.claw_np, 0.16, metal2, (0, 0, 0.22))       # kabel-knop
        self._sphere(self.claw_np, (0.46, 0.46, 0.34), metal, (0, 0, 0))  # hub
        self._sphere(self.claw_np, (0.30, 0.30, 0.14), metal2, (0, 0, -0.16))  # onderkant hub
        # drie gebogen grijp-tanden
        self.fingers = []
        for k in range(3):
            piv = self.claw_np.attachNewNode("fpiv%d" % k)
            piv.setH(k * 120)
            piv.setPos(0, 0, -0.12)
            # lange bovenarm (omlaag, iets naar buiten)
            self._box(piv, 0.11, 0.11, 1.0, metal, (0, 0.16, -0.45))
            # knokkel
            self._sphere(piv, 0.13, metal2, (0, 0.20, -0.92))
            # talon-punt die naar BINNEN haakt
            tip = piv.attachNewNode("tip")
            tip.setPos(0, 0.20, -0.92)
            tip.setP(-60)
            self._box(tip, 0.10, 0.10, 0.46, dark, (0, 0, -0.20))
            self._sphere(tip, 0.08, dark, (0, 0, -0.44))             # puntje
            self.fingers.append(piv)
        self.claw_x = 0.0
        self.claw_y = 0.0
        self.claw_z = TOPZ
        self._update_fingers()

    def _update_fingers(self):
        # grip 0 = open (mild gespreid, omlaag), 1 = dicht (tanden samen)
        pitch = -12 + self.grip * 27
        for piv in self.fingers:
            piv.setP(pitch)

    def _settle(self):
        for _ in range(260):
            self.world.doPhysics(1 / 60.0, 4, 1 / 120.0)

    # ---- audio ----
    def _audio_dir(self):
        # portable: alles in een 'cache'-map in de app-map zelf (geen Temp/AppData)
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(base, "cache")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d

    def _init_audio(self):
        threading.Thread(target=self._load_audio, daemon=True).start()

    def _load_audio(self):
        try:
            folder = self._audio_dir()
            files = build_audio_files(folder)
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
                self.music.setVolume(v * 0.5)
            except Exception:
                pass

    def play_sfx(self, name):
        if self.muted:
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
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
        if self.music:
            try:
                if self.muted:
                    self.music.stop()
                elif self.state == PLAY:
                    self.music.play()
            except Exception:
                pass

    # ---- GUI ----
    def _build_gui(self):
        self.hud = OnscreenText(text="", pos=(-1.30, 0.86), scale=0.06,
                                fg=(1, 1, 1, 1), align=TextNode.ALeft,
                                mayChange=True)
        self.hint = OnscreenText(text="", pos=(0, -0.86), scale=0.055,
                                 fg=(1, 0.9, 0.5, 1), align=TextNode.ACenter,
                                 mayChange=True)
        # persistent clickable donation link
        self.donate_btn = DirectButton(
            text=DONATE, scale=0.045, pos=(0, 0, -0.95),
            relief=None, text_fg=(0.4, 0.7, 1, 1),
            command=lambda: webbrowser.open(DONATE))
        # menu overlay
        self.menu = DirectFrame(frameColor=(0.05, 0.06, 0.10, 0.82),
                                frameSize=(-2, 2, -1, 1))
        OnscreenText(text="DraveClaw", parent=self.menu, pos=(0, 0.55),
                     scale=0.2, fg=(0.5, 0.8, 1, 1))
        OnscreenText(text=T("sub"), parent=self.menu, pos=(0, 0.35),
                     scale=0.08, fg=(1, 0.85, 0.3, 1))
        OnscreenText(text=T("start"), parent=self.menu, pos=(0, 0.05),
                     scale=0.07, fg=(1, 1, 1, 1))
        OnscreenText(text=T("ctrl"), parent=self.menu, pos=(0, -0.12),
                     scale=0.05, fg=(0.7, 0.78, 0.9, 1))
        OnscreenText(text=T("donationware") + "   " + T("info_hint"),
                     parent=self.menu, pos=(0, -0.42), scale=0.05,
                     fg=(0.7, 0.78, 0.9, 1))
        # info overlay
        self.infop = DirectFrame(frameColor=(0.05, 0.06, 0.10, 0.9),
                                 frameSize=(-2, 2, -1, 1))
        OnscreenText(text=T("info_title"), parent=self.infop, pos=(0, 0.55),
                     scale=0.1, fg=(0.5, 0.8, 1, 1))
        OnscreenText(text=T("donationware"), parent=self.infop, pos=(0, 0.32),
                     scale=0.07, fg=(1, 1, 1, 1))
        OnscreenText(text=T("donate_line"), parent=self.infop, pos=(0, 0.15),
                     scale=0.05, fg=(0.7, 0.78, 0.9, 1))
        DirectButton(text=DONATE, parent=self.infop, scale=0.06, pos=(0, 0, 0.0),
                     relief=None, text_fg=(0.4, 0.7, 1, 1),
                     command=lambda: webbrowser.open(DONATE))
        OnscreenText(text=T("contact") + ":  " + CONTACT, parent=self.infop,
                     pos=(0, -0.2), scale=0.05, fg=(0.7, 0.78, 0.9, 1))
        OnscreenText(text=T("back"), parent=self.infop, pos=(0, -0.45),
                     scale=0.05, fg=(1, 0.85, 0.3, 1))

    def _apply_state(self):
        self.menu.hide()
        self.infop.hide()
        if self.state == MENU:
            self.menu.show()
        elif self.state == INFO:
            self.infop.show()

    # ---- input ----
    def _bind_keys(self):
        m = {"arrow_left": "l", "arrow_right": "r",
             "arrow_up": "f", "arrow_down": "b"}
        for key, slot in m.items():
            self.accept(key, self._set_key, [slot, True])
            self.accept(key + "-up", self._set_key, [slot, False])
        self.accept("space", self.on_space)
        self.accept("p", self.toggle_pause)
        self.accept("i", self.toggle_info)
        self.accept("m", self.toggle_mute)
        self.accept("d", lambda: webbrowser.open(DONATE))
        self.accept("r", self.on_restart)
        self.accept("minus", self.set_volume, [-0.1])
        self.accept("=", self.set_volume, [0.1])
        self.accept("+", self.set_volume, [0.1])
        self.accept("escape", self.userExit)

    def _set_key(self, slot, val):
        self.keymap[slot] = val

    def on_space(self):
        if self.state == MENU:
            self.state = PLAY
            self._apply_state()
            if self.music and not self.muted:
                try:
                    self.music.play()
                except Exception:
                    pass
            return
        if self.state == PLAY and not self.paused and self.phase == "idle":
            if self.credits <= 0:
                self.flash(T("no_credits"))
                return
            self.credits -= 1
            self.phase = "drop"
            self.play_sfx("drop")

    def toggle_pause(self):
        if self.state == PLAY:
            self.paused = not self.paused

    def toggle_info(self):
        if self.state == INFO:
            self.state = self._prev_state
        else:
            self._prev_state = self.state
            self.state = INFO
        self._apply_state()

    def on_restart(self):
        if self.state in (OVER,):
            self.reset_game()

    def reset_game(self):
        for p in self.prizes:
            try:
                if not self.world.getRigidBodies().count(p["node"]):
                    self.world.attachRigidBody(p["node"])
            except Exception:
                pass
        self.credits = 12
        self.won = 0
        self.phase = "idle"
        self.held = None
        self.state = PLAY
        self._apply_state()

    def flash(self, text):
        self.msg = text
        self.msg_t = 2.0

    # ---- claw sequence ----
    def try_grab(self):
        cx, cy = self.claw_x, self.claw_y
        best = None
        bestd = 1e9
        for p in self.prizes:
            if p["held"] or p["won"]:
                continue
            pos = p["np"].getPos(self.render)
            d = math.hypot(pos.x - cx, pos.y - cy)
            if d < GRIP_RADIUS and pos.z < GRABZ + 1.6:
                if d < bestd:
                    bestd = d
                    best = p
        if best is None:
            return False
        chance = self.base_grip * max(0.15, 1.0 - bestd / GRIP_RADIUS)
        if random.random() <= chance:
            self.world.removeRigidBody(best["node"])
            best["np"].reparentTo(self.claw_np)
            best["np"].setPos(0, 0, -0.9)   # netjes in de greep van de tanden
            best["np"].setHpr(0, 0, 0)
            best["held"] = True
            self.held = best
            return True
        return False

    def release(self):
        if not self.held:
            return
        p = self.held
        over_chute = (math.hypot(self.claw_x - HOMEX, self.claw_y - HOMEY) < 0.9)
        p["np"].wrtReparentTo(self.render)
        try:
            p["node"].setLinearVelocity(Vec3(0, 0, 0))
            p["node"].setAngularVelocity(Vec3(0, 0, 0))
        except Exception:
            pass
        self.world.attachRigidBody(p["node"])   # valt nu echt (door het gat de bak in)
        if over_chute:
            p["won"] = True
            self.won += 1
            p["collecting"] = 1.8   # valt zichtbaar in de bak, daarna door de koker weg
            self.flash(T("win_prize"))
            self.play_sfx("win")
        self.held = None

    def _update_collected(self, dt):
        for p in self.prizes:
            if p.get("collecting") is not None:
                p["collecting"] -= dt
                if p["collecting"] <= 0:
                    try:
                        self.world.removeRigidBody(p["node"])
                    except Exception:
                        pass
                    p["np"].hide()
                    p["collecting"] = None

    def _advance(self, dt):
        sp_z = 4.0
        sp_xy = 3.2
        if self.phase == "idle":
            vx = (1 if self.keymap["r"] else 0) - (1 if self.keymap["l"] else 0)
            vy = (1 if self.keymap["f"] else 0) - (1 if self.keymap["b"] else 0)
            self.claw_x = max(-BX + 0.6, min(BX - 0.6, self.claw_x + vx * sp_xy * dt))
            self.claw_y = max(-BY + 0.6, min(BY - 0.6, self.claw_y + vy * sp_xy * dt))
        elif self.phase == "drop":
            self.claw_z -= sp_z * dt
            if self.claw_z <= GRABZ:
                self.claw_z = GRABZ
                self.phase = "close"
                self.phase_t = 0.0
                self.play_sfx("close")
        elif self.phase == "close":
            self.phase_t += dt
            self.grip = min(1.0, self.phase_t / 0.4)
            if self.phase_t >= 0.4:
                self.got = self.try_grab()
                self.phase = "lift"
                self.play_sfx("lift")
        elif self.phase == "lift":
            self.claw_z += sp_z * dt
            if self.claw_z >= TOPZ:
                self.claw_z = TOPZ
                if self.held:
                    self.flash(T("got_it"))
                    self.phase = "return"
                else:
                    self.flash(T("missed"))
                    self.play_sfx("miss")
                    self.phase = "open"
                    self.phase_t = 0.0
        elif self.phase == "return":
            dx = HOMEX - self.claw_x
            dy = HOMEY - self.claw_y
            dist = math.hypot(dx, dy)
            if dist < 0.05:
                self.phase = "open"
                self.phase_t = 0.0
            else:
                step = min(dist, sp_xy * dt)
                self.claw_x += dx / dist * step
                self.claw_y += dy / dist * step
        elif self.phase == "open":
            self.phase_t += dt
            self.grip = max(0.0, 1.0 - self.phase_t / 0.4)
            if self.phase_t >= 0.4:
                self.release()
                self.phase = "idle"
                if self.credits <= 0:
                    self.state = OVER

    # ---- main loop ----
    def update(self, task):
        dt = globalClock.getDt()
        if dt > 0.05:
            dt = 0.05
        self.world.doPhysics(dt, 5, 1 / 120.0)
        if self.state == PLAY and not self.paused:
            self._advance(dt)
            self._update_collected(dt)
        # move claw body
        self.claw_np.setPos(self.claw_x, self.claw_y, self.claw_z)
        self._update_fingers()
        if self.msg_t > 0:
            self.msg_t -= dt
        self._update_hud()
        return task.cont

    def _update_hud(self):
        if self.state == PLAY:
            self.hud.setText("%s: %d    %s: %d" %
                             (T("credits"), self.credits, T("prizes"), self.won))
            if self.msg_t > 0:
                self.hint.setText(self.msg)
            elif self.paused:
                self.hint.setText(T("paused"))
            elif self.phase == "idle":
                self.hint.setText(T("aim"))
            else:
                self.hint.setText(T("grabbing"))
        elif self.state == OVER:
            self.hud.setText("%s: %d" % (T("prizes"), self.won))
            self.hint.setText(T("gameover"))
        else:
            self.hud.setText("")
            self.hint.setText("")
        if self.muted:
            self.hud.setText(self.hud.getText() + "    (" + T("sound_off") + ")")


if __name__ == "__main__":
    Game().run()

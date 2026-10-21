# -*- coding: utf-8 -*-
"""DraveJump - a friendly 3D platformer (Panda3D + Bullet).

Hop across the platforms, collect the coins and reach the glowing goal.
Forgiving controls (few keys, generous jumps), clear big shapes, calm camera.
Language follows the PC (Dutch/English). Donationware. Portable (everything in
the app folder).

Speel/Play:
  - Arrow keys / WASD: move    Space: jump
  - R: restart level   P: pause   I: info/donate   M: sound   Esc: quit
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

loadPrcFileData("", "window-title DraveJump")
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
                          GeomTriangles, Filename)
from panda3d.bullet import (BulletWorld, BulletRigidBodyNode, BulletBoxShape,
                            BulletCapsuleShape, BulletCharacterControllerNode,
                            ZUp)

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
    "sub": {"nl": "Een vrolijke 3D-springer", "en": "A friendly 3D jumper"},
    "start": {"nl": "Druk op SPATIE om te spelen", "en": "Press SPACE to play"},
    "ctrl": {"nl": "Pijltjes / WASD = lopen    Spatie = springen",
             "en": "Arrows / WASD = move    Space = jump"},
    "coins": {"nl": "Munten", "en": "Coins"},
    "level": {"nl": "Level", "en": "Level"},
    "goal_hint": {"nl": "Pak de munten en bereik het lichtbaken!",
                  "en": "Grab the coins and reach the glowing goal!"},
    "level_done": {"nl": "Level gehaald!", "en": "Level complete!"},
    "fell": {"nl": "Oeps! Opnieuw...", "en": "Oops! Try again..."},
    "win_title": {"nl": "Helemaal uitgespeeld!", "en": "You finished them all!"},
    "win_sub": {"nl": "Goed gesprongen, kampioen!", "en": "Great jumping, champ!"},
    "restart": {"nl": "Druk op R om opnieuw te spelen", "en": "Press R to play again"},
    "paused": {"nl": "GEPAUZEERD  (P = verder)", "en": "PAUSED  (P = resume)"},
    "sound_off": {"nl": "geluid uit", "en": "sound off"},
    "info_hint": {"nl": "I = info / donatie", "en": "I = info / donate"},
    "info_title": {"nl": "Over DraveJump", "en": "About DraveJump"},
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
AUDIO_SR = 22050
SPEED = 7.0
MENU, PLAY, WIN, INFO = "menu", "play", "win", "info"


# ---------------------------------------------------------------------------
# geometry helpers
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


def _sphere_node(slices=18, stacks=12):
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
# procedural audio -> WAV (app-local cache)
# ---------------------------------------------------------------------------
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
        else:
            s = math.sin(2 * math.pi * x)
        e = 1.0
        if i < atk:
            e = i / atk
        elif i > n - rel:
            e = max(0.0, (n - i) / rel)
        buf[i] = int(max(-1.0, min(1.0, s * e * vol)) * 32767)
    return buf


def _sweep(f0, f1, ms, vol=0.5, wave_t="square"):
    n = max(1, int(AUDIO_SR * ms / 1000))
    buf = array.array("h", bytes(2 * n))
    rel = max(1, int(0.05 * AUDIO_SR))
    ph = 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        ph += f / AUDIO_SR
        x = ph - math.floor(ph)
        s = (1.0 if x < 0.5 else -1.0) if wave_t == "square" else 2 * x - 1
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
    bpm = 132
    beat = 60000 / bpm / 2.0
    scale = [330, 370, 392, 440, 494, 523, 587, 659]
    bass = [165, 165, 196, 196, 220, 196, 165, 147,
            165, 165, 196, 196, 247, 220, 196, 165]
    mel = [0, 2, 4, 5, 4, 2, 0, 2, 4, 5, 7, 5, 4, 2, 4, 0]
    bb = array.array("h")
    mm = array.array("h")
    for k in range(16):
        bb += _tone(bass[k], beat, 0.26, "tri")
        mm += _tone(scale[mel[k] % len(scale)], beat, 0.16, "square")
    n = min(len(bb), len(mm))
    return _mix(bb[:n], mm[:n])


def _write_wav(path, buf):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(AUDIO_SR)
        w.writeframes(buf.tobytes())


def build_audio_files(folder):
    gens = {
        "music": _music_buf,
        "jump": lambda: _sweep(360, 760, 150, 0.4, "square"),
        "coin": lambda: _seq([_tone(880, 60, 0.4, "square"),
                              _tone(1318, 110, 0.4, "square")]),
        "win": lambda: _seq([_tone(523, 110, .4), _tone(659, 110, .4),
                             _tone(784, 110, .4), _tone(1047, 240, .45)]),
        "fall": lambda: _sweep(500, 120, 360, 0.4, "square"),
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
# levels:  platforms (cx,cy,cz, sx,sy,sz), coins [(x,y,z)], goal (x,y,z),
#          spawn (x,y,z)
# ---------------------------------------------------------------------------
def build_levels():
    L = []
    # ---- level 1 : easy straight-ish path ----
    L.append({
        "plats": [(0, 0, 0, 7, 7, 1), (0, 9, 0, 5, 5, 1),
                  (0, 16, 1, 5, 5, 1), (5, 23, 2, 5, 5, 1),
                  (5, 31, 3, 7, 7, 1)],
        "coins": [(0, 9, 2.2), (0, 16, 3.2), (5, 23, 4.2)],
        "goal": (5, 31, 4.2),
        "spawn": (0, 0, 3.0),
    })
    # ---- level 2 : milde zigzag, grote platforms, kleine gaten ----
    L.append({
        "plats": [(0, 0, 0, 6, 6, 1), (-2, 7, 1, 5, 5, 1),
                  (2, 13, 1, 5, 5, 1), (-2, 19, 2, 5, 5, 1),
                  (2, 25, 2, 5, 5, 1), (0, 32, 3, 7, 7, 1)],
        "coins": [(-2, 7, 3.2), (2, 13, 3.2), (-2, 19, 4.2), (2, 25, 4.2)],
        "goal": (0, 32, 4.2),
        "spawn": (0, 0, 3.0),
    })
    # ---- level 3 : rustige klim (+1 per stap, grote platforms) ----
    L.append({
        "plats": [(0, 0, 0, 6, 6, 1), (0, 7, 1, 5, 5, 1),
                  (3, 13, 2, 5, 5, 1), (-1, 19, 3, 5, 5, 1),
                  (3, 25, 4, 5, 5, 1), (0, 32, 5, 7, 7, 1)],
        "coins": [(0, 7, 3.2), (3, 13, 4.2), (-1, 19, 5.2), (3, 25, 6.2)],
        "goal": (0, 32, 6.2),
        "spawn": (0, 0, 3.0),
    })
    return L


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.has_win = self.win is not None
        self.render.setTwoSided(True)
        self._setup_lights()
        if self.has_win:
            self.setBackgroundColor(0.53, 0.70, 0.92)
            self.render.setShaderAuto()
            self.disableMouse()

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -22))
        self.cube_tmpl = NodePath(_cube_node())
        self.sphere_tmpl = NodePath(_sphere_node())

        self.levels = build_levels()
        self.level_i = 0
        self.coins = 0
        self.coin_nodes = []
        self.plat_node = None
        self.goal_np = None

        self._build_char()
        if self.has_win:
            self._build_backdrop()
        self.load_level(0)

        self.state = MENU
        self.paused = False
        self.msg = ""
        self.msg_t = 0.0
        self.coyote = 0.0
        self.jump_buf = 0.0
        self.t = 0.0

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
        amb.setColor(Vec4(0.55, 0.56, 0.62, 1))
        self.render.setLight(self.render.attachNewNode(amb))
        key = DirectionalLight("key")
        key.setColor(Vec4(0.95, 0.93, 0.85, 1))
        knp = self.render.attachNewNode(key)
        knp.setHpr(-30, -55, 0)
        self.render.setLight(knp)

    def _box(self, parent, sx, sy, sz, color, pos=(0, 0, 0)):
        np = self.cube_tmpl.copyTo(parent)
        np.setScale(sx, sy, sz)
        np.setPos(*pos)
        np.setColor(*color, 1)
        return np

    def _sphere(self, parent, scale, color, pos=(0, 0, 0)):
        np = self.sphere_tmpl.copyTo(parent)
        if isinstance(scale, (tuple, list)):
            np.setScale(*scale)
        else:
            np.setScale(scale)
        np.setPos(*pos)
        np.setColor(color[0], color[1], color[2], 1)
        return np

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
        np.setBin("background", 0)
        np.setDepthWrite(False)
        np.setTwoSided(True)
        return np

    def _build_backdrop(self):
        # lucht-gradient die met de camera meebeweegt
        sky = self.render.attachNewNode("sky")
        q = self._grad_quad(
            [(-80, 60, -40), (80, 60, -40), (80, 60, 70), (-80, 60, 70)],
            [(0.78, 0.85, 0.95, 1), (0.78, 0.85, 0.95, 1),
             (0.40, 0.60, 0.90, 1), (0.40, 0.60, 0.90, 1)])
        q.reparentTo(sky)
        self.sky = sky

    def _build_char(self):
        shape = BulletCapsuleShape(0.4, 0.9, ZUp)
        self.char = BulletCharacterControllerNode(shape, 0.4, "player")
        self.char.setGravity(28)
        self.char.setMaxJumpHeight(2.8)
        self.char.setJumpSpeed(10.5)
        self.charNP = self.render.attachNewNode(self.char)
        self.world.attachCharacter(self.char)
        # mascotte (duidelijk, vrolijk)
        self.mascot = self.charNP.attachNewNode("mascot")
        body = (0.98, 0.55, 0.25)
        self._sphere(self.mascot, (0.55, 0.55, 0.6), body, (0, 0, -0.25))
        self._sphere(self.mascot, 0.42, body, (0, 0, 0.5))            # head
        # gezicht aan de VOORkant (+Y), zodat hij vooruit/in de looprichting kijkt
        self._sphere(self.mascot, 0.16, (1, 1, 1), (0.16, 0.34, 0.6))
        self._sphere(self.mascot, 0.16, (1, 1, 1), (-0.16, 0.34, 0.6))
        self._sphere(self.mascot, 0.07, (0.1, 0.1, 0.12), (0.18, 0.46, 0.6))
        self._sphere(self.mascot, 0.07, (0.1, 0.1, 0.12), (-0.18, 0.46, 0.6))
        self._sphere(self.mascot, (0.18, 0.10, 0.10), (0.9, 0.4, 0.2),
                     (0, 0.42, 0.42))                                 # snuit
        self._sphere(self.mascot, 0.15, body, (0.42, 0, 0.55))       # oren
        self._sphere(self.mascot, 0.15, body, (-0.42, 0, 0.55))
        self._sphere(self.mascot, (0.2, 0.22, 0.16), (0.2, 0.5, 0.85),
                     (0.28, 0, -0.7))                                 # voetjes
        self._sphere(self.mascot, (0.2, 0.22, 0.16), (0.2, 0.5, 0.85),
                     (-0.28, 0, -0.7))

    def load_level(self, i):
        self.level_i = i
        lv = self.levels[i]
        # ruim oude op
        if self.plat_node is not None:
            self.world.removeRigidBody(self.plat_node.node())
            self.plat_node.removeNode()
        for c in self.coin_nodes:
            c["np"].removeNode()
        self.coin_nodes = []
        if self.goal_np is not None:
            self.goal_np.removeNode()
            self.goal_np = None
        # platforms (1 statisch lichaam met meerdere boxes + visuals)
        body = BulletRigidBodyNode("plats")
        from panda3d.core import TransformState
        palette = [(0.45, 0.75, 0.95), (0.55, 0.85, 0.55), (0.95, 0.8, 0.4),
                   (0.9, 0.55, 0.7), (0.7, 0.6, 0.95)]
        self.plat_node = self.render.attachNewNode(body)
        for idx, (cx, cy, cz, sx, sy, sz) in enumerate(lv["plats"]):
            body.addShape(BulletBoxShape(Vec3(sx / 2, sy / 2, sz / 2)),
                          TransformState.makePos(Point3(cx, cy, cz)))
            col = palette[idx % len(palette)]
            self._box(self.plat_node, sx, sy, sz, (col[0] * 0.8, col[1] * 0.8,
                      col[2] * 0.8), (cx, cy, cz))
            self._box(self.plat_node, sx, sy, 0.12, col, (cx, cy, cz + sz / 2))
        self.world.attachRigidBody(body)
        # coins
        for (x, y, z) in lv["coins"]:
            cnp = self.render.attachNewNode("coin")
            cnp.setPos(x, y, z)
            self._sphere(cnp, (0.34, 0.10, 0.34), (1.0, 0.85, 0.2))
            self._sphere(cnp, (0.18, 0.05, 0.18), (1.0, 0.95, 0.5))
            self.coin_nodes.append({"np": cnp, "pos": (x, y, z), "got": False})
        # goal beacon
        gx, gy, gz = lv["goal"]
        self.goal_np = self.render.attachNewNode("goal")
        self.goal_np.setPos(gx, gy, gz)
        beam = self._box(self.goal_np, 0.5, 0.5, 5.0, (0.4, 1.0, 0.7), (0, 0, 2.0))
        beam.setLightOff()
        beam.setShaderOff()
        star = self._sphere(self.goal_np, 0.4, (0.5, 1.0, 0.8), (0, 0, 0.8))
        star.setLightOff()
        star.setShaderOff()
        self.goal_pos = (gx, gy, gz)
        # plaats speler
        sp = lv["spawn"]
        self.charNP.setPos(sp[0], sp[1], sp[2])

    # ---- audio ----
    def _audio_dir(self):
        d = os.path.join(_app_dir(), "cache")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d

    def _init_audio(self):
        threading.Thread(target=self._load_audio, daemon=True).start()

    def _load_audio(self):
        try:
            files = build_audio_files(self._audio_dir())
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
        self.hud = OnscreenText(text="", pos=(-1.30, 0.86), scale=0.07,
                                fg=(1, 1, 1, 1), align=TextNode.ALeft,
                                mayChange=True, shadow=(0, 0, 0, 0.6))
        self.hint = OnscreenText(text="", pos=(0, -0.88), scale=0.06,
                                 fg=(1, 1, 0.7, 1), align=TextNode.ACenter,
                                 mayChange=True, shadow=(0, 0, 0, 0.6))
        DirectButton(text=DONATE, scale=0.045, pos=(0, 0, -0.96), relief=None,
                     text_fg=(0.2, 0.35, 0.9, 1),
                     command=lambda: webbrowser.open(DONATE))
        self.menu = DirectFrame(frameColor=(0.1, 0.12, 0.2, 0.78),
                                frameSize=(-2, 2, -1, 1))
        OnscreenText(text="DraveJump", parent=self.menu, pos=(0, 0.55),
                     scale=0.22, fg=(1, 0.8, 0.3, 1))
        OnscreenText(text=T("sub"), parent=self.menu, pos=(0, 0.33),
                     scale=0.08, fg=(0.9, 0.95, 1, 1))
        OnscreenText(text=T("start"), parent=self.menu, pos=(0, 0.03),
                     scale=0.07, fg=(1, 1, 1, 1))
        OnscreenText(text=T("ctrl"), parent=self.menu, pos=(0, -0.14),
                     scale=0.05, fg=(0.85, 0.9, 1, 1))
        OnscreenText(text=T("donationware") + "   " + T("info_hint"),
                     parent=self.menu, pos=(0, -0.42), scale=0.05,
                     fg=(0.85, 0.9, 1, 1))
        self.infop = DirectFrame(frameColor=(0.1, 0.12, 0.2, 0.9),
                                 frameSize=(-2, 2, -1, 1))
        OnscreenText(text=T("info_title"), parent=self.infop, pos=(0, 0.55),
                     scale=0.1, fg=(1, 0.8, 0.3, 1))
        OnscreenText(text=T("donationware"), parent=self.infop, pos=(0, 0.32),
                     scale=0.07, fg=(1, 1, 1, 1))
        OnscreenText(text=T("donate_line"), parent=self.infop, pos=(0, 0.15),
                     scale=0.05, fg=(0.85, 0.9, 1, 1))
        DirectButton(text=DONATE, parent=self.infop, scale=0.06, pos=(0, 0, 0.0),
                     relief=None, text_fg=(0.3, 0.5, 1, 1),
                     command=lambda: webbrowser.open(DONATE))
        OnscreenText(text=T("contact") + ":  " + CONTACT, parent=self.infop,
                     pos=(0, -0.2), scale=0.05, fg=(0.85, 0.9, 1, 1))
        OnscreenText(text=T("back"), parent=self.infop, pos=(0, -0.45),
                     scale=0.05, fg=(1, 0.85, 0.3, 1))

    def _apply_state(self):
        if not self.has_win:
            return
        self.menu.hide()
        self.infop.hide()
        if self.state == MENU:
            self.menu.show()
        elif self.state == INFO:
            self.infop.show()

    # ---- input ----
    def _bind_keys(self):
        self.keymap = {"l": False, "r": False, "f": False, "b": False}
        binds = {"arrow_left": "l", "a": "l", "arrow_right": "r", "d": "r",
                 "arrow_up": "f", "w": "f", "arrow_down": "b", "s": "b"}
        for key, slot in binds.items():
            self.accept(key, self._set_key, [slot, True])
            self.accept(key + "-up", self._set_key, [slot, False])
        self.accept("space", self.on_jump)
        self.accept("p", self.toggle_pause)
        self.accept("i", self.toggle_info)
        self.accept("m", self.toggle_mute)
        self.accept("d", lambda: webbrowser.open(DONATE))
        self.accept("r", self.on_restart)
        self.accept("minus", self.set_volume, [-0.1])
        self.accept("=", self.set_volume, [0.1])
        self.accept("escape", self.userExit)

    def _set_key(self, slot, val):
        self.keymap[slot] = val

    def on_jump(self):
        if self.state == MENU:
            self.start_game()
            return
        if self.state == PLAY and not self.paused:
            self.jump_buf = 0.16

    def start_game(self):
        self.level_i = 0
        self.coins = 0
        self.load_level(0)
        self.state = PLAY
        self._apply_state()
        if self.music and not self.muted:
            try:
                self.music.play()
            except Exception:
                pass

    def toggle_pause(self):
        if self.state == PLAY:
            self.paused = not self.paused

    def toggle_info(self):
        if self.state == INFO:
            self.state = self._prev
        else:
            self._prev = self.state
            self.state = INFO
        self._apply_state()

    def on_restart(self):
        if self.state == PLAY:
            self.load_level(self.level_i)
        elif self.state == WIN:
            self.start_game()

    def flash(self, text):
        self.msg = text
        self.msg_t = 1.8

    # ---- main loop ----
    def update(self, task):
        dt = globalClock.getDt()
        if dt > 0.05:
            dt = 0.05
        self.t += dt
        if self.state == PLAY and not self.paused:
            self._play_step(dt)
        self.world.doPhysics(dt, 4, 1 / 120.0)
        self._update_camera(dt)
        if hasattr(self, "sky"):
            self.sky.setPos(self.camera.getX(), 0, 0)
        if self.msg_t > 0:
            self.msg_t -= dt
        self._update_hud()
        return task.cont

    def _play_step(self, dt):
        # beweging in wereld-assen (camera kijkt langs +Y)
        dx = (1 if self.keymap["r"] else 0) - (1 if self.keymap["l"] else 0)
        dy = (1 if self.keymap["f"] else 0) - (1 if self.keymap["b"] else 0)
        mv = Vec3(dx, dy, 0)
        if mv.lengthSquared() > 0:
            mv.normalize()
            self.charNP.setH(math.degrees(math.atan2(-mv.x, mv.y)))
        self.char.setLinearMovement(mv * SPEED, False)
        # coyote-tijd + sprong-buffer (vergevingsgezind)
        if self.char.isOnGround():
            self.coyote = 0.12
        else:
            self.coyote = max(0.0, self.coyote - dt)
        if self.jump_buf > 0:
            self.jump_buf -= dt
        if self.jump_buf > 0 and self.coyote > 0:
            self.char.doJump()
            self.jump_buf = 0.0
            self.coyote = 0.0
            self.play_sfx("jump")
        # munten
        p = self.charNP.getPos()
        for c in self.coin_nodes:
            if c["got"]:
                continue
            cx, cy, cz = c["pos"]
            if (p.x - cx) ** 2 + (p.y - cy) ** 2 + (p.z - cz) ** 2 < 1.4:
                c["got"] = True
                c["np"].hide()
                self.coins += 1
                self.play_sfx("coin")
        # doel
        gx, gy, gz = self.goal_pos
        if (p.x - gx) ** 2 + (p.y - gy) ** 2 + (p.z - gz) ** 2 < 2.6:
            self._level_done()
            return
        # vallen
        if p.z < -8:
            self.play_sfx("fall")
            self.flash(T("fell"))
            self.load_level(self.level_i)

    def _level_done(self):
        if self.level_i + 1 < len(self.levels):
            self.play_sfx("win")
            self.flash(T("level_done"))
            self.load_level(self.level_i + 1)
        else:
            self.state = WIN
            self.play_sfx("win")
            if self.music:
                try:
                    self.music.stop()
                except Exception:
                    pass

    def _update_camera(self, dt):
        if not self.has_win:
            return
        p = self.charNP.getPos()
        target = Point3(p.x * 0.5, p.y - 12, p.z + 6.5)
        cur = self.camera.getPos()
        k = min(1.0, dt * 4.0)
        self.camera.setPos(cur + (target - cur) * k)
        self.camera.lookAt(p.x * 0.5, p.y + 2, p.z + 1.0)

    def _spin_coins(self):
        ang = (self.t * 120) % 360
        for c in self.coin_nodes:
            if not c["got"]:
                c["np"].setH(ang)
                cx, cy, cz = c["pos"]
                c["np"].setZ(cz + 0.18 * math.sin(self.t * 3))

    def _update_hud(self):
        self._spin_coins()
        if self.goal_np is not None:
            self.goal_np.setH((self.t * 60) % 360)
        if self.state == PLAY:
            self.hud.setText("%s: %d    %s: %d/%d" %
                             (T("coins"), self.coins, T("level"),
                              self.level_i + 1, len(self.levels)))
            if self.msg_t > 0:
                self.hint.setText(self.msg)
            elif self.paused:
                self.hint.setText(T("paused"))
            else:
                self.hint.setText(T("goal_hint"))
        elif self.state == WIN:
            self.hud.setText("%s: %d" % (T("coins"), self.coins))
            self.hint.setText(T("win_title") + " - " + T("restart"))
        else:
            self.hud.setText("")
            self.hint.setText("")
        if self.muted and self.state == PLAY:
            self.hud.setText(self.hud.getText() + "   (" + T("sound_off") + ")")


if __name__ == "__main__":
    Game().run()

# -*- coding: utf-8 -*-
"""DraveRunner - een Lode Runner-achtig spel (pygame).

Eigen graphics + naam (Dravenlock). Taal volgt de pc (NL/EN). Donationware.
Verzamel al het goud, ontwijk de bewakers (graaf gaten om ze te vangen) en
ontsnap naar de bovenkant.

Besturing: pijltjes = lopen/klimmen, Z = graaf links, X = graaf rechts,
P = pauze, M = geluid aan/uit, - / + = volume, I = info, Esc = afsluiten.
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
# taal volgt de pc
# ---------------------------------------------------------------------------
def _lang():
    try:
        c = (locale.getdefaultlocale()[0] or "")
    except Exception:
        c = ""
    return "nl" if c.lower().startswith("nl") else "en"


LANG = _lang()
TXT = {
    "sub": {"nl": "De Goudjager", "en": "The Gold Runner"},
    "start": {"nl": "Druk op SPATIE om te starten", "en": "Press SPACE to start"},
    "help": {"nl": "Pijltjes = lopen/klimmen   Z/X = graven links/rechts   P = pauze",
             "en": "Arrows = run/climb   Z/X = dig left/right   P = pause"},
    "help2": {"nl": "Pak al het goud en ontsnap naar boven. Pas op de bewakers!",
              "en": "Grab all the gold and escape upward. Beware the guards!"},
    "gold": {"nl": "Goud", "en": "Gold"},
    "lives": {"nl": "Levens", "en": "Lives"},
    "level": {"nl": "Level", "en": "Level"},
    "sound": {"nl": "Geluid", "en": "Sound"},
    "off": {"nl": "uit", "en": "off"},
    "paused": {"nl": "GEPAUZEERD", "en": "PAUSED"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "over": {"nl": "Game over", "en": "Game over"},
    "win": {"nl": "Je hebt alle levels gehaald!", "en": "You cleared all levels!"},
    "restart": {"nl": "Druk op R om opnieuw te spelen", "en": "Press R to play again"},
    "levelclear": {"nl": "Level gehaald!", "en": "Level cleared!"},
    "audio_hint": {"nl": "M = geluid aan/uit    - / + = volume    I = info",
                   "en": "M = sound on/off    - / + = volume    I = info"},
    "info": {"nl": "Info", "en": "Info"},
    "donation": {"nl": "Donationware - een vrijwillige donatie is welkom:",
                 "en": "Donationware - a voluntary donation is welcome:"},
    "back": {"nl": "Druk op een toets om terug te gaan", "en": "Press a key to go back"},
}


def T(k):
    d = TXT.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

# ---------------------------------------------------------------------------
W, H, HUD = 920, 600, 52
FPS = 60
SIM = 0.10          # logica-stap in seconden
HOLE_TIME = 5.0     # hoe lang een gegraven gat open blijft
LIVES0 = 3

BG = (10, 12, 18)
BRICK = (158, 74, 48)
MORTAR = (54, 26, 18)
STONE = (90, 94, 108)
LAD = (214, 184, 92)
BARC = (200, 200, 150)
GOLDC = (246, 205, 60)
PCOL = (96, 200, 255)
GCOL = (228, 92, 80)
TEXT = (235, 240, 250)
SUB = (150, 165, 190)

MENU, PLAY, OVER, WIN, INFO = "menu", "play", "over", "win", "info"

# ---------------------------------------------------------------------------
# geluid (zelf opgewekt, geen losse bestanden)
# ---------------------------------------------------------------------------
AUDIO_SR = 22050


def _envv(i, n, sr, atk=0.008, rel=0.05):
    return min(min(1.0, i / max(1, atk * sr)), min(1.0, (n - i) / max(1, rel * sr)))


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
        out.append(int(v * amp * _envv(i, n, sr)))
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
        out.append(int(v * amp * _envv(i, n, sr, 0.004, 0.08)))
    return out


def _seq(notes, vol=0.4, wave="square"):
    out = array.array("h")
    for f, ms in notes:
        out.extend(_tone(f, ms, vol, wave) if f > 0 else _tone(1, ms, 0.0))
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


def _track(bars, bpm, lead_wave="tri", lead_vol=0.32, bass_vol=0.26):
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


# ---------------------------------------------------------------------------
# levels (procedureel opgebouwd zodat ladders/platforms netjes uitlijnen)
# ---------------------------------------------------------------------------
def _make_level(cols, rows, plats, ladders, bars, golds, pstart, guards):
    g = [[" "] * cols for _ in range(rows)]
    for c in range(cols):
        g[rows - 1][c] = "="                       # vloer
    for pr in plats:
        for c in range(cols):
            g[pr][c] = "#"
    for (br, c0, c1) in bars:
        for c in range(c0, c1):
            g[br][c] = "-"
    for lc in ladders:
        for r in range(0, rows - 1):
            g[r][lc] = "H"                          # ladders reiken tot de top
    for (r, c) in golds:
        g[r][c] = "$"
    return {"grid": g, "cols": cols, "rows": rows,
            "pstart": pstart, "guards": list(guards),
            "gold": sum(row.count("$") for row in g)}


def build_levels():
    L = []
    # --- Level 1 ---
    cols, rows = 24, 13
    plats = [2, 4, 6, 8, 10]
    ladders = [4, 11, 18]
    bars = [(3, 12, 18), (7, 5, 11)]
    golds = [(1, 2), (1, 8), (1, 15), (1, 21), (3, 6), (3, 21),
             (5, 2), (5, 9), (5, 15), (7, 2), (7, 21),
             (9, 6), (9, 15), (11, 2), (11, 21)]
    L.append(_make_level(cols, rows, plats, ladders, bars, golds,
                         (11, 1), [(1, 11), (5, 18)]))
    # --- Level 2 (meer ladders, meer bewakers) ---
    cols, rows = 26, 14
    plats = [2, 5, 8, 11]
    ladders = [3, 9, 16, 22]
    bars = [(4, 4, 9), (4, 16, 22), (7, 9, 16), (10, 3, 9)]
    golds = [(1, 3), (1, 12), (1, 22), (4, 6), (4, 19), (4, 12),
             (7, 3), (7, 12), (7, 22), (10, 6), (10, 19),
             (12, 3), (12, 12), (12, 22), (1, 16)]
    L.append(_make_level(cols, rows, plats, ladders, bars, golds,
                         (12, 1), [(1, 9), (4, 16), (7, 22)]))
    # --- Level 3 ---
    cols, rows = 28, 14
    plats = [2, 5, 8, 11]
    ladders = [3, 8, 13, 18, 24]
    bars = [(3, 8, 13), (6, 13, 18), (9, 3, 8), (9, 18, 24)]
    golds = [(1, 5), (1, 11), (1, 16), (1, 21), (1, 26),
             (4, 6), (4, 15), (4, 22), (7, 5), (7, 11), (7, 20), (7, 26),
             (10, 6), (10, 16), (10, 22), (12, 2), (12, 26)]
    L.append(_make_level(cols, rows, plats, ladders, bars, golds,
                         (12, 1), [(1, 13), (4, 18), (7, 8)]))
    # --- Level 4 (smaller, taller, krap) ---
    cols, rows = 22, 15
    plats = [2, 4, 6, 8, 10, 12]
    ladders = [4, 10, 17]
    bars = [(3, 12, 17), (5, 10, 17), (9, 4, 10)]
    golds = [(1, 2), (1, 8), (1, 14), (1, 20), (3, 6), (3, 14),
             (5, 2), (5, 14), (5, 20), (7, 6), (7, 8),
             (9, 2), (9, 20), (11, 6), (11, 14), (13, 2), (13, 20)]
    L.append(_make_level(cols, rows, plats, ladders, bars, golds,
                         (13, 1), [(1, 10), (5, 17), (9, 4)]))
    # --- Level 5 (groot, finale) ---
    cols, rows = 30, 14
    plats = [2, 5, 8, 11]
    ladders = [3, 9, 15, 21, 27]
    bars = [(4, 3, 9), (4, 21, 27), (7, 9, 15), (7, 15, 21),
            (10, 3, 9), (10, 21, 27)]
    golds = [(1, 6), (1, 12), (1, 18), (1, 24), (4, 6), (4, 12), (4, 18), (4, 24),
             (7, 6), (7, 12), (7, 18), (7, 24), (10, 6), (10, 12), (10, 18),
             (10, 24), (12, 2), (12, 28)]
    L.append(_make_level(cols, rows, plats, ladders, bars, golds,
                         (12, 1), [(1, 9), (4, 15), (7, 21), (10, 3)]))
    return L


LEVELS = build_levels()


# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        try:
            pygame.mixer.pre_init(AUDIO_SR, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        pygame.display.set_caption("DraveRunner")
        self.screen = pygame.display.set_mode((W, H))
        try:
            ic = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "assets", "icon-64.png")
            if os.path.exists(ic):
                pygame.display.set_icon(pygame.image.load(ic))
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.big = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.mid = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.small = pygame.font.SysFont("Segoe UI", 16)
        self.volume = 0.6
        self.muted = False
        self.paused = False
        self.dig = 0
        self.sim_acc = 0.0
        self.gtick = 0
        self.link_rects = []
        self._init_audio()
        self.state = MENU
        self.level_i = 0
        self.lives = LIVES0
        self.load_level(0)

    # ---- geluid ----
    def _init_audio(self):
        self.audio = False
        self.snd = {}
        self.music = []
        self.mch = None
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
            self.snd["dig"] = self._snd(_sweep(300, 120, 200, 0.5, "saw"))
            self.snd["gold"] = self._snd(_seq([(988, 60), (1319, 90)], 0.5, "square"))
            self.snd["die"] = self._snd(_sweep(600, 110, 500, 0.5, "saw"))
            self.snd["win"] = self._snd(_seq([(523, 90), (659, 90), (784, 90),
                                              (1047, 200)], 0.5, "square"))
            self.audio = True
            self._apply_volume()
            threading.Thread(target=self._build_music, daemon=True).start()
        except Exception:
            self.audio = False

    def _snd(self, arr):
        return pygame.mixer.Sound(buffer=arr.tobytes())

    def _build_music(self):
        try:
            barsA = [
                (131, [(523, 1), (392, 1), (523, 1), (659, 1)]),
                (110, [(440, 1), (330, 1), (440, 1), (523, 1)]),
                (147, [(587, 1), (440, 1), (587, 1), (440, 1)]),
                (196, [(392, 2), (494, 2)]),
                (131, [(523, 1), (659, 1), (784, 1), (659, 1)]),
                (110, [(440, 2), (330, 2)]),
                (175, [(349, 1), (440, 1), (523, 1), (440, 1)]),
                (196, [(392, 2), (0, 2)]),
            ]
            barsB = [
                (110, [(330, .5), (440, .5), (523, .5), (440, .5),
                       (330, .5), (440, .5), (523, .5), (659, .5)]),
                (147, [(294, .5), (349, .5), (440, .5), (349, .5),
                       (294, .5), (349, .5), (440, .5), (587, .5)]),
                (131, [(262, .5), (330, .5), (392, .5), (330, .5),
                       (262, .5), (392, .5), (523, .5), (392, .5)]),
                (196, [(392, 1), (494, 1), (587, 2)]),
            ]
            self.music = [self._snd(_track(barsA, 124, "tri")),
                          self._snd(_track(barsB, 138, "square", 0.28))]
        except Exception:
            pass

    def _apply_volume(self):
        if not self.audio:
            return
        mv = 0.0 if self.muted else self.volume
        try:
            if self.mch:
                self.mch.set_volume(mv * 0.5)
            for s in self.snd.values():
                s.set_volume(mv)
        except Exception:
            pass

    def _music(self, on):
        if not self.audio:
            return
        try:
            if on:
                if self.music and not self.mch.get_busy():
                    self._mi = (self._mi + 1) % len(self.music)
                    self.mch.play(self.music[self._mi], loops=-1)
                    self._apply_volume()
            else:
                self.mch.stop()
        except Exception:
            pass

    def play_sfx(self, name):
        if self.audio and not self.muted and name in self.snd:
            try:
                self.snd[name].play()
            except Exception:
                pass

    def set_volume(self, d):
        self.volume = max(0.0, min(1.0, round(self.volume + d, 2)))
        self.muted = False
        self._apply_volume()

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    # ---- level laden ----
    def load_level(self, i):
        lv = LEVELS[i]
        self.grid = [row[:] for row in lv["grid"]]
        self.cols, self.rows = lv["cols"], lv["rows"]
        self.gold = lv["gold"]
        pr, pc = lv["pstart"]
        self.player = {"r": pr, "c": pc}
        self.pstart = (pr, pc)
        self.guards = [{"r": r, "c": c, "sr": r, "sc": c} for (r, c) in lv["guards"]]
        self.gstarts = list(lv["guards"])
        self.holes = []
        self.dig = 0
        self.sim_acc = 0.0
        # tegelgrootte berekenen
        self.ts = min(W // self.cols, (H - HUD) // self.rows)
        self.ox = (W - self.cols * self.ts) // 2
        self.oy = HUD + ((H - HUD) - self.rows * self.ts) // 2

    # ---- veld-helpers ----
    def _solid(self, r, c):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return True
        return self.grid[r][c] in ("#", "=")

    def _ladder(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == "H"

    def _bar(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == "-"

    def _in_hole(self, r, c):
        return any(h["r"] == r and h["c"] == c for h in self.holes)

    # ---- logica-stap ----
    def _step(self, keys):
        p = self.player
        if self.dig != 0:
            self._do_dig(self.dig)
            self.dig = 0
        else:
            self._move_player(keys)
        self._gravity(p)
        # goud
        if self.grid[p["r"]][p["c"]] == "$":
            self.grid[p["r"]][p["c"]] = " "
            self.gold -= 1
            self.play_sfx("gold")
        # ontsnappen
        if self.gold <= 0 and p["r"] <= 0:
            self._level_done()
            return
        # bewakers
        self.gtick = (self.gtick + 1) % 2
        for g in self.guards:
            if self.gtick == 0:
                self._guard_ai(g)
            self._gravity(g)
        self._update_holes()
        for g in self.guards:
            if g["r"] == p["r"] and g["c"] == p["c"]:
                self._player_die()
                return

    def _move_player(self, keys):
        p = self.player
        r, c = p["r"], p["c"]
        up = keys[pygame.K_UP]
        dn = keys[pygame.K_DOWN]
        lf = keys[pygame.K_LEFT]
        rt = keys[pygame.K_RIGHT]
        if up and self._ladder(r, c) and not self._solid(r - 1, c):
            p["r"] -= 1
        elif dn and (self._ladder(r, c) or self._ladder(r + 1, c) or self._bar(r, c)) \
                and not self._solid(r + 1, c):
            p["r"] += 1
        elif lf and not self._solid(r, c - 1):
            p["c"] -= 1
        elif rt and not self._solid(r, c + 1):
            p["c"] += 1

    def _gravity(self, e):
        r, c = e["r"], e["c"]
        if self._ladder(r, c) or self._bar(r, c):
            return
        support = (r + 1 >= self.rows or self._solid(r + 1, c)
                   or self._ladder(r + 1, c) or self._bar(r + 1, c))
        if not support:
            e["r"] += 1

    def _guard_ai(self, g):
        if self._in_hole(g["r"], g["c"]):
            return                                  # gevangen tot het gat dichtgaat
        p = self.player
        r, c = g["r"], g["c"]
        if self._ladder(r, c):
            if p["r"] < r and not self._solid(r - 1, c):
                g["r"] -= 1
                return
            if p["r"] > r and not self._solid(r + 1, c):
                g["r"] += 1
                return
        if p["r"] > r and self._ladder(r + 1, c) and not self._solid(r + 1, c):
            g["r"] += 1
            return
        if p["c"] < c and not self._solid(r, c - 1):
            g["c"] -= 1
        elif p["c"] > c and not self._solid(r, c + 1):
            g["c"] += 1

    def _do_dig(self, dirn):
        p = self.player
        r2, c2 = p["r"] + 1, p["c"] + dirn
        if 0 <= c2 < self.cols and 0 <= r2 < self.rows \
                and self.grid[r2][c2] == "#" and not self._solid(p["r"], c2):
            self.grid[r2][c2] = " "
            self.holes.append({"r": r2, "c": c2, "t": HOLE_TIME})
            self.play_sfx("dig")

    def _update_holes(self):
        for h in self.holes[:]:
            h["t"] -= SIM
            if h["t"] <= 0:
                for g in self.guards:
                    if g["r"] == h["r"] and g["c"] == h["c"]:
                        self._guard_die(g)
                if self.player["r"] == h["r"] and self.player["c"] == h["c"]:
                    self._player_die()
                self.grid[h["r"]][h["c"]] = "#"
                self.holes.remove(h)

    def _guard_die(self, g):
        g["r"], g["c"] = g["sr"], g["sc"]

    def _player_die(self):
        self.play_sfx("die")
        self.lives -= 1
        if self.lives <= 0:
            self.state = OVER
            self._music(False)
        else:
            self.player = {"r": self.pstart[0], "c": self.pstart[1]}

    def _level_done(self):
        self.play_sfx("win")
        if self.level_i + 1 < len(LEVELS):
            self.level_i += 1
            self.load_level(self.level_i)
        else:
            self.state = WIN
            self._music(False)

    # ---- tekenen ----
    def _cell_rect(self, r, c):
        return pygame.Rect(self.ox + c * self.ts, self.oy + r * self.ts,
                           self.ts, self.ts)

    def draw_play(self):
        s = self.screen
        s.fill(BG)
        ts = self.ts
        for r in range(self.rows):
            for c in range(self.cols):
                ch = self.grid[r][c]
                x, y = self.ox + c * ts, self.oy + r * ts
                if ch == "#":
                    pygame.draw.rect(s, BRICK, (x, y, ts, ts))
                    pygame.draw.line(s, MORTAR, (x, y), (x + ts, y), 1)
                    pygame.draw.line(s, MORTAR, (x, y + ts // 2),
                                     (x + ts, y + ts // 2), 1)
                    pygame.draw.line(s, MORTAR, (x + ts // 2, y),
                                     (x + ts // 2, y + ts // 2), 1)
                    pygame.draw.line(s, MORTAR, (x + ts // 4, y + ts // 2),
                                     (x + ts // 4, y + ts), 1)
                elif ch == "=":
                    pygame.draw.rect(s, STONE, (x, y, ts, ts))
                    pygame.draw.rect(s, (70, 74, 88), (x, y, ts, ts), 1)
                elif ch == "H":
                    pygame.draw.line(s, LAD, (x + 6, y), (x + 6, y + ts), 3)
                    pygame.draw.line(s, LAD, (x + ts - 6, y), (x + ts - 6, y + ts), 3)
                    for yy in range(y + 5, y + ts, 9):
                        pygame.draw.line(s, LAD, (x + 6, yy), (x + ts - 6, yy), 2)
                elif ch == "-":
                    pygame.draw.line(s, BARC, (x, y + 4), (x + ts, y + 4), 3)
                elif ch == "$":
                    pygame.draw.circle(s, GOLDC, (x + ts // 2, y + ts // 2),
                                       max(4, ts // 4))
                    pygame.draw.circle(s, (180, 140, 30),
                                       (x + ts // 2, y + ts // 2), max(4, ts // 4), 1)
        # bewakers
        for g in self.guards:
            self._draw_runner(g["c"], g["r"], GCOL)
        # speler
        self._draw_runner(self.player["c"], self.player["r"], PCOL)
        self.draw_hud()
        self._banner(T("help"))
        if self.paused:
            self.draw_pause()

    def _draw_runner(self, c, r, col):
        x = self.ox + c * self.ts
        y = self.oy + r * self.ts
        ts = self.ts
        pygame.draw.rect(self.screen, col, (x + ts // 3, y + ts // 3,
                                            ts // 3, ts // 2), border_radius=2)
        pygame.draw.circle(self.screen, col, (x + ts // 2, y + ts // 4), max(3, ts // 6))

    def draw_hud(self):
        s = self.screen
        f = self.small
        pygame.draw.rect(s, (8, 10, 16), (0, 0, W, HUD))
        s.blit(f.render("%s: %d" % (T("gold"), self.gold), True, GOLDC), (14, 8))
        s.blit(f.render("%s: %d" % (T("lives"), self.lives), True, TEXT), (14, 30))
        s.blit(f.render("%s: %d" % (T("level"), self.level_i + 1), True, TEXT), (150, 8))
        astr = T("off") if self.muted else ("%d%%" % int(self.volume * 100))
        s.blit(f.render(T("sound") + ": " + astr, True, SUB), (150, 30))

    def _banner(self, text):
        b = self.small.render(text, True, SUB)
        self.screen.blit(b, (W / 2 - b.get_width() / 2, H - 24))

    def draw_pause(self):
        s = self.screen
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        s.blit(ov, (0, 0))
        t = self.big.render(T("paused"), True, GOLDC)
        s.blit(t, (W / 2 - t.get_width() / 2, H / 2 - 50))
        r = self.font.render(T("resume"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, H / 2 + 20))

    def _draw_link(self, text, cx, cy, font, color=(120, 200, 255)):
        r = font.render(text, True, color)
        rect = r.get_rect(center=(cx, cy))
        self.screen.blit(r, rect)
        pygame.draw.line(self.screen, color, (rect.left, rect.bottom + 1),
                         (rect.right, rect.bottom + 1), 1)
        self.link_rects.append((rect, DONATE))

    def draw_menu(self):
        s = self.screen
        s.fill(BG)
        title = self.big.render("DraveRunner", True, GOLDC)
        s.blit(title, (W / 2 - title.get_width() / 2, 120))
        sub = self.mid.render(T("sub"), True, TEXT)
        s.blit(sub, (W / 2 - sub.get_width() / 2, 190))
        self._draw_runner_xy(W / 2 - 10, 280, PCOL, 3)
        st = self.font.render(T("start"), True, TEXT)
        s.blit(st, (W / 2 - st.get_width() / 2, 360))
        for i, key in enumerate(("help", "help2", "audio_hint")):
            h = self.small.render(T(key), True, SUB)
            s.blit(h, (W / 2 - h.get_width() / 2, 410 + i * 22))
        lbl = self.small.render("Donationware  -  ", True, (150, 200, 160))
        full_w = lbl.get_width() + self.small.size(DONATE)[0]
        s.blit(lbl, (W / 2 - full_w / 2, H - 44))
        self._draw_link(DONATE, W / 2 - full_w / 2 + lbl.get_width()
                        + self.small.size(DONATE)[0] / 2, H - 44 + 8, self.small)

    def _draw_runner_xy(self, x, y, col, scale=1):
        pygame.draw.rect(self.screen, col, (x, y, 20 * scale, 30 * scale),
                         border_radius=3)
        pygame.draw.circle(self.screen, col, (int(x + 10 * scale), int(y - 6 * scale)),
                           7 * scale)

    def draw_over(self):
        s = self.screen
        s.fill((20, 10, 14))
        t = self.big.render(T("over"), True, GCOL)
        s.blit(t, (W / 2 - t.get_width() / 2, 210))
        r = self.font.render(T("restart"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, 320))

    def draw_win(self):
        s = self.screen
        s.fill((10, 20, 16))
        t = self.big.render(T("win"), True, GOLDC)
        s.blit(t, (W / 2 - t.get_width() / 2, 210))
        r = self.font.render(T("restart"), True, SUB)
        s.blit(r, (W / 2 - r.get_width() / 2, 320))

    def draw_info(self):
        s = self.screen
        s.fill(BG)
        t = self.big.render(T("info"), True, GOLDC)
        s.blit(t, (W / 2 - t.get_width() / 2, 70))
        lines = [
            "DraveRunner - Dravenlock",
            "",
            T("help"),
            T("help2"),
            "",
            T("donation"),
            DONATE,
            CONTACT,
        ]
        y = 170
        for ln in lines:
            if ln == DONATE:
                self._draw_link(ln, W / 2, y + 12, self.font)
            else:
                r = self.font.render(ln, True, TEXT if ln else SUB)
                s.blit(r, (W / 2 - r.get_width() / 2, y))
            y += 34
        b = self.small.render(T("back"), True, SUB)
        s.blit(b, (W / 2 - b.get_width() / 2, H - 40))

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
                    if e.key == pygame.K_m:
                        self.toggle_mute()
                    elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.set_volume(-0.1)
                    elif e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        self.set_volume(0.1)
                    elif e.key == pygame.K_d:
                        try:
                            webbrowser.open(DONATE)
                        except Exception:
                            pass
                    if self.state == MENU:
                        if e.key == pygame.K_SPACE:
                            self.level_i = 0
                            self.lives = LIVES0
                            self.load_level(0)
                            self.state = PLAY
                        elif e.key == pygame.K_i:
                            self.state = INFO
                    elif self.state == INFO:
                        self.state = MENU
                    elif self.state == PLAY:
                        if e.key == pygame.K_p:
                            self.paused = not self.paused
                        elif e.key in (pygame.K_z, pygame.K_COMMA):
                            self.dig = -1
                        elif e.key in (pygame.K_x, pygame.K_PERIOD):
                            self.dig = 1
                    elif self.state in (OVER, WIN) and e.key == pygame.K_r:
                        self.state = MENU
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for rect, url in self.link_rects:
                        if rect.collidepoint(e.pos):
                            try:
                                webbrowser.open(url)
                            except Exception:
                                pass
            keys = pygame.key.get_pressed()
            self._music(self.state == PLAY and not self.paused)
            if self.state == PLAY and not self.paused:
                self.sim_acc += dt
                steps = 0
                while self.sim_acc >= SIM and steps < 4:
                    self.sim_acc -= SIM
                    steps += 1
                    self._step(keys)
                    if self.state != PLAY:
                        break

            self.link_rects = []
            if self.state == MENU:
                self.draw_menu()
            elif self.state == INFO:
                self.draw_info()
            elif self.state == PLAY:
                self.draw_play()
            elif self.state == OVER:
                self.draw_over()
            elif self.state == WIN:
                self.draw_win()
            mp = pygame.mouse.get_pos()
            over = any(rect.collidepoint(mp) for rect, _ in self.link_rects)
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if over
                                        else pygame.SYSTEM_CURSOR_ARROW)
            except Exception:
                pass
            pygame.display.flip()


def main():
    Game().run()


if __name__ == "__main__":
    main()

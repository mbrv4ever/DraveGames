# -*- coding: utf-8 -*-
"""DraveKarate - 2D een-tegen-een karate op timing (Dravenlock).

Toernooiladder: versla steeds sterkere vechters (wit -> zwart band).
Besturing (geen WASD+muis):
  Pijltjes links/rechts = lopen (naar/van tegenstander)
  Pijl omhoog = springen        Pijl omlaag = bukken
  Achteruit vasthouden = dekken (staand dekt mid/hoog, gebukt dekt laag/mid)
  Z = stoot (kort bereik)       X = trap (lang bereik)
  Hoog/laag mikken: staand = mid, gebukt = laag, in de sprong = hoog.
Portable (cache/), tweetalig NL/EN, procedurele audio. Donationware.
"""
import os
import sys
import math
import json
import locale
import random
import array

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame


# ---------------------------------------------------------------- paden
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def cache_dir():
    d = os.path.join(app_dir(), "cache")
    os.makedirs(d, exist_ok=True)
    return d


SCORE_PATH = os.path.join(cache_dir(), "score.json")


# ---------------------------------------------------------------- taal
def is_nl():
    try:
        lang = (locale.getdefaultlocale()[0] or "").lower()
    except Exception:
        lang = ""
    return lang.startswith("nl")


NL = is_nl()
TX = {
    "title": ("DraveKarate", "DraveKarate"),
    "sub": ("Karate op timing - beklim de toernooiladder",
            "Timing karate - climb the tournament ladder"),
    "start": ("Klik of Enter = start toernooi", "Click or Enter = start tournament"),
    "controls": ("Pijltjes = bewegen   Muisklik: links = stoot, rechts = trap",
                 "Arrows = move   Mouse: left = punch, right = kick"),
    "hint_hilo": ("Naar achteren lopen = automatisch dekken. (Ook Z = stoot, X = trap.)",
                  "Walk backward = auto-block. (Also Z = punch, X = kick.)"),
    "belt": ("Band", "Belt"),
    "opp": ("Tegenstander", "Opponent"),
    "you": ("JIJ", "YOU"),
    "ready": ("KLAAR?", "READY?"),
    "fight": ("VECHTEN!", "FIGHT!"),
    "ko": ("K.O.!", "K.O.!"),
    "you_win": ("Gewonnen!", "You win!"),
    "you_lose": ("Verloren...", "You lose..."),
    "champion": ("KAMPIOEN! Je versloeg iedereen!",
                 "CHAMPION! You beat them all!"),
    "next": ("Klik = volgende gevecht", "Click = next fight"),
    "retry": ("Klik = opnieuw   Esc = menu", "Click = retry   Esc = menu"),
    "menu": ("Esc = menu", "Esc = menu"),
    "paused": ("PAUZE", "PAUSED"),
    "resume": ("Enter = verder", "Enter = resume"),
    "record": ("Verste band", "Best belt"),
    "newrec": ("NIEUW RECORD!", "NEW RECORD!"),
    "donate": ("Doneren: paypal.me/roger076  -  service@dravenlock.nl",
               "Donate: paypal.me/roger076  -  service@dravenlock.nl"),
    "defeated": ("verslagen", "defeated"),
}


def T(k):
    v = TX.get(k, (k, k))
    return v[0] if NL else v[1]


# ---------------------------------------------------------------- kleuren
C_SKY_TOP = (46, 34, 66)
C_SKY_BOT = (28, 22, 40)
C_FLOOR = (74, 58, 40)
C_FLOOR2 = (60, 46, 32)
C_MAT = (120, 70, 66)
C_TEXT = (238, 236, 246)
C_DIM = (172, 166, 198)
C_ACCENT = (181, 156, 255)
C_PANEL = (22, 19, 31)
C_PANEL2 = (34, 29, 50)
C_HP = (90, 200, 120)
C_HP_LOW = (230, 90, 90)
C_HP_BG = (52, 48, 62)
C_GI = (238, 238, 244)
C_GI_SHADE = (205, 205, 216)
C_SKIN = (232, 190, 158)

WIDTH, HEIGHT = 1200, 720
GROUND_Y = 600
FPS = 60

# banden-ladder (naam NL/EN, gi-band-kleur, moeilijkheid)
LADDER = [
    ("Witte band", "White belt", (245, 245, 245), 0.30),
    ("Gele band", "Yellow belt", (240, 210, 70), 0.45),
    ("Oranje band", "Orange belt", (240, 150, 60), 0.58),
    ("Groene band", "Green belt", (90, 190, 100), 0.70),
    ("Blauwe band", "Blue belt", (80, 150, 240), 0.82),
    ("Bruine band", "Brown belt", (150, 100, 60), 0.92),
    ("Zwarte band", "Zwarte band", (40, 40, 48), 1.0),
]


def belt_name(i):
    n = LADDER[i]
    return n[0] if NL else n[1]


# ---------------------------------------------------------------- aanvallen
# (startup, active, recovery, bereik, schade)
ATK = {
    "punch": (6, 4, 8, 118, 8),
    "kick": (10, 6, 15, 165, 13),
}
HITSTUN = 20
BLOCKSTUN = 10
KO_HEALTH = 100


class Fighter:
    def __init__(self, x, facing, gi_belt, is_player=False, skill=0.5,
                 gi_main=(235, 235, 240)):
        self.x = float(x)
        self.y = 0.0            # hoogte boven de grond (spring)
        self.vy = 0.0
        self.facing = facing    # 1 = kijkt naar rechts, -1 naar links
        self.gi_belt = gi_belt
        self.gi_main = gi_main   # kleur van de gi (jas + broek)
        self.is_player = is_player
        self.skill = skill
        self.health = KO_HEALTH
        self.state = "idle"
        self.crouch = False
        self.blocking = False
        self.block_low = False
        # aanval
        self.atk = None
        self.atk_t = 0
        self.atk_hit = False
        self.hitstun = 0
        self.walk_phase = 0.0
        self.anim = 0.0
        # AI
        self.ai_t = 0.0
        self.ai_plan = "idle"
        self.win_pose = False

    # -- afgeleiden --
    @property
    def on_ground(self):
        return self.y <= 0.001

    def height_of_attack(self):
        if self.y > 6:
            return "high"
        if self.crouch:
            return "low"
        return "mid"

    def can_act(self):
        return self.hitstun <= 0 and self.atk is None and self.state != "ko"

    def start_attack(self, kind):
        if not self.can_act():
            return
        self.atk = kind
        self.atk_t = 0
        self.atk_hit = False
        self.state = kind

    def phase(self):
        """('startup'|'active'|'recovery'|None, resterende frames)"""
        if not self.atk:
            return None, 0
        s, a, r, _, _ = ATK[self.atk]
        t = self.atk_t
        if t < s:
            return "startup", s - t
        if t < s + a:
            return "active", s + a - t
        if t < s + a + r:
            return "recovery", s + a + r - t
        return None, 0


class Audio:
    def __init__(self):
        self.ok = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.ok = True
        except Exception:
            self.ok = False
        self.music_chan = None
        self.tracks = []
        self.menu_track = None
        self.cur_music = None
        if self.ok:
            self.whoosh = self._whoosh()
            self.thud = self._thud()
            self.block = self._click()
            self.bell = self._chime()
            self.beep = self._tone(680, 0.09, 0.3)
            try:
                pygame.mixer.set_num_channels(8)
                pygame.mixer.set_reserved(1)          # kanaal 0 = muziek
                self.music_chan = pygame.mixer.Channel(0)
            except Exception:
                self.music_chan = None
            self._build_music()

    def _snd(self, samples):
        return pygame.mixer.Sound(buffer=array.array("h", samples).tobytes())

    # ------- muziek (procedureel, chiptune) -------
    def _track(self, seq, bass, bpm=128, duty=0.5, vol=0.13):
        """seq/bass = lijsten halve-tonen t.o.v. A4 (None = rust). Achtste noten."""
        rate = 22050
        step = (60.0 / bpm) / 2.0
        n = int(rate * step)
        out = []
        for i, semi in enumerate(seq):
            broot = bass[i % len(bass)] if bass else None
            for k in range(n):
                t = k / rate
                env = 0.15 + 0.85 * max(0.0, 1 - (k / n))    # pluk-envelope
                s = 0.0
                if semi is not None:
                    f = 440.0 * (2.0 ** (semi / 12.0))
                    ph = (f * t) % 1.0
                    s += (0.5 if ph < duty else -0.5)
                if broot is not None:
                    fb = 440.0 * (2.0 ** ((broot - 24) / 12.0))
                    s += math.sin(2 * math.pi * fb * t) * 0.45
                out.append(int(max(-1.0, min(1.0, s)) * env * vol * 32767))
        return self._snd(out)

    def _build_music(self):
        try:
            # menu: rustig, mineur-pentatonisch, langzaam
            m = [0, 3, 7, 3, 5, 3, 0, None, -2, 0, 3, 0, 2, 0, -2, None]
            mb = [0, 7, 5, 3]
            self.menu_track = self._track(m, mb, bpm=98, duty=0.5, vol=0.11)
            # gevechtsdeuntjes (3 varianten, feller, verschillende toonaard/patroon)
            t1s = [0, 0, 7, 0, 5, 3, 5, 7, 8, 7, 5, 3, 0, 3, 5, 0]
            t1b = [0, 0, 5, 7]
            t2s = [2, 5, 9, 5, 7, 5, 2, 5, 10, 9, 7, 5, 2, 7, 5, 2]
            t2b = [2, 2, 7, 9]
            t3s = [-3, 4, 7, 4, 9, 7, 4, 0, 2, 4, 7, 9, 7, 4, 2, 0]
            t3b = [-3, 4, 0, -3]
            self.tracks = [
                self._track(t1s, t1b, bpm=138, duty=0.5, vol=0.12),
                self._track(t2s, t2b, bpm=150, duty=0.35, vol=0.12),
                self._track(t3s, t3b, bpm=132, duty=0.5, vol=0.12),
            ]
        except Exception:
            self.tracks = []
            self.menu_track = None

    def play_music(self, snd):
        if not (self.ok and self.music_chan and snd):
            return
        if self.cur_music is snd:
            return
        self.cur_music = snd
        try:
            self.music_chan.play(snd, loops=-1)
        except Exception:
            pass

    def menu_music(self):
        self.play_music(self.menu_track)

    def fight_music(self, level):
        if self.tracks:
            self.play_music(self.tracks[level % len(self.tracks)])

    def stop_music(self):
        self.cur_music = None
        if self.music_chan:
            try:
                self.music_chan.stop()
            except Exception:
                pass

    def _tone(self, f, dur, vol=0.4):
        rate = 22050
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = min(1.0, t * 40) * max(0.0, 1 - t / dur)
            out.append(int(math.sin(2 * math.pi * f * t) * env * vol * 32767))
        return self._snd(out)

    def _whoosh(self):
        rate = 22050
        dur = 0.16
        n = int(rate * dur)
        out = []
        seed = 12345
        for i in range(n):
            t = i / rate
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            noise = (seed / 0x7fffffff) * 2 - 1
            env = max(0.0, 1 - t / dur)
            f = 1.0 - t / dur
            out.append(int(noise * env * env * 0.25 * 32767 * (0.4 + f)))
        return self._snd(out)

    def _thud(self):
        rate = 22050
        dur = 0.14
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = max(0.0, 1 - t / dur)
            s = math.sin(2 * math.pi * (150 - 400 * t) * t)
            out.append(int(s * env * 0.5 * 32767))
        return self._snd(out)

    def _click(self):
        rate = 22050
        out = []
        for f, dur in ((900, 0.03), (1400, 0.04)):
            n = int(rate * dur)
            for i in range(n):
                t = i / rate
                env = max(0.0, 1 - t / dur)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.3 * 32767))
        return self._snd(out)

    def _chime(self):
        rate = 22050
        out = []
        for f, dur in ((523, 0.12), (784, 0.12), (1046, 0.2)):
            n = int(rate * dur)
            for i in range(n):
                t = i / rate
                env = min(1.0, t * 30) * max(0.0, 1 - t / dur)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.32 * 32767))
        return self._snd(out)

    def play(self, s):
        if self.ok and s:
            try:
                s.play()
            except Exception:
                pass


# ---------------------------------------------------------------- tekenen vechter
def _darker(c, fct=0.68):
    return (int(c[0] * fct), int(c[1] * fct), int(c[2] * fct))


def _leg(surf, gi, gid, skin, hip, knee, foot, big=False):
    pygame.draw.line(surf, gi, hip, knee, 22)       # dij (broek)
    pygame.draw.line(surf, gid, hip, knee, 4)
    pygame.draw.line(surf, gi, knee, foot, 18)      # scheen (broek)
    pygame.draw.circle(surf, gi, (int(knee[0]), int(knee[1])), 11)
    pygame.draw.circle(surf, skin, (int(foot[0]), int(foot[1])), 11 if big else 10)
    pygame.draw.circle(surf, (26, 26, 32), (int(foot[0]), int(foot[1])),
                       11 if big else 10, 2)


def draw_fighter(surf, f):
    """Getekende karateka (groot): kop met haar+hoofdband, open gi, blote
    onderarmen + vuisten, gi-broek, vechthouding met poses."""
    cx = int(f.x)
    base = GROUND_Y - int(f.y)
    fac = f.facing
    t = f.anim
    dark = (26, 26, 32)
    gi = f.gi_main
    gid = _darker(gi)
    skin = C_SKIN
    belt = f.gi_belt

    crouch = 44 if f.crouch else 0
    lean = -16 * fac if f.state == "hit" else 0
    hip_y = base - 96 + crouch
    sh_y = base - 168 + crouch
    head_y = base - 206 + crouch
    if f.state in ("idle", "block"):
        b = int(math.sin(t * 3) * 2)
        sh_y += b
        head_y += b
    tx = cx + lean

    # ---- benen (gi-broek, blote voeten) ----
    stance = 32
    lx, rx = cx - stance, cx + stance
    knee_y = (hip_y + base) // 2
    if f.atk == "kick":
        ph, _ = f.phase()
        ext = 1.0 if ph == "active" else (0.55 if ph == "startup" else 0.35)
        h = f.height_of_attack()
        ky = base - 96 if h == "high" else base - 58
        if h == "low":
            ky = base - 20
        foot = (cx + fac * int(120 * ext), ky)
        back = (lx if fac > 0 else rx, base)
        _leg(surf, gi, gid, skin, (cx, hip_y), (back[0], knee_y), back)
        _leg(surf, gi, gid, skin, (cx, hip_y),
             (cx + fac * 44, (hip_y + ky) // 2), foot, big=True)
    else:
        sw = math.sin(t * 12) * 16 if f.state == "walk" else 0
        _leg(surf, gi, gid, skin, (cx, hip_y), (lx, knee_y), (lx + int(sw), base))
        _leg(surf, gi, gid, skin, (cx, hip_y), (rx, knee_y), (rx - int(sw), base))

    # ---- torso (gi-jas met open V, skin borst) ----
    torso = [(tx - 32, hip_y), (tx + 32, hip_y), (tx + 26, sh_y), (tx - 26, sh_y)]
    pygame.draw.polygon(surf, gi, torso)
    pygame.draw.polygon(surf, dark, torso, 3)
    # borst-V (huid)
    pygame.draw.polygon(surf, skin, [(tx, hip_y - 8), (tx - 16, sh_y), (tx + 16, sh_y)])
    pygame.draw.line(surf, gid, (tx - 16, sh_y), (tx, hip_y - 8), 5)
    pygame.draw.line(surf, gid, (tx + 16, sh_y), (tx, hip_y - 8), 5)
    # band + knoop + slippen
    pygame.draw.rect(surf, belt, (tx - 32, hip_y - 16, 64, 13), border_radius=2)
    pygame.draw.rect(surf, dark, (tx - 32, hip_y - 16, 64, 13), 2, border_radius=2)
    pygame.draw.circle(surf, belt, (tx - fac * 8, hip_y - 9), 7)
    pygame.draw.rect(surf, belt, (tx - fac * 12, hip_y - 3, 8, 26), border_radius=2)
    pygame.draw.rect(surf, belt, (tx - fac * 2, hip_y - 3, 8, 22), border_radius=2)

    # ---- nek ----
    hx = tx + fac * 6
    pygame.draw.line(surf, skin, (tx, sh_y + 2), (hx, head_y + 14), 14)
    pygame.draw.line(surf, _darker(skin, 0.9), (tx, sh_y + 2), (hx, head_y + 14), 3)

    # ---- hoofd ----
    pygame.draw.circle(surf, skin, (hx, head_y), 20)
    pygame.draw.circle(surf, dark, (hx, head_y), 20, 2)
    # haar (bovenkant)
    pygame.draw.arc(surf, dark, (hx - 21, head_y - 24, 42, 36), 0.15, math.pi - 0.15, 10)
    # hoofdband (Dravenlock-paars) + wapperende slip naar achteren
    pygame.draw.rect(surf, C_ACCENT, (hx - 20, head_y - 9, 40, 8))
    pygame.draw.line(surf, C_ACCENT, (hx - fac * 20, head_y - 5),
                     (hx - fac * 34, head_y + 3), 5)
    # gezicht: wenkbrauw (fel) + oog
    pygame.draw.line(surf, dark, (hx + fac * 2, head_y - 3),
                     (hx + fac * 14, head_y - 1), 3)
    pygame.draw.circle(surf, dark, (hx + fac * 9, head_y + 4), 2)

    # ---- armen ----
    def arm(shoulder, elbow, hand, fist=11):
        pygame.draw.line(surf, gi, shoulder, elbow, 17)     # bovenarm (mouw)
        pygame.draw.line(surf, gid, shoulder, elbow, 3)
        pygame.draw.line(surf, skin, elbow, hand, 13)       # onderarm (bloot)
        pygame.draw.circle(surf, skin, (int(hand[0]), int(hand[1])), fist)  # vuist
        pygame.draw.circle(surf, dark, (int(hand[0]), int(hand[1])), fist, 2)

    sh_f = (tx + fac * 24, sh_y + 6)
    sh_b = (tx - fac * 18, sh_y + 6)
    if f.state == "block":
        # voorarm verticaal voor het gezicht (garde hoog)
        arm(sh_f, (tx + fac * 26, sh_y + 24), (tx + fac * 20, sh_y - 22), 12)
        arm(sh_b, (tx - fac * 12, sh_y + 26), (tx - fac * 2, sh_y + 10))
    elif f.atk == "punch":
        ph, _ = f.phase()
        ext = 1.0 if ph == "active" else (0.55 if ph == "startup" else 0.35)
        h = f.height_of_attack()
        hy = sh_y + (30 if h == "low" else 0)
        hand = (int(tx + fac * (34 + 78 * ext)), hy)
        arm(sh_f, (int(tx + fac * (24 + 44 * ext)), hy), hand, 12)
        arm(sh_b, (tx - fac * 10, sh_y + 22), (tx - fac * 2, sh_y + 6))
    else:
        # vechthouding: beide vuisten omhoog bij het gezicht
        arm(sh_f, (tx + fac * 26, sh_y + 20), (tx + fac * 20, sh_y - 12))
        arm(sh_b, (tx - fac * 14, sh_y + 20), (tx + fac * 3, sh_y - 6))


# ---------------------------------------------------------------- game
class Game:
    def __init__(self):
        pygame.init()
        try:
            ic = os.path.join(app_dir(), "assets", "icon.png")
            if os.path.exists(ic):
                pygame.display.set_icon(pygame.image.load(ic))
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("DraveKarate")
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arial", 76, bold=True)
        self.mid = pygame.font.SysFont("arial", 42, bold=True)
        self.font = pygame.font.SysFont("consolas,arial", 30, bold=True)
        self.small = pygame.font.SysFont("consolas,arial", 23)
        self.audio = Audio()
        self.scores = self._load()
        self.state = "menu"
        self.level = 0
        self.pending = None
        self.msg = ""
        self.msg_t = 0.0
        self._bg = self._make_bg()
        self.reset_match(0)
        self.audio.menu_music()

    def _load(self):
        try:
            with open(SCORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):
        try:
            with open(SCORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except Exception:
            pass

    def _make_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            c = [int(C_SKY_TOP[i] + (C_SKY_BOT[i] - C_SKY_TOP[i]) * t) for i in range(3)]
            pygame.draw.line(bg, c, (0, y), (WIDTH, y))
        # vloer
        pygame.draw.rect(bg, C_FLOOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(bg, C_MAT, (60, GROUND_Y, WIDTH - 120, 12))
        for x in range(0, WIDTH, 60):
            pygame.draw.line(bg, C_FLOOR2, (x, GROUND_Y + 14), (x, HEIGHT), 2)
        # dojo-banners
        for bx in (180, WIDTH - 180):
            pygame.draw.rect(bg, C_PANEL2, (bx - 34, 40, 68, 150), border_radius=8)
            pygame.draw.circle(bg, C_ACCENT, (bx, 110), 26, 4)
        return bg

    def reset_match(self, level):
        self.level = level
        skill = LADDER[level][3]
        self.p = Fighter(WIDTH * 0.32, 1, (40, 40, 48), is_player=True,
                         gi_main=(236, 236, 242))          # speler: witte gi
        self.e = Fighter(WIDTH * 0.68, -1, LADDER[level][2], skill=skill,
                         gi_main=(200, 74, 68))            # tegenstander: rode gi
        self.pending = None
        self.round_state = "ready"     # ready -> fight -> over
        self.round_timer = 1.4
        self.over_timer = 0.0
        self.win = None
        self.result_shown = False

    # ---- lus ----
    def run(self, selftest=0):
        running = True
        frames = 0
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    self.on_key(ev.key)
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    self.on_mouse(ev.button)
            keys = pygame.key.get_pressed()
            if self.state == "fight":
                self.update(dt, keys, selftest)
            self.draw()
            if self.msg_t > 0:
                self.msg_t -= dt
            frames += 1
            if selftest and frames >= selftest:
                try:
                    out = os.path.join(app_dir(), "voorbeeld.png")
                    pygame.image.save(self.screen, out)
                    print("SELFTEST OK ->", out)
                except Exception as e:
                    print("SELFTEST render-fout:", e)
                running = False
        pygame.quit()

    def on_key(self, key):
        if self.state == "menu":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.reset_match(0)
                self.state = "fight"
                self.audio.fight_music(0)
            elif key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == "fight":
            if key == pygame.K_ESCAPE:
                self.state = "paused"
            elif self.round_state == "over" and key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._advance()
        elif self.state == "paused":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "fight"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
                self.audio.menu_music()

    def on_mouse(self, button):
        if self.state == "menu":
            self.reset_match(0)
            self.state = "fight"
            self.audio.fight_music(0)
        elif self.state == "fight":
            if self.round_state == "over":
                self._advance()
            elif self.round_state == "fight":
                if button == 1:
                    self.pending = "punch"
                elif button == 3:
                    self.pending = "kick"
        elif self.state == "paused":
            self.state = "fight"

    def _advance(self):
        if self.win == "player":
            # record bijwerken
            best = self.scores.get("best_belt", -1)
            if self.level > best:
                self.scores["best_belt"] = self.level
                self._save()
            if self.level + 1 < len(LADDER):
                self.reset_match(self.level + 1)
                self.state = "fight"
                self.audio.fight_music(self.level)
            else:
                self.scores["best_belt"] = len(LADDER) - 1
                self._save()
                self.state = "menu"
                self.audio.menu_music()
        else:
            self.state = "menu"
            self.audio.menu_music()

    # ---- update ----
    def update(self, dt, keys, selftest=0):
        if self.round_state == "ready":
            self.round_timer -= dt
            if self.round_timer <= 0:
                self.round_state = "fight"
                self.flash(T("fight"))
                self.audio.play(self.audio.beep)
            return
        if self.round_state == "over":
            return

        # facing bijwerken
        self.p.facing = 1 if self.e.x >= self.p.x else -1
        self.e.facing = 1 if self.p.x >= self.e.x else -1

        self._control_player(dt, keys)
        self._ai(dt)
        for f in (self.p, self.e):
            self._physics(f, dt)
        self._resolve(self.p, self.e)
        self._resolve(self.e, self.p)

        # KO?
        for atk, dfn, who in ((self.p, self.e, "player"), (self.e, self.p, "enemy")):
            if dfn.health <= 0 and self.round_state == "fight":
                dfn.health = 0
                dfn.state = "ko"
                atk.win_pose = True
                self.round_state = "over"
                self.win = who
                self.audio.play(self.audio.bell)
                self.flash(T("ko"))

    def _control_player(self, dt, keys):
        # Bewegen met PIJLTJES (links/rechts). Naar achteren = automatisch dekken.
        # Aanvallen: muisklik (links=stoot, rechts=trap) of Z/X.
        p = self.p
        if p.state == "ko":
            return
        p.crouch = False
        p.block_low = False
        away = -p.facing
        move = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
        retreating = (move != 0 and move == away)
        p.blocking = retreating and p.atk is None and p.hitstun <= 0
        # aanval: muisklik (self.pending) of toetsen Z/X
        atk = self.pending
        if atk is None and p.can_act():
            if keys[pygame.K_z]:
                atk = "punch"
            elif keys[pygame.K_x]:
                atk = "kick"
        if atk and p.can_act():
            p.start_attack(atk)
            self.audio.play(self.audio.whoosh)
        self.pending = None
        # lopen (niet tijdens aanval/hitstun/dekken)
        if p.can_act() and move != 0 and not p.blocking:
            p.x += move * 240 * dt
            p.state = "walk"
        elif p.atk is None and p.hitstun <= 0:
            p.state = "block" if p.blocking else "idle"

    def _ai(self, dt):
        e = self.e
        p = self.p
        if e.state == "ko":
            return
        dist = abs(e.x - p.x)
        sk = e.skill
        e.ai_t -= dt
        # standaard: richting speler draaien al gedaan
        e.crouch = False
        e.blocking = False
        # reageren op speler-aanval: dekken (kans schaalt met skill)
        p_ph, _ = p.phase()
        if p_ph in ("startup", "active") and dist < 150 and e.can_act():
            if random.random() < 0.25 + 0.6 * sk:
                e.blocking = True
                # dek de juiste hoogte afhankelijk van speler-aanval
                e.block_low = (p.height_of_attack() == "low")
                e.crouch = e.block_low
                e.state = "block"
                return
        if e.ai_t > 0:
            # bezig met huidig plan
            pass
        else:
            r = random.random()
            if dist > ATK["kick"][3] - 10:
                e.ai_plan = "approach"
            elif r < 0.4 + 0.4 * sk:
                e.ai_plan = "attack"
            elif r < 0.7:
                e.ai_plan = "approach"
            else:
                e.ai_plan = "retreat"
            e.ai_t = random.uniform(0.25, 0.7) * (1.3 - 0.5 * sk)

        spd = (120 + 120 * sk)
        if e.ai_plan == "approach" and e.can_act():
            e.x += e.facing * spd * dt
            e.state = "walk"
        elif e.ai_plan == "retreat" and e.can_act():
            e.x -= e.facing * spd * 0.7 * dt
            e.state = "walk"
        elif e.ai_plan == "attack" and e.can_act():
            if dist <= ATK["punch"][3]:
                kind = "punch" if random.random() < 0.6 else "kick"
            else:
                kind = "kick"
            # soms laag of hoog mikken
            hl = random.random()
            if hl < 0.25:
                e.crouch = True   # laag
            e.start_attack(kind)
            self.audio.play(self.audio.whoosh)
            e.ai_t = random.uniform(0.3, 0.6)

    def _physics(self, f, dt):
        # sprong
        if not f.on_ground or f.vy > 0:
            f.y += f.vy
            f.vy -= 30 * dt * 2.0
            if f.y <= 0:
                f.y = 0
                f.vy = 0
        # aanval-timer
        if f.atk:
            f.atk_t += 1
            ph, _ = f.phase()
            if ph is None:
                f.atk = None
                if f.state in ("punch", "kick"):
                    f.state = "idle"
        # hitstun
        if f.hitstun > 0:
            f.hitstun -= 1
            if f.hitstun <= 0 and f.state == "hit":
                f.state = "idle"
        f.anim += dt * (10 if f.state == "walk" else 4)
        # binnen de mat houden
        f.x = max(110, min(WIDTH - 110, f.x))
        # niet door elkaar heen
        other = self.e if f is self.p else self.p
        if abs(f.x - other.x) < 98:
            mid = (f.x + other.x) / 2
            f.x = mid + (49 if f.x >= other.x else -49)
            other.x = mid + (49 if other.x > f.x else -49)

    def _resolve(self, atk, dfn):
        if atk.atk is None or atk.atk_hit:
            return
        ph, _ = atk.phase()
        if ph != "active":
            return
        rng = ATK[atk.atk][3]
        dmg = ATK[atk.atk][4]
        dist = abs(atk.x - dfn.x)
        # moet naar de tegenstander gericht zijn
        facing_ok = (dfn.x - atk.x) * atk.facing > 0
        if not facing_ok or dist > rng:
            return
        atk.atk_hit = True
        h = atk.height_of_attack()
        # blok-zones
        blocked = False
        if dfn.blocking and dfn.hitstun <= 0:
            covered = {"mid", "high"} if not dfn.block_low else {"mid", "low"}
            if h in covered:
                blocked = True
        if blocked:
            dfn.hitstun = max(dfn.hitstun, BLOCKSTUN)
            dfn.x += atk.facing * 10
            self.audio.play(self.audio.block)
        else:
            dfn.health -= dmg
            dfn.hitstun = HITSTUN
            dfn.state = "hit"
            dfn.atk = None
            dfn.x += atk.facing * 16
            self.audio.play(self.audio.thud)

    def flash(self, m):
        self.msg = m
        self.msg_t = 1.2

    # ---- tekenen ----
    def draw(self):
        s = self.screen
        if self.state == "menu":
            self.draw_menu()
        else:
            s.blit(self._bg, (0, 0))
            # schaduwen
            for f in (self.p, self.e):
                sh = pygame.Surface((110, 22), pygame.SRCALPHA)
                pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 110, 22))
                s.blit(sh, (int(f.x) - 55, GROUND_Y - 6))
            draw_fighter(s, self.e)
            draw_fighter(s, self.p)
            self.draw_hud()
            if self.round_state == "ready":
                self.center(T("ready"), C_ACCENT, -20)
            if self.round_state == "over":
                self.draw_over()
            if self.state == "paused":
                self.overlay(T("paused"), T("resume"))
            if self.msg_t > 0 and self.round_state != "over":
                self.center(self.msg, C_TEXT, -20)
        pygame.display.flip()

    def bar(self, x, y, w, val, flip=False):
        s = self.screen
        h = 30
        pygame.draw.rect(s, C_HP_BG, (x, y, w, h), border_radius=6)
        frac = max(0.0, val / KO_HEALTH)
        col = C_HP if frac > 0.3 else C_HP_LOW
        bw = int(w * frac)
        rx = x + (w - bw) if flip else x
        pygame.draw.rect(s, col, (rx, y, bw, h), border_radius=6)
        pygame.draw.rect(s, (20, 18, 28), (x, y, w, h), 3, border_radius=6)

    def draw_hud(self):
        s = self.screen
        bw = 470
        self.bar(24, 24, bw, self.p.health)
        self.bar(WIDTH - 24 - bw, 24, bw, self.e.health, flip=True)
        s.blit(self.font.render(T("you"), True, C_TEXT), (24, 60))
        er = self.font.render(belt_name(self.level), True, C_TEXT)
        s.blit(er, (WIDTH - 24 - er.get_width(), 60))
        lt = self.font.render("%s %d/%d" % (T("belt"), self.level + 1, len(LADDER)),
                              True, C_DIM)
        s.blit(lt, (WIDTH // 2 - lt.get_width() // 2, 28))

    def center(self, text, col, dy=0):
        s = self.screen
        r = self.big.render(text, True, col)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 30 + dy))

    def overlay(self, title, sub):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 170))
        s.blit(ov, (0, 0))
        self.center(title, C_ACCENT, -20)
        r = self.mid.render(sub, True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 + 40))

    def draw_over(self):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 150))
        s.blit(ov, (0, 0))
        champion = self.win == "player" and self.level + 1 >= len(LADDER)
        if champion:
            title, col = T("champion"), (250, 220, 90)
        elif self.win == "player":
            title, col = T("you_win"), C_HP
        else:
            title, col = T("you_lose"), C_HP_LOW
        r = self.big.render(title, True, col)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 70))
        sub = T("next") if self.win == "player" and not champion else T("retry")
        r2 = self.mid.render(sub, True, C_TEXT)
        s.blit(r2, (WIDTH // 2 - r2.get_width() // 2, HEIGHT // 2 + 20))

    def draw_menu(self):
        s = self.screen
        s.blit(self._bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 8, 16, 120))
        s.blit(ov, (0, 0))
        r = self.big.render(T("title"), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 60))
        r = self.font.render(T("sub"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 150))
        try:
            lp = os.path.join(app_dir(), "assets", "logo.png")
            if os.path.exists(lp):
                img = pygame.image.load(lp).convert_alpha()
                img = pygame.transform.smoothscale(img, (110, 110))
                s.blit(img, (WIDTH // 2 - 55, 195))
        except Exception:
            pass
        # bandenrij
        y = 340
        step = 58
        bx = WIDTH // 2 - (len(LADDER) * step) // 2
        best = self.scores.get("best_belt", -1)
        for i, item in enumerate(LADDER):
            col = item[2]
            rect = pygame.Rect(bx + i * step, y, 46, 46)
            pygame.draw.rect(s, col, rect, border_radius=8)
            pygame.draw.rect(s, (20, 18, 28), rect, 2, border_radius=8)
            if i <= best:
                pygame.draw.line(s, C_HP, (rect.x + 9, rect.centery),
                                 (rect.centerx - 3, rect.bottom - 10), 4)
                pygame.draw.line(s, C_HP, (rect.centerx - 3, rect.bottom - 10),
                                 (rect.right - 7, rect.y + 9), 4)
        rec = self.font.render(
            "%s: %s" % (T("record"), belt_name(best) if best >= 0 else "-"),
            True, C_ACCENT)
        s.blit(rec, (WIDTH // 2 - rec.get_width() // 2, y + 60))

        for i, line in enumerate((T("start"), T("controls"), T("hint_hilo"))):
            fnt = self.mid if i == 0 else self.font
            col = C_TEXT if i == 0 else C_DIM
            r = fnt.render(line, True, col)
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, 470 + i * 46))
        r = self.font.render(T("donate"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 40))


def main():
    selftest = 0
    if "--selftest" in sys.argv:
        try:
            selftest = int(sys.argv[sys.argv.index("--selftest") + 1])
        except Exception:
            selftest = 150
    g = Game()
    if selftest:
        g.reset_match(0)
        g.state = "fight"
        g.round_state = "fight"
    g.run(selftest=selftest)


if __name__ == "__main__":
    main()
# einde

# -*- coding: utf-8 -*-
"""beat.py - DraveBeat, een ritmespel van Dravenlock Games.

Noten vallen in vier banen naar de trefbalk. Druk de juiste toets (D, F, J, K)
of klik de baan precies op het moment dat de noot de balk raakt. Hoe strakker je
timing, hoe meer punten: Perfect, Goed of Mis. Bouw een combo op en haal een zo
hoog mogelijke accuratesse en rang. De muziek is volledig procedureel en de
noten lopen mee op de maat.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke banen/HUD; procedurele muziek en geluiden (sfx.py); gesproken
intro (neuvoice) in een apart splashvenster. Volledig draagbaar: alles wordt
bewaard in een map "DraveBeat-data" naast het programma.
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

APP_NAME = "DraveBeat"
APP_VERSION = "0.1.2"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
HUD_H = 50
LANES = 4
LANE_W = 116
LANE_AREA_W = LANES * LANE_W
LANE_X0 = (WIDTH - LANE_AREA_W) // 2
FIELD_T = HUD_H + 6
HIT_Y = HEIGHT - 116
NOTE_H = 26
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_LETTERS = ["D", "F", "J", "K"]

# timingvensters (seconden)
W_PERFECT = 0.058
W_GOOD = 0.125
W_MISS = 0.165

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
LANE_COLORS = [ACCENT, GOED, GOLD, PURPLE]

# nummers: bpm afgestemd op sfx.SONG_BPM; oplopend tempo/dichtheid
SONGS = [
    {"key": "song1", "naam_nl": "Rustig", "naam_en": "Calm", "bpm": 100, "dur": 64, "density": 0.30, "lead": 3.05, "seed": 1017, "min_gap": 0.5, "global_gap": 0.72},
    {"key": "song2", "naam_nl": "Stevig", "naam_en": "Steady", "bpm": 124, "dur": 72, "density": 0.5, "lead": 2.6, "seed": 2049, "min_gap": 0.22, "global_gap": 0.16},
    {"key": "song3", "naam_nl": "Snel", "naam_en": "Fast", "bpm": 140, "dur": 80, "density": 0.66, "lead": 2.3, "seed": 3071, "min_gap": 0.13, "global_gap": 0.085},
]


# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveBeat-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveBeat-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "best_song1": 0, "best_song2": 0, "best_song3": 0,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
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
    "onder": {"nl": "Een ritmespel van Dravenlock Games", "en": "A rhythm game by Dravenlock Games"},
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
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "hervat": {"nl": "Hervatten", "en": "Resume"},
    "hoofdmenu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "opnieuw": {"nl": "Opnieuw", "en": "Retry"},
    "kies_nummer": {"nl": "Kies een nummer", "en": "Choose a song"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "combo": {"nl": "Combo", "en": "Combo"},
    "perfect": {"nl": "Perfect", "en": "Perfect"},
    "goed": {"nl": "Goed", "en": "Good"},
    "mis": {"nl": "Mis", "en": "Miss"},
    "accuratesse": {"nl": "Accuratesse", "en": "Accuracy"},
    "rang": {"nl": "Rang", "en": "Rank"},
    "klaar": {"nl": "Nummer klaar!", "en": "Song complete!"},
    "max_combo": {"nl": "Hoogste combo", "en": "Max combo"},
    "uitleg1": {"nl": "Noten vallen in vier banen naar de balk onderaan.", "en": "Notes fall in four lanes to the bar below."},
    "uitleg2": {"nl": "Druk D, F, J of K als een noot de balk raakt.", "en": "Press D, F, J or K as a note hits the bar."},
    "uitleg3": {"nl": "Je kunt ook op een baan klikken.", "en": "You can also click a lane."},
    "uitleg4": {"nl": "Strakke timing = Perfect; bouw een combo op.", "en": "Tight timing = Perfect; build a combo."},
    "uitleg5": {"nl": "Esc of P = pauze.", "en": "Esc or P = pause."},
    "tik_start": {"nl": "Klaar...", "en": "Ready..."},
}


def t(key):
    e = TR.get(key, {})
    return e.get(_LANG, e.get("nl", key))


def song_name(song):
    return song["naam_nl"] if _LANG == "nl" else song["naam_en"]


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


def lane_center_x(i):
    return LANE_X0 + i * LANE_W + LANE_W // 2


# ----------------------------------------------------------------------------
class Button:
    def __init__(self, label, rect, action, kind="normal", sub=None):
        self.label = label
        self.rect = pygame.Rect(rect)
        self.action = action
        self.kind = kind
        self.sub = sub

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surf, font, font_s=None, hot=False, focus=False):
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
        elif self.sub and font_s:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=(r.centerx, r.centery - 10)))
            img2 = font_s.render(self.sub, True, GOLD)
            surf.blit(img2, img2.get_rect(center=(r.centerx, r.centery + 15)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


class Note:
    def __init__(self, time, lane):
        self.time = time
        self.lane = lane
        self.hit = False
        self.judged = False   # geoordeeld (geraakt of gemist)


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app, song):
        self.app = app
        self.song = song
        self.lead = song["lead"]
        self.travel = HIT_Y - FIELD_T
        self.scroll = self.travel / self.lead
        self.notes = self._make_beatmap()
        self.idx0 = 0
        self.song_t = 0.0
        self.count = 3.0
        self.phase = "count"     # count -> play -> done
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.n_perfect = 0
        self.n_good = 0
        self.n_miss = 0
        self.lane_flash = [0.0, 0.0, 0.0, 0.0]
        self.judge_text = ""
        self.judge_col = TEXT
        self.judge_t = 0.0
        self.finished = False
        self.end_t = 0.0
        self.total = len(self.notes)

    def _make_beatmap(self):
        bpm = self.song["bpm"]
        step = (60.0 / bpm) / 2.0
        dens = self.song["density"]
        dur = self.song["dur"]
        min_gap = self.song.get("min_gap", 0.16)        # minimale tijd tussen 2 noten in dezelfde baan
        global_gap = self.song.get("global_gap", min_gap * 0.6)   # minimale tijd tussen 2 noten totaal
        chords = dens >= 0.6                             # alleen het drukste nummer heeft akkoorden
        rng = random.Random(self.song.get("seed", 1234))
        notes = []
        last_lane_t = [-9.0] * LANES
        last_any_t = -9.0
        t0 = self.lead + 0.6
        i = 0
        tcur = t0
        while tcur < dur:
            if rng.random() < dens:
                # voorkom te veel tegelijk / te snel in dezelfde baan
                choices = [ln for ln in range(LANES) if tcur - last_lane_t[ln] >= min_gap]
                if choices and tcur - last_any_t >= global_gap:
                    ln = rng.choice(choices)
                    notes.append(Note(round(tcur, 4), ln))
                    last_lane_t[ln] = tcur
                    last_any_t = tcur
                    # af en toe een tweede baan tegelijk (akkoord) in het drukste nummer
                    if chords and rng.random() < 0.14:
                        others = [x for x in choices if x != ln]
                        if others:
                            ln2 = rng.choice(others)
                            notes.append(Note(round(tcur, 4), ln2))
                            last_lane_t[ln2] = tcur
            tcur += step
            i += 1
        notes.sort(key=lambda n: n.time)
        return notes

    def start_play(self):
        self.phase = "play"
        self.song_t = 0.0
        if self.app.sfx and self.app.cfg.get("music", True):
            self.app.sfx.start_music(self.song["key"])

    def update(self, dt):
        if self.finished:
            return
        if self.phase == "count":
            prev = math.ceil(self.count)
            self.count -= dt
            now = math.ceil(self.count)
            if now != prev and now >= 1 and self.app.sfx:
                self.app.sfx.play("count")
            if self.count <= 0:
                if self.app.sfx:
                    self.app.sfx.play("go")
                self.start_play()
            return
        self.song_t += dt
        for i in range(LANES):
            self.lane_flash[i] = max(0.0, self.lane_flash[i] - dt)
        self.judge_t = max(0.0, self.judge_t - dt)
        # gemiste noten (voorbij het venster, niet geraakt)
        for n in self.notes:
            if not n.judged and self.song_t - n.time > W_MISS:
                n.judged = True
                self._register("mis")
        # einde
        if self.song_t > self.song["dur"] + 0.5:
            self.end_t += dt
            if self.end_t > 1.2:
                self._finish()

    def hit_lane(self, lane):
        if self.phase != "play":
            return
        self.lane_flash[lane] = 0.12
        # zoek dichtstbijzijnde nog niet geoordeelde noot in deze baan binnen venster
        best = None
        bestdt = 999
        for n in self.notes:
            if n.judged or n.lane != lane:
                continue
            d = abs(n.time - self.song_t)
            if d < bestdt:
                bestdt = d
                best = n
        if best is None or bestdt > W_GOOD:
            return  # geen rake noot in de buurt: negeer (vergevingsgezind)
        best.judged = True
        best.hit = True
        if bestdt <= W_PERFECT:
            self._register("perfect")
        else:
            self._register("goed")

    def _register(self, kind):
        if kind == "perfect":
            self.n_perfect += 1
            self.combo += 1
            self.score += 300 + min(self.combo, 50) * 4
            self.judge_text = t("perfect")
            self.judge_col = GOLD
            if self.app.sfx:
                self.app.sfx.play("perfect")
        elif kind == "goed":
            self.n_good += 1
            self.combo += 1
            self.score += 150 + min(self.combo, 50) * 2
            self.judge_text = t("goed")
            self.judge_col = GOED
            if self.app.sfx:
                self.app.sfx.play("good")
        else:  # mis
            self.n_miss += 1
            self.combo = 0
            self.judge_text = t("mis")
            self.judge_col = WARN
            if self.app.sfx:
                self.app.sfx.play("miss")
        self.judge_t = 0.45
        self.max_combo = max(self.max_combo, self.combo)
        if self.combo and self.combo % 25 == 0 and self.app.sfx:
            self.app.sfx.play("combo")

    def accuracy(self):
        tot = self.n_perfect + self.n_good + self.n_miss
        if tot == 0:
            return 0.0
        return (self.n_perfect * 1.0 + self.n_good * 0.6) / tot * 100.0

    def rank(self):
        a = self.accuracy()
        return ("S" if a >= 93 else "A" if a >= 85 else "B" if a >= 73 else
                "C" if a >= 58 else "D")

    def _finish(self):
        if self.finished:
            return
        self.finished = True
        if self.app.sfx:
            self.app.sfx.stop_music()
            self.app.sfx.play("victory")
        key = "best_" + self.song["key"]
        if self.score > self.app.cfg.get(key, 0):
            self.app.cfg[key] = self.score
            save_config(self.app.cfg)

    # ---------- tekenen ----------
    def draw(self, surf):
        # banen
        for i in range(LANES):
            x = LANE_X0 + i * LANE_W
            base = mix(LANE_COLORS[i], BG, 0.85)
            if self.lane_flash[i] > 0:
                base = mix(base, LANE_COLORS[i], clamp(self.lane_flash[i] / 0.12, 0, 1) * 0.6)
            pygame.draw.rect(surf, base, (x, FIELD_T, LANE_W, HEIGHT - FIELD_T))
            pygame.draw.line(surf, LINE, (x, FIELD_T), (x, HEIGHT), 1)
        pygame.draw.line(surf, LINE, (LANE_X0 + LANE_AREA_W, FIELD_T), (LANE_X0 + LANE_AREA_W, HEIGHT), 1)
        # trefbalk
        pygame.draw.line(surf, mix(ACCENT, (255, 255, 255), 0.2), (LANE_X0, HIT_Y), (LANE_X0 + LANE_AREA_W, HIT_Y), 3)
        # trefpads met letters
        for i in range(LANES):
            cx = lane_center_x(i)
            lit = self.lane_flash[i] > 0
            col = LANE_COLORS[i]
            pad = mix(col, BG, 0.2) if lit else mix(col, BG, 0.55)
            pygame.draw.rect(surf, pad, (LANE_X0 + i * LANE_W + 6, HIT_Y - 4, LANE_W - 12, 40), border_radius=8)
            pygame.draw.rect(surf, col, (LANE_X0 + i * LANE_W + 6, HIT_Y - 4, LANE_W - 12, 40), 2, border_radius=8)
            img = self.app.font_m.render(LANE_LETTERS[i], True, (245, 245, 248) if lit else TEXT)
            surf.blit(img, img.get_rect(center=(cx, HIT_Y + 16)))
        # noten
        if self.phase == "play":
            for n in self.notes:
                if n.judged:
                    continue
                y = HIT_Y - (n.time - self.song_t) * self.scroll
                if y < FIELD_T - NOTE_H or y > HEIGHT:
                    continue
                x = LANE_X0 + n.lane * LANE_W + 8
                col = LANE_COLORS[n.lane]
                pygame.draw.rect(surf, col, (x, int(y - NOTE_H / 2), LANE_W - 16, NOTE_H), border_radius=6)
                pygame.draw.rect(surf, mix(col, (255, 255, 255), 0.25), (x, int(y - NOTE_H / 2), LANE_W - 16, 6), border_radius=4)
        # aftellen
        if self.phase == "count":
            n = max(1, math.ceil(self.count))
            img = self.app.font_xl.render(str(n), True, GOLD)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        # oordeel + combo
        if self.judge_t > 0:
            a = int(clamp(self.judge_t / 0.45, 0, 1) * 255)
            img = self.app.font_l.render(self.judge_text, True, self.judge_col)
            img.set_alpha(a)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, HIT_Y - 130)))
        if self.combo >= 2:
            img = self.app.font_m.render("%s %d" % (t("combo"), self.combo), True, TEXT)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, HIT_Y - 90)))


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
    f_title = pygame.font.Font(None, 80)
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

        self.font_xl = pygame.font.Font(None, 110)
        self.font_l = pygame.font.Font(None, 56)
        self.font_m = pygame.font.Font(None, 36)
        self.font_s = pygame.font.Font(None, 26)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.game = None
        self.song_idx = 0
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)

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
        if self.state in ("title", "songselect", "settings", "help", "results"):
            self.sfx.start_music("menu")
        # in 'play' regelt het spel zelf de muziek (op de maat)

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        if s != "play":
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

    def _action(self, a):
        if a is None:
            return
        if self.sfx:
            self.sfx.play("click")
        if a == "play":
            self.set_state("songselect")
        elif a and a.startswith("song_"):
            self.song_idx = int(a.split("_")[1])
            if self.sfx:
                self.sfx.play("select")
            self.start_game(self.song_idx)
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "back_title":
            self.set_state("title")
        elif a == "to_songselect":
            self.set_state("songselect")
        elif a == "resume":
            self.set_state("play")
        elif a == "pause":
            if self.sfx:
                self.sfx.stop_music()
            self.set_state("pause")
        elif a == "retry":
            self.start_game(self.song_idx)
        elif a == "to_title":
            if self.sfx:
                self.sfx.stop_music()
            self.set_state("title")
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

    def _back_for_state(self):
        return {"help": "back_title", "settings": "back_title", "songselect": "back_title",
                "pause": "resume", "results": "to_songselect"}.get(self.state)

    def on_key(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
                return
            if self.game and key in LANE_KEYS:
                self.game.hit_lane(LANE_KEYS.index(key))
            return
        if self.state == "results" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("retry"); return
        if key == pygame.K_ESCAPE:
            self._action(self._back_for_state())
            return
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

    def on_click(self, pos, button):
        if button != 1:
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return
        if self.state == "play" and self.game and pos[1] > FIELD_T:
            x = pos[0]
            if LANE_X0 <= x <= LANE_X0 + LANE_AREA_W:
                lane = int((x - LANE_X0) // LANE_W)
                self.game.hit_lane(clamp(lane, 0, LANES - 1))

    def start_game(self, idx):
        self.song_idx = idx
        self.game = Game(self, SONGS[idx])
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            self.game.update(dt)
            if self.game.finished and self.t_state > 0.3:
                self.set_state("results")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "songselect":
            self._draw_songselect(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st in ("play", "pause"):
            s.fill(BG)
            self.game.draw(s)
            self._draw_hud(s)
            if st == "pause":
                self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "results":
            self._draw_results(s)
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

    def _add_button(self, label, rect, action, kind="normal", sub=None):
        self.buttons.append(Button(label, rect, action, kind=kind, sub=sub))

    def _add_donate(self):
        self._add_button(t("donatie"), (WIDTH - 190, 14, 172, 46), "donate", kind="donate")

    def _stack(self, items, top, w=380, h=64, gap=18, kinds=None):
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
        play_like = self.state in ("play", "pause")
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, self.font_s, hot=b.hit(self.mouse), focus=(i == self.focus and not play_like))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_l, ACCENT, WIDTH // 2, 56)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=210, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        best = max(self.cfg.get("best_song1", 0), self.cfg.get("best_song2", 0), self.cfg.get("best_song3", 0))
        self._text(s, "%s: %d" % (t("best"), best), self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_songselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_nummer"), self.font_l, ACCENT, WIDTH // 2, 70)
        w = 460
        x = WIDTH // 2 - w // 2
        y = 150
        for i, song in enumerate(SONGS):
            best = self.cfg.get("best_" + song["key"], 0)
            label = "%s   (%d bpm)" % (song_name(song), song["bpm"])
            kind = "primary" if i == 0 else "normal"
            self._add_button(label, (x, y, w, 64), "song_%d" % i, kind=kind,
                             sub="%s %d" % (t("best"), best))
            y += 84
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 64, 220, 50), "back_title", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 60)
        y = 150
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_m, TEXT, WIDTH // 2, y)
            y += 50
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 56), "back_title", kind="back")
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

    def _draw_hud(self, s):
        g = self.game
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, HUD_H))
        self._text(s, "%s %d" % (t("score"), g.score), self.font_m, TEXT, 100, HUD_H // 2)
        self._text(s, song_name(g.song), self.font_m, ACCENT, WIDTH // 2, HUD_H // 2)
        self._text(s, "%s %.0f%%" % (t("accuratesse"), g.accuracy()), self.font_s, GOLD, WIDTH - 230, HUD_H // 2, center=False)
        if self.state == "play":
            self._add_button(t("pauze"), (WIDTH - 120, 8, 104, 34), "pause", kind="back")

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_l, color, WIDTH // 2, 160)
        y = 240
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 44
        if buttons_def:
            self._stack(buttons_def, top=max(y + 10, 320), w=360, h=64, gap=18,
                        kinds=["primary"] + ["normal"] * (len(buttons_def) - 1))

    def _draw_results(self, s):
        s.fill(BG)
        g = self.game
        self._text(s, t("klaar"), self.font_l, GOLD, WIDTH // 2, 70)
        rank = g.rank()
        rcol = {"S": GOLD, "A": GOED, "B": ACCENT, "C": WARN, "D": RED}.get(rank, TEXT)
        self._text(s, rank, self.font_xl, rcol, WIDTH // 2, 170)
        lines = [
            "%s: %d" % (t("score"), g.score),
            "%s: %.0f%%" % (t("accuratesse"), g.accuracy()),
            "%s %d   %s %d   %s %d" % (t("perfect"), g.n_perfect, t("goed"), g.n_good, t("mis"), g.n_miss),
            "%s: %d" % (t("max_combo"), g.max_combo),
            "%s: %d" % (t("best"), self.cfg.get("best_" + g.song["key"], 0)),
        ]
        y = 250
        for i, ln in enumerate(lines):
            self._text(s, ln, self.font_m, TEXT if i else GOLD, WIDTH // 2, y)
            y += 42
        self._stack([(t("opnieuw"), "retry"), (t("kies_nummer"), "to_songselect"), (t("hoofdmenu"), "to_title")],
                    top=y + 6, w=360, h=54, gap=14, kinds=["primary", "normal", "normal"])


# ----------------------------------------------------------------------------
def main():
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

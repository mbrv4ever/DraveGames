# -*- coding: utf-8 -*-
"""dragon.py - DraveDragon, een one-button vlieggame van Dravenlock Games.

Tik (spatie of muisknop) om met de draak te klimmen; laat los om te dalen.
Vlieg door de openingen tussen de stenen pilaren, verzamel edelstenen en haal
een zo hoog mogelijke score. De snelheid loopt op. Een "rustige" stand
(grotere openingen, lager tempo) maakt het toegankelijker.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke HUD; procedurele muziek en geluiden (sfx.py); gesproken intro
(neuvoice) in een apart splashvenster. Volledig draagbaar: alles wordt bewaard
in een map "DraveDragon-data" naast het programma.
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

APP_NAME = "DraveDragon"
APP_VERSION = "0.2.0"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
CEIL_Y = 54
GROUND_Y = HEIGHT - 56
GRAVITY = 1350.0
FLAP_V = -400.0
MAX_FALL = 560.0
DRAGON_X = 250
DRAGON_R = 21
PILLAR_W = 88

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

DIFFS = {
    # gap=opening, speed=basistempo, cap/factor=snelheidsopbouw,
    # spacing=afstand tussen pilaren, start=extra ruimte aan het begin,
    # gem=kans op edelsteen
    "makkelijk": {"gap": 255, "speed": 172, "cap": 55, "factor": 0.9, "spacing": 390, "start": 280, "gem": 0.55},
    "moeilijk":  {"gap": 205, "speed": 215, "cap": 120, "factor": 1.6, "spacing": 360, "start": 140, "gem": 0.5},
    "zwaar":     {"gap": 178, "speed": 236, "cap": 150, "factor": 2.0, "spacing": 332, "start": 70, "gem": 0.42},
}
DIFF_ORDER = ["makkelijk", "moeilijk", "zwaar"]


THEMES = [
    {"sky_top": (24, 28, 40), "sky_bot": (40, 46, 62), "pillar": (70, 74, 86), "pillar2": (52, 56, 66)},
    {"sky_top": (30, 22, 34), "sky_bot": (52, 38, 50), "pillar": (84, 66, 80), "pillar2": (60, 48, 58)},
    {"sky_top": (20, 32, 30), "sky_bot": (34, 52, 48), "pillar": (62, 82, 74), "pillar2": (46, 60, 54)},
]


# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script),
    nooit in systeemmappen zoals %APPDATA%."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveDragon-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveDragon-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "difficulty": "moeilijk",
    "best_makkelijk": 0, "best_moeilijk": 0, "best_zwaar": 0,
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
    "onder": {"nl": "Een vlieggame van Dravenlock Games", "en": "A flying game by Dravenlock Games"},
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
    "kies_moeilijkheid": {"nl": "Kies moeilijkheid", "en": "Choose difficulty"},
    "makkelijk": {"nl": "Makkelijk", "en": "Easy"},
    "moeilijk": {"nl": "Moeilijk", "en": "Hard"},
    "zwaar": {"nl": "Zwaar", "en": "Brutal"},
    "uitleg_makkelijk": {"nl": "Ruime openingen, rustig tempo. Ontspannen vliegen.",
                         "en": "Wide gaps, gentle pace. Relaxed flying."},
    "uitleg_moeilijk": {"nl": "Gemiddelde openingen; snelheid loopt geleidelijk op.",
                        "en": "Medium gaps; speed builds up gradually."},
    "uitleg_zwaar": {"nl": "Krappe openingen, hoog tempo. Voor de durfal.",
                     "en": "Tight gaps, fast pace. For the daredevil."},
    "aan": {"nl": "aan", "en": "on"},
    "uit": {"nl": "uit", "en": "off"},
    "auto": {"nl": "OS", "en": "OS"},
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "hervat": {"nl": "Hervatten", "en": "Resume"},
    "hoofdmenu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "opnieuw": {"nl": "Opnieuw", "en": "Retry"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "verloren": {"nl": "Neergestort", "en": "Crashed"},
    "tik_start": {"nl": "Tik om te vliegen", "en": "Tap to fly"},
    "uitleg1": {"nl": "Tik (spatie of muisknop) om te klimmen.", "en": "Tap (space or mouse) to climb."},
    "uitleg2": {"nl": "Laat los om te dalen.", "en": "Release to descend."},
    "uitleg3": {"nl": "Vlieg door de openingen; raak niets.", "en": "Fly through the gaps; hit nothing."},
    "uitleg4": {"nl": "Pak edelstenen voor extra punten.", "en": "Grab gems for extra points."},
    "uitleg5": {"nl": "Esc of P = pauze.", "en": "Esc or P = pause."},
    "nieuw_record": {"nl": "Nieuw record!", "en": "New record!"},
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
        pygame.draw.rect(surf, bg, r, border_radius=12)
        pygame.draw.rect(surf, ACCENT if (hot or focus) else LINE, r,
                         width=3 if (hot or focus) else 2, border_radius=12)
        col = TEXT if not (hot or focus) else (245, 245, 248)
        if self.kind == "donate":
            draw_heart(surf, r.left + 26, r.centery, 11, WARN if not (hot or focus) else (235, 120, 110))
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(midleft=(r.left + 46, r.centery)))
        else:
            img = font.render(self.label, True, col)
            surf.blit(img, img.get_rect(center=r.center))


# ----------------------------------------------------------------------------
def draw_dragon(surf, x, y, vy, flap_t):
    # vleugelslag uit flap-timer
    wing = math.sin(flap_t * 16) * 0.5 + (0.5 if vy < 0 else 0.0)
    tilt = clamp(vy / 700.0, -0.5, 0.7)
    body = mix(RED, BG, 0.05)
    # staart
    pygame.draw.polygon(surf, mix(RED, BG, 0.25),
                        [(x - 22, y), (x - 46, y - 10 + tilt * 10), (x - 40, y + 8 + tilt * 10)])
    # lichaam
    pygame.draw.ellipse(surf, body, (x - 24, y - 16, 50, 32))
    # vleugel (omhoog/omlaag)
    wy = y - 26 - wing * 18
    pygame.draw.polygon(surf, mix(PURPLE, BG, 0.1),
                        [(x - 6, y - 6), (x - 24, wy), (x + 14, y - 8)])
    # kop
    pygame.draw.circle(surf, body, (x + 22, y - 6), 13)
    # hoorn
    pygame.draw.polygon(surf, GOLD, [(x + 18, y - 16), (x + 12, y - 26), (x + 24, y - 18)])
    # oog
    pygame.draw.circle(surf, GOLD, (x + 27, y - 9), 3)
    # snuit / vuurgloed
    pygame.draw.polygon(surf, mix(GOLD, RED, 0.3), [(x + 33, y - 6), (x + 40, y - 9), (x + 40, y - 2)])


def draw_gem(surf, x, y, t):
    s = 11 + math.sin(t * 4) * 1.5
    pts = [(x, y - s), (x + s * 0.8, y), (x, y + s), (x - s * 0.8, y)]
    pygame.draw.polygon(surf, ACCENT, pts)
    pygame.draw.polygon(surf, (220, 235, 250), pts, 2)
    pygame.draw.line(surf, (235, 245, 255), (x, y - s), (x, y + s), 1)


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app, difficulty="moeilijk"):
        self.app = app
        self.rng = random.Random()
        self.difficulty = difficulty if difficulty in DIFFS else "moeilijk"
        d = DIFFS[self.difficulty]
        self.gap_h = d["gap"]
        self.base_speed = d["speed"]
        self.speed_cap = d["cap"]
        self.speed_factor = d["factor"]
        self.spacing = d["spacing"]
        self.gem_chance = d["gem"]
        self.x = DRAGON_X
        self.y = HEIGHT * 0.42
        self.vy = 0.0
        self.flap_t = 0.0
        self.started = False
        self.dead = False
        self.score = 0
        self.gems_got = 0
        self.scroll = 0.0
        self.pillars = []      # dicts: x, gap_y, passed, gem(None of [gx,gy,got])
        self.theme = 0
        self.new_record = False
        self.dead_t = 0.0
        self._spawn_initial(d["start"])

    def speed(self):
        return self.base_speed + min(self.speed_cap, self.score * self.speed_factor)

    def _spawn_initial(self, start_extra):
        x = WIDTH + 80 + start_extra
        for i in range(4):
            self._add_pillar(x)
            x += self.spacing

    def _add_pillar(self, x):
        margin = 90
        gy = self.rng.uniform(CEIL_Y + margin + self.gap_h / 2,
                              GROUND_Y - margin - self.gap_h / 2)
        gem = None
        if self.rng.random() < self.gem_chance:
            gem = [x + PILLAR_W + 120, gy + self.rng.uniform(-self.gap_h * 0.25, self.gap_h * 0.25), False]
        self.pillars.append({"x": x, "gap_y": gy, "passed": False, "gem": gem})

    def flap(self):
        if self.dead:
            return
        self.started = True
        self.vy = FLAP_V
        self.flap_t = 0.0
        if self.app.sfx:
            self.app.sfx.play("flap")

    def update(self, dt):
        self.flap_t += dt
        if self.dead:
            self.dead_t += dt
            self.vy = clamp(self.vy + GRAVITY * dt, -700, MAX_FALL)
            self.y = clamp(self.y + self.vy * dt, CEIL_Y + DRAGON_R, GROUND_Y - DRAGON_R)
            return
        if not self.started:
            # zweven op de plek (lichte bob) tot de eerste tik
            self.y = HEIGHT * 0.42 + math.sin(self.flap_t * 2) * 8
            return
        self.vy = clamp(self.vy + GRAVITY * dt, -700, MAX_FALL)
        self.y += self.vy * dt
        sp = self.speed()
        self.scroll += sp * dt
        for p in self.pillars:
            p["x"] -= sp * dt
            if p["gem"]:
                p["gem"][0] -= sp * dt
        # nieuwe pilaren
        while self.pillars and self.pillars[-1]["x"] < WIDTH - self.spacing:
            self._add_pillar(self.pillars[-1]["x"] + self.spacing)
        # oude weg
        self.pillars = [p for p in self.pillars if p["x"] > -PILLAR_W - 160]
        # score + thema
        for p in self.pillars:
            if not p["passed"] and p["x"] + PILLAR_W < self.x:
                p["passed"] = True
                self.score += 1
                if self.app.sfx:
                    self.app.sfx.play("score")
                if self.score % 10 == 0:
                    self.theme = (self.theme + 1) % len(THEMES)
                    if self.app.sfx:
                        self.app.sfx.play("milestone")
        # edelstenen
        for p in self.pillars:
            g = p["gem"]
            if g and not g[2] and math.hypot(g[0] - self.x, g[1] - self.y) < DRAGON_R + 12:
                g[2] = True
                self.score += 5
                self.gems_got += 1
                if self.app.sfx:
                    self.app.sfx.play("gem")
        self._collide()

    def _collide(self):
        if self.y - DRAGON_R < CEIL_Y or self.y + DRAGON_R > GROUND_Y:
            self._die()
            return
        for p in self.pillars:
            if p["x"] - DRAGON_R < self.x < p["x"] + PILLAR_W + DRAGON_R:
                gt = p["gap_y"] - self.gap_h / 2
                gb = p["gap_y"] + self.gap_h / 2
                # binnen de pilaarkolom: check boven/onder de opening
                nearest_x = clamp(self.x, p["x"], p["x"] + PILLAR_W)
                if abs(nearest_x - self.x) <= DRAGON_R:
                    if self.y - DRAGON_R < gt or self.y + DRAGON_R > gb:
                        self._die()
                        return

    def _die(self):
        if self.dead:
            return
        self.dead = True
        self.y = clamp(self.y, CEIL_Y + DRAGON_R, GROUND_Y - DRAGON_R)
        key = "best_" + self.difficulty
        if self.score > self.app.cfg.get(key, 0):
            self.app.cfg[key] = self.score
            self.new_record = True
            save_config(self.app.cfg)
        if self.app.sfx:
            self.app.sfx.play("crash")
            self.app.sfx.play("roar")

    # ---------- tekenen ----------
    def draw(self, surf):
        th = THEMES[self.theme]
        for i in range(0, HEIGHT, 4):
            surf.fill(mix(th["sky_top"], th["sky_bot"], i / HEIGHT), (0, i, WIDTH, 4))
        # parallax verre pilaren (decor)
        off = int(self.scroll * 0.3) % 180
        for bx in range(-180, WIDTH + 180, 180):
            x = bx - off
            pygame.draw.rect(surf, mix(th["sky_bot"], (0, 0, 0), 0.2), (x, CEIL_Y, 60, 40))
            pygame.draw.rect(surf, mix(th["sky_bot"], (0, 0, 0), 0.2), (x + 90, GROUND_Y - 40, 60, 40))
        # plafond en grond
        pygame.draw.rect(surf, mix(th["pillar2"], (0, 0, 0), 0.3), (0, 0, WIDTH, CEIL_Y))
        pygame.draw.rect(surf, mix(th["pillar2"], (0, 0, 0), 0.3), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(surf, LINE, (0, CEIL_Y), (WIDTH, CEIL_Y), 2)
        pygame.draw.line(surf, LINE, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        # pilaren
        for p in self.pillars:
            x = int(p["x"])
            gt = int(p["gap_y"] - self.gap_h / 2)
            gb = int(p["gap_y"] + self.gap_h / 2)
            self._pillar(surf, th, x, CEIL_Y, gt - CEIL_Y, lip_bottom=True)
            self._pillar(surf, th, x, gb, GROUND_Y - gb, lip_bottom=False)
            g = p["gem"]
            if g and not g[2]:
                draw_gem(surf, int(g[0]), int(g[1]), self.flap_t)
        # draak
        draw_dragon(surf, int(self.x), int(self.y), self.vy, self.flap_t)

    def _pillar(self, surf, th, x, y, h, lip_bottom):
        if h <= 0:
            return
        pygame.draw.rect(surf, th["pillar"], (x, y, PILLAR_W, h))
        pygame.draw.rect(surf, th["pillar2"], (x, y, PILLAR_W, h), 3)
        pygame.draw.rect(surf, mix(th["pillar"], (255, 255, 255), 0.12), (x + 6, y, 6, h))
        lip_y = (y + h - 16) if lip_bottom else y
        pygame.draw.rect(surf, mix(th["pillar"], (0, 0, 0), 0.2), (x - 6, lip_y, PILLAR_W + 12, 16), border_radius=4)


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

    f_title = pygame.font.Font(None, 84)
    f_sub = pygame.font.Font(None, 34)
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
    FADE_END = 1.5
    MIN_TIME = 3.0
    MAX_AFTER = 16.0
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
        if t0 >= FADE_END and not spoke:
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
        win.blit(title_img, title_img.get_rect(center=(SW // 2, 310)))
        sub_img.set_alpha(fade(1.0, 0.5))
        win.blit(sub_img, sub_img.get_rect(center=(SW // 2, 362)))
        pygame.display.flip()

        if skipped:
            break
        if use_voice:
            if spoke and not tts.busy() and t0 > (speak_time or 0) + 0.3:
                break
            if spoke and t0 > (speak_time or 0) + MAX_AFTER:
                break
        else:
            if t0 >= MIN_TIME:
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

        self.game = None
        self.difficulty = self.cfg.get("difficulty", "moeilijk")
        if self.difficulty not in DIFFS:
            self.difficulty = "moeilijk"
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
        if self.state in ("title", "modeselect", "settings", "help", "gameover"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            self.sfx.start_music("fly1" if (self.game and self.game.theme % 2 == 0) else "fly2")

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
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

    # ---------- acties ----------
    def _action(self, a):
        if a is None:
            return
        if self.sfx:
            self.sfx.play("click")
        if a == "play":
            self.set_state("modeselect")
        elif a in ("start_makkelijk", "start_moeilijk", "start_zwaar"):
            if self.sfx:
                self.sfx.play("select")
            self.start_game(a.split("_", 1)[1])
        elif a == "help":
            self.set_state("help")
        elif a == "settings":
            self.set_state("settings")
        elif a == "back_title":
            self.set_state("title")
        elif a == "resume":
            self.set_state("play")
        elif a == "pause":
            self.set_state("pause")
        elif a == "retry":
            self.start_game()
        elif a == "to_title":
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
        return {"help": "back_title", "settings": "back_title", "modeselect": "back_title",
                "pause": "resume", "gameover": "to_title"}.get(self.state)

    def _flap(self):
        if self.state == "play" and self.game:
            if self.game.dead:
                return
            self.game.flap()

    def on_key(self, key):
        if self.state == "play":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self._flap()
            return
        if key == pygame.K_ESCAPE:
            self._action(self._back_for_state())
            return
        if self.state == "gameover" and key in (pygame.K_SPACE, pygame.K_RETURN):
            self._action("retry"); return
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
        if self.state == "play" and button == 1:
            self._flap()
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    # ---------- spel ----------
    def start_game(self, difficulty=None):
        if difficulty:
            self.difficulty = difficulty
            self.cfg["difficulty"] = difficulty
            save_config(self.cfg)
        self.game = Game(self, self.difficulty)
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            self.game.update(dt)
            if self.game.dead and self.game.dead_t > 0.7:
                self.set_state("gameover")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "modeselect":
            self._draw_modeselect(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st == "play":
            self.game.draw(s)
            self._draw_hud(s)
            if not self.game.started:
                self._center_hint(s, t("tik_start"))
        elif st == "pause":
            self.game.draw(s)
            self._draw_hud(s)
            self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "gameover":
            self.game.draw(s)
            best = self.cfg.get("best_" + self.game.difficulty, 0)
            lines = ["%s %d   %s %d" % (t(self.game.difficulty), self.game.score, t("best"), best)]
            if self.game.new_record:
                lines.append(t("nieuw_record"))
            self._overlay(s, t("verloren"), lines,
                          [(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")],
                          color=GOLD if self.game.new_record else WARN)
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

    def _center_hint(self, s, txt):
        img = self.font_m.render(txt, True, TEXT)
        bg = pygame.Surface((img.get_width() + 40, img.get_height() + 20), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        s.blit(bg, bg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        s.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    def _add_button(self, label, rect, action, kind="normal"):
        self.buttons.append(Button(label, rect, action, kind=kind))

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
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, hot=b.hit(self.mouse), focus=(i == self.focus))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        # vliegende draak als sfeer
        draw_dragon(s, WIDTH // 2, 170, -100, self.t_state)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=230, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        best = max(self.cfg.get("best_makkelijk", 0), self.cfg.get("best_moeilijk", 0),
                   self.cfg.get("best_zwaar", 0))
        self._text(s, "%s: %d" % (t("best"), best), self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_modeselect(self, s):
        s.fill(BG)
        self._text(s, t("kies_moeilijkheid"), self.font_l, ACCENT, WIDTH // 2, 70)
        info = {"makkelijk": ("uitleg_makkelijk", GOED),
                "moeilijk": ("uitleg_moeilijk", ACCENT),
                "zwaar": ("uitleg_zwaar", WARN)}
        w = 460
        x = WIDTH // 2 - w // 2
        y = 150
        for mode in DIFF_ORDER:
            best = self.cfg.get("best_" + mode, 0)
            label = "%s    (%s %d)" % (t(mode), t("best"), best)
            kind = "primary" if mode == "moeilijk" else "normal"
            self._add_button(label, (x, y, w, 60), "start_" + mode, kind=kind)
            self._text(s, t(info[mode][0]), self.font_s, MUTED, WIDTH // 2, y + 76)
            y += 116
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 64, 220, 50), "back_title", kind="back")
        self._add_donate()

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 60)
        y = 150
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_m, TEXT, WIDTH // 2, y)
            y += 56
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 90, 220, 60), "back_title", kind="back")
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
        pygame.draw.rect(s, (0, 0, 0), (0, 0, WIDTH, 46))
        self._text(s, "%s %d" % (t("score"), self.game.score), self.font_m, TEXT, 110, 23)
        self._text(s, "%s %d" % (t("best"), self.cfg.get("best_" + self.game.difficulty, 0)),
                   self.font_m, GOLD, WIDTH // 2, 23)
        if self.state == "play" and not self.game.dead:
            self._add_button(t("pauze"), (WIDTH - 128, 52, 110, 38), "pause", kind="back")

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 170)
        y = 260
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 46
        if buttons_def:
            self._stack(buttons_def, top=max(y + 10, 330), w=360, h=64, gap=18,
                        kinds=["primary"] + ["normal"] * (len(buttons_def) - 1))


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

# -*- coding: utf-8 -*-
"""tetris.py - DraveTris, een Tetris-spel van Dravenlock Games.

De zeven bekende stukken vallen in de put. Schuif (links/rechts), draai (omhoog
of X/Z) en laat ze zakken (omlaag = zacht, spatie = hard) om volle rijen te maken
die verdwijnen. Vier rijen tegelijk is een 'Tetris'. Het tempo loopt op per level.
Een schaduw-stuk laat zien waar het stuk landt, je kunt een stuk vasthouden (C of
Shift) en het volgende stuk staat rechts in beeld.

NL-basis met OS-taaldetectie en Engels; donker Dravenlock-palet, grote en
contrastrijke put/HUD; procedurele muziek en geluiden (sfx.py); gesproken intro
(neuvoice) in een apart splashvenster. Volledig draagbaar: alles wordt bewaard in
een map "DraveTris-data" naast het programma.
"""
from __future__ import annotations

import json
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

APP_NAME = "DraveTris"
APP_VERSION = "0.1.1"
STUDIO = "Dravenlock Games"
DONATIE = "https://paypal.me/roger076"

WIDTH, HEIGHT = 960, 600
FPS = 60
COLS = 10
ROWS = 20
CELL = 28
FIELD_W = COLS * CELL
FIELD_H = ROWS * CELL
FIELD_X = (WIDTH - FIELD_W) // 2
FIELD_Y = HEIGHT - FIELD_H - 14

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
GRID_BG = (18, 18, 23)

# stukken: 4 draaistanden, elk 4 cellen (x,y) in een 4x4-vak; + kleur
SHAPES = {
    "I": ([[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)],
           [(0, 2), (1, 2), (2, 2), (3, 2)], [(1, 0), (1, 1), (1, 2), (1, 3)]], (90, 196, 214)),
    "O": ([[(1, 0), (2, 0), (1, 1), (2, 1)]] * 4, (212, 184, 90)),
    "T": ([[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)],
           [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]], (158, 110, 200)),
    "S": ([[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)],
           [(1, 1), (2, 1), (0, 2), (1, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)]], (127, 176, 105)),
    "Z": ([[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)],
           [(0, 1), (1, 1), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (0, 2)]], (200, 84, 84)),
    "J": ([[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)],
           [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]], (111, 143, 214)),
    "L": ([[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)],
           [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]], (214, 150, 90)),
}
PIECES = list(SHAPES.keys())
KICKS = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0), (0, -2)]
LINE_SCORE = [0, 100, 300, 500, 800]


# ----------------------------------------------------------------------------
def config_dir():
    """Draagbaar: bewaar alles in een map NAAST de .exe (of het script)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    d = os.path.join(base, "DraveTris-data")
    try:
        os.makedirs(d, exist_ok=True)
        test = os.path.join(d, ".schrijftest")
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return d
    except Exception:
        import tempfile
        d2 = os.path.join(tempfile.gettempdir(), "DraveTris-data")
        try:
            os.makedirs(d2, exist_ok=True)
        except Exception:
            pass
        return d2


CONFIG_PATH = os.path.join(config_dir(), "config.json")
DEFAULT_CONFIG = {
    "lang": "", "sound": True, "music": True, "voice": True, "volume": 0.8,
    "voice_name": "M1", "highscore": 0, "ghost": True,
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
    "donatie": {"nl": "Donatie", "en": "Donate"},
    "speel": {"nl": "Spelen", "en": "Play"},
    "gids": {"nl": "Hoe te spelen", "en": "How to play"},
    "instellingen": {"nl": "Instellingen", "en": "Settings"},
    "terug": {"nl": "Terug", "en": "Back"},
    "geluid": {"nl": "Geluid", "en": "Sound"},
    "muziek": {"nl": "Muziek", "en": "Music"},
    "stem": {"nl": "Stem", "en": "Voice"},
    "schaduw": {"nl": "Schaduw-stuk", "en": "Ghost piece"},
    "volume": {"nl": "Volume", "en": "Volume"},
    "taal": {"nl": "Taal", "en": "Language"},
    "aan": {"nl": "aan", "en": "on"},
    "uit": {"nl": "uit", "en": "off"},
    "auto": {"nl": "OS", "en": "OS"},
    "pauze": {"nl": "Pauze", "en": "Paused"},
    "hervat": {"nl": "Hervatten", "en": "Resume"},
    "hoofdmenu": {"nl": "Hoofdmenu", "en": "Main menu"},
    "opnieuw": {"nl": "Opnieuw", "en": "Retry"},
    "score": {"nl": "Score", "en": "Score"},
    "best": {"nl": "Beste", "en": "Best"},
    "level": {"nl": "Level", "en": "Level"},
    "rijen": {"nl": "Rijen", "en": "Lines"},
    "volgende": {"nl": "Volgende", "en": "Next"},
    "vast": {"nl": "Vast", "en": "Hold"},
    "gameover": {"nl": "Game over", "en": "Game over"},
    "uitleg1": {"nl": "Pijltjes links/rechts: schuiven.", "en": "Arrows left/right: move."},
    "uitleg2": {"nl": "Pijl omhoog of X: draaien (Z = andersom).", "en": "Up or X: rotate (Z = other way)."},
    "uitleg3": {"nl": "Pijl omlaag: zacht zakken. Spatie: hard laten vallen.", "en": "Down: soft drop. Space: hard drop."},
    "uitleg4": {"nl": "C of Shift: stuk vasthouden voor later.", "en": "C or Shift: hold a piece for later."},
    "uitleg5": {"nl": "Maak volle rijen; vier tegelijk = Tetris! Esc/P = pauze.", "en": "Clear full rows; four at once = Tetris! Esc/P = pause."},
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


def fall_interval(level):
    return max(0.05, 0.80 * (0.85 ** level))


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


# ----------------------------------------------------------------------------
class Game:
    def __init__(self, app):
        self.app = app
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 0
        self.bag = []
        self.next_q = [self._draw_from_bag() for _ in range(3)]
        self.hold = None
        self.hold_used = False
        self.cur = None
        self.cx = 0
        self.cy = 0
        self.rot = 0
        self.fall_t = 0.0
        self.lock_t = 0.0
        self.locking = False
        self.finished = False
        self.flash_rows = []
        self.flash_t = 0.0
        self._spawn()

    def _draw_from_bag(self):
        if not self.bag:
            self.bag = PIECES[:]
            random.shuffle(self.bag)
        return self.bag.pop()

    def _cells(self, piece, rot, cx, cy):
        return [(cx + dx, cy + dy) for (dx, dy) in SHAPES[piece][0][rot % 4]]

    def _valid(self, piece, rot, cx, cy):
        for (x, y) in self._cells(piece, rot, cx, cy):
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def _spawn(self, piece=None):
        if piece is None:
            piece = self.next_q.pop(0)
            self.next_q.append(self._draw_from_bag())
        self.cur = piece
        self.rot = 0
        self.cx = 3
        self.cy = -1 if piece != "I" else -2
        self.hold_used = False
        self.locking = False
        self.lock_t = 0.0
        self.fall_t = 0.0
        if not self._valid(self.cur, self.rot, self.cx, self.cy):
            # nog een rij hoger proberen, anders game over
            self.cy -= 1
            if not self._valid(self.cur, self.rot, self.cx, self.cy):
                self._game_over()

    def move(self, dx):
        if self.finished:
            return
        if self._valid(self.cur, self.rot, self.cx + dx, self.cy):
            self.cx += dx
            if self.app.sfx:
                self.app.sfx.play("move")
            self._reset_lock()

    def rotate(self, d):
        if self.finished:
            return
        nr = (self.rot + d) % 4
        for (kx, ky) in KICKS:
            if self._valid(self.cur, nr, self.cx + kx, self.cy + ky):
                self.rot = nr
                self.cx += kx
                self.cy += ky
                if self.app.sfx:
                    self.app.sfx.play("rotate")
                self._reset_lock()
                return

    def soft_drop(self):
        if self.finished:
            return
        if self._valid(self.cur, self.rot, self.cx, self.cy + 1):
            self.cy += 1
            self.score += 1
            self.fall_t = 0.0

    def hard_drop(self):
        if self.finished:
            return
        d = 0
        while self._valid(self.cur, self.rot, self.cx, self.cy + 1):
            self.cy += 1
            d += 1
        self.score += d * 2
        if self.app.sfx:
            self.app.sfx.play("drop")
        self._lock()

    def hold_piece(self):
        if self.finished or self.hold_used:
            return
        if self.hold is None:
            self.hold = self.cur
            self._spawn()
        else:
            self.hold, swap = self.cur, self.hold
            self._spawn(swap)
        self.hold_used = True
        if self.app.sfx:
            self.app.sfx.play("hold")

    def ghost_y(self):
        gy = self.cy
        while self._valid(self.cur, self.rot, self.cx, gy + 1):
            gy += 1
        return gy

    def _reset_lock(self):
        if self.locking and self._valid(self.cur, self.rot, self.cx, self.cy + 1):
            self.locking = False
            self.lock_t = 0.0

    def _lock(self):
        color = SHAPES[self.cur][1]
        for (x, y) in self._cells(self.cur, self.rot, self.cx, self.cy):
            if y < 0:
                self._game_over()
                return
            self.grid[y][x] = color
        if self.app.sfx:
            self.app.sfx.play("lock")
        self._clear_lines()
        self._spawn()

    def _clear_lines(self):
        full = [y for y in range(ROWS) if all(self.grid[y][x] is not None for x in range(COLS))]
        if not full:
            return
        n = len(full)
        for y in full:
            del self.grid[y]
            self.grid.insert(0, [None] * COLS)
        self.lines += n
        self.score += LINE_SCORE[n] * (self.level + 1)
        new_level = self.lines // 10
        if new_level > self.level:
            self.level = new_level
            if self.app.sfx:
                self.app.sfx.play("levelup")
            self.app.music_for_state()
        elif self.app.sfx:
            self.app.sfx.play("tetris" if n == 4 else "line")
        self.flash_rows = full
        self.flash_t = 0.12

    def _game_over(self):
        if self.finished:
            return
        self.finished = True
        if self.score > self.app.cfg.get("highscore", 0):
            self.app.cfg["highscore"] = self.score
            save_config(self.app.cfg)
        if self.app.sfx:
            self.app.sfx.play("defeat")

    def update(self, dt, soft):
        if self.finished:
            return
        self.flash_t = max(0.0, self.flash_t - dt)
        interval = fall_interval(self.level)
        if soft:
            interval = min(interval, 0.045)
        self.fall_t += dt
        if self.fall_t >= interval:
            self.fall_t = 0.0
            if self._valid(self.cur, self.rot, self.cx, self.cy + 1):
                self.cy += 1
                if soft:
                    self.score += 1
            else:
                self.locking = True
        if self.locking:
            self.lock_t += dt
            if not self._valid(self.cur, self.rot, self.cx, self.cy + 1):
                if self.lock_t >= 0.4:
                    self._lock()
            else:
                self.locking = False
                self.lock_t = 0.0

    # ---------- tekenen ----------
    def _cell_rect(self, x, y):
        return pygame.Rect(FIELD_X + x * CELL, FIELD_Y + y * CELL, CELL, CELL)

    def _draw_block(self, surf, x, y, color, ghost=False):
        r = self._cell_rect(x, y)
        if ghost:
            pygame.draw.rect(surf, mix(color, BG, 0.55), r, border_radius=4)
            pygame.draw.rect(surf, color, r, 2, border_radius=4)
        else:
            pygame.draw.rect(surf, color, r, border_radius=4)
            pygame.draw.rect(surf, mix(color, (0, 0, 0), 0.35), r, 2, border_radius=4)
            pygame.draw.rect(surf, mix(color, (255, 255, 255), 0.3), (r.x + 3, r.y + 3, r.w - 6, 4), border_radius=2)

    def draw(self, surf):
        # put
        pygame.draw.rect(surf, GRID_BG, (FIELD_X, FIELD_Y, FIELD_W, FIELD_H))
        for x in range(COLS + 1):
            pygame.draw.line(surf, (26, 26, 32), (FIELD_X + x * CELL, FIELD_Y), (FIELD_X + x * CELL, FIELD_Y + FIELD_H))
        for y in range(ROWS + 1):
            pygame.draw.line(surf, (26, 26, 32), (FIELD_X, FIELD_Y + y * CELL), (FIELD_X + FIELD_W, FIELD_Y + y * CELL))
        pygame.draw.rect(surf, LINE, (FIELD_X - 2, FIELD_Y - 2, FIELD_W + 4, FIELD_H + 4), 2)
        # vaste blokken
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x] is not None:
                    c = self.grid[y][x]
                    if y in self.flash_rows and self.flash_t > 0:
                        c = mix(c, (255, 255, 255), 0.7)
                    self._draw_block(surf, x, y, c)
        if self.finished:
            return
        # schaduw
        if self.app.cfg.get("ghost", True):
            gy = self.ghost_y()
            if gy != self.cy:
                for (x, y) in self._cells(self.cur, self.rot, self.cx, gy):
                    if y >= 0:
                        self._draw_block(surf, x, y, SHAPES[self.cur][1], ghost=True)
        # huidig stuk
        for (x, y) in self._cells(self.cur, self.rot, self.cx, self.cy):
            if y >= 0:
                self._draw_block(surf, x, y, SHAPES[self.cur][1])


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

        self.font_xl = pygame.font.Font(None, 80)
        self.font_l = pygame.font.Font(None, 52)
        self.font_m = pygame.font.Font(None, 34)
        self.font_s = pygame.font.Font(None, 26)

        self.sfx = None
        if sfxmod is not None:
            self.sfx = sfxmod.Sfx()
            self.sfx.init()
            self.sfx.set_enabled(self.cfg.get("sound", True))
            self.sfx.set_volume(self.cfg.get("volume", 0.8))

        self.game = None
        self.buttons = []
        self.focus = 0
        self.mouse = (0, 0)
        self.das_dir = 0
        self.das_t = 0.0
        self.das_started = False

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
        if self.state in ("title", "settings", "help", "gameover"):
            self.sfx.start_music("menu")
        elif self.state == "play":
            tracks = ["play1", "play2", "play3", "play4"]
            self.sfx.start_music(tracks[(self.game.level % 4) if self.game else 0])

    def set_state(self, s):
        self.state = s
        self.t_state = 0.0
        self.focus = 0
        self.buttons = []
        self.das_dir = 0
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
            elif e.type == pygame.KEYUP:
                self.on_key_up(e.key)
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
            self.start_game()
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
        elif a == "toggle_ghost":
            self.cfg["ghost"] = not self.cfg.get("ghost", True)
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
        return {"help": "back_title", "settings": "back_title", "pause": "resume",
                "gameover": "to_title"}.get(self.state)

    def on_key(self, key):
        if self.state == "play":
            g = self.game
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self._action("pause")
            elif key in (pygame.K_LEFT, pygame.K_a):
                g.move(-1); self.das_dir = -1; self.das_t = 0.0; self.das_started = False
            elif key in (pygame.K_RIGHT, pygame.K_d):
                g.move(1); self.das_dir = 1; self.das_t = 0.0; self.das_started = False
            elif key in (pygame.K_UP, pygame.K_x, pygame.K_w):
                g.rotate(1)
            elif key in (pygame.K_z, pygame.K_LCTRL, pygame.K_RCTRL):
                g.rotate(-1)
            elif key == pygame.K_SPACE:
                g.hard_drop()
            elif key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
                g.hold_piece()
            return
        if self.state == "gameover" and key in (pygame.K_SPACE, pygame.K_RETURN):
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

    def on_key_up(self, key):
        if key in (pygame.K_LEFT, pygame.K_a) and self.das_dir == -1:
            self.das_dir = 0
        elif key in (pygame.K_RIGHT, pygame.K_d) and self.das_dir == 1:
            self.das_dir = 0

    def on_click(self, pos, button):
        if button != 1:
            return
        for b in self.buttons:
            if b.hit(pos):
                self._action(b.action)
                return

    def start_game(self):
        self.game = Game(self)
        self.das_dir = 0
        self.set_state("play")

    def update(self, dt):
        if self.state == "play" and self.game:
            # DAS auto-herhaal voor links/rechts
            if self.das_dir != 0:
                self.das_t += dt
                if not self.das_started:
                    if self.das_t >= 0.17:
                        self.das_started = True
                        self.das_t = 0.0
                        self.game.move(self.das_dir)
                else:
                    if self.das_t >= 0.05:
                        self.das_t = 0.0
                        self.game.move(self.das_dir)
            keys = pygame.key.get_pressed()
            soft = keys[pygame.K_DOWN] or keys[pygame.K_s]
            self.game.update(dt, soft)
            if self.game.finished and self.t_state > 0.4:
                self.set_state("gameover")

    # ---------- tekenen ----------
    def draw(self):
        s = self.screen
        st = self.state
        self.buttons = []
        if st == "title":
            self._draw_title(s)
        elif st == "help":
            self._draw_help(s)
        elif st == "settings":
            self._draw_settings(s)
        elif st in ("play", "pause"):
            s.fill(BG)
            self.game.draw(s)
            self._draw_panels(s)
            if st == "pause":
                self._overlay(s, t("pauze"), [], [(t("hervat"), "resume"), (t("hoofdmenu"), "to_title")])
        elif st == "gameover":
            s.fill(BG)
            self.game.draw(s)
            self._draw_panels(s)
            self._overlay(s, t("gameover"),
                          ["%s %d   %s %d" % (t("score"), self.game.score, t("best"), self.cfg.get("highscore", 0))],
                          [(t("opnieuw"), "retry"), (t("hoofdmenu"), "to_title")], color=WARN)
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

    def _mini_piece(self, surf, piece, ox, oy, scale=20):
        cells = SHAPES[piece][0][0]
        col = SHAPES[piece][1]
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        w = (max(xs) - min(xs) + 1) * scale
        h = (max(ys) - min(ys) + 1) * scale
        bx = ox - w // 2 - min(xs) * scale
        by = oy - h // 2 - min(ys) * scale
        for (dx, dy) in cells:
            r = pygame.Rect(bx + dx * scale, by + dy * scale, scale - 2, scale - 2)
            pygame.draw.rect(surf, col, r, border_radius=3)
            pygame.draw.rect(surf, mix(col, (0, 0, 0), 0.35), r, 2, border_radius=3)

    def _panel(self, surf, x, y, w, h, title):
        pygame.draw.rect(surf, PANEL, (x, y, w, h), border_radius=10)
        pygame.draw.rect(surf, LINE, (x, y, w, h), 2, border_radius=10)
        self._text(surf, title, self.font_s, MUTED, x + w // 2, y + 18)

    def _draw_panels(self, s):
        g = self.game
        lx = FIELD_X - 200
        # Vast
        self._panel(s, lx, FIELD_Y, 180, 120, t("vast"))
        if g.hold:
            self._mini_piece(s, g.hold, lx + 90, FIELD_Y + 75)
        # rechts: volgende
        rx = FIELD_X + FIELD_W + 20
        self._panel(s, rx, FIELD_Y, 180, 230, t("volgende"))
        for i, p in enumerate(g.next_q[:3]):
            self._mini_piece(s, p, rx + 90, FIELD_Y + 70 + i * 60)
        # rechts: score
        self._panel(s, rx, FIELD_Y + 250, 180, FIELD_H - 250, "")
        yy = FIELD_Y + 272
        for label, val in [(t("score"), g.score), (t("best"), max(g.score, self.cfg.get("highscore", 0))),
                           (t("level"), g.level), (t("rijen"), g.lines)]:
            self._text(s, label, self.font_s, MUTED, rx + 90, yy)
            self._text(s, str(val), self.font_m, TEXT, rx + 90, yy + 26)
            yy += 64
        if self.state == "play":
            self._add_button(t("pauze"), (lx, FIELD_Y + 150, 180, 44), "pause", kind="back")

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
        play_like = self.state in ("play", "pause", "gameover")
        for i, b in enumerate(self.buttons):
            b.draw(s, self.font_m, hot=b.hit(self.mouse), focus=(i == self.focus and not play_like))

    def _draw_title(self, s):
        s.fill(BG)
        pygame.draw.rect(s, PANEL, (0, 0, WIDTH, 120))
        self._text(s, APP_NAME, self.font_xl, ACCENT, WIDTH // 2, 50)
        self._text(s, t("made_by"), self.font_s, MUTED, WIDTH // 2, 96)
        self._stack([(t("speel"), "play"), (t("gids"), "help"), (t("instellingen"), "settings")],
                    top=210, w=380, h=66, gap=20, kinds=["primary", "normal", "normal"])
        self._add_donate()
        self._text(s, "%s: %d" % (t("best"), self.cfg.get("highscore", 0)),
                   self.font_s, GOLD, WIDTH // 2, HEIGHT - 40)

    def _draw_help(self, s):
        s.fill(BG)
        self._text(s, t("gids"), self.font_l, ACCENT, WIDTH // 2, 70)
        y = 160
        for k in ("uitleg1", "uitleg2", "uitleg3", "uitleg4", "uitleg5"):
            self._text(s, t(k), self.font_m, TEXT, WIDTH // 2, y)
            y += 52
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 80, 220, 56), "back_title", kind="back")
        self._add_donate()

    def _draw_settings(self, s):
        s.fill(BG)
        self._text(s, t("instellingen"), self.font_l, ACCENT, WIDTH // 2, 50)
        on = lambda b: t("aan") if b else t("uit")
        lang = {"": t("auto"), "nl": "Nederlands", "en": "English"}[self.cfg.get("lang", "")]
        w = 460
        x = WIDTH // 2 - w // 2
        y = 110
        self._add_button("%s: %s" % (t("geluid"), on(self.cfg.get("sound", True))), (x, y, w, 50), "toggle_sound"); y += 60
        self._add_button("%s: %s" % (t("muziek"), on(self.cfg.get("music", True))), (x, y, w, 50), "toggle_music"); y += 60
        self._add_button("%s: %s" % (t("stem"), on(self.voice_on)), (x, y, w, 50), "toggle_voice"); y += 60
        self._add_button("%s: %s" % (t("schaduw"), on(self.cfg.get("ghost", True))), (x, y, w, 50), "toggle_ghost"); y += 60
        self._text(s, "%s: %d%%" % (t("volume"), int(self.cfg.get("volume", 0.8) * 100)),
                   self.font_m, TEXT, WIDTH // 2, y + 25)
        self._add_button("-", (x, y, 70, 50), "vol_down")
        self._add_button("+", (x + w - 70, y, 70, 50), "vol_up"); y += 60
        self._add_button("%s: %s" % (t("taal"), lang), (x, y, w, 50), "cycle_lang")
        self._add_button(t("terug"), (WIDTH // 2 - 110, HEIGHT - 66, 220, 50), "back_title", kind="back")
        self._add_donate()

    def _overlay(self, s, title, lines, buttons_def=None, color=ACCENT):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        s.blit(ov, (0, 0))
        self._text(s, title, self.font_xl, color, WIDTH // 2, 170)
        y = 250
        for ln in lines:
            self._text(s, ln, self.font_m, TEXT, WIDTH // 2, y)
            y += 44
        if buttons_def:
            self._stack(buttons_def, top=max(y + 10, 320), w=360, h=64, gap=18,
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

# -*- coding: utf-8 -*-
"""DraveHop - Frogger-stijl arcade (Dravenlock).

Een drakenjong steekt drukke wegen en een rivier over naar de nesten bovenaan.
Besturing: PIJLTJES (elke druk = 1 stap). Groot en goed leesbaar.
Weg: pas op de auto's. Rivier: spring op stammen/schildpadden, val niet in het
water. Vul alle nesten -> volgende, snellere ronde. Portable, tweetalig,
procedurele audio. Donationware.
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
        return (locale.getdefaultlocale()[0] or "").lower().startswith("nl")
    except Exception:
        return False


NL = is_nl()
TX = {
    "title": ("DraveHop", "DraveHop"),
    "sub": ("Breng de drakenjongen veilig naar de nesten",
            "Get the dragon hatchlings safely to the nests"),
    "start": ("Klik of Enter = start", "Click or Enter = start"),
    "controls": ("Pijltjes = stappen (op/neer/links/rechts)",
                 "Arrows = hop (up/down/left/right)"),
    "hint": ("Weg = ontwijk auto's. Rivier = spring op stammen/schildpadden!",
             "Road = dodge cars. River = ride logs/turtles!"),
    "score": ("Score", "Score"),
    "level": ("Ronde", "Level"),
    "lives": ("Levens", "Lives"),
    "best": ("Record", "Best"),
    "nests": ("Nesten", "Nests"),
    "gameover": ("GAME OVER", "GAME OVER"),
    "newrec": ("NIEUW RECORD!", "NEW RECORD!"),
    "levelup": ("Ronde gehaald!", "Level cleared!"),
    "again": ("Klik of Enter = opnieuw   Esc = menu", "Click or Enter = again   Esc = menu"),
    "paused": ("PAUZE", "PAUSED"),
    "resume": ("Enter = verder", "Enter = resume"),
    "donate": ("Doneren: paypal.me/roger076  -  service@dravenlock.nl",
               "Donate: paypal.me/roger076  -  service@dravenlock.nl"),
    "drown": ("PLONS!", "SPLASH!"),
    "splat": ("BOTS!", "SPLAT!"),
}


def T(k):
    v = TX.get(k, (k, k))
    return v[0] if NL else v[1]


# ---------------------------------------------------------------- layout
CELL = 64
COLS = 17
ROWS = 11                     # 0 nest, 1-4 water, 5 berm, 6-9 weg, 10 start
HUD_H = 56
MARGIN = 16
WIDTH = COLS * CELL + MARGIN * 2
HEIGHT = HUD_H + ROWS * CELL
FPS = 60

# rij-types
NEST_ROW = 0
WATER_ROWS = (1, 2, 3, 4)
MEDIAN_ROW = 5
ROAD_ROWS = (6, 7, 8, 9)
START_ROW = 10

# kleuren
C_GRASS = (46, 120, 60)
C_GRASS2 = (40, 106, 54)
C_ROAD = (52, 52, 60)
C_ROAD_LINE = (210, 200, 120)
C_WATER = (40, 90, 165)
C_WATER2 = (34, 80, 150)
C_NESTBG = (30, 70, 40)
C_NEST = (24, 20, 34)
C_TEXT = (238, 236, 246)
C_DIM = (176, 170, 200)
C_ACCENT = (181, 156, 255)
C_PANEL = (22, 19, 31)
C_DRAGON = (110, 205, 120)
C_DRAGON_D = (70, 150, 84)
CAR_COLORS = [(220, 70, 70), (70, 150, 240), (240, 190, 70),
              (200, 110, 220), (240, 140, 60)]
LOG_COL = (120, 82, 46)
LOG_DK = (92, 60, 32)
TURT_COL = (80, 175, 120)


def cell_x(col):
    return MARGIN + col * CELL


def row_y(row):
    return HUD_H + row * CELL


# ---------------------------------------------------------------- objecten
class Mover:
    """Auto (weg) of stam/schildpad (rivier)."""
    def __init__(self, row, x, cells, speed, kind, color):
        self.row = row
        self.x = float(x)                # linkerrand in px
        self.w = cells * CELL
        self.speed = speed               # px/s (teken; + = rechts)
        self.kind = kind                 # "car" | "log" | "turtle"
        self.color = color

    def update(self, dt):
        self.x += self.speed * dt
        span = WIDTH
        if self.speed > 0 and self.x > span + 10:
            self.x = -self.w - random.randint(0, CELL)
        elif self.speed < 0 and self.x + self.w < -10:
            self.x = span + random.randint(0, CELL)

    def rect(self):
        return pygame.Rect(int(self.x), row_y(self.row) + 6, int(self.w), CELL - 12)


# ---------------------------------------------------------------- audio
class Audio:
    def __init__(self):
        self.ok = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.ok = True
        except Exception:
            self.ok = False
        if self.ok:
            self.hop = self._blip(660, 0.06)
            self.splash = self._splash()
            self.crash = self._crash()
            self.win = self._chime()
            self.over = self._down()

    def _snd(self, s):
        return pygame.mixer.Sound(buffer=array.array("h", s).tobytes())

    def _blip(self, f, dur, vol=0.35):
        rate = 22050
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = max(0.0, 1 - t / dur)
            fr = f * (1 + 2 * t)
            out.append(int(math.sin(2 * math.pi * fr * t) * env * vol * 32767))
        return self._snd(out)

    def _splash(self):
        rate = 22050
        dur = 0.25
        n = int(rate * dur)
        out = []
        seed = 7
        for i in range(n):
            t = i / rate
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            noise = (seed / 0x7fffffff) * 2 - 1
            env = max(0.0, 1 - t / dur)
            out.append(int(noise * env * env * 0.4 * 32767))
        return self._snd(out)

    def _crash(self):
        rate = 22050
        dur = 0.22
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = max(0.0, 1 - t / dur)
            s = math.sin(2 * math.pi * (180 - 300 * t) * t)
            out.append(int(s * env * 0.5 * 32767))
        return self._snd(out)

    def _chime(self):
        rate = 22050
        out = []
        for f, d in ((523, 0.1), (659, 0.1), (784, 0.1), (1046, 0.18)):
            n = int(rate * d)
            for i in range(n):
                t = i / rate
                env = min(1.0, t * 30) * max(0.0, 1 - t / d)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.32 * 32767))
        return self._snd(out)

    def _down(self):
        rate = 22050
        out = []
        for f, d in ((523, 0.12), (392, 0.12), (262, 0.22)):
            n = int(rate * d)
            for i in range(n):
                t = i / rate
                env = max(0.0, 1 - t / d)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.3 * 32767))
        return self._snd(out)

    def play(self, s):
        if self.ok and s:
            try:
                s.play()
            except Exception:
                pass


# ---------------------------------------------------------------- tekenen draak
def draw_dragon(surf, cx, cy, r=24, facing=0, color=C_DRAGON):
    """Klein drakenjong: lijf, horens, vleugeltjes, ogen, staart."""
    dark = C_DRAGON_D
    dk = (24, 40, 28)
    # staart
    pygame.draw.line(surf, dark, (cx, cy + r - 2), (cx - facing * (r + 6), cy + r + 4), 7)
    # vleugels
    for s in (-1, 1):
        pygame.draw.polygon(surf, dark, [(cx, cy - 4),
                                         (cx + s * (r + 8), cy - r),
                                         (cx + s * (r - 2), cy + 6)])
    # lijf
    pygame.draw.circle(surf, color, (cx, cy), r)
    pygame.draw.circle(surf, dark, (cx, cy), r, 3)
    # buik
    pygame.draw.circle(surf, (200, 230, 200), (cx, cy + 4), r - 9)
    # horens
    pygame.draw.line(surf, dk, (cx - 7, cy - r + 4), (cx - 11, cy - r - 8), 5)
    pygame.draw.line(surf, dk, (cx + 7, cy - r + 4), (cx + 11, cy - r - 8), 5)
    # ogen (richting facing)
    ex = facing * 6
    pygame.draw.circle(surf, (255, 255, 255), (cx - 8 + ex, cy - 6), 6)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 8 + ex, cy - 6), 6)
    pygame.draw.circle(surf, dk, (cx - 8 + ex + facing * 2, cy - 6), 3)
    pygame.draw.circle(surf, dk, (cx + 8 + ex + facing * 2, cy - 6), 3)
    # neusgaten
    pygame.draw.circle(surf, dk, (cx - 4, cy + 8), 2)
    pygame.draw.circle(surf, dk, (cx + 4, cy + 8), 2)


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
        pygame.display.set_caption("DraveHop")
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arial", 64, bold=True)
        self.mid = pygame.font.SysFont("arial", 36, bold=True)
        self.font = pygame.font.SysFont("consolas,arial", 28, bold=True)
        self.small = pygame.font.SysFont("consolas,arial", 20)
        self.audio = Audio()
        self.scores = self._load()
        self.state = "menu"
        self.msg = ""
        self.msg_t = 0.0
        self.n_nests = 5
        self.reset_game()

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

    def reset_game(self):
        self.level = 1
        self.score = 0
        self.lives = 3
        self.best = self.scores.get("best", 0)
        self.nests = [False] * self.n_nests
        self._build_lanes()
        self._spawn_player()

    def _spawn_player(self):
        self.px = cell_x(COLS // 2) + CELL / 2
        self.py_row = START_ROW
        self.pfacing = 0
        self.on_log = None
        self.dead_t = 0.0

    def _build_lanes(self):
        self.movers = []
        base = 70 + self.level * 16
        # weg-banen
        for i, row in enumerate(ROAD_ROWS):
            direction = 1 if row % 2 == 0 else -1
            speed = direction * (base + i * 14) * random.uniform(0.9, 1.2)
            cells = random.choice([1, 1, 2])
            gap = random.randint(3, 4) * CELL
            n = 3
            for k in range(n):
                x = k * (WIDTH // n) + random.randint(0, CELL)
                self.movers.append(Mover(row, x, cells, speed, "car",
                                         random.choice(CAR_COLORS)))
        # rivier-banen
        for i, row in enumerate(WATER_ROWS):
            direction = 1 if row % 2 == 0 else -1
            speed = direction * (base * 0.7 + i * 10) * random.uniform(0.9, 1.15)
            kind = "turtle" if i % 3 == 2 else "log"
            cells = 3 if kind == "log" else 2
            n = 3
            for k in range(n):
                x = k * (WIDTH // n) + random.randint(0, CELL)
                self.movers.append(Mover(row, x, cells, speed, kind,
                                         LOG_COL if kind == "log" else TURT_COL))

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
                    self.on_click()
            if self.state == "play":
                self.update(dt)
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

    def on_click(self):
        if self.state == "menu":
            self.reset_game()
            self.state = "play"
        elif self.state == "over":
            self.reset_game()
            self.state = "play"

    def on_key(self, key):
        if self.state == "menu":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.reset_game()
                self.state = "play"
            elif key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == "play":
            if key == pygame.K_ESCAPE:
                self.state = "paused"
            elif self.dead_t <= 0:
                if key == pygame.K_UP:
                    self.hop(0, -1)
                elif key == pygame.K_DOWN:
                    self.hop(0, 1)
                elif key == pygame.K_LEFT:
                    self.hop(-1, 0)
                elif key == pygame.K_RIGHT:
                    self.hop(1, 0)
        elif self.state == "paused":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "play"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
        elif self.state == "over":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.reset_game()
                self.state = "play"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"

    def hop(self, dx, dy):
        if dx:
            self.pfacing = 1 if dx > 0 else -1
        nr = self.py_row + dy
        if nr < 0 or nr > START_ROW:
            return
        self.px += dx * CELL
        self.px = max(cell_x(0) + CELL / 2, min(cell_x(COLS - 1) + CELL / 2, self.px))
        self.py_row = nr
        self.audio.play(self.audio.hop)
        if dy < 0 and nr != NEST_ROW:
            self.score += 10
        if nr == NEST_ROW:
            self._reach_nest()

    def _reach_nest(self):
        # dichtstbijzijnde nest-slot
        slot_w = (COLS * CELL) / self.n_nests
        idx = int((self.px - MARGIN) / slot_w)
        idx = max(0, min(self.n_nests - 1, idx))
        if self.nests[idx]:
            self.die("splat")       # al bezet -> mislukt
            return
        self.nests[idx] = True
        self.score += 60
        self.audio.play(self.audio.win)
        if all(self.nests):
            self.level += 1
            self.score += 200
            self.nests = [False] * self.n_nests
            self._build_lanes()
            self.flash(T("levelup"))
        self._spawn_player()

    def die(self, why):
        if self.dead_t > 0:
            return
        self.lives -= 1
        self.dead_t = 0.9
        self.flash(T("drown") if why == "drown" else T("splat"))
        self.audio.play(self.audio.splash if why == "drown" else self.audio.crash)
        if self.lives <= 0:
            if self.score > self.best:
                self.best = self.score
                self.scores["best"] = self.best
                self._save()
            self.state = "over"
            self.audio.play(self.audio.over)

    def flash(self, m):
        self.msg = m
        self.msg_t = 1.2

    # ---- update ----
    def update(self, dt):
        for m in self.movers:
            m.update(dt)
        if self.dead_t > 0:
            self.dead_t -= dt
            if self.dead_t <= 0 and self.state == "play":
                self._spawn_player()
            return
        row = self.py_row
        prect = pygame.Rect(int(self.px - 22), row_y(row) + 8, 44, CELL - 16)
        if row in ROAD_ROWS:
            for m in self.movers:
                if m.row == row and m.rect().colliderect(prect):
                    self.die("splat")
                    return
        elif row in WATER_ROWS:
            carried = None
            for m in self.movers:
                if m.row == row and m.rect().colliderect(prect):
                    carried = m
                    break
            if carried is None:
                self.die("drown")
                return
            self.px += carried.speed * dt
            if self.px < cell_x(0) or self.px > cell_x(COLS - 1) + CELL:
                self.die("drown")
                return

    # ---- tekenen ----
    def draw(self):
        s = self.screen
        if self.state == "menu":
            self.draw_menu()
            pygame.display.flip()
            return
        s.fill(C_PANEL)
        self._draw_field()
        for m in self.movers:
            self._draw_mover(m)
        self._draw_nests()
        if self.dead_t <= 0 or int(self.dead_t * 10) % 2 == 0:
            draw_dragon(s, int(self.px), row_y(self.py_row) + CELL // 2,
                        r=CELL // 2 - 8, facing=self.pfacing)
        self._draw_hud()
        # blijvende besturingshint onderaan
        hint = self.font.render(
            ("Pijltjes = springen  " + chr(0x2191) + chr(0x2193)
             + chr(0x2190) + chr(0x2192)) if NL else
            ("Arrows = hop  " + chr(0x2191) + chr(0x2193) + chr(0x2190) + chr(0x2192)),
            True, C_TEXT)
        hb = pygame.Surface((hint.get_width() + 24, hint.get_height() + 10),
                            pygame.SRCALPHA)
        hb.fill((14, 11, 22, 170))
        s.blit(hb, (WIDTH // 2 - hb.get_width() // 2, HEIGHT - hint.get_height() - 14))
        s.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - hint.get_height() - 9))
        if self.msg_t > 0:
            self._banner(self.msg)
        if self.state == "paused":
            self._overlay(T("paused"), T("resume"))
        elif self.state == "over":
            self._draw_over()
        pygame.display.flip()

    def _draw_field(self):
        s = self.screen
        for row in range(ROWS):
            y = row_y(row)
            if row == NEST_ROW:
                col = C_NESTBG
            elif row in WATER_ROWS:
                col = C_WATER if row % 2 == 0 else C_WATER2
            elif row in ROAD_ROWS:
                col = C_ROAD
            else:
                col = C_GRASS if row % 2 == 0 else C_GRASS2
            pygame.draw.rect(s, col, (0, y, WIDTH, CELL))
            # weg-strepen
            if row in ROAD_ROWS:
                for x in range(MARGIN, WIDTH, CELL):
                    pygame.draw.rect(s, C_ROAD_LINE, (x + CELL // 2 - 12, y + CELL // 2 - 3, 24, 6))

    def _draw_mover(self, m):
        s = self.screen
        r = m.rect()
        if m.kind == "car":
            pygame.draw.rect(s, m.color, r, border_radius=10)
            pygame.draw.rect(s, (20, 20, 26), r, 3, border_radius=10)
            # ruit
            ww = r.width // 3
            pygame.draw.rect(s, (200, 225, 245),
                             (r.centerx - ww // 2, r.y + 6, ww, r.height - 12), border_radius=4)
            # wielen
            for wx in (r.x + 12, r.right - 12):
                pygame.draw.circle(s, (15, 15, 18), (wx, r.bottom), 6)
        elif m.kind == "log":
            pygame.draw.rect(s, LOG_COL, r, border_radius=12)
            pygame.draw.rect(s, LOG_DK, r, 3, border_radius=12)
            for lx in range(r.x + 12, r.right - 8, 18):
                pygame.draw.line(s, LOG_DK, (lx, r.y + 6), (lx, r.bottom - 6), 2)
            pygame.draw.circle(s, LOG_DK, (r.x + 8, r.centery), 7, 2)
            pygame.draw.circle(s, LOG_DK, (r.right - 8, r.centery), 7, 2)
        else:  # turtle(s)
            n = max(1, r.width // CELL)
            for k in range(n):
                cxk = r.x + CELL // 2 + k * CELL
                pygame.draw.circle(s, TURT_COL, (cxk, r.centery), CELL // 2 - 10)
                pygame.draw.circle(s, (50, 130, 90), (cxk, r.centery), CELL // 2 - 10, 3)
                pygame.draw.circle(s, (40, 110, 76), (cxk, r.centery), 5)

    def _draw_nests(self):
        s = self.screen
        slot_w = (COLS * CELL) / self.n_nests
        for i in range(self.n_nests):
            cx = int(MARGIN + slot_w * (i + 0.5))
            cy = row_y(NEST_ROW) + CELL // 2
            pygame.draw.circle(s, C_NEST, (cx, cy), CELL // 2 - 8)
            pygame.draw.circle(s, (60, 120, 70), (cx, cy), CELL // 2 - 8, 3)
            if self.nests[i]:
                draw_dragon(s, cx, cy, r=CELL // 2 - 14, facing=0)

    def _draw_hud(self):
        s = self.screen
        pygame.draw.rect(s, C_PANEL, (0, 0, WIDTH, HUD_H))
        s.blit(self.font.render("%s: %d" % (T("score"), self.score), True, C_TEXT), (16, 12))
        lvl = self.font.render("%s %d" % (T("level"), self.level), True, C_ACCENT)
        s.blit(lvl, (WIDTH // 2 - lvl.get_width() // 2, 12))
        # levens als drakenkopjes
        lx = WIDTH - 20
        for i in range(self.lives):
            draw_dragon(s, lx - 24 - i * 40, HUD_H // 2, r=14, facing=-1)
        bt = self.small.render("%s: %d" % (T("best"), self.best), True, C_DIM)
        s.blit(bt, (WIDTH - 20 - bt.get_width(), HUD_H - 22))

    def _banner(self, text):
        s = self.screen
        r = self.mid.render(text, True, C_TEXT)
        bg = pygame.Surface((r.get_width() + 40, r.get_height() + 16), pygame.SRCALPHA)
        bg.fill((14, 11, 22, 210))
        s.blit(bg, (WIDTH // 2 - bg.get_width() // 2, HEIGHT // 2 - 30))
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 22))

    def _overlay(self, title, sub):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 170))
        s.blit(ov, (0, 0))
        r = self.big.render(title, True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 70))
        r2 = self.mid.render(sub, True, C_TEXT)
        s.blit(r2, (WIDTH // 2 - r2.get_width() // 2, HEIGHT // 2 + 20))

    def _draw_over(self):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 190))
        s.blit(ov, (0, 0))
        r = self.big.render(T("gameover"), True, (240, 110, 110))
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 110))
        r = self.mid.render("%s: %d" % (T("score"), self.score), True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 40))
        if self.score >= self.best and self.score > 0:
            r = self.mid.render(T("newrec"), True, (250, 220, 90))
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 + 6))
        r = self.font.render(T("again"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 60))

    def draw_menu(self):
        s = self.screen
        s.fill(C_PANEL)
        # sfeer: wat banen tekenen
        for row in range(ROWS):
            y = row_y(row)
            if row in WATER_ROWS:
                col = C_WATER
            elif row in ROAD_ROWS:
                col = C_ROAD
            else:
                col = C_GRASS
            pygame.draw.rect(s, col, (0, y, WIDTH, CELL))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 8, 16, 150))
        s.blit(ov, (0, 0))
        r = self.big.render(T("title"), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 70))
        r = self.font.render(T("sub"), True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 150))
        try:
            lp = os.path.join(app_dir(), "assets", "logo.png")
            if os.path.exists(lp):
                img = pygame.image.load(lp).convert_alpha()
                img = pygame.transform.smoothscale(img, (110, 110))
                s.blit(img, (WIDTH // 2 - 55, 195))
        except Exception:
            pass
        draw_dragon(s, WIDTH // 2, 360, r=40, facing=1)
        for i, line in enumerate((T("start"), T("controls"), T("hint"))):
            fnt = self.mid if i == 0 else self.font
            col = C_TEXT if i == 0 else C_DIM
            r = fnt.render(line, True, col)
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, 430 + i * 44))
        best = self.scores.get("best", 0)
        r = self.font.render("%s: %d" % (T("best"), best), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 580))
        r = self.small.render(T("donate"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 30))


def main():
    selftest = 0
    if "--selftest" in sys.argv:
        try:
            selftest = int(sys.argv[sys.argv.index("--selftest") + 1])
        except Exception:
            selftest = 120
    g = Game()
    if selftest:
        g.reset_game()
        g.state = "play"
    g.run(selftest=selftest)


if __name__ == "__main__":
    main()

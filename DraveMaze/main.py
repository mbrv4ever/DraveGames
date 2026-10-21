# -*- coding: utf-8 -*-
"""DraveMaze - Pac-Man-stijl arcade (Dravenlock).

Een draak eet het doolhof leeg terwijl spoken hem achtervolgen. Pak een power-pil
om de spoken tijdelijk bang (en eetbaar) te maken. Alles opgegeten = volgende,
snellere ronde. Besturing: PIJLTJES (richting aanhouden, bochten op kruispunten).
Portable, tweetalig, procedurele audio. Donationware.
"""
import os
import sys
import math
import json
import locale
import random
import array
from collections import deque

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
    "title": ("DraveMaze", "DraveMaze"),
    "sub": ("Eet het doolhof leeg, ontwijk de spoken",
            "Eat the maze, dodge the ghosts"),
    "start": ("Klik of Enter = start", "Click or Enter = start"),
    "controls": ("Pijltjes = bewegen", "Arrows = move"),
    "hint": ("Power-pil (groot) = spoken worden even eetbaar!",
             "Power pill (big) = ghosts become edible for a bit!"),
    "score": ("Score", "Score"),
    "level": ("Ronde", "Level"),
    "best": ("Record", "Best"),
    "ready": ("KLAAR?", "READY?"),
    "gameover": ("GAME OVER", "GAME OVER"),
    "clear": ("Ronde gehaald!", "Level cleared!"),
    "newrec": ("NIEUW RECORD!", "NEW RECORD!"),
    "again": ("Klik of Enter = opnieuw   Esc = menu",
              "Click or Enter = again   Esc = menu"),
    "paused": ("PAUZE", "PAUSED"),
    "resume": ("Enter = verder", "Enter = resume"),
    "donate": ("Doneren: paypal.me/roger076  -  service@dravenlock.nl",
               "Donate: paypal.me/roger076  -  service@dravenlock.nl"),
}


def T(k):
    v = TX.get(k, (k, k))
    return v[0] if NL else v[1]


# ---------------------------------------------------------------- layout
GW, GH = 9, 10                    # doolhof-cellen
W = 2 * GW + 1                    # 19 tegels breed
H = 2 * GH + 1                    # 21 tegels hoog
TILE = 38
HUD_H = 58
MARGIN = 14
WIDTH = W * TILE + MARGIN * 2
HEIGHT = HUD_H + H * TILE + MARGIN
FPS = 60

C_BG = (14, 12, 22)
C_WALL = (44, 42, 120)
C_WALL2 = (70, 66, 175)
C_PELLET = (250, 224, 150)
C_POWER = (255, 180, 90)
C_TEXT = (238, 236, 246)
C_DIM = (176, 170, 200)
C_ACCENT = (181, 156, 255)
C_DRAGON = (120, 210, 130)
C_DRAGON_D = (70, 150, 84)
GHOST_COLORS = [(230, 80, 90), (240, 150, 200), (110, 200, 235)]
C_FRIGHT = (70, 90, 230)
C_FRIGHT2 = (200, 200, 255)


def tcx(col):
    return MARGIN + col * TILE + TILE // 2


def tcy(row):
    return HUD_H + row * TILE + TILE // 2


# ---------------------------------------------------------------- doolhof
def gen_maze():
    """Recursieve-backtracker + braiding (lussen). ' '=open, '#'=muur."""
    grid = [['#'] * W for _ in range(H)]
    vis = [[False] * GW for _ in range(GH)]
    sys.setrecursionlimit(10000)

    def carve(cx, cy):
        vis[cy][cx] = True
        grid[2 * cy + 1][2 * cx + 1] = ' '
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < GW and 0 <= ny < GH and not vis[ny][nx]:
                grid[2 * cy + 1 + dy][2 * cx + 1 + dx] = ' '
                carve(nx, ny)

    carve(0, 0)
    # braiding: dood-lopende cellen extra verbinden -> lussen (Pac-Man-gevoel)
    for cy in range(GH):
        for cx in range(GW):
            tx, ty = 2 * cx + 1, 2 * cy + 1
            opens = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                     if grid[ty + dy][tx + dx] == ' ']
            if len(opens) <= 1:
                cand = [(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 < tx + dx < W - 1 and 0 < ty + dy < H - 1
                        and grid[ty + dy][tx + dx] == '#']
                if cand:
                    dx, dy = random.choice(cand)
                    grid[ty + dy][tx + dx] = ' '
    return grid


def build_level():
    """Geef (grid met pellets, spawnhuis-tegels, spelerstart)."""
    for _ in range(30):
        g = gen_maze()
        # ghost-huis: midden 3x1 openmaken
        hcx, hcy = W // 2, H // 2
        house = []
        for dx in (-1, 0, 1):
            g[hcy][hcx + dx] = ' '
            house.append((hcx + dx, hcy))
        # opening naar boven
        g[hcy - 1][hcx] = ' '
        # speler-start: onderaan-midden, dichtstbijzijnde open tegel
        start = None
        for r in range(H - 2, 0, -1):
            if g[r][W // 2] == ' ':
                start = (W // 2, r)
                break
        if not start:
            continue
        # connectiviteit check (flood fill vanaf start)
        seen = set([start])
        dq = deque([start])
        while dq:
            cx, cy = dq.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < W and 0 <= ny < H and g[ny][nx] != '#' and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    dq.append((nx, ny))
        open_tiles = [(x, y) for y in range(H) for x in range(W) if g[y][x] != '#']
        if len(seen) != len(open_tiles):
            continue
        # pellets op alle open tegels behalve huis + start
        for (x, y) in open_tiles:
            if (x, y) in house or (x, y) == start or (x, y) == (hcx, hcy - 1):
                g[y][x] = ' '
            else:
                g[y][x] = '.'
        # power-pillen: dichtst bij de 4 hoeken
        corners = [(1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2)]
        for (cxc, cyc) in corners:
            best = None
            bd = 1e9
            for (x, y) in open_tiles:
                if g[y][x] == '.':
                    d = (x - cxc) ** 2 + (y - cyc) ** 2
                    if d < bd:
                        bd = d
                        best = (x, y)
            if best:
                g[best[1]][best[0]] = 'o'
        return g, house, start
    # fallback: leeg kader
    return gen_maze(), [(W // 2, H // 2)], (1, 1)


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
            self.chomp = self._blip(430, 0.05)
            self.chomp2 = self._blip(320, 0.05)
            self.power = self._chime()
            self.eat = self._blip(880, 0.12, up=True)
            self.death = self._down()

    def _snd(self, s):
        return pygame.mixer.Sound(buffer=array.array("h", s).tobytes())

    def _blip(self, f, dur, vol=0.3, up=False):
        rate = 22050
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = max(0.0, 1 - t / dur)
            fr = f * (1 + (2 * t if up else 0))
            out.append(int((1 if (fr * t) % 1 < 0.5 else -1) * env * vol * 32767))
        return self._snd(out)

    def _chime(self):
        rate = 22050
        out = []
        for f, d in ((523, 0.09), (784, 0.09), (1046, 0.14)):
            n = int(rate * d)
            for i in range(n):
                t = i / rate
                env = min(1.0, t * 30) * max(0.0, 1 - t / d)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.3 * 32767))
        return self._snd(out)

    def _down(self):
        rate = 22050
        out = []
        for f, d in ((660, 0.12), (500, 0.12), (330, 0.24)):
            n = int(rate * d)
            for i in range(n):
                t = i / rate
                env = max(0.0, 1 - t / d)
                out.append(int(math.sin(2 * math.pi * f * t) * env * 0.32 * 32767))
        return self._snd(out)

    def play(self, s):
        if self.ok and s:
            try:
                s.play()
            except Exception:
                pass


# ---------------------------------------------------------------- entiteiten
class Ent:
    def __init__(self, col, row):
        self.px = float(tcx(col))
        self.py = float(tcy(row))
        self.dir = (0, 0)
        self.want = (0, 0)

    def tile(self):
        col = int(round((self.px - MARGIN - TILE / 2) / TILE))
        row = int(round((self.py - HUD_H - TILE / 2) / TILE))
        return col, row

    def centered(self, speed):
        col, row = self.tile()
        return abs(self.px - tcx(col)) <= speed and abs(self.py - tcy(row)) <= speed


class Ghost(Ent):
    def __init__(self, col, row, color):
        super().__init__(col, row)
        self.color = color
        self.home = (col, row)
        self.fright = 0.0
        self.dir = (0, -1)


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
        pygame.display.set_caption("DraveMaze")
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arial", 60, bold=True)
        self.mid = pygame.font.SysFont("arial", 34, bold=True)
        self.font = pygame.font.SysFont("consolas,arial", 26, bold=True)
        self.small = pygame.font.SysFont("consolas,arial", 19)
        self.audio = Audio()
        self.scores = self._load()
        self.state = "menu"
        self.msg = ""
        self.msg_t = 0.0
        self.anim = 0.0
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
        self._new_level()

    def _new_level(self):
        self.grid, self.house, self.start = build_level()
        self.pellets = sum(row.count('.') + row.count('o') for row in self.grid)
        self._spawn_actors()
        self.ready_t = 1.3

    def _spawn_actors(self):
        self.player = Ent(*self.start)
        self.player.dir = (0, 0)
        self.player.want = (0, 0)
        self.ghosts = []
        hcx, hcy = W // 2, H // 2
        spots = [(hcx, hcy - 1), (hcx - 1, hcy), (hcx + 1, hcy)]
        for i in range(3):
            gx, gy = spots[i % len(spots)]
            self.ghosts.append(Ghost(gx, gy, GHOST_COLORS[i]))
        self.dead_t = 0.0

    def is_wall(self, col, row):
        if col < 0 or col >= W or row < 0 or row >= H:
            return True
        return self.grid[row][col] == '#'

    # ---- lus ----
    def run(self, selftest=0):
        running = True
        frames = 0
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.anim += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    self.on_key(ev.key)
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click()
            keys = pygame.key.get_pressed()
            if self.state == "play":
                self.update(dt, keys)
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
        if self.state in ("menu", "over"):
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
            elif key == pygame.K_UP:
                self.player.want = (0, -1)
            elif key == pygame.K_DOWN:
                self.player.want = (0, 1)
            elif key == pygame.K_LEFT:
                self.player.want = (-1, 0)
            elif key == pygame.K_RIGHT:
                self.player.want = (1, 0)
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

    # ---- update ----
    def update(self, dt, keys):
        if self.ready_t > 0:
            self.ready_t -= dt
            return
        if self.dead_t > 0:
            self.dead_t -= dt
            if self.dead_t <= 0:
                self._spawn_actors()
                self.ready_t = 0.8
            return
        pspd = 2.6 + 0.06 * self.level
        gspd = min(pspd - 0.35, 2.2 + 0.09 * self.level)
        self._move_player(pspd)
        for g in self.ghosts:
            self._move_ghost(g, gspd)
        self._collisions()

    @staticmethod
    def _reached(e, cx, cy, speed):
        """True als e dit frame het tegelmidden (cx,cy) bereikt/gepasseerd is."""
        dx, dy = e.dir
        if dx == 0 and dy == 0:
            return True
        if dx > 0:
            return e.px >= cx and (e.px - speed) < cx
        if dx < 0:
            return e.px <= cx and (e.px + speed) > cx
        if dy > 0:
            return e.py >= cy and (e.py - speed) < cy
        return e.py <= cy and (e.py + speed) > cy

    def _move_player(self, speed):
        p = self.player
        col, row = p.tile()
        cx, cy = tcx(col), tcy(row)
        # eerst bewegen, dan kijken of we het midden passeerden
        p.px += p.dir[0] * speed
        p.py += p.dir[1] * speed
        if not self._reached(p, cx, cy, speed):
            return
        p.px, p.py = cx, cy
        # richting bijstellen op het tegelmidden
        if p.want != (0, 0) and not self.is_wall(col + p.want[0], row + p.want[1]):
            p.dir = p.want
        if self.is_wall(col + p.dir[0], row + p.dir[1]):
            p.dir = (0, 0)
        # eten
        tile = self.grid[row][col]
        if tile == '.':
            self.grid[row][col] = ' '
            self.pellets -= 1
            self.score += 10
            self.audio.play(self.audio.chomp if (self.pellets % 2) else self.audio.chomp2)
        elif tile == 'o':
            self.grid[row][col] = ' '
            self.pellets -= 1
            self.score += 50
            for g in self.ghosts:
                g.fright = 6.0
            self.audio.play(self.audio.power)
        if self.pellets <= 0:
            self.level += 1
            self.score += 300
            self.flash(T("clear"))
            self._new_level()

    def _move_ghost(self, g, speed):
        if g.fright > 0:
            g.fright -= 1 / 60.0
            speed *= 0.6
        col, row = g.tile()
        cx, cy = tcx(col), tcy(row)
        g.px += g.dir[0] * speed
        g.py += g.dir[1] * speed
        if not self._reached(g, cx, cy, speed):
            return
        g.px, g.py = cx, cy
        # kies richting op het tegelmidden (niet omkeren)
        opts = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (dx, dy) == (-g.dir[0], -g.dir[1]):
                continue
            if not self.is_wall(col + dx, row + dy):
                opts.append((dx, dy))
        if not opts:
            opts = [(-g.dir[0], -g.dir[1])]
        tgt = self.player.tile()
        if g.fright > 0:
            g.dir = random.choice(opts)
        else:
            best, bd = opts[0], 1e9
            for (dx, dy) in opts:
                d = (col + dx - tgt[0]) ** 2 + (row + dy - tgt[1]) ** 2
                if d < bd:
                    bd = d
                    best = (dx, dy)
            g.dir = best

    def _collisions(self):
        p = self.player
        for g in self.ghosts:
            if abs(p.px - g.px) < TILE * 0.6 and abs(p.py - g.py) < TILE * 0.6:
                if g.fright > 0:
                    g.fright = 0.0
                    hx, hy = g.home
                    g.px, g.py = tcx(hx), tcy(hy)
                    g.dir = (0, -1)
                    self.score += 200
                    self.audio.play(self.audio.eat)
                else:
                    self._die()
                    return

    def _die(self):
        self.lives -= 1
        self.audio.play(self.audio.death)
        if self.lives <= 0:
            if self.score > self.best:
                self.best = self.score
                self.scores["best"] = self.best
                self._save()
            self.state = "over"
        else:
            self.dead_t = 1.0

    def flash(self, m):
        self.msg = m
        self.msg_t = 1.2

    # ---- tekenen ----
    def draw(self):
        s = self.screen
        if self.state == "menu":
            self.draw_menu()
            pygame.display.flip()
            return
        s.fill(C_BG)
        self._draw_maze()
        for g in self.ghosts:
            self._draw_ghost(g)
        if self.dead_t <= 0 or int(self.dead_t * 10) % 2 == 0:
            self._draw_player()
        self._draw_hud()
        if self.ready_t > 0:
            self._banner(T("ready"), C_ACCENT)
        elif self.msg_t > 0:
            self._banner(self.msg, C_TEXT)
        if self.state == "paused":
            self._overlay(T("paused"), T("resume"))
        elif self.state == "over":
            self._draw_over()
        pygame.display.flip()

    def _draw_maze(self):
        s = self.screen
        for y in range(H):
            for x in range(W):
                t = self.grid[y][x]
                cx, cy = tcx(x), tcy(y)
                if t == '#':
                    rect = pygame.Rect(MARGIN + x * TILE + 3, HUD_H + y * TILE + 3,
                                       TILE - 6, TILE - 6)
                    pygame.draw.rect(s, C_WALL, rect, border_radius=7)
                    pygame.draw.rect(s, C_WALL2, rect, 2, border_radius=7)
                elif t == '.':
                    pygame.draw.circle(s, C_PELLET, (cx, cy), 4)
                elif t == 'o':
                    r = 8 + int(2 * math.sin(self.anim * 6))
                    pygame.draw.circle(s, C_POWER, (cx, cy), r)

    def _draw_player(self):
        s = self.screen
        p = self.player
        cx, cy = int(p.px), int(p.py)
        r = TILE // 2 - 3
        # richting-hoek
        d = p.dir if p.dir != (0, 0) else (1, 0)
        ang = math.atan2(d[1], d[0])
        mouth = (0.12 + 0.30 * (0.5 + 0.5 * math.sin(self.anim * 14))) * math.pi
        # drakenkop (chomp)
        pts = [(cx, cy)]
        a = ang + mouth
        steps = 22
        while a <= ang + 2 * math.pi - mouth + 0.001:
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            a += (2 * math.pi - 2 * mouth) / steps
        pygame.draw.polygon(s, C_DRAGON, pts)
        pygame.draw.polygon(s, C_DRAGON_D, pts, 2)
        # horens (haaks op richting, aan de bovenkant)
        bx, by = -d[0], -d[1]
        hxp, hyp = cx - d[1] * r * 0.5, cy + d[0] * r * 0.5
        pygame.draw.line(s, (24, 40, 28), (cx - d[1] * r, cy + d[0] * r),
                         (cx - d[1] * (r + 8) - d[0] * 4, cy + d[0] * (r + 8) - d[1] * 4), 4)
        pygame.draw.line(s, (24, 40, 28), (cx + d[1] * r, cy - d[0] * r),
                         (cx + d[1] * (r + 8) - d[0] * 4, cy - d[0] * (r + 8) - d[1] * 4), 4)
        # oog
        ex = cx + d[0] * 3 - d[1] * 6
        ey = cy + d[1] * 3 + d[0] * 6
        pygame.draw.circle(s, (255, 255, 255), (int(ex), int(ey)), 5)
        pygame.draw.circle(s, (20, 30, 24), (int(ex + d[0] * 2), int(ey + d[1] * 2)), 2)

    def _draw_ghost(self, g):
        s = self.screen
        cx, cy = int(g.px), int(g.py)
        r = TILE // 2 - 3
        if g.fright > 0:
            body = C_FRIGHT if (g.fright > 1.6 or int(g.fright * 6) % 2 == 0) else C_FRIGHT2
        else:
            body = g.color
        top = cy - r
        pygame.draw.circle(s, body, (cx, cy - 2), r)
        pygame.draw.rect(s, body, (cx - r, cy - 2, 2 * r, r))
        # golvende onderrand
        pts = []
        n = 4
        for i in range(n + 1):
            x = cx - r + (2 * r) * i / n
            y = cy + r - 2 + (5 if i % 2 == 0 else -3)
            pts.append((x, y))
        pts += [(cx + r, cy - 2), (cx - r, cy - 2)]
        pygame.draw.polygon(s, body, pts)
        # ogen
        d = g.dir if g.dir != (0, 0) else (0, 1)
        for sx in (-1, 1):
            ecx, ecy = cx + sx * 7, cy - 4
            pygame.draw.circle(s, (255, 255, 255), (ecx, ecy), 6)
            pygame.draw.circle(s, (30, 30, 60),
                               (int(ecx + d[0] * 3), int(ecy + d[1] * 3)), 3)

    def _draw_hud(self):
        s = self.screen
        pygame.draw.rect(s, C_BG, (0, 0, WIDTH, HUD_H))
        s.blit(self.font.render("%s: %d" % (T("score"), self.score), True, C_TEXT), (14, 14))
        lv = self.font.render("%s %d" % (T("level"), self.level), True, C_ACCENT)
        s.blit(lv, (WIDTH // 2 - lv.get_width() // 2, 14))
        # levens als drakenkopjes
        for i in range(self.lives):
            self._mini_dragon(WIDTH - 26 - i * 34, HUD_H // 2)

    def _mini_dragon(self, cx, cy):
        s = self.screen
        r = 12
        pts = [(cx, cy)]
        a = 0.5
        while a <= 2 * math.pi - 0.5:
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            a += (2 * math.pi - 1.0) / 16
        pygame.draw.polygon(s, C_DRAGON, pts)

    def _banner(self, text, col):
        s = self.screen
        r = self.mid.render(text, True, col)
        bg = pygame.Surface((r.get_width() + 40, r.get_height() + 14), pygame.SRCALPHA)
        bg.fill((14, 11, 22, 210))
        s.blit(bg, (WIDTH // 2 - bg.get_width() // 2, HEIGHT // 2 - 26))
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 20))

    def _overlay(self, title, sub):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 175))
        s.blit(ov, (0, 0))
        r = self.big.render(title, True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 60))
        r2 = self.mid.render(sub, True, C_TEXT)
        s.blit(r2, (WIDTH // 2 - r2.get_width() // 2, HEIGHT // 2 + 16))

    def _draw_over(self):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 6, 14, 195))
        s.blit(ov, (0, 0))
        r = self.big.render(T("gameover"), True, (240, 110, 110))
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 100))
        r = self.mid.render("%s: %d" % (T("score"), self.score), True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 34))
        if self.score >= self.best and self.score > 0:
            r = self.mid.render(T("newrec"), True, (250, 220, 90))
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 + 8))
        r = self.font.render(T("again"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 54))

    def draw_menu(self):
        s = self.screen
        s.fill(C_BG)
        r = self.big.render(T("title"), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 70))
        r = self.font.render(T("sub"), True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 150))
        try:
            lp = os.path.join(app_dir(), "assets", "logo.png")
            if os.path.exists(lp):
                img = pygame.image.load(lp).convert_alpha()
                img = pygame.transform.smoothscale(img, (120, 120))
                s.blit(img, (WIDTH // 2 - 60, 200))
        except Exception:
            pass
        for i, line in enumerate((T("start"), T("controls"), T("hint"))):
            fnt = self.mid if i == 0 else self.font
            col = C_TEXT if i == 0 else C_DIM
            r = fnt.render(line, True, col)
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, 360 + i * 46))
        best = self.scores.get("best", 0)
        r = self.font.render("%s: %d" % (T("best"), best), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 520))
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
        g.ready_t = 0.0
    g.run(selftest=selftest)


if __name__ == "__main__":
    main()

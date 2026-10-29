# -*- coding: utf-8 -*-
"""DravePit - top-down racer met pitstops (Dravenlock).

Drie modi: Arcade-race, Uithoudingsrace (strategie) en Tijdrit.
Besturing: pijltjes (links/rechts sturen, omhoog gas, omlaag rem).
Pitstop: rijd langzaam de pitbox in (bij start/finish) -> banden + brandstof.
Portable (cache/), tweetalig NL/EN, procedurele audio. Donationware.
"""
import os
import sys
import math
import json
import locale
import random
import struct
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
    "title": ("DravePit", "DravePit"),
    "sub": ("Top-down racen met pitstops", "Top-down racing with pit stops"),
    "arcade": ("Arcade-race", "Arcade race"),
    "arcade_d": ("Rondjes tegen 3 rivalen", "Laps against 3 rivals"),
    "endur": ("Uithoudingsrace", "Endurance race"),
    "endur_d": ("Lang + strategisch pitten", "Long + strategic pitting"),
    "trial": ("Tijdrit", "Time trial"),
    "trial_d": ("Jaag op de snelste ronde", "Chase the fastest lap"),
    "start": ("Pijltjes = rijden  •  Enter = start", "Arrows = drive  •  Enter = start"),
    "choose": ("Kies een modus (1/2/3 of pijltjes + Enter)",
               "Pick a mode (1/2/3 or arrows + Enter)"),
    "lap": ("Ronde", "Lap"),
    "pos": ("Positie", "Pos"),
    "tyre": ("Banden", "Tyres"),
    "fuel": ("Brandstof", "Fuel"),
    "best": ("Beste", "Best"),
    "cur": ("Ronde", "Lap"),
    "pit_in": ("PITSTOP: langzaam blijven...", "PIT STOP: keep it slow..."),
    "pit_done": ("Klaar! Volle tank, verse banden", "Done! Full tank, fresh tyres"),
    "pit_hint": ("Pitbox = de blauwe zone bij start/finish",
                 "Pit box = blue zone at start/finish"),
    "fuel_out": ("Brandstof op! Naar de pit!", "Out of fuel! Pit now!"),
    "finish": ("FINISH", "FINISH"),
    "you_pos": ("Je eindigde als", "You finished"),
    "record": ("NIEUW RECORD!", "NEW RECORD!"),
    "best_lap": ("Snelste ronde", "Fastest lap"),
    "again": ("Enter = opnieuw   •   Esc = menu", "Enter = again   •   Esc = menu"),
    "menu": ("Esc = menu", "Esc = menu"),
    "paused": ("PAUZE", "PAUSED"),
    "resume": ("Enter = verder", "Enter = resume"),
    "donate": ("Doneren: paypal.me/roger076  •  service@dravenlock.nl",
               "Donate: paypal.me/roger076  •  service@dravenlock.nl"),
    "info": ("i = info", "i = info"),
    "countdown_go": ("GO!", "GO!"),
    "of": ("van", "of"),
    "laps_word": ("rondes", "laps"),
}


def T(key):
    v = TX.get(key, (key, key))
    return v[0] if NL else v[1]


# ---------------------------------------------------------------- kleuren
C_GRASS = (34, 90, 50)
C_GRASS2 = (30, 80, 44)
C_ROAD = (54, 54, 62)
C_ROAD_EDGE = (225, 225, 235)
C_KERB1 = (210, 60, 60)
C_KERB2 = (240, 240, 240)
C_PIT = (40, 70, 150)
C_PIT_EDGE = (120, 170, 255)
C_TEXT = (238, 236, 246)
C_DIM = (170, 165, 195)
C_ACCENT = (181, 156, 255)
C_PANEL = (22, 19, 31)
C_PANEL2 = (32, 28, 48)

WIDTH, HEIGHT = 960, 600
FPS = 60

# ---------------------------------------------------------------- baan
ROAD_W = 210.0            # wegbreedte (wereld-px)


def build_track():
    """Afgeronde-rechthoek circuit als lijst wereld-waypoints (gesloten lus)."""
    cx, cy = 0.0, 0.0
    hw, hh = 900.0, 520.0     # halve breedte/hoogte van het circuit
    r = 300.0                 # bochtstraal
    pts = []
    # start bovenaan midden, met de klok mee
    # rechte stukken + kwartcirkels in de hoeken
    straights = [
        # (van-hoek, naar-hoek) worden via de hoeken afgehandeld hieronder
    ]
    # hoekmiddelpunten
    corners = [
        (cx + hw - r, cy - hh + r, -90, 0),    # rechtsboven
        (cx + hw - r, cy + hh - r, 0, 90),     # rechtsonder
        (cx - hw + r, cy + hh - r, 90, 180),   # linksonder
        (cx - hw + r, cy - hh + r, 180, 270),  # linksboven
    ]
    # bovenrand (start/finish in het midden bovenaan) -> naar rechtsboven
    top_y = cy - hh
    pts.append((cx, top_y))
    x = cx
    while x < cx + hw - r:
        x += 40
        pts.append((min(x, cx + hw - r), top_y))
    for (mx, my, a0, a1) in corners:
        a = a0
        while a <= a1:
            rad = math.radians(a)
            pts.append((mx + r * math.cos(rad), my + r * math.sin(rad)))
            a += 8
        # recht stuk na de bocht wordt door volgende hoekpunten/segmenten gevuld
        # verbind naar begin volgende hoek met tussenpunten
    # sluit de bovenrand: van linksboven terug naar start (x=cx)
    # verzamel opnieuw met nette interpolatie langs de vier zijden
    return _rounded_rect_loop(cx, cy, hw, hh, r)


def _rounded_rect_loop(cx, cy, hw, hh, r, step=34.0):
    pts = []

    def arc(mx, my, a0, a1):
        a = a0
        n = max(2, int(abs(a1 - a0) / 8))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            rad = math.radians(a)
            pts.append((mx + r * math.cos(rad), my + r * math.sin(rad)))

    def line(x0, y0, x1, y1):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / step))
        for i in range(n):
            t = i / n
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))

    top = cy - hh
    bot = cy + hh
    left = cx - hw
    right = cx + hw
    # bovenrand vanaf midden naar rechts
    line(cx, top, right - r, top)
    arc(right - r, top + r, -90, 0)          # rechtsboven
    line(right, top + r, right, bot - r)      # rechterzijde
    arc(right - r, bot - r, 0, 90)            # rechtsonder
    line(right - r, bot, left + r, bot)       # onderrand
    arc(left + r, bot - r, 90, 180)           # linksonder
    line(left, bot - r, left, top + r)        # linkerzijde
    arc(left + r, top + r, 180, 270)          # linksboven
    line(left + r, top, cx, top)              # terug naar midden-boven
    return pts


class Track:
    def __init__(self):
        self.pts = build_track()
        # Start/finish op de LINKER rechte, waar de auto OMHOOG rijdt, zodat de
        # besturing intuitief is: omhoog = omhoog, links = links.
        k = min(range(len(self.pts)),
                key=lambda i: self.pts[i][0] * 1000 + abs(self.pts[i][1]))
        self.pts = self.pts[k:] + self.pts[:k]
        self.n = len(self.pts)
        # cumulatieve lengte
        self.seglen = []
        self.cum = [0.0]
        total = 0.0
        for i in range(self.n):
            a = self.pts[i]
            b = self.pts[(i + 1) % self.n]
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            self.seglen.append(d)
            total += d
            self.cum.append(total)
        self.length = total
        # start/finish op waypoint 0 (midden boven); rijrichting = met de klok mee
        self.start = self.pts[0]
        # startheading: richting van pt0 -> pt1
        p0 = self.pts[0]
        p1 = self.pts[1]
        self.start_heading = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        # pitbox: net binnen de baan bij start/finish (iets naar het midden/onder)
        nx, ny = self._normal_at(0)
        self.pit = (p0[0] + nx * (ROAD_W * 0.5 + 60),
                    p0[1] + ny * (ROAD_W * 0.5 + 60))

    def _normal_at(self, i):
        a = self.pts[i]
        b = self.pts[(i + 1) % self.n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        # normaal naar binnen (naar circuitcentrum 0,0)
        nx, ny = -dy / d, dx / d
        # zorg dat normaal naar (0,0) wijst
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if (mx + nx) * (mx + nx) + (my + ny) * (my + ny) > mx * mx + my * my:
            nx, ny = -nx, -ny
        return nx, ny

    def nearest(self, x, y):
        """Geef (afstand, fractie[0..1], segment-index) van dichtstbijzijnde punt."""
        best_d = 1e18
        best_f = 0.0
        best_i = 0
        best_px = x
        best_py = y
        for i in range(self.n):
            ax, ay = self.pts[i]
            bx, by = self.pts[(i + 1) % self.n]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 <= 1e-9:
                continue
            t = ((x - ax) * dx + (y - ay) * dy) / L2
            t = max(0.0, min(1.0, t))
            px, py = ax + dx * t, ay + dy * t
            d = (x - px) ** 2 + (y - py) ** 2
            if d < best_d:
                best_d = d
                best_i = i
                best_f = t
                best_px, best_py = px, py
        frac = (self.cum[best_i] + best_f * self.seglen[best_i]) / self.length
        return math.sqrt(best_d), frac, best_i, (best_px, best_py)

    def point_at_frac(self, frac):
        frac %= 1.0
        target = frac * self.length
        # binair/lineair zoeken
        i = 0
        while i < self.n and self.cum[i + 1] < target:
            i += 1
        i = min(i, self.n - 1)
        rem = target - self.cum[i]
        t = rem / (self.seglen[i] or 1.0)
        ax, ay = self.pts[i]
        bx, by = self.pts[(i + 1) % self.n]
        return (ax + (bx - ax) * t, ay + (by - ay) * t)


# ---------------------------------------------------------------- auto
class Car:
    def __init__(self, track, color, is_player=False, skill=1.0):
        self.tr = track
        self.color = color
        self.is_player = is_player
        self.skill = skill
        self.x, self.y = track.start
        self.angle = track.start_heading
        self.speed = 0.0
        self.frac = 0.0
        self.prev_frac = 0.0
        self.lap = 0
        self.progress = 0.0
        self.tyre = 1.0          # 1.0 = vers, 0.0 = kapot
        self.fuel = 1.0
        self.finished = False
        self.finish_time = 0.0
        self.servicing = 0.0     # seconden bezig in pit
        self.throttle = 0.0
        self.on_road = True
        # AI-lookahead index
        _, f, i, _ = track.nearest(self.x, self.y)
        self.frac = f
        self.prev_frac = f

    MAX_SPEED = 330.0
    ACCEL = 220.0
    BRAKE = 320.0

    def grip(self):
        # banden + ondergrond bepalen grip
        g = 0.55 + 0.45 * self.tyre
        if not self.on_road:
            g *= 0.45
        return g

    def top_speed(self):
        ts = self.MAX_SPEED
        if not self.on_road:
            ts *= 0.55
        if self.fuel <= 0.0:
            ts *= 0.0  # geen gas
        return ts

    def update_common(self, dt):
        # positie
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        # baanvoortgang
        d, f, i, proj = self.tr.nearest(self.x, self.y)
        self.on_road = d <= (ROAD_W * 0.5 + 6)
        # rondetelling via wrap-detectie
        if self.prev_frac > 0.85 and f < 0.15:
            self.lap += 1
        elif self.prev_frac < 0.15 and f > 0.85:
            self.lap -= 1
        self.prev_frac = f
        self.frac = f
        self.progress = self.lap + f
        # slijtage/verbruik
        if self.speed > 5:
            self.tyre = max(0.0, self.tyre - dt * (0.010 + 0.02 * self.throttle))
        if self.throttle > 0 and self.fuel > 0:
            self.fuel = max(0.0, self.fuel - dt * 0.018 * (0.4 + self.throttle))

    def update_player(self, dt, keys):
        steer = 0.0
        if keys[pygame.K_LEFT]:
            steer -= 1.0
        if keys[pygame.K_RIGHT]:
            steer += 1.0
        self.throttle = 1.0 if keys[pygame.K_UP] else 0.0
        braking = keys[pygame.K_DOWN]
        ts = self.top_speed()
        if self.throttle > 0:
            self.speed += self.ACCEL * dt
        elif braking:
            self.speed -= self.BRAKE * dt
        else:
            self.speed -= 60 * dt  # motorrem/rol
        self.speed = max(-60.0, min(ts, self.speed))
        # sturen schaalt met snelheid en grip
        turn = 2.6 * self.grip()
        v = self.speed / self.MAX_SPEED
        self.angle += steer * turn * dt * (0.35 + 0.9 * min(1.0, abs(v))) * (1 if self.speed >= 0 else -1)
        if not self.on_road:
            self.speed *= (1 - 0.5 * dt)
        self.update_common(dt)

    def update_ai(self, dt):
        tr = self.tr
        # mik op punt vooruit langs de lus
        look = 0.045 + 0.02 * self.skill
        aim = tr.point_at_frac(self.frac + look)
        ang_to = math.atan2(aim[1] - self.y, aim[0] - self.x)
        diff = (ang_to - self.angle + math.pi) % (2 * math.pi) - math.pi
        # bochtscherpte -> gas dosering
        sharp = abs(diff)
        self.throttle = 1.0 if sharp < 0.5 else 0.35
        target = self.top_speed() * (0.62 + 0.36 * self.skill) * (1.0 if sharp < 0.4 else 0.6)
        if self.speed < target:
            self.speed += self.ACCEL * 0.9 * dt
        else:
            self.speed -= self.BRAKE * 0.5 * dt
        self.speed = max(0.0, min(self.top_speed(), self.speed))
        turn = 2.6 * self.grip()
        self.angle += max(-1, min(1, diff * 2.2)) * turn * dt
        # AI pit automatisch als banden/brandstof te laag
        self.update_common(dt)
        # AI regenereert simpel in pit-zone (vereenvoudigd): tank nooit helemaal leeg
        if self.fuel < 0.08:
            self.fuel = 1.0
            self.tyre = 1.0


# ---------------------------------------------------------------- audio
class Audio:
    def __init__(self):
        self.ok = False
        self.engine = None
        self.chan = None
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.ok = True
        except Exception:
            self.ok = False
        if self.ok:
            self.engine = self._engine_loop()
            self.beep_hi = self._tone(880, 0.08, vol=0.35)
            self.beep_lo = self._tone(440, 0.10, vol=0.35)
            self.chime = self._chime()

    def _buf(self, samples):
        return pygame.mixer.Sound(buffer=array.array("h", samples).tobytes())

    def _tone(self, freq, dur, vol=0.4):
        rate = 22050
        n = int(rate * dur)
        out = []
        for i in range(n):
            t = i / rate
            env = min(1.0, t * 30) * max(0.0, 1 - t / dur)
            s = math.sin(2 * math.pi * freq * t)
            out.append(int(s * env * vol * 32767))
        return self._buf(out)

    def _chime(self):
        rate = 22050
        out = []
        for freq, dur in ((660, 0.10), (880, 0.10), (1180, 0.16)):
            n = int(rate * dur)
            for i in range(n):
                t = i / rate
                env = min(1.0, t * 30) * max(0.0, 1 - t / dur)
                out.append(int(math.sin(2 * math.pi * freq * t) * env * 0.35 * 32767))
        return self._buf(out)

    def _engine_loop(self):
        rate = 22050
        dur = 0.25
        n = int(rate * dur)
        out = []
        base = 70.0
        for i in range(n):
            t = i / rate
            # zaagtand-achtige brom
            ph = (base * t) % 1.0
            s = (ph * 2 - 1) * 0.6
            s += 0.3 * math.sin(2 * math.pi * base * 2 * t)
            out.append(int(max(-1, min(1, s)) * 0.28 * 32767))
        return self._buf(out)

    def start_engine(self):
        if self.ok and self.engine and self.chan is None:
            try:
                self.chan = self.engine.play(loops=-1)
                self.chan.set_volume(0.0)
            except Exception:
                self.chan = None

    def engine_rev(self, frac):
        if self.chan:
            try:
                self.chan.set_volume(max(0.05, min(0.9, 0.15 + frac * 0.7)))
            except Exception:
                pass

    def play(self, snd):
        if self.ok and snd:
            try:
                snd.play()
            except Exception:
                pass

    def stop(self):
        if self.chan:
            try:
                self.chan.stop()
            except Exception:
                pass
            self.chan = None


# ---------------------------------------------------------------- game
MODE_ARCADE, MODE_ENDUR, MODE_TRIAL = "arcade", "endur", "trial"
MODE_LAPS = {MODE_ARCADE: 5, MODE_ENDUR: 12, MODE_TRIAL: 4}
CAR_COLORS = [(210, 60, 60), (70, 150, 240), (240, 200, 60), (120, 220, 120)]


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
        pygame.display.set_caption("DravePit")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas,arial", 22)
        self.fontbig = pygame.font.SysFont("arial", 54, bold=True)
        self.fontmid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("consolas,arial", 17)
        self.track = Track()
        self.audio = Audio()
        self.state = "menu"
        self.menu_i = 0
        self.mode = MODE_ARCADE
        self.scores = self._load_scores()
        self.msg = ""
        self.msg_t = 0.0
        self.show_info = False
        self.reset_race(MODE_ARCADE)

    # ---- opslag ----
    def _load_scores(self):
        try:
            with open(SCORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_scores(self):
        try:
            with open(SCORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except Exception:
            pass

    # ---- race opzetten ----
    def reset_race(self, mode):
        self.mode = mode
        self.laps_total = MODE_LAPS[mode]
        self.cars = []
        self.player = Car(self.track, CAR_COLORS[0], is_player=True)
        self.cars.append(self.player)
        if mode != MODE_TRIAL:
            for k in range(3):
                c = Car(self.track, CAR_COLORS[k + 1], skill=0.75 + 0.08 * k)
                self.cars.append(c)
        # startopstelling: iets achter elkaar op de startlijn
        for idx, c in enumerate(self.cars):
            back = self.track.point_at_frac((1.0 - 0.01 * (idx + 1)) % 1.0)
            side = (-1) ** idx * 26
            nx, ny = self.track._normal_at(0)
            c.x = back[0] + nx * side * 0.0
            c.y = back[1]
            c.x, c.y = back[0], back[1]
            c.angle = self.track.start_heading
            c.lap = 0
            c.prev_frac = c.frac = (1.0 - 0.01 * (idx + 1)) % 1.0
        self.countdown = 3.0
        self.race_time = 0.0
        self.best_lap = self.scores.get(self._best_key(), {}).get("best_lap", 0.0)
        self.player_lap_start = 0.0
        self.player_best_this = 0.0
        self.pit_flag = False
        self.result = None
        self.finish_order = []
        self.audio.start_engine()

    def _best_key(self):
        return "mode_" + self.mode

    # ---- lus ----
    def run(self, selftest=0):
        running = True
        frames = 0
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    self.on_key(e.key)
            keys = pygame.key.get_pressed()
            if self.state == "race":
                self.update_race(dt, keys)
            self.draw()
            if self.msg_t > 0:
                self.msg_t -= dt
            frames += 1
            if selftest and frames >= selftest:
                self._selftest_shot()
                running = False
        self.audio.stop()
        pygame.quit()

    def on_key(self, key):
        if self.state == "menu":
            if key in (pygame.K_1,):
                self.start(MODE_ARCADE)
            elif key in (pygame.K_2,):
                self.start(MODE_ENDUR)
            elif key in (pygame.K_3,):
                self.start(MODE_TRIAL)
            elif key in (pygame.K_LEFT, pygame.K_UP):
                self.menu_i = (self.menu_i - 1) % 3
            elif key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.menu_i = (self.menu_i + 1) % 3
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start([MODE_ARCADE, MODE_ENDUR, MODE_TRIAL][self.menu_i])
            elif key == pygame.K_i:
                self.show_info = not self.show_info
            elif key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == "race":
            if key == pygame.K_ESCAPE:
                self.state = "paused"
        elif self.state == "paused":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "race"
            elif key == pygame.K_ESCAPE:
                self.state = "menu"
        elif self.state == "result":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start(self.mode)
            elif key == pygame.K_ESCAPE:
                self.state = "menu"

    def start(self, mode):
        self.reset_race(mode)
        self.state = "race"

    # ---- update race ----
    def update_race(self, dt, keys):
        if self.countdown > 0:
            self.countdown -= dt
            # motoren stationair
            self.audio.engine_rev(0.1)
            return
        self.race_time += dt
        # speler
        p = self.player
        if not p.finished:
            p.update_player(dt, keys)
        # pit-servicing speler
        self._service(p, dt, is_player=True)
        # AI
        for c in self.cars[1:]:
            if not c.finished:
                c.update_ai(dt)
        # rondes speler bijhouden voor beste-ronde
        self._track_player_lap(p)
        # motorgeluid
        self.audio.engine_rev(max(0.0, p.speed) / Car.MAX_SPEED)
        # brandstof waarschuwing
        if p.fuel <= 0.0 and self.msg_t <= 0:
            self.flash(T("fuel_out"))
        # finish
        for c in self.cars:
            if not c.finished and c.lap >= self.laps_total:
                c.finished = True
                c.finish_time = self.race_time
                self.finish_order.append(c)
                if c is p:
                    self.audio.play(self.audio.chime)
        # einde: speler klaar (of alle auto's klaar in tijdrit)
        if p.finished and self.result is None:
            self.finish_race()

    def _service(self, car, dt, is_player):
        d = math.hypot(car.x - self.track.pit[0], car.y - self.track.pit[1])
        in_box = d < 90
        self.pit_flag = in_box and is_player
        if in_box and car.speed < 55:
            car.servicing += dt
            car.speed *= (1 - 3.5 * dt)  # afremmen tot stilstand
            # vullen over ~2.2s
            car.fuel = min(1.0, car.fuel + dt / 2.2)
            car.tyre = min(1.0, car.tyre + dt / 2.0)
            if is_player:
                if car.fuel >= 0.999 and car.tyre >= 0.999:
                    if self.msg_t <= 0:
                        self.flash(T("pit_done"))
                else:
                    self.flash(T("pit_in"))
        else:
            car.servicing = 0.0

    def _track_player_lap(self, p):
        # detecteer nieuwe ronde
        if not hasattr(self, "_last_lap"):
            self._last_lap = p.lap
        if p.lap > self._last_lap:
            lap_time = self.race_time - self.player_lap_start
            self.player_lap_start = self.race_time
            if lap_time > 1.0:
                if self.player_best_this <= 0 or lap_time < self.player_best_this:
                    self.player_best_this = lap_time
                self.audio.play(self.audio.beep_hi)
            self._last_lap = p.lap
        if not hasattr(self, "_cur_lap_start"):
            self._cur_lap_start = 0.0

    def cur_lap_time(self):
        return self.race_time - self.player_lap_start

    def positions(self):
        order = sorted(self.cars, key=lambda c: (-(c.finish_time == 0.0),
                       c.finish_time if c.finished else -c.progress))
        # eenvoudiger: klaar-auto's op finishvolgorde, rest op progress
        done = [c for c in self.finish_order]
        rest = sorted([c for c in self.cars if c not in done],
                      key=lambda c: -c.progress)
        return done + rest

    def finish_race(self):
        order = self.positions()
        pos = order.index(self.player) + 1
        rec = False
        key = self._best_key()
        entry = self.scores.get(key, {})
        if self.player_best_this > 0:
            old = entry.get("best_lap", 0.0)
            if old <= 0 or self.player_best_this < old:
                entry["best_lap"] = self.player_best_this
                rec = True
        if self.mode != MODE_TRIAL:
            bestpos = entry.get("best_pos", 99)
            if pos < bestpos:
                entry["best_pos"] = pos
        self.scores[key] = entry
        self._save_scores()
        self.result = {"pos": pos, "record": rec,
                       "best_lap": self.player_best_this,
                       "total": len(self.cars)}
        self.state = "result"

    def flash(self, msg):
        self.msg = msg
        self.msg_t = 1.6

    # ---- tekenen ----
    def world_to_screen(self, x, y, cam):
        return int(x - cam[0] + WIDTH / 2), int(y - cam[1] + HEIGHT / 2)

    def draw(self):
        s = self.screen
        if self.state == "menu":
            self.draw_menu()
        else:
            cam = (self.player.x, self.player.y)
            s.fill(C_GRASS)
            self.draw_track(cam)
            for c in self.cars:
                self.draw_car(c, cam)
            self.draw_hud()
            if self.countdown > 0:
                self.draw_countdown()
            if self.state == "paused":
                self.overlay(T("paused"), T("resume"))
            if self.state == "result":
                self.draw_result()
            if self.msg_t > 0:
                self.center_banner(self.msg, HEIGHT - 120)
        pygame.display.flip()

    def draw_track(self, cam):
        s = self.screen
        tr = self.track
        # weg als dikke polygoon-strip
        left = []
        right = []
        for i in range(tr.n):
            ax, ay = tr.pts[i]
            bx, by = tr.pts[(i + 1) % tr.n]
            dx, dy = bx - ax, by - ay
            d = math.hypot(dx, dy) or 1
            nx, ny = -dy / d, dx / d
            hw = ROAD_W / 2
            left.append(self.world_to_screen(ax + nx * hw, ay + ny * hw, cam))
            right.append(self.world_to_screen(ax - nx * hw, ay - ny * hw, cam))
        poly = left + right[::-1]
        pygame.draw.polygon(s, C_ROAD, poly)
        # kantlijnen
        if len(left) > 1:
            pygame.draw.lines(s, C_ROAD_EDGE, True, left, 3)
            pygame.draw.lines(s, C_ROAD_EDGE, True, right, 3)
        # middenstrepen (gestreept, om-en-om segment)
        for i in range(0, tr.n, 2):
            a = self.world_to_screen(tr.pts[i][0], tr.pts[i][1], cam)
            b = self.world_to_screen(tr.pts[(i + 1) % tr.n][0],
                                     tr.pts[(i + 1) % tr.n][1], cam)
            pygame.draw.line(s, (235, 225, 130), a, b, 3)
        # start/finish streep (blokjes)
        p0 = tr.pts[0]
        dx = tr.pts[1][0] - p0[0]
        dy = tr.pts[1][1] - p0[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        for k in range(-4, 5):
            col = C_KERB2 if k % 2 == 0 else (40, 40, 40)
            cxp = p0[0] + nx * (k * ROAD_W / 9)
            cyp = p0[1] + ny * (k * ROAD_W / 9)
            r = pygame.Rect(0, 0, 14, 14)
            r.center = self.world_to_screen(cxp, cyp, cam)
            pygame.draw.rect(s, col, r)
        # pitbox
        pb = self.world_to_screen(tr.pit[0], tr.pit[1], cam)
        rect = pygame.Rect(0, 0, 120, 120)
        rect.center = pb
        pygame.draw.rect(s, C_PIT, rect, border_radius=10)
        pygame.draw.rect(s, C_PIT_EDGE, rect, 3, border_radius=10)
        lab = self.small.render("PIT", True, (200, 220, 255))
        s.blit(lab, (rect.centerx - lab.get_width() // 2, rect.centery - 9))

    def draw_car(self, car, cam):
        s = self.screen
        sx, sy = self.world_to_screen(car.x, car.y, cam)
        # auto als getekende sprite op eigen surface, dan roteren
        w, h = 26, 46
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        body = pygame.Rect(3, 4, w - 6, h - 8)
        pygame.draw.rect(surf, car.color, body, border_radius=6)
        pygame.draw.rect(surf, (20, 20, 26), body, 2, border_radius=6)
        # voorruit
        pygame.draw.rect(surf, (30, 40, 60), pygame.Rect(6, 9, w - 12, 9), border_radius=3)
        # spoiler achter
        pygame.draw.rect(surf, (30, 30, 36), pygame.Rect(4, h - 9, w - 8, 5), border_radius=2)
        # wielen
        for wy in (12, h - 16):
            pygame.draw.rect(surf, (15, 15, 18), pygame.Rect(-1, wy, 5, 10), border_radius=2)
            pygame.draw.rect(surf, (15, 15, 18), pygame.Rect(w - 4, wy, 5, 10), border_radius=2)
        # richting: sprite wijst 'omhoog' (=-90°); rotatie t.o.v. heading
        rot = pygame.transform.rotate(surf, -math.degrees(car.angle) - 90)
        rect = rot.get_rect(center=(sx, sy))
        s.blit(rot, rect)
        if car.is_player:
            pygame.draw.circle(s, C_ACCENT, (sx, sy), 3)

    def draw_hud(self):
        s = self.screen
        # paneel
        panel = pygame.Surface((250, 132), pygame.SRCALPHA)
        panel.fill((18, 15, 26, 210))
        s.blit(panel, (10, 10))
        p = self.player
        pos = self.positions().index(p) + 1
        lines = [
            "%s: %d/%d" % (T("lap"), min(p.lap + 1, self.laps_total), self.laps_total),
        ]
        if self.mode != MODE_TRIAL:
            lines.append("%s: %d/%d" % (T("pos"), pos, len(self.cars)))
        y = 18
        for ln in lines:
            s.blit(self.font.render(ln, True, C_TEXT), (22, y))
            y += 28
        # banden/brandstof balken
        self.bar(22, y, T("tyre"), p.tyre, (90, 200, 120))
        y += 24
        self.bar(22, y, T("fuel"), p.fuel, (240, 200, 80))
        # tijden rechtsboven
        tp = pygame.Surface((250, 96), pygame.SRCALPHA)
        tp.fill((18, 15, 26, 210))
        s.blit(tp, (WIDTH - 260, 10))
        cur = self.cur_lap_time()
        s.blit(self.font.render("%s: %s" % (T("cur"), fmt_time(cur)), True, C_TEXT),
               (WIDTH - 248, 18))
        best_now = self.player_best_this if self.player_best_this > 0 else self.best_lap
        s.blit(self.font.render("%s: %s" % (T("best"), fmt_time(best_now)), True, C_ACCENT),
               (WIDTH - 248, 46))
        s.blit(self.small.render(T("pit_hint"), True, C_DIM), (WIDTH - 248, 78))

    def bar(self, x, y, label, val, col):
        s = self.screen
        s.blit(self.small.render(label, True, C_DIM), (x, y - 2))
        bx = x + 74
        w = 140
        pygame.draw.rect(s, (50, 50, 60), (bx, y, w, 14), border_radius=4)
        c = col
        if val < 0.25:
            c = (230, 80, 80)
        pygame.draw.rect(s, c, (bx, y, int(w * max(0, val)), 14), border_radius=4)

    def draw_countdown(self):
        n = int(math.ceil(self.countdown))
        txt = T("countdown_go") if self.countdown <= 0.0 else str(n)
        if self.countdown <= 0.6 and self.countdown > 0:
            txt = T("countdown_go")
        r = self.fontbig.render(txt, True, C_ACCENT)
        self.screen.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 40))
        # piepjes bij hele seconden
        cur = int(math.ceil(self.countdown))
        if not hasattr(self, "_last_cd") or self._last_cd != cur:
            self._last_cd = cur
            self.audio.play(self.audio.beep_lo if cur > 0 else self.audio.beep_hi)

    def center_banner(self, text, y):
        s = self.screen
        r = self.fontmid.render(text, True, C_TEXT)
        bg = pygame.Surface((r.get_width() + 40, r.get_height() + 16), pygame.SRCALPHA)
        bg.fill((18, 15, 26, 210))
        s.blit(bg, (WIDTH // 2 - bg.get_width() // 2, y - 8))
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, y))

    def overlay(self, title, sub):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 8, 16, 170))
        s.blit(ov, (0, 0))
        r = self.fontbig.render(title, True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT // 2 - 70))
        r2 = self.fontmid.render(sub, True, C_TEXT)
        s.blit(r2, (WIDTH // 2 - r2.get_width() // 2, HEIGHT // 2 + 10))

    def draw_result(self):
        s = self.screen
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((10, 8, 16, 200))
        s.blit(ov, (0, 0))
        res = self.result
        y = 120
        r = self.fontbig.render(T("finish"), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, y))
        y += 90
        if self.mode != MODE_TRIAL:
            txt = "%s %d/%d" % (T("you_pos"), res["pos"], res["total"])
            r = self.fontmid.render(txt, True, C_TEXT)
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, y))
            y += 46
        bl = res["best_lap"]
        if bl > 0:
            r = self.fontmid.render("%s: %s" % (T("best_lap"), fmt_time(bl)), True, C_TEXT)
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, y))
            y += 46
        if res["record"]:
            r = self.fontmid.render(T("record"), True, (250, 220, 90))
            s.blit(r, (WIDTH // 2 - r.get_width() // 2, y))
            y += 46
        r = self.font.render(T("again"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 70))

    def draw_menu(self):
        s = self.screen
        s.fill(C_PANEL)
        # sfeerbaan op achtergrond
        cam = self.track.point_at_frac(0.0)
        # titel
        r = self.fontbig.render(T("title"), True, C_ACCENT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 60))
        r = self.font.render(T("sub"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, 128))
        # logo
        try:
            lp = os.path.join(app_dir(), "assets", "logo.png")
            if os.path.exists(lp):
                img = pygame.image.load(lp).convert_alpha()
                img = pygame.transform.smoothscale(img, (84, 84))
                s.blit(img, (WIDTH // 2 - 42, 158))
        except Exception:
            pass
        modes = [(MODE_ARCADE, "arcade", "arcade_d"),
                 (MODE_ENDUR, "endur", "endur_d"),
                 (MODE_TRIAL, "trial", "trial_d")]
        y = 270
        for i, (mk, nk, dk) in enumerate(modes):
            sel = (i == self.menu_i)
            w = 560
            rect = pygame.Rect(WIDTH // 2 - w // 2, y, w, 62)
            pygame.draw.rect(s, C_PANEL2 if not sel else (54, 46, 82), rect, border_radius=12)
            if sel:
                pygame.draw.rect(s, C_ACCENT, rect, 3, border_radius=12)
            num = self.fontmid.render(str(i + 1), True, C_ACCENT)
            s.blit(num, (rect.x + 18, rect.y + 14))
            name = self.fontmid.render(T(nk), True, C_TEXT)
            s.blit(name, (rect.x + 64, rect.y + 8))
            desc = self.small.render(T(dk) + "  •  %d %s" % (MODE_LAPS[mk], T("laps_word")),
                                     True, C_DIM)
            s.blit(desc, (rect.x + 66, rect.y + 38))
            best = self.scores.get("mode_" + mk, {}).get("best_lap", 0.0)
            if best > 0:
                bt = self.small.render("%s: %s" % (T("best"), fmt_time(best)), True, C_ACCENT)
                s.blit(bt, (rect.right - bt.get_width() - 16, rect.y + 22))
            y += 76
        r = self.font.render(T("choose"), True, C_TEXT)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, y + 6))
        r = self.small.render(T("donate"), True, C_DIM)
        s.blit(r, (WIDTH // 2 - r.get_width() // 2, HEIGHT - 30))
        if self.show_info:
            self.center_banner(T("pit_hint"), HEIGHT - 110)

    def _selftest_shot(self):
        try:
            out = os.path.join(app_dir(), "voorbeeld.png")
            pygame.image.save(self.screen, out)
            print("SELFTEST OK ->", out)
        except Exception as e:
            print("SELFTEST render-fout:", e)


def fmt_time(t):
    if not t or t <= 0:
        return "--:--"
    m = int(t // 60)
    s = t - m * 60
    return "%d:%05.2f" % (m, s)


def main():
    selftest = 0
    if "--selftest" in sys.argv:
        try:
            selftest = int(sys.argv[sys.argv.index("--selftest") + 1])
        except Exception:
            selftest = 120
    g = Game()
    if selftest:
        g.start(MODE_ARCADE)
    g.run(selftest=selftest)


if __name__ == "__main__":
    main()

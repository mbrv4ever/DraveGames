# -*- coding: utf-8 -*-
"""DraveDuel - een zwaardduel op timing (Dravenlock).

Jij bent de draken-ridder. Je tegenstander haalt uit naar je HOGE of LAGE lijn
(je ziet zijn zwaard opladen). Zet je dekking met OMHOOG/OMLAAG om te pareren,
en druk dan SPATIE om terug te steken zolang hij open staat. Versla steeds
sterkere ridders in de toernooiladder.

Besturing: OMHOOG/OMLAAG = hoge/lage dekking, SPATIE = terugsteken, Enter =
start/verder, P = pauze, Esc = terug. Tweetalig NL/EN, procedurele audio,
portable. Donationware.
"""
import json
import locale
import math
import os
import random
import sys
import webbrowser
from array import array

import pygame

try:
    from pygame import gfxdraw
    HAS_GFX = True
except Exception:
    HAS_GFX = False

W, H = 900, 600
FPS = 60
SR = 22050
GY = H - 150                  # grondlijn waar de vechters staan

BG_TOP = (26, 20, 40)
BG_BOT = (56, 42, 84)
PURPLE = (128, 94, 205)
PURPLE_L = (176, 150, 236)
PURPLE_D = (74, 58, 110)
BELLY = (206, 190, 240)
HORN = (238, 232, 250)
EYE = (255, 208, 66)
INK = (232, 226, 246)
GOLDC = (255, 205, 70)
STEEL = (200, 205, 220)
STEEL_D = (140, 146, 165)


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def cache_dir():
    d = os.path.join(app_dir(), "cache")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _lang():
    try:
        loc = (locale.getdefaultlocale()[0] or "")
    except Exception:
        loc = ""
    return "nl" if loc.lower().startswith("nl") else "en"


LANG = _lang()
TX = {
    "title": {"nl": "DraveDuel", "en": "DraveDuel"},
    "sub": {"nl": "Zwaardduel op timing", "en": "A duel of timing"},
    "start": {"nl": "Enter = start", "en": "Enter = start"},
    "ctrl": {"nl": "Omhoog/Omlaag = dekking   Spatie = terugsteken   P = pauze",
             "en": "Up/Down = guard   Space = riposte   P = pause"},
    "how": {"nl": "Pareer zijn uithaal met de juiste dekking, sla dan terug.",
            "en": "Parry his strike with the right guard, then strike back."},
    "donate": {"nl": "D = doneren", "en": "D = donate"},
    "info": {"nl": "I = info", "en": "I = info"},
    "quit": {"nl": "Esc = afsluiten", "en": "Esc = quit"},
    "foe": {"nl": "Tegenstander", "en": "Opponent"},
    "score": {"nl": "Verslagen", "en": "Beaten"},
    "best": {"nl": "Record", "en": "Best"},
    "guard": {"nl": "Dekking", "en": "Guard"},
    "high": {"nl": "HOOG", "en": "HIGH"},
    "low": {"nl": "LAAG", "en": "LOW"},
    "parry": {"nl": "Pareer!", "en": "Parry!"},
    "hit_you": {"nl": "Geraakt!", "en": "You're hit!"},
    "riposte": {"nl": "Raak!", "en": "Riposte!"},
    "whiff": {"nl": "Mis!", "en": "Whiff!"},
    "win": {"nl": "Tegenstander verslagen!", "en": "Opponent defeated!"},
    "next": {"nl": "Enter = volgende ridder", "en": "Enter = next knight"},
    "paused": {"nl": "Pauze", "en": "Paused"},
    "resume": {"nl": "P = verder", "en": "P = resume"},
    "gameover": {"nl": "Je bent gevallen!", "en": "You have fallen!"},
    "reached": {"nl": "%d ridders verslagen", "en": "Defeated %d knights"},
    "retry": {"nl": "Enter = opnieuw", "en": "Enter = retry"},
    "menu": {"nl": "Esc = menu", "en": "Esc = menu"},
    "tip": {"nl": "Tip: druk pas Spatie als hij OPEN staat (na je pareer).",
            "en": "Tip: press Space only when he's OPEN (after your parry)."},
    "info_txt": {
        "nl": "DraveDuel - lees zijn uithaal (hoog/laag), pareer met de juiste "
              "dekking en steek terug.\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl",
        "en": "DraveDuel - read his strike (high/low), parry with the right "
              "guard and riposte.\n"
              "Donationware - https://paypal.me/roger076\nservice@dravenlock.nl"},
}


def T(k):
    d = TX.get(k, {})
    return d.get(LANG) or d.get("en") or k


DONATE = "https://paypal.me/roger076"


def circ(surf, x, y, r, color):
    x, y, r = int(x), int(y), int(r)
    if HAS_GFX and r > 0:
        try:
            gfxdraw.filled_circle(surf, x, y, r, color)
            gfxdraw.aacircle(surf, x, y, r, color)
            return
        except Exception:
            pass
    pygame.draw.circle(surf, color, (x, y), r)


def poly(surf, pts, color):
    ipts = [(int(round(x)), int(round(y))) for x, y in pts]
    if HAS_GFX and len(ipts) >= 3:
        try:
            gfxdraw.filled_polygon(surf, ipts, color)
            gfxdraw.aapolygon(surf, ipts, color)
            return
        except Exception:
            pass
    pygame.draw.polygon(surf, color, ipts)


def draw_sword(sc, hand, ang, length=64, col=STEEL):
    tip = (hand[0] + math.cos(ang) * length, hand[1] + math.sin(ang) * length)
    # kling
    pygame.draw.line(sc, col, hand, tip, 6)
    pygame.draw.line(sc, (255, 255, 255), hand, tip, 2)
    # pareerstang
    perp = ang + math.pi / 2
    g1 = (hand[0] + math.cos(perp) * 9, hand[1] + math.sin(perp) * 9)
    g2 = (hand[0] - math.cos(perp) * 9, hand[1] - math.sin(perp) * 9)
    pygame.draw.line(sc, (120, 90, 54), g1, g2, 5)
    return tip


class Fighter:
    def __init__(self, x, facing, dragon=False, col=PURPLE):
        self.x = x
        self.facing = facing            # 1 = kijkt naar rechts
        self.dragon = dragon
        self.col = col
        self.guard = "high"
        self.pose = "guard"             # guard / windup / strike / open / hurt
        self.line = "high"
        self.anim = 0.0
        self.cur_adv = 0.0              # huidige voorwaartse verplaatsing (px)
        self.adv_target = 0.0

    def draw(self, sc, shake=(0, 0)):
        x = self.x + shake[0] + self.facing * self.cur_adv
        y = GY + shake[1]
        f = self.facing
        col = self.col
        dark = tuple(max(0, c - 40) for c in col)
        # benen
        poly(sc, [(x - 12, y), (x - 4, y - 40), (x + 4, y - 40), (x - 4, y)],
             dark)
        poly(sc, [(x + 12, y), (x + 4, y - 40), (x + 12, y - 40), (x + 6, y)],
             dark)
        # torso
        poly(sc, [(x - 14, y - 38), (x + 14, y - 38), (x + 10, y - 78),
                  (x - 10, y - 78)], col)
        # buik/harnas
        pygame.draw.line(sc, (255, 255, 255), (x - 6, y - 50),
                         (x + 6, y - 50), 2)
        # hoofd
        hx, hy = x + f * 4, y - 92
        if self.dragon:
            circ(sc, hx, hy, 12, col)
            poly(sc, [(hx - 10, hy - 6), (hx - 4, hy - 6), (hx - 12, hy - 20)],
                 HORN)
            poly(sc, [(hx + 2, hy - 6), (hx + 8, hy - 6), (hx + 12, hy - 20)],
                 HORN)
            poly(sc, [(hx + f * 6, hy - 2), (hx + f * 20, hy + 2),
                      (hx + f * 6, hy + 6)], col)
            circ(sc, hx + f * 6, hy - 1, 2, EYE)
        else:
            circ(sc, hx, hy, 12, (210, 185, 155))
            pygame.draw.arc(sc, STEEL_D, (hx - 12, hy - 12, 24, 26),
                            0.1, 3.0, 5)
            pygame.draw.rect(sc, STEEL_D, (hx - 12, hy - 2, 24, 5))
            pygame.draw.line(sc, (30, 24, 30), (hx + f * 2, hy - 4),
                             (hx + f * 10, hy - 4), 2)
        # zwaardarm: hoek op basis van pose/lijn
        shoulder = (x + f * 12, y - 70)
        ang = self._sword_angle()
        hand = (shoulder[0] + f * 14, shoulder[1] + 6)
        pygame.draw.line(sc, col, shoulder, hand, 7)
        draw_sword(sc, hand, ang)

    def _sword_angle(self):
        f = self.facing
        base_up = -1.15 if f == 1 else (math.pi + 1.15)
        base_lo = 0.5 if f == 1 else (math.pi - 0.5)
        fwd = 0.0 if f == 1 else math.pi
        if self.pose in ("guard",):
            return base_up if self.guard == "high" else base_lo
        if self.pose == "windup":
            return (base_up - f * 0.5) if self.line == "high" \
                else (base_lo + f * 0.4)
        if self.pose == "strike":
            return (fwd - 0.35) if self.line == "high" else (fwd + 0.35)
        if self.pose == "open":
            return base_lo if f == 1 else base_lo
        if self.pose == "hurt":
            return base_lo + f * 0.6
        return base_up


# ---------------------------------------------------------------- audio
def _env(i, n, atk=0.01, rel=0.3):
    a = int(n * atk) or 1
    r = int(n * rel) or 1
    if i < a:
        return i / a
    if i > n - r:
        return max(0.0, (n - i) / r)
    return 1.0


def tone(freq, ms, vol=0.4, wave="sine"):
    n = int(SR * ms / 1000)
    buf = array("h")
    for i in range(n):
        t = i / SR
        if wave == "square":
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave == "saw":
            v = 2.0 * ((freq * t) % 1.0) - 1.0
        elif wave == "noise":
            v = random.uniform(-1, 1)
        else:
            v = math.sin(2 * math.pi * freq * t)
        buf.append(int(max(-1, min(1, v)) * _env(i, n) * vol * 32767))
    return buf


def mixbuf(*bufs):
    n = max(len(b) for b in bufs)
    out = [0] * n
    for b in bufs:
        for i, s in enumerate(b):
            out[i] += s
    return array("h", (int(max(-32767, min(32767, v))) for v in out))


def make_sound(buf):
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


class Audio:
    def __init__(self):
        self.ok = pygame.mixer.get_init() is not None
        self.snd = {}
        if not self.ok:
            return
        self.snd["clang"] = make_sound(mixbuf(tone(760, 130, 0.34, "square"),
                                              tone(1180, 90, 0.22)))
        self.snd["windup"] = make_sound(tone(300, 160, 0.2, "saw"))
        self.snd["hit"] = make_sound(mixbuf(tone(180, 220, 0.36, "saw"),
                                            tone(90, 240, 0.3, "square")))
        self.snd["riposte"] = make_sound(mixbuf(tone(700, 100, 0.3),
                                                tone(1050, 130, 0.26)))
        self.snd["whiff"] = make_sound(tone(200, 140, 0.24, "sine"))
        self.snd["win"] = make_sound(mixbuf(tone(660, 120, 0.3),
                                            tone(880, 140, 0.28),
                                            tone(1100, 170, 0.24)))
        self._music()

    def _music(self):
        base = [165, 196, 220, 196, 147, 185, 220, 185]
        loop = array("h")
        for f in base:
            loop.extend(mixbuf(tone(f, 300, 0.12, "saw"),
                               tone(f / 2, 300, 0.1, "sine")))
        self.music = make_sound(loop)

    def play(self, k):
        s = self.snd.get(k)
        if s:
            try:
                s.play()
            except Exception:
                pass

    def start_music(self):
        if getattr(self, "music", None):
            try:
                self.music.play(loops=-1)
            except Exception:
                pass


FOE_COLS = [(150, 120, 90), (120, 140, 160), (150, 90, 90), (110, 150, 110),
            (160, 130, 170), (170, 90, 70)]


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.quit()
            pygame.mixer.init(SR, -16, 1, 512)
        except Exception:
            pass
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(T("title"))
        ic = os.path.join(app_dir(), "assets", "icon.ico")
        if os.path.exists(ic):
            try:
                pygame.display.set_icon(pygame.image.load(ic))
            except Exception:
                pass
        self.clock = pygame.time.Clock()
        self.big = pygame.font.SysFont("arialrounded,arial", 54, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.small = pygame.font.SysFont("arial", 22, bold=True)
        self.tiny = pygame.font.SysFont("arial", 17, bold=True)
        self.audio = Audio()
        self.bg = self._make_bg()
        self.best = self._load_best()
        self.state = "menu"
        self.reset()
        self.audio.start_music()

    def _load_best(self):
        try:
            with open(os.path.join(cache_dir(), "score.json")) as f:
                return int(json.load(f).get("best", 0))
        except Exception:
            return 0

    def _save_best(self):
        try:
            with open(os.path.join(cache_dir(), "score.json"), "w") as f:
                json.dump({"best": self.best}, f)
        except Exception:
            pass

    def _make_bg(self):
        s = pygame.Surface((W, H))
        for y in range(H):
            s.fill((int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * y / H),
                    int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * y / H),
                    int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * y / H)),
                   (0, y, W, 1))
        # arena-vloer
        pygame.draw.rect(s, (44, 36, 56), (0, GY, W, H - GY))
        pygame.draw.line(s, (66, 54, 80), (0, GY), (W, GY), 3)
        for x in range(0, W, 60):
            pygame.draw.line(s, (36, 30, 46), (x, GY), (x, H), 2)
        # publiek-silhouet + toortsen
        for tx in (80, W - 80):
            pygame.draw.line(s, (90, 70, 50), (tx, GY - 120), (tx, GY), 5)
            circ(s, tx, GY - 128, 10, (255, 170, 60))
        return s

    def reset(self):
        self.player = Fighter(300, 1, dragon=True, col=PURPLE)
        self.foe_n = 1
        self.php = 6
        self.pmaxhp = 6
        self.score = 0
        self.shake = 0
        self.pinv = 0
        self.whiff = 0
        self._pending_open = 0
        self._p_adv_timer = 0
        self.msg = ""
        self.msg_col = INK
        self.msgt = 0
        self._new_foe()               # zet zelf phase = "enter" (aanlopen)

    def _new_foe(self):
        self.foe = Fighter(600, -1, dragon=False,
                           col=FOE_COLS[(self.foe_n - 1) % len(FOE_COLS)])
        self.fhp = 5 + self.foe_n * 2
        self.fmaxhp = self.fhp
        self.foe.pose = "guard"
        self.f_state = "idle"
        self.f_timer = random.randint(40, 80)
        self.f_open = 0
        self.parried = False
        # beide vechters komen van de zijkant aanlopen naar hun plek
        self.player.cur_adv = -150
        self.player.adv_target = 0
        self.foe.cur_adv = -150
        self.foe.adv_target = 0
        self.phase = "enter"

    def _wind_time(self):
        return max(22, 62 - self.foe_n * 5)

    # ---------- loop ----------
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                elif e.type == pygame.KEYDOWN:
                    self._key(e.key)
            if self.state == "play" and self.phase in ("fight", "enter"):
                self._update()
            self._draw()
            self.clock.tick(FPS)

    def _quit(self):
        if self.score > self.best:
            self.best = self.score
        self._save_best()
        pygame.quit()
        sys.exit()

    def _key(self, k):
        if k == pygame.K_i:
            self._info()
            return
        if k == pygame.K_d and self.state != "play":
            try:
                webbrowser.open(DONATE)
            except Exception:
                pass
            return
        if self.state == "menu":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self._quit()
        elif self.state == "play":
            if self.phase == "fight":
                if k == pygame.K_UP:
                    self.player.guard = "high"
                elif k == pygame.K_DOWN:
                    self.player.guard = "low"
                elif k == pygame.K_SPACE:
                    self._player_strike()
                elif k in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = "pause"
            elif self.phase == "won":
                if k == pygame.K_RETURN:
                    self.foe_n += 1
                    self.score += 1
                    self.php = min(self.pmaxhp, self.php + 2)
                    self._new_foe()          # aanlopen naar de volgende ridder
                elif k in (pygame.K_p, pygame.K_ESCAPE):
                    self.state = "pause"
        elif self.state == "pause":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "play"
        elif self.state == "over":
            if k == pygame.K_RETURN:
                self.reset()
                self.state = "play"
            elif k == pygame.K_ESCAPE:
                self.state = "menu"

    def _player_strike(self):
        # alleen effectief als de vijand OPEN staat
        if self.f_state == "open" and self.f_open > 0:
            dmg = 2 if self.parried else 1
            self.fhp -= dmg
            self.foe.pose = "hurt"
            self.f_open = 0
            self.f_state = "recover"
            self.f_timer = 26
            self._p_adv_timer = 16          # jij stapt vooruit met de steek
            self._flash(T("riposte"), (120, 255, 140))
            self.audio.play("riposte")
            self.shake = 6
            if self.fhp <= 0:
                self.phase = "won"
                self.audio.play("win")
                self._flash(T("win"), GOLDC)
        else:
            # misslag -> jij staat even open
            self.whiff = 26
            self._flash(T("whiff"), (255, 150, 120))
            self.audio.play("whiff")

    def _flash(self, txt, col):
        self.msg = txt
        self.msg_col = col
        self.msgt = 55

    # ---------- update ----------
    def _update(self):
        # positie-lerp (aanlopen naar elkaar / uithalen / terugdeinzen)
        for ftr in (self.player, self.foe):
            ftr.cur_adv += (ftr.adv_target - ftr.cur_adv) * 0.14
        if self.phase == "enter":
            self.player.pose = self.foe.pose = "guard"
            if abs(self.player.cur_adv) < 5 and abs(self.foe.cur_adv) < 5:
                self.player.cur_adv = self.foe.cur_adv = 0.0
                self.phase = "fight"
            return
        if self.pinv > 0:
            self.pinv -= 1
        if self.whiff > 0:
            self.whiff -= 1
        if self.shake > 0:
            self.shake -= 1
        if self.msgt > 0:
            self.msgt -= 1
        self.player.pose = "guard"

        st = self.f_state
        self.f_timer -= 1
        if st == "idle":
            self.foe.pose = "guard"
            if self.f_timer <= 0:
                self.foe.line = random.choice(["high", "low"])
                self.foe.pose = "windup"
                self.f_state = "windup"
                self.f_timer = self._wind_time()
                self.audio.play("windup")
        elif st == "windup":
            self.foe.pose = "windup"
            if self.f_timer <= 0:
                self._resolve_strike()
        elif st == "strike":
            self.foe.pose = "strike"
            if self.f_timer <= 0:
                self.f_state = "open"
                self.f_open = self._pending_open
        elif st == "open":
            self.foe.pose = "open"
            self.f_open -= 1
            if self.f_open <= 0:
                self.f_state = "idle"
                self.f_timer = random.randint(30, 70)
        elif st == "recover":
            self.foe.pose = "hurt"
            if self.f_timer <= 0:
                self.f_state = "idle"
                self.f_timer = random.randint(30, 70)

        # doelverplaatsingen bepalen (uithalen / deinzen)
        adv_map = {"idle": 0, "windup": 16, "strike": 72,
                   "open": -26, "recover": -18}
        self.foe.adv_target = adv_map.get(self.f_state, 0)
        if self._p_adv_timer > 0:
            self._p_adv_timer -= 1
            self.player.adv_target = 60
        elif self.whiff > 0:
            self.player.adv_target = 40
        elif self.pinv > 30:
            self.player.adv_target = -24
        else:
            self.player.adv_target = 0

    def _resolve_strike(self):
        line = self.foe.line
        if self.whiff > 0:
            # jij staat open door een misslag -> gegarandeerd raak
            self._apply_hit(extra=True)
        elif self.player.guard == line:
            self.parried = True
            self._pending_open = 42        # gepareerd -> groot counter-venster
            self._flash(T("parry"), (150, 220, 255))
            self.audio.play("clang")
            self.shake = 5
        else:
            self._apply_hit(extra=False)
        # korte zichtbare uithaal-fase (vijand stapt vooruit), dan open
        self.foe.pose = "strike"
        self.f_state = "strike"
        self.f_timer = 10

    def _apply_hit(self, extra=False):
        if self.pinv == 0:
            self.php -= 1 + self.foe_n // 4
            self.pinv = 40
            self.shake = 9
            self._flash(T("hit_you"), (255, 120, 120))
            self.audio.play("hit")
        self.parried = False
        self._pending_open = 20 if not extra else 12
        if self.php <= 0:
            if self.score > self.best:
                self.best = self.score
                self._save_best()
            self.state = "over"

    # ---------- teken ----------
    def _draw(self):
        sc = self.screen
        sc.blit(self.bg, (0, 0))
        if self.state == "menu":
            self._menu(sc)
            pygame.display.flip()
            return
        sh = (0, 0)
        if self.shake > 0:
            sh = (random.randint(-self.shake, self.shake), 0)
        # lijn-markers (hoog/laag) ter oriëntatie
        self._lines(sc)
        self.foe.draw(sc, (sh[0], 0) if self.foe.pose in
                      ("strike", "hurt") else (0, 0))
        self.player.draw(sc, sh if self.pinv > 0 else (0, 0))
        self._hud(sc)
        if self.state == "play" and self.phase == "fight":
            self._guard_ind(sc)
        if self.msgt > 0:
            r = self.mid.render(self.msg, True, self.msg_col)
            sc.blit(r, (W // 2 - r.get_width() // 2, 170))
        if self.phase == "won" and self.state == "play":
            self._center(sc, T("win"), self.big, GOLDC, 40)
            self._center(sc, T("next"), self.small, INK, 100)
        if self.state == "pause":
            self._overlay(sc, T("paused"), T("resume"))
        elif self.state == "over":
            self._overlay(sc, T("gameover"), T("reached") % self.score)
        pygame.display.flip()

    def _lines(self, sc):
        # subtiele hoge/lage lijn tussen de vechters
        for ly, lab in ((GY - 78, "high"), (GY - 40, "low")):
            hot = (self.f_state == "windup" and self.foe.line == lab)
            col = (255, 120, 80) if hot else (60, 52, 76)
            pygame.draw.line(sc, col, (340, ly), (560, ly), 4 if hot else 2)

    def _guard_ind(self, sc):
        g = self.player.guard
        y = GY - 78 if g == "high" else GY - 40
        pygame.draw.circle(sc, PURPLE_L, (330, y), 8)
        t = self.tiny.render(T("guard") + ": " + T(g), True, PURPLE_L)
        sc.blit(t, (250, GY + 20))

    def _hud(self, sc):
        for i in range(self.pmaxhp):
            c = (220, 70, 90) if i < self.php else (70, 55, 70)
            self._heart(sc, 26 + i * 26, 30, c)
        # vijand-HP
        pygame.draw.rect(sc, (40, 24, 30), (W - 250, 22, 230, 16),
                         border_radius=8)
        fr = max(0, self.fhp / self.fmaxhp)
        pygame.draw.rect(sc, (220, 90, 90), (W - 250, 22, int(230 * fr), 16),
                         border_radius=8)
        f = self.small.render("%s %d" % (T("foe"), self.foe_n), True, INK)
        sc.blit(f, (W - 250, 42))
        s = self.small.render("%s: %d   %s: %d" %
                              (T("score"), self.score, T("best"), self.best),
                              True, GOLDC)
        sc.blit(s, (W // 2 - s.get_width() // 2, 20))

    def _heart(self, sc, x, y, c):
        circ(sc, x - 4, y, 5, c)
        circ(sc, x + 4, y, 5, c)
        poly(sc, [(x - 9, y + 1), (x + 9, y + 1), (x, y + 11)], c)

    def _center(self, sc, txt, font, col, dy=0):
        r = font.render(txt, True, col)
        sc.blit(r, (W // 2 - r.get_width() // 2, H // 2 + dy))

    def _overlay(self, sc, title, sub):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((10, 8, 16, 180))
        sc.blit(o, (0, 0))
        self._center(sc, title, self.big, (240, 130, 130), -50)
        self._center(sc, sub, self.mid, INK, 16)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 64)
        self._center(sc, T("menu"), self.small, (170, 160, 190), 98)

    def _menu(self, sc):
        p = Fighter(360, 1, dragon=True, col=PURPLE)
        e = Fighter(540, -1, dragon=False, col=FOE_COLS[0])
        p.guard = "high"
        e.pose = "windup"
        e.line = "low"
        e.draw(sc)
        p.draw(sc)
        self._center(sc, T("title"), self.big, PURPLE_L, -200)
        self._center(sc, T("sub"), self.mid, (200, 190, 225), -140)
        self._center(sc, T("how"), self.small, INK, 120)
        self._center(sc, T("start"), self.mid, GOLDC, 158)
        self._center(sc, T("ctrl"), self.small, (210, 204, 230), 200)
        self._center(sc, "%s    %s    %s" %
                     (T("donate"), T("info"), T("quit")),
                     self.small, (170, 160, 195), 234)
        self._center(sc, "%s: %d" % (T("best"), self.best), self.small,
                     GOLDC, 268)

    def _info(self):
        self._draw()
        box = pygame.Surface((660, 190), pygame.SRCALPHA)
        box.fill((20, 16, 30, 240))
        pygame.draw.rect(box, PURPLE_L, box.get_rect(), 2, border_radius=10)
        y = 24
        for line in T("info_txt").split("\n"):
            box.blit(self.small.render(line, True, INK), (24, y))
            y += 30
        self.screen.blit(box, (W // 2 - 330, H // 2 - 95))
        pygame.display.flip()
        wait = True
        while wait:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._quit()
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    wait = False
            self.clock.tick(30)


def main():
    Game().run()


if __name__ == "__main__":
    main()

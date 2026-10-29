# -*- coding: utf-8 -*-
"""sfx.py - procedureel geluid + muziek voor DraveBoulder (Dravenlock Games)."""
from __future__ import annotations

import math

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None
try:
    import pygame
except Exception:  # pragma: no cover
    pygame = None

SR = 44100


def _ci(v, lo, hi):
    return max(lo, min(hi, v))


class Sfx:
    def __init__(self):
        self.ready = False
        self.enabled = True
        self.volume = 0.8
        self._sounds = {}
        self._music = {}
        self._music_name = None
        self.ch_music = None

    def init(self):
        if np is None or pygame is None:
            self.ready = False
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(SR, -16, 2, 512)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(24)
            self.ch_music = pygame.mixer.Channel(0)
            self._build_sounds()
            self.ready = True
        except Exception:
            self.ready = False

    @staticmethod
    def _adsr(n, a=0.01, d=0.05, s=0.7, r=0.05):
        if n <= 0:
            return np.zeros(0, dtype=np.float32)
        ai = _ci(int(a * SR), 0, n)
        di = _ci(int(d * SR), 0, n - ai)
        ri = _ci(int(r * SR), 0, n - ai - di)
        si = max(0, n - ai - di - ri)
        env = np.ones(n, dtype=np.float32)
        if ai > 0:
            env[:ai] = np.linspace(0, 1, ai, dtype=np.float32)
        if di > 0:
            env[ai:ai + di] = np.linspace(1, s, di, dtype=np.float32)
        if si > 0:
            env[ai + di:ai + di + si] = s
        if ri > 0:
            env[ai + di + si:] = np.linspace(s, 0, ri, dtype=np.float32)
        return env

    @staticmethod
    def _tone(freq, dur, kind="sine"):
        n = max(1, int(dur * SR))
        t = np.arange(n, dtype=np.float32) / SR
        ph = 2 * math.pi * freq * t
        if kind == "square":
            w = np.sign(np.sin(ph))
        elif kind == "saw":
            w = 2.0 * (freq * t - np.floor(0.5 + freq * t))
        elif kind == "tri":
            w = 2.0 * np.abs(2.0 * (freq * t - np.floor(0.5 + freq * t))) - 1.0
        else:
            w = np.sin(ph)
        return w.astype(np.float32)

    @staticmethod
    def _noise(dur):
        n = max(1, int(dur * SR))
        return (np.random.rand(n).astype(np.float32) * 2 - 1)

    def _snd(self, mono):
        mono = np.clip(mono, -1, 1)
        pcm = (mono * 32767 * 0.9).astype(np.int16)
        return pygame.sndarray.make_sound(np.ascontiguousarray(np.column_stack([pcm, pcm])))

    def _build_sounds(self):
        S = {}

        def add(name, mono):
            try:
                S[name] = self._snd(mono)
            except Exception:
                pass

        # graven (zacht ruisje)
        dg = self._noise(0.06)
        dg = np.convolve(dg, np.ones(8, dtype=np.float32) / 8, mode="same") * self._adsr(int(0.06 * SR), 0.003, 0.02, 0.4, 0.03)
        add("dig", dg * 0.3)
        # diamant pakken
        add("diamond", np.concatenate([
            self._tone(1175, 0.05, "tri") * self._adsr(int(0.05 * SR)),
            self._tone(1568, 0.08, "tri") * self._adsr(int(0.08 * SR))]) * 0.4)
        # rots schuiven/duwen
        add("push", self._tone(90, 0.1, "saw") * self._adsr(int(0.1 * SR), 0.004, 0.04, 0.4, 0.04) * 0.34)
        # rots landt (val)
        rk = self._noise(0.12) * np.exp(-np.linspace(0, 16, int(0.12 * SR)))
        rk += self._tone(70, 0.12, "square") * self._adsr(int(0.12 * SR), 0.002, 0.04, 0.4, 0.05)
        add("rock", rk.astype(np.float32) * 0.4)
        # uitgang open
        add("exit", np.concatenate([self._tone(f, 0.09, "tri") * self._adsr(int(0.09 * SR))
                                    for f in [523, 659, 784, 1047, 1319]]) * 0.45)
        # ontploffing
        n = int(0.4 * SR)
        ex = self._noise(0.4) * np.exp(-np.linspace(0, 9, n))
        ex += (self._tone(60, 0.4, "square") * self._adsr(n, 0.002, 0.1, 0.5, 0.25)) * 0.5
        add("boom", ex.astype(np.float32) * 0.5)
        # tijd bijna op (tik)
        add("tick", self._tone(880, 0.04, "square") * self._adsr(int(0.04 * SR), 0.002, 0.01, 0.4, 0.02) * 0.35)
        # dood
        add("death", np.concatenate([
            self._tone(300, 0.12, "square") * self._adsr(int(0.12 * SR)),
            self._tone(200, 0.16, "square") * self._adsr(int(0.16 * SR)),
            self._tone(120, 0.24, "square") * self._adsr(int(0.24 * SR))]) * 0.45)
        # grot klaar
        add("clear", np.concatenate([self._tone(f, d, "tri") * self._adsr(int(d * SR))
                                     for f, d in [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.28)]]) * 0.5)
        add("life", np.concatenate([
            self._tone(784, 0.08, "tri") * self._adsr(int(0.08 * SR)),
            self._tone(1047, 0.14, "tri") * self._adsr(int(0.14 * SR))]) * 0.45)
        add("click", self._tone(660, 0.05, "square") * self._adsr(int(0.05 * SR), 0.005, 0.01, 0.5, 0.02) * 0.5)
        add("select", np.concatenate([
            self._tone(523, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(784, 0.09, "tri") * self._adsr(int(0.09 * SR))]) * 0.5)
        add("victory", np.concatenate([self._tone(f, d, "tri") * self._adsr(int(d * SR))
                                       for f, d in [(523, 0.14), (659, 0.14), (784, 0.14), (1047, 0.3)]]) * 0.5)
        self._sounds = S

    def play(self, name):
        if not self.ready or not self.enabled:
            return
        s = self._sounds.get(name)
        if s is None:
            return
        try:
            s.set_volume(self.volume)
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.play(s)
        except Exception:
            pass

    # ---------- muziek ----------
    def _scale(self, root):
        return [root * (2 ** (st / 12.0)) for st in (0, 2, 3, 5, 7, 8, 10, 12)]

    def _build_track(self, name):
        info = {
            "menu":  dict(bpm=100, root=196, kind="tri", bars=8, seed=5, drums=False,
                          prog=[0, 5, 3, 4, 0, 5, 4, 4]),
            "play1": dict(bpm=120, root=220, kind="tri", bars=16, seed=9, drums=True,
                          prog=[0, 3, 5, 4, 0, 3, 4, 4, 0, 3, 5, 4, 6, 5, 4, 0]),
            "play2": dict(bpm=132, root=247, kind="saw", bars=16, seed=15, drums=True,
                          prog=[0, 6, 3, 5, 0, 6, 4, 4, 0, 6, 3, 5, 2, 6, 5, 4]),
            "victory": dict(bpm=120, root=262, kind="tri", bars=4, seed=21, drums=True,
                            prog=[0, 4, 5, 0]),
        }.get(name)
        if info is None:
            info = dict(bpm=124, root=220, kind="tri", bars=16, seed=0, drums=True, prog=[0, 5, 3, 4] * 4)
        bpm = info["bpm"]
        step = (60.0 / bpm) / 2.0
        bars = info["bars"]
        steps = bars * 8
        buf = np.zeros(int(steps * step * SR), dtype=np.float32)
        scale = self._scale(info["root"])
        kind = info["kind"]
        prog = info["prog"]
        rng = np.random.RandomState(info["seed"])

        def place(start, frag, gain=1.0):
            e = min(len(buf), start + len(frag))
            if e > start:
                buf[start:e] += frag[:e - start] * gain

        def note(deg):
            return scale[deg % len(scale)] * (1 + deg // len(scale))

        bank = []
        for _ in range(6):
            ph = [(-1 if rng.rand() < 0.24 else int(rng.choice([0, 2, 4, 2, 0, 4, 5, 7, 3]))) for _ in range(8)]
            bank.append(ph)
        order = [(rng.randint(0, len(bank)) if b % 4 == 3 else [0, 0, 1, 2][b % 4] % len(bank)) for b in range(bars)]
        for b in range(bars):
            chord = prog[b % len(prog)]
            ph = bank[order[b]]
            lift = 0 if b < bars // 2 else 7
            for j in range(8):
                d = ph[j]
                if d < 0:
                    continue
                dur = step * (0.9 if j % 2 == 0 else 0.7)
                place(int((b * 8 + j) * step * SR),
                      self._tone(note(chord + d + lift), dur, kind) *
                      self._adsr(int(dur * SR), 0.005, 0.04, 0.55, 0.08), 0.22)
        for b in range(bars):
            chord = prog[b % len(prog)]
            for half in (0, 1):
                deg = chord + (0 if half == 0 else 4)
                dur = step * 1.7
                place(int((b * 8 + half * 4) * step * SR),
                      self._tone(note(deg) * 0.5, dur, "saw") *
                      self._adsr(int(dur * SR), 0.005, 0.06, 0.7, 0.1), 0.28)
        if info["drums"]:
            for i in range(steps):
                pos = int(i * step * SR)
                if i % 4 == 0:
                    n = int(0.12 * SR)
                    tt = np.arange(n, dtype=np.float32) / SR
                    f = 120 * np.exp(-18 * tt) + 48
                    kick = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-9 * tt)
                    place(pos, kick.astype(np.float32), 0.4)
                if i % 8 == 4:
                    n = int(0.13 * SR)
                    sn = self._noise(0.13) * np.exp(-np.linspace(0, 22, n))
                    place(pos, sn.astype(np.float32), 0.2)
                if i % 2 == 1:
                    n = int(0.05 * SR)
                    hh = self._noise(0.05) * np.exp(-np.linspace(0, 36, n))
                    place(pos, hh.astype(np.float32), 0.07)
        peak = np.max(np.abs(buf)) + 1e-6
        buf = buf / peak * 0.72
        try:
            return self._snd(buf)
        except Exception:
            return None

    def start_music(self, name):
        if not self.ready or not self.enabled:
            self._music_name = name
            return
        if self._music_name == name and self.ch_music and self.ch_music.get_busy():
            return
        snd = self._music.get(name)
        if snd is None:
            snd = self._build_track(name)
            if snd is not None:
                self._music[name] = snd
        self._music_name = name
        if snd and self.ch_music:
            try:
                self.ch_music.play(snd, loops=-1)
                self.ch_music.set_volume(0.44 * self.volume)
            except Exception:
                pass

    def stop_music(self):
        self._music_name = None
        if self.ch_music:
            try:
                self.ch_music.stop()
            except Exception:
                pass

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        if self.ch_music:
            try:
                self.ch_music.set_volume(0.44 * self.volume)
            except Exception:
                pass

    def set_enabled(self, on):
        self.enabled = bool(on)
        if not on:
            self.stop_music()
        elif self._music_name:
            nm = self._music_name
            self._music_name = None
            self.start_music(nm)

    def update(self):
        pass

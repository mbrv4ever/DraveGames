# -*- coding: utf-8 -*-
"""sfx.py - procedureel geluid + muziek voor DraveBeat (Dravenlock Games).

De muziek is hier de kern: per nummer een melodieuze, herhalende track op een
vaste bpm (afgestemd op de noten in het spel). Plus korte trefgeluiden.
"""
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

# bpm per nummer (DraveBeat gebruikt dezelfde waarden voor de noottijden)
SONG_BPM = {"song1": 100, "song2": 124, "song3": 140, "menu": 92, "victory": 120}
SONG_STEPS = 64   # aantal 1/8-stappen in een loop


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

        # perfect - heldere dubbele chime
        add("perfect", np.concatenate([
            self._tone(1047, 0.05, "sine") * self._adsr(int(0.05 * SR)),
            self._tone(1568, 0.1, "sine") * self._adsr(int(0.1 * SR))]) * 0.4)
        # goed - zachtere ping
        add("good", self._tone(880, 0.08, "tri") * self._adsr(int(0.08 * SR), 0.003, 0.03, 0.5, 0.04) * 0.38)
        # mis - doffe dud
        add("miss", self._tone(150, 0.12, "square") * self._adsr(int(0.12 * SR), 0.003, 0.04, 0.4, 0.05) * 0.35)
        # combo-mijlpaal
        add("combo", np.concatenate([
            self._tone(659, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(988, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(1319, 0.12, "tri") * self._adsr(int(0.12 * SR))]) * 0.42)
        # aftel-tik
        add("count", self._tone(880, 0.05, "square") * self._adsr(int(0.05 * SR), 0.002, 0.01, 0.4, 0.02) * 0.4)
        add("go", np.concatenate([
            self._tone(784, 0.08, "tri") * self._adsr(int(0.08 * SR)),
            self._tone(1175, 0.16, "tri") * self._adsr(int(0.16 * SR))]) * 0.45)
        add("click", self._tone(660, 0.05, "square") * self._adsr(int(0.05 * SR), 0.005, 0.01, 0.5, 0.02) * 0.5)
        add("select", np.concatenate([
            self._tone(523, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(784, 0.09, "tri") * self._adsr(int(0.09 * SR))]) * 0.5)
        add("victory", np.concatenate([self._tone(f, d, "tri") * self._adsr(int(d * SR))
                                       for f, d in [(523, 0.14), (659, 0.14), (784, 0.14), (1047, 0.3)]]) * 0.5)
        add("defeat", np.concatenate([self._tone(f, d, "tri") * self._adsr(int(d * SR))
                                      for f, d in [(392, 0.2), (330, 0.2), (262, 0.4)]]) * 0.5)
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
        # majeur-pentatonisch klinkt vrolijk en past bij elke noot
        return [root * (2 ** (st / 12.0)) for st in (0, 2, 4, 7, 9, 12, 14, 16)]

    def _build_track(self, name):
        bpm = SONG_BPM.get(name, 110)
        step = (60.0 / bpm) / 2.0           # 1/8 noot
        steps = SONG_STEPS
        buf = np.zeros(int(steps * step * SR), dtype=np.float32)
        root = {"song1": 220, "song2": 247, "song3": 262, "menu": 196, "victory": 262}.get(name, 220)
        scale = self._scale(root)
        rng = np.random.RandomState({"song1": 1, "song2": 2, "song3": 3, "menu": 4, "victory": 5}.get(name, 0))

        def place(start, frag, gain=1.0):
            e = min(len(buf), start + len(frag))
            if e > start:
                buf[start:e] += frag[:e - start] * gain

        kind = {"song1": "tri", "song2": "saw", "song3": "square", "menu": "tri", "victory": "tri"}.get(name, "tri")
        # melodie: een herhalend motief van 8 stappen, gevarieerd over de loop
        motif = [int(x) for x in rng.randint(0, len(scale), size=8)]
        for i in range(steps):
            if (i % 4 == 3) and rng.rand() < 0.4:
                continue  # af en toe een rust voor groove
            deg = motif[i % 8]
            octv = 1 + (1 if (i // 8) % 2 == 1 else 0)
            freq = scale[deg] * octv
            dur = step * 0.92
            place(int(i * step * SR),
                  self._tone(freq, dur, kind) * self._adsr(int(dur * SR), 0.004, 0.04, 0.6, 0.07), 0.24)
        # bas op de tel
        bass_seq = [0, 0, 4, 4, 3, 3, 5, 5]
        for i in range(0, steps, 2):
            freq = scale[bass_seq[(i // 2) % len(bass_seq)] % len(scale)] * 0.5
            dur = step * 1.8
            place(int(i * step * SR),
                  self._tone(freq, dur, "saw") * self._adsr(int(dur * SR), 0.005, 0.06, 0.7, 0.1), 0.3)
        # drums
        for i in range(steps):
            pos = int(i * step * SR)
            if i % 4 == 0:
                n = int(0.12 * SR)
                t = np.arange(n, dtype=np.float32) / SR
                f = 120 * np.exp(-18 * t) + 48
                kick = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-9 * t)
                place(pos, kick.astype(np.float32), 0.5)
            if i % 4 == 2:
                n = int(0.14 * SR)
                sn = self._noise(0.14) * np.exp(-np.linspace(0, 22, n))
                place(pos, sn.astype(np.float32), 0.28)
            if i % 2 == 1:
                n = int(0.05 * SR)
                hh = self._noise(0.05) * np.exp(-np.linspace(0, 36, n))
                place(pos, hh.astype(np.float32), 0.12)
        peak = np.max(np.abs(buf)) + 1e-6
        buf = buf / peak * 0.82
        try:
            return self._snd(buf)
        except Exception:
            return None

    def loop_seconds(self, name):
        bpm = SONG_BPM.get(name, 110)
        return SONG_STEPS * ((60.0 / bpm) / 2.0)

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
                self.ch_music.set_volume(0.6 * self.volume)
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
                self.ch_music.set_volume(0.6 * self.volume)
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

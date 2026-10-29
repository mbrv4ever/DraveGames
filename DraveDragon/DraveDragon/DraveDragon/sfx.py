# -*- coding: utf-8 -*-
"""sfx.py - procedureel geluid + muziek voor DraveDragon (Dravenlock Games).

Alles met numpy gesynthetiseerd; geen losse audiobestanden. Robuust: korte
tonen mogen de opbouw nooit laten crashen (ADSR wordt geklemd). Faalt audio
toch, dan blijft het spel gewoon stil werken (ready=False).
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
            pygame.mixer.set_num_channels(16)
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

        # vleugelslag (flap): korte zwoosh + lichte toon omhoog
        n = int(0.18 * SR)
        t = np.arange(n, dtype=np.float32) / SR
        flap = np.sin(2 * math.pi * (180 + 220 * t) * t) * 0.5
        flap += self._noise(0.18) * 0.25 * np.exp(-8 * t)
        add("flap", flap * self._adsr(n, 0.005, 0.04, 0.4, 0.09) * 0.5)
        # poort gehaald (score) - heldere ping
        add("score", np.concatenate([
            self._tone(784, 0.07, "sine") * self._adsr(int(0.07 * SR)),
            self._tone(1175, 0.12, "sine") * self._adsr(int(0.12 * SR))]) * 0.5)
        # edelsteen
        add("gem", np.concatenate([
            self._tone(988, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(1319, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(1760, 0.12, "tri") * self._adsr(int(0.12 * SR))]) * 0.45)
        # crash
        cr = self._noise(0.35) * self._adsr(int(0.35 * SR), 0.001, 0.06, 0.3, 0.2)
        cr += self._tone(110, 0.35, "square") * 0.4 * self._adsr(int(0.35 * SR))
        add("crash", cr * 0.6)
        # draak-brul
        n = int(0.6 * SR)
        t = np.arange(n, dtype=np.float32) / SR
        roar = np.sin(2 * math.pi * (80 + 30 * np.sin(2 * math.pi * 6 * t)) * t)
        roar = roar * self._adsr(n, 0.05, 0.2, 0.7, 0.3)
        add("roar", roar * 0.5)
        # menu
        add("click", self._tone(660, 0.05, "square") * self._adsr(int(0.05 * SR), 0.005, 0.01, 0.5, 0.02) * 0.5)
        add("select", np.concatenate([
            self._tone(523, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(784, 0.09, "tri") * self._adsr(int(0.09 * SR))]) * 0.5)
        add("milestone", np.concatenate([
            self._tone(659, 0.1, "tri") * self._adsr(int(0.1 * SR)),
            self._tone(880, 0.1, "tri") * self._adsr(int(0.1 * SR)),
            self._tone(1319, 0.2, "tri") * self._adsr(int(0.2 * SR))]) * 0.5)
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
        bpm = {"menu": 88, "fly1": 120, "fly2": 132, "victory": 120}.get(name, 116)
        step = (60.0 / bpm) / 2.0
        steps = 48
        buf = np.zeros(int(steps * step * SR), dtype=np.float32)
        root = {"menu": 196, "fly1": 220, "fly2": 262, "victory": 262}.get(name, 220)
        scale = self._scale(root)
        pats = {
            "menu":    [0, -1, 2, 4, -1, 2, 3, -1, 5, 4, 2, 0, 4, -1, 2, -1],
            "fly1":    [0, 2, 4, 5, 7, 5, 4, 2, 4, 5, 7, 9, 7, 5, 4, 2],
            "fly2":    [4, 5, 7, 9, 7, 5, 4, 7, 5, 4, 2, 0, 2, 4, 5, 7],
            "victory": [0, 2, 4, 7, 4, 2, 0, 4, 7, 9, 7, 5, 7, 4, 2, 0],
        }
        mel = pats.get(name, pats["fly1"])
        kind = {"menu": "tri", "fly1": "tri", "fly2": "saw", "victory": "tri"}.get(name, "tri")

        def place(start, frag):
            e = min(len(buf), start + len(frag))
            if e > start:
                buf[start:e] += frag[:e - start]

        for i in range(steps):
            note = mel[i % len(mel)]
            if note < 0:
                continue
            freq = scale[note % len(scale)] * (1 + note // len(scale))
            dur = step * 0.9
            place(int(i * step * SR),
                  self._tone(freq, dur, kind) * self._adsr(int(dur * SR), 0.005, 0.04, 0.6, 0.08) * 0.26)
        bass = [0, 0, 5, 5, 3, 3, 4, 4]
        for i in range(0, steps, 2):
            freq = scale[bass[(i // 2) % len(bass)] % len(scale)] * 0.5
            dur = step * 1.8
            place(int(i * step * SR),
                  self._tone(freq, dur, "saw") * self._adsr(int(dur * SR), 0.005, 0.06, 0.7, 0.1) * 0.3)
        for i in range(steps):
            pos = int(i * step * SR)
            if i % 2 == 0:
                n = int(0.12 * SR)
                t = np.arange(n, dtype=np.float32) / SR
                f = 110 * np.exp(-18 * t) + 45
                kick = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-9 * t)
                place(pos, kick.astype(np.float32) * 0.45)
        peak = np.max(np.abs(buf)) + 1e-6
        buf = buf / peak * 0.8
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
                self.ch_music.set_volume(0.5 * self.volume)
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
                self.ch_music.set_volume(0.5 * self.volume)
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

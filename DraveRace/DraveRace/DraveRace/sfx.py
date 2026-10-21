# -*- coding: utf-8 -*-
"""sfx.py - procedureel geluid + muziek voor DraveRace (Dravenlock Games).

Alles wordt met numpy gesynthetiseerd; geen losse audiobestanden. De motor is
robuust: korte tonen mogen de opbouw nooit laten crashen (de ADSR-omhullende
wordt netjes geklemd). Faalt audio toch, dan blijft het spel gewoon werken
(stil) - `ready` wordt dan False.

Gebruik:
    sfx = Sfx(); sfx.init()
    sfx.start_music("menu")        # muziek aan
    sfx.update()                   # elke frame aanroepen
    sfx.play("crash")              # los effect
    sfx.set_engine(speed_ratio)    # motorgeluid (0..1), 0 = uit
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


def _clampi(v, lo, hi):
    return max(lo, min(hi, v))


class Sfx:
    def __init__(self):
        self.ready = False
        self.enabled = True
        self.volume = 0.8
        self._sounds = {}
        self._engine_loops = []     # losse motor-loops per toerental
        self._engine_idx = -1
        self._music = {}            # naam -> Sound (lui opgebouwd)
        self._music_name = None
        self.ch_engine = None
        self.ch_music = None

    # ---------- init ----------
    def init(self):
        if np is None or pygame is None:
            self.ready = False
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(SR, -16, 2, 512)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self.ch_engine = pygame.mixer.Channel(0)
            self.ch_music = pygame.mixer.Channel(1)
            self._build_sounds()
            self._build_engine_loops()
            self.ready = True
        except Exception:
            self.ready = False

    # ---------- synth-helpers ----------
    @staticmethod
    def _adsr(n, a=0.01, d=0.05, s=0.7, r=0.05):
        """Veilige ADSR-omhullende; klemt segmenten zodat korte tonen niet crashen."""
        if n <= 0:
            return np.zeros(0, dtype=np.float32)
        ai = _clampi(int(a * SR), 0, n)
        di = _clampi(int(d * SR), 0, n - ai)
        ri = _clampi(int(r * SR), 0, n - ai - di)
        si = n - ai - di - ri
        si = max(0, si)
        env = np.ones(n, dtype=np.float32)
        if ai > 0:
            env[:ai] = np.linspace(0.0, 1.0, ai, dtype=np.float32)
        if di > 0:
            env[ai:ai + di] = np.linspace(1.0, s, di, dtype=np.float32)
        if si > 0:
            env[ai + di:ai + di + si] = s
        if ri > 0:
            env[ai + di + si:] = np.linspace(s, 0.0, ri, dtype=np.float32)
        return env

    @staticmethod
    def _tone(freq, dur, kind="sine", detune=0.0):
        n = max(1, int(dur * SR))
        t = np.arange(n, dtype=np.float32) / SR
        f = freq * (1.0 + detune)
        ph = 2 * math.pi * f * t
        if kind == "sine":
            w = np.sin(ph)
        elif kind == "square":
            w = np.sign(np.sin(ph))
        elif kind == "saw":
            w = 2.0 * (f * t - np.floor(0.5 + f * t))
        elif kind == "tri":
            w = 2.0 * np.abs(2.0 * (f * t - np.floor(0.5 + f * t))) - 1.0
        else:
            w = np.sin(ph)
        return w.astype(np.float32)

    @staticmethod
    def _noise(dur):
        n = max(1, int(dur * SR))
        return (np.random.rand(n).astype(np.float32) * 2.0 - 1.0)

    def _to_sound(self, mono):
        mono = np.clip(mono, -1.0, 1.0)
        pcm = (mono * 32767.0 * 0.9).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))

    # ---------- effecten ----------
    def _build_sounds(self):
        S = {}

        def add(name, mono):
            try:
                S[name] = self._to_sound(mono)
            except Exception:
                pass

        # menu-klik
        m = self._tone(660, 0.05, "square") * self._adsr(int(0.05 * SR), 0.005, 0.01, 0.5, 0.02)
        add("click", m * 0.5)
        # selecteren
        m = np.concatenate([
            self._tone(523, 0.06, "tri") * self._adsr(int(0.06 * SR)),
            self._tone(784, 0.09, "tri") * self._adsr(int(0.09 * SR)),
        ])
        add("select", m * 0.5)
        # checkpoint-chime
        m = np.concatenate([
            self._tone(880, 0.08, "sine") * self._adsr(int(0.08 * SR)),
            self._tone(1175, 0.12, "sine") * self._adsr(int(0.12 * SR)),
        ])
        add("checkpoint", m * 0.5)
        # ronde/stage klaar
        m = np.concatenate([
            self._tone(523, 0.1, "tri") * self._adsr(int(0.1 * SR)),
            self._tone(659, 0.1, "tri") * self._adsr(int(0.1 * SR)),
            self._tone(784, 0.1, "tri") * self._adsr(int(0.1 * SR)),
            self._tone(1047, 0.22, "tri") * self._adsr(int(0.22 * SR)),
        ])
        add("lap", m * 0.5)
        # countdown-beep
        m = self._tone(440, 0.12, "square") * self._adsr(int(0.12 * SR), 0.005, 0.02, 0.8, 0.03)
        add("beep", m * 0.45)
        m = self._tone(880, 0.25, "square") * self._adsr(int(0.25 * SR), 0.005, 0.02, 0.8, 0.05)
        add("go", m * 0.5)
        # skid (ruis met snelle uitdoving)
        nz = self._noise(0.35)
        env = self._adsr(len(nz), 0.005, 0.05, 0.4, 0.25)
        # eenvoudige laagdoorlaat door cumulatief gemiddelde
        k = 8
        nz = np.convolve(nz, np.ones(k, dtype=np.float32) / k, mode="same")
        add("skid", nz * env * 0.5)
        # crash (lage dreun + ruis)
        nz = self._noise(0.4)
        thump = self._tone(70, 0.4, "sine")
        env = self._adsr(len(nz), 0.001, 0.08, 0.3, 0.3)
        add("crash", (nz * 0.6 + thump * 0.8) * env * 0.6)
        # boost/nitro
        n = int(0.5 * SR)
        t = np.arange(n, dtype=np.float32) / SR
        sweep = np.sin(2 * math.pi * (300 + 900 * t) * t)
        add("boost", sweep * self._adsr(n, 0.02, 0.1, 0.6, 0.2) * 0.4)
        # victory-fanfare
        notes = [(523, 0.14), (659, 0.14), (784, 0.14), (1047, 0.3)]
        parts = [self._tone(f, d, "tri") * self._adsr(int(d * SR)) for f, d in notes]
        add("victory", np.concatenate(parts) * 0.5)
        # defeat
        notes = [(392, 0.2), (330, 0.2), (262, 0.4)]
        parts = [self._tone(f, d, "tri") * self._adsr(int(d * SR)) for f, d in notes]
        add("defeat", np.concatenate(parts) * 0.5)

        self._sounds = S

    # ---------- motorgeluid ----------
    def _build_engine_loops(self):
        """Maak een paar gezoem-loops voor oplopend toerental."""
        self._engine_loops = []
        base_freqs = [60, 80, 105, 135, 170, 210, 260]
        for bf in base_freqs:
            dur = 0.25
            n = int(dur * SR)
            t = np.arange(n, dtype=np.float32) / SR
            # ruige motor: saw + lichte ruis + subharmonische
            w = (0.6 * (2.0 * (bf * t - np.floor(0.5 + bf * t)))
                 + 0.25 * np.sin(2 * math.pi * bf * 0.5 * t)
                 + 0.15 * (np.random.rand(n).astype(np.float32) * 2 - 1))
            # naadloos maken: vermenigvuldig met milde raamfunctie-cross? houd simpel
            w = w / (np.max(np.abs(w)) + 1e-6)
            try:
                self._engine_loops.append(self._to_sound(w * 0.5))
            except Exception:
                pass

    def set_engine(self, ratio):
        """Motorgeluid op basis van snelheidsverhouding (0..1). 0 = uit."""
        if not self.ready or not self.enabled or not self._engine_loops:
            return
        if ratio <= 0.01:
            if self.ch_engine and self.ch_engine.get_busy():
                self.ch_engine.stop()
            self._engine_idx = -1
            return
        idx = _clampi(int(ratio * (len(self._engine_loops) - 1) + 0.0),
                      0, len(self._engine_loops) - 1)
        if idx != self._engine_idx:
            self._engine_idx = idx
            try:
                self.ch_engine.play(self._engine_loops[idx], loops=-1)
                self.ch_engine.set_volume(0.35 * self.volume)
            except Exception:
                pass

    # ---------- losse effecten ----------
    def play(self, name):
        if not self.ready or not self.enabled:
            return
        s = self._sounds.get(name)
        if s is None:
            return
        try:
            s.set_volume(self.volume)
            ch = pygame.mixer.find_channel(True)
            if ch is not None:
                ch.play(s)
        except Exception:
            pass

    # ---------- muziek ----------
    def _scale(self, root):
        # mineur-pentatonisch klinkt lekker "race-achtig"
        return [root * (2 ** (st / 12.0)) for st in (0, 3, 5, 7, 10, 12)]

    def _build_track(self, name):
        """Bouw een ~12s muziek-loop. Verschillende stijlen per naam."""
        bpm_map = {"menu": 96, "race1": 138, "race2": 150, "chase": 162,
                   "victory": 120, "race3": 128}
        bpm = bpm_map.get(name, 130)
        beat = 60.0 / bpm
        step = beat / 2.0          # achtsten
        steps = 48                 # ~ aantal achtsten in de loop
        total = int(steps * step * SR)
        buf = np.zeros(total, dtype=np.float32)

        roots = {"menu": 220, "race1": 165, "race2": 196, "chase": 147,
                 "victory": 262, "race3": 175}
        root = roots.get(name, 196)
        scale = self._scale(root)

        # melodie-patroon (indices in scale, -1 = stilte)
        patterns = {
            "menu":    [0, -1, 2, -1, 4, -1, 2, 3, 0, -1, 2, 4, 5, 4, 2, 0],
            "race1":   [0, 2, 3, 2, 4, 3, 2, 0, 5, 4, 3, 2, 0, 2, 4, 5],
            "race2":   [4, 5, 4, 2, 3, 2, 0, 2, 5, 4, 5, 3, 4, 2, 0, 4],
            "race3":   [0, 0, 3, 4, 2, 2, 4, 5, 3, 3, 2, 0, 4, 5, 4, 2],
            "chase":   [0, 1, 0, 3, 2, 1, 0, 4, 3, 2, 1, 0, 5, 4, 3, 2],
            "victory": [0, 2, 4, 5, 4, 2, 0, 2, 4, 5, 4, 5, 0, 2, 4, 5],
        }
        mel = patterns.get(name, patterns["race1"])
        kind = {"menu": "tri", "race1": "saw", "race2": "saw",
                "race3": "square", "chase": "square", "victory": "tri"}.get(name, "saw")

        def place(arr, start, frag):
            end = min(len(arr), start + len(frag))
            if end > start:
                arr[start:end] += frag[:end - start]

        # melodie
        for i in range(steps):
            note = mel[i % len(mel)]
            if note < 0:
                continue
            idx = note % len(scale)
            octv = 1 + (note // len(scale))
            freq = scale[idx] * octv
            dur = step * 0.9
            n = int(dur * SR)
            frag = self._tone(freq, dur, kind) * self._adsr(n, 0.005, 0.04, 0.6, 0.08)
            place(buf, int(i * step * SR), frag * 0.28)

        # bas (kwart-noten, grondtoon/kwint)
        bass_seq = [0, 0, 4, 4, 2, 2, 5, 5]
        for i in range(0, steps, 2):
            bn = bass_seq[(i // 2) % len(bass_seq)]
            freq = scale[bn % len(scale)] * 0.5
            dur = step * 1.8
            n = int(dur * SR)
            frag = self._tone(freq, dur, "saw") * self._adsr(n, 0.005, 0.06, 0.7, 0.1)
            place(buf, int(i * step * SR), frag * 0.3)

        # drums: kick op de tel, hi-hat op de achtste, snare op 2 en 4
        for i in range(steps):
            pos = int(i * step * SR)
            if i % 2 == 0:  # kick
                n = int(0.12 * SR)
                t = np.arange(n, dtype=np.float32) / SR
                f = 110 * np.exp(-18 * t) + 45
                kick = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-9 * t)
                place(buf, pos, kick.astype(np.float32) * 0.5)
            # hi-hat
            n = int(0.04 * SR)
            hh = (np.random.rand(n).astype(np.float32) * 2 - 1) * np.exp(
                -np.linspace(0, 30, n))
            place(buf, pos, hh * 0.10)
            if i % 8 == 4:  # snare
                n = int(0.1 * SR)
                sn = (np.random.rand(n).astype(np.float32) * 2 - 1) * np.exp(
                    -np.linspace(0, 16, n))
                place(buf, pos, sn * 0.28)

        # normaliseren
        peak = np.max(np.abs(buf)) + 1e-6
        buf = buf / peak * 0.8
        try:
            return self._to_sound(buf)
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
        if snd is not None and self.ch_music is not None:
            try:
                self.ch_music.play(snd, loops=-1)
                self.ch_music.set_volume(0.5 * self.volume)
            except Exception:
                pass

    def stop_music(self):
        self._music_name = None
        if self.ch_music is not None:
            try:
                self.ch_music.stop()
            except Exception:
                pass

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        if self.ch_music is not None:
            try:
                self.ch_music.set_volume(0.5 * self.volume)
            except Exception:
                pass

    def set_enabled(self, on):
        self.enabled = bool(on)
        if not on:
            self.stop_music()
            if self.ch_engine:
                try:
                    self.ch_engine.stop()
                except Exception:
                    pass
            self._engine_idx = -1
        else:
            if self._music_name:
                start = self._music_name
                self._music_name = None
                self.start_music(start)

    def update(self):
        # muziek loopt vanzelf (loops=-1); niets te doen, maar gehouden voor API.
        pass

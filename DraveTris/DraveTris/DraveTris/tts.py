# -*- coding: utf-8 -*-
"""tts.py - gesproken stem voor DraveArrow via neuvoice (draagbaar).

Zelfde aanpak als DraveDungeon/DraveQuest: het stem-model downloadt zichzelf
bij het eerste gebruik. De standaardstem is "mofasa". Alles draait op een
achtergrond-thread zodat het spel nooit blokkeert, en faalt er iets (geen
model, geen internet, geen audio), dan blijft het spel gewoon stil verder
werken.
"""
from __future__ import annotations

import threading

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    import pygame
except Exception:  # pragma: no cover
    pygame = None


class Tts:
    def __init__(self, voice="M1", lang="nl", data_dir=None):
        self.voice = voice
        self.lang = lang
        self.enabled = True
        self.data_dir = data_dir
        self._tts = None
        self._style = None
        self._sr = 24000
        self._ready = False
        self._failed = False
        self._active = False     # er wordt geladen of gesproken
        self._lock = threading.Lock()

    def busy(self):
        """True zolang er geladen of gesproken wordt."""
        return self._active

    # ---------- model laden ----------
    def warmup(self):
        """Laad het model alvast op de achtergrond (niet-blokkerend)."""
        threading.Thread(target=self._ensure, daemon=True).start()

    def _voice_dir(self):
        # draagbaar: gebruik de map die de app meegeeft (naast de .exe);
        # anders een map naast het uitvoerbare bestand/script.
        import os
        import sys
        if self.data_dir:
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                return self.data_dir
            except Exception:
                pass
        if getattr(sys, "frozen", False):
            base = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base = os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
        try:
            os.makedirs(base, exist_ok=True)
        except Exception:
            pass
        return base

    def _ensure(self):
        if self._ready or self._failed:
            return
        with self._lock:
            if self._ready or self._failed:
                return
            try:
                from neuvoice import TTS
                tts = TTS(auto_download=True)
                names = list(getattr(tts, "voice_style_names", []) or [])

                want = (self.voice or "").strip().lower()
                pick = None
                # 1) exacte (hoofdletterongevoelige) match op de gevraagde code
                for n in names:
                    if n.strip().lower() == want:
                        pick = n
                        break
                # 2) anders: voorkeur voor een mannenstem (M..., niet F)
                if pick is None:
                    for n in names:
                        u = n.upper()
                        if u.startswith("M") or "MALE" in u or ("M" in u and "F" not in u):
                            pick = n
                            break
                # 3) laatste redmiddel: de eerste stem
                if pick is None and names:
                    pick = names[0]
                # gevonden stemmen wegschrijven (handig om de juiste te kiezen)
                try:
                    import os
                    with open(os.path.join(self._voice_dir(), "dravearrow-stemmen.txt"),
                              "w", encoding="utf-8") as f:
                        f.write("Gevraagde stem: %s\n" % self.voice)
                        f.write("Gekozen stem: %s\n\n" % pick)
                        f.write("Beschikbare stemmen (zet er een in config.json bij "
                                "'voice_name'):\n")
                        for n in names:
                            f.write("  - %s\n" % n)
                except Exception:
                    pass
                self._pick_name = pick
                self._style = tts.get_voice_style(pick) if pick else None
                self._sr = int(getattr(tts, "sample_rate", 24000) or 24000)
                self._tts = tts
                self._ready = True
            except Exception:
                self._failed = True

    # ---------- spreken ----------
    def set_voice(self, voice):
        if voice and voice.lower() != (self.voice or "").lower():
            self.voice = voice
            self._ready = False
            self._failed = False
            self._style = None
            self._tts = None

    def speak(self, text):
        if not self.enabled or np is None or pygame is None:
            return
        self._active = True
        threading.Thread(target=self._speak_blocking, args=(text,), daemon=True).start()

    def _speak_blocking(self, text):
        try:
            self._ensure()
            if not self._ready:
                self._active = False
                return
            with self._lock:
                wav, _dur = self._tts.synthesize(
                    text, voice_style=self._style, total_steps=10,
                    speed=1.0, lang=self.lang)
            snd = self._to_sound(wav)
            if snd is not None and pygame.mixer.get_init():
                snd.set_volume(1.0)
                ch = pygame.mixer.find_channel(True)
                if ch is not None:
                    ch.play(snd)
                    # wachten tot het afspelen klaar is
                    import time
                    while ch.get_busy():
                        time.sleep(0.05)
        except Exception:
            pass
        finally:
            self._active = False

    def _to_sound(self, wav):
        try:
            data = np.asarray(wav, dtype=np.float32).flatten()
            init = pygame.mixer.get_init()
            mr = init[0] if init else 44100
            if self._sr != mr and len(data) > 1:
                n = int(len(data) * mr / float(self._sr))
                xp = np.linspace(0.0, 1.0, len(data), dtype=np.float32)
                xq = np.linspace(0.0, 1.0, n, dtype=np.float32)
                data = np.interp(xq, xp, data).astype(np.float32)
            data = np.clip(data, -1.0, 1.0)
            pcm = (data * 32767.0 * 0.9).astype(np.int16)
            stereo = np.column_stack([pcm, pcm])
            return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))
        except Exception:
            return None

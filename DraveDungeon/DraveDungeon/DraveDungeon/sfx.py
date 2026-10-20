# -*- coding: utf-8 -*-
"""
DraveDungeon - procedurele retro-geluiden en muziek.

Alles wordt in het geheugen gegenereerd met numpy (geen externe bestanden).
Werkt alleen als numpy + de pygame-mixer beschikbaar zijn; anders stil.
"""
import math
import random
import threading

SR = 44100
_enabled = True
_volume = 0.6
_ready = False
_sounds = {}
_tracks = []
_track_last = -1
_music_chan = None
_np = None
_pg = None


def available():
    return _ready


def is_enabled():
    return _enabled and _ready


def get_volume():
    return _volume


# ---------------------------------------------------------------- bouwen
def _adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    np = _np
    env = np.ones(n)
    ai = int(SR * a); di = int(SR * d); ri = int(SR * r)
    ai = min(ai, n)
    if ai > 0:
        env[:ai] = np.linspace(0, 1, ai)
    if di > 0 and ai + di <= n:
        env[ai:ai + di] = np.linspace(1, s, di)
    env[ai + di:n - ri] = s
    if ri > 0:
        env[n - ri:] = np.linspace(s, 0, ri)
    return env


def _tone(freq, dur, vol=0.5, wave="square", a=0.005, d=0.05, s=0.7, r=0.08):
    np = _np
    n = max(1, int(SR * dur))
    t = np.arange(n) / SR
    ph = 2 * math.pi * freq * t
    if wave == "square":
        w = np.sign(np.sin(ph))
    elif wave == "sine":
        w = np.sin(ph)
    elif wave == "saw":
        w = 2 * ((freq * t) % 1.0) - 1
    elif wave == "tri":
        w = 2 * np.abs(2 * ((freq * t) % 1.0) - 1) - 1
    elif wave == "noise":
        w = np.random.uniform(-1, 1, n)
    else:
        w = np.sin(ph)
    return w * _adsr(n, a, d, s, r) * vol


def _sweep(f0, f1, dur, vol=0.5, wave="sine"):
    np = _np
    n = max(1, int(SR * dur))
    t = np.arange(n) / SR
    freq = np.linspace(f0, f1, n)
    ph = 2 * math.pi * np.cumsum(freq) / SR
    if wave == "square":
        w = np.sign(np.sin(ph))
    else:
        w = np.sin(ph)
    return w * _adsr(n, 0.005, 0.05, 0.8, 0.1) * vol


def _silence(dur):
    return _np.zeros(max(1, int(SR * dur)))


def _seq(parts):
    return _np.concatenate(parts) if parts else _np.zeros(1)


def _mk(arr):
    np = _np
    arr = np.clip(arr, -1, 1)
    data = (arr * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([data, data]))
    return _pg.sndarray.make_sound(stereo)


# noten (Hz)
N = dict(C=261.63, D=293.66, E=329.63, F=349.23, G=392.0, A=440.0, B=493.88,
         C5=523.25, D5=587.33, E5=659.25, F5=698.46, G5=783.99, A5=880.0,
         Bb=466.16, Ab=415.30, Eb=311.13, Db=277.18, Gb=369.99,
         C3=130.81, E3=164.81, G3=196.0, A3=220.0, F3=174.61, D3=146.83, Bb3=233.08)


def _build_sounds():
    s = {}
    # klik
    s["click"] = _mk(_tone(660, 0.05, 0.35, "square", r=0.03))
    # zwaardklap: lage thud + ruis
    s["hit"] = _mk(_tone(120, 0.12, 0.5, "square", r=0.1) * 0.6
                   + _tone(70, 0.12, 0.4, "noise", r=0.1) * 0.5)
    # magie: opgaande sweep met staart
    s["magic"] = _mk(_seq([_sweep(300, 900, 0.26, 0.4, "sine"),
                           _tone(900, 0.08, 0.25, "sine")]))
    # kritiek: stijgende fanfare
    s["crit"] = _mk(_seq([_tone(N["G"], 0.08, 0.5), _tone(N["C5"], 0.08, 0.5),
                          _tone(N["E5"], 0.08, 0.5), _tone(N["G5"], 0.18, 0.55)]))
    # mis: dalend womp
    s["miss"] = _mk(_seq([_tone(300, 0.1, 0.4, "saw"), _tone(180, 0.16, 0.4, "saw")]))
    # dobbelsteen-rammel
    tick = _tone(900, 0.018, 0.3, "noise", r=0.01)
    gap = _silence(0.045)
    s["dice"] = _mk(_seq([tick, gap] * 9))
    # genezen: zachte stijgende chime
    s["heal"] = _mk(_seq([_tone(N["C5"], 0.1, 0.35, "sine"),
                          _tone(N["E5"], 0.1, 0.35, "sine"),
                          _tone(N["G5"], 0.16, 0.35, "sine")]))
    # level-up: vrolijke arpeggio
    s["levelup"] = _mk(_seq([_tone(N["C"], 0.09, 0.5), _tone(N["E"], 0.09, 0.5),
                             _tone(N["G"], 0.09, 0.5), _tone(N["C5"], 0.09, 0.5),
                             _tone(N["E5"], 0.18, 0.55)]))
    # overwinning
    s["victory"] = _mk(_seq([_tone(N["C5"], 0.14, 0.5), _tone(N["E5"], 0.14, 0.5),
                             _tone(N["G5"], 0.14, 0.5), _tone(N["C5"], 0.1, 0.5),
                             _tone(N["G5"], 0.28, 0.55)]))
    # verlies
    s["defeat"] = _mk(_seq([_tone(N["E"], 0.18, 0.45, "tri"),
                            _tone(N["D"], 0.18, 0.45, "tri"),
                            _tone(N["C"], 0.18, 0.45, "tri"),
                            _tone(N["C3"], 0.4, 0.5, "tri")]))
    # draak-gebrul
    s["roar"] = _mk(_sweep(160, 60, 0.5, 0.55, "square")
                    + _tone(50, 0.5, 0.3, "noise", r=0.3))
    return s


def _part(seq, wave, vol, beat, s=0.6):
    """seq = lijst van (noot of None, duur-in-beats)."""
    out = []
    for note, d in seq:
        dur = d * beat
        if note is None:
            out.append(_silence(dur))
        else:
            r = min(0.1, dur * 0.35)
            out.append(_tone(N.get(note, 440), dur, vol, wave, d=0.04, s=s, r=r))
    return _seq(out)


def _drums(pattern, beat, sub=0.5):
    """pattern: tekst, elk teken = sub beats. K=kick S=snare H=hihat .=stilte."""
    np = _np
    kick = _sweep(150, 50, 0.12, 0.6, "sine")
    snare = _tone(240, 0.09, 0.4, "noise", d=0.02, s=0.2, r=0.05)
    hat = _tone(900, 0.035, 0.18, "noise", d=0.01, s=0.1, r=0.02)
    hits = {"K": kick, "S": snare, "H": hat}
    step = sub * beat
    total = int(SR * len(pattern) * step) + len(kick) + 8
    buf = np.zeros(total)
    for i, ch in enumerate(pattern):
        snd = hits.get(ch)
        if snd is not None:
            p = int(SR * i * step)
            buf[p:p + len(snd)] += snd
    return buf


def _mix(*parts):
    np = _np
    L = max(len(p) for p in parts)
    acc = np.zeros(L)
    for p in parts:
        acc[:len(p)] += p
    return _mk(np.clip(acc, -1, 1) * 0.55)


def _build_music_tracks():
    np = _np
    tracks = []

    # 1) Kerker-drone: traag, sferisch, lange sine-noten + lage drone, geen drums
    b = 0.5
    lead = [("A", 2), ("C5", 1.5), (None, 0.5), ("E5", 2), (None, 1),
            ("G", 2), ("F", 1.5), (None, 0.5), ("E5", 1), ("D5", 3), (None, 1)]
    bass = [("A3", 4), ("F3", 4), ("C3", 4), ("E3", 4)]
    tracks.append(_mix(_part(lead, "sine", 0.17, b, s=0.8),
                       _part(bass, "tri", 0.16, b, s=0.85)))

    # 2) Strijdmars: snel, scherp square + stevige drums, drijvend
    b = 0.2
    lead = [("D5", 1), ("D5", 0.5), ("F5", 0.5), ("E5", 1), ("A", 1),
            ("D5", 1), ("F5", 0.5), ("A5", 0.5), ("G5", 1), ("F5", 1),
            ("E5", 1), ("E5", 0.5), ("F5", 0.5), ("D5", 2)]
    bass = [("D3", 1)] * 4 + [("Bb3", 1)] * 2 + [("A3", 1)] * 2
    drums = "K.H.S.H.K.H.S.H.K.H.S.H.K.S.S.H."
    tracks.append(_mix(_part(lead, "square", 0.15, b, s=0.5),
                       _part(bass, "saw", 0.16, b, s=0.6),
                       _drums(drums, b)))

    # 3) Mysterie: pentatonisch, plukkende saw, syncopisch, licht
    b = 0.26
    lead = [("E", 0.5), (None, 0.5), ("G", 0.5), ("A", 1), (None, 0.5),
            ("C5", 0.5), ("D5", 1), (None, 0.5), ("A", 0.5), ("G", 0.5),
            ("E", 1), (None, 0.5), ("D", 0.5), ("E", 2)]
    bass = [("E3", 2), ("A3", 2), ("C3", 2), ("G3", 2)]
    tracks.append(_mix(_part(lead, "saw", 0.13, b, s=0.25),
                       _part(bass, "tri", 0.15, b, s=0.7),
                       _drums("..H...H...H...H.", b)))

    # 4) Heroisch thema: majeur, gepunteerd ritme, optimistisch
    b = 0.24
    lead = [("C5", 1.5), ("E5", 0.5), ("G5", 1.5), ("E5", 0.5), ("F5", 1),
            ("E5", 1), ("D5", 1.5), ("C5", 0.5), ("G", 1), ("C5", 2),
            ("D5", 1.5), ("E5", 0.5), ("C5", 2)]
    bass = [("C3", 2), ("G3", 2), ("F3", 2), ("G3", 2), ("C3", 2)]
    tracks.append(_mix(_part(lead, "square", 0.15, b, s=0.6),
                       _part(bass, "tri", 0.16, b, s=0.8),
                       _drums("K..H.S..K..H.S..", b)))

    # 5) Spookwals: 3/4, zweverige sine, mineur, onheilspellend
    b = 0.34
    lead = [("A", 1), ("B", 0.5), ("C5", 1.5), ("E5", 1), ("D5", 0.5),
            ("C5", 1.5), ("B", 1), ("Ab", 0.5), ("A", 2.5), (None, 1)]
    bass = [("A3", 3), ("F3", 3), ("E3", 3), ("A3", 3)]
    tracks.append(_mix(_part(lead, "sine", 0.16, b, s=0.85),
                       _part(bass, "tri", 0.15, b, s=0.85)))

    # 6) Kabouterdans: bouncy triangle-jig, lichte kick
    b = 0.17
    lead = [("G", 0.5), ("A", 0.5), ("B", 0.5), ("C5", 0.5), ("D5", 1),
            ("B", 0.5), ("G", 0.5), ("A", 1), ("E", 0.5), ("G", 0.5),
            ("D5", 0.5), ("B", 0.5), ("C5", 0.5), ("A", 0.5), ("G", 2)]
    bass = [("G3", 1), ("D3", 1), ("E3", 1), ("C3", 1)] * 2
    tracks.append(_mix(_part(lead, "tri", 0.18, b, s=0.4),
                       _part(bass, "tri", 0.15, b, s=0.6),
                       _drums("K..K..H.K..K..H.", b)))

    return tracks


# ---------------------------------------------------------------- API
def init(enabled=True, volume=0.6):
    global _enabled, _volume, _ready, _np, _pg, _sounds, _tracks
    _enabled = bool(enabled)
    _volume = max(0.0, min(1.0, volume))
    try:
        import numpy as np
        import pygame
        _np = np; _pg = pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)
    except Exception:
        _ready = False
        return

    def worker():
        global _sounds, _tracks, _ready
        try:
            _sounds = _build_sounds()
            _tracks = _build_music_tracks()
            _ready = True
            if _enabled:
                start_music()
        except Exception:
            _ready = False
    # bouwen kan even duren -> in achtergrond
    threading.Thread(target=worker, daemon=True).start()


def play(name, vol=1.0):
    if not (_enabled and _ready):
        return
    snd = _sounds.get(name)
    if snd is None:
        return
    try:
        snd.set_volume(_volume * vol)
        snd.play()
    except Exception:
        pass


def _play_next_track():
    global _music_chan, _track_last
    if not _tracks:
        return
    if len(_tracks) > 1:
        i = _track_last
        while i == _track_last:
            i = random.randint(0, len(_tracks) - 1)
    else:
        i = 0
    _track_last = i
    try:
        track = _tracks[i]
        length = track.get_length() or 4.0
        loops = max(0, int(round(8.0 / length)) - 1)   # ~8s per nummer voor de wissel
        _music_chan = _pg.mixer.Channel(15)
        _music_chan.set_volume(_volume * 0.5)
        _music_chan.play(track, loops=loops)
    except Exception:
        pass


def start_music():
    if not (_enabled and _ready) or not _tracks:
        return
    if _music_chan and _music_chan.get_busy():
        return
    _play_next_track()


def update():
    """Elke frame aanroepen: wisselt naar een volgend nummer als het huidige klaar is."""
    if not (_enabled and _ready) or not _tracks:
        return
    if _music_chan is None or not _music_chan.get_busy():
        _play_next_track()


def stop_music():
    global _music_chan
    try:
        if _music_chan:
            _music_chan.stop()
            _music_chan = None
    except Exception:
        pass


def set_enabled(value):
    global _enabled
    _enabled = bool(value)
    if _enabled:
        start_music()
    else:
        stop_music()


def set_volume(v):
    global _volume
    _volume = max(0.0, min(1.0, v))
    try:
        if _music_chan:
            _music_chan.set_volume(_volume * 0.5)
    except Exception:
        pass

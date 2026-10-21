# -*- coding: utf-8 -*-
"""
DraveDungeon - spraak (TTS) via neuvoice.

Per rol (held/Kira/vijand/verteller) een eigen stem, volume, snelheid en
toonhoogte. neuvoice draait on-device (ONNX) en downloadt zijn model zelf.
Spraak draait in een achtergrond-thread. Status is opvraagbaar voor het
instellingenscherm.
"""
import os
import sys
import copy
import queue
import tempfile
import threading
import importlib.util
import subprocess

VOICE_NAMES = ["Leon", "Cole", "Mustafa", "Sarp", "Giray", "Cem",
               "Lina", "Linda", "Selin", "Sema", "Alina", "Soras"]

ROLES = ["hero", "kira", "enemy", "narrator"]

DEFAULTS = {
    "hero":     dict(voice="Leon",    volume=0.9,  speed=1.05, pitch=1.0),
    "kira":     dict(voice="Lina",    volume=0.95, speed=1.10, pitch=1.18),
    "enemy":    dict(voice="Mustafa", volume=0.9,  speed=0.95, pitch=0.88),
    "narrator": dict(voice="Cole",    volume=0.9,  speed=1.0,  pitch=1.0),
}

_roles = copy.deepcopy(DEFAULTS)
_status = "uit"            # uit|laden|klaar|mislukt|niet_geinstalleerd|installeren
_engine = None
_worker = None
_jobs = None
_enabled = False


# ---------------------------------------------------------------- info
def is_installed():
    try:
        return importlib.util.find_spec("neuvoice") is not None
    except Exception:
        return False


def is_frozen():
    return getattr(sys, "frozen", False)


def is_enabled():
    return _enabled


def status():
    return _status


def status_text(lang="nl"):
    nl = {"uit": "Stem staat uit",
          "laden": "Stemmodel laden / downloaden... (kan even duren)",
          "klaar": "Stem is klaar",
          "mislukt": "Stem mislukt - kon model niet laden",
          "niet_geinstalleerd": "neuvoice is niet geinstalleerd",
          "installeren": "neuvoice wordt geinstalleerd..."}
    en = {"uit": "Voice is off",
          "laden": "Loading / downloading voice model... (may take a while)",
          "klaar": "Voice is ready",
          "mislukt": "Voice failed - could not load model",
          "niet_geinstalleerd": "neuvoice is not installed",
          "installeren": "installing neuvoice..."}
    return (nl if lang == "nl" else en).get(_status, _status)


def voices():
    return list(VOICE_NAMES)


# ---------------------------------------------------------------- per-rol instellingen
def _r(role):
    return _roles.get(role, _roles["hero"])


def get_voice(role):
    return _r(role)["voice"]


def set_voice(role, name):
    if name in VOICE_NAMES:
        _r(role)["voice"] = name


def voice_for(role):
    return _r(role)["voice"]


def get_volume(role):
    return _r(role)["volume"]


def set_volume(role, v):
    _r(role)["volume"] = max(0.0, min(1.0, v))


def get_speed(role):
    return _r(role)["speed"]


def set_speed(role, v):
    _r(role)["speed"] = max(0.7, min(2.0, v))


def get_pitch(role):
    return _r(role)["pitch"]


def set_pitch(role, v):
    _r(role)["pitch"] = max(0.75, min(1.4, v))


def role_cfg(role):
    return dict(_r(role))


def all_cfg():
    return copy.deepcopy(_roles)


# ---------------------------------------------------------------- engine
def _set_status(s):
    global _status
    _status = s


def _ensure_engine():
    global _engine
    if _engine is not None:
        return True
    if not is_installed():
        _set_status("niet_geinstalleerd")
        return False
    try:
        _set_status("laden")
        from neuvoice import TTS
        _engine = TTS(auto_download=True)
        _set_status("klaar")
        return True
    except Exception:
        _engine = None
        _set_status("mislukt")
        return False


def _shift_pitch(wav, pitch):
    """Verschuift de toonhoogte door te herbemonsteren (tempo is al gecompenseerd)."""
    try:
        import numpy as np
        data = np.asarray(wav, dtype="float32").reshape(-1)
        n = len(data)
        new_len = max(1, int(n / pitch))
        xs = np.linspace(0, n - 1, new_len)
        out = np.interp(xs, np.arange(n), data).astype("float32")
        return out.reshape(1, -1)
    except Exception:
        return wav


def _play_wav(path, volume):
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        snd = pygame.mixer.Sound(path)
        snd.set_volume(volume)
        ch = snd.play()
        ms = int(snd.get_length() * 1000)
        waited = 0
        while ch and ch.get_busy() and waited < min(ms + 200, 15000):
            pygame.time.wait(50); waited += 50
    except Exception:
        pass
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def _run():
    while True:
        job = _jobs.get()
        try:
            if job is None:
                return
            kind = job[0]
            if kind == "load":
                _ensure_engine()
            elif kind == "speak":
                _, text, voice, lang, on_done, volume, speed, pitch = job
                try:
                    if _ensure_engine():
                        style = _engine.get_voice_style(voice)
                        eff = max(0.7, min(2.0, speed / pitch))
                        wav, _dur = _engine.synthesize(text, voice_style=style,
                                                       lang=lang, speed=eff)
                        if abs(pitch - 1.0) > 0.01:
                            wav = _shift_pitch(wav, pitch)
                        fd, path = tempfile.mkstemp(suffix=".wav")
                        os.close(fd)
                        _engine.save_audio(wav, path)
                        _play_wav(path, volume)
                finally:
                    if on_done:
                        try:
                            on_done()
                        except Exception:
                            pass
        finally:
            _jobs.task_done()


def _ensure_worker():
    global _worker, _jobs
    if _worker is None:
        _jobs = queue.Queue()
        _worker = threading.Thread(target=_run, daemon=True)
        _worker.start()


# ---------------------------------------------------------------- publieke API
def start(enabled=True, roles_cfg=None):
    global _enabled
    _enabled = bool(enabled)
    if roles_cfg:
        for role, cfg in roles_cfg.items():
            if role in _roles and isinstance(cfg, dict):
                r = _roles[role]
                if cfg.get("voice") in VOICE_NAMES:
                    r["voice"] = cfg["voice"]
                if "volume" in cfg:
                    r["volume"] = max(0.0, min(1.0, float(cfg["volume"])))
                if "speed" in cfg:
                    r["speed"] = max(0.7, min(2.0, float(cfg["speed"])))
                if "pitch" in cfg:
                    r["pitch"] = max(0.75, min(1.4, float(cfg["pitch"])))
    _ensure_worker()
    if not is_installed():
        _set_status("niet_geinstalleerd")
    elif _enabled:
        preload()
    else:
        _set_status("uit")


def set_enabled(value):
    global _enabled
    _enabled = bool(value)
    if _enabled:
        _ensure_worker()
        if not is_installed():
            _set_status("niet_geinstalleerd")
        else:
            preload()
    else:
        _set_status("uit" if is_installed() else "niet_geinstalleerd")


def preload():
    if not is_installed():
        _set_status("niet_geinstalleerd")
        return
    _ensure_worker()
    _set_status("laden")
    try:
        _jobs.put(("load",))
    except Exception:
        pass


def _enqueue_role(text, role, lang, on_done):
    _ensure_worker()
    c = _r(role)
    try:
        _jobs.put(("speak", text, c["voice"], lang, on_done,
                   c["volume"], c["speed"], c["pitch"]))
    except Exception:
        if on_done:
            on_done()


def speak(text, role="hero", lang="nl", on_done=None):
    if not _enabled or not text:
        if on_done:
            on_done()
        return
    _enqueue_role(text, role, lang, on_done)


def say(text, role="narrator", lang="nl", on_done=None):
    """Spreekt uit, ongeacht of de stem in het spel aan staat."""
    _enqueue_role(text, role, lang, on_done)


def test(role="hero", lang="nl"):
    samples = {
        "hero": ("Ik ben er klaar voor!", "I am ready!"),
        "kira": ("Waf! Waf!", "Woof! Woof!"),
        "enemy": ("Jullie zijn verloren!", "You are doomed!"),
        "narrator": ("Welkom in DraveDungeon!", "Welcome to DraveDungeon!"),
    }
    nl, en = samples.get(role, samples["hero"])
    _enqueue_role(nl if lang == "nl" else en, role, lang, None)


def install():
    if is_frozen() or _status == "installeren":
        return
    _set_status("installeren")

    def run():
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "neuvoice"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        finally:
            _set_status("uit" if is_installed() else "niet_geinstalleerd")

    threading.Thread(target=run, daemon=True).start()


def stop():
    try:
        if _worker is not None:
            _jobs.put(None)
    except Exception:
        pass

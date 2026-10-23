# -*- coding: utf-8 -*-
# Panda3D-eigen manier om een EXE te bouwen (build_apps).
# Bouwen:  python setup.py build_apps  ->  build\win_amd64\DraveJump.exe
from setuptools import setup

setup(
    name="DraveJump",
    version="1.0",
    options={
        "build_apps": {
            "gui_apps": {"DraveJump": "main.py"},
            "include_patterns": [
                "assets/*.ico",
                "assets/*.png",
            ],
            "icons": {"DraveJump": ["assets/icon-256.png", "assets/icon-64.png"]},
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            "platforms": ["win_amd64"],
        }
    },
)

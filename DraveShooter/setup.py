# -*- coding: utf-8 -*-
# Panda3D build_apps:  python setup.py build_apps -> build\win_amd64\DraveShooter.exe
from setuptools import setup

setup(
    name="DraveShooter",
    version="1.0",
    options={
        "build_apps": {
            "gui_apps": {"DraveShooter": "main.py"},
            "include_patterns": ["assets/*.ico", "assets/*.png"],
            "icons": {"DraveShooter": ["assets/icon-256.png", "assets/icon-64.png"]},
            "plugins": ["pandagl", "p3openal_audio"],
            "platforms": ["win_amd64"],
        }
    },
)

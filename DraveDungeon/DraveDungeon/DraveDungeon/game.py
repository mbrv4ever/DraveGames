# -*- coding: utf-8 -*-
"""
DraveDungeon - een retro D&D-achtig RPG (Dravenlock).
Visueel turn-based gevecht, klassekeuze, Kira als metgezel, tekstballonnen + TTS.
Nederlands met OS-taaldetectie en Engelse vertaling.
"""
import os
import sys
import json
import math
import random
import locale

import pygame

import tts
import sfx

APP_NAME = "DraveDungeon"
APP_VERSION = "0.15.1"
DONATE_URL = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

WIDTH, HEIGHT = 1000, 640
FPS = 60

# ---------------------------------------------------------------- palet (donker, hoog contrast)
BG       = (14, 14, 17)
PANEL    = (22, 22, 27)
PANEL2   = (28, 28, 34)
LINE     = (44, 44, 52)
TEXT     = (224, 224, 228)
MUTED    = (140, 140, 150)
ACCENT   = (111, 163, 214)
GOLD     = (212, 175, 90)
GOOD     = (127, 176, 105)
WARN     = (214, 138, 111)
RED      = (200, 70, 70)
PURPLE   = (150, 110, 200)


# ---------------------------------------------------------------- config + taal
def _config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "DraveDungeon")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _config_path():
    return os.path.join(_config_dir(), "config.json")


def load_config():
    try:
        with open(_config_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception:
        pass


def _save_path():
    return os.path.join(_config_dir(), "save.json")


def write_save(data):
    try:
        with open(_save_path(), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def read_save():
    try:
        with open(_save_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def delete_save():
    try:
        os.remove(_save_path())
    except Exception:
        pass


def has_save():
    return read_save() is not None


def detect_lang():
    try:
        loc = (pygame.system and "") or ""
    except Exception:
        loc = ""
    try:
        code = (locale.getdefaultlocale()[0] or "").lower()
        if code.startswith("nl"):
            return "nl"
        if code.startswith("en"):
            return "en"
    except Exception:
        pass
    return "nl"  # Dravenlock-basistaal


LANG = "nl"

# Vertalingen: bronstring is Nederlands; EN-woordenboek vertaalt.
EN = {
    "DraveDungeon": "DraveDungeon",
    "Een retro kerkertocht": "A retro dungeon crawl",
    "Nieuw spel": "New game",
    "Taal": "Language", "Nederlands": "Dutch", "Engels": "English",
    "Stem aan": "Voice on", "Stem uit": "Voice off",
    "Afsluiten": "Quit", "Druk op een toets": "Press any key",
    "Kies je held": "Choose your hero", "Kies": "Choose",
    "Vorige": "Back", "Volgende": "Next", "Start": "Start",
    "Leven": "Health", "Aanval": "Attack", "Verdediging": "Defense",
    "Magie": "Magic", "Snelheid": "Speed",
    "Aanvallen": "Attack", "Vaardigheid": "Skill", "Verdedigen": "Defend",
    "Drankje": "Potion",
    "valt aan!": "attacks!", "verdedigt zich.": "defends.",
    "gebruikt": "uses", "drinkt een drankje!": "drinks a potion!",
    "bijt!": "bites!", "Voor jou, baas!": "For you, boss!",
    "Het is verslagen!": "It is defeated!", "Overwinning!": "Victory!",
    "Je bent gevallen...": "You have fallen...", "Spel voorbij": "Game over",
    "Niveau omhoog!": "Level up!", "Niveau": "Level",
    "Volgende vijand...": "Next foe...", "De baas verschijnt!": "The boss appears!",
    "Opnieuw spelen": "Play again", "Terug naar titel": "Back to title",
    "Geen drankjes meer!": "No potions left!", "Drankjes": "Potions",
    "Ervaring": "Experience", "Donatie": "Donate",
    "Instellingen": "Settings", "Stem": "Voice", "aan": "on", "uit": "off",
    "Volume": "Volume", "Snelheid": "Speed", "Stem (held)": "Voice (hero)",
    "Test stem": "Test voice", "Stem installeren": "Install voice",
    "Stem (Kira)": "Voice (Kira)", "Stem (vijand)": "Voice (enemy)",
    "Terug": "Back", "Status": "Status",
    "Geef je held een naam": "Name your hero", "Naam": "Name",
    "Begin avontuur": "Begin adventure", "Typ een naam en druk op Enter":
        "Type a name and press Enter",
    "Verder": "Continue", "Het avontuur begint": "The adventure begins",
    "Even geduld, het spel start": "Please wait, the game is starting",
    "De stemmen draaien op je eigen pc (neuvoice). De eerste keer wordt het":
        "Voices run on your own PC (neuvoice). The first time the model is",
    "stemmodel gedownload; dat kan een paar minuten duren.":
        "downloaded; that may take a few minutes.",
    "Krijger": "Warrior", "Magier": "Mage", "Schurk": "Rogue",
    "Boogschutter": "Archer", "Paladijn": "Paladin", "Barbaar": "Barbarian",
    "Druide": "Druid", "Bard": "Bard",
    "Stevige vechter met veel leven en een zwaard.":
        "Sturdy fighter with lots of health and a sword.",
    "Zwak maar machtige spreuken die hard raken.":
        "Frail but mighty spells that hit hard.",
    "Snel en gemeen; steekt toe en ontwijkt.":
        "Fast and sneaky; stabs and dodges.",
    "Raakt vijanden van afstand met pijlen.":
        "Strikes foes from afar with arrows.",
    "Heilige ridder die zichzelf kan genezen.":
        "Holy knight who can heal himself.",
    "Woeste krijger die in razernij extra hard slaat.":
        "Wild warrior who rages for extra damage.",
    "Natuurmagier met giftige en helende krachten.":
        "Nature mage with poison and healing powers.",
    "Bemoedigt met liederen en verzwakt de vijand.":
        "Inspires with songs and weakens the foe.",
    "Machtige slag": "Mighty blow", "Vuurbal": "Fireball",
    "Sluipsteek": "Backstab", "Gerichte pijl": "Aimed arrow",
    "Heilig licht": "Holy light", "Razernij": "Rage",
    "Gifstoot": "Poison strike", "Strijdlied": "Battle song",
    "Wervelwind": "Whirlwind", "Strijdkreet": "War cry", "Doodsklap": "Death blow",
    "Vlammenzee": "Sea of flames", "IJslans": "Ice lance", "Meteoor": "Meteor",
    "Mesregen": "Knife rain", "Gifdolk": "Poison dagger", "Schaduwdans": "Shadow dance",
    "Pijlenregen": "Arrow rain", "Doorborende pijl": "Piercing arrow",
    "Stormschot": "Storm shot", "Wijding": "Consecration", "Hemelse slag": "Heavenly strike",
    "Goddelijke gloed": "Divine glow", "Aardbeving": "Earthquake",
    "Bloeddorst": "Bloodthirst", "Slachting": "Slaughter", "Doornenrank": "Thorn vine",
    "Genezing": "Healing", "Natuurwoede": "Nature's wrath", "Dissonant": "Dissonance",
    "Helend lied": "Healing song", "Finale": "Finale",
    "Aardsplijter": "Earthsplitter", "Vernietiging": "Annihilation",
    "Duizend sneden": "Thousand cuts", "Pijlenstorm": "Arrow storm",
    "Goddelijk oordeel": "Divine judgment", "Bloedrazernij": "Blood frenzy",
    "Oerkracht": "Primal force", "Zwanenzang": "Swan song",
    "Vuuradem!": "Fire breath!",
    "Stevige allrounder. Veel leven, betrouwbare klappen en Wervelwind tegen groepen.":
        "Sturdy all-rounder. Lots of health, reliable hits and Whirlwind against groups.",
    "Glaskanon. Enorme magie die alles raakt, maar kwetsbaar - sla snel en hard.":
        "Glass cannon. Huge magic hitting everything, but fragile - strike fast and hard.",
    "Razendsnel. Hoge schade op een doel; schakel de gevaarlijkste vijand eerst uit.":
        "Lightning fast. High single-target damage; take out the deadliest enemy first.",
    "Pijlen van afstand. Constante schade aan groepen met regen-aanvallen.":
        "Arrows from afar. Steady damage to groups with rain attacks.",
    "Taaie ridder die zichzelf geneest. Hou vol en overleef de lange gevechten.":
        "Tough knight who heals himself. Endure and outlast the long fights.",
    "Meeste leven en schade. Steelt leven met Bloedrazernij - agressief doorbeuken.":
        "Most health and damage. Steals life with Blood frenzy - push aggressively.",
    "Natuurmagie en genezing. Schade aan groepen en jezelf oplappen; flexibel.":
        "Nature magic and healing. Group damage and self-mending; flexible.",
    "Manusje-van-alles. Versterkt jezelf, magie op groepen en genezing.":
        "Jack of all trades. Buffs yourself, group magic and healing.",
    "Gids": "Guide", "Hoe te spelen": "How to play", "De klassen": "The classes",
    "Volgende": "Next", "Vorige": "Previous", "Moeilijkheid": "Difficulty",
    "Normaal": "Normal", "Zwaar": "Hard", "Helse": "Brutal",
    "Doel": "Goal", "Tips": "Tips",
    "Kritieke treffer!": "Critical hit!", "Mis!": "Miss!",
    "Dobbelsteen": "Dice roll", "Gooien...": "Rolling...",
    "Geluid": "Sound",
    "Pauze": "Paused", "Hervatten": "Resume", "Hoofdmenu": "Main menu",
    "ESC of P om te hervatten": "ESC or P to resume",
    "Het verhaal wordt verteld...": "The story is being told...",
    "Verdoofd!": "Stunned!",
    "Doorgaan": "Continue", "Eindeloze modus": "Endless mode",
    "Beste diepte": "Best depth", "Diepte bereikt": "Depth reached", "Record": "Record",
    "Status-effecten": "Status effects", "Vergif": "Poison", "Brand": "Burn",
    "Verdoving": "Stun", "Pantserbreuk": "Armor break",
    "Kies een beloning": "Choose a reward", "Buit na de overwinning": "Loot after victory",
    "ZELDZAAM": "RARE", "Kies": "Choose", "Pijltjes + Enter, of klik": "Arrows + Enter, or click",
    "Levenskracht": "Vitality", "Amulet van Kracht": "Amulet of Power",
    "Amulet van Magie": "Amulet of Magic", "Harnasplaat": "Armor Plate",
    "Snelle Laarzen": "Swift Boots", "Genezende Bron": "Healing Spring",
    "Legendarisch Wapen": "Legendary Weapon",
    "+30 max leven (en genezen)": "+30 max health (and heal)",
    "+2 drankjes": "+2 potions", "+4 aanval": "+4 attack", "+4 magie": "+4 magic",
    "+3 verdediging": "+3 defense", "+3 snelheid": "+3 speed",
    "Volledig genezen + 1 drankje": "Full heal + 1 potion",
    "Veel sterker wapen (+7 aanval)": "Much stronger weapon (+7 attack)",
    "Kies vaardigheid": "Choose skill", "Kies doel": "Choose target",
    "Held": "Hero", "Vijand": "Enemy", "Verteller": "Narrator",
    "Toonhoogte": "Pitch", "Opslaan": "Save", "Sluiten": "Close",
    "Stem instellen": "Configure voice", "Klik op een stem om in te stellen":
        "Click a voice to configure",
    "Nieuwe vaardigheid": "New skill", "Nieuw wapen": "New weapon",
    "Vijanden naderen!": "Enemies approach!", "Annuleer": "Cancel",
    "Slijm": "Slime", "Goblin": "Goblin", "Skelet": "Skeleton",
    "Vleermuis": "Bat", "Ork": "Orc", "Wolf": "Wolf",
    "Geest": "Ghost", "Draak": "Dragon",
    "Kerker": "Dungeon", "Bos": "Forest", "Crypte": "Crypt",
    "IJsgrot": "Ice cave", "Vulkaan": "Volcano", "Woestijn": "Desert",
    "Moeras": "Swamp", "Drakenhol": "Dragon lair",
    "Kira springt mee in het gevecht!": "Kira leaps into the fight!",
    "Grrr!": "Grrr!", "Waf!": "Woof!",
}


def t(s):
    if LANG == "nl":
        return s
    return EN.get(s, s)


def set_lang(code):
    global LANG
    LANG = code if code in ("nl", "en") else "nl"


# ---------------------------------------------------------------- hulpmiddelen
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def load_icon():
    p = resource_path(os.path.join("assets", "logo.png"))
    try:
        return pygame.image.load(p)
    except Exception:
        return None


_FONTS = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _FONTS:
        f = pygame.font.Font(None, size)
        f.set_bold(bold)
        _FONTS[key] = f
    return _FONTS[key]


def draw_text(surf, text, x, y, size=28, color=TEXT, center=False, bold=False, shadow=True):
    f = font(size, bold)
    # schaduw alleen bij lichte tekst; bij donkere tekst geeft het een dubbel-effect
    if shadow and sum(color[:3]) > 130:
        sh = f.render(text, True, (0, 0, 0))
        r = sh.get_rect()
        if center:
            r.center = (x + 2, y + 2)
        else:
            r.topleft = (x + 2, y + 2)
        surf.blit(sh, r)
    img = f.render(text, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(img, r)
    return r


def wrap_text(text, f, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def round_rect(surf, rect, color, radius=10, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=radius)


def lerp(a, b, f):
    return a + (b - a) * f


# ---------------------------------------------------------------- pixel-art
def px_surface(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    return s


def scale_px(surf, factor):
    return pygame.transform.scale(
        surf, (surf.get_width() * factor, surf.get_height() * factor))


def shade(color, d):
    return tuple(max(0, min(255, c + d)) for c in color[:3])


def draw_hero_sprite(colors, size=44):
    """Tekent een eenvoudige held op lage resolutie en schaalt op (retro)."""
    base = colors.get("base", (90, 100, 120))
    skin = (224, 188, 150)
    trim = colors.get("trim", shade(base, 40))
    s = px_surface(16, 20)
    # benen
    pygame.draw.rect(s, shade(base, -40), (5, 15, 2, 4))
    pygame.draw.rect(s, shade(base, -40), (9, 15, 2, 4))
    # lijf
    pygame.draw.rect(s, base, (4, 8, 8, 8))
    pygame.draw.rect(s, trim, (4, 8, 8, 2))
    # armen
    pygame.draw.rect(s, base, (3, 9, 1, 5))
    pygame.draw.rect(s, base, (12, 9, 1, 5))
    # hoofd
    pygame.draw.rect(s, skin, (6, 3, 4, 5))
    # haar/helm
    pygame.draw.rect(s, colors.get("hair", (60, 45, 35)), (5, 2, 6, 2))
    # ogen
    pygame.draw.rect(s, (20, 20, 30), (7, 5, 1, 1))
    pygame.draw.rect(s, (20, 20, 30), (9, 5, 1, 1))
    sp = scale_px(s, max(2, size // 20))
    # embleem (wapen) er los naast tekenen
    return sp


def draw_weapon(emblem, colors, size=44):
    s = px_surface(16, 20)
    c = colors.get("weapon", (200, 200, 210))
    if emblem == "sword":
        pygame.draw.rect(s, c, (13, 4, 1, 9))
        pygame.draw.rect(s, GOLD, (12, 12, 3, 1))
    elif emblem == "staff":
        pygame.draw.rect(s, (120, 90, 60), (13, 3, 1, 12))
        pygame.draw.circle(s, ACCENT, (13, 3), 2)
    elif emblem == "dagger":
        pygame.draw.rect(s, c, (13, 7, 1, 5))
    elif emblem == "bow":
        pygame.draw.arc(s, (150, 110, 70), pygame.Rect(11, 4, 5, 11), -1.2, 1.2, 1)
    elif emblem == "mace":
        pygame.draw.rect(s, (120, 90, 60), (13, 6, 1, 8))
        pygame.draw.circle(s, GOLD, (13, 5), 2)
    elif emblem == "axe":
        pygame.draw.rect(s, (120, 90, 60), (13, 4, 1, 10))
        pygame.draw.rect(s, c, (11, 4, 3, 3))
    elif emblem == "lute":
        pygame.draw.circle(s, (150, 110, 70), (13, 11), 2)
        pygame.draw.rect(s, (150, 110, 70), (13, 4, 1, 6))
    return scale_px(s, max(2, size // 20))


def draw_kira_sprite(size=40):
    """Kira: slanke bruine Podenco-teef met grote spitse oren (kijkt naar rechts)."""
    brown = (150, 96, 56)
    dark = shade(brown, -45)
    s = px_surface(20, 14)
    # lijf (slank)
    pygame.draw.rect(s, brown, (4, 6, 9, 3))
    # borst
    pygame.draw.rect(s, brown, (11, 5, 3, 4))
    # poten (lang, dun)
    for px in (5, 7, 10, 12):
        pygame.draw.rect(s, dark, (px, 9, 1, 4))
    # nek + kop
    pygame.draw.rect(s, brown, (13, 3, 2, 4))
    pygame.draw.rect(s, brown, (15, 4, 3, 3))   # snuit (spits)
    # grote spitse oren (Podenco)
    pygame.draw.polygon(s, brown, [(13, 3), (12, 0), (14, 2)])
    pygame.draw.polygon(s, brown, [(15, 3), (15, 0), (16, 2)])
    # oog + neus
    pygame.draw.rect(s, (20, 20, 20), (15, 4, 1, 1))
    pygame.draw.rect(s, (20, 20, 20), (17, 5, 1, 1))
    # staart (dun, omhoog)
    pygame.draw.line(s, dark, (4, 6), (2, 3), 1)
    return scale_px(s, max(2, size // 14))


def draw_enemy_sprite(kind, size=56):
    s = px_surface(20, 18)
    if kind == "slime":
        c = (90, 180, 120)
        pygame.draw.ellipse(s, c, (3, 8, 14, 9))
        pygame.draw.ellipse(s, shade(c, 40), (5, 9, 10, 5))
        pygame.draw.rect(s, (20, 30, 25), (7, 11, 1, 2))
        pygame.draw.rect(s, (20, 30, 25), (12, 11, 1, 2))
    elif kind == "goblin":
        c = (110, 150, 80)
        pygame.draw.rect(s, c, (6, 7, 8, 8))
        pygame.draw.rect(s, c, (7, 3, 6, 5))
        pygame.draw.polygon(s, c, [(6, 5), (3, 4), (6, 7)])
        pygame.draw.polygon(s, c, [(13, 5), (16, 4), (13, 7)])
        pygame.draw.rect(s, (200, 40, 40), (8, 5, 1, 1))
        pygame.draw.rect(s, (200, 40, 40), (11, 5, 1, 1))
    elif kind == "skeleton":
        c = (220, 220, 210)
        pygame.draw.rect(s, c, (7, 3, 5, 5))
        pygame.draw.rect(s, (20, 20, 20), (8, 5, 1, 1))
        pygame.draw.rect(s, (20, 20, 20), (10, 5, 1, 1))
        pygame.draw.rect(s, c, (8, 8, 4, 7))
        for yy in range(9, 15, 2):
            pygame.draw.rect(s, shade(c, -40), (8, yy, 4, 1))
    elif kind == "bat":
        c = (90, 70, 110)
        pygame.draw.ellipse(s, c, (8, 7, 4, 5))
        pygame.draw.polygon(s, c, [(8, 9), (2, 5), (3, 11)])
        pygame.draw.polygon(s, c, [(12, 9), (18, 5), (17, 11)])
        pygame.draw.rect(s, (220, 60, 60), (9, 8, 1, 1))
        pygame.draw.rect(s, (220, 60, 60), (11, 8, 1, 1))
    elif kind == "orc":
        c = (110, 140, 90)
        pygame.draw.rect(s, c, (5, 6, 10, 9))
        pygame.draw.rect(s, c, (7, 2, 6, 5))
        pygame.draw.rect(s, (240, 240, 230), (8, 6, 1, 2))  # slagtand
        pygame.draw.rect(s, (240, 240, 230), (11, 6, 1, 2))
        pygame.draw.rect(s, (180, 40, 40), (8, 4, 1, 1))
        pygame.draw.rect(s, (180, 40, 40), (11, 4, 1, 1))
    elif kind == "wolf":
        c = (120, 120, 130)
        pygame.draw.ellipse(s, c, (4, 7, 11, 6))
        pygame.draw.rect(s, c, (13, 5, 4, 4))
        pygame.draw.polygon(s, c, [(13, 5), (12, 2), (14, 4)])
        pygame.draw.polygon(s, c, [(15, 5), (16, 2), (16, 4)])
        pygame.draw.rect(s, (220, 200, 60), (15, 6, 1, 1))
        for px in (5, 8, 11, 13):
            pygame.draw.rect(s, shade(c, -40), (px, 12, 1, 3))
    elif kind == "ghost":
        c = (180, 200, 220)
        pygame.draw.ellipse(s, c, (5, 3, 10, 10))
        pygame.draw.rect(s, c, (5, 8, 10, 6))
        pygame.draw.rect(s, (40, 50, 70), (8, 7, 1, 2))
        pygame.draw.rect(s, (40, 50, 70), (11, 7, 1, 2))
    elif kind == "dragon":
        c = (170, 60, 60)
        pygame.draw.ellipse(s, c, (3, 7, 12, 7))
        pygame.draw.rect(s, c, (13, 4, 4, 5))      # kop
        pygame.draw.polygon(s, c, [(13, 4), (12, 1), (15, 3)])  # hoorn
        pygame.draw.polygon(s, shade(c, -50), [(3, 9), (0, 4), (5, 8)])  # vleugel
        pygame.draw.rect(s, GOLD, (15, 6, 1, 1))   # oog
        pygame.draw.polygon(s, c, [(3, 10), (0, 12), (4, 12)])  # staart
    else:
        pygame.draw.rect(s, (160, 120, 160), (5, 5, 10, 10))
    return scale_px(s, max(3, size // 18))


def make_background(theme):
    """Sfeer-achtergrond per thema, met decors."""
    bg = pygame.Surface((WIDTH, HEIGHT))
    top, bottom, floor = THEME_COLORS.get(theme, ((30, 30, 40), (16, 16, 22), (40, 34, 30)))
    for y in range(HEIGHT):
        f = y / HEIGHT
        col = tuple(int(lerp(top[i], bottom[i], f)) for i in range(3))
        pygame.draw.line(bg, col, (0, y), (WIDTH, y))
    fy = int(HEIGHT * 0.72)
    rng = random.Random(hash(theme) & 0xffff)

    def torch(x, ty):
        pygame.draw.rect(bg, (60, 45, 35), (x - 2, ty, 4, 26))
        for r, c in ((10, (200, 90, 30)), (7, (240, 150, 40)), (4, (255, 220, 120))):
            pygame.draw.circle(bg, c, (x, ty - 4), r)

    if theme == "Kerker":
        # bakstenen muur
        bh = 26
        for row, yy in enumerate(range(60, fy, bh)):
            off = (bh // 2) if row % 2 else 0
            for xx in range(-off, WIDTH, 54):
                pygame.draw.rect(bg, shade(floor, 8), (xx + 2, yy + 2, 50, bh - 4))
        torch(150, fy - 150); torch(WIDTH - 150, fy - 150)
    elif theme == "Bos":
        pygame.draw.circle(bg, (220, 225, 200), (WIDTH - 130, 90), 34)  # maan
        for _ in range(6):
            x = rng.randint(40, WIDTH - 40); th = rng.randint(120, 200)
            pygame.draw.rect(bg, (60, 45, 32), (x - 6, fy - th, 12, th))
            for k in range(3):
                pygame.draw.circle(bg, shade((40, 90, 50), k * 8),
                                   (x, fy - th + k * 26), 34 - k * 4)
    elif theme == "Crypte":
        for _ in range(5):  # vleermuizen
            x = rng.randint(80, WIDTH - 80); y = rng.randint(70, 200)
            pygame.draw.line(bg, (20, 16, 26), (x - 8, y), (x, y - 5), 2)
            pygame.draw.line(bg, (20, 16, 26), (x, y - 5), (x + 8, y), 2)
        for _ in range(5):  # kruisen op de achtergrond
            x = rng.randint(60, WIDTH - 60); h = rng.randint(40, 70); yb = fy - 6
            pygame.draw.rect(bg, shade(floor, 18), (x - 3, yb - h, 6, h))
            pygame.draw.rect(bg, shade(floor, 18), (x - 12, yb - h + 14, 24, 6))
    elif theme == "IJsgrot":
        for _ in range(14):  # ijspegels
            x = rng.randint(20, WIDTH - 20); h = rng.randint(24, 80)
            pygame.draw.polygon(bg, (190, 220, 240), [(x - 9, 0), (x + 9, 0), (x, h)])
        for _ in range(20):
            x = rng.randint(0, WIDTH); y = rng.randint(60, fy - 20)
            pygame.draw.circle(bg, (210, 235, 250), (x, y), 2)
    elif theme == "Vulkaan":
        pygame.draw.polygon(bg, (40, 22, 18),
                            [(WIDTH // 2 - 180, fy), (WIDTH // 2, fy - 230), (WIDTH // 2 + 180, fy)])
        pygame.draw.polygon(bg, (230, 110, 40),
                            [(WIDTH // 2 - 30, fy - 200), (WIDTH // 2, fy - 232), (WIDTH // 2 + 30, fy - 200)])
        for _ in range(7):
            x = rng.randint(40, WIDTH - 40); y = rng.randint(60, 220)
            pygame.draw.circle(bg, (250, 160, 60), (x, y), 2)
    elif theme == "Woestijn":
        pygame.draw.circle(bg, (250, 220, 130), (WIDTH - 160, 110), 46)  # zon
        for px in (220, 520):  # piramides
            pygame.draw.polygon(bg, shade(floor, -30),
                                [(px - 110, fy), (px, fy - 130), (px + 110, fy)])
    elif theme == "Moeras":
        for _ in range(3):  # mist
            ms = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
            ms.fill((180, 200, 180, 26))
            bg.blit(ms, (0, rng.randint(120, fy - 60)))
        x = rng.randint(120, WIDTH - 120)  # dode boom
        pygame.draw.rect(bg, (40, 38, 30), (x - 6, fy - 180, 12, 180))
        for dx, dy in ((-40, -150), (40, -160), (-20, -120)):
            pygame.draw.line(bg, (40, 38, 30), (x, fy - 150), (x + dx, fy - 150 + dy), 4)
    elif theme == "Drakenhol":
        for _ in range(8):  # stalactieten
            x = rng.randint(20, WIDTH - 20); h = rng.randint(30, 90)
            pygame.draw.polygon(bg, (40, 18, 20), [(x - 12, 0), (x + 12, 0), (x, h)])
        glow = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
        glow.fill((200, 50, 40, 40)); bg.blit(glow, (0, fy - 120))

    # vloer
    pygame.draw.rect(bg, floor, (0, fy, WIDTH, HEIGHT - fy))
    pygame.draw.line(bg, shade(floor, 25), (0, fy), (WIDTH, fy), 3)

    # vloer-decor
    if theme == "Kerker":
        for xx in range(0, WIDTH, 80):
            pygame.draw.line(bg, shade(floor, -12), (xx, fy + 6), (xx, HEIGHT), 2)
    elif theme in ("Bos", "Moeras"):
        for _ in range(8):
            x = rng.randint(0, WIDTH); y = rng.randint(fy + 10, HEIGHT - 10)
            pygame.draw.ellipse(bg, shade(floor, 16), (x, y, 30, 12))
        if theme == "Moeras":
            for _ in range(10):  # riet
                x = rng.randint(0, WIDTH); h = rng.randint(20, 46)
                pygame.draw.line(bg, (70, 90, 50), (x, fy + 14), (x, fy + 14 - h), 2)
                pygame.draw.rect(bg, (90, 60, 40), (x - 2, fy + 14 - h - 6, 4, 8))
    elif theme == "Crypte":
        for _ in range(4):  # grafstenen
            x = rng.randint(60, WIDTH - 60)
            pygame.draw.rect(bg, shade(floor, 22), (x - 16, fy + 8, 32, 40), border_radius=10)
            pygame.draw.rect(bg, shade(floor, -10), (x - 2, fy + 14, 4, 14))
            pygame.draw.rect(bg, shade(floor, -10), (x - 10, fy + 18, 20, 4))
    elif theme == "IJsgrot":
        for _ in range(6):
            x = rng.randint(0, WIDTH)
            pygame.draw.ellipse(bg, (220, 240, 250), (x, fy + 6, 60, 16))
    elif theme == "Vulkaan":
        for _ in range(10):  # lava-scheuren
            x = rng.randint(0, WIDTH); y = rng.randint(fy + 10, HEIGHT - 6)
            pygame.draw.line(bg, (230, 110, 40), (x, y), (x + rng.randint(20, 60), y + rng.randint(-6, 6)), 2)
    elif theme == "Woestijn":
        for _ in range(3):
            x = rng.randint(40, WIDTH - 40)  # cactus
            pygame.draw.rect(bg, (60, 110, 60), (x - 4, fy + 4, 8, 30))
            pygame.draw.rect(bg, (60, 110, 60), (x - 4, fy + 10, -10, 6))
    elif theme == "Drakenhol":
        for _ in range(5):  # schat + botten
            x = rng.randint(40, WIDTH - 40)
            for _ in range(6):
                pygame.draw.circle(bg, (220, 180, 70),
                                   (x + rng.randint(-14, 14), HEIGHT - rng.randint(10, 30)), 3)
    return bg


def make_particles(theme):
    kind = {"Vulkaan": "ember", "Drakenhol": "ember", "IJsgrot": "snow",
            "Bos": "firefly", "Moeras": "firefly", "Woestijn": "dust"}.get(theme, "mote")
    n = {"ember": 34, "snow": 60, "firefly": 22, "dust": 28, "mote": 18}[kind]
    rng = random.Random()
    ps = []
    for _ in range(n):
        ps.append(dict(x=rng.uniform(0, WIDTH), y=rng.uniform(0, HEIGHT * 0.72),
                       ph=rng.uniform(0, 6.28), sp=rng.uniform(0.5, 1.6)))
    return ps, kind


def update_particles(particles, kind, t, dt):
    fy = HEIGHT * 0.72
    for p in particles:
        if kind == "ember":
            p["y"] -= 24 * p["sp"] * dt
            p["x"] += math.sin(t + p["ph"]) * 10 * dt
            if p["y"] < 0:
                p["y"] = fy; p["x"] = random.uniform(0, WIDTH)
        elif kind == "snow":
            p["y"] += 42 * p["sp"] * dt
            p["x"] += math.sin(t * p["sp"] + p["ph"]) * 12 * dt
            if p["y"] > fy:
                p["y"] = 0; p["x"] = random.uniform(0, WIDTH)
        elif kind == "firefly":
            p["x"] += math.cos(t * p["sp"] + p["ph"]) * 16 * dt
            p["y"] += math.sin(t * p["sp"] * 0.8 + p["ph"]) * 10 * dt
            p["x"] %= WIDTH; p["y"] = max(40, min(fy, p["y"]))
        elif kind == "dust":
            p["x"] += 34 * p["sp"] * dt
            if p["x"] > WIDTH:
                p["x"] = 0; p["y"] = random.uniform(60, fy)
        else:  # mote
            p["y"] += 8 * p["sp"] * dt
            if p["y"] > fy:
                p["y"] = 0


def draw_particles(surf, particles, kind, t):
    base = {"ember": (250, 150, 60), "snow": (230, 240, 255),
            "firefly": (200, 230, 120), "dust": (200, 180, 135), "mote": (170, 170, 185)}[kind]
    for p in particles:
        tw = (math.sin(t * 2 + p["ph"]) + 1) * 0.5  # 0..1
        if kind == "firefly" and tw < 0.35:
            continue
        if kind in ("dust", "mote"):
            col = base
            r = 2
        else:
            f = 0.5 + 0.5 * tw
            col = tuple(int(c * f) for c in base)
            r = 3 if kind == "ember" else 2
        pygame.draw.circle(surf, col, (int(p["x"]), int(p["y"])), r)


THEME_COLORS = {
    "Kerker":   ((40, 38, 50), (14, 13, 18), (46, 40, 34)),
    "Bos":      ((30, 60, 40), (12, 22, 16), (40, 50, 30)),
    "Crypte":   ((40, 30, 50), (12, 10, 16), (34, 30, 38)),
    "IJsgrot":  ((90, 130, 160), (20, 34, 50), (120, 150, 175)),
    "Vulkaan":  ((90, 40, 30), (24, 10, 8), (60, 30, 24)),
    "Woestijn": ((180, 150, 90), (90, 70, 40), (170, 140, 90)),
    "Moeras":   ((50, 60, 40), (16, 22, 14), (40, 44, 30)),
    "Drakenhol":((70, 30, 36), (18, 8, 10), (50, 24, 24)),
}

THEMES = list(THEME_COLORS.keys())


# ---------------------------------------------------------------- spel-data
# klassen: hp, atk, def, mag, spd, skill(naam, kosten, soort, kracht), wapen, kleuren
CLASSES = [
    dict(key="krijger", name="Krijger", desc="Stevige vechter met veel leven en een zwaard.",
         hp=120, atk=18, dfn=10, mag=2, spd=8, weapon="sword",
         skill=("Machtige slag", "dmg", 1.8),
         skills=[("Machtige slag", "dmg", 1.8, 1), ("Wervelwind", "aoe", 1.1, 3),
                 ("Strijdkreet", "buff", 1.7, 5), ("Doodsklap", "dmg", 2.8, 7, "pantserbreuk"), ("Aardsplijter", "aoe", 2.7, 10)],
         colors=dict(base=(90, 100, 120), trim=(150, 150, 165), hair=(70, 50, 40), weapon=(210, 210, 220))),
    dict(key="magier", name="Magier", desc="Zwak maar machtige spreuken die hard raken.",
         hp=80, atk=8, dfn=5, mag=22, spd=9, weapon="staff",
         skill=("Vuurbal", "mdmg", 2.1),
         skills=[("Vuurbal", "mdmg", 2.1, 1), ("Vlammenzee", "maoe", 1.4, 3, "brand"),
                 ("IJslans", "mdmg", 2.7, 5), ("Meteoor", "maoe", 2.1, 7), ("Vernietiging", "maoe", 2.9, 10)],
         colors=dict(base=(70, 60, 130), trim=(150, 120, 210), hair=(40, 30, 30), weapon=(120, 90, 60))),
    dict(key="schurk", name="Schurk", desc="Snel en gemeen; steekt toe en ontwijkt.",
         hp=95, atk=15, dfn=7, mag=4, spd=15, weapon="dagger",
         skill=("Sluipsteek", "dmg", 2.2),
         skills=[("Sluipsteek", "dmg", 2.2, 1), ("Mesregen", "aoe", 1.2, 3),
                 ("Gifdolk", "lifesteal", 2.2, 5, "vergif"), ("Schaduwdans", "dmg", 3.1, 7), ("Duizend sneden", "aoe", 2.5, 10)],
         colors=dict(base=(50, 60, 60), trim=(90, 110, 110), hair=(30, 25, 20), weapon=(200, 200, 210))),
    dict(key="boog", name="Boogschutter", desc="Raakt vijanden van afstand met pijlen.",
         hp=95, atk=16, dfn=6, mag=5, spd=13, weapon="bow",
         skill=("Gerichte pijl", "dmg", 2.0),
         skills=[("Gerichte pijl", "dmg", 2.0, 1), ("Pijlenregen", "aoe", 1.3, 3),
                 ("Doorborende pijl", "dmg", 2.7, 5, "pantserbreuk"), ("Stormschot", "aoe", 1.9, 7), ("Pijlenstorm", "aoe", 2.5, 10)],
         colors=dict(base=(70, 100, 70), trim=(120, 160, 110), hair=(60, 45, 30), weapon=(150, 110, 70))),
    dict(key="paladijn", name="Paladijn", desc="Heilige ridder die zichzelf kan genezen.",
         hp=115, atk=15, dfn=12, mag=10, spd=7, weapon="mace",
         skill=("Heilig licht", "heal", 0.5),
         skills=[("Heilig licht", "heal", 0.5, 1), ("Wijding", "maoe", 1.2, 3),
                 ("Hemelse slag", "dmg", 2.5, 5, "verdoving"), ("Goddelijke gloed", "heal", 0.9, 7), ("Goddelijk oordeel", "maoe", 2.7, 10)],
         colors=dict(base=(180, 170, 110), trim=(230, 220, 160), hair=(80, 60, 40), weapon=(120, 90, 60))),
    dict(key="barbaar", name="Barbaar", desc="Woeste krijger die in razernij extra hard slaat.",
         hp=130, atk=20, dfn=7, mag=1, spd=9, weapon="axe",
         skill=("Razernij", "buff", 1.6),
         skills=[("Razernij", "buff", 1.7, 1), ("Aardbeving", "aoe", 1.3, 3),
                 ("Bloeddorst", "lifesteal", 2.2, 5), ("Slachting", "aoe", 2.1, 7, "pantserbreuk"), ("Bloedrazernij", "lifesteal", 3.3, 10)],
         colors=dict(base=(140, 80, 60), trim=(180, 110, 80), hair=(50, 35, 25), weapon=(190, 190, 200))),
    dict(key="druide", name="Druide", desc="Natuurmagier met giftige en helende krachten.",
         hp=90, atk=10, dfn=7, mag=18, spd=10, weapon="staff",
         skill=("Gifstoot", "mdmg", 1.7),
         skills=[("Gifstoot", "mdmg", 1.8, 1), ("Doornenrank", "maoe", 1.2, 3, "vergif"),
                 ("Genezing", "heal", 0.6, 5), ("Natuurwoede", "maoe", 2.1, 7), ("Oerkracht", "maoe", 2.8, 10)],
         colors=dict(base=(70, 110, 80), trim=(120, 170, 120), hair=(60, 70, 40), weapon=(90, 110, 60))),
    dict(key="bard", name="Bard", desc="Bemoedigt met liederen en verzwakt de vijand.",
         hp=100, atk=12, dfn=8, mag=14, spd=12, weapon="lute",
         skill=("Strijdlied", "buff", 1.5),
         skills=[("Strijdlied", "buff", 1.5, 1), ("Dissonant", "maoe", 1.1, 3, "verdoving"),
                 ("Helend lied", "heal", 0.6, 5), ("Finale", "maoe", 2.0, 7), ("Zwanenzang", "maoe", 2.7, 10)],
         colors=dict(base=(130, 80, 140), trim=(180, 130, 200), hair=(70, 40, 60), weapon=(150, 110, 70))),
]

CLASS_TIPS = {
    "krijger": "Stevige allrounder. Veel leven, betrouwbare klappen en Wervelwind tegen groepen.",
    "magier": "Glaskanon. Enorme magie die alles raakt, maar kwetsbaar - sla snel en hard.",
    "schurk": "Razendsnel. Hoge schade op een doel; schakel de gevaarlijkste vijand eerst uit.",
    "boog": "Pijlen van afstand. Constante schade aan groepen met regen-aanvallen.",
    "paladijn": "Taaie ridder die zichzelf geneest. Hou vol en overleef de lange gevechten.",
    "barbaar": "Meeste leven en schade. Steelt leven met Bloedrazernij - agressief doorbeuken.",
    "druide": "Natuurmagie en genezing. Schade aan groepen en jezelf oplappen; flexibel.",
    "bard": "Manusje-van-alles. Versterkt jezelf, magie op groepen en genezing.",
}

ENEMY_DEFS = {
    "Slijm":     dict(hp=55, atk=10, dfn=3, spd=5, kind="slime", status="vergif"),
    "Goblin":    dict(hp=60, atk=13, dfn=5, spd=11, kind="goblin"),
    "Skelet":    dict(hp=70, atk=14, dfn=8, spd=8, kind="skeleton"),
    "Vleermuis": dict(hp=45, atk=12, dfn=3, spd=16, kind="bat"),
    "Ork":       dict(hp=95, atk=18, dfn=9, spd=7, kind="orc"),
    "Wolf":      dict(hp=70, atk=16, dfn=5, spd=14, kind="wolf"),
    "Geest":     dict(hp=80, atk=15, dfn=10, spd=12, kind="ghost", status="verdoving"),
    "Draak":     dict(hp=170, atk=18, dfn=12, spd=10, kind="dragon"),  # baas
}

# welke vijanden horen bij welk thema
THEME_ENEMIES = {
    "Kerker":   ["Slijm", "Goblin", "Skelet"],
    "Bos":      ["Wolf", "Goblin", "Slijm"],
    "Crypte":   ["Skelet", "Geest", "Vleermuis"],
    "IJsgrot":  ["Wolf", "Geest", "Skelet"],
    "Vulkaan":  ["Ork", "Vleermuis", "Slijm"],
    "Woestijn": ["Ork", "Wolf", "Skelet"],
    "Moeras":   ["Slijm", "Geest", "Vleermuis"],
    "Drakenhol": ["Ork", "Geest"],
}


# welkomst-/introverhaaltjes (willekeurig); {name} = heldennaam
INTRO_STORIES = [
    ("Welkom, dappere {name}. Voor je ligt een duistere kerker vol monsters. "
     "Alleen de moedigsten bereiken de draak. Trek je zwaard en ga voorwaarts!",
     "Welcome, brave {name}. Before you lies a dark dungeon full of monsters. "
     "Only the bravest reach the dragon. Draw your sword and march onward!"),
    ("Reiziger {name}, het dorp rekent op je. Diep in de grotten huist een oude draak. "
     "Versla alles wat je tegenkomt en maak een einde aan zijn schrikbewind.",
     "Traveler {name}, the village is counting on you. Deep in the caves dwells an "
     "ancient dragon. Defeat all you meet and end its reign of terror."),
    ("De poorten openen zich, {name}. Met Kira trouw aan je zijde betreed je het "
     "onbekende. Vele beproevingen scheiden je van de draak. Succes, held.",
     "The gates open, {name}. With loyal Kira at your side you step into the unknown. "
     "Many trials stand between you and the dragon. Good luck, hero."),
    ("Het is donker en koud, {name}. Toortsen flikkeren aan de muren. Iets groots "
     "beweegt in de diepte. Jij en Kira zijn de laatste hoop. Wees dapper!",
     "It is dark and cold, {name}. Torches flicker on the walls. Something huge stirs "
     "in the depths. You and Kira are the last hope. Be brave!"),
    ("Lang geleden viel een draak het land binnen, {name}. Niemand keerde terug uit "
     "zijn hol. Vandaag verander jij dat verhaal. Het avontuur begint nu!",
     "Long ago a dragon invaded the land, {name}. None returned from its lair. "
     "Today you change that tale. The adventure begins now!"),
]


def intro_story(name):
    nl, en = random.choice(INTRO_STORIES)
    return (nl if LANG == "nl" else en).format(name=name)


# ---------------------------------------------------------------- personages
class Entity:
    def __init__(self, name, key, max_hp, atk, dfn, mag, spd, is_player,
                 sprite, weapon=None, level=1):
        self.name = name
        self.key = key
        self.max_hp = max_hp
        self.hp = max_hp
        self.atk = atk
        self.dfn = dfn
        self.mag = mag
        self.spd = spd
        self.is_player = is_player
        self.sprite = sprite
        self.weapon = weapon
        self.level = level
        self.alive = True
        self.defending = False
        self.buff = 1.0
        self.x = 0
        self.y = 0
        self.anim_off = 0.0      # voorwaartse uitval bij aanval
        self.flash = 0.0         # rood oplichten bij rake klap
        self.shake = 0.0
        self.hp_shown = float(max_hp)  # vloeiend zakkende balk
        self.statuses = {}             # naam -> resterende beurten

    def add_status(self, name, turns):
        self.statuses[name] = max(self.statuses.get(name, 0), turns)

    def has_status(self, name):
        return self.statuses.get(name, 0) > 0

    def eff_dfn(self):
        return self.dfn * (0.5 if self.has_status("pantserbreuk") else 1.0)

    def take_damage(self, dmg):
        dmg = max(1, int(dmg))
        if self.defending:
            dmg = max(1, dmg // 2)
        self.hp = max(0, self.hp - dmg)
        self.flash = 0.35
        self.shake = 0.3
        if self.hp <= 0:
            self.alive = False
        return dmg

    def heal(self, amount):
        amount = int(amount)
        self.hp = min(self.max_hp, self.hp + amount)
        return amount


def make_hero(cls, level=1):
    sp = draw_hero_sprite(cls["colors"], 120)
    wp = draw_weapon(cls["weapon"], cls["colors"], 120)
    e = Entity(t(cls["name"]), cls["key"], cls["hp"], cls["atk"], cls["dfn"],
               cls["mag"], cls["spd"], True, sp, wp, level)
    e.cls = cls
    e.weapon_tier = 0
    return e


def unlocked_skills(cls, level):
    """Vaardigheden die op dit niveau vrijgespeeld zijn (naam, soort, kracht, status)."""
    out = []
    for sk in cls.get("skills", []):
        name, typ, power, lvl = sk[0], sk[1], sk[2], sk[3]
        status = sk[4] if len(sk) > 4 else None
        if level >= lvl:
            out.append((name, typ, power, status))
    return out


# status-effecten: kleur, label, en hoe ze werken
STATUS_INFO = {
    "vergif":       dict(color=(120, 200, 90), short="GIF", turns=3),
    "brand":        dict(color=(230, 130, 70), short="BRD", turns=2),
    "verdoving":    dict(color=(170, 130, 220), short="STUN", turns=1),
    "pantserbreuk": dict(color=(110, 170, 220), short="DEF-", turns=3),
}


def upgrade_weapon(hero):
    """Sterker, glanzender wapen bij hogere tier."""
    hero.weapon_tier += 1
    cols = dict(hero.cls["colors"])
    # wapen wordt goudkleuriger/lichter per tier
    base = cols.get("weapon", (200, 200, 210))
    cols["weapon"] = tuple(min(255, c + 18 * hero.weapon_tier) for c in
                           (max(base[0], 180), max(base[1], 150), max(base[2], 70)))
    hero.weapon = draw_weapon(hero.cls["weapon"], cols, 120)


def make_kira(level=1):
    sp = draw_kira_sprite(90)
    e = Entity("Kira", "kira", 60, 12, 6, 0, 14, True, sp, level=level)
    return e


DIFF_LIN = 0.12      # lineaire groei per niveau (de reis)
DIFF_QUAD = 0.0      # versnelling (uit; finale-zwaarte zit in de draak)
DRAGON_HP = 2.5      # draak-baas: hoeveel taaier
DRAGON_ATK = 1.4     # draak-baas: hoeveel harder

DIFFICULTY = "zwaar"
DIFF_SCALE = {"normaal": 0.60, "zwaar": 1.0, "helse": 1.18}
DIFF_STATUS = {"normaal": 0.22, "zwaar": 0.38, "helse": 0.5}


def diff_factor():
    return DIFF_SCALE.get(DIFFICULTY, 1.0)


def diff_status_chance():
    return DIFF_STATUS.get(DIFFICULTY, 0.38)


def enemy_boost(level):
    d = level - 1
    return 1.0 + d * DIFF_LIN + (d * d) * DIFF_QUAD


def make_enemy(name, level=1, elite=False):
    d = ENEMY_DEFS[name]
    f = diff_factor()
    boost = enemy_boost(level)
    hp = int(d["hp"] * boost * f)
    atk = int(d["atk"] * boost * f)
    if name == "Draak":                 # baas: extra taai en hard
        hp = int(hp * DRAGON_HP)
        atk = int(atk * DRAGON_ATK)
    big = 130 if name != "Draak" else 210
    if elite:                           # mini-baas: taaier, harder, groter
        hp = int(hp * 1.55)
        atk = int(atk * 1.3)
        big = int(big * 1.25)
    sp = draw_enemy_sprite(d["kind"], big)
    sp = pygame.transform.flip(sp, True, False)  # naar de helden toe gericht
    disp = (("Elite " if LANG == "nl" else "Elite ") + t(name)) if elite else t(name)
    e = Entity(disp, name, hp, atk,
               int(d["dfn"] * (1 + (level - 1) * 0.05)), 0, d.get("spd", 8), False, sp, level=level)
    e.elite = elite
    if elite:                           # mini-baas krijgt altijd zijn truc-status
        e.elite_status = d.get("status") or random.choice(["pantserbreuk", "verdoving"])
    return e


def draw_hp_bar_small(surf, ent, x, y, w=170):
    h = 13
    round_rect(surf, (x, y, w, h), (20, 20, 24), 5)
    frac = max(0.0, ent.hp_shown / ent.max_hp)
    col = GOOD if frac > 0.5 else (GOLD if frac > 0.25 else RED)
    if frac > 0:
        round_rect(surf, (x, y, int(w * frac), h), col, 5)
    round_rect(surf, (x, y, w, h), LINE, 5, 2)
    draw_text(surf, f"{ent.name} Lv{ent.level}", x, y - 19, 21, TEXT, bold=True)


# ---------------------------------------------------------------- UI-onderdelen
def draw_hp_bar(surf, ent, x, y, w=190):
    h = 16
    round_rect(surf, (x, y, w, h), (20, 20, 24), 6)
    frac = max(0.0, ent.hp_shown / ent.max_hp)
    col = GOOD if frac > 0.5 else (GOLD if frac > 0.25 else RED)
    if frac > 0:
        round_rect(surf, (x, y, int(w * frac), h), col, 6)
    round_rect(surf, (x, y, w, h), LINE, 6, 2)
    draw_text(surf, f"{ent.name}  Lv{ent.level}", x, y - 22, 24, TEXT, bold=True)
    f = font(22)
    img = f.render(f"{max(0, ent.hp)}/{ent.max_hp}", True, MUTED)
    surf.blit(img, (x + w - img.get_width(), y - 20))


def draw_balloon(surf, cx, top_y, text, color=TEXT):
    f = font(26)
    lines = wrap_text(text, f, 320)
    lh = f.get_linesize()
    bw = max(60, max(f.size(ln)[0] for ln in lines) + 28)
    bh = lh * len(lines) + 18
    bx = int(cx - bw / 2)
    by = int(top_y - bh - 14)
    bx = max(8, min(WIDTH - bw - 8, bx))
    round_rect(surf, (bx, by, bw, bh), (245, 245, 245), 12)
    round_rect(surf, (bx, by, bw, bh), LINE, 12, 2)
    pygame.draw.polygon(surf, (245, 245, 245),
                        [(cx - 8, by + bh - 1), (cx + 8, by + bh - 1), (cx, by + bh + 12)])
    for i, ln in enumerate(lines):
        img = f.render(ln, True, (20, 20, 24))
        surf.blit(img, (bx + 14, by + 9 + i * lh))


def draw_sprite_at(surf, ent, scale=1.0):
    sp = ent.sprite
    if ent.flash > 0:
        sp = sp.copy()
        ov = pygame.Surface(sp.get_size(), pygame.SRCALPHA)
        a = int(160 * (ent.flash / 0.35))
        ov.fill((255, 80, 80, a))
        sp.blit(ov, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    sx = ent.x + ent.anim_off + (random.randint(-3, 3) if ent.shake > 0 else 0)
    sy = ent.y
    rect = sp.get_rect(midbottom=(int(sx), int(sy)))
    if not ent.alive:
        sp = pygame.transform.rotate(sp, 80)
        rect = sp.get_rect(midbottom=(int(sx), int(sy)))
    surf.blit(sp, rect)
    if ent.weapon and ent.alive:
        wrect = ent.weapon.get_rect(midbottom=(int(sx), int(sy)))
        surf.blit(ent.weapon, wrect)
    # status-iconen (gif/brand/verdoving/pantserbreuk) boven het hoofd
    if ent.alive and getattr(ent, "statuses", None):
        items = [(nm, n) for nm, n in ent.statuses.items() if nm in STATUS_INFO]
        if items:
            bw = 30; gap = 4
            total = len(items) * bw + (len(items) - 1) * gap
            bx = int(sx) - total // 2
            by = rect.top - 24
            f = font(15)
            for nm, n in items:
                info = STATUS_INFO[nm]
                r = pygame.Rect(bx, by, bw, 18)
                round_rect(surf, r, (20, 20, 24), 5)
                round_rect(surf, r, info["color"], 5, 2)
                img = f.render(f"{info['short']}", True, info["color"])
                surf.blit(img, img.get_rect(center=(r.centerx, r.centery)))
                bx += bw + gap
    return rect


# ---------------------------------------------------------------- states
class State:
    def __init__(self, app):
        self.app = app

    def handle(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, s):
        pass


class SplashState(State):
    MIN = 4.0      # minimaal zo lang tonen
    MAX = 10.0     # maximaal wachten op de stem

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.spoke = False
        self.voice_done = False

    def _voice_done(self):
        self.voice_done = True

    def _go(self):
        self.app.set_state(TitleState(self.app))

    def handle(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._go()

    def update(self, dt):
        self.t += dt
        if not self.spoke and self.t > 0.3:
            self.spoke = True
            if tts.is_installed():
                line = (APP_NAME + ". Een spel gemaakt door Dravenlock Games."
                        if LANG == "nl" else
                        APP_NAME + ". A game made by Dravenlock Games.")
                tts.say(line, role="narrator", lang=LANG, on_done=self._voice_done)
            else:
                self.voice_done = True   # geen stem om op te wachten
        ready = self.t >= self.MIN and (self.voice_done or self.t >= self.MAX)
        if ready:
            self._go()

    def draw(self, s):
        s.fill((8, 8, 11))
        if self.app.splash_logo:
            r = self.app.splash_logo.get_rect(center=(WIDTH // 2, 220))
            s.blit(self.app.splash_logo, r)
        draw_text(s, APP_NAME, WIDTH // 2, 410, 72, GOLD, center=True, bold=True)
        credit = ("Een spel gemaakt door Dravenlock Games" if LANG == "nl"
                  else "A game made by Dravenlock Games")
        draw_text(s, credit, WIDTH // 2, 470, 26, TEXT, center=True)
        dots = "." * (1 + int(self.t * 2) % 3)
        if not self.voice_done and self.t > 0.3:
            draw_text(s, t("Even geduld, het spel start") + dots,
                      WIDTH // 2, 512, 24, MUTED, center=True)
        # fade-in
        if self.t < 0.5:
            ov = pygame.Surface((WIDTH, HEIGHT)); ov.fill((8, 8, 11))
            ov.set_alpha(int(255 * (1 - self.t / 0.5))); s.blit(ov, (0, 0))


class PauseState(State):
    def __init__(self, app, game_state):
        super().__init__(app)
        self.game_state = game_state
        self.sel = 0
        self.buttons = []
        self.items = [
            ("Hervatten", self._resume),
            ("Instellingen", lambda: self.app.set_state(SettingsState(self.app, return_state=self))),
            ("Gids", lambda: self.app.set_state(HelpState(self.app, return_state=self))),
            ("Nieuw spel", self._new_game),
            ("Hoofdmenu", lambda: self.app.set_state(TitleState(self.app))),
        ]

    def _new_game(self):
        delete_save()
        self.app.set_state(ClassSelectState(self.app))

    def _resume(self):
        self.app.set_state(self.game_state)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p):
                self._resume()
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.items)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.items)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.items[self.sel][1]()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return

    def draw(self, s):
        # bevroren spel op de achtergrond
        try:
            self.game_state.draw(s)
        except Exception:
            s.blit(self.app.bg_title, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((8, 8, 12, 180))
        s.blit(ov, (0, 0))
        draw_text(s, t("Pauze"), WIDTH // 2, 130, 64, GOLD, center=True, bold=True)
        self.buttons = []
        y = 250
        mx, my = pygame.mouse.get_pos()
        for i, (label, fn) in enumerate(self.items):
            rect = pygame.Rect(WIDTH // 2 - 170, y, 340, 52)
            hov = rect.collidepoint(mx, my) or i == self.sel
            round_rect(s, rect, PANEL2 if hov else PANEL, 10)
            round_rect(s, rect, ACCENT if hov else LINE, 10, 2)
            draw_text(s, t(label), WIDTH // 2, y + 26, 30, TEXT, center=True, bold=hov)
            self.buttons.append((rect, fn))
            y += 64
        draw_text(s, t("ESC of P om te hervatten"), WIDTH // 2, HEIGHT - 40, 22,
                  MUTED, center=True)


class HelpState(State):
    def __init__(self, app, return_state=None):
        super().__init__(app)
        self.page = 0
        self.buttons = []
        self.return_state = return_state

    def _back(self):
        self.app.set_state(self.return_state or TitleState(self.app))

    def _nav(self, d):
        self.page = (self.page + d) % 3

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self._back()
            elif e.key in (pygame.K_RIGHT, pygame.K_SPACE, pygame.K_RETURN, pygame.K_d):
                self._nav(1)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self._nav(-1)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return

    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((10, 10, 14, 180))
        s.blit(ov, (0, 0))
        if self.page == 0:
            self._draw_play(s)
        elif self.page == 1:
            self._draw_classes(s)
        else:
            self._draw_status(s)
        # navigatie
        self.buttons = []
        prev = pygame.Rect(40, HEIGHT - 66, 180, 46)
        nxt = pygame.Rect(WIDTH - 220, HEIGHT - 66, 180, 46)
        for rect, lab, fn in [(prev, "Vorige", lambda: self._nav(-1)),
                              (nxt, "Volgende", lambda: self._nav(1))]:
            round_rect(s, rect, PANEL2, 10); round_rect(s, rect, LINE, 10, 2)
            draw_text(s, t(lab), rect.centerx, rect.centery, 26, TEXT, center=True, bold=True)
            self.buttons.append((rect, fn))
        back = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 66, 180, 46)
        round_rect(s, back, ACCENT, 10)
        draw_text(s, t("Terug"), back.centerx, back.centery, 26, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.buttons.append((back, self._back))
        draw_text(s, f"{self.page + 1} / 3", WIDTH // 2, HEIGHT - 92, 20, MUTED, center=True)

    def _draw_play(self, s):
        draw_text(s, t("Gids") + " - " + t("Hoe te spelen"), WIDTH // 2, 46, 44,
                  GOLD, center=True, bold=True)
        x = 80
        y = 100
        lines = [
            (t("Doel") + ": " + (
                "versla alle 13 gevechten en de draak." if LANG == "nl"
                else "beat all 13 fights and the dragon."), GOLD, 26),
            ((("Gevechten gaan om de beurt. Op je beurt kies je:")
              if LANG == "nl" else
              "Fights are turn-based. On your turn you choose:"), TEXT, 24),
            (("- Aanvallen: een vijand (kies zelf je doel)." if LANG == "nl"
              else "- Attack: one enemy (pick your target)."), MUTED, 23),
            (("- Vaardigheid: klasse-krachten; sommige raken alle vijanden."
              if LANG == "nl" else
              "- Skill: class powers; some hit all enemies."), MUTED, 23),
            (("- Verdedigen: halveert de volgende klap." if LANG == "nl"
              else "- Defend: halves the next hit."), MUTED, 23),
            (("- Drankje: geneest je, beperkt aantal." if LANG == "nl"
              else "- Potion: heals you, limited supply."), MUTED, 23),
            (("Bij een aanval rolt een d20: 20 = kritieke treffer, 1 = mis."
              if LANG == "nl" else
              "Each attack rolls a d20: 20 = critical hit, 1 = miss."), ACCENT, 24),
            (("Kira vecht automatisch met je mee." if LANG == "nl"
              else "Kira fights alongside you automatically."), TEXT, 24),
            (("Win je: niveau omhoog (vaardigheden op 3/5/7/10, wapens op 3/6/9)"
              if LANG == "nl" else
              "On a win: level up (skills at 3/5/7/10, weapons at 3/6/9)"), TEXT, 24),
            (("en daarna kies je een beloning (buit) uit drie kaarten."
              if LANG == "nl" else
              "and then you pick a reward (loot) from three cards."), TEXT, 24),
        ]
        for txt, col, sz in lines:
            draw_text(s, txt, x, y, sz, col)
            y += sz + 7
        y += 4
        draw_text(s, t("Tips") + ":", x, y, 26, ACCENT, bold=True); y += 30
        tips = ([
            "- Gebruik vaardigheden die alle vijanden raken tegen groepen.",
            "- Bewaar drankjes voor noodgevallen; verdedig tegen de vuuradem.",
            "- Pauzeer met ESC of P (ook voor instellingen en de gids).",
            "- De draak is loeizwaar: kies een sterke klasse en speel slim.",
        ] if LANG == "nl" else [
            "- Use skills that hit all enemies against groups.",
            "- Save potions for emergencies; defend against the fire breath.",
            "- Pause with ESC or P (also for settings and the guide).",
            "- The dragon is brutal: pick a strong class and play smart.",
        ])
        for tp in tips:
            draw_text(s, tp, x, y, 23, MUTED); y += 28

    def _draw_classes(self, s):
        draw_text(s, t("Gids") + " - " + t("De klassen"), WIDTH // 2, 42, 42,
                  GOLD, center=True, bold=True)
        draw_text(s, ("Elke klasse speelt anders - en is te winnen met de juiste aanpak."
                      if LANG == "nl" else
                      "Each class plays differently - and is winnable with the right approach."),
                  WIDTH // 2, 84, 22, MUTED, center=True)
        x = 70
        y = 112
        for cls in CLASSES:
            sp = draw_hero_sprite(cls["colors"], 48)
            s.blit(sp, (x, y - 4))
            draw_text(s, t(cls["name"]), x + 64, y, 25, ACCENT, bold=True)
            draw_text(s, t(CLASS_TIPS.get(cls["key"], "")), x + 64, y + 26, 20, MUTED)
            y += 54

    def _draw_status(self, s):
        draw_text(s, t("Gids") + " - " + t("Status-effecten"), WIDTH // 2, 42, 42,
                  GOLD, center=True, bold=True)
        draw_text(s, ("Verschijnen als icoontje boven een strijder. Jouw skills en sommige"
                      if LANG == "nl" else
                      "Shown as a badge above a fighter. Your skills and some"),
                  WIDTH // 2, 84, 22, MUTED, center=True)
        draw_text(s, ("vijanden brengen ze aan - elke klasse heeft een eigen debuff."
                      if LANG == "nl" else
                      "enemies apply them - each class has its own debuff."),
                  WIDTH // 2, 110, 22, MUTED, center=True)
        rows = [
            ("vergif", "Vergif", ("Schade per beurt, enkele beurten lang."
                                  if LANG == "nl" else "Damage each turn for a few turns.")),
            ("brand", "Brand", ("Meer schade per beurt, maar korter."
                                if LANG == "nl" else "More damage per turn, but shorter.")),
            ("verdoving", "Verdoving", ("Sla een beurt over."
                                        if LANG == "nl" else "Skip a turn.")),
            ("pantserbreuk", "Pantserbreuk", ("Halve verdediging - neemt meer schade."
                                              if LANG == "nl" else
                                              "Half defense - takes more damage.")),
        ]
        x = 120
        y = 160
        f = font(16)
        for key, name, desc in rows:
            info = STATUS_INFO[key]
            badge = pygame.Rect(x, y, 64, 30)
            round_rect(s, badge, (20, 20, 24), 6)
            round_rect(s, badge, info["color"], 6, 2)
            img = f.render(info["short"], True, info["color"])
            s.blit(img, img.get_rect(center=badge.center))
            draw_text(s, t(name), x + 84, y + 2, 28, info["color"], bold=True)
            draw_text(s, desc, x + 84, y + 32, 21, MUTED)
            y += 76
        draw_text(s, ("Tip: gif/brand stapelen niet, maar verlengen wel. Versla snel!"
                      if LANG == "nl" else
                      "Tip: poison/burn don't stack but do refresh. Win fast!"),
                  WIDTH // 2, y + 6, 22, ACCENT, center=True)


class TitleState(State):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE:
                self.app.set_state(ClassSelectState(self.app))
            elif e.key == pygame.K_l:
                set_lang("en" if LANG == "nl" else "nl")
                self.app.cfg["lang"] = LANG; save_config(self.app.cfg)
            elif e.key == pygame.K_v:
                self.app.toggle_voice()
            elif e.key == pygame.K_ESCAPE:
                self.app.running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.app.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.blit(self.app.bg_title, (0, 0))
        if self.app.icon_big:
            r = self.app.icon_big.get_rect(center=(WIDTH // 2, 150))
            s.blit(self.app.icon_big, r)
        draw_text(s, APP_NAME, WIDTH // 2, 270, 84, GOLD, center=True, bold=True)
        draw_text(s, t("Een retro kerkertocht"), WIDTH // 2, 320, 30, MUTED, center=True)
        self.app.buttons = []
        items = []
        if has_save():
            items.append((t("Doorgaan"), self._continue_run))
        items += [
            (t("Nieuw spel"), lambda: self.app.set_state(ClassSelectState(self.app))),
            (t("Gids"), lambda: self.app.set_state(HelpState(self.app))),
            (t("Instellingen"), lambda: self.app.set_state(SettingsState(self.app))),
            (t("Taal") + ": " + (t("Nederlands") if LANG == "nl" else t("Engels")),
             self.app.toggle_lang),
            (t("Afsluiten"), self.app.quit),
        ]
        n = len(items)
        y = max(330, 360 - (n - 5) * 25)
        step = 50 if n <= 5 else 46
        mx, my = pygame.mouse.get_pos()
        for label, fn in items:
            rect = pygame.Rect(WIDTH // 2 - 170, y, 340, 44)
            hov = rect.collidepoint(mx, my)
            round_rect(s, rect, PANEL2 if hov else PANEL, 10)
            round_rect(s, rect, ACCENT if hov else LINE, 10, 2)
            draw_text(s, label, WIDTH // 2, y + 22, 27, TEXT, center=True, bold=hov)
            self.app.buttons.append((rect, fn))
            y += step
        best = self.app.cfg.get("best_depth", 0)
        sub = f"v{APP_VERSION}  -  {DONATE_URL}"
        if best:
            sub = (t("Beste diepte") + f": {best}   |   ") + sub
        draw_text(s, sub, WIDTH // 2, HEIGHT - 16, 19, MUTED, center=True)

    def _continue_run(self):
        if not self.app.load_run():
            delete_save()
            self.app.set_state(ClassSelectState(self.app))


class ClassSelectState(State):
    def __init__(self, app):
        super().__init__(app)
        self.idx = 0

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_d):
                self.idx = (self.idx + 1) % len(CLASSES)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.idx = (self.idx - 1) % len(CLASSES)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start()
            elif e.key == pygame.K_ESCAPE:
                self.app.set_state(TitleState(self.app))
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.app.buttons:
                if rect.collidepoint(e.pos):
                    fn()

    def start(self):
        cls = CLASSES[self.idx]
        self.app.set_state(NameEntryState(self.app, cls))

    def _cycle_diff(self):
        order = ["normaal", "zwaar", "helse"]
        global DIFFICULTY
        i = (order.index(DIFFICULTY) + 1) % len(order) if DIFFICULTY in order else 1
        DIFFICULTY = order[i]
        self.app.cfg["difficulty"] = DIFFICULTY; save_config(self.app.cfg)

    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        draw_text(s, t("Kies je held"), WIDTH // 2, 60, 56, GOLD, center=True, bold=True)
        cls = CLASSES[self.idx]
        # grote sprite-preview
        prev = draw_hero_sprite(cls["colors"], 130)
        wp = draw_weapon(cls["weapon"], cls["colors"], 130)
        cx, cy = WIDTH // 2, 250
        s.blit(prev, prev.get_rect(center=(cx, cy)))
        s.blit(wp, wp.get_rect(center=(cx, cy)))
        draw_text(s, t(cls["name"]), WIDTH // 2, 358, 44, TEXT, center=True, bold=True)
        # speelstijl (zodat elke klasse anders voelt)
        lines = wrap_text(t(CLASS_TIPS.get(cls["key"], cls["desc"])), font(24), 640)
        for i, ln in enumerate(lines):
            draw_text(s, ln, WIDTH // 2, 398 + i * 28, 24, ACCENT, center=True)
        # stats
        stats = [("Leven", cls["hp"]), ("Aanval", cls["atk"]), ("Verdediging", cls["dfn"]),
                 ("Magie", cls["mag"]), ("Snelheid", cls["spd"])]
        sx = WIDTH // 2 - 250
        sy = 478
        for i, (lab, val) in enumerate(stats):
            draw_text(s, t(lab), sx, sy + i * 0, 24, MUTED)
            bar = pygame.Rect(sx + 130, sy + 4, 120, 12)
            round_rect(s, bar, (30, 30, 36), 6)
            frac = min(1.0, val / 140 if lab == "Leven" else val / 25)
            round_rect(s, (bar.x, bar.y, int(120 * frac), 12), ACCENT, 6)
            if i == 2:
                sx = WIDTH // 2 + 30; sy = 478
            sy += 30 if i != 2 else 0
        # navigatie
        self.app.buttons = []
        left = pygame.Rect(WIDTH // 2 - 360, 240, 60, 60)
        right = pygame.Rect(WIDTH // 2 + 300, 240, 60, 60)
        for rect, lab, fn in [(left, "<", lambda: self._nav(-1)),
                              (right, ">", lambda: self._nav(1))]:
            round_rect(s, rect, PANEL2, 10); round_rect(s, rect, LINE, 10, 2)
            draw_text(s, lab, rect.centerx, rect.centery, 40, TEXT, center=True, bold=True)
            self.app.buttons.append((rect, fn))
        # moeilijkheidsknop (rechtsboven)
        diff_lbl = {"normaal": "Normaal", "zwaar": "Zwaar", "helse": "Helse"}.get(DIFFICULTY, "Zwaar")
        dcol = {"normaal": GOOD, "zwaar": GOLD, "helse": RED}.get(DIFFICULTY, GOLD)
        db = pygame.Rect(WIDTH - 290, 92, 270, 44)
        round_rect(s, db, PANEL2, 10); round_rect(s, db, dcol, 10, 2)
        draw_text(s, t("Moeilijkheid") + ": " + t(diff_lbl), db.centerx, db.centery, 24,
                  dcol, center=True, bold=True)
        self.app.buttons.append((db, self._cycle_diff))
        start_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT - 64, 220, 50)
        round_rect(s, start_btn, ACCENT, 10)
        draw_text(s, t("Start"), start_btn.centerx, start_btn.centery, 30, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.app.buttons.append((start_btn, self.start))
        draw_text(s, f"{self.idx + 1} / {len(CLASSES)}", WIDTH // 2, 150, 24, MUTED, center=True)

    def _nav(self, d):
        self.idx = (self.idx + d) % len(CLASSES)


# ---------------------------------------------------------------- gevecht
FLOOR_Y = int(HEIGHT * 0.72) + 30


class BattleState(State):
    def __init__(self, app, theme, enemy_names, level, intro_boss=False, elite=False):
        super().__init__(app)
        self.theme = theme
        self.bg = make_background(theme)
        self.particles, self.pkind = make_particles(theme)
        self.ptime = 0.0
        self.hero = app.hero
        self.kira = app.kira
        self.hero.statuses = {}
        self.kira.statuses = {}
        if isinstance(enemy_names, str):
            enemy_names = [enemy_names]
        self.enemies = [make_enemy(n, level, elite=elite) for n in enemy_names]
        self.intro_boss = intro_boss
        self.hero.x, self.hero.y = 330, FLOOR_Y
        self.kira.x, self.kira.y = 200, FLOOR_Y + 18
        self._place_enemies()
        self.party = [self.hero, self.kira]
        for e in self.all():
            e.hp_shown = float(e.hp)
            e.defending = False
        self.queue = []
        self.phase = "intro"
        self.menu_idx = 0
        self.skill_idx = 0
        self.target_idx = 0
        self.pending = None
        self.menu = ["Aanvallen", "Vaardigheid", "Verdedigen", "Drankje"]
        self.floaters = []
        self.balloon = None
        self.timer = 0.0
        self.action = None
        self.applied = False
        self.menu_rects = []
        self.skill_rects = []
        intro = (t("De baas verschijnt!") if intro_boss else
                 (t("Vijanden naderen!") if len(self.enemies) > 1 else
                  t("Kira springt mee in het gevecht!")))
        spk = self.enemies[0] if intro_boss else self.kira
        self._set_balloon(spk, intro, ACCENT,
                          role=("enemy" if intro_boss else "kira"))

    # -- opstelling / lijsten
    def _place_enemies(self):
        n = len(self.enemies)
        layout = {1: [690], 2: [620, 810], 3: [575, 715, 855],
                  4: [545, 660, 775, 905]}.get(n, [545, 660, 775, 905])
        for i, en in enumerate(self.enemies):
            en.x = layout[i] if i < len(layout) else 700 + i * 40
            en.y = FLOOR_Y + (-12 if i % 2 else 0)

    def all(self):
        return [self.hero, self.kira] + self.enemies

    def alive_players(self):
        return [p for p in self.party if p.alive]

    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    # -- helpers
    def _set_balloon(self, ent, text, color=TEXT, role="hero"):
        self.balloon = (ent, text, color)
        tts.speak(text, role=role, lang=LANG)

    def _add_float(self, x, y, text, color):
        self.floaters.append(dict(x=x, y=y, text=text, color=color, life=1.0))

    def _calc_dmg(self, power, target, magic=False):
        base = power - target.eff_dfn() * (0.3 if magic else 0.5)
        base += random.randint(-2, 3)
        return max(1, int(base))

    # -- beurt-logica
    def start_round(self):
        combatants = [c for c in self.all() if c.alive]
        self.queue = sorted(combatants, key=lambda c: c.spd + random.random(), reverse=True)
        self.next_turn()

    def _tick_status(self, actor):
        """Past gif/brand-schade toe en telt duren af. Geeft True als verdoofd."""
        stunned = actor.has_status("verdoving")
        for nm in ("vergif", "brand"):
            if actor.has_status(nm):
                frac = 0.06 if nm == "vergif" else 0.09
                dmg = max(5 if nm == "vergif" else 7, int(actor.max_hp * frac))
                actor.hp = max(0, actor.hp - dmg)
                actor.flash = 0.3
                self._add_float(actor.x, actor.y - 80, f"-{dmg}", STATUS_INFO[nm]["color"])
                if actor.hp <= 0:
                    actor.alive = False
        for nm in list(actor.statuses):
            actor.statuses[nm] -= 1
            if actor.statuses[nm] <= 0:
                del actor.statuses[nm]
        return stunned

    def next_turn(self):
        if not self.alive_enemies():
            self.victory(); return
        if not self.hero.alive:
            self.defeat(); return
        if not self.queue:
            self.start_round(); return
        actor = self.queue.pop(0)
        if not actor.alive:
            self.next_turn(); return
        actor.defending = False
        self.current = actor
        # status-effecten aan het begin van de beurt
        stunned = self._tick_status(actor)
        if not actor.alive:
            if actor is self.hero:
                self.defeat()
            else:
                sfx.play("hit")
                self.next_turn()
            return
        if stunned:
            self._set_balloon(actor, t("Verdoofd!"),
                              STATUS_INFO["verdoving"]["color"],
                              "hero" if actor.is_player else "enemy")
            self.phase = "post"; self.timer = 0.0
            return
        if actor is self.hero:
            self.phase = "menu"; self.menu_idx = 0
        elif actor is self.kira:
            self.timer = 0.0; self._kira_action()
        else:
            self.timer = 0.0; self._enemy_action(actor)

    def _begin_action(self, actor, hits, heal=0, heal_target=None, text="",
                      role="hero", color=TEXT, snd=None, status_applies=None):
        self.action = dict(actor=actor, hits=hits, heal=heal, heal_target=heal_target,
                           snd=snd, status_applies=status_applies or [])
        self.applied = False
        self.phase = "act"
        self.timer = 0.0
        self._set_balloon(actor, text, color, role)

    # -- speler-acties (met d20-worp)
    def _do_attack(self, target):
        self._start_roll("attack", None, target)

    def _do_skill(self, skill, target=None):
        typ = skill[1]
        if typ in ("dmg", "mdmg", "aoe", "maoe", "lifesteal"):
            self._start_roll("skill", skill, target)
            return
        name, typ, power = skill[0], skill[1], skill[2]
        txt = t("gebruikt") + " " + t(name) + "!"
        if typ == "heal":
            self._begin_action(self.hero, [], heal=int(self.hero.max_hp * power),
                               heal_target=self.hero, text=txt, role="hero", color=GOOD)
        elif typ == "buff":
            self.hero.buff = power
            self._begin_action(self.hero, [], text=txt, role="hero", color=GOLD)

    def _start_roll(self, kind, skill, target):
        self.pending_act = dict(kind=kind, skill=skill, target=target)
        if getattr(self.app, "dice", True):
            sfx.play("dice")
            self.phase = "roll"
            self.roll_t = 0.0
            self.roll_step = -1
            self.roll_val = None
            self.roll_hold = 0.0
            self.roll_shown = random.randint(1, 20)
        else:
            self._resolve_roll(None)

    def _resolve_roll(self, roll):
        pa = self.pending_act
        crit = roll == 20
        miss = roll == 1
        if roll is None:
            mult = 1.0
        elif crit:
            mult = 2.0
        elif miss:
            mult = 0.0
        else:
            mult = 0.75 + (roll - 2) / 18.0 * 0.55
        suffix = ""
        if crit:
            suffix = " " + t("Kritieke treffer!")
        elif miss:
            suffix = " " + t("Mis!")

        def dmg_for(base, tgt, magic=False):
            return 0 if miss else max(1, int(self._calc_dmg(base, tgt, magic) * mult))

        def snd_for(base):
            return "crit" if crit else ("miss" if miss else base)

        if pa["kind"] == "attack":
            target = pa["target"]
            d = dmg_for(self.hero.atk * self.hero.buff, target)
            self.hero.buff = 1.0
            self._begin_action(self.hero, [(target, d)], text=t("valt aan!") + suffix,
                               role="hero", color=(GOLD if crit else ACCENT), snd=snd_for("hit"))
            return
        skill = pa["skill"]
        name, typ, power = skill[0], skill[1], skill[2]
        status = skill[3] if len(skill) > 3 else None
        txt = t("gebruikt") + " " + t(name) + "!" + suffix
        col = GOLD if crit else PURPLE

        def st_for(hits):
            if status and not miss:
                return [(tg, status) for tg, _ in hits]
            return None

        if typ == "dmg":
            d = dmg_for(self.hero.atk * power * self.hero.buff, pa["target"])
            self.hero.buff = 1.0
            hits = [(pa["target"], d)]
            self._begin_action(self.hero, hits, text=txt, role="hero",
                               color=GOLD, snd=snd_for("hit"), status_applies=st_for(hits))
        elif typ == "mdmg":
            d = dmg_for(self.hero.mag * power, pa["target"], True)
            hits = [(pa["target"], d)]
            self._begin_action(self.hero, hits, text=txt, role="hero",
                               color=col, snd=snd_for("magic"), status_applies=st_for(hits))
        elif typ == "aoe":
            hits = [(en, dmg_for(self.hero.atk * power * 0.7 * self.hero.buff, en))
                    for en in self.alive_enemies()]
            self.hero.buff = 1.0
            self._begin_action(self.hero, hits, text=txt, role="hero",
                               color=GOLD, snd=snd_for("hit"), status_applies=st_for(hits))
        elif typ == "maoe":
            hits = [(en, dmg_for(self.hero.mag * power * 0.6, en, True))
                    for en in self.alive_enemies()]
            self._begin_action(self.hero, hits, text=txt, role="hero",
                               color=col, snd=snd_for("magic"), status_applies=st_for(hits))
        elif typ == "lifesteal":
            d = dmg_for(self.hero.atk * power, pa["target"])
            hits = [(pa["target"], d)]
            self._begin_action(self.hero, hits, heal=d // 2,
                               heal_target=self.hero, text=txt, role="hero",
                               color=RED, snd=snd_for("hit"), status_applies=st_for(hits))

    def _hero_defend(self):
        self.hero.defending = True
        self._begin_action(self.hero, [], text=t("verdedigt zich."), color=MUTED)

    def _potion_prompt(self):
        if self.app.potions <= 0:
            self._set_balloon(self.hero, t("Geen drankjes meer!"), WARN)
            self.phase = "post"; self.timer = 0.0
            return
        if self.kira.alive:                 # kies wie je geneest
            self.phase = "potiontarget"; self.pt_idx = 0
        else:
            self._give_potion(self.hero)

    def _give_potion(self, target):
        if self.app.potions <= 0:
            self.phase = "menu"; return
        self.app.potions -= 1
        heal = max(80, int(target.max_hp * 0.45))
        if target is self.hero:
            txt = t("drinkt een drankje!")
        else:
            txt = (f"geeft {target.name} een drankje!" if LANG == "nl"
                   else f"gives {target.name} a potion!")
        self._begin_action(self.hero, [], heal=heal, heal_target=target,
                           text=txt, role="hero", color=GOOD, snd="heal")

    def _kira_action(self):
        target = min(self.alive_enemies(), key=lambda e: e.hp)
        dmg = self._calc_dmg(self.kira.atk, target)
        name = self.hero.name
        cries = [t("bijt!"), t("Waf!"), t("Grrr!"),
                 (f"Voor jou, {name}!" if LANG == "nl" else f"For you, {name}!"),
                 (f"Pas op, {name}!" if LANG == "nl" else f"Watch out, {name}!")]
        self._begin_action(self.kira, [(target, dmg)], text=random.choice(cries),
                           role="kira", color=GOOD, snd="hit")

    def _enemy_action(self, enemy):
        alive = self.alive_players()
        # draak: kans op vuuradem die iedereen raakt + brandt
        if enemy.key == "Draak" and len(alive) > 1 and random.random() < 0.26:
            hits = [(p, self._calc_dmg(enemy.atk * 0.5, p)) for p in alive]
            st = [(p, "brand") for p in alive]
            self._begin_action(enemy, hits, text=t("Vuuradem!"),
                               role="enemy", color=WARN, snd="roar", status_applies=st)
            return
        target = random.choice(alive)
        dmg = self._calc_dmg(enemy.atk, target)
        st = None
        es = getattr(enemy, "elite_status", None) or ENEMY_DEFS.get(enemy.key, {}).get("status")
        chance = diff_status_chance() + (0.15 if getattr(enemy, "elite", False) else 0.0)
        if es and random.random() < chance:
            st = [(target, es)]
        self._begin_action(enemy, [(target, dmg)], text=t("valt aan!"),
                           role="enemy", color=WARN, snd="hit", status_applies=st)

    # -- input
    def handle(self, e):
        # pauze: P altijd, ESC behalve in sub-menu's (daar betekent ESC 'terug')
        if e.type == pygame.KEYDOWN and (e.key == pygame.K_p or
                (e.key == pygame.K_ESCAPE and self.phase not in
                 ("skillmenu", "target", "potiontarget"))):
            self.app.set_state(PauseState(self.app, self)); return
        if e.type == pygame.MOUSEBUTTONDOWN and getattr(self, "pause_rect", None) \
                and self.pause_rect.collidepoint(e.pos):
            self.app.set_state(PauseState(self.app, self)); return
        if self.phase == "menu":
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_idx = (self.menu_idx + 1) % len(self.menu)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.menu_idx = (self.menu_idx - 1) % len(self.menu)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._choose(self.menu_idx)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(self.menu_rects):
                    if rect.collidepoint(e.pos):
                        self._choose(i)
        elif self.phase == "skillmenu":
            skills = unlocked_skills(self.hero.cls, self.hero.level)
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_DOWN, pygame.K_s):
                    self.skill_idx = (self.skill_idx + 1) % (len(skills) + 1)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.skill_idx = (self.skill_idx - 1) % (len(skills) + 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._pick_skill(self.skill_idx)
                elif e.key == pygame.K_ESCAPE:
                    self.phase = "menu"
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in self.skill_rects:
                    if rect.collidepoint(e.pos):
                        self._pick_skill(i)
        elif self.phase == "target":
            en = self.alive_enemies()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.target_idx = (self.target_idx + 1) % len(en)
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self.target_idx = (self.target_idx - 1) % len(en)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._confirm_target()
                elif e.key == pygame.K_ESCAPE:
                    self.phase = "menu"
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for i, en_i in enumerate(en):
                    r = en_i.sprite.get_rect(midbottom=(int(en_i.x), int(en_i.y)))
                    if r.collidepoint(e.pos):
                        self.target_idx = i; self._confirm_target(); break
        elif self.phase == "potiontarget":
            targets = [self.hero, self.kira]
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    self.pt_idx = (self.pt_idx + 1) % 2
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._give_potion(targets[self.pt_idx])
                elif e.key == pygame.K_ESCAPE:
                    self.phase = "menu"
            elif e.type == pygame.MOUSEBUTTONDOWN:
                for rect, tgt in getattr(self, "potion_rects", []):
                    if rect.collidepoint(e.pos):
                        self._give_potion(tgt); break
        elif self.phase in ("post", "intro") and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.timer = 99

    def _choose(self, i):
        sfx.play("click", 0.5)
        if i == 0:
            self.pending = "attack"; self.phase = "target"; self.target_idx = 0
        elif i == 1:
            self.phase = "skillmenu"; self.skill_idx = 0
        elif i == 2:
            self._hero_defend()
        elif i == 3:
            self._potion_prompt()

    def _pick_skill(self, idx):
        skills = unlocked_skills(self.hero.cls, self.hero.level)
        if idx >= len(skills):       # 'Annuleer'
            self.phase = "menu"; return
        skill = skills[idx]
        typ = skill[1]
        if typ in ("dmg", "mdmg", "lifesteal"):
            self.pending = skill; self.phase = "target"; self.target_idx = 0
        else:
            self._do_skill(skill, None)

    def _confirm_target(self):
        en = self.alive_enemies()
        if not en:
            self.phase = "menu"; return
        target = en[self.target_idx % len(en)]
        if self.pending == "attack":
            self._do_attack(target)
        else:
            self._do_skill(self.pending, target)
        self.pending = None

    # -- update
    def update(self, dt):
        for ent in self.all():
            if ent.hp_shown > ent.hp:
                ent.hp_shown = max(ent.hp, ent.hp_shown - 140 * dt)
            elif ent.hp_shown < ent.hp:
                ent.hp_shown = min(ent.hp, ent.hp_shown + 140 * dt)
            ent.flash = max(0, ent.flash - dt)
            ent.shake = max(0, ent.shake - dt)
        for fl in self.floaters:
            fl["y"] -= 40 * dt
            fl["life"] -= dt
        self.floaters = [f for f in self.floaters if f["life"] > 0]
        self.ptime += dt
        update_particles(self.particles, self.pkind, self.ptime, dt)

        self.timer += dt
        if self.phase == "intro":
            if self.timer > 1.6:
                self.start_round()
        elif self.phase == "roll":
            self.roll_t += dt
            if self.roll_t < 0.7:                 # tollen
                step = int(self.roll_t / 0.06)
                if step != self.roll_step:
                    self.roll_step = step
                    self.roll_shown = random.randint(1, 20)
            elif self.roll_val is None:           # vastzetten
                self.roll_val = random.randint(1, 20)
                self.roll_shown = self.roll_val
            else:
                self.roll_hold += dt              # even tonen
                if self.roll_hold > 0.75:
                    self._resolve_roll(self.roll_val)
        elif self.phase == "act":
            a = self.action
            actor = a["actor"]
            prog = min(1.0, self.timer / 0.5)
            if a["hits"]:
                tx = sum(tg.x for tg, _ in a["hits"]) / len(a["hits"])
                direction = 1 if actor.x < tx else -1
                actor.anim_off = math.sin(prog * math.pi) * 55 * direction
            else:
                actor.anim_off = math.sin(prog * math.pi) * -18
            if not self.applied and prog >= 0.5:
                self.applied = True
                if a.get("snd"):
                    sfx.play(a["snd"])
                for tgt, dmg in a["hits"]:
                    if dmg <= 0:                   # gemiste worp
                        self._add_float(tgt.x, tgt.y - 80, t("Mis!"), MUTED)
                    else:
                        dealt = tgt.take_damage(dmg)
                        self._add_float(tgt.x, tgt.y - 80, f"-{dealt}",
                                        RED if tgt.is_player else GOLD)
                if a["heal"] and a["heal_target"]:
                    got = a["heal_target"].heal(a["heal"])
                    self._add_float(a["heal_target"].x, a["heal_target"].y - 80, f"+{got}", GOOD)
                for tgt, nm in a.get("status_applies", []):
                    if tgt.alive and nm in STATUS_INFO:
                        tgt.add_status(nm, STATUS_INFO[nm]["turns"])
                        self._add_float(tgt.x, tgt.y - 52, STATUS_INFO[nm]["short"],
                                        STATUS_INFO[nm]["color"])
            if prog >= 1.0:
                actor.anim_off = 0
                self.phase = "post"; self.timer = 0.0
        elif self.phase == "post":
            wait = 1.4 if tts.is_enabled() else 0.9
            if self.timer >= wait:
                self.balloon = None
                self.next_turn()

    def victory(self):
        self.phase = "victory"; self.balloon = None
        self.app.on_victory(self)

    def defeat(self):
        self.phase = "defeat"; self.balloon = None
        self.app.set_state(GameOverState(self.app))

    # -- teken
    def draw(self, s):
        s.blit(self.bg, (0, 0))
        draw_particles(s, self.particles, self.pkind, self.ptime)
        # vijand-hp rechtsboven (gestapeld)
        for i, en in enumerate(self.enemies):
            draw_hp_bar_small(s, en, WIDTH - 200, 56 + i * 42)
        # speler-hp linksboven
        draw_hp_bar(s, self.hero, 30, 60)
        draw_hp_bar(s, self.kira, 30, 120)
        draw_text(s, f"{t('Drankjes')}: {self.app.potions}", 30, 150, 24, GOLD)
        # pauzeknop (rechtsboven)
        self.pause_rect = pygame.Rect(WIDTH - 46, 12, 34, 34)
        round_rect(s, self.pause_rect, PANEL2, 8); round_rect(s, self.pause_rect, LINE, 8, 2)
        pygame.draw.rect(s, TEXT, (self.pause_rect.x + 11, self.pause_rect.y + 9, 4, 16))
        pygame.draw.rect(s, TEXT, (self.pause_rect.x + 19, self.pause_rect.y + 9, 4, 16))
        # sprites: vijanden achter, dan helden
        for en in self.enemies:
            draw_sprite_at(s, en)
        draw_sprite_at(s, self.hero)
        draw_sprite_at(s, self.kira)
        # doel-aanwijzer
        if self.phase == "target":
            en = self.alive_enemies()
            if en:
                tg = en[self.target_idx % len(en)]
                top = tg.y - tg.sprite.get_height() - 14
                pygame.draw.polygon(s, GOLD, [(tg.x - 12, top), (tg.x + 12, top), (tg.x, top + 18)])
        # zwevende getallen
        for fl in self.floaters:
            draw_text(s, fl["text"], int(fl["x"]), int(fl["y"]), 36, fl["color"], center=True, bold=True)
        # ballon
        if self.balloon:
            ent, text, color = self.balloon
            draw_balloon(s, int(ent.x), int(ent.y - ent.sprite.get_height() - 6), text)
        # menu's
        self.menu_rects = []
        self.skill_rects = []
        if self.phase == "menu":
            self._draw_menu(s)
        elif self.phase == "skillmenu":
            self._draw_skillmenu(s)
        elif self.phase == "target":
            draw_text(s, t("Kies doel"), WIDTH // 2, HEIGHT - 30, 26, GOLD, center=True, bold=True)
        elif self.phase == "potiontarget":
            self._draw_potion_target(s)
        elif self.phase == "roll":
            self._draw_dice(s)

    def _draw_potion_target(self, s):
        draw_text(s, (t("Aan wie geef je het drankje?") if LANG == "nl"
                      else "Who gets the potion?"), WIDTH // 2, HEIGHT - 156, 26,
                  GOLD, center=True, bold=True)
        targets = [(self.hero, t("Held")), (self.kira, "Kira")]
        self.potion_rects = []
        bw, bh, gap = 220, 92, 40
        x0 = WIDTH // 2 - bw - gap // 2
        y = HEIGHT - 128
        mx, my = pygame.mouse.get_pos()
        for i, (tgt, label) in enumerate(targets):
            rect = pygame.Rect(x0 + i * (bw + gap), y, bw, bh)
            hov = rect.collidepoint(mx, my) or i == self.pt_idx
            round_rect(s, rect, PANEL2 if hov else PANEL, 12)
            round_rect(s, rect, GOOD if hov else LINE, 12, 3 if hov else 2)
            draw_text(s, label, rect.centerx, rect.y + 24, 28, TEXT, center=True, bold=True)
            draw_text(s, f"{int(tgt.hp)}/{tgt.max_hp}", rect.centerx, rect.y + 58, 24,
                      GOOD if tgt.hp < tgt.max_hp else MUTED, center=True)
            self.potion_rects.append((rect, tgt))

    def _draw_dice(self, s):
        cx, cy = WIDTH // 2, HEIGHT // 2 - 40
        settled = self.roll_val is not None
        val = self.roll_shown
        # kleur: 20 = goud (kritiek), 1 = rood (mis), anders accent
        if settled and val == 20:
            col = GOLD
        elif settled and val == 1:
            col = RED
        elif settled:
            col = ACCENT
        else:
            col = TEXT
        size = 96
        # lichte trilling tijdens het tollen
        jit = 0 if settled else random.randint(-3, 3)
        rect = pygame.Rect(cx - size // 2 + jit, cy - size // 2 + jit, size, size)
        round_rect(s, rect, PANEL, 16)
        round_rect(s, rect, col, 16, 4)
        draw_text(s, str(val), rect.centerx, rect.centery, 56, col, center=True, bold=True)
        draw_text(s, "d20", rect.centerx, rect.top - 18, 24, MUTED, center=True)
        if settled and val == 20:
            draw_text(s, t("Kritieke treffer!"), cx, rect.bottom + 22, 30, GOLD,
                      center=True, bold=True)
        elif settled and val == 1:
            draw_text(s, t("Mis!"), cx, rect.bottom + 22, 30, RED, center=True, bold=True)
        else:
            draw_text(s, t("Gooien..."), cx, rect.bottom + 22, 24, MUTED, center=True)

    def _draw_menu(self, s):
        panel = pygame.Rect(30, HEIGHT - 190, 320, 170)
        round_rect(s, panel, PANEL, 12); round_rect(s, panel, ACCENT, 12, 2)
        draw_text(s, self.hero.name, panel.x + 16, panel.y + 12, 26, GOLD, bold=True)
        mx, my = pygame.mouse.get_pos()
        for i, opt in enumerate(self.menu):
            rect = pygame.Rect(panel.x + 14, panel.y + 44 + i * 30, panel.w - 28, 28)
            hov = rect.collidepoint(mx, my) or i == self.menu_idx
            if hov:
                round_rect(s, rect, PANEL2, 6)
            label = t(opt)
            draw_text(s, ("> " if i == self.menu_idx else "  ") + label,
                      rect.x + 6, rect.y + 4, 26, TEXT if hov else MUTED, bold=hov)
            self.menu_rects.append(rect)

    def _draw_skillmenu(self, s):
        skills = unlocked_skills(self.hero.cls, self.hero.level)
        rows = skills + [("Annuleer", "_", 0)]
        h = 38 + len(rows) * 30
        panel = pygame.Rect(30, HEIGHT - h - 20, 360, h)
        round_rect(s, panel, PANEL, 12); round_rect(s, panel, GOLD, 12, 2)
        draw_text(s, t("Kies vaardigheid"), panel.x + 16, panel.y + 10, 24, GOLD, bold=True)
        mx, my = pygame.mouse.get_pos()
        for i, sk in enumerate(rows):
            rect = pygame.Rect(panel.x + 14, panel.y + 40 + i * 30, panel.w - 28, 28)
            hov = rect.collidepoint(mx, my) or i == self.skill_idx
            if hov:
                round_rect(s, rect, PANEL2, 6)
            name = t(sk[0])
            kind = {"dmg": "", "mdmg": "", "aoe": " (allen)", "maoe": " (allen)",
                    "heal": " (genezen)", "buff": " (kracht)", "lifesteal": " (levenssteel)"}.get(sk[1], "")
            if LANG == "en":
                kind = {" (allen)": " (all)", " (genezen)": " (heal)", " (kracht)": " (power)",
                        " (levenssteel)": " (lifesteal)"}.get(kind, kind)
            label = name + (kind if sk[0] != "Annuleer" else "")
            draw_text(s, ("> " if i == self.skill_idx else "  ") + label,
                      rect.x + 6, rect.y + 4, 24, TEXT if hov else MUTED, bold=hov)
            self.skill_rects.append((i, rect))


class LevelUpState(State):
    def __init__(self, app, new_skill, new_weapon, finished):
        super().__init__(app)
        self.new_skill = new_skill
        self.new_weapon = new_weapon
        self.finished = finished
        self.buttons = []
        self.t = 0.0
        self.spoke = False
        sfx.play("levelup")

    def _continue(self):
        if self.finished:
            self.app.set_state(VictoryState(self.app))
        else:
            self.app.set_state(RewardState(self.app))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._continue()

    def update(self, dt):
        self.t += dt
        if not self.spoke and self.t > 0.2:
            self.spoke = True
            tts.speak(t("Niveau omhoog!"), role="hero", lang=LANG)

    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((8, 8, 12, 140))
        s.blit(ov, (0, 0))
        draw_text(s, t("Niveau omhoog!"), WIDTH // 2, 110, 58, GOLD, center=True, bold=True)
        h = self.app.hero
        sp = scale_px(draw_hero_sprite(h.cls["colors"], 130), 1)
        s.blit(sp, sp.get_rect(center=(WIDTH // 2, 230)))
        wp = h.weapon
        s.blit(wp, wp.get_rect(center=(WIDTH // 2, 230)))
        draw_text(s, f"{h.name}  -  {t('Niveau')} {h.level}", WIDTH // 2, 320, 36,
                  TEXT, center=True, bold=True)
        y = 370
        if self.new_skill:
            draw_text(s, f"{t('Nieuwe vaardigheid')}: {t(self.new_skill)}", WIDTH // 2, y,
                      30, ACCENT, center=True, bold=True)
            y += 40
        if self.new_weapon:
            draw_text(s, f"{t('Nieuw wapen')}!", WIDTH // 2, y, 30, GOLD, center=True, bold=True)
            y += 40
        if not self.new_skill and not self.new_weapon:
            draw_text(s, f"+ {t('Leven')}, {t('Aanval')}, {t('Magie')}", WIDTH // 2, y, 28,
                      MUTED, center=True)
            y += 40
        self.buttons = []
        btn = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 110, 240, 52)
        round_rect(s, btn, ACCENT, 12)
        draw_text(s, t("Verder"), btn.centerx, btn.centery, 30, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.buttons.append((btn, self._continue))
        draw_text(s, t("Druk op een toets"), WIDTH // 2, HEIGHT - 34, 22, MUTED, center=True)


REWARDS = [
    dict(key="hp", name="Levenskracht", desc="+30 max leven (en genezen)",
         icon="hart", color=GOOD, rare=False),
    dict(key="potion", name="Drankjes", desc="+2 drankjes",
         icon="fles", color=GOOD, rare=False),
    dict(key="atk", name="Amulet van Kracht", desc="+4 aanval",
         icon="amulet", color=WARN, rare=False),
    dict(key="mag", name="Amulet van Magie", desc="+4 magie",
         icon="amulet", color=PURPLE, rare=False),
    dict(key="dfn", name="Harnasplaat", desc="+3 verdediging",
         icon="schild", color=ACCENT, rare=False),
    dict(key="spd", name="Snelle Laarzen", desc="+3 snelheid",
         icon="amulet", color=ACCENT, rare=False),
    dict(key="heal", name="Genezende Bron", desc="Volledig genezen + 1 drankje",
         icon="hart", color=GOOD, rare=False),
    dict(key="weapon", name="Legendarisch Wapen", desc="Veel sterker wapen (+7 aanval)",
         icon="zwaard", color=GOLD, rare=True),
]


def apply_reward(app, key):
    h = app.hero
    if key == "hp":
        h.max_hp += 30; h.heal(30)
    elif key == "potion":
        app.potions = min(12, app.potions + 2)
    elif key == "atk":
        h.atk += 4
    elif key == "mag":
        h.mag += 4
    elif key == "dfn":
        h.dfn += 3
    elif key == "spd":
        h.spd += 3
    elif key == "heal":
        h.heal(h.max_hp); app.potions = min(12, app.potions + 1)
    elif key == "weapon":
        upgrade_weapon(h); h.atk += 7


def _draw_reward_icon(s, icon, cx, cy, col):
    if icon == "hart":
        pygame.draw.circle(s, col, (cx - 9, cy - 4), 10)
        pygame.draw.circle(s, col, (cx + 9, cy - 4), 10)
        pygame.draw.polygon(s, col, [(cx - 18, cy - 1), (cx + 18, cy - 1), (cx, cy + 20)])
    elif icon == "fles":
        pygame.draw.rect(s, col, (cx - 9, cy - 14, 18, 30), border_radius=6)
        pygame.draw.rect(s, (40, 40, 46), (cx - 5, cy - 20, 10, 8))
    elif icon == "schild":
        pygame.draw.polygon(s, col, [(cx, cy - 16), (cx + 16, cy - 8),
                                     (cx + 12, cy + 16), (cx - 12, cy + 16), (cx - 16, cy - 8)])
    elif icon == "zwaard":
        pygame.draw.rect(s, col, (cx - 3, cy - 18, 6, 28))
        pygame.draw.rect(s, col, (cx - 12, cy + 8, 24, 6))
        pygame.draw.polygon(s, col, [(cx - 3, cy - 18), (cx + 3, cy - 18), (cx, cy - 26)])
    else:  # amulet
        pygame.draw.circle(s, col, (cx, cy + 2), 13, 4)
        pygame.draw.circle(s, col, (cx, cy + 2), 5)
        pygame.draw.line(s, col, (cx - 8, cy - 12), (cx + 8, cy - 12), 3)


class RewardState(State):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = []
        self.sel = 0
        # 3 kaarten: zeldzame buit minder vaak
        pool = []
        for r in REWARDS:
            pool += [r] * (1 if r["rare"] else 4)
        picks = []
        while len(picks) < 3:
            r = random.choice(pool)
            if r not in picks:
                picks.append(r)
        self.cards = picks
        sfx.play("levelup")

    def _take(self, i):
        apply_reward(self.app, self.cards[i]["key"])
        sfx.play("heal")
        self.app._start_encounter()

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % 3
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % 3
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._take(self.sel)
        elif e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return

    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((10, 10, 14, 150))
        s.blit(ov, (0, 0))
        draw_text(s, t("Kies een beloning"), WIDTH // 2, 80, 52, GOLD, center=True, bold=True)
        draw_text(s, t("Buit na de overwinning"), WIDTH // 2, 130, 26, MUTED, center=True)
        self.buttons = []
        cw, ch = 270, 300
        gap = 30
        total = cw * 3 + gap * 2
        x0 = (WIDTH - total) // 2
        cy = 180
        mx, my = pygame.mouse.get_pos()
        for i, card in enumerate(self.cards):
            x = x0 + i * (cw + gap)
            rect = pygame.Rect(x, cy, cw, ch)
            hov = rect.collidepoint(mx, my) or i == self.sel
            round_rect(s, rect, PANEL2 if hov else PANEL, 16)
            round_rect(s, rect, card["color"] if hov else LINE, 16, 3 if hov else 2)
            if card["rare"]:
                draw_text(s, t("ZELDZAAM"), rect.centerx, rect.y + 24, 20, GOLD,
                          center=True, bold=True)
            _draw_reward_icon(s, card["icon"], rect.centerx, rect.y + 110, card["color"])
            draw_text(s, t(card["name"]), rect.centerx, rect.y + 170, 26,
                      card["color"], center=True, bold=True)
            for j, ln in enumerate(wrap_text(t(card["desc"]), font(22), cw - 30)):
                draw_text(s, ln, rect.centerx, rect.y + 210 + j * 26, 22, TEXT, center=True)
            btn = pygame.Rect(rect.centerx - 80, rect.bottom - 52, 160, 38)
            round_rect(s, btn, card["color"] if hov else PANEL2, 10)
            draw_text(s, t("Kies"), btn.centerx, btn.centery, 24,
                      (10, 10, 14) if hov else TEXT, center=True, bold=True, shadow=False)
            self.buttons.append((rect, (lambda k=i: self._take(k))))
        draw_text(s, t("Pijltjes + Enter, of klik"), WIDTH // 2, HEIGHT - 40, 22,
                  MUTED, center=True)


class VictoryState(State):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0
        self.buttons = []
        sfx.play("victory")

    def _to_menu(self):
        delete_save()
        self.app.set_state(TitleState(self.app))

    def _new_game(self):
        delete_save()
        self.app.set_state(ClassSelectState(self.app))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.app.start_endless()
            elif e.key == pygame.K_ESCAPE:
                self._to_menu()

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.blit(self.app.bg_title, (0, 0))
        draw_text(s, t("Overwinning!"), WIDTH // 2, 140, 76, GOLD, center=True, bold=True)
        draw_text(s, t("Je hebt de draak verslagen!") if LANG == "nl" else "You slayed the dragon!",
                  WIDTH // 2, 214, 32, TEXT, center=True)
        if self.app.icon_big:
            r = self.app.icon_big.get_rect(center=(WIDTH // 2, 330))
            s.blit(self.app.icon_big, r)
        draw_text(s, ("Ga je door in de eindeloze modus? Hoe diep kom je?"
                      if LANG == "nl" else
                      "Continue into endless mode? How deep can you go?"),
                  WIDTH // 2, 440, 24, MUTED, center=True)
        self.buttons = []
        bw, gap = 220, 24
        total = bw * 3 + gap * 2
        x0 = (WIDTH - total) // 2
        y = HEIGHT - 100
        endb = pygame.Rect(x0, y, bw, 54)
        newb = pygame.Rect(x0 + bw + gap, y, bw, 54)
        menb = pygame.Rect(x0 + 2 * (bw + gap), y, bw, 54)
        round_rect(s, endb, GOLD, 12)
        draw_text(s, t("Eindeloze modus"), endb.centerx, endb.centery, 24, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        round_rect(s, newb, PANEL2, 12); round_rect(s, newb, ACCENT, 12, 2)
        draw_text(s, t("Nieuw spel"), newb.centerx, newb.centery, 24, TEXT, center=True, bold=True)
        round_rect(s, menb, PANEL2, 12); round_rect(s, menb, LINE, 12, 2)
        draw_text(s, t("Hoofdmenu"), menb.centerx, menb.centery, 24, TEXT, center=True, bold=True)
        self.buttons.append((endb, self.app.start_endless))
        self.buttons.append((newb, self._new_game))
        self.buttons.append((menb, self._to_menu))


class GameOverState(State):
    def __init__(self, app):
        super().__init__(app)
        self.endless = getattr(app, "endless", False)
        self.depth = getattr(app, "depth", 0)
        self.best = app.cfg.get("best_depth", 0)
        self.buttons = []
        delete_save()
        sfx.play("defeat")

    def _new_game(self):
        self.app.set_state(ClassSelectState(self.app))

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._new_game()
            elif e.key == pygame.K_ESCAPE:
                self.app.set_state(TitleState(self.app))

    def draw(self, s):
        s.fill((10, 8, 10))
        draw_text(s, t("Spel voorbij"), WIDTH // 2, 180, 72, RED, center=True, bold=True)
        draw_text(s, t("Je bent gevallen..."), WIDTH // 2, 260, 32, MUTED, center=True)
        if self.endless:
            draw_text(s, t("Diepte bereikt") + f": {self.depth}", WIDTH // 2, 330, 34,
                      GOLD, center=True, bold=True)
            draw_text(s, t("Record") + f": {self.best}", WIDTH // 2, 372, 26,
                      MUTED, center=True)
        self.buttons = []
        bw, gap = 230, 30
        x0 = (WIDTH - (bw * 2 + gap)) // 2
        y = HEIGHT - 110
        newb = pygame.Rect(x0, y, bw, 54)
        menb = pygame.Rect(x0 + bw + gap, y, bw, 54)
        round_rect(s, newb, ACCENT, 12)
        draw_text(s, t("Opnieuw spelen"), newb.centerx, newb.centery, 25, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        round_rect(s, menb, PANEL2, 12); round_rect(s, menb, LINE, 12, 2)
        draw_text(s, t("Hoofdmenu"), menb.centerx, menb.centery, 25, TEXT, center=True, bold=True)
        self.buttons.append((newb, self._new_game))
        self.buttons.append((menb, lambda: self.app.set_state(TitleState(self.app))))


class IntroStoryState(State):
    def __init__(self, app):
        super().__init__(app)
        self.text = intro_story(app.hero.name)
        self.t = 0.0
        self.spoke = False
        self.voice_done = False
        self.buttons = []

    def _mark_done(self):
        self.voice_done = True

    def _ready(self):
        # actief zodra de vertelling klaar is (of na een ruime noodgrens)
        return self.voice_done or self.t > 30

    def _advance(self):
        if self._ready():
            self.app._start_encounter()

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); return
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._advance()

    def update(self, dt):
        self.t += dt
        if not self.spoke and self.t > 0.25:
            self.spoke = True
            # speak() roept on_done meteen aan als de stem uit staat -> knop direct actief
            tts.speak(self.text, role="narrator", lang=LANG, on_done=self._mark_done)

    def draw(self, s):
        s.blit(self.app.bg_title, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((8, 8, 12, 150))
        s.blit(ov, (0, 0))
        draw_text(s, t("Het avontuur begint"), WIDTH // 2, 90, 52, GOLD, center=True, bold=True)
        if self.app.icon_big:
            r = self.app.icon_big.get_rect(center=(WIDTH // 2, 190))
            s.blit(self.app.icon_big, r)
        # verhaal-paneel
        panel = pygame.Rect(WIDTH // 2 - 360, 300, 720, 200)
        round_rect(s, panel, PANEL, 14); round_rect(s, panel, GOLD, 14, 2)
        lines = wrap_text(self.text, font(30), panel.w - 56)
        ty = panel.y + 30
        for ln in lines:
            draw_text(s, ln, WIDTH // 2, ty, 30, TEXT, center=True)
            ty += 38
        self.buttons = []
        ready = self._ready()
        btn = pygame.Rect(WIDTH // 2 - 110, 530, 220, 52)
        if ready:
            round_rect(s, btn, ACCENT, 12)
            draw_text(s, t("Verder"), btn.centerx, btn.centery, 30, (10, 10, 14),
                      center=True, bold=True, shadow=False)
            self.buttons.append((btn, self._advance))
            draw_text(s, t("Druk op een toets"), WIDTH // 2, HEIGHT - 30, 22, MUTED, center=True)
        else:
            round_rect(s, btn, PANEL2, 12); round_rect(s, btn, LINE, 12, 2)
            draw_text(s, t("Verder"), btn.centerx, btn.centery, 30, MUTED,
                      center=True, bold=True)
            draw_text(s, t("Het verhaal wordt verteld..."), WIDTH // 2, HEIGHT - 30, 22,
                      MUTED, center=True)


class NameEntryState(State):
    def __init__(self, app, cls):
        super().__init__(app)
        self.cls = cls
        self.name = app.cfg.get("hero_name", "")
        self.caret = 0.0
        self.sprite = draw_hero_sprite(cls["colors"], 130)
        self.weapon = draw_weapon(cls["weapon"], cls["colors"], 130)
        self.buttons = []

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                self._confirm()
            elif e.key == pygame.K_ESCAPE:
                self.app.set_state(ClassSelectState(self.app))
            elif e.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            else:
                ch = e.unicode
                if ch and ch.isprintable() and len(self.name) < 14 and ch not in "\t\r\n":
                    self.name += ch
        if e.type == pygame.MOUSEBUTTONDOWN:
            for rect, fn in self.buttons:
                if rect.collidepoint(e.pos):
                    fn(); break

    def _confirm(self):
        name = self.name.strip() or t(self.cls["name"])
        self.app.cfg["hero_name"] = self.name.strip()
        save_config(self.app.cfg)
        self.app.start_run(self.cls, name)

    def update(self, dt):
        self.caret = (self.caret + dt) % 1.0

    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        draw_text(s, t("Geef je held een naam"), WIDTH // 2, 70, 52, GOLD, center=True, bold=True)
        cx = WIDTH // 2
        s.blit(self.sprite, self.sprite.get_rect(center=(cx, 230)))
        s.blit(self.weapon, self.weapon.get_rect(center=(cx, 230)))
        draw_text(s, t(self.cls["name"]), cx, 320, 34, MUTED, center=True)
        # tekstvak
        box = pygame.Rect(cx - 230, 370, 460, 64)
        round_rect(s, box, (233, 233, 233), 12)
        round_rect(s, box, ACCENT, 12, 3)
        shown = self.name
        cursor = "|" if self.caret < 0.5 else " "
        draw_text(s, shown + cursor, box.x + 20, box.centery, 40, (20, 20, 24),
                  center=False, shadow=False)
        # placeholder
        if not self.name:
            draw_text(s, t("Naam"), box.x + 20, box.centery - 2, 36, (150, 150, 155),
                      shadow=False)
            # cursor opnieuw boven placeholder
            draw_text(s, cursor, box.x + 20, box.centery, 40, (20, 20, 24), shadow=False)
        self.buttons = []
        begin = pygame.Rect(cx - 130, 470, 260, 56)
        round_rect(s, begin, ACCENT, 12)
        draw_text(s, t("Begin avontuur"), begin.centerx, begin.centery, 30,
                  (10, 10, 14), center=True, bold=True, shadow=False)
        self.buttons.append((begin, self._confirm))
        back = pygame.Rect(cx - 130, 538, 260, 44)
        round_rect(s, back, PANEL2, 10); round_rect(s, back, LINE, 10, 2)
        draw_text(s, t("Terug"), back.centerx, back.centery, 26, TEXT, center=True)
        self.buttons.append((back, lambda: self.app.set_state(ClassSelectState(self.app))))
        draw_text(s, t("Typ een naam en druk op Enter"), cx, HEIGHT - 36, 24, MUTED, center=True)


class SettingsState(State):
    ROLE_LABELS = [("hero", "Held"), ("kira", "Kira"), ("enemy", "Vijand"),
                   ("narrator", "Verteller")]

    def __init__(self, app, return_state=None):
        super().__init__(app)
        self.rows = []
        self.popup = None          # rol die bewerkt wordt, of None
        self.pop_rows = []
        self.return_state = return_state

    def _back(self):
        self.app.set_state(self.return_state or TitleState(self.app))

    # -- opslaan
    def _save(self):
        self.app.cfg["voice"] = tts.is_enabled()
        self.app.cfg["roles"] = tts.all_cfg()
        save_config(self.app.cfg)

    def _toggle_voice(self):
        tts.set_enabled(not tts.is_enabled())
        self._save()

    def _toggle_dice(self):
        self.app.dice = not getattr(self.app, "dice", True)
        self.app.cfg["dice"] = self.app.dice
        save_config(self.app.cfg)

    def _toggle_sound(self):
        sfx.set_enabled(not sfx.is_enabled())
        self.app.cfg["sound"] = sfx.is_enabled()
        save_config(self.app.cfg)

    def _snd_vol(self, d):
        sfx.set_volume(round(sfx.get_volume() + d, 2))
        sfx.play("click")
        self.app.cfg["sound_vol"] = sfx.get_volume()
        save_config(self.app.cfg)

    def _open(self, role):
        self.popup = role

    def _close(self):
        self._save()
        self.popup = None

    # -- input
    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.popup:
                self._close()
            else:
                self._back()
            return
        if e.type == pygame.MOUSEBUTTONDOWN:
            rows = self.pop_rows if self.popup else self.rows
            for rect, fn in rows:
                if rect.collidepoint(e.pos):
                    fn(); return

    # -- popup-acties
    def _voice(self, role, d):
        names = tts.voices()
        i = (names.index(tts.get_voice(role)) + d) % len(names)
        tts.set_voice(role, names[i]); self._save()

    def _vol(self, role, d):
        tts.set_volume(role, round(tts.get_volume(role) + d, 2)); self._save()

    def _spd(self, role, d):
        tts.set_speed(role, round(tts.get_speed(role) + d, 2)); self._save()

    def _pit(self, role, d):
        tts.set_pitch(role, round(tts.get_pitch(role) + d, 2)); self._save()

    # -- teken
    def draw(self, s):
        s.blit(self.app.bg_select, (0, 0))
        draw_text(s, t("Instellingen"), WIDTH // 2, 56, 52, GOLD, center=True, bold=True)
        self.rows = []
        x = WIDTH // 2 - 300
        w = 600
        y = 120
        # Stem aan/uit
        round_rect(s, (x, y, w, 50), PANEL, 10); round_rect(s, (x, y, w, 50), LINE, 10, 2)
        draw_text(s, t("Stem"), x + 18, y + 13, 28, TEXT, bold=True)
        on = tts.is_enabled()
        btn = pygame.Rect(x + w - 150, y + 8, 130, 34)
        round_rect(s, btn, GOOD if on else PANEL2, 8); round_rect(s, btn, LINE, 8, 2)
        draw_text(s, t("aan") if on else t("uit"), btn.centerx, btn.centery, 26,
                  (10, 10, 14) if on else MUTED, center=True, bold=True, shadow=False)
        self.rows.append((btn, self._toggle_voice))
        y += 62
        # Status
        round_rect(s, (x, y, w, 44), PANEL, 10); round_rect(s, (x, y, w, 44), LINE, 10, 2)
        draw_text(s, t("Status"), x + 18, y + 11, 24, MUTED)
        col = {"klaar": GOOD, "mislukt": WARN, "niet_geinstalleerd": WARN,
               "laden": GOLD, "installeren": GOLD}.get(tts.status(), TEXT)
        draw_text(s, tts.status_text(LANG), x + 120, y + 12, 22, col)
        y += 54
        # Dobbelsteen (D&D) aan/uit
        round_rect(s, (x, y, w, 50), PANEL, 10); round_rect(s, (x, y, w, 50), LINE, 10, 2)
        draw_text(s, t("Dobbelsteen") + " (D&D)", x + 18, y + 13, 26, TEXT, bold=True)
        don = getattr(self.app, "dice", True)
        dbtn = pygame.Rect(x + w - 150, y + 8, 130, 34)
        round_rect(s, dbtn, GOOD if don else PANEL2, 8); round_rect(s, dbtn, LINE, 8, 2)
        draw_text(s, t("aan") if don else t("uit"), dbtn.centerx, dbtn.centery, 26,
                  (10, 10, 14) if don else MUTED, center=True, bold=True, shadow=False)
        self.rows.append((dbtn, self._toggle_dice))
        y += 56
        # Geluid (muziek + effecten): aan/uit + volume
        round_rect(s, (x, y, w, 50), PANEL, 10); round_rect(s, (x, y, w, 50), LINE, 10, 2)
        draw_text(s, t("Geluid"), x + 18, y + 13, 26, TEXT, bold=True)
        son = sfx.is_enabled() if sfx.available() else False
        # volume -/+
        vx = x + 220
        for lbl, fn, bx in [("-", lambda: self._snd_vol(-0.1), vx),
                            ("+", lambda: self._snd_vol(0.1), vx + 150)]:
            b = pygame.Rect(bx, y + 8, 40, 34)
            round_rect(s, b, PANEL2, 8); round_rect(s, b, LINE, 8, 2)
            draw_text(s, lbl, b.centerx, b.centery, 28, TEXT, center=True, bold=True)
            self.rows.append((b, fn))
        bar = pygame.Rect(vx + 48, y + 18, 92, 12)
        round_rect(s, bar, (30, 30, 36), 6)
        round_rect(s, (bar.x, bar.y, int(92 * sfx.get_volume()), 12), ACCENT, 6)
        sbtn = pygame.Rect(x + w - 150, y + 8, 130, 34)
        round_rect(s, sbtn, GOOD if son else PANEL2, 8); round_rect(s, sbtn, LINE, 8, 2)
        draw_text(s, t("aan") if son else t("uit"), sbtn.centerx, sbtn.centery, 26,
                  (10, 10, 14) if son else MUTED, center=True, bold=True, shadow=False)
        self.rows.append((sbtn, self._toggle_sound))
        y += 58
        # stem-kaarten (klik om in te stellen)
        draw_text(s, t("Klik op een stem om in te stellen"), WIDTH // 2, y + 4, 22,
                  MUTED, center=True)
        y += 30
        cw = (w - 20) // 2
        for i, (role, lab) in enumerate(self.ROLE_LABELS):
            cx = x + (i % 2) * (cw + 20)
            cy = y + (i // 2) * 76
            rect = pygame.Rect(cx, cy, cw, 66)
            hov = rect.collidepoint(*pygame.mouse.get_pos())
            round_rect(s, rect, PANEL2 if hov else PANEL, 12)
            round_rect(s, rect, ACCENT if hov else LINE, 12, 2)
            draw_text(s, t(lab), rect.x + 16, rect.y + 12, 28, TEXT, bold=True)
            draw_text(s, tts.get_voice(role), rect.x + 16, rect.y + 40, 22, ACCENT)
            det = f"{tts.get_volume(role)*100:.0f}%  {tts.get_speed(role):.2f}x"
            f = font(19)
            img = f.render(det, True, MUTED)
            s.blit(img, (rect.right - 16 - img.get_width(), rect.y + 41))
            self.rows.append((rect, (lambda r=role: self._open(r))))
        y += 2 * 76 + 6
        # installeren / terug
        if not tts.is_installed() and not tts.is_frozen():
            inst = pygame.Rect(x, y, 260, 46)
            round_rect(s, inst, GOLD, 10)
            draw_text(s, t("Stem installeren"), inst.centerx, inst.centery, 24,
                      (10, 10, 14), center=True, bold=True, shadow=False)
            self.rows.append((inst, tts.install))
        back = pygame.Rect(x + w - 200, y, 200, 46)
        round_rect(s, back, ACCENT, 10)
        draw_text(s, t("Terug"), back.centerx, back.centery, 28, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.rows.append((back, self._back))

        if self.popup:
            self._draw_popup(s)

    def _draw_popup(self, s):
        role = self.popup
        lab = dict(self.ROLE_LABELS)[role]
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); ov.fill((0, 0, 0, 150))
        s.blit(ov, (0, 0))
        pw, ph = 540, 430
        px = WIDTH // 2 - pw // 2
        py = HEIGHT // 2 - ph // 2
        round_rect(s, (px, py, pw, ph), PANEL, 16)
        round_rect(s, (px, py, pw, ph), GOLD, 16, 3)
        draw_text(s, t("Stem instellen") + ": " + t(lab), WIDTH // 2, py + 30, 34,
                  GOLD, center=True, bold=True)
        self.pop_rows = []
        rx = px + 30
        rw = pw - 60
        yy = py + 80

        def arrows(fn_l, fn_r):
            for lbl, fn, bx in [("<", fn_l, px + pw - 110), (">", fn_r, px + pw - 60)]:
                b = pygame.Rect(bx, yy - 4, 40, 36)
                round_rect(s, b, PANEL2, 8); round_rect(s, b, LINE, 8, 2)
                draw_text(s, lbl, b.centerx, b.centery, 28, TEXT, center=True, bold=True)
                self.pop_rows.append((b, fn))

        # Stem
        draw_text(s, t("Stem"), rx, yy, 26, MUTED)
        draw_text(s, tts.get_voice(role), rx + 180, yy - 2, 30, ACCENT, bold=True)
        arrows(lambda: self._voice(role, -1), lambda: self._voice(role, 1))
        yy += 56
        # Volume
        draw_text(s, t("Volume"), rx, yy, 26, MUTED)
        bar = pygame.Rect(rx + 180, yy + 4, 150, 12)
        round_rect(s, bar, (30, 30, 36), 6)
        round_rect(s, (bar.x, bar.y, int(150 * tts.get_volume(role)), 12), ACCENT, 6)
        draw_text(s, f"{tts.get_volume(role)*100:.0f}%", rx + 345, yy, 24, TEXT)
        arrows(lambda: self._vol(role, -0.1), lambda: self._vol(role, 0.1))
        yy += 56
        # Snelheid
        draw_text(s, t("Snelheid"), rx, yy, 26, MUTED)
        draw_text(s, f"{tts.get_speed(role):.2f}x", rx + 180, yy, 26, TEXT)
        arrows(lambda: self._spd(role, -0.05), lambda: self._spd(role, 0.05))
        yy += 56
        # Toonhoogte
        draw_text(s, t("Toonhoogte"), rx, yy, 26, MUTED)
        draw_text(s, f"{tts.get_pitch(role):.2f}", rx + 180, yy, 26, TEXT)
        arrows(lambda: self._pit(role, -0.05), lambda: self._pit(role, 0.05))
        yy += 66
        # Test + Opslaan
        tb = pygame.Rect(px + 30, py + ph - 64, 200, 46)
        round_rect(s, tb, PANEL2, 10); round_rect(s, tb, ACCENT, 10, 2)
        draw_text(s, t("Test stem"), tb.centerx, tb.centery, 26, TEXT, center=True, bold=True)
        self.pop_rows.append((tb, (lambda r=role: tts.test(r, LANG))))
        sv = pygame.Rect(px + pw - 230, py + ph - 64, 200, 46)
        round_rect(s, sv, GOOD, 10)
        draw_text(s, t("Opslaan"), sv.centerx, sv.centery, 26, (10, 10, 14),
                  center=True, bold=True, shadow=False)
        self.pop_rows.append((sv, self._close))


# ---------------------------------------------------------------- app
class App:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(APP_NAME)
        pygame.key.set_repeat(350, 45)
        self.clock = pygame.time.Clock()
        self.running = True
        self.cfg = load_config()
        set_lang(self.cfg.get("lang") or detect_lang())
        _df = self.cfg.get("difficulty", "zwaar")
        if _df in DIFF_SCALE:
            globals()["DIFFICULTY"] = _df
        self.dice = bool(self.cfg.get("dice", True))
        sfx.init(enabled=bool(self.cfg.get("sound", True)),
                 volume=float(self.cfg.get("sound_vol", 0.6)))
        icon = load_icon()
        if icon:
            pygame.display.set_icon(icon)
            self.icon_big = pygame.transform.smoothscale(icon, (170, 170))
            self.splash_logo = pygame.transform.smoothscale(icon, (260, 260))
        else:
            self.icon_big = None
            self.splash_logo = None
        self.bg_title = make_background("Drakenhol")
        self.bg_select = make_background("Kerker")
        self.buttons = []
        roles_cfg = self.cfg.get("roles", {}) if isinstance(self.cfg.get("roles"), dict) else {}
        tts.start(enabled=bool(self.cfg.get("voice", False)), roles_cfg=roles_cfg)
        self.state = SplashState(self)

    # run-beheer
    def start_run(self, cls, name=None):
        delete_save()
        self.cls = cls
        self.hero = make_hero(cls)
        if name:
            self.hero.name = name
        self.kira = make_kira()
        self.potions = 5
        self.endless = False
        self.depth = 0
        self.encounters = []
        n_fights = 12
        for i in range(n_fights):
            depth = i + 1
            th = random.choice(THEMES[:-1])
            elite = depth in (4, 8)                  # mini-bazen onderweg
            if elite:
                enemies = [random.choice(THEME_ENEMIES[th])]
            else:
                count = min(4, 1 + depth // 3)
                enemies = [random.choice(THEME_ENEMIES[th]) for _ in range(count)]
            self.encounters.append({"theme": th, "enemies": enemies,
                                    "level": depth, "elite": elite})
        self.encounters.append({"theme": "Drakenhol", "enemies": ["Draak", "Ork", "Ork"],
                                "level": n_fights + 2, "elite": False})
        self.enc_index = 0
        self.set_state(IntroStoryState(self))

    def _start_encounter(self):
        enc = self.encounters[self.enc_index]
        self.save_run()
        boss = "Draak" in enc["enemies"]
        self.set_state(BattleState(self, enc["theme"], enc["enemies"], enc["level"],
                                   intro_boss=boss, elite=enc.get("elite", False)))

    # opslaan & doorgaan
    def save_run(self):
        h = self.hero; k = self.kira
        write_save({
            "cls": self.cls["key"], "name": h.name,
            "hero": {"level": h.level, "max_hp": h.max_hp, "hp": h.hp, "atk": h.atk,
                     "dfn": h.dfn, "mag": h.mag, "spd": h.spd,
                     "weapon_tier": getattr(h, "weapon_tier", 0)},
            "kira": {"level": k.level, "max_hp": k.max_hp, "hp": k.hp,
                     "atk": k.atk, "dfn": k.dfn},
            "potions": self.potions, "enc_index": self.enc_index,
            "difficulty": DIFFICULTY, "encounters": self.encounters,
            "endless": self.endless, "depth": self.depth,
        })

    def load_run(self):
        data = read_save()
        if not data:
            return False
        try:
            cls = next((c for c in CLASSES if c["key"] == data["cls"]), CLASSES[0])
            self.cls = cls
            self.hero = make_hero(cls)
            self.hero.name = data.get("name", "Held")
            hd = data["hero"]
            for key in ("level", "max_hp", "hp", "atk", "dfn", "mag", "spd"):
                setattr(self.hero, key, hd[key])
            self.hero.weapon_tier = 0
            for _ in range(hd.get("weapon_tier", 0)):
                upgrade_weapon(self.hero)
            self.kira = make_kira()
            kd = data["kira"]
            for key in ("level", "max_hp", "hp", "atk", "dfn"):
                setattr(self.kira, key, kd[key])
            self.potions = data.get("potions", 5)
            self.enc_index = data.get("enc_index", 0)
            self.encounters = data.get("encounters", [])
            self.endless = data.get("endless", False)
            self.depth = data.get("depth", 0)
            df = data.get("difficulty", "zwaar")
            if df in DIFF_SCALE:
                globals()["DIFFICULTY"] = df
            if not self.encounters or self.enc_index >= len(self.encounters):
                if self.endless:
                    self._add_endless_encounter()
                else:
                    return False
            self.hero.hp = max(1, min(self.hero.hp, self.hero.max_hp))
            self.hero.hp_shown = float(self.hero.hp)
            self.kira.hp_shown = float(self.kira.hp)
        except Exception:
            return False
        self._start_encounter()
        return True

    # eindeloze modus
    def _add_endless_encounter(self):
        lvl = (self.encounters[-1]["level"] if self.encounters else 13) + 1
        th = random.choice(THEMES[:-1])
        elite = (lvl % 4 == 0)
        if elite:
            enemies = [random.choice(THEME_ENEMIES[th])]
        else:
            count = min(4, 2 + lvl // 6)
            enemies = [random.choice(THEME_ENEMIES[th]) for _ in range(count)]
        self.encounters.append({"theme": th, "enemies": enemies, "level": lvl, "elite": elite})
        self.depth = lvl
        if lvl > self.cfg.get("best_depth", 0):
            self.cfg["best_depth"] = lvl; save_config(self.cfg)

    def start_endless(self):
        self.endless = True
        self._add_endless_encounter()
        self.enc_index = len(self.encounters) - 1
        self._start_encounter()

    def on_victory(self, battle):
        before = unlocked_skills(self.cls, self.hero.level)
        # niveau omhoog - groei volgt de aard van de klasse
        cls = self.cls
        self.hero.level += 1
        self.kira.level += 1
        self.hero.max_hp += max(8, cls["hp"] // 10)
        self.hero.atk += max(2, cls["atk"] // 5)
        self.hero.mag += max(0, cls["mag"] // 5)
        self.hero.dfn += 1
        self.hero.spd += 1
        self.kira.max_hp += 8; self.kira.atk += 2; self.kira.dfn += 1
        # slechts gedeeltelijk genezen tussen gevechten (pittiger)
        for ent in (self.hero, self.kira):
            ent.alive = True
            ent.hp = min(ent.max_hp, ent.hp + ent.max_hp // 2)
            ent.hp_shown = float(ent.hp)
        self.potions = min(8, self.potions + 1)
        # nieuwe vaardigheid vrijgespeeld?
        after = unlocked_skills(self.cls, self.hero.level)
        new_skill = after[-1][0] if len(after) > len(before) else None
        # wapen-upgrade elke 3 niveaus
        new_weapon = False
        if self.hero.level % 3 == 0:
            upgrade_weapon(self.hero); self.hero.atk += 3; new_weapon = True
        self.enc_index += 1
        if self.endless:
            if self.enc_index >= len(self.encounters):
                self._add_endless_encounter()
            finished = False
        else:
            finished = self.enc_index >= len(self.encounters)
        self.set_state(LevelUpState(self, new_skill, new_weapon, finished))

    # taal/stem
    def toggle_lang(self):
        set_lang("en" if LANG == "nl" else "nl")
        self.cfg["lang"] = LANG; save_config(self.cfg)

    def toggle_voice(self):
        on = not tts.is_enabled()
        tts.set_enabled(on)
        self.cfg["voice"] = on; save_config(self.cfg)

    def quit(self):
        self.running = False

    def set_state(self, st):
        self.state = st

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle(e)
            self.state.update(dt)
            sfx.update()
            self.state.draw(self.screen)
            pygame.display.flip()
        tts.stop()
        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()

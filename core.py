# -*- coding: utf-8 -*-
"""Ядро игры: константы, темы, скины, звуки, шрифты, сохранения."""
import io
import json
import math
import os
import struct
import wave

import pygame

# --- Основные настройки экрана ---
W, H = 800, 600
FPS = 60
TITLE = "PARKOUR RUNNER"

# --- Физика ---
GRAVITY = 0.72
JUMP_V = -14.2
JUMP2_V = -12.0
MAX_FALL = 16
MOVE_SPEED = 5.6
PLAYER_W = 26
PLAYER_H = 40
GROUND_Y = 470

# --- Цвета ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (18, 22, 38)
GOLD = (255, 205, 70)
RED = (230, 70, 75)
GREEN = (90, 210, 120)
CYAN = (80, 210, 235)
GREY = (150, 158, 180)

# --- Тема оформления уровней ---
THEMES = [
    {"name": "Город",   "sky1": (101, 178, 240), "sky2": (190, 228, 250),
     "hill": (120, 170, 130), "hill2": (95, 145, 110), "plat": (70, 95, 120), "top": (120, 200, 130)},
    {"name": "Закат",   "sky1": (255, 130, 90),  "sky2": (255, 200, 130),
     "hill": (150, 90, 100),  "hill2": (110, 65, 85),  "plat": (90, 60, 80),  "top": (240, 150, 110)},
    {"name": "Ночь",    "sky1": (20, 24, 60),    "sky2": (55, 60, 110),
     "hill": (35, 40, 80),    "hill2": (25, 28, 60),    "plat": (45, 48, 85),  "top": (120, 130, 200)},
    {"name": "Пустыня", "sky1": (250, 200, 120), "sky2": (255, 235, 190),
     "hill": (210, 160, 95),  "hill2": (180, 130, 75),  "plat": (150, 105, 70), "top": (235, 195, 120)},
    {"name": "Лёд",     "sky1": (150, 215, 235), "sky2": (225, 245, 255),
     "hill": (160, 200, 220), "hill2": (125, 170, 200), "plat": (105, 145, 185), "top": (220, 245, 255)},
    {"name": "Лес",     "sky1": (120, 190, 170), "sky2": (200, 235, 200),
     "hill": (70, 130, 90),   "hill2": (45, 100, 70),   "plat": (80, 100, 70),  "top": (110, 180, 100)},
]

# --- Скины (24 штуки) ---
# body - основной цвет, accent - детали, extra - тип головного убора/эффекта
SKINS = [
    {"id": "classic",  "name": "Классик",     "price": 0,    "body": (60, 120, 220),  "accent": (255, 255, 255), "extra": "none"},
    {"id": "red",      "name": "Красный",     "price": 0,    "body": (220, 70, 70),   "accent": (255, 220, 150), "extra": "none"},
    {"id": "green",    "name": "Зелёный",     "price": 0,    "body": (70, 190, 100),  "accent": (240, 255, 200), "extra": "none"},
    {"id": "ninja",    "name": "Ниндзя",      "price": 60,   "body": (40, 42, 55),    "accent": (220, 60, 60),   "extra": "hood"},
    {"id": "spider",   "name": "Спайдер",     "price": 80,   "body": (180, 35, 45),   "accent": (30, 30, 40),    "extra": "mask"},
    {"id": "cosmo",    "name": "Космонавт",   "price": 100,  "body": (235, 235, 240), "accent": (60, 120, 200),  "extra": "helmet"},
    {"id": "knight",   "name": "Рыцарь",      "price": 120,  "body": (150, 160, 175), "accent": (220, 225, 235), "extra": "helmet"},
    {"id": "zombie",   "name": "Зомби",       "price": 140,  "body": (105, 170, 110), "accent": (60, 100, 65),   "extra": "none"},
    {"id": "robot",    "name": "Робот",       "price": 160,  "body": (110, 130, 150), "accent": (90, 240, 220),  "extra": "antenna"},
    {"id": "pirate",   "name": "Пират",       "price": 180,  "body": (170, 60, 55),   "accent": (35, 35, 40),    "extra": "cap"},
    {"id": "wizard",   "name": "Волшебник",   "price": 200,  "body": (105, 70, 180),  "accent": (250, 220, 90),  "extra": "hat"},
    {"id": "hero",     "name": "Супергерой",  "price": 220,  "body": (45, 90, 190),   "accent": (230, 60, 60),   "extra": "cape"},
    {"id": "tank",     "name": "Танк",        "price": 240,  "body": (90, 105, 70),   "accent": (55, 65, 45),    "extra": "helmet"},
    {"id": "scout",    "name": "Лазутчик",    "price": 260,  "body": (190, 150, 90),  "accent": (90, 70, 50),    "extra": "hood"},
    {"id": "mech",     "name": "Механик",     "price": 280,  "body": (200, 130, 60),  "accent": (70, 75, 85),    "extra": "antenna"},
    {"id": "dragon",   "name": "Дракон",      "price": 300,  "body": (60, 160, 120),  "accent": (255, 190, 60),  "extra": "horns"},
    {"id": "ice",      "name": "Ледяной",     "price": 320,  "body": (130, 210, 235), "accent": (245, 255, 255), "extra": "crown"},
    {"id": "fire",     "name": "Огненный",    "price": 340,  "body": (230, 100, 45),  "accent": (255, 220, 80),  "extra": "horns"},
    {"id": "ghost",    "name": "Призрак",     "price": 360,  "body": (210, 220, 235), "accent": (150, 190, 230), "extra": "none"},
    {"id": "king",     "name": "Король",      "price": 380,  "body": (150, 60, 170),  "accent": (255, 215, 70),  "extra": "crown"},
    {"id": "neon",     "name": "Неон",        "price": 400,  "body": (40, 230, 200),  "accent": (255, 80, 200),  "extra": "antenna"},
    {"id": "gold",     "name": "Золото",      "price": 450,  "body": (235, 190, 60),  "accent": (255, 245, 190), "extra": "crown"},
    {"id": "galaxy",   "name": "Галактика",   "price": 500,  "body": (70, 50, 140),   "accent": (200, 140, 255), "extra": "horns"},
    {"id": "legend",   "name": "Легенда",     "price": 600,  "body": (240, 80, 120),  "accent": (255, 230, 100), "extra": "cape"},
]

_FONT_CACHE = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        try:
            f = pygame.font.SysFont("Arial", size, bold=bold)
        except Exception:
            f = pygame.font.Font(None, size)
        _FONT_CACHE[key] = f
    return _FONT_CACHE[key]


def text(surf, s, x, y, size=20, color=WHITE, align="left", bold=False, shadow=True):
    f = font(size, bold)
    img = f.render(str(s), True, color)
    r = img.get_rect()
    if align == "center":
        r.center = (x, y)
    elif align == "right":
        r.right = x
        r.top = y
    else:
        r.topleft = (x, y)
    if shadow:
        sh = f.render(str(s), True, (0, 0, 0))
        surf.blit(sh, (r.x + 2, r.y + 2))
    surf.blit(img, r)
    return r


def gradient(surf, rect, c1, c2, vertical=True):
    x, y, w, h = rect
    if vertical:
        for i in range(max(1, h)):
            t = i / max(1, h - 1)
            col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
            pygame.draw.line(surf, col, (x, y + i), (x + w, y + i))
    else:
        for i in range(max(1, w)):
            t = i / max(1, w - 1)
            col = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
            pygame.draw.line(surf, col, (x + i, y), (x + i, y + h))


def panel(surf, rect, color=(25, 30, 50), border=(90, 110, 160), alpha=225, radius=10):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    if border:
        pygame.draw.rect(s, (*border, 255), (0, 0, rect[2], rect[3]), 2, border_radius=radius)
    surf.blit(s, (rect[0], rect[1]))


def button(surf, rect, label, hover=False, selected=False, coin_icon=False, font_size=22):
    x, y, w, h = rect
    col = (70, 120, 210) if selected else ((55, 70, 115) if hover else (40, 50, 85))
    if selected:
        col = (85, 145, 235)
    pygame.draw.rect(surf, col, rect, border_radius=8)
    pygame.draw.rect(surf, (140, 175, 240) if (hover or selected) else (85, 100, 145), rect, 2, border_radius=8)
    text(surf, label, x + w // 2, y + h // 2, font_size, WHITE, "center", bold=True)
    if coin_icon:
        pygame.draw.circle(surf, GOLD, (x + 18, y + h // 2), 7)
        pygame.draw.circle(surf, (200, 150, 30), (x + 18, y + h // 2), 7, 1)


def draw_coin(surf, x, y, r=9):
    pygame.draw.circle(surf, (200, 150, 25), (x, y), r)
    pygame.draw.circle(surf, GOLD, (x, y), r - 2)
    pygame.draw.line(surf, (200, 150, 25), (x - 3, y - 4), (x - 3, y + 4), 2)


def draw_flag(surf, x, y):
    pygame.draw.line(surf, (230, 230, 235), (x, y - 70), (x, y), 3)
    pygame.draw.polygon(surf, (240, 70, 70), [(x, y - 70), (x + 42, y - 56), (x, y - 42)])
    pygame.draw.circle(surf, GOLD, (x, y - 74), 4)


def draw_spikes(surf, x, y, w=30):
    n = max(1, w // 12)
    sw = w / n
    for i in range(n):
        px = x + i * sw
        pygame.draw.polygon(surf, (200, 205, 215), [(px, y), (px + sw / 2, y - 14), (px + sw, y)])


def draw_runner(surf, rct, skin, facing=1, frame=0, ghost=False):
    """Отрисовывает персонажа в прямоугольнике rct."""
    x, y, w, h = rct
    body = skin.get("body", (60, 120, 220))
    accent = skin.get("accent", (255, 255, 255))
    extra = skin.get("extra", "none")
    if ghost:
        body = tuple(min(255, c + 70) for c in body)
    # ноги
    leg_swing = int(math.sin(frame * 0.35) * 4)
    pygame.draw.rect(surf, (35, 40, 60), (x + 4, y + h - 12, 7, 12))
    pygame.draw.rect(surf, (35, 40, 60), (x + w - 11, y + h - 12, 7, 12))
    pygame.draw.rect(surf, (25, 30, 45), (x + 2 + leg_swing, y + h - 5, 11, 5), border_radius=2)
    pygame.draw.rect(surf, (25, 30, 45), (x + w - 13 - leg_swing, y + h - 5, 11, 5), border_radius=2)
    # тело
    pygame.draw.rect(surf, body, (x + 2, y + 13, w - 4, h - 24), border_radius=5)
    pygame.draw.rect(surf, accent, (x + 2, y + 13, w - 4, 4), border_radius=2)
    # руки
    arm = int(math.sin(frame * 0.35 + 3) * 3)
    pygame.draw.rect(surf, body, (x - 2, y + 17 + arm, 6, 13), border_radius=3)
    pygame.draw.rect(surf, body, (x + w - 4, y + 17 - arm, 6, 13), border_radius=3)
    # голова
    hx = x + w // 2
    hy = y + 9
    pygame.draw.circle(surf, (245, 205, 170), (hx, hy), 9)
    # глаз в сторону движения
    ex = hx + 3 * facing
    pygame.draw.circle(surf, (30, 30, 40), (ex, hy - 1), 2)
    # аксессуар
    if extra == "hood":
        pygame.draw.arc(surf, accent, (hx - 11, hy - 12, 22, 20), 3.14, 6.28, 4)
    elif extra == "mask":
        pygame.draw.rect(surf, body, (hx - 9, hy - 3, 18, 6), border_radius=3)
        pygame.draw.circle(surf, accent, (hx - 3, hy), 1)
        pygame.draw.circle(surf, accent, (hx + 3, hy), 1)
    elif extra == "helmet":
        pygame.draw.arc(surf, accent, (hx - 11, hy - 13, 22, 22), 3.14, 6.28, 5)
        pygame.draw.rect(surf, (40, 50, 70), (hx - 6, hy - 2, 12, 3), border_radius=1)
    elif extra == "cap":
        pygame.draw.rect(surf, accent, (hx - 11, hy - 12, 22, 6), border_radius=3)
        pygame.draw.rect(surf, accent, (hx + (2 * facing) - 2, hy - 9, 11, 3), border_radius=2)
    elif extra == "hat":
        pygame.draw.polygon(surf, body, [(hx - 12, hy - 6), (hx, hy - 24), (hx + 12, hy - 6)])
        pygame.draw.rect(surf, accent, (hx - 12, hy - 8, 24, 3), border_radius=1)
    elif extra == "antenna":
        pygame.draw.line(surf, accent, (hx, hy - 9), (hx, hy - 19), 2)
        pygame.draw.circle(surf, GOLD, (hx, hy - 20), 3)
    elif extra == "crown":
        pygame.draw.polygon(surf, GOLD, [(hx - 10, hy - 10), (hx - 7, hy - 18), (hx - 2, hy - 12),
                                          (hx + 3, hy - 18), (hx + 7, hy - 12), (hx + 10, hy - 18), (hx + 10, hy - 10)])
    elif extra == "horns":
        pygame.draw.polygon(surf, accent, [(hx - 9, hy - 6), (hx - 13, hy - 17), (hx - 4, hy - 10)])
        pygame.draw.polygon(surf, accent, [(hx + 9, hy - 6), (hx + 13, hy - 17), (hx + 4, hy - 10)])
    elif extra == "cape":
        pygame.draw.polygon(surf, accent, [(x + 2, y + 14), (x - 8 - facing * 3, y + h - 6), (x + 8, y + h - 8)])


# --- Звуки (генерируются на лету, без внешних файлов) ---
def _make_wav(freq, dur, volume=0.25, kind="square", slide=0.0):
    rate = 22050
    n = int(rate * dur)
    bio = io.BytesIO()
    try:
        with wave.open(bio, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            frames = bytearray()
            for i in range(n):
                t = i / rate
                f = freq + slide * (i / max(1, n))
                if kind == "square":
                    v = 1.0 if (f * t) % 1.0 < 0.5 else -1.0
                elif kind == "sine":
                    v = math.sin(2 * math.pi * f * t)
                else:
                    v = 2 * ((f * t) % 1.0) - 1
                env = min(1.0, (i / (rate * 0.008))) * min(1.0, (n - i) / (rate * 0.04))
                frames += struct.pack("<h", int(v * volume * 32767 * env))
            w.writeframes(bytes(frames))
        bio.seek(0)
        return pygame.mixer.Sound(fileobj=bio)
    except Exception:
        return None


class Sounds:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.sounds = {
                "jump":  _make_wav(420, 0.12, 0.16, "square", 260),
                "double":_make_wav(620, 0.12, 0.14, "square", 200),
                "coin":  _make_wav(880, 0.09, 0.14, "sine", 440),
                "hit":   _make_wav(180, 0.30, 0.20, "saw", -110),
                "win":   _make_wav(520, 0.45, 0.16, "sine", 520),
                "click": _make_wav(660, 0.05, 0.10, "square"),
                "buy":   _make_wav(760, 0.20, 0.14, "sine", 380),
            }
        except Exception:
            self.sounds = {}

    def play(self, name):
        if not self.enabled:
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass


# --- Сохранение ---
SAVE_NAME = "save.json"


def save_path():
    import sys
    if sys.platform == "android" or os.getenv("ANDROID_ROOT"):
        base = os.getcwd()
    else:
        base = os.getenv("APPDATA") or os.path.expanduser("~") or os.getcwd()
    d = os.path.join(base, "ParkourGame")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        d = base
    return os.path.join(d, SAVE_NAME)


def default_save():
    return {
        "coins": 0,
        "skins": ["classic", "red", "green"],
        "skin": "classic",
        "levels": 1,      # самый высокий открытый уровень
        "cleared": [],
        "endless_best": 0,
        "time_best": None,
        "sound": True,
        "fullscreen": False,
    }


def load_save():
    data = default_save()
    try:
        with open(save_path(), "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            for k, v in loaded.items():
                data[k] = v
    except Exception:
        pass
    if not isinstance(data.get("skins"), list):
        data["skins"] = ["classic", "red", "green"]
    if data["skin"] not in data["skins"]:
        data["skin"] = data["skins"][0]
    return data


def write_save(data):
    try:
        with open(save_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_skin(sid):
    for s in SKINS:
        if s["id"] == sid:
            return s
    return SKINS[0]

# -*- coding: utf-8 -*-
"""Процедурная генерация уровней (60 штук) и бесконечного режима."""
import random

from core import GROUND_Y, THEMES

LEVEL_COUNT = 60


def next_platform(rng, last_x, last_w, last_y, diff):
    """Создаёт следующую платформу после заданной."""
    diff = int(diff)
    gap = rng.randint(52, int(88 + min(80, diff * 1.6)))
    w = rng.randint(max(72, 158 - diff), max(96, 224 - diff // 2))
    x = last_x + last_w + gap
    y = max(285, min(GROUND_Y, last_y + rng.randint(-62, 62)))
    kind = "normal"
    r = rng.random()
    if diff >= 8 and r < 0.16:
        kind = "move"
    elif diff >= 16 and r < 0.28:
        kind = "crumble"
    return {
        "x": x, "y": y, "w": w, "h": 620 - y, "kind": kind,
        "dx": 0, "prev_x": x, "timer": -1, "gone": False,
        "phase": rng.random() * 6.28, "move_range": rng.randint(30, 75),
    }


def make_level(n):
    """Детерминированный уровень n (1..LEVEL_COUNT)."""
    rng = random.Random(9001 + n * 7919)
    diff = min(60, n)
    theme = THEMES[(n - 1) % len(THEMES)]
    platforms = [{
        "x": -80, "y": GROUND_Y, "w": 340, "h": 200, "kind": "normal",
        "dx": 0, "prev_x": -80, "timer": -1, "gone": False,
        "phase": 0, "move_range": 0,
    }]
    count = 8 + min(14, n // 3)
    last = platforms[0]
    for _ in range(count):
        last = next_platform(rng, last["x"], last["w"], last["y"], diff)
        platforms.append(last)
    # Финишная платформа
    fin = next_platform(rng, last["x"], last["w"], last["y"], diff)
    fin["kind"] = "finish"
    fin["w"] = max(fin["w"], 150)
    platforms.append(fin)

    spikes = []
    coins = []
    spike_chance = min(0.55, 0.08 + n * 0.008)
    for i, p in enumerate(platforms):
        if i == 0 or p["kind"] == "finish" or p["gone"]:
            continue
        if p["w"] > 95 and rng.random() < spike_chance:
            sw = 26 if p["kind"] != "move" else 20
            sx = p["x"] + rng.randint(10, max(11, int(p["w"] - sw - 10)))
            spikes.append({"x": sx, "y": p["y"], "w": sw, "h": 14,
                           "base_x": sx, "platform": p})
        cnum = 1 + (1 if rng.random() < 0.5 else 0) + (1 if n > 20 and rng.random() < 0.4 else 0)
        for j in range(cnum):
            cx = p["x"] + p["w"] * (j + 1) / (cnum + 1)
            coins.append({"x": cx, "y": p["y"] - 42, "got": False, "phase": rng.random() * 6.28})

    return {
        "number": n,
        "theme": theme,
        "platforms": platforms,
        "spikes": spikes,
        "coins": coins,
        "finish_x": fin["x"] + fin["w"] - 60,
        "finish_y": fin["y"],
        "endless": False,
    }


def endless_chunk(rng, last, diff, out_spikes, out_coins, start_index):
    """Добавляет одну платформу в бесконечный уровень."""
    p = next_platform(rng, last["x"], last["w"], last["y"], min(60, diff))
    p["index"] = start_index
    if p["w"] > 100 and rng.random() < min(0.5, 0.12 + diff * 0.007):
        sw = 24
        sx = p["x"] + rng.randint(8, max(9, int(p["w"] - sw - 8)))
        out_spikes.append({"x": sx, "y": p["y"], "w": sw, "h": 14,
                           "base_x": sx, "platform": p})
    for j in range(1 + (1 if rng.random() < 0.5 else 0)):
        out_coins.append({"x": p["x"] + p["w"] * (j + 1) / 3,
                          "y": p["y"] - 42, "got": False, "phase": rng.random() * 6.28})
    return p


def make_endless(seed=None):
    rng = random.Random(seed if seed is not None else random.randint(1, 10 ** 9))
    start = {"x": -80, "y": GROUND_Y, "w": 340, "h": 200, "kind": "normal",
             "dx": 0, "prev_x": -80, "timer": -1, "gone": False,
             "phase": 0, "move_range": 0, "index": 0}
    return {
        "number": 0,
        "theme": THEMES[0],
        "platforms": [start],
        "spikes": [],
        "coins": [],
        "finish_x": None,
        "finish_y": None,
        "endless": True,
        "rng": rng,
        "next_index": 1,
    }


def make_time_trial():
    """Фиксированный скоростной уровень."""
    lv = make_level(12)
    lv["theme"] = THEMES[2]
    lv["number"] = 0
    lv["time_trial"] = True
    return lv

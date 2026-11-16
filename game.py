# -*- coding: utf-8 -*-
"""Основная логика и все экраны игры."""
import math
import os
import random
import sys

import pygame
from pygame.locals import *

from core import (W, H, FPS, GRAVITY, JUMP_V, JUMP2_V, MAX_FALL, MOVE_SPEED,
                  PLAYER_W, PLAYER_H, GROUND_Y, WHITE, BLACK, GOLD, RED, GREEN,
                  CYAN, GREY, DARK, SKINS, button, draw_coin, draw_flag,
                  draw_spikes, draw_runner, font, get_skin, gradient, panel,
                  text, load_save, write_save, Sounds)
from levels import LEVEL_COUNT, make_level, make_endless, endless_chunk, make_time_trial
from hero_asset import load_hero

SPRITE_H = 86
CTRL_LEFT = (16, H - 104, 86, 86)
CTRL_RIGHT = (112, H - 104, 86, 86)
CTRL_JUMP = (W - 132, H - 114, 116, 96)


class Game:
    def __init__(self):
        pygame.init()
        self.mobile = (sys.platform == "android" or "ANDROID_ROOT" in os.environ)
        if self.mobile:
            try:
                info = pygame.display.Info()
                self.real_screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
            except Exception:
                self.real_screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
            self.base = pygame.Surface((W, H))
            self.screen = self.base
            self.scale, self.ox, self.oy = 1.0, 0, 0
            self.calc_scale()
        else:
            self.real_screen = None
            self.base = None
            self.screen = pygame.display.set_mode((W, H))
        self.touch = {"left": False, "right": False, "jump": False}
        pygame.display.set_caption("PARKOUR RUNNER - паркур")
        try:
            self.icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(self.icon, (60, 120, 220), (4, 4, 24, 24), border_radius=5)
            pygame.display.set_icon(self.icon)
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.save = load_save()
        self.snd = Sounds()
        self.snd.enabled = bool(self.save.get("sound", True))
        try:
            self.hero = load_hero()
        except Exception:
            self.hero = None
        self.hero_left = pygame.transform.flip(self.hero, True, False) if self.hero else None
        self.state = "menu"
        self.prev_state = "menu"
        self.buttons = []
        self.sel = 0
        self.mouse = (0, 0)
        self.click = False
        self.running = True
        self.t = 0.0
        self.dt = 1.0 / FPS
        self.level = None
        self.player = None
        self.mode = "level"
        self.cam = 0
        self.run_coins = 0
        self.deaths = 0
        self.run_time = 0.0
        self.combo = 0
        self.jump_req = False
        self.msg = ""
        self.msg_t = 0.0
        self.shake = 0
        self.confirm_reset = False
        self._sky = {}
        self.set_fullscreen(bool(self.save.get("fullscreen", False)))

    # ---------- служебное ----------
    def calc_scale(self):
        if not self.mobile:
            return
        sw, sh = self.real_screen.get_size()
        self.scale = min(sw / W, sh / H)
        self.ox = int((sw - W * self.scale) / 2)
        self.oy = int((sh - H * self.scale) / 2)

    def to_base(self, pos):
        if not self.mobile:
            return pos
        return ((pos[0] - self.ox) / self.scale, (pos[1] - self.oy) / self.scale)

    def present(self):
        if self.mobile:
            big = pygame.transform.smoothscale(self.base, (int(W * self.scale), int(H * self.scale)))
            self.real_screen.fill((0, 0, 0))
            self.real_screen.blit(big, (self.ox, self.oy))
        pygame.display.flip()

    def set_fullscreen(self, on):
        if self.mobile:
            return
        try:
            self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN if on else 0)
            self.save["fullscreen"] = on
        except Exception:
            pass

    def say(self, s, dur=1.8):
        self.msg = s
        self.msg_t = dur

    def add_btn(self, rect, label, action, value=None, **kw):
        self.buttons.append({"rect": rect, "label": label, "action": action,
                             "value": value, **kw})

    def do(self, action, value=None):
        self.snd.play("click")
        if action == "state":
            self.state = value
            self.sel = 0
        elif action == "play_level":
            self.start_level(value)
        elif action == "endless":
            self.start_endless()
        elif action == "time":
            self.start_time_trial()
        elif action == "buy":
            self.buy_skin(value)
        elif action == "wear":
            self.save["skin"] = value
            write_save(self.save)
            self.say("Скин надет: " + get_skin(value)["name"])
        elif action == "sound":
            self.save["sound"] = not self.save.get("sound", True)
            self.snd.enabled = self.save["sound"]
            write_save(self.save)
        elif action == "fullscreen":
            self.set_fullscreen(not self.save.get("fullscreen", False))
            write_save(self.save)
        elif action == "reset":
            if not self.confirm_reset:
                self.confirm_reset = True
                self.say("Нажми ещё раз для сброса прогресса", 3)
            else:
                from core import default_save
                self.save = default_save()
                write_save(self.save)
                self.confirm_reset = False
                self.say("Прогресс сброшен")
        elif action == "resume":
            self.state = "play"
        elif action == "restart":
            if self.mode == "level":
                self.start_level(self.level["number"])
            elif self.mode == "endless":
                self.start_endless()
            else:
                self.start_time_trial()
        elif action == "quit":
            self.running = False
        elif action == "next_level":
            n = min(LEVEL_COUNT, self.level["number"] + 1)
            self.start_level(n)
        elif action == "menu":
            self.state = "menu"
            self.sel = 0

    def buy_skin(self, sid):
        sk = get_skin(sid)
        if sid in self.save["skins"]:
            self.save["skin"] = sid
            self.say("Скин надет: " + sk["name"])
        elif self.save["coins"] >= sk["price"]:
            self.save["coins"] -= sk["price"]
            self.save["skins"].append(sid)
            self.save["skin"] = sid
            self.snd.play("buy")
            self.say("Куплено: " + sk["name"])
        else:
            self.say("Не хватает монет! Нужно " + str(sk["price"]), 2)
        write_save(self.save)

    # ---------- запуск режимов ----------
    def init_run(self):
        self.player = {"x": 60, "y": GROUND_Y - PLAYER_H, "w": PLAYER_W, "h": PLAYER_H,
                       "vx": 0, "vy": 0, "on_ground": True, "jumps": 0,
                       "standing": None, "facing": 1, "frame": 0, "invuln": 0}
        self.cam = 0
        self.run_coins = 0
        self.deaths = 0
        self.run_time = 0.0
        self.cam = 0
        self.shake = 0
        for p in self.level["platforms"]:
            p["base_x"] = p["x"]
        self.jump_req = False

    def start_level(self, n):
        self.level = make_level(max(1, min(LEVEL_COUNT, n)))
        self.mode = "level"
        self.init_run()
        self.state = "play"

    def start_endless(self):
        self.level = make_endless()
        self.mode = "endless"
        self.init_run()
        self.state = "play"

    def start_time_trial(self):
        self.level = make_time_trial()
        self.mode = "time"
        self.init_run()
        self.state = "play"

    # ---------- события ----------
    def touch_at(self, pos):
        """Возвращает имя нажатой сенсорной кнопки или None."""
        for name, r in (("left", CTRL_LEFT), ("right", CTRL_RIGHT), ("jump", CTRL_JUMP)):
            if pygame.Rect(r).collidepoint(pos):
                return name
        return None

    def events(self):
        self.click = False
        for e in pygame.event.get():
            if e.type == QUIT:
                self.running = False
            elif e.type == MOUSEMOTION:
                self.mouse = self.to_base(e.pos)
                if self.mobile and self.state == "play":
                    held = self.touch_at(self.mouse) if getattr(e, "buttons", (0,)) and e.buttons[0] else None
                    for k in ("left", "right", "jump"):
                        self.touch[k] = (held == k)
            elif e.type == MOUSEBUTTONDOWN:
                self.mouse = self.to_base(e.pos)
                if self.mobile and self.state == "play":
                    k = self.touch_at(self.mouse)
                    if k:
                        self.touch[k] = True
                        if k == "jump":
                            self.jump_req = True
                else:
                    self.click = True
            elif e.type == MOUSEBUTTONUP:
                if self.mobile:
                    k = self.touch_at(self.to_base(e.pos))
                    if k:
                        self.touch[k] = False
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    if self.state == "play":
                        self.state = "pause"
                    elif self.state == "pause":
                        self.state = "play"
                    elif self.state in ("levels", "skins", "settings", "about"):
                        self.state = "menu"
                    elif self.state == "menu":
                        self.running = False
                elif e.key in (K_SPACE, K_RETURN):
                    if self.state == "play" and e.key == K_SPACE:
                        self.jump_req = True
                    elif self.state != "play":
                        self.activate_sel()
                elif e.key in (K_UP, K_w):
                    if self.state == "play":
                        self.jump_req = True
                    else:
                        self.sel = (self.sel - 1) % max(1, len(self.buttons))
                elif e.key in (K_DOWN, K_s):
                    self.sel = (self.sel + 1) % max(1, len(self.buttons))
                elif e.key == K_LEFT:
                    self.sel = max(0, self.sel - 1)
                elif e.key == K_RIGHT:
                    self.sel = min(max(0, len(self.buttons) - 1), self.sel + 1)
                elif e.key == K_p and self.state in ("play", "pause"):
                    self.state = "pause" if self.state == "play" else "play"
                elif e.key == K_r and self.state in ("play", "pause", "dead", "complete"):
                    self.do("restart")

    def activate_sel(self):
        if self.buttons and 0 <= self.sel < len(self.buttons):
            b = self.buttons[self.sel]
            self.do(b["action"], b.get("value"))

    # ---------- обновление ----------
    def update(self):
        self.t += self.dt
        if self.click:
            for b in self.buttons:
                if pygame.Rect(b["rect"]).collidepoint(self.mouse):
                    self.do(b["action"], b.get("value"))
                    break
        if self.msg_t > 0:
            self.msg_t -= self.dt
        if self.shake > 0:
            self.shake -= self.dt
        if self.state == "play":
            self.update_play()
        elif self.state == "dead":
            pass

    def update_play(self):
        p = self.player
        lv = self.level
        self.run_time += self.dt
        keys = pygame.key.get_pressed()
        move = 0
        if keys[K_LEFT] or keys[K_a] or self.touch["left"]:
            move -= 1
        if keys[K_RIGHT] or keys[K_d] or self.touch["right"]:
            move += 1
        if move:
            p["facing"] = move
        p["vx"] = move * MOVE_SPEED
        p["frame"] += abs(move) * 0.35 + (1 if not p["on_ground"] else 0)

        # прыжок
        if self.jump_req:
            if p["jumps"] < 2:
                if p["jumps"] == 0:
                    p["vy"] = JUMP_V
                    self.snd.play("jump")
                else:
                    p["vy"] = JUMP2_V
                    self.snd.play("double")
                    self.puff(p["x"] + p["w"] / 2, p["y"] + p["h"])
                p["jumps"] += 1
                p["on_ground"] = False
            self.jump_req = False

        # платформы
        for pl in lv["platforms"]:
            pl["prev_x"] = pl["x"]
            if pl["kind"] == "move" and not pl["gone"]:
                if "base_x" not in pl:
                    pl["base_x"] = pl["x"]
                pl["x"] = pl["base_x"] + math.sin(self.t * 1.3 + pl["phase"]) * pl["move_range"]
            if pl["timer"] is not None and pl["timer"] >= 0:
                pl["timer"] -= self.dt
                if pl["timer"] < 0:
                    pl["gone"] = True
                    if p["standing"] is pl:
                        p["standing"] = None

        if p["standing"] is not None and not p["standing"].get("gone", False):
            p["x"] += p["standing"]["x"] - p["standing"]["prev_x"]

        # гравитация
        p["vy"] += GRAVITY
        if p["vy"] > MAX_FALL:
            p["vy"] = MAX_FALL
        old_y = p["y"]
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["on_ground"] = False
        p["standing"] = None

        if p["vy"] >= 0:
            for pl in lv["platforms"]:
                if pl.get("gone"):
                    continue
                if p["x"] + p["w"] > pl["x"] and p["x"] < pl["x"] + pl["w"]:
                    if old_y + p["h"] <= pl["y"] + 8 and p["y"] + p["h"] >= pl["y"]:
                        p["y"] = pl["y"] - p["h"]
                        p["vy"] = 0
                        p["on_ground"] = True
                        p["jumps"] = 0
                        p["standing"] = pl
                        if pl["kind"] == "crumble" and (pl["timer"] is None or pl["timer"] < 0):
                            pl["timer"] = 0.55
                        break

        # шипы
        for sp in lv["spikes"]:
            pl = sp.get("platform")
            if isinstance(pl, dict):
                sp["x"] = sp["base_x"] + (pl["x"] - pl.get("base_x", pl["x"]))
            if p["invuln"] <= 0 and self.rect_hit(p, sp, -4, -4):
                self.die()
                return

        # монеты
        for c in lv["coins"]:
            if c["got"]:
                continue
            if abs(p["x"] + p["w"] / 2 - c["x"]) < 20 and abs(p["y"] + p["h"] / 2 - c["y"]) < 28:
                c["got"] = True
                self.run_coins += 1
                self.combo += 1
                self.snd.play("coin")

        # бесконечный режим: генерация вперёд и очистка позади
        if lv["endless"]:
            last = lv["platforms"][-1]
            while last["x"] < p["x"] + W + 500:
                pl = endless_chunk(lv["rng"], last, 2 + lv["next_index"] * 0.32,
                                   lv["spikes"], lv["coins"], lv["next_index"])
                pl["base_x"] = pl["x"]
                lv["platforms"].append(pl)
                lv["next_index"] += 1
                last = pl
            if len(lv["platforms"]) > 40:
                cut = lv["platforms"][:12]
                lv["platforms"] = lv["platforms"][12:]
                lv["spikes"] = [s for s in lv["spikes"]
                                if not (isinstance(s.get("platform"), dict) and s["platform"] in cut)]
                lv["coins"] = [c for c in lv["coins"] if c["x"] > p["x"] - 200]

        # смерть / финиш
        if p["y"] > H + 120:
            self.die()
            return
        if p["invuln"] > 0:
            p["invuln"] -= self.dt
        if not lv["endless"] and p["x"] > lv["finish_x"] and p["on_ground"]:
            self.complete()

        target = max(0, int(p["x"] - 230))
        self.cam += (target - self.cam) * min(1.0, 12 * self.dt)

    def rect_hit(self, a, b, padx=0, pady=0):
        return (a["x"] + padx < b["x"] + b["w"] and
                a["x"] + a["w"] - padx > b["x"] and
                a["y"] + pady < b["y"] + b["h"] and
                a["y"] + a["h"] - pady > b["y"])

    def die(self):
        self.snd.play("hit")
        self.deaths += 1
        self.shake = 0.35
        self.combo = 0
        if self.mode == "endless":
            self.save["coins"] = self.save.get("coins", 0) + self.run_coins
            d = int(max(0, self.player["x"] - 60) / 10)
            if d > self.save.get("endless_best", 0):
                self.save["endless_best"] = d
            write_save(self.save)
            self.end_score = d
        self.state = "dead"
        self.sel = 0

    def complete(self):
        self.snd.play("win")
        bonus = 40 + self.level["number"] * 4 + max(0, 30 - int(self.run_time))
        self.save["coins"] += self.run_coins + bonus
        n = self.level["number"]
        if n not in self.save["cleared"]:
            self.save["cleared"].append(n)
        if self.save.get("levels", 1) < min(LEVEL_COUNT, n + 1):
            self.save["levels"] = min(LEVEL_COUNT, n + 1)
        if self.mode == "time":
            if self.save.get("time_best") is None or self.run_time < self.save["time_best"]:
                self.save["time_best"] = round(self.run_time, 2)
                self.say("Новый рекорд!")
        write_save(self.save)
        self.bonus = bonus
        self.state = "complete"
        self.sel = 0

    def puff(self, x, y):
        pass

    # ---------- отрисовка ----------
    def draw(self):
        s = self.screen
        s.fill((10, 12, 24))
        self.buttons = []
        if self.state == "play":
            self.draw_play(s)
        elif self.state == "menu":
            self.draw_menu(s)
        elif self.state == "levels":
            self.draw_levels(s)
        elif self.state == "skins":
            self.draw_skins(s)
        elif self.state == "settings":
            self.draw_settings(s)
        elif self.state == "pause":
            self.draw_play(s)
            self.overlay(s)
            text(s, "ПАУЗА", W // 2, 175, 48, WHITE, "center", True)
            self.menu_buttons(s, [("Продолжить", "resume"), ("Заново", "restart"),
                                  ("В меню", "menu")], 260)
        elif self.state == "dead":
            self.draw_play(s)
            self.overlay(s)
            text(s, "ТЫ УПАЛ!", W // 2, 150, 46, RED, "center", True)
            if self.mode == "endless":
                text(s, "Результат: " + str(getattr(self, "end_score", 0)), W // 2, 210, 26, GOLD, "center")
            self.menu_buttons(s, [("Заново", "restart"), ("В меню", "menu")], 270)
        elif self.state == "complete":
            self.draw_play(s)
            self.overlay(s)
            text(s, "УРОВЕНЬ ПРОЙДЕН!", W // 2, 140, 40, GREEN, "center", True)
            text(s, "Монеты: +%d  Бонус: +%d" % (self.run_coins, getattr(self, "bonus", 0)),
                 W // 2, 195, 22, GOLD, "center")
            text(s, "Время: %.1f сек" % self.run_time, W // 2, 225, 18, WHITE, "center")
            btns = [("Заново", "restart"), ("В меню", "menu")]
            if self.mode == "level" and self.level["number"] < LEVEL_COUNT:
                btns.insert(0, ("Следующий уровень", "next_level"))
            self.menu_buttons(s, btns, 265)
        if self.msg_t > 0:
            a = min(1.0, self.msg_t * 2)
            m = pygame.Surface((W, 44), pygame.SRCALPHA)
            m.fill((0, 0, 0, int(150 * a)))
            s.blit(m, (0, H - 44))
            text(s, self.msg, W // 2, H - 30, 19, WHITE, "center", True)
        self.present()

    def overlay(self, s):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((0, 0, 0, 175))
        s.blit(o, (0, 0))

    def menu_buttons(self, s, items, y0, spacing=54):
        for i, (label, action, *rest) in enumerate(items):
            r = (W // 2 - 130, y0 + i * spacing, 260, 44)
            self.add_btn(r, label, action, rest[0] if rest else None)
            button(s, r, label, self.mouse in self.rect_obj(r), i == self.sel)

    def rect_obj(self, r):
        return pygame.Rect(r)

    def in_rect(self, r):
        return pygame.Rect(r).collidepoint(self.mouse)

    def sky(self, theme):
        key = theme["name"]
        if key not in self._sky:
            surf = pygame.Surface((W, H))
            gradient(surf, (0, 0, W, H), theme["sky1"], theme["sky2"])
            self._sky[key] = surf
        return self._sky[key]

    def draw_bg(self, s, theme, cam=0):
        s.blit(self.sky(theme), (0, 0))
        # облака
        for i in range(6):
            cx = (i * 230 - cam * 0.15) % (W + 200) - 100
            cy = 70 + (i % 3) * 55
            pygame.draw.ellipse(s, (255, 255, 255, 90), (cx, cy, 90, 26))
            pygame.draw.ellipse(s, (255, 255, 255, 90), (cx + 25, cy - 16, 60, 32))
        # холмы
        for layer, (col, speed, base, amp) in enumerate([
            (theme["hill2"], 0.22, 430, 55), (theme["hill"], 0.4, 470, 40)]):
            pts = [(0, H)]
            for x in range(0, W + 40, 40):
                yy = base + math.sin((x + cam * speed) * 0.006 + layer * 2) * amp
                pts.append((x, yy))
            pts.append((W, H))
            pygame.draw.polygon(s, col, pts)

    def draw_play(self, s):
        lv = self.level
        if lv is None:
            return
        self.draw_bg(s, lv["theme"], self.cam)
        sh = random.uniform(-3, 3) if self.shake > 0 else 0
        off = int(sh)
        cam = self.cam
        # платформы
        for pl in lv["platforms"]:
            if pl.get("gone") or pl["x"] + pl["w"] < cam - 60 or pl["x"] > cam + W + 60:
                continue
            x, y = int(pl["x"] - cam + off), int(pl["y"] + off)
            col = lv["theme"]["plat"]
            if pl["kind"] == "move":
                col = tuple(min(255, c + 30) for c in col)
            if pl["kind"] == "finish":
                col = (90, 160, 100)
            pygame.draw.rect(s, col, (x, y, pl["w"], pl["h"]))
            pygame.draw.rect(s, lv["theme"]["top"], (x, y, pl["w"], 9))
            pygame.draw.rect(s, (0, 0, 0, 55), (x, y + 9, pl["w"], 4))
            if pl["kind"] == "move":
                for i in (-1, 1):
                    pygame.draw.polygon(s, WHITE, [(x + pl["w"] // 2 + i * 6 - 3, y - 12),
                                                   (x + pl["w"] // 2 + i * 6 + 3, y - 12),
                                                   (x + pl["w"] // 2 + i * 6, y - 18)])
            if pl["kind"] == "crumble" and pl["timer"] is not None and pl["timer"] >= 0:
                for i in range(3):
                    pygame.draw.line(s, (40, 30, 30), (x + pl["w"] * i / 3, y + 9),
                                     (x + pl["w"] * (i + 0.7) / 3, y + 30), 2)

        # шипы
        for sp in lv["spikes"]:
            if sp["x"] > cam + W or sp["x"] < cam - 50:
                continue
            draw_spikes(s, int(sp["x"] - cam + off), int(sp["y"] + off), sp["w"])
        # монеты
        for c in lv["coins"]:
            if c["got"] or c["x"] < cam - 30 or c["x"] > cam + W + 30:
                continue
            bob = math.sin(self.t * 4 + c["phase"]) * 4
            draw_coin(s, int(c["x"] - cam + off), int(c["y"] + bob + off))
        # флаг
        if not lv["endless"]:
            draw_flag(s, int(lv["finish_x"] - cam + off), int(lv["finish_y"] + off))

        # игрок (фотография)
        p = self.player
        px = int(p["x"] - cam + off)
        py = int(p["y"] + off)
        sk = get_skin(self.save["skin"])
        img = self.hero if p["facing"] > 0 else self.hero_left
        if img:
            iw = max(1, int(SPRITE_H * img.get_width() / img.get_height()))
            spr = pygame.transform.smoothscale(img, (iw, SPRITE_H))
            sx = px + p["w"] // 2 - iw // 2
            sy = py + p["h"] - SPRITE_H + 4
            if p["invuln"] > 0 and int(self.t * 14) % 2 == 0:
                spr = spr.copy()
                spr.fill((255, 80, 80, 110), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(spr, (sx, sy))
            # эффект скина
            if sk["extra"] == "crown":
                pygame.draw.polygon(s, GOLD, [(sx + iw // 2 - 8, sy - 2), (sx + iw // 2 - 5, sy - 10),
                                              (sx + iw // 2, sy - 4), (sx + iw // 2 + 5, sy - 10),
                                              (sx + iw // 2 + 8, sy - 2)])
            elif sk["extra"] == "antenna":
                pygame.draw.line(s, sk["accent"], (sx + iw // 2, sy - 2), (sx + iw // 2, sy - 14), 2)
                pygame.draw.circle(s, GOLD, (sx + iw // 2, sy - 15), 3)
            elif sk["extra"] == "horns":
                pygame.draw.polygon(s, sk["accent"], [(sx + 4, sy + 6), (sx - 2, sy - 6), (sx + 12, sy + 4)])
                pygame.draw.polygon(s, sk["accent"], [(sx + iw - 4, sy + 6), (sx + iw + 2, sy - 6), (sx + iw - 12, sy + 4)])
            elif sk["extra"] == "cape":
                pygame.draw.polygon(s, sk["accent"], [(sx + 3, sy + 28), (sx - 14 - p["facing"] * 4, sy + SPRITE_H - 6),
                                                      (sx + 10, sy + SPRITE_H - 10)])
            if sk["id"] not in ("classic", "red", "green"):
                pygame.draw.rect(s, sk["accent"], (sx, sy + SPRITE_H - 5, iw, 3))
        else:
            draw_runner(s, (px, py, p["w"], p["h"]), sk, p["facing"], p["frame"])

        # HUD
        panel(s, (10, 10, 210, 42), alpha=170)
        draw_coin(s, 28, 31, 8)
        text(s, str(self.save["coins"] + self.run_coins), 44, 20, 18, WHITE, bold=True)
        text(s, "Ур. " + str(lv["number"]) if not lv["endless"] else "БЕСКОНЕЧНЫЙ",
             118, 20, 16, WHITE, bold=True)
        text(s, "Смерти: " + str(self.deaths), 118, 36, 13, GREY)
        panel(s, (W - 200, 10, 190, 42), alpha=170)
        if self.mode == "time":
            text(s, "%.2f сек" % self.run_time, W - 105, 20, 20, GOLD, "center", True)
            b = self.save.get("time_best")
            text(s, "Рекорд: " + (("%.2f" % b) if b else "-"), W - 105, 38, 13, WHITE, "center")
        elif self.mode == "endless":
            text(s, "Дистанция: %d" % int(max(0, p["x"] - 60) / 10), W - 105, 18, 18, GOLD, "center", True)
            text(s, "Рекорд: " + str(self.save.get("endless_best", 0)), W - 105, 37, 13, WHITE, "center")
        else:
            text(s, "%.1f сек" % self.run_time, W - 105, 20, 18, WHITE, "center", True)
        if self.mobile:
            self.draw_touch(s)
        else:
            text(s, "Space - прыжок (x2)", W // 2, H - 26, 14, (200, 205, 220), "center")

    def draw_touch(self, s):
        for name, r in (("left", CTRL_LEFT), ("right", CTRL_RIGHT), ("jump", CTRL_JUMP)):
            col = (70, 120, 210) if self.touch[name] else (45, 60, 95)
            pygame.draw.circle(s, (*col, 200), (r[0] + r[2] // 2, r[1] + r[3] // 2),
                               min(r[2], r[3]) // 2)
            pygame.draw.circle(s, (150, 185, 240), (r[0] + r[2] // 2, r[1] + r[3] // 2),
                               min(r[2], r[3]) // 2, 2)
        text(s, "◀", CTRL_LEFT[0] + 43, CTRL_LEFT[1] + 43, 34, WHITE, "center", True)
        text(s, "▶", CTRL_RIGHT[0] + 43, CTRL_RIGHT[1] + 43, 34, WHITE, "center", True)
        text(s, "ПРЫЖОК", CTRL_JUMP[0] + 58, CTRL_JUMP[1] + 48, 17, WHITE, "center", True)

    def draw_menu(self, s):
        theme = [t for t in __import__("core").THEMES][int(self.t * 0.15) % 6]
        self.draw_bg(s, theme, self.t * 40)
        # декоративные платформы
        for i in range(5):
            x = (i * 220 - self.t * 55) % (W + 220) - 110
            y = 500 + (i % 2) * 30
            pygame.draw.rect(s, (45, 60, 90), (x, y, 150, 100))
            pygame.draw.rect(s, (110, 190, 130), (x, y, 150, 8))
        panel(s, (W // 2 - 265, 60, 530, 480), color=(15, 20, 40), border=(80, 110, 175), alpha=205)
        # портрет
        if self.hero:
            ph = 110
            pw = int(ph * self.hero.get_width() / self.hero.get_height())
            p = pygame.transform.smoothscale(self.hero, (pw, ph))
            s.blit(p, (W // 2 - 235, 78))
            pygame.draw.rect(s, (90, 130, 200), (W // 2 - 237, 76, pw + 4, ph + 4), 2)
        text(s, "PARKOUR RUNNER", W // 2 + 20, 100, 38, WHITE, "center", True)
        text(s, "Паркур с героем с фотографии", W // 2 + 20, 135, 15, CYAN, "center")
        draw_coin(s, W // 2 + 100, 170, 9)
        text(s, str(self.save["coins"]), W // 2 + 116, 159, 18, GOLD, bold=True)
        items = [
            ("ИГРАТЬ УРОВНИ (" + str(LEVEL_COUNT) + ")", "state", "levels"),
            ("БЕСКОНЕЧНЫЙ РЕЖИМ", "endless", None),
            ("НА ВРЕМЯ", "time", None),
            ("СКИНЫ (" + str(len(SKINS)) + ")", "state", "skins"),
            ("НАСТРОЙКИ", "state", "settings"),
            ("ВЫХОД", "quit", None),
        ]
        for i, (label, action, val) in enumerate(items):
            r = (W // 2 - 150, 195 + i * 55, 300, 46)
            self.add_btn(r, label, action, val)
            button(s, r, label, self.in_rect(r), i == self.sel, font_size=20)
        text(s, "Управление: стрелки / WASD, Space - прыжок (двойной), P - пауза",
             W // 2, H - 22, 13, (190, 200, 220), "center")

    def draw_levels(self, s):
        self.draw_bg(s, __import__("core").THEMES[0], self.t * 20)
        panel(s, (24, 20, W - 48, H - 40), color=(15, 20, 40), border=(80, 110, 175), alpha=230)
        text(s, "ВЫБЕРИ УРОВЕНЬ", W // 2, 48, 30, WHITE, "center", True)
        text(s, "Пройдено: %d из %d" % (len(self.save["cleared"]), LEVEL_COUNT), W // 2, 78, 15, CYAN, "center")
        cols, rows = 10, 6
        bw, bh, gap = 58, 52, 8
        x0 = (W - (cols * bw + (cols - 1) * gap)) // 2
        y0 = 105
        for i in range(LEVEL_COUNT):
            row, col = divmod(i, cols)
            r = (x0 + col * (bw + gap), y0 + row * (bh + gap), bw, bh)
            n = i + 1
            locked = n > self.save.get("levels", 1)
            cleared = n in self.save["cleared"]
            label = str(n)
            self.add_btn(r, label, "play_level", None if locked else n, locked=locked)
            colr = (50, 55, 75) if locked else ((45, 130, 80) if cleared else (55, 75, 125))
            pygame.draw.rect(s, colr, r, border_radius=6)
            pygame.draw.rect(s, (120, 150, 210) if i == self.sel else (80, 95, 140), r, 2, border_radius=6)
            if locked:
                text(s, "X", r[0] + bw // 2, r[1] + bh // 2 - 6, 20, (170, 175, 195), "center", True)
            else:
                text(s, label, r[0] + bw // 2, r[1] + bh // 2 - 5, 20, WHITE, "center", True)
                if cleared:
                    text(s, "★", r[0] + bw // 2, r[1] + bh - 15, 12, GOLD, "center")
            if self.in_rect(r) and not locked:
                text(s, "Уровень " + str(n), W // 2, H - 40, 16, GOLD, "center")
        r = (W // 2 - 90, H - 68, 180, 40)
        self.add_btn(r, "Назад", "state", "menu")
        button(s, r, "Назад", self.in_rect(r), self.sel == LEVEL_COUNT, font_size=18)

    def draw_skins(self, s):
        self.draw_bg(s, __import__("core").THEMES[5], self.t * 20)
        panel(s, (20, 18, W - 40, H - 36), color=(15, 20, 40), border=(80, 110, 175), alpha=230)
        text(s, "СКИНЫ", W // 2, 48, 30, WHITE, "center", True)
        draw_coin(s, W // 2 - 45, 78, 8)
        text(s, str(self.save["coins"]), W // 2 - 28, 68, 18, GOLD, bold=True)
        text(s, "Фотография всегда остаётся персонажем — скин меняет эффект", W // 2, 92, 12, CYAN, "center")
        cols = 6
        bw, bh, gap = 112, 88, 8
        x0 = (W - (cols * bw + (cols - 1) * gap)) // 2
        y0 = 112
        for i, sk in enumerate(SKINS):
            row, col = divmod(i, cols)
            r = (x0 + col * (bw + gap), y0 + row * (bh + gap), bw, bh)
            owned = sk["id"] in self.save["skins"]
            worn = self.save["skin"] == sk["id"]
            self.add_btn(r, sk["name"], "wear" if owned else "buy", sk["id"])
            pygame.draw.rect(s, (55, 130, 80) if worn else ((45, 60, 100) if owned else (48, 45, 70)),
                             r, border_radius=7)
            pygame.draw.rect(s, GOLD if worn else ((100, 130, 190) if owned else (85, 80, 110)),
                             r, 2, border_radius=7)
            # мини-портрет с эффектом скина
            if self.hero:
                ph = 56
                pw = max(1, int(ph * self.hero.get_width() / self.hero.get_height()))
                pic = pygame.transform.smoothscale(self.hero, (pw, ph))
                s.blit(pic, (r[0] + bw // 2 - pw // 2, r[1] + 6))
                if sk["extra"] == "crown":
                    pygame.draw.polygon(s, GOLD, [(r[0] + bw // 2 - 8, r[1] + 6), (r[0] + bw // 2, r[1] - 3),
                                                  (r[0] + bw // 2 + 8, r[1] + 6)])
                elif sk["extra"] == "antenna":
                    pygame.draw.line(s, sk["accent"], (r[0] + bw // 2, r[1] + 6), (r[0] + bw // 2, r[1] - 6), 2)
                    pygame.draw.circle(s, GOLD, (r[0] + bw // 2, r[1] - 7), 3)
                elif sk["extra"] == "horns":
                    pygame.draw.polygon(s, sk["accent"], [(r[0] + bw // 2 - 12, r[1] + 10), (r[0] + bw // 2 - 16, r[1] - 2), (r[0] + bw // 2 - 6, r[1] + 8)])
                    pygame.draw.polygon(s, sk["accent"], [(r[0] + bw // 2 + 12, r[1] + 10), (r[0] + bw // 2 + 16, r[1] - 2), (r[0] + bw // 2 + 6, r[1] + 8)])
                elif sk["extra"] == "cape":
                    pygame.draw.polygon(s, sk["accent"], [(r[0] + bw // 2 - 8, r[1] + 30), (r[0] + bw // 2 - 22, r[1] + 62), (r[0] + bw // 2 - 4, r[1] + 60)])
            text(s, sk["name"], r[0] + bw // 2, r[1] + bh - 22, 12, WHITE, "center", True)
            if not owned:
                draw_coin(s, r[0] + 16, r[1] + 13, 6)
                text(s, str(sk["price"]), r[0] + 25, r[1] + 5, 12, GOLD, bold=True)
            elif worn:
                text(s, "НАДЕТ", r[0] + bw // 2, r[1] + bh - 10, 11, GREEN, "center")
        r = (W // 2 - 90, H - 46, 180, 34)
        self.add_btn(r, "Назад", "state", "menu")
        button(s, r, "Назад", self.in_rect(r), self.sel == len(SKINS), font_size=16)

    def draw_settings(self, s):
        self.draw_bg(s, __import__("core").THEMES[2], self.t * 20)
        panel(s, (W // 2 - 240, 70, 480, 460), color=(15, 20, 40), border=(80, 110, 175), alpha=230)
        text(s, "НАСТРОЙКИ", W // 2, 105, 30, WHITE, "center", True)
        items = [
            ("Звук: " + ("ВКЛ" if self.save.get("sound") else "ВЫКЛ"), "sound", None),
            ("Полный экран: " + ("ВКЛ" if self.save.get("fullscreen") else "ВЫКЛ"), "fullscreen", None),
            ("Сбросить прогресс", "reset", None),
            ("Назад", "state", "menu"),
        ]
        self.menu_buttons(s, items, 165, 60)
        text(s, "Управление:", W // 2, 430, 18, CYAN, "center", True)
        text(s, "← → или A D — движение", W // 2, 460, 15, WHITE, "center")
        text(s, "Space / ↑ / W — прыжок, ещё раз — двойной прыжок", W // 2, 485, 15, WHITE, "center")
        text(s, "P — пауза, Esc — назад, R — перезапуск", W // 2, 510, 15, WHITE, "center")
        text(s, "Прогресс: ур. %d, cleared %d, best endless %d" %
             (self.save.get("levels", 1), len(self.save["cleared"]), self.save.get("endless_best", 0)),
             W // 2, 550, 13, GREY, "center")

    # ---------- цикл ----------
    def run(self):
        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

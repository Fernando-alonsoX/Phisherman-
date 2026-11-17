import math
import random
import pygame
from . import art_items
from . import config as C


class MoneyRain:
    """Efek hujan uang berupa lembar dolar dan koin yang berputar dan bergoyang saat jatuh."""

    def __init__(self, count=70, seed=1):
        self.r = random.Random(seed)
        self.parts = [self._new(True) for _ in range(count)]
        self.bills = {s: art_items.bill_frames(s, 24) for s in (2, 3)}
        self.coins = {s: art_items.coin_frames(s) for s in (2, 3)}

    def _new(self, initial=False):
        r = self.r
        return {
            "x": r.uniform(-20, C.BASE_W + 20),
            "y": r.uniform(-C.BASE_H, C.BASE_H) if initial else r.uniform(-160, -40),
            "vy": r.uniform(130, 340),
            "amp": r.uniform(10, 50),
            "ph": r.uniform(0, 6.28),
            "spin": r.uniform(0.6, 2.4) * r.choice((-1, 1)),
            "t": r.uniform(0, 10),
            "coin": r.random() < 0.28,
            "s": r.choice((2, 2, 3)),
            "front": r.random() < 0.3,
        }

    def update(self, dt):
        for p in self.parts:
            p["y"] += p["vy"] * dt
            p["t"] += dt
            if p["y"] > C.BASE_H + 60:
                p.update(self._new())

    def draw(self, surf, front=None):
        for p in self.parts:
            if front is not None and p["front"] != front:
                continue
            x = p["x"] + math.sin(p["t"] * 2 + p["ph"]) * p["amp"]
            if p["coin"]:
                frames = self.coins[p["s"]]
                img = frames[int(abs(p["t"] * p["spin"] * 6)) % len(frames)]
            else:
                frames = self.bills[p["s"]]
                img = frames[int(p["t"] * p["spin"] * 6) % len(frames)]
            surf.blit(img, img.get_rect(center=(x, p["y"])))

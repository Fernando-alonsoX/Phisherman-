import math
import random
import pygame


class Splash:
    """Efek percikan air berisi cincin riak, tiang air, dan tetesan yang jatuh, dipakai bersama oleh menu dan scene memancing."""

    def __init__(self):
        self.rings = []
        self.drops = []
        self.spouts = []

    def add(self, x, y, power=1.0):
        """Memunculkan percikan baru di titik air dengan kekuatan tertentu."""
        self.rings.append([x, y, 0.0, power])
        self.rings.append([x, y, -0.18, power * 0.8])
        self.spouts.append([x, y, 0.0, power])
        for _ in range(int(9 * power) + 7):
            vx = random.uniform(-150, 150) * (0.6 + 0.5 * power)
            vy = -random.uniform(200, 420) * (0.6 + 0.5 * power)
            self.drops.append([x + random.uniform(-8, 8), y, vx, vy, y + 4, random.choice((3, 4, 5))])

    def ripple(self, x, y, power=0.5):
        """Memunculkan satu cincin riak halus tanpa tetesan."""
        self.rings.append([x, y, 0.0, power])

    def update(self, dt):
        """Menggerakkan semua unsur percikan dan membuang yang sudah selesai."""
        for r in self.rings:
            r[2] += dt
        self.rings = [r for r in self.rings if r[2] < 1.0]
        for s in self.spouts:
            s[2] += dt
        self.spouts = [s for s in self.spouts if s[2] < 0.34]
        for d in self.drops:
            d[3] += 980 * dt
            d[0] += d[2] * dt
            d[1] += d[3] * dt
        self.drops = [d for d in self.drops if d[1] < d[4] or d[3] < 0]

    def draw(self, surf):
        """Menggambar riak, tiang air, dan tetesan di atas permukaan air."""
        for x, y, age, p in self.rings:
            if age < 0:
                continue
            k = age / 1.0
            w = int((26 + 150 * p * k))
            h = max(3, int(w * 0.26))
            a = int(200 * (1 - k) ** 1.5)
            if a <= 0:
                continue
            layer = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (225, 245, 255, a), (2, 2, w, h), 2)
            surf.blit(layer, layer.get_rect(center=(int(x), int(y))))
        for x, y, age, p in self.spouts:
            k = age / 0.34
            hh = int(54 * p * math.sin(math.pi * k))
            ww = int(22 * p * (1 - 0.5 * k)) + 6
            if hh < 3:
                continue
            layer = pygame.Surface((ww + 4, hh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(layer, (235, 250, 255, int(190 * (1 - k))), (2, 2, ww, hh * 2 if hh < 6 else hh * 2))
            layer = layer.subsurface((0, 0, ww + 4, hh + 2)).copy()
            surf.blit(layer, (int(x - ww // 2 - 2), int(y - hh)))
        for x, y, vx, vy, floor, sz in self.drops:
            pygame.draw.rect(surf, (236, 250, 255), (int(x), int(y), sz, sz))
            pygame.draw.rect(surf, (150, 205, 245), (int(x), int(y) + sz - 1, sz, 1))

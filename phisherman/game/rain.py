import math
import random
import pygame


class RainWindow:
    """Hujan beranimasi di dalam kaca jendela dengan tetes jatuh miring percikan di ambang dan kilat sesekali."""

    def __init__(self, rect, count=34, seed=3):
        self.rect = pygame.Rect(rect)
        self.rs = random.Random(seed)
        self.drops = [[self.rs.uniform(0, self.rect.w), self.rs.uniform(0, self.rect.h), self.rs.uniform(240, 420), self.rs.choice((8, 10, 12))] for _ in range(count)]
        self.streaks = [[self.rs.uniform(4, self.rect.w - 4), self.rs.uniform(0, self.rect.h), self.rs.uniform(14, 30), self.rs.uniform(0, 6)] for _ in range(5)]
        self.t = 0.0
        self.flash = 0.0
        self.next_flash = self.rs.uniform(5, 9)

    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt * 2.2)
        self.next_flash -= dt
        if self.next_flash <= 0:
            self.flash = 1.0
            self.next_flash = self.rs.uniform(6, 12)
        for d in self.drops:
            d[0] -= d[2] * dt * 0.16
            d[1] += d[2] * dt
            if d[1] > self.rect.h or d[0] < -10:
                d[0] = self.rs.uniform(0, self.rect.w + 20)
                d[1] = -12
        for s in self.streaks:
            s[1] += dt * 14
            if s[1] > self.rect.h + 10:
                s[1] = -s[2]
                s[0] = self.rs.uniform(4, self.rect.w - 4)

    def draw(self, surf):
        old = surf.get_clip()
        surf.set_clip(self.rect.clip(old) if old else self.rect)
        r = self.rect
        for x, y, v, ln in self.drops:
            a = (r.x + x, r.y + y)
            pygame.draw.line(surf, (150, 185, 235), a, (a[0] - ln * 0.4, a[1] + ln), 2)
        for x, y, ln, ph in self.streaks:
            pygame.draw.line(surf, (120, 150, 210), (r.x + x, r.y + y), (r.x + x + math.sin(self.t + ph) * 1.5, r.y + y + ln), 1)
        if self.flash > 0:
            fl = pygame.Surface(r.size, pygame.SRCALPHA)
            fl.fill((220, 230, 255, int(150 * self.flash)))
            surf.blit(fl, r.topleft)
        surf.set_clip(old)

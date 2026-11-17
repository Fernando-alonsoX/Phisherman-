import math
import pygame
from .base import Scene
from .. import ui, pixelfont, art_items
from ..assets import PRELOAD
from .. import config as C


class BootScene(Scene):
    """Layar pemuatan yang membuat semua ilustrasi dan memuat model AI sebelum masuk menu."""

    exit_button = False

    def __init__(self, app):
        super().__init__(app)
        self.tasks = [lambda n=n: app.assets.get(n) for n in PRELOAD]
        for pose, expr in (("sit", "tired"), ("aha", "wide"), ("type", "smirk"), ("huddle", "cry")):
            self.tasks.append(lambda p=pose, x=expr: app.assets.man(p, x))
        for expr in ("tired", "wide", "smirk", "sad", "happy", "shock", "cry"):
            self.tasks.append(lambda x=expr: app.assets.portrait(x, 120))
            self.tasks.append(lambda x=expr: app.assets.portrait(x, 96))
        self.total = len(self.tasks)
        self.done = 0
        self.t = 0.0
        self.go = False
        self.face = -1.0

    def enter(self):
        self.app.adapter.load_async()

    def update(self, dt):
        self.t += dt
        want = -1.0 if math.cos(self.t * 1.7) < 0 else 1.0
        self.face += (want - self.face) * min(1.0, dt * 9)
        if self.tasks:
            self.tasks.pop(0)()
            self.done += 1
        elif self.t > 1.6 and self.app.adapter.status != "loading" and not self.go:
            self.go = True
            self.app.go_login()

    def draw(self, surf):
        for y in range(C.BASE_H):
            t = y / C.BASE_H
            surf.fill((int(6 + 20 * t), int(14 + 50 * t), int(44 + 70 * t)), (0, y, C.BASE_W, 1))
        title = pixelfont.render("PHISHERMAN", 9, grad=((255, 255, 255), (150, 210, 255)), outline=(8, 20, 64), shadow=(1, 1, (4, 10, 40)))
        surf.blit(title, title.get_rect(center=(C.BASE_W // 2, 280 + math.sin(self.t * 3) * 4)))
        fish = art_items.envelope_fish(5)
        w, h = fish.get_size()
        k = abs(self.face)
        if k < 0.98:
            fish = pygame.transform.scale(fish, (max(4, int(w * k)), h))
        if self.face > 0:
            fish = pygame.transform.flip(fish, True, False)
        surf.blit(fish, fish.get_rect(center=(C.BASE_W // 2 + math.sin(self.t * 1.7) * 190, 400 + math.sin(self.t * 3.4) * 8)))
        bar = pygame.Rect(0, 0, 520, 26)
        bar.center = (C.BASE_W // 2, 500)
        pygame.draw.rect(surf, (10, 20, 40), bar.inflate(6, 6), border_radius=8)
        pygame.draw.rect(surf, (232, 238, 248), bar, border_radius=6)
        p = self.done / max(1, self.total)
        fill = pygame.Rect(bar.x + 2, bar.y + 2, int((bar.w - 4) * p), bar.h - 4)
        if fill.w > 2:
            pygame.draw.rect(surf, (60, 190, 80), fill, border_radius=5)
            pygame.draw.rect(surf, (140, 230, 150), (fill.x, fill.y, fill.w, fill.h // 2), border_radius=5)
            shine = int((self.t * 220) % (fill.w + 60)) - 30
            pygame.draw.rect(surf, (210, 255, 215), (fill.x + max(0, min(fill.w - 8, shine)), fill.y, 8, fill.h), border_radius=4)
        ui.draw_text(surf, "Preparing illustrations and AI model...", ui.font(18), (220, 236, 255), (C.BASE_W // 2, 546), "midtop")
        ui.draw_text(surf, self.app.adapter.label, ui.font(15), (150, 190, 235), (C.BASE_W // 2, 580), "midtop")

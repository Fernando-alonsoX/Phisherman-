import math
import pygame
from . import ui, icons
from . import config as C

BOX = pygame.Rect(236, 470, 808, 218)


class DialogBox:
    """Kotak dialog bergaya cutscene dengan nama pembicara avatar ikon efek mesin ketik dan tombol lanjut berdenyut."""

    def __init__(self, app, name, icon="shield", box=BOX):
        self.app = app
        self.name = name
        self.icon = icon
        self.box = pygame.Rect(box)
        self.tw = None
        self.play_t = 0.0
        self.font = ui.font(22)

    def say(self, text):
        self.tw = ui.Typewriter(text, self.font, self.box.w - 214, (30, 36, 52), cps=34, on_tick=lambda: self.app.sfx.play("type"))
        self.play_t = 0.0

    @property
    def finished(self):
        return self.tw is not None and self.tw.finished

    def play_rect(self):
        return pygame.Rect(0, 0, 60, 60).move(self.box.right - 82, self.box.bottom - 82)

    def event(self, e):
        """Mengembalikan True saat pemain meminta lanjut setelah teks selesai tampil."""
        if self.tw is None:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.tw.finished and self.play_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                return True
            if self.box.collidepoint(e.pos) and not self.tw.finished:
                self.tw.skip()
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.tw.finished:
                self.app.sfx.play("click")
                return True
            self.tw.skip()
        return False

    def update(self, dt):
        if self.tw is None:
            return
        self.tw.update(dt)
        if self.tw.finished:
            self.play_t += dt
            if self.play_rect().collidepoint(self.app.mouse):
                ui.HOT["hand"] = True

    def draw(self, surf):
        box = self.box
        sh = pygame.Surface((box.w + 40, box.h + 40), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 70), (20, 28, box.w, box.h), border_radius=22)
        surf.blit(sh, (box.x - 20, box.y - 20))
        surf.blit(ui.glass(box.w, box.h, 20, (190, 220, 252), 232, True), box)
        pygame.draw.rect(surf, (255, 255, 255), box.inflate(-8, -8), 1, border_radius=17)
        lf = ui.font(18, True)
        tag = pygame.Rect(box.x + 96, box.y - 16, max(110, lf.size(self.name)[0] + 36), 32)
        pygame.draw.rect(surf, (20, 40, 84), tag, border_radius=10)
        pygame.draw.rect(surf, (255, 206, 80), tag, 2, border_radius=10)
        ui.draw_text(surf, self.name, lf, (255, 226, 120), tag.center, "center")
        if self.tw:
            self.tw.draw(surf, (box.x + 106, box.y + 28))
        c = (box.x + 28, box.bottom - 46)
        shd = pygame.Surface((132, 132), pygame.SRCALPHA)
        pygame.draw.circle(shd, (0, 0, 0, 80), (66, 70), 62)
        surf.blit(shd, shd.get_rect(center=(c[0], c[1] + 6)))
        pygame.draw.circle(surf, (20, 40, 84), c, 56)
        pygame.draw.circle(surf, (60, 130, 220), c, 50)
        pygame.draw.circle(surf, (255, 255, 255), c, 56, 3)
        icons.draw_icon(surf, self.icon, c, 62, (255, 255, 255))
        if self.finished:
            pr = self.play_rect()
            hover = pr.collidepoint(self.app.mouse)
            pulse = 0.5 + 0.5 * math.sin(self.play_t * 5)
            ring = pygame.Surface((110, 110), pygame.SRCALPHA)
            pygame.draw.circle(ring, (120, 190, 255, int(60 + 80 * pulse)), (55, 55), int(32 + 14 * pulse), 4)
            surf.blit(ring, ring.get_rect(center=pr.center))
            k = min(1.0, self.play_t / 0.25)
            d = int(60 * (1 + 0.1 * (1 if hover else 0)) * (0.6 + 0.4 * k))
            img = pygame.transform.smoothscale(ui.button_surface(60, 60, "primary", "hover" if hover else "normal", 30), (d, d))
            surf.blit(img, img.get_rect(center=pr.center))
            icons.draw_icon(surf, "play", (pr.centerx + 2, pr.centery), int(32 * k + 4), (255, 255, 255))

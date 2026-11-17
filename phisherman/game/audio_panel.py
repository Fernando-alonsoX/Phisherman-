import pygame
from . import ui, icons

PANEL_W = 316
PANEL_H = 214
BTN = 46


class AudioPanel:
    """Tombol speaker di pojok kiri atas yang membuka panel untuk membisukan dan mengatur volume musik serta efek suara."""

    def __init__(self, app):
        self.app = app
        self.open = False
        self.drag = None
        self.hover_main = False
        self.press_main = False
        self.t = 0.0
        self.base = pygame.Rect(18, 14, BTN, BTN)

    def anchor(self):
        """Menentukan posisi tombol agar berdampingan dengan tombol EXIT bila tombol itu tampil."""
        x = 18 + 138 + 10 if self.app.scene.exit_button else 18
        self.base = pygame.Rect(x, 14, BTN, BTN)
        self.panel = pygame.Rect(x, 14 + BTN + 8, PANEL_W, PANEL_H)
        cx = self.panel.x + 8
        cy = self.panel.y + 32
        self.client = pygame.Rect(cx, cy, PANEL_W - 16, PANEL_H - 40)
        self.rows = []
        for i, key in enumerate(("music", "sfx")):
            ry = self.client.y + 14 + i * 74
            toggle = pygame.Rect(self.client.x + 14, ry + 6, 40, 40)
            track = pygame.Rect(self.client.x + 70, ry + 34, 160, 8)
            self.rows.append((key, toggle, track, ry))

    def close(self):
        self.open = False
        self.drag = None

    def state(self, key):
        """Mengambil nilai aktif dan volume untuk musik atau efek suara."""
        s = self.app.sfx
        if key == "music":
            return s.music_on, s.music_vol
        return s.sfx_on, s.sfx_vol

    def set_value(self, key, v):
        """Mengubah volume musik atau efek suara pada rentang 0 sampai 1."""
        s = self.app.sfx
        v = max(0.0, min(1.0, v))
        if key == "music":
            s.music_vol = v
            if v > 0:
                s.music_on = True
        else:
            s.sfx_vol = v
            if v > 0:
                s.sfx_on = True

    def toggle(self, key):
        """Membisukan atau menyalakan kembali musik atau efek suara."""
        s = self.app.sfx
        if key == "music":
            s.music_on = not s.music_on
            if s.music_on and s.music_vol <= 0:
                s.music_vol = 0.5
        else:
            s.sfx_on = not s.sfx_on
            if s.sfx_on and s.sfx_vol <= 0:
                s.sfx_vol = 0.5

    def value_at(self, track, x):
        return (x - track.x) / track.w

    def event(self, e):
        """Memproses klik dan geser slider lalu mengembalikan True bila peristiwa ditangani panel."""
        self.anchor()
        s = self.app.sfx
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and self.open:
            self.close()
            return True
        if e.type == pygame.MOUSEMOTION:
            self.hover_main = self.base.collidepoint(e.pos)
            if self.drag:
                for key, toggle, track, ry in self.rows:
                    if key == self.drag:
                        self.set_value(key, self.value_at(track, e.pos[0]))
                return True
            return self.open and self.panel.collidepoint(e.pos)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.base.collidepoint(e.pos):
                self.press_main = True
                return True
            if self.open:
                if self.panel.collidepoint(e.pos):
                    for key, toggle, track, ry in self.rows:
                        if toggle.collidepoint(e.pos):
                            self.toggle(key)
                            s.play("click")
                            s.save_settings()
                            return True
                        if track.inflate(24, 30).collidepoint(e.pos):
                            self.drag = key
                            self.set_value(key, self.value_at(track, e.pos[0]))
                            return True
                    return True
                self.close()
            return False
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.press_main:
                self.press_main = False
                if self.base.collidepoint(e.pos):
                    self.open = not self.open
                    s.play("click")
                return True
            if self.drag:
                key = self.drag
                self.drag = None
                s.save_settings()
                if key == "sfx":
                    s.play("coin")
                return True
        return False

    def update(self, dt):
        self.t += dt
        self.anchor()
        m = self.app.mouse
        if self.base.collidepoint(m) or (self.open and self.panel.collidepoint(m)):
            ui.HOT["hand"] = True

    def all_off(self):
        s = self.app.sfx
        return s.muted or (not s.music_on and not s.sfx_on)

    def draw_slider(self, surf, key, toggle, track, ry):
        on, vol = self.state(key)
        shown = vol if on else 0.0
        label = "Music" if key == "music" else "Sound Effects"
        hover = toggle.collidepoint(self.app.mouse)
        img = ui.button_surface(toggle.w, toggle.h, "primary" if on else "default", "hover" if hover else "normal")
        surf.blit(img, toggle)
        name = ("note" if key == "music" else "speaker") if on else "speaker_off"
        col = (255, 255, 255) if on else (70, 80, 100)
        icons.draw_icon(surf, name, toggle.center, 24, col)
        ui.draw_text(surf, label, ui.font(15, True), (30, 50, 90), (track.x, ry + 8))
        ui.draw_text(surf, f"{int(round(shown * 100))}%", ui.font(14, True), (50, 90, 150), (track.right + 40, ry + 8), "topright")
        pygame.draw.rect(surf, (200, 212, 232), track, border_radius=4)
        pygame.draw.rect(surf, (120, 140, 175), track, 1, border_radius=4)
        fw = int(track.w * shown)
        if fw > 0:
            pygame.draw.rect(surf, (60, 150, 235) if on else (150, 160, 180), (track.x, track.y, fw, track.h), border_radius=4)
            pygame.draw.rect(surf, (170, 215, 255), (track.x, track.y, fw, 3), border_radius=2)
        kx = track.x + fw
        kc = (kx, track.centery)
        pygame.draw.circle(surf, (60, 80, 120), kc, 11)
        pygame.draw.circle(surf, (245, 249, 255), kc, 10)
        pygame.draw.circle(surf, (110, 160, 225) if on else (170, 178, 192), kc, 6)

    def draw(self, surf):
        self.anchor()
        state = "pressed" if self.press_main and self.hover_main else ("hover" if self.hover_main else "normal")
        img = ui.button_surface(self.base.w, self.base.h, "dark", state)
        surf.blit(img, self.base)
        name = "speaker_off" if self.all_off() else "speaker"
        icons.draw_icon(surf, name, self.base.center, 28, (255, 255, 255))
        if not self.open:
            return
        ui.draw_window(surf, self.panel, "Sound Settings", controls=False, icon=icons.icon_fn("speaker"))
        pygame.draw.rect(surf, (240, 245, 253), self.client)
        for key, toggle, track, ry in self.rows:
            self.draw_slider(surf, key, toggle, track, ry)
        ui.draw_text(surf, "F9 to mute all sounds", ui.font(12), (100, 114, 140), (self.client.centerx, self.client.bottom - 14), "midbottom")

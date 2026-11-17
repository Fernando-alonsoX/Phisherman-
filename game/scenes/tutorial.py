import math
import pygame
from .compose import ComposeScene
from .. import ui, icons, scoring
from .. import config as C

SAMPLE_SUBJECT = "Account verification needed"
SAMPLE_BODY = "Hello Sir,\nWe noticed unusual activity on your company account and it will be suspended within 24 hours. Please open the attached invoice and confirm your details right away to keep your access.\nThank you"

STEPS = [
    {
        "title": "Tiga bagian utama email",
        "text": "Setiap email phishing harus punya Opening (salam pembuka), Body (isi pesan) dan Closing (salam penutup). Tambahkan juga Subject di kolom subjek.",
        "focus": "window",
    },
    {
        "title": "Isi pesan minimal 25 kata",
        "text": "Bagian Body harus berisi minimal 25 kata supaya terlihat meyakinkan. Pantau penghitung kata pada chip Body di bawah. Chip akan hijau saat bagian itu lengkap.",
        "focus": "body",
    },
    {
        "title": "Unggah file lampiran",
        "text": "Klik tombol Attach untuk membuka File Explorer, pilih satu file lalu tekan Upload. Lampiran bersifat opsional dan hanya boleh satu file per email. File bisa saja berisi malware, tapi kamu baru tahu hasilnya saat AI selesai memeriksa.",
        "focus": "attach",
    },
    {
        "title": "Cara mendapat poin",
        "text": "Email yang lolos dari AI memberi poin dan uang. Lampiran malware yang lolos memberi bonus besar, tetapi jika terdeteksi poinmu berkurang banyak.",
        "focus": "points",
    },
]


class TutorialScene(ComposeScene):
    """Tutorial sebelum permainan dengan tata letak sama seperti layar menulis email disertai sorotan area dan tombol Next di kanan bawah."""

    counter = False

    def __init__(self, app):
        super().__init__(app)
        self.step = 0
        self.step_t = 0.0
        self.subject.text = SAMPLE_SUBJECT
        self.subject.focus = False
        self.area.text = SAMPLE_BODY
        self.area.focus = False
        self.area.enabled = False
        self.area.cursor = self.area.anchor = 0
        self.btn_next = ui.Button((C.BASE_W - 236, C.BASE_H - 84, 210, 54), "Next", self.next_step, "primary", icon=icons.icon_fn("play"), size=20)
        self.btn_next.pulse = True
        self.apply_step()

    def apply_step(self):
        self.step_t = 0.0
        f = STEPS[self.step]["focus"]
        self.attachment = "Invoice_October.pdf" if f in ("attach", "points") else None
        self.explorer.open = f == "attach"
        if self.explorer.open:
            self.explorer.t = 0.0
            self.explorer.sel = 0
            self.explorer.upload.enabled = True
        self.btn_next.label = "Start Mission" if self.step == len(STEPS) - 1 else "Next"
        self.app.sfx.play("pop")

    def next_step(self):
        if self.step + 1 >= len(STEPS):
            self.app.goto(lambda: ComposeScene(self.app))
            return
        self.step += 1
        self.apply_step()

    def event(self, e):
        self.btn_next.handle_event(e, self.app)
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_RIGHT):
            self.app.sfx.play("click")
            self.next_step()

    def update(self, dt):
        self.t += dt
        self.step_t += dt
        self.rain.update(dt)
        self.btn_next.update(dt, self.app.mouse)
        from ..validator import check_email
        self.status = check_email(self.area.text, self.subject.text)
        self.explorer.t += dt if self.explorer.open else 0
        self.chip_pop = max(0.0, getattr(self, "chip_pop", 0.0) - dt * 3)

    def focus_rect(self):
        f = STEPS[self.step]["focus"]
        c = self.client
        if f == "window":
            return self.win.inflate(10, 10)
        if f == "body":
            return pygame.Rect(c.x + 256, c.bottom - 54, 176, 48)
        if f == "attach":
            return pygame.Rect(c.x + 4, c.y + 94, c.w - 8, 36)
        return pygame.Rect(c.x + 4, c.bottom - 60, 440, 58)

    def draw_points(self, surf):
        r = pygame.Rect(0, 0, 560, 300)
        r.center = (self.scr.centerx - 40, self.scr.centery - 30)
        cl = ui.draw_window(surf, r, "Scoring Guide", icon=lambda s, c, z, col: icons.draw_icon(s, "star", c, z, (255, 224, 110)))
        pygame.draw.rect(surf, (248, 250, 254), cl)
        rows = (
            ("Not detected", "Clean file or no file", f"+{C.BASE_POINTS} pts", f"+${C.REWARD}", (50, 160, 90)),
            ("Not detected", "Malware attached", f"+{C.BASE_POINTS + C.MALWARE_BONUS_POINTS} pts", f"+${C.REWARD + C.MALWARE_BONUS_MONEY}", (226, 160, 20)),
            ("Detected", "Clean file or no file", "0 pts", "$0", (110, 124, 150)),
            ("Detected", "Malware attached", f"-{C.MALWARE_PENALTY} pts", "$0", (210, 70, 60)),
        )
        ui.draw_text(surf, "Result", ui.font(13, True), (90, 104, 132), (cl.x + 16, cl.y + 10))
        ui.draw_text(surf, "Points", ui.font(13, True), (90, 104, 132), (cl.x + 330, cl.y + 10))
        ui.draw_text(surf, "Money", ui.font(13, True), (90, 104, 132), (cl.x + 430, cl.y + 10))
        for i, (a, b, pts, mon, col) in enumerate(rows):
            y = cl.y + 34 + i * 58
            k = min(1.0, max(0.0, (self.step_t - 0.15 * i) / 0.25))
            if k <= 0:
                continue
            row = pygame.Rect(cl.x + 8, y, cl.w - 16, 50)
            pygame.draw.rect(surf, (236, 241, 249), row, border_radius=8)
            pygame.draw.rect(surf, col, (row.x, row.y + 6, 5, row.h - 12), border_radius=3)
            ui.draw_text(surf, a, ui.font(16, True), (30, 44, 80), (row.x + 18, row.y + 6))
            ui.draw_text(surf, b, ui.font(13), (96, 110, 140), (row.x + 18, row.y + 28))
            ui.draw_text(surf, pts, ui.font(20, True), col, (cl.x + 322, row.centery), "midleft")
            ui.draw_text(surf, mon, ui.font(20, True), (40, 130, 70) if mon != "$0" else (110, 124, 150), (cl.x + 422, row.centery), "midleft")

    def draw_overlay(self):
        fr = self.focus_rect()
        dim = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        dim.fill((4, 8, 24, 170))
        pygame.draw.rect(dim, (0, 0, 0, 0), fr.inflate(10, 10), border_radius=12)
        return dim, fr

    def draw(self, surf):
        self.draw_room(surf)
        self.draw_screen(surf)
        if STEPS[self.step]["focus"] == "points":
            dim = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
            dim.fill((4, 8, 24, 170))
            surf.blit(dim, (0, 0))
            self.draw_points(surf)
        else:
            dim, fr = self.draw_overlay()
            surf.blit(dim, (0, 0))
            pulse = 0.5 + 0.5 * math.sin(self.t * 5)
            ring = fr.inflate(10 + int(4 * pulse), 10 + int(4 * pulse))
            pygame.draw.rect(surf, (255, 214, 80), ring, 3, border_radius=12)
            pygame.draw.rect(surf, (255, 255, 255), fr.inflate(6, 6), 1, border_radius=10)
        self.draw_card(surf)
        self.btn_next.draw(surf)

    def draw_card(self, surf):
        s = STEPS[self.step]
        r = pygame.Rect(40, C.BASE_H - 130, 960, 112)
        k = min(1.0, self.step_t / 0.25)
        r.y += int((1 - k) * 30)
        surf.blit(ui.glass(r.w, r.h, 16, (30, 60, 120), 240), r)
        pygame.draw.rect(surf, (255, 214, 80), r, 2, border_radius=16)
        n = f"{self.step + 1}/{len(STEPS)}"
        badge = pygame.Rect(r.x + 16, r.y + 14, 64, 28)
        pygame.draw.rect(surf, (255, 214, 80), badge, border_radius=14)
        ui.draw_text(surf, n, ui.font(16, True), (60, 36, 4), badge.center, "center")
        ui.draw_text(surf, s["title"], ui.font(22, True), (255, 255, 255), (badge.right + 14, badge.centery), "midleft", shadow=(0, 20, 60))
        for i, ln in enumerate(ui.wrap_lines(ui.font(16), s["text"], r.w - 40)[:3]):
            ui.draw_text(surf, ln, ui.font(16), (222, 236, 255), (r.x + 20, r.y + 52 + i * 21))

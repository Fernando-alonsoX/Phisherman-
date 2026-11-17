import math
import random
import pygame
from .base import Scene
from ..dialog import DialogBox
from .. import ui, icons, art_ui, art_char, scoring
from ..canvas import radial_glow
from ..validator import find_patterns
from .. import config as C


def ease_out(k):
    """Kurva gerak cepat di awal lalu melambat."""
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


class BuildingScene(Scene):
    """Adegan pembuka verifikasi berupa sudut rendah gedung YuBeatEm yang miring ke atas dengan teks Beberapa jam kemudian."""

    hud = "money"
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.img = app.assets.get("building")
        self.rs = random.Random(8)
        self.drops = [[self.rs.uniform(0, C.BASE_W), self.rs.uniform(0, C.BASE_H), self.rs.uniform(500, 800)] for _ in range(70)]
        self.panel = pygame.Rect(0, 0, 720, 96)
        self.panel.midbottom = (C.BASE_W // 2, C.BASE_H - 40)
        self.tw = None
        self.play_t = 0.0
        self.vig = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        for i in range(50):
            a = int(150 * (1 - i / 50) ** 2)
            pygame.draw.rect(self.vig, (2, 4, 14, a), (i * 3, i * 3, C.BASE_W - i * 6, C.BASE_H - i * 6), 3)

    def backdrop_art(self):
        return self.img.subsurface((0, 180, C.BASE_W, 720))

    def go_next(self):
        from .verify import OfficeScene
        self.app.goto(lambda: OfficeScene(self.app))

    def event(self, e):
        if self.tw is None:
            return
        if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
            if not self.tw.finished:
                self.tw.skip()
            else:
                self.app.sfx.play("click")
                self.go_next()

    def update(self, dt):
        self.t += dt
        for d in self.drops:
            d[1] += d[2] * dt
            d[0] -= d[2] * dt * 0.12
            if d[1] > C.BASE_H or d[0] < 0:
                d[0] = self.rs.uniform(0, C.BASE_W + 100)
                d[1] = -20
        if self.t > 3.2 and self.tw is None:
            self.tw = ui.Typewriter("Beberapa jam kemudian...", ui.font(30, True), self.panel.w - 80, (30, 36, 52), cps=14, on_tick=lambda: self.app.sfx.play("type"))
            self.app.sfx.play("pop")
        if self.tw:
            self.tw.update(dt)
            if self.tw.finished:
                self.play_t += dt
                if self.play_t > 4.0:
                    self.go_next()

    def draw(self, surf):
        off = 380 + (20 - 380) * ease_out(self.t / 6.5)
        surf.blit(self.img, (0, 0), (0, int(off), C.BASE_W, C.BASE_H))
        for x, y, v in self.drops:
            pygame.draw.line(surf, (150, 185, 235), (x, y), (x - 6, y + 16), 1)
        beacon_y = 64 - off
        if -20 < beacon_y < C.BASE_H:
            a = 0.5 + 0.5 * math.sin(self.t * 4)
            g = radial_glow(40, (255, 40, 40), a)
            surf.blit(g, g.get_rect(center=(640, beacon_y)), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.vig, (0, 0))
        if self.tw is not None:
            k = min(1.0, self.tw.finished and 1.0 or 0.0)
            surf.blit(ui.glass(self.panel.w, self.panel.h, 18, (190, 220, 252), 232, True), self.panel)
            pygame.draw.rect(surf, (255, 255, 255), self.panel.inflate(-8, -8), 1, border_radius=14)
            self.tw.draw(surf, (self.panel.x + 40, self.panel.y + 26))
            if self.tw.finished:
                pulse = 0.5 + 0.5 * math.sin(self.play_t * 5)
                icons.draw_icon(surf, "play", (self.panel.right - 36, self.panel.centery + int(pulse * 3)), 26, (40, 100, 190))
        bars = pygame.Surface((C.BASE_W, 36))
        bars.fill((0, 0, 0))
        surf.blit(bars, (0, 0))
        surf.blit(bars, (0, C.BASE_H - 36))


class OfficeScene(Scene):
    """Adegan kantor keamanan siber saat alarm menyala karena phishing terdeteksi lengkap dengan analis dan dialog."""

    hud = "money"
    exit_kind = "story"

    LINES = [
        "Alarm berbunyi! Sistem mendeteksi pesan-pesan mencurigakan yang masuk ke jaringan YuBeatEm. Modelnya memang dibuat sangat sensitif, jadi hampir semua dari kelima pesan ini ikut tertandai.",
        "Tapi pesan yang lolos dari model pun harus kuperiksa. Aku akan meninjau kelimanya satu per satu, lalu label dariku dipakai untuk melatih ulang model.",
    ]

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.room, self.scr = app.assets.get("office_room")
        self.poses = {p: art_char.back_view_analyst(p, 2) for p in ("sit", "alert")}
        self.dialog = DialogBox(app, "ANALIS KEAMANAN", "shield")
        self.idx = 0
        self.alarm_t = 0.0
        self.flash = 0.0
        self.dialog.say(self.LINES[0])
        self.siren = (628, 63)

    def backdrop_art(self):
        return self.room

    def enter(self):
        self.app.sfx.play("alarm")

    def go_review(self):
        self.app.goto(lambda: ReviewScene(self.app))

    def event(self, e):
        if self.dialog.event(e):
            self.flash = 1.0
            if self.idx + 1 >= len(self.LINES):
                self.go_review()
            else:
                self.idx += 1
                self.dialog.say(self.LINES[self.idx])
                self.app.sfx.play("pop")

    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt * 2.6)
        self.dialog.update(dt)
        self.alarm_t += dt
        if self.alarm_t > 1.6 and self.t < 7:
            self.alarm_t = 0.0
            self.app.sfx.play("alarm", 0.6)

    def draw_alert_screen(self, surf):
        scr = self.scr
        old = surf.get_clip()
        surf.set_clip(scr)
        pulse = 0.5 + 0.5 * math.sin(self.t * 6)
        for y in range(0, scr.h, 4):
            t = y / scr.h
            pygame.draw.rect(surf, (int(40 + 40 * pulse * (1 - t)), 10, 16), (scr.x, scr.y + y, scr.w, 4))
        cx = scr.centerx
        icons.draw_icon(surf, "warning", (cx, scr.y + 77), int(56 + 4 * pulse), (255, 80, 70))
        ui.draw_text(surf, "SECURITY ALERT", ui.mono(26, True), (255, 255, 255), (cx, scr.y + 106), "midtop", shadow=(80, 0, 0))
        ui.draw_text(surf, "5 suspicious emails flagged by MailGuard AI", ui.mono(14), (255, 190, 180), (cx, scr.y + 134), "midtop")
        for i in range(5):
            on = int(self.t * 3) % 5 == i
            px = cx - 56 + i * 28
            icons.draw_icon(surf, "envelope", (px, scr.y + 36), 18, (255, 220, 120) if on else (140, 80, 80))
        mq = "  PHISHING DETECTED  ///  REVIEW REQUIRED  ///  "
        f = ui.mono(13, True)
        w = f.size(mq)[0]
        x = scr.x - int((self.t * 70) % w)
        for k in range(0, 4):
            ui.draw_text(surf, mq, f, (255, 120, 110), (x + k * w, scr.y + 10))
        surf.set_clip(old)

    def draw_side(self, surf):
        r = pygame.Rect(864, 238, 210, 150)
        old = surf.get_clip()
        surf.set_clip(r)
        pygame.draw.rect(surf, (6, 18, 30), r)
        for i in range(4):
            pts = [(r.x + x, r.centery + math.sin(x / 18 + self.t * (2 + i) + i) * (16 + i * 6) - 14 + i * 9) for x in range(0, r.w + 6, 6)]
            pygame.draw.lines(surf, [(80, 220, 240), (255, 120, 110), (120, 240, 160), (255, 220, 120)][i], False, pts, 2)
        surf.set_clip(old)

    def draw(self, surf):
        pulse = 0.5 + 0.5 * math.sin(self.t * 6)
        surf.blit(self.room, (0, 0))
        self.draw_side(surf)
        self.draw_alert_screen(surf)
        pose = "alert" if self.t < 2.6 else "sit"
        img = self.poses[pose]
        bob = abs(math.sin(self.t * 8)) * -6 if pose == "alert" else math.sin(self.t * 1.4) * 2
        surf.blit(img, (585 - img.get_width() // 2, 280 + bob))
        g = radial_glow(260, (255, 40, 40), 0.3 + 0.6 * pulse)
        surf.blit(g, g.get_rect(center=self.siren), special_flags=pygame.BLEND_RGB_ADD)
        ov = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        ov.fill((200, 0, 0, int(34 * pulse)))
        surf.blit(ov, (0, 0))
        self.dialog.draw(surf)
        if self.flash > 0:
            f = pygame.Surface((C.BASE_W, C.BASE_H))
            f.fill((255, 255, 255))
            f.set_alpha(int(200 * self.flash))
            surf.blit(f, (0, 0))


class ReviewScene(Scene):
    """Konsol analis dengan daftar lima email detail pesan dan tombol Phishing atau Legitimate untuk melatih ulang model dengan umpan balik manusia."""

    hud = "money"
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.room, self.scr = app.assets.get("analyst_room")
        self.taskbar = app.assets.get("taskbar")
        self.desktop = app.assets.get("desktop")
        self.rounds = list(app.session.rounds)
        self.sel = 0
        scr = self.scr
        self.win = pygame.Rect(scr.x + 90, scr.y + 8, 790, 424)
        self.client = pygame.Rect(self.win.x + 8, self.win.y + 32, self.win.w - 16, self.win.h - 40)
        c = self.client
        self.list_rect = pygame.Rect(c.x + 8, c.y + 8, 250, c.h - 70)
        self.pane = pygame.Rect(c.x + 266, c.y + 8, c.w - 274, c.h - 70)
        p = self.pane
        self.btn_phish = ui.Button((p.x + 10, p.bottom - 46, 236, 38), "Phishing", lambda: self.label("phishing"), "danger", icon=icons.icon_fn("warning"), size=16)
        self.btn_legit = ui.Button((p.right - 246, p.bottom - 46, 236, 38), "Legitimate", lambda: self.label("legit"), "success", icon=icons.icon_fn("check"), size=16)
        self.btn_submit = ui.Button((c.right - 232, c.bottom - 54, 220, 44), "Submit Labels", self.submit, "primary", icon=icons.icon_fn("shield"), size=16)
        self.btn_cont = ui.Button((0, 0, 220, 42), "Continue", self.go_stats, "primary", icon=icons.icon_fn("play"), size=17)
        self.scroll = 0.0
        self.hover = -1
        self.phase = "review"
        self.train_i = 0
        self.train_t = 0.0
        self.infos = []
        self.done_t = 0.0
        self.pop_t = 0.0
        self.body_cache = {}
        self.hints = [find_patterns(r.text, 5, "en") for r in self.rounds]
        for r in self.rounds:
            if getattr(r, "label", None) not in ("phishing", "legit"):
                r.label = None
        self.apply_btn_state()

    def backdrop_art(self):
        return self.room

    def labeled(self):
        return sum(1 for r in self.rounds if r.label)

    def apply_btn_state(self):
        r = self.rounds[self.sel]
        self.btn_submit.enabled = self.labeled() == len(self.rounds)
        self.btn_submit.pulse = self.btn_submit.enabled
        self.btn_phish.pulse = r.label is None
        self.btn_legit.pulse = r.label is None

    def select(self, i):
        self.sel = max(0, min(len(self.rounds) - 1, int(i)))
        self.scroll = 0.0
        self.pop_t = 0.0
        self.apply_btn_state()

    def label(self, value):
        if self.phase != "review":
            return
        r = self.rounds[self.sel]
        r.label = value
        self.app.sfx.play("coin" if self.labeled() == len(self.rounds) else "confirm")
        nxt = next((i for i in range(len(self.rounds)) if self.rounds[i].label is None), None)
        if nxt is not None:
            self.select(nxt)
        else:
            self.apply_btn_state()

    def submit(self):
        if self.phase != "review" or self.labeled() < len(self.rounds):
            return
        self.phase = "train"
        self.train_i = 0
        self.train_t = 0.0
        self.infos = []
        self.start_train()
        self.app.sfx.play("scan")

    def start_train(self):
        r = self.rounds[self.train_i]
        self.waiting = True
        self.app.adapter.learn_async(r.subject, r.body, r.label == "phishing", self.on_trained)

    def on_trained(self, info):
        self.infos.append(info)
        self.waiting = False

    def go_stats(self):
        from .stats import StatsScene
        self.app.goto(lambda: StatsScene(self.app))

    def event(self, e):
        if self.phase == "done":
            self.btn_cont.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                self.go_stats()
            return
        if self.phase != "review":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.list_rect.collidepoint(e.pos):
            i = int((e.pos[1] - self.list_rect.y - 4) // 62)
            if 0 <= i < len(self.rounds) and i != self.sel:
                self.app.sfx.play("click")
                self.select(i)
                return
        if e.type == pygame.MOUSEWHEEL and self.pane.collidepoint(self.app.mouse):
            self.scroll = max(0, self.scroll - e.y * 30)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_DOWN:
                self.select(self.sel + 1)
            elif e.key == pygame.K_UP:
                self.select(self.sel - 1)
            elif e.key == pygame.K_p:
                self.label("phishing")
            elif e.key == pygame.K_l:
                self.label("legit")
        for b in (self.btn_phish, self.btn_legit, self.btn_submit):
            if b.handle_event(e, self.app):
                return

    def update(self, dt):
        self.t += dt
        self.pop_t += dt
        m = self.app.mouse
        if self.phase == "review":
            for b in (self.btn_phish, self.btn_legit, self.btn_submit):
                b.update(dt, m)
            self.hover = -1
            if self.list_rect.collidepoint(m):
                i = int((m[1] - self.list_rect.y - 4) // 62)
                if 0 <= i < len(self.rounds):
                    self.hover = i
                    ui.HOT["hand"] = True
        elif self.phase == "train":
            self.train_t += dt
            if not self.waiting and self.train_t > 0.7:
                self.train_i += 1
                self.train_t = 0.0
                if self.train_i >= len(self.rounds):
                    self.phase = "done"
                    self.done_t = 0.0
                    self.app.sfx.play("win", 0.7)
                else:
                    self.app.sfx.play("pop")
                    self.start_train()
        elif self.phase == "done":
            self.done_t += dt
            self.btn_cont.update(dt, m)
            self.btn_cont.pulse = True

    def draw_list(self, surf):
        r = self.list_rect
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=6)
        pygame.draw.rect(surf, (150, 166, 196), r, 1, border_radius=6)
        for i, rd in enumerate(self.rounds):
            row = pygame.Rect(r.x + 4, r.y + 4 + i * 62, r.w - 8, 58)
            sel = i == self.sel
            if sel:
                pygame.draw.rect(surf, (214, 232, 255), row, border_radius=8)
                pygame.draw.rect(surf, (70, 130, 214), row, 2, border_radius=8)
            elif i == self.hover:
                pygame.draw.rect(surf, (238, 244, 254), row, border_radius=8)
            icons.draw_icon(surf, "envelope", (row.x + 22, row.y + 20), 24, (70, 110, 180))
            sub = rd.subject if len(rd.subject) <= 22 else rd.subject[:21] + ".."
            ui.draw_text(surf, sub, ui.font(15, True), (24, 40, 78), (row.x + 42, row.y + 6))
            ui.draw_text(surf, rd.sender, ui.font(12), (110, 124, 150), (row.x + 42, row.y + 26))
            flagged = rd.pred_phishing
            tag = pygame.Rect(row.x + 42, row.y + 40, 66, 14)
            pygame.draw.rect(surf, (226, 90, 76) if flagged else (80, 180, 120), tag, border_radius=7)
            ui.draw_text(surf, "FLAGGED" if flagged else "PASSED", ui.font(10, True), (255, 255, 255), tag.center, "center")
            if rd.attachment:
                icons.draw_icon(surf, "paperclip", (row.x + 124, row.y + 47), 14, (110, 124, 150))
            if rd.label:
                lab = pygame.Rect(row.right - 70, row.y + 18, 62, 22)
                col = (210, 70, 60) if rd.label == "phishing" else (50, 160, 90)
                pygame.draw.rect(surf, col, lab, border_radius=11)
                ui.draw_text(surf, "Phishing" if rd.label == "phishing" else "Legit", ui.font(12, True), (255, 255, 255), lab.center, "center")
            else:
                ui.draw_text(surf, "?", ui.font(22, True), (240, 170, 50), (row.right - 30, row.centery), "center")

    def draw_detail(self, surf):
        p = self.pane
        rd = self.rounds[self.sel]
        pygame.draw.rect(surf, (255, 255, 255), p, border_radius=6)
        pygame.draw.rect(surf, (150, 166, 196), p, 1, border_radius=6)
        sub = rd.subject if ui.font(19, True).size(rd.subject)[0] < p.w - 24 else rd.subject[:36] + ".."
        ui.draw_text(surf, sub, ui.font(19, True), (20, 44, 92), (p.x + 12, p.y + 8))
        ui.draw_text(surf, "From", ui.font(13, True), (110, 124, 150), (p.x + 12, p.y + 36))
        ui.draw_text(surf, rd.sender, ui.font(14), (40, 52, 80), (p.x + 60, p.y + 35))
        ui.draw_text(surf, "To", ui.font(13, True), (110, 124, 150), (p.x + 250, p.y + 36))
        ui.draw_text(surf, rd.recipient, ui.font(14), (40, 52, 80), (p.x + 276, p.y + 35))
        ui.draw_text(surf, "File", ui.font(13, True), (110, 124, 150), (p.x + 12, p.y + 62))
        if rd.attachment:
            chip = pygame.Rect(p.x + 60, p.y + 56, 250, 26)
            pygame.draw.rect(surf, (226, 238, 255), chip, border_radius=13)
            pygame.draw.rect(surf, (96, 148, 226), chip, 1, border_radius=13)
            art_ui.draw_file_icon(surf, scoring.file_kind(rd.attachment), (chip.x + 18, chip.centery), 18)
            ui.draw_text(surf, rd.attachment, ui.font(13, True), (24, 48, 100), (chip.x + 34, chip.centery), "midleft")
            ui.draw_text(surf, scoring.file_size(rd.attachment), ui.font(12), (96, 112, 144), (chip.right - 10, chip.centery), "midright")
        else:
            ui.draw_text(surf, "No attachment", ui.font(14), (130, 142, 166), (p.x + 60, p.y + 62))
        flagged = rd.pred_phishing
        pill = pygame.Rect(p.right - 190, p.y + 58, 178, 24)
        pygame.draw.rect(surf, (226, 90, 76) if flagged else (80, 180, 120), pill, border_radius=12)
        ui.draw_text(surf, f"AI: {'FLAGGED' if flagged else 'PASSED'}  {int(round(rd.prob * 100))}%", ui.font(13, True), (255, 255, 255), pill.center, "center")
        body = pygame.Rect(p.x + 10, p.y + 92, p.w - 20, 120)
        pygame.draw.rect(surf, (248, 250, 254), body, border_radius=4)
        pygame.draw.rect(surf, (200, 208, 224), body, 1, border_radius=4)
        key = rd.body
        lines = self.body_cache.get(key)
        if lines is None:
            lines = ui.wrap_lines(ui.font(15), rd.body, body.w - 24)
            self.body_cache[key] = lines
        total = len(lines) * 20
        self.scroll = max(0, min(max(0, total - body.h + 16), self.scroll))
        old = surf.get_clip()
        surf.set_clip(body.inflate(-2, -2))
        for i, ln in enumerate(lines):
            y = body.y + 8 + i * 20 - int(self.scroll)
            if body.y - 20 < y < body.bottom:
                ui.draw_text(surf, ln, ui.font(15), (30, 40, 66), (body.x + 12, y))
        surf.set_clip(old)
        if total > body.h - 16:
            ui.draw_text(surf, "scroll", ui.font(11), (150, 160, 180), (body.right - 8, body.bottom - 6), "bottomright")
        hs = self.hints[self.sel]
        ui.draw_text(surf, "Red flags", ui.font(13, True), (110, 124, 150), (p.x + 12, p.y + 222))
        x = p.x + 84
        if not hs:
            ui.draw_text(surf, "None obvious", ui.font(13), (130, 142, 166), (x, p.y + 222))
        for h in hs[:3]:
            tw = ui.font(12, True).size(h["title"])[0] + 18
            if x + tw > p.right - 8:
                break
            chip = pygame.Rect(x, p.y + 220, tw, 20)
            pygame.draw.rect(surf, (255, 233, 200), chip, border_radius=10)
            pygame.draw.rect(surf, (230, 160, 60), chip, 1, border_radius=10)
            ui.draw_text(surf, h["title"], ui.font(12, True), (140, 80, 10), chip.center, "center")
            x += tw + 6
        rd_label = rd.label
        for b, val in ((self.btn_phish, "phishing"), (self.btn_legit, "legit")):
            b.draw(surf)
            if rd_label == val:
                pygame.draw.rect(surf, (255, 214, 80), b.rect.inflate(8, 8), 3, border_radius=9)

    def draw_bottom(self, surf):
        c = self.client
        y = c.bottom - 56
        pygame.draw.rect(surf, (236, 241, 249), (c.x, y, c.w, 56))
        pygame.draw.line(surf, (190, 200, 218), (c.x, y), (c.right, y))
        n = self.labeled()
        ui.draw_text(surf, f"Labeled {n}/{len(self.rounds)}", ui.font(15, True), (60, 76, 108), (c.x + 16, y + 10))
        bar = pygame.Rect(c.x + 16, y + 34, 300, 10)
        pygame.draw.rect(surf, (214, 222, 236), bar, border_radius=5)
        if n:
            pygame.draw.rect(surf, (70, 170, 100), (bar.x, bar.y, int(bar.w * n / len(self.rounds)), bar.h), border_radius=5)
        hint = "Pick Phishing or Legitimate (keys P / L)" if n < len(self.rounds) else "All labeled. Submit to retrain."
        ui.draw_text(surf, hint, ui.font(12), (110, 124, 150), (c.x + 332, y + 28), "midleft")
        self.btn_submit.draw(surf)

    def draw_train(self, surf):
        scr = self.scr
        dim = pygame.Surface(scr.size, pygame.SRCALPHA)
        dim.fill((0, 0, 0, 130))
        surf.blit(dim, scr.topleft)
        r = pygame.Rect(0, 0, 520, 230)
        r.center = (scr.centerx, scr.centery - 20)
        cl = ui.draw_window(surf, r, "Model Retraining", controls=False, icon=lambda s, c, z, col: icons.draw_icon(s, "retrain", c, z, (255, 255, 255)))
        pygame.draw.rect(surf, (248, 250, 254), cl)
        done = self.phase == "done"
        if done:
            icons.draw_icon(surf, "check", (cl.x + 56, cl.y + 62), 64, (60, 170, 90))
            ui.draw_text(surf, "Model updated", ui.font(24, True), (30, 110, 60), (cl.x + 108, cl.y + 22))
            ui.draw_text(surf, "Your labels have been added to the training data.", ui.font(15), (70, 84, 112), (cl.x + 108, cl.y + 58))
            ok = sum(1 for i in self.infos if i.get("ok"))
            ui.draw_text(surf, f"{ok} of {len(self.infos)} examples learned", ui.font(15, True), (70, 84, 112), (cl.x + 108, cl.y + 84))
            self.btn_cont.rect.midbottom = (cl.centerx, cl.bottom - 14)
            self.btn_cont.draw(surf)
            return
        a = self.t * 6
        for k in range(8):
            ang = a + k * math.tau / 8
            pygame.draw.circle(surf, (70, 130, 214), (cl.x + 56 + int(math.cos(ang) * 22), cl.y + 62 + int(math.sin(ang) * 22)), 3 + (k % 3))
        ui.draw_text(surf, "Retraining the model...", ui.font(22, True), (20, 44, 92), (cl.x + 108, cl.y + 22))
        ui.draw_text(surf, f"Learning example {min(self.train_i + 1, len(self.rounds))} of {len(self.rounds)}", ui.font(15), (70, 84, 112), (cl.x + 108, cl.y + 58))
        bar = pygame.Rect(cl.x + 24, cl.y + 128, cl.w - 48, 20)
        pygame.draw.rect(surf, (214, 222, 236), bar, border_radius=10)
        fr = (self.train_i + min(1.0, self.train_t / 0.7)) / len(self.rounds)
        pygame.draw.rect(surf, (70, 170, 100), (bar.x, bar.y, int(bar.w * min(1.0, fr)), bar.h), border_radius=10)

    def draw(self, surf):
        scr = self.scr
        surf.blit(self.room, (0, 0))
        g = radial_glow(320, (50, 110, 210), 0.3)
        surf.blit(pygame.transform.smoothscale(g, (1500, 900)), (scr.centerx - 750, scr.centery - 450), special_flags=pygame.BLEND_RGB_ADD)
        old = surf.get_clip()
        surf.set_clip(scr)
        surf.blit(self.desktop, scr.topleft)
        ui.draw_window(surf, self.win, f"SOC Console - Email Review ({self.labeled()}/{len(self.rounds)} labeled)", icon=lambda s, c, z, col: icons.draw_icon(s, "shield", c, z, (255, 255, 255)))
        c = self.client
        pygame.draw.rect(surf, (244, 247, 252), c)
        self.draw_list(surf)
        self.draw_detail(surf)
        self.draw_bottom(surf)
        surf.blit(self.taskbar, (scr.x, scr.bottom - 40))
        icons.draw_icon(surf, "shield", (scr.x + 82, scr.bottom - 20), 22, (235, 246, 255))
        for i, name in enumerate(("chevup", "wifi", "speaker")):
            icons.draw_icon(surf, name, (scr.right - 93 + i * 32, scr.bottom - 20), 18, (235, 246, 255))
        if self.phase in ("train", "done"):
            self.draw_train(surf)
        glare = pygame.Surface(scr.size, pygame.SRCALPHA)
        pygame.draw.polygon(glare, (255, 255, 255, 12), [(0, 0), (scr.w * 0.5, 0), (scr.w * 0.2, scr.h), (0, scr.h)])
        surf.blit(glare, scr.topleft)
        surf.set_clip(old)

import math
import random
import threading
import pygame
from .base import Scene
from .. import ui, icons, pixelfont, art_ui, scoring
from ..canvas import mix, radial_glow
from ..validator import find_patterns
from .. import config as C

WIN = pygame.Rect(150, 84, 980, 584)
PURPLE = (190, 130, 255)
GREEN = (60, 205, 120)
YELLOW = (250, 210, 70)
RED = (238, 72, 62)
CYAN = (90, 220, 240)


def gauge_color(p):
    return mix(GREEN, YELLOW, p / 0.5) if p < 0.5 else mix(YELLOW, RED, (p - 0.5) / 0.5)


def build_gauge(radius=130, thick=26):
    """Membuat gambar busur setengah lingkaran bergradasi hijau kuning merah untuk pengukur probabilitas phishing."""
    size = (radius * 2 + 20, radius + 30)
    s = pygame.Surface(size, pygame.SRCALPHA)
    cx, cy = size[0] // 2, radius + 8
    segs = 60
    for i in range(segs):
        a1 = math.pi - math.pi * i / segs
        a2 = math.pi - math.pi * (i + 1) / segs + 0.002
        pts = [
            (cx + math.cos(a1) * radius, cy - math.sin(a1) * radius),
            (cx + math.cos(a2) * radius, cy - math.sin(a2) * radius),
            (cx + math.cos(a2) * (radius - thick), cy - math.sin(a2) * (radius - thick)),
            (cx + math.cos(a1) * (radius - thick), cy - math.sin(a1) * (radius - thick)),
        ]
        pygame.draw.polygon(s, gauge_color(i / segs), pts)
    pygame.draw.arc(s, (230, 250, 255), (cx - radius, cy - radius, radius * 2, radius * 2), 0, math.pi, 2)
    pygame.draw.arc(s, (230, 250, 255), (cx - radius + thick, cy - radius + thick, (radius - thick) * 2, (radius - thick) * 2), 0, math.pi, 2)
    f = ui.font(13, True)
    for v in (0, 25, 50, 75, 100):
        a = math.pi - math.pi * v / 100
        x1, y1 = cx + math.cos(a) * (radius + 4), cy - math.sin(a) * (radius + 4)
        x2, y2 = cx + math.cos(a) * (radius + 12), cy - math.sin(a) * (radius + 12)
        pygame.draw.line(s, (200, 230, 240), (x1, y1), (x2, y2), 2)
    return s, (cx, cy)


class AnalysisScene(Scene):
    """Layar hasil analisis AI bertema ruang server dengan gauge pemindaian pesan pemeriksaan lampiran gacha malware dan rincian poin otomatis."""

    hud = "money"
    counter = True
    exit_kind = "story"

    def __init__(self, app, rd):
        super().__init__(app)
        self.rd = rd
        self.t = 0.0
        self.bg = app.assets.get("cyber_bg")
        self.pred = None
        self.phase = "scan"
        self.phase_t = 0.0
        self.needle = 0.0
        self.shown_prob = 0.0
        self.hints = find_patterns(rd.text, 5, "en")
        self.gauge, self.pivot = build_gauge()
        self.hex = art_ui.hex_pattern(WIN.w, WIN.h)
        self.client = pygame.Rect(WIN.x + 8, WIN.y + 32, WIN.w - 16, WIN.h - 40)
        c = self.client
        self.left = pygame.Rect(c.x + 14, c.y + 12, 440, 300)
        self.right = pygame.Rect(c.x + 468, c.y + 12, 482, 300)
        y = c.y + 324
        self.pat = pygame.Rect(c.x + 14, y, 316, 206)
        self.att = pygame.Rect(c.x + 338, y, 292, 206)
        self.score = pygame.Rect(c.x + 638, y, 312, 206)
        last = len(app.session.rounds) >= C.TOTAL_ROUNDS
        self.btn_next = ui.Button((self.score.x + 12, self.score.bottom - 50, self.score.w - 24, 40), "View Results" if last else "Next Email", self.go_next, "primary", icon=icons.icon_fn("play"), size=17)
        self.btn_next.visible = False
        self.res = None
        self.stamp_t = 0.0
        self.roll_t = 0.0
        self.count_t = 0.0
        self.scan_sfx = False
        self.lines = ui.wrap_lines(ui.mono(14), rd.body.replace("\r", ""), self.left.w - 36)
        self.noise = random.Random(4)
        threading.Thread(target=self._predict, daemon=True).start()

    def _predict(self):
        try:
            self.pred = self.app.adapter.predict(self.rd.subject, self.rd.body)
        except Exception:
            from ..model_adapter import Prediction
            self.pred = Prediction(True, 0.9, "demo")

    def backdrop_art(self):
        return self.bg

    def go_phase(self, name):
        self.phase = name
        self.phase_t = 0.0

    def apply_result(self):
        """Menghitung hasil ronde dari deteksi AI dan gacha malware lalu menerapkannya ke uang poin dan catatan ronde."""
        rd = self.rd
        pred = self.pred
        detected = bool(pred.is_phishing)
        res = scoring.resolve(detected, bool(rd.attachment), bool(rd.malware))
        rd.prob = pred.prob
        rd.pred_phishing = detected
        rd.ai_correct = detected
        self.app.session.apply(rd, res)
        self.app.adapter.record(detected)
        self.res = res
        self.count_t = 0.0
        if res["money"]:
            self.app.hud.gain(res["money"])
        self.app.sfx.play({"jackpot": "win", "pass": "coin", "busted": "lose", "caught": "error"}[res["code"]])
        self.go_phase("result")

    def go_next(self):
        if self.res is None:
            return
        if len(self.app.session.rounds) >= C.TOTAL_ROUNDS:
            from .ending import make_ending
            self.app.goto(lambda: make_ending(self.app))
        else:
            from .compose import ComposeScene
            self.app.goto(lambda: ComposeScene(self.app))

    def event(self, e):
        if self.btn_next.visible:
            self.btn_next.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.sfx.play("click")
                self.go_next()

    def update(self, dt):
        self.t += dt
        self.phase_t += dt
        m = self.app.mouse
        if not self.scan_sfx:
            self.scan_sfx = True
            self.app.sfx.play("scan")
        if self.phase == "scan":
            if self.phase_t > 2.6 and self.pred is not None:
                self.go_phase("verdict")
                self.stamp_t = 0.0
                self.app.sfx.play("alarm" if self.pred.is_phishing else "confirm")
            else:
                self.needle += (self.noise.random() * 0.9 + 0.05 - self.needle) * min(1.0, dt * 9)
        elif self.pred is not None:
            self.needle += (self.pred.prob - self.needle) * min(1.0, dt * 4.5)
            self.shown_prob += (self.pred.prob - self.shown_prob) * min(1.0, dt * 5)
            self.stamp_t += dt
            if self.phase == "verdict" and self.phase_t > 1.4:
                if self.rd.attachment:
                    self.go_phase("gacha")
                    self.roll_t = 0.0
                    self.app.sfx.play("scan")
                else:
                    self.apply_result()
            elif self.phase == "gacha":
                self.roll_t += dt
                if self.roll_t > 1.8:
                    self.apply_result()
        if self.phase == "result":
            self.count_t += dt
            self.btn_next.visible = self.phase_t > 0.9
            self.btn_next.pulse = True
        self.btn_next.update(dt, m)

    def panel(self, surf, r, title):
        pygame.draw.rect(surf, (9, 22, 38), r, border_radius=8)
        surf.blit(self.hex, r.topleft, (r.x - self.client.x + 8, r.y - self.client.y, r.w, r.h))
        pygame.draw.rect(surf, (28, 96, 124), r, 2, border_radius=8)
        pygame.draw.rect(surf, (14, 50, 70), (r.x + 2, r.y + 2, r.w - 4, 28), border_top_left_radius=6, border_top_right_radius=6)
        ui.draw_text(surf, title, ui.mono(14, True), CYAN, (r.x + 14, r.y + 7))

    def draw_left(self, surf):
        r = self.left
        rd = self.rd
        self.panel(surf, r, "INCOMING MESSAGE")
        mf = ui.mono(14)
        rows = (("From", rd.sender), ("To", rd.recipient), ("Subject", rd.subject))
        for i, (lab, val) in enumerate(rows):
            yy = r.y + 40 + i * 20
            ui.draw_text(surf, lab + ":", ui.mono(14, True), (90, 190, 210), (r.x + 16, yy))
            v = val if mf.size(val)[0] < r.w - 110 else val[:34] + ".."
            ui.draw_text(surf, v, mf, (200, 230, 240), (r.x + 92, yy))
        yy = r.y + 102
        ui.draw_text(surf, "Attach:", ui.mono(14, True), (90, 190, 210), (r.x + 16, yy))
        if rd.attachment:
            art_ui.draw_file_icon(surf, scoring.file_kind(rd.attachment), (r.x + 108, yy + 8), 18)
            ui.draw_text(surf, rd.attachment, mf, (255, 214, 120), (r.x + 124, yy))
        else:
            ui.draw_text(surf, "none", mf, (110, 140, 156), (r.x + 92, yy))
        pygame.draw.line(surf, (28, 96, 124), (r.x + 12, r.y + 128), (r.right - 12, r.y + 128))
        lh = 19
        top = r.y + 138
        max_lines = (r.h - 150) // lh
        beam_y = None
        if self.phase == "scan":
            k = (self.phase_t / 1.3) % 1.0
            beam_y = r.y + 36 + k * (r.h - 46)
        old = surf.get_clip()
        surf.set_clip(pygame.Rect(r.x + 4, top - 4, r.w - 8, r.bottom - top - 4))
        for i, ln in enumerate(self.lines[:max_lines]):
            y = top + i * lh
            col = (176, 220, 232)
            if beam_y is not None and y > beam_y:
                col = (70, 110, 128)
            surf.blit(ui.text_surf(mf, ln, col), (r.x + 18, y))
        surf.set_clip(old)
        if len(self.lines) > max_lines:
            ui.draw_text(surf, f"... +{len(self.lines) - max_lines} more lines", ui.mono(12), (90, 150, 170), (r.right - 14, r.bottom - 20), "midright")
        if beam_y is not None:
            b = pygame.Surface((r.w - 8, 26), pygame.SRCALPHA)
            for yy in range(26):
                a = int(110 * (1 - abs(yy - 13) / 13))
                pygame.draw.line(b, (80, 230, 255, a), (0, yy), (r.w, yy))
            surf.blit(b, (r.x + 4, beam_y - 13))
            pygame.draw.line(surf, (160, 250, 255), (r.x + 6, beam_y), (r.right - 6, beam_y), 2)

    def draw_right(self, surf):
        r = self.right
        self.panel(surf, r, "AI ANALYSIS  >  PHISHING PROBABILITY")
        gx = r.centerx - self.pivot[0]
        gy = r.y + 36
        surf.blit(self.gauge, (gx, gy))
        px, py = gx + self.pivot[0], gy + self.pivot[1]
        ang = math.pi - math.pi * max(0.0, min(1.0, self.needle))
        col = gauge_color(self.needle)
        tip = (px + math.cos(ang) * 102, py - math.sin(ang) * 102)
        pygame.draw.line(surf, (4, 10, 20), (px + 2, py + 2), (tip[0] + 2, tip[1] + 2), 7)
        pygame.draw.line(surf, (240, 250, 255), (px, py), tip, 5)
        pygame.draw.circle(surf, (4, 10, 20), (px, py), 15)
        pygame.draw.circle(surf, col, (px, py), 11)
        pygame.draw.circle(surf, (255, 255, 255), (px - 3, py - 3), 3)
        ui.draw_text(surf, "SAFE", ui.font(13, True), GREEN, (gx + 12, py + 8), "topleft")
        ui.draw_text(surf, "PHISHING", ui.font(13, True), RED, (gx + self.gauge.get_width() - 12, py + 8), "topright")
        if self.phase == "scan":
            txt = pixelfont.render("??%", 3, color=(120, 170, 190), outline=(4, 14, 24))
            surf.blit(txt, txt.get_rect(midtop=(r.centerx, py + 14)))
            status = ["Reading the message", "Searching for suspicious patterns", "Calculating probability"][int(self.phase_t * 1.6) % 3] + "." * (int(self.t * 3) % 4)
            ui.draw_text(surf, status, ui.mono(14), CYAN, (r.centerx, py + 48), "midtop")
            bar = pygame.Rect(r.x + 70, py + 72, r.w - 140, 12)
            pygame.draw.rect(surf, (10, 30, 44), bar, border_radius=6)
            pygame.draw.rect(surf, (40, 110, 140), bar, 1, border_radius=6)
            fw = int((bar.w - 4) * min(1.0, self.phase_t / 2.6))
            pygame.draw.rect(surf, CYAN, (bar.x + 2, bar.y + 2, fw, bar.h - 4), border_radius=4)
        else:
            pct = int(round(self.shown_prob * 100))
            txt = pixelfont.render(f"{pct}%", 4, color=gauge_color(self.pred.prob), outline=(4, 14, 24))
            surf.blit(txt, txt.get_rect(midtop=(r.centerx, py + 14)))
            self.draw_stamp(surf, (r.centerx, py + 78))

    def draw_stamp(self, surf, center):
        phish = self.pred.is_phishing
        word = "PHISHING DETECTED" if phish else "PASSED INSPECTION"
        col = RED if phish else GREEN
        k = min(1.0, self.stamp_t / 0.22)
        if k <= 0:
            return
        f = ui.font(22, True)
        t = f.render(word, True, col)
        w, h = t.get_width() + 36, t.get_height() + 14
        st = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(st, (*col, 38), (0, 0, w, h), border_radius=8)
        pygame.draw.rect(st, col, (0, 0, w, h), 4, border_radius=8)
        pygame.draw.rect(st, col, (5, 5, w - 10, h - 10), 1, border_radius=5)
        st.blit(t, (18, 7))
        sc = 1 + (1 - k) * 1.6
        st = pygame.transform.rotozoom(st, 4, sc)
        st.set_alpha(int(255 * k))
        shake = int(math.sin(self.stamp_t * 60) * 5 * max(0.0, 1 - self.stamp_t * 4))
        surf.blit(st, st.get_rect(center=(center[0] + shake, center[1])))

    def draw_patterns(self, surf):
        r = self.pat
        self.panel(surf, r, "SUSPICIOUS PATTERNS")
        if self.phase == "scan":
            ui.draw_text(surf, "Waiting for scan results...", ui.mono(13), (80, 130, 150), (r.x + 14, r.y + 48))
            return
        y = r.y + 40
        if not self.hints:
            for ln in ui.wrap_lines(ui.font(14), "No clear suspicious pattern found. That is why a message like this is hard for the AI to tell apart from a normal email.", r.w - 28):
                ui.draw_text(surf, ln, ui.font(14), (200, 225, 235), (r.x + 14, y))
                y += 20
            return
        for i, h in enumerate(self.hints[:3]):
            k = (self.phase_t + (0.0 if self.phase != "verdict" else 0.0) - 0.2 - i * 0.25) / 0.2
            if k <= 0 and self.phase == "verdict":
                continue
            pygame.draw.circle(surf, (255, 190, 70), (r.x + 20, y + 10), 5)
            ui.draw_text(surf, h["title"], ui.font(14, True), (255, 214, 120), (r.x + 32, y))
            hits = ", ".join('"' + x + '"' for x in h["hits"][:2])
            hs = ui.font(13)
            while hs.size(hits)[0] > r.w - 46 and len(hits) > 6:
                hits = hits[:-4] + ".."
            ui.draw_text(surf, hits, hs, (170, 210, 225), (r.x + 32, y + 17))
            y += 38
        tip = self.hints[int(self.t / 3.2) % len(self.hints)]["tip"]
        yy = r.bottom - 8 - 17 * min(2, len(ui.wrap_lines(ui.font(12), "Tips: " + tip, r.w - 28)))
        for j, ln in enumerate(ui.wrap_lines(ui.font(12), "Tips: " + tip, r.w - 28)[:2]):
            ui.draw_text(surf, ln, ui.font(12), (120, 190, 205), (r.x + 14, yy + j * 16))

    def draw_attachment(self, surf):
        r = self.att
        rd = self.rd
        self.panel(surf, r, "ATTACHMENT SCAN")
        if not rd.attachment:
            cx, cy = r.centerx, r.y + 88
            icons.draw_icon(surf, "paperclip", (cx, cy), 64, (60, 96, 112))
            pygame.draw.line(surf, (200, 90, 80), (cx - 30, cy - 30), (cx + 30, cy + 30), 4)
            ui.draw_text(surf, "No file attached", ui.font(18, True), (200, 225, 235), (cx, r.y + 134), "midtop")
            ui.draw_text(surf, "Nothing to scan in this email.", ui.font(13), (110, 150, 168), (cx, r.y + 162), "midtop")
            return
        name = rd.attachment
        art_ui.draw_file_icon(surf, scoring.file_kind(name), (r.x + 44, r.y + 72), 58)
        nf = ui.font(15, True)
        lines = ui.wrap_lines(nf, name.replace("_", "_ "), r.w - 100)
        for i, ln in enumerate(lines[:2]):
            ui.draw_text(surf, ln.replace("_ ", "_"), nf, (255, 226, 150), (r.x + 82, r.y + 52 + i * 20))
        ui.draw_text(surf, scoring.file_size(name), ui.font(13), (130, 170, 190), (r.x + 82, r.y + 96))
        box = pygame.Rect(r.x + 14, r.y + 128, r.w - 28, 66)
        pygame.draw.rect(surf, (6, 16, 28), box, border_radius=8)
        mal = bool(rd.malware)
        if self.phase in ("scan", "verdict"):
            pygame.draw.rect(surf, (40, 110, 140), box, 2, border_radius=8)
            txt = "Waiting for message scan..." if self.phase == "scan" else "Queued for file scan..."
            ui.draw_text(surf, txt, ui.mono(13), (110, 170, 190), box.center, "center")
            return
        if self.phase == "gacha" and self.roll_t < 1.5:
            slow = 0.07 + 0.22 * (self.roll_t / 1.5) ** 2
            show_mal = int(self.roll_t / slow) % 2 == 0
            col = RED if show_mal else GREEN
            pygame.draw.rect(surf, col, box, 2, border_radius=8)
            ui.draw_text(surf, "ANALYZING FILE", ui.mono(11, True), (150, 200, 215), (box.centerx, box.y + 6), "midtop")
            ui.draw_text(surf, "MALWARE?" if show_mal else "CLEAN?", ui.font(24, True), col, (box.centerx, box.centery + 8), "center")
            return
        col = RED if mal else GREEN
        k = min(1.0, max(0.0, (self.roll_t - 1.5) / 0.25)) if self.phase == "gacha" else 1.0
        sc = 1 + (1 - k) * 0.6
        pygame.draw.rect(surf, col, box, 3, border_radius=8)
        fill = pygame.Surface(box.size, pygame.SRCALPHA)
        fill.fill((*col, 40))
        surf.blit(fill, box)
        label = "MALWARE FOUND" if mal else "CLEAN FILE"
        t = ui.text_surf(ui.font(22, True), label, col)
        t = pygame.transform.smoothscale(t, (max(1, int(t.get_width() * sc)), max(1, int(t.get_height() * sc))))
        icons.draw_icon(surf, "warning" if mal else "check", (box.x + 32, box.centery), 30, col)
        surf.blit(t, t.get_rect(midleft=(box.x + 58, box.centery)))

    def draw_score(self, surf):
        r = self.score
        self.panel(surf, r, "ROUND RESULT")
        if self.res is None:
            dots = "." * (int(self.t * 3) % 4)
            ui.draw_text(surf, "Calculating" + dots, ui.mono(14), (110, 170, 190), (r.x + 14, r.y + 52))
            return
        res = self.res
        col = {"jackpot": (255, 214, 70), "pass": GREEN, "caught": (240, 150, 60), "busted": RED}[res["code"]]
        k = min(1.0, self.phase_t / 0.3)
        ui.draw_text(surf, res["title"], ui.font(26, True), col, (r.x + 14, r.y + 34), shadow=(0, 0, 0))
        for i, ln in enumerate(ui.wrap_lines(ui.font(13), res["detail"], r.w - 28)[:2]):
            ui.draw_text(surf, ln, ui.font(13), (200, 224, 234), (r.x + 14, r.y + 68 + i * 17))
        c = min(1.0, self.count_t / 0.9)
        pts = int(res["points"] * c)
        mon = int(res["money"] * c)
        for i, (lab, val, unit_col) in enumerate((("POINTS", f"{pts:+d}", (150, 220, 255)), ("MONEY", f"+${mon}" if res["money"] else "$0", (150, 255, 170)))):
            bx = pygame.Rect(r.x + 12 + i * 146, r.y + 104, 140, 44)
            pygame.draw.rect(surf, (6, 16, 28), bx, border_radius=6)
            pygame.draw.rect(surf, (28, 96, 124), bx, 1, border_radius=6)
            ui.draw_text(surf, lab, ui.mono(11, True), (110, 160, 180), (bx.x + 10, bx.y + 4))
            neg = res["points"] < 0 and i == 0
            ui.draw_text(surf, val, ui.font(20, True), RED if neg else unit_col, (bx.x + 10, bx.y + 18))
        self.btn_next.draw(surf)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        g = radial_glow(500, (20, 120, 160), 0.35)
        surf.blit(pygame.transform.scale(g, (1200, 760)), (40, -20), special_flags=pygame.BLEND_RGB_ADD)
        ui.draw_window(surf, WIN, "YuBeatEm MailGuard AI - Email Scanner", tint=(36, 108, 168), body=(6, 14, 26), icon=lambda s, c, z, col: icons.draw_icon(s, "shield", c, z, (130, 255, 190)))
        self.draw_left(surf)
        self.draw_right(surf)
        self.draw_patterns(surf)
        self.draw_attachment(surf)
        self.draw_score(surf)

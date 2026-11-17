import math
import threading
import pygame
from .base import Scene
from .. import ui, icons, pixelfont
from ..validator import find_patterns
from .. import config as C

WIN = pygame.Rect(52, 70, 1176, 600)
GREEN = (46, 170, 90)
RED = (214, 66, 58)


class LiveScene(Scene):
    """Mode Live Simulation tanpa batas pesan untuk menguji model AI dan melatihnya ulang lewat verifikasi pemain."""

    hud = None
    exit_kind = "live"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.bg = app.assets.get("aero_lab")
        self.client = pygame.Rect(WIN.x + 8, WIN.y + 32, WIN.w - 16, WIN.h - 40)
        c = self.client
        self.subject = ui.LineInput((c.x + 96, c.y + 50, 482, 32), ui.font(17), "Write a subject line", 100, (24, 30, 44), on_submit=self.focus_body, on_change=lambda t: app.sfx.play("type"))
        self.subject.focus = False
        self.area = ui.TextArea((c.x + 18, c.y + 94, 560, 334), ui.font(18), (24, 30, 44), "Write or paste any email message here.\nTry phishing and normal messages, then see how the AI judges them.\n\nThere is no limit on the number of messages.", 2400, 12, 7)
        self.area.focus = False
        self.area.on_type = lambda s: app.sfx.play("type")
        self.send_btn = ui.Button((c.x + 18 + 560 - 176, c.y + 444, 176, 46), "Send", self.send, "primary", icon=icons.icon_fn("send"), size=18)
        self.clear_btn = ui.Button((c.x + 18, c.y + 444, 140, 46), "Clear", self.clear, "default", size=16)
        rx = c.x + 600
        self.right = pygame.Rect(rx, c.y + 14, c.right - rx - 16, c.h - 28)
        r = self.right
        self.btn_right = ui.Button((r.x + 16, r.y + 258, 232, 46), "AI Correct", lambda: self.verify(True), "success", icon=icons.icon_fn("check"), size=17)
        self.btn_wrong = ui.Button((r.x + 262, r.y + 258, r.w - 278, 46), "AI Wrong, Retrain", lambda: self.verify(False), "danger", icon=icons.icon_fn("retrain"), size=17)
        self.pred = None
        self.text = ""
        self.subj = ""
        self.state = "idle"
        self.state_t = 0.0
        self.history = []
        self.hscroll = 0.0
        self.htarget = 0.0
        self.hdrag = None
        self.verified = False
        self.learning = False
        self.note = ""
        self.hints = []
        self.shake = 0.0
        self.pending = None
        self.close_down = False
        self.btn_right.enabled = False
        self.btn_wrong.enabled = False

    def backdrop_art(self):
        return self.bg

    def hist_rect(self):
        """Menghitung area daftar histori yang bisa digulir di kartu performa."""
        r = pygame.Rect(self.right.x, self.right.y + 378, self.right.w, self.right.h - 378)
        top = r.y + 80 + (22 if self.note else 0)
        return pygame.Rect(r.x + 8, top, r.w - 16, max(10, r.bottom - 8 - top))

    def hist_max(self):
        """Menghitung batas gulir daftar histori."""
        return max(0, len(self.history) * 22 - self.hist_rect().h)

    def hist_track(self):
        """Menghitung area jalur scrollbar histori."""
        hr = self.hist_rect()
        return pygame.Rect(hr.right - 8, hr.y, 8, hr.h)

    def hist_thumb(self):
        """Menghitung area pegangan scrollbar histori sesuai posisi gulir."""
        tr = self.hist_track()
        total = max(1, len(self.history) * 22)
        h = max(24, int(tr.h * min(1.0, tr.h / total)))
        ms = self.hist_max()
        y = tr.y + (int((tr.h - h) * (self.hscroll / ms)) if ms else 0)
        return pygame.Rect(tr.x, y, tr.w, h)

    def close_rect(self):
        """Menghitung area tombol X pada bilah judul jendela Live Simulation."""
        return pygame.Rect(WIN.right - 8 - 98 + 52, WIN.y + 1, 46, 20)

    def focus_body(self):
        """Memindahkan fokus ketikan dari kolom subjek ke isi pesan."""
        self.subject.focus = False
        self.area.focus = True

    def clear(self):
        """Mengosongkan subjek dan isi pesan lalu memfokuskan subjek."""
        self.subject.set_text("")
        self.area.set_text("")
        self.area.focus = False
        self.subject.focus = True

    def send(self):
        text = self.area.text.strip()
        subject = self.subject.text.strip()
        if len(text) < 3 or self.app.adapter.busy or self.state == "scan":
            self.shake = 1.0
            self.app.sfx.play("error")
            return
        self.app.sfx.play("whoosh")
        self.text = text
        self.subj = subject
        self.state = "scan"
        self.state_t = 0.0
        self.pred = None
        self.verified = False
        self.note = ""
        self.hints = find_patterns(subject + "\n" + text, 3, "en")
        threading.Thread(target=self._predict, args=(subject, text), daemon=True).start()

    def _predict(self, subject, text):
        """Memprediksi pesan di thread terpisah dan memakai penilai cadangan bila model gagal."""
        try:
            self.pred = self.app.adapter.predict(subject, text)
        except Exception:
            from ..model_adapter import Prediction
            self.pred = Prediction(True, 0.9, "demo")

    def verify(self, ai_correct):
        if self.state != "result" or self.verified or self.pred is None:
            return
        self.verified = True
        p = self.pred
        self.app.adapter.record(ai_correct)
        truth = p.is_phishing if ai_correct else (not p.is_phishing)
        entry = {"text": (self.subj + ": " if self.subj else "") + self.text, "prob": p.prob, "phish": p.is_phishing, "ok": ai_correct}
        self.history.insert(0, entry)
        self.history = self.history[:200]
        self.hscroll = self.htarget = 0.0
        if ai_correct:
            self.note = "Thanks. The correct prediction was recorded for accuracy."
            self.app.sfx.play("confirm")
        else:
            self.learning = True
            self.note = "The AI is learning from your correction..."
            self.app.sfx.play("scan")
            self.app.adapter.learn_async(self.subj, self.text, truth, self.on_learned)

    def on_learned(self, info):
        self.learning = False
        meth = {"online": "retrained from your correction", "partial_fit": "trained incrementally (partial fit)", "refit": "retrained from the dataset", "memory": "correction saved in AI memory"}.get(info.get("method"), "updated")
        self.note = "Done! Model " + meth + "."
        self.app.sfx.play("win")

    def event(self, e):
        if e.type == pygame.MOUSEWHEEL and self.hist_rect().collidepoint(self.app.mouse) and self.hist_max() > 0:
            self.htarget = max(0, min(self.hist_max(), self.htarget - e.y * 44))
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.hist_max() > 0 and self.hist_track().inflate(8, 0).collidepoint(e.pos):
            th = self.hist_thumb()
            if th.collidepoint(e.pos):
                self.hdrag = e.pos[1] - th.y
            else:
                self.htarget = max(0, min(self.hist_max(), self.htarget + (self.hist_rect().h if e.pos[1] > th.y else -self.hist_rect().h)))
            return
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.hdrag = None
        if e.type == pygame.MOUSEMOTION and self.hdrag is not None:
            tr = self.hist_track()
            span = max(1, tr.h - self.hist_thumb().h)
            self.hscroll = self.htarget = max(0, min(self.hist_max(), (e.pos[1] - self.hdrag - tr.y) / span * self.hist_max()))
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.close_rect().collidepoint(e.pos):
            self.close_down = True
            return
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.close_down:
            self.close_down = False
            if self.close_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                self.app.go_menu()
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (e.mod & pygame.KMOD_CTRL):
            self.send()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            if self.subject.focus:
                self.focus_body()
            else:
                self.area.focus = False
                self.subject.focus = True
            return
        for b in (self.send_btn, self.clear_btn, self.btn_right, self.btn_wrong):
            if b.handle_event(e, self.app):
                return
        if self.subject.handle_event(e, self.app.mouse):
            self.area.focus = False
            return
        self.area.handle_event(e, self.app.mouse)

    def update(self, dt):
        self.t += dt
        self.state_t += dt
        self.shake = max(0.0, self.shake - dt * 3)
        m = self.app.mouse
        self.area.update(dt, m)
        self.subject.update(dt, m)
        self.htarget = max(0, min(self.hist_max(), self.htarget))
        self.hscroll += (self.htarget - self.hscroll) * min(1.0, dt * 14)
        if abs(self.htarget - self.hscroll) < 0.3:
            self.hscroll = self.htarget
        if self.close_rect().collidepoint(m):
            ui.HOT["hand"] = True
        busy = self.app.adapter.busy or self.state == "scan"
        self.send_btn.enabled = not busy
        can_verify = self.state == "result" and not self.verified
        self.btn_right.enabled = can_verify
        self.btn_wrong.enabled = can_verify
        for b in (self.send_btn, self.clear_btn, self.btn_right, self.btn_wrong):
            b.update(dt, m)
        if self.state == "scan" and self.state_t > 1.1 and self.pred is not None:
            self.state = "result"
            self.state_t = 0.0
            self.app.sfx.play("alarm" if self.pred.is_phishing else "confirm")

    def card(self, surf, r, title):
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=10)
        pygame.draw.rect(surf, (180, 196, 224), r, 2, border_radius=10)
        pygame.draw.rect(surf, (226, 236, 252), (r.x + 2, r.y + 2, r.w - 4, 28), border_top_left_radius=8, border_top_right_radius=8)
        ui.draw_text(surf, title, ui.font(14, True), (50, 80, 140), (r.x + 14, r.y + 6))

    def draw_verdict(self, surf):
        r = pygame.Rect(self.right.x, self.right.y, self.right.w, 232)
        self.card(surf, r, "AI VERDICT")
        cx, cy = r.x + 78, r.y + 118
        if self.state == "idle":
            icons.draw_icon(surf, "robot", (cx, cy), 80, (150, 170, 205))
            ui.draw_text(surf, "Waiting for your first message", ui.font(20, True), (60, 80, 120), (r.x + 150, r.y + 84))
            ui.draw_text(surf, "Write a message on the left, then press Send.", ui.font(15), (100, 114, 140), (r.x + 150, r.y + 118))
        elif self.state == "scan":
            for k in range(10):
                a = self.t * 6 + k * math.tau / 10
                rr = 4 + (k % 3)
                pygame.draw.circle(surf, (60, 130, 220), (int(cx + math.cos(a) * 34), int(cy + math.sin(a) * 34)), rr)
            icons.draw_icon(surf, "magnifier", (cx, cy), 40, (40, 90, 170))
            ui.draw_text(surf, "AI is scanning" + "." * (int(self.t * 3) % 4), ui.font(20, True), (50, 80, 140), (r.x + 150, r.y + 90))
            bar = pygame.Rect(r.x + 150, r.y + 130, r.w - 180, 14)
            pygame.draw.rect(surf, (222, 230, 244), bar, border_radius=7)
            pygame.draw.rect(surf, (60, 140, 230), (bar.x, bar.y, int(bar.w * min(1.0, self.state_t / 1.1)), bar.h), border_radius=7)
        elif self.pred is not None:
            p = self.pred
            col = RED if p.is_phishing else GREEN
            k = min(1.0, self.state_t / 0.3)
            e = 1 + 2.4 * (k - 1) ** 3 + 1.4 * (k - 1) ** 2
            d = int(86 * e)
            if d > 4:
                pygame.draw.circle(surf, tuple(int(c * 0.6) for c in col), (cx, cy), d // 2 + 4)
                pygame.draw.circle(surf, col, (cx, cy), d // 2)
                icons.draw_icon(surf, "warning" if p.is_phishing else "check", (cx, cy), int(d * 0.6), (255, 255, 255))
            ui.draw_text(surf, "PHISHING" if p.is_phishing else "NORMAL / SAFE", ui.font(26, True), col, (r.x + 150, r.y + 62))
            ui.draw_text(surf, f"Phishing probability: {int(p.prob * 100)}%", ui.font(16), (60, 76, 110), (r.x + 150, r.y + 100))
            bar = pygame.Rect(r.x + 150, r.y + 130, r.w - 180, 16)
            pygame.draw.rect(surf, (222, 230, 244), bar, border_radius=8)
            fw = int(bar.w * p.prob * min(1.0, self.state_t / 0.6))
            if fw > 2:
                pygame.draw.rect(surf, RED if p.prob >= 0.5 else (240, 180, 50), (bar.x, bar.y, fw, bar.h), border_radius=8)
            pygame.draw.line(surf, (60, 70, 100), (bar.centerx, bar.y - 4), (bar.centerx, bar.bottom + 4), 2)
            src = {"model": "NLP model", "memory": "correction memory", "demo": "AI guard"}.get(p.source, "AI")
            ui.draw_text(surf, "Judged by: " + src, ui.font(13), (110, 124, 150), (r.x + 150, r.y + 158))
            if self.hints:
                txt = "Patterns: " + ", ".join(h["title"] for h in self.hints)
            else:
                txt = "No clear suspicious patterns."
            for j, ln in enumerate(ui.wrap_lines(ui.font(13), txt, r.w - 170)[:2]):
                ui.draw_text(surf, ln, ui.font(13), (150, 100, 20), (r.x + 150, r.y + 180 + j * 18))

    def draw_verify(self, surf):
        r = pygame.Rect(self.right.x, self.right.y + 244, self.right.w, 70)
        r.h = 68
        r2 = pygame.Rect(self.right.x, self.right.y + 244, self.right.w, 122)
        self.card(surf, r2, "YOUR VERIFICATION")
        ui.draw_text(surf, "Is the AI verdict above correct?", ui.font(15), (50, 62, 90), (r2.x + 16, r2.y + 36))
        self.btn_right.rect.y = r2.y + 66
        self.btn_wrong.rect.y = r2.y + 66
        self.btn_right.rect.height = 44
        self.btn_wrong.rect.height = 44
        self.btn_right.draw(surf)
        self.btn_wrong.draw(surf)

    def draw_stats(self, surf):
        r = pygame.Rect(self.right.x, self.right.y + 378, self.right.w, self.right.h - 378)
        self.card(surf, r, "HISTORY AND AI PERFORMANCE")
        st = self.app.adapter.stats
        acc = self.app.adapter.accuracy()
        chips = (("Verified", str(st["verified"])), ("Accuracy", "-" if acc is None else f"{int(acc * 100)}%"), ("Retrained", f"{st['retrains']}x"))
        cw = (r.w - 32 - 16) // 3
        for i, (lab, val) in enumerate(chips):
            cr = pygame.Rect(r.x + 16 + i * (cw + 8), r.y + 34, cw, 38)
            pygame.draw.rect(surf, (232, 240, 252), cr, border_radius=8)
            ui.draw_text(surf, val, ui.font(18, True), (30, 70, 140), (cr.x + 10, cr.centery), "midleft")
            ui.draw_text(surf, lab, ui.font(12), (90, 104, 134), (cr.right - 8, cr.centery), "midright")
        y = r.y + 80
        if self.note:
            col = (30, 120, 70) if not self.learning else (40, 90, 170)
            ui.draw_text(surf, self.note, ui.font(14, True), col, (r.x + 16, y))
            if self.learning:
                for k in range(8):
                    a = self.t * 8 + k * math.tau / 8
                    pygame.draw.circle(surf, (60, 130, 220), (int(r.right - 30 + math.cos(a) * 9), int(y + 9 + math.sin(a) * 9)), 2 + (k % 3))
            y += 22
        hr = self.hist_rect()
        old = surf.get_clip()
        surf.set_clip(hr)
        sb = 14 if self.hist_max() > 0 else 0
        for i, h in enumerate(self.history):
            ry = hr.y + i * 22 - int(self.hscroll)
            if ry + 22 < hr.y or ry > hr.bottom:
                continue
            ok = h["ok"]
            icons.draw_icon(surf, "check" if ok else "cross", (hr.x + 18, ry + 11), 14, GREEN if ok else RED)
            label = "phishing" if h["phish"] else "normal"
            snippet = h["text"].replace("\n", " ")
            f = ui.font(13)
            room = hr.w - 36 - sb - 70
            while f.size(snippet)[0] > room and len(snippet) > 4:
                snippet = snippet[:-2]
            if snippet != h["text"].replace("\n", " "):
                snippet = snippet.rstrip() + "..."
            ui.draw_text(surf, snippet, f, (60, 72, 100), (hr.x + 36, ry + 3))
            ui.draw_text(surf, label, ui.font(12, True), RED if h["phish"] else GREEN, (hr.right - sb - 6, ry + 4), "topright")
        surf.set_clip(old)
        if self.hist_max() > 0:
            tr = self.hist_track()
            pygame.draw.rect(surf, (226, 232, 244), tr, border_radius=4)
            th = self.hist_thumb()
            surf.blit(ui.button_surface(th.w, th.h, "default", "hover" if self.hdrag is not None else "normal", 4), th)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        ui.draw_window(surf, WIN, "Live Simulation - Phisherman Lab", tint=(50, 120, 200), icon=lambda s, c, z, col: icons.draw_icon(s, "robot", c, z, (255, 255, 255)))
        if self.close_rect().collidepoint(self.app.mouse):
            cr = self.close_rect()
            hot = pygame.Surface(cr.size, pygame.SRCALPHA)
            pygame.draw.rect(hot, (255, 120, 100, 230 if self.close_down else 170), hot.get_rect(), border_bottom_right_radius=5)
            pygame.draw.rect(hot, (255, 255, 255, 200), hot.get_rect(), 1, border_bottom_right_radius=5)
            surf.blit(hot, cr)
            pygame.draw.line(surf, (255, 255, 255), (cr.x + 17, cr.y + 5), (cr.x + 27, cr.y + 14), 3)
            pygame.draw.line(surf, (255, 255, 255), (cr.x + 27, cr.y + 5), (cr.x + 17, cr.y + 14), 3)
        c = self.client
        pygame.draw.rect(surf, (238, 244, 254), c)
        ox = int(math.sin(self.t * 60) * 8 * self.shake)
        ui.draw_text(surf, "Email Message", ui.font(18, True), (30, 60, 120), (c.x + 18, c.y + 12))
        ui.draw_text(surf, "Ctrl+Enter to send", ui.font(13), (110, 124, 150), (c.x + 578, c.y + 20), "topright")
        ui.draw_text(surf, "Subject", ui.font(16, True), (30, 60, 120), (c.x + 18, c.y + 66), "midleft")
        sr = self.subject.rect
        sr.x = c.x + 96 + ox
        pygame.draw.rect(surf, (255, 255, 255), sr)
        self.subject.draw(surf)
        pygame.draw.rect(surf, (130, 156, 200) if self.subject.focus else (190, 202, 224), sr, 1)
        a = self.area
        a.rect.x = c.x + 18 + ox
        pygame.draw.rect(surf, (255, 255, 255), a.rect)
        a.draw(surf)
        pygame.draw.rect(surf, (214, 70, 60) if self.shake > 0 else ((130, 156, 200) if a.focus else (190, 202, 224)), a.rect, 2 if self.shake > 0 else 1)
        ui.draw_text(surf, f"{len(a.text)} characters", ui.font(13), (110, 124, 150), (c.x + 18 + 160 + 16, c.y + 444 + 14))
        self.send_btn.draw(surf)
        self.clear_btn.draw(surf)
        pygame.draw.line(surf, (190, 202, 224), (c.x + 596, c.y + 12), (c.x + 596, c.bottom - 12))
        self.draw_verdict(surf)
        self.draw_verify(surf)
        self.draw_stats(surf)

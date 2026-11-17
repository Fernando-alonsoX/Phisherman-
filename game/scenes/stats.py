import math
import pygame
from .base import Scene
from .. import ui, icons, pixelfont, art_items, art_ui, scoring, art_button, cosmetics
from ..canvas import radial_glow
from .. import config as C

TIPS = [
    "Phishing often uses urgency such as 'act now' or 'your account will be blocked' so victims panic and stop thinking.",
    "Check the sender address and links. Hover over a link before clicking it to see where it really goes.",
    "Real organizations never ask for your password, PIN, or OTP code by email or text message.",
    "Sudden prizes and lotteries are classic bait. If it sounds too good to be true, stay alert.",
    "Even an AI detector can be fooled by a neatly written message. Human awareness is still the main defense.",
    "Turn on two-step verification so your account stays safe even if your password leaks.",
    "This is an educational simulation only. Real-world phishing is a cybercrime that can lead to prison.",
]
WIN = pygame.Rect(100, 82, 1080, 616)
CODE_STYLE = {
    "jackpot": ((255, 190, 40), "JACKPOT"),
    "pass": ((60, 180, 90), "PASSED"),
    "busted": ((200, 50, 50), "BUSTED"),
    "caught": ((230, 120, 60), "DETECTED"),
}


class StatsScene(Scene):
    """Layar statistik akhir berisi potret pemain skor uang rincian lima pesan peringkat tombol papan peringkat dan satu tombol kembali ke menu."""

    hud = "money"
    exit_button = False
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        s = app.session
        self.won = s.won
        self.name = app.player_name or s.player or "PLAYER"
        self.bg = app.assets.get("aero" if self.won else "aero_lab")
        self.portrait_big = app.assets.portrait("happy" if self.won else "cry", 164)
        self.shown_score = 0.0
        self.shown_money = float(C.START_MONEY)
        self.record()
        self.rank = app.players.stats(self.name)["rank"] if self.name else None
        self.btn = ui.Button((0, 0, 360, 52), "BACK TO MAIN MENU", app.go_menu, "primary", icon=icons.icon_fn("home"), size=18)
        self.btn_board = art_button.ArtButton((0, 0, 240, 58), "LEADERBOARD", app.open_leaderboard, "default", art_button.board_art, (255, 255, 255), size=17)
        self.tip_i = 0

    def record(self):
        """Menyimpan hasil permainan ke data pemain tepat satu kali per sesi."""
        s = self.app.session
        if s.recorded or not self.name:
            return
        s.recorded = True
        codes = [r.outcome["code"] for r in s.rounds if r.outcome]
        self.app.players.record_run(self.name, s.score, s.money, s.wins, s.won, codes)

    def enter(self):
        self.app.sfx.play("win" if self.won else "lose")

    def backdrop_art(self):
        return self.bg

    def on_escape(self):
        self.app.go_menu()

    def event(self, e):
        self.btn.handle_event(e, self.app)
        self.btn_board.handle_event(e, self.app)
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.app.go_menu()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_l:
            self.app.open_leaderboard()

    def update(self, dt):
        self.t += dt
        s = self.app.session
        if self.t > 0.5:
            self.shown_score = min(float(s.score), self.shown_score + max(30.0, s.score * dt * 0.6))
            self.shown_money = min(float(s.money), self.shown_money + max(1.0, (s.money - C.START_MONEY) * dt * 0.6))
        self.tip_i = int(self.t / 6.0) % len(TIPS)
        self.btn.update(dt, self.app.mouse)
        self.btn_board.update(dt, self.app.mouse)

    def draw_left(self, surf, cl, accent):
        panel = pygame.Rect(cl.x, cl.y, 280, cl.h)
        pygame.draw.rect(surf, (226, 236, 250), panel)
        pygame.draw.line(surf, (170, 190, 220), (panel.right, panel.y), (panel.right, panel.bottom))
        pc = (panel.centerx, panel.y + 190)
        halo = radial_glow(150, accent, 0.5)
        surf.blit(halo, halo.get_rect(center=pc), special_flags=pygame.BLEND_RGB_ADD)
        sh = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(sh, (0, 0, 0, 60), (100, 106), 92)
        surf.blit(sh, sh.get_rect(center=pc))
        bob = math.sin(self.t * 2) * 3
        surf.blit(self.portrait_big, self.portrait_big.get_rect(center=(pc[0], pc[1] + bob)))
        cosmetics.draw_border(surf, (pc[0], int(pc[1] + bob)), 80, self.app.eggs.look(self.app.player_name)["border"])
        ui.draw_text(surf, self.name.upper(), ui.font(22, True), (30, 56, 104), (panel.centerx, pc[1] + 92), "midtop")
        pill = pygame.Rect(0, 0, 200, 34)
        pill.midtop = (panel.centerx, pc[1] + 128)
        pygame.draw.rect(surf, (255, 226, 130), pill, border_radius=17)
        pygame.draw.rect(surf, (190, 140, 30), pill, 2, border_radius=17)
        icons.draw_icon(surf, "crown", (pill.x + 24, pill.centery), 22, (150, 96, 10))
        label = f"Rank #{self.rank}" if self.rank else "Unranked"
        ui.draw_text(surf, label, ui.font(16, True), (110, 70, 6), (pill.x + 42, pill.centery), "midleft")
        self.btn_board.rect.midtop = (panel.centerx, pill.bottom + 24)
        self.btn_board.draw(surf)

    def draw_card(self, surf, r, icon, label, value, col, sub):
        pygame.draw.rect(surf, (255, 255, 255), r, border_radius=12)
        pygame.draw.rect(surf, col, r, 3, border_radius=12)
        band = pygame.Rect(r.x, r.y, 78, r.h)
        pygame.draw.rect(surf, col, band, border_top_left_radius=12, border_bottom_left_radius=12)
        icon(surf, band.center)
        ui.draw_text(surf, label, ui.font(15, True), (80, 96, 130), (band.right + 14, r.y + 8))
        t = pixelfont.render(value, 4, color=col, outline=(20, 30, 60), shadow=(1, 1, (200, 208, 224)))
        surf.blit(t, (band.right + 14, r.y + 24))
        ui.draw_text(surf, sub, ui.font(12), (110, 124, 150), (band.right + 14, r.bottom - 8), "bottomleft")

    def draw_rows(self, surf, x, y, w):
        rounds = self.app.session.rounds
        ui.draw_text(surf, "Five message breakdown", ui.font(17, True), (30, 70, 140), (x, y))
        y += 28
        for i in range(C.TOTAL_ROUNDS):
            k = max(0.0, min(1.0, (self.t - 0.5 - i * 0.18) / 0.3))
            if k <= 0 or i >= len(rounds):
                continue
            rd = rounds[i]
            code = rd.outcome["code"] if rd.outcome else "caught"
            col, lab = CODE_STYLE.get(code, CODE_STYLE["caught"])
            r = pygame.Rect(x + int((1 - k) * 60), y + i * 40, w, 36)
            row = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(row, (255, 255, 255, 255), row.get_rect(), border_radius=8)
            pygame.draw.rect(row, (186, 200, 226, 255), row.get_rect(), 1, border_radius=8)
            row.set_alpha(int(255 * k))
            surf.blit(row, r)
            pygame.draw.circle(surf, col, (r.x + 22, r.centery), 13)
            icons.draw_icon(surf, "check" if rd.success else "cross", (r.x + 22, r.centery), 15, (255, 255, 255))
            sub = rd.subject if len(rd.subject) <= 24 else rd.subject[:23] + ".."
            ui.draw_text(surf, sub, ui.font(15, True), (30, 44, 80), (r.x + 46, r.centery), "midleft")
            if rd.attachment:
                art_ui.draw_file_icon(surf, scoring.file_kind(rd.attachment), (r.x + 262, r.centery), 22)
                tag = "malware" if rd.malware else "safe"
                ui.draw_text(surf, tag, ui.font(12, True), (190, 50, 50) if rd.malware else (60, 130, 90), (r.x + 280, r.centery), "midleft")
            else:
                ui.draw_text(surf, "no file", ui.font(12), (130, 142, 166), (r.x + 252, r.centery), "midleft")
            pill = pygame.Rect(r.x + 350, r.y + 6, 124, 24)
            pygame.draw.rect(surf, col, pill, border_radius=12)
            ui.draw_text(surf, lab, ui.font(12, True), (255, 255, 255), pill.center, "center")
            pts = rd.points
            ui.draw_text(surf, f"{pts:+d} pts" if pts else "0 pts", ui.font(15, True), (190, 50, 50) if pts < 0 else ((150, 100, 10) if pts else (110, 124, 150)), (r.right - 150, r.centery), "midright")
            ui.draw_text(surf, f"+${rd.money}" if rd.money else "$0", ui.font(15, True), (40, 140, 70) if rd.money else (110, 124, 150), (r.right - 16, r.centery), "midright")

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        s = self.app.session
        accent = (60, 190, 90) if self.won else (220, 70, 62)
        cl = ui.draw_window(surf, WIN, "Mission Report - Phisherman", tint=(70, 130, 200) if self.won else (110, 90, 140), icon=lambda a, c, z, col: icons.draw_icon(a, "star", c, z, (255, 220, 100)))
        pygame.draw.rect(surf, (244, 248, 254), cl)
        self.draw_left(surf, cl, accent)
        x0 = cl.x + 300
        w = cl.w - 320
        head = "MISSION COMPLETE" if self.won else "MISSION FAILED"
        title = pixelfont.render(head, 4, grad=((255, 255, 255), accent), outline=(10, 30, 70) if self.won else (50, 10, 20), shadow=(1, 1, (10, 20, 50)))
        surf.blit(title, (x0, cl.y + 8))
        ui.draw_text(surf, f"{s.wins} of {C.TOTAL_ROUNDS} messages passed the AI", ui.font(16, True), (70, 90, 130), (x0 + title.get_width() + 20, cl.y + 36), "midleft")
        cw = (w - 14) // 2
        c1 = pygame.Rect(x0, cl.y + 64, cw, 92)
        c2 = pygame.Rect(x0 + cw + 14, cl.y + 64, cw, 92)
        self.draw_card(surf, c1, lambda a, c: icons.draw_icon(a, "star", c, 44, (255, 255, 255)), "SCORE", f"{int(round(self.shown_score))}", (214, 150, 30), "malware bonus adds to score")
        coin = art_items.coin(3)
        self.draw_card(surf, c2, lambda a, c: a.blit(coin, coin.get_rect(center=c)), "MONEY", f"${int(round(self.shown_money)):,}", (46, 150, 80), f"starting balance ${C.START_MONEY}")
        self.draw_rows(surf, x0, cl.y + 170, w)
        card = pygame.Rect(x0, cl.y + 170 + 28 + 5 * 40 + 8, w, 74)
        pygame.draw.rect(surf, (255, 255, 255), card, border_radius=10)
        pygame.draw.rect(surf, (186, 200, 226), card, 2, border_radius=10)
        icons.draw_icon(surf, "info", (card.x + 30, card.y + 26), 30, (60, 120, 200))
        ui.draw_text(surf, "Did you know?", ui.font(15, True), (30, 70, 140), (card.x + 56, card.y + 8))
        lines = ui.wrap_lines(ui.font(14), TIPS[self.tip_i], card.w - 76)
        for j, ln in enumerate(lines[:3]):
            ui.draw_text(surf, ln, ui.font(14), (50, 62, 90), (card.x + 56, card.y + 28 + j * 18))
        for i in range(len(TIPS)):
            pygame.draw.circle(surf, (60, 120, 200) if i == self.tip_i else (200, 210, 228), (card.right - 18 - (len(TIPS) - 1 - i) * 11, card.y + 14), 3)
        by = cl.bottom - 66
        self.btn.rect.midtop = (x0 + w // 2, by)
        self.btn.draw(surf)

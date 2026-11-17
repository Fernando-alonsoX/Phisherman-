import math
import random
import time
import pygame
from .base import Scene
from .. import ui, icons, art_items, art_rooms, art_ui, scoring
from ..canvas import radial_glow
from ..players import email_handle
from ..rain import RainWindow
from ..session import Round
from ..validator import check_email
from .. import config as C

HELP = "Write a phishing email to the YuBeatEm staff.\n\nYour email must include:\n1. Opening, such as Hello or Dear Sir/Madam\n2. Body, at least 25 words to convince the target\n3. Closing, such as Thank you or Best regards"
RECIPIENT = "staff@yubeatem.id"
PAD = 14


def sender_for(name):
    """Menyusun alamat pengirim dari nama pemain dengan domain sunib.id."""
    return f"{email_handle(name or 'player')}@sunib.id"


class FileExplorer:
    """Jendela file explorer mini di dalam layar komputer untuk memilih satu file lampiran lalu menekan Upload."""

    def __init__(self, scene, scr):
        self.scene = scene
        self.rect = pygame.Rect(scr.right - 352, scr.y + 8, 344, 366)
        self.open = False
        self.t = 0.0
        self.sel = -1
        self.hover = -1
        self.close_hover = False
        self.last_click = (0.0, -1)
        self.local = pygame.Rect(PAD, PAD, self.rect.w, self.rect.h)
        self.client = pygame.Rect(self.local.x + 8, self.local.y + 32, self.local.w - 16, self.local.h - 40)
        self.rows_y = self.client.y + 62
        self.upload = ui.Button((self.client.right - 8 - 132, self.client.bottom - 46, 132, 38), "Upload", self.do_upload, "primary", icon=icons.icon_fn("paperclip"), size=16)
        self.upload.enabled = False

    def origin(self):
        return (self.rect.x - PAD, self.rect.y - PAD)

    def local_pos(self, pos):
        o = self.origin()
        return (pos[0] - o[0], pos[1] - o[1])

    def show(self):
        self.open = True
        self.t = 0.0
        self.sel = -1
        self.upload.enabled = False
        self.scene.app.sfx.play("pop")

    def close(self):
        self.open = False
        self.scene.app.sfx.play("click")

    def close_rect(self):
        return pygame.Rect(self.local.right - 8 - 98 + 52, self.local.y + 1, 46, 20)

    def row_rect(self, i):
        return pygame.Rect(self.client.x + 6, self.rows_y + i * 24, self.client.w - 12, 24)

    def do_upload(self):
        if self.sel < 0:
            return
        name = scoring.FILES[self.sel][0]
        self.scene.attach_request(name)

    def contains(self, pos):
        return self.open and self.rect.inflate(0, 0).collidepoint(pos)

    def event(self, e):
        if not self.open:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_DOWN, pygame.K_UP):
                n = len(scoring.FILES)
                self.sel = (self.sel + (1 if e.key == pygame.K_DOWN else -1)) % n if self.sel >= 0 else 0
                self.upload.enabled = True
                self.scene.app.sfx.play("hover")
                return True
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.sel >= 0:
                self.do_upload()
                return True
            return False
        if not hasattr(e, "pos"):
            return False
        lp = self.local_pos(e.pos)
        inside = self.rect.collidepoint(e.pos)
        le = pygame.event.Event(e.type, {**e.dict, "pos": lp})
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and inside:
            if self.close_rect().collidepoint(lp):
                self.close()
                return True
            for i in range(len(scoring.FILES)):
                if self.row_rect(i).collidepoint(lp):
                    now = time.time()
                    if self.sel == i and now - self.last_click[0] < 0.45 and self.last_click[1] == i:
                        self.do_upload()
                        return True
                    self.sel = i
                    self.last_click = (now, i)
                    self.upload.enabled = True
                    self.scene.app.sfx.play("click")
                    return True
        if self.upload.handle_event(le, self.scene.app):
            return True
        return inside and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)

    def update(self, dt, mouse):
        if not self.open:
            return
        self.t += dt
        lp = self.local_pos(mouse)
        self.upload.update(dt, lp)
        self.hover = -1
        for i in range(len(scoring.FILES)):
            if self.row_rect(i).collidepoint(lp) and self.rect.collidepoint(mouse):
                self.hover = i
                ui.HOT["hand"] = True
        self.close_hover = self.close_rect().collidepoint(lp) and self.rect.collidepoint(mouse)
        if self.close_hover:
            ui.HOT["hand"] = True

    def draw_local(self, p):
        r = self.local
        cl = ui.draw_window(p, r, "File Explorer - Documents", icon=lambda s, c, z, col: icons.draw_icon(s, "folder", c, z, (255, 224, 130)))
        if self.close_hover:
            cr = self.close_rect()
            hot = pygame.Surface(cr.size, pygame.SRCALPHA)
            pygame.draw.rect(hot, (255, 120, 100, 200), hot.get_rect(), border_bottom_right_radius=5)
            p.blit(hot, cr)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 17, cr.y + 5), (cr.x + 27, cr.y + 14), 3)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 27, cr.y + 5), (cr.x + 17, cr.y + 14), 3)
        pygame.draw.rect(p, (255, 255, 255), cl)
        bar = pygame.Rect(cl.x + 6, cl.y + 6, cl.w - 12, 26)
        pygame.draw.rect(p, (244, 247, 252), bar, border_radius=4)
        pygame.draw.rect(p, (186, 196, 214), bar, 1, border_radius=4)
        icons.draw_icon(p, "folder", (bar.x + 16, bar.centery), 18, (240, 190, 70))
        ui.draw_text(p, "This PC  >  Documents", ui.font(14), (60, 76, 108), (bar.x + 32, bar.centery), "midleft")
        head = pygame.Rect(cl.x + 6, cl.y + 38, cl.w - 12, 22)
        pygame.draw.rect(p, (236, 241, 249), head)
        pygame.draw.line(p, (200, 210, 228), head.bottomleft, head.bottomright)
        ui.draw_text(p, "Name", ui.font(13, True), (90, 104, 132), (head.x + 38, head.centery), "midleft")
        ui.draw_text(p, "Size", ui.font(13, True), (90, 104, 132), (head.right - 10, head.centery), "midright")
        for i, (name, kind, risk) in enumerate(scoring.FILES):
            rr = self.row_rect(i)
            if i == self.sel:
                pygame.draw.rect(p, (205, 227, 255), rr, border_radius=3)
                pygame.draw.rect(p, (110, 160, 230), rr, 1, border_radius=3)
            elif i == self.hover:
                pygame.draw.rect(p, (232, 242, 255), rr, border_radius=3)
            art_ui.draw_file_icon(p, kind, (rr.x + 18, rr.centery), 20)
            ui.draw_text(p, name, ui.font(14), (28, 40, 70), (rr.x + 36, rr.centery), "midleft")
            ui.draw_text(p, scoring.file_size(name), ui.font(12), (110, 122, 148), (rr.right - 6, rr.centery), "midright")
        foot = pygame.Rect(cl.x, cl.bottom - 52, cl.w, 52)
        pygame.draw.rect(p, (232, 238, 248), foot)
        pygame.draw.line(p, (186, 198, 220), foot.topleft, foot.topright)
        label = scoring.FILES[self.sel][0] if self.sel >= 0 else "No file selected"
        ui.draw_text(p, label if len(label) < 20 else label[:18] + "..", ui.font(13), (60, 76, 108) if self.sel >= 0 else (130, 142, 166), (foot.x + 10, foot.centery), "midleft")
        self.upload.draw(p)

    def draw(self, surf):
        if not self.open:
            return
        k = min(1.0, self.t / 0.2)
        ease = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        w, h = self.rect.w + PAD * 2, self.rect.h + PAD * 2
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        self.draw_local(panel)
        scale = 0.86 + 0.14 * ease
        if scale < 0.999:
            panel = pygame.transform.smoothscale(panel, (max(1, int(w * scale)), max(1, int(h * scale))))
        panel.set_alpha(int(255 * min(1.0, k * 1.8)))
        surf.blit(panel, panel.get_rect(center=(self.rect.centerx, self.rect.centery)))


class ComposeScene(Scene):
    """Layar menulis email di komputer ala Windows 7 dengan subjek lampiran file explorer checklist bagian email dan taskbar bergaya Windows."""

    hud = "money"
    counter = True
    exit_kind = "story"

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.room, self.scr = app.assets.get("compose_room")
        self.desktop = app.assets.get("desktop")
        self.taskbar = app.assets.get("taskbar")
        self.rain = RainWindow(art_rooms.WINDOW_RECT, 38, 7)
        scr = self.scr
        self.win = pygame.Rect(scr.x + 90, scr.y + 8, 790, 424)
        self.client = pygame.Rect(self.win.x + 8, self.win.y + 32, self.win.w - 16, self.win.h - 40)
        c = self.client
        self.sender = sender_for(app.player_name)
        self.subject = ui.LineInput((c.x + 86, c.y + 66, c.w - 100, 28), ui.font(16), "Write a subject line", 80, (40, 52, 80), on_submit=self.focus_body, on_change=lambda t: app.sfx.play("type"))
        self.subject.focus = False
        self.area = ui.TextArea((c.x + 8, c.y + 134, c.w - 16, c.h - 134 - 62), ui.font(18), (24, 30, 44), HELP, 2200, 12, 7)
        self.area.on_type = lambda s: app.sfx.play("type")
        self.area.focus = False
        self.attach_btn = ui.Button((c.x + 86, c.y + 98, 126, 28), "Attach", self.toggle_explorer, "default", icon=icons.icon_fn("paperclip"), size=14)
        self.send_btn = ui.Button((c.right - 176, c.bottom - 52, 164, 44), "Send", self.try_send, "primary", icon=icons.icon_fn("send"), size=18)
        self.explorer = FileExplorer(self, scr)
        self.attachment = None
        self.chip_x = pygame.Rect(0, 0, 0, 0)
        self.chip_hover = False
        self.alert = 0.0
        self.popup = None
        self.popup_t = 0.0
        self.ok_btn = ui.Button((0, 0, 110, 38), "OK", self.close_popup, "primary", size=17)
        self.flight = None
        self.status = check_email("", "")
        self.pops = {k: 0.0 for k in ("subject", "open", "body", "close")}
        self.prev_ok = {k: False for k in self.pops}
        self.edge = self._edge_glow()
        mon_glow = radial_glow(320, (50, 110, 210), 0.3)
        self.glow = pygame.transform.smoothscale(mon_glow, (1500, 900))
        self.round_no = app.session.sent + 1
        self.tray_hover = -1
        self.tb_hover = -1

    def _edge_glow(self):
        s = pygame.Surface((C.BASE_W, C.BASE_H), pygame.SRCALPHA)
        for i in range(46):
            a = int(200 * (1 - i / 46) ** 2)
            pygame.draw.rect(s, (230, 30, 30, a), (i, i, C.BASE_W - 2 * i, C.BASE_H - 2 * i), 2)
        return s

    def backdrop_art(self):
        return self.room

    def focus_body(self):
        self.subject.focus = False
        self.area.focus = True

    def toggle_explorer(self):
        if self.explorer.open:
            self.explorer.close()
        else:
            self.explorer.show()

    def taskbar_rects(self):
        scr = self.scr
        y = scr.bottom - 36
        return [pygame.Rect(scr.x + 60, y, 46, 32), pygame.Rect(scr.x + 112, y, 46, 32)]

    def tray_rects(self):
        scr = self.scr
        return [pygame.Rect(scr.right - 108 + i * 32, scr.bottom - 36, 30, 32) for i in range(3)]

    def attach_request(self, name):
        """Menerima file yang dipilih di explorer dan memasangnya sebagai lampiran atau menampilkan pesan batas satu file."""
        if self.attachment:
            self.explorer.sel = -1
            self.explorer.upload.enabled = False
            self.show_popup({
                "title": "Attachment Limit",
                "icon": "warning",
                "tint": (200, 70, 60),
                "head": "Only one attachment per email",
                "lines": [f"This email already has \"{self.attachment}\" attached."],
                "tip": "Remove the current file with the X button, then upload another one.",
            })
            return
        self.attachment = name
        self.app.sfx.play("coin")
        self.explorer.open = False
        self.chip_pop = 1.0

    def remove_attachment(self):
        self.attachment = None
        self.app.sfx.play("click")

    def show_popup(self, data):
        self.popup = data
        self.popup_t = 0.0
        self.alert = 1.0 if data.get("alert") else self.alert
        self.area.focus = False
        self.subject.focus = False
        self.app.sfx.play("error")

    def close_popup(self):
        self.popup = None

    def try_send(self):
        if self.flight or self.popup:
            return
        text = self.area.text.strip()
        res = check_email(text, self.subject.text)
        if not res["ok"]:
            miss = ", ".join(res["missing"])
            lines = [f"Missing parts: {miss}."]
            if "Body" in res["missing"]:
                lines.append(f"Your body has {res['words']} of {res['need']} words needed.")
            self.alert = 1.0
            self.show_popup({
                "title": "Email Incomplete",
                "icon": "warning",
                "tint": (200, 70, 60),
                "head": "Your email cannot be sent yet",
                "lines": lines,
                "tip": "A convincing email always has a subject, an opening greeting, a body of at least 25 words and a closing.",
            })
            return
        self.app.sfx.play("whoosh")
        self.app.session.sent += 1
        rd = Round(text, self.subject.text.strip(), self.sender, RECIPIENT, self.attachment)
        rd.malware = bool(self.attachment) and random.random() < scoring.file_risk(self.attachment)
        self.app.session.rounds.append(rd)
        self.flight = {"t": 0.0, "round": rd}
        self.area.enabled = False
        self.subject.focus = False
        self.explorer.open = False

    def event(self, e):
        if self.flight:
            return
        if self.popup:
            self.ok_btn.handle_event(e, self.app)
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_o):
                self.app.sfx.play("click")
                self.close_popup()
            return
        if self.explorer.event(e):
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.taskbar_rects()):
                if r.collidepoint(e.pos):
                    self.app.sfx.play("click")
                    if i == 1:
                        self.toggle_explorer()
                    return
            if self.attachment and self.chip_x.collidepoint(e.pos):
                self.remove_attachment()
                return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (e.mod & pygame.KMOD_CTRL):
            self.try_send()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            if self.subject.focus:
                self.focus_body()
            else:
                self.area.focus = False
                self.subject.focus = True
            return
        if self.send_btn.handle_event(e, self.app):
            return
        if self.attach_btn.handle_event(e, self.app):
            return
        if self.subject.handle_event(e, self.app.mouse):
            return
        self.area.handle_event(e, self.app.mouse)

    def update(self, dt):
        self.t += dt
        self.rain.update(dt)
        m = self.app.mouse
        self.chip_pop = max(0.0, getattr(self, "chip_pop", 0.0) - dt * 3)
        for k in self.pops:
            self.pops[k] = max(0.0, self.pops[k] - dt * 2.4)
        if self.popup:
            self.popup_t += dt
            self.ok_btn.update(dt, m)
        else:
            self.alert = max(0.0, self.alert - dt * 0.9)
            if not self.flight:
                self.area.update(dt, m)
                self.subject.update(dt, m)
                self.send_btn.update(dt, m)
                self.attach_btn.update(dt, m)
                self.explorer.update(dt, m)
                self.status = check_email(self.area.text, self.subject.text)
                for k in self.pops:
                    ok = self.status[k]
                    if ok and not self.prev_ok[k]:
                        self.pops[k] = 1.0
                        self.app.sfx.play("pop")
                    self.prev_ok[k] = ok
                self.tb_hover = -1
                for i, r in enumerate(self.taskbar_rects()):
                    if r.collidepoint(m):
                        self.tb_hover = i
                        ui.HOT["hand"] = True
                self.tray_hover = -1
                for i, r in enumerate(self.tray_rects()):
                    if r.collidepoint(m):
                        self.tray_hover = i
                self.chip_hover = bool(self.attachment) and self.chip_x.collidepoint(m)
                if self.chip_hover:
                    ui.HOT["hand"] = True
        if self.flight:
            self.flight["t"] += dt
            if self.flight["t"] > 1.0:
                rd = self.flight["round"]
                self.flight = None
                from .analysis import AnalysisScene
                self.app.goto(lambda: AnalysisScene(self.app, rd))

    def draw_chip(self, surf, rect, label, ok, pop, progress=None, extra=""):
        grow = int(5 * pop)
        r = rect.inflate(grow * 2, grow)
        if ok:
            surf.blit(ui.button_surface(r.w, r.h, "success", "normal", r.h // 2), r)
        else:
            pygame.draw.rect(surf, (238, 242, 249), r, border_radius=r.h // 2)
            pygame.draw.rect(surf, (156, 170, 196), r, 1, border_radius=r.h // 2)
        if pop > 0:
            halo = pygame.Surface((r.w + 24, r.h + 24), pygame.SRCALPHA)
            pygame.draw.rect(halo, (255, 255, 255, int(190 * pop)), halo.get_rect(), 3, border_radius=(r.h + 24) // 2)
            surf.blit(halo, (r.x - 12, r.y - 12))
        ic = (r.x + 19, r.centery - (2 if progress is not None else 0))
        pygame.draw.circle(surf, (255, 255, 255) if ok else (214, 222, 236), ic, 11)
        icons.draw_icon(surf, "check" if ok else "cross", ic, 14, (40, 150, 70) if ok else (170, 120, 120))
        col = (255, 255, 255) if ok else (84, 98, 128)
        ui.draw_text(surf, label, ui.font(15, True), col, (r.x + 38, ic[1]), "midleft", shadow=(10, 80, 30) if ok else None)
        if extra:
            ui.draw_text(surf, extra, ui.font(12, True), col, (r.right - 12, ic[1]), "midright")
        if progress is not None:
            tr = pygame.Rect(r.x + 14, r.bottom - 9, r.w - 28, 4)
            pygame.draw.rect(surf, (0, 0, 0, 0) if ok else (206, 214, 230), tr, border_radius=2)
            if ok:
                pygame.draw.rect(surf, (255, 255, 255), tr, border_radius=2)
            elif progress > 0:
                pygame.draw.rect(surf, (80, 150, 230), (tr.x, tr.y, int(tr.w * progress), tr.h), border_radius=2)

    def draw_status(self, surf):
        c = self.client
        y = c.bottom - 60
        pygame.draw.rect(surf, (236, 241, 249), (c.x, y, c.w, 60))
        pygame.draw.line(surf, (190, 200, 218), (c.x, y), (c.right, y))
        st = self.status
        x = c.x + 12
        specs = (("subject", "Subject", 116, None), ("open", "Opening", 116, None), ("body", "Body", 168, st["words"]), ("close", "Closing", 116, None))
        for key, label, w, words in specs:
            r = pygame.Rect(x, y + 10, w, 40)
            prog = None
            extra = ""
            if words is not None:
                prog = min(1.0, words / st["need"])
                extra = f"{min(words, 99)}/{st['need']}"
            self.draw_chip(surf, r, label, st[key], self.pops[key], prog, extra)
            x += w + 8

    def draw_attach_row(self, surf):
        c = self.client
        y = c.y + 98
        self.attach_btn.draw(surf)
        if not self.attachment:
            ui.draw_text(surf, "No file attached (optional)", ui.font(13), (130, 142, 166), (self.attach_btn.rect.right + 14, y + 14), "midleft")
            self.chip_x = pygame.Rect(0, 0, 0, 0)
            return
        name = self.attachment
        kind = scoring.file_kind(name)
        f = ui.font(14, True)
        sz = scoring.file_size(name)
        szw = ui.font(12).size(sz)[0]
        w = 36 + f.size(name)[0] + 12 + szw + 38
        chip = pygame.Rect(self.attach_btn.rect.right + 12, y, w, 28)
        pop = getattr(self, "chip_pop", 0.0)
        chip = chip.inflate(int(10 * pop), 0)
        pygame.draw.rect(surf, (226, 238, 255), chip, border_radius=14)
        pygame.draw.rect(surf, (96, 148, 226), chip, 1, border_radius=14)
        art_ui.draw_file_icon(surf, kind, (chip.x + 18, chip.centery), 20)
        ui.draw_text(surf, name, f, (24, 48, 100), (chip.x + 36, chip.centery), "midleft")
        ui.draw_text(surf, sz, ui.font(12), (96, 112, 144), (chip.right - 36, chip.centery), "midright")
        xr = pygame.Rect(0, 0, 20, 20)
        xr.center = (chip.right - 16, chip.centery)
        self.chip_x = xr.inflate(6, 6)
        pygame.draw.circle(surf, (226, 90, 76) if self.chip_hover else (170, 184, 212), xr.center, 10)
        icons.draw_icon(surf, "cross", xr.center, 12, (255, 255, 255))

    def draw_taskbar(self, surf):
        scr = self.scr
        surf.blit(self.taskbar, (scr.x, scr.bottom - 40))
        rects = self.taskbar_rects()
        for i, r in enumerate(rects):
            active = i == 0 or (i == 1 and self.explorer.open)
            state = "pressed" if active else ("hover" if self.tb_hover == i else None)
            if state:
                surf.blit(ui.button_surface(r.w, r.h, "dark", "hover" if state != "pressed" else "pressed", 4), r)
            if active:
                pygame.draw.rect(surf, (140, 210, 255), (r.x + 8, r.bottom - 3, r.w - 16, 2), border_radius=1)
            if i == 0:
                icons.draw_icon(surf, "envelope", r.center, 22, (235, 246, 255))
            else:
                icons.draw_icon(surf, "folder", r.center, 22, (255, 214, 110))
        for i, (r, name) in enumerate(zip(self.tray_rects(), ("chevup", "wifi", "speaker"))):
            if self.tray_hover == i:
                surf.blit(ui.button_surface(r.w, r.h, "dark", "hover", 4), r)
            icons.draw_icon(surf, name, r.center, 18, (235, 246, 255))

    def draw_header(self, surf):
        c = self.client
        pygame.draw.rect(surf, (244, 247, 252), (c.x, c.y, c.w, 130))
        rows = (("To", RECIPIENT), ("From", self.sender))
        for i, (lab, val) in enumerate(rows):
            fy = c.y + 6 + i * 30
            ui.draw_text(surf, lab, ui.font(15, True), (70, 84, 112), (c.x + 16, fy + 5))
            fr = pygame.Rect(c.x + 86, fy, c.w - 100, 28)
            pygame.draw.rect(surf, (236, 240, 247), fr, border_radius=3)
            pygame.draw.rect(surf, (200, 208, 224), fr, 1, border_radius=3)
            ui.draw_text(surf, val, ui.font(16), (60, 72, 100), (fr.x + 12, fr.centery), "midleft")
        ui.draw_text(surf, "Subject", ui.font(15, True), (70, 84, 112), (c.x + 16, c.y + 66 + 5))
        sub_state = "normal"
        self.subject.draw(surf, sub_state)
        ui.draw_text(surf, "Attach", ui.font(15, True), (70, 84, 112), (c.x + 16, c.y + 98 + 5))
        self.draw_attach_row(surf)
        pygame.draw.line(surf, (190, 200, 218), (c.x, c.y + 130), (c.right, c.y + 130))

    def draw_screen(self, surf):
        scr = self.scr
        old = surf.get_clip()
        surf.set_clip(scr)
        surf.blit(self.desktop, scr.topleft)
        client = ui.draw_window(surf, self.win, f"New Message ({self.round_no}/{C.TOTAL_ROUNDS}) - Mail", icon=lambda s, c, z, col: icons.draw_icon(s, "envelope", c, z, (255, 255, 255)))
        c = self.client
        self.draw_header(surf)
        pygame.draw.rect(surf, (255, 255, 255), (c.x, c.y + 131, c.w, c.h - 131))
        a = self.area
        pygame.draw.rect(surf, (255, 255, 255), a.rect)
        a.draw(surf)
        pygame.draw.rect(surf, (140, 160, 196) if a.focus else (200, 208, 224), a.rect, 1)
        self.draw_status(surf)
        self.send_btn.draw(surf)
        self.draw_taskbar(surf)
        self.explorer.draw(surf)
        glare = pygame.Surface(scr.size, pygame.SRCALPHA)
        pygame.draw.polygon(glare, (255, 255, 255, 12), [(0, 0), (scr.w * 0.5, 0), (scr.w * 0.2, scr.h), (0, scr.h)])
        surf.blit(glare, scr.topleft)
        surf.set_clip(old)

    def draw_popup(self, surf):
        pp = self.popup
        r = pygame.Rect(0, 0, 500, 270)
        r.center = (self.scr.centerx, self.scr.centery - 10)
        k = min(1.0, self.popup_t / 0.18)
        dim = pygame.Surface(self.scr.size, pygame.SRCALPHA)
        dim.fill((0, 0, 0, int(110 * k)))
        surf.blit(dim, self.scr.topleft)
        shake = int(math.sin(self.popup_t * 50) * 6 * max(0.0, 1 - self.popup_t * 3))
        r.x += shake
        cl = ui.draw_window(surf, r, pp["title"], tint=pp["tint"], icon=lambda s, c, z, col: icons.draw_icon(s, pp["icon"], c, z, (255, 230, 120)))
        pygame.draw.rect(surf, (252, 250, 250), cl)
        icons.draw_icon(surf, pp["icon"], (cl.x + 52, cl.y + 56), 64, (240, 70, 60))
        ui.draw_text(surf, pp["head"], ui.font(20, True), (120, 24, 24), (cl.x + 100, cl.y + 18))
        y = cl.y + 52
        for ln in pp["lines"]:
            for sub in ui.wrap_lines(ui.font(16, True), ln, cl.w - 120):
                ui.draw_text(surf, sub, ui.font(16, True), (170, 40, 40), (cl.x + 100, y))
                y += 22
        y += 8
        for sub in ui.wrap_lines(ui.font(15), pp["tip"], cl.w - 120):
            ui.draw_text(surf, sub, ui.font(15), (70, 78, 98), (cl.x + 100, y))
            y += 21
        self.ok_btn.rect.bottomright = (cl.right - 14, cl.bottom - 12)
        self.ok_btn.draw(surf)

    def draw_alert(self, surf):
        a = self.alert
        if a <= 0:
            return
        pulse = 0.65 + 0.35 * math.sin(self.t * 10)
        g = self.edge.copy()
        g.set_alpha(int(255 * min(1.0, a) * pulse))
        surf.blit(g, (0, 0))
        for off, w in ((6, 8), (18, 4)):
            for horizontal in (True, False):
                pts_a, pts_b = [], []
                span = C.BASE_W if horizontal else C.BASE_H
                other = C.BASE_H if horizontal else C.BASE_W
                for v in range(0, span + 20, 20):
                    d = off + math.sin(v / 38 + self.t * 9 + off) * 5
                    if horizontal:
                        pts_a.append((v, d))
                        pts_b.append((v, other - d))
                    else:
                        pts_a.append((d, v))
                        pts_b.append((other - d, v))
                col = (235, 40, 40) if w == 8 else (255, 130, 120)
                if a < 1.0:
                    col = tuple(int(c * min(1.0, a * 1.5)) for c in col)
                pygame.draw.lines(surf, col, False, pts_a, w)
                pygame.draw.lines(surf, col, False, pts_b, w)

    def draw_flight(self, surf):
        f = self.flight
        k = min(1.0, f["t"] / 0.9)
        e = 1 - (1 - k) ** 3
        sx, sy = self.send_btn.rect.center
        ex, ey = 1180, 40
        x = sx + (ex - sx) * e
        y = sy + (ey - sy) * e - math.sin(e * math.pi) * 140
        img = art_items.envelope_fish(4)
        img = pygame.transform.rotozoom(img, -e * 30, 1.0 - 0.4 * e)
        for i in range(6):
            kk = max(0.0, e - i * 0.05)
            px = sx + (ex - sx) * kk
            py = sy + (ey - sy) * kk - math.sin(kk * math.pi) * 140
            pygame.draw.circle(surf, (190, 225, 255), (int(px), int(py)), max(1, 7 - i))
        surf.blit(img, img.get_rect(center=(x, y)))

    def draw_room(self, surf):
        surf.blit(self.room, (0, 0))
        self.rain.draw(surf)
        surf.blit(self.glow, self.glow.get_rect(center=self.scr.center), special_flags=pygame.BLEND_RGB_ADD)

    def draw(self, surf):
        self.draw_room(surf)
        self.draw_screen(surf)
        if self.popup:
            self.draw_popup(surf)
        if self.flight:
            self.draw_flight(surf)
        self.draw_alert(surf)

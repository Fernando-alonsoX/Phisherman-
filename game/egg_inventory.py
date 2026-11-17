import math
import pygame
from . import ui, icons, art_egg, cosmetics
from .egg_data import FISH
from .leaderboard import blurred
from .canvas import mix
from . import config as C

COLS = 5
GAP = 10
CARD_H = 164
SHOP_COLS = 4
SHOP_H = 178
HEAD_H = 38
AV = (70, 130, 214)


class InventoryModal:
    """Kotak perkakas berlatar buram dengan tab Fish untuk melihat dan menjual ikan serta tab Shop untuk membeli border avatar dan spanduk, dan hanya area daftar yang bisa digulir."""

    def __init__(self, app, snapshot, on_close):
        self.app = app
        self.on_close = on_close
        self.eggs = app.eggs
        self.bg = blurred(snapshot)
        self.rect = pygame.Rect(0, 0, 900, 580)
        self.rect.center = (C.BASE_W // 2, C.BASE_H // 2)
        self.t = 0.0
        self.tab = 0
        self.scroll = [0.0, 0.0]
        self.target = [0.0, 0.0]
        self.drag = None
        self.close_down = False
        self.close_hover = False
        self.cache = {}
        self.sel = set()
        self.confirm_t = 0.0
        self.toast = None
        self.shake = 0.0
        self.refresh()
        self.btn_all = ui.Button((0, 0, 150, 42), "Select All", self.select_all, "default", size=16)
        self.btn_sell = ui.Button((0, 0, 210, 42), "Sell Selected", self.sell, "success", icon=icons.icon_fn("check"), size=16)
        self.place_buttons()

    def close(self):
        self.on_close()

    def refresh(self):
        """Mengurutkan ikan dari kelangkaan tertinggi ke terendah dan yang terbaru lebih dulu lalu menghitung ulang ringkasan."""
        self.items = sorted(reversed(self.eggs.catches), key=lambda c: -c["r"])
        self.counts = self.eggs.counts()
        alive = {id(c) for c in self.items}
        self.sel = {i for i in self.sel if i in alive}

    def client(self):
        """Menghitung area klien jendela pada koordinat lokal panel."""
        return pygame.Rect(8, 32, self.rect.w - 16, self.rect.h - 40)

    def area(self):
        """Menghitung area gulir daftar pada koordinat lokal panel."""
        c = self.client()
        return pygame.Rect(c.x + 14, c.y + 100, c.w - 28 - 18, c.h - 100 - 70)

    def place_buttons(self):
        c = self.client()
        self.btn_sell.rect.bottomright = (c.right - 16, c.bottom - 12)
        self.btn_all.rect.bottomright = (self.btn_sell.rect.x - 12, c.bottom - 12)

    def tab_rect(self, i):
        c = self.client()
        return pygame.Rect(c.x + 16 + i * 128, c.y + 54, 120, 34)

    def card_w(self):
        return (self.area().w - GAP * (COLS - 1)) // COLS

    def fish_layout(self):
        """Menghitung kotak setiap kartu ikan pada koordinat isi daftar."""
        cw = self.card_w()
        return [pygame.Rect((i % COLS) * (cw + GAP), (i // COLS) * (CARD_H + GAP), cw, CARD_H) for i in range(len(self.items))]

    def shop_layout(self):
        """Menghitung susunan judul bagian dan kartu skin pada koordinat isi daftar beserta tinggi totalnya."""
        a = self.area()
        cw = (a.w - GAP * (SHOP_COLS - 1)) // SHOP_COLS
        out = []
        y = 0
        for kind, title in (("border", "Avatar Borders"), ("banner", "Profile Banners")):
            out.append({"head": title, "rect": pygame.Rect(0, y, a.w, HEAD_H)})
            y += HEAD_H + 4
            for i, item in enumerate(cosmetics.KINDS[kind]):
                out.append({"kind": kind, "item": item, "rect": pygame.Rect((i % SHOP_COLS) * (cw + GAP), y + (i // SHOP_COLS) * (SHOP_H + GAP), cw, SHOP_H)})
            rows = (len(cosmetics.KINDS[kind]) + SHOP_COLS - 1) // SHOP_COLS
            y += rows * (SHOP_H + GAP) + 8
        return out, y

    def content_h(self):
        if self.tab == 0:
            rows = (len(self.items) + COLS - 1) // COLS
            return rows * (CARD_H + GAP) - GAP if rows else 0
        return self.shop_layout()[1]

    def max_scroll(self):
        return max(0, self.content_h() - self.area().h)

    def track(self):
        """Menghitung jalur scrollbar pada koordinat layar."""
        a = self.area()
        return pygame.Rect(self.rect.x + a.right + 6, self.rect.y + a.y, 12, a.h)

    def thumb(self):
        """Menghitung kotak penggeser scrollbar pada koordinat layar sesuai posisi gulir."""
        tr = self.track()
        mx = self.max_scroll()
        if mx <= 0:
            return None
        h = max(36, int(tr.h * self.area().h / self.content_h()))
        y = tr.y + int((tr.h - h) * (self.scroll[self.tab] / mx))
        return pygame.Rect(tr.x, y, tr.w, h)

    def close_rect(self):
        """Menghitung area tombol X jendela pada koordinat layar."""
        return pygame.Rect(self.rect.right - 8 - 98 + 52, self.rect.y + 1, 46, 20)

    def scroll_to(self, v):
        self.target[self.tab] = max(0.0, min(float(self.max_scroll()), v))

    def set_tab(self, i):
        if i != self.tab:
            self.tab = i
            self.confirm_t = 0.0
            self.app.sfx.play("click")

    def select_all(self):
        """Memilih semua ikan atau membatalkan pilihan bila semuanya sudah terpilih."""
        ids = {id(c) for c in self.items}
        self.sel = set() if self.sel == ids else ids
        self.confirm_t = 0.0

    def selected(self):
        return [c for c in self.items if id(c) in self.sel]

    def worth(self):
        return sum(FISH[c["r"]]["price"] for c in self.selected())

    def sell(self):
        """Menjual ikan terpilih dengan satu konfirmasi tambahan bila ada ikan epic atau legendary di dalamnya."""
        chosen = self.selected()
        if not chosen:
            return
        risky = any(c["r"] >= 3 for c in chosen)
        if risky and self.confirm_t <= 0:
            self.confirm_t = 3.0
            self.app.sfx.play("alarm", 0.4)
            return
        gain = self.eggs.sell(chosen)
        self.confirm_t = 0.0
        self.sel = set()
        self.refresh()
        self.scroll_to(self.target[0])
        self.say(f"Sold {len(chosen)} fish for ${gain}", (255, 214, 90))
        self.app.sfx.play("coin")

    def say(self, text, col):
        self.toast = [text, 2.2, col]

    def shop_action(self, kind, item):
        """Membeli atau memakai skin sesuai keadaannya dan memberi tahu bila uang kurang."""
        cid = item["id"]
        if self.eggs.equipped(kind) == cid:
            return
        if self.eggs.owns(kind, cid):
            self.eggs.equip(kind, cid)
            self.say(f"{item['name']} equipped", (140, 235, 160))
            self.app.sfx.play("confirm")
            return
        if self.eggs.buy(kind, cid):
            self.say(f"{item['name']} bought and equipped", (255, 214, 90))
            self.app.sfx.play("coin")
        else:
            self.shake = 0.35
            self.say("Not enough money. Sell some fish first", (255, 140, 120))
            self.app.sfx.play("error", 0.6)

    def button_rect(self, card):
        return pygame.Rect(card.x + 12, card.bottom - 44, card.w - 24, 34)

    def event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_i):
                self.app.sfx.play("click")
                self.close()
            elif e.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                self.set_tab(1 - self.tab)
            elif e.key == pygame.K_DOWN:
                self.scroll_to(self.target[self.tab] + 60)
            elif e.key == pygame.K_UP:
                self.scroll_to(self.target[self.tab] - 60)
            elif e.key == pygame.K_PAGEDOWN:
                self.scroll_to(self.target[self.tab] + self.area().h)
            elif e.key == pygame.K_PAGEUP:
                self.scroll_to(self.target[self.tab] - self.area().h)
            elif e.key == pygame.K_HOME:
                self.scroll_to(0)
            elif e.key == pygame.K_END:
                self.scroll_to(self.max_scroll())
            return
        if e.type == pygame.MOUSEWHEEL:
            self.scroll_to(self.target[self.tab] - e.y * 64)
            return
        local = None
        if hasattr(e, "pos"):
            local = (e.pos[0] - self.rect.x, e.pos[1] - self.rect.y)
        if e.type == pygame.MOUSEMOTION:
            self.close_hover = self.close_rect().collidepoint(e.pos)
            if self.drag is not None:
                tr = self.track()
                th = self.thumb()
                span = max(1, tr.h - th.h)
                k = (e.pos[1] - self.drag - tr.y) / span
                self.target[self.tab] = self.scroll[self.tab] = max(0.0, min(1.0, k)) * self.max_scroll()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.close_rect().collidepoint(e.pos):
                self.close_down = True
                return
            for i in range(2):
                if self.tab_rect(i).collidepoint(local):
                    self.set_tab(i)
                    return
            th = self.thumb()
            if th and th.collidepoint(e.pos):
                self.drag = e.pos[1] - th.y
                return
            if th and self.track().collidepoint(e.pos):
                self.scroll_to(self.target[self.tab] + (self.area().h if e.pos[1] > th.centery else -self.area().h))
                return
            a = self.area()
            if a.collidepoint(local):
                cy = local[1] - a.y + int(self.scroll[self.tab])
                cx = local[0] - a.x
                if self.tab == 0:
                    for c, r in zip(self.items, self.fish_layout()):
                        if r.collidepoint((cx, cy)):
                            if id(c) in self.sel:
                                self.sel.discard(id(c))
                            else:
                                self.sel.add(id(c))
                            self.confirm_t = 0.0
                            self.app.sfx.play("pop", 0.6)
                            return
                else:
                    for ent in self.shop_layout()[0]:
                        if "item" in ent and self.button_rect(ent["rect"]).collidepoint((cx, cy)):
                            self.shop_action(ent["kind"], ent["item"])
                            return
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = None
            was = self.close_down
            self.close_down = False
            if was and self.close_rect().collidepoint(e.pos):
                self.app.sfx.play("click")
                self.close()
                return
        if self.tab == 0 and local is not None:
            ev = pygame.event.Event(e.type, **{k: v for k, v in e.__dict__.items() if k != "pos"}, pos=local)
            if not self.btn_all.handle_event(ev, self.app):
                self.btn_sell.handle_event(ev, self.app)

    def update(self, dt):
        self.t += dt
        m = self.app.mouse
        for i in range(2):
            self.scroll[i] += (self.target[i] - self.scroll[i]) * min(1.0, dt * 14)
            if abs(self.target[i] - self.scroll[i]) < 0.3:
                self.scroll[i] = self.target[i]
        self.shake = max(0.0, self.shake - dt)
        self.confirm_t = max(0.0, self.confirm_t - dt)
        if self.toast:
            self.toast[1] -= dt
            if self.toast[1] <= 0:
                self.toast = None
        self.close_hover = self.close_rect().collidepoint(m)
        lm = (m[0] - self.rect.x, m[1] - self.rect.y)
        hand = self.close_hover
        th = self.thumb()
        if th and th.collidepoint(m):
            hand = True
        for i in range(2):
            if self.tab_rect(i).collidepoint(lm):
                hand = True
        a = self.area()
        if a.collidepoint(lm):
            cy = lm[1] - a.y + int(self.scroll[self.tab])
            cx = lm[0] - a.x
            if self.tab == 0:
                hand = hand or any(r.collidepoint((cx, cy)) for r in self.fish_layout())
            else:
                hand = hand or any("item" in ent and self.button_rect(ent["rect"]).collidepoint((cx, cy)) for ent in self.shop_layout()[0])
        if hand:
            ui.HOT["hand"] = True
        self.btn_all.visible = self.btn_sell.visible = self.tab == 0
        self.btn_all.label = "Clear" if self.items and self.sel == {id(c) for c in self.items} else "Select All"
        self.btn_all.enabled = bool(self.items)
        self.btn_sell.enabled = bool(self.sel)
        risky = self.confirm_t > 0
        self.btn_sell.label = "Tap again to confirm" if risky else "Sell Selected"
        self.btn_sell.style = "danger" if risky else "success"
        self.btn_all.update(dt, lm)
        self.btn_sell.update(dt, lm)

    def sprite(self, idx, box):
        """Mengambil gambar ikan yang diperkecil agar muat pada kotak lalu menyimpannya."""
        key = (idx, box)
        s = self.cache.get(key)
        if s is None:
            src = art_egg.fishmail(idx, 3)
            k = min(box[0] / src.get_width(), box[1] / src.get_height(), 1.0)
            s = pygame.transform.smoothscale(src, (max(1, int(src.get_width() * k)), max(1, int(src.get_height() * k))))
            self.cache[key] = s
        return s

    def draw_fish_card(self, p, c, rect):
        idx = c["r"]
        f = FISH[idx]
        sel = id(c) in self.sel
        pygame.draw.rect(p, (10, 22, 52), rect, border_radius=10)
        top = mix((16, 36, 80), f["color"], 0.18 + (0.22 if sel else 0.0))
        for y in range(rect.h - 2):
            pygame.draw.line(p, mix(top, (8, 18, 44), y / rect.h), (rect.x + 2, rect.y + 1 + y), (rect.right - 3, rect.y + 1 + y))
        pygame.draw.rect(p, (255, 255, 255) if sel else f["color"], rect, 3 if sel else 2, border_radius=10)
        img = self.sprite(idx, (rect.w - 26, 62))
        p.blit(img, img.get_rect(center=(rect.centerx, rect.y + 48)))
        y = rect.y + 88
        for ln in ui.wrap_lines(ui.font(13, True), f["name"], rect.w - 14)[:2]:
            ui.draw_text(p, ln, ui.font(13, True), (236, 244, 255), (rect.centerx, y), "midtop")
            y += 16
        pill = ui.text_surf(ui.font(11, True), f["rarity"].upper(), (255, 255, 255))
        pr = pygame.Rect(0, 0, pill.get_width() + 14, 18)
        pr.midbottom = (rect.centerx, rect.bottom - 8)
        pygame.draw.rect(p, tuple(int(v * 0.6) for v in f["color"]), pr, border_radius=9)
        pygame.draw.rect(p, f["color"], pr, 1, border_radius=9)
        p.blit(pill, pill.get_rect(center=pr.center))
        tag = ui.text_surf(ui.font(12, True), f"${f['price']}", (60, 40, 0))
        tr = pygame.Rect(rect.x + 6, rect.y + 6, tag.get_width() + 12, 20)
        pygame.draw.rect(p, (255, 214, 90), tr, border_radius=10)
        p.blit(tag, tag.get_rect(center=tr.center))
        if sel:
            ck = pygame.Rect(rect.right - 28, rect.y + 6, 22, 22)
            pygame.draw.circle(p, (70, 190, 100), ck.center, 11)
            icons.draw_icon(p, "check", ck.center, 14, (255, 255, 255))

    def draw_shop_card(self, p, kind, item, rect):
        cid = item["id"]
        eq = self.eggs.equipped(kind) == cid
        own = self.eggs.owns(kind, cid)
        pygame.draw.rect(p, (10, 22, 52), rect, border_radius=10)
        for y in range(rect.h - 2):
            pygame.draw.line(p, mix((22, 44, 92), (8, 18, 44), y / rect.h), (rect.x + 2, rect.y + 1 + y), (rect.right - 3, rect.y + 1 + y))
        edge = (255, 214, 90) if eq else ((90, 210, 130) if own else (80, 110, 170))
        pygame.draw.rect(p, edge, rect, 2, border_radius=10)
        if kind == "border":
            c = (rect.centerx, rect.y + 52)
            pygame.draw.circle(p, AV, c, 26)
            pygame.draw.circle(p, (255, 255, 255), c, 26, 2)
            icons.draw_icon(p, "user", c, 30, (255, 255, 255))
            cosmetics.draw_border(p, c, 26, cid, self.t)
        else:
            pr = pygame.Rect(rect.x + 12, rect.y + 12, rect.w - 24, 70)
            if cid == "n0":
                for yy in range(pr.h):
                    pygame.draw.line(p, mix((226, 238, 255), (250, 252, 255), yy / pr.h), (pr.x, pr.y + yy), (pr.right - 1, pr.y + yy))
            else:
                cosmetics.draw_banner(p, pr, cid, self.t)
            pygame.draw.rect(p, (255, 255, 255), pr, 1)
        ui.draw_text(p, item["name"], ui.font(15, True), (236, 244, 255), (rect.centerx, rect.y + 98), "midtop")
        br = self.button_rect(rect)
        can = self.eggs.money >= item["price"]
        if eq:
            pygame.draw.rect(p, (255, 214, 90), br, border_radius=8)
            ui.draw_text(p, "Equipped", ui.font(15, True), (80, 52, 0), br.center, "center")
        elif own:
            p.blit(ui.button_surface(br.w, br.h, "primary", "normal"), br)
            ui.draw_text(p, "Equip", ui.font(15, True), (255, 255, 255), br.center, "center", shadow=(0, 30, 80))
        else:
            style = "success" if can else "disabled"
            p.blit(ui.button_surface(br.w, br.h, style, "normal"), br)
            col = (255, 255, 255) if can else (150, 150, 150)
            ui.draw_text(p, f"Buy  ${item['price']}", ui.font(15, True), col, br.center, "center", shadow=(0, 40, 0) if can else None)

    def draw_wallet(self, p, client):
        txt = ui.text_surf(ui.font(18, True), f"${self.eggs.money}", (80, 52, 0))
        pr = pygame.Rect(0, 0, 44 + txt.get_width() + 14, 34)
        pr.topright = (client.right - 16, client.y + 10)
        pygame.draw.rect(p, (255, 226, 120), pr, border_radius=17)
        pygame.draw.rect(p, (196, 140, 24), pr, 2, border_radius=17)
        pygame.draw.circle(p, (232, 168, 20), (pr.x + 19, pr.centery), 11)
        pygame.draw.circle(p, (255, 240, 170), (pr.x + 19, pr.centery), 8, 2)
        ui.draw_text(p, "$", ui.font(14, True), (140, 90, 0), (pr.x + 19, pr.centery), "center")
        p.blit(txt, txt.get_rect(midleft=(pr.x + 38, pr.centery)))

    def draw_tabs(self, p):
        for i, name in enumerate(("Fish", "Shop")):
            r = self.tab_rect(i)
            on = i == self.tab
            p.blit(ui.button_surface(r.w, r.h, "primary" if on else "default", "normal"), r)
            ui.draw_text(p, name, ui.font(16, True), (255, 255, 255) if on else (40, 52, 80), r.center, "center", shadow=(0, 30, 80) if on else None)

    def draw_panel(self, p):
        r = pygame.Rect(0, 0, self.rect.w, self.rect.h)
        client = ui.draw_window(p, r, "Tackle Box - Phisherman", icon=lambda s, c, z, col: icons.draw_icon(s, "folder", c, z, (255, 224, 110)))
        if self.close_hover:
            cr = pygame.Rect(self.rect.w - 8 - 98 + 52, 1, 46, 20)
            pygame.draw.rect(p, (255, 120, 100), cr, border_bottom_right_radius=5)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 17, cr.y + 5), (cr.x + 27, cr.y + 14), 3)
            pygame.draw.line(p, (255, 255, 255), (cr.x + 27, cr.y + 5), (cr.x + 17, cr.y + 14), 3)
        pygame.draw.rect(p, (236, 242, 252), client)
        ui.draw_text(p, "Tackle Box", ui.font(24, True), (20, 44, 92), (client.x + 16, client.y + 10))
        self.draw_wallet(p, client)
        self.draw_tabs(p)
        a = self.area()
        if self.tab == 0:
            cx = client.right - 16
            for i in range(len(FISH) - 1, -1, -1):
                f = FISH[i]
                txt = ui.text_surf(ui.font(13, True), f"{self.counts[i]}", (255, 255, 255))
                pr = pygame.Rect(0, 0, 40 + txt.get_width(), 28)
                pr.topright = (cx, client.y + 58)
                pygame.draw.rect(p, tuple(int(v * 0.55) for v in f["color"]), pr, border_radius=14)
                pygame.draw.rect(p, f["color"], pr, 2, border_radius=14)
                img = self.sprite(i, (22, 14))
                p.blit(img, img.get_rect(center=(pr.x + 20, pr.centery)))
                p.blit(txt, txt.get_rect(midleft=(pr.x + 34, pr.centery)))
                cx = pr.x - 8
        pygame.draw.rect(p, (14, 28, 62), a.inflate(8, 8), border_radius=8)
        pygame.draw.rect(p, (60, 90, 150), a.inflate(8, 8), 1, border_radius=8)
        off = int(self.scroll[self.tab])
        if self.tab == 0:
            if not self.items:
                ic = art_egg.tackle_icon(7)
                p.blit(ic, ic.get_rect(center=(a.centerx, a.centery - 30 + math.sin(self.t * 2.2) * 4)))
                ui.draw_text(p, "No fish yet", ui.font(22, True), (230, 242, 255), (a.centerx, a.centery + 46), "center")
                ui.draw_text(p, "Press START and cast your line to catch your first fishmail.", ui.font(15), (160, 190, 230), (a.centerx, a.centery + 76), "center")
            else:
                p.set_clip(a)
                for c, rr in zip(self.items, self.fish_layout()):
                    cr = rr.move(a.x, a.y - off)
                    if cr.bottom < a.y or cr.y > a.bottom:
                        continue
                    self.draw_fish_card(p, c, cr)
                p.set_clip(None)
        else:
            p.set_clip(a)
            ents, _ = self.shop_layout()
            for ent in ents:
                cr = ent["rect"].move(a.x, a.y - off)
                if cr.bottom < a.y or cr.y > a.bottom:
                    continue
                if "head" in ent:
                    ui.draw_text(p, ent["head"], ui.font(18, True), (200, 224, 255), (cr.x + 4, cr.y + 8))
                    pygame.draw.line(p, (70, 110, 180), (cr.x + 4, cr.bottom - 2), (cr.right - 4, cr.bottom - 2))
                else:
                    self.draw_shop_card(p, ent["kind"], ent["item"], cr)
            p.set_clip(None)
        if self.max_scroll() > 0:
            trk = self.track()
            tr = pygame.Rect(trk.x - self.rect.x, trk.y - self.rect.y, 12, a.h)
            pygame.draw.rect(p, (200, 214, 236), tr, border_radius=6)
            th = self.thumb()
            if th:
                tl = pygame.Rect(th.x - self.rect.x, th.y - self.rect.y, th.w, th.h)
                pygame.draw.rect(p, (86, 130, 200) if self.drag is None else (50, 100, 180), tl, border_radius=6)
                pygame.draw.rect(p, (255, 255, 255), tl.inflate(-6, -10), 1, border_radius=4)
        base = client.bottom - 34
        if self.tab == 0:
            n = len(self.sel)
            ui.draw_text(p, f"Selected {n} fish   |   Value ${self.worth()}", ui.font(16, True), (30, 50, 96), (client.x + 18, client.bottom - 50))
            ui.draw_text(p, "Click a fish to select it. Mouse wheel to scroll", ui.font(13), (110, 124, 150), (client.x + 18, client.bottom - 28))
            self.btn_all.draw(p)
            self.btn_sell.draw(p)
        else:
            ui.draw_text(p, "Equipped skins appear in the Player List", ui.font(16, True), (30, 50, 96), (client.x + 18, client.bottom - 50))
            ui.draw_text(p, "Earn money by selling fish. Mouse wheel to scroll", ui.font(13), (110, 124, 150), (client.x + 18, client.bottom - 28))
        if self.toast:
            ts = ui.text_surf(ui.font(16, True), self.toast[0], (255, 255, 255))
            tr = pygame.Rect(0, 0, ts.get_width() + 36, 38)
            tr.center = (client.centerx, a.bottom - 28)
            sh = int(math.sin(self.t * 60) * 5 * (self.shake / 0.35)) if self.shake > 0 else 0
            tr.x += sh
            ov = pygame.Surface(tr.size, pygame.SRCALPHA)
            pygame.draw.rect(ov, (10, 20, 50, 235), ov.get_rect(), border_radius=19)
            pygame.draw.rect(ov, self.toast[2], ov.get_rect(), 2, border_radius=19)
            ov.blit(ts, ts.get_rect(center=(tr.w // 2, tr.h // 2)))
            ov.set_alpha(int(255 * min(1.0, self.toast[1] * 3)))
            p.blit(ov, tr)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        k = min(1.0, self.t / 0.28)
        ease = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2
        scale = 0.82 + 0.18 * ease
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.draw_panel(panel)
        if scale < 0.999:
            panel = pygame.transform.smoothscale(panel, (max(1, int(self.rect.w * scale)), max(1, int(self.rect.h * scale))))
        panel.set_alpha(int(255 * min(1.0, k * 1.6)))
        surf.blit(panel, panel.get_rect(center=self.rect.center))

import pygame
from . import ui, icons

OUTLINE_OFFSETS = ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, -2), (1, -2), (-1, 2), (1, 2))


def people_art(w, h):
    """Menggambar kumpulan siluet pemain anonim berbagai ukuran dan warna pucat sebagai ilustrasi tombol daftar pemain."""
    art = pygame.Surface((w, h), pygame.SRCALPHA)
    spots = ((0.07, 0.62, (255, 255, 255), 70), (0.19, 0.78, (190, 232, 255), 90), (0.31, 0.7, (255, 232, 160), 80), (0.5, 1.0, (255, 255, 255), 56), (0.69, 0.72, (190, 255, 220), 80), (0.81, 0.8, (255, 255, 255), 90), (0.93, 0.62, (255, 214, 190), 70))
    base = h + 6
    for fx, k, col, alpha in spots:
        cx = int(w * fx)
        r = max(5, int(h * 0.2 * k))
        head_y = base - int(h * 0.78 * k)
        body = pygame.Surface((r * 5, r * 4), pygame.SRCALPHA)
        c = col + (alpha,)
        pygame.draw.circle(body, c, (r * 5 // 2, r), r)
        pygame.draw.ellipse(body, c, (r * 5 // 2 - int(r * 2.1), int(r * 2.1), int(r * 4.2), int(r * 3.4)))
        art.blit(body, body.get_rect(midtop=(cx, head_y - r)))
    return art


def board_art(w, h):
    """Menggambar podium lima peringkat berwarna emas perak perunggu biru dan hijau dengan mahkota kecil sebagai ilustrasi tombol papan peringkat."""
    art = pygame.Surface((w, h), pygame.SRCALPHA)
    cols = ((255, 204, 64), (190, 204, 226), (226, 148, 90), (110, 168, 240), (90, 206, 186))
    heights = (0.66, 0.54, 0.44, 0.36, 0.28)
    n = 5
    gap = 6
    bw = (w - gap * (n + 1)) // n
    for i in range(n):
        x = gap + i * (bw + gap)
        bh = int(h * heights[i])
        r = pygame.Rect(x, h - bh, bw, bh + 6)
        pygame.draw.rect(art, cols[i] + (150,), r, border_radius=4)
        pygame.draw.rect(art, (255, 255, 255, 120), (r.x, r.y, r.w, 4), border_radius=3)
        pygame.draw.rect(art, (40, 60, 110, 70), r, 1, border_radius=4)
        num = ui.text_surf(ui.font(max(11, h // 4), True), str(i + 1), (255, 255, 255))
        num = num.copy()
        num.set_alpha(120)
        art.blit(num, num.get_rect(midtop=(r.centerx, r.y + 4)))
    icons.draw_icon(art, "crown", (gap + bw // 2, h - int(h * heights[0]) - 8), 14, (255, 200, 40))
    return art


class ArtButton(ui.Button):
    """Tombol bergaya Windows 7 dengan ilustrasi di latar dan teks bergaris tepi agar tetap kontras di atas ilustrasi."""

    def __init__(self, rect, label, callback, style, art, outline, size=18, sound="click"):
        super().__init__(rect, label, callback, style, None, size, True, sound)
        self.art = art
        self.outline = outline
        self.cache = {}

    def layer(self, style, state):
        """Menyusun gambar tombol dasar bersama ilustrasi yang dipotong mengikuti sudut tombol dan menyimpannya."""
        key = (self.rect.w, self.rect.h, style, state)
        img = self.cache.get(key)
        if img is None:
            base = ui.button_surface(self.rect.w, self.rect.h, style, state).copy()
            art = self.art(self.rect.w, self.rect.h)
            art.blit(ui.rounded_mask(self.rect.w, self.rect.h, 5), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            base.blit(art, (0, 0))
            pygame.draw.rect(base, ui.STYLES[style][state][4], (0, 0, self.rect.w, self.rect.h), 1, border_radius=5)
            img = base
            self.cache[key] = img
        return img

    def draw(self, surf):
        if not self.visible:
            return
        style = self.style if self.enabled else "disabled"
        state = "pressed" if (self.press and self.hover) else ("hover" if self.hover else "normal")
        surf.blit(self.layer(style, state), self.rect)
        f = ui.font(self.size, True)
        col = ui.STYLES[style]["text"]
        label = ui.text_surf(f, self.label, col)
        ring = ui.text_surf(f, self.label, self.outline)
        lr = label.get_rect(center=(self.rect.centerx, self.rect.centery + (1 if state == "pressed" else 0)))
        for dx, dy in OUTLINE_OFFSETS:
            surf.blit(ring, lr.move(dx, dy))
        surf.blit(label, lr)

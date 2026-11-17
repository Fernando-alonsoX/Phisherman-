import random
import pygame


def mix(a, b, t):
    """Campuran linear dua warna RGB dengan faktor t."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, f):
    """Menggelapkan atau mencerahkan warna dengan faktor f."""
    if f >= 0:
        return tuple(min(255, int(v + (255 - v) * f)) for v in c[:3])
    return tuple(max(0, int(v * (1 + f))) for v in c[:3])


class Px:
    """Kanvas pixel art kecil dengan primitif gambar tanpa antialias."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.surf = pygame.Surface((w, h), pygame.SRCALPHA)

    def rect(self, x, y, w, h, c):
        pygame.draw.rect(self.surf, c, (int(x), int(y), int(w), int(h)))

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.surf.set_at((int(x), int(y)), c)

    def line(self, x1, y1, x2, y2, c, w=1):
        pygame.draw.line(self.surf, c, (x1, y1), (x2, y2), w)

    def ellipse(self, x, y, w, h, c):
        pygame.draw.ellipse(self.surf, c, (int(x), int(y), int(w), int(h)))

    def circle(self, cx, cy, r, c):
        pygame.draw.circle(self.surf, c, (int(cx), int(cy)), int(r))

    def poly(self, pts, c):
        pygame.draw.polygon(self.surf, c, pts)

    def vgrad(self, x, y, w, h, c1, c2):
        for i in range(int(h)):
            t = i / max(1, h - 1)
            pygame.draw.line(self.surf, mix(c1, c2, t), (x, y + i), (x + w - 1, y + i))

    def hgrad(self, x, y, w, h, c1, c2):
        for i in range(int(w)):
            t = i / max(1, w - 1)
            pygame.draw.line(self.surf, mix(c1, c2, t), (x + i, y), (x + i, y + h - 1))

    def dither(self, x, y, w, h, c, phase=0):
        for j in range(int(h)):
            for i in range(int(w)):
                if (i + j + phase) % 2 == 0:
                    self.px(x + i, y + j, c)

    def speckle(self, x, y, w, h, c, n, seed=1):
        r = random.Random(seed)
        for _ in range(n):
            self.px(x + r.randrange(int(w)), y + r.randrange(int(h)), c)

    def blit(self, other, x, y):
        src = other.surf if isinstance(other, Px) else other
        self.surf.blit(src, (int(x), int(y)))

    def outline(self, color):
        """Memberi outline satu piksel di sekeliling bentuk yang tidak transparan."""
        mask = pygame.mask.from_surface(self.surf, 10)
        out = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pts = set()
        for x in range(self.w):
            for y in range(self.h):
                if mask.get_at((x, y)):
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and mask.get_at((nx, ny)):
                        pts.add((x, y))
                        break
        for p in pts:
            out.set_at(p, color)
        out.blit(self.surf, (0, 0))
        self.surf = out

    def scaled(self, k):
        return pygame.transform.scale(self.surf, (self.w * k, self.h * k))


def radial_glow(radius, color, strength=1.0):
    """Membuat cahaya radial lembut dengan RGB memudar ke hitam untuk dipakai dengan blend aditif."""
    size = radius * 2
    surf = pygame.Surface((size, size))
    surf.fill((0, 0, 0))
    for r in range(radius, 0, -1):
        t = 1 - r / radius
        k = (t ** 2) * strength
        c = (min(255, int(color[0] * k)), min(255, int(color[1] * k)), min(255, int(color[2] * k)))
        pygame.draw.circle(surf, c, (radius, radius), r)
    return surf


def blur(surface, factor=8):
    """Mengaburkan surface dengan mengecilkan lalu membesarkan kembali."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // factor), max(1, h // factor)))
    small = pygame.transform.smoothscale(small, (max(1, w // (factor * 2)), max(1, h // (factor * 2))))
    return pygame.transform.smoothscale(small, (w, h))


def aa_surface(size, draw_fn, ss=4):
    """Menggambar dengan supersampling lalu mengecilkan agar tepi halus."""
    w, h = size
    big = pygame.Surface((w * ss, h * ss), pygame.SRCALPHA)
    draw_fn(big, ss)
    return pygame.transform.smoothscale(big, (w, h))

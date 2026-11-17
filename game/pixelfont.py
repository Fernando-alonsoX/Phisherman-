import pygame

_RAW = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.###.",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": ".###.|..#..|..#..|..#..|..#..|..#..|.###.",
    "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "N": "#...#|##..#|#.#.#|#..##|#...#|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "#####|...#.|..#..|...#.|....#|#...#|.###.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": "..##.|.#...|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|...#.|.##..",
    ".": ".....|.....|.....|.....|.....|.##..|.##..",
    ",": ".....|.....|.....|.....|.##..|..#..|.#...",
    "!": "..#..|..#..|..#..|..#..|..#..|.....|..#..",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    ":": ".....|.##..|.##..|.....|.##..|.##..|.....",
    "-": ".....|.....|.....|#####|.....|.....|.....",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "$": "..#..|.####|#.#..|.###.|..#.#|####.|..#..",
    "/": "....#|....#|...#.|..#..|.#...|#....|#....",
    "'": "..#..|..#..|.#...|.....|.....|.....|.....",
    "%": "##..#|##..#|...#.|..#..|.#...|#..##|#..##",
    "(": "...#.|..#..|.#...|.#...|.#...|..#..|...#.",
    ")": ".#...|..#..|...#.|...#.|...#.|..#..|.#...",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "=": ".....|#####|.....|#####|.....|.....|.....",
    " ": ".....|.....|.....|.....|.....|.....|.....",
}

GLYPHS = {k: [row for row in v.split("|")] for k, v in _RAW.items()}
_CACHE = {}


def measure(text, scale=4, spacing=1):
    """Menghitung ukuran piksel layar dari teks pixel font."""
    n = len(text)
    if n == 0:
        return 0, 7 * scale
    return (n * 5 + (n - 1) * spacing) * scale, 7 * scale


def _mask(text, spacing):
    cells = set()
    x0 = 0
    for ch in text.upper():
        g = GLYPHS.get(ch, GLYPHS["?"])
        for y, row in enumerate(g):
            for x, v in enumerate(row):
                if v == "#":
                    cells.add((x0 + x, y))
        x0 += 5 + spacing
    return cells, max(0, x0 - spacing)


def render(text, scale=4, color=(255, 255, 255), grad=None, outline=None, shadow=None, spacing=1, thick=1):
    """Merender teks pixel font menjadi Surface dengan outline gradien dan bayangan opsional."""
    key = (text, scale, color, grad, outline, shadow, spacing, thick)
    if key in _CACHE:
        return _CACHE[key]
    cells, width = _mask(text, spacing)
    pad = thick + 2
    sx = shadow[0] if shadow else 0
    sy = shadow[1] if shadow else 0
    w = width + pad * 2 + abs(sx)
    h = 7 + pad * 2 + abs(sy)
    ox = pad + (abs(sx) if sx < 0 else 0)
    oy = pad + (abs(sy) if sy < 0 else 0)
    small = pygame.Surface((w, h), pygame.SRCALPHA)

    def dilate(src, r):
        out = set(src)
        for (x, y) in src:
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    out.add((x + dx, y + dy))
        return out

    base = {(x + ox, y + oy) for (x, y) in cells}
    if shadow:
        sh = dilate(base, thick) if outline else base
        for (x, y) in sh:
            small.set_at((x + sx, y + sy), shadow[2])
    if outline:
        for (x, y) in dilate(base, thick):
            small.set_at((x, y), outline)
    for (x, y) in base:
        if grad:
            t = (y - oy) / 6.0
            c = tuple(int(grad[0][i] + (grad[1][i] - grad[0][i]) * t) for i in range(3))
        else:
            c = color
        small.set_at((x, y), c)
    surf = pygame.transform.scale(small, (w * scale, h * scale))
    _CACHE[key] = surf
    return surf


def stamp(canvas, ch, x, y, color):
    """Menempelkan satu glyph langsung ke kanvas pixel pada skala satu tanpa padding."""
    g = GLYPHS.get(ch.upper(), GLYPHS["?"])
    for j, row in enumerate(g):
        for i, v in enumerate(row):
            if v == "#":
                canvas.px(x + i, y + j, color)

from . import art_rooms, art_char, art_items, art_ui
from . import config as C

BUILDERS = {
    "slum_room": art_rooms.slum_room,
    "building": art_rooms.company_building,
    "office_room": art_rooms.office_room,
    "analyst_room": art_rooms.analyst_room,
    "story_room": art_rooms.story_room,
    "compose_room": art_rooms.compose_room,
    "prison_room": art_rooms.prison_room,
    "prison_bars": art_rooms.prison_bars,
    "cyber_bg": art_rooms.cyber_bg,
    "menu_bg": art_rooms.menu_bg,
    "story_card": art_rooms.story_card_art,
    "live_card": art_rooms.live_card_art,
    "aero": lambda: art_ui.aero_wallpaper(C.BASE_W, C.BASE_H),
    "aero_lab": lambda: art_ui.aero_wallpaper(C.BASE_W, C.BASE_H, (4, 16, 52), (14, 70, 150), (70, 170, 215), 9),
    "desktop": lambda: art_ui.desktop(900, 480),
    "taskbar": lambda: art_ui.taskbar(900, 40),
}

PRELOAD = ["menu_bg", "story_card", "live_card", "slum_room", "story_room", "compose_room", "building", "office_room", "analyst_room", "desktop", "taskbar", "cyber_bg", "prison_room", "prison_bars", "aero", "aero_lab"]


class Assets:
    """Penyimpan cache seluruh ilustrasi buatan sendiri agar tiap gambar hanya dibuat sekali."""

    def __init__(self):
        self.cache = {}

    def get(self, name):
        if name not in self.cache:
            self.cache[name] = BUILDERS[name]()
        return self.cache[name]

    def portrait(self, expr, size=120):
        key = ("portrait", expr, size)
        if key not in self.cache:
            self.cache[key] = art_char.draw_portrait(expr, size)
        return self.cache[key]

    def man(self, pose, expr, light=None, scale=3):
        key = ("man", pose, expr, light, scale)
        if key not in self.cache:
            import pygame
            spr = art_char.draw_man(pose, expr, light)
            self.cache[key] = pygame.transform.scale(spr, (spr.get_width() * scale, spr.get_height() * scale))
        return self.cache[key]

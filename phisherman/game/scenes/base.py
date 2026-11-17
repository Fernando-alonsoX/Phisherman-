class Scene:
    """Kelas dasar semua scene berisi alur enter event update draw dan permintaan keluar."""

    hud = None
    counter = False
    exit_button = True
    exit_kind = "story"
    music_level = 1.0
    music_track = None

    def __init__(self, app):
        self.app = app

    def enter(self):
        pass

    def backdrop_art(self):
        return None

    def event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def on_escape(self):
        self.on_exit_request()

    def on_exit_request(self):
        self.app.open_exit(self.exit_kind)

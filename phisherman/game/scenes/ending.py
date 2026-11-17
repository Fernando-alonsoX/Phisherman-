def make_ending(app):
    if app.session.won:
        from .ending_win import WinScene
        return WinScene(app)
    from .ending_lose import LoseScene
    return LoseScene(app)

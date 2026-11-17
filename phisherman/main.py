import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    """Titik masuk game Phisherman dengan opsi memilih berkas model pkl lewat argumen --model."""
    parser = argparse.ArgumentParser(description="Phisherman")
    parser.add_argument("--model", default=None, help="jalur berkas model .pkl")
    parser.add_argument("--demo", action="store_true", help="pakai penilai rule-based sementara untuk menguji alur dan ending")
    args = parser.parse_args()
    from game.app import App
    from game.model_adapter import ModelAdapter
    from game.scenes.boot import BootScene

    app = App(ModelAdapter(args.model, test_mode=args.demo))
    app.set_scene(BootScene(app))
    app.run()


if __name__ == "__main__":
    main()

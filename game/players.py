import json
import os
import re
import time
from . import config as C

NAME_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.\-]*$")


def email_handle(name):
    """Mengubah nama pemain menjadi bagian depan alamat email huruf kecil tanpa spasi atau simbol aneh."""
    h = re.sub(r"[^a-z0-9]+", ".", name.strip().lower()).strip(".")
    return h or "player"


class PlayerStore:
    """Penyimpan data pemain berupa daftar nama, riwayat permainan, statistik, dan papan peringkat dalam satu berkas json."""

    def __init__(self, path=None, persist=True):
        self.path = path or C.PLAYERS_PATH
        self.persist = persist
        self.players = {}
        if persist:
            self.load()

    def load(self):
        """Membaca berkas pemain dan mengabaikan berkas rusak agar game tetap berjalan."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.players = data.get("players", {}) if isinstance(data, dict) else {}
        except Exception:
            self.players = {}

    def save(self):
        """Menyimpan data pemain secara atomik ke disk kecuali pada mode uji yang hanya memakai memori."""
        if not self.persist:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"players": self.players}, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def key(self, name):
        return name.strip().lower()

    def exists(self, name):
        return self.key(name) in self.players

    def validate_new(self, name):
        """Memeriksa nama baru lalu mengembalikan pasangan sah dan pesan kesalahan berbahasa Inggris."""
        n = name.strip()
        if not n:
            return False, "Name cannot be empty."
        if len(n) < C.MIN_NAME:
            return False, f"Name must be at least {C.MIN_NAME} characters."
        if len(n) > C.MAX_NAME:
            return False, f"Name must be at most {C.MAX_NAME} characters."
        if not NAME_RX.match(n):
            return False, "Use letters, numbers, spaces, dots, or dashes only."
        if self.exists(n):
            return False, "That name is taken. Pick another or log in from Player List."
        return True, ""

    def add(self, name):
        """Mendaftarkan pemain baru dan mengembalikan nama yang tersimpan."""
        n = " ".join(name.strip().split())
        self.players[self.key(n)] = {"name": n, "created": time.time(), "last": time.time(), "runs": []}
        self.save()
        return n

    def touch(self, name):
        """Menandai pemain baru saja masuk sehingga muncul di urutan atas daftar."""
        p = self.players.get(self.key(name))
        if p:
            p["last"] = time.time()
            self.save()

    def record_run(self, name, score, money, wins, won, rounds):
        """Mencatat satu permainan story yang selesai lengkap dengan ringkasan tiap ronde."""
        p = self.players.get(self.key(name))
        if not p:
            self.add(name)
            p = self.players[self.key(name)]
        p["runs"].append({"time": time.time(), "score": int(score), "money": int(money), "wins": int(wins), "won": bool(won), "rounds": list(rounds)})
        p["last"] = time.time()
        self.save()

    def names(self):
        """Daftar nama pemain dari yang terakhir bermain."""
        items = sorted(self.players.values(), key=lambda p: p.get("last", 0), reverse=True)
        return [p["name"] for p in items]

    def stats(self, name):
        """Menghitung statistik lengkap seorang pemain dari seluruh riwayat permainannya."""
        p = self.players.get(self.key(name))
        out = {"name": name, "games": 0, "best": 0, "total": 0, "avg": 0, "won": 0, "money_best": 0, "money_total": 0, "passed": 0, "caught": 0, "malware": 0, "jackpots": 0, "last": 0, "rank": None, "created": 0}
        if not p:
            return out
        out["name"] = p["name"]
        out["created"] = p.get("created", 0)
        out["last"] = p.get("last", 0)
        runs = p.get("runs", [])
        out["games"] = len(runs)
        for r in runs:
            out["best"] = max(out["best"], r.get("score", 0))
            out["total"] += r.get("score", 0)
            out["won"] += 1 if r.get("won") else 0
            out["money_best"] = max(out["money_best"], r.get("money", 0))
            out["money_total"] += r.get("money", 0)
            for code in r.get("rounds", []):
                if code in ("pass", "jackpot"):
                    out["passed"] += 1
                else:
                    out["caught"] += 1
                if code == "jackpot":
                    out["jackpots"] += 1
                if code == "busted":
                    out["malware"] += 1
        out["avg"] = int(out["total"] / out["games"]) if out["games"] else 0
        board = self.leaderboard(1000)
        for i, row in enumerate(board):
            if row["name"].lower() == p["name"].lower():
                out["rank"] = i + 1
        return out

    def leaderboard(self, limit=5):
        """Peringkat pemain berdasarkan skor terbaik tertinggi dengan hanya pemain yang pernah menamatkan permainan."""
        rows = []
        for p in self.players.values():
            runs = p.get("runs", [])
            if not runs:
                continue
            best = max(runs, key=lambda r: (r.get("score", 0), -r.get("time", 0)))
            rows.append({"name": p["name"], "score": best.get("score", 0), "money": best.get("money", 0), "games": len(runs), "time": best.get("time", 0)})
        rows.sort(key=lambda r: (-r["score"], r["time"]))
        return rows[:limit]

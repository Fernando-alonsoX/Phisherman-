import json
import os
import random
import time
from . import config as C
from . import cosmetics

CAP = 600

FISH = [
    {
        "name": "Junk Mail Minnow",
        "rarity": "Common",
        "color": (196, 206, 222),
        "weight": 30,
        "stages": 2,
        "green": 0.32,
        "period": 2.2,
        "passes": 3.0,
        "wobble": 0.0,
        "miss": 0.6,
        "storm": 0.0,
        "pause": 0.55,
        "price": 10,
        "info": "Bulk spam that floods every inbox. Annoying, but rarely dangerous.",
        "tip": "Never click unsubscribe links in mail from unknown senders.",
    },
    {
        "name": "Promo Perch",
        "rarity": "Uncommon",
        "color": (116, 224, 136),
        "weight": 25,
        "stages": 3,
        "green": 0.27,
        "period": 2.1,
        "passes": 3.0,
        "wobble": 0.0,
        "miss": 0.6,
        "storm": 0.35,
        "pause": 0.7,
        "price": 25,
        "info": "Fake discounts and free prize offers that tempt people to click fast.",
        "tip": "If a deal sounds too good to be true, it almost always is.",
    },
    {
        "name": "Spoof Snapper",
        "rarity": "Rare",
        "color": (96, 164, 255),
        "weight": 20,
        "stages": 4,
        "green": 0.22,
        "period": 2.0,
        "passes": 2.8,
        "wobble": 0.15,
        "miss": 0.65,
        "storm": 0.6,
        "pause": 0.9,
        "price": 60,
        "info": "Wears the mask of a trusted brand and sends from a look-alike address.",
        "tip": "Read the sender address letter by letter before you trust it.",
    },
    {
        "name": "Spear Phish Barracuda",
        "rarity": "Epic",
        "color": (196, 128, 255),
        "weight": 15,
        "stages": 5,
        "green": 0.165,
        "period": 1.7,
        "passes": 2.4,
        "wobble": 0.35,
        "miss": 0.7,
        "storm": 0.85,
        "pause": 1.1,
        "price": 150,
        "info": "Targets one person with their real name, school, and friends to sound convincing.",
        "tip": "Be careful what you share online. Attackers read it too.",
    },
    {
        "name": "Zero-Day Leviathan",
        "rarity": "Legendary",
        "color": (255, 204, 74),
        "weight": 10,
        "stages": 7,
        "green": 0.13,
        "period": 1.55,
        "passes": 2.2,
        "wobble": 0.55,
        "miss": 0.8,
        "storm": 1.0,
        "pause": 1.3,
        "price": 400,
        "info": "A monster that abuses a flaw nobody has fixed yet. Almost impossible to spot.",
        "tip": "Keep your apps and system updated so known flaws get patched.",
    },
]


def roll(rng=random):
    """Mengundi jenis ikan dengan peluang tetap 30 25 20 15 dan 10 persen menurut kelangkaan."""
    return rng.choices(range(len(FISH)), weights=[f["weight"] for f in FISH], k=1)[0]


def pkey(name):
    """Mengubah nama pemain menjadi kunci huruf kecil dan memakai guest bila kosong."""
    n = (name or "").strip().lower()
    return n or "guest"


def blank():
    """Membuat data awal seorang pemain berisi koleksi kosong uang nol dan skin bawaan."""
    return {
        "catches": [],
        "money": 0,
        "owned": {"border": ["b0"], "banner": ["n0"]},
        "equip": {"border": "b0", "banner": "n0"},
    }


class EggStore:
    """Penyimpan koleksi ikan uang dan skin kosmetik setiap pemain dalam berkas json terpisah dari data pemain."""

    def __init__(self, path=None, persist=True):
        self.path = path or C.EGG_PATH
        self.persist = persist
        self.players = {}
        self.owner = "guest"
        if persist:
            self.load()

    def load(self):
        """Membaca berkas dan membersihkan data rusak agar game tetap berjalan."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            rows = data.get("players", {}) if isinstance(data, dict) else {}
            for k, v in rows.items():
                self.players[k] = self.clean(v)
        except Exception:
            self.players = {}

    def clean(self, v):
        """Menyaring data satu pemain agar hanya berisi nilai yang sah."""
        out = blank()
        if not isinstance(v, dict):
            return out
        for c in v.get("catches", []):
            try:
                r = int(c["r"])
                if 0 <= r < len(FISH):
                    out["catches"].append({"r": r, "t": int(c.get("t", 0))})
            except Exception:
                continue
        try:
            out["money"] = max(0, int(v.get("money", 0)))
        except Exception:
            out["money"] = 0
        for kind in cosmetics.KINDS:
            own = v.get("owned", {}).get(kind, []) if isinstance(v.get("owned"), dict) else []
            for cid in own:
                if cosmetics.valid(kind, cid) and cid not in out["owned"][kind]:
                    out["owned"][kind].append(cid)
            eq = v.get("equip", {}).get(kind) if isinstance(v.get("equip"), dict) else None
            if eq in out["owned"][kind]:
                out["equip"][kind] = eq
        return out

    def save(self):
        """Menyimpan data secara atomik ke disk kecuali pada mode uji yang hanya memakai memori."""
        if not self.persist:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"players": self.players}, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def use(self, name):
        """Mengganti pemain aktif yang datanya dipakai oleh semua fungsi koleksi."""
        self.owner = pkey(name)

    def prof(self, name=None):
        """Mengambil data pemain aktif atau pemain bernama dan membuatnya bila belum ada."""
        k = self.owner if name is None else pkey(name)
        p = self.players.get(k)
        if p is None:
            p = blank()
            self.players[k] = p
        return p

    @property
    def catches(self):
        return self.prof()["catches"]

    @property
    def money(self):
        return self.prof()["money"]

    def add(self, idx):
        """Menambah satu ikan ke koleksi pemain aktif lalu menyimpannya dan mengembalikan apakah jenis ini baru pertama kali didapat."""
        p = self.prof()
        fresh = not any(c["r"] == idx for c in p["catches"])
        p["catches"].append({"r": idx, "t": int(time.time())})
        if len(p["catches"]) > CAP:
            p["catches"] = p["catches"][-CAP:]
        self.save()
        return fresh

    def counts(self):
        """Menghitung jumlah ikan pemain aktif untuk setiap tingkat kelangkaan."""
        out = [0] * len(FISH)
        for c in self.catches:
            out[c["r"]] += 1
        return out

    def sell(self, items):
        """Menjual ikan terpilih dari koleksi pemain aktif lalu menambah uangnya dan mengembalikan jumlah yang didapat."""
        p = self.prof()
        ids = {id(c) for c in items}
        gain = 0
        keep = []
        for c in p["catches"]:
            if id(c) in ids:
                gain += FISH[c["r"]]["price"]
            else:
                keep.append(c)
        p["catches"] = keep
        p["money"] += gain
        self.save()
        return gain

    def owns(self, kind, cid):
        return cid in self.prof()["owned"][kind]

    def equipped(self, kind):
        return self.prof()["equip"][kind]

    def buy(self, kind, cid):
        """Membeli skin bila uang cukup dan belum dimiliki lalu langsung memakainya dan mengembalikan berhasil atau tidak."""
        item = cosmetics.find(kind, cid)
        p = self.prof()
        if item is None or cid in p["owned"][kind] or p["money"] < item["price"]:
            return False
        p["money"] -= item["price"]
        p["owned"][kind].append(cid)
        p["equip"][kind] = cid
        self.save()
        return True

    def equip(self, kind, cid):
        """Memakai skin yang sudah dimiliki pemain aktif."""
        p = self.prof()
        if cid in p["owned"][kind]:
            p["equip"][kind] = cid
            self.save()
            return True
        return False

    def look(self, name):
        """Mengambil skin yang dipakai pemain bernama tanpa membuat data baru bila belum pernah main."""
        p = self.players.get(pkey(name))
        if p is None:
            return dict(cosmetics.DEFAULTS)
        return dict(p["equip"])

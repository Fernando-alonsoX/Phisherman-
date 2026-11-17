from . import config as C


class Round:
    """Catatan satu email yang dikirim pemain berisi isi pesan lampiran hasil deteksi hasil gacha dan perolehan poin."""

    def __init__(self, text, subject="", sender="", recipient="", attachment=None):
        self.body = text
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.attachment = attachment
        self.malware = None
        self.prob = 0.0
        self.pred_phishing = True
        self.verified = False
        self.ai_correct = None
        self.success = False
        self.outcome = None
        self.points = 0
        self.money = 0
        self.label = None

    @property
    def text(self):
        """Teks lengkap untuk dinilai model yaitu subjek diikuti isi pesan."""
        return (self.subject + "\n\n" + self.body).strip() if self.subject else self.body


class Session:
    """Status permainan Story Mode meliputi pemain uang poin jumlah email dan riwayat tiap ronde."""

    def __init__(self):
        self.player = ""
        self.reset()

    def reset(self):
        self.money = C.START_MONEY
        self.score = 0
        self.sent = 0
        self.rounds = []
        self.recorded = False

    @property
    def wins(self):
        return sum(1 for r in self.rounds if r.success)

    @property
    def finished(self):
        return len(self.rounds) >= C.TOTAL_ROUNDS and all(r.verified for r in self.rounds)

    @property
    def won(self):
        return self.wins >= C.WIN_THRESHOLD

    def apply(self, rd, outcome):
        """Menerapkan hasil satu ronde ke uang dan poin lalu menyimpannya pada ronde itu."""
        rd.outcome = outcome
        rd.success = outcome["success"]
        rd.points = outcome["points"]
        rd.money = outcome["money"]
        self.money += outcome["money"]
        self.score = max(0, self.score + outcome["points"])
        rd.verified = True

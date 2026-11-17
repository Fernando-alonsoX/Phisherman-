import re
from . import config as C

OPENERS = re.compile(
    r"^\s*(halo|hallo|hai|hi|hey|hello|dear|greetings|good\s+day|attention|yth|yang terhormat|kepada|selamat\s+(pagi|siang|sore|malam)|assalamu|assalamualaikum|salam|dengan hormat|bapak|ibu|bpk|pak|bu|good\s+(morning|afternoon|evening)|greetings|attn|to whom|om |sdr)",
    re.I,
)
CLOSERS = re.compile(
    r"(terima\s*kasih|terimakasih|best,|best$|respectfully|warm regards|many thanks|with gratitude|faithfully|hormat\s+(kami|saya)|salam\s+(hormat|hangat|sukses|sejahtera|dari)|salam,|wassalam|regards|sincerely|thanks|thank you|best wishes|kind regards|yours|cheers|tertanda|atas perhatian|sampai jumpa|hormat,|salam$)",
    re.I,
)

PATTERNS = [
    ("Rasa mendesak", "Penipu memaksa korban bertindak cepat agar tidak sempat berpikir.",
     r"segera|right away|act now|within\s+\d+\s*(hours?|minutes?|days?)|final notice|last chance|limited time|locked|deactivated|sekarang juga|secepatnya|dalam\s+\d+\s*(jam|menit|hari)|batas waktu|terakhir|urgent|immediately|expire|kedaluwarsa|kadaluarsa|ditangguhkan|diblokir|dibekukan|suspended|deadline|asap"),
    ("Tautan mencurigakan", "Tautan palsu mengarahkan korban ke situs tiruan untuk mencuri data.",
     r"https?://\S+|www\.\S+|bit\.ly\S*|\bklik\b|click here|click the link|click below|follow the link|verify here|tautan|\blink\b|\S+\.(com|net|xyz|top|info)/\S*"),
    ("Meminta data pribadi", "Lembaga resmi tidak pernah meminta password, PIN, atau OTP lewat pesan.",
     r"password|passcode|one-time|verification code|credit card|card number|bank account|account number|social security|login credentials|confirm your (identity|account|details)|sign in|update your (account|information|billing)|kata sandi|sandi|\bpin\b|\botp\b|kode verifikasi|nomor rekening|nomor kartu|\bcvv\b|\bktp\b|login|username|verifikasi akun|konfirmasi data|data diri"),
    ("Iming-iming hadiah atau uang", "Hadiah mendadak adalah umpan klasik untuk memancing korban.",
     r"winner|congratulations|prize|lottery|gift card|claim your|cash|hadiah|menang|undian|gratis|bonus|transfer|rp\s?[\d.]+|\$\s?\d+|saldo|refund|pengembalian dana|bitcoin|crypto|kripto|pemenang|reward|giveaway"),
    ("Menyamar jadi pihak resmi", "Penipu memakai nama bank atau perusahaan agar terlihat tepercaya.",
     r"bank|paypal|amazon|microsoft|apple|google|it department|it support|human resources|administrator|official|admin|helpdesk|customer service|tim keamanan|security team|support|pihak resmi|petugas|manajemen|hrd|direktur|ceo"),
    ("Ancaman", "Ancaman dipakai untuk menakut-nakuti korban agar menurut.",
     r"will be (closed|deleted|suspended|terminated|blocked)|account closure|permanently|akan (ditutup|dihapus|dibekukan|diblokir)|tindakan hukum|denda|dilaporkan|polisi|konsekuensi|penutupan akun|legal action"),
]
PATTERNS.append(("Lampiran mencurigakan", "File tak dikenal bisa berisi malware yang mencuri data saat dibuka.", r"attached|attachment|invoice|download|open the file|see the file|enable (macros|content)|\.exe\b|\.zip\b|lampiran|unduh"))
EN_TEXT = [
    ("Urgency", "Scammers rush victims so they do not have time to think."),
    ("Suspicious link", "Fake links lead victims to look-alike sites that steal data."),
    ("Asks for personal data", "Real organizations never ask for passwords, PINs, or OTP codes by message."),
    ("Bait of prizes or money", "A sudden prize is a classic bait to hook victims."),
    ("Pretends to be official", "Scammers use a bank or company name to look trustworthy."),
    ("Threats", "Threats are used to scare victims into obeying."),
    ("Suspicious attachment", "Unknown files can contain malware that steals data when opened."),
]
_COMPILED = [(t, tip, re.compile(p, re.I), EN_TEXT[i]) for i, (t, tip, p) in enumerate(PATTERNS)]


def _lines(text):
    return [ln.strip() for ln in text.replace("\r", "").split("\n") if ln.strip()]


def count_words(text):
    """Menghitung jumlah kata bermakna yaitu token dengan minimal dua huruf atau angka."""
    return len([w for w in text.split() if len(re.sub(r"\W", "", w)) >= 2])


def check_email(text, subject=None):
    """Memeriksa subjek, pembuka, isi minimal 25 kata, dan penutup lalu mengembalikan status tiap bagian beserta jumlah kata isi."""
    lines = _lines(text)
    res = {"subject": True, "open": False, "body": False, "close": False, "ok": False, "missing": [], "words": 0, "need": C.MIN_BODY_WORDS}
    if subject is not None:
        res["subject"] = len(subject.strip()) >= 3
    if not lines:
        res["missing"] = (["Subject"] if not res["subject"] else []) + ["Opening", "Body", "Closing"]
        return res
    first = lines[0]
    res["open"] = bool(OPENERS.search(first[:60]))
    close_idx = None
    for i in range(len(lines) - 1, max(-1, len(lines) - 5), -1):
        if CLOSERS.search(lines[i]):
            close_idx = i
            break
    res["close"] = close_idx is not None
    start = 1 if (res["open"] and len(first.split()) <= 8) else 0
    end = len(lines)
    if close_idx is not None and len(lines[close_idx].split()) <= 8:
        end = close_idx
    body_words = [w for ln in lines[start:end] for w in ln.split() if len(re.sub(r"\W", "", w)) >= 2]
    if res["open"] and start == 0:
        body_words = body_words[3:]
    res["words"] = len(body_words)
    res["body"] = len(body_words) >= C.MIN_BODY_WORDS
    names = {"subject": "Subject", "open": "Opening", "body": "Body", "close": "Closing"}
    res["missing"] = [names[k] for k in ("subject", "open", "body", "close") if not res[k]]
    res["ok"] = not res["missing"]
    return res


def find_patterns(text, limit=5, lang="id"):
    """Mencari pola khas phishing pada pesan untuk dijelaskan sebagai bahan belajar siswa dengan judul berbahasa Indonesia atau Inggris sesuai lang."""
    found = []
    for title, tip, rx, en in _COMPILED:
        if lang == "en":
            title, tip = en
        hits = []
        for m in rx.finditer(text):
            frag = m.group(0).strip()
            if frag and frag.lower() not in [h.lower() for h in hits]:
                hits.append(frag[:28])
            if len(hits) >= 3:
                break
        if hits:
            found.append({"title": title, "tip": tip, "hits": hits})
    return found[:limit]

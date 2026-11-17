import re
import unicodedata
import urllib.parse
import pandas as pd

try:
    import idna
except ImportError:
    idna = None

INVISIBLE = re.compile(r"[​-‍⁠﻿­͏᠎-\U000e0020-\U000e007f]")
URL_RE = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
EXCLUDED = ["parser", "ner", "senter"]


def unicode_features(url, parsed_url=None):
    """Mengekstrak lima fitur unicode dari sebuah URL yaitu punycode karakter non ASCII karakter tak terlihat campuran skrip dan keragaman skrip."""
    url_normalized = unicodedata.normalize("NFKC", url)
    parsed_url = parsed_url if parsed_url else urllib.parse.urlparse(url_normalized)
    hostname = parsed_url.hostname or url
    is_punycode = 1 if hostname.startswith("xn--") else 0
    decoded = hostname
    if idna is not None:
        try:
            decoded = idna.decode(hostname)
        except idna.IDNAError:
            decoded = hostname
    non_ascii = sum(1 for c in decoded if ord(c) > 127)
    invisible = len(INVISIBLE.findall(url))
    scripts = set()
    for ch in decoded:
        if ch.isalnum():
            try:
                name = unicodedata.name(ch, "").split()[0]
                if name in ("LATIN", "CYRILLIC", "GREEK", "ARABIC", "HEBREW"):
                    scripts.add(name)
            except (ValueError, IndexError):
                continue
    return is_punycode, non_ascii, invisible, 1 if len(scripts) > 1 else 0, len(scripts)


def link_details(bodies):
    """Menghitung fitur tautan untuk setiap isi email dan mengembalikan DataFrame dengan kolom yang sama seperti saat model dilatih."""
    keys = ("url_count", "max_length", "max_dots", "max_hyphens", "has_ip", "has_at_symbol", "all_domains", "url_texts", "has_punnycode", "has_mixed_script", "non_ascii_sum", "invisible_char_sum", "lang_diversity_max")
    out = {k: [] for k in keys}
    for body in bodies:
        urls = URL_RE.findall(body)
        out["url_count"].append(len(urls))
        max_length = max_dots = max_hyphens = has_ip = has_at = punycode = mixed = non_ascii_sum = invisible_sum = diversity = 0
        words_all = []
        domains = set()
        for url in urls:
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            try:
                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc.split(":")[0]
                max_length = max(max_length, len(url))
                max_dots = max(max_dots, domain.count("."))
                max_hyphens = max(max_hyphens, domain.count("-"))
                path = parsed.path + " " + parsed.query
                path = re.sub(r"[\./\-_=\?&%]", " ", path)
                path = re.sub(r"\b(html|php|asp|aspx|js)\b", " ", path)
                path = re.sub(r"\d+", " ", path)
                words_all.extend(w.lower() for w in path.split() if len(w) > 1)
                if "@" in parsed.netloc:
                    has_at = 1
                    domain = domain.split("@")[-1]
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
                    has_ip = 1
                domains.add(domain)
                p, n, iv, mx, dv = unicode_features(url, parsed)
                punycode = max(punycode, p)
                mixed = max(mixed, mx)
                non_ascii_sum += n
                invisible_sum += iv
                diversity = max(diversity, dv)
            except Exception:
                continue
        out["max_length"].append(max_length)
        out["max_dots"].append(max_dots)
        out["max_hyphens"].append(max_hyphens)
        out["has_ip"].append(has_ip)
        out["has_at_symbol"].append(has_at)
        out["all_domains"].append(" ".join(domains))
        out["url_texts"].append(" ".join(set(words_all)))
        out["has_punnycode"].append(punycode)
        out["has_mixed_script"].append(mixed)
        out["non_ascii_sum"].append(non_ascii_sum)
        out["invisible_char_sum"].append(invisible_sum)
        out["lang_diversity_max"].append(diversity)
    return pd.DataFrame(out)


def clean_words(words):
    """Membersihkan teks mentah dengan huruf kecil serta membuang tautan dan tag HTML sebelum dilematisasi."""
    if words != words or len(words) > 999000:
        return ""
    words = words.strip(" ").lower()
    words = re.sub(r"https?://\S+|www\.\S+", "", words)
    return re.sub(r"<[^>]+>", "", words)


class Featurizer:
    """Pengubah subjek dan isi email menjadi tabel fitur untuk model memakai lemmatizer spaCy yang diberikan."""

    def __init__(self, lemma_path):
        self.lemma_path = lemma_path
        self.nlp = None

    def load(self):
        """Memuat lemmatizer dari folder dengan mengecualikan komponen yang tidak dipakai agar cepat."""
        import spacy
        self.nlp = spacy.load(self.lemma_path, exclude=EXCLUDED)

    def lemmas(self, texts):
        """Mengubah daftar teks menjadi daftar string lemma tanpa tanda baca angka spasi dan stop word."""
        cleaned = [clean_words(t) for t in texts]
        out = []
        for doc in self.nlp.pipe(cleaned, batch_size=64):
            toks = [w.lemma_.lower() for w in doc if not (w.is_punct or w.is_digit or len(w.text) <= 1 or w.is_space or w.is_stop)]
            out.append(" ".join(toks))
        return out

    def frame(self, subjects, bodies):
        """Membangun DataFrame fitur dari daftar subjek dan isi email dengan kolom clean_subject clean_body dan fitur tautan."""
        subjects = [s or "" for s in subjects]
        bodies = [b or "" for b in bodies]
        df = pd.DataFrame({"subject": subjects, "body": bodies})
        df = pd.concat([df, link_details(bodies)], axis=1)
        df["clean_body"] = self.lemmas(bodies)
        df["clean_subject"] = self.lemmas(subjects)
        return df

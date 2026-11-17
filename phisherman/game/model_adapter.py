import csv
import json
import math
import os
import pickle
import re
import threading
import time
from . import config as C


class Prediction:
    """Hasil prediksi satu pesan berisi label phishing probabilitas dan sumber penilaian."""

    def __init__(self, is_phishing, prob, source="model"):
        self.is_phishing = is_phishing
        self.prob = prob
        self.source = source


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def _jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class DemoScorer:
    """Penilai cadangan berbasis kata kunci hanya untuk menguji tampilan saat file model belum ada."""

    WORDS = ("segera", "klik", "password", "kata sandi", "otp", "pin", "verifikasi", "hadiah", "menang", "transfer",
             "diblokir", "ditangguhkan", "urgent", "http", "www", "bank", "saldo", "login", "akun", "bonus", "gratis",
             "click", "verify", "account", "suspended", "prize", "bitcoin", "rekening", "immediately", "confirm", "security", "winner", "refund", "invoice", "attachment", "download", "expire", "claim", "congratulations", "locked", "credentials")

    PASS_TAG = "#lolos"
    CATCH_TAG = "#tangkap"

    def tag(self, text):
        """Mengembalikan probabilitas tetap bila pesan memuat tag uji #lolos atau #tangkap."""
        t = text.lower()
        if self.CATCH_TAG in t:
            return 0.95
        if self.PASS_TAG in t:
            return 0.08
        return None

    def prob(self, text):
        t = text.lower()
        fixed = self.tag(t)
        if fixed is not None:
            return fixed
        score = sum(1 for w in self.WORDS if w in t)
        return max(0.03, min(0.97, 0.08 + score * 0.17))


class ModelAdapter:
    """Memuat pipeline SVC dan lemmatizer spaCy lalu memprediksi email dari subjek dan isi serta melatih ulang secara online dari koreksi pemain."""

    MAX_ITER = 40
    ETA = 0.12
    MARGIN = 0.25
    SCALE = 1.6

    def __init__(self, model_path=None, test_mode=False):
        self.test_mode = test_mode
        self.model_path = model_path or C.MODEL_PATH
        self.status = "idle"
        self.message = ""
        self.raw = None
        self.feat = None
        self.demo = DemoScorer()
        self.overrides = {}
        self.lock = threading.RLock()
        self.busy = False
        self.stats = {"predictions": 0, "verified": 0, "correct": 0, "wrong": 0, "retrains": 0, "updated": ""}
        self.method = "none"
        self.loaded_from = ""
        self.memory = []
        self._save_pending = False
        self._save_lock = threading.Lock()
        self._load_stats()

    @property
    def model(self):
        return self.raw

    def _load_stats(self):
        try:
            with open(C.STATS_PATH, "r", encoding="utf-8") as f:
                self.stats.update(json.load(f))
        except Exception:
            pass
        try:
            with open(os.path.join(C.DATA_DIR, "overrides.json"), "r", encoding="utf-8") as f:
                self.overrides = json.load(f)
        except Exception:
            self.overrides = {}

    def load_async(self):
        self.status = "loading"
        threading.Thread(target=self.load, daemon=True).start()

    def _candidates(self):
        """Menentukan urutan berkas model dengan memakai hasil latih ulang hanya bila lebih baru dari model asli."""
        upd = C.UPDATED_MODEL_PATH
        if self.model_path != C.MODEL_PATH or not os.path.exists(upd):
            return [self.model_path]
        if os.path.exists(self.model_path) and os.path.getmtime(upd) < os.path.getmtime(self.model_path):
            return [self.model_path]
        return [upd, self.model_path]

    def load(self):
        """Membaca pipeline pkl dan lemmatizer lalu mencoba model hasil latih ulang lebih dulu dan beralih ke model asli bila gagal."""
        self.status = "loading"
        if self.test_mode:
            self.raw = None
            self.message = "Rule-based test mode active"
            self.status = "demo"
            return
        error = ""
        for path in self._candidates():
            if not os.path.exists(path):
                continue
            try:
                self.raw = self._read(path)
                self._prepare()
                self.loaded_from = path
                self.status = "ready"
                self.message = "Model loaded from " + os.path.basename(path)
                return
            except Exception as exc:
                error = "Failed to load " + os.path.basename(path) + ": " + str(exc)[:80]
        self.raw = None
        self.feat = None
        self.status = "demo"
        self.message = error or "Model file not found. Using the demo scorer"

    def _read(self, path):
        try:
            import joblib
            return joblib.load(path)
        except ImportError:
            with open(path, "rb") as f:
                return pickle.load(f)

    def _prepare(self):
        """Memuat lemmatizer lalu menguji satu prediksi agar kegagalan terdeteksi sejak awal."""
        from .nlp_features import Featurizer
        if self.feat is None:
            feat = Featurizer(C.LEMMA_PATH)
            feat.load()
            self.feat = feat
        if not hasattr(self.raw, "decision_function"):
            raise ValueError("pipeline has no decision_function")
        self._score("Test", "This is a short test message.")

    def _score(self, subject, body):
        """Menghitung skor keputusan SVC lalu mengubahnya menjadi probabilitas phishing lewat fungsi sigmoid."""
        df = self.feat.frame([subject], [body])
        d = float(self.raw.decision_function(df)[0])
        return 1.0 / (1.0 + math.exp(-self.SCALE * d))

    def _override(self, text):
        n = _norm(text)
        if not n:
            return None
        if n in self.overrides:
            return self.overrides[n]
        for k, v in self.overrides.items():
            if _jaccard(n, k) >= 0.88:
                return v
        return None

    def predict(self, subject, body):
        """Memprediksi satu email dari subjek dan isinya dengan memeriksa memori koreksi dulu lalu model atau penilai demo."""
        with self.lock:
            full = (subject + " " + body).strip()
            ov = self._override(full)
            fixed = self.demo.tag(full) if self.test_mode else None
            if fixed is not None:
                prob = fixed
                src = "demo"
            elif ov is not None:
                prob = 0.96 if ov else 0.04
                src = "memory"
            elif self.raw is not None and self.feat is not None:
                try:
                    prob = self._score(subject, body)
                    src = "model"
                except Exception:
                    prob = self.demo.prob(full)
                    src = "demo"
            else:
                prob = self.demo.prob(full)
                src = "demo"
            self.stats["predictions"] += 1
            return Prediction(prob >= 0.5, prob, src)

    def record(self, was_correct):
        """Mencatat hasil verifikasi pemain untuk menghitung akurasi model."""
        with self.lock:
            self.stats["verified"] += 1
            self.stats["correct" if was_correct else "wrong"] += 1
        self.save_stats()

    def accuracy(self):
        v = self.stats["verified"]
        return (self.stats["correct"] / v) if v else None

    def learn_async(self, subject, body, is_phishing, callback=None):
        """Menjalankan pelatihan ulang di thread terpisah agar layar tidak membeku."""
        self.busy = True

        def work():
            """Pekerjaan latih ulang di latar belakang."""
            try:
                info = self.learn(subject, body, is_phishing)
            except Exception as exc:
                info = {"ok": False, "method": "error", "message": str(exc)[:80]}
            self.busy = False
            if callback:
                callback(info)

        threading.Thread(target=work, daemon=True).start()

    def learn(self, subject, body, is_phishing):
        """Melatih ulang model dengan contoh yang salah diprediksi lewat pembaruan hinge online pada bobot SVC dan memori koreksi sebagai cadangan."""
        self._log_feedback(subject, body, is_phishing)
        with self.lock:
            info = {"ok": True, "method": "memory", "message": ""}
            if self.raw is not None and self.feat is not None:
                try:
                    info = self._online(subject, body, is_phishing)
                except Exception as exc:
                    info = {"ok": False, "method": "online", "message": str(exc)[:80]}
            full = (subject + " " + body).strip()
            if not info["ok"] or info["method"] == "memory":
                self.overrides[_norm(full)] = bool(is_phishing)
                self._save_overrides()
                info["method"] = "memory"
                info["ok"] = True
            self.stats["retrains"] += 1
            self.stats["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.method = info["method"]
        self.save_stats()
        self._schedule_save()
        return info

    def _schedule_save(self):
        """Menunda penyimpanan model agar beberapa koreksi beruntun cukup ditulis satu kali di latar belakang."""
        if self._save_pending:
            return
        self._save_pending = True

        def work():
            """Menunggu sebentar lalu menyimpan model."""
            time.sleep(1.5)
            self._save_pending = False
            self.save()

        threading.Thread(target=work, daemon=True).start()

    def _vector(self, subject, body):
        """Mengubah satu email menjadi baris sparse fitur akhir yang dipakai classifier SVC."""
        import scipy.sparse as sp
        df = self.feat.frame([subject], [body])
        x = self.raw[:-1].transform(df)
        return sp.csr_matrix(x)

    def _online(self, subject, body, is_phishing):
        """Memperbarui koef dan intersep LinearSVC dengan langkah hinge sampai contoh baru terklasifikasi benar lalu mengulang contoh koreksi sebelumnya agar tidak lupa."""
        import numpy as np
        svc = self.raw[-1]
        coef = np.array(svc.coef_, dtype=float).reshape(-1).copy()
        b = float(np.array(svc.intercept_).reshape(-1)[0])
        y = 1.0 if is_phishing else -1.0
        x = self._vector(subject, body)
        self.memory.append((x, y))
        self.memory = self.memory[-60:]
        done = 0
        for it in range(self.MAX_ITER):
            for xi, yi in self.memory:
                w = 1.0 if xi is x else 0.5
                margin = yi * (float(xi.dot(coef)[0]) + b)
                if margin < 1.0:
                    coef[xi.indices] += self.ETA * w * yi * xi.data
                    b += self.ETA * w * yi * 0.2
            done += 1
            if y * (float(x.dot(coef)[0]) + b) >= self.MARGIN:
                break
        ok = y * (float(x.dot(coef)[0]) + b) > 0
        if not ok:
            return {"ok": False, "method": "online", "message": "not converged"}
        svc.coef_ = coef.reshape(1, -1)
        svc.intercept_ = np.array([b])
        return {"ok": True, "method": "online", "message": str(done) + " iterations"}

    def _log_feedback(self, subject, body, is_phishing):
        if self.test_mode:
            return
        try:
            os.makedirs(C.DATA_DIR, exist_ok=True)
            new = not os.path.exists(C.FEEDBACK_PATH)
            with open(C.FEEDBACK_PATH, "a", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["subject", "body", "label", "time"])
                w.writerow([subject.replace("\r", " "), body.replace("\r", " "), 1 if is_phishing else 0, time.strftime("%Y-%m-%d %H:%M:%S")])
        except Exception:
            pass

    def _save_overrides(self):
        if self.test_mode:
            return
        try:
            os.makedirs(C.DATA_DIR, exist_ok=True)
            with open(os.path.join(C.DATA_DIR, "overrides.json"), "w", encoding="utf-8") as f:
                json.dump(self.overrides, f, ensure_ascii=False)
        except Exception:
            pass

    def save_stats(self):
        """Menyimpan statistik performa model ke file json."""
        if self.test_mode:
            return
        try:
            os.makedirs(C.DATA_DIR, exist_ok=True)
            with open(C.STATS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass

    def save(self):
        """Menyimpan pipeline hasil latih ulang beserta statistik secara atomik agar performa tidak hilang."""
        self.save_stats()
        if self.raw is None or self.test_mode or self.stats["retrains"] == 0:
            return
        with self._save_lock:
            try:
                os.makedirs(C.MODEL_DIR, exist_ok=True)
                tmp = C.UPDATED_MODEL_PATH + ".tmp"
                try:
                    import joblib
                    joblib.dump(self.raw, tmp)
                except ImportError:
                    with open(tmp, "wb") as f:
                        pickle.dump(self.raw, f)
                os.replace(tmp, C.UPDATED_MODEL_PATH)
            except Exception:
                pass

    @property
    def label(self):
        if self.status == "ready":
            return "AI model ready"
        if self.status == "loading":
            return "Loading AI model"
        if self.status == "demo":
            return "AI guard ready"
        return "Model error"

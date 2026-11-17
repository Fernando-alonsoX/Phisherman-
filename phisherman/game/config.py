import os
import sys

BASE_W = 1280
BASE_H = 720
FPS = 60
TITLE = "Phisherman"
TOTAL_ROUNDS = 5
WIN_THRESHOLD = 3
REWARD = 100
START_MONEY = 5
MIN_BODY_WORDS = 25
BASE_POINTS = 100
MALWARE_BONUS_POINTS = 150
MALWARE_BONUS_MONEY = 75
MALWARE_PENALTY = 150
MAX_NAME = 14
MIN_NAME = 3

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_DIR = os.path.join(ROOT, "model")
DATA_DIR = os.environ.get("PHISHERMAN_DATA_DIR") or os.path.join(ROOT, "data")
MODEL_PATH = os.path.join(MODEL_DIR, "svc_pipeline.pkl")
UPDATED_MODEL_PATH = os.path.join(MODEL_DIR, "svc_pipeline_updated.pkl")
LEMMA_PATH = os.path.join(MODEL_DIR, "lemmatizer")
BASE_DATASET_PATH = os.path.join(DATA_DIR, "base_dataset.csv")
FEEDBACK_PATH = os.path.join(DATA_DIR, "feedback.csv")
STATS_PATH = os.path.join(DATA_DIR, "model_stats.json")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
PLAYERS_PATH = os.path.join(DATA_DIR, "players.json")
EGG_PATH = os.path.join(DATA_DIR, "tackle_box.json")
MUSIC_PATH = os.path.join(ROOT, "assets", "music", "heat.mp3")
FISHING_MUSIC_PATH = os.path.join(ROOT, "assets", "music", "fishing.mp3")
MANIA_PATH = os.path.join(ROOT, "assets", "music", "mancing_mania.mp3")

PHISHING_LABEL_HINTS = ("phish", "spam", "malicious", "fraud", "scam", "bahaya", "penipuan")
NORMAL_LABEL_HINTS = ("normal", "ham", "safe", "legit", "benign", "aman")

INK = (18, 22, 34)
WHITE = (255, 255, 255)
AERO_LIGHT = (205, 227, 250)
AERO_MID = (120, 170, 225)
AERO_DEEP = (36, 84, 150)
AERO_NAVY = (14, 34, 74)
GREEN = (70, 190, 90)
GREEN_DARK = (28, 110, 52)
RED = (220, 60, 56)
RED_DARK = (140, 28, 28)
GOLD = (255, 206, 70)
TEXT_DARK = (28, 34, 48)
TEXT_SOFT = (84, 96, 120)

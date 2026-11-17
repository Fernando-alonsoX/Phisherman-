from . import config as C

FILES = (
    ("Invoice_October.pdf", "pdf", 0.30),
    ("Salary_Slip_2026.xlsx", "xls", 0.45),
    ("Meeting_Notes.docx", "doc", 0.20),
    ("Holiday_Photos.zip", "zip", 0.55),
    ("Security_Update.exe", "exe", 0.70),
    ("Project_Proposal.pptx", "ppt", 0.35),
    ("Budget_Report.xlsx", "xls", 0.40),
    ("Employee_List.csv", "csv", 0.25),
    ("Receipt_Scan.png", "img", 0.15),
)


SIZES = {
    "Invoice_October.pdf": "184 KB",
    "Salary_Slip_2026.xlsx": "96 KB",
    "Meeting_Notes.docx": "52 KB",
    "Holiday_Photos.zip": "4.2 MB",
    "Security_Update.exe": "2.8 MB",
    "Project_Proposal.pptx": "1.6 MB",
    "Budget_Report.xlsx": "238 KB",
    "Employee_List.csv": "31 KB",
    "Receipt_Scan.png": "712 KB",
}


def file_size(name):
    """Mengambil ukuran tampilan sebuah file contoh dalam teks seperti 184 KB."""
    return SIZES.get(name, "120 KB")


def file_kind(name):
    """Mengambil jenis file contoh untuk menentukan ikon yang dipakai."""
    for n, kind, risk in FILES:
        if n == name:
            return kind
    return "doc"


def file_risk(name):
    """Mengambil peluang tersembunyi sebuah file ternyata malware berdasarkan namanya."""
    for n, kind, risk in FILES:
        if n == name:
            return risk
    return 0.3


def resolve(detected, has_file, malware):
    """Menghitung hasil satu ronde dari status terdeteksi dan hasil gacha malware lalu mengembalikan poin uang dan penjelasannya."""
    if not detected:
        if has_file and malware:
            return {
                "code": "jackpot", "success": True,
                "points": C.BASE_POINTS + C.MALWARE_BONUS_POINTS,
                "money": C.REWARD + C.MALWARE_BONUS_MONEY,
                "title": "JACKPOT!",
                "detail": "The message passed and the file was malware. Bonus points and money!",
            }
        return {
            "code": "pass", "success": True,
            "points": C.BASE_POINTS,
            "money": C.REWARD,
            "title": "PASSED",
            "detail": "The phishing message was not detected. Money comes in as usual." if not has_file else "The message passed. The file was harmless, so no bonus.",
        }
    if has_file and malware:
        return {
            "code": "busted", "success": False,
            "points": -C.MALWARE_PENALTY,
            "money": 0,
            "title": "BUSTED",
            "detail": "The message was detected and the malware was found too. Big point penalty.",
        }
    return {
        "code": "caught", "success": False,
        "points": 0,
        "money": 0,
        "title": "DETECTED",
        "detail": "The AI detected the phishing message. No points and no money.",
    }

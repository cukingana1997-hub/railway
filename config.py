import os

# ================= TOKEN BOT =================
TOKEN_NASABAH = os.getenv("TOKEN_NASABAH")
TOKEN_ABSENSI = os.getenv("TOKEN_ABSENSI")

# ================= GROUP CHAT ID =================
DATA_GROUP_ID = int(os.getenv("DATA_GROUP_ID"))
ABSEN_GROUP_ID = int(os.getenv("ABSEN_GROUP_ID"))

# ================= ADMIN IDS =================
try:
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
except ValueError:
    ADMIN_IDS = []

# ================= EXCEL / FOLDER PATH =================
EXCEL_NASABAH = "nasabah.xlsx"
EXCEL_ABSENSI = "absensi.xlsx"
BACKUP_DIR = "backup"
ARSIP_DIR = "arsip"

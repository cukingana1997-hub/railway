import os

# ================= TOKEN BOT =================
# Ambil dari GitHub Environment / Secrets
TOKEN_NASABAH = os.getenv("TOKEN_NASABAH")  # 666
TOKEN_ABSENSI = os.getenv("TOKEN_ABSENSI")  # Distrugle

# ================= GROUP CHAT ID =================
DATA_GROUP_ID = int(os.getenv("DATA_GROUP_ID"))     # grup nasabah
ABSEN_GROUP_ID = int(os.getenv("ABSEN_GROUP_ID"))   # grup absensi

# ================= ADMIN IDS =================
# Bisa banyak admin, pisahkan koma, contoh: "7971506744,123456789"
try:
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
except ValueError:
    ADMIN_IDS = []

# ================= EXCEL / FOLDER PATH =================
EXCEL_NASABAH = "nasabah.xlsx"
EXCEL_ABSENSI = "absensi.xlsx"
BACKUP_DIR = "backup"
ARSIP_DIR = "arsip"

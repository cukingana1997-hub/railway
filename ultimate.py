import os, re, shutil, asyncio, logging, pandas as pd
from datetime import datetime, time as dt_time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import *

# ================= LOGGING =================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logging.info("Ultimate Bot starting...")

# ================= FOLDER SETUP =================
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(ARSIP_DIR, exist_ok=True)

# ================= UTILS =================
def backup_file(path):
    if os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = os.path.basename(path).split(".")[0]
        backup_path = os.path.join(BACKUP_DIR, f"{name}_{ts}.xlsx")
        shutil.copy(path, backup_path)
        logging.info(f"Backup OK: {backup_path}")

def normalize_wa(text: str) -> str:
    digits = re.sub(r"\D", "", text or "")
    if digits.startswith("60"):
        digits = "0" + digits[2:]
    return digits

def normalize_link(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"^https?://", "", t)
    t = re.sub(r"^www\.", "", t)
    return t.rstrip("/")

# ================= EXCEL INIT =================
nasabah_cols = ["Input_By","Admin","Nama","Asal","Negara","Umur","Agama_Hobby",
                "Status","Status_Hub","Pekerjaan","Lama_Kerja","Aset","NoWA","Link","Tanggal"]
absensi_cols = ["Tanggal","Nama","UserID","Event","Start","End","Durasi","Warning"]

def init_excel(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_excel(path, index=False)

init_excel(EXCEL_NASABAH, nasabah_cols)
init_excel(EXCEL_ABSENSI, absensi_cols)
init_excel(os.path.join(ARSIP_DIR, "arsip_nasabah.xlsx"), nasabah_cols)

# ================= NASABAH BOT =================
# fungsi load/save nasabah
def load_nasabah():
    return pd.read_excel(EXCEL_NASABAH)

def save_nasabah(df):
    backup_file(EXCEL_NASABAH)
    df.to_excel(EXCEL_NASABAH, index=False)

def load_arsip():
    return pd.read_excel(os.path.join(ARSIP_DIR, "arsip_nasabah.xlsx"))

def save_arsip(df):
    df.to_excel(os.path.join(ARSIP_DIR, "arsip_nasabah.xlsx"), index=False)

async def nasabah_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Input Nasabah", callback_data="input")]])
    await update.effective_message.reply_text("Menu Nasabah:", reply_markup=kb)

# ================= ABSENSI BOT =================
# (gunakan kode yang sama, refactor sedikit)
def load_absen():
    df = pd.read_excel(EXCEL_ABSENSI)
    for c in absensi_cols:
        if c not in df.columns:
            df[c] = None
    return df

def save_absen(df):
    backup_file(EXCEL_ABSENSI)
    df.to_excel(EXCEL_ABSENSI, index=False)

async def absensi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Kerja", callback_data="Kerja"),
         InlineKeyboardButton("Istirahat", callback_data="Istirahat")],
        [InlineKeyboardButton("Toilet", callback_data="Toilet"),
         InlineKeyboardButton("Smoking", callback_data="Smoking")],
        [InlineKeyboardButton("Others", callback_data="Others"),
         InlineKeyboardButton("Duduk", callback_data="Duduk")],
        [InlineKeyboardButton("Pulang", callback_data="Pulang")]
    ]
    await update.message.reply_text("ABSENSI HARI INI", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= BACKUP LOOP =================
async def backup_loop():
    while True:
        await asyncio.sleep(60*60*6)
        backup_file(EXCEL_NASABAH)
        backup_file(EXCEL_ABSENSI)

# ================= MULTI BOT =================
async def launch_bot(token, register, name):
    while True:
        try:
            logging.info(f"Launching {name}")
            app = ApplicationBuilder().token(token).build()
            register(app)
            await app.run_polling()
        except Exception:
            logging.exception(f"{name} crashed, restart in 5s")
            await asyncio.sleep(5)

# ================= MAIN =================
def run():
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def main():
        def reg_abs(app):
            app.add_handler(CommandHandler("start", absensi_start))

        def reg_nas(app):
            app.add_handler(CommandHandler("start", nasabah_start))

        await asyncio.gather(
            launch_bot(TOKEN_ABSENSI, reg_abs, "ABSENSI BOT"),
            launch_bot(TOKEN_NASABAH, reg_nas, "NASABAH BOT"),
            backup_loop()
        )

    asyncio.run(main())

if __name__ == "__main__":
    run()
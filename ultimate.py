import os, re, shutil, asyncio, logging, pandas as pd
from datetime import datetime, date, time as dt_time
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from config import 

# ================= LOGGING =================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
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
nasabah_cols = [
    "Input_By","Admin","Nama","Asal","Negara","Umur","Agama_Hobby",
    "Status","Status_Hub","Pekerjaan","Lama_Kerja",
    "Aset","NoWA","Link","Tanggal"
]
absensi_cols = ["Tanggal","Nama","UserID","Event","Start","End","Durasi","Warning"]

def init_excel(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_excel(path, index=False)

init_excel(EXCEL_NASABAH, nasabah_cols)
init_excel(EXCEL_ABSENSI, absensi_cols)
init_excel(os.path.join(ARSIP_DIR, "arsip_nasabah.xlsx"), nasabah_cols)

# ================= NASABAH BOT =================
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
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Input Nasabah", callback_data="input")]
    ])
    await update.effective_message.reply_text("Menu Nasabah:", reply_markup=kb)

async def nasabah_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = update.callback_query
        await q.answer()

        if q.data.startswith("arsip|"):
            wa = q.data.split("|")[1]
            df = load_nasabah()
            target = df[df["NoWA"] == wa]
            if target.empty:
                await q.edit_message_text("Data tidak ditemukan")
                return

            arsip_df = load_arsip()
            arsip_df = pd.concat([arsip_df, target], ignore_index=True)
            save_arsip(arsip_df)

            df = df[df["NoWA"] != wa]
            save_nasabah(df)
            await q.edit_message_text("Data berhasil diarsip")

        elif q.data.startswith("unarsip|"):
            wa = q.data.split("|")[1]
            arsip_df = load_arsip()
            target = arsip_df[arsip_df["NoWA"] == wa]
            if target.empty:
                await q.edit_message_text("Data tidak ditemukan di arsip")
                return

            df = load_nasabah()
            df = pd.concat([df, target], ignore_index=True)
            save_nasabah(df)

            arsip_df = arsip_df[arsip_df["NoWA"] != wa]
            save_arsip(arsip_df)
            await q.edit_message_text("Data dikembalikan ke aktif")

    except Exception:
        logging.exception("Nasabah button error")

async def nasabah_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.effective_message
        user = msg.from_user
        if user.id not in ADMIN_IDS:
            return

        text = msg.text or ""
        if "NoWA" not in text or "LINK" not in text:
            return

        def get(key):
            for line in text.split("\n"):
                if key.lower() in line.lower():
                    return line.split(":", 1)[-1].strip()
            return ""

        record = {
            "Input_By": user.username or f"ID:{user.id}",
            "Admin": get("ADMIN"),
            "Nama": get("NAMA"),
            "Asal": get("ASAL"),
            "Negara": get("NEGARA"),
            "Umur": get("UMUR"),
            "Agama_Hobby": get("AGAMA"),
            "Status": get("STATUS"),
            "Status_Hub": get("STATUS HUB"),
            "Pekerjaan": get("PEKERJAAN"),
            "Lama_Kerja": get("LAMA KERJA"),
            "Aset": get("ASET"),
            "NoWA": normalize_wa(get("NoWA")),
            "Link": normalize_link(get("LINK")),
            "Tanggal": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        df = load_nasabah()
        if record["NoWA"] in df["NoWA"].values or record["Link"] in df["Link"].values:
            await msg.reply_text("❌ Data sudah ada")
            return

        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        save_nasabah(df)

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ARSIP", callback_data=f"arsip|{record['NoWA']}"),
                InlineKeyboardButton("UN-ARSIP", callback_data=f"unarsip|{record['NoWA']}")
            ]
        ])

        await msg.reply_text(
            f"✅ Data tersimpan:\n{record['Nama']} | {record['NoWA']}",
            reply_markup=kb
        )

    except Exception:
        logging.exception("Nasabah handle error")

# ================= ABSENSI BOT =================
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
    await update.message.reply_text(
        "ABSENSI HARI INI",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_absen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.message.chat.id != ABSEN_GROUP_ID:
        return

    df = load_absen()
    user = query.from_user

    record = {
        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
        "Nama": user.full_name,
        "UserID": user.id,
        "Event": query.data,
        "Start": datetime.now().strftime("%H:%M") if query.data == "Kerja" else None,
        "End": datetime.now().strftime("%H:%M") if query.data == "Pulang" else None,
        "Durasi": None,
        "Warning": ""
    }

    if query.data == "Pulang":
        start_row = df[(df["UserID"] == user.id) & (df["Start"].notna())].tail(1)
        if not start_row.empty:
            start = datetime.strptime(start_row["Start"].values[0], "%H:%M")
            end = datetime.strptime(record["End"], "%H:%M")
            record["Durasi"] = (end - start).seconds // 60

    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    save_absen(df)
    await query.edit_message_text(f"{record['Event']} tercatat")

# ================= BACKUP LOOP =================
async def backup_loop():
    while True:
        await asyncio.sleep(60 * 60 * 6)
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
            app.add_handler(CallbackQueryHandler(handle_absen))

        def reg_nas(app):
            app.add_handler(CommandHandler("start", nasabah_start))
            app.add_handler(CallbackQueryHandler(nasabah_button))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nasabah_handle))

        await asyncio.gather(
            launch_bot(TOKEN_ABSENSI, reg_abs, "ABSENSI BOT"),
            launch_bot(TOKEN_NASABAH, reg_nas, "NASABAH BOT"),
            backup_loop()
        )

    asyncio.run(main())

if __name__ == "__main__":
    run()

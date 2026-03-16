# -*- coding: utf-8 -*-
"""
YGF Telegram Bot
Yarışmacılar portföylerini Telegram'dan gönderir, bot Google Sheets'e yazar.
"""

import sys
import io
import os
import json
import glob
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ── Windows encoding fix ──
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── Sabitler ──
SCRIPT_DIR = Path(__file__).parent
AYAR_DOSYA = SCRIPT_DIR / "ygf_ayarlar.json"
LOG_DOSYA = SCRIPT_DIR / "ygf_telegram_bot.log"
VERILER_KLASOR = Path(r"C:\Users\PDS\Desktop\is api\veriler")
YARISMA_BASLANGIC = datetime(2026, 1, 2)
PERIYOT_GUN = 14
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Logging ──
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_DOSYA, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ygf_bot")

# ── Ayarları yükle ──
with open(AYAR_DOSYA, "r", encoding="utf-8") as f:
    AYARLAR = json.load(f)

BOT_TOKEN = AYARLAR["telegram_bot_token"]
ADMIN_ID = AYARLAR.get("telegram_admin_id", 0)
YARISMACILAR = AYARLAR["yarismacilar"]
CREDS_PATH = AYARLAR["credentials_json"]
SHEET_ID = AYARLAR["google_sheet_id"]

# ── Google Sheets bağlantısı (bir kez) ──
log.info("Google Sheets'e baglaniliyor...")
gs_creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
gc = gspread.authorize(gs_creds)
SS = gc.open_by_key(SHEET_ID)
log.info("Sheets baglantisi kuruldu.")

# ── bisttum_pd.xlsx'i bir kez oku ──
log.info("bisttum_pd.xlsx yukleniyor...")
BISTTUM_YOL = VERILER_KLASOR / "bisttum_pd.xlsx"
DF_PD = pd.read_excel(str(BISTTUM_YOL), sheet_name="PD", index_col=0)
yeni_cols = []
for col in DF_PD.columns:
    if isinstance(col, datetime):
        yeni_cols.append(col)
    else:
        try:
            yeni_cols.append(pd.to_datetime(col))
        except Exception:
            yeni_cols.append(col)
DF_PD.columns = yeni_cols
TARIH_LISTESI = [c for c in DF_PD.columns if isinstance(c, (datetime, pd.Timestamp))]
log.info("bisttum_pd yuklendi: %d hisse, %d tarih", len(DF_PD), len(TARIH_LISTESI))


# ══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════

def turkce_normalize(s):
    """Türkçe karakterleri ASCII'ye dönüştür ve küçük harfe çevir."""
    tr_map = {"ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
              "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    result = ""
    for ch in s:
        result += tr_map.get(ch, ch)
    return result.lower().strip()


def isim_esle(girdi):
    """Girdiyi yarışmacı listesiyle eşleştir. None dönerse eşleşmedi."""
    girdi_n = turkce_normalize(girdi)
    for isim in YARISMACILAR:
        if turkce_normalize(isim) == girdi_n:
            return isim
    return None


def aktif_periyot():
    bugun = datetime.now()
    for p in range(1, 27):
        basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (p - 1))
        sonu = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * p)
        if basi <= bugun < sonu:
            return p, basi, sonu
    basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * 25)
    sonu = datetime(2026, 12, 31)
    return 26, basi, sonu


def en_yakin_tarih(hedef):
    oncekiler = [t for t in TARIH_LISTESI if t <= hedef]
    if oncekiler:
        return max(oncekiler)
    return min(TARIH_LISTESI, key=lambda t: abs((t - hedef).days))


def snap_tarih_pd(tarih_str):
    """Belirli bir tarihin snap PD dosyasını oku. Yoksa None."""
    dosya = VERILER_KLASOR / "snap_bugun_pd_{}.xlsx".format(tarih_str)
    if dosya.exists():
        return pd.read_excel(str(dosya), sheet_name="PD", index_col=0)
    return None


def snap_bugun_pd():
    bugun_str = datetime.now().strftime("%Y-%m-%d")
    dosya = VERILER_KLASOR / "snap_bugun_pd_{}.xlsx".format(bugun_str)
    if not dosya.exists():
        snap_files = sorted(glob.glob(str(VERILER_KLASOR / "snap_bugun_pd_*.xlsx")))
        if not snap_files:
            return None
        dosya = Path(snap_files[-1])
    df = pd.read_excel(str(dosya), sheet_name="PD", index_col=0)
    return df


def periyot_basi_pd(hisse, p_basi):
    """
    Hisse için periyot başı PD'sini bul.
    Önce bisttum_pd'de tam tarihi ara, yoksa snap dosyasına bak,
    yoksa bisttum_pd'den en yakın önceki tarihi kullan.
    """
    p_basi_ts = pd.Timestamp(p_basi)

    # 1) bisttum_pd'de tam tarih var mı?
    if p_basi_ts in DF_PD.columns and hisse in DF_PD.index:
        return float(DF_PD.loc[hisse, p_basi_ts])

    # 2) O tarihin snap dosyası var mı?
    snap_df = snap_tarih_pd(p_basi.strftime("%Y-%m-%d"))
    if snap_df is not None and hisse in snap_df.index:
        return float(snap_df.iloc[:, 0].loc[hisse])

    # 3) bisttum_pd'den en yakın önceki tarih
    yakin = en_yakin_tarih(p_basi)
    if hisse in DF_PD.index:
        return float(DF_PD.loc[hisse, yakin])

    return None


def parse_portfoy_mesaji(metin):
    """
    Mesajı parse et.
    Dönüş: (isim_orijinal, portfoy_list, hata_mesaji)
    """
    kelimeler = metin.strip().split()
    if len(kelimeler) < 3:
        return None, None, "En az isim + 1 hisse + 1 tutar gerekli.\nOrnek: Selim 50 KLGYO 50 THYAO"

    # İsim eşleştirme: önce ilk kelime, sonra ilk iki kelime
    isim = isim_esle(kelimeler[0])
    kalan_idx = 1

    if isim is None and len(kelimeler) >= 4:
        iki_kelime = kelimeler[0] + " " + kelimeler[1]
        isim = isim_esle(iki_kelime)
        if isim is not None:
            kalan_idx = 2

    if isim is None:
        return None, None, '"{}" taninmadi.\nYarismacilar: {}'.format(
            kelimeler[0], ", ".join(YARISMACILAR))

    kalan = kelimeler[kalan_idx:]
    portfoy = []
    i = 0
    while i < len(kalan):
        if i + 1 >= len(kalan):
            break
        a, b = kalan[i], kalan[i + 1]

        try:
            tutar = float(a.replace(",", "."))
            hisse = b.upper()
            portfoy.append({"hisse": hisse, "tutar": tutar})
            i += 2
        except ValueError:
            try:
                tutar = float(b.replace(",", "."))
                hisse = a.upper()
                portfoy.append({"hisse": hisse, "tutar": tutar})
                i += 2
            except ValueError:
                i += 1

    if not portfoy:
        return None, None, "Portfoy parse edilemedi.\nOrnek: Selim 50 KLGYO 50 THYAO"

    return isim, portfoy, None


# ══════════════════════════════════════════════════════════════
# SHEETS İŞLEMLERİ
# ══════════════════════════════════════════════════════════════

def portfoy_kaydet(isim, portfoy):
    """Portföyü Google Sheets'e yaz. Dönüş: (basarili, mesaj)"""
    p_no, p_basi, p_sonu = aktif_periyot()

    # Yarışmacı worksheet'ini bul
    target_ws = None
    for ws in SS.worksheets():
        if isim in ws.title or ws.title in isim:
            target_ws = ws
            break

    if target_ws is None:
        return False, "Sheets'te '{}' sayfasi bulunamadi!".format(isim)

    y_vals = target_ws.get_all_values()

    # Aktif periyot bloğunu bul
    periyot_baslik = "{}. Periyot".format(p_no)
    blok_start = None
    blok_toplam = None

    for i, row in enumerate(y_vals):
        if periyot_baslik in str(row[0]):
            blok_start = i
        if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
            blok_toplam = i
            break

    # Blok yoksa oluştur
    if blok_start is None:
        son_toplam = None
        for i, row in enumerate(y_vals):
            if row[0] == "TOPLAM":
                son_toplam = i

        if son_toplam is None:
            son_toplam = len(y_vals) - 1

        yeni_start = son_toplam + 3  # 1-indexed
        satirlar = [
            ["\U0001f4c5 {}. Periyot".format(p_no), "", "", "", "", "", "", ""],
            ["Hisse", "Agirlik %", "TL", "P.Basi Fiyat", "P.Sonu Fiyat", "Getiri %", "Katki %", "Tutar"],
        ]
        for _ in range(5):
            satirlar.append(["", "", "", "", "", "", "", ""])
        satirlar.append(["TOPLAM", "100%", "", "", "", "", "", ""])

        cell_range = "A{}:H{}".format(yeni_start, yeni_start + len(satirlar) - 1)
        target_ws.update(values=satirlar, range_name=cell_range, value_input_option="USER_ENTERED")
        time.sleep(1)

        y_vals = target_ws.get_all_values()
        blok_start = None
        blok_toplam = None
        for i, row in enumerate(y_vals):
            if periyot_baslik in str(row[0]):
                blok_start = i
            if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                blok_toplam = i
                break

    if blok_start is None or blok_toplam is None:
        return False, "Periyot blogu olusturulamadi!"

    data_start = blok_start + 2  # 0-based
    available_rows = blok_toplam - data_start
    needed_rows = len(portfoy)

    # Ek satır gerekiyorsa ekle
    if needed_rows > available_rows:
        extra = needed_rows - available_rows
        target_ws.insert_rows([[""] * 8] * extra, row=blok_toplam + 1)
        blok_toplam += extra
        time.sleep(1)

    toplam_row_1idx = blok_toplam + 1  # 1-indexed

    # Mevcut satırları temizle
    temiz_cells = []
    for r in range(data_start, blok_toplam):
        for c in range(1, 9):
            temiz_cells.append(gspread.Cell(r + 1, c, ""))
    if temiz_cells:
        target_ws.update_cells(temiz_cells)
        time.sleep(1)

    toplam_tutar = sum(h["tutar"] for h in portfoy)
    df_bugun = snap_bugun_pd()

    cells = []
    formul_updates = []
    pd_bilgileri = []

    # Header satırına H sütunu "Tutar" yaz
    header_row_1idx = blok_start + 2  # 1-indexed
    formul_updates.append({
        "range": "H{}".format(header_row_1idx),
        "values": [["Tutar"]]
    })

    for j, h in enumerate(portfoy):
        row_1idx = data_start + j + 1
        hisse = h["hisse"]
        tutar = h["tutar"]

        cells.append(gspread.Cell(row_1idx, 1, hisse))
        cells.append(gspread.Cell(row_1idx, 3, tutar))

        formul_updates.append({
            "range": "B{}".format(row_1idx),
            "values": [['=IFERROR(ROUND(C{}/C{}*100;1)&"%";"")'.format(row_1idx, toplam_row_1idx)]]
        })

        pd_val = None
        pd_milyon = None
        if hisse.upper() not in ("NAKİT", "NAKIT"):
            # P.Başı PD: bisttum_pd -> snap tarihi -> en yakın tarih
            basi_raw = periyot_basi_pd(hisse, p_basi)
            if basi_raw is not None:
                pd_milyon = round(basi_raw / 1_000_000)
                cells.append(gspread.Cell(row_1idx, 4, pd_milyon))

            # P.Sonu PD: snap_bugun
            if df_bugun is not None and hisse in df_bugun.index:
                sonu_val = float(df_bugun.iloc[:, 0].loc[hisse])
                sonu_milyon = round(sonu_val / 1_000_000)
                cells.append(gspread.Cell(row_1idx, 5, sonu_milyon))

            # F: Getiri formülü
            formul_updates.append({
                "range": "F{}".format(row_1idx),
                "values": [['=IFERROR(ROUND((E{n}-D{n})/D{n}*100;2);"")'.format(n=row_1idx)]]
            })
            # G: Katkı formülü
            formul_updates.append({
                "range": "G{}".format(row_1idx),
                "values": [['=IFERROR(ROUND(F{n}*C{n}/C{t};2);"")'.format(n=row_1idx, t=toplam_row_1idx)]]
            })
        else:
            # NAKİT: F sütununa 14 günlük net faiz getirisi formülü
            formul_updates.append({
                "range": "F{}".format(row_1idx),
                "values": [['=ROUND(((1+0,428*(1-0,175)/365)^14-1)*100;2)']]
            })
            # G: Katkı formülü (NAKİT için de)
            formul_updates.append({
                "range": "G{}".format(row_1idx),
                "values": [['=IFERROR(ROUND(F{n}*C{n}/C{t};2);"")'.format(n=row_1idx, t=toplam_row_1idx)]]
            })

        # H: Tutar formülü (tüm hisseler için, NAKİT dahil)
        formul_updates.append({
            "range": "H{}".format(row_1idx),
            "values": [['=IFERROR(ROUND(C{n}*(1+F{n}/100);2);"")'.format(n=row_1idx)]]
        })

        pd_bilgileri.append({"hisse": hisse, "tutar": tutar, "pd": pd_milyon})

    # TOPLAM satırı
    ilk_hisse_1 = data_start + 1  # 1-indexed
    son_hisse_1 = data_start + len(portfoy)  # 1-indexed
    formul_updates.append({
        "range": "C{}".format(toplam_row_1idx),
        "values": [["=SUM(C{}:C{})".format(ilk_hisse_1, son_hisse_1)]]
    })
    formul_updates.append({
        "range": "B{}".format(toplam_row_1idx),
        "values": [["100%"]]
    })
    # TOPLAM F ve G: portföy toplam getirisi
    formul_updates.append({
        "range": "F{}".format(toplam_row_1idx),
        "values": [["=SUM(G{}:G{})".format(ilk_hisse_1, son_hisse_1)]]
    })
    formul_updates.append({
        "range": "G{}".format(toplam_row_1idx),
        "values": [["=SUM(G{}:G{})".format(ilk_hisse_1, son_hisse_1)]]
    })
    # H TOPLAM: Tutar toplamı
    formul_updates.append({
        "range": "H{}".format(toplam_row_1idx),
        "values": [["=SUM(H{}:H{})".format(ilk_hisse_1, son_hisse_1)]]
    })

    if cells:
        target_ws.update_cells(cells)
    if formul_updates:
        target_ws.batch_update(formul_updates, value_input_option="USER_ENTERED")

    # Format: Calibri 11pt siyah + D,E binlik + F,G ondalıklı
    sheet_id = target_ws.id
    SS.batch_update({
        "requests": [
            # D,E: #,##0 (binlik ayırıcı, ondalıksız)
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": data_start,
                        "endRowIndex": blok_toplam + 1,
                        "startColumnIndex": 3,
                        "endColumnIndex": 5
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": "#,##0"},
                            "textFormat": {
                                "fontFamily": "Calibri", "fontSize": 11,
                                "foregroundColorStyle": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(numberFormat,textFormat)"
                }
            },
            # F,G: 2 ondalıklı
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": data_start,
                        "endRowIndex": blok_toplam + 1,
                        "startColumnIndex": 5,
                        "endColumnIndex": 7
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"},
                            "textFormat": {
                                "fontFamily": "Calibri", "fontSize": 11,
                                "foregroundColorStyle": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(numberFormat,textFormat)"
                }
            },
            # A,B,C,H: Calibri 11pt siyah
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": data_start,
                        "endRowIndex": blok_toplam + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 3
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "fontFamily": "Calibri", "fontSize": 11,
                                "foregroundColorStyle": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat"
                }
            },
        ]
    })

    # Ana Sayfa Portföy güncelle — C sütununa aktif periyot H TOPLAM referansı
    try:
        ws_ana = SS.worksheet("Ana Sayfa")
        ana_vals = ws_ana.get_all_values()
        for i, row in enumerate(ana_vals):
            if len(row) > 1 and isim in row[1]:
                formula = "='{}'!H{}".format(target_ws.title, toplam_row_1idx)
                ws_ana.batch_update([{
                    "range": "C{}".format(i + 1),
                    "values": [[formula]]
                }], value_input_option="USER_ENTERED")
                break
        time.sleep(1)
    except Exception as e:
        log.error("Ana Sayfa portfoy guncelleme hatasi: %s", e)

    # Onay mesajı
    satirlar = []
    satirlar.append("\u2705 {} \u2014 {}P Portfoyu Kaydedildi".format(isim, p_no))
    satirlar.append("")
    for h in pd_bilgileri:
        pd_str = "PD: {:,.0f}M".format(h["pd"]).replace(",", ".") if h["pd"] else ""
        satirlar.append("\U0001f4ca {}  %{}  {}".format(h["hisse"], h["tutar"], pd_str))
    satirlar.append("")
    satirlar.append("Toplam: %{} | {} hisse".format(toplam_tutar, len(portfoy)))
    satirlar.append("\U0001f4c5 {}. Periyot: {} \u2192 {}".format(
        p_no, p_basi.strftime("%d.%m"), p_sonu.strftime("%d.%m")))

    return True, "\n".join(satirlar)


# ══════════════════════════════════════════════════════════════
# BOT KOMUTLARI
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mesaj = (
        "\U0001f3c6 YGF \u2014 Yatirim Getiri Farki\n\n"
        "Portfoy gondermek icin:\n"
        "Selim 50 KLGYO 50 THYAO\n\n"
        "Format: ISIM TUTAR HISSE TUTAR HISSE\n"
        "Toplam 100 olmali."
    )
    await update.message.reply_text(mesaj)


async def cmd_siralama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ws_ana = SS.worksheet("Ana Sayfa")
        ana_vals = ws_ana.get_all_values()

        p_no, _, _ = aktif_periyot()
        satirlar = ["\U0001f3c6 YGF Siralama \u2014 {}P".format(p_no), ""]

        for row in ana_vals[5:]:
            if len(row) < 4:
                continue
            sira = row[0].strip()
            isim = row[1].strip()
            portfoy = row[2].strip()
            getiri = row[3].strip()

            if not isim or isim in ("", "Yarışmacı"):
                continue

            if sira == "\u2014" or sira == "\u2014":
                satirlar.append("\U0001f4c8 {} {} ({})".format(isim, getiri, portfoy))
                continue

            if sira == "1":
                prefix = "\U0001f947"
            elif sira == "2":
                prefix = "\U0001f948"
            elif sira == "3":
                prefix = "\U0001f949"
            else:
                prefix = "{:>2s}.".format(sira)

            satirlar.append("{} {:<12s} {:>8s}  ({})".format(prefix, isim, getiri, portfoy))

        await update.message.reply_text("\n".join(satirlar))
    except Exception as e:
        log.error("Siralama hatasi: %s", e)
        await update.message.reply_text("\u274c Siralama alinamadi: {}".format(e))


async def cmd_periyot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_no, p_basi, p_sonu = aktif_periyot()
    sonraki_basi = p_sonu
    sonraki_sonu = sonraki_basi + timedelta(days=PERIYOT_GUN)
    gun_no = (datetime.now() - p_basi).days + 1

    mesaj = (
        "\U0001f4c5 Aktif: {}P ({} \u2192 {}) Gun {}/{}\n"
        "Sonraki: {}P ({} \u2192 {})"
    ).format(
        p_no, p_basi.strftime("%d.%m"), p_sonu.strftime("%d.%m"), gun_no, PERIYOT_GUN,
        p_no + 1, sonraki_basi.strftime("%d.%m"), sonraki_sonu.strftime("%d.%m"),
    )
    await update.message.reply_text(mesaj)


# ══════════════════════════════════════════════════════════════
# MESAJ HANDLER
# ══════════════════════════════════════════════════════════════

async def mesaj_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metin = update.message.text
    if not metin:
        return

    isim, portfoy, hata = parse_portfoy_mesaji(metin)

    if hata:
        await update.message.reply_text("\u274c {}".format(hata))
        return

    toplam = sum(h["tutar"] for h in portfoy)
    log.info("Portfoy alindi: %s -> %s (toplam: %d)", isim, portfoy, toplam)

    try:
        basarili, mesaj = portfoy_kaydet(isim, portfoy)
        if basarili:
            log.info("Portfoy kaydedildi: %s", isim)
        else:
            log.error("Portfoy kayit hatasi: %s - %s", isim, mesaj)
        await update.message.reply_text(mesaj)
    except Exception as e:
        log.error("Sheets yazim hatasi: %s", e)
        await update.message.reply_text("\u274c Kayit hatasi: {}".format(e))


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    log.info("Bot baslatiliyor...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("siralama", cmd_siralama))
    app.add_handler(CommandHandler("periyot", cmd_periyot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_handler))

    log.info("Bot hazir, polling basliyor...")
    print("Bot baslatildi. Ctrl+C ile durdurun.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

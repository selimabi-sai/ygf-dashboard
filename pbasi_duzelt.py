# -*- coding: utf-8 -*-
"""
P.Basi Duzeltme — bisttum_pd.xlsx'ten dogru periyot basi degerlerini
tum yarismaci sayfalarinin aktif periyot bloklarina yazar.
Sadece D (P.Basi) sutununa dokunur, baska hicbir seyi degistirmez.
"""
import sys, io, os, json, time
from datetime import datetime, timedelta
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AYAR_DOSYA = os.path.join(SCRIPT_DIR, "ygf_ayarlar.json")
VERILER_KLASOR = r"C:\Users\PDS\Desktop\is api\veriler"
YARISMA_BASLANGIC = datetime(2026, 1, 2)
PERIYOT_GUN = 14

with open(AYAR_DOSYA, "r", encoding="utf-8") as f:
    ayarlar = json.load(f)

creds = Credentials.from_service_account_file(ayarlar["credentials_json"], scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(ayarlar["google_sheet_id"])

yarismacilar = ayarlar["yarismacilar"]

# ── bisttum_pd oku ──
bisttum_yol = os.path.join(VERILER_KLASOR, "bisttum_pd.xlsx")
df_pd = pd.read_excel(bisttum_yol, sheet_name="PD", index_col=0)
tarih_sutunlar = []
for col in df_pd.columns:
    if isinstance(col, datetime):
        tarih_sutunlar.append(col)
    else:
        try:
            tarih_sutunlar.append(pd.to_datetime(col))
        except Exception:
            tarih_sutunlar.append(col)
df_pd.columns = tarih_sutunlar
tarih_listesi = [c for c in df_pd.columns if isinstance(c, (datetime, pd.Timestamp))]

# ── Aktif periyot ──
bugun = datetime.now()
for p in range(1, 27):
    basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (p - 1))
    sonu = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * p)
    if basi <= bugun < sonu:
        periyot_no = p
        p_basi = basi
        break
else:
    periyot_no = 26
    p_basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * 25)

# Periyot basina en yakin tarih
oncekiler = [t for t in tarih_listesi if t <= p_basi]
if oncekiler:
    basi_tarih = max(oncekiler)
else:
    basi_tarih = min(tarih_listesi, key=lambda t: abs((t - p_basi).days))

print("=" * 55)
print("  P.BASI DUZELTME")
print("  Aktif periyot: {}P".format(periyot_no))
print("  P.Basi hedef: {} → Kaynak tarih: {}".format(
    p_basi.strftime("%Y-%m-%d"), basi_tarih.strftime("%Y-%m-%d")))
print("=" * 55)

# ── Her yarismaciyi isle ──
ws_dict = {w.title: w for w in ss.worksheets()}

for isim in yarismacilar:
    target_ws = None
    for title, ws_obj in ws_dict.items():
        if isim in title or title in isim:
            target_ws = ws_obj
            break
    if target_ws is None:
        print("  [UYARI] {} sayfasi bulunamadi.".format(isim))
        continue

    y_vals = target_ws.get_all_values()

    # Aktif periyot blogunu bul
    periyot_baslik = "{}. Periyot".format(periyot_no)
    blok_start = None
    blok_toplam = None
    for i, row in enumerate(y_vals):
        if periyot_baslik in str(row[0]):
            blok_start = i
        if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
            blok_toplam = i
            break

    if blok_start is None:
        print("  {} - '{}' bulunamadi.".format(isim, periyot_baslik))
        continue

    data_start = blok_start + 2
    data_end = blok_toplam

    cells = []
    for r in range(data_start, data_end):
        row = y_vals[r]
        hisse = row[0].strip() if row[0] else ""
        if not hisse or hisse.upper() in ("NAKİT", "NAKIT"):
            continue

        if hisse in df_pd.index:
            pd_val = df_pd.loc[hisse, basi_tarih]
            if pd_val and not pd.isna(pd_val):
                cells.append(gspread.Cell(r + 1, 4, round(float(pd_val), 2)))
        else:
            print("    {} - {} bisttum_pd'de yok.".format(isim, hisse))

    if cells:
        target_ws.update_cells(cells)
        print("  {} - {} hisse P.Basi yazildi.".format(isim, len(cells)))
    else:
        print("  {} - degisiklik yok.".format(isim))
    time.sleep(0.5)

print("\n  P.Basi duzeltme tamamlandi!")

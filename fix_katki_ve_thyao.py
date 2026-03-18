# -*- coding: utf-8 -*-
"""
1) Tüm yarışmacı sayfalarında G sütununu (Katkı %) temizle
2) THYAO PD sorununu araştır
"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
VERILER = r"C:\Users\PDS\Desktop\is api\veriler"

# Ayarlar
with open(r"C:\Users\PDS\Desktop\claude\ygf\ygf_ayarlar.json", "r", encoding="utf-8") as f:
    ayar = json.load(f)

creds = Credentials.from_service_account_file(ayar["credentials_json"], scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(ayar["google_sheet_id"])

yarismacilar = ayar["yarismacilar"]

# ═══════════════════════════════════════════
# GÖREV 2: THYAO PD ARAŞTIRMASI
# ═══════════════════════════════════════════
print("=" * 60)
print("  THYAO PD ARAŞTIRMASI")
print("=" * 60)

# bisttum_pd.xlsx
bisttum = os.path.join(VERILER, "bisttum_pd.xlsx")
df_bisttum = pd.read_excel(bisttum, sheet_name="PD", index_col=0)
thyao_row = None
for idx in df_bisttum.index:
    if "THYAO" in str(idx).upper():
        thyao_row = idx
        break

if thyao_row is not None:
    son_col = df_bisttum.columns[-1]
    thyao_bisttum = df_bisttum.loc[thyao_row, son_col]
    print(f"  bisttum_pd.xlsx -> THYAO son sutun ({son_col}): {thyao_bisttum}")
else:
    print("  bisttum_pd.xlsx -> THYAO bulunamadi!")

# snap_bugun_pd (en son)
snap_dosya = os.path.join(VERILER, "snap_bugun_pd_2026-03-16.xlsx")
df_snap = pd.read_excel(snap_dosya, sheet_name="PD", index_col=0)
thyao_snap_row = None
for idx in df_snap.index:
    if "THYAO" in str(idx).upper():
        thyao_snap_row = idx
        break

if thyao_snap_row is not None:
    snap_col = df_snap.columns[0]
    thyao_snap = df_snap.loc[thyao_snap_row, snap_col]
    print(f"  snap_bugun_pd (16.03): THYAO = {thyao_snap}")
else:
    print("  snap_bugun_pd -> THYAO bulunamadi!")

# Sheets'teki Selim sayfası
print("\n  Selim sayfasindan 6P THYAO kontrol ediliyor...")
selim_ws = None
for ws in ss.worksheets():
    if "Selim" in ws.title:
        selim_ws = ws
        break

if selim_ws:
    vals = selim_ws.get_all_values()
    for i, row in enumerate(vals):
        if "6. Periyot" in str(row[0]):
            # Blok başlangıcı bulundu, THYAO'yu ara
            for j in range(i+1, min(i+20, len(vals))):
                if "THYAO" in str(vals[j][0]).upper():
                    print(f"    Satir {j+1}: {vals[j][:8]}")
                    break
                if vals[j][0] == "TOPLAM":
                    break
            break
    time.sleep(2)

# ═══════════════════════════════════════════
# GÖREV 1: G SÜTUNU TEMİZLİĞİ
# ═══════════════════════════════════════════
print("\n" + "=" * 60)
print("  G SÜTUNU (KATKI %) TEMİZLİĞİ")
print("=" * 60)

skip_sheets = {"Ana Sayfa", "Hisse İcmal", "VERİ", "AYARLAR", "Rozetler"}

for ws in ss.worksheets():
    if ws.title in skip_sheets:
        continue
    # Yarışmacı sayfası mı kontrol et
    is_yarismaci = any(y in ws.title or ws.title in y for y in yarismacilar)
    if not is_yarismaci:
        continue

    print(f"\n  {ws.title} isleniyor...")
    vals = ws.get_all_values()

    # G sütunundaki (col 7, 1-indexed) temizlenecek hücreleri bul
    cells_to_clear = []
    in_block = False
    for i, row in enumerate(vals):
        # Periyot başlığı
        if ". Periyot" in str(row[0]):
            in_block = True
            continue
        if in_block:
            g_val = row[6] if len(row) > 6 else ""
            if g_val:  # Boş değilse temizle
                cells_to_clear.append(f"G{i+1}")
            if row[0] == "TOPLAM":
                in_block = False

    if cells_to_clear:
        # Batch clear - her hücreyi boş string yap
        batch = []
        for cell_ref in cells_to_clear:
            batch.append({"range": cell_ref, "values": [[""]]})
        ws.batch_update(batch, value_input_option="RAW")
        print(f"    {len(cells_to_clear)} hucre temizlendi: {cells_to_clear[:5]}...")
    else:
        print(f"    Temizlenecek hucre yok")

    time.sleep(2)

print("\n" + "=" * 60)
print("  TAMAMLANDI")
print("=" * 60)

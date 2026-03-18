# -*- coding: utf-8 -*-
"""
Ana Sayfa Duzeltme:
1. 1-4P eksik getirileri yaz
2. D=Volatilite, E=Poz%, F=Max DD, G=BIST Alfa formulleri
3. A sutunu 1-14 sabit
4. Temiz uniform format
"""
import sys, io, os, json, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AYAR_DOSYA = os.path.join(SCRIPT_DIR, "ygf_ayarlar.json")

with open(AYAR_DOSYA, "r", encoding="utf-8") as f:
    ayarlar = json.load(f)

creds = Credentials.from_service_account_file(ayarlar["credentials_json"], scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(ayarlar["google_sheet_id"])
ws_ana = ss.worksheet("Ana Sayfa")

# ── 1-4P tarihsel getiriler (referans fotodan) ──
# Periyot sutunlari: H=6P, I=5P, J=4P, K=3P, L=2P, M=1P
tarihsel = {
    "Özhan":    {"1P": 11.45, "2P": 16.75, "3P": 7.84,  "4P": -8.20},
    "Serkan":   {"1P": 17.01, "2P": 9.95,  "3P": 3.18,  "4P": -6.73},
    "Barış":    {"1P": 11.72, "2P": 8.42,  "3P": 2.58,  "4P": -6.91},
    "Ali Cenk": {"1P": 9.76,  "2P": 10.72, "3P": 4.28,  "4P": -5.80},
    "BIST 100": {"1P": 10.18, "2P": 9.23,  "3P": 2.47,  "4P": -3.26},
    "Turan":    {"1P": 3.78,  "2P": 9.17,  "3P": 5.09,  "4P": -8.93},
    "Faiz":     {"1P": 1.42,  "2P": 1.42,  "3P": 1.42,  "4P": 1.42},
    "Selim":    {"1P": 24.68, "2P": -6.73, "3P": 3.00,  "4P": -7.74},
    "Berkan":   {"1P": 7.66,  "2P": 6.34,  "3P": 0.62,  "4P": -8.09},
    "Oğuz":     {"1P": 3.96,  "2P": 11.18, "3P": 3.31,  "4P": -5.95},
    "USDTRY":   {"1P": 0.55,  "2P": 0.20,  "3P": 0.45,  "4P": 0.00},
    "Mehmet":   {"1P": 14.90, "2P": 1.56,  "3P": 3.09,  "4P": -6.90},
    "Gürkan":   {"1P": 19.61, "2P": -3.86, "3P": 1.32,  "4P": -12.18},
    "Osman":    {"1P": 21.02, "2P": 0.22,  "3P": -1.74, "4P": -13.54},
}

# Periyot → sutun harfı (1-indexed)
# J=4P(10), K=3P(11), L=2P(12), M=1P(13)
p_col = {"1P": "M", "2P": "L", "3P": "K", "4P": "J"}

print("  Ana Sayfa duzeltme basliyor...")

# ── Mevcut satirlari oku ──
ana_vals = ws_ana.get_all_values()
isim_row = {}  # isim → satir numarasi (1-indexed)
for idx in range(5, min(20, len(ana_vals))):
    row = ana_vals[idx]
    if len(row) > 1 and row[1].strip():
        isim_row[row[1].strip()] = idx + 1

print("  Mevcut satirlar: {}".format(isim_row))

batch = []

# ── 1) 1-4P verilerini yaz ──
for isim, periyotlar in tarihsel.items():
    rn = isim_row.get(isim)
    if rn is None:
        print("  [UYARI] '{}' Ana Sayfa'da bulunamadi.".format(isim))
        continue
    for p_label, col in p_col.items():
        val = periyotlar.get(p_label)
        if val is not None:
            batch.append({"range": "{}{}".format(col, rn), "values": [[val]]})

print("  {} tarihsel deger yazilacak.".format(len(batch)))

# ── 2) D/E/F/G formulleri ──
for isim, rn in isim_row.items():
    # D = Volatilite = STDEV(H:M) — dolu hucrelerin std sapması
    batch.append({"range": "D{}".format(rn),
        "values": [['=IFERROR(STDEV(H{0}:M{0});"")'.format(rn)]]})

    # E = Poz% = pozitif periyot sayisi / toplam dolu periyot sayisi
    batch.append({"range": "E{}".format(rn),
        "values": [['=IFERROR(COUNTIF(H{0}:M{0};">"&0)/COUNTA(H{0}:M{0});"")'.format(rn)]]})

    # F = Max DD = en kotu periyot getirisi
    batch.append({"range": "F{}".format(rn),
        "values": [['=IFERROR(MIN(H{0}:M{0});"")'.format(rn)]]})

    # G = BIST Alfa = Portfoy toplam getiri - BIST toplam getiri
    batch.append({"range": "G{}".format(rn),
        "values": [['=IFERROR(C{0}-INDEX($C$6:$C$19;MATCH("BIST 100";$B$6:$B$19;0));"")'.format(rn)]]})

print("  {} formul yazilacak.".format(len(batch) - len([b for b in batch if b["range"][0] in "JKLM"])))

# ── 3) A sutunu 1-14 ──
for i, rn in enumerate(sorted(isim_row.values())):
    batch.append({"range": "A{}".format(rn), "values": [[i + 1]]})

print("  1-14 numaralama yazilacak.")

# ── Toplu yaz ──
if batch:
    ws_ana.batch_update(batch, value_input_option="USER_ENTERED")
    print("  {} hucre guncellendi.".format(len(batch)))
time.sleep(2)

# ── 4) Format duzeltme ──
ana_sheet_id = ws_ana.id
fmt = []

# Tum veri alani (A6:M19) uniform beyaz arka plan, siyah yazi
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "cell": {"userEnteredFormat": {
        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
        "textFormat": {"fontFamily": "Calibri", "fontSize": 10,
                       "foregroundColor": {"red": 0, "green": 0, "blue": 0},
                       "bold": False},
    }},
    "fields": "userEnteredFormat(backgroundColor,textFormat)"
}})

# A sutunu (sira no) — center
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 0, "endColumnIndex": 1},
    "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
    "fields": "userEnteredFormat.horizontalAlignment"
}})

# C (portfoy) sayi formati 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 2, "endColumnIndex": 3},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"},
             "horizontalAlignment": "RIGHT"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# D (volatilite) 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 3, "endColumnIndex": 4},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"},
             "horizontalAlignment": "RIGHT"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# E (poz%) yuzde formati
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 4, "endColumnIndex": 5},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"},
             "horizontalAlignment": "CENTER"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# F (max dd) 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 5, "endColumnIndex": 6},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"},
             "horizontalAlignment": "RIGHT"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# G (bist alfa) 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 6, "endColumnIndex": 7},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"},
             "horizontalAlignment": "RIGHT"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# H-M (periyot sutunlari) 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 7, "endColumnIndex": 13},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"},
             "horizontalAlignment": "RIGHT"}},
    "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
}})

# Satirlar arasi cizgileri kaldir (tum ic kenarliklari sifirla)
fmt.append({"updateBorders": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "innerHorizontal": {"style": "NONE"},
    "innerVertical": {"style": "NONE"},
}})

# Alt kenarligi ince cizgi
fmt.append({"updateBorders": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
}})

ss.batch_update({"requests": fmt})
print("  Format duzeltildi.")
time.sleep(1)

print("\n  Duzeltme tamamlandi!")

# -*- coding: utf-8 -*-
"""
Kapsamli Ana Sayfa Duzeltme — HICBIR SEY SILINMIYOR.
Sadece hedef hucrelere yazilir. Mevcut veriler korunur.

1. Bos satir kaymasini duzelt (B sütununda bosluk varsa satiri kaydir)
2. 1-4P tarihsel getirileri yaz (sabit degerler)
3. C + 5P + 6P formullerini yaz
4. D-G formullerini yaz
5. A sutunu 1-14
6. Sayi formati 2 ondalik
7. sortRange B-M (A sabit), endRow=20
8. Cizgi en alt satira
"""
import sys, io, os, json, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, "ygf_ayarlar.json"), "r", encoding="utf-8") as f:
    ayarlar = json.load(f)

creds = Credentials.from_service_account_file(ayarlar["credentials_json"], scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(ayarlar["google_sheet_id"])
ws = ss.worksheet("Ana Sayfa")
sid = ws.id

print("=" * 55)
print("  KAPSAMLI ANA SAYFA DUZELTME")
print("=" * 55)

# ══════════════════════════════════════════════════════════
# ADIM 1: Bos satir kaymasini duzelt
# ══════════════════════════════════════════════════════════
print("\n  1) Bos satir kontrol...")
raw = ws.get("A6:M20", value_render_option="UNFORMATTED_VALUE")
dolu = []
bos_var = False
for row in raw:
    if row and len(row) > 1 and row[1] and str(row[1]).strip():
        padded = list(row) + [''] * max(0, 13 - len(row))
        dolu.append(padded[:13])
    else:
        bos_var = True

if bos_var:
    # Dolu satirlari basa topla, kalanini bosalt
    while len(dolu) < 15:
        dolu.append([''] * 13)
    ws.update(values=dolu, range_name="A6:M20", value_input_option="RAW")
    time.sleep(1)
    print("    Kayma duzeltildi. {} dolu satir.".format(
        sum(1 for r in dolu if r[1] and str(r[1]).strip())))
else:
    print("    Kayma yok.")
time.sleep(1)

# ══════════════════════════════════════════════════════════
# ADIM 2: 1-4P tarihsel getirileri (sabit degerler)
# ══════════════════════════════════════════════════════════
print("\n  2) 1-4P tarihsel getirileri yaziliyor...")

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

# Periyot haritasini header'dan oku
ana_vals = ws.get_all_values()
ana_header = ana_vals[4] if len(ana_vals) > 4 else []
periyot_map = {}
for i, h in enumerate(ana_header):
    if h.endswith("P") and h[:-1].isdigit():
        periyot_map[int(h[:-1])] = i  # 0-indexed

print("    Periyot haritasi: {}".format(
    {k: chr(65+v) for k, v in sorted(periyot_map.items())}))

# Isim → satir numarasi haritasi
isim_row = {}
for idx in range(5, min(20, len(ana_vals))):
    row = ana_vals[idx]
    if len(row) > 1 and row[1] and str(row[1]).strip():
        isim_row[str(row[1]).strip()] = idx + 1  # 1-indexed

batch = []
tarihsel_sayac = 0
for isim, periyotlar in tarihsel.items():
    rn = isim_row.get(isim)
    if rn is None:
        print("    [UYARI] '{}' bulunamadi.".format(isim))
        continue
    for p_no, getiri in periyotlar.items():
        p_int = int(p_no.replace("P", ""))
        col_idx = periyot_map.get(p_int)
        if col_idx is not None:
            cl = chr(65 + col_idx)
            batch.append({"range": "{}{}".format(cl, rn), "values": [[getiri]]})
            tarihsel_sayac += 1

print("    {} tarihsel deger yazilacak.".format(tarihsel_sayac))

# ══════════════════════════════════════════════════════════
# ADIM 3: C + 5P + 6P formullerini yaz
# ══════════════════════════════════════════════════════════
print("\n  3) C + periyot formulleri yaziliyor...")

ws_dict = {w.title: w for w in ss.worksheets()}
sorted_periyots = sorted(periyot_map.keys(), reverse=True)
aktif_periyot = max(periyot_map.keys()) if periyot_map else 6

formul_sayac = 0
for isim, rn in isim_row.items():
    sayfa_adi = None
    for title in ws_dict:
        if isim == title or isim in title or title in isim:
            sayfa_adi = title
            break
    if not sayfa_adi:
        continue

    try:
        yv = ws_dict[sayfa_adi].get_all_values()
        for p in sorted_periyots:
            # Sadece 5P ve 6P (aktif) icin formul yaz, 1-4P zaten sabit yazildi
            if p <= 4:
                continue
            baslik = "{}. Periyot".format(p)
            found = False
            for yi, yr in enumerate(yv):
                c0 = str(yr[0]) if yr else ""
                if baslik in c0:
                    found = True
                if found and c0.strip() == "TOPLAM":
                    tr = yi + 1
                    ci = periyot_map.get(p)
                    if ci is not None:
                        cl = chr(65 + ci)
                        batch.append({"range": "{}{}".format(cl, rn),
                            "values": [["='{}'!F{}".format(sayfa_adi, tr)]]})
                        formul_sayac += 1
                    if p == aktif_periyot:
                        batch.append({"range": "C{}".format(rn),
                            "values": [["='{}'!H{}".format(sayfa_adi, tr)]]})
                        formul_sayac += 1
                    found = False
                    break
        time.sleep(0.2)
    except Exception as e:
        print("    [HATA] {}: {}".format(isim, e))

print("    {} formul yazilacak.".format(formul_sayac))

# ══════════════════════════════════════════════════════════
# ADIM 4: D-G formulleri
# ══════════════════════════════════════════════════════════
print("\n  4) D-G formulleri yaziliyor...")
for isim, rn in isim_row.items():
    # D = Volatilite
    batch.append({"range": "D{}".format(rn),
        "values": [['=IFERROR(STDEV(H{0}:M{0});"")'.format(rn)]]})
    # E = Poz%
    batch.append({"range": "E{}".format(rn),
        "values": [['=IFERROR(COUNTIF(H{0}:M{0};">"&0)/COUNTA(H{0}:M{0});"")'.format(rn)]]})
    # F = Max DD
    batch.append({"range": "F{}".format(rn),
        "values": [['=IFERROR(MIN(H{0}:M{0});"")'.format(rn)]]})
    # G = BIST Alfa
    batch.append({"range": "G{}".format(rn),
        "values": [['=IFERROR(C{0}-INDEX($C$6:$C$20;MATCH("BIST 100";$B$6:$B$20;0));"")'.format(rn)]]})

# ══════════════════════════════════════════════════════════
# ADIM 5: A sutunu 1-14
# ══════════════════════════════════════════════════════════
print("\n  5) A sutunu 1-14...")
sorted_rows = sorted(isim_row.values())
for i, rn in enumerate(sorted_rows):
    batch.append({"range": "A{}".format(rn), "values": [[i + 1]]})

# ══════════════════════════════════════════════════════════
# TOPLU YAZ (tek batch — hic silme yok)
# ══════════════════════════════════════════════════════════
print("\n  Toplu yazim: {} hucre...".format(len(batch)))
if batch:
    ws.batch_update(batch, value_input_option="USER_ENTERED")
print("  Yazim tamamlandi.")
time.sleep(3)  # Formullerin hesaplanmasi icin bekle

# ══════════════════════════════════════════════════════════
# ADIM 6: Sayi formati
# ══════════════════════════════════════════════════════════
print("\n  6) Sayi formati duzeltiliyor...")
fmt = []

# C: 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 2, "endColumnIndex": 3},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# D: 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 3, "endColumnIndex": 4},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# E: yuzde (0.83 → %83)
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 4, "endColumnIndex": 5},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# F: 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 5, "endColumnIndex": 6},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# G: 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 6, "endColumnIndex": 7},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# H-M: 2 ondalik
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 7, "endColumnIndex": 13},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
    "fields": "userEnteredFormat.numberFormat"}})

# Uniform beyaz arka plan + temiz font
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "cell": {"userEnteredFormat": {
        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
        "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": False,
                       "foregroundColor": {"red": 0, "green": 0, "blue": 0}},
    }},
    "fields": "userEnteredFormat(backgroundColor,textFormat)"}})

# Tum borderleri temizle
fmt.append({"updateBorders": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "innerHorizontal": {"style": "NONE"},
    "innerVertical": {"style": "NONE"},
    "top": {"style": "NONE"},
    "bottom": {"style": "NONE"},
    "left": {"style": "NONE"},
    "right": {"style": "NONE"}}})

# En alt dolu satirun altina ince cizgi
son_row_0 = 5 + len(isim_row) - 1
fmt.append({"updateBorders": {
    "range": {"sheetId": sid, "startRowIndex": son_row_0, "endRowIndex": son_row_0 + 1,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}}}})

ss.batch_update({"requests": fmt})
print("  Format tamamlandi.")
time.sleep(1)

# ══════════════════════════════════════════════════════════
# ADIM 7: sortRange B-M, C'ye gore (A sabit)
# ══════════════════════════════════════════════════════════
print("\n  7) sortRange...")
ss.batch_update({"requests": [{
    "sortRange": {
        "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
                  "startColumnIndex": 1, "endColumnIndex": 13},
        "sortSpecs": [{"dimensionIndex": 2, "sortOrder": "DESCENDING"}]
    }
}]})
print("  sortRange tamamlandi.")

print("\n" + "=" * 55)
print("  DUZELTME TAMAMLANDI!")
print("=" * 55)

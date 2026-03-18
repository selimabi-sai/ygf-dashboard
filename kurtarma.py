# -*- coding: utf-8 -*-
"""
Ana Sayfa Kurtarma — Yarismacilari geri yaz, formulleri kur, format duzelt.
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

yarismacilar = ayarlar["yarismacilar"]
benchmarks = ["BIST 100", "USDTRY", "Faiz"]
tum_isimler = yarismacilar + benchmarks  # 14 satir (11 + 3)

print("  Ana Sayfa kurtarma basliyor...")
print("  {} yarismacilar + {} benchmark = {} satir".format(
    len(yarismacilar), len(benchmarks), len(tum_isimler)))

# ── 1) A6:M20 temizle ──
bos = [[''] * 13 for _ in range(15)]
ws_ana.update(values=bos, range_name="A6:M20", value_input_option="RAW")
time.sleep(1)
print("  A6:M20 temizlendi.")

# ── 2) Yarismaci + benchmark isimlerini yaz (A + B sutunlari) ──
ab_data = []
sira = 0
for isim in tum_isimler:
    if isim in benchmarks:
        ab_data.append(["\u2014", isim])
    else:
        sira += 1
        ab_data.append([sira, isim])
while len(ab_data) < 15:
    ab_data.append(["", ""])

ws_ana.update(values=ab_data, range_name="A6:B20", value_input_option="RAW")
time.sleep(1)
print("  {} isim yazildi.".format(len(tum_isimler)))

# ── 3) Tum worksheetleri oku ──
ws_dict = {}
for ws_item in ss.worksheets():
    ws_dict[ws_item.title] = ws_item

# ── 4) C + periyot formulleri yaz ──
# Periyot haritasi
ana_vals = ws_ana.get_all_values()
ana_header = ana_vals[4] if len(ana_vals) > 4 else []
periyot_map = {}
for i, h in enumerate(ana_header):
    if h.endswith("P") and h[:-1].isdigit():
        periyot_map[int(h[:-1])] = i

sorted_periyots = sorted(periyot_map.keys(), reverse=True)
aktif_periyot = max(periyot_map.keys()) if periyot_map else 6

print("  Periyot haritasi: {}".format(
    {k: chr(65+v) for k, v in sorted(periyot_map.items())}))
print("  Aktif periyot: {}P".format(aktif_periyot))

formula_batch = []
for si, isim in enumerate(tum_isimler):
    row_num = 6 + si

    sayfa_adi = None
    for title in ws_dict:
        if isim == title or isim in title or title in isim:
            sayfa_adi = title
            break
    if not sayfa_adi:
        print("  [UYARI] '{}' icin sayfa bulunamadi.".format(isim))
        continue

    y_ws = ws_dict[sayfa_adi]
    try:
        y_vals = y_ws.get_all_values()

        for p in sorted_periyots:
            p_baslik = "{}. Periyot".format(p)
            found = False
            for yi, yrow in enumerate(y_vals):
                cell0 = str(yrow[0]) if yrow else ""
                if p_baslik in cell0:
                    found = True
                if found and cell0.strip() == "TOPLAM":
                    toplam_row = yi + 1
                    col_idx = periyot_map.get(p)
                    if col_idx is not None:
                        cl = chr(65 + col_idx)
                        formula_batch.append({"range": "{}{}".format(cl, row_num),
                            "values": [["='{}'!F{}".format(sayfa_adi, toplam_row)]]})
                    if p == aktif_periyot:
                        formula_batch.append({"range": "C{}".format(row_num),
                            "values": [["='{}'!H{}".format(sayfa_adi, toplam_row)]]})
                    found = False
                    break

        print("  {} → '{}' formulleri hazir.".format(isim, sayfa_adi))
    except Exception as e:
        print("  [HATA] {}: {}".format(isim, e))

if formula_batch:
    ws_ana.batch_update(formula_batch, value_input_option="USER_ENTERED")
    print("  {} formul yazildi.".format(len(formula_batch)))
time.sleep(2)

# ── 5) Sayi formati: 2 ondalik ──
ana_sheet_id = ws_ana.id
fmt_requests = []

# C6:C20 (Portfoy) — 2 ondalik
fmt_requests.append({"repeatCell": {
    "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 2, "endColumnIndex": 3},
    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}}},
    "fields": "userEnteredFormat.numberFormat"
}})

# H-M (periyot sutunlari) — 2 ondalik
for col_idx in periyot_map.values():
    fmt_requests.append({"repeatCell": {
        "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 20,
                  "startColumnIndex": col_idx, "endColumnIndex": col_idx + 1},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}}},
        "fields": "userEnteredFormat.numberFormat"
    }})

ss.batch_update({"requests": fmt_requests})
print("  Sayi formati duzeltildi.")
time.sleep(1)

# ── 6) sortRange: B-M arasi, C'ye gore (A sabit kaliyor) ──
ss.batch_update({"requests": [{
    "sortRange": {
        "range": {"sheetId": ana_sheet_id, "startRowIndex": 5, "endRowIndex": 19,
                  "startColumnIndex": 1, "endColumnIndex": 13},
        "sortSpecs": [{"dimensionIndex": 2, "sortOrder": "DESCENDING"}]
    }
}]})
print("  sortRange tamamlandi (B-M, A sabit).")

print("\n  Kurtarma tamamlandi!")

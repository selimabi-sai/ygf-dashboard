# -*- coding: utf-8 -*-
"""Kayma duzeltme — bos satir temizle, sort range'i 6-20 yap."""
import sys, io, os, json, time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, "ygf_ayarlar.json"), "r", encoding="utf-8") as f:
    ayarlar = json.load(f)

creds = Credentials.from_service_account_file(ayarlar["credentials_json"], scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(ayarlar["google_sheet_id"])
ws = ss.worksheet("Ana Sayfa")
sid = ws.id

# 1) B6:M20 oku (UNFORMATTED), bos satirlari filtrele
raw = ws.get("B6:M20", value_render_option="UNFORMATTED_VALUE")
dolu = []
for row in raw:
    if row and len(row) > 0 and str(row[0]).strip():
        padded = list(row) + [''] * max(0, 12 - len(row))
        dolu.append(padded[:12])

print("  {} dolu satir bulundu.".format(len(dolu)))

# 2) B6:M20 temizle, dolu satirlari basa yaz
bos = [[''] * 12 for _ in range(15)]
ws.update(values=bos, range_name="B6:M20", value_input_option="RAW")
time.sleep(1)

end_row = 6 + len(dolu) - 1
ws.update(values=dolu, range_name="B6:M{}".format(end_row), value_input_option="RAW")
time.sleep(1)
print("  B6:M{} yazildi.".format(end_row))

# 3) A6:A20 numarala (1-14, fazlasi bos)
nums = [[i+1] for i in range(len(dolu))]
while len(nums) < 15:
    nums.append([''])
ws.update(values=nums, range_name="A6:A20", value_input_option="RAW")
time.sleep(1)

# 4) Tum ic cizgileri kaldir, sadece en alt cizgi
fmt = []
# Tum borderleri temizle
fmt.append({"updateBorders": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "innerHorizontal": {"style": "NONE"},
    "innerVertical": {"style": "NONE"},
    "top": {"style": "NONE"},
    "bottom": {"style": "NONE"},
    "left": {"style": "NONE"},
    "right": {"style": "NONE"},
}})

# Son dolu satirun altina ince cizgi
son_row_0 = 5 + len(dolu) - 1  # 0-indexed son satir
fmt.append({"updateBorders": {
    "range": {"sheetId": sid, "startRowIndex": son_row_0, "endRowIndex": son_row_0 + 1,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
}})

# Uniform arka plan (beyaz)
fmt.append({"repeatCell": {
    "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
              "startColumnIndex": 0, "endColumnIndex": 13},
    "cell": {"userEnteredFormat": {
        "backgroundColor": {"red": 1, "green": 1, "blue": 1},
    }},
    "fields": "userEnteredFormat.backgroundColor"
}})

ss.batch_update({"requests": fmt})
print("  Format duzeltildi.")

# 5) C+periyot formullerini yeniden yaz
ana_vals = ws.get_all_values()
ana_header = ana_vals[4] if len(ana_vals) > 4 else []
periyot_map = {}
for i, h in enumerate(ana_header):
    if h.endswith("P") and h[:-1].isdigit():
        periyot_map[int(h[:-1])] = i
sorted_p = sorted(periyot_map.keys(), reverse=True)
aktif_p = max(periyot_map.keys()) if periyot_map else 6

ws_dict = {w.title: w for w in ss.worksheets()}
fbatch = []
for idx in range(5, min(20, len(ana_vals))):
    row = ana_vals[idx]
    if not row or len(row) < 2 or not str(row[1]).strip():
        continue
    isim = str(row[1]).strip()
    rn = idx + 1

    sayfa = None
    for t in ws_dict:
        if isim == t or isim in t or t in isim:
            sayfa = t
            break
    if not sayfa:
        continue

    try:
        yv = ws_dict[sayfa].get_all_values()
        for p in sorted_p:
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
                        fbatch.append({"range": "{}{}".format(cl, rn),
                            "values": [["='{}'!F{}".format(sayfa, tr)]]})
                    if p == aktif_p:
                        fbatch.append({"range": "C{}".format(rn),
                            "values": [["='{}'!H{}".format(sayfa, tr)]]})
                    found = False
                    break
        time.sleep(0.2)
    except Exception as e:
        print("  [HATA] {}: {}".format(isim, e))

if fbatch:
    ws.batch_update(fbatch, value_input_option="USER_ENTERED")
    print("  {} formul yazildi.".format(len(fbatch)))
time.sleep(2)

# 6) sortRange B-M, C'ye gore (A sabit) — endRowIndex=20
ss.batch_update({"requests": [{
    "sortRange": {
        "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": 20,
                  "startColumnIndex": 1, "endColumnIndex": 13},
        "sortSpecs": [{"dimensionIndex": 2, "sortOrder": "DESCENDING"}]
    }
}]})
print("  sortRange tamamlandi.")

print("\n  Duzeltme bitti!")

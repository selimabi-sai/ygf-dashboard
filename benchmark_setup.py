# -*- coding: utf-8 -*-
"""
Benchmark Sayfa Kurulum — Tek sefer calistirilir.
Google Finance formulleri dogrudan benchmark sayfalarinda.
Ana Sayfa'daki panel bolumleri silinir.

Sayfa yapisi (her periyot 5 satir):
  P{n} baslik = 3 + (n-1)*5    (1-indexed)
  P{n} header = baslik + 1
  P{n} data   = baslik + 2  = 5n
  P{n} TOPLAM = baslik + 3  = 5n + 1
  bos         = baslik + 4

Canli fiyat hucresi: J1
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

BENCHMARKS = {
    "BIST 100": {
        "varlik": "XU100",
        "gfinance": '=GOOGLEFINANCE("BIST:XU100")',
        "periyotlar": {
            1: {"getiri": 10.18, "portfoy": 110.18},
            2: {"getiri": 9.23,  "portfoy": 120.35},
            3: {"getiri": 2.47,  "portfoy": 123.32},
            4: {"getiri": -3.26, "portfoy": 119.30},
            5: {"getiri": -5.55, "portfoy": 112.68},
        },
        "p6_pbasi": 13092.93,
    },
    "USDTRY": {
        "varlik": "USDTRY",
        "gfinance": '=GOOGLEFINANCE("CURRENCY:USDTRY")',
        "periyotlar": {
            1: {"getiri": 0.55, "portfoy": 100.55},
            2: {"getiri": 0.20, "portfoy": 100.75},
            3: {"getiri": 0.45, "portfoy": 101.20},
            4: {"getiri": 0.00, "portfoy": 101.20},
            5: {"getiri": 0.51, "portfoy": 101.72},
        },
        "p6_pbasi": 43.97,
    },
    "Faiz": {
        "varlik": "FAIZ",
        "gfinance": None,
        "periyotlar": {
            1: {"getiri": 1.42, "portfoy": 101.42},
            2: {"getiri": 1.42, "portfoy": 102.86},
            3: {"getiri": 1.42, "portfoy": 104.32},
            4: {"getiri": 1.42, "portfoy": 105.80},
            5: {"getiri": 1.42, "portfoy": 107.30},
        },
        "p6_getiri": 1.36,
    },
}


def build_sheet(bench_name, bd):
    print("\n  {} olusturuluyor...".format(bench_name))

    try:
        ws = ss.worksheet(bench_name)
        ws.clear()
        try:
            ss.batch_update({"requests": [{"unmergeCells": {"range": {
                "sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 140,
                "startColumnIndex": 0, "endColumnIndex": 12}}}]})
        except Exception:
            pass
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=bench_name, rows=140, cols=12)
    time.sleep(1)

    # ── Veri ──
    all_data = []
    all_data.append([bench_name])  # Row 1
    all_data.append([""])          # Row 2

    for p in range(1, 27):
        all_data.append(["{}. Periyot".format(p)])
        all_data.append(["Varlik", "Agirlik", "Tutar", "P.Basi", "P.Sonu",
                         "Getiri", "Katki", "Portfoy"])
        if p <= 5:
            pd = bd["periyotlar"][p]
            all_data.append([bd["varlik"], 100, "", "", "",
                             pd["getiri"], pd["getiri"], pd["portfoy"]])
            all_data.append(["TOPLAM", "", pd["portfoy"], "", "",
                             pd["getiri"], "", pd["portfoy"]])
        elif p == 6:
            if bd.get("gfinance"):
                all_data.append([bd["varlik"], 100, "", bd.get("p6_pbasi", ""),
                                 "", "", "", ""])
            else:
                all_data.append([bd["varlik"], 100, "", "", "",
                                 bd.get("p6_getiri", ""), "", ""])
            all_data.append(["TOPLAM", "", "", "", "", "", "", ""])
        else:
            all_data.append([bd["varlik"], 100, "", "", "", "", "", ""])
            all_data.append(["TOPLAM", "", "", "", "", "", "", ""])
        all_data.append([""])

    # Faiz hesaplama tablosu
    if bench_name == "Faiz":
        all_data.append([""])
        all_data.append(["FAİZ ORAN"])
        all_data.append(["Oran değiştiğinde yeni satır ekle. Stopaj: %17,5"])
        all_data.append(["Başlangıç", "Brüt Oran", "Stopaj", "Net Oran",
                         "Gün", "Dönem Getir", "Kümülatif"])
        all_data.append(["02.01.2026", 0.428, 0.175, "", "", "", ""])

    ws.update(values=all_data, range_name="A1:H{}".format(len(all_data)),
              value_input_option="RAW")
    time.sleep(2)

    # ── Canli fiyat hucresi (J1) ──
    formulas = []
    if bd.get("gfinance"):
        formulas.append({"range": "J1", "values": [[bd["gfinance"]]]})
        formulas.append({"range": "I1", "values": [["Canlı:"]]})

    # ── 6P formuller ──
    dr = 30  # data row
    tr = 31  # TOPLAM row
    prev_h = 26  # 5P TOPLAM H satiri

    if bd.get("gfinance"):
        formulas.append({"range": "E{}".format(dr), "values": [["=$J$1"]]})
        formulas.append({"range": "F{}".format(dr),
                         "values": [["=(E{0}-D{0})/D{0}*100".format(dr)]]})

    formulas.append({"range": "G{}".format(dr), "values": [["=F{}".format(dr)]]})
    formulas.append({"range": "H{}".format(dr),
                     "values": [["=H{}*(1+F{}/100)".format(prev_h, dr)]]})
    formulas.append({"range": "C{}".format(tr), "values": [["=H{}".format(dr)]]})
    formulas.append({"range": "F{}".format(tr), "values": [["=F{}".format(dr)]]})
    formulas.append({"range": "H{}".format(tr), "values": [["=H{}".format(dr)]]})

    # Faiz hesaplama tablosu formulleri
    if bench_name == "Faiz":
        r = len(all_data)  # Son satir (faiz veri satiri)
        formulas.append({"range": "D{}".format(r), "values": [["=B{0}*(1-C{0})".format(r)]]})
        formulas.append({"range": "E{}".format(r), "values": [['=DAYS(TODAY();A{})'.format(r)]]})
        formulas.append({"range": "F{}".format(r),
                         "values": [["=(1+D{0}/365)^E{0}".format(r)]]})
        formulas.append({"range": "G{}".format(r), "values": [["=F{}".format(r)]]})

    ws.batch_update(formulas, value_input_option="USER_ENTERED")
    time.sleep(1)

    # ── Formatlama ──
    sid = ws.id
    lac = {"red": 0.122, "green": 0.306, "blue": 0.475}
    byz = {"rgbColor": {"red": 1, "green": 1, "blue": 1}}
    fmt = []

    fmt.append({"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 0,
        "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8},
        "mergeType": "MERGE_ALL"}})
    fmt.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0,
        "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8},
        "cell": {"userEnteredFormat": {"backgroundColor": lac,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 14, "bold": True,
                "foregroundColorStyle": byz}, "horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}})

    for p in range(26):
        t0 = 2 + p * 5
        h0 = t0 + 1
        fmt.append({"repeatCell": {"range": {"sheetId": sid,
            "startRowIndex": t0, "endRowIndex": t0 + 1,
            "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"backgroundColor": lac,
                "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": True,
                    "foregroundColorStyle": byz}}},
            "fields": "userEnteredFormat(backgroundColor,textFormat)"}})
        fmt.append({"repeatCell": {"range": {"sheetId": sid,
            "startRowIndex": h0, "endRowIndex": h0 + 1,
            "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri",
                "fontSize": 10, "bold": True}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}})

    if bench_name == "Faiz":
        faiz_title = len(all_data) - 4  # 0-indexed
        fmt.append({"repeatCell": {"range": {"sheetId": sid,
            "startRowIndex": faiz_title, "endRowIndex": faiz_title + 1,
            "startColumnIndex": 0, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"backgroundColor": lac,
                "textFormat": {"fontFamily": "Calibri", "fontSize": 12, "bold": True,
                    "foregroundColorStyle": byz}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}})

    for ci, w in enumerate([85, 60, 70, 85, 85, 65, 65, 80]):
        fmt.append({"updateDimensionProperties": {"range": {"sheetId": sid,
            "dimension": "COLUMNS", "startIndex": ci, "endIndex": ci + 1},
            "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    ss.batch_update({"requests": fmt})
    time.sleep(1)
    print("    {} tamamlandi.".format(bench_name))


# ══════════════════════════════════════════════════════════
for bench_name, bd in BENCHMARKS.items():
    build_sheet(bench_name, bd)

# ── Ana Sayfa: Panel bolumlerini sil (Row 22+) ──
print("\n  Ana Sayfa panel bolumleri temizleniyor...")
ws_ana = ss.worksheet("Ana Sayfa")
ana_vals = ws_ana.get_all_values()

# Row 22'den sonrasini temizle (Kiyaslama, Periyot Getirileri, Faiz Oran)
if len(ana_vals) > 21:
    son_satir = len(ana_vals)
    bos = [[''] * 10 for _ in range(son_satir - 21)]
    ws_ana.update(values=bos,
                  range_name="A22:J{}".format(son_satir),
                  value_input_option="RAW")
    print("    Satir 22-{} temizlendi.".format(son_satir))
time.sleep(1)

# ── Ana Sayfa benchmark satirlarini kontrol et ──
print("  Benchmark satirlari kontrol...")
ana_vals = ws_ana.get_all_values()
mevcut = {}
for idx in range(5, min(20, len(ana_vals))):
    row = ana_vals[idx]
    if len(row) > 1 and row[1].strip():
        mevcut[row[1].strip()] = idx + 1

for bn in BENCHMARKS:
    if bn in mevcut:
        print("    {} satir {}'de.".format(bn, mevcut[bn]))
    else:
        for idx in range(5, 20):
            if idx >= len(ana_vals) or not ana_vals[idx] or len(ana_vals[idx]) < 2 or not ana_vals[idx][1].strip():
                ws_ana.update(values=[["\u2014", bn]],
                              range_name="A{}:B{}".format(idx+1, idx+1),
                              value_input_option="RAW")
                print("    {} satir {}'e eklendi.".format(bn, idx+1))
                time.sleep(0.5)
                break

# ── A sutununu sabit numarala (1-14) ──
ana_vals = ws_ana.get_all_values()
benchmarks_set = {"Faiz", "BIST 100", "USDTRY"}
num_batch = []
sira = 0
for idx in range(5, min(19, len(ana_vals))):
    row = ana_vals[idx]
    if not row or len(row) < 2 or not str(row[1]).strip():
        continue
    isim = str(row[1]).strip()
    rn = idx + 1
    if isim in benchmarks_set:
        num_batch.append({"range": "A{}".format(rn), "values": [["\u2014"]]})
    else:
        sira += 1
        num_batch.append({"range": "A{}".format(rn), "values": [[sira]]})
if num_batch:
    ws_ana.batch_update(num_batch, value_input_option="RAW")
    print("    {} satir numaralandi.".format(len(num_batch)))

print("\n  Kurulum tamamlandi! Simdi ygf_guncelle.py calistirin.")

# -*- coding: utf-8 -*-
"""
Tüm yarışmacı sayfalarında 26 periyotluk standart yapı oluştur.
Her periyot: başlık + header + 7 veri satırı + TOPLAM + boşluk = 11 satır
Mevcut verileri korur.
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from google.oauth2.service_account import Credentials

CREDS = r"C:\Users\PDS\Desktop\snap code\credentials.json"
SHEET_ID = "1RvQnrukTy8LVxWjskFYUzlpCOuAqEU9IH7YTFM2XJQI"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CREDS, scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SHEET_ID)

SATIR_PER_BLOK = 11   # başlık(1) + header(1) + veri(7) + toplam(1) + boşluk(1)
VERI_SATIR = 7
PERIYOT_SAYISI = 26
HEADER_SATIRLARI = 4  # sayfanın ilk 4 satırı (portföy özet)
TOPLAM_SATIR = HEADER_SATIRLARI + PERIYOT_SAYISI * SATIR_PER_BLOK  # 4 + 286 = 290

ws_list = ss.worksheets()

for idx in range(1, 12):
    ws = ws_list[idx]
    print("\n" + "=" * 50)
    print("  {}".format(ws.title))
    print("=" * 50)

    # ── 1) Mevcut verileri oku ──
    vals = ws.get_all_values()
    # Ayrıca formülleri de oku (B, F, G sütunları formül olabilir)
    formulas = ws.get("A1:H{}".format(len(vals)), value_render_option="FORMULA")
    # Unformatted values (sayıları doğru almak için)
    uvals = ws.get("A1:H{}".format(len(vals)), value_render_option="UNFORMATTED_VALUE")

    # İlk 4 satırı sakla (portföy özet)
    header_rows = vals[:HEADER_SATIRLARI]

    # Mevcut periyot verilerini çıkar
    mevcut_periyotlar = {}  # {periyot_no: {"hisseler": [...], "toplam_f": ..., ...}}

    i = HEADER_SATIRLARI
    while i < len(vals):
        row = vals[i]
        # Periyot başlığı mı?
        for p in range(1, 27):
            if "{}. Periyot".format(p) in str(row[0]):
                # Bu periyodun verilerini oku
                hisseler = []
                toplam_verisi = ["TOPLAM", "100%", "", "", "", "", "", ""]

                # Header satırını atla (i+1)
                # Veri satırları (i+2'den TOPLAM'a kadar)
                j = i + 2
                while j < len(vals):
                    if vals[j][0] == "TOPLAM":
                        # TOPLAM satırındaki değerleri sakla
                        if j < len(uvals):
                            toplam_verisi = list(uvals[j]) + [""] * (8 - len(uvals[j]))
                        break
                    # Hisse satırı
                    if vals[j][0].strip():
                        hisse_data = list(uvals[j]) if j < len(uvals) else list(vals[j])
                        # 8 sütuna tamamla
                        while len(hisse_data) < 8:
                            hisse_data.append("")
                        hisseler.append(hisse_data[:8])
                    j += 1

                mevcut_periyotlar[p] = {
                    "hisseler": hisseler,
                    "toplam": toplam_verisi,
                }
                break
        i += 1

    print("  Mevcut periyotlar: {}".format(sorted(mevcut_periyotlar.keys())))
    for p, data in sorted(mevcut_periyotlar.items()):
        print("    {}P: {} hisse".format(p, len(data["hisseler"])))

    # ── 2) Yeni yapıyı oluştur ──
    # Toplam satır sayısı: 4 header + 26 * 11 = 290
    yeni_satirlar = []

    for p in range(1, PERIYOT_SAYISI + 1):
        # Başlık satırı
        yeni_satirlar.append(
            ["\U0001f4c5 {}. Periyot".format(p), "", "", "", "", "", "", ""]
        )
        # Header satırı
        yeni_satirlar.append(
            ["Hisse", "Agirlik %", "TL", "P.Basi Fiyat", "P.Sonu Fiyat", "Getiri %", "Katki %", ""]
        )

        # 7 veri satırı
        mevcut = mevcut_periyotlar.get(p, {"hisseler": [], "toplam": None})
        for v in range(VERI_SATIR):
            if v < len(mevcut["hisseler"]):
                row_data = mevcut["hisseler"][v]
                # B sütununu temizle (formül sonra yazılacak)
                row_data[1] = ""
                # F ve G sütunlarını temizle (formül sonra yazılacak)
                row_data[5] = ""
                row_data[6] = ""
                yeni_satirlar.append(row_data)
            else:
                yeni_satirlar.append(["", "", "", "", "", "", "", ""])

        # TOPLAM satırı
        toplam_row = ["TOPLAM", "100%", "", "", "", "", "", ""]
        if mevcut["toplam"]:
            # C sütununu (TL toplam) koru
            toplam_row[2] = mevcut["toplam"][2] if len(mevcut["toplam"]) > 2 else ""
        yeni_satirlar.append(toplam_row)

        # Boş satır
        yeni_satirlar.append(["", "", "", "", "", "", "", ""])

    # ── 3) Sayfayı güncelle ──
    # Önce yeterli satır olduğundan emin ol
    gereken = HEADER_SATIRLARI + len(yeni_satirlar)
    mevcut_satir = len(vals)

    if mevcut_satir < gereken:
        # Eksik satırları ekle
        eksik = gereken - mevcut_satir
        ws.add_rows(eksik)
        time.sleep(1)

    # Satır 5'ten itibaren yaz (A5:H290)
    baslangic = HEADER_SATIRLARI + 1  # 1-indexed = 5
    bitis = baslangic + len(yeni_satirlar) - 1
    cell_range = "A{}:H{}".format(baslangic, bitis)
    ws.update(values=yeni_satirlar, range_name=cell_range, value_input_option="RAW")
    time.sleep(1)

    # Fazla satırları temizle (eski veriden kalan)
    if mevcut_satir > gereken:
        temiz = []
        for r in range(gereken + 1, mevcut_satir + 1):
            for c in range(1, 9):
                temiz.append(gspread.Cell(r, c, ""))
        if temiz:
            ws.update_cells(temiz)
            time.sleep(1)

    # ── 4) Formülleri yaz ──
    formul_updates = []

    for p in range(1, PERIYOT_SAYISI + 1):
        # Blok başlangıç satırı (1-indexed)
        blok_bas = HEADER_SATIRLARI + 1 + (p - 1) * SATIR_PER_BLOK
        # Veri satırları: blok_bas+2 ... blok_bas+8 (7 satır)
        ilk_veri = blok_bas + 2
        son_veri = blok_bas + 8
        toplam_satir_1 = blok_bas + 9  # TOPLAM

        mevcut = mevcut_periyotlar.get(p, {"hisseler": []})
        hisse_sayisi = len(mevcut["hisseler"])

        if hisse_sayisi > 0:
            # B sütunu: Ağırlık formülleri
            for v in range(hisse_sayisi):
                row_1 = ilk_veri + v
                formul_updates.append({
                    "range": "B{}".format(row_1),
                    "values": [['=IFERROR(ROUND(C{}/C{}*100;1)&"%";"")'.format(row_1, toplam_satir_1)]]
                })

            # F sütunu: Getiri formülleri
            for v in range(hisse_sayisi):
                row_1 = ilk_veri + v
                # NAKİT kontrolü
                formul_updates.append({
                    "range": "F{}".format(row_1),
                    "values": [['=IFERROR(ROUND((E{n}-D{n})/D{n}*100;2);"")'.format(n=row_1)]]
                })

            # G sütunu: Katkı formülleri
            for v in range(hisse_sayisi):
                row_1 = ilk_veri + v
                formul_updates.append({
                    "range": "G{}".format(row_1),
                    "values": [['=IFERROR(ROUND(F{n}*C{n}/C{t};2);"")'.format(n=row_1, t=toplam_satir_1)]]
                })

            # C TOPLAM: SUM
            formul_updates.append({
                "range": "C{}".format(toplam_satir_1),
                "values": [["=SUM(C{}:C{})".format(ilk_veri, ilk_veri + hisse_sayisi - 1)]]
            })

            # F TOPLAM: =SUM(G veri satırları)
            formul_updates.append({
                "range": "F{}".format(toplam_satir_1),
                "values": [["=SUM(G{}:G{})".format(ilk_veri, ilk_veri + hisse_sayisi - 1)]]
            })
            # G TOPLAM
            formul_updates.append({
                "range": "G{}".format(toplam_satir_1),
                "values": [["=SUM(G{}:G{})".format(ilk_veri, ilk_veri + hisse_sayisi - 1)]]
            })

    if formul_updates:
        # Batch update max 60000 cells, split if needed
        batch_size = 100
        for start in range(0, len(formul_updates), batch_size):
            batch = formul_updates[start:start + batch_size]
            ws.batch_update(batch, value_input_option="USER_ENTERED")
            time.sleep(1)

    # ── 5) Format: Calibri 11pt siyah tüm periyot alanı ──
    sheet_id = ws.id
    ss.batch_update({"requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": HEADER_SATIRLARI,
                    "endRowIndex": gereken,
                    "startColumnIndex": 0,
                    "endColumnIndex": 8
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {
                            "fontFamily": "Calibri",
                            "fontSize": 11,
                            "foregroundColorStyle": {
                                "rgbColor": {"red": 0, "green": 0, "blue": 0}
                            }
                        }
                    }
                },
                "fields": "userEnteredFormat.textFormat(fontFamily,fontSize,foregroundColorStyle)"
            }
        },
        # D,E number format tüm periyotlar
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": HEADER_SATIRLARI,
                    "endRowIndex": gereken,
                    "startColumnIndex": 3,
                    "endColumnIndex": 5
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }
                },
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        # F,G number format
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": HEADER_SATIRLARI,
                    "endRowIndex": gereken,
                    "startColumnIndex": 5,
                    "endColumnIndex": 7
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}
                    }
                },
                "fields": "userEnteredFormat.numberFormat"
            }
        },
    ]})

    print("  -> 26 periyot yazildi ({} satir), {} periyotta veri var".format(
        len(yeni_satirlar), len(mevcut_periyotlar)))
    time.sleep(3)

print("\n" + "=" * 50)
print("  TAMAMLANDI - 11 yarismaci x 26 periyot")
print("=" * 50)

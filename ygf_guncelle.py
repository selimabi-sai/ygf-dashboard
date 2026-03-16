# -*- coding: utf-8 -*-
"""
YGF Günlük Güncelleme Scripti
Her akşam çalıştırılır. Periyot bazlı getiri hesaplar, Google Sheets'i günceller.
"""

import sys, io, os, json, glob, logging, argparse
from datetime import datetime, timedelta
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ── Windows encoding fix ──
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ── Sabitler ──
YARISMA_BASLANGIC = datetime(2026, 1, 2)
PERIYOT_GUN = 14
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
VERILER_KLASOR = r"C:\Users\PDS\Desktop\is api\veriler"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DOSYA = os.path.join(SCRIPT_DIR, "ygf_guncelle.log")
AYAR_DOSYA = os.path.join(SCRIPT_DIR, "ygf_ayarlar.json")


# ── Logging ──
def setup_logging():
    logger = logging.getLogger("ygf")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_DOSYA, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


log = setup_logging()


# ── Yardımcı fonksiyonlar ──
def tr_format(val, suffix="%"):
    """Float değeri Türkçe formata çevir: 12.34 → '12,34%'"""
    s = "{:.2f}".format(val).replace(".", ",")
    return s + suffix


def parse_tr_float(s):
    """Türkçe formatı float'a çevir: '12,34%' → 12.34"""
    if not s or s.strip() == "":
        return None
    s = s.strip().replace("%", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def aktif_periyot(bugun=None):
    """Bugünün tarihine göre aktif periyodu hesapla."""
    if bugun is None:
        bugun = datetime.now()
    for p in range(1, 27):
        basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (p - 1))
        sonu = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * p)
        if basi <= bugun < sonu:
            return p, basi, sonu
    # Son periyot (26P) — 2026 sonuna kadar
    basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * 25)
    sonu = datetime(2026, 12, 31)
    return 26, basi, sonu


def en_yakin_tarih(tarihler, hedef):
    """Tarih listesinden hedefe en yakın olanı bul (hedef veya öncesini tercih et)."""
    oncekiler = [t for t in tarihler if t <= hedef]
    if oncekiler:
        return max(oncekiler)
    return min(tarihler, key=lambda t: abs((t - hedef).days))


def icmal_guncelle(ss, yarismacilar, ws_dict, periyot_no):
    """Hisse İcmal sayfasını güncelle."""
    import time as _t

    periyotlar = list(range(periyot_no, max(periyot_no - 2, 0), -1))  # aktif + önceki
    icmal = {}

    for p in periyotlar:
        p_key = "{}P".format(p)
        icmal[p_key] = {}
        periyot_baslik = "{}. Periyot".format(p)

        for isim in yarismacilar:
            target_ws = None
            for title, ws_obj in ws_dict.items():
                if isim in title or title in isim:
                    target_ws = ws_obj
                    break
            if target_ws is None:
                continue

            vals = target_ws.get_all_values()
            blok_start = None
            blok_toplam = None
            for i, row in enumerate(vals):
                if periyot_baslik in str(row[0]):
                    blok_start = i
                if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                    blok_toplam = i
                    break
            if blok_start is None or blok_toplam is None:
                continue

            for r in range(blok_start + 2, blok_toplam):
                hisse = vals[r][0].strip() if vals[r][0] else ""
                if not hisse:
                    continue
                try:
                    tutar = float(str(vals[r][2]).replace(",", ".").replace(" ", ""))
                except (ValueError, IndexError):
                    tutar = 0
                if hisse not in icmal[p_key]:
                    icmal[p_key][hisse] = {"tutar": 0, "kisi": 0}
                icmal[p_key][hisse]["tutar"] += tutar
                icmal[p_key][hisse]["kisi"] += 1
            _t.sleep(0.3)

    # Sayfayı bul veya oluştur
    try:
        ws_icmal = ss.worksheet("Hisse İcmal")
    except Exception:
        ws_icmal = ss.add_worksheet(title="Hisse İcmal", rows=100, cols=20)
    ws_icmal.clear()
    try:
        ss.batch_update({"requests": [{"unmergeCells": {
            "range": {"sheetId": ws_icmal.id, "startRowIndex": 0, "endRowIndex": 100,
                      "startColumnIndex": 0, "endColumnIndex": 20}}}]})
    except Exception:
        pass
    _t.sleep(1)

    sorted_periyots = sorted(icmal.keys(), key=lambda x: int(x.replace("P", "")), reverse=True)
    if not sorted_periyots:
        return

    max_hisse = max(len(icmal[p]) for p in sorted_periyots)
    total_cols = len(sorted_periyots) * 4

    all_data = [["HİSSE İCMAL"] + [""] * (total_cols - 1)]
    all_data.append([""] * total_cols)

    row3 = []
    for p_key in sorted_periyots:
        row3.extend(["{}. Periyot".format(p_key.replace("P", "")), "", "", ""])
    all_data.append(row3)

    row4 = []
    for _ in sorted_periyots:
        row4.extend(["Hisse", "Toplam TL", "Kişi", "% Pay"])
    all_data.append(row4)

    periyot_toplam = {}
    for p_key in sorted_periyots:
        periyot_toplam[p_key] = sum(d["tutar"] for d in icmal[p_key].values())

    for row_idx in range(max_hisse + 1):
        row = []
        for p_key in sorted_periyots:
            data = icmal[p_key]
            sorted_items = sorted(data.items(), key=lambda x: x[1]["tutar"], reverse=True)
            p_toplam = periyot_toplam[p_key]
            if row_idx < len(sorted_items):
                hisse, info = sorted_items[row_idx]
                pay = round(info["tutar"] / p_toplam * 100, 1) if p_toplam > 0 else 0
                row.extend([hisse, round(info["tutar"], 2), info["kisi"], pay])
            elif row_idx == len(sorted_items):
                row.extend(["TOPLAM", round(p_toplam, 2), 11, 100])
            else:
                row.extend(["", "", "", ""])
        all_data.append(row)

    end_col = chr(64 + total_cols)
    ws_icmal.update(values=all_data, range_name="A1:{}{}".format(end_col, len(all_data)),
                    value_input_option="RAW")
    _t.sleep(1)

    # Formatlama
    icmal_id = ws_icmal.id
    lacivert = {"red": 0.122, "green": 0.306, "blue": 0.475}
    beyaz = {"rgbColor": {"red": 1, "green": 1, "blue": 1}}
    fmt = []
    fmt.append({"mergeCells": {"range": {"sheetId": icmal_id, "startRowIndex": 0, "endRowIndex": 1,
        "startColumnIndex": 0, "endColumnIndex": total_cols}, "mergeType": "MERGE_ALL"}})
    fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 0, "endRowIndex": 1,
        "startColumnIndex": 0, "endColumnIndex": total_cols},
        "cell": {"userEnteredFormat": {"backgroundColor": lacivert,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 14, "bold": True,
                "foregroundColorStyle": beyaz}, "horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}})
    for pi in range(len(sorted_periyots)):
        cs = pi * 4
        fmt.append({"mergeCells": {"range": {"sheetId": icmal_id, "startRowIndex": 2, "endRowIndex": 3,
            "startColumnIndex": cs, "endColumnIndex": cs + 4}, "mergeType": "MERGE_ALL"}})
    fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 2, "endRowIndex": 4,
        "startColumnIndex": 0, "endColumnIndex": total_cols},
        "cell": {"userEnteredFormat": {"backgroundColor": lacivert,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True,
                "foregroundColorStyle": beyaz}, "horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}})
    fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 4,
        "endRowIndex": len(all_data), "startColumnIndex": 0, "endColumnIndex": total_cols},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 11}}},
        "fields": "userEnteredFormat.textFormat"}})
    for pi in range(len(sorted_periyots)):
        tl_col = pi * 4 + 1
        fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 4,
            "endRowIndex": len(all_data), "startColumnIndex": tl_col, "endColumnIndex": tl_col + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"},
                "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})
        kisi_col = pi * 4 + 2
        fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 4,
            "endRowIndex": len(all_data), "startColumnIndex": kisi_col, "endColumnIndex": kisi_col + 1},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat.horizontalAlignment"}})
        pay_col = pi * 4 + 3
        fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": 4,
            "endRowIndex": len(all_data), "startColumnIndex": pay_col, "endColumnIndex": pay_col + 1},
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "0.0"},
                "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}})
        for offset, width in [(0, 75), (1, 75), (2, 45), (3, 55)]:
            fmt.append({"updateDimensionProperties": {"range": {"sheetId": icmal_id,
                "dimension": "COLUMNS", "startIndex": pi*4+offset, "endIndex": pi*4+offset+1},
                "properties": {"pixelSize": width}, "fields": "pixelSize"}})
    toplam_row = 4 + max_hisse
    fmt.append({"repeatCell": {"range": {"sheetId": icmal_id, "startRowIndex": toplam_row,
        "endRowIndex": toplam_row + 1, "startColumnIndex": 0, "endColumnIndex": total_cols},
        "cell": {"userEnteredFormat": {"textFormat": {"bold": True},
            "borders": {"top": {"style": "SOLID_MEDIUM"}}}},
        "fields": "userEnteredFormat(textFormat.bold,borders.top)"}})
    fmt.append({"updateSheetProperties": {"properties": {"sheetId": icmal_id,
        "tabColorStyle": {"rgbColor": {"red": 0.231, "green": 0.510, "blue": 0.965}}},
        "fields": "tabColorStyle"}})
    ss.batch_update({"requests": fmt})

    return len(sorted_periyots), sum(len(icmal[p]) for p in sorted_periyots)


# ══════════════════════════════════════════════════════════════
#  ANA SCRIPT
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="YGF Günlük Güncelleme")
    parser.add_argument("--kuru-calistir", action="store_true",
                        help="Sheets'e yazmadan test et")
    parser.add_argument("--cuma-guncelle", action="store_true",
                        help="Cuma guncellemesini zorla (biten periyot basi PD yaz)")
    parser.add_argument("--periyot", type=int, default=0,
                        help="Periyot numarasini override et (test icin)")
    parser.add_argument("--whatsapp", action="store_true",
                        help="WhatsApp'a sonuc mesaji gonder")
    parser.add_argument("--pazar-guncelle", action="store_true",
                        help="Pazar guncelleme: yeni periyot baslangic degerlerini kaydet")
    args = parser.parse_args()
    kuru = args.kuru_calistir

    bugun = datetime.now()
    bugun_str = bugun.strftime("%Y-%m-%d")
    bugun_tr = bugun.strftime("%d.%m.%Y %H:%M")

    print("\n" + "=" * 55)
    print("  YGF GUNCELLEME -- {}".format(bugun_tr))
    if kuru:
        print("  [KURU CALISTIRMA - Sheets'e yazilmayacak]")
    print("=" * 55)

    # ── 1) Ayarları oku ──
    with open(AYAR_DOSYA, "r", encoding="utf-8") as f:
        ayarlar = json.load(f)
    creds_path = ayarlar["credentials_json"]
    sheet_id = ayarlar["google_sheet_id"]
    yarismacilar = ayarlar["yarismacilar"]
    log.info("Ayarlar yuklendi. %d yarismacilar.", len(yarismacilar))

    # ── 2) Aktif periyot ──
    if args.periyot > 0:
        periyot_no = args.periyot
        p_basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (periyot_no - 1))
        p_sonu = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * periyot_no)
        print("  [OVERRIDE] Periyot: {}P".format(periyot_no))
    else:
        periyot_no, p_basi, p_sonu = aktif_periyot(bugun)
    p_basi_str = p_basi.strftime("%d.%m")
    p_sonu_str = p_sonu.strftime("%d.%m")
    gun_no = (bugun - p_basi).days + 1

    print("  Aktif Periyot: {}P ({} -> {}) Gun {}/{}".format(
        periyot_no, p_basi_str, p_sonu_str, gun_no, PERIYOT_GUN))
    log.info("Aktif periyot: %dP (%s -> %s)", periyot_no, p_basi_str, p_sonu_str)

    # ── 3) bisttum_pd.xlsx oku (periyot başı PD) ──
    bisttum_yol = os.path.join(VERILER_KLASOR, "bisttum_pd.xlsx")
    if not os.path.exists(bisttum_yol):
        print("\n  [HATA] bisttum_pd.xlsx bulunamadi: {}".format(bisttum_yol))
        log.error("bisttum_pd.xlsx bulunamadi!")
        return

    df_pd = pd.read_excel(bisttum_yol, sheet_name="PD", index_col=0)
    # Sütun başlıklarını datetime'a çevir
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

    # Periyot başlangıç tarihine en yakın sütunu bul
    tarih_listesi = [c for c in df_pd.columns if isinstance(c, (datetime, pd.Timestamp))]
    basi_tarih = en_yakin_tarih(tarih_listesi, p_basi)
    print("  Periyot basi PD tarihi: {} (hedef: {})".format(
        basi_tarih.strftime("%Y-%m-%d"), p_basi.strftime("%Y-%m-%d")))
    log.info("Periyot basi PD tarihi: %s", basi_tarih.strftime("%Y-%m-%d"))

    # ── 4) snap_bugun_pd oku (bugünün PD'si) ──
    snap_dosya = os.path.join(VERILER_KLASOR, "snap_bugun_pd_{}.xlsx".format(bugun_str))
    if not os.path.exists(snap_dosya):
        # En yeni snap dosyasını bul
        snap_files = sorted(glob.glob(os.path.join(VERILER_KLASOR, "snap_bugun_pd_*.xlsx")))
        if not snap_files:
            print("\n  [HATA] Hicbir snap_bugun_pd dosyasi bulunamadi!")
            log.error("snap_bugun_pd dosyasi bulunamadi!")
            return
        snap_dosya = snap_files[-1]
        snap_tarih = os.path.basename(snap_dosya).replace("snap_bugun_pd_", "").replace(".xlsx", "")
        print("  [UYARI] Bugunun snap dosyasi yok, en yenisi kullaniliyor: {}".format(snap_tarih))
    else:
        snap_tarih = bugun_str

    df_bugun = pd.read_excel(snap_dosya, sheet_name="PD", index_col=0)
    # Tek sütun — ilk sütunu al
    bugun_col = df_bugun.columns[0]
    print("  Gunluk PD dosyasi: snap_bugun_pd_{}.xlsx".format(snap_tarih))
    log.info("Snap dosyasi: %s", snap_tarih)

    # ── 5) Google Sheets bağlan ──
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(sheet_id)

    ws_ana = ss.worksheet("Ana Sayfa")
    ana_vals = ws_ana.get_all_values()
    ana_header = ana_vals[4]  # Satır 5 (0-indexed 4)

    # Periyot sütun haritası: {periyot_no: col_idx_0based}
    periyot_map = {}
    for i, h in enumerate(ana_header):
        if h.endswith("P") and h[:-1].isdigit():
            periyot_map[int(h[:-1])] = i
    print("  Periyot haritasi: {}".format(
        {k: chr(65 + v) for k, v in sorted(periyot_map.items())}))

    # Yarışmacı worksheet'lerini hazırla
    ws_dict = {}
    for ws in ss.worksheets():
        ws_dict[ws.title] = ws

    print("\n" + "-" * 55)

    # ── 6) Periyot sütununu Ana Sayfa'da bul ──
    periyot_label = "{}P".format(periyot_no)
    periyot_col_idx = periyot_map.get(periyot_no)  # 0-based, None if not found

    if periyot_col_idx is not None:
        periyot_col_no = periyot_col_idx + 1  # 1-indexed
        print("  Periyot sutunu: {} = sutun {} (1-indexed: {})".format(
            periyot_label, periyot_col_idx, periyot_col_no))
    else:
        periyot_col_no = None
        print("  [BILGI] {} sutunu henuz yok (cuma guncellemede eklenecek)".format(periyot_label))

    # ── 7) Her yarışmacı için getiri hesapla ──
    sonuclar = []  # [(isim, periyot_getiri, portfoy_degeri, hisse_detay)]

    for isim in yarismacilar:
        # Yarışmacının worksheet'ini bul
        target_ws = None
        for title, ws_obj in ws_dict.items():
            if isim in title or title in isim:
                target_ws = ws_obj
                break

        if target_ws is None:
            print("  [UYARI] '{}' icin worksheet bulunamadi, atlaniyor.".format(isim))
            log.warning("Worksheet bulunamadi: %s", isim)
            # Geçmiş portföy değerini Ana Sayfa'dan hesapla
            ana_row_idx = None
            for i, row in enumerate(ana_vals):
                if len(row) > 1 and isim in row[1]:
                    ana_row_idx = i
                    break
            gecmis_portfoy = 100.0
            if ana_row_idx is not None:
                for p in range(1, periyot_no):
                    col = periyot_map.get(p)
                    if col is not None and col < len(ana_vals[ana_row_idx]):
                        val = parse_tr_float(ana_vals[ana_row_idx][col])
                        if val is not None:
                            gecmis_portfoy *= (1 + val / 100)
            sonuclar.append((isim, 0.0, gecmis_portfoy, []))
            continue

        # Yarışmacının sayfasını oku
        y_vals = target_ws.get_all_values()

        # Aktif periyot bloğunu bul
        periyot_baslik = "{}. Periyot".format(periyot_no)
        blok_start = None
        blok_toplam = None

        for i, row in enumerate(y_vals):
            if periyot_baslik in str(row[0]):
                blok_start = i  # 0-based
            if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                blok_toplam = i
                break

        if blok_start is None:
            print("  [UYARI] '{}' sayfasinda '{}' bulunamadi.".format(isim, periyot_baslik))
            log.warning("%s: periyot blogu bulunamadi", isim)
            # Geçmiş periyotlardan portföy değerini hesapla
            ana_row_idx = None
            for i, row in enumerate(ana_vals):
                if len(row) > 1 and isim in row[1]:
                    ana_row_idx = i
                    break
            gecmis_portfoy = 100.0
            if ana_row_idx is not None:
                for p in range(1, periyot_no):
                    col = periyot_map.get(p)
                    if col is not None and col < len(ana_vals[ana_row_idx]):
                        val = parse_tr_float(ana_vals[ana_row_idx][col])
                        if val is not None:
                            gecmis_portfoy *= (1 + val / 100)
            sonuclar.append((isim, 0.0, gecmis_portfoy, []))
            continue

        # Header satırı: blok_start + 1, veri satırları: blok_start + 2 ... blok_toplam - 1
        data_start = blok_start + 2  # 0-based
        data_end = blok_toplam        # 0-based (exclusive)

        # Hisseleri ve ağırlıkları oku
        hisse_detay = []
        for r in range(data_start, data_end):
            row = y_vals[r]
            hisse = row[0].strip() if row[0] else ""
            agirlik_str = row[1].strip() if len(row) > 1 and row[1] else ""

            if not hisse:
                continue

            agirlik = parse_tr_float(agirlik_str)
            if agirlik is None:
                agirlik = 0.0

            # NAKİT özel durumu — 14 günlük net faiz getirisi
            if hisse.upper() in ("NAKİT", "NAKIT"):
                nakit_getiri = ((1 + 0.428 * (1 - 0.175) / 365) ** 14 - 1) * 100
                nakit_katki = nakit_getiri * (agirlik / 100)
                hisse_detay.append({
                    "hisse": hisse,
                    "agirlik": agirlik,
                    "basi_pd": 0,
                    "sonu_pd": 0,
                    "getiri": nakit_getiri,
                    "katki": nakit_katki,
                    "row": r,
                })
                continue

            # Periyot başı PD
            if hisse in df_pd.index:
                basi_pd = df_pd.loc[hisse, basi_tarih]
            else:
                print("  [UYARI] '{}' bisttum_pd'de bulunamadi.".format(hisse))
                log.warning("%s: %s hissesi bisttum_pd'de yok", isim, hisse)
                hisse_detay.append({
                    "hisse": hisse, "agirlik": agirlik,
                    "basi_pd": 0, "sonu_pd": 0,
                    "getiri": 0.0, "katki": 0.0, "row": r,
                })
                continue

            # Bugünün PD'si
            if hisse in df_bugun.index:
                sonu_pd = df_bugun.loc[hisse, bugun_col]
            else:
                print("  [UYARI] '{}' snap_bugun_pd'de bulunamadi.".format(hisse))
                log.warning("%s: %s hissesi snap_bugun'de yok", isim, hisse)
                hisse_detay.append({
                    "hisse": hisse, "agirlik": agirlik,
                    "basi_pd": basi_pd, "sonu_pd": 0,
                    "getiri": 0.0, "katki": 0.0, "row": r,
                })
                continue

            # Getiri hesapla
            if basi_pd and basi_pd != 0:
                getiri = (sonu_pd - basi_pd) / basi_pd * 100
            else:
                getiri = 0.0
            katki = getiri * (agirlik / 100)

            hisse_detay.append({
                "hisse": hisse,
                "agirlik": agirlik,
                "basi_pd": basi_pd,
                "sonu_pd": sonu_pd,
                "getiri": getiri,
                "katki": katki,
                "row": r,
            })

        # Portföy toplam getiri (bu periyot)
        periyot_getiri = sum(h["katki"] for h in hisse_detay)

        # Kümülatif portföy değeri hesapla
        # Ana Sayfa'dan geçmiş periyot getirilerini oku
        ana_row = None
        for i, row in enumerate(ana_vals):
            if len(row) > 1 and isim in row[1]:
                ana_row = i
                break

        portfoy_degeri = 100.0
        if ana_row is not None:
            # Geçmiş periyotların getirilerini oku (1P'den aktif-1'e kadar)
            for p in range(1, periyot_no):
                col = periyot_map.get(p)
                if col is not None and col < len(ana_vals[ana_row]):
                    val = parse_tr_float(ana_vals[ana_row][col])
                    if val is not None:
                        portfoy_degeri *= (1 + val / 100)

        # Bu periyodun getirisini de ekle
        portfoy_degeri *= (1 + periyot_getiri / 100)
        toplam_getiri = portfoy_degeri - 100

        sonuclar.append((isim, periyot_getiri, portfoy_degeri, hisse_detay))
        log.info("%s: %dP getiri=%.2f%%, portfoy=%.2f", isim, periyot_no, periyot_getiri, portfoy_degeri)

    # ── 8) Sonuçları sırala (portföy değerine göre) ──
    sonuclar.sort(key=lambda x: x[2], reverse=True)

    print("\n" + "-" * 55)
    for sira, (isim, p_getiri, portfoy, _) in enumerate(sonuclar):
        if sira == 0:
            medal = "  1."
        elif sira == 1:
            medal = "  2."
        elif sira == 2:
            medal = "  3."
        else:
            medal = "  {}.".format(sira + 1)

        print("{}  {:<12s}  {}P: {:>7s}   (Portfoy: {:>7s})".format(
            medal, isim, periyot_no,
            tr_format(p_getiri), tr_format(portfoy, "")))
    print("-" * 55)

    # ── 9) Google Sheets güncelle ──
    import time

    if not kuru:
        # 9a) Ana Sayfa güncelleme
        print("\n  Ana Sayfa guncelleniyor...")
        ana_cells = []

        for isim, p_getiri, portfoy, _ in sonuclar:
            ana_row = None
            for i, row in enumerate(ana_vals):
                if len(row) > 1 and isim in row[1]:
                    ana_row = i + 1
                    break
            if ana_row is None:
                print("    [UYARI] '{}' Ana Sayfa'da bulunamadi.".format(isim))
                continue

            # C sütunu (portfoy) artık 9c'de H TOPLAM'dan yazılıyor
            if periyot_col_no is not None:
                ana_cells.append(gspread.Cell(ana_row, periyot_col_no, tr_format(p_getiri)))

        if ana_cells:
            ws_ana.update_cells(ana_cells)

        ws_ana.update_cell(2, 4, bugun.strftime("%d.%m.%Y"))
        ws_ana.update_cell(2, 6, "{}. Periyot".format(periyot_no))
        gun_sayisi = (bugun - YARISMA_BASLANGIC).days
        ws_ana.update_cell(2, 8, str(gun_sayisi))

        print("    Ana Sayfa {} yarismacilar guncellendi.".format(len(sonuclar)))
        log.info("Ana Sayfa guncellendi: %d yarismacilar", len(sonuclar))

        # 9b) Yarışmacı sayfaları güncelleme
        print("  Yarismacilar sayfalari guncelleniyor...")
        for isim, p_getiri, portfoy, hisse_detay in sonuclar:
            if not hisse_detay:
                continue

            target_ws = None
            for title, ws_obj in ws_dict.items():
                if isim in title or title in isim:
                    target_ws = ws_obj
                    break
            if target_ws is None:
                continue

            cells = []
            formul_updates = []
            for h in hisse_detay:
                row_1idx = h["row"] + 1
                if h["basi_pd"] and not pd.isna(h["basi_pd"]):
                    cells.append(gspread.Cell(row_1idx, 4, round(h["basi_pd"], 2)))
                if h["sonu_pd"] and not pd.isna(h["sonu_pd"]):
                    cells.append(gspread.Cell(row_1idx, 5, round(h["sonu_pd"], 2)))
                # NAKİT: F sütununa faiz formülü, diğerleri: getiri değeri
                if h["hisse"].upper() in ("NAKİT", "NAKIT"):
                    formul_updates.append({
                        "range": "F{}".format(row_1idx),
                        "values": [['=ROUND(((1+0,428*(1-0,175)/365)^14-1)*100;2)']]
                    })
                elif h["getiri"] is not None and not pd.isna(h["getiri"]):
                    formul_updates.append({
                        "range": "F{}".format(row_1idx),
                        "values": [[round(h["getiri"], 2)]]
                    })

            y_vals = target_ws.get_all_values()
            periyot_baslik = "{}. Periyot".format(periyot_no)
            toplam_row = None
            found_block = False
            for i, row in enumerate(y_vals):
                if periyot_baslik in str(row[0]):
                    found_block = True
                if found_block and row[0] == "TOPLAM":
                    toplam_row = i + 1
                    break

            if toplam_row and p_getiri is not None and not pd.isna(p_getiri):
                formul_updates.append({
                    "range": "F{}".format(toplam_row),
                    "values": [[round(p_getiri, 2)]]
                })

            if cells:
                target_ws.update_cells(cells)
            if formul_updates:
                target_ws.batch_update(formul_updates, value_input_option="USER_ENTERED")
            time.sleep(1)

        print("    {} yarismacilar sayfalari guncellendi.".format(len(sonuclar)))
        log.info("Yarismacilar sayfalari guncellendi.")

        # 9c) Siralama + benchmark ayirma
        print("  Siralama guncelleniyor...")
        ana_vals = ws_ana.get_all_values()
        benchmarks_set = {"Faiz", "BIST 100", "USDTRY"}
        data_rows = []
        bench_rows = {}

        for idx in range(5, min(20, len(ana_vals))):
            row = ana_vals[idx]
            if not row or not row[1].strip():
                continue
            padded = list(row[:13]) + [''] * max(0, 13 - len(row[:13]))
            isim = padded[1].strip()
            if isim in benchmarks_set:
                bench_rows[isim] = padded
                continue
            if not isim:
                continue
            try:
                pv = float(str(padded[2]).replace(',', '.'))
            except (ValueError, IndexError):
                pv = 0.0
            data_rows.append({'isim': isim, 'portfoy': pv, 'data': padded})

        data_rows.sort(key=lambda x: x['portfoy'], reverse=True)

        # Satir 6-20 tamamen temizle
        bos = [[''] * 13 for _ in range(15)]
        ws_ana.update(values=bos, range_name="A6:M20", value_input_option="RAW")
        time.sleep(1)

        # Yarismacilar (satir 6-16)
        write_rows = []
        for si, r in enumerate(data_rows[:11]):
            row = list(r["data"])
            row[0] = si + 1
            row[2] = ''
            row[7] = ''
            row[8] = ''
            write_rows.append(row)
        while len(write_rows) < 11:
            write_rows.append([''] * 13)
        ws_ana.update(values=write_rows, range_name="A6:M16", value_input_option="USER_ENTERED")
        time.sleep(1)

        # Benchmark (satir 18-20: BIST100, USDTRY, Faiz)
        bench_order = ["BIST 100", "USDTRY", "Faiz"]
        bench_write = []
        for bname in bench_order:
            if bname in bench_rows:
                brow = list(bench_rows[bname])
                brow[0] = "\u2014"
                brow[2] = ''
                brow[7] = ''
                bench_write.append(brow)
            else:
                bench_write.append(["\u2014", bname] + [''] * 11)
        ws_ana.update(values=bench_write, range_name="A18:M20", value_input_option="USER_ENTERED")
        time.sleep(1)

        # Formuller: C (portfoy), H (6P), I (5P) - dinamik TOPLAM satiri
        formula_batch = []
        aktif_baslik = "{}. Periyot".format(periyot_no)
        onceki_baslik = "{}. Periyot".format(periyot_no - 1) if periyot_no > 1 else None

        for si, dr in enumerate(data_rows[:11]):
            row_num = 6 + si
            isim_r = dr["isim"]
            sayfa_adi = isim_r
            for title in ws_dict:
                if isim_r in title or title in isim_r:
                    sayfa_adi = title
                    break

            try:
                y_ws = ws_dict.get(sayfa_adi)
                if y_ws is None:
                    continue
                y_vals = y_ws.get_all_values()
                toplam_h = None
                toplam_f = None
                onceki_f = None
                found_a = False
                found_o = False

                for yi, yrow in enumerate(y_vals):
                    if aktif_baslik in str(yrow[0]):
                        found_a = True
                        found_o = False
                    if onceki_baslik and onceki_baslik in str(yrow[0]):
                        found_o = True
                        found_a = False
                    if found_a and yrow[0] == "TOPLAM":
                        toplam_h = yi + 1
                        toplam_f = yi + 1
                        found_a = False
                    if found_o and yrow[0] == "TOPLAM":
                        onceki_f = yi + 1
                        found_o = False

                if toplam_h:
                    formula_batch.append({"range": "C{}".format(row_num),
                        "values": [["='{}'!H{}".format(sayfa_adi, toplam_h)]]})
                if toplam_f:
                    formula_batch.append({"range": "H{}".format(row_num),
                        "values": [["='{}'!F{}".format(sayfa_adi, toplam_f)]]})
                if onceki_f:
                    formula_batch.append({"range": "I{}".format(row_num),
                        "values": [["='{}'!F{}".format(sayfa_adi, onceki_f)]]})
                time.sleep(0.3)
            except Exception as e:
                log.error("Formul hatasi %s: %s", isim_r, e)

        # Benchmark 6P getirileri — Kiyaslama Paneli Periyot Getirileri tablosundan oku
        try:
            for yi, yrow in enumerate(ana_vals):
                if "PER" in str(yrow).upper() and "GET" in str(yrow).upper():
                    for bi in range(yi + 2, min(yi + 6, len(ana_vals))):
                        brow = ana_vals[bi]
                        if not brow or not brow[0]:
                            continue
                        label = brow[0].strip().upper()
                        gv = ""
                        for ci in range(1, min(5, len(brow))):
                            val = str(brow[ci]).replace(",", ".").replace("%", "").strip()
                            try:
                                float(val)
                                gv = val
                            except ValueError:
                                pass
                        if "BIST" in label and gv:
                            formula_batch.append({"range": "H18", "values": [[gv]]})
                        elif "USD" in label and gv:
                            formula_batch.append({"range": "H19", "values": [[gv]]})
                        elif "FA" in label and gv:
                            formula_batch.append({"range": "H20", "values": [[gv]]})
                    break
        except Exception as e:
            log.error("Benchmark getiri hatasi: %s", e)

        # Benchmark C (Portfoy) — Kiyaslama Paneli YTD Tutar
        try:
            for yi, yrow in enumerate(ana_vals):
                if "KIYASLAMA" in str(yrow).upper() or "YTD" in str(yrow).upper():
                    for bi in range(yi + 2, min(yi + 6, len(ana_vals))):
                        brow = ana_vals[bi]
                        if not brow or not brow[0]:
                            continue
                        label = brow[0].strip().upper()
                        tv = ""
                        for ci in range(len(brow) - 1, 0, -1):
                            val = str(brow[ci]).replace(",", ".").strip()
                            try:
                                fv = float(val)
                                if fv > 50:
                                    tv = val
                                    break
                            except ValueError:
                                pass
                        if "BIST" in label and tv:
                            formula_batch.append({"range": "C18", "values": [[tv]]})
                        elif "USD" in label and tv:
                            formula_batch.append({"range": "C19", "values": [[tv]]})
                        elif "FA" in label and tv:
                            formula_batch.append({"range": "C20", "values": [[tv]]})
                    break
        except Exception as e:
            log.error("Benchmark portfoy hatasi: %s", e)

        if formula_batch:
            ws_ana.batch_update(formula_batch, value_input_option="USER_ENTERED")
            print("    {} formul/deger yazildi.".format(len(formula_batch)))
        time.sleep(1)

        # Ana Sayfa'yı yeniden oku (güncel haliyle)
        ana_vals = ws_ana.get_all_values()

        # 9d) Hisse İcmal güncelle
        print("  Hisse Icmal guncelleniyor...")
        try:
            p_count, h_count = icmal_guncelle(ss, yarismacilar, ws_dict, periyot_no)
            print("    Icmal guncellendi: {} periyot, {} hisse.".format(p_count, h_count))
            log.info("Hisse Icmal guncellendi: %d periyot, %d hisse", p_count, h_count)
        except Exception as e:
            print("    [HATA] Icmal hatasi: {}".format(e))
            log.error("Icmal hatasi: %s", e)

        print("    Sheets guncellendi!")
        log.info("Guncelleme tamamlandi.")
    else:
        print("\n  [KURU CALISTIRMA] Gunluk guncelleme yazilmadi.")

    # ══════════════════════════════════════════════════════════
    # ── 11) CUMA GÜNCELLEME BLOĞU ──
    # Biten periyodun başlangıç PD'lerini yarışmacı sayfalarına yaz
    # ══════════════════════════════════════════════════════════
    cuma_guncelle = args.cuma_guncelle or (bugun.weekday() == 4)

    if cuma_guncelle:
        # Biten periyodu hesapla
        # Bugün bir periyot bitiş tarihiyse → biten = o periyot
        # Değilse → biten = aktif - 1
        biten_periyot = None
        for p in range(1, 27):
            p_sonu_tarih = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * p)
            if bugun.date() == p_sonu_tarih.date():
                biten_periyot = p
                break

        if biten_periyot is None:
            biten_periyot = periyot_no - 1 if periyot_no > 1 else periyot_no

        if biten_periyot < 1:
            print("\n  [CUMA] Biten periyot hesaplanamadi, atlaniyor.")
        else:
            biten_basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (biten_periyot - 1))
            biten_basi_tarih = en_yakin_tarih(tarih_listesi, biten_basi)

            print("\n" + "-" * 55)
            print("  CUMA GUNCELLEME: {}P basi PD'leri".format(biten_periyot))
            print("  Periyot basi: {} -> PD tarihi: {}".format(
                biten_basi.strftime("%d.%m.%Y"), biten_basi_tarih.strftime("%Y-%m-%d")))
            print("-" * 55)

            biten_baslik = "{}. Periyot".format(biten_periyot)
            cuma_sayac = 0

            for isim in yarismacilar:
                target_ws = None
                for title, ws_obj in ws_dict.items():
                    if isim in title or title in isim:
                        target_ws = ws_obj
                        break
                if target_ws is None:
                    continue

                y_vals = target_ws.get_all_values()

                # Biten periyot bloğunu bul
                blok_start = None
                blok_toplam = None
                for i, row in enumerate(y_vals):
                    if biten_baslik in str(row[0]):
                        blok_start = i
                    if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                        blok_toplam = i
                        break

                if blok_start is None:
                    print("    {} - '{}' bulunamadi, atlaniyor.".format(isim, biten_baslik))
                    continue

                data_start = blok_start + 2
                data_end = blok_toplam

                cells = []
                hisse_sayac = 0
                for r in range(data_start, data_end):
                    row = y_vals[r]
                    hisse = row[0].strip() if row[0] else ""
                    if not hisse:
                        continue
                    if hisse.upper() in ("NAKİT", "NAKIT"):
                        continue

                    if hisse in df_pd.index:
                        pd_val = df_pd.loc[hisse, biten_basi_tarih]
                        cells.append(gspread.Cell(r + 1, 4, round(float(pd_val), 2)))
                        hisse_sayac += 1
                    else:
                        print("    [UYARI] {} - {} bisttum_pd'de yok".format(isim, hisse))

                if cells:
                    if not kuru:
                        target_ws.update_cells(cells)
                        time.sleep(1)
                    print("    {} - {} hisse P.Basi PD yazildi{}".format(
                        isim, hisse_sayac, " [KURU]" if kuru else ""))
                    cuma_sayac += 1

            print("\n  Cuma guncelleme: {}P baslangic PD'leri {} yarismacilar icin guncellendi{}".format(
                biten_periyot, cuma_sayac, " [KURU]" if kuru else ""))
            log.info("Cuma guncelleme: %dP basi PD, %d yarismaci", biten_periyot, cuma_sayac)

            # ── Yeni periyot sütunu kontrolü ──
            yeni_p_label = "{}P".format(periyot_no)
            if periyot_no not in periyot_map:
                print("\n  Yeni periyot sutunu: {} ekleniyor...".format(yeni_p_label))
                log.info("Yeni periyot sutunu ekleniyor: %s", yeni_p_label)

                # Bir yarışmacının sayfasından yeni periyot TOPLAM F satırını bul
                toplam_f_satir = None
                periyot_baslik_yeni = "{}. Periyot".format(periyot_no)
                for isim_y in yarismacilar:
                    target_ws_y = None
                    for title, ws_obj in ws_dict.items():
                        if isim_y in title or title in isim_y:
                            target_ws_y = ws_obj
                            break
                    if target_ws_y is None:
                        continue
                    y_vals_y = target_ws_y.get_all_values()
                    for i_y, row_y in enumerate(y_vals_y):
                        if periyot_baslik_yeni in str(row_y[0]):
                            for j_y in range(i_y + 1, min(i_y + 15, len(y_vals_y))):
                                if y_vals_y[j_y][0] == "TOPLAM":
                                    toplam_f_satir = j_y + 1  # 1-indexed
                                    break
                            break
                    if toplam_f_satir:
                        print("    TOPLAM satiri: F{} ({}'dan tespit edildi)".format(
                            toplam_f_satir, isim_y))
                        break
                    time.sleep(0.5)

                if toplam_f_satir is None:
                    print("    [HATA] {} TOPLAM satiri bulunamadi!".format(periyot_baslik_yeni))
                else:
                    # Ana Sayfa'yı yeniden oku
                    ana_vals = ws_ana.get_all_values()
                    ana_header = ana_vals[4]

                    # Periyot sütunlarını bul
                    periyot_cols = []
                    for i_pc, h_pc in enumerate(ana_header):
                        if h_pc.endswith("P") and h_pc[:-1].isdigit():
                            periyot_cols.append((i_pc, h_pc))

                    if not periyot_cols:
                        print("    [HATA] Periyot sutunlari bulunamadi!")
                    else:
                        ilk_col = min(c[0] for c in periyot_cols)  # H = 7
                        son_col = max(c[0] for c in periyot_cols)
                        col_letter = lambda c: chr(65 + c)
                        benchmarks_set = {'Faiz', 'BIST 100', 'USDTRY'}

                        # Yeni sütun verilerini hazırla
                        yeni_col_data = [yeni_p_label]  # Satır 5: başlık
                        formul_sayac = 0
                        for row_idx in range(5, 20):  # Satır 6-20 (0-based 5-19)
                            row_data = ana_vals[row_idx]
                            isim_cell = row_data[1] if len(row_data) > 1 else ""
                            if isim_cell in benchmarks_set or not isim_cell:
                                yeni_col_data.append("")
                            else:
                                # Yarışmacı sayfasının tam adını bul
                                sayfa_adi = isim_cell
                                for title in ws_dict:
                                    if isim_cell in title or title in isim_cell:
                                        sayfa_adi = title
                                        break
                                yeni_col_data.append("='{}'!F{}".format(sayfa_adi, toplam_f_satir))
                                formul_sayac += 1

                        if not kuru:
                            # Mevcut periyot verilerini oku (değer olarak) ve bir sağa kaydır
                            read_range = "{}5:{}19".format(col_letter(ilk_col), col_letter(son_col))
                            mevcut_data = ws_ana.get(read_range, value_render_option="FORMATTED_VALUE")

                            write_range = "{}5:{}19".format(col_letter(ilk_col + 1), col_letter(son_col + 1))
                            ws_ana.update(values=mevcut_data, range_name=write_range, value_input_option="RAW")
                            time.sleep(2)

                            # H sütununa yeni periyot başlığı ve formüller yaz
                            formul_range = "{}5:{}19".format(col_letter(ilk_col), col_letter(ilk_col))
                            ws_ana.update(
                                values=[[v] for v in yeni_col_data],
                                range_name=formul_range,
                                value_input_option="USER_ENTERED"
                            )
                            time.sleep(2)

                            # Başlık formatı (lacivert bg, beyaz bold)
                            ana_sheet_id = ws_ana.id
                            ss.batch_update({
                                "requests": [{
                                    "repeatCell": {
                                        "range": {
                                            "sheetId": ana_sheet_id,
                                            "startRowIndex": 4,
                                            "endRowIndex": 5,
                                            "startColumnIndex": ilk_col,
                                            "endColumnIndex": ilk_col + 1
                                        },
                                        "cell": {
                                            "userEnteredFormat": {
                                                "backgroundColor": {"red": 0.122, "green": 0.306, "blue": 0.475},
                                                "textFormat": {
                                                    "fontFamily": "Calibri",
                                                    "fontSize": 10,
                                                    "bold": True,
                                                    "foregroundColorStyle": {
                                                        "rgbColor": {"red": 1, "green": 1, "blue": 1}
                                                    }
                                                },
                                                "horizontalAlignment": "CENTER"
                                            }
                                        },
                                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                                    }
                                }]
                            })
                            time.sleep(1)

                            # Değişkenleri güncelle
                            periyot_map[periyot_no] = ilk_col
                            periyot_col_idx = ilk_col
                            periyot_col_no = ilk_col + 1
                            ana_vals = ws_ana.get_all_values()
                            ana_header = ana_vals[4]

                            print("    {} eklendi (sutun {})".format(yeni_p_label, col_letter(ilk_col)))
                        else:
                            print("    [KURU] {} eklenecek (sutun {})".format(
                                yeni_p_label, col_letter(ilk_col)))

                        print("    Formul: ='Isim'!F{} ({} yarismaci)".format(
                            toplam_f_satir, formul_sayac))
                        for v in yeni_col_data[1:]:
                            if v and v.startswith("="):
                                print("      {}".format(v))
                        log.info("Yeni periyot sutunu %s: F%d, %d formul",
                                 yeni_p_label, toplam_f_satir, formul_sayac)
            else:
                print("\n  {} zaten mevcut (sutun {})".format(
                    yeni_p_label, chr(65 + periyot_map[periyot_no])))

    # ══════════════════════════════════════════════════════════
    # ── 12) WHATSAPP RAPOR GÖNDERME ──
    # ══════════════════════════════════════════════════════════
    whatsapp_gonder = args.whatsapp or (bugun.weekday() == 4 and not kuru)

    # Mesaj metnini oluştur
    gun_sayisi = (bugun - YARISMA_BASLANGIC).days
    karli = sum(1 for _, _, p, _ in sonuclar if p > 100)

    # Ana Sayfa'dan BIST ve Faiz değerlerini oku
    bist_str = ""
    faiz_str = ""
    bist_yenen = 0
    bist_getiri = 0.0
    for row in ana_vals[5:20]:  # Yarismaci (6-16) + benchmark (18-20)
        if len(row) > 1 and "BIST" in row[1]:
            pv = parse_tr_float(row[2])
            if pv is not None:
                bist_getiri = pv - 100
                bist_str = tr_format(bist_getiri)
        if len(row) > 1 and "Faiz" in row[1]:
            pv = parse_tr_float(row[2])
            if pv is not None:
                faiz_str = tr_format(pv - 100)

    for _, _, portfoy, _ in sonuclar:
        if (portfoy - 100) > bist_getiri:
            bist_yenen += 1

    mesaj_satirlar = []
    mesaj_satirlar.append("\U0001f3c6 YGF \u2014 {}. Periyot Sonuclari".format(periyot_no))
    mesaj_satirlar.append("\U0001f4c5 {} | {}. Gun".format(bugun.strftime("%d.%m.%Y"), gun_sayisi))
    mesaj_satirlar.append("")
    mesaj_satirlar.append("\u2501" * 26)

    for sira, (isim, p_getiri, portfoy, _) in enumerate(sonuclar):
        toplam_g = portfoy - 100
        portfoy_str = tr_format(portfoy, "")
        getiri_str = tr_format(toplam_g)

        if sira == 0:
            prefix = "\U0001f947"
        elif sira == 1:
            prefix = "\U0001f948"
        elif sira == 2:
            prefix = "\U0001f949"
        else:
            prefix = "{:>2d}.".format(sira + 1)

        mesaj_satirlar.append("{} {:<12s} {:>8s}  ({})".format(
            prefix, isim, getiri_str, portfoy_str))

    mesaj_satirlar.append("\u2501" * 26)
    mesaj_satirlar.append("\U0001f4ca Karli: {}/{}".format(karli, len(sonuclar)))
    mesaj_satirlar.append("\U0001f4c8 BIST 100: {} | Faiz: {}".format(bist_str, faiz_str))
    mesaj_satirlar.append("\U0001f3c6 BIST'i yenen: {} kisi".format(bist_yenen))
    mesaj_satirlar.append("")
    mesaj_satirlar.append("Sai Amator Yatirim \u00a9 2026")

    mesaj = "\n".join(mesaj_satirlar)

    if kuru or not whatsapp_gonder:
        if kuru:
            print("\n" + "-" * 55)
            print("  WHATSAPP MESAJI (onizleme):")
            print("-" * 55)
            print(mesaj)
            print("-" * 55)
    else:
        print("\n  WhatsApp mesaji gonderiliyor...")
        log.info("WhatsApp mesaji gonderiliyor...")

        try:
            # whatsapp_gonder modülünü import et
            from pathlib import Path as _P
            _snap_dir = str(_P(os.environ.get("USERPROFILE", "")) / "Desktop" / "snap code")
            if _snap_dir not in sys.path:
                sys.path.append(_snap_dir)
            from whatsapp_gonder import whatsapp_gonder_tum as _wa_gonder

            # Mesajı geçici txt dosyasına yaz (modül sadece dosya gönderiyor)
            import tempfile
            mesaj_dosya = os.path.join(SCRIPT_DIR, "ygf_rapor.txt")
            with open(mesaj_dosya, "w", encoding="utf-8") as f:
                f.write(mesaj)

            _wa_gonder(dosyalar=[mesaj_dosya])
            print("    WhatsApp mesaji gonderildi!")
            log.info("WhatsApp mesaji gonderildi.")

            # Geçici dosyayı sil
            try:
                os.remove(mesaj_dosya)
            except OSError:
                pass

        except Exception as e:
            print("    [HATA] WhatsApp gonderilemedi: {}".format(e))
            log.error("WhatsApp hata: %s", e)

    # ══════════════════════════════════════════════════════════
    # ── 13) PAZAR GÜNCELLEME — Yeni periyot başlangıç değerleri ──
    # Pazar 22:00'da çalışır. Google Finance'ten Cuma kapanış
    # değerlerini alır, sonraki periyodun başlangıcı olarak kaydeder.
    # ══════════════════════════════════════════════════════════
    pazar_guncelle = args.pazar_guncelle or (bugun.weekday() == 6)  # 6 = Pazar

    if pazar_guncelle:
        print("\n" + "-" * 55)
        print("  PAZAR GUNCELLEME: Yeni periyot baslangic degerleri")
        print("-" * 55)

        try:
            # C33:C34 = Google Finance Cuma kapanis (hafta sonu da Cuma kapanisi gosterir)
            panel_vals = ws_ana.get("C33:C34", value_render_option="UNFORMATTED_VALUE")
            if panel_vals and len(panel_vals) >= 2:
                bist_guncel = panel_vals[0][0] if panel_vals[0] else None
                usd_guncel = panel_vals[1][0] if panel_vals[1] else None

                if bist_guncel and usd_guncel:
                    if not kuru:
                        ws_ana.update("B33", [[bist_guncel]], value_input_option="RAW")
                        ws_ana.update("B34", [[usd_guncel]], value_input_option="RAW")
                    print("  BIST 100 P.Basi: {:.2f}{}".format(bist_guncel, " [KURU]" if kuru else ""))
                    print("  USDTRY  P.Basi: {:.4f}{}".format(usd_guncel, " [KURU]" if kuru else ""))
                    log.info("Pazar guncelleme: BIST=%.2f, USDTRY=%.4f", bist_guncel, usd_guncel)
                else:
                    print("  [UYARI] Panel degerleri okunamadi")
            else:
                print("  [UYARI] Panel hucreleri bos")
        except Exception as e:
            print("  [HATA] Pazar guncelleme hatasi: {}".format(e))
            log.error("Pazar guncelleme hatasi: %s", e)

    print("=" * 55)


if __name__ == "__main__":
    main()

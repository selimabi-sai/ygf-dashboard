# -*- coding: utf-8 -*-
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

ws = ss.worksheet("Ana Sayfa")
sheet_id = ws.id

# ── 1) Sağ paneli temizle (P1:S16) ──
# Önce merge'leri kaldır
ss.batch_update({"requests": [
    {"unmergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 15, "endColumnIndex": 19}}},
    {"unmergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 15, "endColumnIndex": 19}}},
]})
time.sleep(1)

# Hücreleri temizle
temiz = []
for r in range(1, 17):
    for c in range(16, 20):  # P=16, Q=17, R=18, S=19
        temiz.append(gspread.Cell(r, c, ""))
ws.update_cells(temiz)

# Arka plan ve border temizle
ss.batch_update({"requests": [
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 16, "startColumnIndex": 15, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 1, "green": 1, "blue": 1},
            "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": False,
                           "foregroundColorStyle": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}}
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }},
    {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 16, "startColumnIndex": 15, "endColumnIndex": 19},
        "top": {"style": "NONE"}, "bottom": {"style": "NONE"},
        "left": {"style": "NONE"}, "right": {"style": "NONE"},
        "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"},
    }},
]})
print("Sag panel temizlendi")
time.sleep(1)

# ── 2) Sol alta yaz (satır 24'ten başla) ──
# Satır 24: KIYASLAMA PANELİ (A24:D24 merge)
# Satır 26: başlıklar
# Satır 27-29: BIST, USDTRY, Faiz
# Satır 31: PERİYOT GETİRİLERİ (A31:D31 merge)
# Satır 32: başlıklar
# Satır 33-35: periyot BIST, USDTRY, Faiz
# Satır 37: Son Güncelleme

updates = [
    {"range": "A24", "values": [["KIYASLAMA PANEL\u0130"]]},
    {"range": "A26:D26", "values": [["", "Ba\u015flang\u0131\u00e7", "G\u00fcncel", "Getiri"]]},

    {"range": "A27", "values": [["BIST 100"]]},
    {"range": "B27", "values": [[11498.38]]},
    {"range": "C27", "values": [['=IFERROR(GOOGLEFINANCE("INDEXIST:XU100";"price");"")']]},
    {"range": "D27", "values": [['=IFERROR(ROUND((C27-B27)/B27*100;2)&"%";"")']]},

    {"range": "A28", "values": [["USDTRY"]]},
    {"range": "B28", "values": [[43.0375]]},
    {"range": "C28", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:USDTRY");"")']]},
    {"range": "D28", "values": [['=IFERROR(ROUND((C28-B28)/B28*100;2)&"%";"")']]},

    {"range": "A29", "values": [["Faiz (Mevduat)"]]},
    {"range": "B29", "values": [[100]]},
    {"range": "C29", "values": [["=ROUND(100*(1+0,428/365)^(TODAY()-DATE(2026;1;2));2)"]]},
    {"range": "D29", "values": [['=IFERROR(ROUND(C29-100;2)&"%";"")']]},

    {"range": "A31", "values": [["PER\u0130YOT GET\u0130R\u0130LER\u0130"]]},
    {"range": "A32:D32", "values": [["", "P.Ba\u015f\u0131", "P.Sonu", "Getiri"]]},

    {"range": "A33", "values": [["BIST 100"]]},
    {"range": "B33", "values": [[13717.81]]},
    {"range": "C33", "values": [['=IFERROR(GOOGLEFINANCE("INDEXIST:XU100";"price");"")']]},
    {"range": "D33", "values": [['=IFERROR(ROUND((C33-B33)/B33*100;2)&"%";"")']]},

    {"range": "A34", "values": [["USDTRY"]]},
    {"range": "B34", "values": [[43.9702]]},
    {"range": "C34", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:USDTRY");"")']]},
    {"range": "D34", "values": [['=IFERROR(ROUND((C34-B34)/B34*100;2)&"%";"")']]},

    {"range": "A35", "values": [["Faiz"]]},
    {"range": "B35", "values": [[100]]},
    {"range": "C35", "values": [["=ROUND(100*(1+0,428/365)^14;2)"]]},
    {"range": "D35", "values": [['=IFERROR(ROUND(C35-100;2)&"%";"")']]},

    {"range": "A37", "values": [["Son G\u00fcncelleme:"]]},
    {"range": "B37", "values": [["=NOW()"]]},
]

ws.batch_update(updates, value_input_option="USER_ENTERED")
print("Sol alta yazildi")
time.sleep(1)

# ── 3) Formatlama ──
LAC = {"red": 0.122, "green": 0.306, "blue": 0.475}
WHT = {"red": 1, "green": 1, "blue": 1}
BLK = {"red": 0, "green": 0, "blue": 0}
GRY = {"red": 0.4, "green": 0.4, "blue": 0.4}

requests = [
    # A24:D24 merge + lacivert bg, beyaz bold, Calibri 12
    {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 23, "endRowIndex": 24, "startColumnIndex": 0, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 23, "endRowIndex": 24, "startColumnIndex": 0, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 12, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
    }},

    # A31:D31 merge + lacivert
    {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 30, "endRowIndex": 31, "startColumnIndex": 0, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 30, "endRowIndex": 31, "startColumnIndex": 0, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 12, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
    }},

    # A26:D26 ve A32:D32 header: lacivert bg, beyaz bold, Calibri 10
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 25, "endRowIndex": 26, "startColumnIndex": 0, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 31, "endRowIndex": 32, "startColumnIndex": 0, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }},

    # A27:A29, A33:A35: bold
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 26, "endRowIndex": 29, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": True, "foregroundColorStyle": {"rgbColor": BLK}}}},
        "fields": "userEnteredFormat.textFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 32, "endRowIndex": 35, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": True, "foregroundColorStyle": {"rgbColor": BLK}}}},
        "fields": "userEnteredFormat.textFormat"
    }},

    # B-D veri: Calibri 11, saga hizali
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 26, "endRowIndex": 29, "startColumnIndex": 1, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "foregroundColorStyle": {"rgbColor": BLK}},
            "horizontalAlignment": "RIGHT"
        }}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 32, "endRowIndex": 35, "startColumnIndex": 1, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {
            "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "foregroundColorStyle": {"rgbColor": BLK}},
            "horizontalAlignment": "RIGHT"
        }}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
    }},

    # B-C number format
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 26, "endRowIndex": 29, "startColumnIndex": 1, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}}},
        "fields": "userEnteredFormat.numberFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 32, "endRowIndex": 35, "startColumnIndex": 1, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}}},
        "fields": "userEnteredFormat.numberFormat"
    }},

    # Border
    {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 25, "endRowIndex": 29, "startColumnIndex": 0, "endColumnIndex": 4},
        "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
    }},
    {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 31, "endRowIndex": 35, "startColumnIndex": 0, "endColumnIndex": 4},
        "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
    }},

    # A37: gri, B37 datetime format
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 36, "endRowIndex": 37, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": GRY}}}},
        "fields": "userEnteredFormat.textFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 36, "endRowIndex": 37, "startColumnIndex": 1, "endColumnIndex": 2},
        "cell": {"userEnteredFormat": {
            "numberFormat": {"type": "DATE_TIME", "pattern": "dd.MM.yyyy HH:mm"},
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "foregroundColorStyle": {"rgbColor": GRY}}
        }}, "fields": "userEnteredFormat(numberFormat,textFormat)"
    }},
]

ss.batch_update({"requests": requests})
print("Formatlama tamamlandi")
time.sleep(1)

# Kontrol
vals = ws.get("A24:D37", value_render_option="FORMATTED_VALUE")
print()
for i, row in enumerate(vals):
    if any(str(c).strip() for c in row):
        print("  {}: {}".format(24 + i, row))

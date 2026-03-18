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

# ── 1) Veri ve formüller ──
updates = [
    {"range": "P1", "values": [["KIYASLAMA PANEL\u0130"]]},
    {"range": "P3:S3", "values": [["", "Ba\u015flang\u0131\u00e7", "G\u00fcncel", "Getiri"]]},

    # BIST 100
    {"range": "P4", "values": [["BIST 100"]]},
    {"range": "Q4", "values": [[11498.38]]},
    {"range": "R4", "values": [['=IFERROR(GOOGLEFINANCE("INDEXIST:XU100";"price");"")']]},
    {"range": "S4", "values": [['=IFERROR(ROUND((R4-Q4)/Q4*100;2)&"%";"")']]},

    # USDTRY
    {"range": "P5", "values": [["USDTRY"]]},
    {"range": "Q5", "values": [[43.0375]]},
    {"range": "R5", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:USDTRY");"")']]},
    {"range": "S5", "values": [['=IFERROR(ROUND((R5-Q5)/Q5*100;2)&"%";"")']]},

    # Faiz
    {"range": "P6", "values": [["Faiz (Mevduat)"]]},
    {"range": "Q6", "values": [[100]]},
    {"range": "R6", "values": [["=ROUND(100*(1+0,428/365)^(TODAY()-DATE(2026;1;2));2)"]]},
    {"range": "S6", "values": [['=IFERROR(ROUND(R6-100;2)&"%";"")']]},

    # Altin TL/gram
    {"range": "P7", "values": [["Alt\u0131n (gr/TL)"]]},
    {"range": "Q7", "values": [[2925]]},
    {"range": "R7", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:XAUTRY");"")']]},
    {"range": "S7", "values": [['=IFERROR(ROUND((R7-Q7)/Q7*100;2)&"%";"")']]},

    # Altin USD/oz
    {"range": "P8", "values": [["Alt\u0131n (USD/oz)"]]},
    {"range": "Q8", "values": [[2640]]},
    {"range": "R8", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:XAUUSD");"")']]},
    {"range": "S8", "values": [['=IFERROR(ROUND((R8-Q8)/Q8*100;2)&"%";"")']]},

    # Periyot basligi
    {"range": "P10", "values": [["PER\u0130YOT GET\u0130R\u0130LER\u0130"]]},
    {"range": "P11:S11", "values": [["", "P.Ba\u015f\u0131", "P.Sonu", "Getiri"]]},

    # Periyot BIST
    {"range": "P12", "values": [["BIST 100"]]},
    {"range": "Q12", "values": [[12800]]},
    {"range": "R12", "values": [['=IFERROR(GOOGLEFINANCE("INDEXIST:XU100";"price");"")']]},
    {"range": "S12", "values": [['=IFERROR(ROUND((R12-Q12)/Q12*100;2)&"%";"")']]},

    # Periyot USDTRY
    {"range": "P13", "values": [["USDTRY"]]},
    {"range": "Q13", "values": [[36.18]]},
    {"range": "R13", "values": [['=IFERROR(GOOGLEFINANCE("CURRENCY:USDTRY");"")']]},
    {"range": "S13", "values": [['=IFERROR(ROUND((R13-Q13)/Q13*100;2)&"%";"")']]},

    # Periyot Faiz
    {"range": "P14", "values": [["Faiz"]]},
    {"range": "Q14", "values": [[100]]},
    {"range": "R14", "values": [["=ROUND(100*(1+0,428/365)^14;2)"]]},
    {"range": "S14", "values": [['=IFERROR(ROUND(R14-100;2)&"%";"")']]},

    # Son guncelleme
    {"range": "P16", "values": [["Son G\u00fcncelleme:"]]},
    {"range": "Q16", "values": [["=NOW()"]]},
]

ws.batch_update(updates, value_input_option="USER_ENTERED")
print("Veriler ve formuller yazildi")
time.sleep(1)

# ── 2) Formatlama ──
LAC = {"red": 0.122, "green": 0.306, "blue": 0.475}
WHT = {"red": 1, "green": 1, "blue": 1}
BLK = {"red": 0, "green": 0, "blue": 0}
GRY = {"red": 0.4, "green": 0.4, "blue": 0.4}

requests = [
    # Merge P1:S1 ve P10:S10
    {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 15, "endColumnIndex": 19}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 15, "endColumnIndex": 19}, "mergeType": "MERGE_ALL"}},

    # P1 ve P10: lacivert, beyaz bold, Calibri 12, ortali
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 15, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 12, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 15, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 12, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
    }},

    # P3:S3 ve P11:S11: lacivert bg, beyaz bold, Calibri 10, ortali
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 15, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 10, "endRowIndex": 11, "startColumnIndex": 15, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "backgroundColor": LAC,
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": WHT}},
            "horizontalAlignment": "CENTER"
        }}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }},

    # P4:P8, P12:P14: bold, Calibri 11
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 3, "endRowIndex": 8, "startColumnIndex": 15, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": True, "foregroundColorStyle": {"rgbColor": BLK}}}},
        "fields": "userEnteredFormat.textFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 11, "endRowIndex": 14, "startColumnIndex": 15, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 11, "bold": True, "foregroundColorStyle": {"rgbColor": BLK}}}},
        "fields": "userEnteredFormat.textFormat"
    }},

    # Q-S veri: Calibri 11, saga hizali
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 3, "endRowIndex": 8, "startColumnIndex": 16, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "foregroundColorStyle": {"rgbColor": BLK}},
            "horizontalAlignment": "RIGHT"
        }}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 11, "endRowIndex": 14, "startColumnIndex": 16, "endColumnIndex": 19},
        "cell": {"userEnteredFormat": {
            "textFormat": {"fontFamily": "Calibri", "fontSize": 11, "foregroundColorStyle": {"rgbColor": BLK}},
            "horizontalAlignment": "RIGHT"
        }}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
    }},

    # Q-R number format #,##0.00
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 3, "endRowIndex": 8, "startColumnIndex": 16, "endColumnIndex": 18},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}}},
        "fields": "userEnteredFormat.numberFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 11, "endRowIndex": 14, "startColumnIndex": 16, "endColumnIndex": 18},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"}}},
        "fields": "userEnteredFormat.numberFormat"
    }},

    # P16 bold gri, Q16 datetime format
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 15, "endRowIndex": 16, "startColumnIndex": 15, "endColumnIndex": 16},
        "cell": {"userEnteredFormat": {"textFormat": {"fontFamily": "Calibri", "fontSize": 10, "bold": True, "foregroundColorStyle": {"rgbColor": GRY}}}},
        "fields": "userEnteredFormat.textFormat"
    }},
    {"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 15, "endRowIndex": 16, "startColumnIndex": 16, "endColumnIndex": 17},
        "cell": {"userEnteredFormat": {
            "numberFormat": {"type": "DATE_TIME", "pattern": "dd.MM.yyyy HH:mm"},
            "textFormat": {"fontFamily": "Calibri", "fontSize": 10, "foregroundColorStyle": {"rgbColor": GRY}}
        }}, "fields": "userEnteredFormat(numberFormat,textFormat)"
    }},

    # Sutun genislikleri
    {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 15, "endIndex": 16}, "properties": {"pixelSize": 130}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 16, "endIndex": 18}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 18, "endIndex": 19}, "properties": {"pixelSize": 80}, "fields": "pixelSize"}},

    # Border
    {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 8, "startColumnIndex": 15, "endColumnIndex": 19},
        "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
    }},
    {"updateBorders": {
        "range": {"sheetId": sheet_id, "startRowIndex": 10, "endRowIndex": 14, "startColumnIndex": 15, "endColumnIndex": 19},
        "top": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "bottom": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "left": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "right": {"style": "SOLID", "color": {"red": 0.7, "green": 0.7, "blue": 0.7}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.85, "green": 0.85, "blue": 0.85}},
    }},
]

ss.batch_update({"requests": requests})
print("Formatlama tamamlandi")
time.sleep(2)

# ── 3) Kontrol ──
vals = ws.get("P1:S16", value_render_option="FORMATTED_VALUE")
print()
for i, row in enumerate(vals):
    if any(c for c in row):
        print("  {}: {}".format(i + 1, row))

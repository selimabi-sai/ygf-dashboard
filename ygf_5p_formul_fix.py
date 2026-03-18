# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from google.oauth2.service_account import Credentials
import time

CREDS = r"C:\Users\PDS\Desktop\snap code\credentials.json"
SHEET_ID = "1RvQnrukTy8LVxWjskFYUzlpCOuAqEU9IH7YTFM2XJQI"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file(CREDS, scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SHEET_ID)

YARISMACILAR_IDX = list(range(1, 12))  # worksheet index 1-11

for idx in YARISMACILAR_IDX:
    ws = ss.worksheets()[idx]
    all_vals = ws.get_all_values()

    print(f"\n{ws.title}:")

    # 5. Periyot bul
    periyot5_row = None
    toplam5_row = None
    for i, row in enumerate(all_vals):
        if '5. Periyot' in str(row[0]):
            periyot5_row = i + 1
        if periyot5_row and i + 1 > periyot5_row + 1 and row[0] == 'TOPLAM':
            toplam5_row = i + 1
            break

    if not periyot5_row or not toplam5_row:
        print(f"  [HATA] 5P bulunamadi!")
        continue

    data_start = periyot5_row + 2

    # Veri satırlarını bul (hisse adı olan satırlar)
    formula_updates = []
    for r in range(data_start, toplam5_row):
        hisse = all_vals[r - 1][0]  # 0-indexed
        if hisse and hisse != '':
            # Türkçe locale: noktalı virgül ayracı
            formula = f'=IF(C{r}="";"";\u0025ROUND(C{r}/C{toplam5_row}*100;1)&"%")'
            # Aslında daha basit formül kullanalım
            formula = f'=IFERROR(ROUND(C{r}/C{toplam5_row}*100;1)&"%";"")'
            formula_updates.append({
                'range': f'B{r}',
                'values': [[formula]]
            })
            print(f"  B{r}: {formula}")

    if formula_updates:
        ws.batch_update(formula_updates, value_input_option='USER_ENTERED')
        print(f"  -> {len(formula_updates)} formul guncellendi")

    time.sleep(1)

print(f"\nTAMAMLANDI!")

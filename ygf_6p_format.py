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

guncellenen = 0
ws_list = ss.worksheets()

for idx in range(1, 12):
    ws = ws_list[idx]
    vals = ws.get_all_values()

    # 6P bloğunu bul
    blok_start = None
    blok_toplam = None
    for i, row in enumerate(vals):
        if '6. Periyot' in str(row[0]):
            blok_start = i
        if blok_start is not None and i > blok_start + 1 and row[0] == 'TOPLAM':
            blok_toplam = i
            break

    if blok_start is None:
        print("{} - 6P blogu YOK, atlaniyor".format(ws.title))
        continue

    data_start = blok_start + 2
    toplam_row = blok_toplam + 1  # 1-indexed

    # Hisse satırlarını bul
    hisse_rows = []
    for r in range(data_start, blok_toplam):
        if vals[r][0].strip():
            hisse_rows.append(r)

    if not hisse_rows:
        print("{} - 6P hisse yok, atlaniyor".format(ws.title))
        continue

    ilk_hisse_1 = hisse_rows[0] + 1
    son_hisse_1 = hisse_rows[-1] + 1

    print("\n{}: 6P blok satir {}-{}, {} hisse".format(
        ws.title, data_start + 1, toplam_row, len(hisse_rows)))

    cells = []
    formul_updates = []

    for r in hisse_rows:
        row_1 = r + 1
        d_val = vals[r][3].strip()
        e_val = vals[r][4].strip()

        # D: milyona böl
        if d_val:
            try:
                d_num = round(float(d_val) / 1_000_000)
                cells.append(gspread.Cell(row_1, 4, d_num))
            except ValueError:
                pass

        # E: milyona böl
        if e_val:
            try:
                e_num = round(float(e_val) / 1_000_000)
                cells.append(gspread.Cell(row_1, 5, e_num))
            except ValueError:
                pass

        # F: Getiri formülü
        formul_updates.append({
            'range': 'F{}'.format(row_1),
            'values': [['=IFERROR(ROUND((E{n}-D{n})/D{n}*100;2);"")'.format(n=row_1)]]
        })

        # G: Katkı formülü
        formul_updates.append({
            'range': 'G{}'.format(row_1),
            'values': [['=IFERROR(ROUND(F{n}*C{n}/C{t};2);"")'.format(n=row_1, t=toplam_row)]]
        })

        # H: Not temizle
        cells.append(gspread.Cell(row_1, 8, ''))

    # Header row H temizle
    header_row = blok_start + 2  # 1-indexed
    cells.append(gspread.Cell(header_row, 8, ''))

    # Boş satırların H'sini temizle
    for r in range(data_start, blok_toplam):
        if r not in hisse_rows:
            cells.append(gspread.Cell(r + 1, 8, ''))

    # TOPLAM satırı
    formul_updates.append({
        'range': 'F{}'.format(toplam_row),
        'values': [['=SUM(G{}:G{})'.format(ilk_hisse_1, son_hisse_1)]]
    })
    formul_updates.append({
        'range': 'G{}'.format(toplam_row),
        'values': [['=SUM(G{}:G{})'.format(ilk_hisse_1, son_hisse_1)]]
    })
    cells.append(gspread.Cell(toplam_row, 8, ''))

    # Yaz
    if cells:
        ws.update_cells(cells)
    if formul_updates:
        ws.batch_update(formul_updates, value_input_option='USER_ENTERED')

    # Format
    sheet_id = ws.id
    requests = [
        # D,E: #.##0
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': data_start,
                    'endRowIndex': blok_toplam + 1,
                    'startColumnIndex': 3,
                    'endColumnIndex': 5
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {'type': 'NUMBER', 'pattern': '#.##0'},
                        'textFormat': {
                            'fontFamily': 'Calibri', 'fontSize': 11,
                            'foregroundColorStyle': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}
                        }
                    }
                },
                'fields': 'userEnteredFormat(numberFormat,textFormat)'
            }
        },
        # F,G: 0,00
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': data_start,
                    'endRowIndex': blok_toplam + 1,
                    'startColumnIndex': 5,
                    'endColumnIndex': 7
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {'type': 'NUMBER', 'pattern': '0,00'},
                        'textFormat': {
                            'fontFamily': 'Calibri', 'fontSize': 11,
                            'foregroundColorStyle': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}
                        }
                    }
                },
                'fields': 'userEnteredFormat(numberFormat,textFormat)'
            }
        },
        # A,B,C: Calibri 11 siyah
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': data_start,
                    'endRowIndex': blok_toplam + 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 3
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'fontFamily': 'Calibri', 'fontSize': 11,
                            'foregroundColorStyle': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat'
            }
        },
    ]
    ss.batch_update({'requests': requests})

    guncellenen += 1
    print("  -> {} hisse: D/E milyona bolundu, F/G formul, H temizlendi".format(len(hisse_rows)))
    time.sleep(2)

print("\n" + "=" * 50)
print("{} / 11 yarismaci 6P blogu guncellendi.".format(guncellenen))
print("=" * 50)

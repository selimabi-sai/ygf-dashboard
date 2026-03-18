import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

CREDENTIALS_PATH = r"C:\Users\PDS\Desktop\snap code\credentials.json"
SHEET_ID = "1RvQnrukTy8LVxWjskFYUzlpCOuAqEU9IH7YTFM2XJQI"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

okuma_ok = False
yazma_ok = False

try:
    creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)

    # --- OKUMA TESTİ ---
    print("=" * 50)
    print("OKUMA TESTİ - 'Ana Sayfa' worksheet")
    print("=" * 50)
    ws_ana = spreadsheet.worksheet("Ana Sayfa")
    rows = ws_ana.get_all_values()
    for i, row in enumerate(rows[:5]):
        print(f"Satır {i+1}: {row}")
    okuma_ok = True
    print()

    # --- YAZMA TESTİ ---
    print("=" * 50)
    print("YAZMA TESTİ - 'VERİ' worksheet")
    print("=" * 50)
    ws_veri = spreadsheet.worksheet("VERİ")
    test_row = ["TEST", "Bağlantı OK", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    ws_veri.append_row(test_row)
    print(f"Test satırı yazıldı: {test_row}")

    # Yazılan satırı bul ve sil
    all_rows = ws_veri.get_all_values()
    for idx, row in enumerate(all_rows):
        if row[0] == "TEST" and row[1] == "Bağlantı OK":
            ws_veri.delete_rows(idx + 1)  # 1-indexed
            print(f"Test satırı silindi (satır {idx + 1})")
            break
    yazma_ok = True
    print()

except Exception as e:
    print(f"\nHATA: {type(e).__name__}: {e}")

print("=" * 50)
if okuma_ok:
    print("OKUMA: BASARILI")
else:
    print("OKUMA: BASARISIZ")
if yazma_ok:
    print("YAZMA: BASARILI")
else:
    print("YAZMA: BASARISIZ")
print("=" * 50)

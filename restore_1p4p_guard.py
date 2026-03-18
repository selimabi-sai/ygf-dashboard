# -*- coding: utf-8 -*-
import argparse
import json
import math
import os
import sys
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(SCRIPT_DIR, "ygf_ayarlar.json")
SNAPSHOT_PATH = "/tmp/ygf_restore_snapshot.json"
BENCHMARKS = {"BIST 100", "Faiz", "USDTRY"}
REFERENCES = {
    "Barış": {4: -6.91, 3: 2.58, 2: 8.42, 1: 11.72},
    "Serkan": {4: -6.73, 3: 3.18, 2: 9.95, 1: 17.01},
    "Ali Cenk": {4: -5.80, 3: 4.28, 2: 10.72, 1: 9.76},
    "Özhan": {4: -8.20, 3: 7.84, 2: 16.75, 1: 11.45},
    "Turan": {4: -8.93, 3: 5.09, 2: 9.17, 1: 3.78},
    "Berkan": {4: -8.09, 3: 0.62, 2: 6.34, 1: 7.66},
    "Selim": {4: -7.74, 3: 3.00, 2: -6.73, 1: 24.68},
    "Gürkan": {4: -12.18, 3: 1.32, 2: -3.86, 1: 19.61},
    "Osman": {4: -13.54, 3: -1.74, 2: 0.22, 1: 21.02},
    "Oğuz": {4: -5.95, 3: 3.31, 2: 11.18, 1: 3.96},
    "Mehmet": {4: -6.90, 3: 3.09, 2: 1.56, 1: 14.90},
}


def load_settings():
    with open(SETTINGS_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_local_path(path):
    if path and len(path) > 2 and path[1:3] == ":\\":
        drive = path[0].lower()
        rest = path[3:].replace("\\", "/")
        return f"/mnt/{drive}/{rest}"
    return path


def connect():
    settings = load_settings()
    creds = Credentials.from_service_account_file(
        normalize_local_path(settings["credentials_json"]), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(settings["google_sheet_id"])
    return settings, ss


def col_to_a1(col_idx_1based):
    result = []
    col = col_idx_1based
    while col:
        col, rem = divmod(col - 1, 26)
        result.append(chr(65 + rem))
    return "".join(reversed(result))


def to_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("%", "").replace("\xa0", "").replace(" ", "")
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def fmt_value(value):
    if value is None:
        return "[BOS]"
    return f"{value:.2f}"


def row_is_blank(row):
    return all(not str(cell).strip() for cell in row)


def get_ana_layout(ws_ana):
    values = ws_ana.get_all_values()
    if len(values) < 5:
        raise RuntimeError("Ana Sayfa'da 5. satır başlıkları bulunamadı.")
    headers = values[4]
    period_cols = {}
    for idx, header in enumerate(headers, start=1):
        head = str(header).strip()
        if head.endswith("P") and head[:-1].isdigit():
            period_cols[int(head[:-1])] = idx
    return values, headers, period_cols


def find_row_by_name(ana_values, name):
    for idx in range(5, len(ana_values)):
        row = ana_values[idx]
        if len(row) > 1 and str(row[1]).strip() == name:
            return idx + 1
    return None


def find_sheet_by_name(ss, name):
    for ws in ss.worksheets():
        title = ws.title.strip()
        if title == name or title in name or name in title:
            return ws
    raise RuntimeError(f"'{name}' için worksheet bulunamadı.")


def find_total_f_value(rows, period_no):
    header = f"{period_no}. Periyot"
    in_block = False
    for idx, row in enumerate(rows, start=1):
        first = str(row[0]).strip() if row else ""
        if header == first:
            in_block = True
            continue
        if in_block and first == "TOPLAM":
            raw_value = row[5] if len(row) > 5 else ""
            return idx, to_number(raw_value), raw_value
    return None, None, ""


def print_step_header(step_name):
    print("=" * 72)
    print(step_name)
    print("=" * 72)


def step1():
    settings, ss = connect()
    ws_ana = ss.worksheet("Ana Sayfa")
    ana_values, headers, period_cols = get_ana_layout(ws_ana)
    competitors = settings["yarismacilar"]

    print_step_header("ADIM 1 - ANA SAYFA DURUM OKUMA")
    print("Satır 5 başlıkları:")
    for idx, header in enumerate(headers, start=1):
        print(f"  {col_to_a1(idx)}5 = {header}")

    sorted_periods = sorted(period_cols.keys(), reverse=True)
    if not sorted_periods:
        raise RuntimeError("Ana Sayfa'da periyot sütunu bulunamadı.")

    print("\nYarışmacı satırları (tüm periyot sütunları):")
    blank_cells = []
    for name in competitors:
        row_num = find_row_by_name(ana_values, name)
        if row_num is None:
            print(f"  [HATA] {name} Ana Sayfa'da bulunamadı.")
            continue
        row = ana_values[row_num - 1]
        parts = [f"Satır {row_num}", f"İsim={name}"]
        for period in sorted_periods:
            col_num = period_cols[period]
            raw_value = row[col_num - 1] if len(row) >= col_num else ""
            label = f"{period}P"
            if str(raw_value).strip():
                parts.append(f"{label}={raw_value}")
            else:
                cell = f"{col_to_a1(col_num)}{row_num}"
                parts.append(f"{label}=[BOS]")
                if period in {1, 2, 3, 4}:
                    blank_cells.append((cell, name, label))
        print("  " + " | ".join(parts))

    print("\nÖzellikle 4P / 3P / 2P / 1P boş hücreler:")
    if blank_cells:
        for cell, name, label in blank_cells:
            print(f"  {cell} | {name} | {label} | BOS")
    else:
        print("  [BOS YOK]")


def read_sheet_period_totals(ss, competitors):
    results = {}
    for name in competitors:
        ws = find_sheet_by_name(ss, name)
        rows = ws.get_all_values()
        results[name] = {
            "sheet_title": ws.title,
            "rows": rows,
            "periods": {},
        }
        for period in (1, 2, 3, 4):
            toplam_row, num_value, raw_value = find_total_f_value(rows, period)
            results[name]["periods"][period] = {
                "toplam_row": toplam_row,
                "value": None if num_value is None else round(num_value, 2),
                "raw": raw_value,
            }
    return results


def step2():
    settings, ss = connect()
    competitors = settings["yarismacilar"]
    sheet_data = read_sheet_period_totals(ss, competitors)

    print_step_header("ADIM 2 - YARIŞMACI SAYFALARINDAN DOĞRULAMA")
    print("İsim | 1P (Sheet) | 2P (Sheet) | 3P (Sheet) | 4P (Sheet)")
    mismatches = []

    for name in competitors:
        periods = sheet_data[name]["periods"]
        print(
            " | ".join(
                [
                    name,
                    fmt_value(periods[1]["value"]),
                    fmt_value(periods[2]["value"]),
                    fmt_value(periods[3]["value"]),
                    fmt_value(periods[4]["value"]),
                ]
            )
        )

        ref = REFERENCES[name]
        for period in (1, 2, 3, 4):
            sheet_val = periods[period]["value"]
            ref_val = round(ref[period], 2)
            if sheet_val is None or round(sheet_val, 2) != ref_val:
                mismatches.append((name, period, sheet_val, ref_val))

    print("\nReferans karşılaştırması:")
    if mismatches:
        for name, period, sheet_val, ref_val in mismatches:
            print(
                f"  [UYUŞMAZLIK] {name} {period}P | Sheet={fmt_value(sheet_val)} | "
                f"Referans={ref_val:.2f}"
            )
        raise SystemExit(2)

    print("  Tüm 1P-4P değerleri referansla uyuşuyor. Yazım için sheet değerleri kullanılabilir.")


def step3(apply_fix):
    settings, ss = connect()
    competitors = settings["yarismacilar"]

    print_step_header("ADIM 3 - SATIR KAYMASI KONTROLÜ")
    shifted = []

    for name in competitors:
        ws = find_sheet_by_name(ss, name)
        rows = ws.get_all_values()
        first_five = rows[:5]
        row1 = first_five[0] if len(first_five) >= 1 else []
        row2 = first_five[1] if len(first_five) >= 2 else []
        is_shifted = row_is_blank(row1) and len(row2) > 0 and str(row2[0]).strip() == "1. Periyot"

        print(f"\n{name} | Worksheet={ws.title}")
        print("  İlk 5 satır (önce):")
        for idx in range(5):
            row = first_five[idx] if idx < len(first_five) else []
            print(f"    Satır {idx + 1}: {row}")
        status = "KAYMA VAR" if is_shifted else "Kayma yok"
        print(f"  Durum: {status}")
        shifted.append((name, ws, is_shifted))

    if not apply_fix:
        return

    any_fixed = False
    for name, ws, is_shifted in shifted:
        if not is_shifted:
            continue
        all_rows = ws.get_all_values()
        row1 = all_rows[0] if all_rows else []
        row2 = all_rows[1] if len(all_rows) > 1 else []
        if not (row_is_blank(row1) and len(row2) > 0 and str(row2[0]).strip() == "1. Periyot"):
            raise RuntimeError(f"{name} için kayma koşulu tekrar doğrulanamadı; işlem durduruldu.")
        ws.delete_rows(1)
        any_fixed = True

        after_rows = ws.get_all_values()[:5]
        print(f"\n{name} | 1. satır silindi, ilk 5 satır (sonra):")
        for idx in range(5):
            row = after_rows[idx] if idx < len(after_rows) else []
            print(f"  Satır {idx + 1}: {row}")

    if not any_fixed:
        print("\nKayma tespit edilmedi; hiçbir satır silinmedi.")


def build_updates(ws_ana, ana_values, competitors, verified_values):
    _, headers, period_cols = get_ana_layout(ws_ana)
    missing = []

    for name in competitors:
        row_num = find_row_by_name(ana_values, name)
        if row_num is None:
            raise RuntimeError(f"{name} Ana Sayfa'da bulunamadı.")
        row = ana_values[row_num - 1]
        for period in (4, 3, 2, 1):
            col_num = period_cols.get(period)
            if col_num is None:
                raise RuntimeError(f"Ana Sayfa'da {period}P sütunu bulunamadı.")
            current = row[col_num - 1] if len(row) >= col_num else ""
            if str(current).strip():
                continue
            value = verified_values[name]["periods"][period]["value"]
            if value is None:
                raise RuntimeError(f"{name} {period}P sheet değeri boş; yazma durduruldu.")
            missing.append(
                {
                    "name": name,
                    "period": period,
                    "cell": f"{col_to_a1(col_num)}{row_num}",
                    "value": float(value),
                }
            )

    non_target_headers = []
    for idx, header in enumerate(headers, start=1):
        label = str(header).strip()
        if idx < 3:
            continue
        if label in {"1P", "2P", "3P", "4P"}:
            continue
        non_target_headers.append((idx, label))

    snapshot_rows = {}
    for row_num in range(6, min(20, len(ana_values)) + 1):
        row = ana_values[row_num - 1]
        name = row[1].strip() if len(row) > 1 else ""
        if not name:
            continue
        snapshot_rows[str(row_num)] = {
            "name": name,
            "values": {
                label: row[idx - 1] if len(row) >= idx else ""
                for idx, label in non_target_headers
            },
        }

    snapshot = {
        "saved_at": datetime.now().isoformat(),
        "non_target_headers": [label for _, label in non_target_headers],
        "rows": snapshot_rows,
        "targets": missing,
    }
    return missing, snapshot


def step4(apply_write):
    settings, ss = connect()
    competitors = settings["yarismacilar"]
    ws_ana = ss.worksheet("Ana Sayfa")
    ana_values, _, _ = get_ana_layout(ws_ana)

    verified = read_sheet_period_totals(ss, competitors)
    for name in competitors:
        ref = REFERENCES[name]
        for period in (1, 2, 3, 4):
            value = verified[name]["periods"][period]["value"]
            if value is None or round(value, 2) != round(ref[period], 2):
                raise RuntimeError(f"{name} {period}P referans uyuşmazlığı nedeniyle yazma durduruldu.")

    updates, snapshot = build_updates(ws_ana, ana_values, competitors, verified)

    print_step_header("ADIM 4 - ANA SAYFA'YA 1P-4P YAZIMI")
    print("Yazılacak hücreler [Hücre | Değer]:")
    if updates:
        for item in updates:
            print(f"  {item['cell']} | {item['value']:.2f}")
    else:
        print("  [YAZILACAK BOŞ HÜCRE YOK]")

    if not apply_write or not updates:
        return

    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, ensure_ascii=False, indent=2)

    body = [{"range": item["cell"], "values": [[item["value"]]]} for item in updates]
    ws_ana.batch_update(body, value_input_option="RAW")
    print(f"\n{len(updates)} hücre sayısal değer olarak yazıldı.")


def step5():
    if not os.path.exists(SNAPSHOT_PATH):
        raise RuntimeError(f"Snapshot bulunamadı: {SNAPSHOT_PATH}")

    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as handle:
        snapshot = json.load(handle)

    settings, ss = connect()
    competitors = settings["yarismacilar"]
    ws_ana = ss.worksheet("Ana Sayfa")
    ana_values, _, period_cols = get_ana_layout(ws_ana)

    print_step_header("ADIM 5 - DOĞRULAMA")
    print("Ana Sayfa 1P-4P değerleri:")
    blanks = []
    for name in competitors:
        row_num = find_row_by_name(ana_values, name)
        if row_num is None:
            print(f"  [HATA] {name} Ana Sayfa'da bulunamadı.")
            continue
        row = ana_values[row_num - 1]
        parts = [name]
        for period in (4, 3, 2, 1):
            col_num = period_cols[period]
            raw_value = row[col_num - 1] if len(row) >= col_num else ""
            if str(raw_value).strip():
                parts.append(f"{period}P={raw_value}")
            else:
                cell = f"{col_to_a1(col_num)}{row_num}"
                parts.append(f"{period}P=[BOS]")
                blanks.append(cell)
        print("  " + " | ".join(parts))

    print("\nBoş hücre kontrolü:")
    if blanks:
        for cell in blanks:
            print(f"  [BOS KALDI] {cell}")
    else:
        print("  1P-4P içinde boş yarışmacı hücresi kalmadı.")

    print("\nDiğer sütun doğrulaması:")
    diffs = []
    snapshot_headers = snapshot["non_target_headers"]
    row_snapshots = snapshot["rows"]
    for row_num_str, row_snapshot in row_snapshots.items():
        row_num = int(row_num_str)
        row = ana_values[row_num - 1] if len(ana_values) >= row_num else []
        for header in snapshot_headers:
            header_idx = None
            for idx, head in enumerate(ana_values[4], start=1):
                if str(head).strip() == header:
                    header_idx = idx
                    break
            if header_idx is None:
                diffs.append((row_num, row_snapshot["name"], header, "[SÜTUN YOK]", row_snapshot["values"][header]))
                continue
            current = row[header_idx - 1] if len(row) >= header_idx else ""
            before = row_snapshot["values"][header]
            if str(current) != str(before):
                diffs.append((row_num, row_snapshot["name"], header, current, before))

    if diffs:
        for row_num, name, header, current, before in diffs:
            print(
                f"  [DEĞİŞMİŞ] Satır {row_num} | {name} | {header} | Önce={before!r} | Sonra={current!r}"
            )
        raise SystemExit(3)

    print("  5P, 6P, Portföy ve diğer hedef dışı sütunlarda değişiklik yok.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["step1", "step2", "step3", "step4", "step5"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.step == "step1":
        step1()
    elif args.step == "step2":
        step2()
    elif args.step == "step3":
        step3(apply_fix=args.apply)
    elif args.step == "step4":
        step4(apply_write=args.apply)
    elif args.step == "step5":
        step5()


if __name__ == "__main__":
    main()

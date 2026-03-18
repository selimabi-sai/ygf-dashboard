# -*- coding: utf-8 -*-
"""
YGF 6. Periyot → Dashboard Özet Screenshot → WhatsApp Gönder
=============================================================
1. Google Sheets'ten tüm yarışmacıların 6. Periyot hisselerini okur
2. Benzersiz hisse listesi çıkarır
3. SNAP Dashboard'u çalıştırıp her hisse için Özet ekran görüntüsü alır
4. WhatsApp'a gönderir

Windows Python ile çalıştırılmalıdır (Playwright browser desteği için).
"""

import sys
import os
import time
import json
import logging
import subprocess
import urllib.request
from pathlib import Path
from datetime import datetime

# ── YOLLAR (Windows) ──
_home = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
SNAP_DIR = _home / "Desktop" / "claude" / "snap code"
if not SNAP_DIR.exists():
    SNAP_DIR = _home / "Desktop" / "snap code"
YGF_DIR = _home / "Desktop" / "claude" / "YGF"
APP_PY = SNAP_DIR / "app.py"
DASH_URL = "http://localhost:8501"
SCREENSHOT_DIR = SNAP_DIR / "sabah_raporlari" / datetime.now().strftime("%Y-%m-%d")
CREDS = _home / "Desktop" / "snap code" / "credentials.json"
SHEET_ID = "1RvQnrukTy8LVxWjskFYUzlpCOuAqEU9IH7YTFM2XJQI"

sys.path.insert(0, str(SNAP_DIR))

import gspread
from google.oauth2.service_account import Credentials
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── LOG ──
LOG_DIR = SNAP_DIR / "loglar"
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"ygf_6p_screenshot_{datetime.now():%Y-%m-%d}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ygf_6p")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


# ═══════════════════════════════════════════════════════════
# ADIM 1: Google Sheets → 6P hisseleri
# ═══════════════════════════════════════════════════════════
def google_sheets_6p_hisseler():
    logger.info("Google Sheets'e bağlanılıyor...")
    creds = Credentials.from_service_account_file(str(CREDS), scopes=SCOPES)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    ws_list = ss.worksheets()

    tum_hisseler = []

    for idx in range(1, min(12, len(ws_list))):
        ws = ws_list[idx]
        vals = ws.get_all_values()

        blok_start = None
        blok_toplam = None
        for i, row in enumerate(vals):
            if "6. Periyot" in str(row[0]):
                blok_start = i
            if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                blok_toplam = i
                break

        if blok_start is None:
            logger.info(f"  {ws.title} - 6P blogu YOK, atlaniyor")
            continue

        data_start = blok_start + 2
        hisseler = []
        for r in range(data_start, blok_toplam):
            hisse = vals[r][0].strip()
            if hisse and hisse != "TOPLAM":
                hisseler.append(hisse)
                if hisse not in tum_hisseler:
                    tum_hisseler.append(hisse)

        logger.info(f"  {ws.title}: {len(hisseler)} hisse -> {', '.join(hisseler)}")

    logger.info(f"\nToplam benzersiz hisse: {len(tum_hisseler)}")
    logger.info(f"Hisseler: {', '.join(tum_hisseler)}")
    return tum_hisseler


# ═══════════════════════════════════════════════════════════
# ADIM 2: Dashboard yönetimi
# ═══════════════════════════════════════════════════════════
def dashboard_acik_mi():
    try:
        urllib.request.urlopen(DASH_URL, timeout=5)
        return True
    except Exception:
        return False


def dashboard_baslat():
    if dashboard_acik_mi():
        logger.info("Dashboard zaten calisiyor.")
        return None

    logger.info(f"Dashboard baslatiliyor: {APP_PY}")
    proc = subprocess.Popen(
        ["streamlit", "run", str(APP_PY), "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(APP_PY.parent),
    )
    for attempt in range(40):
        time.sleep(2)
        if dashboard_acik_mi():
            logger.info(f"Dashboard hazir! ({(attempt + 1) * 2} sn)")
            return proc
    logger.error("Dashboard 80 sn icinde hazir olmadi!")
    return proc


def dashboard_kapat(proc):
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=10)
        logger.info("Dashboard kapatildi.")
    except Exception:
        proc.kill()


# ═══════════════════════════════════════════════════════════
# ADIM 3: Screenshot al
# ═══════════════════════════════════════════════════════════
def hisse_screenshot_al(page, ticker):
    logger.info(f"  {ticker} ...")
    try:
        ozet_label = page.locator('[data-testid="stSidebar"] label:has-text("Özet")')
        if ozet_label.count() > 0:
            ozet_label.first.click()
            time.sleep(1)

        sidebar = page.locator('[data-testid="stSidebar"]')
        hisse_selectbox = sidebar.locator('div[data-testid="stSelectbox"]').first
        hisse_selectbox.click()
        time.sleep(0.5)

        active_input = page.locator('input[aria-expanded="true"]')
        if active_input.count() == 0:
            active_input = sidebar.locator('div[data-testid="stSelectbox"] input')
        active_input.first.fill("")
        time.sleep(0.2)
        active_input.first.fill(ticker)
        time.sleep(1.5)

        option = page.locator(f'li[role="option"]:has-text("{ticker}")')
        option.first.wait_for(state="visible", timeout=5000)
        option.first.click()
        time.sleep(0.5)

        logger.info(f"    Grafikler yukleniyor...")
        time.sleep(5)

        page.evaluate("""() => {
            const sb = document.querySelector('[data-testid="stSidebar"]');
            const btn = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
            const header = document.querySelector('[data-testid="stHeader"]');
            const deploy = document.querySelector('[data-testid="stToolbar"]');
            if (sb) sb.style.display = 'none';
            if (btn) btn.style.display = 'none';
            if (header) header.style.display = 'none';
            if (deploy) deploy.style.display = 'none';
        }""")
        time.sleep(0.3)

        page.evaluate("""() => {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        window.scrollTo(0, 0);
                        resolve();
                    }
                }, 200);
            });
        }""")
        time.sleep(2)

        content_height = page.evaluate("""() => {
            const main = document.querySelector('[data-testid="stMain"]')
                      || document.querySelector('.main');
            if (!main) return 2000;
            const children = main.querySelectorAll('div, svg, canvas, iframe');
            let maxBottom = 0;
            children.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.height > 0 && rect.bottom > maxBottom) {
                    maxBottom = rect.bottom;
                }
            });
            return Math.ceil(maxBottom) + 15;
        }""")
        page.set_viewport_size({"width": 1920, "height": max(content_height, 800)})
        time.sleep(1)

        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        ss_path = SCREENSHOT_DIR / f"{ticker}.png"
        page.screenshot(path=str(ss_path), full_page=True)

        try:
            from PIL import Image
            img = Image.open(str(ss_path))
            pixels = img.load()
            w, h = img.size
            bottom = h - 1
            for row in range(h - 1, 0, -1):
                is_blank = True
                for col in range(0, w, 20):
                    r, g, b = pixels[col, row][:3]
                    if not (r > 245 and g > 245 and b > 245):
                        is_blank = False
                        break
                if not is_blank:
                    bottom = row + 25
                    break
            if bottom < h - 10:
                img_cropped = img.crop((0, 0, w, min(bottom, h)))
                img_cropped.save(str(ss_path))
                logger.info(f"    Kirpildi: {h}px -> {min(bottom, h)}px")
        except Exception as crop_err:
            logger.warning(f"    Kirpma hatasi: {crop_err}")

        page.set_viewport_size({"width": 1920, "height": 1080})

        page.evaluate("""() => {
            const sb = document.querySelector('[data-testid="stSidebar"]');
            const btn = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
            const header = document.querySelector('[data-testid="stHeader"]');
            const deploy = document.querySelector('[data-testid="stToolbar"]');
            if (sb) sb.style.display = '';
            if (btn) btn.style.display = '';
            if (header) header.style.display = '';
            if (deploy) deploy.style.display = '';
        }""")

        logger.info(f"    OK: {ss_path.name}")
        return ss_path

    except Exception as e:
        logger.error(f"    HATA {ticker}: {e}")
        try:
            page.evaluate("""() => {
                const sb = document.querySelector('[data-testid="stSidebar"]');
                const btn = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
                const header = document.querySelector('[data-testid="stHeader"]');
                if (sb) sb.style.display = '';
                if (btn) btn.style.display = '';
                if (header) header.style.display = '';
            }""")
        except Exception:
            pass
        return None


def tum_screenshotlar_al(hisseler):
    if not hisseler:
        return []

    ayarlar_dosyasi = SNAP_DIR / "snap_ayarlar.json"
    try:
        ayarlar = json.loads(ayarlar_dosyasi.read_text(encoding="utf-8"))
    except Exception:
        ayarlar = {}
    ayarlar["ozet_metrikler"] = [
        "SATIŞLAR Y", "BRÜT KAR Y", "EFK Y",
        "NAKİT Y", "Net Borç", "ÖZKAYNAKLAR",
    ]
    ayarlar_dosyasi.write_text(
        json.dumps(ayarlar, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dosyalar = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080}, locale="tr-TR"
        )
        page = context.new_page()

        logger.info(f"Dashboard aciliyor: {DASH_URL}")
        page.goto(DASH_URL, wait_until="networkidle", timeout=60000)
        logger.info("Dashboard verisi yukleniyor...")
        time.sleep(12)

        try:
            page.wait_for_selector('[data-testid="stSidebar"]', timeout=30000)
            logger.info("Dashboard hazir!")
        except PlaywrightTimeout:
            logger.error("Dashboard yuklenemedi!")
            browser.close()
            return []

        page.evaluate("""() => {
            const style = document.createElement('style');
            style.textContent = `
                .main, [data-testid="stMain"],
                [data-testid="stAppViewContainer"],
                [data-testid="stVerticalBlock"],
                section.main, .block-container,
                [data-testid="stMainBlockContainer"] {
                    overflow: visible !important;
                    max-height: none !important;
                    height: auto !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        try:
            page.locator(
                '[data-testid="stSidebar"] div[data-testid="stSelectbox"]'
            ).first.wait_for(state="visible", timeout=15000)
        except Exception:
            time.sleep(5)

        for ticker in hisseler:
            path = hisse_screenshot_al(page, ticker)
            if not path:
                logger.info(f"  Tekrar deneniyor: {ticker}")
                time.sleep(5)
                page.reload(wait_until="networkidle", timeout=30000)
                time.sleep(8)
                path = hisse_screenshot_al(page, ticker)
            if path:
                dosyalar.append(path)
            time.sleep(1)

        browser.close()

    logger.info(f"Toplam {len(dosyalar)} screenshot -> {SCREENSHOT_DIR}")
    return dosyalar


# ═══════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═══════════════════════════════════════════════════════════
def main():
    logger.info("=" * 60)
    logger.info("YGF 6P -> Dashboard Ozet Screenshot -> WhatsApp")
    logger.info(f"Tarih: {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 60)

    # 1. Google Sheets'ten 6P hisseleri oku
    try:
        hisseler = google_sheets_6p_hisseler()
    except Exception as e:
        logger.error(f"Google Sheets hatasi: {e}")
        return

    if not hisseler:
        logger.info("6. Periyotta hisse bulunamadi.")
        return

    # 2. Dashboard baslat
    dash_proc = dashboard_baslat()
    if not dashboard_acik_mi():
        logger.error("Dashboard baslatilamadi!")
        return

    try:
        # 3. Screenshot al
        logger.info(f"\n{len(hisseler)} hisse icin dashboard screenshot alinacak...")
        dosyalar = tum_screenshotlar_al(hisseler)
        logger.info(f"\n{len(dosyalar)}/{len(hisseler)} screenshot alindi.")

        # 4. WhatsApp'a gonder
        if dosyalar:
            try:
                from whatsapp_gonder import whatsapp_gonder_tum
                logger.info("\nWhatsApp gonderimi basliyor...")
                sonuclar = whatsapp_gonder_tum(dosyalar=dosyalar, logger=logger)
                toplam = sum(len(v) for v in sonuclar.values())
                logger.info(f"WhatsApp: {toplam} dosya, {len(sonuclar)} aliciya gonderildi.")
            except ImportError:
                logger.warning("whatsapp_gonder modulu bulunamadi, gonderim atlandi.")
            except Exception as wa_err:
                logger.error(f"WhatsApp hatasi: {wa_err}")
        else:
            logger.warning("Gonderilecek screenshot yok!")

    finally:
        dashboard_kapat(dash_proc)

    logger.info("\n" + "=" * 60)
    logger.info("TAMAMLANDI")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

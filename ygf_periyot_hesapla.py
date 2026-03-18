#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YGF PERİYOT HESAPLAMA & GÜNCELLEME
Sai Amatör Yatırım — Selim Uysal, Mart 2026

İŞ AKIŞI:
  1. ygf_ayarlar.json'dan ayarları oku
  2. Excel dosyasından periyot başı/sonu fiyatları çek
  3. Her yarışmacının VERİ sayfasındaki portföyünü oku
  4. Getirileri hesapla
  5. Ana Sayfa + Yarışmacı sayfalarını güncelle
  6. İsteğe bağlı: Telegram/WhatsApp rapor gönder

KULLANIM:
  py ygf_periyot_hesapla.py                     → Sadece hesapla & güncelle
  py ygf_periyot_hesapla.py --rapor              → Hesapla + Telegram rapor
  py ygf_periyot_hesapla.py --rapor --whatsapp   → Hesapla + her iki rapor
"""

import os, sys, json, math, argparse, logging
from datetime import datetime, timedelta
from pathlib import Path

# ── AYARLAR ──────────────────────────────────────────────

AYARLAR_DOSYA = Path(__file__).parent / "ygf_ayarlar.json"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(Path(__file__).parent / "ygf_hesaplama.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("YGF_HESAP")


def ayarlari_yukle():
    if not AYARLAR_DOSYA.exists():
        log.error(f"Ayar dosyası bulunamadı: {AYARLAR_DOSYA}")
        log.error("Önce ygf_telegram_bot.py çalıştırarak oluşturun.")
        sys.exit(1)
    with open(AYARLAR_DOSYA, "r", encoding="utf-8") as f:
        return json.load(f)


# ── PERİYOT TAKVİMİ ─────────────────────────────────────
# Başlangıç: 2 Ocak 2026 Cuma kapanış
# Her periyot: 14 takvim günü (Cuma kapanış → Cuma kapanış)
# Pazar günü yeni periyot "başlar", Cuma kapanış fiyatı referans

YARISMA_BASLANGIC = datetime(2026, 1, 2)  # İlk Cuma kapanış
PERIYOT_GUN = 14

def periyot_tarihleri(periyot_no: int) -> tuple[datetime, datetime]:
    """Periyot numarasından başlangıç ve bitiş Cuma tarihlerini hesapla."""
    basi = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * (periyot_no - 1))
    sonu = YARISMA_BASLANGIC + timedelta(days=PERIYOT_GUN * periyot_no)
    return basi, sonu

def aktif_periyot_bul() -> int:
    """Bugünün tarihine göre aktif periyot numarasını bul."""
    bugun = datetime.now()
    for p in range(1, 27):
        basi, sonu = periyot_tarihleri(p)
        if basi <= bugun < sonu:
            return p
    return 26  # Yıl sonuna yaklaşmışsa son periyot

def tum_periyot_takvimi() -> list[dict]:
    """Tüm yılın periyot takvimini döndür."""
    takvim = []
    bugun = datetime.now()
    for p in range(1, 27):
        basi, sonu = periyot_tarihleri(p)
        durum = "Tamamlandı" if sonu <= bugun else "Aktif" if basi <= bugun < sonu else "Bekliyor"
        takvim.append({
            "periyot": p,
            "basi": basi.strftime("%d.%m.%Y"),
            "sonu": sonu.strftime("%d.%m.%Y"),
            "basi_dt": basi,
            "sonu_dt": sonu,
            "durum": durum,
        })
    return takvim


# ── EXCEL FİYAT OKUMA ────────────────────────────────────

def fiyatlari_oku(excel_yolu: str, hisseler: list[str], 
                   basi_tarih: str, sonu_tarih: str) -> dict:
    """
    Excel dosyasından hisse fiyatlarını oku.
    
    Excel yapısı (beklenen):
      A sütunu: Tarih
      B sütunu: Hisse kodu (veya header'da hisse kodları, satırlarda tarihler)
    
    İki olası format:
      Format A: Her satır bir tarih, her sütun bir hisse (pivot tablo)
      Format B: Uzun format — Tarih | Hisse | Fiyat
    
    Returns: {"THYAO": {"basi": 320.50, "sonu": 335.20}, ...}
    """
    import pandas as pd
    
    log.info(f"📂 Excel okunuyor: {excel_yolu}")
    
    # Önce Excel'in yapısını anlamaya çalış
    try:
        df = pd.read_excel(excel_yolu)
    except Exception as e:
        log.error(f"Excel okuma hatası: {e}")
        return {}
    
    log.info(f"   Sütunlar: {list(df.columns)}")
    log.info(f"   Satır sayısı: {len(df)}")
    
    fiyatlar = {}
    
    # ── FORMAT A: Pivot (tarihler satırda, hisseler sütunda) ──
    # İlk sütun tarih ise ve diğer sütunlar hisse kodlarıysa
    ilk_sutun = df.columns[0]
    diger_sutunlar = list(df.columns[1:])
    
    # Hisse kodları sütun başlıklarında mı kontrol et
    hisse_sutunlari = [s for s in diger_sutunlar if str(s).upper() in [h.upper() for h in hisseler]]
    
    if hisse_sutunlari:
        log.info(f"   Format A tespit edildi (pivot). Eşleşen hisseler: {hisse_sutunlari}")
        
        # Tarihleri parse et
        df[ilk_sutun] = pd.to_datetime(df[ilk_sutun], dayfirst=True, errors="coerce")
        basi_dt = pd.to_datetime(basi_tarih, dayfirst=True)
        sonu_dt = pd.to_datetime(sonu_tarih, dayfirst=True)
        
        for hisse in hisseler:
            hisse_upper = hisse.upper()
            # Sütunu bul (büyük/küçük harf duyarsız)
            sutun = None
            for s in diger_sutunlar:
                if str(s).upper() == hisse_upper:
                    sutun = s
                    break
            
            if sutun is None:
                log.warning(f"   ⚠️ {hisse} sütunu bulunamadı")
                continue
            
            # En yakın tarihi bul
            basi_row = df.iloc[(df[ilk_sutun] - basi_dt).abs().argsort()[:1]]
            sonu_row = df.iloc[(df[ilk_sutun] - sonu_dt).abs().argsort()[:1]]
            
            basi_fiyat = basi_row[sutun].values[0]
            sonu_fiyat = sonu_row[sutun].values[0]
            
            if pd.notna(basi_fiyat) and pd.notna(sonu_fiyat):
                fiyatlar[hisse_upper] = {
                    "basi": float(basi_fiyat),
                    "sonu": float(sonu_fiyat),
                }
                log.info(f"   ✅ {hisse}: {basi_fiyat:.2f} → {sonu_fiyat:.2f}")
    else:
        # ── FORMAT B: Uzun format (Tarih | Hisse | Fiyat) ──
        log.info("   Format B tespit edildi (uzun format). Hisse sütunu aranıyor...")
        
        # Hisse kodu ve fiyat sütunlarını bulmaya çalış
        hisse_col = None
        fiyat_col = None
        tarih_col = ilk_sutun
        
        for col in df.columns:
            col_str = str(col).lower()
            if any(k in col_str for k in ["hisse", "ticker", "kod", "sembol"]):
                hisse_col = col
            elif any(k in col_str for k in ["fiyat", "kapanış", "close", "price", "son"]):
                fiyat_col = col
        
        if hisse_col and fiyat_col:
            df[tarih_col] = pd.to_datetime(df[tarih_col], dayfirst=True, errors="coerce")
            basi_dt = pd.to_datetime(basi_tarih, dayfirst=True)
            sonu_dt = pd.to_datetime(sonu_tarih, dayfirst=True)
            
            for hisse in hisseler:
                hisse_df = df[df[hisse_col].str.upper() == hisse.upper()]
                if hisse_df.empty:
                    log.warning(f"   ⚠️ {hisse} verisi bulunamadı")
                    continue
                
                basi_row = hisse_df.iloc[(hisse_df[tarih_col] - basi_dt).abs().argsort()[:1]]
                sonu_row = hisse_df.iloc[(hisse_df[tarih_col] - sonu_dt).abs().argsort()[:1]]
                
                basi_fiyat = basi_row[fiyat_col].values[0]
                sonu_fiyat = sonu_row[fiyat_col].values[0]
                
                if pd.notna(basi_fiyat) and pd.notna(sonu_fiyat):
                    fiyatlar[hisse.upper()] = {
                        "basi": float(basi_fiyat),
                        "sonu": float(sonu_fiyat),
                    }
                    log.info(f"   ✅ {hisse}: {basi_fiyat:.2f} → {sonu_fiyat:.2f}")
        else:
            log.error("   ❌ Excel formatı tanınamadı. Sütunları kontrol edin.")
            log.error(f"      Sütunlar: {list(df.columns)}")
    
    log.info(f"📊 Toplam {len(fiyatlar)} hisse fiyatı okundu")
    return fiyatlar


# ── GETİRİ HESAPLAMA ─────────────────────────────────────

def getiri_hesapla(portfoy: list[dict], fiyatlar: dict) -> dict:
    """
    Portföy getirisi hesapla.
    
    portfoy: [{"hisse": "THYAO", "agirlik": 30, "lot": 100}, ...]
    fiyatlar: {"THYAO": {"basi": 320, "sonu": 335}, ...}
    
    Returns: {
        "toplam_getiri": 5.52,
        "hisseler": [
            {"hisse": "THYAO", "agirlik": 30, "basi": 320, "sonu": 335, 
             "getiri": 4.69, "katki": 1.41},
            ...
        ]
    }
    """
    toplam_getiri = 0
    detaylar = []
    
    for p in portfoy:
        hisse = p["hisse"].upper()
        agirlik = p["agirlik"]
        
        if hisse not in fiyatlar:
            log.warning(f"   ⚠️ {hisse} fiyatı bulunamadı, atlanıyor")
            detaylar.append({
                "hisse": hisse, "agirlik": agirlik,
                "basi": None, "sonu": None, "getiri": 0, "katki": 0,
                "hata": "Fiyat bulunamadı"
            })
            continue
        
        basi = fiyatlar[hisse]["basi"]
        sonu = fiyatlar[hisse]["sonu"]
        getiri = ((sonu - basi) / basi) * 100
        katki = getiri * (agirlik / 100)
        
        toplam_getiri += katki
        detaylar.append({
            "hisse": hisse, "agirlik": agirlik,
            "basi": basi, "sonu": sonu,
            "getiri": round(getiri, 2),
            "katki": round(katki, 2),
        })
    
    return {
        "toplam_getiri": round(toplam_getiri, 2),
        "hisseler": detaylar,
    }


# ── GOOGLE SHEETS GÜNCELLEME ─────────────────────────────

def sheets_baglantisi(ayarlar):
    """Google Sheets bağlantısı kur."""
    import gspread
    from google.oauth2.service_account import Credentials
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        ayarlar["credentials_json"], scopes=scopes
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(ayarlar["google_sheet_id"])


def veri_sayfasindan_portfoy_oku(sh, ad: str, periyot: int) -> list[dict]:
    """VERİ sayfasından yarışmacının portföyünü oku."""
    ws = sh.worksheet("VERİ")
    tum_veri = ws.get_all_values()
    
    portfoy = []
    for row in tum_veri:
        if len(row) >= 5 and row[1] == ad and f"{periyot}. Periyot" in row[2]:
            agirlik_str = row[4].replace("%", "").replace(",", ".").strip()
            try:
                agirlik = float(agirlik_str)
            except ValueError:
                continue
            portfoy.append({"hisse": row[3].upper(), "agirlik": agirlik})
    
    return portfoy


def ana_sayfayi_guncelle(sh, sonuclar: dict, periyot: int):
    """Ana Sayfa sıralama tablosunu güncelle."""
    ws = sh.worksheet("Ana Sayfa")
    
    # Mevcut verileri oku (satır 6-20 arası)
    tum_veri = ws.get_all_values()
    
    for ad, sonuc in sonuclar.items():
        # Yarışmacıyı bul
        for i, row in enumerate(tum_veri):
            if len(row) > 1 and row[1] == ad:
                satir = i + 1  # 1-indexed
                
                # Periyot getirisi (sütun 5+periyot-1 = E,F,G,H,I)
                periyot_sutun = 4 + periyot  # E=5, F=6, ...
                ws.update_cell(satir, periyot_sutun, sonuc["toplam_getiri"] / 100)
                
                log.info(f"   ✅ Ana Sayfa: {ad} → Periyot {periyot}: %{sonuc['toplam_getiri']:.2f}")
                break


def yarismaci_sayfasini_guncelle(sh, ad: str, periyot: int, sonuc: dict):
    """Yarışmacı sayfasına fiyat ve getiri verilerini yaz."""
    try:
        ws = sh.worksheet(ad)
        
        # Periyot bloğunun veri başlangıcı
        blok_boyutu = 9
        baslangic = 5 + (periyot - 1) * blok_boyutu
        veri_satir = baslangic + 2
        
        for i, h in enumerate(sonuc["hisseler"]):
            if i >= 5:
                break
            satir = veri_satir + i
            
            if h.get("basi") is not None:
                ws.update_cell(satir, 4, h["basi"])    # P.Başı Fiyat
                ws.update_cell(satir, 5, h["sonu"])    # P.Sonu Fiyat
                ws.update_cell(satir, 6, h["getiri"] / 100)  # Getiri %
                ws.update_cell(satir, 7, h["katki"] / 100)   # Katkı %
        
        # Toplam satırı
        toplam_satir = veri_satir + 5
        ws.update_cell(toplam_satir, 6, sonuc["toplam_getiri"] / 100)
        
        log.info(f"   ✅ {ad} sayfası güncellendi")
    except Exception as e:
        log.error(f"   ❌ {ad} sayfası güncelleme hatası: {e}")


# ── RAPOR OLUŞTURMA ──────────────────────────────────────

def rapor_olustur(sonuclar: dict, periyot: int) -> str:
    """Periyot sonu rapor metni oluştur."""
    siralama = sorted(sonuclar.items(), key=lambda x: x[1]["toplam_getiri"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    
    satirlar = [
        f"🏆 *YGF — {periyot}. Periyot Sonuçları*",
        f"📅 {datetime.now().strftime('%d.%m.%Y')}\n",
        "─" * 30,
    ]
    
    for i, (ad, sonuc) in enumerate(siralama):
        medal = medals[i] if i < 3 else f"{i+1:2d}."
        getiri = sonuc["toplam_getiri"]
        emoji = "📈" if getiri > 0 else "📉"
        satirlar.append(f"{medal} *{ad}*  →  {emoji} %{getiri:.2f}")
        
        # En iyi hisse
        en_iyi = max(sonuc["hisseler"], key=lambda h: h.get("getiri", 0))
        if en_iyi.get("getiri", 0) != 0:
            satirlar.append(f"     En iyi: {en_iyi['hisse']} (%{en_iyi['getiri']:.1f})")
    
    satirlar.append("\n─" * 30)
    
    # Genel istatistikler
    getiriler = [s["toplam_getiri"] for _, s in siralama]
    karli = len([g for g in getiriler if g > 0])
    satirlar.append(f"\n📊 Kârlı: {karli}/{len(getiriler)}")
    satirlar.append(f"📈 Ortalama: %{sum(getiriler)/len(getiriler):.2f}")
    satirlar.append(f"🏆 En iyi: %{max(getiriler):.2f}")
    satirlar.append(f"💀 En kötü: %{min(getiriler):.2f}")
    satirlar.append(f"\n_Sai Amatör Yatırım — YGF 2026_")
    
    return "\n".join(satirlar)


async def telegram_rapor_gonder(ayarlar, rapor_metni: str):
    """Telegram'a rapor gönder."""
    from telegram import Bot
    
    bot = Bot(token=ayarlar["telegram_bot_token"])
    admin_id = ayarlar["admin_telegram_id"]
    
    if admin_id:
        await bot.send_message(
            chat_id=admin_id,
            text=rapor_metni,
            parse_mode="Markdown"
        )
        log.info("📨 Telegram raporu gönderildi")


# ── ANA FONKSİYON ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YGF Periyot Hesaplama")
    parser.add_argument("--rapor", action="store_true", help="Telegram rapor gönder")
    parser.add_argument("--whatsapp", action="store_true", help="WhatsApp rapor gönder")
    parser.add_argument("--kuru-calistir", action="store_true", help="Sheets'e yazmadan test et")
    parser.add_argument("--periyot", type=int, default=0, help="Manuel periyot no (0=otomatik)")
    args = parser.parse_args()
    
    ayarlar = ayarlari_yukle()
    
    # Periyot otomatik hesapla veya manuel belirle
    if args.periyot > 0:
        periyot = args.periyot
    else:
        periyot = aktif_periyot_bul()
    
    basi_dt, sonu_dt = periyot_tarihleri(periyot)
    basi_tarih = basi_dt.strftime("%d.%m.%Y")
    sonu_tarih = sonu_dt.strftime("%d.%m.%Y")
    excel_yolu = ayarlar.get("excel_dosya_yolu", "")
    
    print("=" * 60)
    print("📊 YGF PERİYOT HESAPLAMA")
    print(f"   Periyot: {periyot}. Periyot")
    print(f"   Tarih aralığı: {basi_tarih} (Cuma) → {sonu_tarih} (Cuma)")
    print(f"   Bugün: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 60)
    
    # Takvim özeti
    takvim = tum_periyot_takvimi()
    log.info("📅 Periyot Takvimi:")
    for t in takvim:
        if t["durum"] != "Bekliyor" or t["periyot"] <= periyot + 2:
            isaret = " ◀" if t["periyot"] == periyot else ""
            log.info(f"   {t['periyot']:2d}P: {t['basi']} → {t['sonu']}  [{t['durum']}]{isaret}")
    
    # 1. Google Sheets bağlan
    log.info("📡 Google Sheets'e bağlanılıyor...")
    sh = sheets_baglantisi(ayarlar)
    log.info("   ✅ Bağlantı kuruldu")
    
    # 2. Her yarışmacının portföyünü oku
    yarismaci_isimleri = list(set(ayarlar.get("yarismacilar", {}).values()))
    log.info(f"\n👥 {len(yarismaci_isimleri)} yarışmacı işlenecek")
    
    tum_hisseler = set()
    yarismaci_portfoyleri = {}
    
    for ad in yarismaci_isimleri:
        portfoy = veri_sayfasindan_portfoy_oku(sh, ad, periyot)
        if portfoy:
            yarismaci_portfoyleri[ad] = portfoy
            for p in portfoy:
                tum_hisseler.add(p["hisse"])
            log.info(f"   📋 {ad}: {len(portfoy)} hisse — {', '.join(p['hisse'] for p in portfoy)}")
        else:
            log.warning(f"   ⚠️ {ad}: Portföy bulunamadı (Periyot {periyot})")
    
    if not tum_hisseler:
        log.error("❌ Hiçbir yarışmacı için portföy bulunamadı!")
        return
    
    # 3. Excel'den fiyatları oku
    log.info(f"\n📂 Fiyatlar okunuyor: {excel_yolu}")
    fiyatlar = fiyatlari_oku(excel_yolu, list(tum_hisseler), basi_tarih, sonu_tarih)
    
    if not fiyatlar:
        log.error("❌ Hiç fiyat okunamadı! Excel dosyasını kontrol edin.")
        return
    
    # 4. Getiri hesapla
    log.info(f"\n📊 Getiriler hesaplanıyor...")
    sonuclar = {}
    
    for ad, portfoy in yarismaci_portfoyleri.items():
        sonuc = getiri_hesapla(portfoy, fiyatlar)
        sonuclar[ad] = sonuc
        log.info(f"   {ad}: %{sonuc['toplam_getiri']:.2f}")
    
    # 5. Sheets güncelle
    if not args.kuru_calistir:
        log.info(f"\n📝 Google Sheets güncelleniyor...")
        ana_sayfayi_guncelle(sh, sonuclar, periyot)
        
        for ad, sonuc in sonuclar.items():
            yarismaci_sayfasini_guncelle(sh, ad, periyot, sonuc)
    else:
        log.info("\n🔄 Kuru çalıştırma modu — Sheets güncellenmedi")
    
    # 6. Rapor
    rapor = rapor_olustur(sonuclar, periyot)
    print("\n" + rapor)
    
    if args.rapor:
        import asyncio
        asyncio.run(telegram_rapor_gonder(ayarlar, rapor))
    
    print("\n" + "=" * 60)
    print("✅ İşlem tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()

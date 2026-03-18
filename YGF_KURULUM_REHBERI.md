# YGF — Yatırım Getiri Farkı Yarışma Sistemi
## Kurulum ve Kullanım Rehberi

---

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `YGF_Sablon.xlsx` | Google Sheets'e yüklenecek yapı şablonu (15 sayfa) |
| `ygf_telegram_bot.py` | Telegram botu — yarışmacı portföy girişi |
| `ygf_periyot_hesapla.py` | Periyot sonu hesaplama & güncelleme scripti |
| `ygf_ayarlar.json` | Tüm ayarlar (bot ilk çalışmada oluşturur) |
| `ygf_dashboard.py` | Streamlit dashboard — SNAP tarzı koyu tema, Sheets'ten canlı veri |
| `ygf_dashboard.jsx` | React dashboard (Claude artifact olarak çalışıyor) |

---

## Kurulum Adımları

### 1. Google Sheets Yapısı

**a)** `YGF_Sablon.xlsx` dosyasını Google Drive'a yükle → "Google E-Tablolar olarak aç"

**b)** Sheet'i service account ile paylaş:
- Sağ üst "Paylaş" → service account e-postanı ekle (snap-works JSON'daki `client_email`)
- "Düzenleyici" yetkisi ver

**c)** Sayfalar:
- **Ana Sayfa** — Sıralama tablosu (otomatik güncellenir)
- **Barış, Serkan, Ali Cenk...** — Her yarışmacının portföy detayı
- **VERİ** — Telegram bot ham verileri buraya yazar
- **AYARLAR** — Script konfigürasyonu
- **Rozetler** — Ödül sistemi açıklamaları

### 2. Telegram Bot Kurulumu

**a)** BotFather'dan yeni bot oluştur:
- Telegram'da @BotFather'a `/newbot` yaz
- Bot adı: `YGF Yarışma Bot` (veya istediğin)
- Token'ı kopyala

**b)** Kütüphaneleri kur:
```
pip install python-telegram-bot gspread google-auth pandas openpyxl
```

**c)** Bot'u ilk kez çalıştır (ayar dosyasını oluşturur):
```
cd /d "%USERPROFILE%\Desktop\claude\ygf"
```
```
py ygf_telegram_bot.py
```

**d)** `ygf_ayarlar.json` dosyasını düzenle:
- `telegram_bot_token` → BotFather'dan aldığın token
- `admin_telegram_id` → Senin Telegram numeric ID'n
- `yarismacilar` → Her yarışmacının Telegram kullanıcı adı eşleştirmesi
- `credentials_json` → Service account JSON yolu
- `google_sheet_id` → Sheet ID'si (URL'deki uzun kod)
- `excel_dosya_yolu` → Fiyat çektiğin Excel'in tam yolu

**e)** Tekrar çalıştır:
```
py ygf_telegram_bot.py
```

### 3. Periyot Sonu Hesaplama

Periyot takvimi otomatik hesaplanır (2 Ocak 2026 başlangıç, 14 günlük Cuma→Cuma). Elle tarih girmeye gerek yok.

Her 15 günde bir, periyot kapandığında (Cuma akşamı):

```
cd /d "%USERPROFILE%\Desktop\claude\ygf"
```
```
py ygf_periyot_hesapla.py
```

Telegram raporu da göndermek için:
```
py ygf_periyot_hesapla.py --rapor
```

Belirli bir periyodu hesaplamak için (örn. 5. periyot):
```
py ygf_periyot_hesapla.py --periyot 5
```

Test amaçlı (Sheets'e yazmadan):
```
py ygf_periyot_hesapla.py --kuru-calistir
```

---

### 4. Streamlit Dashboard

SNAP Dashboard ile aynı koyu lacivert tema. Google Sheets'ten canlı veri çeker.

```
cd /d "%USERPROFILE%\Desktop\claude\ygf"
```
```
streamlit run ygf_dashboard.py
```

5 sekmesi var: Genel Bakış (sıralama + grafikler), Yarışmacı Detay (radar + KPI + periyot karşılaştırma), Karşılaştırma (5'e kadar seç), İstatistikler (en iyi/kötü performanslar), Takvim (26 periyotluk tam takvim).

Veri 5 dakika cache'lenir, sağ üstteki 🔄 butonu ile anında yenilenebilir.

---

## Periyot Takvimi (Otomatik)

Başlangıç: 2 Ocak 2026 Cuma kapanış. Her periyot 14 takvim günü.
Script bugünün tarihine bakarak aktif periyodu otomatik belirler.

```
 1P: 02.01 → 16.01    8P: 10.04 → 24.04   15P: 17.07 → 31.07
 2P: 16.01 → 30.01    9P: 24.04 → 08.05   16P: 31.07 → 14.08
 3P: 30.01 → 13.02   10P: 08.05 → 22.05   17P: 14.08 → 28.08
 4P: 13.02 → 27.02   11P: 22.05 → 05.06   18P: 28.08 → 11.09
 5P: 27.02 → 13.03   12P: 05.06 → 19.06   19P: 11.09 → 25.09
 6P: 13.03 → 27.03   13P: 19.06 → 03.07   20P: 25.09 → 09.10
 7P: 27.03 → 10.04   14P: 03.07 → 17.07   ...26P: 18.12 → 01.01
```

---

## İş Akışı (Her 15 Günde Bir)

```
1. Yarışmacılar Telegram'dan portföy gönderir
       ↓
2. Bot parse eder → VERİ sayfasına + kişisel sayfaya yazar
       ↓
3. Periyot kapanınca: fiyat Excel'in güncellenir (mevcut iş akışı)
       ↓
4. ygf_periyot_hesapla.py çalıştırılır
       ↓
5. Excel'den fiyatları okur → getiri hesaplar
       ↓
6. Ana Sayfa + yarışmacı sayfalarını günceller
       ↓
7. Streamlit dashboard otomatik güncellenir (cache yenile)
       ↓
8. Telegram/WhatsApp raporu gönderir (opsiyonel)
```

---

## Telegram Bot Mesaj Formatları

**Yarışmacı portföy gönderimi:**
```
THYAO 30
EREGL 25
SASA 20
TUPRS 25
```

veya: `THYAO 30, EREGL 25, SASA 20, TUPRS 25`

**Admin başkası adına giriş:**
```
Barış: THYAO 30, EREGL 25, SASA 20, TUPRS 25
```

**Bot komutları:**
- `/start` — Bilgi
- `/siralama` — Güncel sıralama
- `/periyot` — Aktif periyot
- `/periyot_ayarla 6` — Periyotu değiştir (admin)
- `/yardim` — Komut listesi

---

## Rozet Sistemi

| Rozet | Koşul |
|-------|-------|
| 🥇 Periyot Şampiyonu | O periyotta en yüksek getiri |
| 📈 BIST Avcısı | BIST 100'den yüksek getiri |
| 🏦 Faiz Yeneni | Mevduat faizinden yüksek kümülatif getiri |
| 🎯 Tutarlılık Ödülü | En düşük volatilite + pozitif getiri |
| ⭐ 5'te 5 | Tüm periyotlarda pozitif |
| 🛡️ Savunma Ustası | En düşük max drawdown |
| 🚀 Roketçi | Tek periyotta %15+ getiri |
| 👑 Genel Şampiyon | Yıl sonu en yüksek portföy değeri |

---

## Notlar

- **Service account**: SNAP dashboard ile aynı credentials kullanılabilir
- **Excel formatı**: Script iki format tanır (pivot ve uzun). İlk çalıştırmada logları kontrol et
- **Google Sheets API limiti**: Dakikada ~60 istek. 11 yarışmacı için yeterli
- **Bot güvenliği**: Sadece tanımlı kullanıcılar portföy girebilir

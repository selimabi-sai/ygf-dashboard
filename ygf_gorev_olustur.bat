@echo off
chcp 65001 >nul 2>&1

echo YGF Task Scheduler gorevi olusturuluyor...

schtasks /create /tn "YGF Gunluk Guncelleme" /tr "python \"C:\Users\PDS\Desktop\claude\ygf\ygf_guncelle.py\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 19:00 /rl HIGHEST /f

if %ERRORLEVEL% EQU 0 (
    echo BASARILI: Gorev olusturuldu.
) else (
    echo HATA: Gorev olusturulamadi. Yonetici olarak calistirin.
)

echo.
echo Gorev detaylari:
schtasks /query /tn "YGF Gunluk Guncelleme" /fo LIST /v

pause

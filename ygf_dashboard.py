#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YGF DASHBOARD v2

streamlit run ygf_dashboard.py
"""

import json, math, re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ═══════════════════════════════════════════════
# RENKLER
# ═══════════════════════════════════════════════
BG      = "#060d16"
BG2     = "#0a1628"
SURFACE = "#111d32"
CARD    = "#152238"
BORDER  = "#1e3354"
TEXT    = "#e8edf5"
MUTED   = "#8899b4"
DIM     = "#556a8a"
GOLD    = "#f0b429"
GREEN   = "#22c55e"
RED     = "#ef4444"
BLUE    = "#3b82f6"
PURPLE  = "#a855f7"
CYAN    = "#06b6d4"
ACCENT  = "#4a9eff"

PAL = [GOLD, GREEN, BLUE, PURPLE, CYAN, RED, "#f97316", "#ec4899", "#14b8a6", "#a78bfa", "#fb923c"]

# ═══════════════════════════════════════════════
# PERİYOT TAKVİMİ
# ═══════════════════════════════════════════════
YB = datetime(2026, 1, 2)
PG = 14

def p_tarih(p):
    return YB + timedelta(days=PG*(p-1)), YB + timedelta(days=PG*p)

def aktif_p():
    n = datetime.now()
    for p in range(1, 27):
        b, s = p_tarih(p)
        if b <= n < s:
            return p
    return 26

# ═══════════════════════════════════════════════
# SAYFA AYARLARI
# ═══════════════════════════════════════════════
st.set_page_config(page_title="YGF Dashboard", page_icon="🏆", layout="wide",
                   initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════
# ŞİFRE KORUMASI
# ═══════════════════════════════════════════════
def sifre_kontrol():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.markdown(f"""<style>.stApp {{ background-color: {BG}; }}</style>""", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:70vh;">
        <div style="text-align:center;">
            <div style="font-size:64px;font-weight:900;
            background:linear-gradient(135deg,{GOLD},{GREEN});
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            margin-bottom:8px;">YGF</div>
            <div style="color:{DIM};font-size:13px;margin-bottom:24px;">Giriş yapın</div>
        </div>
    </div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        sifre = st.text_input("Şifre", type="password", label_visibility="collapsed", placeholder="Şifre girin...")
        if sifre:
            if sifre == "ygf2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Yanlış şifre")
    return False

if not sifre_kontrol():
    st.stop()

st.markdown(f"""<style>
.stApp {{ background-color: {BG}; }}
[data-testid="stSidebar"] {{ background-color: {SURFACE}; }}
h1,h2,h3 {{ color: {TEXT} !important; }}
p,span,label {{ color: {MUTED}; }}
.stSelectbox label,.stRadio label {{ color: {MUTED} !important; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: {SURFACE}; border-radius: 8px; padding: 4px; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; color: {MUTED}; border-radius: 6px; padding: 8px 16px; font-weight: 500; }}
.stTabs [aria-selected="true"] {{ background: {ACCENT}33; color: {TEXT}; border: 1px solid {ACCENT}55; }}
.block-container {{ padding-top: 2.5rem; }}
header[data-testid="stHeader"] {{ background: {BG}; }}
div[data-testid="stMetricDelta"] > div {{ font-size: 13px; }}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# YARDIMCI
# ═══════════════════════════════════════════════
BENCHMARKS = {"Faiz", "BIST 100", "USDTRY"}
AYAR = Path(__file__).parent / "ygf_ayarlar.json"

def pf(v):
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip().replace("%", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def pf_yerel(v):
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip()
    s = s.replace("₺", "").replace("TL", "").replace("%", "").replace("\xa0", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def fmt_tr(v, digits=2):
    if v is None:
        return "—"
    s = f"{v:,.{digits}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")

def renk(v):
    if v is None: return MUTED
    return GREEN if v > 0 else RED if v < 0 else MUTED

def plotly_layout(title="", height=320):
    return dict(
        title=dict(text=title, font=dict(size=13, color=TEXT, family="Segoe UI")),
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        font=dict(color=MUTED, size=10),
        height=height, margin=dict(l=35, r=15, t=35, b=35),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
    )

def kpi_card(icon, label, value, sub="", color=TEXT):
    return f"""<div style="background:linear-gradient(135deg,{CARD},{SURFACE});
    border:1px solid {BORDER};border-radius:10px;padding:16px 14px;text-align:center;">
    <div style="font-size:22px;">{icon}</div>
    <div style="font-size:10px;color:{DIM};text-transform:uppercase;letter-spacing:1px;margin:4px 0 2px;">{label}</div>
    <div style="font-size:22px;font-weight:700;font-family:Consolas,monospace;color:{color};">{value}</div>
    <div style="font-size:11px;color:{MUTED};margin-top:2px;">{sub}</div></div>"""

def hucre(vals, row_no, col_no):
    if not vals or row_no < 1 or col_no < 1 or row_no > len(vals):
        return None
    row = vals[row_no - 1]
    if col_no > len(row):
        return None
    return row[col_no - 1]

def gram_altin_baz_fiyat(usdtry_vals):
    if not usdtry_vals:
        return None

    v = pf_yerel(hucre(usdtry_vals, 4, 10))
    if v is not None:
        return v

    for r_idx, row in enumerate(usdtry_vals):
        for c_idx, cell in enumerate(row):
            metin = str(cell).strip().casefold()
            if "gram alt" not in metin:
                continue
            for offset in (1, 2, 3):
                rr = r_idx + offset
                if rr >= len(usdtry_vals):
                    continue
                hedef_row = usdtry_vals[rr]
                if c_idx < len(hedef_row):
                    v = pf_yerel(hedef_row[c_idx])
                    if v is not None:
                        return v
                for col_idx in range(len(hedef_row) - 1, -1, -1):
                    v = pf_yerel(hedef_row[col_idx])
                    if v is not None:
                        return v
    return None

@st.cache_data(ttl=900)
def google_finance_gram_altin_fiyat(baz_fiyat=None):
    try:
        req = Request(
            "https://www.google.com/finance/quote/XAUTRY:CUR?hl=tr",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "tr-TR,tr;q=0.9",
            },
        )
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", "ignore")
    except Exception:
        return None

    fiyatlar = re.findall(r'<div class="YMlKec">([^<]+)', html)
    if not fiyatlar:
        return None

    sayac = Counter(fiyatlar)
    hedef = baz_fiyat * 1.10 if baz_fiyat else 6500.0
    adaylar = []
    for raw in fiyatlar:
        val = pf_yerel(raw)
        if val is None:
            continue
        adaylar.append({
            "raw": raw,
            "val": val,
            "count": sayac[raw],
            "is_try": ("₺" in raw) or ("TL" in raw),
        })

    tercihler = [
        [a for a in adaylar if (not a["is_try"]) and a["count"] == 1 and 1000 <= a["val"] <= 10000],
        [a for a in adaylar if (not a["is_try"]) and 1000 <= a["val"] <= 10000],
        [a for a in adaylar if a["is_try"] and a["count"] == 1 and 1000 <= a["val"] <= 10000],
    ]
    for grup in tercihler:
        if grup:
            return min(grup, key=lambda a: abs(a["val"] - hedef))["val"]
    return None

def gram_altin_verisi(detay):
    usdtry_vals = detay.get("USDTRY") if detay else None
    baz = gram_altin_baz_fiyat(usdtry_vals)
    guncel = google_finance_gram_altin_fiyat(baz)
    endeks = (guncel / baz) * 100 if baz and guncel else None
    return baz, guncel, endeks

# ═══════════════════════════════════════════════
# VERİ YÜKLEME
# ═══════════════════════════════════════════════
def sheets_baglan():
    """Streamlit secrets (cloud) veya ygf_ayarlar.json (lokal) ile baglan."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
              "https://www.googleapis.com/auth/drive.readonly"]
    # 1) Streamlit Cloud (secrets.toml)
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
            sheet_id = st.secrets.get("sheets", {}).get("sheet_id", "")
            return gc.open_by_key(sheet_id)
    except Exception:
        pass
    # 2) Lokal (ygf_ayarlar.json)
    try:
        if AYAR.exists():
            with open(AYAR, "r", encoding="utf-8") as f:
                ayar = json.load(f)
            creds = Credentials.from_service_account_file(ayar["credentials_json"], scopes=scopes)
            gc = gspread.authorize(creds)
            return gc.open_by_key(ayar["google_sheet_id"])
    except Exception:
        pass
    return None

@st.cache_data(ttl=300)
def veri_yukle():
    try:
        sh = sheets_baglan()
        if sh is None:
            return None, None, None
        ana = sh.worksheet("Ana Sayfa").get_all_values()
        detay = {}
        for ws in sh.worksheets():
            if ws.title not in ("Ana Sayfa", "Hisse İcmal", "VERİ", "AYARLAR", "Rozetler"):
                try:
                    detay[ws.title] = ws.get_all_values()
                except Exception:
                    pass
        try:
            icmal_raw = sh.worksheet("Hisse İcmal").get_all_values()
        except Exception:
            icmal_raw = None
        return ana, detay, icmal_raw
    except Exception as e:
        st.error(f"Sheets hatasi: {e}")
        return None, None, None

def parse_ana(data):
    if not data or len(data) < 7:
        return pd.DataFrame(), []
    header = data[4]
    p_cols = []
    for i, h in enumerate(header):
        if h.endswith("P") and h[:-1].isdigit():
            p_cols.append((i, h))
    p_cols.sort(key=lambda x: int(x[1].replace("P", "")))

    rows = []
    for r in data[5:19]:
        if len(r) < 3 or not r[1].strip():
            continue
        d = {"sira": r[0], "isim": r[1], "portfoy": pf(r[2]),
             "vol": pf(r[3]), "poz": pf(r[4]), "maxdd": pf(r[5]), "alfa": pf(r[6])}
        for ci, lbl in p_cols:
            d[lbl] = pf(r[ci]) if ci < len(r) else None
        d["benchmark"] = r[1] in BENCHMARKS
        rows.append(d)
    return pd.DataFrame(rows), [lbl for _, lbl in p_cols]

def parse_icmal(raw):
    if not raw or len(raw) < 5:
        return {}
    header4 = raw[3]
    result = {}
    col = 0
    while col + 3 < len(header4):
        if header4[col] == "Hisse":
            p_name = raw[2][col] if col < len(raw[2]) else ""
            items = []
            for r in raw[4:]:
                if col >= len(r) or not r[col].strip():
                    continue
                items.append({
                    "hisse": r[col],
                    "tutar": pf(r[col+1]) or 0,
                    "kisi": int(pf(r[col+2]) or 0),
                    "pay": pf(r[col+3]) or 0,
                })
            if p_name:
                result[p_name] = items
        col += 4
    return result

def parse_yarismaci(vals, p_no):
    bloklar = {}
    for p in range(1, p_no + 1):
        baslik = "{}. Periyot".format(p)
        blok_start = blok_toplam = None
        for i, row in enumerate(vals):
            if baslik in str(row[0]):
                blok_start = i
            if blok_start is not None and i > blok_start + 1 and row[0] == "TOPLAM":
                blok_toplam = i
                break
        if blok_start is None or blok_toplam is None:
            continue
        hisseler = []
        for r in range(blok_start + 2, blok_toplam):
            h = vals[r][0].strip() if vals[r][0] else ""
            if not h:
                continue
            hisseler.append({
                "hisse": h, "agirlik": pf(vals[r][1]),
                "tl": pf(vals[r][2]) or 0,
                "getiri": pf(vals[r][5]), "katki": pf(vals[r][6]),
                "tutar": pf(vals[r][7]) if len(vals[r]) > 7 else None,
            })
        bloklar["{}P".format(p)] = {
            "hisseler": hisseler,
            "getiri": pf(vals[blok_toplam][5]),
            "tutar": pf(vals[blok_toplam][7]) if len(vals[blok_toplam]) > 7 else None,
        }
    return bloklar

# ═══════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════
ap = aktif_p()
ap_b, ap_s = p_tarih(ap)
gun_no = (datetime.now() - ap_b).days + 1

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"""<div style="padding:8px 0;">
    <span style="font-size:36px;font-weight:800;
    background:linear-gradient(90deg,{GOLD},{GREEN});-webkit-background-clip:text;
    -webkit-text-fill-color:transparent;">YGF</span>
    </div>""", unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""<div style="text-align:right;padding:8px 0;">
    <span style="color:{ACCENT};font-weight:600;">{ap}. Periyot</span>
    <span style="color:{DIM};font-size:12px;"> | {ap_b.strftime('%d.%m')} - {ap_s.strftime('%d.%m')} | Gun {gun_no}/{PG}</span>
    </div>""", unsafe_allow_html=True)

c1, c2 = st.columns([10, 1])
with c2:
    if st.button("🔄", help="Veriyi yenile"):
        st.cache_data.clear()
        st.rerun()

# ═══════════════════════════════════════════════
# VERİ
# ═══════════════════════════════════════════════
ana_raw, detay, icmal_raw = veri_yukle()
if ana_raw is None:
    st.error("Veri yuklenemedi.")
    st.stop()

df, p_labels = parse_ana(ana_raw)
if df.empty:
    st.error("Ana Sayfa parse edilemedi.")
    st.stop()

icmal = parse_icmal(icmal_raw) if icmal_raw else {}

dfY = df[~df["benchmark"]]
dfB = df[df["benchmark"]]
bist_row = df[df["isim"] == "BIST 100"].iloc[0] if "BIST 100" in df["isim"].values else None
faiz_row = df[df["isim"] == "Faiz"].iloc[0] if "Faiz" in df["isim"].values else None
usd_row = df[df["isim"] == "USDTRY"].iloc[0] if "USDTRY" in df["isim"].values else None
lider = dfY.sort_values("portfoy", ascending=False).iloc[0] if not dfY.empty else None
karda = len(dfY[dfY["portfoy"] > 100]) if not dfY.empty else 0
gram_baz, gram_guncel, gram_endeks = gram_altin_verisi(detay)

# ═══════════════════════════════════════════════
# SEKMELER
# ═══════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Genel Bakış", "👤 Katılımcılar", "📑 Seçimler", "📊 İstatistikler"])

# ═══════════════════════════════════════════════
# SEKME 1: GENEL BAKIŞ
# ═══════════════════════════════════════════════
with tab1:
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("🏆", "Lider", lider["isim"] if lider is not None else "—",
            f"Portföy: {lider['portfoy']:.2f}" if lider is not None else "", GOLD), unsafe_allow_html=True)
    with k2:
        bv = bist_row["portfoy"] if bist_row is not None else 0
        st.markdown(kpi_card("📈", "BIST 100", f"{bv:.2f}" if bv else "—",
            "", renk(bv-100 if bv else 0)), unsafe_allow_html=True)
    with k3:
        uv = usd_row["portfoy"] if usd_row is not None else 0
        st.markdown(kpi_card("💵", "USDTRY", f"{uv:.2f}" if uv else "—",
            "", renk(uv-100 if uv else 0)), unsafe_allow_html=True)
    with k4:
        fv = faiz_row["portfoy"] if faiz_row is not None else 0
        st.markdown(kpi_card("🏦", "Faiz", f"{fv:.2f}" if fv else "—",
            "", renk(fv-100 if fv else 0)), unsafe_allow_html=True)
    with k5:
        gram_value = f"{gram_endeks:.2f}" if gram_endeks is not None else "—"
        st.markdown(kpi_card("🥇", "Gram Altın", gram_value,
            "", renk(gram_endeks - 100 if gram_endeks is not None else 0)), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Sıralama tablosu
    tbl = f"""<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-family:Segoe UI,sans-serif;font-size:12px;">
    <thead><tr style="background:{BG2};color:{MUTED};font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">
    <th style="padding:8px 6px;text-align:center;border-bottom:2px solid {BORDER};">#</th>
    <th style="padding:8px 6px;text-align:left;border-bottom:2px solid {BORDER};">Katılımcı</th>
    <th style="padding:8px 6px;text-align:right;border-bottom:2px solid {BORDER};">Portföy</th>
    <th style="padding:8px 6px;text-align:right;border-bottom:2px solid {BORDER};">Vol.</th>
    <th style="padding:8px 6px;text-align:center;border-bottom:2px solid {BORDER};">Poz%</th>
    <th style="padding:8px 6px;text-align:right;border-bottom:2px solid {BORDER};">MaxDD</th>
    <th style="padding:8px 6px;text-align:right;border-bottom:2px solid {BORDER};">Alfa</th>"""
    for lbl in reversed(p_labels):
        tbl += f'<th style="padding:8px 4px;text-align:right;border-bottom:2px solid {BORDER};">{lbl}</th>'
    tbl += "</tr></thead><tbody>"

    for idx, row in df.iterrows():
        is_b = row["benchmark"]
        bg_row = f"{SURFACE}88" if is_b else "transparent"
        style_name = f"font-style:italic;color:{DIM};" if is_b else f"color:{TEXT};"
        sira_val = row["sira"]
        try:
            medal = str(int(float(sira_val)))
        except (ValueError, TypeError):
            medal = str(sira_val)
        pv = row["portfoy"]
        pv_c = renk(pv - 100 if pv else 0)

        tbl += f'<tr style="background:{bg_row};border-bottom:1px solid {BORDER}22;">'
        tbl += f'<td style="padding:6px;text-align:center;color:{DIM};">{medal}</td>'
        tbl += f'<td style="padding:6px;{style_name}">{row["isim"]}</td>'
        if pv:
            tbl += f'<td style="padding:6px;text-align:right;font-family:Consolas,monospace;color:{pv_c};font-weight:600;">{pv:.2f}</td>'
        else:
            tbl += f'<td style="padding:6px;text-align:right;color:{DIM};">—</td>'

        for col_name in ["vol", "poz", "maxdd", "alfa"]:
            v = row[col_name]
            if v is not None:
                c = renk(v) if col_name in ("maxdd", "alfa") else MUTED
                if col_name == "poz":
                    tbl += f'<td style="padding:6px;text-align:center;color:{MUTED};">{v:.0f}%</td>'
                else:
                    tbl += f'<td style="padding:6px;text-align:right;font-family:Consolas,monospace;color:{c};">{v:.2f}</td>'
            else:
                tbl += f'<td style="padding:6px;text-align:right;color:{DIM};">—</td>'

        for lbl in reversed(p_labels):
            v = row.get(lbl)
            if v is not None:
                c = renk(v)
                tbl += f'<td style="padding:6px;text-align:right;font-family:Consolas,monospace;color:{c};font-size:11px;">{v:+.2f}</td>'
            else:
                tbl += f'<td style="padding:6px;text-align:right;color:{DIM};font-size:11px;">—</td>'
        tbl += "</tr>"
    tbl += "</tbody></table></div>"
    st.markdown(tbl, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        dfS = df.copy()
        dfS["getiri"] = dfS["portfoy"].apply(lambda x: (x - 100) if x else 0)
        dfS = dfS.sort_values("getiri")
        colors = [MUTED if b else (GREEN if g >= 0 else RED) for b, g in zip(dfS["benchmark"], dfS["getiri"])]
        fig = go.Figure(go.Bar(y=dfS["isim"], x=dfS["getiri"], orientation="h",
            marker_color=colors, text=[f"{v:+.1f}%" for v in dfS["getiri"]],
            textposition="outside", textfont=dict(size=10, color=MUTED)))
        fig.update_layout(**plotly_layout("Toplam Getiri", 380))
        st.plotly_chart(fig, use_container_width=True)

    with gc2:
        top5 = dfY.sort_values("portfoy", ascending=False).head(5)
        fig2 = go.Figure()
        for ci, (_, row) in enumerate(top5.iterrows()):
            vals = [100]
            cum = 100
            for lbl in p_labels:
                v = row.get(lbl)
                if v is not None:
                    cum *= (1 + v / 100)
                vals.append(round(cum, 2))
            fig2.add_trace(go.Scatter(x=["Bas"] + p_labels, y=vals, name=row["isim"],
                mode="lines+markers", line=dict(color=PAL[ci], width=2), marker=dict(size=5)))
        if bist_row is not None:
            vals_b = [100]
            cum_b = 100
            for lbl in p_labels:
                v = bist_row.get(lbl)
                if v is not None:
                    cum_b *= (1 + v / 100)
                vals_b.append(round(cum_b, 2))
            fig2.add_trace(go.Scatter(x=["Bas"] + p_labels, y=vals_b, name="BIST 100",
                mode="lines", line=dict(color=MUTED, width=1.5, dash="dash")))
        fig2.update_layout(**plotly_layout("Kümülatif Performans (Top 5)", 380))
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════
# SEKME 2: YARIŞMACI PROFİLİ
# ═══════════════════════════════════════════════
with tab2:
    y_list = dfY["isim"].tolist()
    if not y_list:
        st.warning("Katılımcı bulunamadı.")
    else:
        secili = st.selectbox("Katılımcı seç", y_list, label_visibility="collapsed")
        row_y = df[df["isim"] == secili].iloc[0]

        sayfa_key = None
        for k in detay:
            if secili in k or k in secili:
                sayfa_key = k
                break
        bloklar = parse_yarismaci(detay[sayfa_key], ap) if sayfa_key else {}

        sira = row_y["sira"]
        try:
            sira_int = int(float(sira))
        except (ValueError, TypeError):
            sira_int = 0
        pv = row_y["portfoy"] or 100
        getiri = pv - 100
        bist_pv = bist_row["portfoy"] if bist_row is not None else 100
        bist_plus = pv - bist_pv

        st.markdown(f"""<div style="display:flex;align-items:center;gap:16px;padding:8px 0;">
        <div style="width:48px;height:48px;border-radius:50%;background:{PAL[sira_int%len(PAL)]}22;
        border:3px solid {PAL[sira_int%len(PAL)]};text-align:center;line-height:44px;font-size:20px;
        font-weight:700;color:{PAL[sira_int%len(PAL)]};">{secili[0]}</div>
        <div><span style="font-size:22px;font-weight:700;color:{TEXT};">{secili}</span>
        <span style="margin-left:12px;background:{GOLD}22;color:{GOLD};padding:2px 8px;border-radius:10px;font-size:11px;">#{sira_int}</span>
        <span style="margin-left:6px;background:{GREEN if bist_plus>=0 else RED}22;
        color:{GREEN if bist_plus>=0 else RED};padding:2px 8px;border-radius:10px;font-size:11px;">
        BIST {bist_plus:+.1f}</span></div></div>""", unsafe_allow_html=True)

        p_vals = [row_y.get(l) for l in p_labels if row_y.get(l) is not None]
        en_iyi = max(p_vals) if p_vals else 0
        en_kotu = min(p_vals) if p_vals else 0

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1:
            st.markdown(kpi_card("💰", "Portföy", f"{pv:.2f}", f"Getiri: {getiri:+.2f}%", renk(getiri)), unsafe_allow_html=True)
        with k2:
            son_p_val = row_y.get(f"{ap}P")
            son_p_g = float(son_p_val) if son_p_val is not None else 0
            st.markdown(kpi_card("📊", f"Aktif P.", f"{son_p_g:+.2f}%", f"{ap}P", renk(son_p_g)), unsafe_allow_html=True)
        with k3:
            st.markdown(kpi_card("⚡", "En İyi Periyot", f"{en_iyi:+.2f}%", "", GREEN), unsafe_allow_html=True)
        with k4:
            st.markdown(kpi_card("💀", "En Kötü Periyot", f"{en_kotu:+.2f}%", "", RED), unsafe_allow_html=True)
        with k5:
            vol = row_y["vol"]
            st.markdown(kpi_card("📉", "Volatilite", f"{vol:.2f}" if vol else "—", "", CYAN), unsafe_allow_html=True)
        with k6:
            mdd = row_y["maxdd"]
            st.markdown(kpi_card("🛡️", "Max DD", f"{mdd:.2f}%" if mdd else "—", "", RED), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        aktif_key = f"{ap}P"
        aktif_blok = bloklar.get(aktif_key)
        aktif_hisseler = []
        if aktif_blok and aktif_blok.get("hisseler"):
            aktif_hisseler = [h for h in aktif_blok["hisseler"] if h["hisse"] != "TOPLAM"][:7]

        g1, g2 = st.columns(2)
        with g1:
            fig3 = go.Figure()
            vals_y = [100]
            for lbl in p_labels:
                blok = bloklar.get(lbl)
                tutar = blok.get("tutar") if blok else None
                if tutar is not None:
                    vals_y.append(round(tutar, 2))
                    continue
                onceki = vals_y[-1]
                v = row_y.get(lbl)
                if v is not None:
                    onceki *= (1 + v / 100)
                vals_y.append(round(onceki, 2))
            fig3.add_trace(go.Scatter(x=["Bas"] + p_labels, y=vals_y, name=secili,
                mode="lines+markers", line=dict(color=GOLD, width=3), marker=dict(size=6)))
            for brow, bname, bcol in [(bist_row, "BIST 100", MUTED), (faiz_row, "Faiz", DIM), (usd_row, "USDTRY", CYAN)]:
                if brow is not None:
                    v_b = [100]
                    c_b = 100
                    for lbl in p_labels:
                        vv = brow.get(lbl)
                        if vv is not None:
                            c_b *= (1 + vv / 100)
                        v_b.append(round(c_b, 2))
                    fig3.add_trace(go.Scatter(x=["Bas"] + p_labels, y=v_b, name=bname,
                        mode="lines", line=dict(color=bcol, width=1.5, dash="dash")))
            fig3.update_layout(**plotly_layout("Kümülatif Performans", 320))
            st.plotly_chart(fig3, use_container_width=True)

            if aktif_hisseler:
                secim_tbl = f"""<div style="margin-top:10px;overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-family:Segoe UI,sans-serif;font-size:11px;">
                <thead><tr style="background:{BG2};color:{MUTED};font-size:10px;text-transform:uppercase;letter-spacing:0.5px;">
                <th style="padding:7px 8px;text-align:left;border-bottom:1px solid {BORDER};">Hisse</th>
                <th style="padding:7px 8px;text-align:right;border-bottom:1px solid {BORDER};">% Ağırlık</th>
                <th style="padding:7px 8px;text-align:right;border-bottom:1px solid {BORDER};">Son % Getiri</th>
                </tr></thead><tbody>"""
                for item in aktif_hisseler:
                    agirlik = item.get("agirlik")
                    getiri_h = item.get("getiri")
                    getiri_renk = renk(getiri_h if getiri_h is not None else 0)
                    agirlik_txt = f"{agirlik:.1f}%" if agirlik is not None else "—"
                    getiri_txt = f"{getiri_h:+.2f}%" if getiri_h is not None else "—"
                    secim_tbl += f"""<tr style="border-bottom:1px solid {BORDER}22;">
                    <td style="padding:7px 8px;color:{TEXT};font-weight:600;">{item['hisse']}</td>
                    <td style="padding:7px 8px;text-align:right;color:{MUTED};font-family:Consolas,monospace;">{agirlik_txt}</td>
                    <td style="padding:7px 8px;text-align:right;color:{getiri_renk};font-family:Consolas,monospace;font-weight:600;">{getiri_txt}</td>
                    </tr>"""
                secim_tbl += "</tbody></table></div>"
                st.markdown(secim_tbl, unsafe_allow_html=True)
            else:
                st.info("Aktif periyot secim verisi yok.")

        with g2:
            if aktif_hisseler:
                pie_data = [h for h in aktif_hisseler if h["tl"] and h["tl"] > 0]
                if pie_data:
                    pie_labels = [h["hisse"] for h in pie_data]
                    pie_values = [h["tl"] for h in pie_data]
                    fig4 = go.Figure(data=[go.Pie(
                        labels=pie_labels, values=pie_values,
                        hole=0.4, textinfo="label+percent",
                        textfont=dict(size=11, color="#e2e8f0"),
                    )])
                    fig4.update_layout(**plotly_layout("Son Periyot Portföy Dağılımı", 320))
                    fig4.update_layout(showlegend=False)
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Aktif periyotta portföy verisi yok.")
            else:
                st.info("Aktif periyotta portföy verisi yok.")
            karne = f"""<div style="margin-top:10px;overflow-x:auto;max-height:360px;">
            <table style="width:100%;font-size:11px;border-collapse:collapse;">
            <tr style="color:{MUTED};border-bottom:1px solid {BORDER};position:sticky;top:0;background:{CARD};">
            <th style="padding:4px;text-align:left;">Periyot</th><th style="padding:4px;text-align:right;">Getiri</th></tr>"""
            for p in range(1, 27):
                lbl = f"{p}P"
                v = row_y.get(lbl)
                aktif_satir = p == ap
                row_bg = f"background:{ACCENT}14;" if aktif_satir else ""
                if v is not None:
                    c = renk(v)
                    val_txt = f"{v:+.2f}%"
                else:
                    c = DIM
                    val_txt = "—"
                karne += f'<tr style="border-bottom:1px solid {BORDER}22;{row_bg}"><td style="padding:4px;color:{TEXT if aktif_satir else MUTED};">{lbl}</td><td style="padding:4px;text-align:right;font-family:Consolas;color:{c};font-weight:{"600" if aktif_satir else "400"};">{val_txt}</td></tr>'
            karne += "</table></div>"
            st.markdown(karne, unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# SEKME 3: HİSSE İCMAL
# ═══════════════════════════════════════════════
with tab3:
    if not icmal:
        st.warning("Seçim verisi bulunamadı.")
    else:
        p_options = list(icmal.keys())
        secili_p = st.radio("Periyot", p_options, horizontal=True, label_visibility="collapsed")
        items = icmal.get(secili_p, [])
        items_data = [i for i in items if i["hisse"] != "TOPLAM"]
        toplam_item = next((i for i in items if i["hisse"] == "TOPLAM"), None)

        toplam_tl = toplam_item["tutar"] if toplam_item else sum(i["tutar"] for i in items_data)
        toplam_hisse = len(items_data)

        k1, k2 = st.columns(2)
        with k1:
            st.markdown(kpi_card("📊", "Farklı Hisse", str(toplam_hisse), secili_p, BLUE), unsafe_allow_html=True)
        with k2:
            st.markdown(kpi_card("💰", "Toplam TL", f"{toplam_tl:,.0f}", f"{len(dfY)} katılımcı", GOLD), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        ig1, ig2 = st.columns([1, 1])
        with ig1:
            top8 = items_data[:8]
            diger_tl = sum(i["tutar"] for i in items_data[8:])
            labels = [i["hisse"] for i in top8]
            values = [i["tutar"] for i in top8]
            if diger_tl > 0:
                labels.append("Diğer")
                values.append(diger_tl)
            fig6 = go.Figure(go.Pie(labels=labels, values=values, hole=0.45,
                marker=dict(colors=PAL[:len(labels)]),
                textinfo="label+percent", textfont=dict(size=10, color=TEXT),
                insidetextorientation="radial"))
            fig6.update_layout(**plotly_layout(f"{secili_p} Hisse Dağılımı", 360))
            st.plotly_chart(fig6, use_container_width=True)

        with ig2:
            tbl_i = f"""<table style="width:100%;font-size:11px;border-collapse:collapse;">
            <tr style="color:{MUTED};border-bottom:2px solid {BORDER};font-size:10px;text-transform:uppercase;">
            <th style="padding:6px;text-align:left;">Hisse</th>
            <th style="padding:6px;text-align:right;">TL</th>
            <th style="padding:6px;text-align:center;">Kişi</th>
            <th style="padding:6px;text-align:left;">% Pay</th></tr>"""
            for ci, item in enumerate(items_data):
                pay = item["pay"]
                bar_w = min(pay * 3, 100)
                bar_c = PAL[ci % len(PAL)]
                tbl_i += f"""<tr style="border-bottom:1px solid {BORDER}22;">
                <td style="padding:5px;color:{TEXT};font-weight:500;">{item['hisse']}</td>
                <td style="padding:5px;text-align:right;font-family:Consolas;color:{MUTED};">{item['tutar']:.1f}</td>
                <td style="padding:5px;text-align:center;color:{MUTED};">{item['kisi']}</td>
                <td style="padding:5px;"><div style="display:flex;align-items:center;gap:6px;">
                <div style="width:{bar_w}%;height:8px;background:{bar_c};border-radius:4px;min-width:2px;"></div>
                <span style="color:{MUTED};font-size:10px;">{pay:.1f}</span></div></td></tr>"""
            tbl_i += "</table>"
            st.markdown(tbl_i, unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# SEKME 4: İSTATİSTİKLER
# ═══════════════════════════════════════════════
with tab4:
    perf_list = []
    for _, row in dfY.iterrows():
        for lbl in p_labels:
            v = row.get(lbl)
            if v is not None:
                perf_list.append({"isim": row["isim"], "periyot": lbl, "getiri": v})
    perf_df = pd.DataFrame(perf_list) if perf_list else pd.DataFrame()

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f'<div style="color:{GREEN};font-weight:600;font-size:14px;margin-bottom:8px;">🏆 En İyi 10 Performans</div>', unsafe_allow_html=True)
        if not perf_df.empty:
            top10 = perf_df.sort_values("getiri", ascending=False).head(10)
            html = ""
            for i, (_, r) in enumerate(top10.iterrows()):
                glow = f"text-shadow:0 0 8px {GREEN}66;" if i < 3 else ""
                html += f"""<div style="display:flex;justify-content:space-between;padding:6px 8px;
                border-bottom:1px solid {BORDER}22;"><span style="color:{TEXT};font-size:12px;">{r['isim']}
                <span style="color:{DIM};font-size:10px;">({r['periyot']})</span></span>
                <span style="font-family:Consolas;color:{GREEN};font-weight:600;font-size:13px;{glow}">{r['getiri']:+.2f}%</span></div>"""
            st.markdown(html, unsafe_allow_html=True)

    with s2:
        st.markdown(f'<div style="color:{RED};font-weight:600;font-size:14px;margin-bottom:8px;">💀 En Kötü 10 Performans</div>', unsafe_allow_html=True)
        if not perf_df.empty:
            bot10 = perf_df.sort_values("getiri").head(10)
            html = ""
            for i, (_, r) in enumerate(bot10.iterrows()):
                glow = f"text-shadow:0 0 8px {RED}66;" if i < 3 else ""
                html += f"""<div style="display:flex;justify-content:space-between;padding:6px 8px;
                border-bottom:1px solid {BORDER}22;"><span style="color:{TEXT};font-size:12px;">{r['isim']}
                <span style="color:{DIM};font-size:10px;">({r['periyot']})</span></span>
                <span style="font-family:Consolas;color:{RED};font-weight:600;font-size:13px;{glow}">{r['getiri']:+.2f}%</span></div>"""
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if bist_row is not None and not perf_df.empty:
        yenen, yenilen = [], []
        for lbl in p_labels:
            bv = bist_row.get(lbl)
            if bv is None:
                yenen.append(0); yenilen.append(0); continue
            y_c = sum(1 for _, yr in dfY.iterrows() if yr.get(lbl) is not None and yr.get(lbl) > bv)
            t_c = sum(1 for _, yr in dfY.iterrows() if yr.get(lbl) is not None)
            yenen.append(y_c); yenilen.append(t_c - y_c)

        fig7 = go.Figure()
        fig7.add_trace(go.Bar(x=p_labels, y=yenen, name="BIST'i Yenen", marker_color=GREEN, opacity=0.8))
        fig7.add_trace(go.Bar(x=p_labels, y=yenilen, name="BIST'e Yenilen", marker_color=RED, opacity=0.5))
        fig7.update_layout(**plotly_layout("BIST 100'ü Yenen Katılımcılar", 300))
        fig7.update_layout(barmode="group")
        st.plotly_chart(fig7, use_container_width=True)

# ═══════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════
st.markdown(f"""<div style="text-align:center;padding:20px 0;border-top:1px solid {BORDER};
margin-top:24px;color:{DIM};font-size:11px;">
YGF &copy; 2026</div>""", unsafe_allow_html=True)

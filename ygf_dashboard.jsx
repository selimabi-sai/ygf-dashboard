import { useState, useMemo } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend } from "recharts";

// ═══════════════════════════════════════════════════════════
// YGF YARIŞMA DASHBOARD — SNAP DARK THEME
// ═══════════════════════════════════════════════════════════

const COLORS = {
  bg: "#0F1923",
  surface: "#1A2744",
  card: "#1E293B",
  cardHover: "#253348",
  border: "#2D3F5A",
  text: "#E2E8F0",
  textMuted: "#94A3B8",
  textDim: "#64748B",
  gold: "#F59E0B",
  green: "#10B981",
  red: "#EF4444",
  blue: "#3B82F6",
  purple: "#8B5CF6",
  cyan: "#06B6D4",
  navy: "#1F4E79",
  accent: "#2E75B6",
};

const CHART_COLORS = ["#F59E0B", "#10B981", "#3B82F6", "#8B5CF6", "#06B6D4", "#EF4444", "#F97316", "#EC4899", "#14B8A6", "#A78BFA", "#FB923C", "#6366F1"];

// ── RAW DATA ──
const YARISMA_BASLANGIC = "2 Ocak 2026";
const ENDEKS_BASI = 11498.38;
const ENDEKS_SON = 13092.93;
const USD_BASI = 43.0375;
const USD_SON = 44.1887;
const FAIZ_BASI = 100;

const BENCHMARKS = {
  endeksGetiri: 13.87,
  usdGetiri: 2.67,
  faizGetiri: 7.12,
  periyotEndeks: -4.56,
  periyotUsd: 0.50,
  periyotFaiz: 1.42,
};

const PERIYOT_LABELS = ["1. Periyot", "2. Periyot", "3. Periyot", "4. Periyot", "5. Periyot"];

const YARISMACILAR = [
  { ad: "Barış", deger: 122.05, periyotlar: [11.72, 8.42, 2.58, -6.91, 5.52] },
  { ad: "Serkan", deger: 129.73, periyotlar: [17.01, 9.95, 3.18, -6.73, 4.78] },
  { ad: "Ali Cenk", deger: 122.14, periyotlar: [9.76, 10.72, 4.28, -5.80, 2.21] },
  { ad: "Özhan", deger: 130.47, periyotlar: [11.45, 16.75, 7.84, -8.20, 1.28] },
  { ad: "Turan", deger: 109.46, periyotlar: [3.78, 9.17, 5.09, -8.93, 0.94] },
  { ad: "Berkan", deger: 105.67, periyotlar: [7.66, 6.34, 0.62, -8.09, -0.20] },
  { ad: "Selim", deger: 107.95, periyotlar: [24.68, -6.73, 3.00, -7.74, -2.32] },
  { ad: "Gürkan", deger: 99.95, periyotlar: [19.61, -3.86, 1.32, -12.18, -2.32] },
  { ad: "Osman", deger: 98.51, periyotlar: [21.02, 0.22, -1.74, -13.54, -4.38] },
  { ad: "Oğuz", deger: 105.17, periyotlar: [3.96, 11.18, 3.31, -5.95, -6.36] },
  { ad: "Mehmet", deger: 99.74, periyotlar: [14.90, 1.56, 3.09, -6.90, -10.94] },
];

const KIYASLAMALAR = [
  { ad: "Faiz", deger: 107.12, periyotlar: [1.42, 1.42, 1.42, 1.42, 1.42], tip: "benchmark" },
  { ad: "USDTRY", deger: 102.67, periyotlar: [0.55, 0.20, 0.45, 0.00, 0.50], tip: "benchmark" },
  { ad: "BIST 100", deger: 113.87, periyotlar: [10.18, 9.23, 2.47, -3.26, -4.56], tip: "benchmark" },
];

// ── HELPERS ──
const fmt = (v, dec = 2) => {
  if (v == null) return "—";
  const s = Number(v).toFixed(dec);
  return s.replace(".", ",");
};
const fmtPct = (v) => `%${fmt(v)}`;
const getColor = (v) => (v > 0 ? COLORS.green : v < 0 ? COLORS.red : COLORS.textMuted);
const getMedal = (i) => ["🥇", "🥈", "🥉"][i] || `${i + 1}.`;

// Kümülatif getiri hesapla (100 bazlı)
const getCumulative = (periyotlar) => {
  let val = 100;
  const result = [{ periyot: "Başlangıç", deger: 100 }];
  periyotlar.forEach((p, i) => {
    val = val * (1 + p / 100);
    result.push({ periyot: PERIYOT_LABELS[i], deger: parseFloat(val.toFixed(2)) });
  });
  return result;
};

// Sıralama
const getSorted = () => {
  return [...YARISMACILAR].sort((a, b) => b.deger - a.deger);
};

// Volatilite (std dev)
const getVolatility = (periyotlar) => {
  const mean = periyotlar.reduce((s, v) => s + v, 0) / periyotlar.length;
  const variance = periyotlar.reduce((s, v) => s + (v - mean) ** 2, 0) / periyotlar.length;
  return Math.sqrt(variance);
};

// Sharpe benzeri (getiri / volatilite)
const getSharpe = (deger, periyotlar) => {
  const ret = deger - 100;
  const vol = getVolatility(periyotlar);
  return vol === 0 ? 0 : ret / vol;
};

// Pozitif periyot oranı
const getWinRate = (periyotlar) => {
  const pos = periyotlar.filter((p) => p > 0).length;
  return (pos / periyotlar.length) * 100;
};

// Max drawdown
const getMaxDrawdown = (periyotlar) => {
  let peak = 100;
  let maxDD = 0;
  let val = 100;
  periyotlar.forEach((p) => {
    val = val * (1 + p / 100);
    if (val > peak) peak = val;
    const dd = ((peak - val) / peak) * 100;
    if (dd > maxDD) maxDD = dd;
  });
  return maxDD;
};

// ═══════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════

const KPICard = ({ label, value, sub, icon, color }) => (
  <div style={{
    background: `linear-gradient(135deg, ${COLORS.card} 0%, ${COLORS.surface} 100%)`,
    borderRadius: 12, padding: "18px 20px",
    border: `1px solid ${COLORS.border}`,
    minWidth: 0, flex: 1,
    transition: "all 0.2s",
  }}>
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span style={{ color: COLORS.textMuted, fontSize: 12, fontWeight: 500, letterSpacing: "0.5px", textTransform: "uppercase" }}>{label}</span>
    </div>
    <div style={{ fontSize: 26, fontWeight: 700, color: color || COLORS.text, fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}>{value}</div>
    {sub && <div style={{ color: COLORS.textDim, fontSize: 11, marginTop: 4 }}>{sub}</div>}
  </div>
);

const Badge = ({ children, color }) => (
  <span style={{
    background: color + "22", color: color, fontSize: 10, fontWeight: 600,
    padding: "2px 8px", borderRadius: 20, letterSpacing: "0.3px",
  }}>{children}</span>
);

const TabBtn = ({ active, onClick, children, icon }) => (
  <button onClick={onClick} style={{
    background: active ? COLORS.accent + "33" : "transparent",
    color: active ? COLORS.text : COLORS.textMuted,
    border: active ? `1px solid ${COLORS.accent}55` : `1px solid transparent`,
    borderRadius: 8, padding: "10px 18px", cursor: "pointer",
    fontWeight: active ? 600 : 400, fontSize: 13,
    display: "flex", alignItems: "center", gap: 6,
    transition: "all 0.2s",
    fontFamily: "inherit",
  }}>
    <span style={{ fontSize: 15 }}>{icon}</span>
    {children}
  </button>
);

// ── CUSTOM TOOLTIP ──
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: COLORS.card, border: `1px solid ${COLORS.border}`,
      borderRadius: 8, padding: "10px 14px", boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    }}>
      <div style={{ color: COLORS.textMuted, fontSize: 11, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: p.color }} />
          <span style={{ color: COLORS.textMuted, fontSize: 11 }}>{p.name}:</span>
          <span style={{ color: COLORS.text, fontSize: 12, fontWeight: 600, fontFamily: "monospace" }}>{fmt(p.value)}</span>
        </div>
      ))}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// ANA SAYFA - GENEL BAKIŞ
// ═══════════════════════════════════════════════════════════
const GenelBakis = ({ onSelect }) => {
  const sorted = getSorted();
  const top3 = sorted.slice(0, 3);

  // Periyot bar chart data
  const barData = sorted.map((y) => ({
    ad: y.ad,
    getiri: parseFloat((y.deger - 100).toFixed(2)),
  }));

  // Cumulative chart data
  const cumData = PERIYOT_LABELS.map((label, i) => {
    const obj = { periyot: label };
    sorted.slice(0, 5).forEach((y) => {
      const cum = getCumulative(y.periyotlar);
      obj[y.ad] = cum[i + 1].deger;
    });
    // benchmarks
    KIYASLAMALAR.forEach((b) => {
      const cum = getCumulative(b.periyotlar);
      obj[b.ad] = cum[i + 1].deger;
    });
    return obj;
  });

  return (
    <div>
      {/* KPI Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
        <KPICard icon="🏆" label="Lider" value={top3[0].ad} sub={`Portföy: ${fmt(top3[0].deger)}`} color={COLORS.gold} />
        <KPICard icon="📈" label="BIST 100" value={fmt(ENDEKS_SON, 0)} sub={`Getiri: %${fmt(BENCHMARKS.endeksGetiri)}`} color={COLORS.green} />
        <KPICard icon="💵" label="USDTRY" value={fmt(USD_SON, 4)} sub={`Getiri: %${fmt(BENCHMARKS.usdGetiri)}`} color={COLORS.blue} />
        <KPICard icon="🏦" label="Faiz" value={fmt(BENCHMARKS.faizGetiri)} sub="Yıllık mevduat" color={COLORS.purple} />
        <KPICard icon="👥" label="Yarışmacı" value={YARISMACILAR.length} sub={`${sorted.filter((y) => y.deger > 100).length} kârda`} color={COLORS.cyan} />
      </div>

      {/* Sıralama Tablosu */}
      <div style={{
        background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`,
        overflow: "hidden", marginBottom: 24,
      }}>
        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${COLORS.border}`, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16 }}>🏅</span>
          <span style={{ color: COLORS.text, fontWeight: 600, fontSize: 15 }}>Genel Sıralama</span>
          <span style={{ color: COLORS.textDim, fontSize: 12, marginLeft: "auto" }}>5. Periyot — Son güncelleme: 13 Mart 2026</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: COLORS.surface }}>
                {["#", "Yarışmacı", "Portföy", "Toplam Getiri", "Son Periyot", "Volatilite", "Kazanma %", "Max DD", ""].map((h, i) => (
                  <th key={i} style={{
                    padding: "10px 14px", textAlign: i < 2 ? "left" : "right",
                    color: COLORS.textMuted, fontSize: 11, fontWeight: 600,
                    letterSpacing: "0.5px", textTransform: "uppercase", whiteSpace: "nowrap",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((y, i) => {
                const totalRet = y.deger - 100;
                const lastPeriyot = y.periyotlar[y.periyotlar.length - 1];
                const vol = getVolatility(y.periyotlar);
                const wr = getWinRate(y.periyotlar);
                const dd = getMaxDrawdown(y.periyotlar);
                const beatsBIST = totalRet > BENCHMARKS.endeksGetiri;
                const beatsFaiz = totalRet > BENCHMARKS.faizGetiri;

                return (
                  <tr key={y.ad} style={{
                    borderBottom: `1px solid ${COLORS.border}`,
                    cursor: "pointer",
                    transition: "background 0.15s",
                  }}
                    onMouseOver={(e) => e.currentTarget.style.background = COLORS.cardHover}
                    onMouseOut={(e) => e.currentTarget.style.background = "transparent"}
                    onClick={() => onSelect(y.ad)}
                  >
                    <td style={{ padding: "12px 14px", fontSize: 16 }}>{getMedal(i)}</td>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: "50%",
                          background: `linear-gradient(135deg, ${CHART_COLORS[i % CHART_COLORS.length]}44, ${CHART_COLORS[i % CHART_COLORS.length]}22)`,
                          border: `2px solid ${CHART_COLORS[i % CHART_COLORS.length]}66`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 13, fontWeight: 700, color: CHART_COLORS[i % CHART_COLORS.length],
                        }}>{y.ad[0]}</div>
                        <div>
                          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14 }}>{y.ad}</div>
                          <div style={{ display: "flex", gap: 4, marginTop: 2 }}>
                            {beatsBIST && <Badge color={COLORS.green}>BIST+</Badge>}
                            {beatsFaiz && <Badge color={COLORS.gold}>FAİZ+</Badge>}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: "monospace", fontWeight: 600, color: COLORS.text, fontSize: 14 }}>{fmt(y.deger)}</td>
                    <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: "monospace", fontWeight: 700, color: getColor(totalRet), fontSize: 14 }}>{fmtPct(totalRet)}</td>
                    <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: "monospace", fontWeight: 600, color: getColor(lastPeriyot), fontSize: 13 }}>{fmtPct(lastPeriyot)}</td>
                    <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: "monospace", color: COLORS.textMuted, fontSize: 13 }}>{fmt(vol)}</td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 6 }}>
                        <div style={{ width: 36, height: 4, borderRadius: 2, background: COLORS.surface, overflow: "hidden" }}>
                          <div style={{ width: `${wr}%`, height: "100%", background: wr >= 60 ? COLORS.green : wr >= 40 ? COLORS.gold : COLORS.red, borderRadius: 2 }} />
                        </div>
                        <span style={{ fontFamily: "monospace", color: COLORS.textMuted, fontSize: 12 }}>{fmt(wr, 0)}%</span>
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "right", fontFamily: "monospace", color: COLORS.red, fontSize: 12 }}>-{fmt(dd)}%</td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <span style={{ color: COLORS.accent, fontSize: 12, fontWeight: 500 }}>Detay →</span>
                    </td>
                  </tr>
                );
              })}
              {/* Benchmarks */}
              {KIYASLAMALAR.map((b) => {
                const totalRet = b.deger - 100;
                const lastPeriyot = b.periyotlar[b.periyotlar.length - 1];
                return (
                  <tr key={b.ad} style={{ borderBottom: `1px solid ${COLORS.border}`, background: COLORS.surface + "44" }}>
                    <td style={{ padding: "10px 14px", color: COLORS.textDim, fontSize: 12 }}>—</td>
                    <td style={{ padding: "10px 14px" }}>
                      <span style={{ color: COLORS.textDim, fontSize: 13, fontStyle: "italic" }}>{b.ad}</span>
                    </td>
                    <td style={{ padding: "10px 14px", textAlign: "right", fontFamily: "monospace", color: COLORS.textDim, fontSize: 13 }}>{fmt(b.deger)}</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", fontFamily: "monospace", color: getColor(totalRet), fontSize: 13 }}>{fmtPct(totalRet)}</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", fontFamily: "monospace", color: getColor(lastPeriyot), fontSize: 12 }}>{fmtPct(lastPeriyot)}</td>
                    <td colSpan={4} />
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Toplam Getiri Bar */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <span>📊</span> Toplam Getiri Sıralaması
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData} layout="vertical" margin={{ left: 60, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} horizontal={false} />
              <XAxis type="number" tick={{ fill: COLORS.textDim, fontSize: 11 }} axisLine={{ stroke: COLORS.border }} tickFormatter={(v) => `%${v}`} />
              <YAxis type="category" dataKey="ad" tick={{ fill: COLORS.textMuted, fontSize: 12 }} axisLine={false} tickLine={false} width={55} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="getiri" radius={[0, 4, 4, 0]} barSize={18}>
                {barData.map((entry, i) => (
                  <Cell key={i} fill={entry.getiri >= 0 ? COLORS.green : COLORS.red} fillOpacity={0.85} />
                ))}
              </Bar>
              {/* Faiz çizgisi */}
              {/* Reference line workaround */}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Kümülatif Performans */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
            <span>📈</span> İlk 5 vs Kıyaslama (Kümülatif)
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={cumData} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
              <XAxis dataKey="periyot" tick={{ fill: COLORS.textDim, fontSize: 10 }} axisLine={{ stroke: COLORS.border }} />
              <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} axisLine={{ stroke: COLORS.border }} domain={["auto", "auto"]} />
              <Tooltip content={<CustomTooltip />} />
              {sorted.slice(0, 5).map((y, i) => (
                <Line key={y.ad} type="monotone" dataKey={y.ad} stroke={CHART_COLORS[i]} strokeWidth={2.5} dot={{ r: 3, fill: CHART_COLORS[i] }} />
              ))}
              <Line type="monotone" dataKey="BIST 100" stroke={COLORS.textDim} strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
              <Line type="monotone" dataKey="Faiz" stroke={COLORS.purple} strokeWidth={1} strokeDasharray="3 3" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// YARIŞMACI DETAY SAYFASI
// ═══════════════════════════════════════════════════════════
const YarismaciDetay = ({ ad, onBack }) => {
  const y = YARISMACILAR.find((x) => x.ad === ad);
  if (!y) return null;

  const sorted = getSorted();
  const rank = sorted.findIndex((x) => x.ad === ad) + 1;
  const totalRet = y.deger - 100;
  const vol = getVolatility(y.periyotlar);
  const sharpe = getSharpe(y.deger, y.periyotlar);
  const wr = getWinRate(y.periyotlar);
  const maxDD = getMaxDrawdown(y.periyotlar);
  const cumData = getCumulative(y.periyotlar);

  // Periyot karşılaştırma
  const periyotComp = PERIYOT_LABELS.map((label, i) => ({
    periyot: label.replace(". Periyot", "P"),
    [y.ad]: y.periyotlar[i],
    "BIST 100": KIYASLAMALAR[2].periyotlar[i],
    "Faiz": KIYASLAMALAR[0].periyotlar[i],
  }));

  // Kümülatif tüm hatlar
  const cumCompare = PERIYOT_LABELS.map((label, i) => {
    const obj = { periyot: label.replace(". Periyot", "P") };
    const yCum = getCumulative(y.periyotlar);
    obj[y.ad] = yCum[i + 1].deger;
    KIYASLAMALAR.forEach((b) => {
      const bCum = getCumulative(b.periyotlar);
      obj[b.ad] = bCum[i + 1].deger;
    });
    return obj;
  });

  // Radar data
  const maxValues = {
    getiri: Math.max(...YARISMACILAR.map((x) => Math.abs(x.deger - 100))),
    vol: Math.max(...YARISMACILAR.map((x) => getVolatility(x.periyotlar))),
    wr: 100,
    sharpe: Math.max(...YARISMACILAR.map((x) => Math.abs(getSharpe(x.deger, x.periyotlar)))),
    dd: Math.max(...YARISMACILAR.map((x) => getMaxDrawdown(x.periyotlar))),
  };

  const radarData = [
    { metric: "Getiri", value: Math.max(0, (totalRet / maxValues.getiri) * 100) },
    { metric: "İstikrar", value: Math.max(0, (1 - vol / maxValues.vol) * 100) },
    { metric: "Kazanma %", value: wr },
    { metric: "Sharpe", value: Math.max(0, sharpe > 0 ? (sharpe / maxValues.sharpe) * 100 : 0) },
    { metric: "Dayanıklılık", value: Math.max(0, (1 - maxDD / (maxValues.dd || 1)) * 100) },
  ];

  // Periyot bazlı sıralama
  const periyotRank = y.periyotlar.map((_, i) => {
    const sortedByPeriyot = [...YARISMACILAR].sort((a, b) => b.periyotlar[i] - a.periyotlar[i]);
    return sortedByPeriyot.findIndex((x) => x.ad === ad) + 1;
  });

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <button onClick={onBack} style={{
          background: COLORS.surface, border: `1px solid ${COLORS.border}`, color: COLORS.textMuted,
          borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 13, fontFamily: "inherit",
        }}>← Geri</button>
        <div style={{
          width: 48, height: 48, borderRadius: "50%",
          background: `linear-gradient(135deg, ${CHART_COLORS[rank - 1]}44, ${CHART_COLORS[rank - 1]}22)`,
          border: `3px solid ${CHART_COLORS[rank - 1]}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 20, fontWeight: 700, color: CHART_COLORS[rank - 1],
        }}>{y.ad[0]}</div>
        <div>
          <div style={{ color: COLORS.text, fontSize: 22, fontWeight: 700 }}>{y.ad}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 2 }}>
            <Badge color={COLORS.gold}>{getMedal(rank - 1)} Sıra</Badge>
            {totalRet > BENCHMARKS.endeksGetiri && <Badge color={COLORS.green}>BIST'i Yendi</Badge>}
            {totalRet > BENCHMARKS.faizGetiri && <Badge color={COLORS.purple}>Faizi Yendi</Badge>}
            {vol < 5 && <Badge color={COLORS.cyan}>Düşük Volatilite</Badge>}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 24 }}>
        <KPICard icon="💰" label="Portföy" value={fmt(y.deger)} color={COLORS.text} />
        <KPICard icon="📊" label="Toplam Getiri" value={fmtPct(totalRet)} color={getColor(totalRet)} />
        <KPICard icon="⚡" label="Son Periyot" value={fmtPct(y.periyotlar[4])} color={getColor(y.periyotlar[4])} />
        <KPICard icon="📉" label="Volatilite" value={fmt(vol)} sub={vol < 5 ? "Düşük" : vol < 10 ? "Orta" : "Yüksek"} />
        <KPICard icon="🎯" label="Sharpe" value={fmt(sharpe)} color={sharpe > 2 ? COLORS.green : sharpe > 1 ? COLORS.gold : COLORS.textMuted} />
        <KPICard icon="🛡️" label="Max Drawdown" value={`-${fmt(maxDD)}%`} color={COLORS.red} />
      </div>

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        {/* Kümülatif */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>📈 Kümülatif Performans</div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={cumCompare}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
              <XAxis dataKey="periyot" tick={{ fill: COLORS.textDim, fontSize: 11 }} />
              <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} domain={["auto", "auto"]} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey={y.ad} stroke={COLORS.gold} strokeWidth={3} dot={{ r: 4, fill: COLORS.gold }} />
              <Line type="monotone" dataKey="BIST 100" stroke={COLORS.textDim} strokeWidth={1.5} strokeDasharray="6 3" dot={false} />
              <Line type="monotone" dataKey="Faiz" stroke={COLORS.purple} strokeWidth={1} strokeDasharray="3 3" dot={false} />
              <Line type="monotone" dataKey="USDTRY" stroke={COLORS.blue} strokeWidth={1} strokeDasharray="3 3" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Radar */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>🎯 Performans Profili</div>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke={COLORS.border} />
              <PolarAngleAxis dataKey="metric" tick={{ fill: COLORS.textMuted, fontSize: 11 }} />
              <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]} />
              <Radar dataKey="value" stroke={COLORS.gold} fill={COLORS.gold} fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Periyot Detay Bar */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20, marginBottom: 24 }}>
        <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>📊 Periyot Bazlı Getiri vs Kıyaslama</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={periyotComp} margin={{ left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
            <XAxis dataKey="periyot" tick={{ fill: COLORS.textDim, fontSize: 11 }} />
            <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} tickFormatter={(v) => `%${v}`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={y.ad} fill={COLORS.gold} radius={[4, 4, 0, 0]} barSize={22} />
            <Bar dataKey="BIST 100" fill={COLORS.textDim} radius={[4, 4, 0, 0]} barSize={14} fillOpacity={0.5} />
            <Bar dataKey="Faiz" fill={COLORS.purple} radius={[4, 4, 0, 0]} barSize={10} fillOpacity={0.4} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Periyot Sıralama Tablosu */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: "hidden" }}>
        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${COLORS.border}` }}>
          <span style={{ color: COLORS.text, fontWeight: 600, fontSize: 14 }}>📋 Periyot Karnesi</span>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: COLORS.surface }}>
              {["Periyot", "Getiri", "BIST 100", "Alfa", "Sıralama"].map((h, i) => (
                <th key={i} style={{ padding: "10px 16px", textAlign: i === 0 ? "left" : "right", color: COLORS.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERIYOT_LABELS.map((label, i) => {
              const alfa = y.periyotlar[i] - KIYASLAMALAR[2].periyotlar[i];
              return (
                <tr key={i} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <td style={{ padding: "10px 16px", color: COLORS.text, fontSize: 13 }}>{label}</td>
                  <td style={{ padding: "10px 16px", textAlign: "right", fontFamily: "monospace", fontWeight: 600, color: getColor(y.periyotlar[i]) }}>{fmtPct(y.periyotlar[i])}</td>
                  <td style={{ padding: "10px 16px", textAlign: "right", fontFamily: "monospace", color: COLORS.textDim, fontSize: 12 }}>{fmtPct(KIYASLAMALAR[2].periyotlar[i])}</td>
                  <td style={{ padding: "10px 16px", textAlign: "right", fontFamily: "monospace", fontWeight: 600, color: getColor(alfa) }}>{fmtPct(alfa)}</td>
                  <td style={{ padding: "10px 16px", textAlign: "right" }}>
                    <span style={{
                      background: periyotRank[i] <= 3 ? COLORS.gold + "22" : COLORS.surface,
                      color: periyotRank[i] <= 3 ? COLORS.gold : COLORS.textMuted,
                      padding: "2px 10px", borderRadius: 12, fontSize: 12, fontWeight: 600,
                    }}>{periyotRank[i]}/{YARISMACILAR.length}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// KARŞILAŞTIRMA SAYFASI
// ═══════════════════════════════════════════════════════════
const Karsilastirma = () => {
  const [selected, setSelected] = useState([YARISMACILAR[0].ad, YARISMACILAR[1].ad]);

  const toggleSelect = (ad) => {
    if (selected.includes(ad)) {
      if (selected.length > 1) setSelected(selected.filter((x) => x !== ad));
    } else if (selected.length < 5) {
      setSelected([...selected, ad]);
    }
  };

  const cumData = [{ periyot: "Başlangıç", ...Object.fromEntries(selected.map((ad) => [ad, 100])) }];
  PERIYOT_LABELS.forEach((label, i) => {
    const obj = { periyot: label.replace(". Periyot", "P") };
    selected.forEach((ad) => {
      const y = YARISMACILAR.find((x) => x.ad === ad);
      if (y) {
        const cum = getCumulative(y.periyotlar);
        obj[ad] = cum[i + 1].deger;
      }
    });
    cumData.push(obj);
  });

  return (
    <div>
      {/* Yarışmacı seçimi */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 16, marginBottom: 20 }}>
        <div style={{ color: COLORS.textMuted, fontSize: 12, marginBottom: 10 }}>Karşılaştırılacak yarışmacıları seç (en fazla 5):</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {getSorted().map((y, i) => (
            <button key={y.ad} onClick={() => toggleSelect(y.ad)} style={{
              background: selected.includes(y.ad) ? CHART_COLORS[i % CHART_COLORS.length] + "33" : COLORS.surface,
              border: `1px solid ${selected.includes(y.ad) ? CHART_COLORS[i % CHART_COLORS.length] : COLORS.border}`,
              color: selected.includes(y.ad) ? COLORS.text : COLORS.textMuted,
              padding: "6px 14px", borderRadius: 20, cursor: "pointer", fontSize: 12, fontWeight: 500, fontFamily: "inherit",
              transition: "all 0.15s",
            }}>{y.ad}</button>
          ))}
        </div>
      </div>

      {/* Karşılaştırma Grafiği */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20, marginBottom: 20 }}>
        <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>📈 Kümülatif Karşılaştırma</div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={cumData}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
            <XAxis dataKey="periyot" tick={{ fill: COLORS.textDim, fontSize: 11 }} />
            <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} domain={["auto", "auto"]} />
            <Tooltip content={<CustomTooltip />} />
            {selected.map((ad, i) => (
              <Line key={ad} type="monotone" dataKey={ad} stroke={CHART_COLORS[getSorted().findIndex((x) => x.ad === ad) % CHART_COLORS.length]} strokeWidth={2.5} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Karşılaştırma Tablosu */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: COLORS.surface }}>
              {["Metrik", ...selected].map((h, i) => (
                <th key={i} style={{ padding: "10px 14px", textAlign: i === 0 ? "left" : "right", color: COLORS.textMuted, fontSize: 11, fontWeight: 600, textTransform: "uppercase" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              { label: "Portföy Değeri", fn: (y) => fmt(y.deger) },
              { label: "Toplam Getiri", fn: (y) => fmtPct(y.deger - 100) },
              { label: "Son Periyot", fn: (y) => fmtPct(y.periyotlar[4]) },
              { label: "En İyi Periyot", fn: (y) => fmtPct(Math.max(...y.periyotlar)) },
              { label: "En Kötü Periyot", fn: (y) => fmtPct(Math.min(...y.periyotlar)) },
              { label: "Volatilite", fn: (y) => fmt(getVolatility(y.periyotlar)) },
              { label: "Kazanma %", fn: (y) => `%${fmt(getWinRate(y.periyotlar), 0)}` },
              { label: "Max Drawdown", fn: (y) => `-${fmt(getMaxDrawdown(y.periyotlar))}%` },
              { label: "Sharpe", fn: (y) => fmt(getSharpe(y.deger, y.periyotlar)) },
            ].map((row, ri) => (
              <tr key={ri} style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                <td style={{ padding: "10px 14px", color: COLORS.textMuted, fontSize: 12 }}>{row.label}</td>
                {selected.map((ad) => {
                  const y = YARISMACILAR.find((x) => x.ad === ad);
                  return (
                    <td key={ad} style={{ padding: "10px 14px", textAlign: "right", fontFamily: "monospace", color: COLORS.text, fontSize: 13 }}>{y ? row.fn(y) : "—"}</td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// İSTATİSTİKLER
// ═══════════════════════════════════════════════════════════
const Istatistikler = () => {
  const sorted = getSorted();

  // En iyi/kötü tek periyot performansları
  const allPerfs = [];
  YARISMACILAR.forEach((y) => {
    y.periyotlar.forEach((p, i) => {
      allPerfs.push({ ad: y.ad, periyot: PERIYOT_LABELS[i], getiri: p });
    });
  });
  allPerfs.sort((a, b) => b.getiri - a.getiri);

  // Endeksi yenen sayısı per periyot
  const beaters = PERIYOT_LABELS.map((label, i) => {
    const count = YARISMACILAR.filter((y) => y.periyotlar[i] > KIYASLAMALAR[2].periyotlar[i]).length;
    return { periyot: label.replace(". Periyot", "P"), yenen: count, yenilen: YARISMACILAR.length - count };
  });

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
        {/* En iyi periyot performansları */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>🏆 En İyi 10 Periyot Performansı</div>
          {allPerfs.slice(0, 10).map((p, i) => (
            <div key={i} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "8px 0", borderBottom: i < 9 ? `1px solid ${COLORS.border}` : "none",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: COLORS.textDim, fontSize: 11, width: 20 }}>{i + 1}.</span>
                <span style={{ color: COLORS.text, fontSize: 13, fontWeight: 500 }}>{p.ad}</span>
                <span style={{ color: COLORS.textDim, fontSize: 11 }}>{p.periyot}</span>
              </div>
              <span style={{ fontFamily: "monospace", color: COLORS.green, fontWeight: 600, fontSize: 13 }}>{fmtPct(p.getiri)}</span>
            </div>
          ))}
        </div>

        {/* En kötü periyot performansları */}
        <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
          <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>💀 En Kötü 10 Periyot Performansı</div>
          {allPerfs.slice(-10).reverse().map((p, i) => (
            <div key={i} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "8px 0", borderBottom: i < 9 ? `1px solid ${COLORS.border}` : "none",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: COLORS.textDim, fontSize: 11, width: 20 }}>{i + 1}.</span>
                <span style={{ color: COLORS.text, fontSize: 13, fontWeight: 500 }}>{p.ad}</span>
                <span style={{ color: COLORS.textDim, fontSize: 11 }}>{p.periyot}</span>
              </div>
              <span style={{ fontFamily: "monospace", color: COLORS.red, fontWeight: 600, fontSize: 13 }}>{fmtPct(p.getiri)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* BIST'i yenen sayısı */}
      <div style={{ background: COLORS.card, borderRadius: 12, border: `1px solid ${COLORS.border}`, padding: 20 }}>
        <div style={{ color: COLORS.text, fontWeight: 600, fontSize: 14, marginBottom: 16 }}>📊 BIST 100'ü Yenen Yarışmacı Sayısı (Periyot Bazlı)</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={beaters}>
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
            <XAxis dataKey="periyot" tick={{ fill: COLORS.textDim, fontSize: 11 }} />
            <YAxis tick={{ fill: COLORS.textDim, fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="yenen" fill={COLORS.green} radius={[4, 4, 0, 0]} name="Yenen" barSize={30} />
            <Bar dataKey="yenilen" fill={COLORS.red} radius={[4, 4, 0, 0]} name="Yenilen" barSize={30} fillOpacity={0.5} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════
export default function App() {
  const [tab, setTab] = useState("genel");
  const [selectedYarismaci, setSelectedYarismaci] = useState(null);

  const handleSelect = (ad) => {
    setSelectedYarismaci(ad);
    setTab("detay");
  };

  return (
    <div style={{
      background: COLORS.bg, minHeight: "100vh", color: COLORS.text,
      fontFamily: "'Segoe UI', 'SF Pro Display', -apple-system, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(180deg, ${COLORS.surface} 0%, ${COLORS.bg} 100%)`,
        borderBottom: `1px solid ${COLORS.border}`,
        padding: "20px 28px 0",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              fontSize: 26, fontWeight: 800, letterSpacing: "-0.5px",
              background: `linear-gradient(135deg, ${COLORS.gold}, ${COLORS.green})`,
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>YGF</div>
            <div>
              <div style={{ color: COLORS.text, fontSize: 16, fontWeight: 600 }}>Yatırım Getiri Farkı</div>
              <div style={{ color: COLORS.textDim, fontSize: 11 }}>Sai Amatör Yatırım — Arkadaşlar Arası Yarışma</div>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ color: COLORS.textMuted, fontSize: 11 }}>Başlangıç: {YARISMA_BASLANGIC}</div>
            <div style={{ color: COLORS.textDim, fontSize: 10 }}>5. Periyot — 70. Gün</div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, paddingBottom: 0 }}>
          <TabBtn active={tab === "genel"} onClick={() => { setTab("genel"); setSelectedYarismaci(null); }} icon="🏠">Genel Bakış</TabBtn>
          <TabBtn active={tab === "detay"} onClick={() => { if (!selectedYarismaci) setSelectedYarismaci(getSorted()[0].ad); setTab("detay"); }} icon="👤">Yarışmacı Detay</TabBtn>
          <TabBtn active={tab === "karsilastir"} onClick={() => setTab("karsilastir")} icon="⚖️">Karşılaştırma</TabBtn>
          <TabBtn active={tab === "istatistik"} onClick={() => setTab("istatistik")} icon="📊">İstatistikler</TabBtn>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: "24px 28px", maxWidth: 1200, margin: "0 auto" }}>
        {tab === "genel" && <GenelBakis onSelect={handleSelect} />}
        {tab === "detay" && selectedYarismaci && <YarismaciDetay ad={selectedYarismaci} onBack={() => { setTab("genel"); setSelectedYarismaci(null); }} />}
        {tab === "karsilastir" && <Karsilastirma />}
        {tab === "istatistik" && <Istatistikler />}
      </div>

      {/* Footer */}
      <div style={{ padding: "16px 28px", borderTop: `1px solid ${COLORS.border}`, textAlign: "center" }}>
        <span style={{ color: COLORS.textDim, fontSize: 10 }}>Sai Amatör Yatırım © 2026 — Veriler 15 günlük periyotlarla güncellenir</span>
      </div>
    </div>
  );
}

import { useState, useMemo } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, PieChart, Pie, Treemap } from "recharts";

/* ═══════════════════════════════════════════════════════
   YGF DASHBOARD v2 — Premium Financial Terminal
   Sai Amatör Yatırım
   ═══════════════════════════════════════════════════════ */

const C = {
  bg: "#060d16", bg2: "#0a1628", surface: "#111d32", card: "#152238",
  cardHover: "#1a2d4a", border: "#1e3354", borderLight: "#264170",
  text: "#e8edf5", textMuted: "#8899b4", textDim: "#556a8a",
  gold: "#f0b429", goldDim: "#b8860b", green: "#22c55e", greenDim: "#15803d",
  red: "#ef4444", redDim: "#b91c1c", blue: "#3b82f6", purple: "#a855f7",
  cyan: "#06b6d4", orange: "#f97316", navy: "#1a3a6a", accent: "#4a9eff",
};
const PAL = ["#f0b429","#22c55e","#3b82f6","#a855f7","#06b6d4","#ef4444","#f97316","#ec4899","#14b8a6","#818cf8","#fb923c","#6366f1","#f43f5e","#84cc16"];

const PERIYOTLAR = ["1P","2P","3P","4P","5P","6P"];

const DATA = [
  {ad:"Serkan",pf:131.24,p:[17.01,9.95,3.18,-6.73,5.33,0],vol:8.18,poz:"67%",dd:-6.73,alfa:17.37},
  {ad:"Özhan",pf:130.47,p:[11.45,16.75,7.84,-8.20,1.28,0],vol:8.95,poz:"67%",dd:-8.20,alfa:16.60},
  {ad:"Ali Cenk",pf:127.14,p:[9.76,10.72,4.28,-5.80,1.00,0],vol:6.27,poz:"67%",dd:-5.80,alfa:13.27},
  {ad:"Barış",pf:122.05,p:[11.72,8.42,2.58,-6.91,5.52,0],vol:6.59,poz:"67%",dd:-6.91,alfa:8.18},
  {ad:"Turan",pf:109.46,p:[3.78,9.17,5.09,-8.93,0.94,0],vol:6.13,poz:"67%",dd:-8.93,alfa:-4.41},
  {ad:"Selim",pf:107.95,p:[24.68,-6.73,3.00,-7.74,-2.31,0],vol:11.91,poz:"33%",dd:-7.74,alfa:-5.92},
  {ad:"Faiz",pf:107.21,p:[1.42,1.42,1.42,1.42,1.42,0],vol:0,poz:"100%",dd:1.42,alfa:null,bench:true},
  {ad:"Berkan",pf:105.67,p:[7.66,6.34,0.62,-8.09,-0.20,0],vol:5.62,poz:"50%",dd:-8.09,alfa:-8.20},
  {ad:"Oğuz",pf:110.00,p:[3.96,11.18,3.31,-5.95,-6.95,0],vol:6.79,poz:"50%",dd:-6.95,alfa:-3.87},
  {ad:"BIST 100",pf:113.87,p:[10.18,9.23,2.47,-3.26,-4.56,0],vol:6.83,poz:"60%",dd:-4.56,alfa:null,bench:true},
  {ad:"USDTRY",pf:102.62,p:[0.55,0.20,0.45,0.00,0.50,0],vol:0.23,poz:"80%",dd:0,alfa:null,bench:true},
  {ad:"Gürkan",pf:100.00,p:[19.61,-3.86,1.32,-12.18,-2.31,0],vol:10.52,poz:"33%",dd:-12.18,alfa:-13.87},
  {ad:"Mehmet",pf:99.75,p:[14.90,1.56,3.09,-6.90,-10.95,0],vol:8.96,poz:"50%",dd:-10.95,alfa:-14.12},
  {ad:"Osman",pf:98.51,p:[21.02,0.22,-1.74,-13.54,-4.37,0],vol:11.37,poz:"33%",dd:-13.54,alfa:-15.36},
];

const PLAYERS = DATA.filter(d=>!d.bench).sort((a,b)=>b.pf-a.pf);
const BENCHMARKS = DATA.filter(d=>d.bench);
const ALL_SORTED = [...DATA].sort((a,b)=>b.pf-a.pf);

const ICMAL_6P = [
  {h:"KLGYO",tl:311.46,kisi:5,pay:25.1},{h:"TUREX",tl:189.93,kisi:2,pay:15.3},
  {h:"MGROS",tl:62.49,kisi:2,pay:5.0},{h:"NAKİT",tl:60.42,kisi:1,pay:4.9},
  {h:"AYDEM",tl:60,kisi:2,pay:4.8},{h:"TNZTP",tl:55,kisi:2,pay:4.4},
  {h:"EKGYO",tl:47.26,kisi:1,pay:3.8},{h:"TRGYO",tl:32.05,kisi:1,pay:2.6},
  {h:"RTALB",tl:30,kisi:2,pay:2.4},{h:"KTLEV",tl:30,kisi:1,pay:2.4},
  {h:"DOHOL",tl:30,kisi:1,pay:2.4},{h:"TRCAS",tl:30,kisi:1,pay:2.4},
  {h:"PSGYO",tl:30,kisi:1,pay:2.4},{h:"AKFYE",tl:25,kisi:2,pay:2.0},
  {h:"AHGAZ",tl:25,kisi:1,pay:2.0},{h:"ENDAE",tl:22.14,kisi:1,pay:1.8},
  {h:"EGEGY",tl:20.67,kisi:1,pay:1.7},{h:"ANSGR",tl:20,kisi:1,pay:1.6},
  {h:"FONET",tl:20,kisi:1,pay:1.6},{h:"PATEK",tl:20,kisi:1,pay:1.6},
  {h:"THYAO",tl:20,kisi:1,pay:1.6},{h:"TRENJ",tl:20,kisi:1,pay:1.6},
  {h:"LIDFA",tl:15,kisi:1,pay:1.2},{h:"KRONT",tl:15,kisi:1,pay:1.2},
];

const ICMAL_5P = [
  {h:"KLGYO",tl:286.52,kisi:5,pay:23.1},{h:"A1CAP",tl:168.82,kisi:3,pay:13.6},
  {h:"MGROS",tl:76,kisi:2,pay:6.1},{h:"EKGYO",tl:76,kisi:2,pay:6.1},
  {h:"TUREX",tl:58.44,kisi:1,pay:4.7},{h:"NAKİT",tl:48.81,kisi:1,pay:3.9},
  {h:"TNZTP",tl:45,kisi:2,pay:3.6},{h:"GUBRF",tl:32.31,kisi:1,pay:2.6},
  {h:"RTALB",tl:31.83,kisi:2,pay:2.6},{h:"KCHOL",tl:30,kisi:1,pay:2.4},
];

const fmt = (v,d=2) => v==null?"—":Number(v).toFixed(d).replace(".",",");
const fmtPct = v => v==null?"—":`%${fmt(v)}`;
const clr = v => v>0?C.green:v<0?C.red:C.textDim;
const medal = i => ["🥇","🥈","🥉"][i]||`${i+1}.`;

const cumSeries = (periyotlar) => {
  let v=100; return [{p:"Baş",v:100},...periyotlar.map((g,i)=>{v*=(1+g/100);return{p:PERIYOTLAR[i],v:+v.toFixed(2)};})];
};

// ─── COMPONENTS ──────────────────────────────────────────

const Glow = ({color,children}) => (
  <span style={{textShadow:`0 0 12px ${color}55, 0 0 4px ${color}33`,color}}>{children}</span>
);

const Card = ({children,style,...p}) => (
  <div style={{background:`linear-gradient(135deg,${C.card},${C.surface})`,borderRadius:14,border:`1px solid ${C.border}`,padding:"16px 18px",transition:"all .2s",...style}} {...p}>{children}</div>
);

const KPI = ({icon,label,value,color=C.text,sub}) => (
  <Card>
    <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:6}}>
      <span style={{fontSize:15}}>{icon}</span>
      <span style={{color:C.textDim,fontSize:10,fontWeight:600,textTransform:"uppercase",letterSpacing:1}}>{label}</span>
    </div>
    <div style={{fontSize:22,fontWeight:800,color,fontFamily:"'DM Mono',monospace"}}>{value}</div>
    {sub&&<div style={{color:C.textDim,fontSize:10,marginTop:2}}>{sub}</div>}
  </Card>
);

const NavBtn = ({active,onClick,children,icon}) => (
  <button onClick={onClick} style={{background:active?`${C.accent}18`:"transparent",color:active?C.text:C.textMuted,border:`1px solid ${active?C.accent+"44":"transparent"}`,borderRadius:10,padding:"10px 16px",cursor:"pointer",fontWeight:active?700:400,fontSize:12,display:"flex",alignItems:"center",gap:5,transition:"all .2s",fontFamily:"inherit",letterSpacing:active?.3:0}}>
    <span style={{fontSize:14}}>{icon}</span>{children}
  </button>
);

const TT = ({active,payload,label})=>{
  if(!active||!payload?.length)return null;
  return(<div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:10,padding:"10px 14px",boxShadow:"0 12px 40px rgba(0,0,0,.6)"}}>
    <div style={{color:C.textDim,fontSize:10,marginBottom:5}}>{label}</div>
    {payload.map((p,i)=>(<div key={i} style={{display:"flex",alignItems:"center",gap:5,marginBottom:1}}>
      <div style={{width:7,height:7,borderRadius:"50%",background:p.color}}/>
      <span style={{color:C.textMuted,fontSize:10}}>{p.name}:</span>
      <span style={{color:C.text,fontSize:11,fontWeight:700,fontFamily:"monospace"}}>{fmt(p.value)}</span>
    </div>))}
  </div>);
};

const layout = (title="",h=320) => ({
  title:{text:title,font:{size:13,color:C.text,family:"DM Sans"}},
  plot_bgcolor:C.card,paper_bgcolor:C.card,font:{color:C.textMuted,size:10},
  height:h,margin:{l:35,r:15,t:35,b:35},
  xaxis:{gridcolor:C.border,zerolinecolor:C.border},
  yaxis:{gridcolor:C.border,zerolinecolor:C.border},
  legend:{bgcolor:"rgba(0,0,0,0)",font:{size:9}},
});

// ═══════════════════════════════════════════════════════
// PAGE 1: GENEL BAKIŞ
// ═══════════════════════════════════════════════════════
const PageOverview = ({onSelect}) => {
  const bist = BENCHMARKS.find(b=>b.ad==="BIST 100");
  const faiz = BENCHMARKS.find(b=>b.ad==="Faiz");
  const usd = BENCHMARKS.find(b=>b.ad==="USDTRY");
  const top3 = PLAYERS.slice(0,3);
  const karda = PLAYERS.filter(p=>p.pf>100).length;

  const barData = ALL_SORTED.map(d=>({ad:d.ad,getiri:+(d.pf-100).toFixed(2),bench:!!d.bench}));
  const cumData = PERIYOTLAR.slice(0,5).map((lbl,i)=>{
    const obj = {p:lbl};
    PLAYERS.slice(0,5).forEach(y=>{const s=cumSeries(y.p);obj[y.ad]=s[i+1]?.v||100;});
    if(bist){const s=cumSeries(bist.p);obj["BIST 100"]=s[i+1]?.v||100;}
    return obj;
  });

  return (<div>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(155px,1fr))",gap:10,marginBottom:20}}>
      <KPI icon="🏆" label="Lider" value={top3[0].ad} color={C.gold} sub={`Portföy: ${fmt(top3[0].pf)}`}/>
      <KPI icon="📈" label="BIST 100" value={fmt(bist?.pf)} color={C.green} sub={`YTD: ${fmtPct(bist?.pf-100)}`}/>
      <KPI icon="💵" label="USDTRY" value={fmt(usd?.pf)} color={C.blue} sub={`YTD: ${fmtPct(usd?.pf-100)}`}/>
      <KPI icon="🏦" label="Faiz" value={fmt(faiz?.pf)} color={C.purple} sub={`YTD: ${fmtPct(faiz?.pf-100)}`}/>
      <KPI icon="👥" label="Yarışmacı" value={`${PLAYERS.length}`} color={C.cyan} sub={`${karda} kârda`}/>
    </div>

    {/* LEADERBOARD */}
    <Card style={{overflow:"hidden",marginBottom:20,padding:0}}>
      <div style={{padding:"14px 18px",borderBottom:`1px solid ${C.border}`,display:"flex",alignItems:"center",gap:8}}>
        <span style={{fontSize:15}}>🏅</span>
        <span style={{color:C.text,fontWeight:700,fontSize:14,letterSpacing:.3}}>Genel Sıralama</span>
        <span style={{color:C.textDim,fontSize:10,marginLeft:"auto"}}>6. Periyot aktif</span>
      </div>
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
          <thead><tr style={{background:C.bg2}}>
            {["#","Yarışmacı","Portföy","Vol.","Poz%","MaxDD","Alfa","6P","5P","4P","3P","2P","1P"].map((h,i)=>(
              <th key={i} style={{padding:"9px 10px",textAlign:i<2?"left":"right",color:C.textDim,fontSize:9,fontWeight:700,textTransform:"uppercase",letterSpacing:.8,whiteSpace:"nowrap"}}>{h}</th>
            ))}
          </tr></thead>
          <tbody>{ALL_SORTED.map((d,i)=>{
            const ret=d.pf-100;const isBench=!!d.bench;
            return(<tr key={d.ad} onClick={()=>!isBench&&onSelect(d.ad)} style={{borderBottom:`1px solid ${C.border}`,cursor:isBench?"default":"pointer",background:isBench?C.bg2+"66":"transparent",transition:"background .15s"}}
              onMouseOver={e=>{if(!isBench)e.currentTarget.style.background=C.cardHover}}
              onMouseOut={e=>{e.currentTarget.style.background=isBench?C.bg2+"66":"transparent"}}>
              <td style={{padding:"10px 10px",fontSize:14,textAlign:"center"}}>{isBench?"—":medal(PLAYERS.indexOf(d))}</td>
              <td style={{padding:"10px 10px"}}>
                <div style={{display:"flex",alignItems:"center",gap:7}}>
                  <div style={{width:28,height:28,borderRadius:"50%",background:`linear-gradient(135deg,${PAL[i%PAL.length]}33,${PAL[i%PAL.length]}11)`,border:`2px solid ${PAL[i%PAL.length]}55`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:800,color:PAL[i%PAL.length]}}>{d.ad[0]}</div>
                  <span style={{fontWeight:isBench?400:600,fontStyle:isBench?"italic":"normal",color:isBench?C.textDim:C.text,fontSize:12}}>{d.ad}</span>
                </div>
              </td>
              <td style={{padding:"10px",textAlign:"right",fontFamily:"'DM Mono',monospace",fontWeight:700,color:clr(ret),fontSize:13}}>{fmt(d.pf)}</td>
              <td style={{padding:"10px",textAlign:"right",fontFamily:"monospace",color:C.textMuted,fontSize:11}}>{d.vol||"—"}</td>
              <td style={{padding:"10px",textAlign:"right",fontSize:11,color:C.textMuted}}>{d.poz}</td>
              <td style={{padding:"10px",textAlign:"right",fontFamily:"monospace",color:C.red,fontSize:10}}>{d.dd?fmt(d.dd):""}</td>
              <td style={{padding:"10px",textAlign:"right",fontFamily:"monospace",fontWeight:600,color:d.alfa!=null?clr(d.alfa):C.textDim,fontSize:11}}>{d.alfa!=null?fmt(d.alfa):"—"}</td>
              {d.p.map((g,j)=>(
                <td key={j} style={{padding:"10px 8px",textAlign:"right",fontFamily:"monospace",color:clr(g),fontSize:10,fontWeight:Math.abs(g)>10?700:400}}>{g!==0?fmt(g,1):"—"}</td>
              ))}
            </tr>);
          })}</tbody>
        </table>
      </div>
    </Card>

    {/* CHARTS */}
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:13,marginBottom:12}}>📊 Toplam Getiri</div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData} layout="vertical" margin={{left:65,right:20}}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} horizontal={false}/>
            <XAxis type="number" tick={{fill:C.textDim,fontSize:10}} tickFormatter={v=>`%${v}`}/>
            <YAxis type="category" dataKey="ad" tick={{fill:C.textMuted,fontSize:10}} width={60}/>
            <Tooltip content={<TT/>}/>
            <Bar dataKey="getiri" radius={[0,4,4,0]} barSize={16}>
              {barData.map((e,i)=>(<Cell key={i} fill={e.bench?C.textDim:e.getiri>=0?C.green:C.red} fillOpacity={e.bench?.4:.8}/>))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:13,marginBottom:12}}>📈 İlk 5 Kümülatif</div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={cumData} margin={{left:5,right:5}}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
            <XAxis dataKey="p" tick={{fill:C.textDim,fontSize:10}}/>
            <YAxis tick={{fill:C.textDim,fontSize:10}} domain={["auto","auto"]}/>
            <Tooltip content={<TT/>}/>
            {PLAYERS.slice(0,5).map((y,i)=>(<Line key={y.ad} type="monotone" dataKey={y.ad} stroke={PAL[i]} strokeWidth={2.5} dot={{r:3,fill:PAL[i]}}/>))}
            <Line type="monotone" dataKey="BIST 100" stroke={C.textDim} strokeWidth={1.5} strokeDasharray="6 3" dot={false}/>
          </LineChart>
        </ResponsiveContainer>
      </Card>
    </div>
  </div>);
};

// ═══════════════════════════════════════════════════════
// PAGE 2: YARIŞMACI PROFİLİ
// ═══════════════════════════════════════════════════════
const PageProfile = ({ad,onBack}) => {
  const d = DATA.find(x=>x.ad===ad); if(!d) return null;
  const rank = PLAYERS.indexOf(d)+1;
  const ret = d.pf-100;
  const wr = d.p.slice(0,5).filter(g=>g>0).length;
  const best = Math.max(...d.p.slice(0,5));
  const worst = Math.min(...d.p.slice(0,5));
  const cumD = cumSeries(d.p.slice(0,5));
  const bist = BENCHMARKS.find(b=>b.ad==="BIST 100");
  const bistCum = bist?cumSeries(bist.p.slice(0,5)):[];

  const compData = PERIYOTLAR.slice(0,5).map((lbl,i)=>({p:lbl,[ad]:d.p[i],"BIST":bist?bist.p[i]:0}));
  const cumComp = PERIYOTLAR.slice(0,5).map((lbl,i)=>({p:lbl,[ad]:cumD[i+1]?.v||100,"BIST":bistCum[i+1]?.v||100}));

  const radarMax = {getiri:Math.max(...PLAYERS.map(p=>Math.abs(p.pf-100)))||1,vol:Math.max(...PLAYERS.map(p=>p.vol))||1,sh:Math.max(...PLAYERS.map(p=>Math.abs((p.pf-100)/(p.vol||1))))||1};
  const radarData = [
    {m:"Getiri",v:Math.max(0,ret/radarMax.getiri*100)},
    {m:"İstikrar",v:Math.max(0,(1-d.vol/radarMax.vol)*100)},
    {m:"Kazanma",v:wr/5*100},
    {m:"Sharpe",v:Math.max(0,((ret/(d.vol||1))/radarMax.sh)*100)},
    {m:"Dayanıklılık",v:Math.max(0,(1-Math.abs(d.dd)/(Math.max(...PLAYERS.map(p=>Math.abs(p.dd)))||1))*100)},
  ];

  // Periyot sıralamaları
  const pRank = d.p.slice(0,5).map((_,i)=>{
    const sorted=[...PLAYERS].sort((a,b)=>b.p[i]-a.p[i]);
    return sorted.findIndex(x=>x.ad===ad)+1;
  });

  return (<div>
    <div style={{display:"flex",alignItems:"center",gap:14,marginBottom:20}}>
      <button onClick={onBack} style={{background:C.surface,border:`1px solid ${C.border}`,color:C.textMuted,borderRadius:8,padding:"7px 12px",cursor:"pointer",fontSize:12,fontFamily:"inherit"}}>← Geri</button>
      <div style={{width:44,height:44,borderRadius:"50%",background:`linear-gradient(135deg,${PAL[(rank-1)%PAL.length]}44,${PAL[(rank-1)%PAL.length]}11)`,border:`3px solid ${PAL[(rank-1)%PAL.length]}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:18,fontWeight:800,color:PAL[(rank-1)%PAL.length]}}>{ad[0]}</div>
      <div>
        <div style={{color:C.text,fontSize:20,fontWeight:800}}>{ad}</div>
        <div style={{display:"flex",gap:6,marginTop:2}}>
          <span style={{background:C.gold+"22",color:C.gold,fontSize:9,fontWeight:700,padding:"2px 8px",borderRadius:20}}>{medal(rank-1)} Sıra</span>
          {ret>(bist?.pf-100||0)&&<span style={{background:C.green+"22",color:C.green,fontSize:9,fontWeight:700,padding:"2px 8px",borderRadius:20}}>BIST+</span>}
        </div>
      </div>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(130px,1fr))",gap:8,marginBottom:18}}>
      <KPI icon="💰" label="Portföy" value={fmt(d.pf)} color={C.text}/>
      <KPI icon="📊" label="Getiri" value={fmtPct(ret)} color={clr(ret)}/>
      <KPI icon="⚡" label="En İyi" value={fmtPct(best)} color={C.green}/>
      <KPI icon="💀" label="En Kötü" value={fmtPct(worst)} color={C.red}/>
      <KPI icon="📉" label="Volatilite" value={fmt(d.vol)} sub={d.vol<6?"Düşük":d.vol<10?"Orta":"Yüksek"}/>
      <KPI icon="🛡️" label="Max DD" value={`${fmt(d.dd)}%`} color={C.red}/>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:18}}>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>📈 Kümülatif vs BIST</div>
        <ResponsiveContainer width="100%" height={230}>
          <LineChart data={cumComp}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
            <XAxis dataKey="p" tick={{fill:C.textDim,fontSize:10}}/>
            <YAxis tick={{fill:C.textDim,fontSize:10}} domain={["auto","auto"]}/>
            <Tooltip content={<TT/>}/>
            <Line type="monotone" dataKey={ad} stroke={C.gold} strokeWidth={3} dot={{r:4,fill:C.gold}}/>
            <Line type="monotone" dataKey="BIST" stroke={C.textDim} strokeWidth={1.5} strokeDasharray="6 3" dot={false}/>
          </LineChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>🎯 Performans Profili</div>
        <ResponsiveContainer width="100%" height={230}>
          <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="65%">
            <PolarGrid stroke={C.border}/>
            <PolarAngleAxis dataKey="m" tick={{fill:C.textMuted,fontSize:10}}/>
            <PolarRadiusAxis tick={false} axisLine={false} domain={[0,100]}/>
            <Radar dataKey="v" stroke={C.gold} fill={C.gold} fillOpacity={.15} strokeWidth={2}/>
          </RadarChart>
        </ResponsiveContainer>
      </Card>
    </div>

    {/* Periyot bar + karne */}
    <div style={{display:"grid",gridTemplateColumns:"1.2fr 1fr",gap:14}}>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>📊 Periyot Getiri vs BIST</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={compData}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false}/>
            <XAxis dataKey="p" tick={{fill:C.textDim,fontSize:10}}/>
            <YAxis tick={{fill:C.textDim,fontSize:10}} tickFormatter={v=>`%${v}`}/>
            <Tooltip content={<TT/>}/>
            <Bar dataKey={ad} fill={C.gold} radius={[4,4,0,0]} barSize={18}/>
            <Bar dataKey="BIST" fill={C.textDim} radius={[4,4,0,0]} barSize={12} fillOpacity={.5}/>
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card style={{padding:"14px 16px"}}>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:8}}>📋 Periyot Karnesi</div>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
          <thead><tr>{["P","Getiri","Sıra"].map((h,i)=>(<th key={i} style={{padding:"5px 6px",textAlign:i===0?"left":"right",color:C.textDim,fontSize:9,fontWeight:600,borderBottom:`1px solid ${C.border}`}}>{h}</th>))}</tr></thead>
          <tbody>{PERIYOTLAR.slice(0,5).map((lbl,i)=>(
            <tr key={i} style={{borderBottom:`1px solid ${C.border}22`}}>
              <td style={{padding:"5px 6px",color:C.textMuted}}>{lbl}</td>
              <td style={{padding:"5px 6px",textAlign:"right",fontFamily:"monospace",fontWeight:600,color:clr(d.p[i])}}>{fmtPct(d.p[i])}</td>
              <td style={{padding:"5px 6px",textAlign:"right"}}><span style={{background:pRank[i]<=3?C.gold+"22":C.surface,color:pRank[i]<=3?C.gold:C.textMuted,padding:"1px 8px",borderRadius:10,fontSize:10,fontWeight:600}}>{pRank[i]}/{PLAYERS.length}</span></td>
            </tr>
          ))}</tbody>
        </table>
      </Card>
    </div>
  </div>);
};

// ═══════════════════════════════════════════════════════
// PAGE 3: HİSSE İCMAL
// ═══════════════════════════════════════════════════════
const PageIcmal = () => {
  const [period,setPeriod] = useState("6P");
  const data = period==="6P"?ICMAL_6P:ICMAL_5P;
  const total = data.reduce((s,d)=>s+d.tl,0);

  const treeData = data.slice(0,12).map((d,i)=>({name:d.h,size:d.tl,pay:d.pay,color:PAL[i%PAL.length]}));

  return (<div>
    <div style={{display:"flex",gap:6,marginBottom:16}}>
      {["6P","5P"].map(p=>(<button key={p} onClick={()=>setPeriod(p)} style={{background:period===p?C.accent+"22":"transparent",color:period===p?C.text:C.textMuted,border:`1px solid ${period===p?C.accent+"55":"transparent"}`,borderRadius:8,padding:"7px 16px",cursor:"pointer",fontWeight:period===p?700:400,fontSize:12,fontFamily:"inherit"}}>{p}</button>))}
    </div>

    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:18}}>
      <KPI icon="📊" label="Toplam Hisse" value={data.length} color={C.cyan} sub={`${period} portföyleri`}/>
      <KPI icon="💰" label="Toplam TL" value={fmt(total,0)} color={C.gold} sub="11 yarışmacı toplamı"/>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      {/* PIE */}
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:8}}>🥧 Dağılım (İlk 8 + Diğer)</div>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={[...data.slice(0,8),{h:"Diğer",tl:data.slice(8).reduce((s,d)=>s+d.tl,0),pay:+(100-data.slice(0,8).reduce((s,d)=>s+d.pay,0)).toFixed(1)}]}
              dataKey="tl" nameKey="h" cx="50%" cy="50%" innerRadius={55} outerRadius={95} paddingAngle={2} strokeWidth={0}>
              {[...data.slice(0,8),{h:"Diğer"}].map((_,i)=>(<Cell key={i} fill={i<8?PAL[i]:C.textDim}/>))}
            </Pie>
            <Tooltip formatter={(v,n)=>[`${fmt(v,0)} TL`,n]}/>
          </PieChart>
        </ResponsiveContainer>
      </Card>

      {/* TABLE */}
      <Card style={{padding:0,overflow:"hidden"}}>
        <div style={{padding:"12px 16px",borderBottom:`1px solid ${C.border}`,color:C.text,fontWeight:600,fontSize:12}}>📋 Hisse Detay — {period}</div>
        <div style={{maxHeight:280,overflowY:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
            <thead><tr style={{background:C.bg2,position:"sticky",top:0}}>
              {["Hisse","TL","Kişi","% Pay"].map((h,i)=>(<th key={i} style={{padding:"7px 10px",textAlign:i===0?"left":"right",color:C.textDim,fontSize:9,fontWeight:700}}>{h}</th>))}
            </tr></thead>
            <tbody>{data.map((d,i)=>(
              <tr key={i} style={{borderBottom:`1px solid ${C.border}22`}}>
                <td style={{padding:"5px 10px",fontWeight:600,color:C.text}}>
                  <div style={{display:"flex",alignItems:"center",gap:5}}>
                    <div style={{width:4,height:16,borderRadius:2,background:PAL[i%PAL.length]}}/>
                    {d.h}
                  </div>
                </td>
                <td style={{padding:"5px 10px",textAlign:"right",fontFamily:"monospace",color:C.textMuted}}>{fmt(d.tl,0)}</td>
                <td style={{padding:"5px 10px",textAlign:"right",color:C.textMuted}}>{d.kisi}</td>
                <td style={{padding:"5px 10px",textAlign:"right"}}>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"flex-end",gap:5}}>
                    <div style={{width:40,height:4,borderRadius:2,background:C.bg2,overflow:"hidden"}}><div style={{width:`${d.pay*4}%`,height:"100%",background:PAL[i%PAL.length],borderRadius:2}}/></div>
                    <span style={{fontFamily:"monospace",fontSize:10,color:C.textMuted}}>{d.pay}</span>
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
    </div>
  </div>);
};

// ═══════════════════════════════════════════════════════
// PAGE 5: İSTATİSTİKLER
// ═══════════════════════════════════════════════════════
const PageStats = () => {
  const allPerfs=[];PLAYERS.forEach(d=>{d.p.slice(0,5).forEach((g,i)=>{allPerfs.push({ad:d.ad,p:PERIYOTLAR[i],g});});});
  allPerfs.sort((a,b)=>b.g-a.g);
  const bist=BENCHMARKS.find(b=>b.ad==="BIST 100");
  const beaters=PERIYOTLAR.slice(0,5).map((lbl,i)=>{const c=PLAYERS.filter(d=>d.p[i]>(bist?.p[i]||0)).length;return{p:lbl,Yenen:c,Yenilen:PLAYERS.length-c};});

  return (<div>
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:18}}>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>🏆 En İyi 10 Performans</div>
        {allPerfs.slice(0,10).map((p,i)=>(
          <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"6px 0",borderBottom:i<9?`1px solid ${C.border}22`:"none"}}>
            <div style={{display:"flex",alignItems:"center",gap:6}}>
              <span style={{color:C.textDim,fontSize:10,width:18}}>{i+1}.</span>
              <span style={{color:C.text,fontSize:12,fontWeight:500}}>{p.ad}</span>
              <span style={{color:C.textDim,fontSize:10}}>{p.p}</span>
            </div>
            <Glow color={C.green}><span style={{fontFamily:"monospace",fontWeight:700,fontSize:12}}>{fmtPct(p.g)}</span></Glow>
          </div>
        ))}
      </Card>
      <Card>
        <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>💀 En Kötü 10 Performans</div>
        {allPerfs.slice(-10).reverse().map((p,i)=>(
          <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"6px 0",borderBottom:i<9?`1px solid ${C.border}22`:"none"}}>
            <div style={{display:"flex",alignItems:"center",gap:6}}>
              <span style={{color:C.textDim,fontSize:10,width:18}}>{i+1}.</span>
              <span style={{color:C.text,fontSize:12,fontWeight:500}}>{p.ad}</span>
              <span style={{color:C.textDim,fontSize:10}}>{p.p}</span>
            </div>
            <Glow color={C.red}><span style={{fontFamily:"monospace",fontWeight:700,fontSize:12}}>{fmtPct(p.g)}</span></Glow>
          </div>
        ))}
      </Card>
    </div>
    <Card>
      <div style={{color:C.text,fontWeight:600,fontSize:12,marginBottom:10}}>📊 BIST'i Yenen Sayısı</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={beaters}>
          <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false}/>
          <XAxis dataKey="p" tick={{fill:C.textDim,fontSize:10}}/>
          <YAxis tick={{fill:C.textDim,fontSize:10}}/>
          <Tooltip content={<TT/>}/>
          <Bar dataKey="Yenen" fill={C.green} radius={[4,4,0,0]} barSize={24}/>
          <Bar dataKey="Yenilen" fill={C.red} radius={[4,4,0,0]} barSize={24} fillOpacity={.4}/>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  </div>);
};

// ═══════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════
export default function App() {
  const [page,setPage]=useState("overview");
  const [selPlayer,setSelPlayer]=useState(null);
  const go=p=>{setPage(p);setSelPlayer(null);};
  const selectPlayer=ad=>{setSelPlayer(ad);setPage("profile");};

  return (
    <div style={{background:`linear-gradient(180deg,${C.bg} 0%,${C.bg2} 100%)`,minHeight:"100vh",color:C.text,fontFamily:"'DM Sans','Segoe UI',sans-serif"}}>
      {/* HEADER */}
      <div style={{background:`linear-gradient(180deg,${C.surface} 0%,transparent 100%)`,borderBottom:`1px solid ${C.border}`,padding:"16px 24px 0"}}>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{fontSize:24,fontWeight:900,letterSpacing:-1,background:`linear-gradient(135deg,${C.gold},${C.green})`,WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>YGF</div>
            <div><div style={{color:C.text,fontSize:14,fontWeight:700}}>YGF</div>
            <div style={{color:C.textDim,fontSize:10}}>Sai Amatör Yatırım — 2026</div></div>
          </div>
          <div style={{textAlign:"right"}}>
            <div style={{color:C.textMuted,fontSize:10}}>6. Periyot Aktif</div>
            <div style={{color:C.textDim,fontSize:9}}>13.03 → 27.03.2026</div>
          </div>
        </div>
        <div style={{display:"flex",gap:3}}>
          <NavBtn active={page==="overview"} onClick={()=>go("overview")} icon="🏠">Genel Bakış</NavBtn>
          <NavBtn active={page==="profile"} onClick={()=>{if(!selPlayer)selectPlayer(PLAYERS[0]?.ad);else setPage("profile");}} icon="👤">Profil</NavBtn>
          <NavBtn active={page==="icmal"} onClick={()=>go("icmal")} icon="📑">Hisse İcmal</NavBtn>
          <NavBtn active={page==="stats"} onClick={()=>go("stats")} icon="📊">İstatistik</NavBtn>
        </div>
      </div>

      {/* CONTENT */}
      <div style={{padding:"20px 24px",maxWidth:1140,margin:"0 auto"}}>
        {page==="overview"&&<PageOverview onSelect={selectPlayer}/>}
        {page==="profile"&&selPlayer&&<PageProfile ad={selPlayer} onBack={()=>go("overview")}/>}
        {page==="icmal"&&<PageIcmal/>}
        {page==="stats"&&<PageStats/>}
      </div>

      <div style={{padding:"14px 24px",borderTop:`1px solid ${C.border}`,textAlign:"center"}}>
        <span style={{color:C.textDim,fontSize:9}}>Sai Amatör Yatırım © 2026 — Dashboard v2</span>
      </div>
    </div>
  );
}

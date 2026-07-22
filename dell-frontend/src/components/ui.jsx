import React, { useState, useEffect, useRef } from "react";
import { T as NIGHT, useTheme } from "../lib/auth.jsx";

function useT() { const c = useTheme(); return c?.T || NIGHT; }

/* ============================ animated background ========================= */
export function ScanGrid() {
  return null;
}

/* -------------------------------- Logo ----------------------------------- */
export function Logo({ size = 26 }) {
  const T = useT();
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <rect x="2" y="2" width="28" height="28" rx="2" stroke={T.dell} strokeWidth="1.5" />
      <circle cx="16" cy="16" r="6" stroke={T.dell} strokeWidth="1.5" />
      <path d="M16 4v6M16 22v6M4 16h6M22 16h6" stroke={T.dell} strokeWidth="1.5" />
      <circle cx="16" cy="16" r="1.5" fill={T.dell} />
    </svg>
  );
}

/* ------------------------------- Button ---------------------------------- */
export function Btn({ children, onClick, variant = "solid", tone, full, type = "button", disabled, size = "md" }) {
  const T = useT();
  if (tone == null) tone = T.dell;
  const [hov, setHov] = useState(false);
  const pad = size === "lg" ? "14px 26px" : size === "sm" ? "7px 14px" : "11px 20px";
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        position: "relative", fontFamily: T.mono, fontSize: size === "sm" ? 12 : 13, fontWeight: 600,
        letterSpacing: "0.06em", textTransform: "uppercase", padding: pad, cursor: disabled ? "not-allowed" : "pointer",
        border: `1px solid ${variant === "solid" ? tone : T.lineHi}`, borderRadius: 2, width: full ? "100%" : "auto",
        color: variant === "solid" ? "#ffffff" : tone, background: variant === "solid" ? tone : "transparent",
        overflow: "hidden", transition: "all .18s ease", opacity: disabled ? 0.5 : 1,
        boxShadow: hov && !disabled ? `0 2px 5px rgba(0,0,0,0.15)` : "none",
        transform: hov && !disabled ? "translateY(-1px)" : "none",
      }}>
      <span style={{ position: "relative", zIndex: 2 }}>{children}</span>
    </button>
  );
}
// Removed Corner function

/* ------------------------------- Panel ----------------------------------- */
export function Panel({ children, style, pad = 22, className = "" }) {
  const T = useT();
  const box = {
    background: T.panel,
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)",
  };
  return <div className={className} style={{ position: "relative", ...box, border: `1px solid ${T.line}`, borderRadius: 8, padding: pad, ...style }}>{children}</div>;
}

export function Eyebrow({ children }) {
  const T = useT();
  return <div style={{ fontFamily: T.mono, fontSize: 11, letterSpacing: "0.18em", textTransform: "uppercase", color: T.inkFaint, display: "flex", alignItems: "center", gap: 8 }}>
    <span style={{ width: 14, height: 1, background: T.lineHi }} />{children}
  </div>;
}

export function Field({ label, hint, ...props }) {
  const T = useT();
  const [foc, setFoc] = useState(false);
  return (
    <label style={{ display: "block", marginBottom: 18 }}>
      <span style={{ display: "block", fontFamily: T.mono, fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: T.inkFaint, marginBottom: 8 }}>{label}</span>
      <input {...props} onFocus={() => setFoc(true)} onBlur={() => setFoc(false)}
        style={{ width: "100%", boxSizing: "border-box", padding: "12px 14px", background: T.bg, color: T.ink, fontFamily: T.mono, fontSize: 14, border: `1px solid ${foc ? T.dell : T.line}`, borderRadius: 2, outline: "none", transition: "border .18s", boxShadow: foc ? `0 0 0 3px ${T.dell}22` : "none" }} />
      {hint && <span style={{ display: "block", fontFamily: T.mono, fontSize: 10, color: T.inkFaint, marginTop: 6 }}>{hint}</span>}
    </label>
  );
}

export function Tag({ children, tone }) {
  const T = useT();
  return <span style={{ fontFamily: T.mono, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em", color: tone, border: `1px solid ${tone}55`, background: `${tone}12`, padding: "3px 9px", borderRadius: 2, whiteSpace: "nowrap" }}>{children}</span>;
}

export function ScoreDial({ score, tone, size = 88 }) {
  const T = useT();
  const s = score ?? 0, r = size * 0.38, circ = 2 * Math.PI * r, off = circ * (1 - s / 100), c = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={c} cy={c} r={r} fill="none" stroke={T.line} strokeWidth="4" />
      <circle cx={c} cy={c} r={r} fill="none" stroke={tone} strokeWidth="4" strokeDasharray={circ} strokeDashoffset={off} strokeLinecap="round" transform={`rotate(-90 ${c} ${c})`} style={{ transition: "stroke-dashoffset 1s ease" }} />
      <text x={c} y={c - 2} textAnchor="middle" fontFamily={T.mono} fontSize={size * 0.25} fontWeight="700" fill={tone}>{score ?? "—"}</text>
      <text x={c} y={c + size * 0.15} textAnchor="middle" fontFamily={T.mono} fontSize={size * 0.09} fill={T.inkFaint} letterSpacing="1">/ 100</text>
    </svg>
  );
}

/* Radar sweep for the running state. */
export function Radar({ size = 120 }) {
  const T = useT();
  const c = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ margin: "0 auto", display: "block" }}>
      {[0.87, 0.57, 0.27].map((f, i) => <circle key={i} cx={c} cy={c} r={c * f} fill="none" stroke={T.line} strokeWidth="1" />)}
      <line x1={c} y1={c - c * 0.87} x2={c} y2={c + c * 0.87} stroke={T.line} />
      <line x1={c - c * 0.87} y1={c} x2={c + c * 0.87} y2={c} stroke={T.line} />
      <g style={{ transformOrigin: `${c}px ${c}px`, animation: "spin 2s linear infinite" }}>
        <path d={`M${c} ${c} L${c} ${c - c * 0.87} A${c * 0.87} ${c * 0.87} 0 0 1 ${c + c * 0.62} ${c - c * 0.6} Z`} fill={T.dell} opacity="0.16" />
        <line x1={c} y1={c} x2={c} y2={c - c * 0.87} stroke={T.dell} strokeWidth="1.5" />
      </g>
      <circle cx={c} cy={c} r="2.5" fill={T.dell} />
    </svg>
  );
}

/* Full-page loading + error + empty helpers. */
export function Loading({ label = "Loading…" }) {
  const T = useT();
  return <div style={{ padding: 60, textAlign: "center", fontFamily: T.mono, fontSize: 13, color: T.inkDim }}>
    <Radar size={80} /><div style={{ marginTop: 16 }}>{label}</div>
  </div>;
}
export function ErrorNote({ children }) {
  const T = useT();
  return <div style={{ fontFamily: T.mono, fontSize: 12.5, color: T.red, padding: "10px 14px", border: `1px solid ${T.red}44`, background: `${T.red}10`, borderRadius: 2 }}>⚠ {children}</div>;
}
export function Empty({ children }) {
  const T = useT();
  return <div style={{ padding: 50, textAlign: "center", fontFamily: T.mono, fontSize: 13, color: T.inkFaint }}>{children}</div>;
}

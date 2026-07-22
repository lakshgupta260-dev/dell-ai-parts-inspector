import React, { createContext, useContext, useState, useEffect } from "react";

/* ============================================================================
   Theme system — two palettes.
     NIGHT (default): black background, green laser, light text (the current look)
     DAY: white/light-grey background, dark text, toned-down green laser
   Components read the active palette via useTheme().T. Toggle lives in the
   header, choice persists, default is night.
   ========================================================================== */

const NIGHT = {
  name: "night",
  bg: "#0A0F1C",
  bg2: "#111827",
  panel: "#162032",
  panelHi: "#1E293B",
  line: "#1E293B",
  lineHi: "#334155",
  ink: "#F8FAFC",
  inkDim: "#94A3B8",
  inkFaint: "#64748B",
  dell: "#0076CE",
  dellHi: "#3B82F6",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  laser: { r: 59, g: 130, b: 246 },
  gridOpacity: 0.05,
  nodeOpacity: 0.2,
  beamOpacity: 0.05,
  lineOpacity: 0.1,
  mono: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', ui-monospace, monospace",
  sans: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
};

const DAY = {
  name: "day",
  bg: "#F8FAFC",
  bg2: "#F1F5F9",
  panel: "#FFFFFF",
  panelHi: "#F8FAFC",
  line: "#E2E8F0",
  lineHi: "#CBD5E1",
  ink: "#0F172A",
  inkDim: "#475569",
  inkFaint: "#64748B",
  dell: "#0076CE",
  dellHi: "#005C9E",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  laser: { r: 0, g: 118, b: 206 },
  gridOpacity: 0.03,
  nodeOpacity: 0.1,
  beamOpacity: 0.03,
  lineOpacity: 0.1,
  mono: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', ui-monospace, monospace",
  sans: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
};

/* Static export kept for any legacy import; equals the default (day). */
export const T = DAY;
export const THEMES = { night: NIGHT, day: DAY };

export const VERDICT = {
  AUTHENTIC: { key: "green", label: "Authentic" },
  SUSPICIOUS: { key: "amber", label: "Suspicious" },
  COUNTERFEIT: { key: "red", label: "Counterfeit" },
};
export function verdictTone(v, P = NIGHT) {
  const hit = VERDICT[v?.toUpperCase()];
  if (!hit) return { tone: P.inkFaint, label: v || "Pending" };
  return { tone: P[hit.key], label: hit.label };
}
export function scoreTone(s, P = NIGHT) {
  if (s == null) return P.inkFaint;
  if (s < 34) return P.green;
  if (s < 67) return P.amber;
  return P.red;
}

/* ------------------------------ Theme context ---------------------------- */
const ThemeCtx = createContext(null);
export function useTheme() { return useContext(ThemeCtx); }

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState(() => localStorage.getItem("pg_theme") || "day");
  useEffect(() => { localStorage.setItem("pg_theme", mode); }, [mode]);
  const toggle = () => setMode((m) => (m === "day" ? "night" : "day"));
  const Tp = THEMES[mode] || DAY;
  return <ThemeCtx.Provider value={{ mode, setMode, toggle, T: Tp }}>{children}</ThemeCtx.Provider>;
}

/* ------------------------------ Auth context ----------------------------- */
const AuthCtx = createContext(null);
export function useAuth() { return useContext(AuthCtx); }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("pg_user")); } catch { return null; }
  });
  const [token, setToken] = useState(() => localStorage.getItem("pg_token"));
  function signIn(data) {
    localStorage.setItem("pg_token", data.access_token);
    const u = { username: data.username, role: data.role };
    localStorage.setItem("pg_user", JSON.stringify(u));
    setToken(data.access_token); setUser(u);
  }
  function signOut() {
    localStorage.removeItem("pg_token"); localStorage.removeItem("pg_user");
    setToken(null); setUser(null);
  }
  useEffect(() => {
    const h = () => setToken(localStorage.getItem("pg_token"));
    window.addEventListener("storage", h);
    return () => window.removeEventListener("storage", h);
  }, []);
  return <AuthCtx.Provider value={{ user, token, signIn, signOut }}>{children}</AuthCtx.Provider>;
}

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
  bg: "#0B1A2F",
  bg2: "#12233D",
  panel: "#0F1F38",
  panelHi: "#152A4A",
  line: "#1D3557",
  lineHi: "#2A4B75",
  ink: "#F8F6F0",
  inkDim: "#E5D5C0",
  inkFaint: "#94A3B8",
  dell: "#E5D5C0",
  dellHi: "#D4C5B0",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  laser: { r: 229, g: 213, b: 192 },
  gridOpacity: 0.05,
  nodeOpacity: 0.2,
  beamOpacity: 0.05,
  lineOpacity: 0.1,
  mono: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', ui-monospace, monospace",
  sans: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
};

const DAY = {
  name: "day",
  bg: "#F8F6F0",
  bg2: "#F1EDE4",
  panel: "#FFFFFF",
  panelHi: "#F9F8F5",
  line: "#EAE5D9",
  lineHi: "#D5CFC1",
  ink: "#0F172A",
  inkDim: "#334155",
  inkFaint: "#64748B",
  dell: "#0F172A",
  dellHi: "#1E293B",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  laser: { r: 15, g: 23, b: 42 },
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

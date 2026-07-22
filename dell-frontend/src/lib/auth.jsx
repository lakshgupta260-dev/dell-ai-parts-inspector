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
  bg: "#000000",
  bg2: "#050a08",
  panel: "#0b1310",
  panelHi: "#101a15",
  line: "#1c2b23",
  lineHi: "#2c4638",
  ink: "#e8f4ee",
  inkDim: "#8ba99a",
  inkFaint: "#5c7568",
  dell: "#3ddc84",
  dellHi: "#5cff9d",
  green: "#3ddc84",
  amber: "#f5b53a",
  red: "#ff5a52",
  // scan-grid laser (bright green on black)
  laser: { r: 61, g: 220, b: 132 },
  gridOpacity: 0.10,
  nodeOpacity: 0.9,
  beamOpacity: 0.11,
  lineOpacity: 0.38,
  mono: "'IBM Plex Mono','JetBrains Mono',ui-monospace,monospace",
  sans: "'IBM Plex Sans','Inter',system-ui,sans-serif",
};

const DAY = {
  name: "day",
  bg: "#f5f7f6",
  bg2: "#eef2f0",
  panel: "#ffffff",
  panelHi: "#f4f8f6",
  line: "#dbe4df",
  lineHi: "#c2d0c9",
  ink: "#12201a",
  inkDim: "#486056",
  inkFaint: "#7d938a",
  dell: "#12a15a",        // deeper green so it reads on white
  dellHi: "#0c7d45",
  green: "#12a15a",
  amber: "#c47d05",
  red: "#d63a30",
  // toned-down green laser on light bg
  laser: { r: 26, g: 160, b: 92 },
  gridOpacity: 0.14,
  nodeOpacity: 0.5,
  beamOpacity: 0.07,
  lineOpacity: 0.28,
  mono: "'IBM Plex Mono','JetBrains Mono',ui-monospace,monospace",
  sans: "'IBM Plex Sans','Inter',system-ui,sans-serif",
};

/* Static export kept for any legacy import; equals the default (night). */
export const T = NIGHT;
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
  const [mode, setMode] = useState(() => localStorage.getItem("pg_theme") || "night");
  useEffect(() => { localStorage.setItem("pg_theme", mode); }, [mode]);
  const toggle = () => setMode((m) => (m === "night" ? "day" : "night"));
  const Tp = THEMES[mode] || NIGHT;
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

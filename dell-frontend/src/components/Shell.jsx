import React from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth, useTheme } from "../lib/auth.jsx";
import { Logo, Btn } from "./ui.jsx";

export default function Shell() {
  const { user, signOut } = useAuth();
  const { T, mode, toggle } = useTheme();
  const nav = useNavigate();
  const links = [["/", "Dashboard"], ["/new", "New Inspection"], ["/history", "History"]];

  const linkStyle = ({ isActive }) => ({
    position: "relative", padding: "8px 14px", fontFamily: T.sans, fontSize: 13, fontWeight: 600,
    letterSpacing: "0.01em", textDecoration: "none",
    color: isActive ? T.dellHi : T.inkDim, transition: "color .15s",
  });

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh" }}>
      <header style={{ position: "sticky", top: 0, zIndex: 10, background: mode === "night" ? "rgba(0,0,0,0.72)" : "rgba(245,247,246,0.82)", backdropFilter: "blur(12px)", borderBottom: `1px solid ${T.line}`, transition: "background-color .35s, border-color .35s" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 62, display: "flex", alignItems: "center", gap: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }} onClick={() => nav("/")}>
            <Logo /><span style={{ fontFamily: T.sans, fontWeight: 700, fontSize: 17, letterSpacing: "-0.01em", color: T.ink }}>Dell PartVision AI</span>
          </div>
          <nav style={{ display: "flex", gap: 4, flex: 1 }}>
            {links.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"} style={linkStyle}>
                {({ isActive }) => (<>
                  {label}
                  {isActive && <span style={{ position: "absolute", left: 14, right: 14, bottom: -1, height: 2, background: T.dell, boxShadow: `0 0 8px ${T.dell}` }} />}
                </>)}
              </NavLink>
            ))}
          </nav>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <ThemeToggle T={T} mode={mode} toggle={toggle} />
            <div style={{ textAlign: "right", lineHeight: 1.3 }}>
              <div style={{ fontFamily: T.sans, fontSize: 14, fontWeight: 600, color: T.ink }}>{user?.username}</div>
              <div style={{ fontFamily: T.sans, fontSize: 12, color: T.inkDim }}>{user?.role === "QA_MANAGER" ? "QA Manager" : "Inspector"}</div>
            </div>
            <div style={{ width: 34, height: 34, borderRadius: "50%", border: `1px solid ${T.lineHi}`, display: "grid", placeItems: "center", fontFamily: T.sans, fontSize: 14, fontWeight: 600, color: T.dellHi, background: T.panel }}>
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <Btn variant="ghost" tone={T.inkDim} size="sm" onClick={() => { signOut(); nav("/login"); }}>Sign out</Btn>
          </div>
        </div>
      </header>
      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "34px 24px 80px" }}>
        <Outlet />
      </main>
    </div>
  );
}

/* Day/Night toggle — sliding switch with sun / moon glyphs. Night is default. */
function ThemeToggle({ T, mode, toggle }) {
  const isDay = mode === "day";
  return (
    <button onClick={toggle} title={isDay ? "Switch to night" : "Switch to day"}
      style={{ position: "relative", width: 58, height: 28, borderRadius: 20, cursor: "pointer",
        border: `1px solid ${T.lineHi}`, background: isDay ? "#dfe7e2" : "#05100b",
        transition: "background .3s, border-color .3s", padding: 0, flexShrink: 0 }}>
      <span style={{ position: "absolute", left: 7, top: "50%", transform: "translateY(-50%)", fontSize: 12, opacity: isDay ? 0.9 : 0.3, transition: "opacity .3s" }}>☀</span>
      <span style={{ position: "absolute", right: 7, top: "50%", transform: "translateY(-50%)", fontSize: 11, opacity: isDay ? 0.25 : 0.9, transition: "opacity .3s" }}>☾</span>
      <span style={{ position: "absolute", top: 2, left: isDay ? 32 : 2, width: 22, height: 22, borderRadius: "50%",
        background: isDay ? "#c47d05" : T.dell,
        boxShadow: isDay ? "0 0 10px #c47d0588" : `0 0 10px ${T.dell}aa`,
        transition: "left .28s cubic-bezier(.4,1.3,.5,1), background .3s" }} />
    </button>
  );
}

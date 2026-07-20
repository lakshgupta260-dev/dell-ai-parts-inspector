import React from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth, T } from "../lib/auth.jsx";
import { Logo, Btn } from "./ui.jsx";

export default function Shell() {
  const { user, signOut } = useAuth();
  const nav = useNavigate();
  const links = [["/", "Dashboard"], ["/new", "New Inspection"], ["/history", "History"]];

  const linkStyle = ({ isActive }) => ({
    position: "relative", padding: "8px 14px", fontFamily: T.mono, fontSize: 12, fontWeight: 600,
    letterSpacing: "0.04em", textTransform: "uppercase", textDecoration: "none",
    color: isActive ? T.dellHi : T.inkDim, transition: "color .15s",
  });

  return (
    <div style={{ position: "relative", zIndex: 2, minHeight: "100vh" }}>
      <header style={{ position: "sticky", top: 0, zIndex: 10, background: `${T.bg}e8`, backdropFilter: "blur(12px)", borderBottom: `1px solid ${T.line}` }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 62, display: "flex", alignItems: "center", gap: 28 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }} onClick={() => nav("/")}>
            <Logo /><span style={{ fontFamily: T.sans, fontWeight: 700, fontSize: 17, letterSpacing: "-0.01em", color: T.ink }}>Dell Parts Inspector</span>
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
            <div style={{ textAlign: "right", lineHeight: 1.3 }}>
              <div style={{ fontFamily: T.mono, fontSize: 12, color: T.ink }}>{user?.username}</div>
              <div style={{ fontFamily: T.mono, fontSize: 10, color: T.inkFaint }}>{user?.role === "QA_MANAGER" ? "QA Manager" : "Inspector"}</div>
            </div>
            <div style={{ width: 32, height: 32, borderRadius: 2, border: `1px solid ${T.lineHi}`, display: "grid", placeItems: "center", fontFamily: T.mono, fontSize: 13, color: T.dellHi, background: T.panel }}>
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

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth, apiError } from "../lib/api.js";
import { useAuth, useTheme } from "../lib/auth.jsx";
import { Logo, ErrorNote, ThemeToggle } from "../components/ui.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const { T, mode, toggle } = useTheme();
  const nav = useNavigate();
  const [authMode, setAuthMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "INSPECTOR" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  async function submit(e) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const data = authMode === "login"
        ? await auth.login({ username: form.username, password: form.password })
        : await auth.register(form);
      signIn(data);
      nav("/");
    } catch (e) { setErr(apiError(e)); } finally { setBusy(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: T.bg, color: T.ink, transition: "background .3s" }}>
      {/* Header */}
      <div style={{ padding: "30px 60px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Logo size={28} />
          <span style={{ fontFamily: T.sans, fontWeight: 700, fontSize: 20, letterSpacing: "-0.01em" }}>Dell PartVision AI</span>
        </div>
        <ThemeToggle T={T} mode={mode} toggle={toggle} />
      </div>

      {/* Main Content Grid */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 60, padding: "20px 60px 80px", maxWidth: 1500, margin: "0 auto", width: "100%", alignItems: "center" }}>
        
        {/* Left Side: Hero */}
        <div style={{ paddingRight: 40, animation: "slideUp 0.6s ease-out forwards" }}>
          <h1 style={{ fontFamily: T.sans, fontSize: 62, fontWeight: 800, lineHeight: 1.1, letterSpacing: "-0.02em", color: T.ink, marginBottom: 24 }}>
            Automate inspections.<br /><span style={{ color: T.dell }}>One solution, total trust.</span>
          </h1>
          
          <div style={{ width: 40, height: 4, background: T.dell, marginBottom: 28 }} />
          
          <p style={{ fontFamily: T.sans, fontSize: 17, lineHeight: 1.6, color: T.inkDim, maxWidth: 540 }}>
            PartVision AI brings computer vision, OCR, and Large Language Model evaluation into a single dashboard — built for QA teams inspecting hardware authenticity at any scale.
          </p>

          <div style={{ display: "flex", gap: 60, marginTop: 48, borderTop: `1px solid ${T.line}`, paddingTop: 36 }}>
            <div>
              <div style={{ fontFamily: T.sans, fontSize: 28, fontWeight: 800, color: T.ink }}>90%</div>
              <div style={{ fontFamily: T.sans, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em", color: T.inkDim, marginTop: 4 }}>TIME SAVED</div>
            </div>
            <div>
              <div style={{ fontFamily: T.sans, fontSize: 28, fontWeight: 800, color: T.ink }}>60s</div>
              <div style={{ fontFamily: T.sans, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em", color: T.inkDim, marginTop: 4 }}>EVALUATION TIME</div>
            </div>
          </div>
        </div>

        {/* Right Side: Login Card */}
        <div style={{ justifySelf: "end", width: "100%", maxWidth: 480, animation: "slideUp 0.6s ease-out forwards", animationDelay: "0.1s", opacity: 0 }}>
          <div style={{ background: T.panel, borderRadius: 12, padding: 40, boxShadow: mode === "day" ? "0 25px 50px rgba(0,0,0,0.05)" : "0 25px 50px rgba(0,0,0,0.4)", border: `1px solid ${T.line}`, transition: "background .3s, border-color .3s" }}>
            
            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, marginBottom: 28, background: T.bg2, padding: 6, borderRadius: 8 }}>
              {["login", "register"].map((m) => (
                <button key={m} onClick={() => { setAuthMode(m); setErr(""); }} type="button"
                  style={{ flex: 1, padding: "12px", fontFamily: T.sans, fontSize: 13, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", cursor: "pointer", border: "none", borderRadius: 6, background: authMode === m ? T.panelHi : "transparent", color: authMode === m ? T.dell : T.inkFaint, transition: "all .2s ease", boxShadow: authMode === m ? `0 2px 5px rgba(0,0,0,0.05)` : "none" }}>
                  {m === "login" ? "Sign in" : "Create Profile"}
                </button>
              ))}
            </div>

            <form onSubmit={submit}>
              <div style={{ marginBottom: 20 }}>
                <span style={{ display: "block", fontFamily: T.sans, fontSize: 13, fontWeight: 700, color: T.ink, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Username</span>
                <input value={form.username} onChange={(e) => set("username", e.target.value)} required placeholder="j.inspector" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: T.bg, border: `1px solid ${T.line}`, borderRadius: 6, fontFamily: T.sans, fontSize: 15, color: T.ink, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = T.dell} onBlur={(e) => e.target.style.borderColor = T.line} />
              </div>
              
              {authMode === "register" && (
                <div style={{ marginBottom: 20 }}>
                  <span style={{ display: "block", fontFamily: T.sans, fontSize: 13, fontWeight: 700, color: T.ink, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Work Email</span>
                  <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required placeholder="you@dell.com" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: T.bg, border: `1px solid ${T.line}`, borderRadius: 6, fontFamily: T.sans, fontSize: 15, color: T.ink, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = T.dell} onBlur={(e) => e.target.style.borderColor = T.line} />
                </div>
              )}
              
              <div style={{ marginBottom: 24 }}>
                <span style={{ display: "block", fontFamily: T.sans, fontSize: 13, fontWeight: 700, color: T.ink, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Password</span>
                <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={authMode === "register" ? 8 : undefined} placeholder="••••••••" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: T.bg, border: `1px solid ${T.line}`, borderRadius: 6, fontFamily: T.sans, fontSize: 15, color: T.ink, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = T.dell} onBlur={(e) => e.target.style.borderColor = T.line} />
              </div>

              {authMode === "register" && (
                <div style={{ marginBottom: 28 }}>
                  <span style={{ display: "block", fontFamily: T.sans, fontSize: 13, fontWeight: 700, color: T.ink, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Role</span>
                  <div style={{ display: "flex", gap: 8 }}>
                    {[["INSPECTOR", "Inspector"], ["QA_MANAGER", "QA Manager"]].map(([v, label]) => (
                      <button type="button" key={v} onClick={() => set("role", v)}
                        style={{ flex: 1, padding: "12px", fontFamily: T.sans, fontSize: 14, fontWeight: 600, cursor: "pointer", borderRadius: 6, border: `1px solid ${form.role === v ? T.dell : T.line}`, background: form.role === v ? (mode === "night" ? "rgba(0,118,206,0.15)" : "rgba(0,118,206,0.05)") : T.panel, color: form.role === v ? T.dell : T.inkFaint, transition: "all .2s" }}>{label}</button>
                    ))}
                  </div>
                </div>
              )}

              {err && <div style={{ marginBottom: 20 }}><ErrorNote>{err}</ErrorNote></div>}
              
              <button type="submit" disabled={busy} style={{ width: "100%", padding: "16px", background: T.dell, color: "#fff", border: "none", borderRadius: 6, fontFamily: T.sans, fontSize: 15, fontWeight: 700, letterSpacing: "0.02em", cursor: busy ? "not-allowed" : "pointer", opacity: busy ? 0.7 : 1, transition: "opacity .2s" }}>
                {busy ? "Authenticating…" : authMode === "login" ? "SIGN IN →" : "CREATE PROFILE"}
              </button>
            </form>
            
            <div style={{ marginTop: 20, fontFamily: T.sans, fontSize: 12, color: T.inkFaint, textAlign: "center", background: T.bg2, padding: 12, borderRadius: 6 }}>
              Demo accounts: <b style={{ color: T.ink }}>j.inspector</b> / <b style={{ color: T.ink }}>m.qa</b><br/>Password: <b style={{ color: T.ink }}>password123</b>
            </div>
          </div>
        </div>
      </div>
      
      {/* Global CSS for the slide up animation */}
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        /* Make sure body margin is 0 since this is a full page background */
        body { margin: 0; }
      `}</style>
    </div>
  );
}

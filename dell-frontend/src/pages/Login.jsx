import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth, apiError } from "../lib/api.js";
import { useAuth } from "../lib/auth.jsx";
import { Logo, ErrorNote } from "../components/ui.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "INSPECTOR" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  // Hardcoded colors for the HackBridge landing page aesthetic
  const C = {
    navy: "#0B1A2F",
    sand: "#E5D5C0",
    white: "#FFFFFF",
    slate: "#94A3B8",
    cardBg: "#F8F6F0",
    inputBg: "#FFFFFF",
    line: "#D5CFC1",
    textDark: "#0F172A",
    textFaint: "#64748B",
    sans: "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', monospace"
  };

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  async function submit(e) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const data = mode === "login"
        ? await auth.login({ username: form.username, password: form.password })
        : await auth.register(form);
      signIn(data);
      nav("/");
    } catch (e) { setErr(apiError(e)); } finally { setBusy(false); }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: C.navy, color: C.white }}>
      {/* Header */}
      <div style={{ padding: "30px 60px", display: "flex", alignItems: "center", gap: 12 }}>
        <Logo size={28} />
        <span style={{ fontFamily: C.sans, fontWeight: 700, fontSize: 20, letterSpacing: "-0.01em" }}>Dell PartVision AI</span>
      </div>

      {/* Main Content Grid */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 60, padding: "20px 60px 80px", maxWidth: 1500, margin: "0 auto", width: "100%", alignItems: "center" }}>
        
        {/* Left Side: Hero */}
        <div style={{ paddingRight: 40, animation: "slideUp 0.6s ease-out forwards" }}>
          <div style={{ fontFamily: C.mono, fontSize: 12, fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: C.sand, display: "flex", gap: 16, alignItems: "center", marginBottom: 24 }}>
            <span>• PLATFORM OPERATIONAL</span> <span>• AI EVALUATION ASSIST</span>
          </div>
          
          <h1 style={{ fontFamily: C.sans, fontSize: 62, fontWeight: 800, lineHeight: 1.1, letterSpacing: "-0.02em", color: C.white, marginBottom: 24 }}>
            Automate inspections.<br /><span style={{ color: C.sand }}>One platform, total trust.</span>
          </h1>
          
          <div style={{ width: 40, height: 4, background: C.sand, marginBottom: 28 }} />
          
          <p style={{ fontFamily: C.sans, fontSize: 17, lineHeight: 1.6, color: C.slate, maxWidth: 540 }}>
            PartVision AI brings computer vision, OCR, and Large Language Model evaluation into a single dashboard — built for QA teams inspecting hardware authenticity at any scale.
          </p>

          <div style={{ display: "flex", gap: 60, marginTop: 48, borderTop: `1px solid rgba(255,255,255,0.1)`, paddingTop: 36 }}>
            <div>
              <div style={{ fontFamily: C.sans, fontSize: 28, fontWeight: 800, color: C.white }}>100%</div>
              <div style={{ fontFamily: C.sans, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em", color: C.slate, marginTop: 4 }}>COVERAGE</div>
            </div>
            <div>
              <div style={{ fontFamily: C.sans, fontSize: 28, fontWeight: 800, color: C.white }}>&lt;2s</div>
              <div style={{ fontFamily: C.sans, fontSize: 11, fontWeight: 600, letterSpacing: "0.05em", color: C.slate, marginTop: 4 }}>EVALUATION TIME</div>
            </div>
          </div>
        </div>

        {/* Right Side: Login Card */}
        <div style={{ justifySelf: "end", width: "100%", maxWidth: 480, animation: "slideUp 0.6s ease-out forwards", animationDelay: "0.1s", opacity: 0 }}>
          <div style={{ background: C.cardBg, borderRadius: 12, padding: 40, boxShadow: "0 25px 50px rgba(0,0,0,0.3)" }}>
            
            {/* Tabs */}
            <div style={{ display: "flex", gap: 4, marginBottom: 28, background: "#EAE5D9", padding: 6, borderRadius: 8 }}>
              {["login", "register"].map((m) => (
                <button key={m} onClick={() => { setMode(m); setErr(""); }}
                  style={{ flex: 1, padding: "12px", fontFamily: C.sans, fontSize: 13, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", cursor: "pointer", border: "none", borderRadius: 6, background: mode === m ? C.navy : "transparent", color: mode === m ? C.white : C.textFaint, transition: "all .2s ease" }}>
                  {m === "login" ? "Sign in" : "Create Profile"}
                </button>
              ))}
            </div>

            <form onSubmit={submit}>
              <div style={{ marginBottom: 20 }}>
                <span style={{ display: "block", fontFamily: C.sans, fontSize: 13, fontWeight: 700, color: C.textDark, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Username</span>
                <input value={form.username} onChange={(e) => set("username", e.target.value)} required placeholder="j.inspector" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: C.inputBg, border: `1px solid ${C.line}`, borderRadius: 6, fontFamily: C.sans, fontSize: 15, color: C.textDark, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = C.navy} onBlur={(e) => e.target.style.borderColor = C.line} />
              </div>
              
              {mode === "register" && (
                <div style={{ marginBottom: 20 }}>
                  <span style={{ display: "block", fontFamily: C.sans, fontSize: 13, fontWeight: 700, color: C.textDark, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Work Email</span>
                  <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required placeholder="you@dell.com" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: C.inputBg, border: `1px solid ${C.line}`, borderRadius: 6, fontFamily: C.sans, fontSize: 15, color: C.textDark, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = C.navy} onBlur={(e) => e.target.style.borderColor = C.line} />
                </div>
              )}
              
              <div style={{ marginBottom: 24 }}>
                <span style={{ display: "block", fontFamily: C.sans, fontSize: 13, fontWeight: 700, color: C.textDark, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Password</span>
                <input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={mode === "register" ? 8 : undefined} placeholder="••••••••" style={{ width: "100%", boxSizing: "border-box", padding: "14px 16px", background: C.inputBg, border: `1px solid ${C.line}`, borderRadius: 6, fontFamily: C.sans, fontSize: 15, color: C.textDark, outline: "none", transition: "border .2s" }} onFocus={(e) => e.target.style.borderColor = C.navy} onBlur={(e) => e.target.style.borderColor = C.line} />
              </div>

              {mode === "register" && (
                <div style={{ marginBottom: 28 }}>
                  <span style={{ display: "block", fontFamily: C.sans, fontSize: 13, fontWeight: 700, color: C.textDark, marginBottom: 8, letterSpacing: "0.02em", textTransform: "uppercase" }}>Role</span>
                  <div style={{ display: "flex", gap: 8 }}>
                    {[["INSPECTOR", "Inspector"], ["QA_MANAGER", "QA Manager"]].map(([v, label]) => (
                      <button type="button" key={v} onClick={() => set("role", v)}
                        style={{ flex: 1, padding: "12px", fontFamily: C.sans, fontSize: 14, fontWeight: 600, cursor: "pointer", borderRadius: 6, border: `1px solid ${form.role === v ? C.navy : C.line}`, background: form.role === v ? "rgba(11,26,47,0.05)" : C.white, color: form.role === v ? C.navy : C.textFaint, transition: "all .2s" }}>{label}</button>
                    ))}
                  </div>
                </div>
              )}

              {err && <div style={{ marginBottom: 20 }}><ErrorNote>{err}</ErrorNote></div>}
              
              <button type="submit" disabled={busy} style={{ width: "100%", padding: "16px", background: C.navy, color: C.white, border: "none", borderRadius: 6, fontFamily: C.sans, fontSize: 15, fontWeight: 700, letterSpacing: "0.02em", cursor: busy ? "not-allowed" : "pointer", opacity: busy ? 0.7 : 1, transition: "opacity .2s" }}>
                {busy ? "Authenticating…" : mode === "login" ? "SIGN IN →" : "CREATE PROFILE"}
              </button>
            </form>
            
            <div style={{ marginTop: 20, fontFamily: C.sans, fontSize: 12, color: C.textFaint, textAlign: "center", background: "rgba(0,0,0,0.03)", padding: 12, borderRadius: 6 }}>
              Demo accounts: <b>j.inspector</b> / <b>m.qa</b><br/>Password: <b>password123</b>
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

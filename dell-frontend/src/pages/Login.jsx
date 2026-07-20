import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { auth, apiError } from "../lib/api.js";
import { useAuth, T } from "../lib/auth.jsx";
import { Panel, Btn, Field, Logo, ErrorNote } from "../components/ui.jsx";

export default function Login() {
  const { signIn } = useAuth();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "INSPECTOR" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

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
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", position: "relative", zIndex: 2, padding: 20 }}>
      <div style={{ width: "min(430px,100%)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6, justifyContent: "center" }}>
          <Logo size={30} />
          <span style={{ fontFamily: T.sans, fontWeight: 700, fontSize: 25, letterSpacing: "-0.02em", color: T.ink }}>Dell Parts Inspector</span>
        </div>
        <div style={{ textAlign: "center", fontFamily: T.mono, fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", color: T.inkFaint, marginBottom: 32 }}>
          AI Fraud Detection Console
        </div>

        <Panel pad={30}>
          <div style={{ display: "flex", gap: 4, marginBottom: 24, background: T.bg, padding: 4, borderRadius: 2, border: `1px solid ${T.line}` }}>
            {["login", "register"].map((m) => (
              <button key={m} onClick={() => { setMode(m); setErr(""); }}
                style={{ flex: 1, padding: "9px", fontFamily: T.mono, fontSize: 12, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", cursor: "pointer", border: "none", borderRadius: 1, background: mode === m ? T.panelHi : "transparent", color: mode === m ? T.dellHi : T.inkFaint, transition: "all .18s" }}>
                {m === "login" ? "Sign in" : "Register"}
              </button>
            ))}
          </div>

          <form onSubmit={submit}>
            <Field label="Username" value={form.username} onChange={(e) => set("username", e.target.value)} placeholder="j.inspector" required autoComplete="username" />
            {mode === "register" && (
              <Field label="Work email" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="you@dell.com" required />
            )}
            <Field label="Password" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} placeholder="••••••••" required minLength={mode === "register" ? 8 : undefined} hint={mode === "register" ? "Minimum 8 characters." : undefined} autoComplete={mode === "login" ? "current-password" : "new-password"} />
            {mode === "register" && (
              <div style={{ marginBottom: 20 }}>
                <span style={{ display: "block", fontFamily: T.mono, fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: T.inkFaint, marginBottom: 8 }}>Role</span>
                <div style={{ display: "flex", gap: 6 }}>
                  {[["INSPECTOR", "Inspector"], ["QA_MANAGER", "QA Manager"]].map(([v, label]) => (
                    <button type="button" key={v} onClick={() => set("role", v)}
                      style={{ flex: 1, padding: "10px", fontFamily: T.mono, fontSize: 12, cursor: "pointer", borderRadius: 2, border: `1px solid ${form.role === v ? T.dell : T.line}`, background: form.role === v ? `${T.dell}18` : T.bg, color: form.role === v ? T.dellHi : T.inkDim, transition: "all .15s" }}>{label}</button>
                  ))}
                </div>
              </div>
            )}
            {err && <div style={{ marginBottom: 16 }}><ErrorNote>{err}</ErrorNote></div>}
            <Btn type="submit" full size="lg" disabled={busy}>{busy ? "Authenticating…" : mode === "login" ? "Sign in →" : "Create account →"}</Btn>
          </form>

          <div style={{ marginTop: 16, fontFamily: T.mono, fontSize: 11, color: T.inkFaint, textAlign: "center", lineHeight: 1.7 }}>
            Connects to the inspection API.<br />Register an account, then sign in.
          </div>
        </Panel>
      </div>
    </div>
  );
}

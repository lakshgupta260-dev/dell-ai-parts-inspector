import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { history, reportDownloadUrl, notify, apiError } from "../lib/api.js";
import { verdictTone, scoreTone, useTheme } from "../lib/auth.jsx";
import { Panel, Eyebrow, Btn, ScoreDial, Tag, Loading, ErrorNote, Field } from "../components/ui.jsx";

export default function InspectionDetail() {
  const { T } = useTheme();
  const { id } = useParams();
  const nav = useNavigate();
  const [r, setR] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setR(await history.detail(id)); }
      catch (e) { setErr(apiError(e)); } finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return <Loading label="Loading inspection…" />;
  if (err) return <div><BackLink nav={nav} /><ErrorNote>{err}</ErrorNote></div>;
  if (!r) return null;

  const v = verdictTone(r.verdict, T);
  const meta = [
    ["Service Tag", r.service_tag], ["Part Number", r.part_number], ["Model", r.model_name],
    ["Express Code", r.express_service_code], ["Inspector", r.inspector_username], ["Status", r.pipeline_status],
  ];

  return (
    <div>
      <BackLink nav={nav} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 24 }}>
        <div>
          <Eyebrow>Inspection report</Eyebrow>
          <h1 style={{ fontFamily: T.mono, fontSize: 20, fontWeight: 600, color: T.ink, margin: "10px 0 0", letterSpacing: "0.01em", wordBreak: "break-all" }}>{r.inspection_id}</h1>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {r.report_path && <Btn tone={T.dell} size="sm" onClick={() => window.open(reportDownloadUrl(r.inspection_id), "_blank")}>Download PDF</Btn>}
        </div>
      </div>

      {/* verdict banner */}
      <Panel style={{ borderLeft: `4px solid ${v.tone}`, marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 26, alignItems: "center", flexWrap: "wrap" }}>
          <ScoreDial score={r.fraud_score} tone={scoreTone(r.fraud_score, T)} />
          <div style={{ flex: 1, minWidth: 220 }}>
            <Tag tone={v.tone}>{v.label}</Tag>
            <div style={{ fontFamily: T.sans, fontSize: 26, fontWeight: 700, color: v.tone, margin: "12px 0 6px" }}>Fraud score {r.fraud_score ?? "—"}/100</div>
            <div style={{ fontFamily: T.mono, fontSize: 12, color: T.inkDim }}>
              Confidence {r.confidence_level || "—"} · Model {r.ai_model_used || "—"} · Risk {r.comparison_risk_score ?? "—"}
            </div>
          </div>
        </div>
      </Panel>

      {/* meta grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 1, background: T.line, border: `1px solid ${T.line}`, borderRadius: 3, overflow: "hidden", marginBottom: 16 }}>
        {meta.map(([k, val]) => (
          <div key={k} style={{ background: T.panel, padding: "14px 16px" }}>
            <div style={{ fontFamily: T.mono, fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: T.inkFaint }}>{k}</div>
            <div style={{ fontFamily: T.mono, fontSize: 13, color: T.ink, marginTop: 5, wordBreak: "break-word" }}>{val || "—"}</div>
          </div>
        ))}
      </div>

      {/* AI reasoning */}
      {r.final_reasoning && (
        <Panel style={{ marginBottom: 16 }}>
          <Eyebrow>AI reasoning</Eyebrow>
          <p style={{ fontFamily: T.mono, fontSize: 13, color: T.inkDim, lineHeight: 1.7, marginTop: 14, marginBottom: 0, whiteSpace: "pre-wrap" }}>{r.final_reasoning}</p>
        </Panel>
      )}

      {/* image quality */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <QualityCard label="Front image" blur={r.front_blur_score} />
        <QualityCard label="Back image" blur={r.back_blur_score} />
      </div>

      <NotifyCard id={r.inspection_id} />
    </div>
  );
}

function BackLink({ nav }) {
  const { T } = useTheme();
  return <button onClick={() => nav(-1)} style={{ fontFamily: T.mono, fontSize: 12, color: T.inkDim, background: "none", border: "none", cursor: "pointer", marginBottom: 18, letterSpacing: "0.04em" }}>← Back</button>;
}

function QualityCard({ label, blur }) {
  const { T } = useTheme();
  const ok = blur != null && blur >= 100; // convention: higher variance-of-Laplacian = sharper
  return (
    <Panel>
      <Eyebrow>{label}</Eyebrow>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
        <div>
          <div style={{ fontFamily: T.mono, fontSize: 10, color: T.inkFaint, letterSpacing: "0.08em", textTransform: "uppercase" }}>Blur score</div>
          <div style={{ fontFamily: T.mono, fontSize: 22, fontWeight: 600, color: T.ink, marginTop: 4 }}>{blur != null ? blur.toFixed(1) : "—"}</div>
        </div>
        <Tag tone={ok ? T.green : T.amber}>{blur == null ? "n/a" : ok ? "sharp" : "soft"}</Tag>
      </div>
    </Panel>
  );
}

function NotifyCard({ id }) {
  const { T } = useTheme();
  const [phone, setPhone] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState("");

  async function send(channel) {
    setMsg(""); setBusy(channel);
    try {
      const fn = channel === "whatsapp" ? notify.whatsapp : notify.vapi;
      const res = await fn(id, phone);
      setMsg(`✓ ${channel} dispatched${res.message_id ? ` (${res.message_id})` : ""}.`);
    } catch (e) { setMsg("⚠ " + apiError(e)); } finally { setBusy(""); }
  }

  return (
    <Panel>
      <Eyebrow>Notify</Eyebrow>
      <div style={{ display: "flex", gap: 14, alignItems: "flex-end", flexWrap: "wrap", marginTop: 14 }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <Field label="Phone (E.164)" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+919876543210" />
        </div>
        <div style={{ display: "flex", gap: 10, marginBottom: 18 }}>
          <Btn tone={T.green} variant="ghost" disabled={!phone || busy} onClick={() => send("whatsapp")}>{busy === "whatsapp" ? "Sending…" : "WhatsApp"}</Btn>
          <Btn tone={T.dell} variant="ghost" disabled={!phone || busy} onClick={() => send("vapi")}>{busy === "vapi" ? "Calling…" : "Voice call"}</Btn>
        </div>
      </div>
      {msg && <div style={{ fontFamily: T.mono, fontSize: 12, color: msg.startsWith("✓") ? T.green : T.red, marginTop: 4 }}>{msg}</div>}
      <div style={{ fontFamily: T.mono, fontSize: 11, color: T.inkFaint, marginTop: 8 }}>Sends this inspection's result via the backend's WhatsApp / Vapi services.</div>
    </Panel>
  );
}

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { history, apiError } from "../lib/api.js";
import { verdictTone, scoreTone, useTheme, useAuth } from "../lib/auth.jsx";
import { Panel, Eyebrow, Tag, Loading, ErrorNote, Empty } from "../components/ui.jsx";

export default function Dashboard() {
  const { T } = useTheme();
  const { user } = useAuth();
  const nav = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [items, setItems] = useState([]);
  const [escalatedItems, setEscalatedItems] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const p = [history.analytics(), history.list(1, 8)];
        if (user?.role === "QA_MANAGER") {
            p.push(history.escalated(1, 8));
        }
        const res = await Promise.all(p);
        setAnalytics(res[0]); 
        setItems(res[1].items || []);
        if (user?.role === "QA_MANAGER") {
            setEscalatedItems(res[2].items || []);
        }
      } catch (e) { setErr(apiError(e)); } finally { setLoading(false); }
    })();
  }, [user?.role]);

  if (loading) return <Loading label="Loading dashboard…" />;

  return (
    <div>
      <div style={{ marginBottom: 24 }} className="slide-up">
        <Eyebrow>{user?.role === "QA_MANAGER" ? "Quality Assurance" : "Overview"}</Eyebrow>
        <h1 style={{ fontFamily: T.sans, fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", color: T.ink, margin: "10px 0 0", display: "inline-block" }}>
          {user?.role === "QA_MANAGER" ? "QA Command Center" : "Inspection dashboard"}
        </h1>
      </div>

      {err && <div style={{ marginBottom: 20 }}><ErrorNote>{err}</ErrorNote></div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 14, marginBottom: 22 }} className="slide-up stagger-1">
        <StatCard label="Total inspected" value={analytics?.total_inspections ?? 0} tone={T.ink} />
        {user?.role === "QA_MANAGER" ? (
          <>
            <StatCard label="Escalated" value={escalatedItems.length} tone={T.amber} />
            <StatCard label="Critical Flags" value={analytics?.counterfeit_count ?? 0} tone={T.red} />
            <StatCard label="Pass Rate" value={`${(analytics?.pass_rate ?? 0).toFixed(1)}%`} tone={T.green} />
          </>
        ) : (
          <>
            <StatCard label="Authentic" value={analytics?.authentic_count ?? 0} tone={T.green} />
            <StatCard label="Suspicious" value={analytics?.suspicious_count ?? 0} tone={T.amber} />
            <StatCard label="Counterfeit" value={analytics?.counterfeit_count ?? 0} tone={T.red} />
          </>
        )}
      </div>

      {user?.role !== "QA_MANAGER" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 22 }} className="slide-up stagger-2">
          <Panel>
            <Eyebrow>Pass rate</Eyebrow>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 14 }}>
              <span style={{ fontFamily: T.mono, fontSize: 44, fontWeight: 700, color: T.green, lineHeight: 1 }}>{(analytics?.pass_rate ?? 0).toFixed(1)}</span>
              <span style={{ fontFamily: T.mono, fontSize: 16, color: T.inkDim }}>%</span>
            </div>
            <div style={{ height: 8, background: T.bg, borderRadius: 4, overflow: "hidden", marginTop: 16, border: `1px solid ${T.line}` }}>
              <div style={{ width: `${analytics?.pass_rate ?? 0}%`, height: "100%", background: `linear-gradient(90deg,${T.green}88,${T.green})`, transition: "width .8s" }} />
            </div>
            <div style={{ fontFamily: T.sans, fontSize: 13, color: T.inkDim, marginTop: 10 }}>Share of parts verdicted AUTHENTIC.</div>
          </Panel>
          <Panel>
            <Eyebrow>Average fraud score</Eyebrow>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 14 }}>
              <span style={{ fontFamily: T.mono, fontSize: 44, fontWeight: 700, color: scoreTone(analytics?.avg_fraud_score, T), lineHeight: 1 }}>{(analytics?.avg_fraud_score ?? 0).toFixed(1)}</span>
              <span style={{ fontFamily: T.mono, fontSize: 16, color: T.inkDim }}>/ 100</span>
            </div>
            <div style={{ height: 8, background: T.bg, borderRadius: 4, overflow: "hidden", marginTop: 16, border: `1px solid ${T.line}` }}>
              <div style={{ width: `${analytics?.avg_fraud_score ?? 0}%`, height: "100%", background: scoreTone(analytics?.avg_fraud_score, T), transition: "width .8s" }} />
            </div>
            <div style={{ fontFamily: T.sans, fontSize: 13, color: T.inkDim, marginTop: 10 }}>Mean across all completed inspections.</div>
          </Panel>
        </div>
      )}

      {user?.role === "QA_MANAGER" && (
        <Panel pad={0} className="slide-up stagger-3" style={{ marginBottom: 22, border: `2px solid ${T.amber}88` }}>
          <div style={{ padding: "18px 22px", borderBottom: `1px solid ${T.line}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Eyebrow><span style={{ color: T.amber }}>Escalated Inspections (Needs Review)</span></Eyebrow>
          </div>
          {escalatedItems.length ? <HistoryTable rows={escalatedItems} onOpen={(id) => nav(`/inspection/${id}`)} /> :
            <Empty>No escalated inspections. Great job!</Empty>}
        </Panel>
      )}

      <Panel pad={0} className="slide-up stagger-4">
        <div style={{ padding: "18px 22px", borderBottom: `1px solid ${T.line}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Eyebrow>{user?.role === "QA_MANAGER" ? "All Recent Inspections" : "Recent inspections"}</Eyebrow>
          <button onClick={() => nav("/history")} style={{ fontFamily: T.sans, fontWeight: 600, fontSize: 13, color: T.dellHi, background: "none", border: "none", cursor: "pointer" }}>view all →</button>
        </div>
        {items.length ? <HistoryTable rows={items} onOpen={(id) => nav(`/inspection/${id}`)} /> :
          <Empty>No inspections yet. Start one from <b style={{ color: T.dellHi }}>New Inspection</b>.</Empty>}
      </Panel>
    </div>
  );
}

function StatCard({ label, value, tone }) {
  const { T } = useTheme();
  const [hov, setHov] = useState(false);
  return (
    <Panel style={{ transition: "transform .18s, border-color .18s", transform: hov ? "translateY(-3px)" : "none", borderColor: hov ? T.lineHi : T.line }}>
      <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}>
        <div style={{ fontFamily: T.sans, fontSize: 13, fontWeight: 600, letterSpacing: "0.02em", textTransform: "uppercase", color: T.inkDim }}>{label}</div>
        <div style={{ fontFamily: T.mono, fontSize: 40, fontWeight: 700, color: tone, marginTop: 8, lineHeight: 1 }}>{value}</div>
      </div>
    </Panel>
  );
}

/* Reusable table used by dashboard + history. */
export function HistoryTable({ rows, onOpen }) {
  const { T } = useTheme();
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: T.mono, fontSize: 12.5 }}>
        <thead>
          <tr style={{ textAlign: "left", color: T.inkFaint, fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}>
            {["Service Tag", "Model", "Verdict", "Score", "Status", "Date", ""].map((h) => (
              <th key={h} style={{ padding: "12px 16px", fontWeight: 600, borderBottom: `1px solid ${T.line}` }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => <Row key={r.inspection_id} r={r} onOpen={onOpen} />)}
        </tbody>
      </table>
    </div>
  );
}
function Row({ r, onOpen }) {
  const { T } = useTheme();
  const [hov, setHov] = useState(false);
  const v = verdictTone(r.verdict, T);
  const td = { padding: "13px 16px", borderBottom: `1px solid ${T.line}`, color: T.inkDim };
  return (
    <tr onClick={() => onOpen(r.inspection_id)} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{ cursor: "pointer", background: hov ? T.panelHi : "transparent", transition: "background .12s", borderLeft: hov ? `2px solid ${T.dell}` : "2px solid transparent" }}>
      <td style={{ ...td, color: T.ink }}>{r.service_tag || "—"}</td>
      <td style={td}>{r.model_name || "—"}</td>
      <td style={td}>{r.verdict ? <Tag tone={v.tone}>{v.label}</Tag> : <span style={{ color: T.inkFaint }}>pending</span>}</td>
      <td style={{ ...td, color: scoreTone(r.fraud_score, T), fontWeight: 600 }}>{r.fraud_score ?? "—"}</td>
      <td style={td}><span style={{ color: r.pipeline_status === "complete" ? T.green : T.inkDim, fontSize: 11 }}>{r.pipeline_status}</span></td>
      <td style={{ ...td, color: T.inkFaint }}>{r.uploaded_at ? new Date(r.uploaded_at).toLocaleDateString() : "—"}</td>
      <td style={{ ...td, color: hov ? T.dellHi : T.inkFaint }}>view →</td>
    </tr>
  );
}

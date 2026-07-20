import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { history, apiError } from "../lib/api.js";
import { T } from "../lib/auth.jsx";
import { Panel, Eyebrow, Loading, ErrorNote, Empty } from "../components/ui.jsx";
import { HistoryTable } from "./Dashboard.jsx";

const VERDICTS = ["All", "AUTHENTIC", "SUSPICIOUS", "COUNTERFEIT"];

export default function History() {
  const nav = useNavigate();
  const [all, setAll] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [verdict, setVerdict] = useState("All");

  useEffect(() => {
    (async () => {
      try { const h = await history.list(1, 100); setAll(h.items || []); }
      catch (e) { setErr(apiError(e)); } finally { setLoading(false); }
    })();
  }, []);

  const filtered = useMemo(() => all.filter((r) => {
    const hay = `${r.inspection_id} ${r.service_tag || ""} ${r.model_name || ""} ${r.part_number || ""}`.toLowerCase();
    const mq = !q || hay.includes(q.toLowerCase());
    const mv = verdict === "All" || (r.verdict || "").toUpperCase() === verdict;
    return mq && mv;
  }), [all, q, verdict]);

  if (loading) return <Loading label="Loading history…" />;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Eyebrow>Full record</Eyebrow>
        <h1 style={{ fontFamily: T.sans, fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", color: T.ink, margin: "10px 0 0" }}>Inspection history</h1>
      </div>

      {err && <div style={{ marginBottom: 16 }}><ErrorNote>{err}</ErrorNote></div>}

      <Panel pad={16} style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
            <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: T.inkFaint, fontFamily: T.mono, fontSize: 13 }}>⌕</span>
            <input placeholder="Search service tag, model, part number, ID…" value={q} onChange={(e) => setQ(e.target.value)}
              style={{ width: "100%", boxSizing: "border-box", padding: "10px 12px 10px 32px", background: T.bg, color: T.ink, fontFamily: T.mono, fontSize: 13, border: `1px solid ${T.line}`, borderRadius: 2, outline: "none" }} />
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {VERDICTS.map((v) => (
              <button key={v} onClick={() => setVerdict(v)}
                style={{ padding: "9px 14px", fontFamily: T.mono, fontSize: 12, cursor: "pointer", borderRadius: 2, border: `1px solid ${verdict === v ? T.dell : T.line}`, background: verdict === v ? `${T.dell}18` : T.bg, color: verdict === v ? T.dellHi : T.inkDim, transition: "all .15s" }}>
                {v === "All" ? "All" : v.charAt(0) + v.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
          <span style={{ fontFamily: T.mono, fontSize: 12, color: T.inkFaint }}>{filtered.length} results</span>
        </div>
      </Panel>

      <Panel pad={0}>
        {filtered.length ? <HistoryTable rows={filtered} onOpen={(id) => nav(`/inspection/${id}`)} /> :
          <Empty>No inspections match these filters.</Empty>}
      </Panel>
    </div>
  );
}

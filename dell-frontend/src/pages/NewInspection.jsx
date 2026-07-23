import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadInspection, streamPipeline, apiError } from "../lib/api.js";
import { verdictTone, scoreTone, useTheme } from "../lib/auth.jsx";
import { Panel, Eyebrow, Btn, Radar, ScoreDial, Tag, ErrorNote } from "../components/ui.jsx";

const STAGES = [
  ["Vision", "OpenCV quality + label detection"],
  ["OCR", "PaddleOCR text extraction"],
  ["Comparison", "Dell field validation"],
  ["AI Reasoning", "LangGraph + Gemini 2.5 Flash verdict"],
  ["Report", "PDF generation"],
];

export default function NewInspection() {
  const { T } = useTheme();
  const nav = useNavigate();
  const [step, setStep] = useState(0);         // 0 upload, 1 running, 2 result
  const [front, setFront] = useState(null);
  const [back, setBack] = useState(null);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);
  const [inspId, setInspId] = useState(null);

  const [progress, setProgress] = useState({});

  async function run() {
    setErr(""); setStep(1); setProgress({});
    try {
      const up = await uploadInspection(front, back);   // POST /upload/inspection
      setInspId(up.inspection_id);
      
      await streamPipeline(up.inspection_id, (evt) => {
        if (evt.stage === "complete") {
          setResult(evt.result);
          setStep(2);
        } else {
          setProgress(p => ({ ...p, [evt.stage]: evt.status || "ok" }));
        }
      });
    } catch (e) {
      setErr(apiError(e)); setStep(0);
    }
  }

  const steps = ["Upload", "Analyse", "Result"];
  return (
    <div>
      <div style={{ marginBottom: 26 }} className="slide-up">
        <Eyebrow>New inspection</Eyebrow>
        <h1 style={{ fontFamily: T.sans, fontSize: 32, fontWeight: 800, letterSpacing: "-0.02em", color: T.ink, margin: "10px 0 0", display: "inline-block" }}>Inspect a part</h1>
      </div>

      <div style={{ display: "flex", alignItems: "center", marginBottom: 30 }} className="slide-up stagger-1">
        {steps.map((s, i) => (
          <React.Fragment key={s}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", display: "grid", placeItems: "center", fontFamily: T.sans, fontSize: 14, fontWeight: 700, border: `1px solid ${i <= step ? T.dell : T.line}`, background: i < step ? T.dell : "transparent", color: i < step ? "#04121c" : i === step ? T.dellHi : T.inkFaint, transition: "all .3s" }}>
                {i < step ? "✓" : i + 1}
              </div>
              <span style={{ fontFamily: T.sans, fontSize: 13, fontWeight: 600, letterSpacing: "0.02em", color: i === step ? T.ink : T.inkFaint }}>{s}</span>
            </div>
            {i < steps.length - 1 && <div style={{ flex: 1, height: 1, margin: "0 16px", background: i < step ? T.dell : T.line, transition: "background .3s" }} />}
          </React.Fragment>
        ))}
      </div>

      {err && <div style={{ marginBottom: 18 }}><ErrorNote>{err}</ErrorNote></div>}

      {step === 0 && (
        <div className="slide-up stagger-2">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
            <DropZone label="Front image" hint="Front-facing photo of the part" file={front} setFile={setFront} id="front" />
            <DropZone label="Back image" hint="Rear-facing photo (label side)" file={back} setFile={setBack} id="back" />
          </div>
          <Btn size="lg" disabled={!front || !back} onClick={run}>Run full pipeline →</Btn>
          {(!front || !back) && <span style={{ fontFamily: T.sans, fontSize: 13, fontWeight: 500, color: T.inkDim, marginLeft: 14 }}>Both images are required.</span>}
        </div>
      )}

      {step === 1 && <RunningView progress={progress} front={front} />}

      {step === 2 && result && (
        <div className="slide-up stagger-1">
          <ResultCard r={result} />
          <StageStrip r={result} />
          <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
            <Btn onClick={() => nav(`/inspection/${inspId}`)}>Open full report →</Btn>
            <Btn variant="ghost" tone={T.inkDim} onClick={() => { setStep(0); setFront(null); setBack(null); setResult(null); }}>Inspect another</Btn>
          </div>
        </div>
      )}
    </div>
  );
}

function DropZone({ label, hint, file, setFile, id }) {
  const { T } = useTheme();
  const [drag, setDrag] = useState(false);
  const preview = file ? URL.createObjectURL(file) : null;
  return (
    <Panel pad={16}>
      <Eyebrow>{label}</Eyebrow>
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
        onClick={() => document.getElementById(id).click()}
        style={{ marginTop: 12, border: `1.5px dashed ${drag ? T.dell : T.lineHi}`, borderRadius: 3, padding: file ? 0 : "44px 20px", textAlign: "center", background: drag ? `${T.dell}0a` : T.bg, transition: "all .18s", cursor: "pointer", position: "relative", overflow: "hidden", minHeight: 160, display: "flex", alignItems: "center", justifyContent: "center" }}>
        {preview ? (
          <div style={{ position: "relative", width: "100%" }}>
            <img src={preview} alt={label} style={{ width: "100%", height: 180, objectFit: "cover", display: "block" }} />
            <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "rgba(0,0,0,0.6)", padding: "8px 12px", fontFamily: T.sans, fontSize: 12, color: "#fff", textAlign: "left" }}>{file.name} · {(file.size / 1024).toFixed(0)} KB</div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 30, marginBottom: 10, color: T.inkFaint }}>⊹</div>
            <div style={{ fontFamily: T.sans, fontSize: 15, color: T.ink }}>Drop here or click</div>
            <div style={{ fontFamily: T.sans, fontSize: 13, fontWeight: 500, color: T.inkDim, marginTop: 6 }}>{hint} — JPG, PNG, WebP</div>
          </div>
        )}
        <input id={id} type="file" accept="image/*" style={{ display: "none" }} onChange={(e) => setFile(e.target.files[0])} />
      </div>
    </Panel>
  );
}

function RunningView({ progress, front }) {
  const { T } = useTheme();
  const stageKeys = ["vision", "ocr", "comparison", "ai", "report"];
  const preview = front ? URL.createObjectURL(front) : null;

  return (
    <Panel pad={40} className="slide-up stagger-1">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 40, alignItems: "center" }}>
        
        {/* Left Side: Image Preview */}
        <div style={{ position: "relative", overflow: "hidden", borderRadius: 6, border: `1px solid ${T.lineHi}`, background: T.line }}>
          {preview ? (
            <img src={preview} alt="Processing" style={{ width: "100%", display: "block" }} />
          ) : (
            <div style={{ width: "100%", paddingBottom: "75%" }} />
          )}
          <div style={{ position: "absolute", bottom: 12, left: 12 }}>
            <Tag tone={T.dell}>PROCESSING...</Tag>
          </div>
        </div>

        {/* Right Side: Checklist */}
        <div>
          <Radar />
          <div style={{ fontFamily: T.sans, fontSize: 15, fontWeight: 600, color: T.dellHi, marginTop: 20 }}>Running pipeline…</div>
          <div style={{ fontFamily: T.mono, fontSize: 12, color: T.inkDim, marginTop: 8 }}>Vision → OCR → Comparison → AI → PDF</div>
          <div style={{ maxWidth: 420, marginTop: 26, display: "flex", flexDirection: "column", gap: 9 }}>
            {STAGES.map(([name, detail], i) => {
              const key = stageKeys[i];
              const isDone = progress[key];
              const isError = isDone && isDone !== "ok";
              
              return (
                <div key={name} style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: T.mono, fontSize: 12, color: T.inkDim }}>
                  {isDone ? (
                    <span style={{ color: isError ? T.red : T.green, fontSize: 14, width: 14 }}>{isError ? "⨯" : "✓"}</span>
                  ) : (
                    <span className="pulse" style={{ width: 8, height: 8, borderRadius: "50%", background: T.dell, margin: "3px 3px 3px 3px" }} />
                  )}
                  <span style={{ color: isDone ? T.ink : T.inkDim }}>{name}</span>
                  <span style={{ color: T.inkFaint }}>· {detail}</span>
                </div>
              );
            })}
          </div>
          <div style={{ fontFamily: T.mono, fontSize: 11, color: T.inkFaint, marginTop: 22 }}>Live streaming updates...</div>
        </div>
      </div>
    </Panel>
  );
}

function ResultCard({ r }) {
  const { T } = useTheme();
  const v = verdictTone(r.verdict, T);
  return (
    <Panel style={{ borderLeft: `4px solid ${v.tone}` }}>
      <div style={{ display: "flex", gap: 26, alignItems: "center", flexWrap: "wrap" }}>
        <ScoreDial score={r.fraud_score} tone={scoreTone(r.fraud_score, T)} />
        <div style={{ flex: 1, minWidth: 200 }}>
          <Tag tone={v.tone}>{v.label}</Tag>
          <div style={{ fontFamily: T.sans, fontSize: 24, fontWeight: 700, color: v.tone, margin: "12px 0 4px" }}>Fraud score {r.fraud_score ?? "—"}/100</div>
          <div style={{ fontFamily: T.mono, fontSize: 12, color: T.inkDim }}>{r.inspection_id}</div>
        </div>
        <div style={{ display: "flex", gap: 26 }}>
          <Metric label="Service Tag" value={r.service_tag || "—"} />
          <Metric label="Model" value={r.model_name || "—"} />
          <Metric label="Quality" value={r.overall_quality_ok == null ? "—" : r.overall_quality_ok ? "OK" : "Poor"} tone={r.overall_quality_ok ? T.green : T.amber} />
        </div>
      </div>
    </Panel>
  );
}
function Metric({ label, value, tone }) {
  const { T } = useTheme();
  return (
    <div>
      <div style={{ fontFamily: T.mono, fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: T.inkFaint }}>{label}</div>
      <div style={{ fontFamily: T.mono, fontSize: 18, fontWeight: 600, color: tone || T.ink, marginTop: 4 }}>{value}</div>
    </div>
  );
}

/* Shows the per-stage ok/error statuses the pipeline returns. */
function StageStrip({ r }) {
  const { T } = useTheme();
  const map = [
    ["Vision", r.vision_status], ["OCR", r.ocr_status], ["Comparison", r.comparison_status],
    ["AI", r.ai_status], ["Report", r.report_status],
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 1, background: T.line, border: `1px solid ${T.line}`, borderRadius: 3, overflow: "hidden", marginTop: 14 }}>
      {map.map(([name, st]) => {
        const ok = st === "ok";
        return (
          <div key={name} style={{ background: T.panel, padding: "12px 14px" }}>
            <div style={{ fontFamily: T.mono, fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", color: T.inkFaint }}>{name}</div>
            <div style={{ fontFamily: T.mono, fontSize: 12, color: ok ? T.green : T.red, marginTop: 5, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: ok ? T.green : T.red }} />
              {ok ? "ok" : "error"}
            </div>
          </div>
        );
      })}
    </div>
  );
}

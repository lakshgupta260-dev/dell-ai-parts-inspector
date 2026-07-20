import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  HiOutlineShieldCheck,
  HiOutlineViewGrid,
  HiOutlinePlusCircle,
  HiOutlineClock,
  HiOutlineCog,
  HiOutlineLogout,
  HiOutlineExclamationCircle,
} from "react-icons/hi";
import { historyApi } from "../lib/api";

const VERDICT_STYLES = {
  AUTHENTIC: "bg-emerald-50 text-emerald-700 border-emerald-200",
  SUSPICIOUS: "bg-amber-50 text-amber-700 border-amber-200",
  COUNTERFEIT: "bg-rose-50 text-rose-700 border-rose-200",
};

const NAV_ITEMS = [
  { icon: HiOutlineViewGrid, label: "Dashboard", active: true },
  { icon: HiOutlinePlusCircle, label: "New inspection" },
  { icon: HiOutlineClock, label: "History" },
  { icon: HiOutlineCog, label: "Settings" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState(null);
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errored, setErrored] = useState(false);

  const user = JSON.parse(localStorage.getItem("dell_inspector_user") || "{}");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [analyticsRes, historyRes] = await Promise.all([
          historyApi.analytics(),
          historyApi.list({ page: 1, page_size: 8 }),
        ]);
        if (cancelled) return;
        setAnalytics(analyticsRes.data);
        setInspections(historyRes.data?.items ?? historyRes.data ?? []);
      } catch (err) {
        if (!cancelled) setErrored(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("dell_inspector_token");
    localStorage.removeItem("dell_inspector_user");
    navigate("/login");
  };

  const kpis = [
    { label: "Total inspections", value: analytics?.total_inspections ?? "—" },
    { label: "Pass rate", value: analytics?.pass_rate != null ? `${analytics.pass_rate}%` : "—" },
    { label: "Avg. fraud score", value: analytics?.avg_fraud_score ?? "—" },
    { label: "Counterfeit flagged", value: analytics?.counterfeit_count ?? "—" },
  ];

  return (
    <div className="min-h-screen flex bg-milk font-sans text-ink">
      {/* Sidebar */}
      <aside className="w-64 bg-ink flex flex-col shrink-0">
        <div className="px-6 py-6 flex items-center gap-2 text-milk">
          <HiOutlineShieldCheck className="w-5 h-5 text-indigo-400" />
          <span className="font-display font-semibold tracking-tight">Parts Inspector</span>
        </div>

        <nav className="flex-1 px-3 mt-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.label}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium font-display transition-colors ${
                item.active
                  ? "bg-indigo-600 text-white"
                  : "text-milk/60 hover:text-milk hover:bg-white/5"
              }`}
            >
              <item.icon className="w-4.5 h-4.5" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="px-3 pb-5 pt-4 border-t border-white/10 mx-3">
          <div className="flex items-center gap-3 px-1 py-2 mb-1">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-display font-semibold text-white shrink-0">
              {(user.username || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm text-milk truncate">{user.username || "User"}</p>
              <p className="text-xs text-milk/45 font-mono truncate">
                {(user.role || "INSPECTOR").replace("_", " ")}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3.5 py-2 rounded-lg text-sm text-milk/60 hover:text-milk hover:bg-white/5 transition-colors"
          >
            <HiOutlineLogout className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="px-8 py-6 flex items-center justify-between border-b border-milk-300">
          <div>
            <h1 className="font-display text-2xl font-medium">Dashboard</h1>
            <p className="text-sm text-ink-light mt-0.5">
              Overview of inspection activity and fraud detection results.
            </p>
          </div>
          <button className="bg-ink hover:bg-indigo-700 text-milk text-sm font-display font-medium px-4 py-2.5 rounded-lg transition-colors flex items-center gap-2">
            <HiOutlinePlusCircle className="w-4 h-4" />
            New inspection
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-8 py-7">
          {errored && (
            <div className="mb-6 flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3">
              <HiOutlineExclamationCircle className="w-4.5 h-4.5 shrink-0" />
              Couldn't reach the backend at localhost:8000. Showing placeholders until it's back.
            </div>
          )}

          {/* KPI cards */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            {kpis.map((kpi) => (
              <div
                key={kpi.label}
                className="bg-white rounded-xl border border-milk-300 shadow-card px-5 py-5 animate-slide-up"
              >
                <p className="text-xs font-mono uppercase tracking-wide text-ink-faint mb-2.5">
                  {kpi.label}
                </p>
                <p className="font-display text-3xl font-medium">
                  {loading ? <Skeleton /> : kpi.value}
                </p>
              </div>
            ))}
          </div>

          {/* Recent inspections table */}
          <div className="bg-white rounded-xl border border-milk-300 shadow-card overflow-hidden">
            <div className="px-5 py-4 border-b border-milk-300 flex items-center justify-between">
              <h2 className="font-display font-medium">Recent inspections</h2>
              <button className="text-sm text-indigo-600 font-medium hover:text-indigo-700">
                View all
              </button>
            </div>

            {loading ? (
              <div className="p-8 text-center text-ink-faint text-sm">Loading inspections…</div>
            ) : inspections.length === 0 ? (
              <div className="p-10 text-center">
                <p className="font-display text-ink font-medium mb-1">No inspections yet</p>
                <p className="text-sm text-ink-light">
                  Run your first inspection to see results here.
                </p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs font-mono uppercase tracking-wide text-ink-faint border-b border-milk-300">
                    <th className="px-5 py-3 font-medium">Service tag</th>
                    <th className="px-5 py-3 font-medium">Model</th>
                    <th className="px-5 py-3 font-medium">Verdict</th>
                    <th className="px-5 py-3 font-medium">Fraud score</th>
                    <th className="px-5 py-3 font-medium">Inspector</th>
                    <th className="px-5 py-3 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {inspections.map((row, i) => (
                    <tr
                      key={row.inspection_id ?? i}
                      className="border-b border-milk-200 last:border-0 hover:bg-milk-200/50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3.5 font-mono text-ink">{row.service_tag ?? "—"}</td>
                      <td className="px-5 py-3.5 text-ink-light">
                        {row.model_name ?? "—"}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center px-2.5 py-1 rounded-md border text-xs font-medium font-display ${
                            VERDICT_STYLES[row.verdict] ??
                            "bg-milk-200 text-ink-light border-milk-300"
                          }`}
                        >
                          {row.verdict ?? row.pipeline_status ?? "Pending"}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono">{row.fraud_score ?? "—"}</td>
                      <td className="px-5 py-3.5 text-ink-light">{row.inspector_username ?? "—"}</td>
                      <td className="px-5 py-3.5 text-ink-light font-mono text-xs">
                        {row.uploaded_at ? new Date(row.uploaded_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function Skeleton() {
  return <span className="inline-block w-12 h-7 bg-milk-300 rounded animate-pulse" />;
}

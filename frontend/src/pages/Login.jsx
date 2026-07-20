import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { HiOutlineMail, HiOutlineLockClosed, HiOutlineUser, HiOutlineShieldCheck } from "react-icons/hi";
import { authApi } from "../lib/api";

const ROLES = [
  { value: "INSPECTOR", label: "Inspector" },
  { value: "QA_MANAGER", label: "QA Manager" },
];

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    role: "INSPECTOR",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        const { data } = await authApi.login(form.username, form.password);
        localStorage.setItem("dell_inspector_token", data.access_token);
        localStorage.setItem(
          "dell_inspector_user",
          JSON.stringify({ username: data.username, role: data.role })
        );
      } else {
        const { data } = await authApi.register({
          username: form.username,
          email: form.email,
          password: form.password,
          role: form.role,
        });
        localStorage.setItem("dell_inspector_token", data.access_token);
        localStorage.setItem(
          "dell_inspector_user",
          JSON.stringify({ username: data.username, role: data.role })
        );
      }
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "We couldn't verify those details. Check them and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-milk font-sans text-ink">
      {/* Brand panel */}
      <div className="hidden lg:flex lg:w-[42%] relative bg-ink flex-col justify-between overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(#FAF9F5 1px, transparent 1px), linear-gradient(90deg, #FAF9F5 1px, transparent 1px)",
            backgroundSize: "36px 36px",
          }}
        />
        <div className="relative z-10 px-12 pt-12">
          <div className="scan-corners inline-flex items-center gap-2 text-milk px-4 py-3">
            <span className="corner-tl" />
            <HiOutlineShieldCheck className="w-5 h-5 text-indigo-400" />
            <span className="font-display font-semibold tracking-tight text-lg">
              Parts Inspector
            </span>
          </div>
        </div>

        <div className="relative z-10 px-12 pb-14">
          <p className="font-mono text-xs tracking-widest text-indigo-400 uppercase mb-4">
            Dell &middot; Authenticity Verification
          </p>
          <h1 className="font-display text-4xl leading-[1.15] text-milk font-medium max-w-md">
            Every part tells you what it is, if you know how to read it.
          </h1>
          <p className="mt-5 text-milk/60 max-w-sm leading-relaxed">
            Upload, verify, and score genuine Dell components in minutes —
            vision, OCR, and rule-based validation in a single pipeline.
          </p>

          <div className="mt-10 flex gap-8 font-mono text-milk/50 text-xs">
            <div>
              <div className="text-milk text-xl font-semibold mb-1">98%+</div>
              OCR confidence
            </div>
            <div>
              <div className="text-milk text-xl font-semibold mb-1">5</div>
              stage pipeline
            </div>
            <div>
              <div className="text-milk text-xl font-semibold mb-1">0–100</div>
              fraud score
            </div>
          </div>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-fade-in">
          <div className="lg:hidden flex items-center gap-2 mb-8 text-ink">
            <HiOutlineShieldCheck className="w-5 h-5 text-indigo-600" />
            <span className="font-display font-semibold text-lg">Parts Inspector</span>
          </div>

          <div className="flex gap-6 border-b border-milk-300 mb-8">
            {["login", "register"].map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMode(m);
                  setError("");
                }}
                className={`pb-3 text-sm font-medium font-display tracking-tight transition-colors relative ${
                  mode === m ? "text-ink" : "text-ink-faint hover:text-ink-light"
                }`}
              >
                {m === "login" ? "Sign in" : "Create account"}
                {mode === m && (
                  <span className="absolute -bottom-px left-0 right-0 h-[2px] bg-indigo-600 rounded-full" />
                )}
              </button>
            ))}
          </div>

          <h2 className="font-display text-2xl font-medium mb-1">
            {mode === "login" ? "Welcome back" : "Set up your account"}
          </h2>
          <p className="text-ink-light text-sm mb-7">
            {mode === "login"
              ? "Sign in with your inspector or QA manager credentials."
              : "Register to start logging and reviewing inspections."}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Field
              icon={HiOutlineUser}
              type="text"
              placeholder="Username"
              value={form.username}
              onChange={update("username")}
              minLength={3}
              required
            />
            {mode === "register" && (
              <Field
                icon={HiOutlineMail}
                type="email"
                placeholder="Work email"
                value={form.email}
                onChange={update("email")}
                required
              />
            )}
            <Field
              icon={HiOutlineLockClosed}
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={update("password")}
              minLength={mode === "register" ? 8 : undefined}
              required
            />

            {mode === "register" && (
              <div className="grid grid-cols-2 gap-3 pt-1">
                {ROLES.map((r) => (
                  <button
                    type="button"
                    key={r.value}
                    onClick={() => setForm((f) => ({ ...f, role: r.value }))}
                    className={`rounded-lg border px-3 py-2.5 text-sm font-medium font-display transition-colors ${
                      form.role === r.value
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-milk-300 text-ink-light hover:border-ink-faint"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            )}

            {error && (
              <div className="rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm px-3 py-2.5">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-ink hover:bg-indigo-700 text-milk font-display font-medium text-sm rounded-lg py-3 transition-colors disabled:opacity-60 mt-2"
            >
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="text-xs text-ink-faint text-center mt-8 font-mono">
            SECURED · JWT AUTH · ROLE-BASED ACCESS
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({ icon: Icon, ...props }) {
  return (
    <div className="relative">
      <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-faint" />
      <input
        {...props}
        className="w-full rounded-lg border border-milk-300 bg-white pl-10 pr-3.5 py-2.5 text-sm placeholder:text-ink-faint focus:outline-none focus:ring-2 focus:ring-indigo-600/30 focus:border-indigo-600 transition-shadow"
      />
    </div>
  );
}

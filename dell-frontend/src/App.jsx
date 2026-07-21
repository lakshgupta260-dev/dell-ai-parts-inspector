import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth, T } from "./lib/auth.jsx";
import { ScanGrid } from "./components/ui.jsx";
import Shell from "./components/Shell.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import NewInspection from "./pages/NewInspection.jsx";
import InspectionDetail from "./pages/InspectionDetail.jsx";
import History from "./pages/History.jsx";

function Protected({ children }) {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" replace />;
}

function GlobalStyles() {
  return (
    <style>{`
      @keyframes spin { to { transform: rotate(360deg); } }
      @keyframes sweep { to { transform: translateX(100%); } }
      @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
      .pulse { animation: pulse 1.2s ease-in-out infinite; }
      * { box-sizing: border-box; }
      html, body, #root { margin: 0; min-height: 100%; background: ${T.bg}; }
      ::selection { background: ${T.dell}44; }
      ::-webkit-scrollbar { width: 10px; height: 10px; }
      ::-webkit-scrollbar-track { background: ${T.bg}; }
      ::-webkit-scrollbar-thumb { background: ${T.line}; border-radius: 2px; }
      ::-webkit-scrollbar-thumb:hover { background: ${T.lineHi}; }
      input::placeholder { color: ${T.inkFaint}; }
    `}</style>
  );
}

/* One shared layout: black background + green ScanGrid on EVERY page. */
export default function App() {
  return (
    <AuthProvider>
      <GlobalStyles />
      <div style={{ minHeight: "100vh", background: T.bg, backgroundImage: `radial-gradient(circle at 50% -8%, ${T.bg2}, ${T.bg})`, fontFamily: T.sans, color: T.ink }}>
        <ScanGrid />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<Protected><Shell /></Protected>}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewInspection />} />
              <Route path="/history" element={<History />} />
              <Route path="/inspection/:id" element={<InspectionDetail />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

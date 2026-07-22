import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, ThemeProvider, useAuth, useTheme, T as NIGHT } from "./lib/auth.jsx";
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
      @keyframes slideUp { 
        0% { opacity: 0; transform: translateY(20px); } 
        100% { opacity: 1; transform: translateY(0); } 
      }
      .pulse { animation: pulse 1.2s ease-in-out infinite; }
      .slide-up { animation: slideUp 0.3s ease-out forwards; opacity: 0; }
      .stagger-1 { animation-delay: 0.03s; }
      .stagger-2 { animation-delay: 0.06s; }
      .stagger-3 { animation-delay: 0.09s; }
      .stagger-4 { animation-delay: 0.12s; }
      .stagger-5 { animation-delay: 0.15s; }
      * { box-sizing: border-box; }
      html, body, #root { margin: 0; min-height: 100%; }
      ::-webkit-scrollbar { width: 10px; height: 10px; }
      ::-webkit-scrollbar-thumb { border-radius: 2px; }
    `}</style>
  );
}

function LoginNight() {
  return (
    <div style={{ minHeight: "100vh", background: NIGHT.bg, fontFamily: NIGHT.sans, color: NIGHT.ink }}>
      <Login />
    </div>
  );
}

function AppLayout() {
  const { T } = useTheme();
  return (
    <div style={{ minHeight: "100vh", background: T.bg, fontFamily: T.sans, color: T.ink, transition: "background-color .35s ease, color .35s ease" }}>
      <Protected><Shell /></Protected>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <GlobalStyles />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginNight />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/new" element={<NewInspection />} />
              <Route path="/history" element={<History />} />
              <Route path="/inspection/:id" element={<InspectionDetail />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

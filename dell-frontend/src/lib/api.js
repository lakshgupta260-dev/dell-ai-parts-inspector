import axios from "axios";

/* ============================================================================
   API client — matches the dell-ai-parts-inspector backend exactly.
   Base URL is read from VITE_API_URL (set in .env), defaulting to localhost:8000.
   Every path here mirrors a real FastAPI route under /api/v1.
   ========================================================================== */

export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE });

// Attach the JWT to every request if we have one.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("pg_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, clear the session so the app bounces to login.
client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("pg_token");
      localStorage.removeItem("pg_user");
    }
    return Promise.reject(err);
  }
);

/* Pull a human-readable message out of a FastAPI error response. */
export function apiError(err) {
  const d = err?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => e.msg).join("; ");
  return err?.message || "Something went wrong. Is the backend running?";
}

/* ------------------------------- Auth ------------------------------------ */
export const auth = {
  // POST /api/v1/auth/register  { username, email, password, role }
  register: (body) => client.post("/api/v1/auth/register", body).then((r) => r.data),
  // POST /api/v1/auth/login  { username, password }
  login: (body) => client.post("/api/v1/auth/login", body).then((r) => r.data),
};

/* ------------------------------ Upload ----------------------------------- */
// POST /api/v1/upload/inspection  (multipart: front_image, back_image)
export function uploadInspection(frontFile, backFile) {
  const fd = new FormData();
  fd.append("front_image", frontFile);
  fd.append("back_image", backFile);
  return client
    .post("/api/v1/upload/inspection", fd, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
}

/* ----------------------------- Pipeline ---------------------------------- */
// POST /api/v1/pipeline/run/{inspection_id}
export const runPipeline = (id) =>
  client.post(`/api/v1/pipeline/run/${id}`).then((r) => r.data);

export const streamPipeline = async (id, onEvent) => {
  const token = localStorage.getItem("pg_token");
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/api/v1/pipeline/run/${id}`, {
    method: "POST",
    headers,
  });

  if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let lines = buffer.split("\\n\\n");
    buffer = lines.pop(); // keep incomplete chunk
    for (let line of lines) {
      if (line.startsWith("data: ")) {
        const dataStr = line.replace("data: ", "");
        try {
          const parsed = JSON.parse(dataStr);
          onEvent(parsed);
        } catch (e) {}
      }
    }
  }
};

/* ------------------------ Individual stages (optional) ------------------- */
export const stages = {
  vision: (id) => client.post(`/api/v1/vision/analyze/${id}`).then((r) => r.data),
  ocr: (id) => client.post(`/api/v1/ocr/extract/${id}`).then((r) => r.data),
  comparison: (id) => client.post(`/api/v1/comparison/analyze/${id}`).then((r) => r.data),
  ai: (id) => client.post(`/api/v1/ai/analyze/${id}`).then((r) => r.data),
  report: (id) => client.post(`/api/v1/report/generate/${id}`).then((r) => r.data),
};

/* ------------------------------ History ---------------------------------- */
export const history = {
  // GET /api/v1/history?page=&page_size=
  list: (page = 1, pageSize = 50) =>
    client.get(`/api/v1/history`, { params: { page, page_size: pageSize } }).then((r) => r.data),
  // GET /api/v1/history/analytics
  analytics: () => client.get(`/api/v1/history/analytics`).then((r) => r.data),
  // GET /api/v1/history/{inspection_id}
  detail: (id) => client.get(`/api/v1/history/${id}`).then((r) => r.data),
};

/* ------------------------------ Report ----------------------------------- */
// GET /api/v1/report/download/{inspection_id}  -> opens the PDF
export const reportDownloadUrl = (id) => `${API_BASE}/api/v1/report/download/${id}`;

/* --------------------------- Notifications ------------------------------- */
export const notify = {
  // POST /api/v1/notify/whatsapp/{id}  { phone_number }
  whatsapp: (id, phone_number) =>
    client.post(`/api/v1/notify/whatsapp/${id}`, { phone_number }).then((r) => r.data),
  // POST /api/v1/notify/vapi/{id}  { phone_number }
  vapi: (id, phone_number) =>
    client.post(`/api/v1/notify/vapi/${id}`, { phone_number }).then((r) => r.data),
};

export default client;

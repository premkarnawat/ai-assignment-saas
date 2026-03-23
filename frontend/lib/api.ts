// frontend/lib/api.ts
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

// Attach JWT token automatically
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh token on 401
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refresh,
          });
          localStorage.setItem("access_token", data.access_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient.request(error.config);
        } catch {
          localStorage.clear();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const auth = {
  register: (data: { email: string; password: string; name: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  google: (data: { google_token: string; name: string; email: string; avatar_url: string }) =>
    apiClient.post("/auth/google", data),
  refresh: (refresh_token: string) =>
    apiClient.post("/auth/refresh", { refresh_token }),
};

// ── Assignments ───────────────────────────────────────────────────────────────
export const assignments = {
  generate: (data: {
    question: string;
    subject?: string;
    grade_level?: string;
    handwriting_style?: string;
    paper_type?: string;
    font_name?: string;
  }) => apiClient.post("/assignments/generate", data),

  status: (id: string) =>
    apiClient.get(`/assignments/${id}/status`),

  list: (page = 1, limit = 20) =>
    apiClient.get(`/assignments/?page=${page}&limit=${limit}`),

  delete: (id: string) =>
    apiClient.delete(`/assignments/${id}`),
};

// ── Notebook ──────────────────────────────────────────────────────────────────
export const notebook = {
  generate: (data: {
    subject: string;
    topic: string;
    pages: number;
    subtopics?: string[];
    handwriting_style?: string;
    paper_type?: string;
    include_diagrams?: boolean;
    include_examples?: boolean;
  }) => apiClient.post("/notebook/generate", data),
};

// ── OCR ───────────────────────────────────────────────────────────────────────
export const ocr = {
  extract: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post("/ocr/extract", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ── Users ─────────────────────────────────────────────────────────────────────
export const users = {
  me: () => apiClient.get("/users/me"),
  stats: () => apiClient.get("/users/me/stats"),
};

// ── Payments (Razorpay) ───────────────────────────────────────────────────────
export const payments = {
  /**
   * Create a Razorpay order.
   * Returns { order_id, amount, currency, key, plan_name, user_name, user_email }
   * Use this data to open the Razorpay payment popup.
   */
  createOrder: (plan: string) =>
    apiClient.post("/payments/create-order", { plan }),

  /**
   * Verify Razorpay payment after user completes payment.
   * Razorpay returns { razorpay_order_id, razorpay_payment_id, razorpay_signature }
   * Send these to backend for HMAC verification → user tier upgrade.
   */
  verifyPayment: (data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
    plan: string;
  }) => apiClient.post("/payments/verify-payment", data),

  history: () => apiClient.get("/payments/history"),
};

// ── Polling helper ────────────────────────────────────────────────────────────
/**
 * Poll assignment status every intervalMs until done or failed.
 * Calls onUpdate with each status update.
 */
export async function pollStatus(
  assignmentId: string,
  onUpdate: (status: string, data: Record<string, unknown>) => void,
  intervalMs = 2000,
  maxAttempts = 60
): Promise<void> {
  let attempts = 0;
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      attempts++;
      try {
        const { data } = await assignments.status(assignmentId);
        onUpdate(data.status, data);
        if (data.status === "done") { clearInterval(timer); resolve(); }
        if (data.status === "failed") { clearInterval(timer); reject(new Error(data.error || "Failed")); }
        if (attempts >= maxAttempts) { clearInterval(timer); reject(new Error("Timeout")); }
      } catch (err) { clearInterval(timer); reject(err); }
    }, intervalMs);
  });
}

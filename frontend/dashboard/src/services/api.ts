import axios from "axios";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const TENANT_KEY = process.env.NEXT_PUBLIC_TENANT_KEY || "";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT + tenant key on every request
api.interceptors.request.use((config) => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (TENANT_KEY) config.headers["X-Tenant-Key"] = TENANT_KEY;
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  },
);

/* ── Auth ──────────────────────────────────────────────────────────── */

export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/login", {
      email,
      password,
    }),
  me: () => api.get<User>("/auth/me"),
};

/* ── Admin Users ──────────────────────────────────────────────────── */

export const usersApi = {
  list: () => api.get<User[]>("/admin/users"),
  create: (data: { email: string; password: string; role: string }) =>
    api.post<User>("/admin/users", data),
  remove: (id: string) => api.delete(`/admin/users/${id}`),
};

/* ── Admin Properties ─────────────────────────────────────────────── */

export const propertiesApi = {
  list: () => api.get<Property[]>("/admin/properties"),
  create: (data: PropertyCreate) =>
    api.post<Property>("/admin/properties", data),
  remove: (id: string) => api.delete(`/admin/properties/${id}`),
};

/* ── Admin Leads ──────────────────────────────────────────────────── */

export const leadsApi = {
  list: () => api.get<Lead[]>("/admin/leads"),
  detail: (id: string) => api.get<LeadDetail>(`/admin/leads/${id}`),
};

/* ── Types ────────────────────────────────────────────────────────── */

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface Property {
  id: string;
  tenant_id: string;
  location: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  square_feet: number;
  available: boolean;
  created_at: string;
}

export interface PropertyCreate {
  location: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  square_feet: number;
  available: boolean;
}

export interface Lead {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  phone: string;
  budget_min: number | null;
  budget_max: number | null;
  preferred_location: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  tool_name: string | null;
  created_at: string;
}

export interface LeadDetail extends Lead {
  conversation_history: ConversationMessage[];
}

export default api;

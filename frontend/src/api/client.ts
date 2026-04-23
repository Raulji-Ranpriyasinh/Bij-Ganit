import axios from "axios";
import { useAuthStore } from "../stores/authStore";
import { useCompanyStore } from "../stores/companyStore";

// Single shared axios instance. Because Vite proxies /api to the backend
// we can just use a relative baseURL in dev AND prod (assuming the same
// reverse proxy setup).
export const api = axios.create({
  baseURL: "/api",
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Multi-tenancy: forward the active company id on every request so the
  // backend can scope queries (see app/core/deps.py::get_current_company).
  const companyId = useCompanyStore.getState().activeCompanyId;
  if (companyId != null) {
    config.headers["company"] = String(companyId);
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

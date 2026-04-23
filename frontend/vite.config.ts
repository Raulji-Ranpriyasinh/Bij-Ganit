import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite dev server proxies /api to the FastAPI backend so the frontend can
// use relative URLs everywhere and production can serve both services
// behind the same reverse proxy.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

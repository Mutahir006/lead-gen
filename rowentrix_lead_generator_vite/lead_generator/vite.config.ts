import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local dev only: proxies /api to a local uvicorn server so `npm run dev`
// works against your Python backend without CORS issues. In production on
// Vercel, /api is routed straight to api/index.py — this proxy is ignored.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});

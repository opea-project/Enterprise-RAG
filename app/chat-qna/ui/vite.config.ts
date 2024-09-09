import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig, loadEnv } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

const __filename = fileURLToPath(import.meta.url);

const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default ({ mode }: { mode: string }) => {
  process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };

  return defineConfig({
    plugins: [react(), tsconfigPaths()],
    resolve: {
      alias: {
        "@/": path.resolve(__dirname, "./src/"),
        "@/components/*": path.resolve(__dirname, "./src/components"),
        "@/layout/*": path.resolve(__dirname, "./src/layout"),
        "@/pages/*": path.resolve(__dirname, "./src/pages"),
        "@/router/*": path.resolve(__dirname, "./src/router"),
        "@/services/*": path.resolve(__dirname, "./src/services"),
        "@/store/*": path.resolve(__dirname, "./src/store"),
        "@/theme/*": path.resolve(__dirname, "./src/theme"),
      },
    },
    server: {
      port: 8888,
      strictPort: true,
      open: true,
      proxy: {
        "/api/v1/chatqna": {
          target: process.env.VITE_CHAT_QNA_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace("/api/v1/chatqna", "/"),
        },
        "/api/v1/dataprep": {
          target: process.env.VITE_DATA_INGESTION_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace("/api", ""),
        },
      },
    },
  });
};

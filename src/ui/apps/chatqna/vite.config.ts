// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";

import packageJson from "./package.json";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), viteTsconfigPaths()],
  define: {
    "import.meta.env.VITE_APP_VERSION": JSON.stringify(packageJson.version),
  },
  resolve: {
    alias: {
      "@/": path.resolve(__dirname, "./src/"),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: "modern",
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom"],
          "intel-enterprise-rag-ui-auth": ["@intel-enterprise-rag-ui/auth"],
          "intel-enterprise-rag-ui-chat": ["@intel-enterprise-rag-ui/chat"],
          "intel-enterprise-rag-ui-components": [
            "@intel-enterprise-rag-ui/components",
          ],
          "intel-enterprise-rag-ui-control-plane": [
            "@intel-enterprise-rag-ui/control-plane",
          ],
          "intel-enterprise-rag-ui-icons": ["@intel-enterprise-rag-ui/icons"],
          "intel-enterprise-rag-ui-layouts": [
            "@intel-enterprise-rag-ui/layouts",
          ],
          "intel-enterprise-rag-ui-markdown": [
            "@intel-enterprise-rag-ui/markdown",
          ],
          "intel-enterprise-rag-ui-utils": ["@intel-enterprise-rag-ui/utils"],
        },
      },
    },
  },
  server: {
    proxy: {
      "^/api/v1/chatqna$": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
      "^/v1/chat_history": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
      "^/v1/system_fingerprint": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
      "^/api/v1/chatqa/status$": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
      "^/api/v1/edp": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

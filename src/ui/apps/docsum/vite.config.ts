// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), viteTsconfigPaths()],
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
          "intel-enterprise-rag-ui-utils": ["@intel-enterprise-rag-ui/utils"],
        },
      },
    },
  },
  server: {
    proxy: {
      "^/api/v1/docsum": {
        target: "https://erag.com",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});

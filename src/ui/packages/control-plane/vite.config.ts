// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { dirname, resolve } from "path";
import { defineConfig } from "vite";
import dts from "vite-plugin-dts";
import viteTsconfigPaths from "vite-tsconfig-paths";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "intel-enterprise-rag-ui-control-plane",
      fileName: "intel-enterprise-rag-ui-control-plane",
      formats: ["es"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-redux"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "react-redux": "ReactRedux",
        },
        manualChunks: {
          "xyflow-react": ["@xyflow/react"],
          "intel-enterprise-rag-ui-components": [
            "@intel-enterprise-rag-ui/components",
          ],
          "intel-enterprise-rag-ui-icons": ["@intel-enterprise-rag-ui/icons"],
        },
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: "modern",
      },
    },
  },
  plugins: [react(), viteTsconfigPaths(), dts()],
  resolve: {
    alias: {
      "@/": resolve(__dirname, "./src/"),
    },
  },
});

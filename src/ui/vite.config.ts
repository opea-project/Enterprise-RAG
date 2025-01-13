// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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
      },
    },
    server: {
      port: 7777,
      strictPort: true,
      open: true,
      proxy: {
        "/api/v1/chatqna": {
          target: process.env.VITE_CHAT_QNA_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace("/api/v1/chatqna", ""),
        },
        "/api/v1/dataprep": {
          target: process.env.VITE_DATA_INGESTION_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace("/api/v1/dataprep", ""),
        },
        "/v1/system_fingerprint/append_arguments": {
          target: process.env.VITE_SYSTEM_FINGERPRINT_URL,
          changeOrigin: true,
        },
        "/v1/system_fingerprint/change_arguments": {
          target: process.env.VITE_SYSTEM_FINGERPRINT_URL,
          changeOrigin: true,
        },
      },
    },
  });
};

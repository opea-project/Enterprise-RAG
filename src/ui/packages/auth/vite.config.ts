// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fileURLToPath } from "node:url";

import { dirname, resolve } from "path";
import { defineConfig } from "vite";
import dts from "vite-plugin-dts";
import viteTsconfigPaths from "vite-tsconfig-paths";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "intel-enterprise-rag-ui-auth",
      fileName: "intel-enterprise-rag-ui-auth",
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-router-dom"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "react-redux": "ReactRedux",
        },
      },
    },
  },
  plugins: [dts(), viteTsconfigPaths()],
  resolve: {
    alias: {
      "@/": resolve(__dirname, "./src/"),
    },
  },
});

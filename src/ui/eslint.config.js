// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import js from "@eslint/js";
import prettier from "eslint-plugin-prettier/recommended";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import globals from "globals";
import typescriptEslint from "typescript-eslint";

export default typescriptEslint.config(
  { ignores: ["**/dist/**"] },
  {
    extends: [
      js.configs.recommended,
      ...typescriptEslint.configs.recommended,
      prettier,
    ],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      react: react,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "simple-import-sort": simpleImportSort,
    },
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off", // Not needed for React 17+
      "react/prop-types": "off", // Using TypeScript for prop validation
      "react/jsx-sort-props": [
        "error",
        {
          callbacksLast: false,
          shorthandLast: true,
          multiline: "ignore",
          ignoreCase: false,
          noSortAlphabetically: true,
          reservedFirst: true,
          locale: "auto",
        },
      ],
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
);

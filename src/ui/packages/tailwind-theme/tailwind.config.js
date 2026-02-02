// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  plugins: [require("tailwindcss-react-aria-components")],
  theme: {
    extend: {
      colors: {
        // modes colors
        light: {
          primary: "#3D447F",
          secondary: "#3D447F",
          accent: "#3D447F",
          focus: "#3D447F",
          "focus-inverse": "#F2F3FF",
          border: "#3D447F",
          "border-2": "#6A6F78",
          text: {
            primary: "#2B2C30",
            disabled: "#B2B3B9",
            placeholder: "#6A6F78",
            inverse: "#F2F3FF",
            error: "#EB0004",
            accent: "#3D447F",
            "accent-2": "#3D447F",
          },
          bg: {
            1: "#F2F3FF",
            2: "#E6E8FD",
            disabled: "#E9EAEB",
            inverse: "#000000",
            contrast: "#FFFFFF",
          },
          status: {
            success: "#3F9752",
            error: "#EB0004",
            unknown: "#6A6F78",
          },
        },
        dark: {
          primary: "#4850B8",
          secondary: "#FEF0D3",
          accent: "#FFFFFF",
          focus: "#FEF0D3",
          border: "#4850B8",
          "border-2": "#6A6F78",
          text: {
            primary: "#FFFFFF",
            disabled: "#6B6E76",
            placeholder: "#6A6F78",
            inverse: "#090B1C",
            error: "#EB0004",
            accent: "#FFFFFF",
            "accent-2": "#F3B1F5",
          },
          bg: {
            1: "#090B1C",
            2: "#1F2133",
            disabled: "#3C3E42",
            inverse: "#FFFFFF",
            contrast: "#000000",
          },
          status: {
            success: "#3F9752",
            error: "#EB0004",
            unknown: "#6A6F78",
          },
        },
        // common colors for both modes
        tooltip: {
          text: "#FFFFFF",
          background: "#242528",
        },
        scrollbar: {
          thumb: "#A1A1A1CC",
          track: "#A1A1A180",
        },
      },
      animation: {
        "pulsing-dot": "pulsing-dot 600ms ease-out infinite",
        "recording-pulse": "recording-pulse 1.5s ease-in-out infinite",
      },
      keyframes: {
        "pulsing-dot": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.5)" },
        },
        "recording-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.6", transform: "scale(1.1)" },
        },
      },
    },
  },
};

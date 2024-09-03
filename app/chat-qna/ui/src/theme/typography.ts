// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import createTypography, {
  TypographyOptions,
} from "@mui/material/styles/createTypography";
import { CSSProperties } from "react";

import palette from "@/theme/palette";

declare module "@mui/material/styles" {
  // noinspection JSUnusedGlobalSymbols
  interface TypographyVariants {
    "toolbar-app-name": CSSProperties;
    "login-page-app-name": CSSProperties;
    "navigation-item-label": CSSProperties;
    "chat-avatar-name-label": CSSProperties;
  }

  // allow configuration using `createTheme`
  // noinspection JSUnusedGlobalSymbols
  interface TypographyVariantsOptions {
    "toolbar-app-name"?: CSSProperties;
    "login-page-app-name"?: CSSProperties;
    "navigation-item-label"?: CSSProperties;
    "chat-avatar-name-label"?: CSSProperties;
  }
}

// Update the Typography's variant prop options
declare module "@mui/material/Typography" {
  // noinspection JSUnusedGlobalSymbols
  interface TypographyPropsVariantOverrides {
    "toolbar-app-name": true;
    "login-page-app-name": true;
    "navigation-item-label": true;
    "chat-avatar-name-label": true;
  }
}

interface ExtendedTypographyOptions extends TypographyOptions {
  "toolbar-app-name": CSSProperties;
  "login-page-app-name": CSSProperties;
  "navigation-item-label": CSSProperties;
  "chat-avatar-name-label": CSSProperties;
}

const typography = createTypography(palette, {
  h2: { fontSize: 24 },
  h3: { fontSize: 20 },
  h6: { fontWeight: 300 },
  overline: {
    fontSize: 16,
    fontWeight: 500,
    lineHeight: 1,
  },
  caption: {
    lineHeight: 1,
    letterSpacing: 0.01,
  },
  "toolbar-app-name": {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 20,
    fontWeight: 300,
  },
  "login-page-app-name": {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 32,
    fontWeight: 300,
    color: palette.primary.main,
  },
  "navigation-item-label": {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 12,
    lineHeight: 1,
  },
  "chat-avatar-name-label": {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    lineHeight: 1.5,
    fontSize: 12,
  },
  button: {
    textTransform: "none",
  },
} as ExtendedTypographyOptions);

export default typography;

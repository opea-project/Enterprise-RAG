// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Components, Theme } from "@mui/material";

const components: Components<Omit<Theme, "components">> = {
  MuiAppBar: {
    defaultProps: {
      elevation: 0,
      position: "fixed",
    },
  },
  MuiButton: {
    defaultProps: {
      disableElevation: true,
      disableTouchRipple: true,
      variant: "contained",
    },
    styleOverrides: {
      root: ({ ownerState }) => ({
        ...(ownerState.size === "medium" && {
          paddingBlock: 4,
          paddingInline: 12,
        }),
      }),
    },
  },
  MuiDrawer: {
    defaultProps: {
      variant: "permanent",
    },
  },
  MuiInputLabel: {
    styleOverrides: {
      root: {
        fontSize: 12,
        lineHeight: 1.25,
        marginBottom: 4,
        display: "inline",
      },
    },
  },
  MuiLink: {
    defaultProps: {
      underline: "hover",
    },
    styleOverrides: {
      root: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        lineHeight: 1.75,
        fontWeight: 500,
      },
    },
  },
  MuiList: {
    styleOverrides: {
      root: {
        paddingBlock: 0,
        marginBlock: 8,
      },
    },
  },
  MuiListItem: {
    styleOverrides: {
      root: {
        paddingBlock: 0,
        paddingLeft: 14,
        paddingRight: 0,
        "&:not(:first-of-type)": {
          marginTop: 8,
        },
        "&:hover": {
          backgroundColor: "#efefef",
        },
      },
    },
  },
  MuiMenu: {
    styleOverrides: {
      root: {
        "& .MuiList-root.MuiMenu-list": {
          paddingBlock: 0,
          marginBlock: 0,
        },
      },
    },
  },
  MuiMenuItem: {
    styleOverrides: {
      root: {
        fontSize: 14,
        paddingInline: 14,
        paddingBlock: 8,
      },
    },
  },
  MuiOutlinedInput: {
    defaultProps: {
      size: "small",
      fullWidth: true,
    },
    styleOverrides: {
      root: {
        fontSize: 14,
      },
    },
  },
  MuiSelect: {
    defaultProps: {
      MenuProps: {
        sx: { "& .MuiMenu-list": { padding: 0 } },
      },
    },
    styleOverrides: {
      root: {
        fontSize: 14,
        "& .MuiInputBase-input": {
          fontSize: 14,
          paddingBlock: 8,
          paddingInline: 14,
        },
      },
    },
  },
  MuiTextField: {
    defaultProps: {
      size: "small",
      fullWidth: true,
    },
    styleOverrides: {
      root: {
        "& .MuiInputBase-root": {
          fontSize: 14,
        },
      },
    },
  },
  MuiToolbar: {
    defaultProps: {
      variant: "dense",
    },
    styleOverrides: {
      root: {
        minHeight: 48,
        height: 48,
      },
    },
  },
  MuiTypography: {
    defaultProps: {
      variantMapping: {
        "toolbar-app-name": "h1",
        "login-page-app-name": "h1",
        "navigation-item-label": "label",
        "chat-avatar-name-label": "label",
      },
    },
    styleOverrides: {
      root: ({ ownerState }) => ({
        ...(ownerState.variant === "h2" && {
          marginBlock: 8,
        }),
        ...(ownerState.variant === "h3" && {
          marginBlock: 6,
        }),
      }),
    },
  },
};

export default components;

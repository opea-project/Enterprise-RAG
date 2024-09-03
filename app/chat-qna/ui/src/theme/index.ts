// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createTheme } from "@mui/material/styles";

import components from "@/theme/components";
import palette from "@/theme/palette";
import typography from "@/theme/typography";

const theme = createTheme({
  palette,
  typography,
  shape: {
    borderRadius: 0,
  },
  components,
});

export default theme;

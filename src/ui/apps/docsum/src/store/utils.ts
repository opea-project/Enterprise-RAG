// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { summarizationApi } from "@/api";
import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import { resetDocSumGraphSlice } from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import { store } from "@/store";

export const resetStore = () => {
  // reset all Redux store slices
  store.dispatch(resetDocSumGraphSlice());

  // reset all RTK Query API states
  summarizationApi.util.resetApiState();
  controlPlaneApi.util.resetApiState();
};

// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import { resetDocSumGraphSlice } from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import { summarizationApi } from "@/features/docsum/api";
import { resetHistorySlice } from "@/features/docsum/store/history.slice";
import { resetPasteTextTabSlice } from "@/features/docsum/store/pasteTextTab.slice";
import { resetUploadFileTabSlice } from "@/features/docsum/store/uploadFileTab.slice";
import { store } from "@/store";

export const resetStore = () => {
  // reset all Redux store slices
  store.dispatch(resetPasteTextTabSlice());
  store.dispatch(resetUploadFileTabSlice());
  store.dispatch(resetHistorySlice());
  store.dispatch(resetDocSumGraphSlice());

  // reset all RTK Query API states
  summarizationApi.util.resetApiState();
  controlPlaneApi.util.resetApiState();
};

// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import {
  resetChatHistorySlice,
  resetChatSideMenuSlice,
} from "@intel-enterprise-rag-ui/chat";

import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import { audioQnAApi } from "@/features/chat/api/audioQnA.api";
import { chatHistoryApi } from "@/features/chat/api/chatHistory.api";
import { store } from "@/store";
import { resetViewNavigationSlice } from "@/store/viewNavigation.slice";

export const resetStore = () => {
  // reset all Redux store slices
  store.dispatch(resetChatSideMenuSlice());
  store.dispatch(resetChatHistorySlice());
  store.dispatch(resetViewNavigationSlice());

  // reset all RTK Query API states
  audioQnAApi.util.resetApiState();
  chatHistoryApi.util.resetApiState();
  // controlPlaneApi.util.resetApiState();
  edpApi.util.resetApiState();
  s3Api.util.resetApiState();
};

// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  resetChatHistorySlice,
  resetChatSideMenuSlice,
} from "@intel-enterprise-rag-ui/chat";

import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import { resetChatQnAGraphSlice } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import { chatHistoryApi } from "@/features/chat/api/chatHistory.api";
import { chatQnAApi } from "@/features/chat/api/chatQnA.api";
import { store } from "@/store";
import { resetViewNavigationSlice } from "@/store/viewNavigation.slice";

export const resetStore = () => {
  // reset all Redux store slices
  store.dispatch(resetChatQnAGraphSlice());
  store.dispatch(resetChatSideMenuSlice());
  store.dispatch(resetChatHistorySlice());
  store.dispatch(resetViewNavigationSlice());

  // reset all RTK Query API states
  chatQnAApi.util.resetApiState();
  chatHistoryApi.util.resetApiState();
  controlPlaneApi.util.resetApiState();
  edpApi.util.resetApiState();
  s3Api.util.resetApiState();
};

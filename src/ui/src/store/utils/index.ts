// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { controlPlaneApi } from "@/features/admin-panel/control-plane/api";
import { resetChatQnAGraphSlice } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { edpApi } from "@/features/admin-panel/data-ingestion/api/edpApi";
import { s3Api } from "@/features/admin-panel/data-ingestion/api/s3Api";
import { chatHistoryApi } from "@/features/chat/api/chatHistory";
import { chatQnAApi } from "@/features/chat/api/chatQnA";
import { resetChatSideMenusSlice } from "@/features/chat/store/chatSideMenus.slice";
import { resetCurrentChatSlice } from "@/features/chat/store/currentChat.slice";
import { store } from "@/store";

export const resetStore = () => {
  // reset all Redux store slices
  store.dispatch(resetChatQnAGraphSlice());
  store.dispatch(resetChatSideMenusSlice());
  store.dispatch(resetCurrentChatSlice());

  // reset all RTK Query API states
  chatQnAApi.util.resetApiState();
  chatHistoryApi.util.resetApiState();
  controlPlaneApi.util.resetApiState();
  edpApi.util.resetApiState();
  s3Api.util.resetApiState();
};

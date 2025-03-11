// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import AdminPanelIcon from "@/components/icons/AdminPanelIcon/AdminPanelIcon";
import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ChatIcon from "@/components/icons/ChatIcon/ChatIcon";
import CloseIcon from "@/components/icons/CloseIcon/CloseIcon";
import CloseNotificationIcon from "@/components/icons/CloseNotificationIcon/CloseNotificationIcon";
import DarkModeIcon from "@/components/icons/DarkModeIcon/DarkModeIcon";
import DataPrepIcon from "@/components/icons/DataPrepIcon/DataPrepIcon";
import DeleteIcon from "@/components/icons/DeleteIcon/DeleteIcon";
import EmbeddingIcon from "@/components/icons/EmbeddingIcon/EmbeddingIcon";
import FileInputIcon from "@/components/icons/FileInputIcon/FileInputIcon";
import IdentityProviderIcon from "@/components/icons/IdentityProviderIcon/IdentityProviderIcon";
import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import LightModeIcon from "@/components/icons/LightModeIcon/LightModeIcon";
import LoadingIcon from "@/components/icons/LoadingIcon/LoadingIcon";
import LogoutIcon from "@/components/icons/LogoutIcon/LogoutIcon";
import PlusIcon from "@/components/icons/PlusIcon/PlusIcon";
import PromptSendIcon from "@/components/icons/PromptSendIcon/PromptSendIcon";
import PromptStopIcon from "@/components/icons/PromptStopIcon/PromptStopIcon";
import RefreshIcon from "@/components/icons/RefreshIcon/RefreshIcon";
import ScrollToBottomIcon from "@/components/icons/ScrollToBottomIcon/ScrollToBottomIcon";
import SuccessIcon from "@/components/icons/SuccessIcon/SuccessIcon";
import TelemetryIcon from "@/components/icons/TelemetryIcon/TelemetryIcon";
import UploadIcon from "@/components/icons/UploadIcon/UploadIcon";

export const icons = {
  "admin-panel": AdminPanelIcon,
  "chat-bot": ChatBotIcon,
  chat: ChatIcon,
  close: CloseIcon,
  "close-notification": CloseNotificationIcon,
  "dark-mode": DarkModeIcon,
  "data-prep": DataPrepIcon,
  delete: DeleteIcon,
  embedding: EmbeddingIcon,
  "file-input": FileInputIcon,
  "identity-provider": IdentityProviderIcon,
  info: InfoIcon,
  "light-mode": LightModeIcon,
  loading: LoadingIcon,
  logout: LogoutIcon,
  plus: PlusIcon,
  "prompt-send": PromptSendIcon,
  "prompt-stop": PromptStopIcon,
  refresh: RefreshIcon,
  "scroll-to-bottom": ScrollToBottomIcon,
  success: SuccessIcon,
  telemetry: TelemetryIcon,
  upload: UploadIcon,
};

export type IconName = keyof typeof icons;

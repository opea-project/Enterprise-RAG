// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import AdminPanelIcon from "./AdminPanelIcon/AdminPanelIcon";
import ChatBotIcon from "./ChatBotIcon/ChatBotIcon";
import ChatIcon from "./ChatIcon/ChatIcon";
import CloseIcon from "./CloseIcon/CloseIcon";
import CloseNotificationIcon from "./CloseNotificationIcon/CloseNotificationIcon";
import DarkModeIcon from "./DarkModeIcon/DarkModeIcon";
import DataPrepIcon from "./DataPrepIcon/DataPrepIcon";
import DeleteIcon from "./DeleteIcon/DeleteIcon";
import EmbeddingIcon from "./EmbeddingIcon/EmbeddingIcon";
import FileInputIcon from "./FileInputIcon/FileInputIcon";
import IdentityProviderIcon from "./IdentityProviderIcon/IdentityProviderIcon";
import InfoIcon from "./InfoIcon/InfoIcon";
import LightModeIcon from "./LightModeIcon/LightModeIcon";
import LoadingIcon from "./LoadingIcon/LoadingIcon";
import LogoutIcon from "./LogoutIcon/LogoutIcon";
import PlusIcon from "./PlusIcon/PlusIcon";
import PromptSendIcon from "./PromptSendIcon/PromptSendIcon";
import PromptStopIcon from "./PromptStopIcon/PromptStopIcon";
import RefreshIcon from "./RefreshIcon/RefreshIcon";
import ScrollToBottomIcon from "./ScrollToBottomIcon/ScrollToBottomIcon";
import SuccessIcon from "./SuccessIcon/SuccessIcon";
import TelemetryIcon from "./TelemetryIcon/TelemetryIcon";
import UploadIcon from "./UploadIcon/UploadIcon";

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

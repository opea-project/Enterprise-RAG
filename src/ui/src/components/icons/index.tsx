// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import AdminPanelIcon from "@/components/icons/AdminPanelIcon/AdminPanelIcon";
import BucketSynchronizationIcon from "@/components/icons/BucketSynchronizationIcon/BucketSynchronizationIcon";
import ChatBotIcon from "@/components/icons/ChatBotIcon/ChatBotIcon";
import ChatIcon from "@/components/icons/ChatIcon/ChatIcon";
import CloseIcon from "@/components/icons/CloseIcon/CloseIcon";
import CloseNotificationIcon from "@/components/icons/CloseNotificationIcon/CloseNotificationIcon";
import ConfigurableServiceIcon from "@/components/icons/ConfigurableServiceIcon/ConfigurableServiceIcon";
import CopyErrorIcon from "@/components/icons/CopyErrorIcon/CopyErrorIcon";
import CopyIcon from "@/components/icons/CopyIcon/CopyIcon";
import CopySuccessIcon from "@/components/icons/CopySuccessIcon/CopySuccessIcon";
import DarkModeIcon from "@/components/icons/DarkModeIcon/DarkModeIcon";
import DataPrepIcon from "@/components/icons/DataPrepIcon/DataPrepIcon";
import DeleteIcon from "@/components/icons/DeleteIcon/DeleteIcon";
import DownloadIcon from "@/components/icons/DownloadIcon/DownloadIcon";
import EditIcon from "@/components/icons/EditIcon/EditIcon";
import EmbeddingIcon from "@/components/icons/EmbeddingIcon/EmbeddingIcon";
import ExportIcon from "@/components/icons/ExportIcon/ExportIcon";
import FileIcon from "@/components/icons/FileIcon/FileIcon";
import HideSideMenuIcon from "@/components/icons/HideSideMenuIcon/HideSideMenuIcon";
import IdentityProviderIcon from "@/components/icons/IdentityProviderIcon/IdentityProviderIcon";
import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import LightModeIcon from "@/components/icons/LightModeIcon/LightModeIcon";
import LinkIcon from "@/components/icons/LinkIcon/LinkIcon";
import LoadingIcon from "@/components/icons/LoadingIcon/LoadingIcon";
import LogoutIcon from "@/components/icons/LogoutIcon/LogoutIcon";
import MoreOptionsIcon from "@/components/icons/MoreOptionsIcon/MoreOptionsIcon";
import NewChatIcon from "@/components/icons/NewChatIcon/NewChatIcon";
import OptionsIcon from "@/components/icons/OptionsIcon/OptionsIcon";
import PlusIcon from "@/components/icons/PlusIcon/PlusIcon";
import PromptSendIcon from "@/components/icons/PromptSendIcon/PromptSendIcon";
import PromptStopIcon from "@/components/icons/PromptStopIcon/PromptStopIcon";
import RefreshIcon from "@/components/icons/RefreshIcon/RefreshIcon";
import ScrollToBottomIcon from "@/components/icons/ScrollToBottomIcon/ScrollToBottomIcon";
import SettingsIcon from "@/components/icons/SettingsIcon/SettingsIcon";
import SideMenuIcon from "@/components/icons/SideMenuIcon/SideMenuIcon";
import SuccessIcon from "@/components/icons/SuccessIcon/SuccessIcon";
import TelemetryIcon from "@/components/icons/TelemetryIcon/TelemetryIcon";
import UploadIcon from "@/components/icons/UploadIcon/UploadIcon";

export const icons = {
  "admin-panel": AdminPanelIcon,
  "bucket-synchronization": BucketSynchronizationIcon,
  "chat-bot": ChatBotIcon,
  chat: ChatIcon,
  close: CloseIcon,
  "close-notification": CloseNotificationIcon,
  "configurable-service": ConfigurableServiceIcon,
  "copy-error": CopyErrorIcon,
  copy: CopyIcon,
  "copy-success": CopySuccessIcon,
  "dark-mode": DarkModeIcon,
  "data-prep": DataPrepIcon,
  delete: DeleteIcon,
  download: DownloadIcon,
  edit: EditIcon,
  embedding: EmbeddingIcon,
  export: ExportIcon,
  file: FileIcon,
  "hide-side-menu": HideSideMenuIcon,
  "identity-provider": IdentityProviderIcon,
  info: InfoIcon,
  "light-mode": LightModeIcon,
  link: LinkIcon,
  loading: LoadingIcon,
  logout: LogoutIcon,
  "more-options": MoreOptionsIcon,
  options: OptionsIcon,
  "new-chat": NewChatIcon,
  plus: PlusIcon,
  "prompt-send": PromptSendIcon,
  "prompt-stop": PromptStopIcon,
  refresh: RefreshIcon,
  "side-menu": SideMenuIcon,
  "scroll-to-bottom": ScrollToBottomIcon,
  settings: SettingsIcon,
  success: SuccessIcon,
  telemetry: TelemetryIcon,
  upload: UploadIcon,
};

export type IconName = keyof typeof icons;

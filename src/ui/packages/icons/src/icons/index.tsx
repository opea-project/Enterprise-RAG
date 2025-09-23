// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ComponentType } from "react";
import { IconBaseProps } from "react-icons";

import { AdminPanelIcon } from "@/icons/AdminPanelIcon";
import { BucketSynchronizationIcon } from "@/icons/BucketSynchronizationIcon";
import { ChatBotIcon } from "@/icons/ChatBotIcon";
import { ChatIcon } from "@/icons/ChatIcon";
import { CheckboxCheckIcon } from "@/icons/CheckboxCheckIcon";
import { CloseIcon } from "@/icons/CloseIcon";
import { CloseNotificationIcon } from "@/icons/CloseNotificationIcon";
import { ConfigurableServiceIcon } from "@/icons/ConfigurableServiceIcon";
import { CopyErrorIcon } from "@/icons/CopyErrorIcon";
import { CopyIcon } from "@/icons/CopyIcon";
import { CopySuccessIcon } from "@/icons/CopySuccessIcon";
import { DarkModeIcon } from "@/icons/DarkModeIcon";
import { DataPrepIcon } from "@/icons/DataPrepIcon";
import { DeleteIcon } from "@/icons/DeleteIcon";
import { DownloadIcon } from "@/icons/DownloadIcon";
import { EditIcon } from "@/icons/EditIcon";
import { EmbeddingIcon } from "@/icons/EmbeddingIcon";
import { ExportIcon } from "@/icons/ExportIcon";
import { ExternalLinkIcon } from "@/icons/ExternalLinkIcon";
import { FileIcon } from "@/icons/FileIcon";
import { HideSideMenuIcon } from "@/icons/HideSideMenuIcon";
import { IdentityProviderIcon } from "@/icons/IdentityProviderIcon";
import { InfoIcon } from "@/icons/InfoIcon";
import { LightModeIcon } from "@/icons/LightModeIcon";
import { LinkIcon } from "@/icons/LinkIcon";
import { LoadingIcon } from "@/icons/LoadingIcon";
import { LogoutIcon } from "@/icons/LogoutIcon";
import { MoreOptionsIcon } from "@/icons/MoreOptionsIcon";
import { NewChatIcon } from "@/icons/NewChatIcon";
import { OptionsIcon } from "@/icons/OptionsIcon";
import { PlusIcon } from "@/icons/PlusIcon";
import { PromptSendIcon } from "@/icons/PromptSendIcon";
import { PromptStopIcon } from "@/icons/PromptStopIcon";
import { RefreshIcon } from "@/icons/RefreshIcon";
import { ScrollToBottomIcon } from "@/icons/ScrollToBottomIcon";
import { SelectInputArrowDown } from "@/icons/SelectInputArrowDown";
import { SelectInputArrowUp } from "@/icons/SelectInputArrowUp";
import { SettingsIcon } from "@/icons/SettingsIcon";
import { SideMenuIcon } from "@/icons/SideMenuIcon";
import { SuccessIcon } from "@/icons/SuccessIcon";
import { TelemetryIcon } from "@/icons/TelemetryIcon";
import { UploadIcon } from "@/icons/UploadIcon";

export const icons: Record<string, ComponentType<IconBaseProps>> = {
  "admin-panel": AdminPanelIcon,
  "bucket-synchronization": BucketSynchronizationIcon,
  "chat-bot": ChatBotIcon,
  chat: ChatIcon,
  "checkbox-check": CheckboxCheckIcon,
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
  "select-input-arrow-down": SelectInputArrowDown,
  "select-input-arrow-up": SelectInputArrowUp,
  settings: SettingsIcon,
  success: SuccessIcon,
  telemetry: TelemetryIcon,
  upload: UploadIcon,
  "external-link": ExternalLinkIcon,
};

export type IconName = keyof typeof icons;

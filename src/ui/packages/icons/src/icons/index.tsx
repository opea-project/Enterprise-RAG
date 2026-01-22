// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ComponentType } from "react";
import { IconBaseProps } from "react-icons";

import { AdminPanelIcon } from "@/icons/AdminPanelIcon";
import { BucketSynchronizationIcon } from "@/icons/BucketSynchronizationIcon";
import { ChatBotIcon } from "@/icons/ChatBotIcon";
import { ChatIcon } from "@/icons/ChatIcon";
import { CheckboxCheckIcon } from "@/icons/CheckboxCheckIcon";
import { ClearIcon } from "@/icons/ClearIcon";
import { CloseIcon } from "@/icons/CloseIcon";
import { CloseNotificationIcon } from "@/icons/CloseNotificationIcon";
import { ConfigurableServiceIcon } from "@/icons/ConfigurableServiceIcon";
import { CopyErrorIcon } from "@/icons/CopyErrorIcon";
import { CopyIcon } from "@/icons/CopyIcon";
import { CopySuccessIcon } from "@/icons/CopySuccessIcon";
import { DarkModeIcon } from "@/icons/DarkModeIcon";
import { DataPrepIcon } from "@/icons/DataPrepIcon";
import { DeleteIcon } from "@/icons/DeleteIcon";
import { DocFileIcon } from "@/icons/DocFileIcon";
import { DocxFileIcon } from "@/icons/DocxFileIcon";
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
import { MdFileIcon } from "@/icons/MdFileIcon";
import { MoreOptionsIcon } from "@/icons/MoreOptionsIcon";
import { NewChatIcon } from "@/icons/NewChatIcon";
import { OptionsIcon } from "@/icons/OptionsIcon";
import { PanelHideIcon } from "@/icons/PanelHideIcon";
import { PanelShowIcon } from "@/icons/PanelShowIcon";
import { PdfFileIcon } from "@/icons/PdfFileIcon";
import { PinFilledIcon } from "@/icons/PinFilledIcon";
import { PinIcon } from "@/icons/PinIcon";
import { PlainTextIcon } from "@/icons/PlainTextIcon";
import { PlusIcon } from "@/icons/PlusIcon";
import { PromptSendIcon } from "@/icons/PromptSendIcon";
import { PromptStopIcon } from "@/icons/PromptStopIcon";
import { RefreshIcon } from "@/icons/RefreshIcon";
import { ScrollToBottomIcon } from "@/icons/ScrollToBottomIcon";
import { SearchIcon } from "@/icons/SearchIcon";
import { SelectInputArrowDown } from "@/icons/SelectInputArrowDown";
import { SelectInputArrowUp } from "@/icons/SelectInputArrowUp";
import { SettingsIcon } from "@/icons/SettingsIcon";
import { SideMenuIcon } from "@/icons/SideMenuIcon";
import { SortDownIcon } from "@/icons/SortDownIcon";
import { SortUpDownIcon } from "@/icons/SortUpDownIcon";
import { SortUpIcon } from "@/icons/SortUpIcon";
import { SuccessIcon } from "@/icons/SuccessIcon";
import { TelemetryIcon } from "@/icons/TelemetryIcon";
import { TextFileIcon } from "@/icons/TextFileIcon";
import { UploadIcon } from "@/icons/UploadIcon";

export const icons: Record<string, ComponentType<IconBaseProps>> = {
  "admin-panel": AdminPanelIcon,
  "bucket-synchronization": BucketSynchronizationIcon,
  "chat-bot": ChatBotIcon,
  chat: ChatIcon,
  "checkbox-check": CheckboxCheckIcon,
  clear: ClearIcon,
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
  "md-file": MdFileIcon,
  "doc-file": DocFileIcon,
  "docx-file": DocxFileIcon,
  "pdf-file": PdfFileIcon,
  pin: PinIcon,
  "pin-filled": PinFilledIcon,
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
  "panel-hide": PanelHideIcon,
  "panel-show": PanelShowIcon,
  "plain-text": PlainTextIcon,
  plus: PlusIcon,
  "prompt-send": PromptSendIcon,
  "prompt-stop": PromptStopIcon,
  refresh: RefreshIcon,
  "side-menu": SideMenuIcon,
  "scroll-to-bottom": ScrollToBottomIcon,
  search: SearchIcon,
  "select-input-arrow-down": SelectInputArrowDown,
  "select-input-arrow-up": SelectInputArrowUp,
  settings: SettingsIcon,
  "sort-down": SortDownIcon,
  "sort-up-down": SortUpDownIcon,
  "sort-up": SortUpIcon,
  success: SuccessIcon,
  telemetry: TelemetryIcon,
  "text-file": TextFileIcon,
  upload: UploadIcon,
  "external-link": ExternalLinkIcon,
};

export type IconName = keyof typeof icons;

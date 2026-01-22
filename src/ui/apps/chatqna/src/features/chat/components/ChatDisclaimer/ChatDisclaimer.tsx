// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatDisclaimer.scss";

import { getChatQnAAppEnv } from "@/utils";

const chatDisclaimerText = getChatQnAAppEnv("CHAT_DISCLAIMER_TEXT");

const ChatDisclaimer = () => (
  <p className="chat__disclaimer">{chatDisclaimerText}</p>
);

export default ChatDisclaimer;

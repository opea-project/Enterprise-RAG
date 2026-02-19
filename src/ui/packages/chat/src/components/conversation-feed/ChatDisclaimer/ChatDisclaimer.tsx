// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatDisclaimer.scss";

const CHAT_DISCLAIMER_DEFAULT_MESSAGE =
  "Responses from this solution may require further verification. You are solely responsible for verifying the accuracy of the information provided and how you choose to use it.";

interface ChatDisclaimerProps {
  message?: string;
}

export const ChatDisclaimer = ({
  message = CHAT_DISCLAIMER_DEFAULT_MESSAGE,
}: ChatDisclaimerProps) => <p className="chat__disclaimer">{message}</p>;

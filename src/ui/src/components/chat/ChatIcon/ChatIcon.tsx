// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatIcon.scss";

import { Icon } from "@iconify/react";
import classNames from "classnames";

interface ChatIconProps {
  forConversation?: boolean;
}

const ChatIcon = ({ forConversation }: ChatIconProps) => {
  const chatIconClassNames = classNames({
    "chat-page__icon": true,
    "chat-page__icon--conversation": forConversation,
  });
  return <Icon icon="token:atom" className={chatIconClassNames} />;
};

export default ChatIcon;

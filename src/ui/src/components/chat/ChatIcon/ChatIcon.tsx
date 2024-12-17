// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatIcon.scss";

import classNames from "classnames";
import { GiAtom } from "react-icons/gi";

interface ChatIconProps {
  forConversation?: boolean;
}

const ChatIcon = ({ forConversation }: ChatIconProps) => {
  const chatIconClassNames = classNames({
    "chat-page__icon": true,
    "chat-page__icon--conversation": forConversation,
  });
  return <GiAtom className={chatIconClassNames} />;
};

export default ChatIcon;

// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatBotIcon.scss";

import classNames from "classnames";
import { IconBaseProps } from "react-icons";
import { GiAtom } from "react-icons/gi";

interface ChatBotIconProps extends IconBaseProps {
  forConversation?: boolean;
}

const ChatBotIcon = ({
  forConversation,
  className,
  ...props
}: ChatBotIconProps) => {
  const chatIconClassNames = classNames([
    "chat-bot-icon",
    {
      "chat-bot-icon--conversation": forConversation,
    },
    className,
  ]);
  return <GiAtom className={chatIconClassNames} {...props} />;
};

export default ChatBotIcon;

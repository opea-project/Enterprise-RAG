// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessageAvatar.scss";

import { BsPersonCircle, BsRobot } from "react-icons/bs";

interface ChatMessageAvatarProps {
  isUserMessage: boolean;
}

const ChatMessageAvatar = ({ isUserMessage }: ChatMessageAvatarProps) => (
  <div className="chat-message-avatar">
    {isUserMessage ? <BsPersonCircle size={24} /> : <BsRobot size={24} />}
    <p className="chat-message-avatar__name">
      {isUserMessage ? "You" : "ChatBot"}
    </p>
  </div>
);

export default ChatMessageAvatar;

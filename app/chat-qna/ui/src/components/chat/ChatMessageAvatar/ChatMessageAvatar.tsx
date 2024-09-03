// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessageAvatar.scss";

import MemoryIcon from "@mui/icons-material/Memory";
import PersonIcon from "@mui/icons-material/Person";
import { Typography } from "@mui/material";

interface ChatMessageAvatarProps {
  isUserMessage: boolean;
}

const ChatMessageAvatar = ({ isUserMessage }: ChatMessageAvatarProps) => (
  <div className="chat-message-avatar">
    {isUserMessage ? <PersonIcon /> : <MemoryIcon />}
    <Typography variant="chat-avatar-name-label">
      {isUserMessage ? "You" : "ChatBot"}
    </Typography>
  </div>
);

export default ChatMessageAvatar;

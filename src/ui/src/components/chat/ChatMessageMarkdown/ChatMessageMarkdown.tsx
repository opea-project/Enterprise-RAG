// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessageMarkdown.scss";

import { PropsWithChildren } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

const CustomPre = ({ children }: PropsWithChildren) => (
  <pre className="custom-pre-markdown">{children}</pre>
);

const CustomCode = ({ children }: PropsWithChildren) => (
  <code className="custom-code-markdown">{children}</code>
);

const CustomParagraph = ({ children }: PropsWithChildren) => (
  <p className="custom-paragraph-markdown">{children}</p>
);

const customMarkdownComponents = {
  code: CustomCode,
  pre: CustomPre,
  p: CustomParagraph,
};

interface ChatMessageMarkdownProps {
  text: string;
}

const ChatMessageMarkdown = ({ text }: ChatMessageMarkdownProps) => (
  <section className="chatbot-answer">
    <Markdown remarkPlugins={[remarkGfm]} components={customMarkdownComponents}>
      {text}
    </Markdown>
  </section>
);

export default ChatMessageMarkdown;

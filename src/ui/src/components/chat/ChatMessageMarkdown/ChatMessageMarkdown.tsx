// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatMessageMarkdown.scss";

import { AnchorHTMLAttributes, PropsWithChildren } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import Anchor from "@/components/shared/Anchor/Anchor";
import parseChildrenTextContent from "@/utils/parseChildrenTextContent";

const CustomPre = ({ children }: PropsWithChildren) => (
  <pre className="custom-pre-markdown">{children}</pre>
);

const CustomCode = ({ children }: PropsWithChildren) => (
  <code className="custom-code-markdown">
    {parseChildrenTextContent(children)}
  </code>
);

const CustomAnchor = (props: AnchorHTMLAttributes<HTMLAnchorElement>) => (
  <Anchor {...props} />
);

const customMarkdownComponents = {
  code: CustomCode,
  pre: CustomPre,
  a: CustomAnchor,
};

interface ChatMessageMarkdownProps {
  text: string;
}

const ChatMessageMarkdown = ({ text }: ChatMessageMarkdownProps) => (
  <section className="chat-message-markdown">
    <Markdown remarkPlugins={[remarkGfm]} components={customMarkdownComponents}>
      {text}
    </Markdown>
  </section>
);

export default ChatMessageMarkdown;

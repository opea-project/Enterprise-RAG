// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { customMarkdownComponents } from "@/components/markdown/components";

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer = ({ content }: MarkdownRendererProps) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm]} // GitHub Flavored Markdown Plugin
    components={customMarkdownComponents}
    className="max-w-full text-wrap break-words md:max-w-[42rem]"
  >
    {content}
  </ReactMarkdown>
);

export default MarkdownRenderer;

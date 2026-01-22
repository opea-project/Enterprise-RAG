// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

import { parseMarkdown } from "@/utils";
import { CHECK_ICON, COPY_ICON, ERROR_ICON } from "@/utils/icons";

export interface MarkdownProps {
  /**
   * Markdown text to be rendered. If plain text is passed, formatting will not be applied.
   */
  text: string;
}

/**
 * Component for rendering markdown.
 * @param {MarkdownProps} props - Component props.
 */
export function Markdown({ text }: MarkdownProps) {
  const [html, setHtml] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const parsed = parseMarkdown(text);
      setHtml(parsed);
      setError(null);
    } catch (err) {
      console.error("Markdown parsing error:", err);
      setError("Failed to parse markdown content");
      // Fallback: display raw text escaped
      const div = document.createElement("div");
      div.textContent = text;
      setHtml(
        `<pre class="whitespace-pre-wrap text-sm text-light-status-error dark:text-dark-status-error">${div.innerHTML}</pre>`,
      );
    }
  }, [text]);

  useEffect(() => {
    const onClick = async (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const btn = target.closest(
        ".markdown-copy-btn",
      ) as HTMLButtonElement | null;
      if (!btn) return;

      const block = btn.closest(".markdown-code-block");
      const codeEl = block?.querySelector("pre > code");
      if (!codeEl) return;

      const iconEl = btn.querySelector(".markdown-copy-icon");
      const textEl = btn.querySelector(".markdown-copy-text");
      if (!iconEl || !textEl) return;

      const text = codeEl.textContent ?? "";
      try {
        await navigator.clipboard.writeText(text);
        iconEl.innerHTML = CHECK_ICON;
        textEl.textContent = "Copied!";
        setTimeout(() => {
          iconEl.innerHTML = COPY_ICON;
          textEl.textContent = "Copy";
        }, 1500);
      } catch {
        iconEl.innerHTML = ERROR_ICON;
        textEl.textContent = "Failed";
        setTimeout(() => {
          iconEl.innerHTML = COPY_ICON;
          textEl.textContent = "Copy";
        }, 1500);
      }
    };

    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  return (
    <>
      {error && (
        <div
          className="border-light-status-error dark:border-dark-status-error bg-light-status-error/10 dark:bg-dark-status-error/10 text-light-status-error dark:text-dark-status-error mb-2 rounded border px-3 py-2 text-sm"
          role="alert"
        >
          {error}
        </div>
      )}
      <div
        dangerouslySetInnerHTML={{ __html: html }}
        className="max-w-full text-wrap break-words md:max-w-[42rem]"
      />
    </>
  );
}

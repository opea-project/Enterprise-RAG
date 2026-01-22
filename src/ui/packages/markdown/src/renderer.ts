// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeHref } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import type { RendererObject } from "marked";

import hljs from "@/config/highlightjs";
import { escapeHtml } from "@/utils";
import { COPY_ICON } from "@/utils/icons";
import { CSS_CLASSES, HEADING_STYLES } from "@/utils/styles";

export default {
  // ===================
  // Block-level elements
  // ===================

  code({ text, lang }) {
    const trimmedLang = lang?.trim() ?? "";
    const langInfo = hljs.getLanguage(trimmedLang);
    const langLabel = langInfo?.name ?? "Plain Text";
    const escapedLangLabel = escapeHtml(langLabel);

    let highlightedCode: string;
    try {
      if (langInfo && langLabel !== "text") {
        highlightedCode = hljs.highlight(text, {
          language: trimmedLang, // Use the original language alias, not the display name
        }).value;
      } else {
        highlightedCode = escapeHtml(text);
      }
    } catch {
      highlightedCode = escapeHtml(text);
    }

    return `<div class="markdown-code-block mb-4 rounded ${CSS_CLASSES.CONTRAST_BG}" data-lang="${escapedLangLabel}">
      <div class="${CSS_CLASSES.PRIMARY_BG} flex items-center justify-between rounded-t pl-3 pr-2 py-2 text-xs">
        <span class="select-none font-medium">${escapedLangLabel}</span>
        <button type="button" data-markdown-copy="true" class="markdown-copy-btn flex items-center gap-1.5 px-2 h-6 min-w-fit rounded transition-colors bg-black/20 hover:bg-black/40" aria-label="Copy code">
          <span class="markdown-copy-text">Copy</span>
          <span class="markdown-copy-icon">${COPY_ICON}</span>
        </button>
      </div>
      <div class="py-2 pl-3 pr-2 overflow-auto">
        <pre class="m-0 whitespace-pre text-sm"><code class="language-${escapedLangLabel} m-0 bg-transparent p-0 box-border max-w-full overflow-visible whitespace-pre-wrap break-words">${highlightedCode}</code></pre>
      </div>
    </div>`;
  },

  blockquote({ tokens }) {
    const text = this.parser.parse(tokens);
    return `<blockquote class="${CSS_CLASSES.ACCENT_BORDER} border-l-2 pl-3 italic [&_strong]:not-italic [&_strong]:font-semibold [&_code]:not-italic [&_.markdown-code-block]:not-italic">${text}</blockquote>`;
  },

  heading({ tokens, depth }) {
    const text = this.parser.parseInline(tokens);
    const styles = HEADING_STYLES[depth];
    if (!styles) return false;

    const classes = `mb-0 first:mt-0 ${styles} font-medium`;
    return `<h${depth} class="${classes}">${text}</h${depth}>`;
  },

  hr() {
    return `<hr class="${CSS_CLASSES.ACCENT_BORDER} my-4 border border-solid" />`;
  },

  list({ ordered, start, items }) {
    const tag = ordered ? "ol" : "ul";
    const classes = classNames("mb-4", "[&:last-child]:mb-0", {
      "list-decimal pl-10": ordered,
      "list-disc pl-6": !ordered,
    });
    const startAttr =
      ordered && start && start !== 1 ? ` start="${start}"` : "";
    const body = items.map((item) => this.listitem(item)).join("");
    return `<${tag} class="${classes}"${startAttr}>${body}</${tag}>`;
  },

  listitem({ tokens, task }) {
    const parsedTokens = this.parser.parse(tokens);
    const classes = classNames("text-sm", { "list-none": task });
    return `<li class="${classes}">${parsedTokens}</li>`;
  },

  checkbox({ checked }) {
    return `<input ${checked ? "checked" : ""} type="checkbox" class="mr-2 align-middle pointer-events-none accent-light-primary dark:accent-dark-primary" />`;
  },

  paragraph({ tokens }) {
    const text = this.parser.parseInline(tokens);
    return `<p class="whitespace-pre-wrap break-words text-base [&:not(:last-child)]:mb-2">${text}</p>`;
  },

  table({ header, rows }) {
    const headerRow = header.map((cell) => this.tablecell(cell)).join("");
    const rowsHtml = rows
      .map((row) => {
        const cells = row.map((cell) => this.tablecell(cell)).join("");
        return `<tr class="[&:not(:has(th)):not(:last-of-type)]:border-b [&:not(:has(th)):not(:last-of-type)]:border-b-light-border [&:not(:has(th)):not(:last-of-type)]:dark:border-b-dark-border">${cells}</tr>`;
      })
      .join("");

    return `<table class="mb-0 w-full text-xs [&:not(:last-child)]:mb-4">
        <thead><tr>${headerRow}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>`;
  },

  tablecell({ tokens, header, align }) {
    const text = this.parser.parseInline(tokens);
    const tag = header ? "th" : "td";

    const classes = classNames("px-3", "py-1", {
      "text-left": !align || align === "left",
      "text-center": align === "center",
      "text-right": align === "right",
      [CSS_CLASSES.PRIMARY_BG]: header,
      "font-semibold h-8 first:rounded-tl last:rounded-tr": header,
      "h-10": !header,
    });
    return `<${tag} class="${classes}">${text}</${tag}>`;
  },

  // ===================
  // Inline elements
  // ===================

  strong({ tokens }) {
    const text = this.parser.parseInline(tokens);
    return `<strong class="font-semibold">${text}</strong>`;
  },

  em({ tokens }) {
    const text = this.parser.parseInline(tokens);
    return `<em class="italic">${text}</em>`;
  },

  codespan({ text }) {
    const escapedText = escapeHtml(text);
    return `<code class="whitespace-pre-wrap p-1 rounded bg-gray-100 dark:bg-dark-bg-contrast text-light-text-primary dark:text-dark-text-primary text-sm">${escapedText}</code>`;
  },

  br() {
    return "<br />";
  },

  del({ tokens }) {
    const text = this.parser.parseInline(tokens);
    return `<del class="line-through italic">${text}</del>`;
  },

  link({ href, tokens, title }) {
    const sanitizedHref = sanitizeHref(href) ?? "#";
    const escapedTitle = title ? escapeHtml(title) : "";
    const titleAttr = escapedTitle ? ` title="${escapedTitle}"` : "";
    const text = this.parser.parseInline(tokens);
    return `<a href="${sanitizedHref}"${titleAttr} target="_blank" rel="noopener noreferrer" class="underline underline-offset-4 text-light-text-accent dark:text-dark-text-accent">${text}</a>`;
  },

  image({ href, title, text }) {
    const sanitizedSrc = sanitizeHref(href) ?? "#";
    const escapedAlt = escapeHtml(text);
    const escapedTitle = title ? escapeHtml(title) : "";
    const titleAttr = escapedTitle ? ` title="${escapedTitle}"` : "";
    return `<img src="${sanitizedSrc}" alt="${escapedAlt}"${titleAttr} class="h-64 rounded" />`;
  },
} as RendererObject;

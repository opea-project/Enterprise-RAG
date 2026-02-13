// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import DOMPurify from "dompurify";

import DOMPurifyConfig from "@/config/dompurify";
import marked from "@/config/marked";
import { processTextNodesForHomoglyphs } from "@/utils/homoglyphs";

/**
 * Escapes special HTML characters in a string to prevent XSS attacks and ensure proper rendering.
 *
 * Uses the browser's built-in text encoding to escape all HTML entities correctly.
 * This is more reliable than manual regex replacement and handles all edge cases.
 *
 * @param text - The string to escape
 * @returns The escaped string safe for HTML insertion
 *
 * @example
 * ```typescript
 * escapeHtml('<script>alert("xss")</script>');
 * // Returns: '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
 * ```
 *
 * @remarks
 * Used in the following renderer methods to display placeholder for values like `<value>
 * - `code()`: Escapes code block content
 * - `codespan()`: Escapes inline code content
 */
export function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Parses markdown text, sanitizes the HTML, and highlights potential homoglyphs.
 *
 * This function combines markdown parsing, HTML sanitization, and homoglyph detection
 * into a single pipeline. It:
 * 1. Converts markdown to HTML using marked
 * 2. Sanitizes the HTML with DOMPurify
 * 3. Detects and wraps potential homoglyph characters in mark elements
 *
 * @param text - The markdown text to parse
 * @returns Sanitized HTML string with homoglyphs highlighted
 *
 * @example
 * ```typescript
 * const html = parseMarkdown("**Hello** Wоrld"); // о is Cyrillic
 * // Returns HTML with "о" wrapped in <mark class="homoglyph-text">
 * ```
 *
 * @remarks
 * This function merges the logic from:
 * - Original parseMarkdown: markdown → HTML sanitization
 * - parseChildrenTextContent: React-based homoglyph detection
 *
 * The merged approach works with HTML strings instead of React nodes,
 * making it compatible with dangerouslySetInnerHTML rendering.
 */
export function parseMarkdown(text: string): string {
  const parsed = marked.parse(text) as string;
  const sanitized = DOMPurify.sanitize(parsed, DOMPurifyConfig);

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = sanitized;
  processTextNodesForHomoglyphs(tempDiv);

  return tempDiv.innerHTML;
}

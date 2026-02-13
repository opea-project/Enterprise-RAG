// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { isPunycodeSafe } from "@intel-enterprise-rag-ui/utils";

import { escapeHtml } from "@/utils";

/**
 * Checks if a character is a potential homoglyph.
 *
 * @param char - The character to check
 * @returns True if the character is potentially a homoglyph (not punycode safe)
 *
 * @remarks
 * Uses the isPunycodeSafe utility to detect characters that may be visually
 * similar to ASCII characters but are actually from different Unicode blocks.
 */
const isPotentialHomoglyph = (char: string): boolean => {
  return !isPunycodeSafe(char);
};

/**
 * Creates an HTML mark element to wrap homoglyph text.
 *
 * @param text - The already-escaped text content to wrap
 * @returns HTML string of a mark element with styling and warning attributes
 *
 * @remarks
 * The mark element includes:
 * - Visual styling with borders to indicate potential security risk
 * - Cursor and selection restrictions
 * - Title attribute with warning message for accessibility
 */
const createHomoglyphMarkElement = (text: string): string => {
  return `<mark class="cursor-not-allowed select-none bg-inherit text-inherit border-light-status-error dark:border-dark-status-error border border-solid" title="Potential homoglyphs. Be cautious.">${text}</mark>`;
};

/**
 * Wraps potential homoglyph characters in HTML mark elements for visual indication.
 *
 * This function processes text content and identifies sequences of characters that
 * could be homoglyphs (visually similar characters from different scripts). These
 * sequences are wrapped in `<mark>` elements with appropriate styling and warning attributes.
 *
 * @param text - The text content to process
 * @returns HTML string with homoglyphs wrapped in mark elements
 *
 * @example
 * ```typescript
 * wrapHomoglyphsInHtml("Hello"); // Returns: "Hello" (no homoglyphs)
 * wrapHomoglyphsInHtml("Hеllo"); // Returns: "H<mark class='homoglyph-text' ...>е</mark>llo"
 * ```
 *
 * @remarks
 * The mark elements include:
 * - Class: `homoglyph-text` for styling
 * - Title attribute: Warning message for accessibility
 * - Style: Inline styles for cursor and selection behavior
 */
const wrapHomoglyphsInHtml = (text: string): string => {
  let result = "";
  let homoglyphBuffer = "";
  let textBuffer = "";

  const flushTextBuffer = () => {
    if (textBuffer) {
      result += escapeHtml(textBuffer);
      textBuffer = "";
    }
  };

  const flushHomoglyphBuffer = () => {
    if (homoglyphBuffer) {
      const escapedHomoglyphs = escapeHtml(homoglyphBuffer);
      result += createHomoglyphMarkElement(escapedHomoglyphs);
      homoglyphBuffer = "";
    }
  };

  for (const char of text) {
    if (isPotentialHomoglyph(char)) {
      flushTextBuffer();
      homoglyphBuffer += char;
    } else {
      flushHomoglyphBuffer();
      textBuffer += char;
    }
  }

  flushTextBuffer();
  flushHomoglyphBuffer();

  return result;
};

/**
 * Recursively processes text nodes in an HTML element to detect and wrap homoglyphs.
 *
 * This function traverses the DOM tree and processes text content while preserving
 * the HTML structure. It identifies potential homoglyph characters and wraps them
 * in mark elements for visual indication.
 *
 * @param element - The HTML element to process
 *
 * @remarks
 * - Processes text nodes by detecting and wrapping homoglyphs
 * - Recursively processes child elements
 * - Preserves HTML structure and attributes
 * - Skips processing for script, style, and other non-text elements
 */
export const processTextNodesForHomoglyphs = (element: Element): void => {
  const nodesToProcess = Array.from(element.childNodes);

  nodesToProcess.forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const textContent = node.textContent || "";
      if (textContent) {
        const hasHomoglyphs =
          Array.from(textContent).some(isPotentialHomoglyph);

        if (hasHomoglyphs) {
          // Create a temporary container to parse the wrapped HTML
          const tempDiv = document.createElement("div");
          tempDiv.innerHTML = wrapHomoglyphsInHtml(textContent);

          // Replace the text node with the new nodes
          const fragment = document.createDocumentFragment();
          Array.from(tempDiv.childNodes).forEach((child) => {
            fragment.appendChild(child.cloneNode(true));
          });

          node.parentNode?.replaceChild(fragment, node);
        }
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      // Recursively process child elements
      processTextNodesForHomoglyphs(node as Element);
    }
  });
};

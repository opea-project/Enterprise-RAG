// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Config } from "dompurify";
import DOMPurify from "dompurify";

/**
 * Add security hook to ensure only marked buttons are allowed.
 * Removes any button elements that don't have the data-markdown-copy attribute.
 */
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "BUTTON") {
    if (!node.hasAttribute("data-markdown-copy")) {
      node.remove();
    }
  }
});

/**
 * DOMPurify configuration for sanitizing markdown-generated HTML.
 *
 * This configuration provides a strict allowlist of HTML tags and attributes
 * to prevent XSS attacks while allowing standard markdown features.
 *
 * @remarks
 * - ALLOWED_TAGS: Only safe HTML elements from markdown rendering
 * - ALLOWED_ATTR: Only necessary attributes for styling and functionality
 * - FORBID_TAGS: Explicitly blocks dangerous elements
 * - FORBID_ATTR: Blocks event handlers that could execute scripts
 * - ALLOW_DATA_ATTR: Disabled to prevent data attribute injection
 */
const config: Config = {
  ALLOWED_TAGS: [
    // Text formatting
    "p",
    "br",
    "strong",
    "em",
    "del",
    "code",
    "pre",
    // Headings
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    // Lists
    "ul",
    "ol",
    "li",
    // Tables
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    // Block elements
    "blockquote",
    "hr",
    "div",
    "span",
    // Links and images
    "a",
    "img",
    // Homoglyph warnings
    "mark",
    // Task list checkboxes
    "input",
    // Interactive elements
    "button",
    // SVG elements for copy icon
    "svg",
    "path",
    "rect",
    "polyline",
    "line",
  ],
  ALLOWED_ATTR: [
    "href",
    "src",
    "alt",
    "title",
    "class",
    "id",
    "target",
    "rel",
    "aria-label",
    "checked",
    "disabled",
    "type",
    "data-lang",
    "data-markdown-copy",
    "style",
    // SVG attributes
    "width",
    "height",
    "viewBox",
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "rx",
    "ry",
    "d",
    "points",
  ],
  ALLOWED_URI_REGEXP:
    /^(?:(?:(?:f|ht)tps?|mailto|tel):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i,
  FORBID_TAGS: ["script", "style", "iframe", "object", "embed", "form"],
  FORBID_ATTR: ["onerror", "onload", "onclick"],
  ALLOW_DATA_ATTR: false,
};

export default config;

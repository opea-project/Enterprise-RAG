// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Marked } from "marked";

import renderer from "@/renderer";

/**
 * Configure marked with custom renderer
 *
 * The Marked library is used to parse markdown text into HTML.
 * We provide a custom renderer that:
 * - Adds syntax highlighting to code blocks via highlight.js
 * - Applies custom CSS classes for styling
 * - Implements copy-to-clipboard functionality for code blocks
 * - Sanitizes links and images for security
 * - Handles all markdown elements (headings, lists, tables, blockquotes, etc.)
 */
const marked = new Marked().use({ renderer });

export default marked;

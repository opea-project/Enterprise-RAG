// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * SVG markup for the copy icon displayed in code block copy buttons.
 *
 * @remarks
 * Used in:
 * - `code()` renderer method: Initial copy button icon
 * - Markdown component: Copy button click handler for icon states
 */
export const COPY_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;

/**
 * SVG markup for the success checkmark icon displayed after successful copy.
 *
 * @remarks
 * Used in the markdown renderer's copy button click handler to indicate successful copy operation.
 */
export const CHECK_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-light-status-success dark:text-dark-status-success"><polyline points="20 6 9 17 4 12"></polyline></svg>`;

/**
 * SVG markup for the error icon displayed when copy operation fails.
 *
 * @remarks
 * Used in the markdown renderer's copy button click handler to indicate failed copy operation.
 */
export const ERROR_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-light-status-error dark:text-dark-status-error"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/**
 * Mapping of heading levels (1-6) to their corresponding Tailwind CSS classes.
 *
 * Each heading level has predefined margin and text size classes to maintain
 * consistent visual hierarchy throughout the rendered markdown content.
 *
 * @remarks
 * Used in the `heading()` renderer method to apply consistent styling to all heading levels.
 * Aligned with Typography.module.scss from the components folder.
 */
export const HEADING_STYLES: Record<number, string> = {
  1: "text-2xl [&:not(:first-child)]:mt-6 [&:not(:last-child)]:mb-3",
  2: "text-xl [&:not(:first-child)]:mt-5 [&:not(:last-child)]:mb-3",
  3: "text-lg [&:not(:first-child)]:mt-4 [&:not(:last-child)]:mb-3",
  4: "text-base [&:not(:first-child)]:mt-3 [&:not(:last-child)]:mb-2",
  5: "text-sm [&:not(:first-child)]:mt-2 [&:not(:last-child)]:mb-2",
  6: "text-xs [&:not(:first-child)]:mt-2 [&:not(:last-child)]:mb-1",
} as const;

/**
 * Common CSS class combinations used throughout the markdown renderer.
 *
 * @remarks
 * These constants reduce duplication of frequently used Tailwind class patterns.
 */
export const CSS_CLASSES = {
  /** Background and text colors for contrasting content blocks */
  CONTRAST_BG:
    "bg-light-bg-contrast dark:bg-dark-bg-contrast text-light-text-primary dark:text-dark-text-primary",
  /** Primary background and text colors (headers, buttons) */
  PRIMARY_BG:
    "bg-light-primary dark:bg-dark-primary text-light-text-inverse dark:text-dark-text-primary",
  /** Border colors for accents and dividers */
  ACCENT_BORDER: "border-light-accent dark:border-dark-accent",
} as const;

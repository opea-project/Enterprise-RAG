// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import hljs from "highlight.js";

/**
 * Highlight.js configuration for secure syntax highlighting.
 *
 * This configuration prioritizes security by:
 * 1. Including all language packs for comprehensive syntax highlighting
 *    Note: To reduce bundle size, you can register only specific languages:
 *    ```
 *    import hljs from 'highlight.js/lib/core';
 *    import javascript from 'highlight.js/lib/languages/javascript';
 *    import python from 'highlight.js/lib/languages/python';
 *    hljs.registerLanguage('javascript', javascript);
 *    hljs.registerLanguage('python', python);
 *    ```
 *    This can significantly reduce the build size (from ~500KB to ~50KB+ depending on languages).
 * 2. Throwing errors on unescaped HTML (prevents XSS attacks)
 * 3. Enabling safe mode (disables HTML rendering in code)
 */

// Throw errors if unescaped HTML is detected in code blocks
// This prevents potential XSS attacks through code injection
hljs.configure({
  throwUnescapedHTML: true,
});

// Enable safe mode to disable HTML rendering and force plain text handling
// Additional layer of XSS protection
hljs.safeMode();

export default hljs;

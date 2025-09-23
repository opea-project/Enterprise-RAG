# @intel-enterprise-rag-ui/markdown

This package provides a React component for markdown parsing and rendering in the Intel® AI for Enterprise RAG UI. It is based on `react-markdown` and `react-syntax-highlighter` packages along with components and styles that are a part of `@intel-enterprise-rag-ui` pnpm workspace. GitHub Flavored Markdown is supported by using `remark-gfm` plugin.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/markdown": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import `index.scss` from this package into your main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/markdown/index.scss";
```

Import `MarkdownRenderer` component into your code:

```js
import { MarkdownRenderer } from "@intel-enterprise-rag-ui/markdown";

// Usage in a React component
function MyMarkdown() {
  return <MarkdownRenderer markdown={"# Hello World"} />;
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

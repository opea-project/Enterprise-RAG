# @intel-enterprise-rag-ui/components

This package provides reusable UI components and color scheme management utilities for the Intel® AI for Enterprise RAG UI.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/components": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import `index.scss` from this package into your main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/components/index.scss";
```

Import components from this package into your code:

```js
import { Button } from "@intel-enterprise-rag-ui/components";

// Usage in a React component
function MyComponent() {
  return <Button>Click me</Button>;
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

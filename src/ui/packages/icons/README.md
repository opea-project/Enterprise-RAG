# @intel-enterprise-rag-ui/icons

This package provides a large set of React icon components for the Intel® AI for Enterprise RAG UI.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/icons": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import icons from this package into your code:

```js
import { ChatIcon } from "@intel-enterprise-rag-ui/icons";

// Usage in a React component
function MyComponent() {
  return <ChatIcon />;
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

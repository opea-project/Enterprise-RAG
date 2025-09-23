# @intel-enterprise-rag-ui/utils

This package provides utility functions for the Intel® AI for Enterprise RAG UI.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/utils": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import utility functions from this package into your code:

```js
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";

// Usage example
const clean = sanitizeString("<b>unsafe</b>");
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

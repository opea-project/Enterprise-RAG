# @intel-enterprise-rag-ui/input-validation

This package provides utility functions for input validation in the Intel® AI for Enterprise RAG UI applications.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/input-validation": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import validation functions from this package into your code:

```js
import { containsNullCharacters } from "@intel-enterprise-rag-ui/input-validation";

// Usage example
const isSafeFileName = containsNullCharacters(...);
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

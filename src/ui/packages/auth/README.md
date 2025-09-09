# @intel-enterprise-rag-ui/auth

This package provides logic for handling authentication and session, along with a custom React hook for automatic token refresh. Both utilities are built as a wrapper around the `keycloak-js` package and are tailored for use in Intel® AI for Enterprise RAG UI applications.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in your apps or in other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/auth": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm build
```

Import authentication utilities into your code:

```js
import { KeycloakService } from "@intel-enterprise-rag-ui/auth";

// Usage example
const keycloakService = new KeycloakService();
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

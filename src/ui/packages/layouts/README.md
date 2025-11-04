# @intel-enterprise-rag-ui/layouts

This package provides reusable layout components for the Intel® AI for Enterprise RAG UI.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/layouts": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import `style.scss` from this package into your main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/layouts/style.scss";
```

Import layouts from this package into your code:

```js
import { PageLayout } from "@intel-enterprise-rag-ui/layouts";

// Usage in a React component
function MyPage() {
  return <PageLayout>...</PageLayout>;
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

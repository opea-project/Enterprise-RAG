# @intel-enterprise-rag-ui/control-plane

This package provides reusable Control Plane panel component that displays microservices pipeline graph for the Intel® AI for Enterprise RAG UI.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/control-plane": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import `style.scss` from this package into your main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/control-plane/style.scss";
```

Import `PipelineGraph` component from this package into your code:

```js
import { ControlPlanePanel } from "@intel-enterprise-rag-ui/control-plane";

// Usage in a React component
function ControlPlaneTab() {
  ...
  return (
    <ControlPlanePanel
      isLoading={isLoading}
      isRenderable={isRenderable}

    />
  );
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

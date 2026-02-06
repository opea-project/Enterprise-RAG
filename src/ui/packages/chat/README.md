# @intel-enterprise-rag-ui/chat

This package provides reusable UI components, layouts and utilites for the Intel® AI for Enterprise RAG UI applications with chat.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/chat": "workspace:*"
  }
}
```

Rebuild pnpm workspace to include new dependency:

```bash
pnpm install && pnpm -r build
```

Import `style.scss` from this package into your main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/chat/style.scss";
```

Import components from this package into your code:

```tsx
import { PromptInput } from "@intel-enterprise-rag-ui/chat";
import { useState } from "react";

// Usage in a React component
function MyComponent() {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (promptText: string) => {
    console.log("Submitted:", promptText);
    setPrompt("");
  };

  return (
    <PromptInput
      prompt={prompt}
      onChange={(e) => setPrompt(e.target.value)}
      onSubmit={handleSubmit}
    />
  );
}
```

## License

See [`LICENSE`](../../../../LICENSE) for license information.

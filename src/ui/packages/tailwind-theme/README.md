# @intel-enterprise-rag-ui/tailwind-theme

This package provides a custom Tailwind CSS theme for the Intel® AI for Enterprise RAG UI, including a shared Tailwind CSS configuration (tailwind.config.js) with a custom color palette, dark/light mode, and design tokens, as well as index.scss with base styles, font, scrollbar, and theme variables.

## Table of Contents

- [Usage](#usage)
- [License](#license)

## Usage

You can use this package in apps or other packages within the workspace.

Add the package as a dependency in `package.json`:

```json
{
  "dependencies": {
    "@intel-enterprise-rag-ui/tailwind-theme": "workspace:*"
  }
}
```

> [!NOTE] No build step is required for this package. It only contains SCSS and config.js files that are consumed directly. After installing, you can immediately import and use its configuration and styles in your project.

Use Tailwind theme config from this package in your `tailwind.config.js`:

```js
const sharedConfig = require("@intel-enterprise-rag-ui/tailwind-theme/tailwind.config.js");

module.exports = {
  ...sharedConfig,
};
```

Import `index.scss` from this package into main SCSS file:

```scss
@import "@intel-enterprise-rag-ui/tailwind-theme/index.scss";
```

> [!IMPORTANT]
> Tailwind theme styles should always be imported first to correctly apply it to the application.

## License

See [`LICENSE`](../../../../LICENSE) for license information.

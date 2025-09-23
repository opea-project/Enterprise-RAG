# Intel® AI for Enterprise RAG UI

This is the monorepo for the **Intel® AI for Enterprise RAG UI**, containing UI applications for different RAG solutions and supporting packages. It uses [pnpm](https://pnpm.io/) for fast, efficient package management and workspace support.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Workspace Structure](#workspace-structure)
  - [Apps](#apps)
  - [Packages](#packages)
- [Getting Started](#getting-started)
  - [Install dependencies](#install-dependencies)
  - [Build all packages](#build-all-packages)
  - [Launch the UI development server](#launch-the-ui-development-server)
- [License](#license)

## Prerequisites

- [Node.js](https://nodejs.org/) version 20 or higher
- [pnpm](https://pnpm.io/) version 8 or higher
- [npm](https://www.npmjs.com/) version 10 or higher

To check if all were successfully installed run the following commands:

```bash
node --version
```

```bash
npm --version
```

```bash
pnpm --version
```

`--version` option can be replaced with `-v` shorthand

## Workspace Structure

### Apps

- [@intel-enterprise-rag-ui/chatqna](apps/chatqna)

### Packages

- [@intel-enterprise-rag-ui/auth](packages/auth)
- [@intel-enterprise-rag-ui/components](packages/components)
- [@intel-enterprise-rag-ui/icons](packages/icons)
- [@intel-enterprise-rag-ui/layouts](packages/layouts)
- [@intel-enterprise-rag-ui/markdown](packages/markdown)
- [@intel-enterprise-rag-ui/tailwind-theme](packages/tailwind-theme)
- [@intel-enterprise-rag-ui/utils](packages/utils)

## Getting Started

### Install dependencies

```bash
pnpm install
```

This command will install dependencies for all apps and packages in this workspace.

### Build all packages

```bash
pnpm -r build
```

This command runs `build` scripts defined inside `package.json` files of all packages and apps in the workspace, ensuring every dependency is compiled before running the app.

### Launch the UI development server

To start the **Intel® AI for Enterprise RAG ChatQnA UI**, navigate to the `apps/chatqna` directory and run the development server:

```bash
cd apps/chatqna
npm run dev
```

The application will be available at `http://localhost:5173` by default.

For additional details on running and deploying **Intel® AI for Enterprise RAG ChatQnA UI**, refer to its [README](/apps/chatqna/README.md).

## License

See [LICENSE](../../LICENSE) in the repository root.

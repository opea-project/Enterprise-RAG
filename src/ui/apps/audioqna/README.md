# Intel® AI for Enterprise RAG AudioQnA UI

## Table of Contents

- [Requirements](#requirements)
- [Setup](#setup)
  - [Build all packages within the workspace](#build-all-packages-within-the-workspace)
- [Start UI Development Server](#start-ui-development-server)
- [Production Build](#production-build)
  - [Testing production build locally](#testing-production-build-locally)
  - [Deploying production build using Dockerfile](#deploying-production-build-using-dockerfile)
  - [Image configuration](#image-configuration)
  - [Configuring AudioQnA UI for deployment](#configuring-audioqna-ui-for-deployment)

## Requirements

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

## Setup

### Build all packages within the workspace

Go to the root of **Intel® AI for Enterprise RAG UI** pnpm workspace (`src/ui`) and run the following commands.

```bash
pnpm install && pnpm -r build
```

## Start UI Development Server

Run the following command to start UI development server:

```bash
npm run dev
```

By default, it will run on `http://localhost:5173`.

The port and IP address can be changed by setting `--port` and `--host` options
for npm `dev` script inside `package.json` file.

```json
{
  "dev": "vite dev --port 9090 --host 127.0.0.1"
}
```

These options can also be set via CLI by adding inline options `-- --port <port> --host <ip>`.

```bash
npm run dev -- --port 9090 --host 127.0.0.1
```

## Production Build

Run `npm run build` command to build the app.
By default, the build package will be placed at `dist` folder.

### Testing production build locally

Once the build is ready, it can be tested locally by running `npm run preview` command.

This command will boot up a local static web server that serves the files
from `dist` folder at `http://localhost:4173`.

The port of the server can be changed by setting `--port` option
for npm `preview` script inside `package.json` file.

```json
{
  "preview": "vite preview --port 8080"
}
```

This option can also be set via CLI by adding inline option `-- --port <port>`

```bash
npm run preview -- --port 8080
```

---

In case of any server configuring and creating build issues please refer to https://vitejs.dev/config/server-options.

### Deploying production build using Dockerfile

Build docker image with a tag of your choice:

```bash
docker build -t rag-ui .
```

Create and run a new container from an image:

```bash
docker run -dp 127.0.0.1:4173:4173 rag-ui
```

Now you should be able to access **Intel® AI for Enterprise RAG AudioQnA UI** from your browser via `127.0.0.1:4173`

### Image configuration

Frontend files are served by nginx web server which uses `default.conf` for configuration. Traffic is proxied to different pipelines which are independently configured. Some settings may lead to request errors that exceed configuration settings, such as `client_max_body_size` which by default allows files up to `64MB` to be uploaded into the dataprep pipeline. `proxy_*_timeout` may close the request prematurely if the timeout is exceeded, for example when big documents are ingested into the pipeline and processing takes time. Changing `default.conf` requires rebuilding and redeploying of the UI docker image for changes to apply.

### Configuring AudioQnA UI for deployment

Configuration values required to run and access **Intel® AI for Enterprise RAG AudioQnA UI** are set during the deployment process.

If you would like to setup custom domain, please change value for `FQDN` in your inventory `config.yaml` file.

To change disclaimer displayed under text input on the Chat page, please change chatDisclaimerText value in [UI configuration variables for deployment](../../../../deployment/roles/application/ui/defaults/main.yaml).

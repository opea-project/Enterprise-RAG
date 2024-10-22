# Enterprise RAG UI

## Requirements

- [Node.js](https://nodejs.org/) version v20.11.1 or higher
- [npm](https://www.npmjs.com/) version 10.2.4 or higher

To check if both were successfully installed run the following commands:

```bash
node --version
```

```bash
npm --version
```

`--version` option can be replaced with `-v` shorthand

## Setup

### Environment variables

Create `.env` file in this folder.
The Keycloak adapter for has to be configured by setting the following variables:

```
VITE_KEYCLOAK_URL=<keycloak-service-url>
VITE_KEYCLOAK_REALM=<realm-name>
VITE_KEYCLOAK_CLIENT_ID=<client-id>
VITE_ADMIN_RESOURCE_ROLE=<resource-role-name>
```

Additional variables for services must be set in `.env` file:

```
VITE_CHAT_QNA_URL=<chat-qna-service-url>
VITE_DATA_INGESTION_URL=<data-ingestion-service-url>
VITE_GRAFANA_DASHBOARD_URL=<grafana-dashboard-url>
VITE_APISIX_DASHBOARD_URL=<apisix-dashboard-url>
VITE_KEYCLOAK_ADMIN_PANEL_URL=<keycloak-admin-panel-url>
```

### Install dependencies

```bash
npm install
```

## Start UI Development Server

Run `npm run dev` command to start UI development server.
By default, it will run on `http://localhost:5147`.

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

## Deployment using Dockerfile

### Environment variables

Create `.env` file in this folder.
The Keycloak adapter for has to be configured by setting the following variables:

```
VITE_KEYCLOAK_URL=<keycloak-service-url>
VITE_KEYCLOAK_REALM=<realm-name>
VITE_KEYCLOAK_CLIENT_ID=<client-id>
VITE_ADMIN_RESOURCE_ROLE=<resource-role-name>
```

Additional variables for services must be set in `.env` file:

```
VITE_CHAT_QNA_URL=<chat-qna-service-url>
VITE_DATA_INGESTION_URL=<data-ingestion-service-url>
VITE_GRAFANA_DASHBOARD_URL=<grafana-dashboard-url>
VITE_APISIX_DASHBOARD_URL=<apisix-dashboard-url>
VITE_KEYCLOAK_ADMIN_PANEL_URL=<keycloak-admin-panel-url>
```

### Docker image

Build docker image with a tag of your choice:

```bash
docker build -t rag-ui .
```

Create and run a new container from an image:

```bash
docker run -dp 127.0.0.1:4173:4173 rag-ui
```

Now you should be able to access Enterprise RAG UI from your browser via `127.0.0.1:4173`

### Image configuration

Frontend files are served by nginx web server which uses `default.conf` for configuration. Traffic is proxied to different pipelines which are independently configured. Some settings may lead to request errors that exceed configuration settings, such as `client_max_body_size` which by default allows files up to `64MB` to be uploaded into the dataprep pipeline. `proxy_*_timeout` may close the request prematurely if the timeout is exceeded, for example when big documents are ingested into the pipeline and processing takes time. Changing `default.conf` requires rebuilding and redeploying of the UI docker image for changes to apply.

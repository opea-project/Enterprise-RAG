# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM node:20-alpine AS build

RUN apk add --no-cache bash

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /rag-ui

# Copy the workspace configuration and root package.json
COPY ./ui/package.json ./
COPY ./ui/pnpm-lock.yaml ./
COPY ./ui/pnpm-workspace.yaml ./
COPY ./ui/tsconfig.base.json ./

# Copy all packages and app
COPY ./ui/packages/ ./packages/
COPY ./ui/apps/audioqna/ ./apps/audioqna/

# Install dependencies for this app and its workspace dependencies only
RUN pnpm install --frozen-lockfile --filter @intel-enterprise-rag-ui/audioqna...

# Build the app and all its dependencies in correct order
RUN pnpm --filter @intel-enterprise-rag-ui/audioqna... build

FROM nginx:alpine

# Upgrade packages to fix possible vulnerabilities
USER root
RUN apk update && apk upgrade --no-cache libpng && \
    apk upgrade --no-cache && \
    rm -f /bin/dmesg \
          /usr/bin/nc \
          /bin/ping \
          /bin/base64 \
          /sbin/apk \
          /usr/bin/wget \
          /usr/bin/curl

COPY --from=build /rag-ui/apps/audioqna/dist /usr/share/nginx/html

EXPOSE 4173

USER nginx

CMD ["nginx", "-g", "daemon off;"]

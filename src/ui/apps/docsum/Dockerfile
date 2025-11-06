# Copyright (C) 2024-2025 Intel Corporation
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
COPY ./ui/tsconfig.json ./

# Copy the package.json files first
COPY ./ui/packages/icons/package.json ./packages/icons/
COPY ./ui/packages/utils/package.json ./packages/utils/
COPY ./ui/packages/input-validation/package.json ./packages/input-validation/
COPY ./ui/packages/components/package.json ./packages/components/
COPY ./ui/packages/auth/package.json ./packages/auth/
COPY ./ui/packages/control-plane/package.json ./packages/control-plane/
COPY ./ui/packages/markdown/package.json ./packages/markdown/
COPY ./ui/packages/layouts/package.json ./packages/layouts/
COPY ./ui/apps/docsum/package.json ./apps/docsum/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code for all packages used by the app and the app itself
COPY ./ui/packages/icons/ ./packages/icons/
COPY ./ui/packages/utils/ ./packages/utils/
COPY ./ui/packages/input-validation/ ./packages/input-validation/
COPY ./ui/packages/components/ ./packages/components/
COPY ./ui/packages/auth/ ./packages/auth/
COPY ./ui/packages/control-plane/ ./packages/control-plane/
COPY ./ui/packages/layouts/ ./packages/layouts/
COPY ./ui/packages/tailwind-theme/ ./packages/tailwind-theme/
COPY ./ui/packages/markdown/ ./packages/markdown/
COPY ./ui/apps/docsum/ ./apps/docsum/

# Build all packages used by the app
RUN pnpm --filter @intel-enterprise-rag-ui/icons build
RUN pnpm --filter @intel-enterprise-rag-ui/utils build
RUN pnpm --filter @intel-enterprise-rag-ui/input-validation build
RUN pnpm --filter @intel-enterprise-rag-ui/components build
RUN pnpm --filter @intel-enterprise-rag-ui/auth build
RUN pnpm --filter @intel-enterprise-rag-ui/control-plane build
RUN pnpm --filter @intel-enterprise-rag-ui/layouts build
RUN pnpm --filter @intel-enterprise-rag-ui/markdown build

# Then build the app
RUN pnpm --filter @intel-enterprise-rag-ui/docsum build

FROM nginx:alpine

# Upgrade packages to fix possible vulnerabilities
USER root
RUN apk update && apk upgrade --no-cache && \
    rm -f /bin/dmesg \
          /usr/bin/nc \
          /bin/ping \
          /bin/base64 \
          /sbin/apk \
          /usr/bin/wget \
          /usr/bin/curl

COPY --from=build /rag-ui/apps/docsum/dist /usr/share/nginx/html

EXPOSE 4173

USER nginx

CMD ["nginx", "-g", "daemon off;"]

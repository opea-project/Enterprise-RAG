# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM node:20-alpine AS build

RUN apk add --no-cache bash
WORKDIR /rag-ui
COPY ./ui /rag-ui
RUN npm install && npm run build

FROM nginx:alpine

COPY --from=build /rag-ui/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /rag-ui/dist /usr/share/nginx/html

EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]

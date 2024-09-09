FROM node:20-alpine AS build

WORKDIR /rag-ui
COPY . /rag-ui
RUN npm install && npm run build

FROM nginx:alpine

COPY --from=build /rag-ui/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /rag-ui/dist /usr/share/nginx/html

EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]

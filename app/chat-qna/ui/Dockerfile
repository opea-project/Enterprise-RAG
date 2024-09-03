FROM node:20-alpine as build

WORKDIR /ui
COPY ./ui .

RUN npm install
RUN npm run build

FROM nginx:alpine

COPY --from=build /ui/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /ui/dist /usr/share/nginx/html

EXPOSE 4173
CMD ["nginx", "-g", "daemon off;"]

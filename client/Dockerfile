# CostCourt web UI: the Vite build, served by nginx on port 80.
# nginx also proxies /api to the backend (see nginx.conf), so the browser
# talks to one origin, exactly like the Vite dev server.
#
#   docker build -t costcourt-client client

FROM node:22-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /src/dist /usr/share/nginx/html
# Where /api is proxied to; overridable at `docker run`.
ENV API_UPSTREAM=http://backend:8000
EXPOSE 80

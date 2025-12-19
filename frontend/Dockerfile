ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --frozen-lockfile

COPY . ./
RUN npm run build

FROM node:${NODE_VERSION}-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --frozen-lockfile

COPY . ./

CMD ["npm", "run", "dev"]

FROM nginx:alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY ./conf.d /etc/nginx/conf.d

CMD ["nginx", "-g", "daemon off;"]

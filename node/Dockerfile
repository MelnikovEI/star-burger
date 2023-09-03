# syntax=docker/dockerfile:1

FROM node:16-alpine
ENV NODE_ENV=production

WORKDIR /usr/app

COPY ["package.json", "package-lock.json*", "./"]

RUN npm install

COPY . .

RUN ./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

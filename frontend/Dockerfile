# Этап сборки фронтенда
FROM node:18 AS build

WORKDIR /app

# Копируем зависимости и ставим их
COPY package.json package-lock.json ./
RUN npm install

# Копируем фронт и собираем
COPY . .
RUN npm run build


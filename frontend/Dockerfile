# Этап сборки фронтенда
FROM node:18 AS build

WORKDIR /app

# Копируем package.json и package-lock.json и устанавливаем зависимости
COPY package.json package-lock.json ./
RUN npm install

# Копируем весь фронтенд и собираем
COPY . .
RUN npm run build
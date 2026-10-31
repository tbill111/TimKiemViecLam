# Frontend (React + Vite) → nginx. Build từ thư mục gốc repo.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Mặc định gọi API cùng origin qua nginx (/api). Bật chế độ demo không backend bằng --build-arg VITE_OFFLINE_DEMO=true
ARG VITE_API_URL=/api
ARG VITE_OFFLINE_DEMO=false
ENV VITE_API_URL=$VITE_API_URL VITE_OFFLINE_DEMO=$VITE_OFFLINE_DEMO
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

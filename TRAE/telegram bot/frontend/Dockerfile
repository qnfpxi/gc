# Stage 1: Build the React app
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json ./
COPY package-lock.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.23-alpine
# 复制构建好的静态文件到 Nginx 的 web 根目录
COPY --from=build /app/dist /usr/share/nginx/html
# 如果需要，可以复制一个自定义的 Nginx 配置
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
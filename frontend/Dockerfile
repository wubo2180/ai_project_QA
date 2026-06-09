# ===== 前端 Dockerfile (Vue3 + Vite，多阶段构建) =====

# ---- 构建阶段 ----
FROM node:20-alpine AS build

WORKDIR /app

# 先复制依赖清单以利用缓存
COPY package.json package-lock.json ./

RUN npm ci

# 复制源码并构建
COPY . .
RUN npm run build

# ---- 运行阶段（Nginx 托管静态文件）----
FROM nginx:alpine

# 自定义 nginx 配置（含 /api 反向代理与前端路由回退）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

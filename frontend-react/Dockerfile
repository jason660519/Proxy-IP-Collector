# 多階段構建React應用
FROM node:18-alpine as builder

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY package*.json ./

# 安裝依賴
RUN npm ci --only=production

# 複製源代碼
COPY . .

# 構建應用
RUN npm run build

# 生產階段 - 使用Nginx提供靜態文件
FROM nginx:alpine

# 複製構建文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製自定義Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# 啟動Nginx
CMD ["nginx", "-g", "daemon off;"]
# 多階段構建Python應用
FROM python:3.12-slim as builder

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安裝uv包管理器
RUN pip install uv

# 複製依賴文件
COPY pyproject.toml uv.lock ./

# 安裝Python依賴
RUN uv pip install --system --no-cache-dir -e .

# 生產階段
FROM python:3.12-slim

# 設置環境變量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    MONITORING_ENABLED=true \
    LOG_LEVEL=INFO

# 創建非root用戶
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /app

# 複製應用代碼
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# 創建日誌目錄
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# 切換到非root用戶
USER appuser

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/monitoring/health || exit 1

# 啟動命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
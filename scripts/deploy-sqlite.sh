#!/bin/bash

# 代理收集器 SQLite 部署腳本
set -e

echo "🚀 開始部署代理收集器 (SQLite版本)..."

# 檢查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安裝，請先安裝Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安裝，請先安裝Docker Compose"
    exit 1
fi

# 設置環境變量
export COMPOSE_PROJECT_NAME=proxy-collector-sqlite
export BACKEND_TAG=${BACKEND_TAG:-latest}
export FRONTEND_TAG=${FRONTEND_TAG:-latest}

# 創建必要的目錄
echo "📁 創建必要的目錄..."
mkdir -p backend/data backend/logs monitoring/grafana/provisioning/dashboards monitoring/grafana/provisioning/datasources nginx/ssl

# 創建Grafana配置文件
cat > monitoring/grafana/provisioning/datasources/datasource.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

# 創建Grafana儀表板配置文件
cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# 初始化SQLite數據庫
echo "📊 初始化SQLite數據庫..."
if [ ! -f "backend/data/proxy_collector.db" ]; then
    echo "創建新的SQLite數據庫..."
    touch backend/data/proxy_collector.db
else
    echo "使用現有的SQLite數據庫"
fi

# 構建和啟動服務
echo "🔨 構建和啟動服務..."
docker-compose -f docker-compose.sqlite.yml down --remove-orphans
docker-compose -f docker-compose.sqlite.yml build --no-cache
docker-compose -f docker-compose.sqlite.yml up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
services=("backend" "redis" "prometheus" "grafana" "nginx")

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.sqlite.yml ps | grep -q "$service.*Up"; then
        echo "✅ $service 服務運行正常"
    else
        echo "❌ $service 服務未正常運行"
        echo "查看日誌:"
        docker-compose -f docker-compose.sqlite.yml logs --tail=50 "$service"
        exit 1
    fi
done

# 健康檢查
echo "🏥 執行健康檢查..."
if curl -f http://localhost:80/nginx-health > /dev/null 2>&1; then
    echo "✅ Nginx健康檢查通過"
else
    echo "❌ Nginx健康檢查失敗"
    exit 1
fi

if curl -f http://localhost:8000/monitoring/health > /dev/null 2>&1; then
    echo "✅ 後端API健康檢查通過"
else
    echo "❌ 後端API健康檢查失敗"
    exit 1
fi

# 顯示訪問信息
echo ""
echo "🎉 SQLite版本部署成功！"
echo ""
echo "📊 訪問地址："
echo "  • 應用界面: http://localhost"
echo "  • API文檔: http://localhost/api/docs"
echo "  • 監控面板: http://localhost:3000 (admin/admin123)"
echo "  • Prometheus: http://localhost:9090"
echo ""
echo "💾 數據庫信息："
echo "  • 數據庫類型: SQLite"
echo "  • 數據庫文件: backend/data/proxy_collector.db"
echo "  • 數據持久化: ✓ (掛載卷)"
echo ""
echo "🔧 管理命令："
echo "  • 查看日誌: docker-compose -f docker-compose.sqlite.yml logs -f [service]"
echo "  • 重啟服務: docker-compose -f docker-compose.sqlite.yml restart [service]"
echo "  • 停止服務: docker-compose -f docker-compose.sqlite.yml down"
echo "  • 更新部署: ./scripts/deploy-sqlite.sh"
echo ""
echo "⚠️  安全提醒："
echo "  • 請及時修改默認密碼"
echo "  • 生產環境請配置SSL證書"
echo "  • 監控端口建議配置防火牆規則"

# 保存部署信息
cat > deployment_info_sqlite.txt << EOF
部署時間: $(date)
版本標籤: $BACKEND_TAG / $FRONTEND_TAG
數據庫類型: SQLite
訪問地址:
- 應用: http://localhost
- API: http://localhost/api/docs
- 監控: http://localhost:3000
- Prometheus: http://localhost:9090

管理命令:
docker-compose -f docker-compose.sqlite.yml logs -f backend  # 查看後端日誌
docker-compose -f docker-compose.sqlite.yml restart backend   # 重啟後端服務
docker-compose -f docker-compose.sqlite.yml down              # 停止所有服務

數據庫文件: backend/data/proxy_collector.db
EOF

echo "📋 部署信息已保存到 deployment_info_sqlite.txt"
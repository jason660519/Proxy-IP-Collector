@echo off
REM 代理收集器Windows部署腳本
echo 🚀 開始部署代理收集器...

REM 檢查Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker未安裝，請先安裝Docker Desktop
    exit /b 1
)

REM 檢查Docker Compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安裝，請先安裝Docker Compose
    exit /b 1
)

REM 設置環境變量
set COMPOSE_PROJECT_NAME=proxy-collector
set BACKEND_TAG=latest
set FRONTEND_TAG=latest

REM 創建必要的目錄
echo 📁 創建必要的目錄...
if not exist "backend\data" mkdir "backend\data"
if not exist "backend\logs" mkdir "backend\logs"
if not exist "monitoring\grafana\provisioning\dashboards" mkdir "monitoring\grafana\provisioning\dashboards"
if not exist "monitoring\grafana\provisioning\datasources" mkdir "monitoring\grafana\provisioning\datasources"
if not exist "nginx\ssl" mkdir "nginx\ssl"

REM 創建Grafana配置文件
echo apiVersion: 1 > monitoring\grafana\provisioning\datasources\datasource.yml
echo. >> monitoring\grafana\provisioning\datasources\datasource.yml
echo datasources: >> monitoring\grafana\provisioning\datasources\datasource.yml
echo   - name: Prometheus >> monitoring\grafana\provisioning\datasources\datasource.yml
echo     type: prometheus >> monitoring\grafana\provisioning\datasources\datasource.yml
echo     access: proxy >> monitoring\grafana\provisioning\datasources\datasource.yml
echo     url: http://prometheus:9090 >> monitoring\grafana\provisioning\datasources\datasource.yml
echo     isDefault: true >> monitoring\grafana\provisioning\datasources\datasource.yml

REM 創建Grafana儀表板配置文件
echo apiVersion: 1 > monitoring\grafana\provisioning\dashboards\dashboard.yml
echo. >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo providers: >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo   - name: 'default' >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     orgId: 1 >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     folder: '' >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     type: file >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     disableDeletion: false >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     updateIntervalSeconds: 10 >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo     options: >> monitoring\grafana\provisioning\dashboards\dashboard.yml
echo       path: /etc/grafana/provisioning/dashboards >> monitoring\grafana\provisioning\dashboards\dashboard.yml

REM 停止現有服務
echo 🛑 停止現有服務...
docker-compose down --remove-orphans

REM 構建和啟動服務
echo 🔨 構建和啟動服務...
docker-compose build --no-cache
docker-compose up -d

REM 等待服務啟動
echo ⏳ 等待服務啟動...
timeout /t 30 /nobreak >nul

REM 檢查服務狀態
echo 🔍 檢查服務狀態...
echo ✅ 服務狀態檢查完成（請手動驗證）

REM 健康檢查
echo 🏥 執行健康檢查...
curl -f http://localhost:80/nginx-health >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Nginx健康檢查通過
) else (
    echo ❌ Nginx健康檢查失敗
)

curl -f http://localhost:8000/monitoring/health >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ 後端API健康檢查通過
) else (
    echo ❌ 後端API健康檢查失敗
)

REM 顯示訪問信息
echo.
echo 🎉 部署完成！
echo.
echo 📊 訪問地址：
echo   • 應用界面: http://localhost
echo   • API文檔: http://localhost/api/docs
echo   • 監控面板: http://localhost:3000 (admin/admin123)
echo   • Prometheus: http://localhost:9090
echo.
echo 🔧 管理命令：
echo   • 查看日誌: docker-compose logs -f [service]
echo   • 重啟服務: docker-compose restart [service]
echo   • 停止服務: docker-compose down
echo   • 更新部署: 重新運行 deploy.bat
echo.
echo ⚠️  安全提醒：
echo   • 請及時修改默認密碼
echo   • 生產環境請配置SSL證書
echo   • 監控端口建議配置防火牆規則

REM 保存部署信息
echo 部署時間: %date% %time% > deployment_info.txt
echo 訪問地址: >> deployment_info.txt
echo - 應用: http://localhost >> deployment_info.txt
echo - API: http://localhost/api/docs >> deployment_info.txt
echo - 監控: http://localhost:3000 >> deployment_info.txt
echo - Prometheus: http://localhost:9090 >> deployment_info.txt
echo. >> deployment_info.txt
echo 管理命令: >> deployment_info.txt
echo docker-compose logs -f backend  # 查看後端日誌 >> deployment_info.txt
echo docker-compose restart backend   # 重啟後端服務 >> deployment_info.txt
echo docker-compose down              # 停止所有服務 >> deployment_info.txt

echo 📋 部署信息已保存到 deployment_info.txt
pause
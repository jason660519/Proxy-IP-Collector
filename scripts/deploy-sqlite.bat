@echo off
REM 代理收集器 SQLite 部署腳本 (Windows版本)
setlocal enabledelayedexpansion

echo 🚀 開始部署代理收集器 (SQLite版本)...

REM 檢查Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker未安裝，請先安裝Docker
    exit /b 1
)

REM 檢查Docker Compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安裝，請先安裝Docker Compose
    exit /b 1
)

REM 設置環境變量
set COMPOSE_PROJECT_NAME=proxy-collector-sqlite
if "%BACKEND_TAG%"=="" set BACKEND_TAG=latest
if "%FRONTEND_TAG%"=="" set FRONTEND_TAG=latest

REM 創建必要的目錄
echo 📁 創建必要的目錄...
if not exist "backend\data" mkdir backend\data
if not exist "backend\logs" mkdir backend\logs
if not exist "monitoring\grafana\provisioning\dashboards" mkdir monitoring\grafana\provisioning\dashboards
if not exist "monitoring\grafana\provisioning\datasources" mkdir monitoring\grafana\provisioning\datasources
if not exist "nginx\ssl" mkdir nginx\ssl

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

REM 初始化SQLite數據庫
echo 📊 初始化SQLite數據庫...
if not exist "backend\data\proxy_collector.db" (
    echo 創建新的SQLite數據庫...
    type nul > backend\data\proxy_collector.db
) else (
    echo 使用現有的SQLite數據庫
)

REM 構建和啟動服務
echo 🔨 構建和啟動服務...
docker-compose -f docker-compose.sqlite.yml down --remove-orphans
docker-compose -f docker-compose.sqlite.yml build --no-cache
docker-compose -f docker-compose.sqlite.yml up -d

REM 等待服務啟動
echo ⏳ 等待服務啟動...
timeout /t 30 /nobreak >nul

REM 檢查服務狀態
echo 🔍 檢查服務狀態...
set services=backend redis prometheus grafana nginx
set failed_services=

for %%s in (%services%) do (
    docker-compose -f docker-compose.sqlite.yml ps | findstr "%%s.*Up" >nul
    if !errorlevel! equ 0 (
        echo ✅ %%s 服務運行正常
    ) else (
        echo ❌ %%s 服務未正常運行
        set failed_services=!failed_services! %%s
    )
)

if not "%failed_services%"=="" (
    echo 查看失敗服務的日誌:
    for %%s in (%failed_services%) do (
        echo 服務 %%s 的日誌:
        docker-compose -f docker-compose.sqlite.yml logs --tail=50 %%s
    )
    exit /b 1
)

REM 健康檢查
echo 🏥 執行健康檢查...
curl -f http://localhost:80/nginx-health >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ Nginx健康檢查通過
) else (
    echo ❌ Nginx健康檢查失敗
    exit /b 1
)

curl -f http://localhost:8000/monitoring/health >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ 後端API健康檢查通過
) else (
    echo ❌ 後端API健康檢查失敗
    exit /b 1
)

REM 顯示訪問信息
echo.
echo 🎉 SQLite版本部署成功！
echo.
echo 📊 訪問地址：
echo   • 應用界面: http://localhost
echo   • API文檔: http://localhost/api/docs
echo   • 監控面板: http://localhost:3000 (admin/admin123)
echo   • Prometheus: http://localhost:9090
echo.
echo 💾 數據庫信息：
echo   • 數據庫類型: SQLite
echo   • 數據庫文件: backend\data\proxy_collector.db
echo   • 數據持久化: ✓ (掛載卷)
echo.
echo 🔧 管理命令：
echo   • 查看日誌: docker-compose -f docker-compose.sqlite.yml logs -f [service]
echo   • 重啟服務: docker-compose -f docker-compose.sqlite.yml restart [service]
echo   • 停止服務: docker-compose -f docker-compose.sqlite.yml down
echo   • 更新部署: scripts\deploy-sqlite.bat
echo.
echo ⚠️  安全提醒：
echo   • 請及時修改默認密碼
echo   • 生產環境請配置SSL證書
echo   • 監控端口建議配置防火牆規則

REM 保存部署信息
echo 部署時間: %date% %time% > deployment_info_sqlite.txt
echo 版本標籤: %BACKEND_TAG% / %FRONTEND_TAG% >> deployment_info_sqlite.txt
echo 數據庫類型: SQLite >> deployment_info_sqlite.txt
echo 訪問地址: >> deployment_info_sqlite.txt
echo - 應用: http://localhost >> deployment_info_sqlite.txt
echo - API: http://localhost/api/docs >> deployment_info_sqlite.txt
echo - 監控: http://localhost:3000 >> deployment_info_sqlite.txt
echo - Prometheus: http://localhost:9090 >> deployment_info_sqlite.txt
echo. >> deployment_info_sqlite.txt
echo 管理命令: >> deployment_info_sqlite.txt
echo docker-compose -f docker-compose.sqlite.yml logs -f backend  # 查看後端日誌 >> deployment_info_sqlite.txt
echo docker-compose -f docker-compose.sqlite.yml restart backend   # 重啟後端服務 >> deployment_info_sqlite.txt
echo docker-compose -f docker-compose.sqlite.yml down              # 停止所有服務 >> deployment_info_sqlite.txt
echo. >> deployment_info_sqlite.txt
echo 數據庫文件: backend\data\proxy_collector.db >> deployment_info_sqlite.txt

echo 📋 部署信息已保存到 deployment_info_sqlite.txt
endlocal
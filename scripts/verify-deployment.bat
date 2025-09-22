@echo off
setlocal enabledelayedexpansion

:: 代理收集器部署驗證腳本（Windows版本）
:: 用於驗證部署是否成功並提供詳細的系統狀態報告

:: 設置字符編碼
chcp 65001 >nul 2>&1

:: 顏色定義（使用ANSI轉義序列）
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

:: 配置變量
set "COMPOSE_FILE=%COMPOSE_FILE%"
if "%COMPOSE_FILE%"=="" set "COMPOSE_FILE=docker-compose.sqlite.yml"

set "BACKEND_URL=%BACKEND_URL%"
if "%BACKEND_URL%"=="" set "BACKEND_URL=http://localhost:8000"

set "GRAFANA_URL=%GRAFANA_URL%"
if "%GRAFANA_URL%"=="" set "GRAFANA_URL=http://localhost:3000"

set "PROMETHEUS_URL=%PROMETHEUS_URL%"
if "%PROMETHEUS_URL%"=="" set "PROMETHEUS_URL=http://localhost:9090"

set "TIMEOUT=30"

:: 日誌函數
:log_info
echo %BLUE%[INFO]%NC% %~1
exit /b

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
exit /b

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
exit /b

:log_error
echo %RED%[ERROR]%NC% %~1
exit /b

:: 檢查命令是否存在
:command_exists
where %~1 >nul 2>&1
exit /b %errorlevel%

:: 等待服務啟動
:wait_for_service
set "service_name=%~1"
set "url=%~2"
set "max_attempts=%~3"

call :log_info "等待 !service_name! 服務啟動..."

for /l %%i in (1,1,!max_attempts!) do (
    curl -s -f "!url!" >nul 2>&1
    if !errorlevel! equ 0 (
        call :log_success "!service_name! 服務已啟動"
        exit /b 0
    )
    
    if %%i equ !max_attempts! (
        call :log_error "!service_name! 服務啟動超時"
        exit /b 1
    )
    
    timeout /t 2 /nobreak >nul 2>&1
)
exit /b 1

:: 檢查Docker容器狀態
:check_containers
call :log_info "檢查Docker容器狀態..."

call :command_exists docker
if !errorlevel! neq 0 (
    call :log_error "Docker未安裝"
    exit /b 1
)

:: 獲取所有運行中的容器
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}" --filter "label=com.proxy-collector.service" > temp_containers.txt 2>nul

set /p containers=<temp_containers.txt
if "!containers!"=="" (
    call :log_warning "未找到運行中的代理收集器容器"
    del temp_containers.txt 2>nul
    exit /b 1
)

call :log_success "發現運行中的容器:"
type temp_containers.txt

:: 檢查每個容器的健康狀態
for /f "skip=1" %%c in ('docker ps --format "{{.Names}}" --filter "label=com.proxy-collector.service"') do (
    set "container=%%c"
    
    for /f "tokens=*" %%h in ('docker inspect --format="{{.State.Health.Status}}" "!container!" 2^>nul') do (
        set "health_status=%%h"
    )
    
    if "!health_status!"=="healthy" (
        call :log_success "容器 !container!: 健康"
    ) else if "!health_status!"=="unhealthy" (
        call :log_error "容器 !container!: 不健康"
    ) else if "!health_status!"=="starting" (
        call :log_warning "容器 !container!: 啟動中"
    ) else if "!health_status!"=="none" (
        call :log_info "容器 !container!: 無健康檢查"
    ) else (
        call :log_warning "容器 !container!: 未知狀態 (!health_status!)"
    )
)

del temp_containers.txt 2>nul
exit /b 0

:: 檢查後端API
:check_backend_api
call :log_info "檢查後端API..."

:: 等待後端服務啟動
call :wait_for_service "後端" "%BACKEND_URL%/health" 30
if !errorlevel! neq 0 exit /b 1

:: 測試健康檢查端點
curl -s -f "%BACKEND_URL%/health" > temp_health.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "健康檢查端點正常"
    set /p health_response=<temp_health.txt
    echo 響應: !health_response!
) else (
    call :log_error "健康檢查端點無響應"
    del temp_health.txt 2>nul
    exit /b 1
)

:: 測試指標端點
curl -s -f "%BACKEND_URL%/metrics" > temp_metrics.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "指標端點正常"
    
    :: 檢查關鍵指標
    findstr "http_requests_total" temp_metrics.txt >nul 2>&1
    if !errorlevel! equ 0 call :log_success "找到指標: http_requests_total"
    
    findstr "system_cpu_usage_percent" temp_metrics.txt >nul 2>&1
    if !errorlevel! equ 0 call :log_success "找到指標: system_cpu_usage_percent"
    
    findstr "proxy_count_total" temp_metrics.txt >nul 2>&1
    if !errorlevel! equ 0 call :log_success "找到指標: proxy_count_total"
) else (
    call :log_error "指標端點無響應"
    del temp_metrics.txt 2>nul
    exit /b 1
)

:: 測試代理API
curl -s -f "%BACKEND_URL%/api/v1/proxies?limit=5" > temp_proxies.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "代理API端點正常"
    
    :: 解析代理數量
    findstr "total_count" temp_proxies.txt > temp_proxy_count.txt
    for /f "tokens=2 delims=:" %%n in (temp_proxy_count.txt) do (
        set "proxy_count=%%n"
        set "proxy_count=!proxy_count:,=!"
        set "proxy_count=!proxy_count: =!"
    )
    call :log_info "當前代理數量: !proxy_count!"
) else (
    call :log_warning "代理API端點無響應或無代理數據"
)

:: 清理臨時文件
del temp_health.txt temp_metrics.txt temp_proxies.txt temp_proxy_count.txt 2>nul
exit /b 0

:: 檢查Prometheus
:check_prometheus
call :log_info "檢查Prometheus..."

call :wait_for_service "Prometheus" "%PROMETHEUS_URL%/-/healthy" 20
if !errorlevel! neq 0 exit /b 1

:: 檢查Prometheus配置
curl -s -f "%PROMETHEUS_URL%/api/v1/status/config" > temp_prometheus_config.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "Prometheus配置正常"
) else (
    call :log_error "Prometheus配置異常"
    del temp_prometheus_config.txt 2>nul
    exit /b 1
)

:: 檢查目標狀態
curl -s -f "%PROMETHEUS_URL%/api/v1/targets" > temp_targets.txt 2>nul
if !errorlevel! equ 0 (
    :: 統計活躍目標數量
    findstr "\"health\":\"up\"" temp_targets.txt > temp_active_targets.txt
    set /a active_targets=0
    for /f %%t in ('type temp_active_targets.txt ^| find /c /v ""') do set /a active_targets=%%t
    
    :: 統計總目標數量
    findstr "discoveredLabels" temp_targets.txt > temp_total_targets.txt
    set /a total_targets=0
    for /f %%t in ('type temp_total_targets.txt ^| find /c /v ""') do set /a total_targets=%%t
    
    call :log_success "Prometheus目標狀態: !active_targets!/!total_targets! 活躍"
    
    if !active_targets! equ !total_targets! if !total_targets! gtr 0 (
        call :log_success "所有目標都在線"
    ) else (
        call :log_warning "部分目標離線"
    )
)

:: 清理臨時文件
del temp_prometheus_config.txt temp_targets.txt temp_active_targets.txt temp_total_targets.txt 2>nul
exit /b 0

:: 檢查Grafana
:check_grafana
call :log_info "檢查Grafana..."

call :wait_for_service "Grafana" "%GRAFANA_URL%/api/health" 20
if !errorlevel! neq 0 exit /b 1

:: 檢查Grafana健康狀態
curl -s -f "%GRAFANA_URL%/api/health" > temp_grafana_health.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "Grafana健康檢查通過"
    set /p health_response=<temp_grafana_health.txt
    echo 響應: !health_response!
) else (
    call :log_error "Grafana健康檢查失敗"
    del temp_grafana_health.txt 2>nul
    exit /b 1
)

:: 檢查數據源
curl -s -f "%GRAFANA_URL%/api/datasources" > temp_datasources.txt 2>nul
if !errorlevel! equ 0 (
    findstr "\"name\":\"Prometheus\"" temp_datasources.txt >nul 2>&1
    if !errorlevel! equ 0 (
        call :log_success "Prometheus數據源已配置"
    ) else (
        call :log_warning "Prometheus數據源未找到"
    )
)

:: 清理臨時文件
del temp_grafana_health.txt temp_datasources.txt 2>nul
exit /b 0

:: 檢查數據庫連接
:check_database
call :log_info "檢查數據庫連接..."

:: 檢查SQLite文件（如果使用SQLite）
if exist "data\proxy_collector.db" (
    call :log_success "SQLite數據庫文件存在"
    
    :: 檢查文件大小
    for %%f in ("data\proxy_collector.db") do set "db_size=%%~zf"
    set /a db_size_kb=!db_size!/1024
    call :log_info "數據庫大小: !db_size_kb! KB"
) else (
    call :log_warning "SQLite數據庫文件不存在"
)

:: 測試數據庫連接（通過API）
curl -s -f "%BACKEND_URL%/api/v1/health/database" > temp_db_test.txt 2>nul
if !errorlevel! equ 0 (
    call :log_success "數據庫連接測試通過"
) else (
    call :log_warning "無法通過API測試數據庫連接"
)

del temp_db_test.txt 2>nul
exit /b 0

:: 生成部署報告
:generate_deployment_report
call :log_info "生成部署報告..."

set "report_file=deployment-report.txt"
set "timestamp=%date% %time%"

echo 代理收集器部署驗證報告 > "%report_file%"
echo 生成時間: !timestamp! >> "%report_file%"
echo ======================================== >> "%report_file%"
echo. >> "%report_file%"
echo 系統信息: >> "%report_file%"
echo - Docker版本: >> "%report_file%"
docker --version >> "%report_file%" 2>nul
echo - 操作系統: %OS% >> "%report_file%"
echo - 架構: %PROCESSOR_ARCHITECTURE% >> "%report_file%"
echo. >> "%report_file%"
echo 服務狀態: >> "%report_file%"
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}" --filter "label=com.proxy-collector.service" >> "%report_file%" 2>nul

:: 測試各個端點
echo. >> "%report_file%"
echo 端點狀態: >> "%report_file%"

:: 測試後端健康檢查
curl -s -f "%BACKEND_URL%/health" >nul 2>&1
if !errorlevel! equ 0 (
    echo - 後端健康檢查: 正常 >> "%report_file%"
) else (
    echo - 後端健康檢查: 異常 >> "%report_file%"
)

:: 測試Prometheus
curl -s -f "%PROMETHEUS_URL%/-/healthy" >nul 2>&1
if !errorlevel! equ 0 (
    echo - Prometheus: 正常 >> "%report_file%"
) else (
    echo - Prometheus: 異常 >> "%report_file%"
)

:: 測試Grafana
curl -s -f "%GRAFANA_URL%/api/health" >nul 2>&1
if !errorlevel! equ 0 (
    echo - Grafana: 正常 >> "%report_file%"
) else (
    echo - Grafana: 異常 >> "%report_file%"
)

echo. >> "%report_file%"
echo 訪問地址: >> "%report_file%"
echo - 後端API: %BACKEND_URL% >> "%report_file%"
echo - Grafana: %GRAFANA_URL% >> "%report_file%"
echo - Prometheus: %PROMETHEUS_URL% >> "%report_file%"

call :log_success "部署報告已生成: !report_file!"
exit /b 0

:: 主函數
:main
call :log_info "開始代理收集器部署驗證..."

set "exit_code=0"

:: 運行各項檢查
call :check_containers
if !errorlevel! neq 0 set "exit_code=1"

call :check_backend_api
if !errorlevel! neq 0 set "exit_code=1"

call :check_prometheus
if !errorlevel! neq 0 set "exit_code=1"

call :check_grafana
if !errorlevel! neq 0 set "exit_code=1"

call :check_database
if !errorlevel! neq 0 set "exit_code=1"

:: 生成報告
call :generate_deployment_report

if !exit_code! equ 0 (
    call :log_success "部署驗證完成！所有服務運行正常"
) else (
    call :log_error "部署驗證完成，但發現一些問題"
)

call :log_info "使用以下命令管理部署:"
echo   查看日誌: docker-compose -f %COMPOSE_FILE% logs -f [service]
echo   重啟服務: docker-compose -f %COMPOSE_FILE% restart [service]
echo   停止服務: docker-compose -f %COMPOSE_FILE% down
echo   訪問Grafana: %GRAFANA_URL% (admin/admin)
echo   訪問Prometheus: %PROMETHEUS_URL%

exit /b !exit_code!

:: 顯示幫助信息
:show_help
echo 代理收集器部署驗證腳本（Windows版本）
echo.
echo 用法: %~nx0 [選項]
echo.
echo 選項:
echo   -h, --help          顯示幫助信息
echo   -f, --file FILE     指定Docker Compose文件 (默認: docker-compose.sqlite.yml)
echo   --backend URL       指定後端URL (默認: http://localhost:8000)
echo   --grafana URL       指定Grafana URL (默認: http://localhost:3000)
echo   --prometheus URL    指定Prometheus URL (默認: http://localhost:9090)
echo.
echo 示例:
echo   %~nx0                                    :: 使用默認配置
echo   %~nx0 -f docker-compose.yml             :: 使用自定義Compose文件
echo   %~nx0 --backend http://192.168.1.100:8000 :: 測試遠程服務
echo.
exit /b 0

:: 解析命令行參數
:parse_args
if "%~1"=="" goto :main
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-f" (
    set "COMPOSE_FILE=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--file" (
    set "COMPOSE_FILE=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--backend" (
    set "BACKEND_URL=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--grafana" (
    set "GRAFANA_URL=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--prometheus" (
    set "PROMETHEUS_URL=%~2"
    shift
    shift
    goto :parse_args
)

call :log_error "未知選項: %~1"
call :show_help
exit /b 1

:: 運行主函數
:parse_args
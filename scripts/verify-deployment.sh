#!/bin/bash

# 代理收集器部署驗證腳本
# 用於驗證部署是否成功並提供詳細的系統狀態報告

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變量
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.sqlite.yml}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
TIMEOUT=30

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 等待服務啟動
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=$3
    
    log_info "等待 $service_name 服務啟動..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$service_name 服務已啟動"
            return 0
        fi
        
        if [ $i -eq $max_attempts ]; then
            log_error "$service_name 服務啟動超時"
            return 1
        fi
        
        sleep 2
    done
}

# 檢查Docker容器狀態
check_containers() {
    log_info "檢查Docker容器狀態..."
    
    if ! command_exists docker; then
        log_error "Docker未安裝"
        return 1
    fi
    
    # 獲取所有運行中的容器
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=com.proxy-collector.service")
    
    if [ -z "$running_containers" ]; then
        log_warning "未找到運行中的代理收集器容器"
        return 1
    fi
    
    log_success "發現運行中的容器:"
    echo "$running_containers"
    
    # 檢查每個容器的健康狀態
    local container_names=$(docker ps --format "{{.Names}}" --filter "label=com.proxy-collector.service")
    
    for container in $container_names; do
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        
        case "$health_status" in
            "healthy")
                log_success "容器 $container: 健康"
                ;;
            "unhealthy")
                log_error "容器 $container: 不健康"
                ;;
            "starting")
                log_warning "容器 $container: 啟動中"
                ;;
            "none")
                log_info "容器 $container: 無健康檢查"
                ;;
            *)
                log_warning "容器 $container: 未知狀態 ($health_status)"
                ;;
        esac
    done
    
    return 0
}

# 檢查後端API
check_backend_api() {
    log_info "檢查後端API..."
    
    # 等待後端服務啟動
    if ! wait_for_service "後端" "$BACKEND_URL/health" 30; then
        return 1
    fi
    
    # 測試健康檢查端點
    local health_response=$(curl -s -f "$BACKEND_URL/health" 2>/dev/null || echo "")
    
    if [ -n "$health_response" ]; then
        log_success "健康檢查端點正常"
        echo "響應: $health_response"
    else
        log_error "健康檢查端點無響應"
        return 1
    fi
    
    # 測試指標端點
    local metrics_response=$(curl -s -f "$BACKEND_URL/metrics" 2>/dev/null || echo "")
    
    if [ -n "$metrics_response" ]; then
        log_success "指標端點正常"
        
        # 檢查關鍵指標
        local key_metrics=("http_requests_total" "system_cpu_usage_percent" "proxy_count_total")
        
        for metric in "${key_metrics[@]}"; do
            if echo "$metrics_response" | grep -q "$metric"; then
                log_success "找到指標: $metric"
            else
                log_warning "未找到指標: $metric"
            fi
        done
    else
        log_error "指標端點無響應"
        return 1
    fi
    
    # 測試代理API
    local proxies_response=$(curl -s -f "$BACKEND_URL/api/v1/proxies?limit=5" 2>/dev/null || echo "")
    
    if [ -n "$proxies_response" ]; then
        log_success "代理API端點正常"
        
        # 解析代理數量
        local proxy_count=$(echo "$proxies_response" | grep -o '"total_count":[0-9]*' | cut -d':' -f2 || echo "0")
        log_info "當前代理數量: $proxy_count"
    else
        log_warning "代理API端點無響應或無代理數據"
    fi
    
    return 0
}

# 檢查Prometheus
check_prometheus() {
    log_info "檢查Prometheus..."
    
    if ! wait_for_service "Prometheus" "$PROMETHEUS_URL/-/healthy" 20; then
        return 1
    fi
    
    # 檢查Prometheus配置
    local config_status=$(curl -s -f "$PROMETHEUS_URL/api/v1/status/config" 2>/dev/null || echo "")
    
    if [ -n "$config_status" ]; then
        log_success "Prometheus配置正常"
    else
        log_error "Prometheus配置異常"
        return 1
    fi
    
    # 檢查目標狀態
    local targets_response=$(curl -s -f "$PROMETHEUS_URL/api/v1/targets" 2>/dev/null || echo "")
    
    if [ -n "$targets_response" ]; then
        local active_targets=$(echo "$targets_response" | grep -o '"activeTargets":\[.*\]' | grep -o '"health":"up"' | wc -l)
        local total_targets=$(echo "$targets_response" | grep -o '"activeTargets":\[.*\]' | grep -o '"discoveredLabels"' | wc -l)
        
        log_success "Prometheus目標狀態: $active_targets/$total_targets 活躍"
        
        if [ "$active_targets" -eq "$total_targets" ] && [ "$total_targets" -gt 0 ]; then
            log_success "所有目標都在線"
        else
            log_warning "部分目標離線"
        fi
    fi
    
    return 0
}

# 檢查Grafana
check_grafana() {
    log_info "檢查Grafana..."
    
    if ! wait_for_service "Grafana" "$GRAFANA_URL/api/health" 20; then
        return 1
    fi
    
    # 檢查Grafana健康狀態
    local health_response=$(curl -s -f "$GRAFANA_URL/api/health" 2>/dev/null || echo "")
    
    if [ -n "$health_response" ]; then
        log_success "Grafana健康檢查通過"
        echo "響應: $health_response"
    else
        log_error "Grafana健康檢查失敗"
        return 1
    fi
    
    # 檢查數據源
    local datasources_response=$(curl -s -f "$GRAFANA_URL/api/datasources" 2>/dev/null || echo "")
    
    if [ -n "$datasources_response" ]; then
        local prometheus_datasource=$(echo "$datasources_response" | grep -o '"name":"Prometheus"' | wc -l)
        
        if [ "$prometheus_datasource" -gt 0 ]; then
            log_success "Prometheus數據源已配置"
        else
            log_warning "Prometheus數據源未找到"
        fi
    fi
    
    return 0
}

# 檢查Redis
check_redis() {
    log_info "檢查Redis..."
    
    if ! command_exists redis-cli; then
        log_warning "redis-cli未安裝，跳過Redis檢查"
        return 0
    fi
    
    # 嘗試連接Redis
    local redis_response=$(redis-cli -h localhost -p 6379 ping 2>/dev/null || echo "")
    
    if [ "$redis_response" = "PONG" ]; then
        log_success "Redis連接正常"
        
        # 獲取Redis信息
        local redis_info=$(redis-cli -h localhost -p 6379 info server 2>/dev/null | grep -E "redis_version|tcp_port" || echo "")
        if [ -n "$redis_info" ]; then
            echo "Redis信息:"
            echo "$redis_info"
        fi
    else
        log_error "Redis連接失敗"
        return 1
    fi
    
    return 0
}

# 檢查數據庫連接
check_database() {
    log_info "檢查數據庫連接..."
    
    # 檢查SQLite文件（如果使用SQLite）
    if [ -f "data/proxy_collector.db" ]; then
        log_success "SQLite數據庫文件存在"
        
        # 檢查文件大小
        local db_size=$(du -h "data/proxy_collector.db" | cut -f1)
        log_info "數據庫大小: $db_size"
    else
        log_warning "SQLite數據庫文件不存在"
    fi
    
    # 測試數據庫連接（通過API）
    local db_test_response=$(curl -s -f "$BACKEND_URL/api/v1/health/database" 2>/dev/null || echo "")
    
    if [ -n "$db_test_response" ]; then
        log_success "數據庫連接測試通過"
    else
        log_warning "無法通過API測試數據庫連接"
    fi
    
    return 0
}

# 生成部署報告
generate_deployment_report() {
    log_info "生成部署報告..."
    
    local report_file="deployment-report.txt"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$report_file" << EOF
代理收集器部署驗證報告
生成時間: $timestamp
========================================

系統信息:
- Docker版本: $(docker --version 2>/dev/null || echo "未安裝")
- Docker Compose版本: $(docker-compose --version 2>/dev/null || echo "未安裝")
- 操作系統: $(uname -s)
- 架構: $(uname -m)

服務狀態:
EOF

    # 獲取容器狀態
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=com.proxy-collector.service" >> "$report_file"
    
    echo "" >> "$report_file"
    echo "端點狀態:" >> "$report_file"
    
    # 測試各個端點
    local endpoints=(
        "後端健康檢查:$BACKEND_URL/health"
        "後端指標:$BACKEND_URL/metrics"
        "Prometheus:$PROMETHEUS_URL/-/healthy"
        "Grafana:$GRAFANA_URL/api/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local name=$(echo "$endpoint" | cut -d':' -f1)
        local url=$(echo "$endpoint" | cut -d':' -f2-)
        
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "- $name: ✅ 正常" >> "$report_file"
        else
            echo "- $name: ❌ 異常" >> "$report_file"
        fi
    done
    
    echo "" >> "$report_file"
    echo "訪問地址:" >> "$report_file"
    echo "- 後端API: $BACKEND_URL" >> "$report_file"
    echo "- Grafana: $GRAFANA_URL" >> "$report_file"
    echo "- Prometheus: $PROMETHEUS_URL" >> "$report_file"
    
    log_success "部署報告已生成: $report_file"
}

# 主函數
main() {
    log_info "開始代理收集器部署驗證..."
    
    local exit_code=0
    
    # 運行各項檢查
    check_containers || exit_code=1
    check_backend_api || exit_code=1
    check_prometheus || exit_code=1
    check_grafana || exit_code=1
    check_redis || exit_code=1
    check_database || exit_code=1
    
    # 生成報告
    generate_deployment_report
    
    if [ $exit_code -eq 0 ]; then
        log_success "部署驗證完成！所有服務運行正常"
    else
        log_error "部署驗證完成，但發現一些問題"
    fi
    
    log_info "使用以下命令管理部署:"
    echo "  查看日誌: docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "  重啟服務: docker-compose -f $COMPOSE_FILE restart [service]"
    echo "  停止服務: docker-compose -f $COMPOSE_FILE down"
    echo "  訪問Grafana: $GRAFANA_URL (admin/admin)"
    echo "  訪問Prometheus: $PROMETHEUS_URL"
    
    exit $exit_code
}

# 顯示幫助信息
show_help() {
    cat << EOF
代理收集器部署驗證腳本

用法: $0 [選項]

選項:
  -h, --help          顯示幫助信息
  -f, --file FILE     指定Docker Compose文件 (默認: docker-compose.sqlite.yml)
  --backend URL       指定後端URL (默認: http://localhost:8000)
  --grafana URL       指定Grafana URL (默認: http://localhost:3000)
  --prometheus URL    指定Prometheus URL (默認: http://localhost:9090)

示例:
  $0                                    # 使用默認配置
  $0 -f docker-compose.yml             # 使用自定義Compose文件
  $0 --backend http://192.168.1.100:8000 # 測試遠程服務

EOF
}

# 解析命令行參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --backend)
            BACKEND_URL="$2"
            shift 2
            ;;
        --grafana)
            GRAFANA_URL="$2"
            shift 2
            ;;
        --prometheus)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        *)
            log_error "未知選項: $1"
            show_help
            exit 1
            ;;
    esac
done

# 運行主函數
main
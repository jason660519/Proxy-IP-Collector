#!/bin/bash
# 持續整合測試腳本 (Linux/Mac)
# 自動化測試流程，包括環境設置、測試執行和結果報告

set -e  # 遇到錯誤時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 項目路徑
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
TEST_RESULTS_DIR="$PROJECT_ROOT/test_results"
COVERAGE_DIR="$TEST_RESULTS_DIR/coverage"
REPORTS_DIR="$TEST_RESULTS_DIR/reports"

# 測試配置
MIN_COVERAGE=80
TEST_TIMEOUT=300

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

# 創建必要的目錄
create_directories() {
    log_info "創建測試結果目錄..."
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$COVERAGE_DIR"
    mkdir -p "$REPORTS_DIR"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查依賴..."
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安裝"
        exit 1
    fi
    
    # 檢查 pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安裝"
        exit 1
    fi
    
    # 檢查虛擬環境
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_warning "未激活虛擬環境，建議使用虛擬環境運行測試"
    fi
    
    log_success "依賴檢查完成"
}

# 安裝測試依賴
install_test_dependencies() {
    log_info "安裝測試依賴..."
    
    cd "$BACKEND_DIR"
    
    # 安裝測試相關的包
    pip3 install -q pytest pytest-cov pytest-asyncio pytest-timeout \
                 flake8 black mypy pylint coverage
    
    log_success "測試依賴安裝完成"
}

# 代碼質量檢查
run_code_quality_checks() {
    log_info "開始代碼質量檢查..."
    
    cd "$BACKEND_DIR"
    
    local quality_passed=true
    
    # Flake8 檢查
    log_info "運行 flake8 檢查..."
    if python3 -m flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503; then
        log_success "flake8 檢查通過"
    else
        log_error "flake8 檢查失敗"
        quality_passed=false
    fi
    
    # Black 格式化檢查
    log_info "運行 black 格式化檢查..."
    if python3 -m black --check app/ tests/; then
        log_success "black 格式化檢查通過"
    else
        log_error "black 格式化檢查失敗"
        quality_passed=false
    fi
    
    # MyPy 類型檢查
    log_info "運行 mypy 類型檢查..."
    if python3 -m mypy app/ --ignore-missing-imports --no-strict-optional; then
        log_success "mypy 類型檢查通過"
    else
        log_warning "mypy 類型檢查發現問題（非致命）"
    fi
    
    if $quality_passed; then
        log_success "代碼質量檢查通過"
        return 0
    else
        log_error "代碼質量檢查失敗"
        return 1
    fi
}

# 運行單元測試
run_unit_tests() {
    log_info "開始運行單元測試..."
    
    cd "$BACKEND_DIR"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local junit_xml="$REPORTS_DIR/unit_tests_${timestamp}.xml"
    local coverage_xml="$COVERAGE_DIR/unit_coverage_${timestamp}.xml"
    
    if python3 -m pytest tests/unit/ \
        -v \
        --tb=short \
        --strict-markers \
        --junitxml="$junit_xml" \
        --cov=app \
        --cov-report=xml:"$coverage_xml" \
        --cov-report=html:"$COVERAGE_DIR/unit" \
        --cov-report=term-missing \
        --cov-fail-under=$MIN_COVERAGE \
        --asyncio-mode=auto \
        --timeout=$TEST_TIMEOUT; then
        
        log_success "單元測試通過"
        return 0
    else
        log_error "單元測試失敗"
        return 1
    fi
}

# 運行集成測試
run_integration_tests() {
    log_info "開始運行集成測試..."
    
    cd "$BACKEND_DIR"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local junit_xml="$REPORTS_DIR/integration_tests_${timestamp}.xml"
    
    if python3 -m pytest tests/integration/ \
        -v \
        --tb=short \
        --strict-markers \
        --junitxml="$junit_xml" \
        --asyncio-mode=auto \
        --timeout=$TEST_TIMEOUT; then
        
        log_success "集成測試通過"
        return 0
    else
        log_error "集成測試失敗"
        return 1
    fi
}

# 生成測試報告
generate_test_report() {
    log_info "生成測試報告..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$REPORTS_DIR/test_report_${timestamp}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "summary": {
        "test_environment": "$(uname -a)",
        "python_version": "$(python3 --version)",
        "test_results_dir": "$TEST_RESULTS_DIR"
    },
    "test_configuration": {
        "min_coverage": $MIN_COVERAGE,
        "test_timeout": $TEST_TIMEOUT
    }
}
EOF
    
    log_success "測試報告生成完成: $report_file"
}

# 顯示測試摘要
show_test_summary() {
    log_info "測試摘要:"
    echo "========================================"
    echo "測試結果目錄: $TEST_RESULTS_DIR"
    echo "覆蓋率報告: $COVERAGE_DIR"
    echo "測試報告: $REPORTS_DIR"
    echo "========================================"
}

# 主函數
main() {
    log_info "開始持續整合測試流程..."
    
    local exit_code=0
    
    # 創建目錄
    create_directories
    
    # 檢查依賴
    check_dependencies
    
    # 安裝測試依賴
    install_test_dependencies
    
    # 運行各項測試
    if ! run_code_quality_checks; then
        exit_code=1
    fi
    
    if ! run_unit_tests; then
        exit_code=1
    fi
    
    if ! run_integration_tests; then
        exit_code=1
    fi
    
    # 生成報告
    generate_test_report
    
    # 顯示摘要
    show_test_summary
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "所有測試通過！"
    else
        log_error "部分測試失敗！"
    fi
    
    log_info "持續整合測試流程完成"
    
    return $exit_code
}

# 腳本入口
main "$@"
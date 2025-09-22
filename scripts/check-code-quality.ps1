# Code Quality Check Script for My Proxy Collector
# 本地代碼品質檢查腳本 - 比 GitHub Actions 快很多！

param(
    [switch]$SkipBackend,    # 跳過後端檢查
    [switch]$SkipFrontend,   # 跳過前端檢查
    [switch]$SkipTests,      # 跳過測試
    [switch]$FixFormat,      # 自動修復格式問題
    [switch]$Verbose         # 詳細輸出
)

# 顏色輸出函數
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Info { Write-ColorOutput Cyan $args }

# 檢查當前目錄
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$projectRoot\.venv")) {
    Write-Error "❌ Virtual environment not found. Please run: python -m venv .venv"
    exit 1
}

Write-Info "🚀 開始代碼品質檢查..."
Write-Info "📁 項目根目錄: $projectRoot"

$errors = 0
$warnings = 0

# 激活虛擬環境
Write-Info "🔧 激活虛擬環境..."
& "$projectRoot\.venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ 無法激活虛擬環境"
    exit 1
}

# 後端代碼品質檢查
if (-not $SkipBackend) {
    Write-Info "🐍 開始後端代碼品質檢查..."
    
    # 檢查 backend/app 目錄是否存在
    if (-not (Test-Path "$projectRoot\backend\app")) {
        Write-Warning "⚠️ backend\app 目錄不存在，跳過後端檢查"
    } else {
        # 1. Black 格式檢查
        Write-Info "🎨 檢查代碼格式 (black)..."
        if ($FixFormat) {
            & black "$projectRoot\backend\app"
        } else {
            & black --check "$projectRoot\backend\app"
        }
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ Black 格式檢查失敗"
        } else {
            Write-Success "✅ Black 格式檢查通過"
        }
        
        # 2. isort import 排序
        Write-Info "📦 檢查 import 排序 (isort)..."
        if ($FixFormat) {
            & isort "$projectRoot\backend\app"
        } else {
            & isort --check-only "$projectRoot\backend\app"
        }
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ isort 檢查失敗"
        } else {
            Write-Success "✅ isort 檢查通過"
        }
        
        # 3. MyPy 類型檢查
        Write-Info "🔍 類型檢查 (mypy)..."
        & mypy "$projectRoot\backend\app"
        if ($LASTEXITCODE -ne 0) { 
            $warnings++
            Write-Warning "⚠️ MyPy 類型檢查有警告"
        } else {
            Write-Success "✅ MyPy 類型檢查通過"
        }
        
        # 4. Flake8 語法檢查
        Write-Info "🔎 語法檢查 (flake8)..."
        & flake8 "$projectRoot\backend\app"
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ Flake8 語法檢查失敗"
        } else {
            Write-Success "✅ Flake8 語法檢查通過"
        }
    }
}

# 前端代碼品質檢查
if (-not $SkipFrontend) {
    Write-Info "⚛️ 開始前端代碼品質檢查..."
    
    # 檢查 frontend-react 目錄是否存在
    if (-not (Test-Path "$projectRoot\frontend-react")) {
        Write-Warning "⚠️ frontend-react 目錄不存在，跳過前端檢查"
    } else {
        Push-Location "$projectRoot\frontend-react"
        
        # 1. TypeScript 類型檢查
        Write-Info "🔍 TypeScript 類型檢查..."
        & npx tsc --noEmit
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ TypeScript 類型檢查失敗"
        } else {
            Write-Success "✅ TypeScript 類型檢查通過"
        }
        
        # 2. ESLint 檢查
        Write-Info "🔎 ESLint 語法檢查..."
        if ($FixFormat) {
            & npm run lint -- --fix
        } else {
            & npm run lint
        }
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ ESLint 檢查失敗"
        } else {
            Write-Success "✅ ESLint 檢查通過"
        }
        
        # 3. Prettier 格式檢查 (如果存在)
        if (Test-Path "package.json") {
            $packageJson = Get-Content "package.json" | ConvertFrom-Json
            if ($packageJson.scripts.format) {
                Write-Info "🎨 Prettier 格式檢查..."
                if ($FixFormat) {
                    & npm run format
                } else {
                    & npm run format -- --check
                }
                if ($LASTEXITCODE -ne 0) { 
                    $warnings++
                    Write-Warning "⚠️ Prettier 格式檢查有警告"
                } else {
                    Write-Success "✅ Prettier 格式檢查通過"
                }
            }
        }
        
        Pop-Location
    }
}

# 運行測試
if (-not $SkipTests) {
    Write-Info "🧪 運行測試..."
    
    # 後端測試
    if (-not $SkipBackend -and (Test-Path "$projectRoot\backend\tests")) {
        Write-Info "🐍 運行後端測試..."
        Push-Location "$projectRoot\backend"
        & python -m pytest tests\ --tb=short
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ 後端測試失敗"
        } else {
            Write-Success "✅ 後端測試通過"
        }
        Pop-Location
    }
    
    # 前端測試
    if (-not $SkipFrontend -and (Test-Path "$projectRoot\frontend-react")) {
        Write-Info "⚛️ 運行前端測試..."
        Push-Location "$projectRoot\frontend-react"
        & npm test -- --watchAll=false --passWithNoTests
        if ($LASTEXITCODE -ne 0) { 
            $errors++
            Write-Error "❌ 前端測試失敗"
        } else {
            Write-Success "✅ 前端測試通過"
        }
        Pop-Location
    }
}

# 總結報告
Write-Info "📊 檢查完成！"
Write-Info "=" * 50

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Success "🎉 所有檢查都通過！可以安全地進行 Git Push"
} elseif ($errors -eq 0 -and $warnings -gt 0) {
    Write-Warning "⚠️ 有 $warnings 個警告，建議修復後再 Push"
    Write-Warning "💡 使用 -FixFormat 參數可以自動修復部分問題"
} else {
    Write-Error "❌ 有 $errors 個錯誤和 $warnings 個警告"
    Write-Error "🚫 請修復所有錯誤後再進行 Git Push"
    Write-Info "💡 使用 -FixFormat 參數可以自動修復部分問題"
    exit 1
}

Write-Info ""
Write-Info "📖 使用說明:"
Write-Info "  .\scripts\check-code-quality.ps1           # 完整檢查"
Write-Info "  .\scripts\check-code-quality.ps1 -FixFormat # 自動修復格式"
Write-Info "  .\scripts\check-code-quality.ps1 -SkipTests # 跳過測試"
Write-Info "  .\scripts\check-code-quality.ps1 -SkipBackend # 只檢查前端"
Write-Info "  .\scripts\check-code-quality.ps1 -SkipFrontend # 只檢查後端"
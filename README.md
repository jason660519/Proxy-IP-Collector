# Proxy IP Pool Collector

## 🎯 專案概述

代理 IP 池收集器是一個高效、穩定、可擴展的代理 IP 收集和管理系統，從多個公開的代理 IP 網站持續抓取免費代理 IP，進行驗證後存入儲存池，為上游的爬蟲業務提供匿名的網路請求能力。

## 🏗️ 專案架構

```
Proxy IP Pool Collector/
├── 📁 backend/              # 後端服務 (FastAPI + Python)
│   ├── app/                 # 應用核心模組
│   │   ├── api/            # API路由和端點
│   │   ├── core/           # 核心配置和工具
│   │   ├── etl/            # ETL數據處理
│   │   ├── models/         # 數據模型
│   │   ├── schemas/        # Pydantic模式
│   │   └── services/       # 業務邏輯服務
│   ├── config/             # 配置文件
│   └── tests/              # 測試文件
├── 📁 frontend-react/       # 前端應用 (React + TypeScript)
│   ├── src/
│   │   ├── components/     # React組件
│   │   ├── pages/          # 頁面組件
│   │   ├── services/       # API服務
│   │   ├── store/          # Redux狀態管理
│   │   └── types/          # TypeScript類型
│   └── dist/               # 構建產物
└── 📁 Docs/                 # 文檔中心
    ├── 01-專案規劃/        # 專案規劃文檔
    ├── 02-架構設計/        # 架構設計文檔
    ├── 03-開發文件/        # 開發指南
    ├── 04-工作報告/        # 工作報告
    └── 05-配置說明/        # 配置說明
```

## 🚀 快速開始

### 環境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **UV**: Python 包管理器
- **npm**: Node.js 包管理器

### 後端啟動

```bash
# 進入後端目錄
cd backend

# 創建虛擬環境
uv venv

# 安裝依賴
uv pip install -r requirements.txt

# 啟動開發服務器
uv run uvicorn react_server:app --host 0.0.0.0 --port 8000 --reload
```

### 前端啟動

```bash
# 進入前端目錄
cd frontend-react

# 安裝依賴
npm install

# 啟動開發服務器
npm run dev
```

### 訪問應用

- **前端應用**: http://localhost:3000
- **後端 API**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs

## 📋 核心功能

### 🕷️ 爬取模組 (Fetchers)

- 支持 8 個專業代理網站爬取
- 異步並發爬取，提高效率
- 智能速率限制，避免封禁
- 模塊化設計，易於擴展

### ✅ 驗證模組 (Validator)

- 異步代理 IP 驗證
- 多目標 URL 測試
- 響應時間和成功率統計
- 自動重試和錯誤處理

### 💾 存儲模組 (Storage)

- PostgreSQL 主數據庫
- Redis 緩存和隊列
- 數據模型和關係設計
- 數據一致性保障

### 📊 監控界面

- 實時代理狀態監控
- 爬取任務管理
- 數據統計和可視化
- 系統性能監控

## 🔧 技術棧

### 後端技術

- **框架**: FastAPI 0.104+
- **數據庫**: PostgreSQL + SQLAlchemy
- **緩存**: Redis
- **HTTP 客戶端**: aiohttp
- **網頁爬取**: BeautifulSoup4 + Playwright
- **異步處理**: asyncio + Celery
- **數據驗證**: Pydantic

### 前端技術

- **框架**: React 18 + TypeScript
- **UI 組件**: Ant Design 5.0
- **狀態管理**: Redux Toolkit + RTK Query
- **圖表**: Apache ECharts + Recharts
- **構建工具**: Vite 4.0
- **路由**: React Router DOM

## 📚 文檔

詳細文檔請查看 `Docs/` 資料夾：

- **專案規劃**: 需求文檔、商業模式
- **架構設計**: 系統架構、技術選型
- **開發文件**: 開發指南、API 文檔
- **工作報告**: 開發進度、總結報告

## 🧪 測試

```bash
# 後端測試
cd backend
uv run pytest

# 前端測試
cd frontend-react
npm test
```

## 📈 性能指標

- **爬取效率**: 支持並發爬取，每秒可處理 100+請求
- **驗證速度**: 異步驗證，支持 1000+代理同時測試
- **響應時間**: API 響應時間 < 100ms
- **可用性**: 系統可用性 > 99.9%

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 許可證

本專案採用 MIT 許可證 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 📞 聯繫方式

- **專案維護者**: DevOps Team
- **問題反饋**: 請在 Issues 中提交
- **文檔更新**: 請查看 Docs/ 資料夾

---

_最後更新：2024-01-20_

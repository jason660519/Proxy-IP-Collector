/**
 * 代理IP池管理系統 - 主要JavaScript文件
 * 功能：頁面初始化、導航管理、側邊欄控制、通知系統、載入狀態等
 */

class ProxyManager {
    constructor() {
        this.currentPage = 'dashboard';
        this.sidebarCollapsed = false;
        this.notifications = [];
        this.init();
    }

    /**
     * 初始化應用程序
     */
    init() {
        this.initNavigation();
        this.initSidebar();
        this.initSearch();
        this.initNotifications();
        this.initFAB();
        this.initLoading();
        this.initResponsive();
        this.initTheme();
        this.loadPageContent('dashboard');
        
        // 顯示歡迎通知
        this.showNotification('系統初始化完成', 'success');
    }

    /**
     * 初始化導航功能
     */
    initNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.getAttribute('data-page');
                
                // 更新活動狀態
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // 載入對應頁面
                this.loadPageContent(page);
                
                // 關閉移動端菜單
                this.closeMobileMenu();
            });
        });

        // 移動端菜單切換
        const mobileToggle = document.querySelector('.mobile-menu-toggle');
        if (mobileToggle) {
            mobileToggle.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }
    }

    /**
     * 初始化側邊欄功能
     */
    initSidebar() {
        const toggleBtn = document.querySelector('.sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');
        
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // 過濾器事件
        const filterInputs = document.querySelectorAll('.filter-item input, .filter-select');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.applyFilters();
            });
        });
    }

    /**
     * 初始化搜尋功能
     */
    initSearch() {
        const searchInput = document.querySelector('.search-box input');
        const searchIcon = document.querySelector('.search-box i');
        
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 300);
            });
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    clearTimeout(searchTimeout);
                    this.performSearch(e.target.value);
                }
            });
        }

        if (searchIcon) {
            searchIcon.addEventListener('click', () => {
                const searchValue = searchInput.value;
                this.performSearch(searchValue);
            });
        }
    }

    /**
     * 初始化通知系統
     */
    initNotifications() {
        const bellIcon = document.querySelector('.notification-bell');
        
        if (bellIcon) {
            bellIcon.addEventListener('click', () => {
                this.showNotificationPanel();
            });
        }

        // 模擬定期通知
        setInterval(() => {
            if (Math.random() < 0.1) { // 10% 概率
                const notifications = [
                    '新的代理IP已添加到池子中',
                    '代理IP連接測試完成',
                    '系統性能優化完成',
                    '發現異常代理IP，已自動移除'
                ];
                const randomNotification = notifications[Math.floor(Math.random() * notifications.length)];
                this.showNotification(randomNotification, 'info');
            }
        }, 30000); // 每30秒檢查一次
    }

    /**
     * 初始化懸浮操作按鈕
     */
    initFAB() {
        const fabMain = document.querySelector('.fab-main');
        const fabMenu = document.querySelector('.fab-menu');
        
        if (fabMain && fabMenu) {
            fabMain.addEventListener('click', () => {
                this.toggleFABMenu();
            });

            // FAB菜單項點擊事件
            const fabItems = document.querySelectorAll('.fab-item');
            fabItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    const action = e.currentTarget.getAttribute('data-action');
                    this.handleFABAction(action);
                });
            });
        }
    }

    /**
     * 初始化載入狀態
     */
    initLoading() {
        this.loadingOverlay = document.querySelector('.loading-overlay');
        
        // 監聽AJAX請求以顯示/隱藏載入狀態
        this.setupAjaxInterceptors();
    }

    /**
     * 初始化響應式設計
     */
    initResponsive() {
        // 監聽窗口大小變化
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // 初始檢查
        this.handleResize();
    }

    /**
     * 切換側邊欄
     */
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const sidebarCollapsed = document.querySelector('.sidebar.collapsed');
        
        if (sidebar) {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
            
            // 保存狀態到本地存儲
            localStorage.setItem('sidebarCollapsed', this.sidebarCollapsed);
        }
    }

    /**
     * 載入頁面內容
     */
    async loadPageContent(page) {
        this.showLoading();
        this.currentPage = page;
        
        try {
            // 模擬API請求延遲
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const content = this.generatePageContent(page);
            this.updateMainContent(content);
            
            // 更新頁面標題
            this.updatePageTitle(page);
            
            // 初始化頁面特定事件
            this.initializePageEvents(page);
            
        } catch (error) {
            console.error('載入頁面失敗:', error);
            this.showNotification('頁面載入失敗', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 生成頁面內容
     */
    generatePageContent(page) {
        const pages = {
            dashboard: this.generateDashboardContent(),
            proxies: this.generateProxiesContent(),
            monitoring: this.generateMonitoringContent(),
            settings: this.generateSettingsContent()
        };
        
        return pages[page] || this.generateDashboardContent();
    }

    /**
     * 生成儀表板內容
     */
    generateDashboardContent() {
        return `
            <div class="dashboard-grid">
                <div class="stats-card">
                    <div class="stats-card-header">
                        <div class="stats-card-title">總代理數</div>
                        <div class="stats-card-icon primary">
                            <i class="fas fa-server"></i>
                        </div>
                    </div>
                    <div class="stats-card-value" id="totalProxiesValue">1,234</div>
                    <div class="stats-card-subtitle">
                        <span class="stats-card-change positive" id="totalProxiesChange">+12%</span>
                        相比昨日
                    </div>
                </div>
                
                <div class="stats-card">
                    <div class="stats-card-header">
                        <div class="stats-card-title">在線代理</div>
                        <div class="stats-card-icon success">
                            <i class="fas fa-check-circle"></i>
                        </div>
                    </div>
                    <div class="stats-card-value" id="onlineProxiesValue">987</div>
                    <div class="stats-card-subtitle">
                        <span class="stats-card-change positive" id="onlineProxiesChange">+5%</span>
                        正常運行
                    </div>
                </div>
                
                <div class="stats-card">
                    <div class="stats-card-header">
                        <div class="stats-card-title">成功率</div>
                        <div class="stats-card-icon warning">
                            <i class="fas fa-chart-line"></i>
                        </div>
                    </div>
                    <div class="stats-card-value" id="successRateValue">87.3%</div>
                    <div class="stats-card-subtitle">
                        <span class="stats-card-change negative" id="successRateChange">-2%</span>
                        平均成功率
                    </div>
                </div>
                
                <div class="stats-card">
                    <div class="stats-card-header">
                        <div class="stats-card-title">響應時間</div>
                        <div class="stats-card-icon danger">
                            <i class="fas fa-clock"></i>
                        </div>
                    </div>
                    <div class="stats-card-value" id="responseTimeValue">1.2s</div>
                    <div class="stats-card-subtitle">
                        <span class="stats-card-change positive" id="responseTimeChange">-15%</span>
                        平均響應
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <h3 class="chart-title">代理狀態趨勢</h3>
                        <div class="chart-actions">
                            <button class="chart-action-btn active" data-period="24h">24小時</button>
                            <button class="chart-action-btn" data-period="7d">7天</button>
                            <button class="chart-action-btn" data-period="30d">30天</button>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="statusChart"></canvas>
                    </div>
                </div>
                
                <div class="data-table">
                    <div class="table-header">
                        <h3 class="table-title">最近活動</h3>
                        <div class="table-actions">
                            <button class="btn btn-sm btn-secondary" id="viewAllActivity">查看全部</button>
                        </div>
                    </div>
                    <div class="table-content">
                        <table class="table" id="recentActivityTable">
                            <thead>
                                <tr>
                                    <th>代理IP</th>
                                    <th>端口</th>
                                    <th>狀態</th>
                                    <th>匿名度</th>
                                    <th>響應時間</th>
                                    <th>最後檢查</th>
                                </tr>
                            </thead>
                            <tbody id="recentActivityBody">
                                <tr>
                                    <td>192.168.1.100</td>
                                    <td>8080</td>
                                    <td><span class="status-badge online">在線</span></td>
                                    <td><span class="anonymity-badge high">高匿</span></td>
                                    <td>0.8s</td>
                                    <td>2分鐘前</td>
                                </tr>
                                <tr>
                                    <td>10.0.0.50</td>
                                    <td>3128</td>
                                    <td><span class="status-badge testing">檢測中</span></td>
                                    <td><span class="anonymity-badge medium">匿名</span></td>
                                    <td>-</td>
                                    <td>剛剛</td>
                                </tr>
                                <tr>
                                    <td>172.16.0.25</td>
                                    <td>8080</td>
                                    <td><span class="status-badge offline">離線</span></td>
                                    <td><span class="anonymity-badge low">透明</span></td>
                                    <td>-</td>
                                    <td>1小時前</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 生成代理管理內容
     */
    generateProxiesContent() {
        return `
            <div class="proxies-container">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">代理IP列表</h3>
                        <div class="card-actions">
                            <button class="btn btn-primary" id="addProxyBtn">
                                <i class="fas fa-plus"></i> 添加代理
                            </button>
                            <button class="btn btn-secondary" id="exportProxiesBtn">
                                <i class="fas fa-download"></i> 導出
                            </button>
                            <button class="btn btn-info" id="batchTestBtn">
                                <i class="fas fa-play"></i> 批量測試
                            </button>
                        </div>
                    </div>
                    
                    <div class="filters-section">
                        <div class="filter-group">
                            <label>狀態篩選</label>
                            <select class="form-control" id="statusFilter">
                                <option value="">全部</option>
                                <option value="online">在線</option>
                                <option value="offline">離線</option>
                                <option value="testing">檢測中</option>
                                <option value="error">異常</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>匿名度</label>
                            <select class="form-control" id="anonymityFilter">
                                <option value="">全部</option>
                                <option value="high">高匿</option>
                                <option value="medium">匿名</option>
                                <option value="low">透明</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>位置</label>
                            <select class="form-control" id="locationFilter">
                                <option value="">全部</option>
                                <option value="cn">中國</option>
                                <option value="us">美國</option>
                                <option value="jp">日本</option>
                                <option value="hk">香港</option>
                                <option value="sg">新加坡</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>搜索</label>
                            <input type="text" class="form-control" id="searchInput" placeholder="搜索代理IP...">
                        </div>
                        <div class="filter-group">
                            <label>&nbsp;</label>
                            <button class="btn btn-outline-secondary" id="clearFiltersBtn">清除篩選</button>
                        </div>
                    </div>
                    
                    <div class="stats-overview">
                        <div class="stat-card">
                            <div class="stat-card-title">總代理數</div>
                            <div class="stat-card-value" id="totalProxiesCount">1,247</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-card-title">在線代理</div>
                            <div class="stat-card-value text-success" id="onlineProxiesCount">892</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-card-title">離線代理</div>
                            <div class="stat-card-value text-danger" id="offlineProxiesCount">355</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-card-title">成功率</div>
                            <div class="stat-card-value text-warning" id="successRateValue">71.5%</div>
                        </div>
                    </div>
                    
                    <div class="table-container">
                        <div class="table-header">
                            <h3 class="table-title">代理列表</h3>
                            <div class="table-actions">
                                <button class="btn btn-sm btn-outline-primary" id="selectAllBtn">全選</button>
                                <button class="btn btn-sm btn-outline-danger" id="batchDeleteBtn">批量刪除</button>
                            </div>
                        </div>
                        <table class="table" id="proxiesTable">
                            <thead>
                                <tr>
                                    <th><input type="checkbox" id="selectAllCheckbox"></th>
                                    <th>IP地址</th>
                                    <th>端口</th>
                                    <th>狀態</th>
                                    <th>匿名度</th>
                                    <th>延遲</th>
                                    <th>位置</th>
                                    <th>最後檢查</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="proxiesTableBody">
                                <tr data-id="1">
                                    <td><input type="checkbox" class="proxy-checkbox"></td>
                                    <td>192.168.1.100</td>
                                    <td>8080</td>
                                    <td><span class="status-badge online">在線</span></td>
                                    <td><span class="anonymity-badge high">高匿</span></td>
                                    <td>125ms</td>
                                    <td>香港</td>
                                    <td>2分鐘前</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-sm btn-primary" onclick="proxyManager.testProxy(1)" title="測試">
                                                <i class="fas fa-play"></i>
                                            </button>
                                            <button class="btn btn-sm btn-info" onclick="proxyManager.editProxy(1)" title="編輯">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-sm btn-danger" onclick="proxyManager.deleteProxy(1)" title="刪除">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                <tr data-id="2">
                                    <td><input type="checkbox" class="proxy-checkbox"></td>
                                    <td>203.0.113.45</td>
                                    <td>3128</td>
                                    <td><span class="status-badge testing">檢測中</span></td>
                                    <td><span class="anonymity-badge medium">匿名</span></td>
                                    <td>-</td>
                                    <td>美國</td>
                                    <td>1分鐘前</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-sm btn-primary" onclick="proxyManager.testProxy(2)" title="測試">
                                                <i class="fas fa-play"></i>
                                            </button>
                                            <button class="btn btn-sm btn-info" onclick="proxyManager.editProxy(2)" title="編輯">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-sm btn-danger" onclick="proxyManager.deleteProxy(2)" title="刪除">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                <tr data-id="3">
                                    <td><input type="checkbox" class="proxy-checkbox"></td>
                                    <td>198.51.100.25</td>
                                    <td>8080</td>
                                    <td><span class="status-badge offline">離線</span></td>
                                    <td><span class="anonymity-badge low">透明</span></td>
                                    <td>-</td>
                                    <td>德國</td>
                                    <td>5分鐘前</td>
                                    <td>
                                        <div class="action-buttons">
                                            <button class="btn btn-sm btn-primary" onclick="proxyManager.testProxy(3)" title="測試">
                                                <i class="fas fa-play"></i>
                                            </button>
                                            <button class="btn btn-sm btn-info" onclick="proxyManager.editProxy(3)" title="編輯">
                                                <i class="fas fa-edit"></i>
                                            </button>
                                            <button class="btn btn-sm btn-danger" onclick="proxyManager.deleteProxy(3)" title="刪除">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="pagination">
                        <button class="pagination-item disabled" id="prevPageBtn">上一頁</button>
                        <span class="page-info">第 <span id="currentPage">1</span> 頁，共 <span id="totalPages">15</span> 頁</span>
                        <button class="pagination-item" id="nextPageBtn">下一頁</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 生成監控內容
     */
    generateMonitoringContent() {
        return `
            <div class="monitoring-container">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">即時監控</h3>
                        <div class="monitoring-controls">
                            <button class="btn btn-primary btn-sm" onclick="proxyManager.startMonitoring()">
                                <i class="fas fa-play"></i> 開始監控
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="proxyManager.stopMonitoring()">
                                <i class="fas fa-stop"></i> 停止監控
                            </button>
                        </div>
                    </div>
                    <div class="monitoring-dashboard">
                        <div class="metric-cards">
                            <div class="metric-card">
                                <div class="metric-title">當前連接數</div>
                                <div class="metric-value">847</div>
                                <div class="metric-change positive">+12%</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">平均響應時間</div>
                                <div class="metric-value">156ms</div>
                                <div class="metric-change negative">+8ms</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">成功率</div>
                                <div class="metric-value">94.2%</div>
                                <div class="metric-change positive">+2.1%</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-title">帶寬使用</div>
                                <div class="metric-value">2.4GB/s</div>
                                <div class="metric-change positive">+15%</div>
                            </div>
                        </div>
                        
                        <div class="chart-section">
                            <div class="chart-container">
                                <h4>連接數趨勢</h4>
                                <canvas id="connectionChart" width="600" height="300"></canvas>
                            </div>
                            <div class="chart-container">
                                <h4>響應時間分布</h4>
                                <canvas id="responseTimeChart" width="600" height="300"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 生成設置內容
     */
    generateSettingsContent() {
        return `
            <div class="settings-container">
                <div class="page-header">
                    <h1 class="page-title">系統設置</h1>
                    <p class="page-subtitle">配置代理池系統的各項參數</p>
                </div>
                
                <div class="settings-tabs">
                    <div class="tab-nav">
                        <button class="tab-btn active" data-tab="general">基本設置</button>
                        <button class="tab-btn" data-tab="proxy">代理設置</button>
                        <button class="tab-btn" data-tab="notification">通知設置</button>
                        <button class="tab-btn" data-tab="data">數據管理</button>
                        <button class="tab-btn" data-tab="security">安全設置</button>
                    </div>
                    
                    <div class="tab-content">
                        <!-- 基本設置 -->
                        <div class="tab-pane active" id="general">
                            <div class="settings-grid">
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>系統偏好</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>系統語言</label>
                                            <select class="form-control" id="systemLanguage">
                                                <option value="zh-TW">繁體中文</option>
                                                <option value="zh-CN">簡體中文</option>
                                                <option value="en">English</option>
                                                <option value="ja">日本語</option>
                                            </select>
                                        </div>
                                        <div class="form-group">
                                            <label>時區設置</label>
                                            <select class="form-control" id="systemTimezone">
                                                <option value="Asia/Taipei">台北時間 (UTC+8)</option>
                                                <option value="Asia/Shanghai">上海時間 (UTC+8)</option>
                                                <option value="America/New_York">紐約時間 (UTC-5)</option>
                                                <option value="Europe/London">倫敦時間 (UTC+0)</option>
                                                <option value="Asia/Tokyo">東京時間 (UTC+9)</option>
                                            </select>
                                        </div>
                                        <div class="form-group">
                                            <label>日期格式</label>
                                            <select class="form-control" id="dateFormat">
                                                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                                                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                                                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>界面設置</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>主題模式</label>
                                            <div class="radio-group">
                                                <label class="radio-label">
                                                    <input type="radio" name="themeMode" value="light" checked> 亮色主題
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="themeMode" value="dark"> 暗色主題
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="themeMode" value="auto"> 自動切換
                                                </label>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="compactMode"> 緊湊模式
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="animationsEnabled" checked> 啟用動畫效果
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label>每頁顯示數量</label>
                                            <input type="number" class="form-control" id="itemsPerPage" value="20" min="5" max="100">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 代理設置 -->
                        <div class="tab-pane" id="proxy">
                            <div class="settings-grid">
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>測試設置</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>測試超時時間 (秒)</label>
                                            <input type="number" class="form-control" id="testTimeout" value="30" min="5" max="300">
                                        </div>
                                        <div class="form-group">
                                            <label>重試次數</label>
                                            <input type="number" class="form-control" id="retryCount" value="3" min="1" max="10">
                                        </div>
                                        <div class="form-group">
                                            <label>測試URL</label>
                                            <input type="text" class="form-control" id="testUrl" value="https://httpbin.org/ip">
                                        </div>
                                        <div class="form-group">
                                            <label>最大並發測試數</label>
                                            <input type="number" class="form-control" id="maxConcurrentTests" value="50" min="1" max="200">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>收集設置</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>自動收集間隔 (分鐘)</label>
                                            <input type="number" class="form-control" id="collectionInterval" value="60" min="5" max="1440">
                                        </div>
                                        <div class="form-group">
                                            <label>最大收集數量</label>
                                            <input type="number" class="form-control" id="maxCollectionCount" value="1000" min="100" max="10000">
                                        </div>
                                        <div class="form-group">
                                            <label>來源網站</label>
                                            <div class="checkbox-group">
                                                <label class="checkbox-label">
                                                    <input type="checkbox" checked> FreeProxyList
                                                </label>
                                                <label class="checkbox-label">
                                                    <input type="checkbox" checked> ProxyScrape
                                                </label>
                                                <label class="checkbox-label">
                                                    <input type="checkbox"> Geonode
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 通知設置 -->
                        <div class="tab-pane" id="notification">
                            <div class="settings-grid">
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>桌面通知</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="enableDesktopNotifications" checked> 啟用桌面通知
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="notifyOnProxyOffline" checked> 代理離線時通知
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="notifyOnTestComplete"> 測試完成時通知
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="notifyOnCollectionComplete"> 收集完成時通知
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>郵件通知</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="enableEmailNotifications"> 啟用郵件通知
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label>SMTP服務器</label>
                                            <input type="text" class="form-control" id="smtpServer" placeholder="smtp.gmail.com">
                                        </div>
                                        <div class="form-group">
                                            <label>SMTP端口</label>
                                            <input type="number" class="form-control" id="smtpPort" value="587">
                                        </div>
                                        <div class="form-group">
                                            <label>發件人郵箱</label>
                                            <input type="email" class="form-control" id="senderEmail" placeholder="your-email@example.com">
                                        </div>
                                        <div class="form-group">
                                            <label>收件人郵箱</label>
                                            <input type="email" class="form-control" id="recipientEmail" placeholder="recipient@example.com">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 數據管理 -->
                        <div class="tab-pane" id="data">
                            <div class="settings-grid">
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>數據保留</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>測試記錄保留時間 (天)</label>
                                            <input type="number" class="form-control" id="testRecordRetention" value="30" min="1" max="365">
                                        </div>
                                        <div class="form-group">
                                            <label>日誌文件保留時間 (天)</label>
                                            <input type="number" class="form-control" id="logRetention" value="7" min="1" max="90">
                                        </div>
                                        <div class="form-group">
                                            <label>自動清理</label>
                                            <div class="radio-group">
                                                <label class="radio-label">
                                                    <input type="radio" name="autoCleanup" value="daily"> 每天
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoCleanup" value="weekly" checked> 每週
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoCleanup" value="monthly"> 每月
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoCleanup" value="never"> 從不
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>備份與恢復</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label>自動備份</label>
                                            <div class="radio-group">
                                                <label class="radio-label">
                                                    <input type="radio" name="autoBackup" value="daily"> 每天
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoBackup" value="weekly" checked> 每週
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoBackup" value="monthly"> 每月
                                                </label>
                                                <label class="radio-label">
                                                    <input type="radio" name="autoBackup" value="never"> 從不
                                                </label>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label>備份路徑</label>
                                            <input type="text" class="form-control" id="backupPath" value="./backups/">
                                        </div>
                                        <div class="form-group">
                                            <button class="btn btn-warning" id="backupNowBtn">立即備份</button>
                                            <button class="btn btn-info" id="restoreBackupBtn">恢復備份</button>
                                        </div>
                                        <div class="form-group">
                                            <button class="btn btn-danger" id="cleanupDataBtn">清理數據</button>
                                            <button class="btn btn-outline-danger" id="resetSettingsBtn">重置設置</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 安全設置 -->
                        <div class="tab-pane" id="security">
                            <div class="settings-grid">
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>訪問控制</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="enableAuthentication"> 啟用身份驗證
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label>管理員密碼</label>
                                            <input type="password" class="form-control" id="adminPassword" placeholder="留空保持不變">
                                        </div>
                                        <div class="form-group">
                                            <label>會話超時時間 (分鐘)</label>
                                            <input type="number" class="form-control" id="sessionTimeout" value="30" min="5" max="1440">
                                        </div>
                                        <div class="form-group">
                                            <label>允許的IP地址</label>
                                            <textarea class="form-control" id="allowedIPs" placeholder="每行一個IP地址，留空允許所有"></textarea>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="settings-card">
                                    <div class="settings-card-header">
                                        <h3>API設置</h3>
                                    </div>
                                    <div class="settings-card-body">
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="enableAPI" checked> 啟用API接口
                                            </label>
                                        </div>
                                        <div class="form-group">
                                            <label>API密鑰</label>
                                            <div class="input-group">
                                                <input type="text" class="form-control" id="apiKey" value="your-api-key-here" readonly>
                                                <button class="btn btn-outline-secondary" onclick="generateNewAPIKey()">重新生成</button>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label>API速率限制 (請求/分鐘)</label>
                                            <input type="number" class="form-control" id="apiRateLimit" value="100" min="10" max="1000">
                                        </div>
                                        <div class="form-group">
                                            <label class="checkbox-label">
                                                <input type="checkbox" id="enableAPICORS"> 啟用CORS
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="settings-actions">
                    <button class="btn btn-primary" id="saveSettingsBtn">保存設置</button>
                    <button class="btn btn-secondary" id="resetSettingsBtn">重置為默認</button>
                    <button class="btn btn-outline-secondary" id="importSettingsBtn">導入設置</button>
                    <button class="btn btn-outline-primary" id="exportSettingsBtn">導出設置</button>
                </div>
            </div>
        `;
    }}]}

    /**
     * 更新主內容區域
     */
    updateMainContent(content) {
        const contentArea = document.querySelector('.content');
        if (contentArea) {
            contentArea.innerHTML = content;
            
            // 重新初始化新內容中的交互元素
            this.reinitializeContent();
        }
    }

    /**
     * 更新頁面標題
     */
    updatePageTitle(page) {
        const titles = {
            dashboard: '儀表板',
            proxies: '代理管理',
            monitoring: '即時監控',
            settings: '系統設置'
        };
        
        const pageTitle = document.querySelector('.page-title h1');
        if (pageTitle) {
            pageTitle.textContent = titles[page] || '儀表板';
        }
    }

    /**
     * 重新初始化內容中的交互元素
     */
    reinitializeContent() {
        // 重新綁定按鈕事件
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            if (!button.onclick) {
                button.addEventListener('click', (e) => {
                    // 處理通用按鈕點擊
                    this.handleButtonClick(e.target);
                });
            }
        });

        // 初始化圖表
        this.initCharts();
    }

    /**
     * 初始化頁面特定事件
     */
    initializePageEvents(page) {
        switch(page) {
            case 'dashboard':
                this.initializeDashboardEvents();
                break;
            case 'proxies':
                this.initializeProxiesEvents();
                break;
            case 'settings':
                this.initializeSettingsEvents();
                break;
        }
    }

    /**
     * 初始化儀表板事件
     */
    initializeDashboardEvents() {
        // 綁定儀表板特定按鈕事件
        const viewAllBtn = document.getElementById('viewAllActivity');
        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', () => {
                this.loadPageContent('proxies');
            });
        }
    }

    /**
     * 初始化代理管理事件
     */
    initializeProxiesEvents() {
        // 綁定代理管理特定按鈕事件
        const addProxyBtn = document.querySelector('.btn-primary[onclick*="addProxy"]');
        if (addProxyBtn) {
            addProxyBtn.addEventListener('click', () => this.addProxy());
        }
    }

    /**
     * 初始化設置事件
     */
    initializeSettingsEvents() {
        // 標籤頁切換
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchSettingsTab(tabName);
            });
        });

        // 保存設置
        const saveBtn = document.getElementById('saveSettingsBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveSettings();
            });
        }

        // 重置設置
        const resetBtn = document.getElementById('resetSettingsBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetSettings();
            });
        }

        // 導入設置
        const importBtn = document.getElementById('importSettingsBtn');
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                this.importSettings();
            });
        }

        // 導出設置
        const exportBtn = document.getElementById('exportSettingsBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportSettings();
            });
        }

        // 立即備份
        const backupBtn = document.getElementById('backupNowBtn');
        if (backupBtn) {
            backupBtn.addEventListener('click', () => {
                this.backupNow();
            });
        }

        // 恢復備份
        const restoreBtn = document.getElementById('restoreBackupBtn');
        if (restoreBtn) {
            restoreBtn.addEventListener('click', () => {
                this.restoreBackup();
            });
        }

        // 清理數據
        const cleanupBtn = document.getElementById('cleanupDataBtn');
        if (cleanupBtn) {
            cleanupBtn.addEventListener('click', () => {
                this.cleanupData();
            });
        }

        // 重置設置
        const resetAllBtn = document.getElementById('resetSettingsBtn');
        if (resetAllBtn) {
            resetAllBtn.addEventListener('click', () => {
                this.resetAllSettings();
            });
        }

        // 重新生成API密鑰
        const regenerateApiKeyBtn = document.querySelector('[onclick="generateNewAPIKey()"]');
        if (regenerateApiKeyBtn) {
            regenerateApiKeyBtn.addEventListener('click', () => {
                this.generateNewAPIKey();
            });
        }

        // 初始化表單值
        this.loadSettingsValues();
    }

    /**
     * 切換設置標籤頁
     */
    switchSettingsTab(tabName) {
        // 更新按鈕狀態
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新內容顯示
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');
    }

    /**
     * 加載設置值
     */
    loadSettingsValues() {
        // 從localStorage加載保存的設置
        const savedSettings = localStorage.getItem('proxyPoolSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            
            // 基本設置
            if (settings.systemLanguage) document.getElementById('systemLanguage').value = settings.systemLanguage;
            if (settings.systemTimezone) document.getElementById('systemTimezone').value = settings.systemTimezone;
            if (settings.dateFormat) document.getElementById('dateFormat').value = settings.dateFormat;
            
            // 界面設置
            if (settings.themeMode) {
                document.querySelector(`input[name="themeMode"][value="${settings.themeMode}"]`).checked = true;
            }
            if (settings.compactMode) document.getElementById('compactMode').checked = settings.compactMode;
            if (settings.animationsEnabled) document.getElementById('animationsEnabled').checked = settings.animationsEnabled;
            if (settings.itemsPerPage) document.getElementById('itemsPerPage').value = settings.itemsPerPage;
            
            // 代理設置
            if (settings.testTimeout) document.getElementById('testTimeout').value = settings.testTimeout;
            if (settings.retryCount) document.getElementById('retryCount').value = settings.retryCount;
            if (settings.testUrl) document.getElementById('testUrl').value = settings.testUrl;
            if (settings.maxConcurrentTests) document.getElementById('maxConcurrentTests').value = settings.maxConcurrentTests;
            if (settings.collectionInterval) document.getElementById('collectionInterval').value = settings.collectionInterval;
            if (settings.maxCollectionCount) document.getElementById('maxCollectionCount').value = settings.maxCollectionCount;
            
            // 通知設置
            if (settings.enableDesktopNotifications) document.getElementById('enableDesktopNotifications').checked = settings.enableDesktopNotifications;
            if (settings.notifyOnProxyOffline) document.getElementById('notifyOnProxyOffline').checked = settings.notifyOnProxyOffline;
            if (settings.notifyOnTestComplete) document.getElementById('notifyOnTestComplete').checked = settings.notifyOnTestComplete;
            if (settings.notifyOnCollectionComplete) document.getElementById('notifyOnCollectionComplete').checked = settings.notifyOnCollectionComplete;
            if (settings.enableEmailNotifications) document.getElementById('enableEmailNotifications').checked = settings.enableEmailNotifications;
            if (settings.smtpServer) document.getElementById('smtpServer').value = settings.smtpServer;
            if (settings.smtpPort) document.getElementById('smtpPort').value = settings.smtpPort;
            if (settings.senderEmail) document.getElementById('senderEmail').value = settings.senderEmail;
            if (settings.recipientEmail) document.getElementById('recipientEmail').value = settings.recipientEmail;
            
            // 數據管理
            if (settings.testRecordRetention) document.getElementById('testRecordRetention').value = settings.testRecordRetention;
            if (settings.logRetention) document.getElementById('logRetention').value = settings.logRetention;
            if (settings.autoCleanup) {
                document.querySelector(`input[name="autoCleanup"][value="${settings.autoCleanup}"]`).checked = true;
            }
            if (settings.autoBackup) {
                document.querySelector(`input[name="autoBackup"][value="${settings.autoBackup}"]`).checked = true;
            }
            if (settings.backupPath) document.getElementById('backupPath').value = settings.backupPath;
            
            // 安全設置
            if (settings.enableAuthentication) document.getElementById('enableAuthentication').checked = settings.enableAuthentication;
            if (settings.sessionTimeout) document.getElementById('sessionTimeout').value = settings.sessionTimeout;
            if (settings.allowedIPs) document.getElementById('allowedIPs').value = settings.allowedIPs;
            if (settings.enableAPI) document.getElementById('enableAPI').checked = settings.enableAPI;
            if (settings.apiKey) document.getElementById('apiKey').value = settings.apiKey;
            if (settings.apiRateLimit) document.getElementById('apiRateLimit').value = settings.apiRateLimit;
            if (settings.enableAPICORS) document.getElementById('enableAPICORS').checked = settings.enableAPICORS;
        }
    }

    /**
     * 保存設置
     */
    saveSettings() {
        const settings = {
            // 基本設置
            systemLanguage: document.getElementById('systemLanguage').value,
            systemTimezone: document.getElementById('systemTimezone').value,
            dateFormat: document.getElementById('dateFormat').value,
            
            // 界面設置
            themeMode: document.querySelector('input[name="themeMode"]:checked').value,
            compactMode: document.getElementById('compactMode').checked,
            animationsEnabled: document.getElementById('animationsEnabled').checked,
            itemsPerPage: parseInt(document.getElementById('itemsPerPage').value),
            
            // 代理設置
            testTimeout: parseInt(document.getElementById('testTimeout').value),
            retryCount: parseInt(document.getElementById('retryCount').value),
            testUrl: document.getElementById('testUrl').value,
            maxConcurrentTests: parseInt(document.getElementById('maxConcurrentTests').value),
            collectionInterval: parseInt(document.getElementById('collectionInterval').value),
            maxCollectionCount: parseInt(document.getElementById('maxCollectionCount').value),
            
            // 通知設置
            enableDesktopNotifications: document.getElementById('enableDesktopNotifications').checked,
            notifyOnProxyOffline: document.getElementById('notifyOnProxyOffline').checked,
            notifyOnTestComplete: document.getElementById('notifyOnTestComplete').checked,
            notifyOnCollectionComplete: document.getElementById('notifyOnCollectionComplete').checked,
            enableEmailNotifications: document.getElementById('enableEmailNotifications').checked,
            smtpServer: document.getElementById('smtpServer').value,
            smtpPort: parseInt(document.getElementById('smtpPort').value),
            senderEmail: document.getElementById('senderEmail').value,
            recipientEmail: document.getElementById('recipientEmail').value,
            
            // 數據管理
            testRecordRetention: parseInt(document.getElementById('testRecordRetention').value),
            logRetention: parseInt(document.getElementById('logRetention').value),
            autoCleanup: document.querySelector('input[name="autoCleanup"]:checked').value,
            autoBackup: document.querySelector('input[name="autoBackup"]:checked').value,
            backupPath: document.getElementById('backupPath').value,
            
            // 安全設置
            enableAuthentication: document.getElementById('enableAuthentication').checked,
            sessionTimeout: parseInt(document.getElementById('sessionTimeout').value),
            allowedIPs: document.getElementById('allowedIPs').value,
            enableAPI: document.getElementById('enableAPI').checked,
            apiKey: document.getElementById('apiKey').value,
            apiRateLimit: parseInt(document.getElementById('apiRateLimit').value),
            enableAPICORS: document.getElementById('enableAPICORS').checked,
            
            // 時間戳
            lastSaved: new Date().toISOString()
        };
        
        // 保存到localStorage
        localStorage.setItem('proxyPoolSettings', JSON.stringify(settings));
        
        // 應用設置
        this.applySettings(settings);
        
        this.showNotification('設置已保存', 'success');
    }

    /**
     * 應用設置
     */
    applySettings(settings) {
        // 應用主題
        if (settings.themeMode === 'dark') {
            document.body.classList.add('dark-theme');
        } else if (settings.themeMode === 'light') {
            document.body.classList.remove('dark-theme');
        } else {
            // 自動模式
            const hour = new Date().getHours();
            if (hour >= 18 || hour < 6) {
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
            }
        }
        
        // 應用緊湊模式
        if (settings.compactMode) {
            document.body.classList.add('compact-mode');
        } else {
            document.body.classList.remove('compact-mode');
        }
        
        // 應用動畫設置
        if (settings.animationsEnabled) {
            document.body.classList.remove('no-animations');
        } else {
            document.body.classList.add('no-animations');
        }
    }

    /**
     * 重置設置
     */
    resetSettings() {
        if (confirm('確定要重置所有設置嗎？此操作將恢復為默認值。')) {
            localStorage.removeItem('proxyPoolSettings');
            this.loadSettingsValues();
            this.showNotification('設置已重置為默認值', 'info');
        }
    }

    /**
     * 導出設置
     */
    exportSettings() {
        const settings = localStorage.getItem('proxyPoolSettings');
        if (settings) {
            const blob = new Blob([settings], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `proxy-pool-settings-${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.showNotification('設置已導出', 'success');
        } else {
            this.showNotification('沒有設置可導出', 'warning');
        }
    }

    /**
     * 導入設置
     */
    importSettings() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const settings = JSON.parse(e.target.result);
                        localStorage.setItem('proxyPoolSettings', JSON.stringify(settings));
                        this.loadSettingsValues();
                        this.applySettings(settings);
                        this.showNotification('設置已導入', 'success');
                    } catch (error) {
                        this.showNotification('導入失敗：無效的設置文件', 'error');
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }

    /**
     * 立即備份
     */
    backupNow() {
        this.showNotification('正在創建備份...', 'info');
        
        // 模擬備份過程
        setTimeout(() => {
            const backup = {
                settings: JSON.parse(localStorage.getItem('proxyPoolSettings') || '{}'),
                proxies: JSON.parse(localStorage.getItem('proxyPoolData') || '[]'),
                timestamp: new Date().toISOString(),
                version: '1.0.0'
            };
            
            const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `proxy-pool-backup-${new Date().toISOString().slice(0, 10)}-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('備份已完成', 'success');
        }, 2000);
    }

    /**
     * 恢復備份
     */
    restoreBackup() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const backup = JSON.parse(e.target.result);
                        
                        if (backup.settings) {
                            localStorage.setItem('proxyPoolSettings', JSON.stringify(backup.settings));
                        }
                        if (backup.proxies) {
                            localStorage.setItem('proxyPoolData', JSON.stringify(backup.proxies));
                        }
                        
                        this.loadSettingsValues();
                        this.showNotification('備份已恢復', 'success');
                        
                        // 刷新頁面以應用恢復的設置
                        setTimeout(() => {
                            location.reload();
                        }, 1000);
                        
                    } catch (error) {
                        this.showNotification('恢復失敗：無效的備份文件', 'error');
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }

    /**
     * 清理數據
     */
    cleanupData() {
        if (confirm('確定要清理數據嗎？此操作將刪除所有代理數據和測試記錄。')) {
            this.showNotification('正在清理數據...', 'info');
            
            setTimeout(() => {
                localStorage.removeItem('proxyPoolData');
                this.showNotification('數據清理完成', 'success');
            }, 2000);
        }
    }

    /**
     * 重置所有設置
     */
    resetAllSettings() {
        if (confirm('確定要重置所有設置嗎？此操作將刪除所有自定義設置和數據。')) {
            localStorage.clear();
            this.showNotification('所有設置已重置', 'info');
            
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    }

    /**
     * 重新生成API密鑰
     */
    generateNewAPIKey() {
        const newKey = 'proxy-pool-' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        document.getElementById('apiKey').value = newKey;
        this.showNotification('API密鑰已重新生成', 'success');
    }

    /**
     * 初始化圖表
     */
    initCharts() {
        // 創建狀態趨勢圖表
        const ctx = document.getElementById('statusChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
                    datasets: [{
                        label: '在線代理',
                        data: [850, 875, 890, 920, 945, 935, 987],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }, {
                        label: '離線代理',
                        data: [120, 110, 95, 80, 75, 85, 65],
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    elements: {
                        point: {
                            radius: 4,
                            hoverRadius: 6
                        }
                    }
                }
            });
        }
        
        // 綁定圖表時間週期按鈕事件
        this.bindChartPeriodEvents();
    }

    /**
     * 綁定圖表時間週期事件
     */
    bindChartPeriodEvents() {
        const chartButtons = document.querySelectorAll('.chart-action-btn');
        chartButtons.forEach(button => {
            button.addEventListener('click', () => {
                // 移除所有按鈕的活動狀態
                chartButtons.forEach(btn => btn.classList.remove('active'));
                // 添加當前按鈕的活動狀態
                button.classList.add('active');
                
                // 獲取選擇的週期
                const period = button.dataset.period;
                
                // 更新圖表數據
                this.updateChartData(period);
            });
        });
    }

    /**
     * 更新圖表數據
     */
    updateChartData(period) {
        const chart = Chart.getChart('statusChart');
        if (chart) {
            // 根據週期更新數據
            let labels, data1, data2;
            
            switch(period) {
                case '7d':
                    labels = ['第1天', '第2天', '第3天', '第4天', '第5天', '第6天', '第7天'];
                    data1 = [820, 850, 875, 890, 920, 945, 987];
                    data2 = [140, 120, 110, 95, 80, 75, 65];
                    break;
                case '30d':
                    labels = ['第1週', '第2週', '第3週', '第4週'];
                    data1 = [850, 875, 920, 987];
                    data2 = [120, 110, 80, 65];
                    break;
                default: // 24h
                    labels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'];
                    data1 = [850, 875, 890, 920, 945, 935, 987];
                    data2 = [120, 110, 95, 80, 75, 85, 65];
            }
            
            chart.data.labels = labels;
            chart.data.datasets[0].data = data1;
            chart.data.datasets[1].data = data2;
            chart.update();
        }
    }

    /**
     * 生成模擬圖表
     */
    generateMockChart(canvas) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // 清除畫布
        ctx.clearRect(0, 0, width, height);
        
        // 繪製簡單的折線圖
        ctx.strokeStyle = '#1890ff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < width; i += 20) {
            const y = height / 2 + Math.sin(i * 0.02) * height / 4 + Math.random() * 20;
            if (i === 0) {
                ctx.moveTo(i, y);
            } else {
                ctx.lineTo(i, y);
            }
        }
        
        ctx.stroke();
    }

    /**
     * 顯示通知
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.querySelector('.notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    <i class="${icons[type]}"></i>
                    ${type === 'success' ? '成功' : type === 'error' ? '錯誤' : type === 'warning' ? '警告' : '信息'}
                </div>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        `;

        container.appendChild(notification);
        
        // 觸發顯示動畫
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // 自動移除
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, duration);

        // 更新通知計數
        this.updateNotificationCount();
    }

    /**
     * 更新通知計數
     */
    updateNotificationCount() {
        const countElement = document.querySelector('.notification-count');
        if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = currentCount + 1;
            countElement.style.display = 'block';
        }
    }

    /**
     * 顯示載入狀態
     */
    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('active');
        }
    }

    /**
     * 隱藏載入狀態
     */
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('active');
        }
    }

    /**
     * 執行搜尋
     */
    performSearch(query) {
        if (!query.trim()) return;
        
        this.showLoading();
        
        // 模擬搜尋延遲
        setTimeout(() => {
            this.showNotification(`搜尋 "${query}" 找到 ${Math.floor(Math.random() * 50) + 1} 個結果`, 'info');
            this.hideLoading();
        }, 1000);
    }

    /**
     * 切換懸浮菜單
     */
    toggleFABMenu() {
        const fabMenu = document.querySelector('.fab-menu');
        if (fabMenu) {
            fabMenu.classList.toggle('active');
        }
    }

    /**
     * 處理FAB操作
     */
    handleFABAction(action) {
        this.toggleFABMenu(); // 關閉菜單
        
        const actions = {
            'add-proxy': () => this.addProxy(),
            'refresh-all': () => this.refreshAllProxies(),
            'export-data': () => this.exportProxies(),
            'settings': () => this.loadPageContent('settings')
        };
        
        if (actions[action]) {
            actions[action]();
        }
    }

    /**
     * 添加代理
     */
    addProxy() {
        this.showNotification('打開添加代理對話框', 'info');
        // 這裡可以打開模態框
    }

    /**
     * 刷新所有代理
     */
    refreshAllProxies() {
        this.showLoading();
        setTimeout(() => {
            this.showNotification('所有代理已刷新', 'success');
            this.hideLoading();
        }, 2000);
    }

    /**
     * 導出代理
     */
    exportProxies() {
        this.showNotification('正在導出代理數據...', 'info');
        setTimeout(() => {
            this.showNotification('代理數據導出完成', 'success');
        }, 1500);
    }

    /**
     * 應用過濾器
     */
    applyFilters() {
        this.showLoading();
        setTimeout(() => {
            this.showNotification('過濾器已應用', 'success');
            this.hideLoading();
        }, 800);
    }

    /**
     * 處理響應式佈局
     */
    handleResize() {
        const isMobile = window.innerWidth <= 768;
        const sidebar = document.querySelector('.sidebar');
        
        if (isMobile && sidebar) {
            sidebar.classList.add('mobile');
        } else if (sidebar) {
            sidebar.classList.remove('mobile');
        }
    }

    /**
     * 切換移動端菜單
     */
    toggleMobileMenu() {
        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.classList.toggle('mobile-active');
        }
    }

    /**
     * 關閉移動端菜單
     */
    closeMobileMenu() {
        const navMenu = document.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.classList.remove('mobile-active');
        }
    }

    /**
     * 設置AJAX攔截器
     */
    setupAjaxInterceptors() {
        // 這裡可以設置XMLHttpRequest或fetch的攔截器
        // 用於在請求開始時顯示載入狀態，請求完成時隱藏
    }

    /**
     * 處理按鈕點擊
     */
    handleButtonClick(button) {
        const action = button.getAttribute('data-action');
        if (action) {
            // 處理特定的按鈕操作
            console.log('按鈕操作:', action);
        }
    }

    /**
     * 刷新統計數據
     */
    refreshStats() {
        this.showLoading();
        setTimeout(() => {
            this.showNotification('統計數據已刷新', 'success');
            this.hideLoading();
        }, 1000);
    }

    /**
     * 保存設置
     */
    saveSettings() {
        this.showNotification('設置已保存', 'success');
    }

    /**
     * 重新生成API密鑰
     */
    regenerateAPIKey() {
        if (confirm('確定要重新生成API密鑰嗎？')) {
            this.showNotification('API密鑰已重新生成', 'success');
        }
    }

    /**
     * 主題切換功能
     */
    initTheme() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;
        
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // 監聽系統主題變化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                if (!localStorage.getItem('theme')) {
                    const theme = e.matches ? 'dark' : 'light';
                    document.documentElement.setAttribute('data-theme', theme);
                }
            });
        }
        
        // 主題切換按鈕事件
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            this.showNotification(`已切換到${newTheme === 'dark' ? '深色' : '亮色'}主題`, 'success');
        });
    }
}

// 全局實例
let proxyManager;

// 頁面加載完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    proxyManager = new ProxyManager();
});

// 導出給全局使用
window.proxyManager = proxyManager;
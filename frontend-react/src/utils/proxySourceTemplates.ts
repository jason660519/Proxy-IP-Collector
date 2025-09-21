/**
 * 代理來源配置模板
 * 
 * 為每個代理來源提供預設的配置模板
 */

export interface ProxySourceTemplate {
  name: string;
  source_type: 'web_scraping' | 'api' | 'playwright';
  description: string;
  config: {
    [key: string]: any;
  };
}

/**
 * 代理來源配置模板集合
 */
export const proxySourceTemplates: Record<string, ProxySourceTemplate> = {
  '89ip.cn': {
    name: '89ip.cn',
    source_type: 'web_scraping',
    description: '89ip.cn 多頁面代理爬取',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://www.89ip.cn/index_{page}.html',
      page_range: [1, 10],
      rate_limit: 60,
      timeout: 30,
      retry_count: 3,
      source_name: '89ip.cn'
    }
  },
  'kuaidaili-intr': {
    name: 'kuaidaili-intr',
    source_type: 'web_scraping',
    description: '快代理國內代理',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://www.kuaidaili.com/free/intr/',
      proxy_type: 'intr',
      rate_limit: 60,
      timeout: 30,
      retry_count: 3,
      source_name: 'kuaidaili-intr'
    }
  },
  'kuaidaili-inha': {
    name: 'kuaidaili-inha',
    source_type: 'web_scraping',
    description: '快代理海外代理',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://www.kuaidaili.com/free/inha/',
      proxy_type: 'inha',
      rate_limit: 60,
      timeout: 30,
      retry_count: 3,
      source_name: 'kuaidaili-inha'
    }
  },
  'geonode-api-v2': {
    name: 'geonode-api-v2',
    source_type: 'api',
    description: 'GeoNode API 代理服務',
    config: {
      source_type: 'api',
      api_endpoint: 'https://proxylist.geonode.com/api/proxy-list',
      page_range: [1, 5],
      limit_per_page: 50,
      rate_limit: 120,
      timeout: 30,
      retry_count: 3,
      source_name: 'geonode-api-v2'
    }
  },
  'proxydb-net': {
    name: 'proxydb-net',
    source_type: 'web_scraping',
    description: 'ProxyDB.net 代理數據庫',
    config: {
      source_type: 'web_scraping',
      base_url: 'http://proxydb.net/?offset={offset}',
      offset_range: [0, 150, 30],
      rate_limit: 30,
      timeout: 45,
      retry_count: 3,
      source_name: 'proxydb-net'
    }
  },
  'proxynova-com': {
    name: 'proxynova-com',
    source_type: 'web_scraping',
    description: 'ProxyNova.com 多國家代理',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://www.proxynova.com/proxy-server-list/',
      country_pages: ['country-all', 'country-us', 'country-gb'],
      rate_limit: 40,
      timeout: 30,
      retry_count: 3,
      source_name: 'proxynova-com'
    }
  },
  'spys-one': {
    name: 'spys-one',
    source_type: 'playwright',
    description: 'Spys.one JavaScript 代理爬取',
    config: {
      source_type: 'playwright',
      base_url: 'http://spys.one/free-proxy-list/',
      use_playwright: true,
      rate_limit: 20,
      timeout: 60,
      retry_count: 2,
      source_name: 'spys-one'
    }
  },
  'free-proxy-list.net': {
    name: 'free-proxy-list.net',
    source_type: 'web_scraping',
    description: 'Free Proxy List 免費代理',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://free-proxy-list.net/',
      rate_limit: 60,
      timeout: 30,
      retry_count: 3,
      source_name: 'free-proxy-list.net'
    }
  },
  'ssl-proxies': {
    name: 'ssl-proxies',
    source_type: 'web_scraping',
    description: 'SSL Proxies HTTPS代理',
    config: {
      source_type: 'web_scraping',
      base_url: 'https://www.sslproxies.org/',
      rate_limit: 60,
      timeout: 30,
      retry_count: 3,
      source_name: 'ssl-proxies'
    }
  }
};

/**
 * 根據來源名稱獲取配置模板
 * @param sourceName 代理來源名稱
 * @returns 配置模板或null
 */
export function getProxySourceTemplate(sourceName: string): ProxySourceTemplate | null {
  return proxySourceTemplates[sourceName] || null;
}

/**
 * 獲取所有可用的配置模板
 * @returns 配置模板列表
 */
export function getAllProxySourceTemplates(): ProxySourceTemplate[] {
  return Object.values(proxySourceTemplates);
}

/**
 * 根據來源類型篩選配置模板
 * @param sourceType 來源類型
 * @returns 符合類型的配置模板列表
 */
export function getTemplatesByType(sourceType: string): ProxySourceTemplate[] {
  return Object.values(proxySourceTemplates).filter(
    template => template.source_type === sourceType
  );
}
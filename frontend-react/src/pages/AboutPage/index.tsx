import React, { useState } from 'react';
import { Card, Typography, Space, Button, Modal, Tag, Timeline, List } from 'antd';
import { GithubOutlined, MailOutlined, BookOutlined, CodeOutlined, StarOutlined, SafetyOutlined, TeamOutlined, GlobalOutlined, HeartOutlined } from '@ant-design/icons';
import './AboutPage.css';

const { Title, Paragraph, Text } = Typography;

/**
 * 關於頁面組件
 * 提供應用程序信息、開發者信息、功能特性、更新日誌等
 */
const AboutPage: React.FC = () => {
  const [showChangelog, setShowChangelog] = useState(false);
  const [showContributors, setShowContributors] = useState(false);

  // 應用信息
  const appInfo = {
    name: 'Proxy Manager Pro',
    version: '1.0.0',
    description: '專業的代理IP管理工具，支持多種代理協議，提供強大的代理池管理功能',
    author: '開發團隊',
    license: 'MIT',
    repository: 'https://github.com/proxy-manager/proxy-manager-pro',
    website: 'https://proxymanager.pro'
  };

  // 功能特性
  const features = [
    {
      title: '多協議支持',
      description: '支持 HTTP、HTTPS、SOCKS4、SOCKS5 等多種代理協議',
      icon: <GlobalOutlined />,
      color: 'blue'
    },
    {
      title: '智能代理池',
      description: '自動管理代理池，支持代理健康檢查和負載均衡',
      icon: <SafetyOutlined />,
      color: 'green'
    },
    {
      title: '任務調度',
      description: '強大的任務調度系統，支持定時任務和批量操作',
      icon: <CodeOutlined />,
      color: 'orange'
    },
    {
      title: '實時監控',
      description: '實時監控代理狀態，提供詳細的統計和報告',
      icon: <StarOutlined />,
      color: 'purple'
    },
    {
      title: '安全防護',
      description: '多重安全機制，保護您的代理資源和數據安全',
      icon: <SafetyOutlined />,
      color: 'red'
    },
    {
      title: '開源社區',
      description: '開源項目，活躍的社區支持，持續更新和改進',
      icon: <TeamOutlined />,
      color: 'cyan'
    }
  ];

  // 技術棧
  const techStack = [
    { name: 'React', version: '18.x', description: '前端框架' },
    { name: 'TypeScript', version: '5.x', description: '類型安全的 JavaScript' },
    { name: 'Ant Design', version: '5.x', description: '企業級 UI 設計語言' },
    { name: 'Apache ECharts', version: '5.x', description: '強大的圖表庫' },
    { name: 'Redux Toolkit', version: '2.x', description: '狀態管理' },
    { name: 'React Router', version: '6.x', description: '路由管理' },
    { name: 'FastAPI', version: '0.x', description: '後端 API 框架' },
    { name: 'Python', version: '3.11+', description: '後端開發語言' },
    { name: 'PostgreSQL', version: '15+', description: '數據庫' },
    { name: 'Redis', version: '7+', description: '緩存和消息隊列' }
  ];

  // 更新日誌
  const changelog = [
    {
      version: '1.0.0',
      date: '2024-01-01',
      changes: [
        '初始版本發布',
        '代理管理功能',
        '任務調度系統',
        '實時監控面板',
        '設置管理界面'
      ]
    },
    {
      version: '0.9.0',
      date: '2023-12-15',
      changes: [
        'Beta 版本測試',
        '性能優化',
        'Bug 修復',
        'UI 改進'
      ]
    }
  ];

  // 貢獻者
  const contributors = [
    { name: '張三', role: '主要開發者', avatar: '👨‍💻' },
    { name: '李四', role: 'UI/UX 設計師', avatar: '🎨' },
    { name: '王五', role: '後端開發者', avatar: '⚙️' },
    { name: '趙六', role: '測試工程師', avatar: '🧪' }
  ];

  /**
   * 打開外部鏈接
   */
  const openExternalLink = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  /**
   * 複製郵箱地址
   */
  const copyEmail = () => {
    navigator.clipboard.writeText('support@proxymanager.pro');
    Modal.success({
      title: '複製成功',
      content: '郵箱地址已複製到剪貼板'
    });
  };

  return (
    <div className="about-page">
      <div className="about-container">
        {/* 應用信息卡片 */}
        <Card className="about-header-card">
          <div className="about-header">
            <div className="about-logo">
              <div className="logo-icon">
                <CodeOutlined />
              </div>
              <div className="logo-text">
                <Title level={2} className="app-name">{appInfo.name}</Title>
                <Text type="secondary" className="app-version">版本 {appInfo.version}</Text>
              </div>
            </div>
            <div className="about-actions">
              <Button
                type="primary"
                icon={<GithubOutlined />}
                onClick={() => openExternalLink(appInfo.repository)}
              >
                GitHub
              </Button>
              <Button
                icon={<BookOutlined />}
                onClick={() => openExternalLink('https://docs.proxymanager.pro')}
              >
                文檔
              </Button>
            </div>
          </div>
          <Paragraph className="app-description">
            {appInfo.description}
          </Paragraph>
          <div className="app-meta">
            <Text type="secondary">作者：{appInfo.author}</Text>
            <Text type="secondary">許可證：{appInfo.license}</Text>
            <Text type="secondary">網站：{appInfo.website}</Text>
          </div>
        </Card>

        {/* 功能特性 */}
        <Card className="about-section-card">
          <Title level={3} className="section-title">
            <StarOutlined /> 核心功能
          </Title>
          <div className="features-grid">
            {features.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className={`feature-icon ${feature.color}`}>
                  {feature.icon}
                </div>
                <div className="feature-content">
                  <Title level={4} className="feature-title">
                    {feature.title}
                  </Title>
                  <Paragraph className="feature-description">
                    {feature.description}
                  </Paragraph>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* 技術棧 */}
        <Card className="about-section-card">
          <Title level={3} className="section-title">
            <CodeOutlined /> 技術棧
          </Title>
          <List
            grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
            dataSource={techStack}
            renderItem={(tech) => (
              <List.Item>
                <Card className="tech-card" hoverable>
                  <div className="tech-info">
                    <Title level={4} className="tech-name">{tech.name}</Title>
                    <Text type="secondary" className="tech-version">{tech.version}</Text>
                    <Paragraph className="tech-description">
                      {tech.description}
                    </Paragraph>
                  </div>
                </Card>
              </List.Item>
            )}
          />
        </Card>

        {/* 聯繫信息 */}
        <Card className="about-section-card">
          <Title level={3} className="section-title">
            <MailOutlined /> 聯繫我們
          </Title>
          <div className="contact-section">
            <Space direction="vertical" size="large" className="contact-content">
              <div className="contact-item">
                <Button
                  size="large"
                  icon={<MailOutlined />}
                  onClick={copyEmail}
                  className="contact-button"
                >
                  技術支持
                </Button>
                <Text className="contact-description">
                  有任何問題或建議，請聯繫我們的技術支持團隊
                </Text>
              </div>
              
              <div className="contact-item">
                <Button
                  size="large"
                  icon={<GithubOutlined />}
                  onClick={() => openExternalLink(appInfo.repository + '/issues')}
                  className="contact-button"
                >
                  問題反饋
                </Button>
                <Text className="contact-description">
                  在 GitHub 上提交 Issue，我們會盡快回復
                </Text>
              </div>
              
              <div className="contact-item">
                <Button
                  size="large"
                  icon={<HeartOutlined />}
                  onClick={() => openExternalLink(appInfo.repository)}
                  className="contact-button"
                >
                  給我們 Star
                </Button>
                <Text className="contact-description">
                  如果覺得我們的項目不錯，請給個 Star 支持我們
                </Text>
              </div>
            </Space>
          </div>
        </Card>

        {/* 底部操作 */}
        <Card className="about-footer-card">
          <div className="footer-actions">
            <Button
              type="link"
              onClick={() => setShowChangelog(true)}
            >
              更新日誌
            </Button>
            <Button
              type="link"
              onClick={() => setShowContributors(true)}
            >
              貢獻者
            </Button>
            <Button
              type="link"
              onClick={() => openExternalLink(appInfo.repository + '/blob/main/LICENSE')}
            >
              許可證
            </Button>
          </div>
        </Card>
      </div>

      {/* 更新日誌模態框 */}
      <Modal
        title="更新日誌"
        open={showChangelog}
        onCancel={() => setShowChangelog(false)}
        footer={null}
        width={600}
        className="changelog-modal"
      >
        <Timeline
          items={changelog.map((version) => ({
            children: (
              <div className="changelog-item">
                <div className="changelog-header">
                  <Tag color="blue">{version.version}</Tag>
                  <Text type="secondary">{version.date}</Text>
                </div>
                <List
                  size="small"
                  dataSource={version.changes}
                  renderItem={(change) => (
                    <List.Item className="changelog-change">
                      {change}
                    </List.Item>
                  )}
                />
              </div>
            )
          }))}
        />
      </Modal>

      {/* 貢獻者模態框 */}
      <Modal
        title="貢獻者"
        open={showContributors}
        onCancel={() => setShowContributors(false)}
        footer={null}
        width={500}
        className="contributors-modal"
      >
        <List
          dataSource={contributors}
          renderItem={(contributor) => (
            <List.Item className="contributor-item">
              <div className="contributor-avatar">{contributor.avatar}</div>
              <div className="contributor-info">
                <Text className="contributor-name">{contributor.name}</Text>
                <Text type="secondary" className="contributor-role">
                  {contributor.role}
                </Text>
              </div>
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};

export default AboutPage;
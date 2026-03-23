# 🎮 游戏异业合作情报站

自动追踪 20 款热门游戏 × 10 大品牌类别（200+品牌）的跨界合作动态，每日生成精美情报日报。

---

## 📦 项目结构

```
├── config.py              # 配置文件（游戏/品牌/关键词/数据源）
├── database.py            # 数据库模块（SQLite CRUD + 统计查询）
├── collector.py           # 数据采集引擎（Bing搜索/新闻/RSS）
├── report_generator.py    # 每日报告生成器（精美HTML日报）
├── portal_generator.py    # 情报站门户生成器（总入口页面）
├── run.py                 # 一键运行入口（命令行工具）
├── run.bat                # Windows 一键双击运行
├── intel_hub.db           # SQLite 数据库（自动生成）
├── reports/               # 每日报告目录（自动生成）
│   └── daily_2026-03-20.html
└── portal/                # 门户页面目录（自动生成）
    └── index.html
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 lxml
```

### 2. 一键运行

**方式一：双击运行**

直接双击 `run.bat`，自动完成 采集→报告→门户 全流程。

**方式二：命令行运行**

```bash
# 完整流程：采集 + 报告 + 门户
python run.py

# 仅数据采集
python run.py --collect-only

# 仅生成今日报告
python run.py --report-only

# 仅更新门户页面
python run.py --portal-only

# 查看统计数据
python run.py --stats

# 指定日期生成报告
python run.py --report-only --date 2026-03-20

# 采集时提取文章正文（更详细但较慢）
python run.py --fetch-content

# 限制查询数量（加快速度）
python run.py --max-queries 20
```

### 3. 查看结果

- **情报站门户**: 打开 `portal/index.html`
- **每日日报**: 打开 `reports/daily_YYYY-MM-DD.html`

---

## 🎯 功能概览

### 配置模块 (`config.py`)
- 20 款目标游戏（王者荣耀、原神、和平精英等）
- 10 大品牌类别（餐饮、快消、美妆、服饰、3C等）
- 200+ 预设品牌库
- 智能搜索关键词生成
- Bing搜索/新闻 + RSS 三大数据源

### 数据采集引擎 (`collector.py`)
- **Bing 搜索**: 基于关键词的网页搜索采集
- **Bing 新闻**: 实时新闻采集
- **RSS 订阅**: 36氪、游戏葡萄、GameLook 等
- **智能分析**: 自动识别游戏名、品牌名、合作类型
- **热度评分**: 基于游戏热度、品牌量级、时效性等多维度打分
- **内容去重**: 基于标题+URL哈希去重

### 数据库模块 (`database.py`)
- SQLite 存储，自动建表建索引
- 合作情报表、日报记录表、采集日志表
- 支持按日期/游戏/品牌/类别的多维查询
- 丰富的统计分析接口

### 每日报告 (`report_generator.py`)
- 精美暗色主题 HTML 日报
- 4 种交互式图表（Chart.js）
- 游戏分布、品牌类别、合作类型、采集趋势
- 筛选与搜索功能
- 详情弹窗查看完整信息

### 情报站门户 (`portal_generator.py`)
- 总入口页面，汇聚所有日报
- 全局统计面板
- 热门情报 TOP12
- 最新情报流
- 游戏情报排行
- 品牌类别分布 / 合作类型分布图表
- 日报快速导航

---

## ⚙️ 自定义配置

编辑 `config.py` 可以：
- 增删目标游戏列表
- 增删品牌和品牌类别
- 调整搜索关键词模板
- 配置 RSS 源
- 调整采集参数（频率、超时、去重阈值等）
- 调整报告参数（最大条目数、摘要长度等）

---

## 📝 注意事项

1. 首次运行会自动创建数据库和目录
2. 采集依赖网络环境，需能正常访问 Bing
3. 建议每日运行一次，积累数据后趋势分析更有价值
4. `--fetch-content` 模式会逐个提取文章正文，速度较慢
5. 可通过 Windows 任务计划实现每日自动运行

# Sucrawler

> 企业级多平台爬虫框架

Sucrawler 是一个模块化、可扩展的异步爬虫框架，采用插件化架构设计，支持多平台数据采集、多种存储后端、丰富的中间件和数据处理管道。

## 特性

- **异步架构**: 基于 asyncio 构建，支持高并发爬取
- **多平台支持**: 插件化平台注册机制，内置小红书平台实现
- **多种下载器**: 支持 httpx、aiohttp 等多种异步 HTTP 客户端
- **丰富中间件**: 重试、限流、代理、User-Agent 轮换、日志、统计等开箱即用
- **数据管道**: 清洗、去重、丰富、验证四步数据处理流程
- **多存储后端**: JSON、CSV、SQLite、MySQL、PostgreSQL、MongoDB、Redis、Elasticsearch
- **配置驱动**: YAML 配置文件 + 环境变量，支持多环境部署
- **API 服务**: FastAPI 提供 RESTful 接口，支持任务管理和数据查询
- **类型安全**: 全量 Pydantic 类型定义 + mypy 严格模式

## 项目结构

```
sucrawler/
├── api/                    # FastAPI 服务层
│   ├── routes/             # API 路由
│   └── schemas/            # 请求/响应模型
├── config/                 # 配置文件 (YAML)
├── scripts/                # 工具脚本
├── sucrawler/              # 核心框架
│   ├── common/             # 公共模块 (常量、异常、装饰器)
│   ├── config/             # 配置加载与验证
│   ├── core/               # 核心引擎
│   │   ├── base/           # 组件基类
│   │   ├── interfaces/     # 接口定义
│   │   ├── engine.py       # 爬虫引擎
│   │   └── events.py       # 事件总线
│   ├── downloaders/        # 下载器实现
│   ├── extractors/         # 数据提取器
│   ├── logging/            # 日志系统
│   ├── middlewares/        # 中间件
│   ├── models/             # 数据模型
│   ├── parsers/            # 响应解析器
│   ├── pipelines/          # 数据处理管道
│   ├── platforms/          # 平台实现
│   │   └── xiaohongshu/    # 小红书平台
│   ├── repositories/       # 数据仓储层
│   ├── scheduler/          # 任务调度器
│   ├── services/           # 业务服务层
│   ├── storage/            # 存储后端
│   └── utils/              # 工具函数
└── tests/                  # 测试套件
```

## 快速开始

### 环境要求

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/CherryKingOne/sucrawler.git
cd sucrawler

# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -e .
```

### 配置

复制环境变量示例文件：

```bash
cp .env.example .env
```

配置文件位于 `config/` 目录：

- `base.yaml` - 基础配置
- `dev.yaml` - 开发环境
- `test.yaml` - 测试环境
- `prod.yaml` - 生产环境

### 运行爬虫

```bash
# 命令行方式
python scripts/run_spider.py \
  --platform xiaohongshu \
  --spider-type search \
  --keyword "美食" \
  --env dev

# 或使用 CLI 入口
python -m sucrawler.main run --platform xiaohongshu
```

### 启动 API 服务

```bash
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

API 文档地址: http://localhost:8000/docs

## 核心概念

### 爬虫引擎

[CrawlerEngine](file:///workspace/sucrawler/core/engine.py) 是整个框架的核心，协调整个爬取流程：

```
请求 → 请求中间件 → 下载器 → 响应中间件 → 解析器 → 提取器 → 管道 → 存储
```

### 平台 (Platform)

每个平台是一个独立的插件，通过 `@register_platform` 装饰器注册：

```python
from sucrawler.platforms.registry import register_platform
from sucrawler.core.interfaces.platform import BasePlatform

@register_platform("myplatform")
class MyPlatform(BasePlatform):
    name = "myplatform"

    def create_downloader(self): ...
    def create_parser(self): ...
    def create_extractor(self): ...
    def get_middlewares(self): ...
    def get_pipelines(self): ...
```

### 中间件 (Middleware)

中间件可以在请求发送前、响应返回后、异常发生时介入处理：

| 中间件 | 功能 |
|--------|------|
| RetryMiddleware | 失败重试，支持指数退避 |
| RateLimitMiddleware | 令牌桶限流 |
| UserAgentMiddleware | User-Agent 轮换 |
| ProxyMiddleware | 代理池轮换 |
| LogMiddleware | 请求/响应日志 |
| StatsMiddleware | 爬取统计 |

### 数据管道 (Pipeline)

数据管道按顺序处理爬取到的条目：

| 管道 | 功能 |
|------|------|
| CleanPipeline | HTML 清洗、空白去除、特殊字符过滤 |
| DedupPipeline | 去重（支持布隆过滤器） |
| EnrichPipeline | 元数据补充、字段转换、ID 生成 |
| ValidatePipeline | Pydantic 模型验证 |

### 存储后端 (Storage)

通过 `@register_storage` 注册存储后端：

| 存储类型 | 描述 |
|----------|------|
| json | JSON 文件存储 |
| csv | CSV 表格存储 |
| sqlite | SQLite 数据库 |
| mysql | MySQL 数据库 |
| postgres | PostgreSQL 数据库 |
| mongodb | MongoDB 文档数据库 |
| redis | Redis 缓存 |
| es | Elasticsearch 搜索引擎 |
| image | 图片文件存储 |

## 平台支持

### 小红书 (xiaohongshu)

内置小红书平台实现，支持：

- **笔记搜索** - 按关键词搜索笔记
- **笔记详情** - 获取笔记完整内容
- **评论爬取** - 获取笔记评论列表
- **用户爬取** - 获取用户信息和发布的笔记

配置示例：

```yaml
platforms:
  xiaohongshu:
    enabled: true
    base_url: https://www.xiaohongshu.com
    cookie: "your_cookie_here"
    sign_key: "your_sign_key"
    rate_limit:
      enabled: true
      requests_per_second: 5.0
```

## API 接口

### 任务管理

- `POST /api/v1/tasks` - 创建爬取任务
- `GET /api/v1/tasks/{task_id}` - 查询任务状态
- `GET /api/v1/tasks` - 任务列表
- `POST /api/v1/tasks/{task_id}/cancel` - 取消任务

### 数据查询

- `GET /api/v1/data` - 查询数据
- `POST /api/v1/data/query` - 高级查询
- `GET /api/v1/data/stats` - 数据统计
- `POST /api/v1/data/export` - 数据导出

## 配置说明

### 核心配置

```yaml
app:
  name: sucrawler
  log_level: INFO

scheduler:
  type: memory
  max_tasks: 1000

downloader:
  type: httpx
  timeout: 30
  max_concurrent: 10
  retry:
    max_attempts: 3
    backoff_factor: 2.0

middleware:
  retry:
    enabled: true
  rate_limit:
    enabled: true
    requests_per_second: 10.0
  user_agent:
    enabled: true
    rotate: true
  proxy:
    enabled: false
  log:
    enabled: true
  stats:
    enabled: true

storage:
  default_backend: default
  backends:
    default:
      type: local
      base_path: ./data
```

## 开发

### 代码规范

```bash
# 代码格式化
uv run black .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy .
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单元测试
uv run pytest tests/unit

# 查看覆盖率
uv run pytest --cov=sucrawler
```

### 新增平台

1. 在 `sucrawler/platforms/` 下创建平台目录
2. 实现 `BasePlatform` 接口
3. 使用 `@register_platform` 装饰器注册
4. 在 `__init__.py` 中导入以触发注册

### 新增存储后端

1. 在 `sucrawler/storage/` 对应子目录下创建实现
2. 实现 `BaseStorage` 接口
3. 使用 `@register_storage` 装饰器注册
4. 在 `storage/__init__.py` 中导入以触发注册

## 命令行工具

```bash
# 查看版本
python -m sucrawler.main --version

# 列出支持的平台
python -m sucrawler.main list-platforms

# 运行爬虫
python -m sucrawler.main run --platform xiaohongshu

# 启动 API 服务
python -m sucrawler.main serve

# 初始化数据库
python -m sucrawler.main init-db
```

## 许可证

MIT License

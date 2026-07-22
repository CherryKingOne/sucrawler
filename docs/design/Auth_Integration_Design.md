# 登录认证系统集成设计文档

## 1. 项目背景

sucrawler 项目已完成 CDP 浏览器模块的基础建设，但登录认证体系尚未完善。目前存在以下问题：

1. 小红书等平台爬取需要登录态，但缺乏统一的登录认证流程
2. Cookie 管理功能简单，缺乏登录态有效性检测和自动刷新机制
3. 没有扫码登录、手机号登录等交互式登录方式
4. 登录态存储分散，没有统一的凭证管理体系

MediaCrawler 项目有一套成熟的登录认证和凭证存储体系，可以作为参考进行迁移。

## 2. 需求分析

### 2.1 功能需求

- **多方式登录**：支持扫码登录、手机号登录、Cookie 导入登录
- **登录态持久化**：自动保存和恢复登录状态，避免重复登录
- **登录态有效性检测**：自动检测登录是否过期，过期时触发重新登录
- **多平台支持**：认证框架可扩展，支持小红书、抖音、微博等多个平台
- **凭证安全存储**：登录凭证安全存储，支持加密
- **登录流程可交互**：扫码登录时显示二维码，手机号登录时支持验证码输入

### 2.2 非功能需求

- **低耦合**：认证模块与爬虫核心逻辑解耦
- **可扩展**：新增平台登录方式简单
- **高可用**：登录失败时有明确的错误提示和降级方案
- **可配置**：登录方式、存储路径等均可配置

## 3. MediaCrawler 登录认证架构分析

### 3.1 整体架构

MediaCrawler 的登录认证体系分为以下几层：

```
┌─────────────────────────────────────────────────────┐
│                   Crawler (core.py)                   │
│  - 启动浏览器 → 创建 Client → 检测登录态 → 触发登录   │
└──────────────────┬──────────────────────────────────┘
                   │
     ┌─────────────┴─────────────┐
     ▼                           ▼
┌───────────┐             ┌───────────┐
│ Login     │             │ Client    │
│ (login.py)│             │(client.py)│
│ - 扫码    │             │ - API调用 │
│ - 手机号  │             │ - pong()  │
│ - Cookie  │             │ - 检测登录│
└───────────┘             └─────┬─────┘
                                │
                       ┌────────┴────────┐
                       ▼                 ▼
                  ┌─────────┐      ┌──────────┐
                  │  Cookie │      │ 登录状态 │
                  │  管理    │      │  持久化   │
                  └─────────┘      └────┬─────┘
                                        │
                                 ┌──────┴──────┐
                                 ▼             ▼
                           ┌──────────┐  ┌──────────┐
                           │ user_data│  │  缓存系统 │
                           │  _dir    │  │ (Cache)  │
                           └──────────┘  └──────────┘
```

### 3.2 核心模块分析

#### 3.2.1 缓存系统

**文件**：`cache/abs_cache.py`、`cache/local_cache.py`、`cache/redis_cache.py`

**架构设计**：

```
┌─────────────────────┐
│   AbstractCache     │  抽象基类
│  - get(key)         │
│  - set(key, value)  │
│  - keys(pattern)    │
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐ ┌───────────┐
│  Expiring│ │  RedisCache│
│ LocalCache│ │           │
│ - 内存字典│ │ - Redis   │
│ - 定时清理│ │ - 持久化  │
└────┬─────┘ └─────┬─────┘
     │             │
     └──────┬──────┘
            ▼
    ┌───────────────┐
    │  CacheFactory │  工厂模式
    │  create_cache()│
    └───────────────┘
```

**核心设计**：
- **AbstractCache**：定义统一缓存接口（get / set / keys）
- **ExpiringLocalCache**：本地内存缓存，带过期时间和定时清理（cron_interval）
- **RedisCache**：Redis 分布式缓存（可选，用于多进程/多机器场景）
- **CacheFactory**：工厂模式创建缓存实例

**在认证系统中的作用**：
- 存储手机号验证码（key: `xhs_{phone}`）
- 登录态临时缓存
- 跨组件传递验证码等临时数据

#### 3.2.2 AbstractLogin（基类）

**文件**：`base/base_crawler.py`

**职责**：定义登录器抽象接口

**核心方法**：
- `begin()` - 开始登录流程
- `login_by_qrcode()` - 扫码登录
- `login_by_mobile()` - 手机号登录
- `login_by_cookies()` - Cookie 登录

#### 3.2.2 XiaoHongShuLogin（平台实现）

**文件**：`media_platform/xhs/login.py`

**核心功能**：

| 登录方式 | 实现要点 |
|---------|---------|
| **扫码登录** | 1. 获取二维码图片（base64）<br>2. 本地弹窗显示二维码<br>3. 轮询检测登录状态<br>4. 双重验证：UI元素 + Cookie变化 |
| **手机号登录** | 1. 点击登录按钮 → 切换手机号登录<br>2. 输入手机号 → 发送验证码<br>3. 从缓存读取验证码（支持短信转发）<br>4. 输入验证码 → 提交登录 |
| **Cookie登录** | 1. 解析 Cookie 字符串<br>2. 注入 web_session 等关键 Cookie<br>3. 设置正确的 domain 和 path |

**登录状态检测**（双重验证）：
1. **UI 元素检测**：检测"我"按钮是否出现（XPath）
2. **Cookie 变化检测**：检测 `web_session` 是否从未登录状态变为有效值
3. 使用 tenacity 进行重试，最长 600 次（10分钟）

#### 3.2.3 登录态持久化

**实现方式**：Playwright `launch_persistent_context`

**配置项**：
- `SAVE_LOGIN_STATE` - 是否保存登录状态
- `USER_DATA_DIR` - 用户数据目录，按平台区分：`%s_user_data_dir`

**优势**：
- 浏览器原生持久化，Cookie、LocalStorage、IndexedDB 全部保存
- 下次启动直接加载，无需手动注入 Cookie
- 支持浏览器扩展等完整用户配置

#### 3.2.4 工具函数（crawler_util.py）

**核心工具**：

| 函数 | 作用 |
|------|------|
| `find_login_qrcode()` | 从页面中提取二维码图片（支持 URL 和 base64） |
| `find_qrcode_img_from_canvas()` | 从 canvas 元素提取二维码 |
| `show_qrcode()` | 本地弹窗显示二维码图片 |
| `convert_cookies()` | Cookie 列表转字符串和字典 |
| `convert_str_cookie_to_dict()` | Cookie 字符串转字典 |
| `convert_browser_context_cookies()` | 从 BrowserContext 获取 Cookie |

#### 3.2.5 缓存系统

**文件**：`cache/`

**用途**：
- 存储手机号验证码（key: `xhs_{phone}`）
- 支持内存缓存和 Redis 缓存
- 用于手机号登录时的验证码传递

### 3.3 登录流程详细设计

MediaCrawler 的登录流程（来自架构文档 6.2 节）：

```
开始登录
   │
   ▼
登录类型? ── qrcode ──→ 显示二维码
   │                      │
   │                      ▼
   │                  等待扫描
   │                      │
   │                      ▼
   │                  扫描成功? ── 是 ──┐
   │                      │ 否          │
   │                      └──────┐      │
   │                             ▼      │
   ├── phone ──→ 输入手机号         │   │
   │                │                │   │
   │                ▼                │   │
   │            发送验证码            │   │
   │                │                │   │
   │                ▼                │   │
   │            需要滑块? ── 是 ──→ 滑动验证
   │                │ 否             │   │
   │                ▼                │   │
   │            输入验证码            │   │
   │                │                │   │
   │                ▼                │   │
   │            验证登录              │   │
   │                │                │   │
   │                └────────┐       │   │
   │                         ▼       ▼   │
   └── cookie ──→ 加载已保存Cookie      │
                       │                │
                       ▼                │
                   Cookie有效? ── 是 ───┘
                       │ 否
                       ▼
                   登录失败
                       │
                       └───────┐
                               ▼
                          保存Cookie
                               │
                               ▼
                        更新浏览器上下文
                               │
                               ▼
                           登录完成
```

**关键设计要点**：
1. **三种登录方式**：扫码、手机号、Cookie，统一入口
2. **手机号登录包含滑块验证**：检测到滑块时自动滑动
3. **Cookie 登录先验有效性**：无效则失败，不浪费时间
4. **登录成功统一保存**：无论哪种方式，成功后都保存凭证并更新上下文

### 3.4 浏览器管理与登录的关系

MediaCrawler 的浏览器管理（架构文档 6.3 节）：

| 模式 | 启动方式 | 登录态持久化 | 适用场景 |
|------|---------|-------------|---------|
| 标准模式 | `chromium.launch()` | `launch_persistent_context` | 简单场景、无需反检测 |
| CDP 模式 | 独立进程 + `connect_over_cdp` | 用户数据目录继承 | 反检测、连接已有浏览器 |

**CDP 模式的优势**：
- 用户数据持久化完整（Cookie、LocalStorage、扩展等）
- 浏览器扩展和设置全部继承
- 反检测能力更强
- 支持连接用户自己的浏览器（先登录再爬取）

### 3.5 缓存系统在认证中的作用

缓存系统在认证流程中的关键作用：

| 用途 | Key 模式 | 过期时间 | 说明 |
|------|---------|---------|------|
| 手机号验证码 | `{platform}_{phone}` | 60-300秒 | 手机号登录时，从短信转发服务读取验证码存入缓存，登录器读取使用 |
| 登录态临时缓存 | `{platform}_login_state` | 300秒 | 登录过程中的状态暂存 |
| 滑块验证结果 | `{platform}_slider_{session}` | 60秒 | 滑块验证的临时凭证 |

**缓存系统不仅用于认证**，后续代理池、限流、请求去重等都可以复用这套缓存基础设施。

### 3.6 可复用 vs 不可复用

| 类别 | 内容 | 可复用性 |
|------|------|---------|
| **可直接复用** | 扫码登录流程设计 | 🟢 高 |
| | 手机号登录流程设计 | 🟢 高 |
| | Cookie 管理工具函数 | 🟢 高 |
| | 登录状态双重检测机制 | 🟢 高 |
| | 二维码显示/提取逻辑 | 🟢 高 |
| | 持久化上下文方案 | 🟢 高 |
| **需改造复用** | 平台特定选择器（XPath） | 🟡 中 |
| | 平台特定 Cookie 名称（web_session等） | 🟡 中 |
| | 全局 config 变量方式 → 配置对象 | 🟡 中 |
| **不可复用** | MediaCrawler 的 Client 层 | 🔴 低 |
| | 全局变量配置方式 | 🔴 低 |
| | 与爬虫逻辑耦合的部分 | 🔴 低 |

## 4. sucrawler 当前架构分析

### 4.1 现有认证相关模块

| 模块 | 文件 | 能力 | 不足 |
|------|------|------|------|
| **CookieManager** | `browser/cookie/cookie_manager.py` | Cookie CRUD、文件持久化、格式导出 | 无登录态有效性检测、无自动登录 |
| **XHSCookieMiddleware** | `platforms/xiaohongshu/middlewares/cookie_middleware.py` | 请求中注入 Cookie | 仅静态注入，无动态更新 |
| **XHSConfig.cookie** | `platforms/xiaohongshu/config.py` | Cookie 配置 | 仅支持字符串配置，无多种登录方式 |
| **BrowserManager** | `browser/manager/browser_manager.py` | 浏览器生命周期管理 | 无登录流程集成 |

### 4.2 架构特点

- 优点：DDD 分层清晰，各模块职责单一
- 缺点：认证相关能力分散，缺少统一的认证抽象层

## 5. 两者架构对比

### 5.1 功能对比

| 功能 | MediaCrawler | sucrawler | 差距 |
|------|--------------|-----------|------|
| 扫码登录 | ✅ 支持 | ❌ 无 | 需新增 |
| 手机号登录 | ✅ 支持 | ❌ 无 | 需新增 |
| Cookie 导入登录 | ✅ 支持 | ✅ 支持（简单） | 增强 |
| 登录态持久化 | ✅ user_data_dir | ✅ Cookie文件 + browser_state | 增强 |
| 登录态有效性检测 | ✅ 双重检测 | ❌ 无 | 需新增 |
| 多平台登录抽象 | ✅ AbstractLogin | ❌ 无 | 需新增 |
| 二维码显示 | ✅ PIL弹窗 | ❌ 无 | 需新增 |
| 验证码缓存 | ✅ 内存/Redis | ❌ 无 | 需新增 |
| Cookie 管理 | ✅ 工具函数 | ✅ CookieManager | 对齐 |
| 浏览器管理 | ✅ CDP + Playwright | ✅ CDP + Playwright | 对齐 |

### 5.2 架构差异

| 维度 | MediaCrawler | sucrawler |
|------|--------------|-----------|
| **认证抽象** | AbstractLogin 基类 + 平台实现 | 无统一抽象 |
| **配置方式** | 全局 config 模块变量 | Pydantic 配置对象 |
| **持久化方案** | launch_persistent_context（完整用户数据） | Cookie 文件 + browser_state.json |
| **与爬虫关系** | 强耦合（Crawler 内部直接调用 Login） | 需设计为插件/中间件形式 |
| **状态检测** | Client.pong() + Login.check_login_state() | 无 |

### 5.3 风险分析

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 平台选择器变更 | 🟡 中 | 小红书 UI 变更会导致登录选择器失效 |
| 登录流程复杂度 | 🟡 中 | 扫码登录涉及 UI 交互，调试难度较高 |
| 现有功能影响 | 🟢 低 | 认证模块作为可选能力，不影响现有 HTTP 模式 |
| 业务耦合度 | 🟢 低 | 可设计为独立模块，平台自行选择接入 |

**总体风险等级**：🟡 中风险，技术可行，需注意平台 UI 变化带来的维护成本。

## 6. 新架构设计

### 6.1 设计原则

1. **抽象与实现分离**：定义统一的认证接口，各平台自行实现
2. **插件化集成**：认证模块通过组合方式集成到爬虫，不侵入核心逻辑
3. **渐进式增强**：从 Cookie 持久化开始，逐步添加扫码登录等高级功能
4. **配置驱动**：所有认证行为通过配置控制
5. **平台无关核心**：核心认证逻辑与平台无关，平台差异封装在实现层

### 6.2 模块分层

```
sucrawler/
├── auth/                           # 新增：认证模块（核心）
│   ├── __init__.py
│   ├── base.py                     # 抽象基类
│   ├── types.py                    # 类型定义
│   ├── exceptions.py               # 认证异常
│   ├── credential_store.py         # 凭证存储
│   ├── qrcode.py                   # 二维码工具
│   └── cookie_utils.py             # Cookie 工具函数
│
├── cache/                          # 新增：缓存系统（通用）
│   ├── __init__.py
│   ├── base.py                     # 缓存抽象基类
│   ├── local_cache.py              # 本地内存缓存
│   ├── redis_cache.py              # Redis 缓存（可选）
│   └── factory.py                  # 缓存工厂
│
├── browser/
│   └── cookie/
│       └── cookie_manager.py       # 已存在，增强
│
└── platforms/
    └── xiaohongshu/
        └── auth/                   # 新增：平台认证实现
            ├── __init__.py
            └── xhs_login.py        # 小红书登录器
```

## 7. 新目录结构详解

### 7.1 auth/ 模块（核心认证层）

#### 7.1.1 `auth/base.py` - 抽象基类

**作用**：定义统一的登录器接口

**核心类**：
- `BaseAuthenticator` - 认证器抽象基类

**核心方法**：
```python
async def login(self) -> bool:
    """执行登录流程，返回是否成功"""

async def check_login_status(self) -> bool:
    """检测当前是否已登录"""

async def ensure_logged_in(self) -> bool:
    """确保已登录，未登录则触发登录"""

async def get_credentials(self) -> dict:
    """获取当前登录凭证"""
```

#### 7.1.2 `auth/types.py` - 类型定义

**作用**：认证相关的数据类型

**核心类型**：
- `LoginType` - 登录方式枚举（qrcode / phone / cookie）
- `CredentialInfo` - 凭证信息
- `LoginStatus` - 登录状态

#### 7.1.3 `auth/exceptions.py` - 认证异常

**作用**：认证相关的异常类

**核心异常**：
- `AuthError` - 认证基异常
- `LoginFailedError` - 登录失败
- `LoginTimeoutError` - 登录超时
- `QRCodeExpiredError` - 二维码过期
- `InvalidCredentialError` - 凭证无效

#### 7.1.4 `auth/credential_store.py` - 凭证存储

**作用**：统一管理登录凭证的持久化存储

**核心功能**：
- 凭证保存/加载（支持 JSON 文件）
- 凭证有效性检查（过期时间）
- 多平台凭证隔离
- 可选加密存储

**文件路径规则**：
```
~/.sucrawler/credentials/
├── xiaohongshu/
│   ├── cookies.json
│   └── meta.json
├── douyin/
│   ├── cookies.json
│   └── meta.json
└── ...
```

#### 7.1.5 `auth/qrcode.py` - 二维码工具

**作用**：二维码相关的通用工具

**核心功能**：
- 从页面元素提取二维码图片
- base64 解码与显示
- 本地弹窗显示二维码（PIL）
- 终端显示二维码（ASCII art，可选）

#### 7.1.6 `auth/cookie_utils.py` - Cookie 工具

**作用**：Cookie 格式转换等通用工具

**核心函数**：
- `cookies_list_to_string()` - Cookie 列表转 header 字符串
- `string_to_cookies_list()` - 字符串转 Cookie 列表
- `cookies_list_to_dict()` - Cookie 列表转字典
- `filter_cookies_by_domain()` - 按域名过滤 Cookie

### 7.2 cache/ 模块（通用缓存系统）

#### 7.2.1 `cache/base.py` - 缓存抽象基类

**作用**：定义统一的缓存接口

**核心类**：`AbstractCache`

**核心方法**：
```python
def get(self, key: str) -> Any | None:
    """获取缓存值"""

def set(self, key: str, value: Any, expire_time: int) -> None:
    """设置缓存，expire_time: 过期时间（秒）"""

def keys(self, pattern: str) -> list[str]:
    """按模式获取所有键"""
```

#### 7.2.2 `cache/local_cache.py` - 本地内存缓存

**作用**：基于内存的本地缓存实现，带过期自动清理

**核心特性**：
- 字典存储，(value, expire_timestamp) 元组
- 定时清理 cron 任务（默认 10 秒间隔）
- 获取时惰性过期检查（lazy check on read）
- 支持通配符模式匹配

#### 7.2.3 `cache/redis_cache.py` - Redis 缓存（可选）

**作用**：基于 Redis 的分布式缓存

**适用场景**：
- 多进程/多机器部署
- 需要持久化存储
- 跨服务共享验证码等数据

#### 7.2.4 `cache/factory.py` - 缓存工厂

**作用**：工厂模式创建缓存实例

**核心函数**：
```python
class CacheFactory:
    @staticmethod
    def create_cache(cache_type: str = "local") -> AbstractCache:
        """创建缓存实例: local / redis"""
```

### 7.3 平台认证实现

#### 7.3.1 `platforms/xiaohongshu/auth/xhs_login.py`

**作用**：小红书平台的登录实现

**继承**：`BaseAuthenticator`

**实现方式**：
- 扫码登录：页面二维码提取 + 状态轮询
- 手机号登录：表单填写 + 验证码提交
- Cookie 登录：Cookie 注入 + 有效性验证
- 登录检测：UI 元素检测 + Cookie 双重验证

## 8. 新增文件清单

| 文件路径 | 类型 | 说明 | 优先级 |
|----------|------|------|--------|
| `sucrawler/auth/__init__.py` | 新增 | 认证模块入口 | P0 |
| `sucrawler/auth/base.py` | 新增 | 认证抽象基类 | P0 |
| `sucrawler/auth/types.py` | 新增 | 类型定义 | P0 |
| `sucrawler/auth/exceptions.py` | 新增 | 认证异常 | P0 |
| `sucrawler/auth/credential_store.py` | 新增 | 凭证存储 | P0 |
| `sucrawler/auth/cookie_utils.py` | 新增 | Cookie 工具 | P1 |
| `sucrawler/auth/qrcode.py` | 新增 | 二维码工具 | P1 |
| `sucrawler/cache/__init__.py` | 新增 | 缓存模块入口 | P0 |
| `sucrawler/cache/base.py` | 新增 | 缓存抽象基类 | P0 |
| `sucrawler/cache/local_cache.py` | 新增 | 本地内存缓存 | P0 |
| `sucrawler/cache/redis_cache.py` | 新增 | Redis 缓存（可选） | P2 |
| `sucrawler/cache/factory.py` | 新增 | 缓存工厂 | P1 |
| `sucrawler/platforms/xiaohongshu/auth/__init__.py` | 新增 | 平台认证入口 | P0 |
| `sucrawler/platforms/xiaohongshu/auth/xhs_login.py` | 新增 | 小红书登录实现 | P0 |

**共 14 个新增文件**

## 9. 修改文件清单

| 文件路径 | 修改内容 | 影响范围 |
|----------|---------|---------|
| `sucrawler/browser/cookie/cookie_manager.py` | 增强：添加有效期检测、凭证格式导出 | 低 |
| `sucrawler/browser/manager/browser_manager.py` | 增强：集成认证器，启动时自动登录 | 中 |
| `sucrawler/platforms/xiaohongshu/config.py` | 新增：login_type、credential_path 等配置 | 低 |
| `sucrawler/config/settings.py` | 新增：全局认证相关配置 | 低 |
| `sucrawler/platforms/xiaohongshu/spiders/browser_spider.py` | 增强：使用认证器管理登录态 | 中 |

**共 5 个修改文件**

## 10. 数据流程图

```
┌─────────────┐
│  配置加载    │
│  (XHSConfig)│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  BrowserManager      │
│  - 启动浏览器        │
│  - 创建 Context      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐       ┌──────────────────┐
│  XHSAuthenticator    │       │ CredentialStore  │
│  - ensure_logged_in()│──────▶│ - 加载凭证       │
│  - check_login_status│◀──────│ - 保存凭证       │
└──────┬──────────────┘       └──────────────────┘
       │
       ├── 已登录 ────────────────────────────────────────┐
       │                                                  │
       ▼                                                  ▼
┌─────────────────┐                               ┌────────────────┐
│  开始爬取        │                               │ 触发登录流程    │
│  (BrowserSpider)│                               │ (qrcode/phone) │
└─────────────────┘                               └───────┬────────┘
                                                          │
                                                          ▼
                                                    ┌───────────┐
                                                    │ 登录成功   │
                                                    └─────┬─────┘
                                                          │
                                                          ▼
                                                    ┌───────────┐
                                                    │ 保存凭证   │
                                                    └─────┬─────┘
                                                          │
                                                          ▼
                                                    ┌───────────┐
                                                    │ 开始爬取   │
                                                    └───────────┘
```

## 11. 模块依赖图

```
                    ┌──────────────┐
                    │   Browser    │
                    │   Manager    │
                    └──────┬───────┘
                           │ uses
                           ▼
┌────────────────────────────────────────────────────────────┐
│                      auth (核心认证层)                       │
│  ┌─────────┐     ┌─────────────────────┐     ┌─────────┐  │
│  │  Base   │────▶│  CredentialStore     │     │ QRCode  │  │
│  │  Auth   │     └──────────┬──────────┘     │  Util   │  │
│  └────┬────┘                │ uses           └────┬────┘  │
│       │ implements          ▼                     │       │
│       │            ┌──────────────┐               │       │
│       │            │ cookie_utils │               │       │
│       │            └──────────────┘               │       │
│       │                                           │       │
└───────┼───────────────────────────────────────────┼───────┘
        │                                           │
        ├────────────────────────────┐              │
        ▼                            ▼              │
┌──────────────┐              ┌──────────────┐     │
│  XHS Auth    │              │  DY Auth     │     │
│  (platform)  │              │  (未来)      │     │
└──────┬───────┘              └──────────────┘     │
       │                                           │
       ▼                                           │
┌──────────────┐                                   │
│    Cache     │◀──────────────────────────────────┘
│   System     │
│  (通用缓存)  │
└──────────────┘
```

## 12. 登录生命周期图

```
初始化
  │
  ▼
┌──────────────┐
│ 加载凭证      │ ◀── CredentialStore
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 检测登录状态  │
└──┬────────┬──┘
   │        │
  有效     失效
   │        │
   ▼        ▼
  成功   ┌──────────┐
   │     │ 触发登录  │
   │     └────┬─────┘
   │          │
   │    ┌─────┴─────┐
   │    ▼           ▼
   │  扫码       手机号
   │  登录        登录
   │    │           │
   │    └─────┬─────┘
   │          │
   │          ▼
   │     ┌─────────┐
   │     │ 登录成功? │
   │     └──┬───┬───┘
   │       是   否
   │       │    │
   │       ▼    ▼
   │     保存   失败
   │     凭证   (重试/报错)
   │       │
   └───────┘
          │
          ▼
   ┌──────────────┐
   │  进入爬取阶段  │
   └──────────────┘
          │
          ▼
   ┌──────────────┐
   │  爬取过程中    │
   │  定期检测登录  │
   │  状态          │
   └──────┬───────┘
          │
     被检测到失效
          │
          ▼
     重新触发登录
     （循环）
```

## 13. 分阶段开发计划

### Phase 1：基础认证框架

**目标**：建立认证模块基础设施，定义核心接口

**新增文件**：
- `auth/__init__.py`
- `auth/base.py`
- `auth/types.py`
- `auth/exceptions.py`
- `auth/cookie_utils.py`

**修改文件**：无

**风险**：🟢 低
**可独立测试**：✅ 是
**预计工作量**：1-2 天

### Phase 1.5：缓存系统

**目标**：实现通用缓存系统（本地内存缓存 + 工厂）

**新增文件**：
- `cache/__init__.py`
- `cache/base.py`
- `cache/local_cache.py`
- `cache/factory.py`

**修改文件**：无

**核心功能**：
- AbstractCache 抽象基类
- ExpiringLocalCache 带过期的本地缓存
- 定时清理 cron 任务
- CacheFactory 工厂模式

**风险**：🟢 低
**可独立测试**：✅ 是
**预计工作量**：1 天

### Phase 2：凭证存储

**目标**：实现凭证的持久化存储和管理

**新增文件**：
- `auth/credential_store.py`

**修改文件**：
- `browser/cookie/cookie_manager.py` - 增强导出/导入功能

**核心功能**：
- 凭证 JSON 文件存储
- 多平台凭证隔离
- 凭证元数据（创建时间、过期时间等）
- 凭证有效性检查

**风险**：🟢 低
**可独立测试**：✅ 是
**预计工作量**：1-2 天

### Phase 3：二维码工具

**目标**：实现二维码提取和显示功能

**新增文件**：
- `auth/qrcode.py`

**核心功能**：
- 从页面 img 元素提取二维码
- 从 canvas 元素提取二维码
- 本地弹窗显示二维码（PIL）
- base64 编解码

**风险**：🟡 中（PIL 依赖）
**可独立测试**：✅ 是
**预计工作量**：1-2 天

### Phase 4：小红书登录实现

**目标**：实现小红书平台的登录器

**新增文件**：
- `platforms/xiaohongshu/auth/__init__.py`
- `platforms/xiaohongshu/auth/xhs_login.py`

**核心功能**：
- Cookie 登录
- 扫码登录
- 手机号登录（基础版）
- 登录状态双重检测
- 登录后自动保存凭证

**风险**：🟡 中（平台 UI 可能变化）
**可独立测试**：✅ 是
**预计工作量**：3-5 天

### Phase 5：与浏览器管理器集成

**目标**：将认证器集成到 BrowserManager

**修改文件**：
- `browser/manager/browser_manager.py`
- `config/settings.py`
- `platforms/xiaohongshu/config.py`

**核心功能**：
- BrowserManager 启动时自动恢复登录态
- 提供 `ensure_logged_in()` 方法
- 爬取过程中检测登录失效并重登

**风险**：🟡 中
**可独立测试**：✅ 是
**预计工作量**：2-3 天

### Phase 6：CLI 命令增强

**目标**：提供登录管理命令

**修改文件**：
- `cli/` 相关文件
- `main.py`

**新增命令**：
- `sucrawler login --platform xhs` - 交互式登录
- `sucrawler logout --platform xhs` - 清除登录态
- `sucrawler auth-status --platform xhs` - 查看登录状态

**风险**：🟢 低
**可独立测试**：✅ 是
**预计工作量**：1-2 天

### 开发计划总览

| 阶段 | 目标 | 新增文件 | 修改文件 | 风险 | 预计工作量 |
|------|------|---------|---------|------|-----------|
| Phase 1 | 基础认证框架 | 5 | 0 | 🟢 低 | 1-2 天 |
| Phase 1.5 | 缓存系统 | 4 | 0 | 🟢 低 | 1 天 |
| Phase 2 | 凭证存储 | 1 | 1 | 🟢 低 | 1-2 天 |
| Phase 3 | 二维码工具 | 1 | 0 | 🟡 中 | 1-2 天 |
| Phase 4 | 小红书登录实现 | 2 | 0 | 🟡 中 | 3-5 天 |
| Phase 5 | 浏览器管理器集成 | 0 | 3 | 🟡 中 | 2-3 天 |
| Phase 6 | CLI 命令增强 | 0 | 2 | 🟢 低 | 1-2 天 |
| **总计** | | **13** | **6** | | **10-17 天** |

## 14. 配置设计

### 14.1 全局配置（BrowserConfig 增强）

```python
class BrowserConfig:
    # ... 现有配置 ...

    # 登录相关
    auto_login: bool = True              # 启动时自动登录
    login_type: str = "qrcode"           # 登录方式: qrcode/phone/cookie
    credential_dir: str = ""             # 凭证存储目录（默认 ~/.sucrawler/credentials）
    login_timeout: int = 300             # 登录超时时间（秒）
    save_credentials: bool = True        # 是否自动保存凭证
```

### 14.2 平台配置（XHSConfig 增强）

```python
class XHSConfig:
    # ... 现有配置 ...

    use_browser: bool = False
    browser: BrowserConfig = ...

    # 登录相关
    login_phone: str = ""                # 登录手机号
    login_cookie: str = ""               # Cookie 登录内容
```

## 15. 关键设计决策

### 15.1 持久化方案选择

**方案对比**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **Cookie JSON 文件** | 简单、透明、可手动编辑 | 仅保存 Cookie，无 LocalStorage 等 |
| **Playwright persistent_context** | 完整浏览器状态（含扩展、历史等） | 数据量大，不可手动编辑 |
| **两者结合** | 灵活，可按需选择 | 复杂度高 |

**决策**：采用 **Cookie JSON 文件 + 可选 persistent_context** 双模式

- 默认使用 Cookie JSON 文件（轻量、可控）
- 高级用户可配置使用 persistent_context（完整）

### 15.2 登录触发时机

**方案**：
1. 启动时从存储加载凭证
2. 检测登录状态
3. 未登录/已失效 → 触发登录
4. 登录成功 → 保存凭证 → 继续爬取
5. 爬取过程中定期检测

### 15.3 平台扩展方式

**方案**：平台注册机制（类似现有 Platform 注册）

```python
@register_authenticator("xiaohongshu")
class XHSAuthenticator(BaseAuthenticator):
    ...
```

## 16. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 平台 UI 变更导致选择器失效 | 登录功能不可用 | 1. 关键选择器配置化<br>2. 提供 fallback 方案（Cookie 导入）<br>3. 完善错误提示 |
| 二维码扫描超时 | 用户体验差 | 1. 二维码过期自动刷新<br>2. 明确的超时提示 |
| 凭证泄露 | 安全风险 | 1. 文件权限控制<br>2. 可选加密存储<br>3. 文档提示安全风险 |
| 登录态频繁失效 | 爬取中断 | 1. 爬取前检测状态<br>2. 失败自动重试登录<br>3. 合理的重试间隔 |

## 17. 后续开发建议

1. **优先实现 Phase 1 + Phase 1.5**：认证框架 + 缓存系统，都是基础能力，风险低、价值高
2. **缓存系统先行**：缓存不仅用于登录，后续代理、限流等都需要，基础设施先搭好
3. **Cookie 登录先行**：先实现 Cookie 导入登录，最简单实用
4. **扫码登录优先于手机号登录**：手机号登录依赖短信转发系统，复杂度高，优先级可降低
5. **CLI 辅助工具**：独立的 login 命令便于测试和日常使用
6. **多平台验证**：在 2-3 个平台上验证抽象设计的合理性
7. **监控与日志**：完善认证流程的日志记录，便于排查问题
8. **Redis 缓存按需添加**：本地缓存满足大部分场景，Redis 等有多进程需求时再加

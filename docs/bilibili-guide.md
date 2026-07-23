# 哔哩哔哩 (Bilibili) 使用指南

> 返回 [README](../README.md)

## 概述

Sucrawler 内置哔哩哔哩 (B 站) 平台实现，支持爬取 UP 主信息和视频列表，并可选下载视频和封面图片。

B 站平台**默认使用浏览器模式 (CDP)** 爬取，也支持纯 HTTP 模式（需 Cookie）。

## 支持功能

- **UP 主信息** - 获取 UP 主基本信息（昵称、头像、签名、粉丝数、关注数、等级等）
- **视频列表** - 获取 UP 主发布的全部视频（支持分页遍历）
- **视频详情** - 获取单个视频的详细信息（播放量、弹幕、点赞、投币、收藏、分享等）
- **视频标签** - 获取视频的标签信息
- **关键词搜索** - 按关键词搜索视频
- **评论爬取** - 获取视频评论列表
- **媒体下载** - 下载视频文件和封面图片

## 快速开始

### 基本爬取

```bash
# 通过 UP 主主页 URL 爬取（自动识别 B 站平台）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678"

# 通过用户 ID (mid) 爬取（需指定平台）
uv run sucrawler crawl-user --platform bilibili --user-id 12345678

# 指定爬取视频数量（0 表示全部爬取）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --max-notes 100

# 输出到 JSON 文件
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --output ./output/bili_user.json

# 指定 Cookie（可选，用于获取更高的访问权限）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --cookie "your_cookie_here"
```

支持的 B 站 URL 格式：
- `https://space.bilibili.com/{mid}`
- `https://www.bilibili.com/{mid}`

### 下载视频和封面图片

使用 `--download` 参数控制媒体下载行为：

```bash
# 下载视频和封面图片（全部）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --download

# 仅下载视频
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --download video

# 仅下载封面图片
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --download image
```

| 参数 | 说明 |
|------|------|
| `--download` | 不跟值，默认下载视频和封面图片 |
| `--download video` | 仅下载视频 |
| `--download image` | 仅下载封面图片 |
| `--download all` | 下载视频和封面图片（同 `--download`） |
| 不指定 `--download` | 不下载任何媒体文件（默认行为） |

#### 下载依赖

- **yt-dlp**（视频下载）：`pip install yt-dlp` 或 `brew install yt-dlp`
- **ffmpeg**（可选，yt-dlp 合并音视频流时需要）：`brew install ffmpeg`

#### 下载目录结构

爬取结果默认保存到 `output/bilibili/{UP主昵称}/` 目录下：

```
output/bilibili/{UP主昵称}/
├── {UP主昵称}.json     # 完整爬取结果（JSON 格式）
├── {UP主昵称}.csv      # 视频列表（CSV 格式）
├── video/              # 视频文件（--download video/all 时生成）
│   ├── BV1xxx.mp4
│   └── BV1yyy.mp4
└── image/              # 封面图片（--download image/all 时生成）
    ├── BV1xxx.jpg
    └── BV1yyy.jpg
```

## 爬取模式

### 浏览器模式（默认）

B 站默认使用浏览器模式 (CDP) 爬取，反检测能力更强：

```bash
# 默认浏览器模式（推荐）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678"

# 无头模式（不显示浏览器窗口）
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --headless

# 连接已有浏览器（需先以调试模式启动 Chrome）
# google-chrome --remote-debugging-port=9222
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --connect-existing
```

浏览器模式特点：
- 通过 CDP 连接 Chrome 浏览器，模拟真实用户行为
- 支持自动登录检测（检查 SESSDATA cookie）
- 通过网络拦截捕获 API 响应，避免直接调用 API 被风控
- 访问视频详情页补充标签、统计数据等信息

### 纯 HTTP 模式

如不需要浏览器，可使用 `--no-browser` 切换为纯 HTTP 模式：

```bash
uv run sucrawler crawl-user --url "https://space.bilibili.com/12345678" --no-browser --cookie "your_cookie_here"
```

> 纯 HTTP 模式需要提供 Cookie，部分接口可能需要 WBI 签名。

## 数据字段说明

爬取的视频数据 (`BiliVideoItem`) 包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `bvid` | str | 视频 BV 号 |
| `aid` | int | 视频 AV 号 |
| `title` | str | 视频标题 |
| `description` | str | 视频简介 |
| `pic` | str | 封面图片 URL |
| `play` | int | 播放量 |
| `danmaku` | int | 弹幕数 |
| `comment` | int | 评论数 |
| `like` | int | 点赞数 |
| `coin` | int | 投币数 |
| `collect` | int | 收藏数 |
| `share` | int | 分享数 |
| `duration` | int | 时长（秒） |
| `pubdate` | int | 发布时间（Unix 时间戳） |
| `mid` | str | UP 主 ID |
| `author` | str | UP 主名称 |
| `tags` | list[str] | 视频标签 |
| `tname` | str | 分区名称 |
| `video_url` | str | 视频页面 URL（可在浏览器中直接访问） |

## 配置

B 站平台配置示例（`config/base.yaml`）：

```yaml
platforms:
  bilibili:
    enabled: true
    base_url: https://www.bilibili.com
    api_url: https://api.bilibili.com
    cookie: "your_cookie_here"
    sessdata: "your_sessdata_here"
    bili_jct: "your_bili_jct_here"
    rate_limit: 1.0
    user_agent: "Mozilla/5.0 ..."
```

> Cookie 和 SESSDATA 为可选配置，配置后可获得更高的访问权限和更完整的数据。

## 完整参数列表

`crawl-user` 命令在 B 站平台下的常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--url, -u` | UP 主主页 URL | - |
| `--user-id` | UP 主用户 ID (mid) | - |
| `--platform, -p` | 平台名称 | xiaohongshu |
| `--max-notes, -n` | 爬取视频数量上限 (0=全部) | 0 |
| `--output, -o` | 输出 JSON 文件路径 | - |
| `--cookie` | Cookie 字符串 | - |
| `--download` | 下载媒体 (video/image/all) | 不下载 |
| `--browser` | 使用浏览器模式 | B站默认启用 |
| `--no-browser` | 禁用浏览器模式 | false |
| `--headless` | 浏览器无头模式 | false |
| `--connect-existing` | 连接已有浏览器 | false |
| `--debug-port` | 已有浏览器调试端口 | 9222 |
| `--no-save` | 不保存结果到文件 | false |
| `--env, -e` | 运行环境 | dev |

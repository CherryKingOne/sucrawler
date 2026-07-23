from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from loguru import logger

from sucrawler.core.base import BaseParserImpl
from sucrawler.core.response import Response


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}


def _parse_duration_str(duration_str: str) -> int:
    """将 'MM:SS' 或 'HH:MM:SS' 格式转换为秒。"""
    parts = duration_str.strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0


def _parse_iso_duration(iso_str: str) -> int:
    """将 ISO 8601 时长 (PT00H04M18S) 转换为秒。"""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_str)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


class BiliParser(BaseParserImpl):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

    async def _do_parse(self, response: Response) -> dict[str, Any]:
        logger.debug(f"Parsing response from {response.request.url}")
        try:
            json_data = response.json()
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return {"raw": response.text}

        if not isinstance(json_data, dict):
            return {"data": json_data}

        return json_data

    def parse_user(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing user data")
        user_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(user_data, dict):
            result["mid"] = str(
                user_data.get("mid", user_data.get("id", "")),
            )
            result["name"] = str(
                user_data.get("name", user_data.get("uname", "")),
            )
            face = user_data.get("face", user_data.get("avatar", ""))
            result["avatar"] = str(face) if face else ""
            result["sign"] = str(
                user_data.get("sign", user_data.get("description", "")),
            )
            result["sex"] = str(user_data.get("sex", ""))
            result["level"] = _safe_int(user_data.get("level"), 0)

            fans_info = user_data.get("fans", 0)
            if isinstance(fans_info, dict):
                result["fans"] = _safe_int(fans_info.get("total"), 0)
            else:
                result["fans"] = _safe_int(fans_info, 0)

            following = user_data.get("following", 0)
            if isinstance(following, dict):
                result["following"] = _safe_int(following.get("total"), 0)
            else:
                result["following"] = _safe_int(following, 0)

            result["video_count"] = _safe_int(
                user_data.get("video", user_data.get("archive_count", 0)),
                0,
            )
            result["likes"] = _safe_int(user_data.get("likes", 0), 0)
            result["archive_count"] = _safe_int(
                user_data.get("archive_count", 0),
                0,
            )

        result["raw_data"] = data
        return result

    def parse_video(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing video data")
        video_data = _safe_dict(data.get("data", data))
        result: dict[str, Any] = {}

        if isinstance(video_data, dict):
            result["bvid"] = str(video_data.get("bvid", ""))
            result["aid"] = _safe_int(video_data.get("aid"), 0)
            result["title"] = str(video_data.get("title", ""))
            result["description"] = str(
                video_data.get("description", video_data.get("desc", "")),
            )
            result["pic"] = str(video_data.get("pic", ""))

            # 支持「详情格式」(stat 嵌套) 和「列表格式」(扁平) 两种
            stat = _safe_dict(video_data.get("stat", {}))
            if stat:
                result["play"] = _safe_int(stat.get("view"), 0)
                result["danmaku"] = _safe_int(stat.get("danmaku"), 0)
                result["comment"] = _safe_int(stat.get("reply"), 0)
                result["like"] = _safe_int(stat.get("like"), 0)
                result["coin"] = _safe_int(stat.get("coin"), 0)
                result["collect"] = _safe_int(stat.get("favorite"), 0)
                result["share"] = _safe_int(stat.get("share"), 0)
            else:
                # 列表 API 扁平格式
                result["play"] = _safe_int(video_data.get("play"), 0)
                result["danmaku"] = _safe_int(
                    video_data.get("video_review", video_data.get("danmaku")), 0,
                )
                result["comment"] = _safe_int(video_data.get("comment"), 0)
                result["like"] = _safe_int(video_data.get("like"), 0)
                result["coin"] = _safe_int(video_data.get("coin"), 0)
                result["collect"] = _safe_int(video_data.get("collect"), 0)
                result["share"] = _safe_int(video_data.get("share"), 0)

            # duration: 详情格式是 int 秒，列表格式是字符串 "05:43" (字段名为 length)
            duration_val = video_data.get("duration", video_data.get("length", 0))
            if isinstance(duration_val, str):
                result["duration"] = _parse_duration_str(duration_val)
            else:
                result["duration"] = _safe_int(duration_val, 0)

            # pubdate: 详情格式是 pubdate，列表格式是 created
            result["pubdate"] = _safe_int(
                video_data.get("pubdate", video_data.get("created", 0)), 0,
            )

            # owner: 详情格式嵌套，列表格式扁平
            owner = _safe_dict(video_data.get("owner", {}))
            if owner:
                result["mid"] = str(owner.get("mid", ""))
                result["author"] = str(owner.get("name", ""))
            else:
                result["mid"] = str(video_data.get("mid", ""))
                result["author"] = str(video_data.get("author", ""))

            tname = video_data.get("tname", video_data.get("typename", ""))
            result["tname"] = str(tname) if tname else ""

            tag_list = _safe_list(video_data.get("tags", []))
            result["tags"] = [
                str(tag.get("tag_name", tag)) if isinstance(tag, dict) else str(tag)
                for tag in tag_list
            ]

            # 视频页面 URL（可在浏览器中直接访问查看）
            bvid_str = result.get("bvid", "")
            if bvid_str:
                result["video_url"] = f"https://www.bilibili.com/video/{bvid_str}"

        result["raw_data"] = data
        return result

    def parse_video_detail_page(self, html: str, bvid: str = "") -> dict[str, Any]:
        """解析 Bilibili 视频详情页 HTML，提取标签、统计数据等。

        Args:
            html: 视频详情页 HTML 内容
            bvid: 视频 BV 号，用于构造浏览器可访问的视频页面 URL
        """
        result: dict[str, Any] = {"tags": [], "play": 0, "like": 0, "coin": 0,
                                  "collect": 0, "share": 0, "danmaku": 0,
                                  "comment": 0, "duration": 0, "pubdate": 0,
                                  "video_url": "", "audio_urls": []}

        # 1. 从 <meta itemprop="keywords"> 提取标签
        keywords_match = re.search(
            r'<meta[^>]+itemprop="keywords"[^>]+content="([^"]+)"', html,
        )
        if keywords_match:
            keywords = keywords_match.group(1).split(",")
            # 第一个是视频标题，最后几个是 哔哩哔哩/bilibili/B站/弹幕
            raw_tags = [
                k.strip() for k in keywords
                if k.strip() and k.strip() not in ("哔哩哔哩", "bilibili", "B站", "弹幕")
            ]
            # 跳过第一个（视频标题本身）
            if raw_tags:
                result["tags"] = raw_tags[1:] if len(raw_tags) > 1 else raw_tags

        # 2. 从 <meta itemprop="description"> 提取统计数据
        desc_match = re.search(
            r'<meta[^>]+itemprop="description"[^>]+content="([^"]+)"', html,
        )
        if desc_match:
            desc_text = desc_match.group(1)
            result["description"] = desc_text.split(",")[0].strip()
            # 解析: 视频播放量 219683、弹幕量 90、点赞数 22007、投硬币枚数 1306、收藏人数 22521、转发人数 547
            stat_patterns = {
                "play": r"视频播放量\s*(\d+)",
                "danmaku": r"弹幕量\s*(\d+)",
                "like": r"点赞数\s*(\d+)",
                "coin": r"投硬币枚数\s*(\d+)",
                "collect": r"收藏人数\s*(\d+)",
                "share": r"转发人数\s*(\d+)",
            }
            for field, pattern in stat_patterns.items():
                m = re.search(pattern, desc_text)
                if m:
                    result[field] = int(m.group(1))

        # 3. 从 <script type="application/ld+json"> 提取结构化数据
        ld_json_match = re.search(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if ld_json_match:
            try:
                import json
                ld_data = json.loads(ld_json_match.group(1))
                # interactionStatistic -> view / like / comment
                for stat_item in ld_data.get("interactionStatistic", []):
                    interaction_type = (
                        stat_item.get("interactionType", {}).get("@type", "")
                    )
                    count = int(stat_item.get("userInteractionCount", 0))
                    if interaction_type == "WatchAction":
                        result["play"] = count
                    elif interaction_type == "LikeAction":
                        result["like"] = count
                    elif interaction_type == "CommentAction":
                        result["comment"] = count
                # duration: PT00H04M18S -> 258
                duration_str = ld_data.get("duration", "")
                if duration_str:
                    result["duration"] = _parse_iso_duration(duration_str)
                # uploadDate
                upload_date = ld_data.get("uploadDate", "")
                if upload_date:
                    try:
                        dt = datetime.fromisoformat(
                            upload_date.replace("Z", "+00:00")
                        )
                        result["pubdate"] = int(dt.timestamp())
                    except (ValueError, TypeError):
                        pass
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Failed to parse ld+json: {e}")

        # 4. 构造浏览器可访问的视频页面 URL
        if bvid:
            result["video_url"] = f"https://www.bilibili.com/video/{bvid}"

        # 5. 从 <meta itemprop="uploadDate"> 提取发布日期（备用）
        if not result["pubdate"]:
            upload_match = re.search(
                r'<meta[^>]+itemprop="uploadDate"[^>]+content="([^"]+)"', html,
            )
            if upload_match:
                try:
                    dt = datetime.strptime(upload_match.group(1), "%Y-%m-%d %H:%M:%S")
                    result["pubdate"] = int(dt.timestamp())
                except ValueError:
                    pass

        return result

    def parse_comment(self, data: dict[str, Any]) -> dict[str, Any]:
        logger.debug("Parsing comment data")
        result: dict[str, Any] = {}

        if isinstance(data, dict):
            result["rpid"] = str(data.get("rpid", data.get("id", "")))
            result["oid"] = str(data.get("oid", ""))
            result["type"] = _safe_int(data.get("type"), 1)
            result["message"] = str(
                data.get("content", {}).get("message", "")
                if isinstance(data.get("content"), dict)
                else data.get("content", ""),
            )
            member = _safe_dict(data.get("member", {}))
            result["mid"] = str(member.get("mid", ""))
            result["name"] = str(member.get("uname", ""))
            result["avatar"] = str(member.get("avatar", ""))
            result["like"] = _safe_int(data.get("like"), 0)
            result["rcount"] = _safe_int(data.get("rcount"), 0)
            result["ctime"] = _safe_int(data.get("ctime"), 0)

            if result["ctime"]:
                result["created_at"] = datetime.fromtimestamp(result["ctime"])
            else:
                result["created_at"] = datetime.now()

        result["raw_data"] = data
        return result

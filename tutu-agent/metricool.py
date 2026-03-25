"""
Metricool API Integration for Imani
Pulls real analytics from Instagram, Twitter/X, TikTok, and LinkedIn.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://app.metricool.com/api"


class MetricoolClient:
    """Client for the Metricool API. Requires Advanced or Custom plan."""

    def __init__(self):
        self.user_token = os.getenv("METRICOOL_USER_TOKEN", "")
        self.user_id = os.getenv("METRICOOL_USER_ID", "")
        self.blog_id = os.getenv("METRICOOL_BLOG_ID", "")
        self._client = httpx.AsyncClient(timeout=30.0)

    def is_connected(self) -> bool:
        return bool(self.user_token and self.user_id and self.blog_id)

    def _headers(self) -> dict:
        return {"X-Mc-Auth": self.user_token}

    def _base_params(self) -> dict:
        return {"userId": self.user_id, "blogId": self.blog_id}

    def _date_range(self, days: int = 7) -> tuple[str, str]:
        """Return (start, end) in YYYYMMDD format."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")

    async def _get(self, path: str, extra_params: Optional[dict] = None) -> dict | list | None:
        """Make an authenticated GET request."""
        if not self.is_connected():
            logger.warning("Metricool not configured. Skipping API call to %s", path)
            return None
        params = self._base_params()
        if extra_params:
            params.update(extra_params)
        try:
            resp = await self._client.get(
                f"{BASE_URL}{path}",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error("Metricool API error %s: %s", e.response.status_code, e.response.text[:200])
            return None
        except Exception as e:
            logger.error("Metricool request failed: %s", e)
            return None

    # ------------------------------------------------------------------
    # Instagram
    # ------------------------------------------------------------------
    async def instagram_posts(self, days: int = 30, sort: str = "published") -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/instagram/posts", {"start": start, "end": end, "sortcolumn": sort})
        return data if isinstance(data, list) else []

    async def instagram_reels(self, days: int = 30, sort: str = "published") -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/instagram/reels", {"start": start, "end": end, "sortcolumn": sort})
        return data if isinstance(data, list) else []

    async def instagram_stories(self, days: int = 30) -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/instagram/stories", {"start": start, "end": end, "sortcolumn": "published"})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Twitter / X
    # ------------------------------------------------------------------
    async def twitter_posts(self, days: int = 30, sort: str = "created") -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/twitter/posts", {"start": start, "end": end, "sortcolumn": sort})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # TikTok
    # ------------------------------------------------------------------
    async def tiktok_posts(self, days: int = 30) -> list:
        """TikTok post analytics. Metricool exposes campaigns; we also try posts."""
        start, end = self._date_range(days)
        # Try the posts endpoint first; fall back to campaigns
        data = await self._get("/stats/tiktok/posts", {"start": start, "end": end, "sortcolumn": "published"})
        if data is None:
            data = await self._get("/stats/tiktokads/campaigns", {"start": start, "end": end})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # YouTube
    # ------------------------------------------------------------------
    async def youtube_posts(self, days: int = 30, sort: str = "published") -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/youtube/posts", {"start": start, "end": end, "sortcolumn": sort})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # LinkedIn
    # ------------------------------------------------------------------
    async def linkedin_posts(self, days: int = 30, sort: str = "likes") -> list:
        start, end = self._date_range(days)
        data = await self._get("/stats/linkedin/posts", {"start": start, "end": end, "sortcolumn": sort})
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # Cross-platform timeline metrics
    # ------------------------------------------------------------------
    async def timeline(self, metric: str, days: int = 7) -> list:
        """
        Fetch time-series data for a single metric.
        Examples: igFollowers, igEngagement, twitterFollowers, inFollowers
        """
        start, end = self._date_range(days)
        data = await self._get(f"/stats/timeline/{metric}", {"start": start, "end": end})
        return data if isinstance(data, list) else []

    async def aggregations(self, category: str) -> dict | None:
        """
        Fetch aggregated metrics for a category.
        Categories: Instagram, Twitter, Facebook, LinkedIn, Contents, Audience
        """
        data = await self._get(f"/stats/aggregations/{category}")
        return data if isinstance(data, dict) else None

    # ------------------------------------------------------------------
    # Audience demographics
    # ------------------------------------------------------------------
    async def audience_country(self, provider: str = "instagram") -> list:
        data = await self._get(f"/stats/country/{provider}")
        return data if isinstance(data, list) else []

    async def audience_gender(self, provider: str = "instagram") -> list:
        data = await self._get(f"/stats/gender/{provider}")
        return data if isinstance(data, list) else []

    async def audience_age(self, provider: str = "instagram") -> list:
        data = await self._get(f"/stats/age/{provider}")
        return data if isinstance(data, list) else []

    # ------------------------------------------------------------------
    # High-level dashboard data (consumed by Imani's dashboard)
    # ------------------------------------------------------------------
    async def dashboard_overview(self, days: int = 7) -> dict:
        """
        Pull a combined overview for the Imani dashboard.
        Returns structured data for all four platforms.
        """
        ig_agg = await self.aggregations("Instagram")
        tw_agg = await self.aggregations("Twitter")
        li_agg = await self.aggregations("LinkedIn")
        yt_agg = await self.aggregations("Youtube")

        # Timeline data for charts
        ig_reach = await self.timeline("igImpressions", days)
        tw_impressions = await self.timeline("twImpressions", days)
        li_impressions = await self.timeline("inImpressions", days)
        yt_views = await self.timeline("ytViews", days)

        # Recent posts
        ig_posts = await self.instagram_posts(days=days, sort="published")
        tw_posts = await self.twitter_posts(days=days, sort="created")
        tt_posts = await self.tiktok_posts(days=days)
        li_posts = await self.linkedin_posts(days=days, sort="likes")
        yt_posts = await self.youtube_posts(days=days, sort="published")

        return {
            "aggregations": {
                "instagram": ig_agg,
                "twitter": tw_agg,
                "linkedin": li_agg,
                "youtube": yt_agg,
            },
            "timeline": {
                "instagram_reach": _format_timeline(ig_reach),
                "twitter_impressions": _format_timeline(tw_impressions),
                "linkedin_impressions": _format_timeline(li_impressions),
                "youtube_views": _format_timeline(yt_views),
            },
            "posts": {
                "instagram": _format_ig_posts(ig_posts),
                "twitter": _format_tw_posts(tw_posts),
                "tiktok": _format_tt_posts(tt_posts),
                "linkedin": _format_li_posts(li_posts),
                "youtube": _format_yt_posts(yt_posts),
            },
        }

    async def instagram_profile(self) -> dict | None:
        """Fetch Instagram profile/account data for follower count."""
        data = await self._get("/stats/instagram/profile")
        if data is None:
            # Try alternative endpoints
            data = await self._get("/stats/instagram/community")
        return data if isinstance(data, dict) else None

    def _compute_stats_from_posts(self, posts: list, reels: list = None) -> dict:
        """Compute engagement stats from actual post data when aggregations are null."""
        all_posts = list(posts or [])
        if reels:
            all_posts.extend(reels)

        if not all_posts:
            return {}

        total_likes = sum(_safe_int(p.get("likes", 0)) for p in all_posts)
        total_comments = sum(_safe_int(p.get("comments", 0)) for p in all_posts)
        total_reach = sum(_safe_int(p.get("reach", 0)) for p in all_posts)
        total_engagement = total_likes + total_comments
        avg_engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0

        return {
            "posts_count": len(all_posts),
            "total_engagement": total_engagement,
            "total_reach": total_reach,
            "avg_engagement_rate": round(avg_engagement_rate, 1),
            "total_likes": total_likes,
            "total_comments": total_comments,
        }

    async def platform_detail(self, platform: str, days: int = 30) -> dict:
        """Fetch detailed data for a single platform page."""
        if platform == "instagram":
            posts = await self.instagram_posts(days=days)
            reels = await self.instagram_reels(days=days)
            stories = await self.instagram_stories(days=days)
            agg = await self.aggregations("Instagram")
            computed = self._compute_stats_from_posts(posts, reels)
            # Try to get follower count from profile if aggregation is null
            if not agg:
                profile = await self.instagram_profile()
                if profile and isinstance(profile, dict):
                    computed["followers"] = _safe_int(profile.get("followers", 0) or profile.get("followedBy", 0))
            return {
                "aggregation": agg,
                "computed_stats": computed,
                "posts": _format_ig_posts(posts),
                "reels": _format_ig_posts(reels),
                "stories": _format_ig_stories(stories),
            }
        elif platform == "twitter":
            posts = await self.twitter_posts(days=days)
            agg = await self.aggregations("Twitter")
            computed = self._compute_stats_from_posts(posts)
            return {"aggregation": agg, "computed_stats": computed, "posts": _format_tw_posts(posts)}
        elif platform == "tiktok":
            posts = await self.tiktok_posts(days=days)
            computed = self._compute_stats_from_posts(posts)
            return {"computed_stats": computed, "posts": _format_tt_posts(posts)}
        elif platform == "youtube":
            posts = await self.youtube_posts(days=days)
            agg = await self.aggregations("Youtube")
            computed = self._compute_stats_from_posts(posts)
            return {"aggregation": agg, "computed_stats": computed, "posts": _format_yt_posts(posts)}
        elif platform == "linkedin":
            posts = await self.linkedin_posts(days=days)
            agg = await self.aggregations("LinkedIn")
            computed = self._compute_stats_from_posts(posts)
            return {"aggregation": agg, "computed_stats": computed, "posts": _format_li_posts(posts)}
        return {}

    async def close(self):
        await self._client.aclose()


# ------------------------------------------------------------------
# Formatting helpers (normalize Metricool's response into dashboard shape)
# ------------------------------------------------------------------

def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _safe_str(val, default=""):
    return str(val) if val is not None else default


def _format_date(raw) -> str:
    """Try to parse various date formats from Metricool into 'Mar 19, 2026' style."""
    if not raw:
        return ""
    if isinstance(raw, (int, float)):
        # Unix timestamp in milliseconds
        try:
            dt = datetime.utcfromtimestamp(raw / 1000 if raw > 1e12 else raw)
            return dt.strftime("%b %d, %Y")
        except Exception:
            return str(raw)
    if isinstance(raw, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(raw[:19], fmt).strftime("%b %d, %Y")
            except ValueError:
                continue
    return str(raw)


def _post_status(raw_date) -> str:
    """Determine if a post is published or scheduled based on date."""
    if not raw_date:
        return "draft"
    try:
        if isinstance(raw_date, (int, float)):
            ts = raw_date / 1000 if raw_date > 1e12 else raw_date
            dt = datetime.utcfromtimestamp(ts)
        elif isinstance(raw_date, str):
            dt = datetime.strptime(raw_date[:19], "%Y-%m-%dT%H:%M:%S")
        else:
            return "published"
        return "scheduled" if dt > datetime.utcnow() else "published"
    except Exception:
        return "published"


def _extract_title(p: dict, fallback: str = "Untitled post") -> str:
    """Try multiple field names to find a usable post title/caption."""
    for field in ("caption", "text", "description", "message", "title", "name", "commentary"):
        val = p.get(field)
        if val and isinstance(val, str) and val.strip():
            # Take first line, truncate to 80 chars
            first_line = val.strip().split("\n")[0]
            return first_line[:80] if len(first_line) > 80 else first_line
    # If no caption found, generate a descriptive title from type + date
    pub = p.get("published") or p.get("created") or p.get("date")
    post_type = "Reel" if p.get("mediaType") == "VIDEO" or p.get("type") == "reel" else "Post"
    date_str = _format_date(pub)
    if date_str:
        return f"{post_type} — {date_str}"
    return fallback


def _format_ig_posts(posts: list) -> list:
    out = []
    for p in posts[:20]:
        engagement = _safe_int(p.get("likes", 0)) + _safe_int(p.get("comments", 0))
        pub = p.get("published") or p.get("created") or p.get("date")
        post_type = "Reel" if p.get("mediaType") == "VIDEO" or p.get("type") == "reel" else "Post"
        out.append({
            "title": _extract_title(p, "Untitled post"),
            "type": post_type,
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(engagement),
            "likes": _safe_int(p.get("likes")),
            "comments": _safe_int(p.get("comments")),
            "reach": _safe_int(p.get("reach")),
            "impressions": _safe_int(p.get("impressions")),
        })
    return out


def _format_ig_stories(stories: list) -> list:
    out = []
    for s in stories[:20]:
        pub = s.get("published") or s.get("date")
        out.append({
            "title": "Story",
            "type": "Story",
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(_safe_int(s.get("impressions", 0))),
            "reach": _safe_int(s.get("reach")),
            "impressions": _safe_int(s.get("impressions")),
            "replies": _safe_int(s.get("replies")),
        })
    return out


def _format_tw_posts(posts: list) -> list:
    out = []
    for p in posts[:20]:
        engagement = _safe_int(p.get("favorites", 0)) + _safe_int(p.get("retweets", 0))
        pub = p.get("created") or p.get("published") or p.get("date")
        text = _safe_str(p.get("text", ""))
        is_thread = len(text) > 280 or p.get("type") == "thread"
        out.append({
            "title": _extract_title(p, "Untitled tweet"),
            "type": "Thread" if is_thread else "Post",
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(engagement),
            "favorites": _safe_int(p.get("favorites")),
            "retweets": _safe_int(p.get("retweets")),
        })
    return out


def _format_tt_posts(posts: list) -> list:
    out = []
    for p in posts[:20]:
        views = _safe_int(p.get("videoViews", 0)) or _safe_int(p.get("views", 0))
        pub = p.get("published") or p.get("created") or p.get("date")
        out.append({
            "title": _extract_title(p, "Untitled video"),
            "type": "Video",
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(views),
            "views": views,
        })
    return out


def _format_yt_posts(posts: list) -> list:
    out = []
    for p in posts[:20]:
        views = _safe_int(p.get("views", 0)) or _safe_int(p.get("videoViews", 0))
        likes = _safe_int(p.get("likes", 0))
        comments = _safe_int(p.get("comments", 0))
        engagement = likes + comments
        pub = p.get("published") or p.get("created") or p.get("date")
        out.append({
            "title": _extract_title(p, "Untitled video"),
            "type": "Video",
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(engagement),
            "views": views,
            "likes": likes,
            "comments": comments,
        })
    return out


def _format_li_posts(posts: list) -> list:
    out = []
    for p in posts[:20]:
        engagement = _safe_int(p.get("likes", 0)) + _safe_int(p.get("comments", 0))
        pub = p.get("published") or p.get("created") or p.get("date")
        text = _safe_str(p.get("text", "") or p.get("commentary", ""))
        is_article = p.get("type") == "article" or len(text) > 500
        out.append({
            "title": _extract_title(p, "Untitled post"),
            "type": "Article" if is_article else "Post",
            "date": _format_date(pub),
            "status": _post_status(pub),
            "engagement": _format_number(engagement),
            "likes": _safe_int(p.get("likes")),
            "comments": _safe_int(p.get("comments")),
            "impressions": _safe_int(p.get("impressions")),
        })
    return out


def _format_timeline(data: list) -> list:
    """Normalize timeline data into [{label, value}] for charts."""
    out = []
    for point in data[:30]:
        if isinstance(point, dict):
            label = point.get("date", "") or point.get("label", "")
            value = _safe_int(point.get("value", 0) or point.get("total", 0))
            out.append({"label": _format_date(label) if label else "", "value": value})
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            out.append({"label": str(point[0]), "value": _safe_int(point[1])})
    return out


def _format_number(n: int) -> str:
    """Format numbers like 1200 -> '1.2K'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)

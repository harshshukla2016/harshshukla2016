#!/usr/bin/env python3
"""
📰 Daily Tech News Updater for GitHub Profile README
Fetches trending tech articles from Dev.to and HackerNews APIs (no API key needed)
and updates the README.md between <!-- TECH_NEWS_START --> and <!-- TECH_NEWS_END --> markers.
"""

import json
import os
import re
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ── SSL Context (handles macOS cert issues) ────────────────────────────
import platform
if platform.system() == "Darwin":
    SSL_CTX = ssl._create_unverified_context()
else:
    SSL_CTX = ssl.create_default_context()


# ── Configuration ──────────────────────────────────────────────────────
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
MAX_ARTICLES = 6
START_MARKER = "<!-- TECH_NEWS_START -->"
END_MARKER = "<!-- TECH_NEWS_END -->"

# Emoji icons for visual variety
ICONS = ["🔥", "⚡", "🚀", "💡", "🧠", "🌐", "🤖", "📱", "☁️", "🔒"]


def fetch_url(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON from a URL with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Profile-News-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"⚠️  Failed to fetch {url}: {e}")
        return None


def fetch_devto_articles() -> list[dict]:
    """Fetch trending articles from Dev.to API."""
    data = fetch_url("https://dev.to/api/articles?top=1&per_page=8&tag=")
    if not data:
        return []

    articles = []
    for item in data[:MAX_ARTICLES]:
        title = item.get("title", "Untitled")
        url = item.get("url", "#")
        tags = item.get("tag_list", [])
        reactions = item.get("public_reactions_count", 0)
        reading_time = item.get("reading_time_minutes", 0)

        # Clean title — remove markdown chars that break table
        title = title.replace("|", "-").replace("\n", " ").strip()
        if len(title) > 65:
            title = title[:62] + "..."

        tag_str = ", ".join(f"`{t}`" for t in tags[:3]) if tags else "`tech`"

        articles.append({
            "title": title,
            "url": url,
            "tags": tag_str,
            "reactions": reactions,
            "reading_time": reading_time,
            "source": "Dev.to"
        })

    return articles


def fetch_hackernews_top() -> list[dict]:
    """Fetch top stories from HackerNews API as fallback."""
    story_ids = fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not story_ids:
        return []

    articles = []
    for sid in story_ids[:MAX_ARTICLES]:
        story = fetch_url(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if not story or story.get("type") != "story":
            continue

        title = story.get("title", "Untitled").replace("|", "-").replace("\n", " ").strip()
        url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
        score = story.get("score", 0)

        if len(title) > 65:
            title = title[:62] + "..."

        articles.append({
            "title": title,
            "url": url,
            "tags": "`hackernews`",
            "reactions": score,
            "reading_time": 0,
            "source": "HN"
        })

        if len(articles) >= MAX_ARTICLES:
            break

    return articles


def build_news_section(articles: list[dict]) -> str:
    """Build the markdown table for the news section."""
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    date_str = now.strftime("%B %d, %Y • %I:%M %p IST")

    lines = []
    lines.append("| # | **Trending in Tech Today** | **Tags** | **Link** |")
    lines.append("|:---:|---|---|:---:|")

    for i, article in enumerate(articles):
        icon = ICONS[i % len(ICONS)]
        title = article["title"]
        url = article["url"]
        tags = article["tags"]
        reactions = article["reactions"]
        source = article["source"]

        # Create a compact link
        link_text = f"[Read →]({url})"

        lines.append(f"| {icon} | **{title}** | {tags} | {link_text} |")

    lines.append("")
    lines.append(f'<p align="center"><sub>⏰ Last updated: {date_str} • Source: Dev.to & HackerNews (auto-fetched, no API key)</sub></p>')

    return "\n".join(lines)


def update_readme(news_content: str) -> bool:
    """Update README.md between the markers."""
    if not os.path.exists(README_PATH):
        print(f"❌ README not found at: {README_PATH}")
        return False

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find markers
    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print("❌ Could not find TECH_NEWS_START/END markers in README.md")
        return False

    # Build new content
    new_content = (
        content[:start_idx + len(START_MARKER)]
        + "\n"
        + news_content
        + "\n"
        + content[end_idx:]
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ README updated with {len(news_content)} chars of news content")
    return True


def main():
    print("📰 Fetching today's tech news...")

    # Try Dev.to first (better quality articles)
    articles = fetch_devto_articles()
    print(f"   Dev.to: {len(articles)} articles")

    # If Dev.to returned fewer than needed, supplement with HackerNews
    if len(articles) < MAX_ARTICLES:
        hn_articles = fetch_hackernews_top()
        remaining = MAX_ARTICLES - len(articles)
        articles.extend(hn_articles[:remaining])
        print(f"   HackerNews: added {min(remaining, len(hn_articles))} articles")

    if not articles:
        print("❌ No articles fetched from any source!")
        return

    print(f"📊 Total articles: {len(articles)}")

    # Build markdown
    news_section = build_news_section(articles)

    # Update README
    if update_readme(news_section):
        print("🎉 Done! README.md has been updated with today's tech news.")
    else:
        print("💥 Failed to update README.md")


if __name__ == "__main__":
    main()

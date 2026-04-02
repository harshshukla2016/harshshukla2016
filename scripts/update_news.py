#!/usr/bin/env python3
"""
📰 Daily Tech News + Dynamic Profile Updater for GitHub Profile README
- Fetches trending tech articles from Dev.to and HackerNews APIs (no API key needed)
- Updates timestamp, daily dev quote, and streak counter
- Ensures EVERY run produces unique content → guarantees a git commit
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
import hashlib

# ── SSL Context ────────────────────────────────────────────────────────
import platform
if platform.system() == "Darwin":
    SSL_CTX = ssl._create_unverified_context()
else:
    SSL_CTX = ssl.create_default_context()

# ── Configuration ──────────────────────────────────────────────────────
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
MAX_ARTICLES = 6
NEWS_START = "<!-- TECH_NEWS_START -->"
NEWS_END = "<!-- TECH_NEWS_END -->"
ICONS = ["🔥", "⚡", "🚀", "💡", "🧠", "🌐", "🤖", "📱", "☁️", "🔒"]

# ── Dev Quotes Pool ───────────────────────────────────────────────────
DEV_QUOTES = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Experience is the name everyone gives to their mistakes.", "Oscar Wilde"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Fix the cause, not the symptom.", "Steve Maguire"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Before software can be reusable it first has to be usable.", "Ralph Johnson"),
    ("The best error message is the one that never shows up.", "Thomas Fuchs"),
    ("Programming isn't about what you know; it's about what you can figure out.", "Chris Pine"),
    ("The only way to learn a new programming language is by writing programs in it.", "Dennis Ritchie"),
    ("Debugging is twice as hard as writing the code in the first place.", "Brian Kernighan"),
    ("Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.", "Antoine de Saint-Exupery"),
    ("It's not a bug — it's an undocumented feature.", "Anonymous"),
    ("If debugging is the process of removing bugs, then programming must be the process of putting them in.", "Edsger Dijkstra"),
    ("A good programmer is someone who always looks both ways before crossing a one-way street.", "Doug Linder"),
    ("Programming is the art of telling another human being what one wants the computer to do.", "Donald Knuth"),
    ("AI is the new electricity.", "Andrew Ng"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("Software is a great combination between artistry and engineering.", "Bill Gates"),
    ("Measuring programming progress by lines of code is like measuring aircraft building progress by weight.", "Bill Gates"),
    ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
    ("In order to be irreplaceable, one must always be different.", "Coco Chanel"),
    ("Knowledge is power.", "Francis Bacon"),
    ("Java is to JavaScript what Car is to Carpet.", "Chris Heilmann"),
    ("Walking on water and developing software from a specification are easy if both are frozen.", "Edward V. Berard"),
    ("Sometimes it pays to stay in bed on Monday, rather than spending the rest of the week debugging Monday's code.", "Dan Salomon"),
    ("The most disastrous thing that you can ever learn is your first programming language.", "Alan Kay"),
]

TECH_FACTS = [
    "The first computer bug was an actual moth found in a Harvard Mark II computer in 1947 🪲",
    "The first 1GB hard drive (1980) weighed about 550 pounds and cost $40,000 💾",
    "Python was named after Monty Python, not the snake 🐍",
    "The first website ever made is still online: info.cern.ch 🌐",
    "Email existed before the World Wide Web 📧",
    "About 90% of the world's data was created in just the last 2 years 📊",
    "The first computer programmer was Ada Lovelace, in the 1840s 👩‍💻",
    "Google's first tweet was in binary: 'I'm feeling lucky' 🔍",
    "There are about 700 programming languages in existence today 💻",
    "The average person unlocks their phone 150 times a day 📱",
    "The first domain ever registered was Symbolics.com on March 15, 1985 🏷️",
    "JavaScript was created in just 10 days by Brendan Eich in 1995 ⚡",
    "The first YouTube video was uploaded on April 23, 2005 🎬",
    "NASA's entire Apollo 11 computer had less power than a modern calculator 🚀",
    "The first Apple computer sold for $666.66 🍎",
    "Over 3.5 billion Google searches are made every day 🔎",
    "Linux powers 96.3% of the world's top 1 million servers 🐧",
    "The first text message ever sent was 'Merry Christmas' in 1992 💬",
    "Git was created by Linus Torvalds in just 10 days 🔧",
    "Stack Overflow is visited by 50 million developers every month 📚",
    "The first computer mouse was made of wood 🖱️",
    "The world's first webcam watched a coffee pot at Cambridge University ☕",
    "Samsung started as a grocery trading store in 1938 📦",
    "TypeScript was created by Microsoft in 2012 🏗️",
    "React.js was first deployed on Facebook's news feed in 2011 ⚛️",
    "The QWERTY keyboard layout was designed to slow typists down ⌨️",
    ("Wi-Fi doesn't stand for 'Wireless Fidelity' — it's just a brand name 📶"),
    "The term 'robot' comes from a Czech word meaning 'forced labor' 🤖",
    "More than 6,000 new computer viruses are created every month 🦠",
    "The first Apple logo featured Isaac Newton sitting under a tree 🍏",
]


def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Profile-News-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"⚠️  Failed to fetch {url}: {e}")
        return None


def fetch_devto_articles():
    data = fetch_url("https://dev.to/api/articles?top=1&per_page=8&tag=")
    if not data or not isinstance(data, list):
        return []
    articles = []
    for item in data[:MAX_ARTICLES]:
        title = item.get("title", "Untitled").replace("|", "-").replace("\n", " ").strip()
        if len(title) > 65:
            title = title[:62] + "..."
        url = item.get("url", "#")
        tags = item.get("tag_list", [])
        tag_str = ", ".join(f"`{t}`" for t in tags[:3]) if tags else "`tech`"
        articles.append({"title": title, "url": url, "tags": tag_str, "source": "Dev.to"})
    return articles


def fetch_hackernews_top():
    story_ids = fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not story_ids or not isinstance(story_ids, list):
        return []
    articles = []
    for sid in story_ids[:MAX_ARTICLES * 2]:
        story = fetch_url(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if not story or not isinstance(story, dict) or story.get("type") != "story":
            continue
        title = story.get("title", "Untitled").replace("|", "-").replace("\n", " ").strip()
        if len(title) > 65:
            title = title[:62] + "..."
        url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
        articles.append({"title": title, "url": url, "tags": "`hackernews`", "source": "HN"})
        if len(articles) >= MAX_ARTICLES:
            break
    return articles


def get_daily_quote(now):
    seed_str = now.strftime("%Y-%m-%d") + str(now.hour // 6)
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % len(DEV_QUOTES)
    return DEV_QUOTES[seed]


def get_daily_fact(now):
    seed_str = now.strftime("%Y-%m-%d")
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % len(TECH_FACTS)
    return TECH_FACTS[seed]


def get_time_greeting(now):
    hour = now.hour
    if hour < 12:
        return "🌅 Good Morning"
    elif hour < 17:
        return "☀️ Good Afternoon"
    elif hour < 21:
        return "🌇 Good Evening"
    else:
        return "🌙 Good Night"


def days_since_start():
    ist = timezone(timedelta(hours=5, minutes=30))
    start = datetime(2020, 8, 1, tzinfo=ist)
    now = datetime.now(ist)
    return (now - start).days


def build_news_section(articles):
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    date_str = now.strftime("%B %d, %Y • %I:%M %p IST")
    greeting = get_time_greeting(now)
    quote_text, quote_author = get_daily_quote(now)
    fact = get_daily_fact(now)
    coding_days = days_since_start()

    lines = []
    lines.append(f'<div align="center">')
    lines.append(f'<em>{greeting}! • Day <strong>{coding_days}</strong> of my coding journey</em>')
    lines.append(f'</div>')
    lines.append("")
    lines.append("| # | **Trending in Tech Today** | **Tags** | **Link** |")
    lines.append("|:---:|---|---|:---:|")

    for i, article in enumerate(articles):
        icon = ICONS[i % len(ICONS)]
        lines.append(f"| {icon} | **{article['title']}** | {article['tags']} | [Read →]({article['url']}) |")

    lines.append("")
    lines.append(f'<blockquote>')
    lines.append(f'<p>💬 <em>"{quote_text}"</em> — <strong>{quote_author}</strong></p>')
    lines.append(f'</blockquote>')
    lines.append("")
    lines.append(f"> **🧪 Did You Know?** {fact}")
    lines.append("")
    lines.append(f'<p align="center"><sub>⏰ Last updated: {date_str} • Auto-updated 3x daily via GitHub Actions</sub></p>')

    return "\n".join(lines)


def main():
    print("📰 Fetching today's tech news...")

    articles = fetch_devto_articles()
    print(f"   Dev.to: {len(articles)} articles")

    if len(articles) < MAX_ARTICLES:
        hn_articles = fetch_hackernews_top()
        remaining = MAX_ARTICLES - len(articles)
        articles.extend(hn_articles[:remaining])
        print(f"   HackerNews: added {min(remaining, len(hn_articles))} articles")

    if not articles:
        print("⚠️  No articles — using timestamp-only update")

    print(f"📊 Total articles: {len(articles)}")

    news_section = build_news_section(articles)

    if not os.path.exists(README_PATH):
        print(f"❌ README not found at: {README_PATH}")
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_idx = content.find(NEWS_START)
    end_idx = content.find(NEWS_END)
    if start_idx == -1 or end_idx == -1:
        print("❌ Could not find TECH_NEWS markers in README.md")
        return

    new_content = content[:start_idx + len(NEWS_START)] + "\n" + news_section + "\n" + content[end_idx:]

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    print(f"🎉 Done! README updated.")
    print(f"   ⏰ {now.strftime('%B %d, %Y • %I:%M %p IST')}")
    print(f"   📅 Day {days_since_start()} of coding journey")


if __name__ == "__main__":
    main()

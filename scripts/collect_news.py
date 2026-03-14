#!/usr/bin/env python3
"""
Stock & Market Daily News Collector v1.0
Collects overnight US market data, financial news, and generates
a morning briefing for Korean investors.

Pipeline:
  Phase 0 — Market data via yfinance (indices, forex, commodities, futures, crypto, bonds)
  Phase 1 — Financial news via RSS feeds (US + Korean sources)
  Phase 2 — Batch summarization via Gemini Flash
  Phase 3 — Editorial market briefing via Claude Sonnet
  Phase 4 — JSON output to data/{date}.json
"""

import os
import sys
import json
import hashlib
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import trafilatura
except ImportError:
    trafilatura = None

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL_FAST = os.environ.get("OPENROUTER_MODEL_FAST", "google/gemini-3-flash-preview")
MODEL_QUALITY = os.environ.get("OPENROUTER_MODEL_QUALITY", "anthropic/claude-sonnet-4.6")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MAX_PER_FEED = 15
BATCH_SIZE = 8
RETRY = 2
RETRY_DELAY = 5

KST = timezone(timedelta(hours=9))
NOW_KST = datetime.now(KST)
TODAY = NOW_KST.strftime("%Y-%m-%d")
DAY_OF_WEEK = NOW_KST.weekday()  # 0=Mon, 6=Sun

# On Monday (or after weekend), extend window to capture weekend news
# Mon morning KST = 72h covers Fri evening US → Mon morning KST
AGE_HOURS = 72 if DAY_OF_WEEK == 0 else 36
IS_MONDAY = DAY_OF_WEEK == 0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("stock-news")

# ---------------------------------------------------------------------------
# Market Tickers (yfinance symbols)
# ---------------------------------------------------------------------------

TICKERS = {
    "indices": [
        ("S&P 500", "^GSPC"),
        ("NASDAQ", "^IXIC"),
        ("다우존스", "^DJI"),
        ("러셀 2000", "^RUT"),
        ("필라델피아 반도체", "^SOX"),
    ],
    "futures": [
        ("S&P 500 선물", "ES=F"),
        ("나스닥 선물", "NQ=F"),
        ("다우 선물", "YM=F"),
    ],
    "volatility": [
        ("VIX (공포지수)", "^VIX"),
    ],
    "forex": [
        ("달러/원", "KRW=X"),
        ("달러/엔", "JPY=X"),
        ("유로/달러", "EURUSD=X"),
        ("달러인덱스", "DX-Y.NYB"),
    ],
    "commodities": [
        ("WTI 원유", "CL=F"),
        ("브렌트유", "BZ=F"),
        ("금", "GC=F"),
        ("은", "SI=F"),
        ("천연가스", "NG=F"),
        ("구리", "HG=F"),
    ],
    "crypto": [
        ("비트코인", "BTC-USD"),
        ("이더리움", "ETH-USD"),
    ],
    "bonds": [
        ("미국 10년물", "^TNX"),
        ("미국 2년물", "^IRX"),
    ],
}

# ---------------------------------------------------------------------------
# News RSS Feeds
# ---------------------------------------------------------------------------

RSS_FEEDS = [
    # --- US Financial News ---
    {"name": "CNBC Top News", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
    {"name": "CNBC Economy", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"},
    {"name": "CNBC World", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"},
    {"name": "MarketWatch", "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news.rss"},
    {"name": "Seeking Alpha", "url": "https://seekingalpha.com/market_currents.xml"},
    {"name": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"},
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},

    # --- Korean Financial News (미국주식 관련 한국어 소스) ---
    {"name": "한국경제 글로벌", "url": "https://www.hankyung.com/feed/world-news"},
    {"name": "한경 증권", "url": "https://www.hankyung.com/feed/stock"},
    {"name": "매일경제", "url": "https://www.mk.co.kr/rss/30100041/"},
    {"name": "매경 증권", "url": "https://www.mk.co.kr/rss/30200030/"},
    {"name": "연합뉴스 경제", "url": "https://www.yna.co.kr/rss/economy.xml"},
    {"name": "연합인포맥스", "url": "https://news.einfomax.co.kr/rss/S1N1.xml"},
    {"name": "조선비즈", "url": "https://biz.chosun.com/rss/finance/"},
    {"name": "이데일리 증권", "url": "https://rss.edaily.co.kr/edaily/finance/stock/"},
    {"name": "서울경제", "url": "https://www.sedaily.com/rss/Series/FortuneStock"},

    # --- saveticker.com: 직접 스크래핑 불가 (403/SPA). 동일 콘텐츠를 위 한국어 소스들로 커버 ---
]

HEADERS = {"User-Agent": "StockNewsBot/1.0 (github.com/nydad/stock-news)"}


# ---------------------------------------------------------------------------
# Phase 0: Fetch Market Data
# ---------------------------------------------------------------------------

def fetch_market_data() -> dict:
    """Fetch current market data using yfinance."""
    if not yf:
        log.warning("yfinance not installed, skipping market data")
        return {cat: [] for cat in TICKERS}

    log.info("=== Phase 0: Market Data (yfinance) ===")
    market_data = {}

    # Collect all symbols
    all_symbols = []
    symbol_map = {}  # symbol -> (category, name)
    for category, tickers in TICKERS.items():
        for name, symbol in tickers:
            all_symbols.append(symbol)
            symbol_map[symbol] = (category, name)

    # Batch download for speed
    try:
        log.info("Downloading %d tickers...", len(all_symbols))
        df = yf.download(all_symbols, period="5d", interval="1d",
                         progress=False, threads=True, timeout=30)
    except Exception as e:
        log.error("Batch download failed: %s", e)
        # Fallback: individual downloads
        return _fetch_market_individual()

    # Parse results
    for symbol, (category, name) in symbol_map.items():
        try:
            if len(all_symbols) == 1:
                close = df["Close"].dropna()
            else:
                if ("Close", symbol) not in df.columns and symbol not in df.get("Close", {}).columns if hasattr(df.get("Close", {}), "columns") else True:
                    # Try alternative column access
                    try:
                        close = df["Close"][symbol].dropna()
                    except (KeyError, TypeError):
                        log.warning("  No data for %s (%s)", name, symbol)
                        continue
                else:
                    close = df["Close"][symbol].dropna()

            if len(close) < 1:
                continue

            current = float(close.iloc[-1])
            prev = float(close.iloc[-2]) if len(close) >= 2 else current
            change = current - prev
            pct = (change / prev) * 100 if prev else 0

            if category not in market_data:
                market_data[category] = []

            market_data[category].append({
                "name": name,
                "ticker": symbol,
                "price": round(current, 4) if category in ("forex", "bonds") else round(current, 2),
                "change": round(change, 4) if category in ("forex", "bonds") else round(change, 2),
                "change_pct": round(pct, 2),
            })
        except Exception as e:
            log.warning("  %s (%s): %s", name, symbol, e)

    # Ensure all categories exist
    for cat in TICKERS:
        if cat not in market_data:
            market_data[cat] = []
        log.info("  %s: %d items", cat, len(market_data[cat]))

    return market_data


def _fetch_market_individual() -> dict:
    """Fallback: fetch each ticker individually."""
    log.info("Falling back to individual ticker downloads...")
    market_data = {}

    for category, tickers in TICKERS.items():
        category_data = []
        for name, symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if hist.empty or len(hist) < 1:
                    continue
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current
                change = current - prev
                pct = (change / prev) * 100 if prev else 0
                category_data.append({
                    "name": name, "ticker": symbol,
                    "price": round(current, 4) if category in ("forex", "bonds") else round(current, 2),
                    "change": round(change, 4) if category in ("forex", "bonds") else round(change, 2),
                    "change_pct": round(pct, 2),
                })
            except Exception as e:
                log.warning("  %s: %s", name, e)
        market_data[category] = category_data
        log.info("  %s: %d items", category, len(category_data))

    return market_data


# ---------------------------------------------------------------------------
# Phase 0.5: Fear & Greed Index (CNN unofficial API)
# ---------------------------------------------------------------------------

def fetch_fear_greed() -> dict | None:
    """Fetch CNN Fear & Greed Index."""
    try:
        r = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={**HEADERS, "Referer": "https://www.cnn.com/markets/fear-and-greed"},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        fg = data.get("fear_and_greed", {})
        return {
            "score": round(fg.get("score", 0), 1),
            "rating": fg.get("rating", ""),
            "previous_close": round(fg.get("previous_close", 0), 1),
        }
    except Exception as e:
        log.warning("Fear & Greed fetch failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Phase 1: Fetch News
# ---------------------------------------------------------------------------

def _fetch_saveticker() -> list[dict]:
    """Best-effort scrape of saveticker.com/app/news (SPA, often 403)."""
    try:
        r = requests.get("https://saveticker.com/app/news", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        }, timeout=15)
        if r.status_code != 200:
            log.info("SaveTicker: HTTP %d (expected, SPA blocks bots)", r.status_code)
            return []
        # If we get HTML, try to extract article data (unlikely but worth trying)
        if trafilatura:
            text = trafilatura.extract(r.text, include_comments=False)
            if text and len(text) > 100:
                log.info("SaveTicker: extracted %d chars", len(text))
                return [{
                    "title": "SaveTicker 시황 요약",
                    "url": "https://saveticker.com/app/news",
                    "source": "SaveTicker",
                    "published": datetime.now(timezone.utc).isoformat(),
                    "description": text[:600],
                }]
        return []
    except Exception as e:
        log.info("SaveTicker: %s", e)
        return []


def fetch_all_feeds() -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=AGE_HOURS)
    articles = []
    for f in RSS_FEEDS:
        articles.extend(_fetch_rss(f, cutoff))

    # Best-effort saveticker.com
    articles.extend(_fetch_saveticker())

    # Deduplicate by URL hash
    seen: set[str] = set()
    unique: list[dict] = []
    for a in articles:
        key = hashlib.md5(a["url"].lower().split("?")[0].rstrip("/").encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(a)
    log.info("Total unique articles: %d", len(unique))
    return unique


def _fetch_rss(cfg: dict, cutoff: datetime) -> list[dict]:
    name = cfg["name"]
    try:
        feed = feedparser.parse(cfg["url"], request_headers=HEADERS)
        if feed.bozo and not feed.entries:
            log.warning("Parse error for %s: %s", name, feed.bozo_exception)
            return []
        results = []
        for entry in feed.entries[:MAX_PER_FEED]:
            pub = _parse_date(entry)
            if pub and pub < cutoff:
                continue
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            results.append({
                "title": title, "url": link, "source": name,
                "published": (pub or datetime.now(timezone.utc)).isoformat(),
                "description": _clean(entry.get("summary", ""))[:600],
            })
        log.info("%-25s -> %d", name, len(results))
        return results
    except Exception as e:
        log.error("Failed %s: %s", name, e)
        return []


def _parse_date(entry) -> datetime | None:
    for f in ("published_parsed", "updated_parsed", "created_parsed"):
        p = entry.get(f)
        if p:
            try:
                return datetime(*p[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
    return None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def extract_content(url: str) -> str:
    if not trafilatura:
        return ""
    try:
        dl = trafilatura.fetch_url(url)
        if dl:
            t = trafilatura.extract(dl, include_comments=False, include_tables=False, deduplicate=True)
            if t:
                return t[:3000]
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# OpenRouter API
# ---------------------------------------------------------------------------

def _call_api(model: str, system: str, user: str, max_tokens: int = 4096) -> dict | None:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/nydad/stock-news",
        "X-Title": "Stock Daily Digest",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(1, RETRY + 1):
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # Strip markdown code fences
            if content.startswith("```"):
                content = "\n".join(content.split("\n")[1:])
                if content.rstrip().endswith("```"):
                    content = content.rstrip()[:-3]
                content = content.strip()
            result = json.loads(content)
            log.info("API OK (model=%s, attempt=%d)", model, attempt)
            return result
        except Exception as e:
            log.warning("API fail (attempt %d): %s", attempt, e)
            if attempt < RETRY:
                time.sleep(RETRY_DELAY)
    return None


# ---------------------------------------------------------------------------
# Phase 2: Batch Summarization (Gemini Flash)
# ---------------------------------------------------------------------------

BATCH_PROMPT = """You are a financial news analyst. Analyze articles and return JSON.

For EACH article (same order, do NOT skip any), provide:
- "category": classify as one of:
  "market" (시장 동향: 주가, 지수, 시장 전반적 흐름)
  "economy" (경제 지표: GDP, 고용, 인플레이션, 금리, 소비자 심리)
  "policy" (정책/규제: 연준, 정부 정책, 관세, 무역 분쟁)
  "earnings" (기업 실적: 어닝, 가이던스, M&A, 기업 뉴스)
  "forex" (환율/외환: 달러, 원화, 엔화 등)
  "commodity" (원자재: 유가, 금, 천연가스, 원자재 전반)
  "crypto" (암호화폐: 비트코인, 이더리움, 블록체인)
  "geopolitics" (지정학: 전쟁, 외교, 국제 관계가 시장에 미치는 영향)
- "summary": 2-3 sentence summary in KOREAN (한국어). Keep proper nouns, numbers, ticker symbols in English.
- "importance": "high" / "medium" / "low"
- "tags": 2-4 lowercase English tags (e.g., "fed", "nasdaq", "oil", "earnings")

Return:
{"articles": [{"category":"...", "summary":"...", "importance":"...", "tags":["..."]}, ...]}

CRITICAL: Exactly one entry per article, SAME ORDER. All summaries in Korean.
Focus on information relevant to investors."""


def summarize_batch(articles: list[dict]) -> list[dict] | None:
    parts = []
    for i, a in enumerate(articles):
        content = extract_content(a["url"]) or a.get("description", "")
        parts.append(
            f"---ARTICLE {i+1} of {len(articles)}---\n"
            f"Title: {a['title']}\nSource: {a['source']}\n"
            f"Content:\n{content[:2000]}\n"
        )
        time.sleep(0.2)

    user = (f"Summarize {len(articles)} financial news articles. "
            f"Return exactly {len(articles)} entries.\n\n" + "\n".join(parts))
    result = _call_api(MODEL_FAST, BATCH_PROMPT, user)
    if not result:
        return None
    ai = result.get("articles", [])
    log.info("  -> %d summaries for %d articles", len(ai), len(articles))
    return ai


# ---------------------------------------------------------------------------
# Phase 3: Editorial Market Briefing (Claude Sonnet)
# ---------------------------------------------------------------------------

EDITORIAL_PROMPT = """You are a senior financial analyst writing a daily morning market briefing for Korean investors.
The briefing covers overnight US market activity and global financial news.

You will receive:
1. Market data (indices, forex, commodities, futures, crypto, bonds, VIX)
2. Fear & Greed index data
3. Categorized news article summaries
4. Whether today is Monday (weekend recap mode)

Generate the following in KOREAN (한국어), except keep numbers, ticker symbols, and proper nouns in English:

1. "market_briefing": 6-8 sentences. Professional, concise market overview.
   Cover: major index movements, key drivers, notable sector moves, overnight futures.
   If it's MONDAY: include weekend recap covering key events from Saturday/Sunday
   that may impact Monday's trading session (geopolitics, crypto moves, policy announcements).
   Tone: 전문적이고 객관적인 투자 정보 전달 톤.

2. "key_insights": Array of 3-5 actionable insights. Each has:
   - "title": Short Korean title (max 20 chars)
   - "detail": 1-2 sentence Korean description
   - "type": "bullish" (강세) / "bearish" (약세) / "neutral" (중립) / "alert" (주의)

3. "forex_commentary": 2-3 sentences about exchange rate movements (USD/KRW focus).

4. "commodity_commentary": 2-3 sentences about oil, gold, and key commodity moves.

5. "outlook": 2-3 sentences. Today's market outlook and key events to watch.

6. "trends": 3-5 short Korean trend keywords.

Return JSON:
{
  "market_briefing": "...",
  "key_insights": [{"title":"...","detail":"...","type":"..."}],
  "forex_commentary": "...",
  "commodity_commentary": "...",
  "outlook": "...",
  "trends": ["..."]
}

ALL text in Korean except numbers/tickers/proper nouns. Be data-driven and specific."""


def generate_editorial(market_data: dict, fear_greed: dict | None, articles: list[dict]) -> dict:
    parts = []

    # Market data context
    parts.append("=== MARKET DATA ===")
    for category, items in market_data.items():
        if items:
            parts.append(f"\n[{category.upper()}]")
            for item in items:
                direction = "+" if item["change"] >= 0 else ""
                parts.append(
                    f"  {item['name']}: {item['price']} "
                    f"({direction}{item['change']}, {direction}{item['change_pct']}%)"
                )

    # Fear & Greed
    if fear_greed:
        parts.append(f"\n[FEAR & GREED INDEX]")
        parts.append(f"  Score: {fear_greed['score']} ({fear_greed['rating']})")
        parts.append(f"  Previous: {fear_greed['previous_close']}")

    # News summaries by category
    parts.append("\n\n=== NEWS ARTICLES ===")
    categories_seen = {}
    for a in articles:
        cat = a.get("category", "market")
        if cat not in categories_seen:
            categories_seen[cat] = []
        categories_seen[cat].append(a)

    for cat, cat_articles in categories_seen.items():
        parts.append(f"\n[{cat.upper()}]")
        for a in cat_articles:
            parts.append(f"  [{a.get('source', '')}] {a['title']}")
            parts.append(f"    {a.get('summary', '')}")

    monday_note = "\n*** TODAY IS MONDAY — Include a weekend recap section in market_briefing. ***" if IS_MONDAY else ""
    user = (
        f"Today: {datetime.now(KST).strftime('%Y-%m-%d %A')}\n"
        f"Total articles: {len(articles)}\n"
        f"News window: last {AGE_HOURS} hours{' (extended for weekend coverage)' if IS_MONDAY else ''}"
        f"{monday_note}\n\n" + "\n".join(parts)
    )

    result = _call_api(MODEL_QUALITY, EDITORIAL_PROMPT, user, max_tokens=3000)
    if result:
        log.info("Editorial generated successfully")
        return result

    log.warning("Editorial failed, using fallback")
    return {
        "market_briefing": "",
        "key_insights": [],
        "forex_commentary": "",
        "commodity_commentary": "",
        "outlook": "",
        "trends": [],
    }


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def build_digest() -> dict:
    # Phase 0: Market data
    market_data = fetch_market_data()
    fear_greed = fetch_fear_greed()

    # Phase 1: News
    log.info("=== Phase 1: Fetch News ===")
    raw_articles = fetch_all_feeds()

    # Phase 2: Summarize
    log.info("=== Phase 2: Summarization (%s) ===", MODEL_FAST)
    all_articles: list[dict] = []

    for i in range(0, len(raw_articles), BATCH_SIZE):
        batch = raw_articles[i:i + BATCH_SIZE]
        log.info("Batch %d: %d articles", i // BATCH_SIZE + 1, len(batch))

        ai = summarize_batch(batch)
        for j, article in enumerate(batch):
            if ai and j < len(ai):
                item = ai[j]
                enriched = {
                    **article,
                    "summary": item.get("summary", article.get("description", "")),
                    "importance": item.get("importance", "medium"),
                    "category": item.get("category", "market"),
                    "tags": item.get("tags", []),
                }
            else:
                enriched = {
                    **article,
                    "summary": article.get("description", "")[:300],
                    "importance": "medium",
                    "category": "market",
                    "tags": [],
                }
            all_articles.append(enriched)

    # Sort by importance
    imp = {"high": 0, "medium": 1, "low": 2}
    all_articles.sort(key=lambda a: imp.get(a.get("importance", "low"), 2))
    log.info("Phase 2 done: %d articles summarized", len(all_articles))

    # Phase 3: Editorial
    log.info("=== Phase 3: Editorial (%s) ===", MODEL_QUALITY)
    editorial = generate_editorial(market_data, fear_greed, all_articles)

    # Phase 4: Build JSON
    log.info("=== Phase 4: Build Output ===")

    def article_out(a):
        return {
            "title": a["title"], "url": a["url"], "source": a["source"],
            "published": a["published"], "summary": a["summary"],
            "importance": a["importance"], "category": a["category"],
            "tags": a["tags"],
        }

    # Group articles by category
    cat_order = ["market", "economy", "policy", "earnings", "forex", "commodity", "crypto", "geopolitics"]
    cat_names = {
        "market": "시장 동향",
        "economy": "경제 지표",
        "policy": "정책/규제",
        "earnings": "기업 실적",
        "forex": "환율/외환",
        "commodity": "원자재",
        "crypto": "암호화폐",
        "geopolitics": "지정학",
    }
    categories = []
    for cat in cat_order:
        cat_articles = [a for a in all_articles if a.get("category") == cat]
        if cat_articles:
            categories.append({
                "id": cat,
                "name": cat_names.get(cat, cat),
                "articles": [article_out(a) for a in cat_articles],
            })

    return {
        "date": TODAY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market_data": market_data,
        "fear_greed": fear_greed,
        "market_briefing": editorial.get("market_briefing", ""),
        "key_insights": editorial.get("key_insights", []),
        "forex_commentary": editorial.get("forex_commentary", ""),
        "commodity_commentary": editorial.get("commodity_commentary", ""),
        "outlook": editorial.get("outlook", ""),
        "trends": editorial.get("trends", []),
        "total_articles": len(all_articles),
        "categories": categories,
    }


def update_index():
    dates = sorted(
        [f.stem for f in DATA_DIR.glob("*.json") if f.stem != "index"],
        reverse=True
    )
    with open(DATA_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump({"dates": dates, "latest": dates[0] if dates else None}, f, indent=2)
    log.info("Index: %d dates", len(dates))


def main():
    if not OPENROUTER_API_KEY:
        log.error("OPENROUTER_API_KEY not set!")
        sys.exit(1)

    log.info("=" * 50)
    log.info("Stock & Market Daily News v1.0")
    log.info("Fast: %s / Quality: %s", MODEL_FAST, MODEL_QUALITY)
    log.info("Date: %s (KST) | Window: %dh%s", TODAY, AGE_HOURS,
             " (MONDAY - weekend recap)" if IS_MONDAY else "")
    log.info("=" * 50)

    digest = build_digest()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{digest['date']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(digest, f, ensure_ascii=False, indent=2)
    log.info("Saved: %s (%d articles)", path.name, digest["total_articles"])

    update_index()
    log.info("=" * 50)
    log.info("Done!")


if __name__ == "__main__":
    main()

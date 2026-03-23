# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - 数据采集引擎
==================================
从多个渠道采集游戏×品牌异业合作资讯
支持：Bing搜索、Bing新闻、RSS订阅、网页内容提取
"""

import re
import time
import random
import hashlib
import json
import traceback
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    TARGET_GAMES, TARGET_GAMES_T1, TARGET_GAMES_T2, GAME_ALIASES,
    BRAND_CATEGORIES, COLLAB_TYPES,
    SEARCH_ENGINES, RSS_FEEDS, COLLECT_CONFIG,
    build_search_queries, get_brand_category, get_all_brands
)
from database import (
    init_database, save_collaboration, save_collect_log, compute_content_hash
)


# ===================== HTTP 工具 =====================

def make_request(url, params=None, headers=None, timeout=None):
    """发送 HTTP 请求"""
    if timeout is None:
        timeout = COLLECT_CONFIG["request_timeout"]
    
    default_headers = {
        "User-Agent": COLLECT_CONFIG["user_agent"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if headers:
        default_headers.update(headers)
    
    try:
        resp = requests.get(url, params=params, headers=default_headers, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"  [请求失败] {url[:80]}... -> {e}")
        return None


def random_delay():
    """随机延迟，避免请求过快"""
    delay = random.uniform(
        COLLECT_CONFIG["request_delay_min"],
        COLLECT_CONFIG["request_delay_max"]
    )
    time.sleep(delay)


# ===================== 智能分析 =====================

def analyze_collaboration(title, content="", url=""):
    """
    智能分析一条内容，提取游戏名、品牌名、合作类型等
    支持：精确匹配 → 别名匹配 → 动态提取
    """
    text = f"{title} {content}".lower()
    original_text = f"{title} {content}"
    result = {
        "game_name": "",
        "brand_name": "",
        "brand_category": "",
        "collab_type": "",
        "is_relevant": False,
        "hot_score": 0,
    }
    
    # === 识别游戏 ===
    # 第1步：精确匹配 TARGET_GAMES（优先长名字避免子串误匹配）
    sorted_games = sorted(TARGET_GAMES, key=len, reverse=True)
    for game in sorted_games:
        if game.lower() in text or game.replace("：", ":").lower() in text:
            result["game_name"] = game
            break
    
    # 第2步：别名匹配
    if not result["game_name"]:
        for alias, canonical in GAME_ALIASES.items():
            if alias.lower() in text:
                result["game_name"] = canonical
                break
    
    # 第3步：从标题中动态提取（"《XXX》联名/合作/联动..."）
    if not result["game_name"]:
        book_match = re.search(r'《([^》]{2,15})》', title)
        if book_match:
            candidate = book_match.group(1).strip()
            # 检查是否有合作相关的上下文
            collab_words = ["联名", "合作", "联动", "跨界", "携手", "x ", " x ", "×"]
            if any(w in text for w in collab_words):
                result["game_name"] = candidate
    
    # 识别品牌
    all_brands = get_all_brands()
    for brand in all_brands:
        if brand.lower() in text:
            result["brand_name"] = brand
            result["brand_category"] = get_brand_category(brand)
            break
    
    # 如果没匹配到预设品牌，尝试从标题中提取 "X联名Y" / "X x Y" 模式
    if not result["brand_name"]:
        patterns = [
            r'[×xX✖]\s*([^\s,，、。！？]{2,10})',
            r'联名\s*([^\s,，、。！？]{2,10})',
            r'合作\s*([^\s,，、。！？]{2,10})',
            r'联动\s*([^\s,，、。！？]{2,10})',
            r'携手\s*([^\s,，、。！？]{2,10})',
        ]
        for p in patterns:
            match = re.search(p, title)
            if match:
                candidate = match.group(1).strip()
                # 排除常见干扰词
                skip_words = ["打造", "推出", "上线", "开启", "限定", "全新", "首次", "再次", "重磅"]
                if candidate not in skip_words and len(candidate) >= 2:
                    result["brand_name"] = candidate
                    result["brand_category"] = get_brand_category(candidate)
                    break
    
    # 识别合作类型
    type_keywords = {
        "联名产品": ["联名款", "联名产品", "联名商品", "定制款", "联名周边"],
        "主题门店": ["主题店", "快闪店", "主题餐厅", "主题门店", "旗舰店"],
        "限定皮肤": ["限定皮肤", "联名皮肤", "联动皮肤", "定制皮肤", "专属皮肤"],
        "线下活动": ["线下活动", "线下联动", "线下体验", "嘉年华", "粉丝见面"],
        "定制包装": ["定制包装", "联名包装", "限定包装", "主题杯", "主题袋"],
        "积分兑换": ["积分兑换", "消费送", "买赠", "积分换"],
        "抽奖活动": ["抽奖", "盲盒", "集卡", "刮刮卡"],
        "AR互动": ["AR", "扫码", "AR互动", "AR体验"],
        "赛事赞助": ["赛事赞助", "战队赞助", "电竞赞助", "冠名赞助"],
        "代言合作": ["代言", "形象大使", "品牌挚友"],
        "内容共创": ["内容共创", "联合创作", "主题短片", "品牌微电影"],
        "跨界礼盒": ["礼盒", "联名礼盒", "定制礼盒", "福袋"],
    }
    for ctype, keywords in type_keywords.items():
        for kw in keywords:
            if kw in text:
                result["collab_type"] = ctype
                break
        if result["collab_type"]:
            break
    if not result["collab_type"]:
        result["collab_type"] = "其他"
    
    # 判断是否相关（更宽松：有游戏名+合作关键词即可）
    relevance_keywords = ["联名", "合作", "联动", "跨界", "异业", "携手", "牵手", "x ", " x ", "×",
                          "品牌", "赞助", "授权", "快闪", "主题店", "限定", "周边"]
    has_relevance = any(kw in text for kw in relevance_keywords)
    
    if result["game_name"] and (result["brand_name"] or has_relevance):
        result["is_relevant"] = True
    elif result["game_name"] and result["collab_type"] and result["collab_type"] != "其他":
        result["is_relevant"] = True
    elif has_relevance and ("游戏" in text or "手游" in text or "端游" in text or "网游" in text):
        result["is_relevant"] = True
    elif has_relevance and result["brand_name"]:
        # 有品牌+有合作关键词，即使没识别到游戏名也可能相关
        result["is_relevant"] = True
    
    # 计算热度分（按游戏层级加分）
    score = 0
    if result["game_name"]:
        if result["game_name"] in TARGET_GAMES_T1:
            score += 30  # T1 头部
        elif result["game_name"] in TARGET_GAMES_T2:
            score += 22  # T2 主流
        else:
            score += 15  # T3/T4/动态识别
    if result["brand_name"]:
        score += 20
    if result["brand_category"] in ["餐饮", "快消", "3C数码"]:
        score += 10
    if has_relevance:
        score += 10
    # 时效性加分（标题中提到"新"、"首"、"最新"等）
    freshness_words = ["新", "首次", "最新", "重磅", "官宣", "上线", "开启", "首发"]
    if any(w in title for w in freshness_words):
        score += 15
    
    result["hot_score"] = min(score, 100)
    
    return result


# ===================== Bing 搜索采集 =====================

def collect_from_bing_search(query, max_results=10):
    """从 Bing 搜索采集"""
    results = []
    url = SEARCH_ENGINES["bing"]["base_url"]
    params = {"q": query, "count": max_results, "setlang": "zh-CN"}
    
    resp = make_request(url, params=params)
    if not resp:
        return results
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 解析搜索结果
    for item in soup.select("li.b_algo"):
        try:
            title_el = item.select_one("h2 a")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            
            snippet_el = item.select_one(".b_caption p")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            
            # 尝试提取日期
            date_el = item.select_one(".news_dt")
            pub_date = date_el.get_text(strip=True) if date_el else ""
            
            results.append({
                "title": title,
                "url": link,
                "snippet": snippet,
                "published_date": pub_date,
                "source_type": "bing_search",
            })
        except Exception:
            continue
    
    return results


# ===================== Bing 新闻采集 =====================

def collect_from_bing_news(query, max_results=10):
    """从 Bing 新闻采集"""
    results = []
    url = SEARCH_ENGINES["bing_news"]["base_url"]
    params = {"q": query, "count": max_results, "setlang": "zh-CN", "qft": "sortbydate"}
    
    resp = make_request(url, params=params)
    if not resp:
        return results
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    for item in soup.select(".news-card"):
        try:
            title_el = item.select_one("a.title")
            if not title_el:
                continue
            
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            
            snippet_el = item.select_one(".snippet")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            
            source_el = item.select_one(".source")
            source_name = source_el.get_text(strip=True) if source_el else ""
            
            time_el = item.select_one("span[tabindex]")
            pub_date = time_el.get_text(strip=True) if time_el else ""
            
            img_el = item.select_one("img")
            img_url = img_el.get("src", "") if img_el else ""
            
            results.append({
                "title": title,
                "url": link,
                "snippet": snippet,
                "source_name": source_name,
                "published_date": pub_date,
                "image_url": img_url,
                "source_type": "bing_news",
            })
        except Exception:
            continue
    
    # 备用解析（不同页面结构）
    if not results:
        for item in soup.select("div.newsitem, div.news_item, .nws_cwrp"):
            try:
                title_el = item.select_one("a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if title and link:
                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": "",
                        "source_type": "bing_news",
                    })
            except Exception:
                continue
    
    return results


# ===================== RSS 采集 =====================

def collect_from_rss(feed_url, feed_name=""):
    """从 RSS 订阅源采集"""
    results = []
    
    resp = make_request(feed_url)
    if not resp:
        return results
    
    try:
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item") or soup.find_all("entry")
        
        for item in items:
            try:
                title = item.find("title").get_text(strip=True) if item.find("title") else ""
                
                link_el = item.find("link")
                if link_el:
                    link = link_el.get("href", "") or link_el.get_text(strip=True)
                else:
                    link = ""
                
                desc_el = item.find("description") or item.find("summary") or item.find("content")
                desc = ""
                if desc_el:
                    desc_html = desc_el.get_text(strip=True)
                    desc = BeautifulSoup(desc_html, "html.parser").get_text(strip=True)[:500]
                
                pub_el = item.find("pubDate") or item.find("published") or item.find("updated")
                pub_date = pub_el.get_text(strip=True) if pub_el else ""
                
                # 尝试提取图片
                img_url = ""
                enclosure = item.find("enclosure")
                if enclosure and enclosure.get("type", "").startswith("image"):
                    img_url = enclosure.get("url", "")
                if not img_url:
                    media = item.find("media:content") or item.find("media:thumbnail")
                    if media:
                        img_url = media.get("url", "")
                
                results.append({
                    "title": title,
                    "url": link,
                    "snippet": desc[:300],
                    "published_date": pub_date,
                    "source_name": feed_name,
                    "image_url": img_url,
                    "source_type": "rss",
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [RSS解析失败] {feed_name}: {e}")
    
    return results


# ===================== 网页正文提取 =====================

def extract_article_content(url):
    """提取网页文章正文"""
    resp = make_request(url, timeout=10)
    if not resp:
        return {"content": "", "image": ""}
    
    try:
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 移除脚本和样式
        for tag in soup.select("script, style, nav, footer, header, aside, .comment, .ad"):
            tag.decompose()
        
        # 尝试常见正文容器
        content = ""
        selectors = [
            "article", ".article-content", ".post-content", ".entry-content",
            ".content", "#content", ".article_content", ".rich_media_content",
            ".detail-content", "main", ".main-content"
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                content = el.get_text(separator="\n", strip=True)
                if len(content) > 100:
                    break
        
        if not content or len(content) < 100:
            body = soup.find("body")
            if body:
                content = body.get_text(separator="\n", strip=True)
        
        # 提取主图
        image = ""
        og_img = soup.select_one('meta[property="og:image"]')
        if og_img:
            image = og_img.get("content", "")
        if not image:
            for img in soup.select("article img, .content img, .post img"):
                src = img.get("src", "")
                if src and not any(x in src.lower() for x in ["logo", "icon", "avatar", "ad"]):
                    image = src if src.startswith("http") else urljoin(url, src)
                    break
        
        # 清理内容
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        content = "\n".join(lines)
        
        return {"content": content[:5000], "image": image}
    except Exception:
        return {"content": "", "image": ""}


# ===================== 主采集流程 =====================

def run_collection(queries=None, include_rss=True, fetch_content=False, verbose=True):
    """
    执行一次完整的数据采集
    
    Args:
        queries: 搜索查询列表，None则使用默认
        include_rss: 是否包含RSS源
        fetch_content: 是否提取文章正文（较慢）
        verbose: 是否打印详细日志
    
    Returns:
        采集统计摘要
    """
    init_database()
    
    if queries is None:
        queries = build_search_queries()
    
    total_found = 0
    total_saved = 0
    total_dup = 0
    total_errors = 0
    start_time = time.time()
    
    print("=" * 60)
    print(f"🎮 游戏异业合作情报采集开始")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 查询数: {len(queries)}")
    print("=" * 60)
    
    # 1. Bing 搜索采集
    if SEARCH_ENGINES.get("bing", {}).get("enabled"):
        print(f"\n--- Bing 搜索采集 ({len(queries)} 个查询) ---")
        for i, query in enumerate(queries):
            if verbose:
                print(f"  [{i+1}/{len(queries)}] 搜索: {query}")
            
            try:
                raw_results = collect_from_bing_search(query)
                found = 0
                saved = 0
                
                for raw in raw_results:
                    analysis = analyze_collaboration(raw["title"], raw.get("snippet", ""), raw.get("url", ""))
                    
                    if not analysis["is_relevant"]:
                        continue
                    
                    found += 1
                    
                    # 提取正文（可选）
                    full_content = ""
                    image_url = raw.get("image_url", "")
                    if fetch_content and raw.get("url"):
                        article = extract_article_content(raw["url"])
                        full_content = article["content"]
                        if not image_url:
                            image_url = article["image"]
                    
                    data = {
                        "title": raw["title"],
                        "summary": raw.get("snippet", "")[:300],
                        "game_name": analysis["game_name"],
                        "brand_name": analysis["brand_name"],
                        "brand_category": analysis["brand_category"],
                        "collab_type": analysis["collab_type"],
                        "source_url": raw.get("url", ""),
                        "source_name": raw.get("source_name", "Bing搜索"),
                        "source_type": "bing_search",
                        "image_url": image_url,
                        "published_date": raw.get("published_date", ""),
                        "hot_score": analysis["hot_score"],
                        "full_content": full_content,
                        "tags": [],
                    }
                    
                    if save_collaboration(data):
                        saved += 1
                        total_saved += 1
                    else:
                        total_dup += 1
                
                total_found += found
                if verbose and found > 0:
                    print(f"    → 发现 {found} 条相关，新增 {saved} 条")
                
                # 记录日志
                save_collect_log({
                    "source_type": "bing_search",
                    "query_keyword": query,
                    "results_found": found,
                    "new_saved": saved,
                    "duplicates_skipped": len(raw_results) - found,
                })
                
            except Exception as e:
                total_errors += 1
                if verbose:
                    print(f"    ✗ 错误: {e}")
            
            random_delay()
    
    # 2. Bing 新闻采集
    if SEARCH_ENGINES.get("bing_news", {}).get("enabled"):
        print(f"\n--- Bing 新闻采集 ---")
        news_queries = [q for q in queries if any(kw in q for kw in ["联名", "合作", "联动", "跨界"])][:15]
        
        for i, query in enumerate(news_queries):
            if verbose:
                print(f"  [{i+1}/{len(news_queries)}] 新闻: {query}")
            
            try:
                raw_results = collect_from_bing_news(query)
                found = 0
                saved = 0
                
                for raw in raw_results:
                    analysis = analyze_collaboration(raw["title"], raw.get("snippet", ""))
                    
                    if not analysis["is_relevant"]:
                        continue
                    
                    found += 1
                    data = {
                        "title": raw["title"],
                        "summary": raw.get("snippet", "")[:300],
                        "game_name": analysis["game_name"],
                        "brand_name": analysis["brand_name"],
                        "brand_category": analysis["brand_category"],
                        "collab_type": analysis["collab_type"],
                        "source_url": raw.get("url", ""),
                        "source_name": raw.get("source_name", "Bing新闻"),
                        "source_type": "bing_news",
                        "image_url": raw.get("image_url", ""),
                        "published_date": raw.get("published_date", ""),
                        "hot_score": analysis["hot_score"],
                        "tags": [],
                    }
                    
                    if save_collaboration(data):
                        saved += 1
                        total_saved += 1
                    else:
                        total_dup += 1
                
                total_found += found
                if verbose and found > 0:
                    print(f"    → 发现 {found} 条相关，新增 {saved} 条")
                    
            except Exception as e:
                total_errors += 1
                if verbose:
                    print(f"    ✗ 错误: {e}")
            
            random_delay()
    
    # 3. RSS 源采集
    if include_rss:
        print(f"\n--- RSS 源采集 ---")
        for feed in RSS_FEEDS:
            if not feed.get("enabled"):
                continue
            
            if verbose:
                print(f"  RSS: {feed['name']}")
            
            try:
                raw_results = collect_from_rss(feed["url"], feed["name"])
                found = 0
                saved = 0
                
                for raw in raw_results:
                    analysis = analyze_collaboration(raw["title"], raw.get("snippet", ""))
                    
                    if not analysis["is_relevant"]:
                        continue
                    
                    found += 1
                    data = {
                        "title": raw["title"],
                        "summary": raw.get("snippet", "")[:300],
                        "game_name": analysis["game_name"],
                        "brand_name": analysis["brand_name"],
                        "brand_category": analysis["brand_category"],
                        "collab_type": analysis["collab_type"],
                        "source_url": raw.get("url", ""),
                        "source_name": feed["name"],
                        "source_type": "rss",
                        "image_url": raw.get("image_url", ""),
                        "published_date": raw.get("published_date", ""),
                        "hot_score": analysis["hot_score"],
                        "tags": [],
                    }
                    
                    if save_collaboration(data):
                        saved += 1
                        total_saved += 1
                    else:
                        total_dup += 1
                
                total_found += found
                if verbose:
                    print(f"    → 获取 {len(raw_results)} 条，相关 {found} 条，新增 {saved} 条")
                    
            except Exception as e:
                total_errors += 1
                if verbose:
                    print(f"    ✗ 错误: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"✅ 采集完成！")
    print(f"  📊 发现相关: {total_found} 条")
    print(f"  💾 新增保存: {total_saved} 条")
    print(f"  🔄 重复跳过: {total_dup} 条")
    print(f"  ❌ 错误次数: {total_errors}")
    print(f"  ⏱  耗时: {elapsed:.1f} 秒")
    print("=" * 60)
    
    return {
        "total_found": total_found,
        "total_saved": total_saved,
        "total_dup": total_dup,
        "total_errors": total_errors,
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    result = run_collection(verbose=True, fetch_content=False)
    print(f"\n采集结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

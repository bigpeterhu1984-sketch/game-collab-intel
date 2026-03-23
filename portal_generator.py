# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - Web门户生成器
====================================
生成情报站总入口页面，汇聚所有日报和全局统计
"""

import os
import json
from datetime import datetime, timedelta
from config import BASE_DIR, PORTAL_DIR, REPORTS_DIR, TARGET_GAMES, BRAND_CATEGORIES
from database import (
    init_database, get_statistics, get_available_dates,
    get_available_games, get_collaborations
)


def generate_portal():
    """生成情报站门户页面"""
    init_database()
    os.makedirs(PORTAL_DIR, exist_ok=True)
    
    # 获取全局数据
    stats = get_statistics()
    dates = get_available_dates()
    games = get_available_games()
    
    # 获取最近7天的高热度情报
    hot_items = get_collaborations(limit=20, order_by="hot_score DESC")
    
    # 获取最新情报
    latest_items = get_collaborations(limit=30, order_by="created_at DESC")
    
    # 检查已生成的日报文件
    report_files = []
    if os.path.exists(REPORTS_DIR):
        for f in sorted(os.listdir(REPORTS_DIR), reverse=True):
            if f.startswith("daily_") and f.endswith(".html"):
                date_str = f.replace("daily_", "").replace(".html", "")
                report_files.append({
                    "date": date_str,
                    "filename": f,
                    "path": f"../reports/{f}",
                })
    
    html = build_portal_html(stats, dates, games, hot_items, latest_items, report_files)
    
    portal_path = os.path.join(PORTAL_DIR, "index.html")
    with open(portal_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[门户] 已生成: {portal_path}")
    print(f"  - 累计情报: {stats['total']} 条")
    print(f"  - 日报数量: {len(report_files)} 份")
    print(f"  - 涉及游戏: {len(games)} 个")
    return portal_path


def build_portal_html(stats, dates, games, hot_items, latest_items, report_files):
    """构建门户页面HTML"""
    
    total = stats.get("total", 0)
    game_count = len(stats.get("by_game", []))
    cat_count = len(stats.get("by_category", []))
    date_range = stats.get("date_range", {})
    report_count = len(report_files)
    
    # === 日报列表 ===
    report_cards_html = ""
    for r in report_files[:30]:
        # 获取该日期的统计
        day_items = get_collaborations(date=r["date"], limit=1)
        day_count = len(get_collaborations(date=r["date"], limit=500))
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        try:
            dt = datetime.strptime(r["date"], "%Y-%m-%d")
            weekday = weekday_names[dt.weekday()]
        except:
            weekday = ""
        
        report_cards_html += f"""
        <a href="{r['path']}" class="report-card">
            <div class="report-date-big">{r['date'][-2:]}</div>
            <div class="report-info">
                <div class="report-date-full">{r['date']} {weekday}</div>
                <div class="report-count">{day_count} 条情报</div>
            </div>
            <div class="report-arrow">→</div>
        </a>
        """
    
    if not report_cards_html:
        report_cards_html = """
        <div class="empty-hint">
            <div style="font-size:2em;margin-bottom:8px">📭</div>
            <div>暂无日报，运行采集后生成第一份日报</div>
        </div>
        """
    
    # === 热门情报 ===
    hot_cards_html = ""
    for idx, item in enumerate(hot_items[:12]):
        tags_html = ""
        if item.get("game_name"):
            tags_html += f'<span class="tag tag-game">{item["game_name"]}</span>'
        if item.get("brand_name"):
            tags_html += f'<span class="tag tag-brand">{item["brand_name"]}</span>'
        if item.get("collab_type"):
            tags_html += f'<span class="tag tag-type">{item["collab_type"]}</span>'
        
        score = item.get("hot_score", 0)
        score_class = "hot" if score >= 60 else "warm" if score >= 30 else "cool"
        rank_badge = f'<div class="rank-badge rank-{idx+1}">#{idx+1}</div>' if idx < 3 else f'<div class="rank-badge">#{idx+1}</div>'
        
        url = item.get("source_url", "")
        card_tag = f'<a href="{url}" target="_blank" class="hot-card">' if url else '<div class="hot-card">'
        card_close = '</a>' if url else '</div>'
        
        hot_cards_html += f"""
        {card_tag}
            {rank_badge}
            <div class="hot-content">
                <div class="hot-title">{item['title']}</div>
                <div class="hot-meta">
                    <div class="card-tags">{tags_html}</div>
                    <span class="score-mini {score_class}">{score}分</span>
                </div>
                <div class="hot-summary">{item.get('summary', '')[:120]}</div>
            </div>
        {card_close}
        """
    
    if not hot_cards_html:
        hot_cards_html = '<div class="empty-hint">暂无数据，请先运行数据采集</div>'
    
    # === 最新情报流 ===
    latest_html = ""
    for item in latest_items[:15]:
        tags_mini = ""
        if item.get("game_name"):
            tags_mini += f'<span class="tag-mini tag-game">{item["game_name"]}</span>'
        if item.get("brand_name"):
            tags_mini += f'<span class="tag-mini tag-brand">{item["brand_name"]}</span>'
        
        url = item.get("source_url", "")
        feed_tag = f'<a href="{url}" target="_blank" class="feed-item">' if url else '<div class="feed-item">'
        feed_close = '</a>' if url else '</div>'
        
        latest_html += f"""
        {feed_tag}
            <div class="feed-dot"></div>
            <div class="feed-content">
                <div class="feed-title">{item['title']}</div>
                <div class="feed-meta">
                    {tags_mini}
                    <span class="feed-date">{item.get('collected_date', '')}</span>
                </div>
            </div>
        {feed_close}
        """
    
    # === 品牌类别分布 ===
    cat_chart_labels = json.dumps([c["name"] for c in stats.get("by_category", [])], ensure_ascii=False)
    cat_chart_values = json.dumps([c["count"] for c in stats.get("by_category", [])])
    
    # === 当前时间 ===
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 游戏异业合作情报站</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #6C5CE7;
            --primary-light: #A29BFE;
            --primary-dark: #5541D7;
            --accent: #FD79A8;
            --accent2: #FDCB6E;
            --green: #00B894;
            --green-light: #55EFC4;
            --blue: #74B9FF;
            --red: #FF6B6B;
            --orange: #F39C12;
            --bg: #0F0E17;
            --bg2: #141425;
            --bg-card: #1A1A2E;
            --bg-card-hover: #232347;
            --text: #FFFFFE;
            --text-muted: #94A1B2;
            --text-dim: #5C6378;
            --border: #2D2D52;
            --border-light: #3D3D62;
            --shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        /* ===== 导航栏 ===== */
        .navbar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(15,14,23,0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 56px;
        }}
        
        .nav-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1em;
            font-weight: 700;
        }}
        
        .nav-logo span {{
            background: linear-gradient(135deg, #FD79A8, #FDCB6E);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .nav-links {{
            display: flex;
            gap: 4px;
        }}
        
        .nav-links a {{
            color: var(--text-muted);
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9em;
            transition: all 0.3s;
        }}
        
        .nav-links a:hover, .nav-links a.active {{
            color: var(--text);
            background: rgba(108,92,231,0.15);
        }}
        
        .nav-time {{
            color: var(--text-dim);
            font-size: 0.8em;
        }}
        
        /* ===== 主 Hero ===== */
        .hero {{
            padding: 60px 24px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: -100%;
            left: -50%;
            width: 200%;
            height: 300%;
            background: 
                radial-gradient(ellipse at 25% 50%, rgba(108,92,231,0.12) 0%, transparent 60%),
                radial-gradient(ellipse at 75% 30%, rgba(253,121,168,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(0,184,148,0.06) 0%, transparent 50%);
            animation: heroFloat 20s ease-in-out infinite;
        }}
        
        @keyframes heroFloat {{
            0%, 100% {{ transform: translate(0, 0) rotate(0deg); }}
            33% {{ transform: translate(-15px, -10px) rotate(1deg); }}
            66% {{ transform: translate(10px, -5px) rotate(-1deg); }}
        }}
        
        .hero h1 {{
            font-size: 2.8em;
            font-weight: 800;
            position: relative;
            z-index: 1;
            background: linear-gradient(135deg, #FD79A8, #FDCB6E, #A29BFE);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }}
        
        .hero .subtitle {{
            color: var(--text-muted);
            font-size: 1.15em;
            margin-top: 12px;
            position: relative;
            z-index: 1;
        }}
        
        /* ===== 全局统计卡片 ===== */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
        }}
        
        .section {{
            margin: 32px 0;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        
        .section-title {{
            font-size: 1.3em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-title .icon {{
            font-size: 1.2em;
        }}
        
        .section-more {{
            color: var(--primary-light);
            text-decoration: none;
            font-size: 0.9em;
            transition: color 0.3s;
        }}
        
        .section-more:hover {{ color: var(--accent); }}
        
        .mega-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}
        
        .mega-stat {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }}
        
        .mega-stat:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow);
            border-color: var(--primary);
        }}
        
        .mega-stat::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            border-radius: 0 0 16px 16px;
        }}
        
        .mega-stat:nth-child(1)::after {{ background: linear-gradient(90deg, #6C5CE7, #A29BFE); }}
        .mega-stat:nth-child(2)::after {{ background: linear-gradient(90deg, #FD79A8, #FDCB6E); }}
        .mega-stat:nth-child(3)::after {{ background: linear-gradient(90deg, #00B894, #55EFC4); }}
        .mega-stat:nth-child(4)::after {{ background: linear-gradient(90deg, #74B9FF, #A29BFE); }}
        .mega-stat:nth-child(5)::after {{ background: linear-gradient(90deg, #FDCB6E, #F39C12); }}
        
        .mega-num {{
            font-size: 2.8em;
            font-weight: 800;
            line-height: 1;
        }}
        
        .mega-stat:nth-child(1) .mega-num {{ color: #A29BFE; }}
        .mega-stat:nth-child(2) .mega-num {{ color: #FD79A8; }}
        .mega-stat:nth-child(3) .mega-num {{ color: #00B894; }}
        .mega-stat:nth-child(4) .mega-num {{ color: #74B9FF; }}
        .mega-stat:nth-child(5) .mega-num {{ color: #FDCB6E; }}
        
        .mega-label {{
            color: var(--text-muted);
            font-size: 0.9em;
            margin-top: 8px;
        }}
        
        /* ===== 双列布局 ===== */
        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .three-col {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }}
        
        /* ===== 图表卡片 ===== */
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
        }}
        
        .chart-card h3 {{
            color: var(--primary-light);
            font-size: 1em;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        
        /* ===== 日报列表 ===== */
        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}
        
        .report-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            text-decoration: none;
            color: var(--text);
            transition: all 0.3s;
        }}
        
        .report-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--primary-light);
            transform: translateX(4px);
        }}
        
        .report-date-big {{
            font-size: 2em;
            font-weight: 800;
            color: var(--primary-light);
            min-width: 48px;
            text-align: center;
            line-height: 1;
        }}
        
        .report-info {{
            flex: 1;
        }}
        
        .report-date-full {{
            font-size: 0.9em;
            color: var(--text-muted);
        }}
        
        .report-count {{
            font-size: 0.85em;
            color: var(--accent);
            margin-top: 2px;
        }}
        
        .report-arrow {{
            color: var(--text-dim);
            font-size: 1.2em;
            transition: transform 0.3s;
        }}
        
        .report-card:hover .report-arrow {{
            transform: translateX(4px);
            color: var(--primary-light);
        }}
        
        /* ===== 热门情报 ===== */
        .hot-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            gap: 14px;
            align-items: flex-start;
            transition: all 0.3s;
            margin-bottom: 10px;
            text-decoration: none;
            color: var(--text);
            cursor: pointer;
        }}
        
        .hot-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--primary-light);
            transform: translateX(4px);
        }}
        
        .rank-badge {{
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.8em;
            background: rgba(108,92,231,0.15);
            color: var(--primary-light);
        }}
        
        .rank-badge.rank-1 {{ background: linear-gradient(135deg, #FF6B6B, #FD79A8); color: white; }}
        .rank-badge.rank-2 {{ background: linear-gradient(135deg, #FDCB6E, #F39C12); color: #333; }}
        .rank-badge.rank-3 {{ background: linear-gradient(135deg, #74B9FF, #6C5CE7); color: white; }}
        
        .hot-content {{ flex: 1; min-width: 0; }}
        
        .hot-title {{
            font-size: 0.95em;
            font-weight: 600;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .hot-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
            flex-wrap: wrap;
        }}
        
        .hot-summary {{
            color: var(--text-muted);
            font-size: 0.8em;
            margin-top: 6px;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .source-link {{
            color: var(--primary-light);
            text-decoration: none;
            font-size: 0.85em;
        }}
        
        .source-link:hover {{ color: var(--accent); }}
        
        .score-mini {{
            font-size: 0.75em;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 6px;
        }}
        
        .score-mini.hot {{ background: rgba(255,107,107,0.15); color: #FF6B6B; }}
        .score-mini.warm {{ background: rgba(253,203,110,0.15); color: #FDCB6E; }}
        .score-mini.cool {{ background: rgba(108,92,231,0.15); color: #A29BFE; }}
        
        /* ===== 最新情报流 ===== */
        .feed-item {{
            display: flex;
            gap: 14px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(45,45,82,0.5);
            align-items: flex-start;
            text-decoration: none;
            color: var(--text);
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .feed-item:hover {{
            background: rgba(108,92,231,0.06);
            border-radius: 8px;
            padding-left: 8px;
            margin-left: -8px;
        }}
        
        .feed-item:last-child {{ border-bottom: none; }}
        
        .feed-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary);
            margin-top: 8px;
            flex-shrink: 0;
        }}
        
        .feed-content {{ flex: 1; min-width: 0; }}
        
        .feed-title {{
            font-size: 0.9em;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .feed-meta {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 4px;
            flex-wrap: wrap;
        }}
        
        .feed-date {{
            color: var(--text-dim);
            font-size: 0.75em;
        }}
        
        /* ===== 游戏排行 ===== */
        .rank-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
        }}
        
        .rank-num {{
            width: 24px;
            text-align: center;
            font-weight: 700;
            font-size: 0.9em;
            color: var(--text-dim);
        }}
        
        .rank-item:nth-child(1) .rank-num {{ color: #FF6B6B; }}
        .rank-item:nth-child(2) .rank-num {{ color: #FDCB6E; }}
        .rank-item:nth-child(3) .rank-num {{ color: #74B9FF; }}
        
        .rank-name {{
            min-width: 80px;
            font-size: 0.9em;
        }}
        
        .rank-bar-bg {{
            flex: 1;
            height: 8px;
            background: rgba(108,92,231,0.1);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .rank-bar {{
            height: 100%;
            background: linear-gradient(90deg, #6C5CE7, #A29BFE);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        
        .rank-count {{
            min-width: 30px;
            text-align: right;
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        
        /* ===== Tags ===== */
        .tag, .tag-mini {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 500;
            display: inline-block;
        }}
        
        .tag-mini {{
            padding: 1px 6px;
            font-size: 0.7em;
        }}
        
        .tag-game {{ background: rgba(108,92,231,0.15); color: var(--primary-light); }}
        .tag-brand {{ background: rgba(253,121,168,0.15); color: #FD79A8; }}
        .tag-type {{ background: rgba(253,203,110,0.15); color: #FDCB6E; }}
        .tag-cat {{ background: rgba(0,184,148,0.15); color: #00B894; }}
        
        /* ===== 空提示 ===== */
        .empty-hint {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-dim);
        }}
        
        /* ===== Footer ===== */
        .footer {{
            text-align: center;
            padding: 40px 24px;
            color: var(--text-dim);
            font-size: 0.8em;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
        
        .footer a {{
            color: var(--primary-light);
            text-decoration: none;
        }}
        
        /* ===== 响应式 ===== */
        @media (max-width: 1024px) {{
            .three-col {{ grid-template-columns: 1fr; }}
            .two-col {{ grid-template-columns: 1fr; }}
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.8em; }}
            .mega-stats {{ grid-template-columns: repeat(2, 1fr); }}
            .reports-grid {{ grid-template-columns: 1fr; }}
            .navbar {{ padding: 0 12px; }}
            .nav-links {{ display: none; }}
        }}
        
        /* ===== 滚动条 ===== */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--primary); }}
        
        /* ===== 动画 ===== */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .section {{
            animation: fadeInUp 0.6s ease both;
        }}
        
        .section:nth-child(2) {{ animation-delay: 0.1s; }}
        .section:nth-child(3) {{ animation-delay: 0.2s; }}
        .section:nth-child(4) {{ animation-delay: 0.3s; }}
        .section:nth-child(5) {{ animation-delay: 0.4s; }}
    </style>
</head>
<body>

<!-- 导航栏 -->
<nav class="navbar">
    <div class="nav-logo">🎮 <span>游戏异业合作情报站</span></div>
    <div class="nav-links">
        <a href="#overview" class="active">总览</a>
        <a href="#reports">日报</a>
        <a href="#hot">热门</a>
        <a href="#trends">趋势</a>
        <a href="#rankings">排行</a>
    </div>
    <div class="nav-time">更新于 {now_str}</div>
</nav>

<!-- Hero -->
<div class="hero">
    <h1>🎮 游戏异业合作情报站</h1>
    <p class="subtitle">自动追踪 {len(TARGET_GAMES)} 款热门游戏 × {len(BRAND_CATEGORIES)} 大品牌类别的跨界合作动态</p>
</div>

<div class="container">
    
    <!-- 全局统计 -->
    <div class="section" id="overview">
        <div class="mega-stats">
            <div class="mega-stat">
                <div class="mega-num">{total}</div>
                <div class="mega-label">累计情报总量</div>
            </div>
            <div class="mega-stat">
                <div class="mega-num">{game_count}</div>
                <div class="mega-label">涉及游戏数</div>
            </div>
            <div class="mega-stat">
                <div class="mega-num">{cat_count}</div>
                <div class="mega-label">品牌类别</div>
            </div>
            <div class="mega-stat">
                <div class="mega-num">{report_count}</div>
                <div class="mega-label">日报总数</div>
            </div>
            <div class="mega-stat">
                <div class="mega-num">{len(dates)}</div>
                <div class="mega-label">采集天数</div>
            </div>
        </div>
    </div>
    
    <!-- 趋势图表 -->
    <div class="section" id="trends">
        <div class="section-header">
            <div class="section-title"><span class="icon">📈</span> 数据趋势与分布</div>
        </div>
        <div style="max-width:500px;margin:0 auto">
            <div class="chart-card">
                <h3>🏷️ 品牌类别分布</h3>
                <div style="position:relative;height:320px">
                    <canvas id="catChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 日报列表 -->
    <div class="section" id="reports">
        <div class="section-header">
            <div class="section-title"><span class="icon">📋</span> 每日情报日报</div>
        </div>
        <div class="reports-grid">
            {report_cards_html}
        </div>
    </div>
    
    <!-- 热门情报 + 最新动态 -->
    <div class="section" id="hot">
        <div class="two-col">
            <div>
                <div class="section-header">
                    <div class="section-title"><span class="icon">🔥</span> 热门情报 TOP12</div>
                </div>
                {hot_cards_html}
            </div>
            <div>
                <div class="section-header">
                    <div class="section-title"><span class="icon">⚡</span> 最新情报流</div>
                </div>
                <div class="chart-card" style="max-height:600px;overflow-y:auto">
                    {latest_html or '<div class="empty-hint">暂无数据</div>'}
                </div>
            </div>
        </div>
    </div>
    
</div>

<!-- Footer -->
<div class="footer">
    <p>🎮 游戏异业合作情报站 · 数据来源: Bing搜索 / Bing新闻 / RSS订阅</p>
    <p style="margin-top:4px">自动采集 · 智能分析 · 每日更新 · 生成时间 {now_str}</p>
</div>

<script>
// 图表通用配色
const colors = ['#6C5CE7','#FD79A8','#00B894','#FDCB6E','#74B9FF','#FF6B6B','#A29BFE','#55EFC4','#FAB1A0','#81ECEC'];
const chartOpts = {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#94A1B2', font: {{ size: 11 }} }} }} }}
}};

// 品牌类别饼图
new Chart(document.getElementById('catChart'), {{
    type: 'doughnut',
    data: {{
        labels: {cat_chart_labels},
        datasets: [{{ data: {cat_chart_values}, backgroundColor: colors, borderWidth: 0 }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        cutout: '55%',
        plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#94A1B2', font: {{ size: 12 }}, padding: 16 }} }} }}
    }}
}});

// 平滑滚动
document.querySelectorAll('.nav-links a').forEach(link => {{
    link.addEventListener('click', e => {{
        e.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if (target) {{
            target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
    }});
}});

// 滚动高亮导航
const sections = document.querySelectorAll('.section[id]');
window.addEventListener('scroll', () => {{
    let current = '';
    sections.forEach(section => {{
        const top = section.offsetTop - 100;
        if (window.scrollY >= top) current = section.id;
    }});
    document.querySelectorAll('.nav-links a').forEach(link => {{
        link.classList.toggle('active', link.getAttribute('href') === '#' + current);
    }});
}});
</script>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    portal_path = generate_portal()
    print(f"门户页面已生成: {portal_path}")

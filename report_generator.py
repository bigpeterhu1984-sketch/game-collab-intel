# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - 每日报告生成器
====================================
生成精美的每日情报汇总HTML报告
"""

import os
import json
from datetime import datetime, timedelta
from config import BASE_DIR, REPORTS_DIR
from database import (
    init_database, get_collaborations, get_statistics,
    get_available_dates, save_daily_report
)


def generate_daily_report(date=None):
    """
    生成指定日期的每日情报报告
    Args:
        date: 日期字符串 'YYYY-MM-DD'，默认今天
    Returns:
        报告HTML文件路径
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # 获取数据
    items = get_collaborations(date=date, limit=200, order_by="hot_score DESC")
    stats = get_statistics(date=date)
    all_stats = get_statistics()
    
    report_path = os.path.join(REPORTS_DIR, f"daily_{date}.html")
    
    # 构建报告
    html = build_report_html(date, items, stats, all_stats)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 保存报告记录
    save_daily_report({
        "report_date": date,
        "total_items": len(items),
        "new_items": len(items),
        "top_games": [g["name"] for g in stats.get("by_game", [])[:5]],
        "top_brands": [],
        "top_categories": [c["name"] for c in stats.get("by_category", [])[:5]],
        "highlights": [item["title"] for item in items[:5]],
        "report_html_path": report_path,
    })
    
    print(f"[报告] 已生成: {report_path} ({len(items)} 条情报)")
    return report_path


def build_report_html(date, items, stats, all_stats):
    """构建报告HTML"""
    
    # 按品牌类别分组
    by_category = {}
    for item in items:
        cat = item.get("brand_category") or "其他"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    # 按游戏分组
    by_game = {}
    for item in items:
        game = item.get("game_name") or "其他游戏"
        if game not in by_game:
            by_game[game] = []
        by_game[game].append(item)
    
    # ===== 构建「联动速览」模块数据 =====
    # 游戏清单（去重 + 计数）
    game_counter = {}
    brand_counter = {}  # {品牌名: {"count": N, "category": "类别"}}
    collab_pairs = {}   # {(游戏, 品牌): {"count": N, "types": set(), "category": "类别"}}
    
    for item in items:
        g = item.get("game_name", "").strip()
        b = item.get("brand_name", "").strip()
        cat = item.get("brand_category", "").strip()
        ctype = item.get("collab_type", "").strip()
        
        if g:
            game_counter[g] = game_counter.get(g, 0) + 1
        if b:
            if b not in brand_counter:
                brand_counter[b] = {"count": 0, "category": cat or "其他"}
            brand_counter[b]["count"] += 1
        if g and b:
            key = (g, b)
            if key not in collab_pairs:
                collab_pairs[key] = {"count": 0, "types": set(), "category": cat or "其他"}
            collab_pairs[key]["count"] += 1
            if ctype:
                collab_pairs[key]["types"].add(ctype)
    
    # 排序
    sorted_games = sorted(game_counter.items(), key=lambda x: x[1], reverse=True)
    sorted_brands = sorted(brand_counter.items(), key=lambda x: x[1]["count"], reverse=True)
    sorted_pairs = sorted(collab_pairs.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # 生成游戏标签 HTML
    game_tags_html = ""
    for gname, gcount in sorted_games:
        game_tags_html += f'<span class="glance-tag glance-game">{gname}<em>{gcount}</em></span>'
    
    # 生成品牌标签 HTML（按类别分组）
    brand_by_cat = {}
    for bname, binfo in sorted_brands:
        cat = binfo["category"]
        if cat not in brand_by_cat:
            brand_by_cat[cat] = []
        brand_by_cat[cat].append((bname, binfo["count"]))
    
    brand_groups_html = ""
    cat_colors = {
        "餐饮": "#FF6B6B", "快消": "#FDCB6E", "美妆个护": "#FD79A8",
        "服饰潮牌": "#A29BFE", "3C数码": "#74B9FF", "汽车出行": "#00B894",
        "零售电商": "#00CEC9", "金融支付": "#FAB1A0", "文旅酒店": "#81ECEC",
        "其他": "#94A1B2",
    }
    for cat, brands in brand_by_cat.items():
        color = cat_colors.get(cat, "#94A1B2")
        brand_items = ""
        for bname, bcount in brands:
            brand_items += f'<span class="glance-tag glance-brand" style="border-color:{color}40;color:{color}">{bname}<em>{bcount}</em></span>'
        brand_groups_html += f'<div class="brand-group"><span class="brand-cat-label" style="background:{color}22;color:{color};border:1px solid {color}40">{cat}</span>{brand_items}</div>'
    
    # 生成联动配对表 HTML
    pair_rows_html = ""
    for idx, ((gname, bname), pinfo) in enumerate(sorted_pairs):
        types_str = "、".join(pinfo["types"]) if pinfo["types"] else "—"
        cat = pinfo["category"]
        cat_color = cat_colors.get(cat, "#94A1B2")
        pair_rows_html += f"""
        <tr>
            <td><span class="pair-game">{gname}</span></td>
            <td class="pair-x">×</td>
            <td><span class="pair-brand">{bname}</span></td>
            <td><span class="pair-cat" style="color:{cat_color}">{cat}</span></td>
            <td><span class="pair-type">{types_str}</span></td>
            <td class="pair-count">{pinfo['count']}</td>
        </tr>"""
    
    # 构建完整的联动速览区块
    collab_glance_html = f"""
    <!-- 联动速览模块 -->
    <div class="glance-section">
        <h2 class="section-title"><span class="section-icon">🔗</span> 联动速览</h2>
        <p class="section-desc">今日情报涉及 <strong>{len(sorted_games)}</strong> 款游戏、<strong>{len(sorted_brands)}</strong> 个品牌，共 <strong>{len(sorted_pairs)}</strong> 组联动配对</p>
        
        <div class="glance-grid">
            <!-- 游戏清单 -->
            <div class="glance-box">
                <h3 class="glance-box-title">🎮 涉及游戏 ({len(sorted_games)})</h3>
                <div class="glance-tags">{game_tags_html if game_tags_html else '<span class="glance-empty">暂无</span>'}</div>
            </div>
            
            <!-- 品牌清单 -->
            <div class="glance-box">
                <h3 class="glance-box-title">🏢 涉及品牌 ({len(sorted_brands)})</h3>
                <div class="glance-brands">{brand_groups_html if brand_groups_html else '<span class="glance-empty">暂无</span>'}</div>
            </div>
        </div>
        
        <!-- 联动配对表 -->
        {"" if not pair_rows_html else f'''
        <div class="glance-box glance-pairs-box">
            <h3 class="glance-box-title">🤝 联动配对一览 ({len(sorted_pairs)})</h3>
            <div class="pairs-table-wrap">
                <table class="pairs-table">
                    <thead>
                        <tr><th>游戏</th><th></th><th>品牌</th><th>类别</th><th>合作类型</th><th>情报数</th></tr>
                    </thead>
                    <tbody>{pair_rows_html}</tbody>
                </table>
            </div>
        </div>'''}
    </div>
    """ if items else ""
    
    # 生成卡片HTML
    cards_html = ""
    for item in items:
        tags_html = ""
        if item.get("game_name"):
            tags_html += f'<span class="tag tag-game">{item["game_name"]}</span>'
        if item.get("brand_name"):
            tags_html += f'<span class="tag tag-brand">{item["brand_name"]}</span>'
        if item.get("brand_category"):
            tags_html += f'<span class="tag tag-cat">{item["brand_category"]}</span>'
        if item.get("collab_type"):
            tags_html += f'<span class="tag tag-type">{item["collab_type"]}</span>'
        
        score_class = "hot" if item.get("hot_score", 0) >= 60 else "warm" if item.get("hot_score", 0) >= 30 else "cool"
        
        source_info = item.get("source_name", "") or item.get("source_type", "")
        
        cards_html += f"""
        <div class="intel-card" data-game="{item.get('game_name','')}" 
             data-category="{item.get('brand_category','')}" 
             data-type="{item.get('collab_type','')}"
             onclick="showDetail({item['id']})">
            <div class="card-header">
                <div class="score-badge {score_class}">{item.get('hot_score', 0)}</div>
                <h3 class="card-title">{item['title']}</h3>
            </div>
            <div class="card-body">
                <p class="card-summary">{item.get('summary', '')[:150]}</p>
                <div class="card-tags">{tags_html}</div>
            </div>
            <div class="card-footer">
                <span class="source">{source_info}</span>
                <span class="date">{item.get('published_date', '')[:10] or item.get('collected_date', '')}</span>
            </div>
        </div>
        """
    
    # 统计图表数据
    game_chart_data = json.dumps([g["name"] for g in stats.get("by_game", [])[:10]], ensure_ascii=False)
    game_chart_values = json.dumps([g["count"] for g in stats.get("by_game", [])[:10]])
    cat_chart_data = json.dumps([c["name"] for c in stats.get("by_category", [])], ensure_ascii=False)
    cat_chart_values = json.dumps([c["count"] for c in stats.get("by_category", [])])
    type_chart_data = json.dumps([t["name"] for t in stats.get("by_type", [])[:8]], ensure_ascii=False)
    type_chart_values = json.dumps([t["count"] for t in stats.get("by_type", [])[:8]])
    
    # 日期趋势数据
    trend_dates = json.dumps([d["date"] for d in all_stats.get("by_date", [])], ensure_ascii=False)
    trend_values = json.dumps([d["count"] for d in all_stats.get("by_date", [])])
    
    # 筛选选项
    game_options = ""
    for g in stats.get("by_game", []):
        game_options += f'<option value="{g["name"]}">{g["name"]} ({g["count"]})</option>'
    
    cat_options = ""
    for c in stats.get("by_category", []):
        cat_options += f'<option value="{c["name"]}">{c["name"]} ({c["count"]})</option>'
    
    # 全部条目的JSON数据（供详情弹窗使用）
    items_json = json.dumps(
        [{k: v for k, v in item.items() if k != "full_content"} for item in items],
        ensure_ascii=False
    )
    all_items_json = json.dumps(
        items,
        ensure_ascii=False
    )
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮 游戏异业合作日报 - {date}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #6C5CE7;
            --primary-light: #A29BFE;
            --accent: #FD79A8;
            --accent2: #FDCB6E;
            --bg: #0F0E17;
            --bg-card: #1A1A2E;
            --bg-card-hover: #232347;
            --text: #FFFFFE;
            --text-muted: #94A1B2;
            --border: #2D2D52;
            --success: #00B894;
            --warning: #FDCB6E;
            --danger: #FF6B6B;
            --gradient1: linear-gradient(135deg, #6C5CE7, #A29BFE);
            --gradient2: linear-gradient(135deg, #FD79A8, #FDCB6E);
            --gradient3: linear-gradient(135deg, #00B894, #00CEC9);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        /* 顶部背景动画 */
        .hero {{
            background: linear-gradient(135deg, #0F0E17 0%, #1A1A2E 50%, #16213E 100%);
            padding: 40px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
            border-bottom: 1px solid var(--border);
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 50%, rgba(108,92,231,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 70% 50%, rgba(253,121,168,0.08) 0%, transparent 50%);
            animation: float 15s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translate(0, 0); }}
            50% {{ transform: translate(-20px, -20px); }}
        }}
        
        .hero h1 {{
            font-size: 2.2em;
            background: var(--gradient2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            z-index: 1;
        }}
        
        .hero .subtitle {{
            color: var(--text-muted);
            margin-top: 8px;
            font-size: 1.1em;
            position: relative;
            z-index: 1;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* 统计卡片 */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(108,92,231,0.2);
            border-color: var(--primary);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: 800;
            background: var(--gradient1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-card:nth-child(2) .stat-number {{
            background: var(--gradient2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stat-card:nth-child(3) .stat-number {{
            background: var(--gradient3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stat-label {{
            color: var(--text-muted);
            font-size: 0.9em;
            margin-top: 4px;
        }}
        
        /* 图表区 */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 24px 0;
        }}
        
        .chart-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
        }}
        
        .chart-box h3 {{
            margin-bottom: 16px;
            color: var(--primary-light);
            font-size: 1em;
        }}
        
        /* 筛选栏 */
        .filter-bar {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px 20px;
            margin: 24px 0;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-bar label {{
            color: var(--text-muted);
            font-size: 0.9em;
        }}
        
        .filter-bar select, .filter-bar input {{
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 0.9em;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .filter-bar select:focus, .filter-bar input:focus {{
            border-color: var(--primary);
        }}
        
        .filter-bar .search-input {{
            flex: 1;
            min-width: 200px;
        }}
        
        .filter-btn {{
            background: var(--gradient1);
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9em;
            transition: opacity 0.3s;
        }}
        
        .filter-btn:hover {{ opacity: 0.85; }}
        
        .reset-btn {{
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9em;
        }}
        
        /* 情报卡片 */
        .cards-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        
        .intel-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            flex-direction: column;
        }}
        
        .intel-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(108,92,231,0.15);
            border-color: var(--primary-light);
            background: var(--bg-card-hover);
        }}
        
        .card-header {{
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }}
        
        .score-badge {{
            flex-shrink: 0;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.85em;
        }}
        
        .score-badge.hot {{
            background: linear-gradient(135deg, #FF6B6B, #FD79A8);
            color: white;
        }}
        
        .score-badge.warm {{
            background: linear-gradient(135deg, #FDCB6E, #F39C12);
            color: #333;
        }}
        
        .score-badge.cool {{
            background: rgba(108,92,231,0.2);
            color: var(--primary-light);
        }}
        
        .card-title {{
            font-size: 1em;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .card-body {{
            flex: 1;
            margin: 12px 0;
        }}
        
        .card-summary {{
            color: var(--text-muted);
            font-size: 0.85em;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .card-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }}
        
        .tag {{
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 500;
        }}
        
        .tag-game {{
            background: rgba(108,92,231,0.15);
            color: var(--primary-light);
            border: 1px solid rgba(108,92,231,0.3);
        }}
        
        .tag-brand {{
            background: rgba(253,121,168,0.15);
            color: #FD79A8;
            border: 1px solid rgba(253,121,168,0.3);
        }}
        
        .tag-cat {{
            background: rgba(0,184,148,0.15);
            color: #00B894;
            border: 1px solid rgba(0,184,148,0.3);
        }}
        
        .tag-type {{
            background: rgba(253,203,110,0.15);
            color: #FDCB6E;
            border: 1px solid rgba(253,203,110,0.3);
        }}
        
        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 12px;
            border-top: 1px solid var(--border);
            font-size: 0.8em;
            color: var(--text-muted);
        }}
        
        /* 详情弹窗 */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(8px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .modal-overlay.active {{ display: flex; }}
        
        .modal {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            width: 100%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
            padding: 32px;
            position: relative;
            animation: modalIn 0.3s ease;
        }}
        
        @keyframes modalIn {{
            from {{ opacity: 0; transform: scale(0.95) translateY(20px); }}
            to {{ opacity: 1; transform: scale(1) translateY(0); }}
        }}
        
        .modal-close {{
            position: absolute;
            top: 16px;
            right: 16px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1px solid var(--border);
            background: var(--bg);
            color: var(--text-muted);
            font-size: 1.2em;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }}
        
        .modal-close:hover {{
            background: var(--danger);
            color: white;
            border-color: var(--danger);
        }}
        
        .modal h2 {{
            font-size: 1.3em;
            margin-bottom: 16px;
            padding-right: 40px;
            line-height: 1.4;
        }}
        
        .modal .detail-row {{
            display: flex;
            gap: 8px;
            margin: 8px 0;
            align-items: baseline;
        }}
        
        .modal .detail-label {{
            color: var(--text-muted);
            font-size: 0.85em;
            min-width: 80px;
            flex-shrink: 0;
        }}
        
        .modal .detail-value {{
            font-size: 0.95em;
        }}
        
        .modal .detail-content {{
            margin-top: 20px;
            padding: 16px;
            background: var(--bg);
            border-radius: 12px;
            line-height: 1.8;
            font-size: 0.9em;
            color: var(--text-muted);
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
        
        .modal .detail-link {{
            display: inline-block;
            margin-top: 16px;
            padding: 10px 24px;
            background: var(--gradient1);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-size: 0.9em;
            transition: opacity 0.3s;
        }}
        
        .modal .detail-link:hover {{ opacity: 0.85; }}
        
        /* 空状态 */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }}
        
        .empty-state .icon {{ font-size: 4em; margin-bottom: 16px; }}
        
        /* 返回门户按钮 */
        .back-portal {{
            position: fixed;
            top: 20px;
            left: 20px;
            padding: 8px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.85em;
            z-index: 100;
            transition: all 0.3s;
        }}
        
        .back-portal:hover {{
            border-color: var(--primary);
            color: var(--primary-light);
        }}
        
        /* ===== 联动速览模块 ===== */
        .glance-section {{
            margin: 28px 0;
        }}
        
        .section-title {{
            font-size: 1.4em;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .section-icon {{ font-size: 1em; }}
        
        .section-desc {{
            color: var(--text-muted);
            font-size: 0.9em;
            margin-bottom: 18px;
        }}
        
        .section-desc strong {{
            color: var(--accent);
        }}
        
        .glance-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        
        .glance-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
        }}
        
        .glance-box-title {{
            font-size: 1em;
            color: var(--primary-light);
            margin-bottom: 14px;
        }}
        
        .glance-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .glance-tag {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.82em;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .glance-tag:hover {{
            transform: translateY(-2px);
        }}
        
        .glance-tag em {{
            font-style: normal;
            font-size: 0.85em;
            opacity: 0.7;
            background: rgba(255,255,255,0.1);
            padding: 1px 6px;
            border-radius: 10px;
        }}
        
        .glance-game {{
            background: rgba(108,92,231,0.12);
            color: var(--primary-light);
            border: 1px solid rgba(108,92,231,0.25);
        }}
        
        .glance-brand {{
            background: rgba(253,121,168,0.08);
            border: 1px solid rgba(253,121,168,0.2);
        }}
        
        .glance-brands {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .brand-group {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }}
        
        .brand-cat-label {{
            font-size: 0.75em;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 600;
            flex-shrink: 0;
        }}
        
        .glance-empty {{
            color: var(--text-muted);
            font-size: 0.85em;
            font-style: italic;
        }}
        
        .glance-pairs-box {{
            margin-top: 0;
        }}
        
        .pairs-table-wrap {{
            overflow-x: auto;
        }}
        
        .pairs-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88em;
        }}
        
        .pairs-table th {{
            text-align: left;
            padding: 10px 14px;
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.85em;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }}
        
        .pairs-table td {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(45,45,82,0.5);
            vertical-align: middle;
        }}
        
        .pairs-table tr:hover td {{
            background: rgba(108,92,231,0.05);
        }}
        
        .pair-game {{
            color: var(--primary-light);
            font-weight: 600;
        }}
        
        .pair-x {{
            text-align: center;
            color: var(--text-muted);
            font-weight: 300;
            font-size: 1.1em;
            padding: 10px 6px;
        }}
        
        .pair-brand {{
            color: var(--accent);
            font-weight: 600;
        }}
        
        .pair-cat {{
            font-size: 0.85em;
        }}
        
        .pair-type {{
            color: var(--text-muted);
            font-size: 0.85em;
        }}
        
        .pair-count {{
            text-align: center;
            font-weight: 700;
            color: var(--accent2);
        }}
        
        /* 响应式 */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.5em; }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .cards-container {{ grid-template-columns: 1fr; }}
            .filter-bar {{ flex-direction: column; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .glance-grid {{ grid-template-columns: 1fr; }}
        }}
        
        /* 滚动条 */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--primary); }}
    </style>
</head>
<body>

<a href="../portal/index.html" class="back-portal">← 返回情报站</a>

<div class="hero">
    <h1>🎮 游戏异业合作情报日报</h1>
    <p class="subtitle">📅 {date} &nbsp;|&nbsp; 共收录 {len(items)} 条情报</p>
</div>

<div class="container">
    <!-- 核心统计 -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{len(items)}</div>
            <div class="stat-label">今日情报总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(stats.get('by_game', []))}</div>
            <div class="stat-label">涉及游戏数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(stats.get('by_category', []))}</div>
            <div class="stat-label">品牌类别数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{all_stats.get('total', 0)}</div>
            <div class="stat-label">累计情报总量</div>
        </div>
    </div>

    {collab_glance_html}

    <!-- 图表 -->
    <div class="charts-grid">
        <div class="chart-box">
            <h3>📊 游戏分布 TOP10</h3>
            <canvas id="gameChart" height="200"></canvas>
        </div>
        <div class="chart-box">
            <h3>🏷️ 品牌类别分布</h3>
            <canvas id="catChart" height="200"></canvas>
        </div>
        <div class="chart-box">
            <h3>🤝 合作类型分布</h3>
            <canvas id="typeChart" height="200"></canvas>
        </div>
        <div class="chart-box">
            <h3>📈 近30天采集趋势</h3>
            <canvas id="trendChart" height="200"></canvas>
        </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
        <label>🔍</label>
        <input type="text" class="search-input" id="searchInput" placeholder="搜索标题、品牌、游戏..." oninput="filterCards()">
        <select id="gameFilter" onchange="filterCards()">
            <option value="">全部游戏</option>
            {game_options}
        </select>
        <select id="catFilter" onchange="filterCards()">
            <option value="">全部类别</option>
            {cat_options}
        </select>
        <button class="reset-btn" onclick="resetFilters()">重置</button>
    </div>

    <!-- 情报卡片 -->
    <div class="cards-container" id="cardsContainer">
        {cards_html if items else '<div class="empty-state"><div class="icon">📭</div><h3>今日暂无情报</h3><p>运行采集程序后，情报将在这里展示</p></div>'}
    </div>
</div>

<!-- 详情弹窗 -->
<div class="modal-overlay" id="modalOverlay" onclick="closeDetail(event)">
    <div class="modal" id="modalContent" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="closeModal()">×</button>
        <div id="modalBody"></div>
    </div>
</div>

<script>
// 所有条目数据
const allItems = {all_items_json};

// 图表配置
const chartColors = ['#6C5CE7','#FD79A8','#00B894','#FDCB6E','#74B9FF','#FF6B6B','#A29BFE','#55EFC4','#FAB1A0','#81ECEC'];
const chartDefaults = {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#94A1B2', font: {{ size: 11 }} }} }} }}
}};

// 游戏分布图
new Chart(document.getElementById('gameChart'), {{
    type: 'bar',
    data: {{
        labels: {game_chart_data},
        datasets: [{{ data: {game_chart_values}, backgroundColor: chartColors, borderRadius: 6 }}]
    }},
    options: {{ ...chartDefaults, indexAxis: 'y', plugins: {{ ...chartDefaults.plugins, legend: {{ display: false }} }},
        scales: {{ x: {{ ticks: {{ color: '#94A1B2' }}, grid: {{ color: '#2D2D52' }} }}, y: {{ ticks: {{ color: '#94A1B2' }}, grid: {{ display: false }} }} }}
    }}
}});

// 品牌类别图
new Chart(document.getElementById('catChart'), {{
    type: 'doughnut',
    data: {{
        labels: {cat_chart_data},
        datasets: [{{ data: {cat_chart_values}, backgroundColor: chartColors, borderWidth: 0 }}]
    }},
    options: {{ ...chartDefaults, cutout: '55%' }}
}});

// 合作类型图
new Chart(document.getElementById('typeChart'), {{
    type: 'polarArea',
    data: {{
        labels: {type_chart_data},
        datasets: [{{ data: {type_chart_values}, backgroundColor: chartColors.map(c => c + '88') }}]
    }},
    options: {{ ...chartDefaults, scales: {{ r: {{ ticks: {{ color: '#94A1B2' }}, grid: {{ color: '#2D2D52' }} }} }} }}
}});

// 趋势图
new Chart(document.getElementById('trendChart'), {{
    type: 'line',
    data: {{
        labels: {trend_dates},
        datasets: [{{ data: {trend_values}, borderColor: '#6C5CE7', backgroundColor: 'rgba(108,92,231,0.1)',
            fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#6C5CE7' }}]
    }},
    options: {{ ...chartDefaults, plugins: {{ ...chartDefaults.plugins, legend: {{ display: false }} }},
        scales: {{ x: {{ ticks: {{ color: '#94A1B2', maxTicksLimit: 10 }}, grid: {{ color: '#2D2D52' }} }},
                   y: {{ ticks: {{ color: '#94A1B2' }}, grid: {{ color: '#2D2D52' }}, beginAtZero: true }} }}
    }}
}});

// 筛选功能
function filterCards() {{
    const search = document.getElementById('searchInput').value.toLowerCase();
    const game = document.getElementById('gameFilter').value;
    const cat = document.getElementById('catFilter').value;
    
    document.querySelectorAll('.intel-card').forEach(card => {{
        const matchSearch = !search || card.textContent.toLowerCase().includes(search);
        const matchGame = !game || card.dataset.game === game;
        const matchCat = !cat || card.dataset.category === cat;
        card.style.display = (matchSearch && matchGame && matchCat) ? '' : 'none';
    }});
}}

function resetFilters() {{
    document.getElementById('searchInput').value = '';
    document.getElementById('gameFilter').value = '';
    document.getElementById('catFilter').value = '';
    filterCards();
}}

// 详情弹窗
function showDetail(id) {{
    const item = allItems.find(i => i.id === id);
    if (!item) return;
    
    let tagsHtml = '';
    if (item.game_name) tagsHtml += '<span class="tag tag-game">' + item.game_name + '</span>';
    if (item.brand_name) tagsHtml += '<span class="tag tag-brand">' + item.brand_name + '</span>';
    if (item.brand_category) tagsHtml += '<span class="tag tag-cat">' + item.brand_category + '</span>';
    if (item.collab_type) tagsHtml += '<span class="tag tag-type">' + item.collab_type + '</span>';
    
    let html = '<h2>' + item.title + '</h2>';
    html += '<div class="card-tags" style="margin-bottom:16px">' + tagsHtml + '</div>';
    
    const fields = [
        ['游戏', item.game_name],
        ['品牌', item.brand_name],
        ['品牌类别', item.brand_category],
        ['合作类型', item.collab_type],
        ['信息来源', item.source_name || item.source_type],
        ['发布日期', item.published_date],
        ['采集日期', item.collected_date],
        ['热度评分', item.hot_score + '/100'],
    ];
    
    fields.forEach(([label, value]) => {{
        if (value) {{
            html += '<div class="detail-row"><span class="detail-label">' + label + '：</span><span class="detail-value">' + value + '</span></div>';
        }}
    }});
    
    if (item.summary) {{
        html += '<div class="detail-row"><span class="detail-label">摘要：</span></div>';
        html += '<div class="detail-content">' + item.summary + '</div>';
    }}
    
    if (item.full_content) {{
        html += '<div class="detail-row" style="margin-top:16px"><span class="detail-label">正文内容：</span></div>';
        html += '<div class="detail-content">' + item.full_content + '</div>';
    }}
    
    if (item.source_url) {{
        html += '<a href="' + item.source_url + '" target="_blank" class="detail-link">🔗 查看原文</a>';
    }}
    
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modalOverlay').classList.add('active');
    document.body.style.overflow = 'hidden';
}}

function closeDetail(e) {{
    if (e.target === document.getElementById('modalOverlay')) closeModal();
}}

function closeModal() {{
    document.getElementById('modalOverlay').classList.remove('active');
    document.body.style.overflow = '';
}}

document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});
</script>
</body>
</html>"""
    
    return html


if __name__ == "__main__":
    init_database()
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = generate_daily_report(today)
    print(f"报告已生成: {report_path}")

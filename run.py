# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - 一键运行入口
====================================
整合采集、报告生成、门户更新的统一入口
支持命令行参数控制运行模式
"""

import sys
import os
import io
import argparse
import time
from datetime import datetime

# Windows GBK 兼容：强制 stdout/stderr 使用 UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """打印启动横幅"""
    print("""
╔══════════════════════════════════════════════════════╗
║  🎮  游戏异业合作情报站 - Game Collab Intel Hub     ║
║  ──────────────────────────────────────────────────  ║
║  自动采集 · 智能分析 · 每日报告 · 情报门户          ║
╚══════════════════════════════════════════════════════╝
    """)


def run_collect(fetch_content=False, max_queries=50):
    """执行数据采集"""
    print("=" * 55)
    print("📡 [步骤 1/3] 数据采集")
    print("=" * 55)
    
    from collector import run_collection
    from config import build_search_queries
    
    queries = build_search_queries(max_queries)
    result = run_collection(queries=queries, include_rss=True, fetch_content=fetch_content, verbose=True)
    return result


def run_report(date=None):
    """生成每日报告"""
    print("\n" + "=" * 55)
    print("📊 [步骤 2/3] 生成每日报告")
    print("=" * 55)
    
    from report_generator import generate_daily_report
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    report_path = generate_daily_report(date)
    print(f"  ✅ 报告已生成: {report_path}")
    return report_path


def run_portal():
    """更新门户页面"""
    print("\n" + "=" * 55)
    print("🌐 [步骤 3/3] 更新情报站门户")
    print("=" * 55)
    
    from portal_generator import generate_portal
    
    portal_path = generate_portal()
    print(f"  ✅ 门户已更新: {portal_path}")
    return portal_path


def run_init():
    """初始化数据库和目录"""
    print("🔧 初始化数据库和目录...")
    
    from database import init_database
    from config import REPORTS_DIR, PORTAL_DIR
    
    init_database()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(PORTAL_DIR, exist_ok=True)
    
    print("  ✅ 初始化完成")


def run_stats():
    """显示当前统计信息"""
    from database import init_database, get_statistics, get_available_dates
    
    init_database()
    stats = get_statistics()
    dates = get_available_dates()
    
    print("\n📈 当前数据库统计:")
    print(f"  累计情报: {stats['total']} 条")
    print(f"  采集天数: {len(dates)} 天")
    print(f"  日期范围: {stats['date_range']['min']} ~ {stats['date_range']['max']}")
    
    if stats.get("by_game"):
        print(f"\n  🎮 游戏TOP5:")
        for g in stats["by_game"][:5]:
            print(f"     {g['name']}: {g['count']} 条")
    
    if stats.get("by_category"):
        print(f"\n  🏷️ 品牌类别:")
        for c in stats["by_category"][:5]:
            print(f"     {c['name']}: {c['count']} 条")
    
    if stats.get("by_type"):
        print(f"\n  🤝 合作类型:")
        for t in stats["by_type"][:5]:
            print(f"     {t['name']}: {t['count']} 条")
    
    print()


def run_deploy_github():
    """同步 docs 目录并推送到 GitHub Pages"""
    print("\n" + "=" * 55)
    print("🚀 [部署] 同步到 GitHub Pages")
    print("=" * 55)
    
    import subprocess
    import shutil
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(project_dir, "docs")
    docs_reports = os.path.join(docs_dir, "reports")
    portal_src = os.path.join(project_dir, "portal", "index.html")
    reports_src = os.path.join(project_dir, "reports")
    git_exe = r"C:\Program Files\Git\cmd\git.exe"
    
    if not os.path.exists(git_exe):
        print("  ⚠️ Git 未安装，跳过部署")
        return False
    
    try:
        # 1. 同步门户到 docs/
        os.makedirs(docs_reports, exist_ok=True)
        if os.path.exists(portal_src):
            # 复制并修复链接路径
            with open(portal_src, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace('href="../reports/', 'href="reports/')
            with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(content)
            print("  ✅ 门户页面已同步到 docs/")
        
        # 2. 同步所有报告到 docs/reports/
        if os.path.exists(reports_src):
            for fname in os.listdir(reports_src):
                if fname.endswith(".html"):
                    shutil.copy2(
                        os.path.join(reports_src, fname),
                        os.path.join(docs_reports, fname)
                    )
            report_count = len([f for f in os.listdir(docs_reports) if f.endswith(".html")])
            print(f"  ✅ {report_count} 份日报已同步到 docs/reports/")
        
        # 3. Git add + commit + push
        def git_run(*args):
            result = subprocess.run(
                [git_exe] + list(args),
                cwd=project_dir,
                capture_output=True, text=True, encoding="utf-8"
            )
            return result
        
        git_run("add", "docs/")
        
        # 检查是否有变更
        status = git_run("status", "--porcelain", "docs/")
        if not status.stdout.strip():
            print("  ℹ️ 没有新的变更，跳过推送")
            return True
        
        today = datetime.now().strftime("%Y-%m-%d")
        git_run("commit", "-m", f"Update reports and portal - {today}")
        
        push_result = git_run("push", "origin", "main")
        if push_result.returncode == 0:
            print("  ✅ 已推送到 GitHub，Pages 将在 1-2 分钟内更新")
            print("  🔗 https://bigpeterhu1984-sketch.github.io/game-collab-intel/")
            return True
        else:
            print(f"  ❌ 推送失败: {push_result.stderr}")
            return False
    
    except Exception as e:
        print(f"  ❌ 部署异常: {e}")
        return False


def run_all(fetch_content=False, max_queries=50, date=None):
    """完整流程：采集 → 报告 → 门户 → 部署"""
    start_time = time.time()
    print_banner()
    print(f"🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 运行模式: 完整流程 (采集 → 报告 → 门户)")
    print()
    
    # 初始化
    run_init()
    
    # 采集
    collect_result = run_collect(fetch_content=fetch_content, max_queries=max_queries)
    
    # 报告
    report_path = run_report(date)
    
    # 门户
    portal_path = run_portal()
    
    # 部署到 GitHub Pages
    run_deploy_github()
    
    # 汇总
    elapsed = time.time() - start_time
    print("\n" + "=" * 55)
    print("🎉 全部完成！")
    print("=" * 55)
    print(f"  📊 采集结果: 发现 {collect_result['total_found']} 条, 新增 {collect_result['total_saved']} 条")
    print(f"  📄 日报文件: {report_path}")
    print(f"  🌐 门户页面: {portal_path}")
    print(f"  🔗 公网地址: https://bigpeterhu1984-sketch.github.io/game-collab-intel/")
    print(f"  ⏱  总耗时: {elapsed:.1f} 秒")
    print()
    
    # 显示统计
    run_stats()


def main():
    parser = argparse.ArgumentParser(
        description="🎮 游戏异业合作情报站 - 一键运行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行示例:
  python run.py                    # 完整流程：采集+报告+门户
  python run.py --collect-only     # 仅执行数据采集
  python run.py --report-only      # 仅生成今日报告
  python run.py --portal-only      # 仅更新门户页面
  python run.py --stats            # 查看统计数据
  python run.py --init             # 初始化数据库
  python run.py --date 2026-03-20  # 指定日期生成报告
  python run.py --fetch-content    # 采集时提取文章正文（较慢）
  python run.py --max-queries 20   # 限制搜索查询数量
  python run.py --deploy-only      # 仅同步部署到 GitHub Pages
        """
    )
    
    parser.add_argument("--collect-only", action="store_true", help="仅执行数据采集")
    parser.add_argument("--report-only", action="store_true", help="仅生成每日报告")
    parser.add_argument("--portal-only", action="store_true", help="仅更新门户页面")
    parser.add_argument("--deploy-only", action="store_true", help="仅同步部署到 GitHub Pages")
    parser.add_argument("--stats", action="store_true", help="显示统计数据")
    parser.add_argument("--init", action="store_true", help="初始化数据库和目录")
    parser.add_argument("--date", type=str, default=None, help="指定报告日期 (YYYY-MM-DD)")
    parser.add_argument("--fetch-content", action="store_true", help="采集时提取文章正文")
    parser.add_argument("--max-queries", type=int, default=50, help="最大搜索查询数 (默认50)")
    
    args = parser.parse_args()
    
    if args.init:
        print_banner()
        run_init()
        print("✅ 初始化完成！可以运行 python run.py 开始采集。")
    elif args.stats:
        print_banner()
        run_stats()
    elif args.collect_only:
        print_banner()
        run_init()
        run_collect(fetch_content=args.fetch_content, max_queries=args.max_queries)
    elif args.report_only:
        print_banner()
        run_init()
        run_report(args.date)
    elif args.portal_only:
        print_banner()
        run_init()
        run_portal()
    elif args.deploy_only:
        print_banner()
        run_deploy_github()
    else:
        run_all(
            fetch_content=args.fetch_content,
            max_queries=args.max_queries,
            date=args.date,
        )


if __name__ == "__main__":
    main()

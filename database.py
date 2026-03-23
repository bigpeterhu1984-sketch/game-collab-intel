# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - 数据库模块
================================
管理 SQLite 数据库，存储合作情报数据
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from contextlib import contextmanager
from config import DB_PATH


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_session():
    """数据库会话上下文管理器"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """初始化数据库表结构"""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 主表：合作情报
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collaborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                game_name TEXT,
                brand_name TEXT,
                brand_category TEXT,
                collab_type TEXT,
                source_url TEXT,
                source_name TEXT,
                source_type TEXT,
                image_url TEXT,
                published_date TEXT,
                collected_date TEXT NOT NULL,
                hot_score REAL DEFAULT 0,
                tags TEXT,
                full_content TEXT,
                extra_data TEXT,
                is_verified INTEGER DEFAULT 0,
                is_featured INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 每日报告表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT UNIQUE NOT NULL,
                total_items INTEGER DEFAULT 0,
                new_items INTEGER DEFAULT 0,
                top_games TEXT,
                top_brands TEXT,
                top_categories TEXT,
                highlights TEXT,
                report_html_path TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # 采集日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collect_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collect_time TEXT NOT NULL,
                source_type TEXT,
                query_keyword TEXT,
                results_found INTEGER DEFAULT 0,
                new_saved INTEGER DEFAULT 0,
                duplicates_skipped INTEGER DEFAULT 0,
                errors TEXT,
                duration_seconds REAL
            )
        """)
        
        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_game ON collaborations(game_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_brand ON collaborations(brand_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_category ON collaborations(brand_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_date ON collaborations(collected_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_hash ON collaborations(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collab_hot ON collaborations(hot_score DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_date ON daily_reports(report_date)")
        
        print("[DB] 数据库初始化完成")


def compute_content_hash(title, source_url=""):
    """计算内容哈希，用于去重"""
    raw = f"{title.strip().lower()}|{source_url.strip().lower()}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def save_collaboration(data: dict) -> bool:
    """
    保存一条合作情报
    返回 True 表示新增成功，False 表示已存在（去重）
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content_hash = compute_content_hash(data.get("title", ""), data.get("source_url", ""))
    
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO collaborations (
                    content_hash, title, summary, game_name, brand_name,
                    brand_category, collab_type, source_url, source_name,
                    source_type, image_url, published_date, collected_date,
                    hot_score, tags, full_content, extra_data,
                    is_verified, is_featured, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content_hash,
                data.get("title", ""),
                data.get("summary", ""),
                data.get("game_name", ""),
                data.get("brand_name", ""),
                data.get("brand_category", ""),
                data.get("collab_type", ""),
                data.get("source_url", ""),
                data.get("source_name", ""),
                data.get("source_type", ""),
                data.get("image_url", ""),
                data.get("published_date", ""),
                data.get("collected_date", now[:10]),
                data.get("hot_score", 0),
                json.dumps(data.get("tags", []), ensure_ascii=False) if data.get("tags") else "[]",
                data.get("full_content", ""),
                json.dumps(data.get("extra_data", {}), ensure_ascii=False) if data.get("extra_data") else "{}",
                data.get("is_verified", 0),
                data.get("is_featured", 0),
                now,
                now,
            ))
            return True
        except sqlite3.IntegrityError:
            return False


def get_collaborations(date=None, game=None, brand_category=None, 
                       search=None, limit=100, offset=0, order_by="collected_date DESC"):
    """查询合作情报"""
    conditions = []
    params = []
    
    if date:
        conditions.append("collected_date = ?")
        params.append(date)
    if game:
        conditions.append("game_name = ?")
        params.append(game)
    if brand_category:
        conditions.append("brand_category = ?")
        params.append(brand_category)
    if search:
        conditions.append("(title LIKE ? OR summary LIKE ? OR brand_name LIKE ? OR game_name LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern] * 4)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    sql = f"""
        SELECT * FROM collaborations 
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_collaboration_by_id(collab_id):
    """获取单条合作情报详情"""
    with db_session() as conn:
        cursor = conn.cursor()
        # 增加浏览次数
        cursor.execute("UPDATE collaborations SET view_count = view_count + 1 WHERE id = ?", (collab_id,))
        cursor.execute("SELECT * FROM collaborations WHERE id = ?", (collab_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_statistics(date=None):
    """获取统计数据"""
    with db_session() as conn:
        cursor = conn.cursor()
        stats = {}
        
        date_condition = "WHERE collected_date = ?" if date else ""
        params = [date] if date else []
        
        # 总数
        cursor.execute(f"SELECT COUNT(*) FROM collaborations {date_condition}", params)
        stats["total"] = cursor.fetchone()[0]
        
        # 按游戏统计
        cursor.execute(f"""
            SELECT game_name, COUNT(*) as cnt 
            FROM collaborations {date_condition}
            GROUP BY game_name ORDER BY cnt DESC LIMIT 15
        """, params)
        stats["by_game"] = [{"name": r[0] or "未知", "count": r[1]} for r in cursor.fetchall()]
        
        # 按品牌类别统计
        cursor.execute(f"""
            SELECT brand_category, COUNT(*) as cnt 
            FROM collaborations {date_condition}
            GROUP BY brand_category ORDER BY cnt DESC
        """, params)
        stats["by_category"] = [{"name": r[0] or "未知", "count": r[1]} for r in cursor.fetchall()]
        
        # 按合作类型统计
        cursor.execute(f"""
            SELECT collab_type, COUNT(*) as cnt 
            FROM collaborations {date_condition}
            GROUP BY collab_type ORDER BY cnt DESC
        """, params)
        stats["by_type"] = [{"name": r[0] or "未知", "count": r[1]} for r in cursor.fetchall()]
        
        # 按日期统计（最近30天）
        cursor.execute("""
            SELECT collected_date, COUNT(*) as cnt 
            FROM collaborations 
            WHERE collected_date >= date('now', '-30 days')
            GROUP BY collected_date ORDER BY collected_date
        """)
        stats["by_date"] = [{"date": r[0], "count": r[1]} for r in cursor.fetchall()]
        
        # 热门条目
        cursor.execute(f"""
            SELECT id, title, game_name, brand_name, hot_score
            FROM collaborations {date_condition}
            ORDER BY hot_score DESC LIMIT 10
        """, params)
        stats["hot_items"] = [{"id": r[0], "title": r[1], "game": r[2], "brand": r[3], "score": r[4]} 
                              for r in cursor.fetchall()]
        
        # 日期范围
        cursor.execute("SELECT MIN(collected_date), MAX(collected_date) FROM collaborations")
        row = cursor.fetchone()
        stats["date_range"] = {"min": row[0], "max": row[1]} if row[0] else {"min": None, "max": None}
        
        return stats


def get_available_dates():
    """获取所有有数据的日期列表"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT collected_date, COUNT(*) as cnt
            FROM collaborations 
            GROUP BY collected_date 
            ORDER BY collected_date DESC
        """)
        return [{"date": r[0], "count": r[1]} for r in cursor.fetchall()]


def get_available_games():
    """获取所有有数据的游戏列表"""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT game_name, COUNT(*) as cnt
            FROM collaborations
            WHERE game_name != ''
            GROUP BY game_name
            ORDER BY cnt DESC
        """)
        return [{"name": r[0], "count": r[1]} for r in cursor.fetchall()]


def save_daily_report(report_data: dict):
    """保存每日报告记录"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_reports (
                report_date, total_items, new_items, top_games,
                top_brands, top_categories, highlights, report_html_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_data["report_date"],
            report_data.get("total_items", 0),
            report_data.get("new_items", 0),
            json.dumps(report_data.get("top_games", []), ensure_ascii=False),
            json.dumps(report_data.get("top_brands", []), ensure_ascii=False),
            json.dumps(report_data.get("top_categories", []), ensure_ascii=False),
            json.dumps(report_data.get("highlights", []), ensure_ascii=False),
            report_data.get("report_html_path", ""),
            now,
        ))


def save_collect_log(log_data: dict):
    """保存采集日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO collect_logs (
                collect_time, source_type, query_keyword,
                results_found, new_saved, duplicates_skipped,
                errors, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now,
            log_data.get("source_type", ""),
            log_data.get("query_keyword", ""),
            log_data.get("results_found", 0),
            log_data.get("new_saved", 0),
            log_data.get("duplicates_skipped", 0),
            log_data.get("errors", ""),
            log_data.get("duration_seconds", 0),
        ))


if __name__ == "__main__":
    init_database()
    print(f"[DB] 数据库路径: {DB_PATH}")
    stats = get_statistics()
    print(f"[DB] 当前总数据: {stats['total']} 条")

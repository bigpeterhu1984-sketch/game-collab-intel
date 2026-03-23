# -*- coding: utf-8 -*-
"""
游戏异业合作情报站 - 配置文件
============================
定义采集关键词、目标游戏、品牌类别、数据源等核心配置
"""

import os

# ===================== 路径配置 =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "intel_hub.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
PORTAL_DIR = os.path.join(BASE_DIR, "portal")

# ===================== 目标游戏列表 =====================
# 按热度分层：T1 头部 > T2 主流 > T3 热门 > T4 泛覆盖
# 分层用于搜索词分配和热度加分

TARGET_GAMES_T1 = [
    # 国民级 / 现象级
    "王者荣耀", "原神", "和平精英", "英雄联盟", "崩坏：星穹铁道",
    "蛋仔派对", "第五人格", "绝区零", "鸣潮",
]

TARGET_GAMES_T2 = [
    # 头部热门
    "阴阳师", "明日方舟", "光与夜之恋", "恋与深空", "永劫无间",
    "逆水寒", "梦幻西游", "天涯明月刀", "火影忍者手游", "穿越火线",
    "使命召唤手游", "暗区突围", "金铲铲之战", "元梦之星",
    "荒野乱斗", "部落冲突", "皇室战争",
]

TARGET_GAMES_T3 = [
    # 活跃热门
    "三国志战略版", "率土之滨", "少女前线", "碧蓝航线", "崩坏3",
    "未定事件簿", "食物语", "奥比岛", "摩尔庄园", "迷你世界",
    "我的世界", "植物大战僵尸", "宝可梦", "马里奥", "塞尔达",
    "最终幻想", "怪物猎人", "街霸", "拳皇", "DNF手游",
    "地下城与勇士", "剑网3", "天龙八部", "问道", "大话西游",
    "新笑傲江湖", "一念逍遥", "长安幻想", "白荆回廊", "尘白禁区",
    "重返未来1999", "深空之眼", "战双帕弥什", "少女前线2",
    "无期迷途", "花亦山心之月", "以闪亮之名", "闪耀暖暖",
    "恋与制作人", "时空中的绘旅人", "世界之外",
]

TARGET_GAMES_T4 = [
    # 泛覆盖（含主机/PC/新游）
    "VALORANT", "CS2", "DOTA2", "守望先锋", "堡垒之夜",
    "APEX英雄", "彩虹六号", "FIFA", "NBA2K", "赛博朋克2077",
    "艾尔登法环", "黑神话悟空", "幻塔", "塔瑞斯世界",
    "三角洲行动", "无畏契约", "极品飞车", "QQ飞车",
    "QQ炫舞", "天天酷跑", "节奏大师", "欢乐斗地主",
    "开心消消乐", "球球大作战", "香肠派对", "光遇",
    "Sky光遇", "旅行青蛙", "动物森友会", "健身环大冒险",
    "任天堂Switch", "PlayStation", "Xbox",
]

# 全量列表（兼容旧代码引用）
TARGET_GAMES = TARGET_GAMES_T1 + TARGET_GAMES_T2 + TARGET_GAMES_T3 + TARGET_GAMES_T4

# 游戏别名映射（用于模糊匹配）
GAME_ALIASES = {
    "崩铁": "崩坏：星穹铁道",
    "星铁": "崩坏：星穹铁道",
    "崩坏星穹铁道": "崩坏：星穹铁道",
    "崩坏:星穹铁道": "崩坏：星穹铁道",
    "王者": "王者荣耀",
    "吃鸡": "和平精英",
    "LOL": "英雄联盟",
    "lol": "英雄联盟",
    "英雄联盟手游": "英雄联盟",
    "CF手游": "穿越火线",
    "CF": "穿越火线",
    "COD手游": "使命召唤手游",
    "CODM": "使命召唤手游",
    "DNF": "地下城与勇士",
    "地下城": "地下城与勇士",
    "梦幻": "梦幻西游",
    "天刀": "天涯明月刀",
    "火影手游": "火影忍者手游",
    "ZZZ": "绝区零",
    "明日方舟": "明日方舟",
    "方舟": "明日方舟",
    "蛋仔": "蛋仔派对",
    "元梦": "元梦之星",
    "暗区": "暗区突围",
    "剑三": "剑网3",
    "天龙": "天龙八部",
    "大话": "大话西游",
    "黑猴": "黑神话悟空",
    "悟空": "黑神话悟空",
    "宝可梦大集结": "宝可梦",
    "Pokemon": "宝可梦",
    "pokemon": "宝可梦",
    "QQ飞车手游": "QQ飞车",
    "瓦罗兰特": "VALORANT",
    "瓦洛兰特": "VALORANT",
    "堡垒之夜": "堡垒之夜",
    "Fortnite": "堡垒之夜",
    "APEX": "APEX英雄",
    "Apex": "APEX英雄",
}

# ===================== 合作品牌类别 =====================
BRAND_CATEGORIES = {
    "餐饮": ["肯德基", "麦当劳", "必胜客", "瑞幸", "喜茶", "奈雪的茶", "茶百道", "古茗",
             "蜜雪冰城", "星巴克", "海底捞", "德克士", "汉堡王", "达美乐", "棒约翰",
             "Manner", "库迪", "霸王茶姬", "一点点", "书亦烧仙草", "沪上阿姨",
             "乐乐茶", "COCO", "益禾堂", "甜啦啦"],
    "快消": ["可口可乐", "百事可乐", "红牛", "元气森林", "康师傅", "统一", "农夫山泉",
             "蒙牛", "伊利", "脉动", "东鹏特饮", "怡宝", "旺旺", "好丽友",
             "奥利奥", "乐事", "德芙", "士力架", "脑白金"],
    "美妆个护": ["MAC", "完美日记", "花西子", "珀莱雅", "欧莱雅", "SK-II",
                "兰蔻", "雅诗兰黛", "自然堂", "百雀羚", "妮维雅", "多芬",
                "力士", "舒肤佳", "清扬", "潘婷", "海飞丝"],
    "服饰潮牌": ["李宁", "安踏", "特步", "NIKE", "Adidas", "PUMA",
               "优衣库", "H&M", "ZARA", "森马", "海澜之家", "太平鸟",
               "Champion", "MLB", "FILA", "New Balance", "匡威"],
    "3C数码": ["小米", "华为", "OPPO", "vivo", "荣耀", "一加", "iQOO",
              "联想", "ROG", "雷蛇", "赛睿", "罗技", "HyperX",
              "三星", "索尼", "苹果", "戴尔", "惠普", "技嘉", "微星"],
    "汽车出行": ["宝马", "奔驰", "奥迪", "特斯拉", "比亚迪", "蔚来", "小鹏",
               "理想", "极氪", "吉利", "长安", "哈弗", "五菱", "滴滴",
               "高德", "百度地图", "哈啰", "美团单车"],
    "零售电商": ["天猫", "京东", "拼多多", "抖音商城", "名创优品", "泡泡玛特",
               "屈臣氏", "丝芙兰", "三福", "全家", "7-Eleven", "罗森",
               "盒马", "山姆", "Costco"],
    "金融支付": ["招商银行", "工商银行", "建设银行", "支付宝", "微信支付",
               "中国银联", "平安银行", "浦发银行", "中信银行", "民生银行"],
    "文旅酒店": ["万豪", "希尔顿", "洲际", "亚朵", "全季", "携程", "飞猪",
               "去哪儿", "长隆", "迪士尼", "环球影城", "欢乐谷", "方特"],
    "其他": []
}

# ===================== 合作类型标签 =====================
COLLAB_TYPES = [
    "联名产品",      # 联名款商品
    "主题门店",      # 主题餐厅/快闪店
    "限定皮肤",      # 游戏内联名皮肤
    "线下活动",      # 线下联动活动
    "定制包装",      # 产品定制包装
    "积分兑换",      # 消费积分兑换游戏道具
    "抽奖活动",      # 消费抽奖
    "AR互动",        # AR扫码等互动
    "赛事赞助",      # 电竞赛事赞助
    "代言合作",      # 游戏角色/IP代言
    "内容共创",      # 联合内容创作
    "跨界礼盒",      # 联名礼盒
    "其他",
]

# ===================== 采集搜索关键词模板 =====================
# 用于构建搜索查询
SEARCH_KEYWORD_TEMPLATES = [
    "{game} 联名",
    "{game} 合作",
    "{game} 联动",
    "{game} 跨界",
    "{game} 异业合作",
    "{game} 品牌合作",
    "{game} x {brand}",
    "{game} 联名 {brand_category}",
    "{game} 主题店",
    "{game} 限定",
]

# 通用搜索关键词（不绑定特定游戏，覆盖全行业）
GENERIC_KEYWORDS = [
    "游戏 异业合作",
    "游戏 品牌联名",
    "游戏 跨界合作",
    "手游 联名 餐饮",
    "手游 联名 奶茶",
    "手游 联名 快消",
    "游戏IP 商业合作",
    "电竞 品牌赞助",
    "游戏 快闪店",
    "游戏 主题餐厅",
    "游戏联名 2026",
    "游戏联名 2025",
    "游戏 跨界联名 新品",
    "手游 联名活动",
    "游戏IP 授权合作",
    "游戏 联名款 官宣",
    "手游 品牌联动",
    "游戏 x 品牌",
    "网游 联名合作",
    "端游 品牌联名",
    "主机游戏 联名",
    "游戏 联名周边",
    "二次元 联名",
    "二次元游戏 品牌合作",
    "游戏 联名服饰",
    "游戏 联名美妆",
    "游戏 联名饮品",
    "电竞战队 赞助",
    "游戏角色 代言",
    "游戏IP 快闪店",
]

# ===================== 数据源配置 =====================
# 搜索引擎（通过 Bing 搜索）
SEARCH_ENGINES = {
    "bing": {
        "base_url": "https://www.bing.com/search",
        "enabled": True,
        "max_results_per_query": 10,
    },
    "bing_news": {
        "base_url": "https://www.bing.com/news/search",
        "enabled": True,
        "max_results_per_query": 10,
    },
}

# RSS 源（游戏/营销相关）
RSS_FEEDS = [
    {"name": "36氪-游戏", "url": "https://36kr.com/feed/gameinfo", "enabled": True},
    {"name": "游戏葡萄", "url": "https://youxiputao.com/feed", "enabled": True},
    {"name": "GameLook", "url": "https://www.gamelook.com.cn/feed", "enabled": True},
]

# ===================== 采集参数 =====================
COLLECT_CONFIG = {
    "request_timeout": 15,          # 请求超时（秒）
    "request_delay_min": 2,         # 请求间隔最小（秒）
    "request_delay_max": 5,         # 请求间隔最大（秒）
    "max_pages_per_query": 3,       # 每个查询最大翻页数
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "daily_collect_hour": 8,        # 每日采集时间（24小时制）
    "dedup_similarity_threshold": 0.8,  # 去重相似度阈值
}

# ===================== 报告配置 =====================
REPORT_CONFIG = {
    "max_items_per_report": 50,     # 每份报告最大条目
    "summary_max_length": 200,      # 摘要最大字数
    "hot_score_weights": {          # 热度评分权重
        "source_authority": 0.3,    # 来源权威度
        "recency": 0.3,            # 时效性
        "brand_level": 0.2,        # 品牌量级
        "engagement": 0.2,         # 互动量
    },
}

# ===================== 辅助函数 =====================
def get_all_brands():
    """获取所有品牌的扁平列表"""
    brands = []
    for category, brand_list in BRAND_CATEGORIES.items():
        brands.extend(brand_list)
    return brands

def get_brand_category(brand_name):
    """根据品牌名获取其所属类别"""
    for category, brand_list in BRAND_CATEGORIES.items():
        if brand_name in brand_list:
            return category
    return "其他"

def build_search_queries(max_queries=80):
    """构建搜索查询列表 — 全游戏覆盖
    
    策略：
    - 通用关键词：覆盖全行业，不限定游戏
    - T1 头部游戏：每款 3 个搜索词（联名/品牌合作/跨界联动）
    - T2 主流游戏：每款 2 个搜索词（联名/合作）
    - T3 热门游戏：每款 1 个搜索词（联名）
    - T4 泛覆盖：不单独搜索，依赖通用词和 RSS 覆盖
    """
    queries = list(GENERIC_KEYWORDS)
    
    # T1 头部：每款 3 个搜索词
    for game in TARGET_GAMES_T1:
        queries.append(f"{game} 联名")
        queries.append(f"{game} 品牌合作")
        queries.append(f"{game} 跨界联动")
    
    # T2 主流：每款 2 个搜索词
    for game in TARGET_GAMES_T2:
        queries.append(f"{game} 联名")
        queries.append(f"{game} 合作")
    
    # T3 热门：每款 1 个搜索词
    for game in TARGET_GAMES_T3:
        queries.append(f"{game} 联名")
    
    # 去重（保持顺序）
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    return unique_queries[:max_queries]


if __name__ == "__main__":
    print(f"目标游戏数: {len(TARGET_GAMES)}")
    print(f"品牌类别数: {len(BRAND_CATEGORIES)}")
    print(f"总品牌数: {len(get_all_brands())}")
    print(f"搜索查询数: {len(build_search_queries())}")
    print("\n搜索查询示例:")
    for q in build_search_queries()[:10]:
        print(f"  - {q}")

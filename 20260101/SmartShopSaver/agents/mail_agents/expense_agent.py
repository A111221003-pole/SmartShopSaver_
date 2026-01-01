# -*- coding: utf-8 -*-
"""
expense_agent.py

提供「以月為單位」的支出摘要（MongoDB 版本）

- 統計日期：COALESCE(occurred_at, created_at)
- 區間：當月 [YYYY-MM-01, 次月-01)
"""

from __future__ import annotations
import calendar
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Taipei")
except Exception:
    _TZ = timezone(timedelta(hours=8))


def _month_bounds(dt: datetime) -> Tuple[str, str, int, int]:
    """
    取得當月 [start, next_start) 與 (year, month)。
    """
    year, month = dt.year, dt.month
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month == 12:
        next_start = start.replace(year=year + 1, month=1)
    else:
        next_start = start.replace(month=month + 1)
    return start.strftime("%Y-%m-%d"), next_start.strftime("%Y-%m-%d"), year, month


def _format_monthly_stats(stats: List[Dict], year: int, month: int) -> str:
    """格式化月度統計"""
    if not stats:
        return f"📊 {year}年{month}月 支出摘要：\n\n尚無消費記錄。"

    total = sum((s.get('total', 0) or 0) for s in stats)
    lines = [f"📊 {year}年{month}月 支出摘要："]
    lines.append(f"總支出: {int(total):,} 元")
    lines.append("")
    lines.append("各類別支出:")

    for stat in stats:
        name = stat.get('_id', '其他') or '其他'
        amount = stat.get('total', 0) or 0
        pct = (amount / total * 100) if total else 0.0
        lines.append(f"• {name}: {int(amount):,} 元 ({pct:.0f}%)")
    
    return "\n".join(lines)


def category_stats_30d(user_id: str, db=None) -> str:
    """
    回傳「當月」的各類別支出摘要字串（MongoDB 版本）
    
    Args:
        user_id: 用戶 ID
        db: 資料庫管理器實例（可選）
    """
    now = datetime.now(_TZ)
    start_s, next_start_s, year, month = _month_bounds(now)
    
    try:
        # 如果沒有傳入 db，嘗試建立連接
        if db is None:
            from utils.mail_utils.mongodb_adapter import get_db_manager
            db = get_db_manager()
        
        # MongoDB 聚合查詢
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "$or": [
                        {"occurred_at": {"$gte": start_s, "$lt": next_start_s}},
                        {"created_at": {"$gte": datetime.strptime(start_s, "%Y-%m-%d"), 
                                       "$lt": datetime.strptime(next_start_s, "%Y-%m-%d")}}
                    ]
                }
            },
            {
                "$group": {
                    "_id": {"$ifNull": ["$category", "其他"]},
                    "total": {"$sum": "$amount"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"total": -1}}
        ]
        
        stats = list(db.expenses.aggregate(pipeline))
        return _format_monthly_stats(stats, year, month)
        
    except Exception as e:
        return f"❌ 產生統計時發生錯誤：{e}"


class ExpenseAgent:
    """
    支出代理人（MongoDB 版本）
    """
    def __init__(self, db=None):
        self.db = db
        if self.db is None:
            from utils.mail_utils.mongodb_adapter import get_db_manager
            self.db = get_db_manager()
    
    def get_monthly_stats(self, user_id: str) -> str:
        """取得當月統計"""
        return category_stats_30d(user_id, self.db)

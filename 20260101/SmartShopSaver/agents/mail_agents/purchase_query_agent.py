# -*- coding: utf-8 -*-
"""
purchase_query_agent.py (MongoDB 版)
從資料庫 shopping_records 以關鍵字搜尋使用者已記錄的消費，並用 GPT 產生中文分析。
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import re
import os
from collections import defaultdict

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Asia/Taipei")
except Exception:
    _TZ = timezone(timedelta(hours=8))


def _call_gpt(prompt: str, max_retries: int = 2, timeout_sec: int = 25) -> Optional[str]:
    """簡易 GPT 呼叫"""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
            timeout=timeout_sec
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return None


def _search_records_db(
    db: Any,
    user_id: str,
    keyword: str,
    months: int = 12,
    limit: int = 300,
) -> List[Dict]:
    """
    MongoDB 版本：關鍵字搜尋
    """
    start_dt = (datetime.now(_TZ).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                - timedelta(days=30 * (months - 1)))
    start_s = start_dt.strftime("%Y-%m-%d")
    end_dt = datetime.now(_TZ)
    end_s = end_dt.strftime("%Y-%m-%d")
    
    # MongoDB 正則搜尋
    regex_pattern = {"$regex": keyword, "$options": "i"}
    
    query = {
        "user_id": user_id,
        "$or": [
            {"subject": regex_pattern},
            {"vendor": regex_pattern},
            {"description": regex_pattern},
            {"snippet": regex_pattern}
        ]
    }
    
    # 嘗試使用 shopping_records 集合
    collection = getattr(db, 'shopping_records', None)
    if collection is None and hasattr(db, 'db'):
        collection = db.db.shopping_records
    
    if collection is None:
        return []
    
    cursor = collection.find(query).sort("email_date", -1).limit(limit)
    
    rows = []
    for r in cursor:
        d = r.get("email_date", "")
        if hasattr(d, "strftime"):
            d_str = d.strftime("%Y/%m/%d")
        elif isinstance(d, str):
            d_str = d[:10].replace("-", "/")
        else:
            d_str = ""
        
        rows.append({
            "record_id": str(r.get("_id", "")),
            "vendor": r.get("vendor", ""),
            "amount": float(r.get("amount", 0) or 0),
            "category": r.get("category", "其他"),
            "date": d_str,
            "subject": r.get("subject", ""),
            "snippet": r.get("snippet", ""),
        })
    
    return rows


def _gpt_summary(keyword: str, rows: List[Dict]) -> Optional[str]:
    """用 GPT 產生繁中重點摘要"""
    if not rows:
        return f"🔎 找不到與「{keyword}」相關的已記錄消費（近 12 個月）。"
    
    compact = [
        {
            "date": r["date"],
            "vendor": r["vendor"][:80],
            "amount": r["amount"],
            "category": r["category"],
            "subject": (r["subject"] or "")[:120],
        }
        for r in rows[:200]
    ]
    
    prompt = (
        "你是消費分析助手。以下是使用者在資料庫中，"
        "近 12 個月與某個關鍵字相關的紀錄（JSON 陣列）。"
        "請用繁體中文輸出條列重點：\n"
        "1) 符合筆數與總金額；\n"
        "2) 主要商家/平台（最多 5 個，依金額或次數排序）；\n"
        "3) 類別分布（最多 5 類）；\n"
        "4) 最近 3 筆重點（日期／商家／金額／主旨簡述）；\n"
        "5) 若資料看起來是帳單彙整或非單筆購買，請註記『可能非單筆購物憑證』即可。\n"
        "語氣務必精簡。\n\n"
        f"關鍵字: {keyword}\n"
        f"紀錄(JSON): {compact}"
    )
    
    return _call_gpt(prompt, max_retries=2, timeout_sec=25)


def _fallback_summary(keyword: str, rows: List[Dict]) -> str:
    """GPT 不可用時的保底摘要"""
    if not rows:
        return f"🔎 找不到與「{keyword}」相關的已記錄消費（近 12 個月）。"
    
    total = sum(r["amount"] for r in rows)
    by_vendor = defaultdict(float)
    by_cat = defaultdict(float)
    for r in rows:
        by_vendor[r["vendor"]] += r["amount"]
        by_cat[r["category"]] += r["amount"]
    
    top_vendors = sorted(by_vendor.items(), key=lambda x: (-x[1], x[0]))[:5]
    top_cats = sorted(by_cat.items(), key=lambda x: (-x[1], x[0]))[:5]
    
    lines = [
        f"🔎 關鍵字「{keyword}」的消費查詢（近 12 個月）",
        f"共 {len(rows)} 筆，合計 NT$ {int(total):,} 元",
        "",
        "• 主要商家： " + "、".join(f"{v}(NT${int(amt):,})" for v, amt in top_vendors) if top_vendors else "• 主要商家：—",
        "• 類別分布： " + "、".join(f"{c}(NT${int(amt):,})" for c, amt in top_cats) if top_cats else "• 類別分布：—",
        "",
        "最近 3 筆：",
    ]
    for r in rows[:3]:
        lines.append(f"• {r['date']} {r['vendor']} NT$ {int(r['amount']):,}｜{(r['subject'] or '')[:30]}")
    
    return "\n".join(lines)


def query_and_analyze(
    user_id: str,
    keyword: str,
    db: Any = None,
    months: int = 12,
    limit: int = 300,
) -> str:
    """
    主入口：回傳一段可直接發送到 LINE 的文字摘要
    
    Args:
        user_id: 用戶 ID
        keyword: 搜尋關鍵字
        db: 資料庫管理器實例（可選）
        months: 搜尋月數
        limit: 最大筆數
    """
    if db is None:
        from utils.mail_utils.mongodb_adapter import get_db_manager
        db = get_db_manager()
    
    try:
        rows = _search_records_db(db, user_id, keyword, months=months, limit=limit)
    except Exception as e:
        return f"❌ 查詢資料庫失敗：{e}"
    
    # 先嘗試 GPT，失敗則用保底摘要
    gpt = _gpt_summary(keyword, rows)
    if gpt:
        return gpt
    return _fallback_summary(keyword, rows)

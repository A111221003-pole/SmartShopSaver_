# agents/response_formatter.py
# -*- coding: utf-8 -*-
"""回應格式化工具"""

from typing import Dict, List, Any, Optional


def format_price_comparison(products: List[Dict], keyword: str) -> str:
    """格式化價格比較結果"""
    if not products:
        return f"❌ 找不到「{keyword}」的商品"
    
    response = f"🔍 「{keyword}」比價結果\n\n"
    
    for i, product in enumerate(products[:5], 1):
        name = product.get('name', '未知商品')
        if len(name) > 30:
            name = name[:30] + "..."
        
        price = product.get('price', 0)
        platform = product.get('platform', '未知')
        url = product.get('url', '')
        
        response += f"{i}. {name}\n"
        response += f"   💰 NT${price:,}\n"
        response += f"   🏪 {platform}\n"
        if url:
            response += f"   🔗 {url}\n"
        response += "\n"
    
    return response


def format_tracking_list(trackings: List[Dict]) -> str:
    """格式化追蹤清單"""
    if not trackings:
        return "📊 您的追蹤清單目前是空的\n\n💡 輸入「追蹤 [商品名] 目標價格 [金額]」來開始追蹤"
    
    response = f"📊 **您的追蹤清單** (共 {len(trackings)} 項)\n\n"
    
    for i, t in enumerate(trackings, 1):
        name = t.get('product_name', '商品')
        target = t.get('target_price', 0)
        current = t.get('current_lowest_price', 0)
        
        response += f"📱 **{i}. {name}**\n"
        response += f"   🎯 目標價格: NT${target:,}\n"
        response += f"   💰 目前最低: NT${current:,}\n"
        
        if current > 0 and target > 0:
            if current <= target:
                response += "   ✅ 已達標價！建議購買\n"
            else:
                diff = current - target
                response += f"   📈 需降價: NT${diff:,}\n"
        
        response += "\n"
    
    return response


def format_expense_summary(summary: Dict) -> str:
    """格式化支出摘要"""
    total = summary.get('total_spending', 0)
    budget = summary.get('budget', 0)
    categories = summary.get('categories', {})
    
    response = "📊 **本月支出摘要**\n\n"
    response += f"💰 總支出: NT${int(total):,}\n"
    
    if budget > 0:
        remaining = budget - total
        percent = (total / budget) * 100 if budget > 0 else 0
        response += f"📋 預算: NT${int(budget):,}\n"
        response += f"📈 使用率: {percent:.1f}%\n"
        
        if remaining > 0:
            response += f"✅ 剩餘: NT${int(remaining):,}\n"
        else:
            response += f"⚠️ 超支: NT${int(abs(remaining)):,}\n"
    
    if categories:
        response += "\n📂 各類別支出:\n"
        for cat, amount in sorted(categories.items(), key=lambda x: -x[1])[:5]:
            pct = (amount / total * 100) if total > 0 else 0
            response += f"• {cat}: NT${int(amount):,} ({pct:.0f}%)\n"
    
    return response


def format_product_recommendation(products: List[Dict], category: str) -> str:
    """格式化商品推薦"""
    if not products:
        return f"❌ 找不到「{category}」的推薦商品"
    
    response = f"🎯 **{category} 推薦**\n\n"
    
    for i, product in enumerate(products[:5], 1):
        name = product.get('name', '商品')
        price = product.get('price', 0)
        reason = product.get('reason', '')
        
        response += f"**{i}. {name}**\n"
        response += f"   💰 NT${price:,}\n"
        if reason:
            response += f"   💡 {reason}\n"
        response += "\n"
    
    return response

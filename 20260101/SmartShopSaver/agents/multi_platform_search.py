# agents/multi_platform_search.py
# -*- coding: utf-8 -*-
"""多平台商品搜尋模組"""

import logging
import requests
import urllib.parse
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def search_pchome(keyword: str, limit: int = 10) -> List[Dict]:
    """搜尋 PChome 24h"""
    try:
        encoded = urllib.parse.quote(keyword)
        url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={encoded}&page=1&sort=sale/dc"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = data.get('prods', [])[:limit]
            
            results = []
            for p in products:
                results.append({
                    'platform': 'PChome 24h',
                    'name': p.get('name', ''),
                    'price': p.get('price', 0),
                    'url': f"https://24h.pchome.com.tw/prod/{p.get('Id', '')}",
                    'image': p.get('picS', '')
                })
            return results
    except Exception as e:
        logger.error(f"PChome 搜尋失敗: {e}")
    return []


def search_momo(keyword: str, limit: int = 10) -> List[Dict]:
    """搜尋 MOMO（模擬）"""
    # MOMO 需要更複雜的爬蟲，這裡提供框架
    logger.info(f"MOMO 搜尋: {keyword}")
    return []


def search_shopee(keyword: str, limit: int = 10) -> List[Dict]:
    """搜尋蝦皮（模擬）"""
    # 蝦皮需要 API 或爬蟲，這裡提供框架
    logger.info(f"蝦皮搜尋: {keyword}")
    return []


def search_all_platforms(keyword: str, limit: int = 5) -> Dict[str, List[Dict]]:
    """
    同時搜尋所有平台
    
    Args:
        keyword: 搜尋關鍵字
        limit: 每個平台的結果數量限制
        
    Returns:
        各平台搜尋結果的字典
    """
    results = {
        'pchome': [],
        'momo': [],
        'shopee': []
    }
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(search_pchome, keyword, limit): 'pchome',
            executor.submit(search_momo, keyword, limit): 'momo',
            executor.submit(search_shopee, keyword, limit): 'shopee',
        }
        
        for future in as_completed(futures):
            platform = futures[future]
            try:
                results[platform] = future.result()
            except Exception as e:
                logger.error(f"{platform} 搜尋失敗: {e}")
    
    return results


def format_multi_platform_response(results: Dict[str, List[Dict]], keyword: str) -> str:
    """
    格式化多平台搜尋結果
    
    Args:
        results: 各平台搜尋結果
        keyword: 搜尋關鍵字
        
    Returns:
        格式化的回應文字
    """
    all_products = []
    for platform, products in results.items():
        all_products.extend(products)
    
    if not all_products:
        return f"❌ 找不到「{keyword}」的商品"
    
    # 按價格排序
    all_products.sort(key=lambda x: x.get('price', float('inf')))
    
    response = f"🔍 「{keyword}」比價結果\n\n"
    
    for i, product in enumerate(all_products[:5], 1):
        response += f"{i}. {product['name'][:30]}...\n"
        response += f"   💰 NT${product['price']:,}\n"
        response += f"   🏪 {product['platform']}\n"
        response += f"   🔗 {product['url']}\n\n"
    
    if len(all_products) > 5:
        response += f"📊 共找到 {len(all_products)} 個結果"
    
    return response

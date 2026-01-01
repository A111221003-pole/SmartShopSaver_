# agents/__init__.py
"""SmartShopSaver 代理人模組"""

from .base_agent import BaseAgent, AgentRegistry, agent_registry
from .ai_intent_analyzer import AIIntentAnalyzer
from .finance_agent import FinanceAgent
from .gmail_integration_agent import GmailIntegrationAgent
from .price_tracker_agent_improved import PriceTrackerAgent
from .product_review_agent_improved import ProductReviewAgent
from .smart_recommendation_agent import SmartRecommendationAgent
from .response_formatter import (
    format_price_comparison,
    format_tracking_list,
    format_expense_summary,
    format_product_recommendation
)
from .multi_platform_search import (
    search_all_platforms,
    search_pchome,
    format_multi_platform_response
)

__all__ = [
    # 基礎類別
    'BaseAgent',
    'AgentRegistry',
    'agent_registry',
    
    # 代理人
    'AIIntentAnalyzer',
    'FinanceAgent',
    'GmailIntegrationAgent',
    'PriceTrackerAgent',
    'ProductReviewAgent',
    'SmartRecommendationAgent',
    
    # 工具函數
    'format_price_comparison',
    'format_tracking_list',
    'format_expense_summary',
    'format_product_recommendation',
    'search_all_platforms',
    'search_pchome',
    'format_multi_platform_response',
]

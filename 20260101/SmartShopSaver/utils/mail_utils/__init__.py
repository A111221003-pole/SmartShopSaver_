# utils/mail_utils/__init__.py
"""郵件處理工具模組"""

from .mongodb_adapter import MongoDBAdapter, get_db_manager

__all__ = ['MongoDBAdapter', 'get_db_manager']

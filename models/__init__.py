# -*- coding: utf-8 -*-
"""
数据库模型包
提供数据库连接和操作功能
"""

from .db import BookDB, DatabaseError

__all__ = ['BookDB', 'DatabaseError']

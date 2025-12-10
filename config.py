# -*- coding: utf-8 -*-
"""
数据库配置文件
使用Windows身份验证连接SQL Server

使用说明：
1. 将 'server' 修改为你的SQL Server服务器名称
   - 可以通过SQL Server Management Studio查看服务器名称
   - 或者使用 'localhost' 或 '.' 表示本地服务器
2. 确保数据库 'JY' 已创建
3. 确保当前Windows用户有访问数据库的权限
"""

DB_CONFIG = {
    'server': 'LAPTOP-O95VGSES',  # 请修改为你的SQL Server服务器名称
    'database': 'JY',              # 数据库名称
    'charset': 'utf8'              # 字符编码
}


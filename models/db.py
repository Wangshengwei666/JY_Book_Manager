# -*- coding: utf-8 -*-
"""
数据库连接和操作模块
提供对book表的CRUD操作
"""

import pymssql
from config import DB_CONFIG


class DatabaseError(Exception):
    """
    数据库操作异常类
    
    用于统一处理数据库相关的错误，便于在应用层进行异常捕获和处理。
    当数据库操作失败时，抛出此异常而不是通用的Exception，使错误处理更加精确。
    """
    pass


class BookDB:
    """图书数据库操作类"""
    
    def __init__(self):
        self.config = DB_CONFIG
    
    def _get_connection(self):
        """获取数据库连接"""
        try:
            conn = pymssql.connect(
                server=self.config['server'],
                database=self.config['database'],
                charset=self.config['charset']
            )
            return conn
        except Exception as e:
            raise DatabaseError(f"数据库连接失败: {str(e)}")
    
    def get_all_books(self):
        """获取所有图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT 
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                ORDER BY book_id
            """)
            books = cursor.fetchall()
            # 转换MONEY类型为字符串，便于JSON序列化
            for book in books:
                if book['book_price'] is not None:
                    book['book_price'] = float(book['book_price'])
            return books
        except Exception as e:
            raise DatabaseError(f"查询图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_book_by_id(self, book_id):
        """根据ID获取图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT 
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                WHERE book_id = %s
            """, (book_id,))
            book = cursor.fetchone()
            if book and book['book_price'] is not None:
                book['book_price'] = float(book['book_price'])
            return book
        except Exception as e:
            raise DatabaseError(f"查询图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def create_book(self, book_data):
        """创建新图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO book (
                    book_id, book_name, book_isbn, book_author,
                    book_publisher, book_price, interview_times
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                book_data['book_id'],
                book_data['book_name'],
                book_data['book_isbn'],
                book_data['book_author'],
                book_data['book_publisher'],
                book_data['book_price'],
                book_data['interview_times']
            ))
            conn.commit()
            return True
        except pymssql.IntegrityError as e:
            raise DatabaseError(f"图书ID已存在或数据完整性错误: {str(e)}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"创建图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def update_book(self, book_id, book_data):
        """更新图书信息"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE book SET
                    book_name = %s,
                    book_isbn = %s,
                    book_author = %s,
                    book_publisher = %s,
                    book_price = %s,
                    interview_times = %s
                WHERE book_id = %s
            """, (
                book_data['book_name'],
                book_data['book_isbn'],
                book_data['book_author'],
                book_data['book_publisher'],
                book_data['book_price'],
                book_data['interview_times'],
                book_id
            ))
            if cursor.rowcount == 0:
                raise DatabaseError("图书不存在")
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"更新图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def delete_book(self, book_id):
        """删除图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
            if cursor.rowcount == 0:
                raise DatabaseError("图书不存在")
            conn.commit()
            return True
        except pymssql.IntegrityError as e:
            raise DatabaseError(f"无法删除：该图书可能被其他表引用: {str(e)}")
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"删除图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_books_count(self):
        """获取图书总数"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM book")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            raise DatabaseError(f"获取图书总数失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_books_paginated(self, page=1, per_page=10, search=None, sort_by='book_id', sort_order='ASC'):
        """分页获取图书"""
        conn = None
        try:
            # 确保 page 和 per_page 是整数类型
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
            try:
                per_page = int(per_page)
            except (ValueError, TypeError):
                per_page = 10
            
            # 确保 page 和 per_page 是正数
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 10
            
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # 构建WHERE子句
            where_clause = ""
            params = []
            if search:
                where_clause = """
                    WHERE book_name LIKE %s 
                    OR book_author LIKE %s 
                    OR book_isbn LIKE %s 
                    OR book_publisher LIKE %s
                """
                search_pattern = f'%{search}%'
                params = [search_pattern, search_pattern, search_pattern, search_pattern]
            
            # 验证排序字段
            valid_sort_fields = ['book_id', 'book_name', 'book_price', 'interview_times', 'book_author', 'book_publisher']
            if sort_by not in valid_sort_fields:
                sort_by = 'book_id'
            sort_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
            
            # 计算偏移量（确保是整数）
            offset = int((page - 1) * per_page)
            
            # 执行查询
            query = f"""
                SELECT 
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                OFFSET %s ROWS
                FETCH NEXT %s ROWS ONLY
            """
            # 确保 offset 和 per_page 是整数类型
            params.extend([int(offset), int(per_page)])
            
            cursor.execute(query, params)
            books = cursor.fetchall()
            
            # 转换MONEY类型
            for book in books:
                if book['book_price'] is not None:
                    book['book_price'] = float(book['book_price'])
            
            return books
        except Exception as e:
            raise DatabaseError(f"分页查询图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_statistics(self):
        """获取统计数据"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM book")
            total = cursor.fetchone()['total']
            
            # 获取平均价格
            cursor.execute("SELECT AVG(CAST(book_price AS FLOAT)) as avg_price FROM book")
            avg_price_result = cursor.fetchone()
            avg_price = float(avg_price_result['avg_price']) if avg_price_result['avg_price'] else 0.0
            
            # 获取总借阅次数
            cursor.execute("SELECT SUM(interview_times) as total_borrows FROM book")
            total_borrows_result = cursor.fetchone()
            total_borrows = total_borrows_result['total_borrows'] if total_borrows_result['total_borrows'] else 0
            
            # 获取最受欢迎的图书
            cursor.execute("""
                SELECT TOP 1 book_name, interview_times 
                FROM book 
                ORDER BY interview_times DESC
            """)
            popular = cursor.fetchone()
            
            # 获取价格统计
            cursor.execute("""
                SELECT 
                    MIN(CAST(book_price AS FLOAT)) as min_price,
                    MAX(CAST(book_price AS FLOAT)) as max_price
                FROM book
            """)
            price_stats = cursor.fetchone()
            
            # 获取出版社分布（前5名）
            cursor.execute("""
                SELECT TOP 5 
                    book_publisher,
                    COUNT(*) as count
                FROM book
                GROUP BY book_publisher
                ORDER BY count DESC
            """)
            publishers = cursor.fetchall()
            
            return {
                'total': total,
                'avg_price': round(avg_price, 2),
                'total_borrows': total_borrows,
                'popular_book': popular['book_name'] if popular else '无',
                'popular_borrows': popular['interview_times'] if popular else 0,
                'min_price': float(price_stats['min_price']) if price_stats['min_price'] else 0.0,
                'max_price': float(price_stats['max_price']) if price_stats['max_price'] else 0.0,
                'publishers': publishers
            }
        except Exception as e:
            raise DatabaseError(f"获取统计数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def search_books(self, keyword):
        """搜索图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            search_pattern = f'%{keyword}%'
            cursor.execute("""
                SELECT 
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                WHERE book_name LIKE %s 
                OR book_author LIKE %s 
                OR book_isbn LIKE %s 
                OR book_publisher LIKE %s
                ORDER BY book_id
            """, (search_pattern, search_pattern, search_pattern, search_pattern))
            books = cursor.fetchall()
            for book in books:
                if book['book_price'] is not None:
                    book['book_price'] = float(book['book_price'])
            return books
        except Exception as e:
            raise DatabaseError(f"搜索图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def delete_books_batch(self, book_ids):
        """批量删除图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            placeholders = ','.join(['%s'] * len(book_ids))
            cursor.execute(f"DELETE FROM book WHERE book_id IN ({placeholders})", book_ids)
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"批量删除失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_books_advanced_filter(self, filters, page=1, per_page=10, sort_by='book_id', sort_order='ASC'):
        """高级筛选查询"""
        conn = None
        try:
            # 确保 page 和 per_page 是整数类型
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1
            try:
                per_page = int(per_page)
            except (ValueError, TypeError):
                per_page = 10
            
            # 确保 page 和 per_page 是正数
            if page < 1:
                page = 1
            if per_page < 1:
                per_page = 10
            
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # 构建WHERE条件
            where_conditions = []
            params = []
            
            # 价格范围
            if filters.get('price_min') is not None:
                where_conditions.append("CAST(book_price AS FLOAT) >= %s")
                params.append(float(filters['price_min']))
            if filters.get('price_max') is not None:
                where_conditions.append("CAST(book_price AS FLOAT) <= %s")
                params.append(float(filters['price_max']))
            
            # 借阅次数范围
            if filters.get('borrow_min') is not None:
                where_conditions.append("interview_times >= %s")
                params.append(int(filters['borrow_min']))
            if filters.get('borrow_max') is not None:
                where_conditions.append("interview_times <= %s")
                params.append(int(filters['borrow_max']))
            
            # 出版社筛选（关键词搜索）
            publisher = filters.get('publisher')
            if publisher:
                publisher = str(publisher).strip()
                if publisher:
                    # 转义 LIKE 查询中的特殊字符
                    publisher = publisher.replace('[', '[[]').replace('%', '[%]').replace('_', '[_]')
                    where_conditions.append("book_publisher LIKE %s")
                    params.append(f'%{publisher}%')
            
            # 作者筛选（关键词搜索）
            author = filters.get('author')
            if author:
                author = str(author).strip()
                if author:
                    # 转义 LIKE 查询中的特殊字符
                    author = author.replace('[', '[[]').replace('%', '[%]').replace('_', '[_]')
                    where_conditions.append("book_author LIKE %s")
                    params.append(f'%{author}%')
            
            # 指定字段筛选
            if filters.get('field_search'):
                field = filters.get('field_search', {}).get('field', '')
                keyword = filters.get('field_search', {}).get('keyword', '').strip()
                if field and keyword:
                    # 转义 LIKE 查询中的特殊字符
                    keyword = keyword.replace('[', '[[]').replace('%', '[%]').replace('_', '[_]')
                    if field == 'book_name':
                        where_conditions.append("book_name LIKE %s")
                        params.append(f'%{keyword}%')
                    elif field == 'book_author':
                        where_conditions.append("book_author LIKE %s")
                        params.append(f'%{keyword}%')
                    elif field == 'book_isbn':
                        where_conditions.append("book_isbn LIKE %s")
                        params.append(f'%{keyword}%')
                    elif field == 'book_publisher':
                        where_conditions.append("book_publisher LIKE %s")
                        params.append(f'%{keyword}%')
            
            # 构建WHERE子句
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 验证排序字段
            valid_sort_fields = ['book_id', 'book_name', 'book_price', 'interview_times', 'book_author', 'book_publisher']
            if sort_by not in valid_sort_fields:
                sort_by = 'book_id'
            sort_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
            
            # 计算总数（使用筛选参数的副本）
            count_params = list(params)
            count_query = f"SELECT COUNT(*) as total FROM book {where_clause}"
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']
            
            # 计算偏移量（确保是整数）
            offset = int((page - 1) * per_page)
            
            # 执行查询（添加分页参数）
            query = f"""
                SELECT 
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                OFFSET %s ROWS
                FETCH NEXT %s ROWS ONLY
            """
            query_params = list(params)  # 使用筛选参数的副本
            # 确保 offset 和 per_page 是整数类型
            query_params.extend([int(offset), int(per_page)])
            
            cursor.execute(query, query_params)
            books = cursor.fetchall()
            
            # 转换MONEY类型
            for book in books:
                if book['book_price'] is not None:
                    book['book_price'] = float(book['book_price'])
            
            return {
                'books': books,
                'total': total
            }
        except Exception as e:
            raise DatabaseError(f"高级筛选查询失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_filter_options(self):
        """获取筛选选项（出版社、作者列表）"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # 获取所有出版社
            cursor.execute("SELECT DISTINCT book_publisher FROM book ORDER BY book_publisher")
            publishers = [row['book_publisher'] for row in cursor.fetchall()]
            
            # 获取所有作者
            cursor.execute("SELECT DISTINCT book_author FROM book ORDER BY book_author")
            authors = [row['book_author'] for row in cursor.fetchall()]
            
            return {
                'publishers': publishers,
                'authors': authors
            }
        except Exception as e:
            raise DatabaseError(f"获取筛选选项失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_related_books(self, book_id, limit=5):
        """获取相关图书（同作者、同出版社）"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            # 先获取当前图书信息
            current_book = self.get_book_by_id(book_id)
            if not current_book:
                return []
            
            author = current_book['book_author']
            publisher = current_book['book_publisher']
            
            # 查找同作者或同出版社的图书（排除自己）
            # 优先级：同作者 > 同出版社 > 借阅次数
            cursor.execute("""
                SELECT TOP %s
                    book_id,
                    book_name,
                    book_isbn,
                    book_author,
                    book_publisher,
                    book_price,
                    interview_times
                FROM book
                WHERE book_id != %s
                AND (
                    book_author = %s
                    OR book_publisher = %s
                )
                ORDER BY 
                    CASE WHEN book_author = %s THEN 0 ELSE 1 END,
                    CASE WHEN book_publisher = %s THEN 0 ELSE 1 END,
                    interview_times DESC
            """, (limit, book_id, author, publisher, author, publisher))
            
            books = cursor.fetchall()
            
            # 转换MONEY类型
            for book in books:
                if book['book_price'] is not None:
                    book['book_price'] = float(book['book_price'])
            
            return books
        except Exception as e:
            raise DatabaseError(f"获取相关图书失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def import_books_from_data(self, books_data):
        """批量导入图书"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            errors = []
            
            for idx, book_data in enumerate(books_data, 1):
                try:
                    cursor.execute("""
                        INSERT INTO book (
                            book_id, book_name, book_isbn, book_author,
                            book_publisher, book_price, interview_times
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        book_data['book_id'],
                        book_data['book_name'],
                        book_data['book_isbn'],
                        book_data['book_author'],
                        book_data['book_publisher'],
                        book_data['book_price'],
                        book_data['interview_times']
                    ))
                    success_count += 1
                except pymssql.IntegrityError:
                    error_count += 1
                    errors.append(f"第{idx}行: 图书ID {book_data.get('book_id', '未知')} 已存在")
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{idx}行: {str(e)}")
            
            conn.commit()
            
            return {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"批量导入失败: {str(e)}")
        finally:
            if conn:
                conn.close()


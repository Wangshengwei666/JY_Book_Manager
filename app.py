# -*- coding: utf-8 -*-
"""
JY图书管理系统 - Flask主应用
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from models.db import BookDB, DatabaseError
import json
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'jy_book_manager_secret_key_2024'  # 用于flash消息
app.config['JSON_AS_ASCII'] = False  # 确保JSON支持中文

# 初始化数据库操作对象
db = BookDB()


@app.route('/')
def index():
    """首页 - 显示所有图书列表"""
    try:
        books = db.get_all_books()
        return render_template('index.html', books=books)
    except DatabaseError as e:
        flash(f'加载图书列表失败: {str(e)}', 'error')
        return render_template('index.html', books=[])


@app.route('/api/books', methods=['GET'])
def api_get_books():
    """API: 获取所有图书（JSON格式）"""
    try:
        books = db.get_all_books()
        return jsonify({'success': True, 'data': books})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/books/<book_id>', methods=['GET'])
def api_get_book(book_id):
    """API: 获取单个图书"""
    try:
        book = db.get_book_by_id(book_id)
        if book:
            return jsonify({'success': True, 'data': book})
        else:
            return jsonify({'success': False, 'message': '图书不存在'}), 404
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/books', methods=['POST'])
def api_create_book():
    """API: 创建新图书"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['book_id', 'book_name', 'book_isbn', 'book_author', 
                          'book_publisher', 'book_price', 'interview_times']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'字段 {field} 不能为空'}), 400
        
        # 验证数据类型
        try:
            data['book_price'] = float(data['book_price'])
            data['interview_times'] = int(data['interview_times'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '价格和借阅次数必须是数字'}), 400
        
        # 验证字段长度
        if len(data['book_id']) > 8:
            return jsonify({'success': False, 'message': '图书ID不能超过8个字符'}), 400
        if len(data['book_isbn']) > 17:
            return jsonify({'success': False, 'message': 'ISBN不能超过17个字符'}), 400
        
        db.create_book(data)
        return jsonify({'success': True, 'message': '图书创建成功'})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/books/<book_id>', methods=['PUT'])
def api_update_book(book_id):
    """API: 更新图书"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['book_name', 'book_isbn', 'book_author', 
                          'book_publisher', 'book_price', 'interview_times']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'字段 {field} 不能为空'}), 400
        
        # 验证数据类型
        try:
            data['book_price'] = float(data['book_price'])
            data['interview_times'] = int(data['interview_times'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '价格和借阅次数必须是数字'}), 400
        
        # 验证字段长度
        if len(data['book_isbn']) > 17:
            return jsonify({'success': False, 'message': 'ISBN不能超过17个字符'}), 400
        
        db.update_book(book_id, data)
        return jsonify({'success': True, 'message': '图书更新成功'})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/books/<book_id>', methods=['DELETE'])
def api_delete_book(book_id):
    """API: 删除图书"""
    try:
        db.delete_book(book_id)
        return jsonify({'success': True, 'message': '图书删除成功'})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/statistics', methods=['GET'])
def api_statistics():
    """API: 获取统计数据"""
    try:
        stats = db.get_statistics()
        return jsonify({'success': True, 'data': stats})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/books/paginated', methods=['GET'])
def api_get_books_paginated():
    """API: 分页获取图书"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'book_id')
        sort_order = request.args.get('sort_order', 'ASC')
        
        # 获取总数
        total = db.get_books_count()
        if search:
            # 如果有搜索条件，需要重新计算总数
            search_books = db.search_books(search)
            total = len(search_books)
        
        # 获取分页数据
        books = db.get_books_paginated(
            page=page,
            per_page=per_page,
            search=search if search else None,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify({
            'success': True,
            'data': books,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        })
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/books/batch', methods=['DELETE'])
def api_delete_books_batch():
    """API: 批量删除图书"""
    try:
        data = request.get_json()
        book_ids = data.get('book_ids', [])
        
        if not book_ids or not isinstance(book_ids, list):
            return jsonify({'success': False, 'message': '请提供有效的图书ID列表'}), 400
        
        deleted_count = db.delete_books_batch(book_ids)
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 本图书',
            'deleted_count': deleted_count
        })
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/export/csv', methods=['GET'])
def api_export_csv():
    """API: 导出CSV"""
    try:
        books = db.get_all_books()
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['图书ID', '图书名称', 'ISBN', '作者', '出版社', '价格', '借阅次数'])
        
        # 写入数据
        for book in books:
            writer.writerow([
                book['book_id'],
                book['book_name'],
                book['book_isbn'],
                book['book_author'],
                book['book_publisher'],
                book['book_price'],
                book['interview_times']
            ])
        
        # 创建响应
        output.seek(0)
        filename = f'books_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/book/new')
def new_book():
    """显示添加图书表单"""
    return render_template('book_form.html', book=None, action='create')


@app.route('/book/edit/<book_id>')
def edit_book(book_id):
    """显示编辑图书表单"""
    try:
        book = db.get_book_by_id(book_id)
        if not book:
            flash('图书不存在', 'error')
            return redirect(url_for('index'))
        return render_template('book_form.html', book=book, action='edit')
    except DatabaseError as e:
        flash(f'加载图书信息失败: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/book/detail/<book_id>')
def book_detail(book_id):
    """图书详情页"""
    try:
        book = db.get_book_by_id(book_id)
        if not book:
            flash('图书不存在', 'error')
            return redirect(url_for('index'))
        
        # 获取相关图书
        related_books = db.get_related_books(book_id, limit=5)
        
        return render_template('book_detail.html', book=book, related_books=related_books)
    except DatabaseError as e:
        flash(f'加载图书信息失败: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/api/books/<book_id>/related', methods=['GET'])
def api_get_related_books(book_id):
    """API: 获取相关图书"""
    try:
        related_books = db.get_related_books(book_id, limit=5)
        return jsonify({'success': True, 'data': related_books})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/filter/options', methods=['GET'])
def api_get_filter_options():
    """API: 获取筛选选项"""
    try:
        options = db.get_filter_options()
        return jsonify({'success': True, 'data': options})
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/books/filter', methods=['POST'])
def api_filter_books():
    """API: 高级筛选"""
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        # 确保 page 和 per_page 是整数类型
        try:
            page = int(data.get('page', 1))
        except (ValueError, TypeError):
            page = 1
        try:
            per_page = int(data.get('per_page', 12))
        except (ValueError, TypeError):
            per_page = 12
        sort_by = data.get('sort_by', 'book_id')
        sort_order = data.get('sort_order', 'ASC')
        
        result = db.get_books_advanced_filter(
            filters=filters,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify({
            'success': True,
            'data': result['books'],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': result['total'],
                'pages': (result['total'] + per_page - 1) // per_page if result['total'] > 0 else 0
            }
        })
    except DatabaseError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/import/csv', methods=['POST'])
def api_import_csv():
    """API: 导入CSV文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': '只支持CSV文件'}), 400
        
        # 读取CSV文件
        stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)
        
        books_data = []
        errors = []
        
        # 解析CSV数据
        for idx, row in enumerate(reader, 2):  # 从第2行开始（第1行是表头）
            try:
                # 映射CSV列名到数据库字段
                book_data = {
                    'book_id': row.get('图书ID', row.get('book_id', '')).strip(),
                    'book_name': row.get('图书名称', row.get('book_name', '')).strip(),
                    'book_isbn': row.get('ISBN', row.get('book_isbn', '')).strip(),
                    'book_author': row.get('作者', row.get('book_author', '')).strip(),
                    'book_publisher': row.get('出版社', row.get('book_publisher', '')).strip(),
                    'book_price': float(row.get('价格', row.get('book_price', 0))),
                    'interview_times': int(row.get('借阅次数', row.get('interview_times', 0)))
                }
                
                # 验证必填字段
                if not book_data['book_id'] or not book_data['book_name']:
                    errors.append(f"第{idx}行: 图书ID或图书名称为空")
                    continue
                
                books_data.append(book_data)
            except (ValueError, KeyError) as e:
                errors.append(f"第{idx}行: 数据格式错误 - {str(e)}")
        
        if not books_data:
            return jsonify({
                'success': False,
                'message': '没有有效数据',
                'errors': errors
            }), 400
        
        # 批量导入
        result = db.import_books_from_data(books_data)
        result['errors'] = errors + result['errors']
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {result["success_count"]} 本图书',
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


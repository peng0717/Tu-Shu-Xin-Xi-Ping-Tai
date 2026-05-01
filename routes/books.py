# -*- coding: utf-8 -*-
"""
图书路由 - 图书CRUD操作
"""
from flask import Blueprint, request, jsonify
from models import get_db_connection
from utils.auth import token_required, admin_required, g
from utils.isbn_query import query_isbn, search_book_by_title

books_bp = Blueprint('books', __name__)


@books_bp.route('', methods=['GET'])
def get_books():
    """获取图书列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建查询
    where_clauses = []
    params = []
    
    if category_id:
        where_clauses.append('category_id = ?')
        params.append(category_id)
    
    if keyword:
        where_clauses.append('(title LIKE ? OR author LIKE ? OR isbn LIKE ?)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
    
    # 获取总数
    cursor.execute(f'SELECT COUNT(*) as count FROM books WHERE {where_sql}', params)
    total = cursor.fetchone()['count']
    
    # 分页查询
    offset = (page - 1) * page_size
    cursor.execute(f'''
        SELECT b.*, c.name as category_name
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE {where_sql}
        ORDER BY b.created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [page_size, offset])
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'books': books,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size
    })


@books_bp.route('/search', methods=['GET'])
def search_books_online():
    """通过书名在线搜索图书信息"""
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400
    
    results = search_book_by_title(keyword)
    return jsonify({'success': True, 'results': results})


@books_bp.route('/hot', methods=['GET'])
def get_hot_books():
    """获取热门图书（按借阅次数排序）"""
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, COUNT(br.id) as borrow_count
        FROM books b
        LEFT JOIN borrow_records br ON b.id = br.book_id
        GROUP BY b.id
        ORDER BY borrow_count DESC
        LIMIT ?
    ''', (limit,))
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'books': books})


@books_bp.route('/new', methods=['GET'])
def get_new_books():
    """获取新书上架"""
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM books
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'books': books})


@books_bp.route('/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """获取图书详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, c.name as category_name
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.id = ?
    ''', (book_id,))
    
    book = cursor.fetchone()
    conn.close()
    
    if not book:
        return jsonify({'error': '图书不存在'}), 404
    
    return jsonify({'book': dict(book)})


@books_bp.route('', methods=['POST'])
@admin_required
def create_book():
    """创建图书（需要管理员权限）"""
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': '书名不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO books (isbn, title, author, publisher, publish_date, 
                             cover_url, category_id, location, total_count, 
                             available_count, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('isbn', ''),
            data.get('title'),
            data.get('author', ''),
            data.get('publisher', ''),
            data.get('publish_date', ''),
            data.get('cover_url', ''),
            data.get('category_id'),
            data.get('location', ''),
            data.get('total_count', 1),
            data.get('available_count', data.get('total_count', 1)),
            data.get('description', '')
        ))
        conn.commit()
        
        book_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': '图书创建成功',
            'book_id': book_id
        }), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@books_bp.route('/<int:book_id>', methods=['PUT'])
@admin_required
def update_book(book_id):
    """更新图书信息"""
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查图书是否存在
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '图书不存在'}), 404
    
    try:
        cursor.execute('''
            UPDATE books SET
                isbn = COALESCE(?, isbn),
                title = COALESCE(?, title),
                author = COALESCE(?, author),
                publisher = COALESCE(?, publisher),
                publish_date = COALESCE(?, publish_date),
                cover_url = COALESCE(?, cover_url),
                category_id = COALESCE(?, category_id),
                location = COALESCE(?, location),
                total_count = COALESCE(?, total_count),
                available_count = COALESCE(?, available_count),
                description = COALESCE(?, description)
            WHERE id = ?
        ''', (
            data.get('isbn', ''),
            data.get('title', ''),
            data.get('author', ''),
            data.get('publisher', ''),
            data.get('publish_date', ''),
            data.get('cover_url', ''),
            data.get('category_id'),
            data.get('location', ''),
            data.get('total_count'),
            data.get('available_count'),
            data.get('description', ''),
            book_id
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '图书更新成功'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@books_bp.route('/<int:book_id>', methods=['DELETE'])
@admin_required
def delete_book(book_id):
    """删除图书"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查图书是否存在
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '图书不存在'}), 404
    
    # 检查是否有未归还的借阅记录
    cursor.execute('SELECT COUNT(*) as count FROM borrow_records WHERE book_id = ? AND status = "borrowed"', (book_id,))
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return jsonify({'error': '该图书有未归还的借阅记录，无法删除'}), 400
    
    try:
        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '图书删除成功'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500


@books_bp.route('/isbn/query', methods=['GET'])
def query_isbn_api():
    """通过ISBN查询图书信息API"""
    isbn = request.args.get('isbn', '')
    if not isbn:
        return jsonify({'success': False, 'error': 'ISBN不能为空'}), 400
    
    result = query_isbn(isbn)
    
    if result['success']:
        return jsonify({
            'success': True,
            'data': result['data'],
            'source': result['source']
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', '查询失败')
        })


@books_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取图书分类列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'categories': categories})


@books_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    """创建图书分类"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '分类名称不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)',
                      (data['name'], data.get('description', '')))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'message': '分类创建成功', 'category_id': category_id}), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'创建失败: {str(e)}'}), 500


@books_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """删除图书分类"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查分类是否存在
    cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '分类不存在'}), 404
    
    # 检查分类下是否有图书
    cursor.execute('SELECT COUNT(*) as count FROM books WHERE category_id = ?', (category_id,))
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return jsonify({'error': '该分类下有图书，无法删除'}), 400
    
    try:
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': '分类删除成功'})
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

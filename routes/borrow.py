# -*- coding: utf-8 -*-
"""
借还路由 - 借书、还书、续借
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import get_db_connection
from utils.auth import token_required, admin_required, g
from config import DEFAULT_BORROW_DAYS, MAX_RENEW_COUNT

borrow_bp = Blueprint('borrow', __name__)


@borrow_bp.route('/borrow', methods=['POST'])
@token_required
def borrow_book():
    """借书"""
    data = request.get_json()
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': '图书ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查用户借阅数量是否已达上限
    cursor.execute('''
        SELECT COUNT(*) as count FROM borrow_records 
        WHERE user_id = ? AND status = 'borrowed'
    ''', (g.user_id,))
    current_borrows = cursor.fetchone()['count']
    
    cursor.execute('SELECT max_borrow FROM users WHERE id = ?', (g.user_id,))
    max_borrow = cursor.fetchone()['max_borrow']
    
    if current_borrows >= max_borrow:
        conn.close()
        return jsonify({'error': f'已达借阅上限（{max_borrow}本）'}), 400
    
    # 检查图书是否存在且可借
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({'error': '图书不存在'}), 404
    
    if book['available_count'] <= 0:
        conn.close()
        return jsonify({'error': '该图书已全部借出，请预约'}), 400
    
    # 检查是否已有未归还的借阅记录
    cursor.execute('''
        SELECT * FROM borrow_records 
        WHERE user_id = ? AND book_id = ? AND status = 'borrowed'
    ''', (g.user_id, book_id))
    
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': '您已借阅此书，请先归还'}), 400
    
    # 创建借阅记录
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=DEFAULT_BORROW_DAYS)
    
    cursor.execute('''
        INSERT INTO borrow_records (user_id, book_id, borrow_date, due_date, status, renew_count)
        VALUES (?, ?, ?, ?, 'borrowed', 0)
    ''', (g.user_id, book_id, borrow_date, due_date))
    
    # 更新图书可借数量
    cursor.execute('''
        UPDATE books SET available_count = available_count - 1 WHERE id = ?
    ''', (book_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': '借书成功',
        'borrow_date': borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
        'due_date': due_date.strftime('%Y-%m-%d %H:%M:%S')
    })


@borrow_bp.route('/return', methods=['POST'])
@token_required
def return_book():
    """还书"""
    data = request.get_json()
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': '图书ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查借阅记录
    cursor.execute('''
        SELECT * FROM borrow_records 
        WHERE user_id = ? AND book_id = ? AND status = 'borrowed'
    ''', (g.user_id, book_id))
    
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({'error': '没有找到借阅记录'}), 404
    
    # 更新借阅记录
    return_date = datetime.now()
    cursor.execute('''
        UPDATE borrow_records 
        SET return_date = ?, status = 'returned'
        WHERE id = ?
    ''', (return_date, record['id']))
    
    # 更新图书可借数量
    cursor.execute('''
        UPDATE books SET available_count = available_count + 1 WHERE id = ?
    ''', (book_id,))
    
    conn.commit()
    conn.close()
    
    # 检查是否逾期
    is_overdue = return_date > datetime.fromisoformat(record['due_date'])
    
    return jsonify({
        'message': '还书成功',
        'return_date': return_date.strftime('%Y-%m-%d %H:%M:%S'),
        'is_overdue': is_overdue
    })


@borrow_bp.route('/renew', methods=['POST'])
@token_required
def renew_book():
    """续借"""
    data = request.get_json()
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': '图书ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查借阅记录
    cursor.execute('''
        SELECT * FROM borrow_records 
        WHERE user_id = ? AND book_id = ? AND status = 'borrowed'
    ''', (g.user_id, book_id))
    
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({'error': '没有找到借阅记录'}), 404
    
    if record['renew_count'] >= MAX_RENEW_COUNT:
        conn.close()
        return jsonify({'error': f'续借次数已达上限（{MAX_RENEW_COUNT}次）'}), 400
    
    # 续借：延长到期时间
    current_due = datetime.fromisoformat(record['due_date'])
    new_due = current_due + timedelta(days=DEFAULT_BORROW_DAYS)
    
    cursor.execute('''
        UPDATE borrow_records 
        SET due_date = ?, renew_count = renew_count + 1
        WHERE id = ?
    ''', (new_due, record['id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': '续借成功',
        'new_due_date': new_due.strftime('%Y-%m-%d %H:%M:%S'),
        'renew_count': record['renew_count'] + 1
    })


@borrow_bp.route('/my', methods=['GET'])
@token_required
def get_my_borrows():
    """获取我的借阅记录"""
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE br.user_id = ?"
    params = [g.user_id]
    
    if status:
        where_clause += " AND br.status = ?"
        params.append(status)
    
    cursor.execute(f'''
        SELECT br.*, b.title, b.author, b.cover_url, b.isbn,
               u.name as user_name
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        JOIN users u ON br.user_id = u.id
        {where_clause}
        ORDER BY br.borrow_date DESC
    ''', params)
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 检查逾期状态
    now = datetime.now()
    for record in records:
        if record['status'] == 'borrowed':
            due_date = datetime.fromisoformat(record['due_date'])
            record['is_overdue'] = now > due_date
    
    return jsonify({'records': records})


@borrow_bp.route('/all', methods=['GET'])
@admin_required
def get_all_borrows():
    """获取所有借阅记录（管理员）"""
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE 1=1"
    params = []
    
    if status:
        where_clause += " AND br.status = ?"
        params.append(status)
    
    # 获取总数
    cursor.execute(f'SELECT COUNT(*) as count FROM borrow_records br {where_clause}', params)
    total = cursor.fetchone()['count']
    
    # 分页查询
    offset = (page - 1) * page_size
    cursor.execute(f'''
        SELECT br.*, b.title, b.author, b.cover_url, b.isbn,
               u.name as user_name, u.student_id
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        JOIN users u ON br.user_id = u.id
        {where_clause}
        ORDER BY br.borrow_date DESC
        LIMIT ? OFFSET ?
    ''', params + [page_size, offset])
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'records': records,
        'total': total,
        'page': page,
        'page_size': page_size
    })

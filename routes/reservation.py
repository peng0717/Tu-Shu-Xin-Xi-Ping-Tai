# -*- coding: utf-8 -*-
"""
预约路由 - 预约图书
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import get_db_connection
from utils.auth import token_required, g

reservation_bp = Blueprint('reservation', __name__)


@reservation_bp.route('/reserve', methods=['POST'])
@token_required
def reserve_book():
    """预约图书"""
    data = request.get_json()
    book_id = data.get('book_id')
    
    if not book_id:
        return jsonify({'error': '图书ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查图书是否存在
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return jsonify({'error': '图书不存在'}), 404
    
    # 检查是否已有有效的预约记录
    cursor.execute('''
        SELECT * FROM reservations 
        WHERE user_id = ? AND book_id = ? AND status IN ('waiting', 'ready')
    ''', (g.user_id, book_id))
    
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': '您已预约此书'}), 400
    
    # 创建预约记录
    cursor.execute('''
        INSERT INTO reservations (user_id, book_id, reserve_date, status)
        VALUES (?, ?, ?, 'waiting')
    ''', (g.user_id, book_id, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': '预约成功',
        'reserve_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@reservation_bp.route('/cancel', methods=['POST'])
@token_required
def cancel_reservation():
    """取消预约"""
    data = request.get_json()
    reservation_id = data.get('reservation_id')
    book_id = data.get('book_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if reservation_id:
        cursor.execute('''
            UPDATE reservations SET status = 'cancelled'
            WHERE id = ? AND user_id = ?
        ''', (reservation_id, g.user_id))
    elif book_id:
        cursor.execute('''
            UPDATE reservations SET status = 'cancelled'
            WHERE book_id = ? AND user_id = ? AND status = 'waiting'
        ''', (book_id, g.user_id))
    else:
        conn.close()
        return jsonify({'error': '请提供预约ID或图书ID'}), 400
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected > 0:
        return jsonify({'message': '预约已取消'})
    else:
        return jsonify({'error': '未找到预约记录'}), 404


@reservation_bp.route('/my', methods=['GET'])
@token_required
def get_my_reservations():
    """获取我的预约记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, b.title, b.author, b.cover_url, b.isbn, b.available_count
        FROM reservations r
        JOIN books b ON r.book_id = b.id
        WHERE r.user_id = ?
        ORDER BY r.reserve_date DESC
    ''', (g.user_id,))
    
    reservations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'reservations': reservations})


@reservation_bp.route('/all', methods=['GET'])
@token_required
def get_all_reservations():
    """获取所有预约记录（管理员）"""
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_clause = "WHERE 1=1"
    params = []
    
    if status:
        where_clause += " AND r.status = ?"
        params.append(status)
    
    cursor.execute(f'''
        SELECT r.*, b.title, b.author, b.cover_url, b.isbn,
               u.name as user_name, u.student_id
        FROM reservations r
        JOIN books b ON r.book_id = b.id
        JOIN users u ON r.user_id = u.id
        {where_clause}
        ORDER BY r.reserve_date DESC
    ''', params)
    
    reservations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'reservations': reservations})


@reservation_bp.route('/notify-ready', methods=['POST'])
@token_required
def notify_reservation_ready():
    """通知预约到书（管理员操作）"""
    data = request.get_json()
    reservation_id = data.get('reservation_id')
    
    if not reservation_id:
        return jsonify({'error': '预约ID不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reservations 
        SET status = 'ready', notify_date = ?
        WHERE id = ?
    ''', (datetime.now(), reservation_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '已通知读者取书'})

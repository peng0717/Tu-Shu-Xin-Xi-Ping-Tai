# -*- coding: utf-8 -*-
"""
统计路由 - 各种统计数据
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import get_db_connection
from utils.auth import admin_required, token_required

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 图书总数
    cursor.execute('SELECT COUNT(*) as count FROM books')
    total_books = cursor.fetchone()['count']
    
    # 在馆图书数
    cursor.execute('SELECT SUM(available_count) as count FROM books')
    available_books = cursor.fetchone()['count'] or 0
    
    # 读者总数
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    # 今日借书数
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) as count FROM borrow_records 
        WHERE date(borrow_date) = date(?)
    ''', (today,))
    today_borrows = cursor.fetchone()['count']
    
    # 今日还书数
    cursor.execute('''
        SELECT COUNT(*) as count FROM borrow_records 
        WHERE date(return_date) = date(?)
    ''', (today,))
    today_returns = cursor.fetchone()['count']
    
    # 当前借出数
    cursor.execute('''
        SELECT COUNT(*) as count FROM borrow_records WHERE status = 'borrowed'
    ''')
    current_borrows = cursor.fetchone()['count']
    
    # 逾期数
    cursor.execute('''
        SELECT COUNT(*) as count FROM borrow_records 
        WHERE status = 'borrowed' AND date(due_date) < date(?)
    ''', (today,))
    overdue_count = cursor.fetchone()['count']
    
    # 待处理预约数
    cursor.execute('''
        SELECT COUNT(*) as count FROM reservations WHERE status = 'waiting'
    ''')
    pending_reservations = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_books': total_books,
        'available_books': available_books,
        'lent_books': total_books - available_books,
        'total_users': total_users,
        'today_borrows': today_borrows,
        'today_returns': today_returns,
        'current_borrows': current_borrows,
        'overdue_count': overdue_count,
        'pending_reservations': pending_reservations
    })


@stats_bp.route('/borrow-trend', methods=['GET'])
@admin_required
def get_borrow_trend():
    """获取借阅趋势（最近7天）"""
    days = request.args.get('days', 7, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    trend = []
    for i in range(days - 1, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # 借书数
        cursor.execute('''
            SELECT COUNT(*) as count FROM borrow_records 
            WHERE date(borrow_date) = date(?)
        ''', (date,))
        borrows = cursor.fetchone()['count']
        
        # 还书数
        cursor.execute('''
            SELECT COUNT(*) as count FROM borrow_records 
            WHERE date(return_date) = date(?)
        ''', (date,))
        returns = cursor.fetchone()['count']
        
        trend.append({
            'date': date,
            'borrows': borrows,
            'returns': returns
        })
    
    conn.close()
    
    return jsonify({'trend': trend})


@stats_bp.route('/hot-books', methods=['GET'])
@admin_required
def get_hot_books_stats():
    """获取热门图书统计"""
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.id, b.title, b.author, b.cover_url,
               COUNT(br.id) as borrow_count,
               COUNT(CASE WHEN br.status = 'borrowed' AND date(br.due_date) < date('now') THEN 1 END) as overdue_count
        FROM books b
        LEFT JOIN borrow_records br ON b.id = br.book_id
        GROUP BY b.id
        ORDER BY borrow_count DESC
        LIMIT ?
    ''', (limit,))
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'hot_books': books})


@stats_bp.route('/overdue-list', methods=['GET'])
@admin_required
def get_overdue_list():
    """获取逾期列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT br.*, b.title, b.author, u.name, u.student_id, u.phone
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        JOIN users u ON br.user_id = u.id
        WHERE br.status = 'borrowed' AND date(br.due_date) < date('now')
        ORDER BY br.due_date ASC
    ''')
    
    overdue_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'overdue_list': overdue_list})


@stats_bp.route('/user-borrows', methods=['GET'])
@admin_required
def get_user_borrow_stats():
    """获取用户借阅统计"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.name, u.student_id, u.role,
               COUNT(br.id) as total_borrows,
               COUNT(CASE WHEN br.status = 'borrowed' THEN 1 END) as current_borrows,
               COUNT(CASE WHEN br.status = 'returned' THEN 1 END) as returned_count
        FROM users u
        LEFT JOIN borrow_records br ON u.id = br.user_id
        GROUP BY u.id
        ORDER BY total_borrows DESC
    ''')
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'user_stats': users})

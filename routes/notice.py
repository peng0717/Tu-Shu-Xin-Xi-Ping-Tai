# -*- coding: utf-8 -*-
"""
公告路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import get_db_connection
from utils.auth import token_required, admin_required, g

notice_bp = Blueprint('notice', __name__)


@notice_bp.route('', methods=['GET'])
def get_notices():
    """获取公告列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute('SELECT COUNT(*) as count FROM notices WHERE is_active = 1')
    total = cursor.fetchone()['count']
    
    # 分页查询
    offset = (page - 1) * page_size
    cursor.execute('''
        SELECT n.*, u.name as author_name
        FROM notices n
        LEFT JOIN users u ON n.author_id = u.id
        WHERE n.is_active = 1
        ORDER BY n.created_at DESC
        LIMIT ? OFFSET ?
    ''', (page_size, offset))
    
    notices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'notices': notices,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@notice_bp.route('/<int:notice_id>', methods=['GET'])
def get_notice(notice_id):
    """获取公告详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.*, u.name as author_name
        FROM notices n
        LEFT JOIN users u ON n.author_id = u.id
        WHERE n.id = ? AND n.is_active = 1
    ''', (notice_id,))
    
    notice = cursor.fetchone()
    conn.close()
    
    if not notice:
        return jsonify({'error': '公告不存在'}), 404
    
    return jsonify({'notice': dict(notice)})


@notice_bp.route('', methods=['POST'])
@admin_required
def create_notice():
    """发布公告（管理员）"""
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': '标题不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notices (title, content, author_id, created_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    ''', (
        data['title'],
        data.get('content', ''),
        g.user_id,
        datetime.now()
    ))
    
    conn.commit()
    notice_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'message': '公告发布成功',
        'notice_id': notice_id
    }), 201


@notice_bp.route('/<int:notice_id>', methods=['PUT'])
@admin_required
def update_notice(notice_id):
    """更新公告"""
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM notices WHERE id = ?', (notice_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': '公告不存在'}), 404
    
    cursor.execute('''
        UPDATE notices SET
            title = COALESCE(?, title),
            content = COALESCE(?, content),
            is_active = COALESCE(?, is_active)
        WHERE id = ?
    ''', (
        data.get('title'),
        data.get('content'),
        data.get('is_active'),
        notice_id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '公告更新成功'})


@notice_bp.route('/<int:notice_id>', methods=['DELETE'])
@admin_required
def delete_notice(notice_id):
    """删除公告（软删除）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE notices SET is_active = 0 WHERE id = ?', (notice_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '公告已删除'})

# -*- coding: utf-8 -*-
"""
认证路由 - 用户登录、注册
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db_connection
from utils.auth import generate_token, token_required, g

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('student_id'):
        return jsonify({'error': '学号不能为空'}), 400
    if not data.get('name'):
        return jsonify({'error': '姓名不能为空'}), 400
    if not data.get('password'):
        return jsonify({'error': '密码不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查学号是否已存在
    cursor.execute('SELECT id FROM users WHERE student_id = ?', (data['student_id'],))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': '该学号已注册'}), 400
    
    # 密码加密
    password_hash = generate_password_hash(data['password'])
    
    # 确定角色和借阅数量
    role = data.get('role', 'student')
    max_borrow = 10 if role in ['teacher', 'admin'] else 5
    
    try:
        # 插入用户
        cursor.execute('''
            INSERT INTO users (student_id, name, password_hash, role, max_borrow, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['student_id'],
            data['name'],
            password_hash,
            role,
            max_borrow,
            data.get('phone', ''),
            data.get('email', '')
        ))
        conn.commit()
        
        user_id = cursor.lastrowid
        conn.close()
        
        # 生成token
        token = generate_token(user_id, role)
        
        return jsonify({
            'message': '注册成功',
            'token': token,
            'user': {
                'id': user_id,
                'student_id': data['student_id'],
                'name': data['name'],
                'role': role
            }
        }), 201
        
    except Exception as e:
        conn.close()
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data.get('student_id') or not data.get('password'):
        return jsonify({'error': '学号和密码不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE student_id = ?', (data['student_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': '密码错误'}), 401
    
    # 生成token
    token = generate_token(user['id'], user['role'])
    
    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': {
            'id': user['id'],
            'student_id': user['student_id'],
            'name': user['name'],
            'role': user['role'],
            'max_borrow': user['max_borrow']
        }
    })


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """获取当前用户信息"""
    return jsonify({
        'user': {
            'id': g.current_user['id'],
            'student_id': g.current_user['student_id'],
            'name': g.current_user['name'],
            'role': g.current_user['role'],
            'max_borrow': g.current_user['max_borrow'],
            'phone': g.current_user.get('phone', ''),
            'email': g.current_user.get('email', '')
        }
    })


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """修改密码"""
    data = request.get_json()
    
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': '请填写旧密码和新密码'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT password_hash FROM users WHERE id = ?', (g.user_id,))
    user = cursor.fetchone()
    
    if not check_password_hash(user['password_hash'], data['old_password']):
        conn.close()
        return jsonify({'error': '旧密码错误'}), 401
    
    # 更新密码
    new_hash = generate_password_hash(data['new_password'])
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, g.user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': '密码修改成功'})

# -*- coding: utf-8 -*-
"""
JWT认证工具
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from config import SECRET_KEY, JWT_EXPIRATION_HOURS
from models import get_db_connection


def generate_token(user_id, role):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def decode_token(token):
    """解码JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token过期
    except jwt.InvalidTokenError:
        return None  # Token无效


def token_required(f):
    """Token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Token格式错误'}), 401
        
        if not token:
            return jsonify({'error': '缺少Token'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401
        
        # 获取用户信息
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (payload['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 401
        
        # 将用户信息存入g对象
        g.current_user = dict(user)
        g.user_id = payload['user_id']
        g.user_role = payload['role']
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.user_role not in ['admin', 'teacher']:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated

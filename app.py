# -*- coding: utf-8 -*-
"""
图书信息一体化平台 - Flask主入口
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime

# 导入配置
from config import DATABASE_PATH

# 导入模型
from models import init_db, get_db_connection

# 导入路由蓝图
from routes.auth import auth_bp
from routes.books import books_bp
from routes.borrow import borrow_bp
from routes.reservation import reservation_bp
from routes.stats import stats_bp
from routes.notice import notice_bp


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    CORS(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(books_bp, url_prefix='/api/books')
    app.register_blueprint(borrow_bp, url_prefix='/api/borrow')
    app.register_blueprint(reservation_bp, url_prefix='/api/reservation')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(notice_bp, url_prefix='/api/notice')
    
    # 初始化数据库
    init_db()
    
    # 健康检查
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})
    
    # ========== Web管理后台路由 ==========
    
    # 主页
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # 管理后台登录页
    @app.route('/admin/login')
    def admin_login():
        return render_template('admin/login.html')
    
    # 管理后台主页
    @app.route('/admin')
    def admin():
        return render_template('admin/index.html')
    
    # 图书管理
    @app.route('/admin/books')
    def admin_books():
        return render_template('admin/books.html')
    
    # 借还管理
    @app.route('/admin/borrows')
    def admin_borrows():
        return render_template('admin/borrows.html')
    
    # 读者管理
    @app.route('/admin/users')
    def admin_users():
        return render_template('admin/users.html')
    
    # 公告管理
    @app.route('/admin/notices')
    def admin_notices():
        return render_template('admin/notices.html')
    
    # 预约管理
    @app.route('/admin/reservations')
    def admin_reservations():
        return render_template('admin/reservations.html')
    
    # 统计页面
    @app.route('/admin/stats')
    def admin_stats():
        return render_template('admin/stats.html')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': '接口不存在'}), 404
        return render_template('error.html', error='页面不存在'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': '服务器内部错误'}), 500
        return render_template('error.html', error='服务器内部错误'), 500
    
    return app


# 创建应用实例
app = create_app()


if __name__ == '__main__':
    print("=" * 50)
    print("图书信息一体化平台")
    print("=" * 50)
    print("API接口地址: http://127.0.0.1:5000/api")
    print("Web管理后台: http://127.0.0.1:5000/admin")
    print("默认管理员账号: admin / admin123")
    print("=" * 50)
    
    # 启动服务
    app.run(host='0.0.0.0', port=5000, debug=True)

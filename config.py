# -*- coding: utf-8 -*-
"""
配置文件
"""
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'library.db')

# JWT配置
SECRET_KEY = 'library-platform-secret-key-2024'
JWT_EXPIRATION_HOURS = 24 * 7  # 7天过期

# 借阅配置
DEFAULT_BORROW_DAYS = 30  # 默认借阅天数
MAX_RENEW_COUNT = 2  # 最大续借次数
MAX_BORROW_COUNT_STUDENT = 5  # 学生最大借阅数量
MAX_BORROW_COUNT_TEACHER = 10  # 教师最大借阅数量

# ISBN查询API配置
OPENLIBRARY_API = 'https://openlibrary.org/api/books?bibkeys=ISBN:{}&format=json&jscmd=data'
GOOGLE_BOOKS_API = 'https://www.googleapis.com/books/v1/volumes?q=isbn:{}'

# 分页配置
DEFAULT_PAGE_SIZE = 20

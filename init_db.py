# -*- coding: utf-8 -*-
"""
初始化数据库并插入示例数据
"""
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH, DEFAULT_BORROW_DAYS


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # ========== 创建表 ==========
    
    # 分类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    ''')
    
    # 图书表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT,
            publisher TEXT,
            publish_date TEXT,
            cover_url TEXT,
            category_id INTEGER,
            location TEXT,
            total_count INTEGER DEFAULT 1,
            available_count INTEGER DEFAULT 1,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            max_borrow INTEGER DEFAULT 5,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 借阅记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP NOT NULL,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'borrowed',
            renew_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # 预约记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            reserve_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'waiting',
            notify_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # 公告表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            author_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    ''')
    
    print("✓ 数据表创建完成")
    
    # ========== 插入示例数据 ==========
    
    # 1. 插入分类
    categories = [
        ('文学', None),
        ('计算机', None),
        ('历史', None),
        ('经济', None),
        ('自然科学', None),
        ('小说', 1),
        ('散文', 1),
        ('Python', 2),
        ('Java', 2),
        ('人工智能', 2)
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO categories (name, parent_id) VALUES (?, ?)',
        categories
    )
    print("✓ 分类数据插入完成")
    
    # 2. 插入用户
    users = [
        ('admin', '管理员', generate_password_hash('admin123'), 'admin', 20, '13800000001', 'admin@school.edu'),
        ('T001', '张老师', generate_password_hash('123456'), 'teacher', 10, '13800000002', 'zhang@school.edu'),
        ('S2024001', '李明', generate_password_hash('123456'), 'student', 5, '13800000003', 'liming@student.edu'),
        ('S2024002', '王小红', generate_password_hash('123456'), 'student', 5, '13800000004', 'wangxh@student.edu'),
        ('S2024003', '刘伟', generate_password_hash('123456'), 'student', 5, '13800000005', 'liuwei@student.edu'),
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO users (student_id, name, password_hash, role, max_borrow, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?)',
        users
    )
    print("✓ 用户数据插入完成")
    
    # 3. 插入图书
    books = [
        ('9787111213826', 'Python编程：从入门到实践', 'Eric Matthes', '人民邮电出版社', '2016-07-01',
         'https://img1.doubanio.com/view/subject/l/public/s28049685.jpg', 8, 'A-1-1', 5, 4,
         '本书是一本针对所有层次的Python读者而作的Python入门书。全书分两部分：第一部分介绍用Python编程所必须了解的基本概念，第二部分将理论付诸实践。'),
        
        ('9787302423287', '机器学习', '周志华', '清华大学出版社', '2016-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s28313499.jpg', 10, 'A-2-1', 3, 3,
         '机器学习是计算机科学与人工智能的重要分支领域。本书作为该领域的入门教材，在内容上尽可能涵盖机器学习基础知识的各方面。'),
        
        ('9787115546081', '活着', '余华', '作家出版社', '2017-08-01',
         'https://img9.doubanio.com/view/subject/l/public/s29614972.jpg', 6, 'B-1-1', 4, 3,
         '《活着》讲述了农村人福贵悲惨的人生遭遇。福贵本是个阔少爷，可他嗜赌如痕，最终赌光了家业，一贫如洗。'),
        
        ('9787020049294', '红楼梦', '曹雪芹', '人民文学出版社', '1996-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s1070958.jpg', 6, 'B-2-1', 3, 3,
         '《红楼梦》是一部具有世界影响力的人情小说作品，举世公认的中国古典小说巅峰之作。'),
        
        ('9787111385431', '人类简史', '尤瓦尔·赫拉利', '中信出版社', '2014-11-01',
         'https://img9.doubanio.com/view/subject/l/public/s27814883.jpg', 4, 'C-1-1', 2, 2,
         '十万年前，地球上至少有六种不同的人。但今天，只有我们。我们曾经只是非洲角落一个毫不起眼的族群。'),
        
        ('9787508639959', '三体', '刘慈欣', '重庆出版社', '2008-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s22742865.jpg', 6, 'B-3-1', 5, 4,
         '《三体》讲述了地球人类文明和三体文明之间的信息交流、生死搏杀及两个文明在宇宙中的兴衰历程。'),
        
        ('9787115249470', '算法导论', 'Thomas H.Cormen', '机械工业出版社', '2012-12-01',
         'https://img9.doubanio.com/view/subject/l/public/s4813768.jpg', 8, 'A-3-1', 2, 2,
         '本书深入讨论各类算法，并提供了全面的分析。内容深入浅出，算法导论全面的介绍了计算机算法。'),
        
        ('9787111213827', 'JavaScript高级程序设计', 'Nicholas C. Zakas', '人民邮电出版社', '2012-03-01',
         'https://img1.doubanio.com/view/subject/l/public/s10352642.jpg', 8, 'A-4-1', 3, 3,
         '本书是JavaScript超级畅销书的最新版。ECMAScript和DOM标准的发展不断提升。'),
        
        ('9787115396280', '数据结构与算法分析', 'Mark Allen Weiss', '机械工业出版社', '2010-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s4059263.jpg', 8, 'A-5-1', 3, 3,
         '本书是国外数据结构与算法分析方面的经典教材，使用Java语言描述。'),
        
        ('9787121310913', '深度学习入门', '斋藤康毅', '人民邮电出版社', '2018-07-01',
         'https://img9.doubanio.com/view/subject/l/public/s29705847.jpg', 10, 'A-6-1', 4, 4,
         '本书是深度学习入门的好书，基于Python3从理论铺垫到延伸实战，是入门深度学习的好书。'),
        
        ('9787535774393', '时间简史', '史蒂芬·霍金', '湖南科学技术出版社', '2014-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s24944564.jpg', 5, 'E-1-1', 2, 2,
         '《时间简史》讲述是探索时间和空间核心秘密的故事，是关于宇宙本性的最前沿知识。'),
        
        ('9787508679450', '经济学原理', '曼昆', '北京大学出版社', '2017-01-01',
         'https://img9.doubanio.com/view/subject/l/public/s29734237.jpg', 3, 'D-1-1', 3, 3,
         '曼昆的《经济学原理》是世界上最流行的经济学教材。'),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO books (isbn, title, author, publisher, publish_date, 
                                     cover_url, category_id, location, total_count, 
                                     available_count, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', books)
    print("✓ 图书数据插入完成")
    
    # 4. 插入借阅记录（部分已归还，部分在借，部分逾期）
    now = datetime.now()
    
    # 已归还的记录
    borrow_records = [
        (3, 1, (now - timedelta(days=35)).isoformat(), (now - timedelta(days=30)).isoformat(), 
         (now - timedelta(days=30)).isoformat(), 'returned', 1),
        (3, 6, (now - timedelta(days=25)).isoformat(), (now - timedelta(days=20)).isoformat(),
         (now - timedelta(days=20)).isoformat(), 'returned', 0),
        (4, 3, (now - timedelta(days=20)).isoformat(), (now - timedelta(days=15)).isoformat(),
         (now - timedelta(days=15)).isoformat(), 'returned', 0),
        (4, 7, (now - timedelta(days=10)).isoformat(), (now - timedelta(days=5)).isoformat(),
         (now - timedelta(days=5)).isoformat(), 'returned', 0),
        (5, 2, (now - timedelta(days=40)).isoformat(), (now - timedelta(days=35)).isoformat(),
         (now - timedelta(days=35)).isoformat(), 'returned', 2),
    ]
    
    # 在借的记录
    borrowed_records = [
        (3, 4, (now - timedelta(days=10)).isoformat(), (now + timedelta(days=20)).isoformat(),
         None, 'borrowed', 0),
        (4, 8, (now - timedelta(days=5)).isoformat(), (now + timedelta(days=25)).isoformat(),
         None, 'borrowed', 0),
        (5, 9, (now - timedelta(days=2)).isoformat(), (now + timedelta(days=28)).isoformat(),
         None, 'borrowed', 1),
    ]
    
    # 逾期记录
    overdue_records = [
        (3, 1, (now - timedelta(days=40)).isoformat(), (now - timedelta(days=10)).isoformat(),
         None, 'borrowed', 2),
    ]
    
    all_records = borrow_records + borrowed_records + overdue_records
    
    cursor.executemany('''
        INSERT OR IGNORE INTO borrow_records 
        (user_id, book_id, borrow_date, due_date, return_date, status, renew_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', all_records)
    print("✓ 借阅记录插入完成")
    
    # 5. 插入预约记录
    reservations = [
        (3, 2, (now - timedelta(days=3)).isoformat(), 'waiting', None),
        (4, 1, (now - timedelta(days=1)).isoformat(), 'waiting', None),
        (5, 6, (now - timedelta(days=5)).isoformat(), 'ready', (now - timedelta(days=1)).isoformat()),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO reservations 
        (user_id, book_id, reserve_date, status, notify_date)
        VALUES (?, ?, ?, ?, ?)
    ''', reservations)
    print("✓ 预约记录插入完成")
    
    # 6. 插入公告
    notices = [
        ('图书馆开放时间调整通知', 
         '各位读者：\n\n为更好地服务广大师生，图书馆即日起调整开放时间如下：\n'
         '周一至周五：8:00-22:00\n周六周日：9:00-21:00\n\n请各位读者合理安排借阅时间。',
         1),
        ('新书上架通知',
         '本期新书上架包括：《Python编程》、《深度学习入门》等热门技术书籍，欢迎借阅！',
         1),
        ('借阅规则说明',
         '1. 学生可借阅5本书，借期30天，可续借2次\n2. 教师可借阅10本书，借期60天\n'
         '3. 请按时归还，逾期将暂停借阅权限\n4. 预约图书到馆后保留3天',
         1),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO notices (title, content, author_id, is_active)
        VALUES (?, ?, ?, 1)
    ''', notices)
    print("✓ 公告数据插入完成")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    print("默认账号：")
    print("  管理员：admin / admin123")
    print("  教师：张老师 / 123456")
    print("  学生：李明 / 123456")
    print("=" * 50)


if __name__ == '__main__':
    init_database()

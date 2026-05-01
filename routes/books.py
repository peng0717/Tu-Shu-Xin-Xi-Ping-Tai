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
    
    # 处理分类：如果category_id为空，根据书名自动推断分类
    category_id = data.get('category_id')
    if not category_id:
        inferred = _infer_category_from_title(data.get('title', ''))
        if inferred:
            # 查找或创建分类
            cursor.execute('SELECT id FROM categories WHERE name = ?', (inferred,))
            existing = cursor.fetchone()
            if existing:
                category_id = existing['id']
            else:
                cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', 
                              (inferred, f'{inferred}类图书'))
                conn.commit()
                category_id = cursor.lastrowid
    
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
            category_id,
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
    
    # 检查是否已存在同名分类
    cursor.execute('SELECT id FROM categories WHERE name = ?', (data['name'],))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({'message': '分类已存在', 'category_id': existing['id']}), 200
    
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


# ========== AI智能补全相关函数 ==========

def _infer_category_from_title(title):
    """根据书名推断分类"""
    title_lower = title.lower()
    
    # 分类关键词映射
    category_keywords = {
        '计算机': ['python', 'java', 'javascript', '编程', '代码', '算法', '数据结构', '机器学习', '深度学习', '人工智能', 'ai', 'web', '前端', '后端', '数据库', 'sql', 'linux', 'git', '软件工程', '计算机', '编程语言', 'c++', 'c语言', 'rust', 'go', 'golang', 'node'],
        '小说': ['活着', '红楼梦', '三国演义', '水浒传', '西游记', '平凡的世界', '围城', '射雕英雄传', '天龙八部', '神雕侠侣', '百年孤独', '追风筝的人', '解忧杂货店', '挪威的森林', '哈利波特', '霍比特人', '魔戒', '指环王', '小说'],
        '文学': ['诗', '散文', '随笔', '文集', '文学', '人间词话', '谈美', '经典'],
        '历史': ['历史', '史记', '资治通鉴', '全球通史', '万历十五年', '明朝那些事', '人类简史', '未来简史'],
        '哲学': ['哲学', '尼采', '康德', '黑格尔', '苏菲的世界', '西方哲学史'],
        '经济学': ['经济学', '资本论', '国富论', '薛兆丰', '穷爸爸富爸爸', '巴菲特', '投资', '理财', '金融'],
        '心理学': ['心理学', '自卑与超越', '梦的解析', '乌合之众', '情商', '认知'],
        '科普': ['时间简史', '果壳中的宇宙', '第一推动', '科普', '科学'],
        '儿童文学': ['格林童话', '安徒生', '伊索寓言', '一千零一夜', '儿童', '绘本'],
        '传记': ['传记', '自传', '回忆录', '曾国藩', '苏东坡', '李白', '杜甫', '王阳明'],
    }
    
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in title_lower:
                return category
    
    return ''


def _infer_publisher_from_isbn(isbn):
    """根据ISBN前缀推断出版社"""
    if not isbn or len(isbn) < 4:
        return ''
    
    # 中国主要出版社ISBN前缀映射
    publisher_prefixes = {
        '978-7-111': '机械工业出版社',
        '978-7-115': '人民邮电出版社',
        '978-7-302': '清华大学出版社',
        '978-7-508': '中信出版社',
        '978-7-5322': '上海译文出版社',
        '978-7-5399': '人民文学出版社',
        '978-7-5322-2': '上海译文出版社',
        '978-7-5443': '海南出版社',
        '978-7-5611': '大连理工大学出版社',
        '978-7-122': '化学工业出版社',
        '978-7-5605': '西安交通大学出版社',
        '978-7-04': '高等教育出版社',
        '978-7-030': '北京大学出版社',
        '978-7-107': '人民教育出版社',
        '978-7-5000': '中国大百科全书出版社',
        '978-7-5322': '上海译文出版社',
        '978-7-80109': '作家出版社',
        '978-7-5064': '中国纺织出版社',
        '978-7-5381': '辽宁科学技术出版社',
        '978-7-80724': '京华出版社',
        '978-7-5322-1': '上海译文出版社',
    }
    
    # 尝试多种前缀匹配
    for prefix, publisher in publisher_prefixes.items():
        clean_prefix = prefix.replace('-', '')
        if isbn.startswith(clean_prefix):
            return publisher
    
    return ''


def _infer_publisher_from_author(author):
    """根据作者推断常用出版社"""
    if not author:
        return ''
    
    # 常见作者-出版社映射
    author_publishers = {
        '刘慈欣': '重庆出版社',
        '余华': '作家出版社',
        '莫言': '作家出版社',
        '韩少功': '作家出版社',
        '贾平凹': '作家出版社',
        '周作人': '北京十月文艺出版社',
        '鲁迅': '人民文学出版社',
        '村上春树': '上海译文出版社',
        '东野圭吾': '南海出版公司',
        '卡勒德·胡赛尼': '上海人民出版社',
        '加西亚·马尔克斯': '南海出版公司',
        'J.K.罗琳': '人民文学出版社',
        'J.R.R. Tolkien': '译林出版社',
        'Eric Matthes': '人民邮电出版社',
        '周志华': '清华大学出版社',
        '吴军': '人民邮电出版社',
        '尤瓦尔·赫拉利': '中信出版社',
    }
    
    for author_name, publisher in author_publishers.items():
        if author_name in author:
            return publisher
    
    return ''


def _generate_description(title, author, category):
    """根据书名、作者、分类生成较丰富的简介"""
    if not title:
        return ''
    
    main_author = author.split('/')[0].strip() if author else '佚名'
    
    # 根据分类生成不同风格的简介
    templates = {
        '计算机': f'《{title}》是{main_author}编著的计算机类图书。本书系统介绍了相关技术知识，内容深入浅出，适合初学者和进阶读者阅读。通过本书的学习，读者可以全面掌握{title.replace("编程","程序设计").replace("入门","基础")}的核心概念和实践方法，是相关领域从业者和学习者的必备参考书。',
        '小说': f'《{title}》是{main_author}创作的小说作品。本书以其独特的叙事手法和深刻的人物刻画，展现了丰富的文学内涵。作品情节引人入胜，语言优美流畅，具有极高的文学价值和阅读魅力，是{main_author}的代表作之一，深受广大读者喜爱。',
        '文学': f'《{title}》是{main_author}的文学代表作。作品以细腻的笔触和深邃的思想，展现了独特的文学魅力。书中蕴含丰富的人文关怀和深刻的社会思考，语言精炼优美，是文学爱好者不可错过的经典之作。',
        '历史': f'《{title}》是{main_author}撰写的历史类著作。本书以严谨的史学态度和生动的叙述方式，深入解读历史事件的来龙去脉，帮助读者以全新的视角理解历史。内容翔实，观点独到，是历史爱好者的重要参考读物。',
        '哲学': f'《{title}》是{main_author}的哲学著作。本书深入探讨了哲学的核心命题，以清晰的逻辑和深刻的思辨，引导读者思考人生与世界的本质。论述严谨而不失生动，是哲学入门与进阶的佳作。',
        '经济学': f'《{title}》是{main_author}撰写的经济学著作。本书系统地阐述了经济学理论与实践，结合丰富的案例和数据分析，帮助读者理解经济运行规律。内容通俗易懂，既有理论深度又有实践指导，是经济学领域的必读之书。',
        '心理学': f'《{title}》是{main_author}的心理学著作。本书以科学的视角深入剖析人类心理活动的规律，结合大量实验和案例，揭示了行为背后的心理机制。内容兼具学术性和可读性，对自我认知和人际交往具有重要启发意义。',
        '科普': f'《{title}》是{main_author}创作的科普读物。本书以通俗易懂的语言，将深奥的科学知识娓娓道来，让读者在轻松阅读中领略科学的魅力。内容生动有趣，图文并茂，是科学爱好者的优秀入门读物。',
        '儿童文学': f'《{title}》是{main_author}为儿童创作的文学作品。本书以充满想象力的故事和温馨感人的情节，陪伴小读者快乐成长。语言生动活泼，富有教育意义，是儿童阅读的优质选择。',
        '传记': f'《{title}》是关于{main_author}的传记作品。本书详实地记录了传主的生平事迹和心路历程，展现了其不平凡的人生经历和卓越成就。叙述真实感人，是一部值得细细品读的人物传记。',
    }
    
    # 如果有匹配的分类模板，使用它
    if category and category in templates:
        return templates[category]
    
    # 通用模板
    return f'《{title}》是{main_author}的作品。本书内容系统全面，论述深入浅出，对相关领域进行了详细的介绍和分析，是读者了解和学习该领域知识的重要参考。无论是入门学习还是深入研究，本书都具有很高的阅读价值。'


def _normalize_date(date_str):
    """标准化日期格式"""
    if not date_str:
        return ''
    
    # 如果已经是标准格式，直接返回
    import re
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # 如果只有年份，补全为 1月1日
    if re.match(r'^\d{4}$', date_str):
        return f'{date_str}-01-01'
    
    # 如果是 年-月 格式
    if re.match(r'^\d{4}-\d{1,2}$', date_str):
        return f'{date_str}-01'
    
    return date_str


@books_bp.route('/ai-fill', methods=['POST'])
def ai_fill():
    """
    AI智能补全接口
    根据已有信息智能推断并补全空字段
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    result = {
        'isbn': data.get('isbn', ''),
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'publisher': data.get('publisher', ''),
        'publish_date': data.get('publish_date', ''),
        'category': data.get('category', ''),
        'description': data.get('description', ''),
    }
    
    # 1. 补全ISBN（如果为空）
    if not result['isbn']:
        # 尝试从ISBN前缀推断出版社
        pass  # ISBN为空时无法推断
    
    # 2. 补全出版社（如果为空）
    if not result['publisher']:
        # 方式1: 从ISBN前缀推断
        isbn_infer = _infer_publisher_from_isbn(result.get('isbn', ''))
        if isbn_infer:
            result['publisher'] = isbn_infer
        else:
            # 方式2: 从作者推断
            author_infer = _infer_publisher_from_author(result.get('author', ''))
            if author_infer:
                result['publisher'] = author_infer
    
    # 3. 补全分类（如果为空）
    if not result['category']:
        category_infer = _infer_category_from_title(result.get('title', ''))
        if category_infer:
            result['category'] = category_infer
    
    # 4. 补全出版日期格式
    if result['publish_date']:
        result['publish_date'] = _normalize_date(result['publish_date'])
    
    # 5. 补全简介（如果为空）
    if not result['description'] and result['title']:
        result['description'] = _generate_description(
            result['title'], 
            result['author'], 
            result['category']
        )
    
    # 统计补全的字段
    filled_fields = []
    original = {
        'isbn': data.get('isbn', ''),
        'title': data.get('title', ''),
        'author': data.get('author', ''),
        'publisher': data.get('publisher', ''),
        'publish_date': data.get('publish_date', ''),
        'category': data.get('category', ''),
        'description': data.get('description', ''),
    }
    
    for key in original:
        if not original.get(key) and result.get(key):
            filled_fields.append(key)
    
    return jsonify({
        'success': True,
        'data': result,
        'filled_fields': filled_fields
    })

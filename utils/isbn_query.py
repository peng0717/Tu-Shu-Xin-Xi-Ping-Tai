# -*- coding: utf-8 -*-
"""
ISBN查询工具 - 调用豆瓣搜索、Google Books API获取图书信息
"""
import requests
import json
import re
from config import GOOGLE_BOOKS_API, OPENLIBRARY_API

# API超时时间（秒）
TIMEOUT = 8

# 请求头（模拟浏览器访问豆瓣）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 模拟图书数据（所有API不可用时的降级方案）
MOCK_BOOKS = {
    '9787111213826': {
        'title': 'Python编程：从入门到实践',
        'author': 'Eric Matthes',
        'publisher': '人民邮电出版社',
        'publish_date': '2016-07-01',
        'cover_url': 'https://img1.doubanio.com/view/subject/l/public/s28049685.jpg',
        'description': '本书是一本针对所有层次的Python读者而作的Python入门书。全书分两部分：第一部分介绍用Python编程所必须了解的基本概念，第二部分将理论付诸实践。'
    },
    '9787302423287': {
        'title': '机器学习',
        'author': '周志华',
        'publisher': '清华大学出版社',
        'publish_date': '2016-01-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s28313499.jpg',
        'description': '机器学习是计算机科学与人工智能的重要分支领域。本书作为该领域的入门教材，在内容上尽可能涵盖机器学习基础知识的各方面。'
    },
    '9787115546081': {
        'title': '活着',
        'author': '余华',
        'publisher': '作家出版社',
        'publish_date': '2017-08-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s29614972.jpg',
        'description': '《活着》讲述了农村人福贵悲惨的人生遭遇。福贵本是个阔少爷，可他嗜赌如命，终于赌光了家业，一贫如洗。'
    },
    '9787020049294': {
        'title': '红楼梦',
        'author': '曹雪芹',
        'publisher': '人民文学出版社',
        'publish_date': '1996-01-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s1070958.jpg',
        'description': '《红楼梦》是一部具有世界影响力的人情小说作品，举世公认的中国古典小说巅峰之作。'
    },
    '9787111385431': {
        'title': '人类简史',
        'author': '尤瓦尔·赫拉利',
        'publisher': '中信出版社',
        'publish_date': '2014-11-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s27814883.jpg',
        'description': '十万年前，地球上至少有六种不同的人。但今天，只有我们。我们曾经只是非洲角落一个毫不起眼的族群。'
    },
    '9787508639959': {
        'title': '三体',
        'author': '刘慈欣',
        'publisher': '重庆出版社',
        'publish_date': '2008-01-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s22742865.jpg',
        'description': '《三体》讲述了地球人类文明和三体文明之间的信息交流、生死搏杀及两个文明在宇宙中的兴衰历程。'
    },
    '9787115249470': {
        'title': '算法导论',
        'author': 'Thomas H.Cormen',
        'publisher': '机械工业出版社',
        'publish_date': '2012-12-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s4813768.jpg',
        'description': '本书深入讨论各类算法，并提供了全面的分析。内容深入浅出，算法导论全面的介绍了计算机算法。'
    },
    '9787111213827': {
        'title': 'JavaScript高级程序设计',
        'author': 'Nicholas C. Zakas',
        'publisher': '人民邮电出版社',
        'publish_date': '2012-03-01',
        'cover_url': 'https://img1.doubanio.com/view/subject/l/public/s10352642.jpg',
        'description': '本书是JavaScript超级畅销书的最新版。ECMAScript和DOM标准的发展不断提升。'
    },
    '9787115396280': {
        'title': '数据结构与算法分析',
        'author': 'Mark Allen Weiss',
        'publisher': '机械工业出版社',
        'publish_date': '2010-01-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s4059263.jpg',
        'description': '本书是国外数据结构与算法分析方面的经典教材，使用Java语言描述。'
    },
    '9787121310913': {
        'title': '深度学习入门',
        'author': '斋藤康毅',
        'publisher': '人民邮电出版社',
        'publish_date': '2018-07-01',
        'cover_url': 'https://img9.doubanio.com/view/subject/l/public/s29705847.jpg',
        'description': '本书是深度学习入门的好书，基于Python3从理论铺垫到延伸实战，是入门深度学习的好书。'
    }
}


def _parse_douban_abstract(abstract):
    """解析豆瓣搜索结果中的abstract字段，提取作者、出版社等信息
    abstract格式示例: "[美]埃里克·马瑟斯（Eric Matthes） / 袁国忠 / 人民邮电出版社 / 2020-10 / 109.8"
    """
    parts = [p.strip() for p in abstract.split('/')]
    author = parts[0] if len(parts) > 0 else ''
    translator = parts[1] if len(parts) > 1 and '译' in parts[1] else ''
    publisher = ''
    publish_date = ''
    
    for part in parts[1:]:
        part = part.strip()
        # 匹配出版社（中文或英文名称）
        if not publisher and re.search(r'[\u4e00-\u9fff出版社]', part) and not re.match(r'^\d', part):
            publisher = part
        # 匹配出版日期
        if not publish_date and re.match(r'^\d{4}', part):
            publish_date = part
    
    if translator:
        author = f"{author} / {translator}"
    
    return {
        'author': author,
        'publisher': publisher,
        'publish_date': publish_date
    }


def _query_douban(isbn):
    """通过豆瓣搜索页面查询图书信息"""
    try:
        url = f'https://search.douban.com/book/subject_search?search_text={isbn}'
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code == 200:
            match = re.search(r'window\.__DATA__\s*=\s*(\{.*?\});', response.text)
            if match:
                data = json.loads(match.group(1))
                items = data.get('items', [])
                
                if items:
                    item = items[0]
                    title = item.get('title', '')
                    cover_url = item.get('cover_url', '')
                    abstract = item.get('abstract', '')
                    
                    parsed = _parse_douban_abstract(abstract)
                    
                    return {
                        'success': True,
                        'source': 'douban_search',
                        'data': {
                            'title': title,
                            'author': parsed['author'],
                            'publisher': parsed['publisher'],
                            'publish_date': parsed['publish_date'],
                            'cover_url': cover_url,
                            'description': ''
                        }
                    }
    except Exception as e:
        print(f"豆瓣搜索请求失败: {e}")
    
    return None


def _query_google_books(isbn):
    """通过Google Books API查询图书信息"""
    try:
        url = GOOGLE_BOOKS_API.format(isbn)
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                volume_info = data['items'][0]['volumeInfo']
                
                cover_url = ''
                if 'imageLinks' in volume_info:
                    cover_url = volume_info['imageLinks'].get('thumbnail', '').replace('http://', 'https://')
                
                return {
                    'success': True,
                    'source': 'google_books',
                    'data': {
                        'title': volume_info.get('title', ''),
                        'author': ', '.join(volume_info.get('authors', [])),
                        'publisher': volume_info.get('publisher', ''),
                        'publish_date': volume_info.get('publishedDate', ''),
                        'cover_url': cover_url,
                        'description': volume_info.get('description', '')
                    }
                }
    except Exception as e:
        print(f"Google Books API请求失败: {e}")
    
    return None


def _query_openlibrary(isbn):
    """通过OpenLibrary API查询图书信息"""
    try:
        url = OPENLIBRARY_API.format(isbn)
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            key = f"ISBN:{isbn}"
            
            if key in data:
                book_data = data[key]
                authors = []
                if 'authors' in book_data:
                    authors = [a['name'] for a in book_data['authors']]
                
                cover_url = ''
                if 'cover' in book_data:
                    cover = book_data['cover']
                    if 'large' in cover:
                        cover_url = cover['large']
                    elif 'medium' in cover:
                        cover_url = cover['medium']
                    elif 'small' in cover:
                        cover_url = cover['small']
                
                return {
                    'success': True,
                    'source': 'openlibrary',
                    'data': {
                        'title': book_data.get('title', ''),
                        'author': ', '.join(authors),
                        'publisher': book_data['publishers'][0]['name'] if 'publishers' in book_data and book_data['publishers'] else '',
                        'publish_date': book_data.get('publish_date', ''),
                        'cover_url': cover_url,
                        'description': book_data.get('subtitle', '')
                    }
                }
    except Exception as e:
        print(f"OpenLibrary API请求失败: {e}")
    
    return None


def _get_douban_book_description(url):
    """从豆瓣书籍详情页获取简介信息"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            # 尝试从页面中提取简介
            # 方式1: 从 #link-report 提取
            match = re.search(r'<div id="link-report"[^>]*>.*?<div class="intro"[^>]*>(.*?)</div>', response.text, re.DOTALL)
            if match:
                description = match.group(1)
                # 清理HTML标签
                description = re.sub(r'<[^>]+>', '', description).strip()
                return description[:500] if len(description) > 500 else description
            
            # 方式2: 从 abstract 字段提取
            match = re.search(r'"abstract"\s*:\s*"([^"]+)"', response.text)
            if match:
                return match.group(1)[:500] if len(match.group(1)) > 500 else match.group(1)
    except Exception as e:
        print(f"获取豆瓣详情失败: {e}")
    return ''


def query_isbn(isbn):
    """
    通过ISBN查询图书信息
    查询顺序：MOCK_BOOKS → 豆瓣搜索 → Google Books → OpenLibrary → 失败
    """
    # 清理ISBN（去除空格和特殊字符）
    isbn = isbn.strip().replace('-', '').replace(' ', '')
    
    # 先检查模拟数据
    if isbn in MOCK_BOOKS:
        return {
            'success': True,
            'source': 'mock',
            'data': MOCK_BOOKS[isbn]
        }
    
    # 豆瓣搜索（国内最稳定，中文书覆盖最好）
    result = _query_douban(isbn)
    if result:
        return result
    
    # Google Books API
    result = _query_google_books(isbn)
    if result:
        return result
    
    # OpenLibrary API
    result = _query_openlibrary(isbn)
    if result:
        return result
    
    # 所有API都失败
    return {
        'success': False,
        'source': 'none',
        'error': '无法获取图书信息，请手动输入'
    }


def search_book_by_title(keyword):
    """
    通过书名搜索图书信息（调用豆瓣搜索）
    返回格式：[{'isbn': '', 'title': '', 'author': '', 'publisher': '', 'publish_date': '', 'cover_url': '', 'description': ''}, ...]
    """
    # 先检查模拟数据中是否有匹配
    results = []
    keyword_lower = keyword.lower()
    
    for isbn, book in MOCK_BOOKS.items():
        if keyword_lower in book['title'].lower() or keyword_lower in book['author'].lower():
            results.append({
                'isbn': isbn,
                **book
            })
    
    # 调用豆瓣搜索
    try:
        url = f'https://search.douban.com/book/subject_search?search_text={requests.utils.quote(keyword)}&cat=1001'
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        
        if response.status_code == 200:
            match = re.search(r'window\.__DATA__\s*=\s*(\{.*?\});', response.text)
            if match:
                data = json.loads(match.group(1))
                items = data.get('items', [])
                
                for item in items[:10]:  # 最多返回10个结果
                    try:
                        title = item.get('title', '')
                        cover_url = item.get('cover_url', '')
                        abstract = item.get('abstract', '')
                        url_link = item.get('url', '')
                        book_id = item.get('id', '')
                        
                        # 解析abstract获取作者、出版社、出版日期
                        parsed = _parse_douban_abstract(abstract)
                        
                        # 尝试获取详情页简介
                        description = ''
                        if book_id:
                            detail_url = f'https://book.douban.com/subject/{book_id}/'
                            description = _get_douban_book_description(detail_url)
                        
                        results.append({
                            'isbn': '',  # 豆瓣搜索结果中没有ISBN
                            'title': title,
                            'author': parsed['author'],
                            'publisher': parsed['publisher'],
                            'publish_date': parsed['publish_date'],
                            'cover_url': cover_url,
                            'description': description
                        })
                    except Exception as e:
                        print(f"解析豆瓣搜索结果失败: {e}")
                        continue
    except Exception as e:
        print(f"豆瓣书名搜索请求失败: {e}")
    
    # 去重（根据书名）
    seen_titles = set()
    unique_results = []
    for book in results:
        title_key = book['title'].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_results.append(book)
    
    return unique_results

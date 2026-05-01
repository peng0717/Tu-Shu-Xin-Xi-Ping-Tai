# -*- coding: utf-8 -*-
"""
ISBN查询工具 - 调用豆瓣API获取图书信息
"""
import requests
import time
from config import DOUBAN_API_BASE, DOUBAN_API_BACKUP

# 豆瓣API超时时间（秒）
TIMEOUT = 5

# 模拟图书数据（豆瓣API不可用时的降级方案）
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


def query_isbn(isbn):
    """
    通过ISBN查询图书信息
    优先使用豆瓣API，失败则使用模拟数据
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
    
    # 尝试豆瓣API
    try:
        # 尝试主API
        url = f"{DOUBAN_API_BASE}{isbn}"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'source': 'douban',
                'data': {
                    'title': data.get('title', ''),
                    'author': ', '.join(data.get('author', [])),
                    'publisher': data.get('publisher', ''),
                    'publish_date': data.get('pubdate', ''),
                    'cover_url': data.get('image', ''),
                    'description': data.get('summary', '')
                }
            }
    except Exception as e:
        print(f"豆瓣API请求失败: {e}")
    
    # 尝试备用API
    try:
        url = f"{DOUBAN_API_BACKUP}{isbn}"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'source': 'douban_backup',
                'data': {
                    'title': data.get('title', ''),
                    'author': ', '.join(data.get('author', [])),
                    'publisher': data.get('publisher', ''),
                    'publish_date': data.get('pubdate', ''),
                    'cover_url': data.get('image', ''),
                    'description': data.get('summary', '')
                }
            }
    except Exception as e:
        print(f"豆瓣备用API请求失败: {e}")
    
    # 如果所有API都失败，返回失败信息
    return {
        'success': False,
        'source': 'none',
        'error': '无法获取图书信息，请手动输入'
    }


def search_book_by_title(keyword):
    """
    通过书名搜索图书信息（模拟豆瓣搜索）
    """
    results = []
    keyword_lower = keyword.lower()
    
    for isbn, book in MOCK_BOOKS.items():
        if keyword_lower in book['title'].lower() or keyword_lower in book['author'].lower():
            results.append({
                'isbn': isbn,
                **book
            })
    
    return results

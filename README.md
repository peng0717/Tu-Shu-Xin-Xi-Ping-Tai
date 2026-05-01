# 图书信息一体化平台

一个功能完整的图书馆管理系统，包括 Flask 后端、微信小程序前端和 Web 管理后台。

## 📁 项目结构

```
图书信息平台/
├── app.py                 # Flask 主入口
├── config.py             # 配置文件
├── models.py             # 数据库模型
├── init_db.py            # 数据库初始化脚本
├── requirements.txt       # Python 依赖
├── library.db            # SQLite 数据库（自动生成）
│
├── routes/               # API 路由
│   ├── auth.py          # 认证接口（登录、注册）
│   ├── books.py         # 图书接口（CRUD、搜索）
│   ├── borrow.py         # 借还接口
│   ├── reservation.py   # 预约接口
│   ├── stats.py         # 统计接口
│   └── notice.py        # 公告接口
│
├── utils/                # 工具函数
│   ├── auth.py          # JWT 认证工具
│   └── isbn_query.py     # 豆瓣 API 查询
│
├── templates/            # Web 管理后台模板
│   ├── index.html       # 首页
│   ├── error.html       # 错误页
│   └── admin/
│       ├── login.html   # 管理员登录
│       ├── index.html   # 管理后台首页
│       ├── books.html   # 图书管理
│       ├── borrows.html # 借还管理
│       ├── users.html   # 读者管理
│       ├── notices.html # 公告管理
│       ├── reservations.html # 预约管理
│       └── stats.html   # 统计报表
│
└── miniprogram/          # 微信小程序
    ├── app.json         # 小程序配置
    ├── app.js           # 全局逻辑
    ├── app.wxss         # 全局样式
    ├── project.config.json # 项目配置
    └── pages/
        ├── index/       # 首页
        ├── search/      # 搜索页
        ├── book-detail/ # 图书详情
        ├── borrow/      # 借书页
        ├── my/          # 个人中心
        ├── my-borrows/  # 借阅记录
        ├── notice/      # 公告列表
        ├── notice-detail/ # 公告详情
        └── login/       # 登录页
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd 图书信息平台
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_db.py
```

这会创建所有表并插入示例数据。

### 3. 启动服务

```bash
python app.py
```

启动后显示：
```
==================================================
图书信息一体化平台
==================================================
API接口地址: http://127.0.0.1:5000/api
Web管理后台: http://127.0.0.1:5000/admin
默认管理员账号: admin / admin123
==================================================
```

## 📱 访问地址

| 服务 | 地址 |
|------|------|
| Web 首页 | http://127.0.0.1:5000/ |
| Web 管理后台 | http://127.0.0.1:5000/admin |
| API 接口 | http://127.0.0.1:5000/api |

## 🔐 默认账号

| 角色 | 账号 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | admin | admin123 | 可管理所有功能 |
| 教师 | T001 | 123456 | 可借10本书 |
| 学生 | S2024001 | 123456 | 可借5本书 |
| 学生 | S2024002 | 123456 | 可借5本书 |
| 学生 | S2024003 | 123456 | 可借5本书 |

## 📚 API 接口列表

### 认证接口
- `POST /api/auth/login` - 登录
- `POST /api/auth/register` - 注册
- `GET /api/auth/me` - 获取当前用户信息

### 图书接口
- `GET /api/books` - 获取图书列表
- `GET /api/books/{id}` - 获取图书详情
- `POST /api/books` - 添加图书（需管理员权限）
- `PUT /api/books/{id}` - 更新图书
- `DELETE /api/books/{id}` - 删除图书
- `GET /api/books/hot` - 热门图书
- `GET /api/books/new` - 新书上架
- `GET /api/books/isbn/query` - ISBN查询（豆瓣API）
- `GET /api/books/categories` - 获取分类

### 借还接口
- `POST /api/borrow/borrow` - 借书
- `POST /api/borrow/return` - 还书
- `POST /api/borrow/renew` - 续借
- `GET /api/borrow/my` - 我的借阅记录
- `GET /api/borrow/all` - 所有借阅记录（需管理员权限）

### 预约接口
- `POST /api/reservation/reserve` - 预约图书
- `POST /api/reservation/cancel` - 取消预约
- `GET /api/reservation/my` - 我的预约
- `GET /api/reservation/all` - 所有预约（需管理员权限）

### 统计接口
- `GET /api/stats/dashboard` - 仪表盘统计
- `GET /api/stats/borrow-trend` - 借阅趋势
- `GET /api/stats/hot-books` - 热门图书统计
- `GET /api/stats/overdue-list` - 逾期列表
- `GET /api/stats/user-borrows` - 用户借阅统计

### 公告接口
- `GET /api/notice` - 公告列表
- `GET /api/notice/{id}` - 公告详情
- `POST /api/notice` - 发布公告（需管理员权限）
- `PUT /api/notice/{id}` - 更新公告
- `DELETE /api/notice/{id}` - 删除公告

## 📦 小程序配置

### AppID
```
wx07dd1d4fdd2e6908
```

### 修改 API 地址

在 `miniprogram/app.js` 中修改：
```javascript
const API_BASE = 'http://127.0.0.1:5000/api';
```

部署到正式环境时需要改为你的服务器地址：
```javascript
const API_BASE = 'https://your-domain.com/api';
```

### 导入小程序

1. 打开微信开发者工具
2. 导入项目，选择 `图书信息平台/miniprogram` 目录
3. 填入 AppID: `wx07dd1d4fdd2e6908`
4. 点击导入即可

## 🛠️ 功能特性

### Web 管理后台
- ✅ 仪表盘统计（图书总数、在馆数量、逾期统计）
- ✅ 图书管理（增删改查、ISBN扫码添加）
- ✅ 借还管理（借书、还书、续借）
- ✅ 读者管理（添加读者、设置角色）
- ✅ 预约管理（处理预约、通知取书）
- ✅ 公告管理（发布、编辑公告）
- ✅ 统计报表（借阅趋势、热门图书、用户排行）

### 微信小程序
- ✅ 首页（热门推荐、新书上架、公告轮播）
- ✅ 搜索（书名、作者、ISBN搜索）
- ✅ 图书详情（借阅、预约）
- ✅ 扫码借书（ISBN识别）
- ✅ 个人中心（借阅统计）
- ✅ 我的借阅（查看、续借、还书）
- ✅ 公告查看

## 🔧 技术栈

- **后端**：Flask 2.3.3 + SQLite
- **前端**：微信小程序原生开发
- **样式**：Bootstrap 5 + 自定义CSS
- **认证**：JWT Token
- **数据源**：豆瓣 API（带降级方案）

## 📝 注意事项

1. **豆瓣 API 限制**：豆瓣 API 有访问频率限制，已内置降级方案（模拟数据）
2. **CORS 跨域**：已启用 CORS，支持跨域请求
3. **密码加密**：使用 werkzeug.security 加密存储
4. **小程序调试**：需要勾选"不校验合法域名"才能访问本地 API

## 📄 许可证

MIT License

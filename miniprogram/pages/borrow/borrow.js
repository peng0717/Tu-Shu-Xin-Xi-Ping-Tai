// 借书页
const app = getApp();

Page({
  data: {
    isbn: '',
    book: {},
    history: []
  },
  
  onLoad() {
    // 加载扫描历史
    const history = wx.getStorageSync('scanHistory') || [];
    this.setData({ history: history.slice(0, 5) });
  },
  
  onInput(e) {
    this.setData({ isbn: e.detail.value });
  },
  
  scanISBN() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    
    // 模拟扫码（实际使用 wx.scanCode）
    wx.scanCode({
      success: (res) => {
        this.setData({ isbn: res.result });
        this.queryByISBN(res.result);
      },
      fail: () => {
        wx.showToast({ title: '扫码取消', icon: 'none' });
      }
    });
  },
  
  async queryBook() {
    const isbn = this.data.isbn.trim();
    if (!isbn) {
      wx.showToast({ title: '请输入ISBN', icon: 'none' });
      return;
    }
    await this.queryByISBN(isbn);
  },
  
  async queryByISBN(isbn) {
    try {
      wx.showLoading({ title: '查询中...' });
      
      // 先通过ISBN查询图书信息
      const isbnRes = await app.request(`/books/isbn/query?isbn=${isbn}`);
      
      if (isbnRes.success) {
        // 根据书名搜索图书
        const booksRes = await app.request(`/books?keyword=${encodeURIComponent(isbnRes.data.title)}`);
        
        if (booksRes.books && booksRes.books.length > 0) {
          // 找到匹配的图书
          const book = booksRes.books.find(b => b.isbn === isbn) || booksRes.books[0];
          this.setData({ book });
        } else {
          // 未找到，使用ISBN数据创建临时对象
          this.setData({
            book: {
              id: 0,
              title: isbnRes.data.title,
              author: isbnRes.data.author,
              publisher: isbnRes.data.publisher,
              cover_url: isbnRes.data.cover_url,
              isbn: isbn,
              available_count: 0,
              total_count: 1
            }
          });
          wx.showToast({ title: '该书不在图书馆藏中', icon: 'none' });
        }
      } else {
        wx.showToast({ title: isbnRes.error || '未找到图书', icon: 'none' });
      }
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '查询失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },
  
  async borrowBook() {
    if (!this.data.book.id) {
      wx.showToast({ title: '该书无法借阅', icon: 'none' });
      return;
    }
    
    wx.showModal({
      title: '确认借阅',
      content: `确定要借阅《${this.data.book.title}》吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await app.request('/borrow/borrow', 'POST', {
              book_id: this.data.book.id
            });
            
            // 添加到历史
            const history = this.data.history;
            history.unshift({
              id: this.data.book.id,
              title: this.data.book.title,
              time: new Date().toLocaleDateString()
            });
            wx.setStorageSync('scanHistory', history.slice(0, 10));
            
            wx.showToast({ title: result.message || '借阅成功', icon: 'success' });
            this.setData({ book: {}, isbn: '' });
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  },
  
  goDetail(e) {
    wx.navigateTo({ url: `/pages/book-detail/book-detail?id=${e.currentTarget.dataset.id}` });
  }
});

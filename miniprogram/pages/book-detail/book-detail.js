// 图书详情页
const app = getApp();

Page({
  data: {
    book: {}
  },
  
  onLoad(options) {
    if (options.id) {
      this.loadBook(options.id);
    }
  },
  
  async loadBook(id) {
    try {
      const res = await app.request(`/books/${id}`);
      this.setData({ book: res.book || {} });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },
  
  borrowBook() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    
    wx.showModal({
      title: '确认借阅',
      content: `确定要借阅《${this.data.book.title}》吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const res = await app.request('/borrow/borrow', 'POST', {
              book_id: this.data.book.id
            });
            wx.showToast({ title: res.message || '借阅成功', icon: 'success' });
            // 刷新数据
            this.loadBook(this.data.book.id);
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  },
  
  reserveBook() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    
    wx.showModal({
      title: '确认预约',
      content: `确定要预约《${this.data.book.title}》吗？到书后我们会通知您。`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const res = await app.request('/reservation/reserve', 'POST', {
              book_id: this.data.book.id
            });
            wx.showToast({ title: res.message || '预约成功', icon: 'success' });
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  }
});

// 首页逻辑
const app = getApp();

Page({
  data: {
    hotBooks: [],
    newBooks: [],
    notices: []
  },
  
  onLoad() {
    this.loadData();
  },
  
  onShow() {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.showModal({
        title: '提示',
        content: '登录后即可借书和查看借阅记录',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' });
          }
        }
      });
    }
  },
  
  onPullDownRefresh() {
    this.loadData();
  },
  
  async loadData() {
    try {
      // 并行加载数据
      const [hotRes, newRes, noticeRes] = await Promise.all([
        app.request('/books/hot?limit=6'),
        app.request('/books/new?limit=5'),
        app.request('/notice?page_size=3')
      ]);
      
      this.setData({
        hotBooks: hotRes.books || [],
        newBooks: newRes.books || [],
        notices: noticeRes.notices || []
      });
      
      wx.stopPullDownRefresh();
    } catch (e) {
      console.error('加载失败', e);
      wx.stopPullDownRefresh();
    }
  },
  
  goSearch() {
    wx.switchTab({ url: '/pages/search/search' });
  },
  
  goBookDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/book-detail/book-detail?id=${id}` });
  },
  
  goBorrow() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    wx.switchTab({ url: '/pages/borrow/borrow' });
  },
  
  goMyBorrows() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    wx.navigateTo({ url: '/pages/my-borrows/my-borrows' });
  },
  
  goNotice() {
    wx.navigateTo({ url: '/pages/notice/notice' });
  },
  
  goNoticeDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/notice-detail/notice-detail?id=${id}` });
  }
});

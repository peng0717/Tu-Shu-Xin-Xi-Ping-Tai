// 我的页面
const app = getApp();

Page({
  data: {
    userInfo: null,
    stats: {
      current: 0,
      borrowed: 0,
      overdue: 0
    }
  },
  
  onShow() {
    // 获取用户信息
    const userInfo = app.globalData.userInfo;
    this.setData({ userInfo });
    
    if (userInfo) {
      this.loadStats();
    }
  },
  
  async loadStats() {
    try {
      const res = await app.request('/borrow/my');
      const records = res.records || [];
      
      const now = new Date();
      let current = 0, overdue = 0;
      
      records.forEach(r => {
        if (r.status === 'borrowed') {
          current++;
          if (new Date(r.due_date) < now) {
            overdue++;
          }
        }
      });
      
      this.setData({
        stats: {
          current,
          borrowed: records.length,
          overdue
        }
      });
    } catch (e) {
      console.error(e);
    }
  },
  
  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },
  
  goMyBorrows() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    wx.navigateTo({ url: '/pages/my-borrows/my-borrows' });
  },
  
  goMyReservations() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' });
      return;
    }
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },
  
  goNotice() {
    wx.navigateTo({ url: '/pages/notice/notice' });
  },
  
  showAbout() {
    wx.showModal({
      title: '关于系统',
      content: '图书信息一体化平台 v1.0\n\n为学校图书馆打造的智能化管理系统',
      showCancel: false
    });
  },
  
  logout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = null;
          app.globalData.userInfo = null;
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          this.setData({ userInfo: null, stats: { current: 0, borrowed: 0, overdue: 0 } });
          wx.showToast({ title: '已退出登录', icon: 'success' });
        }
      }
    });
  }
});

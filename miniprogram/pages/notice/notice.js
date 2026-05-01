// 公告列表页
const app = getApp();

Page({
  data: {
    notices: [],
    loading: false
  },
  
  onLoad() {
    this.loadNotices();
  },
  
  async loadNotices() {
    this.setData({ loading: true });
    
    try {
      const res = await app.request('/notice?page_size=50');
      const notices = res.notices || [];
      
      // 处理日期
      notices.forEach(n => {
        n.created_at = n.created_at?.slice(0, 10) || '';
      });
      
      this.setData({ notices, loading: false });
    } catch (e) {
      console.error(e);
      this.setData({ loading: false });
    }
  },
  
  goDetail(e) {
    wx.navigateTo({ url: `/pages/notice-detail/notice-detail?id=${e.currentTarget.dataset.id}` });
  }
});

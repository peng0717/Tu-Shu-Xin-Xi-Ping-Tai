// 公告详情页
const app = getApp();

Page({
  data: {
    notice: {}
  },
  
  onLoad(options) {
    if (options.id) {
      this.loadNotice(options.id);
    }
  },
  
  async loadNotice(id) {
    try {
      const res = await app.request(`/notice/${id}`);
      const notice = res.notice || {};
      notice.created_at = notice.created_at?.slice(0, 10) || '';
      this.setData({ notice });
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  }
});

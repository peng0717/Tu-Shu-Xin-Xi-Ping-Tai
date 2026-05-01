// 我的借阅记录页
const app = getApp();

Page({
  data: {
    tab: 'borrowed',
    records: [],
    borrowedCount: 0,
    returnedCount: 0,
    loading: false
  },
  
  onLoad() {
    this.loadRecords();
  },
  
  onShow() {
    this.loadRecords();
  },
  
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ tab });
    this.loadRecords();
  },
  
  async loadRecords() {
    this.setData({ loading: true });
    
    try {
      const res = await app.request('/borrow/my');
      const records = res.records || [];
      const now = new Date();
      
      // 处理逾期状态
      records.forEach(r => {
        r.borrow_date = r.borrow_date?.slice(0, 10) || '';
        r.due_date = r.due_date?.slice(0, 10) || '';
        if (r.status === 'borrowed') {
          r.is_overdue = new Date(r.due_date) < now;
        }
      });
      
      const borrowed = records.filter(r => r.status === 'borrowed');
      const returned = records.filter(r => r.status === 'returned');
      
      this.setData({
        records: this.data.tab === 'borrowed' ? borrowed : returned,
        borrowedCount: borrowed.length,
        returnedCount: returned.length,
        loading: false
      });
    } catch (e) {
      console.error(e);
      this.setData({ loading: false });
    }
  },
  
  goDetail(e) {
    wx.navigateTo({ url: `/pages/book-detail/book-detail?id=${e.currentTarget.dataset.id}` });
  },
  
  async renew(e) {
    const bookId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认续借',
      content: '确定要续借这本书吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await app.request('/borrow/renew', 'POST', { book_id: bookId });
            wx.showToast({ title: result.message || '续借成功', icon: 'success' });
            this.loadRecords();
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  },
  
  async returnBook(e) {
    const bookId = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认还书',
      content: '确定要归还这本书吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await app.request('/borrow/return', 'POST', { book_id: bookId });
            const msg = result.is_overdue ? '还书成功（已逾期）' : '还书成功';
            wx.showToast({ title: msg, icon: 'success' });
            this.loadRecords();
          } catch (e) {
            console.error(e);
          }
        }
      }
    });
  }
});

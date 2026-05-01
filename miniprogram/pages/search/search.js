// 搜索页逻辑
const app = getApp();

Page({
  data: {
    keyword: '',
    books: [],
    loading: false,
    focus: false
  },
  
  onLoad() {
    this.setData({ focus: true });
  },
  
  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },
  
  clearKeyword() {
    this.setData({ keyword: '', books: [] });
  },
  
  cancel() {
    wx.switchTab({ url: '/pages/index/index' });
  },
  
  async search() {
    const keyword = this.data.keyword.trim();
    if (!keyword) return;
    
    this.setData({ loading: true, books: [] });
    
    try {
      const res = await app.request(`/books?keyword=${encodeURIComponent(keyword)}`);
      this.setData({ books: res.books || [] });
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ loading: false });
    }
  },
  
  goBookDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/book-detail/book-detail?id=${id}` });
  }
});

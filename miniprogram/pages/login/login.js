// 登录页
const app = getApp();

Page({
  data: {
    studentId: '',
    password: ''
  },
  
  onStudentIdInput(e) {
    this.setData({ studentId: e.detail.value });
  },
  
  onPasswordInput(e) {
    this.setData({ password: e.detail.value });
  },
  
  fillDemo(e) {
    this.setData({
      studentId: e.currentTarget.dataset.id,
      password: e.currentTarget.dataset.pwd
    });
  },
  
  async login() {
    const { studentId, password } = this.data;
    
    if (!studentId || !password) {
      wx.showToast({ title: '请填写账号密码', icon: 'none' });
      return;
    }
    
    try {
      wx.showLoading({ title: '登录中...' });
      
      const res = await app.request('/auth/login', 'POST', {
        student_id: studentId,
        password: password
      });
      
      // 保存登录信息
      app.globalData.token = res.token;
      app.globalData.userInfo = res.user;
      wx.setStorageSync('token', res.token);
      wx.setStorageSync('userInfo', res.user);
      
      wx.hideLoading();
      wx.showToast({ title: '登录成功', icon: 'success' });
      
      // 返回上一页或跳转首页
      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.switchTab({ url: '/pages/index/index' });
        }
      }, 1500);
    } catch (e) {
      wx.hideLoading();
      console.error(e);
    }
  },
  
  register() {
    wx.showToast({ title: '请联系管理员注册', icon: 'none' });
  }
});

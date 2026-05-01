// 小程序全局配置
const API_BASE = 'http://127.0.0.1:5000/api';

App({
  globalData: {
    userInfo: null,
    token: null,
    API_BASE: API_BASE
  },
  
  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
    }
  },
  
  // 检查登录
  checkLogin(callback) {
    if (this.globalData.token) {
      callback(true);
    } else {
      wx.showModal({
        title: '提示',
        content: '请先登录',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' });
          }
        }
      });
      callback(false);
    }
  },
  
  // API请求封装
  request(url, method = 'GET', data = {}) {
    return new Promise((resolve, reject) => {
      wx.showLoading({ title: '加载中...' });
      
      wx.request({
        url: API_BASE + url,
        method: method,
        data: data,
        header: {
          'Content-Type': 'application/json',
          'Authorization': this.globalData.token ? `Bearer ${this.globalData.token}` : ''
        },
        success: (res) => {
          wx.hideLoading();
          if (res.statusCode === 200) {
            resolve(res.data);
          } else if (res.statusCode === 401) {
            // Token过期，重新登录
            this.globalData.token = null;
            this.globalData.userInfo = null;
            wx.removeStorageSync('token');
            wx.removeStorageSync('userInfo');
            wx.showToast({ title: '请重新登录', icon: 'none' });
            wx.navigateTo({ url: '/pages/login/login' });
            reject(res.data);
          } else {
            wx.showToast({ title: res.data.error || '请求失败', icon: 'none' });
            reject(res.data);
          }
        },
        fail: (err) => {
          wx.hideLoading();
          wx.showToast({ title: '网络请求失败', icon: 'none' });
          reject(err);
        }
      });
    });
  }
});

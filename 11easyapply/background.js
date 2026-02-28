// background.js - 后台服务脚本

// 扩展程序安装时初始化
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    // 不写入忽字段，由 popup.js 的 loadProfiles 接管初始化逻辑
    chrome.storage.local.set({
      profiles: {},
      activeProfileId: 'default',
      applicationRecords: []
    });
    console.log('EasyApply: 扩展已安装');
  }
});

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 可以在这里处理一些后台逻辑
  console.log('Background收到消息:', request);
});

// background.js - Chrome插件后台服务

const API_BASE = 'http://127.0.0.1:8000';

// 插件安装时触发
chrome.runtime.onInstalled.addListener(() => {
    console.log('21视频下载器插件已安装');
});

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'download') {
        handleDownload(message.url, message.title);
    }
    return true;
});

// 处理下载请求
async function handleDownload(url, title) {
    try {
        const res = await fetch(`${API_BASE}/api/add_task`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                source: 'content_script'
            })
        });
        
        const data = await res.json();
        return data;
    } catch (e) {
        console.error('Download failed:', e);
        return { status: 'error', message: e.message };
    }
}

// 检查服务状态
async function checkServiceStatus() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        return res.ok;
    } catch (e) {
        return false;
    }
}

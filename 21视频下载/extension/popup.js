// popup.js - 插件弹窗逻辑

const API_BASE = 'http://127.0.0.1:8000';
let currentUrl = '';
let isOnline = false;

// DOM元素
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const pageUrl = document.getElementById('pageUrl');
const videoTitleContainer = document.getElementById('videoTitleContainer');
const videoTitle = document.getElementById('videoTitle');
const downloadBtn = document.getElementById('downloadBtn');
const captureBtn = document.getElementById('captureBtn');
const messageEl = document.getElementById('message');
const openWebLink = document.getElementById('openWeb');

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await checkServiceStatus();
    await getCurrentTab();
});

// 检查服务状态
async function checkServiceStatus() {
    try {
        const res = await fetch(`${API_BASE}/health`, {
            method: 'GET',
            mode: 'no-cors'
        });
        isOnline = true;
        statusDot.className = 'status-dot online';
        statusText.textContent = '服务在线';
        downloadBtn.disabled = false;
        captureBtn.disabled = false;
    } catch (e) {
        isOnline = false;
        statusDot.className = 'status-dot offline';
        statusText.textContent = '服务离线 - 请先启动下载器';
        downloadBtn.disabled = true;
    }
}

// 获取当前标签页信息
async function getCurrentTab() {
    try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tabs.length > 0) {
            currentUrl = tabs[0].url;
            pageUrl.textContent = truncateUrl(currentUrl);
            
            // 尝试获取视频标题
            try {
                const results = await chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    function: getPageTitle
                });
                
                if (results && results[0] && results[0].result) {
                    const title = results[0].result;
                    if (title && title.length > 5) {
                        videoTitle.textContent = title;
                        videoTitleContainer.style.display = 'block';
                    }
                }
            } catch (e) {
                console.log('Cannot get page title:', e);
            }
        }
    } catch (e) {
        pageUrl.textContent = '无法获取页面信息';
    }
}

// 获取页面标题函数（会在页面上下文中执行）
function getPageTitle() {
    // 尝试获取B站视频标题
    const bilibiliTitle = document.querySelector('.video-info-title, h1.title, .videoTitle');
    if (bilibiliTitle) {
        return bilibiliTitle.textContent.trim();
    }
    
    // 尝试获取页面标题
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
        return ogTitle.getAttribute('content');
    }
    
    return document.title;
}

// 下载按钮点击事件
downloadBtn.addEventListener('click', async () => {
    if (!currentUrl || !isOnline) return;
    
    // 显示加载状态
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner spinner"></i> 发送中...';
    hideMessage();
    
    try {
        const res = await fetch(`${API_BASE}/api/add_task`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: currentUrl,
                source: 'extension'
            })
        });
        
        const data = await res.json();
        
        if (data.status === 'ok') {
            showMessage('success', `✅ 已添加到下载队列！\n任务ID: ${data.task_id}`);
        } else {
            showMessage('error', '❌ 添加任务失败');
        }
    } catch (e) {
        showMessage('error', '❌ 网络错误: ' + e.message);
    }
    
    // 恢复按钮状态
    downloadBtn.disabled = false;
    downloadBtn.innerHTML = '<i class="fas fa-download"></i> 发送到下载器';
});

// 自动从浏览器获取Cookie
captureBtn.addEventListener('click', async () => {
    captureBtn.disabled = true;
    captureBtn.textContent = '获取中...';
    hideMessage();

    try {
        const targetDomains = ['bilibili.com', 'ntulearn.ntu.edu.sg', 'ntu.edu.sg', 'ntu.edu.tw'];
        let allCookies = [];
        for (const domain of targetDomains) {
            const cookies = await chrome.cookies.getAll({ domain });
            allCookies = allCookies.concat(cookies);
        }

        // 去重（同 domain+name 保留最新）
        const seen = new Set();
        const unique = allCookies.filter(c => {
            const key = `${c.domain}|${c.name}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        if (unique.length === 0) {
            showMessage('error', '未找到Cookie，请确保已在浏览器中登录B站或NTU');
        } else {
            const res = await fetch(`${API_BASE}/api/cookies/capture`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookies: unique })
            });
            const data = await res.json();
            if (data.status === 'ok') {
                showMessage('success', `✅ ${data.message}`);
            } else {
                showMessage('error', '保存失败');
            }
        }
    } catch (e) {
        showMessage('error', '获取Cookie出错: ' + e.message);
    }

    captureBtn.textContent = '🍪 自动获取浏览器Cookie';
    captureBtn.disabled = false;
});

// 打开Web界面
openWebLink.addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: API_BASE });
});

// 工具函数
function truncateUrl(url) {
    if (url.length > 40) {
        return url.substring(0, 40) + '...';
    }
    return url;
}

function showMessage(type, text) {
    messageEl.className = `message ${type}`;
    messageEl.textContent = text;
    messageEl.style.display = 'block';
}

function hideMessage() {
    messageEl.style.display = 'none';
}

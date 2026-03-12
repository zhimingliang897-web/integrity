// content.js - 页面内容脚本
// 在每个页面注入，检测视频并添加下载按钮

(function() {
    // 防止重复注入
    if (window.__21VideoDownloaderInjected) return;
    window.__21VideoDownloaderInjected = true;

    const API_BASE = 'http://127.0.0.1:8000';
    
    // 创建下载按钮
    function createDownloadButton() {
        const btn = document.createElement('div');
        btn.id = 'video-download-btn';
        btn.innerHTML = `
            <style>
                #video-download-btn {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 999999;
                    cursor: pointer;
                }
                #video-download-btn .btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 12px 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 25px;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                    transition: all 0.3s ease;
                }
                #video-download-btn .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
                }
                #video-download-btn .icon {
                    width: 20px;
                    height: 20px;
                }
                #video-download-btn .tooltip {
                    position: absolute;
                    bottom: 100%;
                    right: 0;
                    margin-bottom: 8px;
                    padding: 8px 12px;
                    background: rgba(0,0,0,0.8);
                    color: white;
                    border-radius: 8px;
                    font-size: 12px;
                    white-space: nowrap;
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                }
                #video-download-btn:hover .tooltip {
                    opacity: 1;
                    visibility: visible;
                }
            </style>
            <div class="btn">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>21下载</span>
            </div>
            <div class="tooltip">发送到下载器</div>
        `;
        
        btn.addEventListener('click', async () => {
            const url = getVideoUrl();

            if (!url) {
                showNotification('⚠️ 请先进入视频播放页面再点击下载');
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/api/add_task`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        url: url,
                        source: 'content_button'
                    })
                });

                const data = await res.json();

                if (data.status === 'ok') {
                    showNotification('✅ 已添加到下载队列！');
                } else {
                    showNotification('❌ 添加失败: ' + (data.message || '未知错误'));
                }
            } catch (e) {
                showNotification('❌ 网络错误，请确保下载器已启动');
            }
        });
        
        return btn;
    }
    
    // 显示通知
    function showNotification(text) {
        const notification = document.createElement('div');
        notification.innerHTML = `
            <style>
                #video-download-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999999;
                    padding: 16px 24px;
                    background: ${text.includes('✅') ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)'};
                    color: white;
                    border-radius: 12px;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 14px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    animation: slideIn 0.3s ease;
                }
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            </style>
            <div>${text}</div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // 获取最合适的视频URL
    function getVideoUrl() {
        const hostname = window.location.hostname;
        const currentUrl = window.location.href;

        // NTU页面：尝试从iframe找真实视频地址
        if (hostname.includes('ntu.edu')) {
            const panoptoIframe = document.querySelector('iframe[src*="panopto.com"]');
            if (panoptoIframe) return panoptoIframe.src;

            const kalturaIframe = document.querySelector('iframe[src*="kaltura.com"]');
            if (kalturaIframe) return kalturaIframe.src;

            const mediaIframe = document.querySelector('iframe[src*="/media/"], iframe[src*="mediasite"], iframe[src*="lecture"]');
            if (mediaIframe) return mediaIframe.src;

            // LTI wrapper URL 无法下载，提示用户
            if (currentUrl.includes('launchFrame') || currentUrl.includes('/lti/')) {
                return null;
            }
        }

        return currentUrl;
    }

    // 检测是否应该显示按钮
    function shouldShowButton() {
        const hostname = window.location.hostname;
        
        // B站
        if (hostname.includes('bilibili.com')) return true;
        
        // NTU相关
        if (hostname.includes('ntu.edu') || hostname.includes('learn.ntu')) return true;
        
        // 其他视频网站可以在这里添加
        return false;
    }
    
    // 初始化
    function init() {
        if (shouldShowButton()) {
            const btn = createDownloadButton();
            document.body.appendChild(btn);
        }
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

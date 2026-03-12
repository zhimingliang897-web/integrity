// 演示页面通用脚本
// API 基础地址（使用 IP:端口，避免域名备案问题）
const API_BASE = 'http://8.138.164.133:5000';

// 通用工具函数
const DemoUtils = {
    // 检查登录状态
    checkAuth() {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        return { token, username, isLoggedIn: !!token };
    },

    // 显示加载状态
    showLoading(element, text = '处理中...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.disabled = true;
            element.dataset.originalText = element.textContent;
            element.textContent = text;
        }
    },

    // 隐藏加载状态
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element && element.dataset.originalText) {
            element.disabled = false;
            element.textContent = element.dataset.originalText;
        }
    },

    // 显示消息提示
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    },

    // 文件上传辅助
    async uploadFile(file, endpoint, additionalData = {}) {
        const { token } = this.checkAuth();
        if (!token) {
            this.showMessage('请先登录', 'error');
            return null;
        }

        const formData = new FormData();
        formData.append('file', file);
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        try {
            const response = await fetch(API_BASE + endpoint, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Upload error:', error);
            this.showMessage('上传失败: ' + error.message, 'error');
            return null;
        }
    },

    // 下载文件
    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    // 验证文件类型
    validateFileType(file, allowedTypes) {
        const fileType = file.type;
        const fileName = file.name.toLowerCase();
        
        return allowedTypes.some(type => {
            if (type.startsWith('.')) {
                return fileName.endsWith(type);
            }
            return fileType.match(type);
        });
    }
};

// 添加动画样式
if (!document.querySelector('#demo-animations')) {
    const style = document.createElement('style');
    style.id = 'demo-animations';
    style.textContent = `
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
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        .message {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
    `;
    document.head.appendChild(style);
}

/**
 * 认证功能模块
 * 处理登录、注册、Token 管理
 * 
 * 重要设计：
 * - GitHub Pages (静态托管): 只做展示，登录跳转到服务器
 * - 云服务器: 真实登录和 API 调用
 */

const SERVER_URL = 'http://8.138.164.133:5000';
const IS_GITHUB_PAGES = window.location.hostname.includes('github.io');
const API_BASE = IS_GITHUB_PAGES ? SERVER_URL : window.location.origin;
let isRegisterMode = false;

function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}

function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const btn = document.getElementById('auth-btn');
    const loginPrompt = document.getElementById('login-prompt');
    const onlineContent = document.getElementById('online-tools-content');
    
    if (token && username) {
        if (btn) {
            btn.textContent = username;
            btn.classList.add('logged-in');
            btn.onclick = () => { if(confirm('确定退出登录？')) logout(); };
        }
        if (loginPrompt) loginPrompt.style.display = 'none';
        if (onlineContent) onlineContent.style.display = 'block';
    } else {
        if (btn) {
            btn.textContent = '登录';
            btn.classList.remove('logged-in');
            btn.onclick = showAuthModal;
        }
        if (loginPrompt) loginPrompt.style.display = 'block';
        if (onlineContent) onlineContent.style.display = 'none';
    }
}

function showAuthModal() {
    const modal = document.getElementById('auth-modal');
    const errorEl = document.getElementById('auth-error');
    if (modal) modal.style.display = 'flex';
    if (errorEl) errorEl.style.display = 'none';
}

function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    const usernameEl = document.getElementById('auth-username');
    const passwordEl = document.getElementById('auth-password');
    const inviteEl = document.getElementById('auth-invite');
    const errorEl = document.getElementById('auth-error');
    
    if (modal) modal.style.display = 'none';
    if (usernameEl) usernameEl.value = '';
    if (passwordEl) passwordEl.value = '';
    if (inviteEl) inviteEl.value = '';
    if (errorEl) errorEl.style.display = 'none';
}

function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    
    const titleEl = document.getElementById('auth-title');
    const submitEl = document.getElementById('auth-submit');
    const inviteWrapEl = document.getElementById('invite-code-wrap');
    const switchTextEl = document.getElementById('switch-text');
    const switchLinkEl = document.getElementById('switch-link');
    const errorEl = document.getElementById('auth-error');
    
    if (titleEl) titleEl.textContent = isRegisterMode ? '注册' : '登录';
    if (submitEl) submitEl.textContent = isRegisterMode ? '注册' : '登录';
    if (inviteWrapEl) inviteWrapEl.style.display = isRegisterMode ? 'block' : 'none';
    if (switchTextEl) switchTextEl.textContent = isRegisterMode ? '已有账号？' : '没有账号？';
    if (switchLinkEl) switchLinkEl.textContent = isRegisterMode ? '登录' : '注册';
    if (errorEl) errorEl.style.display = 'none';
    return false;
}

async function handleAuth() {
    const usernameEl = document.getElementById('auth-username');
    const passwordEl = document.getElementById('auth-password');
    const inviteEl = document.getElementById('auth-invite');
    const errorEl = document.getElementById('auth-error');
    const submitEl = document.getElementById('auth-submit');
    
    const username = usernameEl ? usernameEl.value.trim() : '';
    const password = passwordEl ? passwordEl.value : '';
    const invite = inviteEl ? inviteEl.value.trim() : '';
    
    if (!username || !password) {
        if (errorEl) {
            errorEl.textContent = '请填写用户名和密码';
            errorEl.style.display = 'block';
        }
        return;
    }
    
    const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
    const body = isRegisterMode 
        ? { username, password, invite_code: invite }
        : { username, password };
    
    if (submitEl) {
        submitEl.disabled = true;
        submitEl.textContent = isRegisterMode ? '注册中...' : '登录中...';
    }
    
    try {
        const res = await fetch(API_BASE + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        
        if (data.error) {
            if (errorEl) {
                errorEl.textContent = data.error;
                errorEl.style.display = 'block';
            }
            showToast(data.error, 'error');
        } else {
            localStorage.setItem('token', data.token);
            localStorage.setItem('username', data.username);
            hideAuthModal();
            checkAuth();
            showToast(isRegisterMode ? '注册成功！' : '登录成功！', 'success');
        }
    } catch (e) {
        if (errorEl) {
            errorEl.textContent = '网络错误: ' + e.message;
            errorEl.style.display = 'block';
        }
        showToast('网络错误: ' + e.message, 'error');
        console.error('Auth error:', e);
    } finally {
        if (submitEl) {
            submitEl.disabled = false;
            submitEl.textContent = isRegisterMode ? '注册' : '登录';
        }
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    checkAuth();
    showToast('已退出登录', 'info');
}

document.addEventListener('DOMContentLoaded', checkAuth);
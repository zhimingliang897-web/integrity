/**
 * 认证功能模块
 * 处理登录、注册、Token 管理
 */

const API_BASE = 'https://api.liangyiren.top';
let isRegisterMode = false;

// 检查登录状态
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    const btn = document.getElementById('auth-btn');
    const loginPrompt = document.getElementById('login-prompt');
    const onlineContent = document.getElementById('online-tools-content');
    
    if (token && username) {
        btn.textContent = username;
        btn.classList.add('logged-in');
        btn.onclick = () => { if(confirm('确定退出登录？')) logout(); };
        if (loginPrompt) loginPrompt.style.display = 'none';
        if (onlineContent) onlineContent.style.display = 'block';
    } else {
        btn.textContent = '登录';
        btn.classList.remove('logged-in');
        btn.onclick = showAuthModal;
        if (loginPrompt) loginPrompt.style.display = 'block';
        if (onlineContent) onlineContent.style.display = 'none';
    }
}

// 显示/隐藏登录弹窗
function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('auth-error').style.display = 'none';
}

function hideAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('auth-username').value = '';
    document.getElementById('auth-password').value = '';
    document.getElementById('auth-invite').value = '';
}

// 切换登录/注册模式
function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    document.getElementById('auth-title').textContent = isRegisterMode ? '注册' : '登录';
    document.getElementById('auth-submit').textContent = isRegisterMode ? '注册' : '登录';
    document.getElementById('invite-code-wrap').style.display = isRegisterMode ? 'block' : 'none';
    document.getElementById('switch-text').textContent = isRegisterMode ? '已有账号？' : '没有账号？';
    document.getElementById('switch-link').textContent = isRegisterMode ? '登录' : '注册';
    document.getElementById('auth-error').style.display = 'none';
    return false;
}

// 处理登录/注册
async function handleAuth() {
    const username = document.getElementById('auth-username').value.trim();
    const password = document.getElementById('auth-password').value;
    const invite = document.getElementById('auth-invite').value.trim();
    const errorEl = document.getElementById('auth-error');
    
    if (!username || !password) {
        errorEl.textContent = '请填写用户名和密码';
        errorEl.style.display = 'block';
        return;
    }
    
    const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
    const body = isRegisterMode 
        ? { username, password, invite_code: invite }
        : { username, password };
    
    try {
        const res = await fetch(API_BASE + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        
        if (data.error) {
            errorEl.textContent = data.error;
            errorEl.style.display = 'block';
        } else {
            localStorage.setItem('token', data.token);
            localStorage.setItem('username', data.username);
            hideAuthModal();
            checkAuth();
        }
    } catch (e) {
        errorEl.textContent = '网络错误: ' + e.message;
        errorEl.style.display = 'block';
        console.error('Auth error:', e);
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    checkAuth();
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkAuth);

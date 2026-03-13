let currentPath = '';
let files = [];
let selectedFiles = [];
let pendingUploadFiles = [];
let isAuthenticated = false;
let mounts = [];
let currentMount = null;
let isReadonlyPath = false;

async function checkAuth() {
    try {
        const res = await fetch('/api/auth/check');
        if (res.ok) {
            isAuthenticated = true;
            const data = await res.json();
            showUserInfo(data.user);
            return true;
        } else {
            isAuthenticated = false;
            window.location.href = '/login';
            return false;
        }
    } catch (e) {
        isAuthenticated = false;
        window.location.href = '/login';
        return false;
    }
}

function showUserInfo(user) {
    const headerRight = document.querySelector('.header-right');
    if (headerRight) {
        const userInfo = document.createElement('span');
        userInfo.style.cssText = 'color:var(--text-dim);font-size:13px;margin-right:10px;';
        userInfo.innerHTML = `👤 已登录`;
        headerRight.insertBefore(userInfo, headerRight.firstChild);
    }
}

async function apiCall(url, options = {}) {
    if (!options.headers) {
        options.headers = {};
    }
    options.credentials = 'include';
    
    const res = await fetch(url, options);
    
    if (res.status === 401) {
        isAuthenticated = false;
        window.location.href = '/login';
        return null;
    }
    
    return res;
}

async function loadFiles(path = '') {
    if (!isAuthenticated) return;
    
    currentPath = path;
    selectedFiles = [];
    updateSelectionBar();
    
    try {
        const res = await apiCall(`/api/files?path=${encodeURIComponent(path)}`);
        if (!res) return;
        
        const data = await res.json();
        files = data.files || [];
        renderBreadcrumb(data.breadcrumb || []);
        renderFiles(files);
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

function renderBreadcrumb(items) {
    const el = document.getElementById('breadcrumb');
    el.innerHTML = items.map((item, i) => {
        const isLast = i === items.length - 1;
        return `<span class="breadcrumb-item ${isLast ? 'current' : ''}" onclick="navigateTo('${item.path}')">${item.name}</span>${!isLast ? '<span>›</span>' : ''}`;
    }).join('');
}

function renderFiles(files) {
    const el = document.getElementById('file-list');
    
    if (files.length === 0) {
        el.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-dim);">空文件夹</div>';
        return;
    }
    
    el.innerHTML = files.map(f => `
        <div class="file-item ${selectedFiles.includes(f.path) ? 'selected' : ''}" data-path="${f.path}">
            <label class="checkbox"><input type="checkbox" ${selectedFiles.includes(f.path) ? 'checked' : ''} onchange="toggleSelect('${f.path}')"></label>
            <div class="file-name" onclick="${f.is_dir ? `navigateTo('${f.path}')` : `previewFile('${f.path}')`}">
                <span class="file-icon">${getFileIcon(f.ext, f.is_dir)}</span>
                ${escapeHtml(f.name)}
                ${f.mount_name ? `<span class="mount-tag">${escapeHtml(f.mount_name)}</span>` : ''}
            </div>
            <div class="file-size">${f.is_dir ? '-' : formatSize(f.size)}</div>
            <div class="file-date">${formatDate(f.modified_at)}</div>
            <div class="file-actions">
                ${!f.is_dir ? `<button class="btn-sm" onclick="downloadFile('${f.path}')">📥</button>` : ''}
                ${!isReadonlyPath ? `<button class="btn-sm btn-danger" onclick="deleteFile('${f.path}')">🗑️</button>` : ''}
            </div>
        </div>
    `).join('');
}

function getFileIcon(ext, isDir) {
    if (isDir) return '📁';
    const icons = {
        '.pdf': '📕', '.doc': '📘', '.docx': '📘', '.xls': '📗', '.xlsx': '📗',
        '.ppt': '📙', '.pptx': '📙', '.txt': '📄', '.md': '📝',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.webp': '🖼️',
        '.mp4': '🎬', '.mov': '🎬', '.avi': '🎬', '.mkv': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.py': '🐍', '.js': '⚡', '.html': '🌐', '.css': '🎨', '.json': '🔧'
    };
    return icons[ext] || '📄';
}

function formatSize(bytes) {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

function formatDate(date) {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString().slice(0, 5);
}

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function navigateTo(path) {
    currentMount = null;
    isReadonlyPath = false;
    
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    
    if (!path) {
        document.getElementById('nav-root')?.classList.add('active');
    }
    
    updateToolbarForReadonly();
    loadFiles(path);
}

function toggleSelect(path) {
    const idx = selectedFiles.indexOf(path);
    if (idx === -1) {
        selectedFiles.push(path);
    } else {
        selectedFiles.splice(idx, 1);
    }
    renderFiles(files);
    updateSelectionBar();
}

function toggleSelectAll() {
    const allPaths = files.map(f => f.path);
    if (selectedFiles.length === allPaths.length) {
        selectedFiles = [];
    } else {
        selectedFiles = [...allPaths];
    }
    renderFiles(files);
    updateSelectionBar();
}

function updateSelectionBar() {
    const bar = document.getElementById('selection-bar');
    const count = document.getElementById('selected-count');
    count.textContent = selectedFiles.length;
    bar.classList.toggle('visible', selectedFiles.length > 0);
}

function clearSelection() {
    selectedFiles = [];
    renderFiles(files);
    updateSelectionBar();
}

function showModal(id) { document.getElementById(id).classList.add('visible'); }
function closeModal(id) { document.getElementById(id).classList.remove('visible'); }

function showUploadModal() {
    if (!isAuthenticated) {
        showToast('请先登录', 'error');
        return;
    }
    if (isReadonlyPath) {
        showToast('挂载目录为只读，不允许上传', 'error');
        return;
    }
    pendingUploadFiles = [];
    document.getElementById('upload-list').innerHTML = '';
    showModal('upload-modal');
}

document.getElementById('upload-area')?.addEventListener('click', () => {
    document.getElementById('file-input').click();
});

document.getElementById('file-input')?.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

document.getElementById('upload-area')?.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
});

document.getElementById('upload-area')?.addEventListener('dragleave', (e) => {
    e.currentTarget.classList.remove('dragover');
});

document.getElementById('upload-area')?.addEventListener('drop', (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

function handleFiles(fileList) {
    for (const file of fileList) {
        pendingUploadFiles.push(file);
        const item = document.createElement('div');
        item.className = 'upload-item';
        item.innerHTML = `<span class="name">${escapeHtml(file.name)}</span><span class="size">${formatSize(file.size)}</span>`;
        document.getElementById('upload-list').appendChild(item);
    }
}

async function doUploadFiles() {
    if (!isAuthenticated) {
        showToast('请先登录', 'error');
        return;
    }

    if (pendingUploadFiles.length === 0) {
        showToast('请选择文件', 'error');
        return;
    }

    const formData = new FormData();
    pendingUploadFiles.forEach(file => formData.append('files', file));
    formData.append('target_path', currentPath);
    
    try {
        const res = await apiCall('/api/files/upload', { method: 'POST', body: formData });
        if (!res) return;
        
        const data = await res.json();
        
        if (data.success_count > 0) {
            showToast(`上传成功 ${data.success_count} 个文件`, 'success');
            closeModal('upload-modal');
            loadFiles(currentPath);
        } else {
            showToast('上传失败', 'error');
        }
    } catch (e) {
        showToast('上传失败', 'error');
    }
}

function showNewFolderModal() {
    if (!isAuthenticated) {
        showToast('请先登录', 'error');
        return;
    }
    if (isReadonlyPath) {
        showToast('挂载目录为只读，不允许创建文件夹', 'error');
        return;
    }
    showModal('new-folder-modal');
}

async function createFolder() {
    const name = document.getElementById('folder-name').value.trim();
    if (!name) {
        showToast('请输入文件夹名称', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('parent_path', currentPath);
        
        const res = await apiCall('/api/files/folder', { method: 'POST', body: formData });
        if (!res) return;
        
        const data = await res.json();
        
        if (data.success) {
            showToast('创建成功', 'success');
            closeModal('new-folder-modal');
            loadFiles(currentPath);
            document.getElementById('folder-name').value = '';
        }
    } catch (e) {
        showToast('创建失败', 'error');
    }
}

async function downloadFile(path) {
    window.location.href = `/api/files/download?paths=${encodeURIComponent(path)}`;
}

async function downloadSelected() {
    if (selectedFiles.length === 0) return;
    window.location.href = `/api/files/download?paths=${encodeURIComponent(selectedFiles.join(','))}`;
}

async function deleteFile(path) {
    if (!confirm('确定要删除吗？文件将移入回收站')) return;

    try {
        const res = await apiCall(`/api/files?paths=${encodeURIComponent(path)}`, { method: 'DELETE' });
        if (!res) return;
        
        const data = await res.json();
        
        if (data.success_count > 0) {
            showToast('已移入回收站', 'success');
            loadFiles(currentPath);
        }
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

async function deleteSelected() {
    if (selectedFiles.length === 0) return;
    if (!confirm(`确定要删除选中的 ${selectedFiles.length} 个文件吗？`)) return;

    try {
        const res = await apiCall(`/api/files?paths=${encodeURIComponent(selectedFiles.join(','))}`, { method: 'DELETE' });
        if (!res) return;
        
        const data = await res.json();
        
        if (data.success_count > 0) {
            showToast(`已删除 ${data.success_count} 个文件`, 'success');
            loadFiles(currentPath);
        }
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

async function previewFile(path) {
    try {
        const res = await apiCall(`/api/preview?path=${encodeURIComponent(path)}`);
        if (!res) return;
        
        const data = await res.json();
        
        const title = document.getElementById('preview-title');
        const body = document.getElementById('preview-body');
        
        title.textContent = data.filename || '预览';
        
        if (data.type === 'image') {
            body.innerHTML = `<img src="${data.url}" alt="${data.filename}">`;
        } else if (data.type === 'video') {
            body.innerHTML = `<video src="${data.url}" controls autoplay></video>`;
        } else if (data.type === 'audio') {
            body.innerHTML = `<audio src="${data.url}" controls autoplay></audio>`;
        } else if (data.type === 'text') {
            body.innerHTML = `<pre>${escapeHtml(data.content)}</pre>`;
        } else if (data.type === 'pdf') {
            body.innerHTML = `<embed src="${data.url}" type="application/pdf" width="100%" height="500px">`;
        } else {
            body.innerHTML = `<p style="color:var(--text-dim);">不支持预览此类型文件</p>`;
        }
        
        showModal('preview-modal');
    } catch (e) {
        showToast('预览失败', 'error');
    }
}

async function searchFiles() {
    const keyword = document.getElementById('search-input').value.trim();
    if (!keyword) return;
    
    try {
        const res = await apiCall(`/api/search?keyword=${encodeURIComponent(keyword)}`);
        if (!res) return;
        
        const data = await res.json();
        
        files = data.results || [];
        renderBreadcrumb([{ name: `搜索: ${keyword}`, path: '' }]);
        renderFiles(files);
    } catch (e) {
        showToast('搜索失败', 'error');
    }
}

async function searchByType(type) {
    try {
        const res = await apiCall(`/api/search/type/${type}`);
        if (!res) return;
        
        const data = await res.json();
        
        files = data.results || [];
        const typeNames = { image: '图片', video: '视频', document: '文档', audio: '音频' };
        renderBreadcrumb([{ name: typeNames[type] || type, path: '' }]);
        renderFiles(files);
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

function showStarred() {
    showToast('收藏功能开发中', '');
}

async function showTrash() {
    try {
        const res = await apiCall('/api/trash');
        if (!res) return;
        
        const data = await res.json();
        
        files = (data.items || []).map(item => ({
            name: item.name,
            path: item.trash_path,
            is_dir: item.is_dir,
            size: item.size,
            ext: null,
            modified_at: item.deleted_at
        }));
        
        renderBreadcrumb([{ name: '回收站', path: '' }]);
        renderFiles(files);
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

function toggleAgent() {
    document.getElementById('agent-panel').classList.toggle('visible');
}

async function sendAgentMsg(text) {
    if (!isAuthenticated) {
        showToast('请先登录', 'error');
        return;
    }
    
    const input = document.getElementById('agent-input');
    const msg = text || input.value.trim();
    if (!msg) return;
    
    input.value = '';
    
    const messagesEl = document.getElementById('agent-messages');
    messagesEl.innerHTML += `<div class="agent-msg user">${escapeHtml(msg)}</div>`;
    
    try {
        const res = await apiCall('/api/agent/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, context: { current_path: currentPath } })
        });
        
        if (!res) return;
        
        const data = await res.json();
        messagesEl.innerHTML += `<div class="agent-msg">${escapeHtml(data.reply)}</div>`;
        messagesEl.scrollTop = messagesEl.scrollHeight;
        
        if (data.files && data.files.length > 0) {
            files = data.files;
            renderFiles(files);
        }
    } catch (e) {
        messagesEl.innerHTML += `<div class="agent-msg">请求失败，请重试</div>`;
    }
}

function showMoveModal() {
    if (selectedFiles.length === 0) return;
    showModal('move-modal');
}

async function moveFiles() {
    showToast('移动功能开发中', '');
    closeModal('move-modal');
}

function showToast(msg, type = '') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast visible ' + type;
    setTimeout(() => toast.classList.remove('visible'), 3000);
}

function logout() {
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }).then(() => {
        window.location.href = '/login';
    });
}

async function loadMounts() {
    try {
        const res = await apiCall('/api/mounts');
        if (!res) return;
        
        const data = await res.json();
        mounts = data.mounts || [];
        renderMounts();
    } catch (e) {
        console.error('加载挂载点失败', e);
    }
}

function renderMounts() {
    const el = document.getElementById('mounts-list');
    if (!el) return;
    
    if (mounts.length === 0) {
        el.innerHTML = '<div style="padding:8px 16px;color:var(--text-dim);font-size:12px;">暂无挂载目录</div>';
        return;
    }
    
    el.innerHTML = mounts.map(m => `
        <div class="nav-item mount-item ${currentMount && currentMount.path === m.path ? 'active' : ''}" 
             onclick="navigateToMount('${m.path}', '${escapeHtml(m.name)}')"
             title="${m.path}${m.readonly ? ' (只读)' : ''}">
            <span class="icon">${m.icon || '📁'}</span> 
            ${escapeHtml(m.name)}
            ${m.readonly ? '<span class="readonly-badge">只读</span>' : ''}
        </div>
    `).join('');
}

async function navigateToMount(path, name) {
    currentMount = { path, name };
    isReadonlyPath = true;
    
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`.mount-item[onclick*="${path}"]`)?.classList.add('active');
    
    await loadFiles(path);
    updateToolbarForReadonly();
}

function updateToolbarForReadonly() {
    const uploadBtn = document.querySelector('button[onclick="showUploadModal()"]');
    const newFolderBtn = document.querySelector('button[onclick="showNewFolderModal()"]');
    
    if (uploadBtn) {
        uploadBtn.disabled = isReadonlyPath;
        uploadBtn.style.opacity = isReadonlyPath ? '0.5' : '1';
    }
    if (newFolderBtn) {
        newFolderBtn.disabled = isReadonlyPath;
        newFolderBtn.style.opacity = isReadonlyPath ? '0.5' : '1';
    }
}

document.getElementById('search-btn')?.addEventListener('click', searchFiles);
document.getElementById('search-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchFiles();
});

checkAuth().then(auth => {
    if (auth) {
        loadMounts();
        loadFiles();
    }
});
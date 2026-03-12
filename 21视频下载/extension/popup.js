// popup.js v3.0

let tabId = null;
let videos = [];

const listEl      = document.getElementById('list');
const emptyState  = document.getElementById('emptyState');
const countLabel  = document.getElementById('countLabel');
const refreshBtn  = document.getElementById('refreshBtn');
const toast       = document.getElementById('toast');
const btnCopyAll  = document.getElementById('btnCopyAll');
const btnOpenDir  = document.getElementById('btnOpenDir');

// ── 初始化 ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;
    tabId = tab.id;
    await fetchAndRender();
});

// ── 获取视频列表并渲染 ─────────────────────────────────────
async function fetchAndRender() {
    refreshBtn.classList.add('spinning');
    countLabel.textContent = '检测中…';

    try {
        const res = await chrome.runtime.sendMessage({ type: 'GET_VIDEOS', tabId });
        videos = res?.videos || [];
        render(videos);
    } catch (e) {
        showToast('获取失败: ' + e.message);
    }

    refreshBtn.classList.remove('spinning');
}

refreshBtn.addEventListener('click', fetchAndRender);

// ── 渲染视频卡片 ───────────────────────────────────────────
function render(list) {
    // 清除旧卡片（保留 emptyState）
    [...listEl.children].forEach(el => {
        if (el.id !== 'emptyState') el.remove();
    });

    if (!list || list.length === 0) {
        emptyState.style.display = 'flex';
        countLabel.textContent = '未找到视频';
        return;
    }

    emptyState.style.display = 'none';
    countLabel.textContent = `共 ${list.length} 个视频`;

    list.forEach((v, idx) => {
        const card = makeCard(v, idx);
        listEl.appendChild(card);
    });
}

function makeCard(v, idx) {
    const ext = v.ext || 'other';
    const isDirectDl = ['mp4', 'webm', 'flv', 'm4v', 'mkv', 'mov'].includes(ext);
    const stripeClass = ['m3u8', 'mp4', 'webm', 'flv'].includes(ext) ? ext : 'other';
    const tagClass    = ['m3u8', 'mp4', 'webm', 'flv', 'ts'].includes(ext) ? ext : 'other';

    const sizeStr = v.size ? formatSize(v.size) : '';
    const displayUrl = shortenUrl(v.url);

    const card = document.createElement('div');
    card.className = 'vcard';
    card.innerHTML = `
        <div class="vcard-stripe stripe-${stripeClass}"></div>
        <div class="vcard-body">
            <div class="vcard-meta">
                <span class="tag tag-${tagClass}">${ext.toUpperCase()}</span>
                ${sizeStr ? `<span class="vcard-size">${sizeStr}</span>` : ''}
                ${v.source ? `<span class="vcard-source">${v.source}</span>` : ''}
            </div>
            <div class="vcard-url" title="${v.url}">${displayUrl}</div>
        </div>
        <div class="vcard-actions">
            <button class="vbtn ${isDirectDl ? 'dl-direct' : 'dl-cmd'}" data-idx="${idx}" data-action="primary">
                ${isDirectDl ? '⬇️ 下载' : '📋 复制'}
            </button>
            <button class="vbtn dl-cmd" data-idx="${idx}" data-action="copy-cmd">
                📝 命令
            </button>
        </div>
    `;

    // 点击事件
    card.querySelectorAll('.vbtn').forEach(btn => {
        btn.addEventListener('click', () => handleAction(btn, v));
    });

    return card;
}

// ── 按钮动作 ───────────────────────────────────────────────
async function handleAction(btn, v) {
    const action = btn.dataset.action;
    const ext = v.ext || '';

    if (action === 'primary') {
        // 直接链接 → 浏览器原生下载
        if (['mp4', 'webm', 'flv', 'm4v', 'mkv', 'mov'].includes(ext)) {
            btn.textContent = '⏳ 下载中';
            const res = await chrome.runtime.sendMessage({
                type: 'DIRECT_DOWNLOAD',
                url: v.url,
            });
            if (res?.ok) {
                btn.textContent = '✅ 已开始';
                showToast('✅ 下载已开始！保存到默认下载文件夹');
            } else {
                // 下载API失败，降级复制命令
                copyCmd(v.url, ext);
                btn.textContent = '📋 已复制';
                showToast('⚠️ 直接下载失败，已复制 yt-dlp 命令');
            }
            setTimeout(() => { btn.textContent = ext === 'mp4' ? '⬇️ 下载' : '📋 复制'; }, 2500);
        } else {
            // m3u8 等流媒体 → 复制 yt-dlp 命令
            copyCmd(v.url, ext);
            btn.textContent = '✅ 已复制';
            btn.classList.add('copied');
            showToast('📋 yt-dlp 命令已复制！粘贴到终端运行');
            setTimeout(() => {
                btn.textContent = '📋 复制';
                btn.classList.remove('copied');
            }, 2000);
        }
    }

    if (action === 'copy-cmd') {
        copyCmd(v.url, ext);
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        showToast('📋 命令已复制！');
        setTimeout(() => {
            btn.textContent = '📝 命令';
            btn.classList.remove('copied');
        }, 2000);
    }
}

function copyCmd(url, ext) {
    // 针对不同格式生成最合适的命令
    let cmd;
    if (ext === 'm3u8' || ext === 'ts') {
        cmd = `yt-dlp -f "bestvideo+bestaudio/best" --merge-output-format mp4 "${url}"`;
    } else if (['mp4', 'webm', 'flv'].includes(ext)) {
        cmd = `yt-dlp "${url}"`;
    } else {
        cmd = `yt-dlp -f "bestvideo+bestaudio/best" --merge-output-format mp4 "${url}"`;
    }
    navigator.clipboard.writeText(cmd).catch(() => {
        // 备用方案
        const el = document.createElement('textarea');
        el.value = cmd;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        el.remove();
    });
    return cmd;
}

// ── 底部按钮 ───────────────────────────────────────────────
btnCopyAll.addEventListener('click', () => {
    if (videos.length === 0) { showToast('没有视频可复制'); return; }
    const cmds = videos.map(v => copyCmd(v.url, v.ext)).join('\n');
    navigator.clipboard.writeText(cmds);
    showToast(`📋 已复制 ${videos.length} 条命令`);
});

btnOpenDir.addEventListener('click', () => {
    // 打开 chrome://downloads 页面
    chrome.tabs.create({ url: 'chrome://downloads/' });
});

// ── 工具函数 ───────────────────────────────────────────────
let toastTimer = null;
function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

function shortenUrl(url) {
    try {
        const u = new URL(url);
        // 显示域名 + 路径末尾
        const path = u.pathname;
        const short = u.hostname + (path.length > 30 ? '…' + path.slice(-24) : path);
        return short.length > 52 ? short.substring(0, 52) + '…' : short;
    } catch {
        return url.substring(0, 52) + (url.length > 52 ? '…' : '');
    }
}

function formatSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB';
}

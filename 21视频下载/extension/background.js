// background.js v3.0
// 核心功能：拦截所有视频请求，实时更新角标计数

// tabId -> [ {url, ext, size, time} ]
const captured = new Map();

// ── 视频识别规则 ──────────────────────────────────────────
const VIDEO_EXT_RE = /\.(m3u8|mp4|webm|flv|ts|m4v|mkv|avi|mov)(\?|#|$)/i;

const VIDEO_CONTENT_RE = [
    /\/manifest\b/i,
    /\/playlist\b/i,
    /\/media\/.*\.(m3u8|mp4)/i,
    /kaltura.*\/p\//i,
    /panopto.*chunk/i,
    /bilibili.*v=\d+/i,
    /\/chunk.*\.ts/i,
    /video\/mp4/i,
];

// 忽略缩略图、广告追踪等
const SKIP_RE = [
    /thumbnail/i, /poster/i, /preview.*\d+x\d+/i,
    /analytics/i, /tracking/i, /beacon/i, /pixel/i,
    /\.jpg/i, /\.png/i, /\.gif/i, /\.webp/i,
    /favicon/i,
];

function isVideoUrl(url) {
    if (SKIP_RE.some(r => r.test(url))) return false;
    if (VIDEO_EXT_RE.test(url)) return true;
    if (VIDEO_CONTENT_RE.some(r => r.test(url))) return true;
    return false;
}

function getExt(url) {
    const m = url.match(VIDEO_EXT_RE);
    return m ? m[1].toLowerCase() : 'stream';
}

// ── 拦截网络请求 ──────────────────────────────────────────
chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
        const { url, tabId, requestId } = details;
        if (tabId < 0 || !isVideoUrl(url)) return;

        if (!captured.has(tabId)) captured.set(tabId, []);
        const list = captured.get(tabId);

        // 去重（相同 URL 不重复添加）
        if (list.find(i => i.url === url)) return;

        const entry = {
            url,
            ext: getExt(url),
            time: Date.now(),
            size: null,     // 后面用 onHeadersReceived 填充
            requestId,
        };

        list.unshift(entry);   // 最新的放最前
        if (list.length > 30) list.pop();

        updateBadge(tabId, list.length);
    },
    { urls: ['<all_urls>'] }
);

// 尝试从响应头获取文件大小
chrome.webRequest.onHeadersReceived.addListener(
    (details) => {
        const { tabId, requestId, responseHeaders } = details;
        if (tabId < 0) return;
        const list = captured.get(tabId);
        if (!list) return;
        const entry = list.find(i => i.requestId === requestId);
        if (!entry) return;
        const cl = responseHeaders.find(h => h.name.toLowerCase() === 'content-length');
        if (cl) entry.size = parseInt(cl.value) || null;
    },
    { urls: ['<all_urls>'] },
    ['responseHeaders']
);

// ── 更新角标 ──────────────────────────────────────────────
function updateBadge(tabId, count) {
    const text = count > 0 ? String(count) : '';
    chrome.action.setBadgeText({ text, tabId });
    chrome.action.setBadgeBackgroundColor({ color: count > 0 ? '#7c3aed' : '#666', tabId });
}

// ── 页面导航时清空当前 tab 的记录 ─────────────────────────
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
    if (changeInfo.status === 'loading') {
        captured.delete(tabId);
        updateBadge(tabId, 0);
    }
});

chrome.tabs.onRemoved.addListener((tabId) => {
    captured.delete(tabId);
});

// ── 消息处理 ─────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

    // popup 请求视频列表
    if (msg.type === 'GET_VIDEOS') {
        const list = captured.get(msg.tabId) || [];
        sendResponse({ videos: list });
        return true;
    }

    // content.js 上报视频（来自页面内 DOM/XHR 拦截）
    if (msg.type === 'REPORT_VIDEO') {
        const tabId = sender.tab?.id;
        if (!tabId || tabId < 0) return;
        if (!captured.has(tabId)) captured.set(tabId, []);
        const list = captured.get(tabId);
        const { url, ext, source } = msg;
        if (!list.find(i => i.url === url)) {
            list.unshift({ url, ext: ext || getExt(url), source, time: Date.now(), size: null });
            if (list.length > 30) list.pop();
            updateBadge(tabId, list.length);
        }
        return true;
    }

    // 用 chrome.downloads API 直接下载
    if (msg.type === 'DIRECT_DOWNLOAD') {
        const filename = msg.filename || decodeURIComponent(msg.url.split('/').pop().split('?')[0]) || 'video.mp4';
        chrome.downloads.download({
            url: msg.url,
            filename: filename.replace(/[<>:"/\\|?*]/g, '_'),
            saveAs: false,
        }, (downloadId) => {
            if (chrome.runtime.lastError) {
                sendResponse({ ok: false, error: chrome.runtime.lastError.message });
            } else {
                sendResponse({ ok: true, downloadId });
            }
        });
        return true; // async
    }
});

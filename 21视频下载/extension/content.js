// content.js v3.0
// 页面内视频嗅探：补充 webRequest 无法捕获的场景
// （比如 blob URL、页内 video 标签、JS 动态播放）

(function () {
    if (window.__vdSnifferRunning) return;
    window.__vdSnifferRunning = true;

    // ── 视频判断 ────────────────────────────────────────────
    const VIDEO_RE = [
        /\.m3u8(\?|#|$)/i,
        /\.mp4(\?|#|$)/i,
        /\.webm(\?|#|$)/i,
        /\.flv(\?|#|$)/i,
        /\.ts(\?|#|$)/i,
        /\.m4v(\?|#|$)/i,
    ];
    const SKIP_RE = [/thumbnail/i, /poster/i, /\.jpg/i, /\.png/i, /analytics/i];

    function getExt(url) {
        const m = url.match(/\.(m3u8|mp4|webm|flv|ts|m4v)/i);
        return m ? m[1].toLowerCase() : 'stream';
    }

    function isVideo(url) {
        if (!url || typeof url !== 'string') return false;
        if (url.startsWith('blob:') || url.startsWith('data:')) return false;
        if (SKIP_RE.some(r => r.test(url))) return false;
        return VIDEO_RE.some(r => r.test(url));
    }

    // 上报给 background（去重在 background 做）
    function report(url, source) {
        if (!isVideo(url)) return;
        chrome.runtime.sendMessage({
            type: 'REPORT_VIDEO',
            url,
            ext: getExt(url),
            source,
        }).catch(() => {});
    }

    // ── 拦截 fetch ──────────────────────────────────────────
    const _fetch = window.fetch;
    window.fetch = function (...args) {
        try {
            const url = typeof args[0] === 'string' ? args[0]
                : (args[0]?.url || '');
            report(url, 'fetch');
        } catch {}
        return _fetch.apply(this, args);
    };

    // ── 拦截 XHR ────────────────────────────────────────────
    const _xhrOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        try { report(url, 'xhr'); } catch {}
        return _xhrOpen.call(this, method, url, ...rest);
    };

    // ── 扫描 video/source 标签 ──────────────────────────────
    function scanEl(el) {
        if (!el || !el.querySelectorAll) return;
        el.querySelectorAll('video, source').forEach(v => {
            [v.src, v.currentSrc, v.getAttribute('src')].forEach(u => {
                if (u) report(u, 'dom');
            });
        });
        // 也检查自身
        if (el.tagName === 'VIDEO' || el.tagName === 'SOURCE') {
            [el.src, el.currentSrc].forEach(u => { if (u) report(u, 'dom'); });
        }
    }

    // 初始扫描
    function initialScan() {
        scanEl(document);
        // 特殊：检查 iframe
        document.querySelectorAll('iframe').forEach(iframe => {
            try {
                const src = iframe.src || iframe.getAttribute('src');
                if (src) report(src, 'iframe');
            } catch {}
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialScan);
    } else {
        initialScan();
    }

    // 监听动态加载的节点
    const obs = new MutationObserver(muts => {
        for (const m of muts) {
            m.addedNodes.forEach(n => {
                if (n.nodeType === 1) scanEl(n);
            });
        }
    });

    const startObs = () => {
        if (document.body) {
            obs.observe(document.body, { childList: true, subtree: true });
        }
    };

    if (document.body) { startObs(); }
    else { document.addEventListener('DOMContentLoaded', startObs); }

    // ── 拦截 HTMLMediaElement.src setter（捕获 JS 动态赋值）──
    try {
        const proto = HTMLMediaElement.prototype;
        const desc = Object.getOwnPropertyDescriptor(proto, 'src');
        if (desc && desc.set) {
            Object.defineProperty(proto, 'src', {
                ...desc,
                set(value) {
                    try { report(value, 'mediaSrc'); } catch {}
                    desc.set.call(this, value);
                }
            });
        }
    } catch {}

})();

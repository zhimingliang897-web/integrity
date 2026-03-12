/**
 * PDF 工具功能模块
 * 处理 PDF 相关操作
 */

// Tab 切换
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById('tab-' + tabName).classList.add('active');
}

// 展开/收起工具
function toggleSection(id) {
    const el = document.getElementById(id);
    const arrow = document.getElementById(id + '-arrow');
    const isOpen = el.style.display !== 'none';
    el.style.display = isOpen ? 'none' : 'block';
    if (arrow) arrow.textContent = isOpen ? '▼' : '▲';
}

// PDF Tab 切换
document.addEventListener('DOMContentLoaded', () => {
    const pdfTabs = document.getElementById('pdf-tabs');
    if (pdfTabs) {
        pdfTabs.addEventListener('click', e => {
            const tab = e.target.closest('.pdf-tab');
            if (!tab) return;
            document.querySelectorAll('.pdf-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.pdf-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    }
});

// 获取 PDF 信息
async function getPdfInfo(input, infoId) {
    const file = input.files[0];
    if (!file) return;
    const token = localStorage.getItem('token');
    const fd = new FormData();
    fd.append('pdf', file);
    try {
        const res = await fetch(API_BASE + '/api/tools/pdf/info', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: fd
        });
        const data = await res.json();
        const el = document.getElementById(infoId);
        el.textContent = data.info || data.error;
        el.style.display = 'block';
    } catch (e) { console.error(e); }
}

// 自动填充结束页码
async function autoFillEndPage(input) {
    const file = input.files[0];
    if (!file) return;
    const token = localStorage.getItem('token');
    const fd = new FormData();
    fd.append('pdf', file);
    try {
        const res = await fetch(API_BASE + '/api/tools/pdf/info', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: fd
        });
        const data = await res.json();
        const m = data.info && data.info.match(/总页数：(\d+)/);
        if (m) document.getElementById('p-toimg-end').value = m[1];
    } catch (e) { console.error(e); }
}

// PDF 操作主函数
async function pdfOp(op) {
    const token = localStorage.getItem('token');
    if (!token) { alert('请先登录'); return; }

    const resultId = 'r-' + op;
    const resultEl = document.getElementById(resultId);
    const btn = resultEl.previousElementSibling;

    resultEl.className = 'pdf-result';
    resultEl.innerHTML = '处理中...';
    resultEl.style.display = 'block';
    btn.disabled = true;

    const fd = new FormData();
    let endpoint = '';

    try {
        if (op === 'img2pdf') {
            const files = document.getElementById('p-img2pdf-files').files;
            if (!files.length) throw new Error('请选择图片');
            for (const f of files) fd.append('images', f);
            if (document.getElementById('p-img2pdf-landscape').checked) fd.append('force_landscape', '1');
            endpoint = '/api/tools/pdf/images_to_pdf';

        } else if (op === 'merge') {
            const files = document.getElementById('p-merge-files').files;
            if (files.length < 2) throw new Error('请选择至少 2 个 PDF');
            for (const f of files) fd.append('pdfs', f);
            endpoint = '/api/tools/pdf/merge';

        } else if (op === 'remove') {
            const file = document.getElementById('p-remove-file').files[0];
            if (!file) throw new Error('请选择 PDF 文件');
            const pages = document.getElementById('p-remove-pages').value.trim();
            if (!pages) throw new Error('请输入要删除的页码');
            fd.append('pdf', file);
            fd.append('pages', pages);
            endpoint = '/api/tools/pdf/remove_pages';

        } else if (op === 'insert') {
            const main = document.getElementById('p-insert-main').files[0];
            const ins = document.getElementById('p-insert-ins').files[0];
            if (!main || !ins) throw new Error('请选择两个 PDF 文件');
            fd.append('main_pdf', main);
            fd.append('insert_pdf', ins);
            fd.append('position', document.getElementById('p-insert-pos').value);
            fd.append('page_index', document.getElementById('p-insert-page').value);
            endpoint = '/api/tools/pdf/insert';

        } else if (op === 'reorder') {
            const file = document.getElementById('p-reorder-file').files[0];
            if (!file) throw new Error('请选择 PDF 文件');
            fd.append('pdf', file);
            endpoint = '/api/tools/pdf/reorder';

        } else if (op === 'normalize') {
            const file = document.getElementById('p-normalize-file').files[0];
            if (!file) throw new Error('请选择 PDF 文件');
            fd.append('pdf', file);
            endpoint = '/api/tools/pdf/normalize';

        } else if (op === 'to_images') {
            const file = document.getElementById('p-toimg-file').files[0];
            if (!file) throw new Error('请选择 PDF 文件');
            fd.append('pdf', file);
            fd.append('start_page', document.getElementById('p-toimg-start').value);
            fd.append('end_page', document.getElementById('p-toimg-end').value);
            fd.append('dpi', document.getElementById('p-toimg-dpi').value);
            fd.append('format', document.getElementById('p-toimg-fmt').value);
            fd.append('max_size', document.getElementById('p-toimg-maxsize').value);
            if (document.getElementById('p-toimg-long').checked) fd.append('long_image', '1');
            endpoint = '/api/tools/pdf/to_images';
        }

        const res = await fetch(API_BASE + endpoint, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: fd
        });
        const data = await res.json();

        if (data.success) {
            resultEl.className = 'pdf-result ok';
            resultEl.innerHTML = data.message +
                `<br><a class="pdf-dl" href="${API_BASE + data.download_url}" target="_blank">下载文件</a>`;
        } else {
            resultEl.className = 'pdf-result err';
            resultEl.textContent = data.error || data.message;
        }
    } catch (e) {
        resultEl.className = 'pdf-result err';
        resultEl.textContent = e.message;
    } finally {
        btn.disabled = false;
    }
}

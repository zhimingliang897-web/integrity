/**
 * 在线工具功能模块
 * 处理 AI 对比、图文互转、AI 辩论、台词学习、视频生成
 */

const API_BASE = window.location.origin;

// ============ 通用工具函数 ============

function getToken() {
    return localStorage.getItem('token');
}

function showResult(elementId, html, isError = false) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<div style="padding:12px;background:${isError ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'};border-radius:8px;color:${isError ? '#ef4444' : '#10b981'};">${html}</div>`;
    }
}

function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = '<div style="padding:12px;color:var(--text-muted);">处理中...</div>';
    }
}

// ============ 折叠展开功能 ============

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const arrow = document.getElementById(sectionId + '-arrow');
    
    if (section && arrow) {
        if (section.style.display === 'none') {
            section.style.display = 'block';
            arrow.textContent = '▲';
        } else {
            section.style.display = 'none';
            arrow.textContent = '▼';
        }
    }
}

// ============ AI 多模型对比 ============

async function startAICompare() {
    const token = getToken();
    if (!token) {
        showResult('ai-compare-result', '请先登录', true);
        return;
    }

    const question = document.getElementById('ai-compare-question').value.trim();
    const systemPrompt = document.getElementById('ai-compare-system').value.trim();
    
    if (!question) {
        showResult('ai-compare-result', '请输入问题', true);
        return;
    }

    const modelCheckboxes = document.querySelectorAll('#ai-compare-tools input[type="checkbox"]:checked');
    const models = Array.from(modelCheckboxes).map(cb => cb.value);
    
    if (models.length === 0) {
        showResult('ai-compare-result', '请至少选择一个模型', true);
        return;
    }

    showLoading('ai-compare-result');

    const results = [];
    
    for (const model of models) {
        try {
            const res = await fetch(API_BASE + '/api/tools/ai-compare/query', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: question,
                    systemPrompt: systemPrompt,
                    provider: 'qwen',
                    model: model
                })
            });

            const data = await res.json();
            results.push({
                model: model,
                success: data.success,
                content: data.content || data.error,
                elapsed: data.elapsed
            });
        } catch (e) {
            results.push({
                model: model,
                success: false,
                content: e.message
            });
        }
    }

    let html = '<div style="display:grid;gap:16px;">';
    results.forEach(r => {
        html += `
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <strong style="color:var(--primary);">${r.model}</strong>
                    ${r.elapsed ? `<span style="color:var(--text-muted);font-size:12px;">${r.elapsed}s</span>` : ''}
                </div>
                <div style="font-size:14px;line-height:1.6;color:${r.success ? '#e2e8f0' : '#ef4444'};">${r.content}</div>
            </div>
        `;
    });
    html += '</div>';

    showResult('ai-compare-result', html);
}

// ============ 图文互转 ============

async function analyzeImage() {
    const token = getToken();
    if (!token) {
        showResult('image-prompt-result', '请先登录', true);
        return;
    }

    const fileInput = document.getElementById('image-prompt-file');
    const style = document.getElementById('image-prompt-style').value;

    if (!fileInput.files || fileInput.files.length === 0) {
        showResult('image-prompt-result', '请上传图片', true);
        return;
    }

    showLoading('image-prompt-result');

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('style', style);

    try {
        const res = await fetch(API_BASE + '/api/tools/image-prompt/analyze', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            showResult('image-prompt-result', `
                <div style="margin-bottom:8px;"><strong>生成的提示词：</strong></div>
                <div style="background:var(--bg-card);padding:12px;border-radius:8px;font-family:monospace;white-space:pre-wrap;">${data.prompt}</div>
            `);
        } else {
            showResult('image-prompt-result', data.error || '分析失败', true);
        }
    } catch (e) {
        showResult('image-prompt-result', '请求失败: ' + e.message, true);
    }
}

// ============ AI 辩论赛 ============

async function startDebate() {
    const token = getToken();
    if (!token) {
        showResult('debate-result', '请先登录', true);
        return;
    }

    const topic = document.getElementById('debate-topic').value.trim();
    const rounds = parseInt(document.getElementById('debate-rounds').value);

    if (!topic) {
        showResult('debate-result', '请输入辩题', true);
        return;
    }

    const resultEl = document.getElementById('debate-result');
    resultEl.innerHTML = '<div style="padding:12px;color:var(--text-muted);">辩论进行中...</div>';

    try {
        const res = await fetch(API_BASE + '/api/tools/ai-debate/start', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ topic, rounds })
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let messages = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.content) {
                            messages.push(data);
                            renderDebateMessages(resultEl, messages);
                        }
                    } catch (e) {}
                }
            }
        }

        if (messages.length === 0) {
            showResult('debate-result', '辩论完成，但未收到消息', true);
        }
    } catch (e) {
        showResult('debate-result', '请求失败: ' + e.message, true);
    }
}

function renderDebateMessages(el, messages) {
    let html = '';
    messages.forEach(m => {
        const sideColor = m.side === 'pro' ? '#10b981' : m.side === 'con' ? '#ef4444' : '#f59e0b';
        html += `
            <div style="margin-bottom:12px;padding:12px;background:var(--bg-card);border-left:3px solid ${sideColor};border-radius:0 8px 8px 0;">
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">${m.speaker} (${m.role})</div>
                <div style="line-height:1.6;">${m.content}</div>
            </div>
        `;
    });
    el.innerHTML = html;
}

// ============ 台词学习 ============

async function startDialogueLearning() {
    const token = getToken();
    if (!token) {
        showResult('dialogue-result', '请先登录', true);
        return;
    }

    const fileInput = document.getElementById('dialogue-pdf');

    if (!fileInput.files || fileInput.files.length === 0) {
        showResult('dialogue-result', '请上传 PDF 文件', true);
        return;
    }

    showLoading('dialogue-result');

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch(API_BASE + '/api/tools/dialogue-learning/process', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });

        const data = await res.json();

        if (data.task_id) {
            pollDialogueStatus(data.task_id, token);
        } else {
            showResult('dialogue-result', data.error || '处理失败', true);
        }
    } catch (e) {
        showResult('dialogue-result', '请求失败: ' + e.message, true);
    }
}

async function pollDialogueStatus(taskId, token) {
    const resultEl = document.getElementById('dialogue-result');
    
    const poll = async () => {
        try {
            const res = await fetch(API_BASE + '/api/tools/dialogue-learning/status/' + taskId, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();

            if (data.status === 'completed') {
                renderDialogueResult(resultEl, data.results);
            } else if (data.status === 'failed') {
                showResult('dialogue-result', data.error || '处理失败', true);
            } else {
                resultEl.innerHTML = `<div style="padding:12px;color:var(--text-muted);">处理中... ${data.progress || 0}%</div>`;
                setTimeout(poll, 2000);
            }
        } catch (e) {
            showResult('dialogue-result', '查询状态失败', true);
        }
    };

    poll();
}

function renderDialogueResult(el, results) {
    if (!results || !results.words) {
        showResult('dialogue-result', '处理完成，但无结果', true);
        return;
    }

    let html = '<div style="display:grid;gap:12px;">';
    results.words.slice(0, 10).forEach(w => {
        html += `
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:12px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <strong style="color:var(--primary);font-size:18px;">${w.word}</strong>
                    <span style="color:var(--text-muted);font-size:12px;">${w.phonetic || ''}</span>
                </div>
                ${w.definition ? `<div style="font-size:13px;margin-bottom:8px;">${w.definition}</div>` : ''}
                ${w.audio_url ? `<audio controls src="${API_BASE + w.audio_url}" style="width:100%;height:32px;"></audio>` : ''}
            </div>
        `;
    });
    html += '</div>';

    el.innerHTML = html;
}

// ============ 视频生成 ============

async function startVideoGeneration() {
    const token = getToken();
    if (!token) {
        showResult('video-result', '请先登录', true);
        return;
    }

    const scene = document.getElementById('video-scene').value.trim();
    const videoType = document.getElementById('video-type').value;

    if (!scene) {
        showResult('video-result', '请输入场景描述', true);
        return;
    }

    showLoading('video-result');

    try {
        const res = await fetch(API_BASE + '/api/tools/video-maker/generate', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scene_description: scene,
                video_type: videoType
            })
        });

        const data = await res.json();

        if (data.task_id) {
            pollVideoStatus(data.task_id, token);
        } else {
            showResult('video-result', data.error || '提交失败', true);
        }
    } catch (e) {
        showResult('video-result', '请求失败: ' + e.message, true);
    }
}

async function pollVideoStatus(taskId, token) {
    const resultEl = document.getElementById('video-result');
    
    const poll = async () => {
        try {
            const res = await fetch(API_BASE + '/api/tools/video-maker/status/' + taskId, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            const data = await res.json();

            if (data.status === 'completed') {
                if (data.video_url) {
                    resultEl.innerHTML = `
                        <div style="padding:12px;background:rgba(16,185,129,0.1);border-radius:8px;">
                            <div style="color:#10b981;margin-bottom:12px;">✅ 视频生成完成</div>
                            <video controls src="${API_BASE + data.video_url}" style="width:100%;border-radius:8px;"></video>
                        </div>
                    `;
                } else if (data.script) {
                    renderScriptResult(resultEl, data.script);
                }
            } else if (data.status === 'failed') {
                showResult('video-result', data.error || '生成失败', true);
            } else {
                resultEl.innerHTML = `<div style="padding:12px;color:var(--text-muted);">生成中... ${data.progress || 0}%</div>`;
                setTimeout(poll, 3000);
            }
        } catch (e) {
            showResult('video-result', '查询状态失败', true);
        }
    };

    poll();
}

function renderScriptResult(el, script) {
    let html = `
        <div style="padding:12px;background:rgba(59,130,246,0.1);border-radius:8px;">
            <div style="color:#3b82f6;margin-bottom:12px;">📝 剧本生成完成（视频合成不可用）</div>
            <div style="font-size:16px;font-weight:600;margin-bottom:16px;">${script.title || '视频剧本'}</div>
    `;

    if (script.scenes) {
        html += '<div style="display:grid;gap:12px;">';
        script.scenes.forEach((scene, i) => {
            html += `
                <div style="background:var(--bg-card);padding:12px;border-radius:8px;">
                    <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">场景 ${i + 1}</div>
                    <div style="font-size:13px;color:var(--text-muted);margin-bottom:8px;">${scene.description || ''}</div>
                    <div style="font-style:italic;">"${scene.narration || ''}"</div>
                </div>
            `;
        });
        html += '</div>';
    }

    html += '</div>';
    el.innerHTML = html;
}
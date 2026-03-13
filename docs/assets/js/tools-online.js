/**
 * 在线工具功能模块
 * 处理 AI 对比、图文互转、AI 辩论、台词学习、视频生成
 *
 * 重要设计：
 * - 仅在云服务器上使用，GitHub Pages 会跳转到服务器
 *
 * 注意：API_BASE、showToast 由 tools-auth.js 统一提供
 */

function getToken() {
    return localStorage.getItem('token');
}

function showResult(elementId, html, isError = false) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<div style="padding:12px;background:${isError ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'};border-radius:8px;color:${isError ? '#ef4444' : '#10b981'};">${html}</div>`;
    }
}

function showLoading(elementId, text = '处理中') {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `
            <div style="padding:16px;text-align:center;color:var(--text-muted);">
                <div class="loading-spinner" style="width:24px;height:24px;margin:0 auto 12px;"></div>
                <div>${text}...</div>
            </div>
        `;
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

    const questionEl = document.getElementById('ai-compare-question');
    const question = questionEl ? questionEl.value.trim() : '';
    const systemPromptEl = document.getElementById('ai-compare-system');
    const systemPrompt = systemPromptEl ? systemPromptEl.value.trim() : '';
    
    if (!question) {
        showResult('ai-compare-result', '请输入问题', true);
        showToast('请输入问题', 'warning');
        return;
    }

    const modelCheckboxes = document.querySelectorAll('#ai-compare-tools input[type="checkbox"]:checked');
    const models = Array.from(modelCheckboxes).map(cb => cb.value);
    
    if (models.length === 0) {
        showResult('ai-compare-result', '请至少选择一个模型', true);
        showToast('请至少选择一个模型', 'warning');
        return;
    }

    showLoading('ai-compare-result', `正在对比 ${models.length} 个模型`);

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

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.error || `HTTP ${res.status}`);
            }

            const data = await res.json();
            results.push({
                model: model,
                success: data.success !== false,
                content: data.content || data.error || '无响应',
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
                    <strong style="color:${r.success ? 'var(--primary)' : '#ef4444'};">${r.model}</strong>
                    ${r.elapsed ? `<span style="color:var(--text-muted);font-size:12px;">${r.elapsed}s</span>` : ''}
                </div>
                <div style="font-size:14px;line-height:1.6;color:${r.success ? '#e2e8f0' : '#ef4444'};">${r.content}</div>
            </div>
        `;
    });
    html += '</div>';

    showResult('ai-compare-result', html);
    showToast('模型对比完成！', 'success');
}

// ============ 图文互转 ============

async function analyzeImage() {
    const token = getToken();
    if (!token) {
        showResult('image-prompt-result', '请先登录', true);
        return;
    }

    const fileInput = document.getElementById('image-prompt-file');
    const styleEl = document.getElementById('image-prompt-style');
    const style = styleEl ? styleEl.value : 'dalle';

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showResult('image-prompt-result', '请上传图片', true);
        showToast('请上传图片', 'warning');
        return;
    }

    showLoading('image-prompt-result', '正在分析图片');

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('style', style);

    try {
        const res = await fetch(API_BASE + '/api/tools/image-prompt/analyze', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP ${res.status}`);
        }

        const data = await res.json();

        if (data.success) {
            showResult('image-prompt-result', `
                <div style="margin-bottom:8px;font-weight:600;">生成的提示词 (${data.style === 'sd' ? 'Stable Diffusion' : 'DALL-E'} 风格)</div>
                <div style="background:var(--bg-card);padding:12px;border-radius:8px;font-family:monospace;white-space:pre-wrap;line-height:1.6;">${data.prompt}</div>
                <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">✓ 可直接复制使用</div>
            `);
            showToast('提示词生成完成！', 'success');
        } else {
            showResult('image-prompt-result', data.error || '分析失败', true);
            showToast('分析失败', 'error');
        }
    } catch (e) {
        showResult('image-prompt-result', '请求失败: ' + e.message, true);
        showToast('请求失败: ' + e.message, 'error');
    }
}

// ============ AI 辩论赛 ============

async function startDebate() {
    const token = getToken();
    if (!token) {
        showResult('debate-result', '请先登录', true);
        return;
    }

    const topicEl = document.getElementById('debate-topic');
    const roundsEl = document.getElementById('debate-rounds');
    
    const topic = topicEl ? topicEl.value.trim() : '';
    const rounds = roundsEl ? parseInt(roundsEl.value) : 4;

    if (!topic) {
        showResult('debate-result', '请输入辩题', true);
        showToast('请输入辩题', 'warning');
        return;
    }

    const resultEl = document.getElementById('debate-result');
    resultEl.innerHTML = `
        <div style="padding:16px;text-align:center;color:var(--text-muted);">
            <div class="loading-spinner" style="width:24px;height:24px;margin:0 auto 12px;"></div>
            <div>辩论进行中...</div>
        </div>
    `;

    try {
        const res = await fetch(API_BASE + '/api/tools/ai-debate/start', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ topic, rounds })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let messages = [];
        let currentEvent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line) {
                    // 事件分隔行，重置当前事件类型
                    currentEvent = '';
                    continue;
                }

                if (line.startsWith('event: ')) {
                    currentEvent = line.substring(7).trim();
                    continue;
                }

                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        const eventType = currentEvent || data.event || '';

                        // 仅对包含完整 content 的消息进行渲染，避免显示 undefined
                        if (eventType === 'message' || (!eventType && typeof data.content === 'string')) {
                            messages.push({
                                speaker: data.speaker,
                                role: data.role,
                                side: data.side,
                                content: data.content
                            });
                            renderDebateMessages(resultEl, messages);
                        } else if (eventType === 'result') {
                            // 结果事件单独追加到结果区域下方
                            const winner = data.winner || '';
                            const comment = data.comment || '';
                            const extra = winner ? `<div style="margin-bottom:4px;font-weight:600;">胜方：${winner}</div>` : '';
                            const existing = resultEl.innerHTML || '';
                            resultEl.innerHTML = `
                                ${existing}
                                <div style="margin-top:16px;padding:12px;border-radius:8px;border:1px dashed var(--border);color:var(--text-muted);">
                                    ${extra}
                                    <div>${comment}</div>
                                </div>
                            `;
                        }
                        // 对于 chunk 等仅包含 text 的事件，这里忽略，由后端最终的 message 事件负责提供 content
                    } catch (e) {
                        // 忽略单条解析错误，继续处理后续行
                    }
                }
            }
        }

        if (messages.length === 0) {
            showResult('debate-result', '辩论完成，但未收到消息', true);
        } else {
            showToast('辩论完成！', 'success');
        }
    } catch (e) {
        showResult('debate-result', '请求失败: ' + e.message, true);
        showToast('请求失败: ' + e.message, 'error');
    }
}

function renderDebateMessages(el, messages) {
    let html = '';
    messages.forEach(m => {
        const sideColor = m.side === 'pro' ? '#10b981' : m.side === 'con' ? '#ef4444' : '#f59e0b';
        const content = typeof m.content === 'string' ? m.content : (typeof m.text === 'string' ? m.text : '');
        html += `
            <div style="margin-bottom:12px;padding:12px;background:var(--bg-card);border-left:3px solid ${sideColor};border-radius:0 8px 8px 0;">
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">${m.speaker} (${m.role})</div>
                <div style="line-height:1.6;">${content}</div>
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
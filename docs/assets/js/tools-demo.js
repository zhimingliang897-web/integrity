/**
 * 演示功能模块
 * 图文互转、多模型对比、AI 辩论赛、Token 计算器
 *
 * 重要设计：
 * - GitHub Pages: 纯静态模拟，所有功能都是演示
 * - 云服务器: 真实 API 调用
 *
 * 注意：SERVER_URL、API_BASE、IS_GITHUB_PAGES、showToast 由 tools-auth.js 统一提供
 */

function createTypewriterEffect(element, text, speed = 20) {
    return new Promise(resolve => {
        element.innerHTML = '';
        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
            } else {
                clearInterval(interval);
                resolve();
            }
        }, speed);
    });
}

function createLoadingHTML(text = '处理中') {
    return `<span class="loading-pulse">${text}</span> <span class="loading-dots"><span></span><span></span><span></span></span>`;
}

// ========== Tab 切换 ==========
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ========== PDF Tab 切换 ==========
document.addEventListener('DOMContentLoaded', function() {
    const pdfTabs = document.querySelectorAll('.pdf-tab');
    pdfTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            pdfTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const tabId = this.dataset.tab;
            document.querySelectorAll('.pdf-panel').forEach(panel => panel.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
        });
    });

    // 初始化演示按钮
    initVisionDemo();
    initCompareDemo();
    initDebateDemo();
    initTokenCalc();
});

// ========== 图文互转演示 ==========
function initVisionDemo() {
    const visionBtn = document.getElementById('start-vision-btn');
    const visionOutput = document.getElementById('vision-output');
    const demoImg = document.getElementById('vision-demo-img');
    let isScanning = false;

    if (visionBtn && visionOutput) {
        visionBtn.addEventListener('click', async () => {
            if (isScanning) return;
            isScanning = true;
            visionBtn.disabled = true;
            visionBtn.innerHTML = createLoadingHTML('分析中');
            
            if (demoImg) {
                demoImg.style.filter = 'brightness(1.2) contrast(1.1)';
                demoImg.style.transition = 'filter 0.3s';
            }
            
            visionOutput.innerHTML = `<div style="color:var(--primary);display:flex;align-items:center;gap:8px;">
                <span class="loading-spinner"></span> 正在调用 Qwen-VL 分析图片...
            </div>`;
            
            await new Promise(r => setTimeout(r, 1200));
            
            visionOutput.innerHTML = `<div style="color:#10b981;display:flex;align-items:center;gap:8px;">
                ✓ 图片分析完成，生成提示词...
            </div>`;
            
            await new Promise(r => setTimeout(r, 500));
            
            if (demoImg) demoImg.style.filter = '';
            
            const promptText = "A stunning cyberpunk cityscape at night. Neon signs in magenta and cyan, reflecting off wet asphalt. Flying vehicles between towering skyscrapers. Cinematic lighting, photorealistic.";
            
            visionOutput.innerHTML = `
                <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">
                    ✓ Qwen-VL-Max 生成的 DALL-E 提示词
                </div>
                <div id="vision-typewriter" style="color:#e2e8f0;line-height:1.6;"></div>
            `;
            
            const typewriterEl = document.getElementById('vision-typewriter');
            await createTypewriterEffect(typewriterEl, promptText, 15);
            
            isScanning = false;
            visionBtn.disabled = false;
            visionBtn.textContent = '重新提取';
            showToast('提示词提取完成！', 'success');
        });
    }
}

// ========== 多模型对比演示 ==========
function initCompareDemo() {
    const compareBtn = document.getElementById('start-compare-btn');

    const modelResponses = {
        'qwen': '大语言模型（LLM）是基于深度学习的AI模型，通过海量文本训练，能理解和生成人类语言。核心特点：规模大、涌现能力、通用性强。',
        'turbo': 'LLM本质是文本预测机器，给定上文预测下文。使用Transformer架构，通过注意力机制处理长文本依赖，从互联网文本中自学语言规律。',
        'max': 'Large Language Model (LLM) is an AI trained on massive text data. Key features: 1) Transformer architecture, 2) Billions of parameters, 3) Multi-task capabilities, 4) Emergent abilities at scale.'
    };

    const modelColors = {
        'qwen': '#f59e0b',
        'turbo': '#3b82f6',
        'max': '#10b981'
    };

    if (compareBtn) {
        compareBtn.addEventListener('click', async () => {
            if (compareBtn.disabled) return;
            compareBtn.disabled = true;
            compareBtn.innerHTML = createLoadingHTML('对比中');
            
            const qwenEl = document.querySelector('#model-qwen > div:last-child');
            const turboEl = document.querySelector('#model-turbo > div:last-child');
            const maxEl = document.querySelector('#model-max > div:last-child');
            
            const elements = [qwenEl, turboEl, maxEl];
            const models = ['qwen', 'turbo', 'max'];
            
            elements.forEach((el, i) => {
                if (el) {
                    el.innerHTML = `<div style="display:flex;align-items:center;gap:6px;color:${modelColors[models[i]]}">
                        <span class="loading-spinner" style="border-top-color:${modelColors[models[i]]}"></span>
                        思考中...
                    </div>`;
                }
            });
            
            await new Promise(r => setTimeout(r, 500));
            
            for (let i = 0; i < models.length; i++) {
                const el = elements[i];
                const model = models[i];
                
                if (el) {
                    el.innerHTML = '';
                    const textSpan = document.createElement('span');
                    textSpan.style.color = '#e2e8f0';
                    el.appendChild(textSpan);
                    
                    await createTypewriterEffect(textSpan, modelResponses[model], 12);
                }
                
                if (i < models.length - 1) {
                    await new Promise(r => setTimeout(r, 200));
                }
            }
            
            compareBtn.disabled = false;
            compareBtn.textContent = '重新对比';
            showToast('多模型对比完成！', 'success');
        });
    }
}

// ========== AI 辩论赛演示 ==========
function initDebateDemo() {
    const debateBtn = document.getElementById('start-debate-btn');
    const debateOutput = document.getElementById('debate-output');
    
    if (debateBtn && debateOutput) {
        debateBtn.addEventListener('click', async () => {
            if (debateBtn.disabled) return;
            debateBtn.disabled = true;
            debateBtn.innerHTML = createLoadingHTML('辩论中');
            
            debateOutput.innerHTML = `
                <div style="text-align:center;padding:20px;color:var(--text-muted);">
                    <span class="loading-spinner" style="width:32px;height:32px;"></span>
                    <div style="margin-top:12px;">正反双方辩手就位中...</div>
                </div>
            `;
            
            await new Promise(r => setTimeout(r, 800));
            
            debateOutput.innerHTML = '';
            
            const messages = [
                { role: '正方', speaker: '千问·论道', text: '我认为AI不会让人类变懒，而是解放了人类的创造力。就像计算器没有让人类丧失数学能力，AI只会让我们专注于更高层次的思考。', color: '#10b981' },
                { role: '反方', speaker: '千问·辨析', text: '恰恰相反，过度依赖AI会导致人类思维能力退化。当所有问题都有AI解答，我们还会主动思考吗？', color: '#ef4444' },
                { role: '正方', speaker: '千问·论道', text: '这种担忧在每次技术革命时都会出现，但历史证明技术总是推动进步。AI是人类思维的扩展，而非替代。', color: '#10b981' }
            ];
            
            for (const msg of messages) {
                const msgDiv = document.createElement('div');
                msgDiv.style.cssText = 'margin-bottom:12px;padding:12px;background:var(--bg-card);border-radius:8px;border-left:3px solid ' + msg.color + ';opacity:0;transform:translateX(-10px);transition:all 0.3s';
                msgDiv.innerHTML = `
                    <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;display:flex;align-items:center;gap:6px;">
                        <span style="color:${msg.color};font-weight:600;">${msg.role}</span>
                        <span>-</span>
                        <span>${msg.speaker}</span>
                    </div>
                    <div class="debate-text" style="line-height:1.6;"></div>
                `;
                debateOutput.appendChild(msgDiv);
                
                await new Promise(r => setTimeout(r, 50));
                msgDiv.style.opacity = '1';
                msgDiv.style.transform = 'translateX(0)';
                
                const textEl = msgDiv.querySelector('.debate-text');
                await createTypewriterEffect(textEl, msg.text, 25);
                
                await new Promise(r => setTimeout(r, 300));
            }
            
            debateBtn.disabled = false;
            debateBtn.textContent = '重新开始';
            showToast('辩论演示完成！', 'success');
        });
    }
}

// ========== Token 计算器演示 ==========
function initTokenCalc() {
    const calcTokenBtn = document.getElementById('calc-token-btn');

    if (calcTokenBtn) {
        calcTokenBtn.addEventListener('click', async () => {
            const modelEl = document.getElementById('token-model');
            const langEl = document.getElementById('token-lang');
            const charsEl = document.getElementById('token-chars');
            
            const model = modelEl ? modelEl.value : 'qwen-plus';
            const lang = langEl ? langEl.value : 'zh';
            const chars = charsEl ? parseInt(charsEl.value) || 100 : 100;
            
            calcTokenBtn.disabled = true;
            calcTokenBtn.innerHTML = createLoadingHTML('计算中');
            
            const promptEl = document.getElementById('result-prompt');
            const completionEl = document.getElementById('result-completion');
            const costEl = document.getElementById('result-cost');
            
            if (promptEl) promptEl.innerHTML = '<span class="loading-pulse">-</span>';
            if (completionEl) completionEl.innerHTML = '<span class="loading-pulse">-</span>';
            if (costEl) costEl.innerHTML = '<span class="loading-pulse">-</span>';
            
            // GitHub Pages 上使用静态模拟数据
            if (IS_GITHUB_PAGES) {
                await new Promise(r => setTimeout(r, 500));
                
                const tokenPrices = {
                    'qwen-plus': { input: 0.004, output: 0.012 },
                    'qwen-turbo': { input: 0.001, output: 0.002 },
                    'gpt-4o': { input: 0.0025, output: 0.01 }
                };
                
                const tokenRatios = { 'zh': 0.5, 'en': 0.25 };
                const ratio = tokenRatios[lang] || 0.5;
                const promptTokens = Math.round(chars * ratio);
                const completionTokens = Math.round(promptTokens * 0.3);
                const prices = tokenPrices[model] || tokenPrices['qwen-plus'];
                const totalCost = (promptTokens / 1000) * prices.input + (completionTokens / 1000) * prices.output;
                
                if (promptEl) promptEl.textContent = promptTokens;
                if (completionEl) completionEl.textContent = completionTokens;
                if (costEl) costEl.textContent = '$' + totalCost.toFixed(6);
                
                calcTokenBtn.disabled = false;
                calcTokenBtn.textContent = '计算消耗';
                showToast('Token 计算完成（演示数据）', 'success');
                return;
            }
            
            // 服务器上调用真实 API
            try {
                const res = await fetch(API_BASE + '/api/tools/token-calc', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model, lang, chars })
                });
                
                if (!res.ok) throw new Error('API 请求失败');
                
                const data = await res.json();
                
                await new Promise(r => setTimeout(r, 300));
                
                if (promptEl) {
                    promptEl.style.animation = 'pulse 0.3s';
                    promptEl.textContent = data.prompt_tokens || '-';
                }
                if (completionEl) {
                    completionEl.style.animation = 'pulse 0.3s';
                    completionEl.textContent = data.completion_tokens || '-';
                }
                if (costEl) {
                    costEl.style.animation = 'pulse 0.3s';
                    costEl.textContent = '$' + (data.total_cost || 0).toFixed(6);
                }
                
                showToast('Token 计算完成！', 'success');
            } catch (e) {
                if (promptEl) promptEl.textContent = '-';
                if (completionEl) completionEl.textContent = '-';
                if (costEl) {
                    costEl.textContent = 'API 错误';
                    costEl.style.color = '#ef4444';
                }
                showToast('计算失败：' + e.message, 'error');
            }
            
            calcTokenBtn.disabled = false;
            calcTokenBtn.textContent = '计算消耗';
        });
    }
}
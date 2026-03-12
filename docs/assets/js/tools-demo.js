/**
 * 演示功能模块
 * 图文互转、多模型对比、AI 辩论赛、Token 计算器
 */

const API_BASE = window.location.origin;

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
            visionBtn.textContent = '分析中...';
            
            if (demoImg) demoImg.style.filter = 'brightness(1.1) contrast(1.1)';
            
            visionOutput.innerHTML = '<span style="color:var(--primary);">分析中...</span>';
            
            await new Promise(r => setTimeout(r, 1500));
            
            if (demoImg) demoImg.style.filter = 'grayscale(0%)';
            
            const promptText = "A stunning cyberpunk cityscape at night. Neon signs in magenta and cyan, reflecting off wet asphalt. Flying vehicles between towering skyscrapers. Cinematic lighting, photorealistic.";
            
            visionOutput.innerHTML = '';
            const targetSpan = document.createElement('span');
            targetSpan.style.color = '#e2e8f0';
            visionOutput.appendChild(targetSpan);
            
            for (let i = 0; i < promptText.length; i++) {
                targetSpan.innerHTML += promptText.charAt(i);
                await new Promise(r => setTimeout(r, 20));
            }
            
            isScanning = false;
            visionBtn.disabled = false;
            visionBtn.textContent = '重新提取';
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

    if (compareBtn) {
        compareBtn.addEventListener('click', async () => {
            if (compareBtn.disabled) return;
            compareBtn.disabled = true;
            compareBtn.textContent = '对比中...';
            
            const qwenEl = document.querySelector('#model-qwen > div:last-child');
            const turboEl = document.querySelector('#model-turbo > div:last-child');
            const maxEl = document.querySelector('#model-max > div:last-child');
            
            if (qwenEl) qwenEl.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
            if (turboEl) turboEl.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
            if (maxEl) maxEl.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
            
            await new Promise(r => setTimeout(r, 600));
            
            if (qwenEl) {
                qwenEl.innerHTML = '';
                for (let c of modelResponses.qwen) {
                    qwenEl.innerHTML += c;
                    await new Promise(r => setTimeout(r, 15));
                }
            }
            
            await new Promise(r => setTimeout(r, 300));
            
            if (turboEl) {
                turboEl.innerHTML = '';
                for (let c of modelResponses.turbo) {
                    turboEl.innerHTML += c;
                    await new Promise(r => setTimeout(r, 12));
                }
            }
            
            await new Promise(r => setTimeout(r, 300));
            
            if (maxEl) {
                maxEl.innerHTML = '';
                for (let c of modelResponses.max) {
                    maxEl.innerHTML += c;
                    await new Promise(r => setTimeout(r, 10));
                }
            }
            
            compareBtn.disabled = false;
            compareBtn.textContent = '重新对比';
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
            debateBtn.textContent = '辩论中...';
            
            debateOutput.innerHTML = '';
            
            const messages = [
                { role: '正方', speaker: '千问·论道', text: '我认为AI不会让人类变懒，而是解放了人类的创造力...' },
                { role: '反方', speaker: '千问·辨析', text: '恰恰相反，过度依赖AI会导致人类思维能力退化...' },
                { role: '正方', speaker: '千问·论道', text: '这种担忧在每次技术革命时都会出现，但历史证明技术总是推动进步...' }
            ];
            
            for (const msg of messages) {
                const msgDiv = document.createElement('div');
                msgDiv.style.cssText = 'margin-bottom:12px;padding:12px;background:var(--bg-card);border-radius:8px;border-left:3px solid ' + (msg.role === '正方' ? '#10b981' : '#ef4444');
                msgDiv.innerHTML = `<div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">${msg.role} - ${msg.speaker}</div><div id="msg-text"></div>`;
                debateOutput.appendChild(msgDiv);
                
                const textEl = msgDiv.querySelector('#msg-text');
                for (let c of msg.text) {
                    textEl.innerHTML += c;
                    await new Promise(r => setTimeout(r, 30));
                }
            }
            
            debateBtn.disabled = false;
            debateBtn.textContent = '重新开始';
        });
    }
}

// ========== Token 计算器演示 ==========
function initTokenCalc() {
    const calcTokenBtn = document.getElementById('calc-token-btn');

    if (calcTokenBtn) {
        calcTokenBtn.addEventListener('click', async () => {
            const model = document.getElementById('token-model')?.value || 'qwen-plus';
            const lang = document.getElementById('token-lang')?.value || 'zh';
            const chars = parseInt(document.getElementById('token-chars')?.value) || 100;
            
            calcTokenBtn.disabled = true;
            calcTokenBtn.textContent = '计算中...';
            
            try {
                const res = await fetch(API_BASE + '/api/tools/token-calc', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model, lang, chars })
                });
                const data = await res.json();
                
                const promptEl = document.getElementById('result-prompt');
                const completionEl = document.getElementById('result-completion');
                const costEl = document.getElementById('result-cost');
                
                if (promptEl) promptEl.textContent = data.prompt_tokens || '-';
                if (completionEl) completionEl.textContent = data.completion_tokens || '-';
                if (costEl) costEl.textContent = '$' + (data.total_cost || 0).toFixed(6);
            } catch (e) {
                const costEl = document.getElementById('result-cost');
                if (costEl) costEl.textContent = 'API 错误';
            }
            
            calcTokenBtn.disabled = false;
            calcTokenBtn.textContent = '计算消耗';
        });
    }
}
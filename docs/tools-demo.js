/**
 * 演示功能模块
 * 图文互转、多模型对比、Token 计算器
 */

// ========== 图文互转演示 ==========
const visionBtn = document.getElementById('start-vision-btn');
const visionOutput = document.getElementById('vision-output');
const scanLine = document.getElementById('scan-line');
const demoImg = document.getElementById('vision-demo-img');
let isScanning = false;

if (visionBtn) {
    visionBtn.addEventListener('click', async () => {
        if (isScanning) return;
        isScanning = true;
        visionBtn.disabled = true;
        visionBtn.textContent = '视觉模型分析中...';
        
        scanLine.style.display = 'block';
        scanLine.style.animation = 'scan 2.5s ease-in-out infinite';
        demoImg.style.filter = 'brightness(1.1) contrast(1.1)';
        
        visionOutput.innerHTML = '<span style="color:var(--primary);">[Model Initialized] Analyzing visual features...</span><br><br>';
        
        await new Promise(r => setTimeout(r, 1800));
        
        scanLine.style.display = 'none';
        demoImg.style.filter = 'grayscale(0%) brightness(1.1)';
        
        const promptText = "A stunning high-quality 3D render of a futuristic cyberpunk cityscape at night. Neon signs glowing in magenta and cyan, reflecting off wet asphalt. Sleek flying vehicles navigate between towering skyscrapers shrouded in volumetric fog. Cinematic lighting, octane render, unreal engine 5, 8k resolution, photorealistic details, deeply atmospheric.";
        
        const targetSpan = document.createElement('span');
        targetSpan.style.color = '#fff';
        visionOutput.appendChild(targetSpan);
        
        for (let i = 0; i < promptText.length; i++) {
            targetSpan.innerHTML += promptText.charAt(i);
            await new Promise(r => setTimeout(r, 15));
        }
        
        isScanning = false;
        visionBtn.disabled = false;
        visionBtn.textContent = '重新提取 ⚡';
    });
}

// ========== 多模型对比演示 ==========
const compareBtn = document.getElementById('start-compare-btn');

const modelResponses = {
    'qwen-plus': '大语言模型（Large Language Model，简称LLM）是一种基于深度学习技术的人工智能模型。它通过海量文本数据进行训练，能够理解和生成人类语言。核心特点包括：1）规模巨大，通常有数十亿到数千亿参数；2）涌现能力，随着规模增大出现小模型不具备的能力；3）通用性，一个模型可以完成多种任务。',
    'deepseek-v3': 'LLM（Large Language Model）是近年来AI领域的重大突破。它本质是一个超级强大的文本预测机器——给定前面的文字，预测下一个最可能出现的文字。训练方式是无监督学习，让模型从海量互联网文本中自学语言规律。典型架构是Transformer，attention机制让它能处理长文本依赖。',
    'gpt-4o-mini': 'A Large Language Model (LLM) is an AI trained on massive text data to understand and generate human language. Key points: 1) Trained using transformer architecture, 2) Learns patterns from billions of parameters, 3) Can perform various NLP tasks like translation, summarization, coding, etc., 4) Shows emergent abilities at scale.'
};

if (compareBtn) {
    compareBtn.addEventListener('click', async () => {
        if (compareBtn.disabled) return;
        compareBtn.disabled = true;
        compareBtn.textContent = '模型回答中...';
        
        const qwenText = document.querySelector('#model-qwen .model-text');
        const deepseekText = document.querySelector('#model-deepseek .model-text');
        const gptText = document.querySelector('#model-gpt .model-text');
        
        qwenText.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
        deepseekText.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
        gptText.innerHTML = '<span style="color:var(--primary);">● 思考中...</span>';
        
        await new Promise(r => setTimeout(r, 800));
        qwenText.innerHTML = '';
        for (let i = 0; i < modelResponses['qwen-plus'].length; i++) {
            qwenText.innerHTML += modelResponses['qwen-plus'].charAt(i);
            await new Promise(r => setTimeout(r, 15));
        }
        
        await new Promise(r => setTimeout(r, 400));
        deepseekText.innerHTML = '';
        for (let i = 0; i < modelResponses['deepseek-v3'].length; i++) {
            deepseekText.innerHTML += modelResponses['deepseek-v3'].charAt(i);
            await new Promise(r => setTimeout(r, 12));
        }
        
        await new Promise(r => setTimeout(r, 400));
        gptText.innerHTML = '';
        for (let i = 0; i < modelResponses['gpt-4o-mini'].length; i++) {
            gptText.innerHTML += modelResponses['gpt-4o-mini'].charAt(i);
            await new Promise(r => setTimeout(r, 10));
        }
        
        compareBtn.disabled = false;
        compareBtn.textContent = '重新对比 🎯';
    });
}

// ========== Token 计算器演示 ==========
const calcTokenBtn = document.getElementById('calc-token-btn');

if (calcTokenBtn) {
    calcTokenBtn.addEventListener('click', async () => {
        const model = document.getElementById('token-model').value;
        const lang = document.getElementById('token-lang').value;
        const chars = parseInt(document.getElementById('token-chars').value) || 100;
        
        calcTokenBtn.disabled = true;
        calcTokenBtn.textContent = '计算中...';
        
        try {
            const res = await fetch(API_BASE + '/api/tools/token-calc', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model, lang, chars })
            });
            const data = await res.json();
            
            document.getElementById('result-prompt').textContent = data.prompt_tokens;
            document.getElementById('result-completion').textContent = data.completion_tokens;
            document.getElementById('result-cost').textContent = '$' + data.total_cost.toFixed(6);
        } catch (e) {
            document.getElementById('result-cost').textContent = 'API 错误';
        }
        
        calcTokenBtn.disabled = false;
        calcTokenBtn.textContent = '计算消耗 💰';
    });
}

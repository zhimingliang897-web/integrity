"""
Integrity API Server
运行在阿里云服务器上的后端服务
"""

import os
import json
from flask import Flask, request, jsonify
import dashscope
from dashscope import Generation

app = Flask(__name__)

# API Key 配置（从环境变量读取）
dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY', '')

# 用户认证（简单版本：内存存储）
# 生产环境建议用数据库
users = {
    "test001": {"name": "测试用户", "api_quota": 1000},
    "test002": {"name": "测试用户2", "api_quota": 1000}
}

# 请求记录
request_history = []

def verify_token(token):
    """验证用户 token"""
    return users.get(token)

@app.route('/')
def index():
    return {"status": "ok", "service": "Integrity API", "version": "1.0"}

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI 对话接口"""
    data = request.get_json()
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "未授权，请先登录"}), 401
    
    message = data.get('message', '')
    model = data.get('model', 'qwen-plus')
    
    if not message:
        return jsonify({"error": "消息不能为空"}), 400
    
    try:
        response = Generation.call(
            model=model,
            messages=[
                {'role': 'user', 'content': message}
            ],
            result_format='message'
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            return jsonify({
                "success": True,
                "reply": content,
                "model": model,
                "usage": dict(response.usage) if hasattr(response, 'usage') else {}
            })
        else:
            return jsonify({
                "success": False,
                "error": response.message
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tools/token-calc', methods=['POST'])
def token_calc():
    """Token 消耗计算"""
    data = request.get_json()
    
    model = data.get('model', 'qwen-plus')
    text = data.get('text', '')
    lang = data.get('lang', 'zh')
    
    # 简单估算（中文字符约 0.5 token，英文约 0.25 token）
    ratio = 0.5 if lang == 'zh' else 0.25
    prompt_tokens = len(text) * ratio
    
    # 模型价格（每 1000 token）
    prices = {
        'qwen-plus': {'input': 0.004, 'output': 0.012},
        'qwen-turbo': {'input': 0.001, 'output': 0.002},
        'qwen-max': {'input': 0.02, 'output': 0.06},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        'gpt-4o': {'input': 0.0025, 'output': 0.01}
    }
    
    price = prices.get(model, prices['qwen-plus'])
    completion_tokens = 100  # 假设输出
    total_tokens = prompt_tokens + completion_tokens
    cost = (total_tokens / 1000) * price['input']
    
    return jsonify({
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": completion_tokens,
        "total_tokens": int(total_tokens),
        "estimated_cost": round(cost, 6)
    })

@app.route('/api/login', methods=['POST'])
def login():
    """简单登录接口"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    # 简单验证（生产环境请用数据库）
    if username in users:
        return jsonify({
            "success": True,
            "token": username,
            "name": users[username]['name'],
            "quota": users[username]['api_quota']
        })
    else:
        # 自动注册
        users[username] = {"name": username, "api_quota": 1000}
        return jsonify({
            "success": True,
            "token": username,
            "name": username,
            "quota": 1000,
            "registered": True
        })

if __name__ == '__main__':
    # 监听 0.0.0.0 让外网可以访问
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
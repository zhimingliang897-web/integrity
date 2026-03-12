"""
AI 多模型对比工具 Blueprint
路径前缀: /api/tools/ai-compare
支持多个 AI 模型的统一调用和对比
"""

import os
import time
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

ai_compare_bp = Blueprint('ai_compare', __name__, url_prefix='/api/tools/ai-compare')

MODEL_CONFIGS = {
    'qwen': {
        'name': '千问',
        'api_key_env': 'QWEN_API_KEY',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'models': {
            'qwen-turbo': 'qwen-turbo',
            'qwen-plus': 'qwen-plus',
            'qwen-max': 'qwen-max',
        }
    },
    'doubao': {
        'name': '豆包',
        'api_key_env': 'DOUBAO_API_KEY',
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'models': {
            'doubao-pro-32k': 'doubao-pro-32k',
            'doubao-pro-128k': 'doubao-pro-128k',
        }
    },
    'deepseek': {
        'name': 'DeepSeek',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'base_url': 'https://api.deepseek.com',
        'models': {
            'deepseek-chat': 'deepseek-chat',
        }
    },
    'kimi': {
        'name': 'Kimi',
        'api_key_env': 'KIMI_API_KEY',
        'base_url': 'https://api.moonshot.cn/v1',
        'models': {
            'moonshot-v1-8k': 'moonshot-v1-8k',
            'moonshot-v1-32k': 'moonshot-v1-32k',
        }
    },
    'openai': {
        'name': 'OpenAI',
        'api_key_env': 'OPENAI_API_KEY',
        'base_url': None,
        'models': {
            'gpt-4o': 'gpt-4o',
            'gpt-4o-mini': 'gpt-4o-mini',
        }
    },
}


def require_token(f):
    """JWT Token 认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        import flask
        secret = flask.current_app.config.get('SECRET_KEY', 'integrity-lab-secret-key-2026')
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '请先登录'}), 401
        try:
            jwt.decode(token, secret, algorithms=['HS256'])
        except Exception:
            return jsonify({'error': 'Token 无效或已过期，请重新登录'}), 401
        return f(*args, **kwargs)
    return decorated


def get_client(provider):
    """获取对应提供商的 OpenAI 客户端"""
    if not HAS_OPENAI:
        return None, '缺少 openai 库'
    
    config = MODEL_CONFIGS.get(provider)
    if not config:
        return None, f'不支持的提供商: {provider}'
    
    api_key = os.environ.get(config['api_key_env'])
    if not api_key:
        return None, f'未配置 {config["name"]} API Key'
    
    client_kwargs = {'api_key': api_key}
    if config['base_url']:
        client_kwargs['base_url'] = config['base_url']
    
    return OpenAI(**client_kwargs), None


def call_model(provider, model, question, system_prompt=None, temperature=0.7, max_tokens=2000):
    """调用单个 AI 模型"""
    client, error = get_client(provider)
    if error:
        return {'error': error}
    
    config = MODEL_CONFIGS[provider]
    model_id = config['models'].get(model)
    if not model_id:
        return {'error': f'不支持的模型: {model}'}
    
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': question})
    
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        elapsed = time.time() - start_time
        content = response.choices[0].message.content
        
        return {
            'success': True,
            'content': content,
            'model': model,
            'provider': config['name'],
            'elapsed': round(elapsed, 2),
            'tokens': {
                'prompt': response.usage.prompt_tokens,
                'completion': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'success': False,
            'error': str(e),
            'model': model,
            'provider': config['name'],
            'elapsed': round(elapsed, 2)
        }


@ai_compare_bp.route('/query', methods=['POST'])
@require_token
def query():
    """
    单个模型查询
    
    请求体:
    {
        "question": "什么是机器学习？",
        "systemPrompt": "你是一个专业技术顾问",
        "temperature": 0.7,
        "provider": "qwen",
        "model": "qwen-turbo"
    }
    
    响应:
    {
        "success": true,
        "content": "机器学习是...",
        "model": "qwen-turbo",
        "provider": "千问",
        "elapsed": 1.23,
        "tokens": {...}
    }
    """
    if not HAS_OPENAI:
        return jsonify({'error': '服务器缺少 openai 库'}), 500
    
    data = request.json
    question = data.get('question', '').strip()
    system_prompt = data.get('systemPrompt', '').strip()
    temperature = float(data.get('temperature', 0.7))
    provider = data.get('provider', 'qwen')
    model = data.get('model', 'qwen-turbo')
    max_tokens = int(data.get('maxTokens', 2000))
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    result = call_model(provider, model, question, system_prompt, temperature, max_tokens)
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result)


@ai_compare_bp.route('/providers', methods=['GET'])
def list_providers():
    """列出所有支持的提供商和模型"""
    providers = []
    for provider_id, config in MODEL_CONFIGS.items():
        providers.append({
            'id': provider_id,
            'name': config['name'],
            'models': [{'id': mid, 'name': mid} for mid in config['models'].keys()]
        })
    return jsonify({'providers': providers})
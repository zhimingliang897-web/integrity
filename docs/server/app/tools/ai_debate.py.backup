"""
AI 辩论赛工具 Blueprint
路径前缀: /api/tools/ai-debate
支持多模型辩论赛，SSE 流式输出
"""

import os
import json
import time
import jwt
import uuid
from functools import wraps
from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

ai_debate_bp = Blueprint('ai_debate', __name__, url_prefix='/api/tools/ai-debate')

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

DEBATER_CONFIGS = [
    {
        'id': 'qwen_pro',
        'name': '千问·论道',
        'api_key': DASHSCOPE_API_KEY,
        'base_url': DASHSCOPE_BASE_URL,
        'model': 'qwen3.5-plus'
    },
    {
        'id': 'qwen_turbo',
        'name': '千问·明理',
        'api_key': DASHSCOPE_API_KEY,
        'base_url': DASHSCOPE_BASE_URL,
        'model': 'qwen-turbo'
    },
    {
        'id': 'qwen_max',
        'name': '千问·深思',
        'api_key': DASHSCOPE_API_KEY,
        'base_url': DASHSCOPE_BASE_URL,
        'model': 'qwen-max'
    },
    {
        'id': 'qwen_plus',
        'name': '千问·辨析',
        'api_key': DASHSCOPE_API_KEY,
        'base_url': DASHSCOPE_BASE_URL,
        'model': 'qwen-plus'
    }
]

debate_sessions = {}


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


def get_client_for_debater(debater_config):
    """获取辩手的 API 客户端"""
    if not debater_config['api_key']:
        return None
    
    return OpenAI(
        api_key=debater_config['api_key'],
        base_url=debater_config['base_url']
    )


def generate_sse_event(event_type, data):
    """生成 SSE 事件格式"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_debate(topic, rounds):
    """流式生成辩论内容"""
    if not HAS_OPENAI:
        yield generate_sse_event('error', {'message': '服务器缺少 openai 库'})
        return
    
    if not DASHSCOPE_API_KEY:
        yield generate_sse_event('error', {'message': '服务器未配置 DASHSCOPE_API_KEY'})
        return
    
    pro_debaters = DEBATER_CONFIGS[:2]
    con_debaters = DEBATER_CONFIGS[2:]
    
    stages = [
        ('开篇立论', '双方一辩阐述各自观点'),
        ('驳论', '双方二辩驳斥对方观点'),
        ('自由辩论', '双方交替发言，展开辩论'),
        ('总结陈词', '双方总结观点')
    ]
    
    debate_history = []
    
    for round_num in range(min(rounds, 4)):
        stage_name, stage_desc = stages[round_num]
        
        yield generate_sse_event('stage', {
            'stage': stage_name,
            'desc': stage_desc,
            'round': round_num + 1
        })
        
        for side, debater in [('pro', pro_debaters[round_num % len(pro_debaters)]),
                               ('con', con_debaters[round_num % len(con_debaters)])]:
            client = get_client_for_debater(debater)
            if not client:
                yield generate_sse_event('error', {
                    'message': f'{debater["name"]} API Key 未配置'
                })
                continue
            
            side_name = '正方' if side == 'pro' else '反方'
            position = f'支持观点：{topic}' if side == 'pro' else f'反对观点：{topic}'
            
            system_prompt = f"""你是辩论赛{side_name}辩手「{debater["name"]}」。
当前环节：{stage_name}
你的立场：{position}

要求：
1. 观点鲜明，逻辑清晰
2. 语言简洁有力，不超过 200 字
3. {stage_desc}
4. 可以引用对方之前的论点进行驳斥（如有）
{'5. 参考之前的辩论内容：' + chr(10).join(debate_history[-4:]) if debate_history else ''}"""
            
            try:
                response = client.chat.completions.create(
                    model=debater['model'],
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': f'请就「{topic}」进行{stage_name}发言'}
                    ],
                    temperature=0.8,
                    max_tokens=500,
                    stream=True
                )
                
                content = ''
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        content += text
                        yield generate_sse_event('chunk', {
                            'speaker': debater['name'],
                            'role': f'{side_name}{(round_num % 2) + 1}辩',
                            'side': side,
                            'text': text
                        })
                
                debate_history.append(f'{side_name}({debater["name"]}): {content}')
                
                yield generate_sse_event('message', {
                    'speaker': debater['name'],
                    'role': f'{side_name}{(round_num % 2) + 1}辩',
                    'side': side,
                    'content': content
                })
                
                time.sleep(0.5)
                
            except Exception as e:
                yield generate_sse_event('error', {
                    'message': f'{debater["name"]} 发言失败: {str(e)}'
                })
    
    yield generate_sse_event('result', {
        'winner': '正方' if hash(topic) % 2 == 0 else '反方',
        'comment': '辩论精彩，双方各有亮点！感谢各位辩手的精彩表现。'
    })


@ai_debate_bp.route('/start', methods=['POST'])
@require_token
def start_debate():
    """
    开始辩论赛
    
    请求体:
    {
        "topic": "人工智能的发展利大于弊",
        "rounds": 4
    }
    
    响应: SSE 流
    event: stage
    data: {"stage": "开篇立论", "desc": "双方一辩阐述观点"}
    
    event: message
    data: {"speaker": "千问·论道", "role": "正方一辩", "side": "pro", "content": "..."}
    
    event: result
    data: {"winner": "正方", "comment": "..."}
    """
    data = request.json
    topic = data.get('topic', '').strip()
    rounds = int(data.get('rounds', 4))
    
    if not topic:
        return jsonify({'error': '辩论主题不能为空'}), 400
    
    if rounds < 1 or rounds > 4:
        rounds = 4
    
    def generate():
        yield from stream_debate(topic, rounds)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@ai_debate_bp.route('/debaters', methods=['GET'])
def list_debaters():
    """列出所有辩手"""
    debaters = []
    for config in DEBATER_CONFIGS:
        debaters.append({
            'id': config['id'],
            'name': config['name'],
            'model': config['model']
        })
    return jsonify({'debaters': debaters})
"""
AI 辩论赛工具 Blueprint - 完整版
路径前缀: /api/tools/ai-debate
支持多模型辩论赛，完整赛制，SSE 流式输出
"""

import os
import json
import time
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.tools.debate_engine import DebateEngine

ai_debate_bp = Blueprint('ai_debate', __name__, url_prefix='/api/tools/ai-debate')

# ========== API Key 配置 ==========
# 从环境变量读取各服务商的 API Key
QWEN_API_KEY = os.environ.get('QWEN_API_KEY', os.environ.get('DASHSCOPE_API_KEY', ''))
DOUBAO_API_KEY = os.environ.get('DOUBAO_API_KEY', '')
KIMI_API_KEY = os.environ.get('KIMI_API_KEY', '')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

# ========== LLM 服务商配置 ==========
LLM_PROVIDERS = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": QWEN_API_KEY,
        "model": "qwen-plus",
    },
    "qwen_max": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": QWEN_API_KEY,
        "model": "qwen-max",
    },
    "doubao": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": DOUBAO_API_KEY,
        "model": "doubao-1.5-pro-32k-250115",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": KIMI_API_KEY,
        "model": "kimi-k2-turbo-preview",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key": DEEPSEEK_API_KEY,
        "model": "deepseek-chat",
    },
}

# ========== 辩手阵容 ==========
DEBATERS = [
    {
        "id": "pro_1",
        "name": "千问·论道",
        "side": "pro",
        "role": "一辩",
        "provider": "qwen",
        "personality": "你是立论型辩手，风格类似黄执中。擅长在开篇就抢占定义权和价值高地，用严密的三段论构建论证框架。"
                       "说话铿锵有力，喜欢用「我方的第一个论点是……」「让我们回到问题的本质」这样的结构化表达。"
                       "善于引用社会学、经济学理论和权威数据来支撑观点。",
        "voice": "zh-CN-YunxiNeural",
    },
    {
        "id": "pro_2",
        "name": "豆包·善辩",
        "side": "pro",
        "role": "二辩",
        "provider": "doubao",
        "personality": "你是攻辩型辩手，风格类似陈铭。擅长用生动的类比和真实案例把抽象问题具象化，让听众产生共鸣。"
                       "质询时善于设置连环问题，引导对方进入预设的逻辑陷阱。"
                       "语言富有感染力，善用排比和反问制造节奏感，经常说「我想请对方辩友回答一个简单的问题」。",
        "voice": "zh-CN-XiaoyiNeural",
    },
    {
        "id": "con_1",
        "name": "Kimi·锐评",
        "side": "con",
        "role": "一辩",
        "provider": "kimi",
        "personality": "你是反驳型辩手，风格类似马薇薇。语速快、攻击性强，擅长抓住对方论述中的逻辑漏洞穷追猛打。"
                       "喜欢用归谬法——「按照对方辩友的逻辑，那岂不是……」来暴露对方的荒谬之处。"
                       "自由辩论时存在感极强，善于打断对方节奏，用短促有力的反驳制造压迫感。",
        "voice": "zh-CN-YunjianNeural",
    },
    {
        "id": "con_2",
        "name": "深思·明辨",
        "side": "con",
        "role": "二辩",
        "provider": "deepseek",
        "personality": "你是思辨型辩手，风格类似庞颖。说话沉稳有条理，擅长从哲学和社会学的底层逻辑出发，"
                       "对辩题中的核心概念进行深度拆解。善于用「我们不妨换一个角度来看这个问题」引入全新视角。"
                       "总结陈词时能把全场交锋升华到价值层面，用温和而坚定的语气说服裁判。",
        "voice": "zh-CN-XiaoxiaoNeural",
    },
]

# ========== 裁判配置 ==========
JUDGE_CONFIG = {
    "provider": "qwen_max",
    "voice": "zh-CN-YunyangNeural",
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


def generate_sse_event(event_type, data):
    """生成 SSE 事件格式"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_debate_full(topic, pro_position, con_position, rounds):
    """完整辩论流程 - 使用 DebateEngine"""
    if not HAS_OPENAI:
        yield generate_sse_event('error', {'message': '服务器缺少 openai 库'})
        return
    
    # 检查 API Key 配置
    missing_keys = []
    for key, provider in LLM_PROVIDERS.items():
        if not provider['api_key']:
            missing_keys.append(key)
    
    if missing_keys:
        yield generate_sse_event('error', {
            'message': f'以下服务商的 API Key 未配置: {", ".join(missing_keys)}'
        })
        return
    
    try:
        # 创建辩论引擎
        params = {
            "max_words": 200,
            "free_debate_rounds": rounds,
            "debate_time_limit": 600,  # 10分钟
            "judge_config": JUDGE_CONFIG,
        }
        
        engine = DebateEngine(
            topic=topic,
            pro_position=pro_position,
            con_position=con_position,
            debaters=DEBATERS,
            providers=LLM_PROVIDERS,
            params=params
        )
        
        # 初始化客户端
        engine.init_clients()
        
        # 运行辩论并转换事件格式
        for event in engine.run_debate():
            event_type = event.get("event")
            data = event.get("data", {})
            
            # 转换事件格式以适配前端
            if event_type == "phase":
                yield generate_sse_event('stage', {
                    'stage': data.get('phase', ''),
                    'desc': data.get('description', '')
                })
            
            elif event_type == "speaker":
                # 辩手开始发言
                pass  # 前端不需要这个事件
            
            elif event_type == "token":
                # 流式输出 token
                speaker_id = data.get('speaker_id', '')
                debater = next((d for d in DEBATERS if d['id'] == speaker_id), None)
                if debater:
                    side_name = '正方' if debater['side'] == 'pro' else '反方'
                    yield generate_sse_event('chunk', {
                        'speaker': debater['name'],
                        'role': f'{side_name}{debater["role"]}',
                        'side': debater['side'],
                        'text': data.get('token', '')
                    })
            
            elif event_type == "turn_end":
                # 一轮发言结束
                speaker_id = data.get('speaker_id', '')
                debater = next((d for d in DEBATERS if d['id'] == speaker_id), None)
                if debater:
                    side_name = '正方' if debater['side'] == 'pro' else '反方'
                    yield generate_sse_event('message', {
                        'speaker': debater['name'],
                        'role': f'{side_name}{debater["role"]}',
                        'side': debater['side'],
                        'content': data.get('full_text', '')
                    })
            
            elif event_type == "judge":
                # 裁判点评
                content = data.get('content', '')
                # 从裁判点评中提取获胜方
                winner = '正方' if '正方' in content and ('获胜' in content or '胜出' in content) else '反方'
                yield generate_sse_event('result', {
                    'winner': winner,
                    'comment': content
                })
            
            elif event_type == "debate_end":
                # 辩论结束
                pass
            
            time.sleep(0.01)  # 避免发送过快
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield generate_sse_event('error', {
            'message': f'辩论过程出错: {str(e)}'
        })


@ai_debate_bp.route('/start', methods=['POST'])
@require_token
def start_debate():
    """
    开始辩论赛 - 完整版
    
    请求体:
    {
        "topic": "人工智能的发展利大于弊",
        "pro_position": "人工智能的发展利大于弊",
        "con_position": "人工智能的发展弊大于利",
        "rounds": 4
    }
    
    响应: SSE 流
    event: stage
    data: {"stage": "开篇立论", "desc": "双方一辩阐述观点"}
    
    event: chunk
    data: {"speaker": "千问·论道", "role": "正方一辩", "side": "pro", "text": "..."}
    
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
    
    # 自动生成正反方立场
    pro_position = data.get('pro_position', topic)
    con_position = data.get('con_position', f'反对：{topic}')
    
    if rounds < 2 or rounds > 8:
        rounds = 4
    
    def generate():
        yield from stream_debate_full(topic, pro_position, con_position, rounds)
    
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
    for config in DEBATERS:
        debaters.append({
            'id': config['id'],
            'name': config['name'],
            'side': config['side'],
            'role': config['role'],
            'model': LLM_PROVIDERS[config['provider']]['model']
        })
    return jsonify({'debaters': debaters})


@ai_debate_bp.route('/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    providers_info = {}
    for key, prov in LLM_PROVIDERS.items():
        providers_info[key] = {
            'base_url': prov['base_url'],
            'model': prov['model'],
            'has_key': bool(prov.get('api_key', '').strip()),
        }
    
    return jsonify({
        'providers': providers_info,
        'debaters': DEBATERS,
        'judge': JUDGE_CONFIG
    })

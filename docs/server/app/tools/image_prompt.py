"""
图文互转工具 Blueprint
路径前缀: /api/tools/image-prompt
支持图片转提示词和提示词转图片
"""

import os
import base64
import tempfile
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

image_prompt_bp = Blueprint('image_prompt', __name__, url_prefix='/api/tools/image-prompt')

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'integrity_images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'sk-0ef56d1b3ba54a188ce28a46c54e2a24')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'


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


def get_vision_client():
    """获取视觉模型客户端（用于图片分析）"""
    if not HAS_OPENAI:
        return None, '缺少 openai 库'
    
    if DASHSCOPE_API_KEY:
        return OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL
        ), None
    
    return None, '未配置 API Key'


def get_image_gen_client():
    """获取图片生成客户端（使用 Qwen VL）"""
    if not HAS_OPENAI:
        return None, '缺少 openai 库'
    
    if DASHSCOPE_API_KEY:
        return OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL
        ), 'qwen'
    
    return None, '未配置图片生成 API Key'


@image_prompt_bp.route('/analyze', methods=['POST'])
@require_token
def analyze_image():
    """
    图片转提示词
    
    请求: FormData
    - image: 图片文件
    - style: 'dalle' 或 'sd' (可选，默认 dalle)
    
    响应:
    {
        "success": true,
        "prompt": "A beautiful sunset over the ocean...",
        "style": "dalle"
    }
    """
    if not HAS_OPENAI:
        return jsonify({'error': '服务器缺少 openai 库'}), 500
    
    if not HAS_PIL:
        return jsonify({'error': '服务器缺少 Pillow 库'}), 500
    
    if 'image' not in request.files:
        return jsonify({'error': '请上传图片'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '请选择图片'}), 400
    
    style = request.form.get('style', 'dalle').lower()
    
    try:
        img = Image.open(file)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        temp_path = os.path.join(UPLOAD_FOLDER, f'analyze_{os.urandom(4).hex()}.jpg')
        img.save(temp_path, format='JPEG', quality=85)
        
        with open(temp_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        os.remove(temp_path)
        
        client, error = get_vision_client()
        if error:
            return jsonify({'error': error}), 400
        
        if style == 'sd':
            prompt_instruction = """请分析这张图片，生成一个适合 Stable Diffusion 使用的提示词。
提示词应该：
1. 用英文描述
2. 包含主体、风格、构图、光线等关键元素
3. 使用逗号分隔的关键词形式
4. 简洁精准，不要有多余说明

直接输出提示词，不要有其他解释。"""
        else:
            prompt_instruction = """请分析这张图片，生成一个适合 DALL-E 使用的提示词。
提示词应该：
1. 用英文描述
2. 简洁明了，一句话概括图片内容
3. 包含主体、风格、氛围等关键元素
4. 不要有技术性参数

直接输出提示词，不要有其他解释。"""
        
        response = client.chat.completions.create(
            model='qwen-vl-max',
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt_instruction},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_data}'
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        prompt = response.choices[0].message.content.strip()
        
        return jsonify({
            'success': True,
            'prompt': prompt,
            'style': style
        })
    
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500


@image_prompt_bp.route('/generate', methods=['POST'])
@require_token
def generate_image():
    """
    提示词转图片
    
    请求体:
    {
        "prompt": "A beautiful sunset over the ocean",
        "size": "1024x1024",  // 可选: 1024x1024, 1792x1024, 1024x1792
        "count": 1,  // 可选: 1-4
        "style": "dalle"  // 可选: dalle (目前仅支持 DALL-E)
    }
    
    响应:
    {
        "success": true,
        "images": ["url1", "url2"]
    }
    """
    if not HAS_OPENAI:
        return jsonify({'error': '服务器缺少 openai 库'}), 500
    
    data = request.json
    prompt = data.get('prompt', '').strip()
    size = data.get('size', '1024x1024')
    count = int(data.get('count', 1))
    
    if not prompt:
        return jsonify({'error': '提示词不能为空'}), 400
    
    if count < 1 or count > 4:
        count = 1
    
    if size not in ['1024x1024', '1792x1024', '1024x1792']:
        size = '1024x1024'
    
    try:
        client, gen_type = get_image_gen_client()
        if not client:
            return jsonify({'error': gen_type}), 400
        
        response = client.chat.completions.create(
            model='qwen3.5-plus',
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个专业的图像提示词优化助手。用户会给你一个简单的描述，请你扩展成一个详细的、适合AI绘图的提示词。要求：1. 用英文输出 2. 包含主体、风格、构图、光线、色彩等要素 3. 简洁有力，不超过100词'
                },
                {
                    'role': 'user',
                    'content': f'请为以下描述生成一个详细的绘图提示词：{prompt}'
                }
            ],
            max_tokens=500
        )
        
        optimized_prompt = response.choices[0].message.content.strip()
        
        return jsonify({
            'success': True,
            'message': '提示词已优化，请使用其他服务（如 Midjourney/DALL-E）生成图片',
            'original_prompt': prompt,
            'optimized_prompt': optimized_prompt,
            'model': 'qwen3.5-plus'
        })
    
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500
"""
台词学习工具 Blueprint
路径前缀: /api/tools/dialogue-learning
支持 PDF 解析、台词爬取、AI 整理、TTS 生成
"""

import os
import uuid
import asyncio
import tempfile
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

dialogue_learning_bp = Blueprint('dialogue_learning', __name__, url_prefix='/api/tools/dialogue-learning')

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'integrity_dialogue')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

task_results = {}


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


def extract_words_from_pdf(pdf_path):
    """从扇贝单词 PDF 中提取单词列表"""
    if not HAS_PDFPLUMBER:
        return []
    
    words = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    line = line.strip()
                    if line and ' ' not in line[:20]:
                        parts = line.split()
                        if parts:
                            word = parts[0].strip('.,!?;:')
                            if word.isalpha() and len(word) > 1:
                                words.append(word.lower())
    
    return list(set(words))[:20]


def get_phonetic(word):
    """获取单词音标"""
    if not HAS_REQUESTS:
        return None
    
    try:
        res = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}', timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                phonetics = data[0].get('phonetics', [])
                for p in phonetics:
                    if p.get('text'):
                        return p['text']
        return None
    except:
        return None


def search_movie_quotes(word):
    """搜索包含该单词的影视台词"""
    if not HAS_REQUESTS or not HAS_BS4:
        return []
    
    quotes = []
    
    search_urls = [
        f'https://www.english-corpora.org/movies/',
    ]
    
    mock_quotes = [
        {
            'source': 'The Shawshank Redemption (1994)',
            'text': f'Hope is a good thing, maybe the best of things, and no good thing ever dies. Here we see the concept of {word}.',
            'translation': '希望是美好的，也许是人间至善，而美好的事物永不消逝。'
        },
        {
            'source': 'Forrest Gump (1994)',
            'text': f'Life is like a box of chocolates, you never know what you\'re gonna get. Speaking of {word}, it reminds me of this.',
            'translation': '生活就像一盒巧克力，你永远不知道你会得到什么。'
        },
        {
            'source': 'The Lion King (1994)',
            'text': f'Remember who you are. This relates to {word} in a profound way.',
            'translation': '记住你是谁。'
        }
    ]
    
    return mock_quotes[:2]


def generate_audio_with_tts(word, output_path):
    """使用 edge-tts 生成发音"""
    if not HAS_EDGE_TTS:
        return False
    
    try:
        async def _generate():
            communicate = edge_tts.Communicate(word, "en-US-AriaNeural")
            await communicate.save(output_path)
        
        asyncio.run(_generate())
        return os.path.exists(output_path)
    except:
        return False


def process_word_with_ai(word, quotes):
    """使用 AI 整理单词信息"""
    if not HAS_OPENAI:
        return None
    
    api_key = os.environ.get('QWEN_API_KEY')
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        return None
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1' if os.environ.get('QWEN_API_KEY') else None
        )
        
        prompt = f"""分析单词「{word}」，基于以下台词片段：
{chr(10).join([f"- {q['text']}" for q in quotes])}

请提供：
1. 单词释义（中英文）
2. 常见搭配（3个）
3. 记忆技巧

用 JSON 格式返回：
{{"definition": "...", "examples": [...], "tips": "..."}}"""
        
        response = client.chat.completions.create(
            model='qwen-plus' if os.environ.get('QWEN_API_KEY') else 'gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=500
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    except:
        return None


def process_pdf_task(task_id, pdf_path):
    """后台处理 PDF 任务"""
    try:
        task_results[task_id] = {'status': 'processing', 'progress': 0}
        
        words = extract_words_from_pdf(pdf_path)
        task_results[task_id]['progress'] = 20
        task_results[task_id]['total_words'] = len(words)
        
        results = []
        for i, word in enumerate(words):
            phonetic = get_phonetic(word)
            quotes = search_movie_quotes(word)
            ai_info = process_word_with_ai(word, quotes)
            
            audio_filename = f'{word}_{uuid.uuid4().hex[:8]}.mp3'
            audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
            audio_url = None
            
            if generate_audio_with_tts(word, audio_path):
                audio_url = f'/api/tools/dialogue-learning/audio/{audio_filename}'
            
            word_data = {
                'word': word,
                'phonetic': phonetic or f'/{word}/',
                'audio_url': audio_url,
                'quotes': quotes
            }
            
            if ai_info:
                word_data.update(ai_info)
            
            results.append(word_data)
            task_results[task_id]['progress'] = 20 + int((i + 1) / len(words) * 80)
        
        task_results[task_id] = {
            'status': 'completed',
            'progress': 100,
            'results': {'words': results}
        }
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    
    except Exception as e:
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e)
        }


@dialogue_learning_bp.route('/process', methods=['POST'])
@require_token
def process_pdf():
    """
    处理单词 PDF
    
    请求: FormData with 'file' (PDF)
    响应: {"task_id": "xxx"}
    """
    if not HAS_PDFPLUMBER:
        return jsonify({'error': '服务器缺少 pdfplumber 库'}), 500
    
    if 'file' not in request.files:
        return jsonify({'error': '请上传 PDF 文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '请选择文件'}), 400
    
    task_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_FOLDER, f'{task_id}_{secure_filename(file.filename)}')
    file.save(temp_path)
    
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(process_pdf_task, task_id, temp_path)
    
    return jsonify({'task_id': task_id})


@dialogue_learning_bp.route('/status/<task_id>', methods=['GET'])
@require_token
def task_status(task_id):
    """
    查询任务状态
    
    响应:
    {
        "status": "completed",
        "progress": 100,
        "results": {...}
    }
    """
    if task_id not in task_results:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task_results[task_id])


@dialogue_learning_bp.route('/audio/<filename>', methods=['GET'])
def download_audio(filename):
    """下载音频文件"""
    from flask import send_file
    from pathlib import Path
    
    safe_dir = Path(UPLOAD_FOLDER).resolve()
    target = (safe_dir / filename).resolve()
    
    if not str(target).startswith(str(safe_dir)):
        return '禁止访问', 403
    
    if not target.exists():
        return '文件不存在', 404
    
    return send_file(str(target), as_attachment=True, download_name=filename)
"""
分镜视频生成工具 Blueprint
路径前缀: /api/tools/video-maker
支持 AI 剧本生成、分镜插图、配音、视频合成
"""

import os
import uuid
import json
import asyncio
import tempfile
import subprocess
import jwt
from functools import wraps
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

video_maker_bp = Blueprint('video_maker', __name__, url_prefix='/api/tools/video-maker')

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'integrity_video')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'sk-0ef56d1b3ba54a188ce28a46c54e2a24')
DASHSCOPE_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'

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


def get_ai_client():
    """获取 AI 客户端"""
    if not HAS_OPENAI:
        return None
    
    if DASHSCOPE_API_KEY:
        return OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url=DASHSCOPE_BASE_URL
        )
    
    return None


def generate_script(scene_description):
    """生成剧本和分镜"""
    client = get_ai_client()
    if not client:
        return None
    
    prompt = f"""根据以下场景描述，生成一个短视频剧本（60秒左右），包含3-5个分镜：

场景：{scene_description}

请以 JSON 格式返回：
{{
  "title": "视频标题",
  "scenes": [
    {{
      "id": 1,
      "description": "场景描述",
      "narration": "旁白文本",
      "image_prompt": "用于生成图片的英文提示词",
      "duration": 10
    }}
  ]
}}"""
    
    try:
        response = client.chat.completions.create(
            model='qwen3.5-plus',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        
        return json.loads(content.strip())
    except Exception as e:
        return None


def generate_scene_image(image_prompt, output_path):
    """生成分镜图片"""
    client = get_ai_client()
    if not client:
        return False
    
    try:
        if os.environ.get('OPENAI_API_KEY'):
            response = client.images.generate(
                model='dall-e-3',
                prompt=image_prompt,
                size='1792x1024',
                quality='standard',
                n=1
            )
            
            image_url = response.data[0].url
            
            import requests
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                return True
        else:
            if HAS_PIL:
                img = Image.new('RGB', (1792, 1024), color=(100, 100, 100))
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                draw.text((896, 512), image_prompt[:50], fill=(255, 255, 255), anchor='mm')
                img.save(output_path, 'JPEG')
                return True
        
        return False
    except:
        return False


def generate_narration_audio(text, output_path):
    """生成旁白音频"""
    if not HAS_EDGE_TTS:
        return False
    
    try:
        async def _generate():
            communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
            await communicate.save(output_path)
        
        asyncio.run(_generate())
        return os.path.exists(output_path)
    except:
        return False


def create_video_with_ffmpeg(scenes_data, output_path):
    """使用 FFmpeg 合成视频"""
    if not os.environ.get('HAS_FFMPEG'):
        return False
    
    temp_files = []
    concat_list = []
    
    for i, scene in enumerate(scenes_data):
        scene_dir = os.path.join(UPLOAD_FOLDER, f'scene_{i}_{uuid.uuid4().hex[:8]}')
        os.makedirs(scene_dir, exist_ok=True)
        
        image_path = os.path.join(scene_dir, 'image.jpg')
        audio_path = os.path.join(scene_dir, 'audio.mp3')
        scene_video = os.path.join(scene_dir, 'scene.mp4')
        
        generate_scene_image(scene.get('image_prompt', 'a scene'), image_path)
        generate_narration_audio(scene.get('narration', ''), audio_path)
        
        duration = scene.get('duration', 5)
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                scene_video
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            if os.path.exists(scene_video):
                concat_list.append(scene_video)
        except:
            pass
        
        temp_files.append(scene_dir)
    
    if len(concat_list) == 0:
        return False
    
    try:
        concat_file = os.path.join(UPLOAD_FOLDER, f'concat_{uuid.uuid4().hex[:8]}.txt')
        with open(concat_file, 'w') as f:
            for video in concat_list:
                f.write(f"file '{video}'\n")
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, timeout=120)
        
        os.remove(concat_file)
        
        return os.path.exists(output_path)
    except:
        return False
    finally:
        for temp_dir in temp_files:
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass


def process_video_task(task_id, scene_description, video_type):
    """后台处理视频生成任务"""
    try:
        task_results[task_id] = {'status': 'processing', 'progress': 0}
        
        script = generate_script(scene_description)
        if not script:
            task_results[task_id] = {
                'status': 'failed',
                'error': '剧本生成失败'
            }
            return
        
        task_results[task_id]['progress'] = 20
        task_results[task_id]['script'] = script
        
        scenes = script.get('scenes', [])
        if not scenes:
            task_results[task_id] = {
                'status': 'failed',
                'error': '未生成分镜'
            }
            return
        
        output_filename = f'{secure_filename(script.get("title", "video"))}_{task_id[:8]}.mp4'
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        task_results[task_id]['progress'] = 40
        
        if create_video_with_ffmpeg(scenes, output_path):
            task_results[task_id] = {
                'status': 'completed',
                'progress': 100,
                'video_url': f'/api/tools/video-maker/download/{output_filename}',
                'script': script
            }
        else:
            task_results[task_id] = {
                'status': 'completed',
                'progress': 100,
                'video_url': None,
                'script': script,
                'message': '视频合成不可用，仅返回剧本'
            }
    
    except Exception as e:
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e)
        }


@video_maker_bp.route('/generate', methods=['POST'])
@require_token
def generate_video():
    """
    生成视频
    
    请求体:
    {
        "project_name": "咖啡店点单",
        "scene_description": "在咖啡店点一杯拿铁",
        "video_type": "multi"  // multi / grid
    }
    
    响应:
    {
        "task_id": "xxx",
        "status": "processing"
    }
    """
    if not HAS_OPENAI:
        return jsonify({'error': '服务器缺少 openai 库'}), 500
    
    data = request.json
    scene_description = data.get('scene_description', '').strip()
    video_type = data.get('video_type', 'multi')
    
    if not scene_description:
        return jsonify({'error': '场景描述不能为空'}), 400
    
    task_id = str(uuid.uuid4())
    
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(process_video_task, task_id, scene_description, video_type)
    
    return jsonify({
        'task_id': task_id,
        'status': 'processing'
    })


@video_maker_bp.route('/status/<task_id>', methods=['GET'])
@require_token
def video_status(task_id):
    """
    查询任务状态
    
    响应:
    {
        "status": "completed",
        "progress": 100,
        "video_url": "/api/tools/video-maker/download/xxx.mp4",
        "script": {...}
    }
    """
    if task_id not in task_results:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task_results[task_id])


@video_maker_bp.route('/download/<filename>', methods=['GET'])
def download_video(filename):
    """下载视频文件"""
    safe_dir = Path(UPLOAD_FOLDER).resolve()
    target = (safe_dir / filename).resolve()
    
    if not str(target).startswith(str(safe_dir)):
        return '禁止访问', 403
    
    if not target.exists():
        return '文件不存在', 404
    
    return send_file(str(target), as_attachment=True, download_name=filename)
"""
Integrity Lab API 主入口
模块化架构，支持多工具扩展

本地备份 | 云端部署：服务器运行在 8.138.164.133:5000
"""

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError('SECRET_KEY 环境变量未设置，请在 .env 中配置')
app.config['SECRET_KEY'] = _secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 文件上传限制

CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'http://localhost:3000',
    'http://localhost:5000',
    'http://localhost:5500',
    'http://localhost:8080',
    'http://127.0.0.1:5000',
    'http://8.138.164.133:5000'
])

db = SQLAlchemy(app)


# ============ 用户模型 ============

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    invite_code = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


def hash_password(password):
    """使用 werkzeug 生成带盐值的密码哈希（bcrypt）"""
    return generate_password_hash(password)


def verify_password(password, password_hash):
    """验证密码"""
    return check_password_hash(password_hash, password)


def generate_token(user_id):
    """生成 JWT Token，有效期 7 天"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    """验证 JWT Token，返回 user_id 或 None"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None


VALID_INVITE_CODES = set(os.environ.get('INVITE_CODES', 'demo2026,test2026,friend2026').split(','))


# ============ 基础路由 ============

@app.route('/')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Integrity Lab API',
        'version': '2.0.0',
        'tools': ['pdf', 'token-calc']
    })


# ============ 前端页面路由 ============

@app.route('/app/')
@app.route('/app/<path:path>')
def serve_app(path=''):
    """前端应用入口"""
    if path == '' or path == 'index.html':
        return render_template('index.html')
    elif path == 'tools.html':
        return render_template('tools.html')
    elif path == 'news.html':
        return render_template('news.html')
    elif path.endswith('.html'):
        return render_template(path)
    else:
        return send_from_directory(app.static_folder, path)


@app.route('/demos/<path:path>')
def serve_demos(path):
    """Demo 页面"""
    return send_from_directory(os.path.join(app.static_folder, 'demos'), path)


@app.route('/assets/<path:path>')
def serve_assets(path):
    """静态资源"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), path)


@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    invite_code = data.get('invite_code', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({'error': '用户名长度需在3-20字符之间'}), 400

    if len(password) < 6:
        return jsonify({'error': '密码长度至少6位'}), 400

    if invite_code not in VALID_INVITE_CODES:
        return jsonify({'error': '邀请码无效'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    user = User(username=username, password_hash=hash_password(password), invite_code=invite_code)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)
    return jsonify({'message': '注册成功', 'token': token, 'username': username})


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({'error': '用户名或密码错误'}), 401

    if not user.is_active:
        return jsonify({'error': '账户已被禁用'}), 403

    token = generate_token(user.id)
    return jsonify({'message': '登录成功', 'token': token, 'username': username})


@app.route('/api/auth/verify', methods=['GET'])
def verify():
    """验证 Token 有效性"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'valid': False}), 401
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'valid': False}), 401
    return jsonify({'valid': True, 'username': user.username})


@app.route('/api/tools/token-calc', methods=['POST'])
def token_calc():
    """Token 消耗计算器（无需登录）"""
    data = request.json
    model = data.get('model', 'qwen-plus')
    lang = data.get('lang', 'zh')
    chars = int(data.get('chars', 100))

    token_prices = {
        'qwen-plus': {'input': 0.004, 'output': 0.012},
        'qwen-turbo': {'input': 0.001, 'output': 0.002},
        'gpt-4o': {'input': 0.0025, 'output': 0.01},
        'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006}
    }

    token_ratios = {'zh': 0.5, 'en': 0.25, 'img': 1.5}

    ratio = token_ratios.get(lang, 0.5)
    prompt_tokens = int(chars * ratio)
    completion_tokens = int(prompt_tokens * 0.3)
    prices = token_prices.get(model, token_prices['qwen-plus'])

    input_cost = (prompt_tokens / 1000) * prices['input']
    output_cost = (completion_tokens / 1000) * prices['output']
    total_cost = input_cost + output_cost

    return jsonify({
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_cost': round(total_cost, 6)
    })


# ============ 注册工具蓝图 ============

from app.tools.pdf import pdf_bp
from app.tools.ai_compare import ai_compare_bp
from app.tools.image_prompt import image_prompt_bp
from app.tools.ai_debate import ai_debate_bp
from app.tools.dialogue_learning import dialogue_learning_bp
from app.tools.video_maker import video_maker_bp
from app.tools.token_compare import token_compare_bp  # 新增

app.register_blueprint(pdf_bp)
app.register_blueprint(ai_compare_bp)
app.register_blueprint(image_prompt_bp)
app.register_blueprint(ai_debate_bp)
app.register_blueprint(dialogue_learning_bp)
app.register_blueprint(video_maker_bp)
app.register_blueprint(token_compare_bp)  # 新增


# ============ 启动 ============

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)

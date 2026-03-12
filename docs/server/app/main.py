from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import jwt
import datetime
import os
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'integrity-lab-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'http://localhost:*',
    'http://127.0.0.1:*'
])

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    invite_code = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

VALID_INVITE_CODES = set(os.environ.get('INVITE_CODES', 'demo2026,test2026').split(','))

@app.route('/')
def health():
    return jsonify({'status': 'ok', 'service': 'Integrity Lab API', 'version': '1.0.0'})

@app.route('/api/auth/register', methods=['POST'])
def register():
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
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or user.password_hash != hash_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'error': '账户已被禁用'}), 403
    
    token = generate_token(user.id)
    return jsonify({'message': '登录成功', 'token': token, 'username': username})

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'valid': False}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({'valid': False}), 401
    return jsonify({'valid': True, 'username': user.username})

@app.route('/api/tools/token-calc', methods=['POST'])
def token_calc():
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

@app.route('/api/tools/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'qwen-plus')
    
    import dashscope
    from dashscope import Generation
    
    dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY')
    
    try:
        response = Generation.call(
            model=model,
            prompt=message,
            max_tokens=500
        )
        return jsonify({'response': response.output.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)
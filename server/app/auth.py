"""
认证模块 - JWT Token 验证装饰器
"""

from functools import wraps
from flask import request, jsonify, current_app
import jwt


def verify_token(token):
    """验证 JWT Token，返回 user_id 或 None"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload.get('user_id')
    except:
        return None


def token_required(f):
    """
    需要登录的 API 装饰器
    用法:
        @pdf_bp.route('/merge', methods=['POST'])
        @token_required
        def api_merge_pdfs():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'success': False, 'message': '请先登录', 'code': 'UNAUTHORIZED'}), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'success': False, 'message': 'Token 无效或已过期', 'code': 'INVALID_TOKEN'}), 401

        # 将 user_id 注入到 request 中，方便后续使用
        request.user_id = user_id
        return f(*args, **kwargs)

    return decorated


def token_optional(f):
    """
    可选登录的 API 装饰器（登录后有额外功能）
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if token:
            user_id = verify_token(token)
            request.user_id = user_id
        else:
            request.user_id = None

        return f(*args, **kwargs)

    return decorated

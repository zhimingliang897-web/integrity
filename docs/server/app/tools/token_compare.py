"""
Token对比工具 - 计算多语言文本在不同模型下的Token消耗
"""
from flask import Blueprint, request, jsonify
import tiktoken
import os
from pathlib import Path

# 创建蓝图
token_compare_bp = Blueprint('token_compare', __name__, url_prefix='/api/tools/token-compare')

# Token价格配置（每1K tokens，单位：元）
TOKEN_PRICING = {
    'qwen-turbo': {'input': 0.0003, 'output': 0.0006},
    'qwen-plus': {'input': 0.0008, 'output': 0.002},
    'qwen-max': {'input': 0.002, 'output': 0.006},
    'qwen-vl-plus': {'input': 0.002, 'output': 0.006},
    'gpt-4o': {'input': 0.0175, 'output': 0.07},
    'gpt-4o-mini': {'input': 0.0025, 'output': 0.01},
    'gpt-4-turbo': {'input': 0.07, 'output': 0.14}
}

# 模型对应的编码器
ENCODERS = {
    'qwen-turbo': 'cl100k_base',
    'qwen-plus': 'cl100k_base',
    'qwen-max': 'cl100k_base',
    'qwen-vl-plus': 'cl100k_base',
    'gpt-4o': 'o200k_base',
    'gpt-4o-mini': 'o200k_base',
    'gpt-4-turbo': 'cl100k_base'
}


def count_tokens(text: str, encoder_name: str = 'cl100k_base') -> int:
    """计算文本的token数量"""
    try:
        encoding = tiktoken.get_encoding(encoder_name)
        return len(encoding.encode(text))
    except Exception as e:
        # 如果失败，使用粗略估算（中文字符数 * 2 + 英文单词数）
        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        return chinese_chars * 2 + english_words + 2  # +2 for special tokens


def estimate_completion_tokens(text: str, language: str = 'zh') -> int:
    """估算输出的token数量"""
    # 假设输出是输入的2-3倍（详细回答）
    base_tokens = len(text)
    if language == 'zh':
        # 中文输出通常比输入更详细
        return int(base_tokens * 2.5)
    else:
        return int(base_tokens * 2)


@token_compare_bp.route('/analyze', methods=['POST'])
def analyze_tokens():
    """
    分析文本在多个模型下的Token消耗
    
    请求体：
    {
        "text": "要分析的文本",
        "language": "zh" | "en" | "image",
        "models": ["qwen-turbo", "qwen-plus", ...]
    }
    
    响应：
    {
        "results": [
            {
                "model": "qwen-turbo",
                "prompt_tokens": 120,
                "completion_tokens": 300,
                "total_tokens": 420,
                "estimated_cost": 0.002
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '请求体为空'}), 400
        
        text = data.get('text', '')
        language = data.get('language', 'zh')
        models = data.get('models', [])
        
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        if not models:
            models = ['qwen-turbo', 'qwen-plus']
        
        # 特殊处理图片模式
        if language == 'image':
            # 图片模式只支持 qwen-vl-plus
            models = ['qwen-vl-plus']
        
        results = []
        
        for model in models:
            if model not in TOKEN_PRICING:
                continue
            
            # 获取编码器
            encoder_name = ENCODERS.get(model, 'cl100k_base')
            
            # 计算输入tokens
            prompt_tokens = count_tokens(text, encoder_name)
            
            # 计算输出tokens（估算）
            completion_tokens = estimate_completion_tokens(text, language)
            
            # 总tokens
            total_tokens = prompt_tokens + completion_tokens
            
            # 计算费用
            pricing = TOKEN_PRICING[model]
            input_cost = (prompt_tokens / 1000) * pricing['input']
            output_cost = (completion_tokens / 1000) * pricing['output']
            total_cost = input_cost + output_cost
            
            results.append({
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'estimated_cost': round(total_cost, 6)
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        import traceback
        print(f"Token对比分析错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'分析失败: {str(e)}'
        }), 500


@token_compare_bp.route('/models', methods=['GET'])
def get_supported_models():
    """获取支持的模型列表"""
    return jsonify({
        'success': True,
        'models': list(TOKEN_PRICING.keys()),
        'pricing': TOKEN_PRICING
    })


# 如果直接运行此文件进行测试
if __name__ == '__main__':
    # 测试
    test_text = "你好，这是一个测试文本。Hello, this is a test text."
    print(f"测试文本: {test_text}")
    
    for model in ['qwen-turbo', 'qwen-plus', 'gpt-4o']:
        encoder_name = ENCODERS.get(model, 'cl100k_base')
        tokens = count_tokens(test_text, encoder_name)
        print(f"{model}: {tokens} tokens")
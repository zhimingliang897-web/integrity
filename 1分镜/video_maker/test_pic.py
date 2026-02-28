"""
test_pic.py — 测试 qwen-image-max 图片生成 API
用法: python test_pic.py

依赖:
  pip install requests openai
环境变量:
  set DASHSCOPE_API_KEY=你的API密钥
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================

# 设置 API 基础地址
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# DashScope API 端点
DASHSCOPE_MULTIMODAL_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
DASHSCOPE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

# 如果没配置环境变量，尝试从settings.json读取
if not API_KEY:
    try:
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                API_KEY = settings.get("api_key", "")
                print(f"[INFO] 从 settings.json 加载 API Key")
    except:
        pass

if not API_KEY:
    print("[错误] 请设置环境变量 DASHSCOPE_API_KEY 或在 settings.json 中配置 api_key")
    print("Windows: set DASHSCOPE_API_KEY=你的API密钥")
    print("或编辑 settings.json 文件")
    sys.exit(1)

print(f"[INFO] 使用 API Key: {API_KEY[:10]}...")


def _dashscope_request(url, data=None, method="POST", timeout=120):
    """通用 DashScope API 请求函数"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    # 注意：qwen-image-max 使用 multimodal-generation，不需要 X-DashScope-Async header
    try:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_detail = e.read().decode("utf-8")
            error_json = json.loads(error_detail)
            msg = error_json.get("message", error_detail)
            code = error_json.get("code", "")
            if code:
                msg = f"{code}: {msg}"
        except:
            msg = str(e)
        print(f"  [DashScope API 错误] HTTP {e.code}: {msg}")
        return {"error": True, "code": e.code, "message": msg}
    except Exception as e:
        print(f"  [DashScope API 异常] {str(e)}")
        return {"error": True, "message": str(e)}


def generate_image(prompt_text, save_path="test_output.png"):
    """调用 qwen-image-max 生成图片"""
    
    print(f"[INFO] 正在请求 qwen-image-max 生成图片...")
    print(f"[INFO] Prompt: {prompt_text[:50]}...")
    
    # 构建请求 payload
    payload = {
        "model": "qwen-image-max",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt_text}
                    ]
                }
            ]
        },
        "parameters": {
            "size": "1024*1024",
            "n": 1,
            "prompt_extend": True,
            "watermark": False,
            "negative_prompt": "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。"
        }
    }
    
    # 1. 提交任务
    res = _dashscope_request(DASHSCOPE_MULTIMODAL_API_URL, payload)
    
    # 2. 处理同步返回结果（qwen-image-max 可能直接返回）
    if "choices" in res.get("output", {}):
        print("[INFO] 任务即时生成成功！")
        try:
            content_items = res["output"]["choices"][0]["message"]["content"]
            for item in content_items:
                if "image" in item:
                    img_url = item["image"]
                    print(f"[INFO] 图片URL: {img_url}")
                    # 下载图片
                    urllib.request.urlretrieve(img_url, save_path)
                    print(f"[SUCCESS] 图片已保存到: {save_path}")
                    return True
        except Exception as e:
            print(f"[ERROR] 解析同步响应失败: {e}")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return False
    
    # 3. 处理异步任务（需要轮询）
    if not res or "output" not in res or "task_id" not in res["output"]:
        print(f"[ERROR] 提交任务失败: {res}")
        return False
    
    task_id = res["output"]["task_id"]
    poll_url = DASHSCOPE_TASK_URL.format(task_id=task_id)
    print(f"[INFO] 任务已提交 (ID: {task_id})，等待生成...")
    
    # 轮询等待结果
    for i in range(60):  # 最多等待 120 秒
        time.sleep(2)
        status_res = _dashscope_request(poll_url, method="GET")
        output = status_res.get("output", {})
        task_status = output.get("task_status")
        
        print(f"  [{i+1}] 状态: {task_status}")
        
        if task_status == "SUCCEEDED":
            img_url = None
            
            # 尝试解析 qwen-image-max 结构
            if "choices" in output:
                try:
                    content_items = output["choices"][0]["message"]["content"]
                    for item in content_items:
                        if "image" in item:
                            img_url = item["image"]
                            break
                except:
                    pass
            
            if img_url:
                print(f"[INFO] 图片URL: {img_url}")
                urllib.request.urlretrieve(img_url, save_path)
                print(f"[SUCCESS] 图片已保存到: {save_path}")
                return True
            else:
                print(f"[ERROR] 未找到图片URL: {output}")
                return False
                
        elif task_status == "FAILED":
            print(f"[ERROR] 任务失败: {output.get('message')}")
            return False
    
    print("[ERROR] 生成超时")
    return False


def main():
    # 测试用的 prompt
    prompt = """一副典雅庄重的对联悬挂于厅堂之中，房间是个安静古典的中式布置，桌子上放着一些青花瓷，对联上左书"义本生知人机同道善思新"，右书"通云赋智乾坤启数高志远"， 横批"智启千问"，字体飘逸，在中间挂着一幅中国风的画作，内容是岳阳楼。
    
    【风格要求】
    - 中国传统水墨画风格
    - 构图清晰，主体突出
    - 画面中绝不要出现文字、气泡
    """
    
    # 可以自定义保存路径
    save_path = "test_output.png"
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    if len(sys.argv) > 2:
        save_path = sys.argv[2]
    
    print("=" * 60)
    print("  qwen-image-max 图片生成测试")
    print("=" * 60)
    
    success = generate_image(prompt, save_path)
    
    print("=" * 60)
    if success:
        print("[完成] 图片生成成功！")
    else:
        print("[失败] 图片生成失败，请检查错误信息")
    print("=" * 60)


if __name__ == "__main__":
    main()

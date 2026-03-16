import json
import os
import argparse
from pathlib import Path
import config
import analyze

def main():
    # 解析命令行输入的文件夹路径
    parser = argparse.ArgumentParser(description="AI 自动匹配资料脚本")
    parser.add_argument("dir", nargs="?", default="input", help="指定要扫描的文件夹路径 (默认: input)")
    args = parser.parse_args()
    
    target_dir = Path(args.dir)
    
    # 检查指定的目录是否存在
    if not target_dir.exists():
        print(f"❌ 错误：指定的目录 '{target_dir}' 不存在。")
        return

    print("="*60)
    print(f"🤖 资料智能匹配向导 (当前扫描目录: {target_dir.absolute()})")
    print("正在扫描指定目录中的视频与PDF文件...")
    
    # 【核心修复】：只扫描指定的 target_dir，不额外扫描其他目录
    videos = list(target_dir.rglob("*.mp4"))
    pdfs = list(target_dir.rglob("*.pdf"))
    
    videos = list(set(videos))
    pdfs = list(set(pdfs))
    
    if not videos or not pdfs:
        print("未找到足够的 mp4 和 pdf 文件。退出。")
        return

    print(f"找到 {len(videos)} 个视频 和 {len(pdfs)} 个 PDF。")
    print("正在提取各自的关键特征...")
    
    import pdfplumber
    
    pdf_features = {}
    for p in pdfs:
        try:
            with pdfplumber.open(p) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    pdf_features[str(p)] = text[:400].replace('\n', ' ')
        except Exception as e:
            pass

    video_features = {}
    for v in videos:
        # 这里保留读取已有转录缓存的逻辑，以便大模型了解视频内容
        cache_paths = [Path(config.CACHE_DIR) / f"{v.stem}.json", Path(f"cache/3d/{v.stem}.json")]
        text = ""
        for cp in cache_paths:
            if cp.exists():
                try:
                    with open(cp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        text = " ".join([s["text"] for s in data[:5]])
                        break
                except Exception:
                    pass
        video_features[str(v)] = text[:400] if text else "（该视频目前没有缓存，建议先随便运行一次生成录音转录）"

    prompt = f"""
    你是一个课程助教。我们有一些课程视频和一些课件或论文PDF，由于文件名混乱，需要你帮我正确搭配它们。
    下面是视频前几句话的文字特征，以及 PDF 第一页的文字特征。

    【视频列表特征】：
    {json.dumps(video_features, ensure_ascii=False, indent=2)}

    【PDF列表特征】：
    {json.dumps(pdf_features, ensure_ascii=False, indent=2)}

    请为【视频列表特征】中的每一个视频，找出最适合作为其配套课件的 PPT（选1个）和补充论文 Paper（选1个，也可为空）。如果没有相关的，则填 null。
    必须仅输出一个合法的 JSON，不要输出任何额外的标记解释和 Markdown 格式符号。结构如下：
    {{
       "视频的完整路径": {{"ppt": "PPT文件的完整路径", "paper": "论文文件的完整路径或null"}},
       "下一个视频的路径": {{"ppt": "...", "paper": "..."}}
    }}
    """
    
    print("\n🧠 正在请求 Qwen AI 帮您进行深度匹配连连看...")
    system = "You are a helpful assistant. Output ONLY valid JSON."
    result = analyze._call_llm(system, prompt)
    
    try:
        # 去除大模型可能输出的多余 markdown 代码块
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0]
        if result.startswith("json"):
            result = result[4:]
            
        matchings = json.loads(result.strip())
        
        script_name = "run_matched.bat"
        with open(script_name, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("echo 开始执行 AI 自动匹配生成的任务组合...\n\n")
            for v, doc in matchings.items():
                cmd = f"python main.py \"{v}\""
                if doc.get("ppt") and doc["ppt"] != "null":
                    cmd += f" --ppt \"{doc['ppt']}\""
                if doc.get("paper") and doc["paper"] != "null":
                    cmd += f" --paper \"{doc['paper']}\""
                f.write(f"echo ===============================\n")
                f.write(f"echo 正在处理 AI 匹配的视频: {Path(v).name}...\n")
                f.write(cmd + "\n")
                f.write("if errorlevel 1 goto end\n\n")
            f.write(":end\necho 所有匹配任务执行完毕。\n")
            
        print(f"\n✅ 匹配成功！已为您生成批处理脚本：`{script_name}`。")
        print(f"您可以打开 `{script_name}` 检查 AI 搭配是否合理，确认无误后直接执行。")
        
    except Exception as e:
        print("\n❌ 解析 AI 匹配结果失败:", e)
        print("AI 原始输出内容:")
        print(result)

if __name__ == "__main__":
    main()
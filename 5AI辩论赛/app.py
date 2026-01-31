"""
Flask 主入口 — 路由 + SSE 实时推送 + 音频服务

启动: python app.py
访问: http://localhost:5000
"""

import json
import os
import queue
import threading
import time

from flask import Flask, Response, jsonify, request, render_template, send_from_directory

from config import DEBATERS, JUDGE, OUTPUT_DIR, LLM_PROVIDERS, ZH_VOICES
from debate_engine import DebateEngine
from topics import PRESET_TOPICS
from tts_engine import generate_turn_audio

app = Flask(__name__)

# 全局状态
active_debate = None        # 当前辩论引擎
debate_clients = []         # SSE 客户端队列列表
debate_status = "idle"      # idle / running / finished
export_status = "idle"      # idle / exporting / done / error
export_video_path = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/topics")
def api_topics():
    """返回预设辩题库"""
    return jsonify(PRESET_TOPICS)


@app.route("/api/debaters")
def api_debaters():
    """返回辩手阵容信息"""
    result = []
    for d in DEBATERS:
        provider = LLM_PROVIDERS[d["provider"]]
        result.append({
            "id": d["id"],
            "name": d["name"],
            "side": d["side"],
            "role": d["role"],
            "model": provider["model"],
            "voice_name": ZH_VOICES.get(d["voice"], d["voice"]),
            "personality": d["personality"],
        })
    return jsonify(result)


@app.route("/api/start", methods=["POST"])
def api_start():
    """启动辩论"""
    global active_debate, debate_status

    if debate_status == "running":
        return jsonify({"error": "辩论正在进行中"}), 400

    data = request.json
    topic = data.get("topic", "").strip()
    pro_position = data.get("pro_position", "").strip()
    con_position = data.get("con_position", "").strip()

    if not topic or not pro_position or not con_position:
        return jsonify({"error": "请填写完整的辩题和正反方立场"}), 400

    # 清理旧输出
    audio_dir = os.path.join(OUTPUT_DIR, "audio")
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            os.remove(os.path.join(audio_dir, f))

    engine = DebateEngine(topic, pro_position, con_position)
    engine.init_clients()
    active_debate = engine
    debate_status = "running"

    def run():
        global debate_status
        turn_index = 0
        try:
            for event in engine.run_debate():
                # 对于 turn_end 事件，生成 TTS 音频
                if event["event"] == "turn_end":
                    try:
                        audio_info = generate_turn_audio(
                            event["data"]["speaker_id"],
                            event["data"]["full_text"],
                            event["data"]["voice"],
                            turn_index,
                        )
                        event["data"]["audio_url"] = f"/audio/{os.path.basename(audio_info['audio_file'])}"
                        event["data"]["duration"] = audio_info["duration"]
                        turn_index += 1
                    except Exception as e:
                        print(f"[TTS错误] {e}")
                        event["data"]["audio_url"] = None

                # 对于裁判点评，也生成 TTS（裁判发言较长，截取前200字生成语音）
                elif event["event"] == "judge":
                    try:
                        short_text = event["data"]["content"][:200]
                        audio_info = generate_turn_audio(
                            "judge", short_text, event["data"]["voice"], turn_index,
                        )
                        event["data"]["audio_url"] = f"/audio/{os.path.basename(audio_info['audio_file'])}"
                        turn_index += 1
                    except Exception as e:
                        print(f"[裁判TTS错误] {e}")
                        event["data"]["audio_url"] = None

                # 推送到所有 SSE 客户端
                for q in debate_clients:
                    q.put(event)

            debate_status = "finished"
        except Exception as e:
            print(f"[辩论引擎错误] {e}")
            debate_status = "finished"
            for q in debate_clients:
                q.put({"event": "error", "data": {"message": str(e)}})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/continue", methods=["POST"])
def api_continue():
    """前端通知后端：可以继续下一步了"""
    global active_debate
    if active_debate and hasattr(active_debate, "step_event"):
        active_debate.step_event.set()
        return jsonify({"status": "continued"})
    return jsonify({"error": "No active debate"}), 400


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """强制停止辩论"""
    global active_debate, debate_status
    if active_debate:
        active_debate.stop()
        debate_status = "finished"
        return jsonify({"status": "stopped"})
    return jsonify({"status": "no active debate"})



@app.route("/api/stream")
def api_stream():
    """SSE 端点 — 实时推送辩论事件"""
    q = queue.Queue()
    debate_clients.append(q)

    def event_stream():
        try:
            while True:
                try:
                    event = q.get(timeout=300)
                except queue.Empty:
                    yield "event: ping\ndata: {}\n\n"
                    continue

                event_type = event.get("event", "message")
                data = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"

                if event_type in ("debate_end", "error"):
                    break
        finally:
            if q in debate_clients:
                debate_clients.remove(q)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/status")
def api_status():
    """查询当前状态"""
    return jsonify({
        "debate_status": debate_status,
        "export_status": export_status,
        "export_video_path": export_video_path,
    })


@app.route("/audio/<filename>")
def serve_audio(filename):
    """提供音频文件"""
    audio_dir = os.path.join(OUTPUT_DIR, "audio")
    return send_from_directory(audio_dir, filename)


@app.route("/api/export_video", methods=["POST"])
def api_export_video():
    """导出辩论视频"""
    global export_status, export_video_path

    if not active_debate or not active_debate.finished:
        return jsonify({"error": "没有已完成的辩论可导出"}), 400

    if export_status == "exporting":
        return jsonify({"error": "视频正在导出中"}), 400

    export_status = "exporting"
    export_video_path = None

    def export():
        global export_status, export_video_path
        try:
            from video_export import export_debate_video
            path = export_debate_video(
                active_debate.history, active_debate.topic,
                active_debate.pro_position, active_debate.con_position,
            )
            export_video_path = path
            export_status = "done"
        except Exception as e:
            print(f"[视频导出错误] {e}")
            export_status = "error"

    threading.Thread(target=export, daemon=True).start()
    return jsonify({"status": "exporting"})


@app.route("/api/download_video")
def download_video():
    """下载导出的视频"""
    if export_video_path and os.path.exists(export_video_path):
        directory = os.path.dirname(export_video_path)
        filename = os.path.basename(export_video_path)
        return send_from_directory(directory, filename, as_attachment=True)
    return jsonify({"error": "视频文件不存在"}), 404


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)
    print("=" * 50)
    print("  AI辩论赛 — http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

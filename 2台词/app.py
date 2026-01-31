import re
import shutil
import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, request, render_template, abort

# ---------------------------------------------------------------------------
# 项目路径
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
WORD_DIR = BASE_DIR / "word"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# 后台处理状态  {day_num: {"step": str, "error": str|None}}
# ---------------------------------------------------------------------------
processing_status: dict[int, dict] = {}


# ===========================================================================
#  Markdown 解析
# ===========================================================================

def parse_study_md(text: str) -> list[dict]:
    """将 _study.md 的固定格式解析为结构化数据."""
    sections = re.split(r"\n## ", text)
    words = []

    for sec in sections:
        sec = sec.strip()
        if not sec or sec.startswith("#"):
            continue

        lines = sec.split("\n")
        word = lines[0].strip()

        # 提取 meaning
        meaning = ""
        meaning_match = re.search(
            r"\*\*meaning:\*\*\s*(.+?)(?=\n\n|\n\*\*|\Z)", sec, re.DOTALL
        )
        if meaning_match:
            meaning = meaning_match.group(1).strip()

        # 提取 example dialogues 部分
        dialogues_part = ""
        dlg_match = re.search(
            r"\*\*example dialogues:\*\*\s*\n([\s\S]*)", sec
        )
        if dlg_match:
            dialogues_part = dlg_match.group(1).strip()

        # 解析每个引用块
        dialogues = _parse_dialogues(dialogues_part)

        words.append({
            "word": word,
            "meaning": meaning,
            "dialogues": dialogues,
        })

    return words


def _parse_dialogues(text: str) -> list[dict]:
    """把 blockquote 区域拆成多段对话."""
    if not text:
        return []

    # 按空行 + '>' 开头切分不同引用块
    blocks = re.split(r"\n\n+(?=>)", text)
    dialogues = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        bq_lines = []
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith(">"):
                line = line[1:].strip()
            if line:
                bq_lines.append(line)

        if not bq_lines:
            continue

        # 第一行通常是 **Title (Year)**
        source = ""
        content_lines = bq_lines
        first = bq_lines[0]
        if first.startswith("**") and first.endswith("**"):
            source = first.strip("* ")
            content_lines = bq_lines[1:]

        entries: list[dict] = []
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            # 中文翻译行：以 ( 或 （ 开头
            if re.match(r"^[\(（]", line):
                translation = line.strip("()（） \t")
                if entries:
                    entries[-1]["zh"] = translation
                else:
                    entries.append({"en": "", "zh": translation})
            # 注释行
            elif line.startswith("*(") or line.startswith("*("):
                if entries:
                    entries[-1]["note"] = line.strip("* ")
            else:
                # 去掉 A: / B: 前缀
                en_text = re.sub(r"^[A-Z]:\s*-?\s*", "", line)
                entries.append({"en": en_text, "zh": ""})

        dialogues.append({
            "source": source,
            "lines": entries,
        })

    return dialogues


# ===========================================================================
#  工具函数
# ===========================================================================

def get_day_dirs() -> list[dict]:
    """列出所有 day 目录及其状态."""
    if not WORD_DIR.exists():
        return []

    days = []
    for d in sorted(WORD_DIR.glob("day*")):
        if not d.is_dir():
            continue
        m = re.match(r"day(\d+)", d.name)
        if not m:
            continue
        num = int(m.group(1))

        txt = d / f"{d.name}.txt"
        json_f = d / f"{d.name}.json"
        md = d / f"{d.name}_study.md"

        word_count = 0
        if txt.exists():
            word_count = len(
                [w for w in txt.read_text("utf-8").splitlines() if w.strip()]
            )

        status = "empty"
        if md.exists():
            status = "ready"
        elif json_f.exists():
            status = "formatting"
        elif txt.exists():
            status = "scraping"
        else:
            status = "extracting"

        # 检查是否正在后台处理
        if num in processing_status:
            ps = processing_status[num]
            if ps["step"] not in ("done", "error"):
                status = ps["step"]

        days.append({
            "num": num,
            "name": d.name,
            "word_count": word_count,
            "status": status,
        })

    return days


def next_day_num() -> int:
    days = get_day_dirs()
    if not days:
        return 1
    return max(d["num"] for d in days) + 1


# ===========================================================================
#  后台处理管线
# ===========================================================================

def run_pipeline(day_num: int):
    """在子线程中依次运行三个处理步骤."""
    day_name = f"day{day_num}"
    day_dir = WORD_DIR / day_name
    pdf_path = day_dir / f"{day_name}.pdf"

    # 需要把项目目录加入 sys.path 以便导入脚本中的类
    sys_path_entry = str(BASE_DIR)
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)

    try:
        # Step 1: PDF -> txt
        txt_path = day_dir / f"{day_name}.txt"
        if not txt_path.exists():
            processing_status[day_num] = {"step": "extracting", "error": None}
            from pdf_extractor import PDFLargeWordExtractor
            ext = PDFLargeWordExtractor(pdf_folder="word")
            chars = ext.extract_large_font_chars(str(pdf_path))
            if chars:
                words = ext.combine_with_llm(chars)
                if words:
                    ext.save_words(words, txt_path)
            if not txt_path.exists():
                processing_status[day_num] = {
                    "step": "error",
                    "error": "PDF extraction failed - no words found",
                }
                return

        # Step 2: txt -> json + csv
        json_path = day_dir / f"{day_name}.json"
        if not json_path.exists():
            processing_status[day_num] = {"step": "scraping", "error": None}
            from pop_mystic_scraper import PopMysticScraper, save_json, save_csv, load_words
            scraper = PopMysticScraper()
            words = load_words(txt_path)
            if words:
                results = scraper.batch_search(words)
                save_json(results, json_path)
                save_csv(results, day_dir / f"{day_name}.csv")

        # Step 3: json -> study.md
        md_path = day_dir / f"{day_name}_study.md"
        if not md_path.exists() and json_path.exists():
            processing_status[day_num] = {"step": "formatting", "error": None}
            from quote_formatter import QuoteFormatter
            fmt = QuoteFormatter()
            fmt.process_file(json_path)

        processing_status[day_num] = {"step": "done", "error": None}

    except Exception as e:
        processing_status[day_num] = {"step": "error", "error": str(e)}


# ===========================================================================
#  路由
# ===========================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/day/<int:n>")
def day_page(n):
    return render_template("index.html")


@app.route("/api/days")
def api_days():
    return jsonify(get_day_dirs())


@app.route("/api/day/<int:n>")
def api_day(n):
    day_name = f"day{n}"
    md_path = WORD_DIR / day_name / f"{day_name}_study.md"
    if not md_path.exists():
        abort(404)
    text = md_path.read_text("utf-8")
    words = parse_study_md(text)
    return jsonify({"day": n, "words": words})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    # Day number specified by user
    day_num_str = request.form.get("day", "").strip()
    if not day_num_str or not day_num_str.isdigit() or int(day_num_str) < 1:
        return jsonify({"error": "Please specify a valid day number"}), 400
    day_num = int(day_num_str)

    day_name = f"day{day_num}"
    day_dir = WORD_DIR / day_name

    # Check if folder already has a PDF
    if day_dir.exists() and (day_dir / f"{day_name}.pdf").exists():
        return jsonify({"error": f"Day {day_num} already exists"}), 400

    day_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = day_dir / f"{day_name}.pdf"
    f.save(str(pdf_path))

    processing_status[day_num] = {"step": "extracting", "error": None}
    t = threading.Thread(target=run_pipeline, args=(day_num,), daemon=True)
    t.start()

    return jsonify({"day": day_num, "status": "started"})


@app.route("/api/day/<int:n>", methods=["DELETE"])
def api_delete_day(n):
    day_name = f"day{n}"
    day_dir = WORD_DIR / day_name
    if not day_dir.exists():
        return jsonify({"error": f"Day {n} not found"}), 404
    shutil.rmtree(day_dir)
    processing_status.pop(n, None)
    return jsonify({"deleted": n})


@app.route("/api/status/<int:n>")
def api_status(n):
    if n in processing_status:
        return jsonify(processing_status[n])
    # 判断文件状态
    day_name = f"day{n}"
    day_dir = WORD_DIR / day_name
    if (day_dir / f"{day_name}_study.md").exists():
        return jsonify({"step": "done", "error": None})
    return jsonify({"step": "unknown", "error": None})


# ===========================================================================
if __name__ == "__main__":
    print(f"Word dir: {WORD_DIR}")
    print(f"Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)

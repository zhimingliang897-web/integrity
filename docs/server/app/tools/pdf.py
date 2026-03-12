"""
PDF 工具集 Blueprint
路径前缀: /api/tools/pdf
需要 JWT 认证（处理接口），下载接口公开（随机文件名已作为保护）

本地备份 | 云端部署
"""

import os
import shutil
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from functools import wraps

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
from pypdf import PdfReader, PdfWriter
import jwt

# PyMuPDF（用于 PDF 转图片）
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

pdf_bp = Blueprint('pdf', __name__, url_prefix='/api/tools/pdf')

# 临时文件目录（持久，不随请求销毁）
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'integrity_pdf')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── 认证装饰器 ───────────────────────────────────────────────

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


# ─── 工具函数 ────────────────────────────────────────────────

def safe_temp_path(original_filename, suffix=None):
    """生成安全的临时文件路径"""
    safe_name = secure_filename(original_filename)
    if not safe_name:
        safe_name = 'upload' + (suffix or '.pdf')
    return os.path.join(UPLOAD_FOLDER, f'{os.urandom(4).hex()}_{safe_name}')


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes > 1024 * 1024:
        return f'{size_bytes / 1024 / 1024:.1f}MB'
    return f'{size_bytes / 1024:.1f}KB'


def close_reader(reader):
    """安全关闭 PdfReader"""
    try:
        if hasattr(reader, 'stream') and reader.stream:
            reader.stream.close()
    except Exception:
        pass


def get_pdf_info(pdf_path):
    """获取 PDF 信息"""
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    portrait = sum(1 for p in reader.pages if float(p.mediabox.height) > float(p.mediabox.width))
    close_reader(reader)
    return f'总页数：{total} | 竖版：{portrait} | 横版：{total - portrait}'


def parse_page_range(pages_str, total_pages):
    """解析页码字符串，支持 1,3,5 或 1-5 或 1,3-5,8 格式"""
    pages = set()
    for part in pages_str.replace(' ', '').split(','):
        if '-' in part:
            try:
                a, b = map(int, part.split('-'))
                if a > b:
                    a, b = b, a
                pages.update(p for p in range(a, b + 1) if 1 <= p <= total_pages)
            except ValueError:
                pass
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p)
            except ValueError:
                pass
    return pages


def _compress_jpg(img, max_kb, path):
    """压缩 JPG 图片到指定大小以下"""
    max_bytes = max_kb * 1024
    for q in range(95, 10, -5):
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=q)
        if buf.tell() <= max_bytes:
            img.save(path, format='JPEG', quality=q)
            return
    scale = 0.9
    while scale > 0.1:
        r = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        for q in range(85, 10, -10):
            buf = BytesIO()
            r.save(buf, format='JPEG', quality=q)
            if buf.tell() <= max_bytes:
                r.save(path, format='JPEG', quality=q)
                return
        scale -= 0.1
    img.resize((int(img.width * 0.3), int(img.height * 0.3)), Image.LANCZOS).save(path, format='JPEG', quality=20)


# ─── API 路由 ────────────────────────────────────────────────

@pdf_bp.route('/info', methods=['POST'])
@require_token
def api_pdf_info():
    """获取 PDF 信息"""
    if 'pdf' not in request.files:
        return jsonify({'info': '未上传文件'})
    temp = safe_temp_path(request.files['pdf'].filename)
    try:
        request.files['pdf'].save(temp)
        return jsonify({'info': get_pdf_info(temp)})
    except Exception as e:
        return jsonify({'info': f'读取失败: {e}'})
    finally:
        if os.path.exists(temp):
            os.remove(temp)


@pdf_bp.route('/images_to_pdf', methods=['POST'])
@require_token
def api_images_to_pdf():
    """图片转 PDF"""
    files = request.files.getlist('images')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'message': '请上传图片'})
    force_landscape = 'force_landscape' in request.form
    try:
        images = []
        for f in files:
            img = Image.open(f)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            if force_landscape and img.height > img.width:
                img = img.rotate(90, expand=True)
            images.append(img)
        out = f'images_to_pdf_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        images[0].save(out_path, save_all=True, append_images=images[1:])
        return jsonify({'success': True, 'message': f'✅ {len(images)} 张图片合成 PDF', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})


@pdf_bp.route('/merge', methods=['POST'])
@require_token
def api_merge_pdfs():
    """合并多个 PDF"""
    files = request.files.getlist('pdfs')
    if len(files) < 2:
        return jsonify({'success': False, 'message': '请上传至少 2 个 PDF'})
    temps = []
    try:
        writer = PdfWriter()
        total = 0
        for f in files:
            t = safe_temp_path(f.filename)
            f.save(t)
            temps.append(t)
            reader = PdfReader(t)
            for page in reader.pages:
                writer.add_page(page)
            total += len(reader.pages)
            close_reader(reader)
        out = f'merged_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with open(out_path, 'wb') as fp:
            writer.write(fp)
        return jsonify({'success': True, 'message': f'✅ {len(files)} 个文件合并，共 {total} 页', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        for t in temps:
            if os.path.exists(t):
                os.remove(t)


@pdf_bp.route('/remove_pages', methods=['POST'])
@require_token
def api_remove_pages():
    """删除 PDF 页面"""
    pages_str = request.form.get('pages', '').strip()
    if not pages_str:
        return jsonify({'success': False, 'message': '请输入页码'})
    temp = safe_temp_path(request.files['pdf'].filename)
    try:
        request.files['pdf'].save(temp)
        reader = PdfReader(temp)
        total = len(reader.pages)
        to_remove = {p - 1 for p in parse_page_range(pages_str, total)}
        writer = PdfWriter()
        for i in range(total):
            if i not in to_remove:
                writer.add_page(reader.pages[i])
        close_reader(reader)
        out = f'removed_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with open(out_path, 'wb') as fp:
            writer.write(fp)
        return jsonify({'success': True, 'message': f'✅ 原 {total} 页，删除 {len(to_remove)} 页', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp):
            os.remove(temp)


@pdf_bp.route('/insert', methods=['POST'])
@require_token
def api_insert_pdf():
    """在指定位置插入 PDF"""
    if 'main_pdf' not in request.files or 'insert_pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传两个 PDF'})
    position = request.form.get('position', 'after')
    page_index = int(request.form.get('page_index', 1) or 1)
    main_t = safe_temp_path(request.files['main_pdf'].filename)
    ins_t = safe_temp_path(request.files['insert_pdf'].filename)
    try:
        request.files['main_pdf'].save(main_t)
        request.files['insert_pdf'].save(ins_t)
        r_main = PdfReader(main_t)
        r_ins = PdfReader(ins_t)
        writer = PdfWriter()
        total = len(r_main.pages)
        ins_count = len(r_ins.pages)

        if position == 'start':
            [writer.add_page(p) for p in r_ins.pages]
            [writer.add_page(p) for p in r_main.pages]
            pos_text = '文档最前面'
        elif position == 'end':
            [writer.add_page(p) for p in r_main.pages]
            [writer.add_page(p) for p in r_ins.pages]
            pos_text = '文档最后面'
        elif position == 'before':
            pos = page_index - 1
            for i in range(total):
                if i == pos:
                    [writer.add_page(p) for p in r_ins.pages]
                writer.add_page(r_main.pages[i])
            pos_text = f'第 {page_index} 页之前'
        else:
            pos = page_index - 1
            for i in range(total):
                writer.add_page(r_main.pages[i])
                if i == pos:
                    [writer.add_page(p) for p in r_ins.pages]
            pos_text = f'第 {page_index} 页之后'

        close_reader(r_main)
        close_reader(r_ins)
        out = f'inserted_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with open(out_path, 'wb') as fp:
            writer.write(fp)
        return jsonify({'success': True, 'message': f'✅ 在{pos_text}插入 {ins_count} 页', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        for t in [main_t, ins_t]:
            if os.path.exists(t):
                os.remove(t)


@pdf_bp.route('/reorder', methods=['POST'])
@require_token
def api_reorder_pages():
    """页面重排（竖版在前，横版在后）"""
    temp = safe_temp_path(request.files['pdf'].filename)
    try:
        request.files['pdf'].save(temp)
        reader = PdfReader(temp)
        portrait, landscape = [], []
        for page in reader.pages:
            (portrait if float(page.mediabox.height) > float(page.mediabox.width) else landscape).append(page)
        close_reader(reader)
        writer = PdfWriter()
        for p in portrait + landscape:
            writer.add_page(p)
        out = f'reordered_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with open(out_path, 'wb') as fp:
            writer.write(fp)
        return jsonify({'success': True, 'message': f'✅ 竖版 {len(portrait)} 页在前，横版 {len(landscape)} 页在后', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp):
            os.remove(temp)


@pdf_bp.route('/normalize', methods=['POST'])
@require_token
def api_normalize_landscape():
    """统一横向页面尺寸"""
    temp = safe_temp_path(request.files['pdf'].filename)
    try:
        request.files['pdf'].save(temp)
        reader = PdfReader(temp)
        tw = th = None
        for page in reader.pages:
            w, h = float(page.mediabox.width), float(page.mediabox.height)
            if w > h:
                tw, th = w, h
                break
        if tw is None:
            return jsonify({'success': False, 'message': 'PDF 中没有横向页面'})
        writer = PdfWriter()
        count = 0
        for page in reader.pages:
            w, h = float(page.mediabox.width), float(page.mediabox.height)
            if w > h:
                page.scale_to(tw, th)
                count += 1
            writer.add_page(page)
        close_reader(reader)
        out = f'normalized_{os.urandom(4).hex()}.pdf'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with open(out_path, 'wb') as fp:
            writer.write(fp)
        return jsonify({'success': True, 'message': f'✅ 统一 {count} 个横向页面为 {tw:.0f}x{th:.0f}', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp):
            os.remove(temp)


@pdf_bp.route('/to_images', methods=['POST'])
@require_token
def api_pdf_to_images():
    """PDF 转图片"""
    if not HAS_FITZ:
        return jsonify({'success': False, 'message': '服务器缺少 PyMuPDF，请联系管理员'})
    try:
        start = int(request.form.get('start_page', 1))
        end = int(request.form.get('end_page', 1))
        dpi = int(request.form.get('dpi', 150))
        max_size = int(request.form.get('max_size', 0))
    except ValueError:
        return jsonify({'success': False, 'message': '参数必须是数字'})

    fmt = request.form.get('format', 'jpg').lower()
    long_image = 'long_image' in request.form
    temp = safe_temp_path(request.files['pdf'].filename)
    temp_dir = None
    try:
        request.files['pdf'].save(temp)
        doc = fitz.open(temp)
        total = len(doc)
        start = max(1, start)
        end = min(total, end)
        if start > end:
            doc.close()
            return jsonify({'success': False, 'message': f'页码错误，PDF 共 {total} 页'})

        zoom = dpi / 72
        images = []
        for n in range(start - 1, end):
            pix = doc[n].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            images.append(Image.frombytes('RGB', [pix.width, pix.height], pix.samples))
        doc.close()

        if long_image:
            mw = max(i.width for i in images)
            th = sum(i.height for i in images)
            canvas = Image.new('RGB', (mw, th), (255, 255, 255))
            y = 0
            for img in images:
                canvas.paste(img, ((mw - img.width) // 2, y))
                y += img.height
            ext = 'jpg' if fmt == 'jpg' else 'png'
            out = f'long_{os.urandom(4).hex()}.{ext}'
            out_path = os.path.join(UPLOAD_FOLDER, out)
            if fmt == 'png':
                canvas.save(out_path, format='PNG')
            elif max_size > 0:
                _compress_jpg(canvas, max_size, out_path)
            else:
                canvas.save(out_path, format='JPEG', quality=85)
            sz = format_size(os.path.getsize(out_path))
            return jsonify({'success': True, 'message': f'✅ 第 {start}-{end} 页合并长图（{mw}x{th}，{sz}）', 'download_url': f'/api/tools/pdf/download/{out}'})

        temp_dir = tempfile.mkdtemp()
        paths, total_sz = [], 0
        for i, img in enumerate(images):
            n = start + i
            ext = 'png' if fmt == 'png' else 'jpg'
            p = os.path.join(temp_dir, f'page_{n}.{ext}')
            if fmt == 'png':
                img.save(p, format='PNG')
            elif max_size > 0:
                _compress_jpg(img, max_size, p)
            else:
                img.save(p, format='JPEG', quality=85)
            total_sz += os.path.getsize(p)
            paths.append(p)

        out = f'images_{os.urandom(4).hex()}.zip'
        out_path = os.path.join(UPLOAD_FOLDER, out)
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                zf.write(p, os.path.basename(p))
        return jsonify({'success': True, 'message': f'✅ 导出第 {start}-{end} 页，共 {len(paths)} 张（{format_size(total_sz)}）', 'download_url': f'/api/tools/pdf/download/{out}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.exists(temp):
            os.remove(temp)


@pdf_bp.route('/download/<filename>')
def download_file(filename):
    """下载文件（无需认证，文件名随机已作为保护）"""
    safe_dir = Path(UPLOAD_FOLDER).resolve()
    target = (safe_dir / filename).resolve()
    if not str(target).startswith(str(safe_dir)):
        return '禁止访问', 403
    if not target.exists():
        return '文件不存在或已过期', 404
    return send_file(str(target), as_attachment=True, download_name=filename)

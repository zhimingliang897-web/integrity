"""
PDF 工具模块 - Blueprint
路由前缀: /api/tools/pdf
"""

import atexit
import os
import shutil
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file, current_app
from PIL import Image
from pypdf import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

# PyMuPDF（用于 PDF 转图片）
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

pdf_bp = Blueprint('pdf', __name__, url_prefix='/api/tools/pdf')

# 临时文件目录
UPLOAD_FOLDER = tempfile.mkdtemp()
atexit.register(shutil.rmtree, UPLOAD_FOLDER, ignore_errors=True)


# ============ 工具函数 ============

def safe_temp_path(original_filename, suffix=None):
    """生成安全的临时文件路径"""
    safe_name = secure_filename(original_filename)
    if not safe_name:
        safe_name = "upload" + (suffix or ".pdf")
    return os.path.join(UPLOAD_FOLDER, f"{os.urandom(4).hex()}_{safe_name}")


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f}MB"
    return f"{size_bytes / 1024:.1f}KB"


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
    total_pages = len(reader.pages)
    portrait_count = 0
    landscape_count = 0
    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        if h > w:
            portrait_count += 1
        else:
            landscape_count += 1
    close_reader(reader)
    return {
        'total_pages': total_pages,
        'portrait': portrait_count,
        'landscape': landscape_count,
        'info': f"总页数：{total_pages} | 竖版：{portrait_count} | 横版：{landscape_count}"
    }


def parse_page_range(pages_str, total_pages):
    """解析页码字符串，支持 1,3,5 或 1-5 或 1,3-5,8 格式"""
    pages = set()
    parts = pages_str.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = part.split('-')
                start = int(start)
                end = int(end)
                if start > end:
                    start, end = end, start
                for p in range(start, end + 1):
                    if 1 <= p <= total_pages:
                        pages.add(p)
            except ValueError:
                continue
        else:
            try:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p)
            except ValueError:
                continue
    return pages


def compress_image_to_size(img, max_size_kb, output_path):
    """压缩图片到指定大小以下（仅支持 JPG）"""
    max_size_bytes = max_size_kb * 1024

    for quality in range(95, 10, -5):
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        if buffer.tell() <= max_size_bytes:
            img.save(output_path, format='JPEG', quality=quality)
            return os.path.getsize(output_path)

    scale = 0.9
    while scale > 0.1:
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.LANCZOS)
        for quality in range(85, 10, -10):
            buffer = BytesIO()
            resized.save(buffer, format='JPEG', quality=quality)
            if buffer.tell() <= max_size_bytes:
                resized.save(output_path, format='JPEG', quality=quality)
                return os.path.getsize(output_path)
        scale -= 0.1

    resized = img.resize((int(img.width * 0.3), int(img.height * 0.3)), Image.LANCZOS)
    resized.save(output_path, format='JPEG', quality=20)
    return os.path.getsize(output_path)


# ============ API 路由 ============

@pdf_bp.route('/info', methods=['POST'])
def api_pdf_info():
    """获取 PDF 信息"""
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '未上传文件'})
    pdf_file = request.files['pdf']
    temp_path = safe_temp_path(pdf_file.filename)
    try:
        pdf_file.save(temp_path)
        info = get_pdf_info(temp_path)
        return jsonify({'success': True, **info})
    except Exception as e:
        return jsonify({'success': False, 'message': f'读取失败: {e}'})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bp.route('/images-to-pdf', methods=['POST'])
def api_images_to_pdf():
    """图片转 PDF"""
    if 'images' not in request.files:
        return jsonify({'success': False, 'message': '请上传图片'})

    files = request.files.getlist('images')
    if not files or files[0].filename == '':
        return jsonify({'success': False, 'message': '请上传至少一张图片'})

    force_landscape = request.form.get('force_landscape') == 'true'

    try:
        images = []
        for f in files:
            img = Image.open(f)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            if force_landscape and img.height > img.width:
                img = img.rotate(90, expand=True)
            images.append(img)

        output_filename = f"images_to_pdf_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        first, rest = images[0], images[1:]
        first.save(output_path, save_all=True, append_images=rest)

        return jsonify({
            'success': True,
            'message': f'完成：{len(images)} 张图片合成 PDF',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})


@pdf_bp.route('/merge', methods=['POST'])
def api_merge_pdfs():
    """合并多个 PDF"""
    if 'pdfs' not in request.files:
        return jsonify({'success': False, 'message': '请上传 PDF 文件'})

    files = request.files.getlist('pdfs')
    if len(files) < 2:
        return jsonify({'success': False, 'message': '请上传至少 2 个 PDF 文件'})

    temp_paths = []
    try:
        writer = PdfWriter()
        total_pages = 0

        for pdf_file in files:
            temp_path = safe_temp_path(pdf_file.filename)
            pdf_file.save(temp_path)
            temp_paths.append(temp_path)
            reader = PdfReader(temp_path)
            for page in reader.pages:
                writer.add_page(page)
            total_pages += len(reader.pages)
            close_reader(reader)

        output_filename = f"merged_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)

        return jsonify({
            'success': True,
            'message': f'合并完成：{len(files)} 个文件，共 {total_pages} 页',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        for p in temp_paths:
            if os.path.exists(p):
                os.remove(p)


@pdf_bp.route('/remove-pages', methods=['POST'])
def api_remove_pages():
    """删除 PDF 页面"""
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传 PDF 文件'})

    pages_str = request.form.get('pages', '')
    if not pages_str.strip():
        return jsonify({'success': False, 'message': '请输入要删除的页码'})

    pdf_file = request.files['pdf']
    temp_path = safe_temp_path(pdf_file.filename)

    try:
        pdf_file.save(temp_path)
        reader = PdfReader(temp_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        pages_to_remove = parse_page_range(pages_str, total_pages)
        if not pages_to_remove:
            return jsonify({'success': False, 'message': '没有有效的页码'})

        remove_idx = {p - 1 for p in pages_to_remove}
        for i in range(total_pages):
            if i not in remove_idx:
                writer.add_page(reader.pages[i])
        close_reader(reader)

        output_filename = f"removed_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)

        return jsonify({
            'success': True,
            'message': f'原 {total_pages} 页，删除 {len(remove_idx)} 页，剩余 {total_pages - len(remove_idx)} 页',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bp.route('/insert', methods=['POST'])
def api_insert_pdf():
    """在指定位置插入 PDF"""
    if 'main_pdf' not in request.files or 'insert_pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传主文档和要插入的文档'})

    position = request.form.get('position', 'after')
    try:
        page_index = int(request.form.get('page_index', 1))
    except ValueError:
        page_index = 1

    main_file = request.files['main_pdf']
    insert_file = request.files['insert_pdf']

    main_path = safe_temp_path(main_file.filename)
    insert_path = safe_temp_path(insert_file.filename)

    try:
        main_file.save(main_path)
        insert_file.save(insert_path)

        reader_main = PdfReader(main_path)
        reader_ins = PdfReader(insert_path)
        writer = PdfWriter()

        total_main = len(reader_main.pages)
        insert_count = len(reader_ins.pages)

        if position == 'start':
            for p in reader_ins.pages:
                writer.add_page(p)
            for p in reader_main.pages:
                writer.add_page(p)
            position_text = "文档最前面"
        elif position == 'end':
            for p in reader_main.pages:
                writer.add_page(p)
            for p in reader_ins.pages:
                writer.add_page(p)
            position_text = "文档最后面"
        elif position == 'before':
            if not 1 <= page_index <= total_main:
                return jsonify({'success': False, 'message': f'页码超范围：1 ~ {total_main}'})
            pos = page_index - 1
            for i in range(total_main):
                if i == pos:
                    for p in reader_ins.pages:
                        writer.add_page(p)
                writer.add_page(reader_main.pages[i])
            position_text = f"第 {page_index} 页之前"
        else:  # after
            if not 1 <= page_index <= total_main:
                return jsonify({'success': False, 'message': f'页码超范围：1 ~ {total_main}'})
            pos = page_index - 1
            for i in range(total_main):
                writer.add_page(reader_main.pages[i])
                if i == pos:
                    for p in reader_ins.pages:
                        writer.add_page(p)
            position_text = f"第 {page_index} 页之后"

        close_reader(reader_main)
        close_reader(reader_ins)

        output_filename = f"inserted_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)

        return jsonify({
            'success': True,
            'message': f'在{position_text}插入 {insert_count} 页',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        for p in [main_path, insert_path]:
            if os.path.exists(p):
                os.remove(p)


@pdf_bp.route('/reorder', methods=['POST'])
def api_reorder_pages():
    """页面重排（竖版在前，横版在后）"""
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传 PDF 文件'})

    pdf_file = request.files['pdf']
    temp_path = safe_temp_path(pdf_file.filename)

    try:
        pdf_file.save(temp_path)
        reader = PdfReader(temp_path)
        writer = PdfWriter()

        portrait_pages = []
        landscape_pages = []

        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            if h > w:
                portrait_pages.append(page)
            else:
                landscape_pages.append(page)

        close_reader(reader)

        for p in portrait_pages:
            writer.add_page(p)
        for p in landscape_pages:
            writer.add_page(p)

        output_filename = f"reordered_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)

        return jsonify({
            'success': True,
            'message': f'竖版 {len(portrait_pages)} 页在前，横版 {len(landscape_pages)} 页在后',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bp.route('/normalize', methods=['POST'])
def api_normalize_landscape():
    """统一横向页面尺寸"""
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传 PDF 文件'})

    pdf_file = request.files['pdf']
    temp_path = safe_temp_path(pdf_file.filename)

    try:
        pdf_file.save(temp_path)
        reader = PdfReader(temp_path)
        writer = PdfWriter()

        target_width = None
        target_height = None

        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            if w > h:
                target_width = w
                target_height = h
                break

        if target_width is None:
            return jsonify({'success': False, 'message': 'PDF 中没有横向页面'})

        landscape_count = 0
        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            if w > h:
                page.scale_to(target_width, target_height)
                landscape_count += 1
            writer.add_page(page)

        close_reader(reader)

        output_filename = f"normalized_{os.urandom(4).hex()}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)

        return jsonify({
            'success': True,
            'message': f'统一 {landscape_count} 个横向页面尺寸为 {target_width:.0f}x{target_height:.0f}',
            'download_url': f'/api/tools/pdf/download/{output_filename}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bp.route('/to-images', methods=['POST'])
def api_pdf_to_images():
    """PDF 转图片"""
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'message': '请上传 PDF 文件'})

    if not HAS_FITZ:
        return jsonify({'success': False, 'message': '服务器未安装 PyMuPDF'})

    try:
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 1))
        dpi = int(request.form.get('dpi', 150))
        max_size = int(request.form.get('max_size', 0))
    except ValueError:
        return jsonify({'success': False, 'message': '参数必须是数字'})

    output_format = request.form.get('format', 'jpg').lower()
    if output_format not in ['jpg', 'png']:
        output_format = 'jpg'

    long_image = request.form.get('long_image') == 'true'

    pdf_file = request.files['pdf']
    temp_path = safe_temp_path(pdf_file.filename)
    temp_dir = None

    try:
        pdf_file.save(temp_path)
        doc = fitz.open(temp_path)
        total_pages = len(doc)

        if start_page < 1:
            start_page = 1
        if end_page > total_pages:
            end_page = total_pages
        if start_page > end_page:
            doc.close()
            return jsonify({'success': False, 'message': f'页码范围错误，PDF 共 {total_pages} 页'})

        temp_dir = tempfile.mkdtemp()
        images = []
        zoom = dpi / 72

        for page_num in range(start_page - 1, end_page):
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()

        # 合并为长图
        if long_image and len(images) > 0:
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)

            long_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in images:
                x_offset = (max_width - img.width) // 2
                long_img.paste(img, (x_offset, y_offset))
                y_offset += img.height

            ext = 'jpg' if output_format == 'jpg' else 'png'
            output_filename = f"long_image_{os.urandom(4).hex()}.{ext}"
            output_path = os.path.join(UPLOAD_FOLDER, output_filename)

            if output_format == 'png':
                long_img.save(output_path, format='PNG')
            else:
                if max_size > 0:
                    compress_image_to_size(long_img, max_size, output_path)
                else:
                    long_img.save(output_path, format='JPEG', quality=85)

            file_size = os.path.getsize(output_path)
            return jsonify({
                'success': True,
                'message': f'第 {start_page}-{end_page} 页合并为长图（{max_width}x{total_height}，{format_size(file_size)}）',
                'download_url': f'/api/tools/pdf/download/{output_filename}'
            })

        # 正常导出多张图片
        image_paths = []
        total_size = 0

        for i, img in enumerate(images):
            page_num = start_page + i
            if output_format == 'png':
                out_path = os.path.join(temp_dir, f"page_{page_num}.png")
                img.save(out_path, format='PNG')
            else:
                out_path = os.path.join(temp_dir, f"page_{page_num}.jpg")
                if max_size > 0:
                    compress_image_to_size(img, max_size, out_path)
                else:
                    img.save(out_path, format='JPEG', quality=85)
            total_size += os.path.getsize(out_path)
            image_paths.append(out_path)

        zip_filename = f"pdf_images_{os.urandom(4).hex()}.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for img_path in image_paths:
                zf.write(img_path, os.path.basename(img_path))

        format_str = "JPG" if output_format == 'jpg' else "PNG"
        size_limit_str = f"，每张≤{max_size}KB" if max_size > 0 and output_format == 'jpg' else ""

        return jsonify({
            'success': True,
            'message': f'导出第 {start_page}-{end_page} 页，共 {len(image_paths)} 张 {format_str} 图片（总计 {format_size(total_size)}{size_limit_str}）',
            'download_url': f'/api/tools/pdf/download/{zip_filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'处理失败: {e}'})
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bp.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    safe_dir = Path(UPLOAD_FOLDER).resolve()
    target = (safe_dir / filename).resolve()
    if not str(target).startswith(str(safe_dir)):
        return jsonify({'success': False, 'message': '禁止访问'}), 403
    if not target.exists():
        return jsonify({'success': False, 'message': '文件不存在或已过期'}), 404
    return send_file(str(target), as_attachment=True, download_name=filename)

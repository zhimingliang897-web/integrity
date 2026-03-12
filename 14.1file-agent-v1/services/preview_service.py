import os
import io
from pathlib import Path
from typing import Optional, Tuple
from fastapi.responses import StreamingResponse, FileResponse

from app.config import settings


class PreviewService:
    def __init__(self):
        self.root_path = Path(settings.root_path)
        
        self.image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'}
        self.video_exts = {'.mp4', '.webm', '.ogg', '.mov'}
        self.audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        self.pdf_exts = {'.pdf'}
        self.text_exts = {'.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.log', '.csv'}
        self.doc_exts = {'.doc', '.docx'}
    
    def _is_path_allowed(self, path: str) -> bool:
        try:
            abs_path = Path(path).resolve()
            root = self.root_path.resolve()
            return str(abs_path).startswith(str(root))
        except Exception:
            return False
    
    def get_preview_type(self, ext: str) -> str:
        ext = ext.lower()
        if ext in self.image_exts:
            return "image"
        elif ext in self.video_exts:
            return "video"
        elif ext in self.audio_exts:
            return "audio"
        elif ext in self.pdf_exts:
            return "pdf"
        elif ext in self.text_exts:
            return "text"
        elif ext in self.doc_exts:
            return "document"
        else:
            return "unknown"
    
    def can_preview(self, path: str) -> bool:
        ext = Path(path).suffix.lower()
        return self.get_preview_type(ext) != "unknown"
    
    def get_file_response(self, path: str, preview: bool = False) -> FileResponse:
        file_path = Path(path)
        
        if not self._is_path_allowed(path):
            raise ValueError("路径不允许访问")
        
        if not file_path.exists():
            raise FileNotFoundError("文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=self._get_mime_type(path)
        )
    
    def get_text_preview(self, path: str, max_size: int = 100000) -> str:
        file_path = Path(path)
        
        if not self._is_path_allowed(path):
            raise ValueError("路径不允许访问")
        
        if not file_path.exists():
            raise FileNotFoundError("文件不存在")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_size)
        except Exception as e:
            return f"无法读取文件: {str(e)}"
    
    def get_image_thumbnail(self, path: str, size: Tuple[int, int] = (200, 200)):
        try:
            from PIL import Image
            
            file_path = Path(path)
            
            if not self._is_path_allowed(path):
                raise ValueError("路径不允许访问")
            
            if not file_path.exists():
                raise FileNotFoundError("文件不存在")
            
            img = Image.open(file_path)
            img.thumbnail(size)
            
            img_byte_arr = io.BytesIO()
            img_format = img.format or 'JPEG'
            if img_format == 'PNG':
                img.save(img_byte_arr, format='PNG')
            else:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(img_byte_arr, format='JPEG')
            
            img_byte_arr.seek(0)
            return img_byte_arr
        except ImportError:
            raise RuntimeError("Pillow 库未安装，无法生成缩略图")
        except Exception as e:
            raise RuntimeError(f"生成缩略图失败: {str(e)}")
    
    def _get_mime_type(self, path: str) -> str:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type or 'application/octet-stream'
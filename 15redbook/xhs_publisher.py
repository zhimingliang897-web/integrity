"""
小红书自动发布模块 - 使用xhs库通过Cookie发布笔记
"""

import json
import time
from pathlib import Path
from typing import List, Optional
import yaml


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class XHSPublisher:
    """小红书发布器"""

    def __init__(self, cookie: Optional[str] = None):
        """
        初始化发布器

        Args:
            cookie: 小红书Cookie字符串（可选，优先使用配置文件）
        """
        from xhs import XhsClient, help

        config = load_config()
        xhs_config = config.get('xiaohongshu', {})

        # 优先使用传入的cookie，否则从配置文件读取
        self.cookie = cookie or xhs_config.get('cookie', '')

        if not self.cookie:
            raise ValueError(
                "未配置小红书Cookie！\n"
                "请在config.yaml中添加:\n"
                "xiaohongshu:\n"
                "  cookie: \"你的cookie字符串\"\n\n"
                "获取方法：\n"
                "1. 浏览器登录 xiaohongshu.com\n"
                "2. F12打开开发者工具 -> Network\n"
                "3. 刷新页面，找到任意请求\n"
                "4. 复制Request Headers中的Cookie值"
            )
            
        # 从cookie中提取a1和web_session
        import re
        
        def extract_cookie_value(cookie_str: str, key: str) -> str:
            """从cookie字符串中提取指定key的值"""
            match = re.search(rf'{key}=([^;]+)', cookie_str)
            return match.group(1) if match else ""
        
        a1 = extract_cookie_value(self.cookie, 'a1')
        web_session = extract_cookie_value(self.cookie, 'web_session')
        
        def sign_wrapper(uri, data=None, **kwargs):
            # 使用从cookie提取的值，忽略传入的参数（因为XhsClient会传a1/web_session但我们用cookie中的值）
            return help.sign(uri, data, a1=a1, b1=web_session)

        self.client = XhsClient(cookie=self.cookie, sign=sign_wrapper)

    def upload_image(self, image_path: str) -> str:
        """
        上传图片

        Args:
            image_path: 图片路径

        Returns:
            上传后的图片ID
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        # 获取上传许可
        # 返回格式是元组: (file_id, token)
        file_type = 'image'
        permit = self.client.get_upload_files_permit(file_type, count=1)
        file_id, token = permit  # 解包元组

        # 确定content_type
        suffix = image_path.suffix.lower()
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(suffix, 'image/jpeg')

        # 上传文件
        self.client.upload_file(file_id, token, str(image_path), content_type)

        return file_id

    def publish_note(
        self,
        title: str,
        content: str,
        image_paths: List[str],
        tags: Optional[List[str]] = None,
        is_private: bool = False
    ) -> dict:
        """
        发布图文笔记

        Args:
            title: 笔记标题（不超过20字）
            content: 笔记正文（不超过1000字）
            image_paths: 图片路径列表
            tags: 话题标签列表
            is_private: 是否私密发布（用于测试）

        Returns:
            发布结果，包含笔记ID和链接
        """
        # 验证标题长度
        if len(title) > 20:
            print(f"警告: 标题超过20字，将被截断: {title[:20]}...")
            title = title[:20]

        # 验证正文长度
        if len(content) > 1000:
            print(f"警告: 正文超过1000字，将被截断")
            content = content[:1000]

        # 验证图片路径
        valid_paths = []
        for path in image_paths:
            p = Path(path)
            if p.exists():
                valid_paths.append(str(p.absolute()))
            else:
                print(f"警告: 图片不存在，跳过: {path}")

        if not valid_paths:
            raise ValueError("没有有效的图片文件")

        print(f"准备发布 {len(valid_paths)} 张图片...")

        # 处理标签
        if tags:
            # 确保标签格式正确（以#开头）
            formatted_tags = []
            for tag in tags:
                if not tag.startswith('#'):
                    tag = '#' + tag
                formatted_tags.append(tag)
            # 将标签添加到正文末尾
            tag_str = ' '.join(formatted_tags)
            if not content.endswith(tag_str):
                content = content.rstrip() + '\n\n' + tag_str

        # 发布笔记
        print("正在发布笔记（xhs库会自动上传图片）...")

        # 使用create_image_note方法
        # 签名: create_image_note(title, desc, files, post_time, ats, topics, is_private)
        # files参数应该是文件路径列表，xhs库内部会处理上传
        result = self.client.create_image_note(
            title=title,
            desc=content,
            files=valid_paths,  # 传入文件路径，不是file_id
            is_private=is_private
        )

        return result

    def test_connection(self) -> bool:
        """测试Cookie是否有效"""
        try:
            # 尝试获取用户信息
            user_info = self.client.get_self_info()
            if user_info and user_info.get('code') == -1:
                print(f"Cookie无效或已过期 (code: {user_info.get('code')})")
                print("请刷新Cookie后重试")
                return False
            if user_info:
                nickname = user_info.get('nickname') or user_info.get('name') or '未知'
                print(f"Cookie有效！当前用户: {nickname}")
                return True
            print(f"Cookie无效或已过期")
            return False
        except Exception as e:
            print(f"Cookie无效或已过期: {e}")
            return False


def publish_to_xiaohongshu(
    title: str,
    content: str,
    image_paths: List[str],
    tags: Optional[List[str]] = None,
    is_private: bool = False,
    cookie: Optional[str] = None
) -> dict:
    """
    便捷函数：发布到小红书

    Args:
        title: 笔记标题
        content: 笔记正文
        image_paths: 图片路径列表
        tags: 话题标签
        is_private: 是否私密发布
        cookie: Cookie字符串（可选）

    Returns:
        发布结果
    """
    publisher = XHSPublisher(cookie)
    return publisher.publish_note(title, content, image_paths, tags, is_private)


def test_cookie(cookie: Optional[str] = None) -> bool:
    """测试Cookie是否有效"""
    try:
        publisher = XHSPublisher(cookie)
        return publisher.test_connection()
    except Exception as e:
        print(f"错误: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书发布工具")
    parser.add_argument("--test", action="store_true", help="测试Cookie是否有效")
    parser.add_argument("--cookie", help="手动指定Cookie")

    args = parser.parse_args()

    if args.test:
        test_cookie(args.cookie)
    else:
        print("使用方法:")
        print("  测试Cookie: python xhs_publisher.py --test")
        print("  指定Cookie: python xhs_publisher.py --test --cookie \"your_cookie_here\"")

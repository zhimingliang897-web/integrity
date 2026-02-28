import os

with open('E:/integrity/1分镜/video_maker/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace _step2 function
import re

# Pattern to match _step2 function
pattern = r'(    def _step2\(self\):.*?        self._launch\(\[.*?self\._v_proj\.get\(\)\.strip\(\),.*?\]\))'
replacement = r'''    def _step2(self):
        if self._busy or not self._check():
            return
        # 根据方案选择对应的文件夹和脚本
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        self._launch([
            sys.executable, "-u", os.path.join(script_dir, "make_video.py"),
            self._v_proj.get().strip(),
        ])'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('E:/integrity/1分镜/video_maker/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')

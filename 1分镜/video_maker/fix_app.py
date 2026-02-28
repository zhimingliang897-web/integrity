# -*- coding: utf-8 -*-
import os

# Read the file
with open('E:/integrity/1分镜/video_maker/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _step1 function
old_step1 = '''    def _step1(self):
        if self._busy or not self._check(need_scene=True):
            return
        script = "gen_text.py" if self._v_strategy.get() == "多图方案" else "gen_text_pre.py"
        cmd = [sys.executable, "-u", os.path.join(SCRIPT_DIR, script),
               self._v_proj.get().strip(), self._v_scene.get().strip()]'''

new_step1 = '''    def _step1(self):
        if self._busy or not self._check(need_scene=True):
            return
        # 根据方案选择对应的文件夹和脚本
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        cmd = [sys.executable, "-u", os.path.join(script_dir, "gen_text.py"),
               self._v_proj.get().strip(), self._v_scene.get().strip()]'''

content = content.replace(old_step1, new_step1)

# Replace _step2 function  
old_step2 = '''    def _step2(self):
        if self._busy or not self._check():
            return
        script = "make_video.py" if self._v_strategy.get() == "多图方案" else "make_video_pre.py"
        cmd = [
            sys.executable, "-u", os.path.join(SCRIPT_DIR, script),
            self._v_proj.get().strip(),
        ]'''

new_step2 = '''    def _step2(self):
        if self._busy or not self._check():
            return
        # 根据方案选择对应的文件夹和脚本
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        cmd = [
            sys.executable, "-u", os.path.join(script_dir, "make_video.py"),
            self._v_proj.get().strip(),
        ]'''

content = content.replace(old_step2, new_step2)

# Replace _run_all function
old_run_all = '''    def _run_all(self):
        if self._busy or not self._check(need_scene=True):
            return
        is_multi = self._v_strategy.get() == "多图方案"
        cmd1 = [sys.executable, "-u",
                os.path.join(SCRIPT_DIR, "gen_text.py" if is_multi else "gen_text_pre.py"),
                self._v_proj.get().strip(), self._v_scene.get().strip()]
        cmd2 = [sys.executable, "-u",
                os.path.join(SCRIPT_DIR, "make_video.py" if is_multi else "make_video_pre.py"),
                self._v_proj.get().strip()]'''

new_run_all = '''    def _run_all(self):
        if self._busy or not self._check(need_scene=True):
            return
        # 根据方案选择对应的文件夹
        if self._v_strategy.get() == "多图方案":
            script_dir = os.path.join(SCRIPT_DIR, "multi")
        else:
            script_dir = os.path.join(SCRIPT_DIR, "grid")
        cmd1 = [sys.executable, "-u",
                os.path.join(script_dir, "gen_text.py"),
                self._v_proj.get().strip(), self._v_scene.get().strip()]
        cmd2 = [sys.executable, "-u",
                os.path.join(script_dir, "make_video.py"),
                self._v_proj.get().strip()]'''

content = content.replace(old_run_all, new_run_all)

# Write back
with open('E:/integrity/1分镜/video_maker/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done!')

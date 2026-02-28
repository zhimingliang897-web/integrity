"""Test with file-based logging"""
import sys, os, traceback

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_output.log")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Logger:
    def __init__(self, filepath):
        self.f = open(filepath, "w", encoding="utf-8")
        self.stdout = sys.stdout
    def write(self, msg):
        self.f.write(msg)
        self.f.flush()
        try:
            self.stdout.write(msg)
        except:
            pass
    def flush(self):
        self.f.flush()

sys.stdout = Logger(LOG_FILE)
sys.stderr = sys.stdout

import config

print("=== TEST START ===")

# Test XHS first (faster, more likely to work)
print("\n--- XHS Searcher Test ---")
try:
    from searchers.xiaohongshu import XiaohongshuSearcher
    cookie = getattr(config, "XIAOHONGSHU_COOKIE", "")
    if not cookie:
        print("SKIP: No cookie configured")
    else:
        print(f"Cookie length: {len(cookie)}")
        searcher = XiaohongshuSearcher(cookie=cookie, speed="fast")
        results = searcher.search("iPhone", max_results=3)
        print(f"XHS RESULTS: {len(results)}")
        for i, r in enumerate(results, 1):
            print(f"  {i}. id={r.content_id}")
            print(f"     title={r.title[:60]}")
            print(f"     url={r.url}")
            print(f"     author={r.author}")
            print(f"     likes={r.like_count} comments={r.comment_count}")
        if len(results) > 0:
            print("XHS: PASS")
        else:
            print("XHS: FAIL (no results)")
except Exception as e:
    print(f"XHS ERROR: {e}")
    traceback.print_exc()

# Test Douyin
print("\n--- Douyin Searcher Test ---")
try:
    from searchers.douyin import DouyinSearcher
    cookie = getattr(config, "DOUYIN_COOKIE", "")
    if not cookie:
        print("SKIP: No cookie configured")
    else:
        print(f"Cookie length: {len(cookie)}")
        searcher = DouyinSearcher(cookie=cookie, speed="fast")
        results = searcher.search("iPhone", max_results=3)
        print(f"DOUYIN RESULTS: {len(results)}")
        for i, r in enumerate(results, 1):
            print(f"  {i}. id={r.content_id}")
            print(f"     title={r.title[:60]}")
            print(f"     url={r.url}")
            print(f"     author={r.author}")
            print(f"     likes={r.like_count} comments={r.comment_count}")
        if len(results) > 0:
            print("DOUYIN: PASS")
        else:
            print("DOUYIN: FAIL (no results)")
except Exception as e:
    print(f"DOUYIN ERROR: {e}")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")

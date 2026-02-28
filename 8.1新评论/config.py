"""
配置文件 - 社媒辅助搜索引擎

获取 Cookie 的方法:
1. 自动获取（推荐）：运行 update_cookie.bat 或 python scripts/refresh_cookie.py -p 平台名
2. 手动获取：浏览器 F12 -> Network -> 任意请求 -> Headers -> Cookie
"""
import os

# ============================================================
# 基础配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "search.db")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")  # 导出目录
OUTPUT_FORMAT = "csv"  # 导出格式: "csv" 或 "excel"

# ============================================================
# 平台 Cookie 配置
# ============================================================

# B站 Cookie（可选，不填也能抓取，但填了可以获取更多数据）
BILIBILI_COOKIE = "buvid3=386CFDB0-9684-53C7-71F9-C923020163DE06891infoc; b_nut=1772043206; _uuid=BDFCF5B5-1E66-C28C-B1056-D1AADE101427207002infoc; home_feed_column=4; browser_resolution=1280-800; bmg_af_switch=1; bmg_src_def_domain=i0.hdslb.com; buvid4=B5466C7C-15D3-18E9-E2D7-CC8780ED4EAC07716-026022602-DSLYvkVJz5k4Vr398VtcWg%3D%3D; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzIzMDI0MDcsImlhdCI6MTc3MjA0MzE0NywicGx0IjotMX0.pK9478pX9koxFWVB_acq1Im-qgalLyzZK4MknBt2bV8; bili_ticket_expires=1772302347; buvid_fp=9a08df9dd762425df4ccf6acb257d4f9; SESSDATA=e483a683%2C1787595222%2Cd2855%2A21CjA3dNin7q2hHwMLu9eJqiPPsM7Z3nygGdZOyoSrMzDf4ouvhRX8sSDXXSSJaWYUbxYSVnhJVDdwQnhFalQ4a0htb2pMamdIUVdfdGpIV0JKWlF2X2RCNjYzM2xtODFrTUM4R2NrNzFEUFdwSFY2VVMzZUp4VVE5WnFtYmFFZXM2ZXNMeUxfUlVnIIEC; bili_jct=c27d19d003cb20cccfb84bcc9b0b7a55; DedeUserID=35106543; DedeUserID__ckMd5=a00be45236c41e98; sid=q9fwbuaq; b_lsid=7EA76F63_19C9601D052"

# 抖音 Cookie（必填，不填无法抓取）
# 打开 https://www.douyin.com 登录后获取
DOUYIN_COOKIE = "__ac_nonce=0699f3b7f001ddd8169bc; __ac_signature=_02B4Z6wo00f01qB-TTAAAIDD9Pltd1og.jqgXmmAAMGM35; enter_pc_once=1; UIFID_TEMP=f670781d5233033367a4d99498efe9bd14a45e82156a15d1881178acac831acfa9ed76b3c5bf9da0ad672e666584f80822ca1f44e596943bc4e9cd3f61ce8442e4993fdea9baa5104abdd646b23fbf36; x-web-secsdk-uid=34a193d1-c04a-422b-8313-931bbdfe944e; s_v_web_id=verify_mm2cqcfi_GRkrqgj4_pdO6_4v8Y_Bcx2_fVj0pzCDegUA; device_web_cpu_core=12; device_web_memory_size=8; architecture=amd64; hevc_supported=true; home_can_add_dy_2_desktop=%220%22; dy_swidth=1280; dy_sheight=800; strategyABtestKey=%221772043139.483%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.5%7D; xgplayer_device_id=91421717490; xgplayer_user_id=454481323492; passport_csrf_token=f4361b9111122541373b01ae4b7c043f; passport_csrf_token_default=f4361b9111122541373b01ae4b7c043f; bd_ticket_guard_client_web_domain=2; fpk1=U2FsdGVkX1+QLdsRPWAy3SOYZOjp3cC8F8CtDUvg0IXvlbumq8lVxcNugI+v9OMcnYzfgidwE69XZ2l8Sm+0nA==; fpk2=9c1ce27f08b16479d2e17743062b28ed; gulu_source_res=eyJwX2luIjoiMDYxZGIwZWU3NGVlNDllYzhlMTYzNzQ5M2NlMTAwYTY4ZmU3YjMxMmViMzU4YzMyMDcxZmE3MzViZjc0NzViYSJ9; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f2736353636313436313537323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=O0D1DJjHUpev6M3dIAtZdFKVL7AVLkQnB08WBfXh4wDBJ7wr8Vg44MwFXgc4awuy6SCMnFIOFagvABLbtGdW8URZSI48rKLcOnUwtrQuVaJp7HAH9ox75-wVxB9ECL19X93wlM0gdCi77RpjGnJ8xH_GoUJ9J9Wi0FG5V6l2NeT0Hm9nb4WXiBGpoSgWA-SDpaJGLFy-VDmB0TCzsE80s7eGXiWzzGbnGMVYzk-EgcF47V6aCvYGv0LUac98R87fvs-AfTs27xoK2iNwt5Nbv8t2caSe_Ie4GrZOPgspHeD9ZQVK6kITiNHflmO9tjb7ENIvs2EQ45q-wYxXtEp9Pal1xTG-HuplXndPGl2xMuPW56EAA89qWK9GZ3WJetq_gI46QVM0Lyj7yv2DjQ24icJcetPIlv-H0r8ezlvEjRVf1kWaIktNs1d-6f-imTGLDGJHWH2WWP317XkNabUAKVozTPFTTqLvAOz3d5JG6xvu6pLRERw9HxK9Osbbz-ch; passport_auth_mix_state=nxg4phf31i1vkbtes7ccapllezwiy5hq5ywifzarn5w7qhkc; passport_mfa_token=CjdtIC0NWTcDQA%2BIaDUtjbLUM9q8YG%2ByCf6k%2BQuSkjihKE2epYzzEuPGJWiukmzzW6Tggqe%2BkMrLGkoKPAAAAAAAAAAAAABQHcBhd3Ri2ngLzi6Fs3O4ck6o38TGLTDr4r15dABzPtuARl3txblRXAkjQsUaYdGzrhDmzIoOGPax0WwgAiIBA5SIYv0%3D; d_ticket=c56fe2bc7d6565eb65e34682231e6247ad8d2; passport_assist_user=CkGU1QTBbxk_FtBKe11GY6h-Q3iyxmkPSwLFCdweZAv-FJvhN0f5aEj7AjDdfYF1hgf8thRR9zRL-k2PdsKWgXSlYhpKCjwAAAAAAAAAAAAAUB0LZnSWtn_JbqFrSr8PMEUoys15RtPXh4wx9soxg0E1qijhrKsBcc9TQlRuXsDWXF0Q4syKDhiJr9ZUIAEiAQPgpvpb; n_mh=t8gkCNWIdtsOddp1wxcZHVe-6xeRg5WvNyTvRCIGC5g; passport_auth_status=446e815697976aa5afcfef30410c51b7%2C; passport_auth_status_ss=446e815697976aa5afcfef30410c51b7%2C; sid_guard=fcb7831c20233ff81494402147991dd5%7C1772043165%7C5184000%7CSun%2C+26-Apr-2026+18%3A12%3A45+GMT; uid_tt=13564b98bfe3d2df59dc482654062baa; uid_tt_ss=13564b98bfe3d2df59dc482654062baa; sid_tt=fcb7831c20233ff81494402147991dd5; sessionid=fcb7831c20233ff81494402147991dd5; sessionid_ss=fcb7831c20233ff81494402147991dd5; session_tlb_tag=sttt%7C3%7C_LeDHCAjP_gUlEAhR5kd1f________-lN3paE8YzBCNRlpD4E_sGwuzyMw_qkRGX5GxyHIngPC0%3D; is_staff_user=false; sid_ucp_v1=1.0.0-KGE0NzAwYTcyYzcyMzhlZDEwNDFlZmMyNjRiYmZkODBiMmJjMDhhMDkKIQjA9cD8ufTjAhCd9_zMBhjvMSAMMJD35_kFOAJA8QdIBBoCbHEiIGZjYjc4MzFjMjAyMzNmZjgxNDk0NDAyMTQ3OTkxZGQ1; ssid_ucp_v1=1.0.0-KGE0NzAwYTcyYzcyMzhlZDEwNDFlZmMyNjRiYmZkODBiMmJjMDhhMDkKIQjA9cD8ufTjAhCd9_zMBhjvMSAMMJD35_kFOAJA8QdIBBoCbHEiIGZjYjc4MzFjMjAyMzNmZjgxNDk0NDAyMTQ3OTkxZGQ1; _bd_ticket_crypt_doamin=2; _bd_ticket_crypt_cookie=fb5a2de82d8964eaed82270c327c1632; __security_mc_1_s_sdk_sign_data_key_web_protect=2d84dd00-41d0-b5ae; __security_mc_1_s_sdk_cert_key=2101ca8b-47f2-83b6; __security_mc_1_s_sdk_crypt_sdk=bf666f50-4a8d-aa26; __security_server_data_status=1; login_time=1772043166057; xg_device_score=7.658129985009262; UIFID=f670781d5233033367a4d99498efe9bd14a45e82156a15d1881178acac831acfa9ed76b3c5bf9da0ad672e666584f8080b6d76bb5f0c627833549d2e97afaecdb3f4006d95dd1ba54e1233ace0caffeece7a45a660d9c6a5b8c254749244b84b3df50d06253c48e595be9e15a296b0ce3d0c80ac187cb3f90db5afb479f07623e87f81d67c202c2c1f9847afa554cf646c07ff7697e7c0a9fcd67a944abecfbb; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A0%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A800%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A12%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22; SelfTabRedDotControl=%5B%7B%22id%22%3A%227585830146305689652%22%2C%22u%22%3A26%2C%22c%22%3A0%7D%5D; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAAF4WxDyKzeBLuuoHb4Mnv7_HQLYjSgStr_IDWEekeIkgv0cTSKAnX2AxBWbHG_NsU%2F1772121600000%2F0%2F1772043169695%2F0%22; is_dash_user=1; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCSHI2eG1yeEd2cTJMNGhFb0ZwakNmUHpKQ0V0NlhqMHdQNFR1OGZoYlZrQmNSc2t2UUY2Qk5sdm9OYkFCR1dvY2t6NDZUZDdMbnhaZmpTRXNiR200WE09IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJIcjZ4bXJ4R3ZxMkw0aEVvRnBqQ2ZQekpDRXQ2WGowd1A0VHU4ZmhiVmtCY1Jza3ZRRjZCTmx2b05iQUJHV29ja3o0NlRkN0xueFpmalNFc2JHbTRYTT0iLCJ0c19zaWduIjoidHMuMi5iN2I0MGEwMmM1Y2ZkYzZlYTkzMWFjMzUxY2Y3Yjc2ZTY4OTVmZjE2NTEyMmYxMTM2M2Q4NjE0YmQ5NTRmOGZkYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJKMmRGMkNGblVzclRRdGdyNlJDMVZxUXljQml4UXpFeDIzdzVsd3FYbmhJPSIsInNlY190cyI6IiNBVjR3NTRMalc4SzJlZ0pROXFJbjN1M05kUk5pUDB0NDdxd1RGZnVIejgvSDdRd0x5SEdaQUlIQ1g3MFEifQ%3D%3D; biz_trace_id=d8557a76; ttwid=1%7CkjDGZlhycsRWmiibhIAUXvoFIbPqZ3tLy-Mchrf6lRg%7C1772043172%7Cc02fff66ed45808cb8a1260118f39fbb5cdbee67764935bfe01091388eb10216; publish_badge_show_info=%220%2C0%2C0%2C1772043173699%22; odin_tt=3f77417351df557613a91d5a4e01060db63002f06bccee8febc1b5081159a87cbba68cd6a6a6ecab6c84e067ee27a09452f88836cc6c6ff884ac0c18b4d3eef7693bbc2419d5290bbdccfb8a8cb0189f; IsDouyinActive=false"

# 小红书 Cookie（必填，不填无法抓取）
# 打开 https://www.xiaohongshu.com 登录后获取
XIAOHONGSHU_COOKIE = "acw_tc=0a00d1a617720431795866886e6b5556c9a39cd76b4cd65424c20e75ddadd7; abRequestId=772c9842-644c-5535-9227-78bf73fbf9a1; webBuild=5.11.0; xsecappid=xhs-pc-web; loadts=1772043181130; a1=19c96011c4c85blzprotnwfia80bpogex6evr47id50000410549; webId=3f3f479d12a1516e54902459bf8366de; websectiga=29098a7cf41f76ee3f8db19051aaa60c0fc7c5e305572fec762da32d457d76ae; sec_poison_id=991e73af-c8c6-4c63-a871-29f923b8f885; gid=yjSjK8yJfdCfyjSjK8yySK4W4SY2D1uUFl9Id3fEi30Y8h28DUlkdF8884y824j8ydiKJYy8; web_session=040069b22b039837bc6bd673aa3b4b45e0cae0; id_token=VjEAAA7vL3uEkgFNx+sO4zdxWdZhkn9iSnFNKfzyHJqTzMApy/spRZAohrM2rLUs8QtUS1vKCCxDg/BlBx7aE2IQYSitCEoW2/wLsiLVTXi4NYTfyHoN434/LWvocr9t8D+zN2Ip; unread={%22ub%22:%22699db29d000000002801eebe%22%2C%22ue%22:%22699d6a0f000000000a033e5a%22%2C%22uc%22:22}"

# ============================================================
# LLM 配置（用于精筛和分析）
# 支持任意 OpenAI 兼容接口（DeepSeek、Qwen、OpenAI 等）
# ============================================================
LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里百炼
LLM_API_KEY = "sk-0ef56d1b3ba54a188ce28a46c54e2a24"                # 百炼 API Key
LLM_MODEL = "qwen-plus"                          # 模型名称
LLM_TIMEOUT = 60                                     # 请求超时（秒）
LLM_BATCH_SIZE = 50                                  # 每批发送给 LLM 的评论数

# 常用模型列表（GUI下拉选择用）
AVAILABLE_MODELS = [
    # 阿里百炼
    "deepseek-v3",
    "deepseek-v3.1",
    "qwen-plus",
    "qwen-turbo",
    "qwen-max",
    "qwen-max-long",
    # OpenAI
    "gpt-3.5-turbo",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    # Anthropic
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    # DeepSeek
    "deepseek-chat",
    "deepseek-coder",
    # 智谱
    "glm-4",
    "glm-4-flash",
    "glm-4-plus",
]

# 常用API地址列表（GUI下拉选择用）
AVAILABLE_API_URLS = [
    # 阿里百炼
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # DeepSeek
    "https://api.deepseek.com/v1",
    # OpenAI
    "https://api.openai.com/v1",
    # 智谱
    "https://open.bigmodel.cn/api/paas/v4",
    # Anthropic
    "https://api.anthropic.com/v1",
    # 月之暗面
    "https://api.moonshot.cn/v1",
    # 硅基流动
    "https://api.siliconflow.cn/v1",
]

# ============================================================
# 爬虫配置
# ============================================================
# 速度档位：控制请求间隔（秒）
#   fast   - 0.5~1s   延迟，速度最快，有风控风险
#   normal - 1.5~3s   延迟，默认推荐
#   slow   - 3~6s     延迟，更安全
#   safe   - 5~10s    延迟，最安全，适合大量抓取
SPEED_PRESETS = {
    "fast": (0.5, 1.0),
    "normal": (1.5, 3.0),
    "slow": (3.0, 6.0),
    "safe": (5.0, 10.0),
}
DEFAULT_SPEED = "safe"

# 默认抓取数量
DEFAULT_MAX_SEARCH = 5       # 每平台最大搜索结果数
DEFAULT_MAX_COMMENTS = 50    # 每内容最大评论数

# 请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

# ============================================================
# 筛选配置
# ============================================================
# Layer 1 规则粗筛
LAYER1_CONFIG = {
    "min_likes": 10,           # 最低点赞数
    "min_comments": 5,         # 最低评论数
    "min_views": 100,          # 最低播放量
    "duplicate_threshold": 0.85,  # 重复内容相似度阈值

    # 广告关键词
    "ad_keywords": [
        "私信", "加微", "VX", "vx", "微信", "wx", "WX",
        "优惠", "限时", "折扣", "福利", "免费领", "领取",
        "加群", "进群", "群聊", "合作", "商务",
    ],

    # 标题党关键词
    "clickbait_keywords": [
        "震惊", "必看", "绝了", "太强了", "99%", "90%",
        "最后一个", "第一个", "千万别", "一定要",
        "真相", "内幕", "揭秘", "曝光",
    ],
}

# Layer 2 LLM 精筛
LAYER2_CONFIG = {
    "min_score": 3,            # 最低相关性评分（1-5）
    "require_substance": True, # 是否要求有实质性内容
    "batch_size": 50,          # LLM 批处理大小（与 LLM_BATCH_SIZE 保持一致）
}

# ============================================================
# 统计配置
# ============================================================
STATS_CONFIG = {
    "default_time_range": "7d",  # 默认时间范围
    "kol_avg_likes": 50,         # KOL 判定：平均点赞阈值
    "kol_total_likes": 500,      # KOL 判定：总点赞阈值
}

# ============================================================
# GUI 配置
# ============================================================
GUI_HOST = "127.0.0.1"
GUI_PORT = 7860

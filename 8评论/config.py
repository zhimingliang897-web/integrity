"""
配置文件 — 在此处填写各平台的 Cookie

获取 Cookie 的方法:
1. 用浏览器打开对应平台网页版并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面，随便点击一个请求
5. 在 Request Headers 中找到 Cookie 字段，复制整个值粘贴到下方
"""

# B站 Cookie（可选，不填也能抓取，但填了可以获取更多数据）
BILIBILI_COOKIE = "buvid3=366A8B9D-74CF-18E2-C49F-531935EAF4CE17752infoc; b_nut=1764733617; _uuid=FA1F7B84-883C-7A61-2A64-110C5C349476F19091infoc; buvid_fp=f314530e39492c106496f55ee2d5d9bd; buvid4=EFAF5E53-1909-CF6F-E31D-A780427E380A21923-025120311-E01RxLbVkYdNRmZstxvq4Q%3D%3D; DedeUserID=35106543; DedeUserID__ckMd5=a00be45236c41e98; theme-tip-show=SHOWED; rpdid=|(J~JkmYkYkl0J'u~YR~JJY)~; theme-avatar-tip-show=SHOWED; hit-dyn-v2=1; CURRENT_QUALITY=80; SESSDATA=d1ee983c%2C1786248463%2C4037f%2A21CjBJrQN8E2E8rYEU8PsFCP1wdY-5MdfDHMCaTK49D9LR37XeugRsLa4upw1kzQqtJTkSVlpodTQ1T05JQUI3TDVEdnpRaWphVXN0MFgxYnJoTW9BN0hmVkhnY1lLS0ZVVUp6MUZfbl83QUxjZkhnb2FSdk9NQU9DSWJUc1Z3a3dzRDZXQ3QxTXdRIIEC; bili_jct=1817cab27443cf63d0bb8a71031a57f8; bp_t_offset_35106543=1167727820244254720; bsource=search_bing; bmg_af_switch=1; bmg_src_def_domain=i0.hdslb.com; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzExMzgyNjEsImlhdCI6MTc3MDg3OTAwMSwicGx0IjotMX0.654AdaB46QpY4_UXMGIqpGpKMTtt7581oJg8vHvgPY0; bili_ticket_expires=1771138201; CURRENT_FNVAL=2000; sid=7v8lw3kf; home_feed_column=4; browser_resolution=286-956; b_lsid=0A10C9DF_19C509E208E"

# 抖音 Cookie（必填，不填无法抓取）
# 打开 https://www.douyin.com 登录后获取
DOUYIN_COOKIE = "gd_random=eyJtYXRjaCI6dHJ1ZSwicGVyY2VudCI6MC4xMzI5NTAzNTE3OTEwNTMwOH0=.nUrdkYxT0TcpCsryCqOf164JiJ1bdWUwPvFkTxOaOlo=; __ac_nonce=0699712e10082a04bf7f8; __ac_signature=_02B4Z6wo00f01xT3zhAAAIDCQHDuVohdQJMU1-qAAKy198; enter_pc_once=1; UIFID_TEMP=1095a6dff7695ad7d7bcf6d11c9f5d2a106aea3524d1e5d99f3ea5d6bdd8961748a91f846752c0b79b66273efe56807f06f7a6e5d8c034da2ee6e64bce22ed80619302e1cef97b44275282f172e0b71d; x-web-secsdk-uid=cadeca67-f0c3-4f4c-a357-6cd5eb87a0a3; s_v_web_id=verify_mltie52h_A0xJCzhp_WExI_4n1m_BxtF_KGqwRH51YfRf; volume_info=%7B%22isMute%22%3Atrue%2C%22isUserMute%22%3Atrue%2C%22volume%22%3A0.5%7D; device_web_cpu_core=12; device_web_memory_size=8; architecture=amd64; hevc_supported=true; home_can_add_dy_2_desktop=%220%22; dy_swidth=1280; dy_sheight=720; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A720%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A12%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22; strategyABtestKey=%221771508453.483%22; record_force_login=%7B%22timestamp%22%3A1771508454466%2C%22force_login_video%22%3A1%2C%22force_login_live%22%3A0%2C%22force_login_direct_video%22%3A0%7D; passport_csrf_token=02405ea9e4d8f869b3fdda681a02e3aa; passport_csrf_token_default=02405ea9e4d8f869b3fdda681a02e3aa; is_dash_user=1; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCRUtHV05haldLdnR6Ymp6ejE4TG1RcC91YXVFcVJ0VDl3K21uTndHV3Q4L1pVcDc0M0xGRVdyRGxsRGtjcjNKT1dKSHEvczlGaGFIK3ZPeGd2T3pFdlU9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_web_domain=2; fpk1=U2FsdGVkX1/NYIh+swkem5vwzbnYiJKpJtmNnPIZnW0kHBgcGkMFJgTh47Dz8U52GcYVdhKGKqeEXHk6gIpROA==; fpk2=7c73ef5b8d3235ae0606f2e84e457ff5; ttwid=1%7CvQVTyLtn52vxfpuZp2m5wTSpDe-22Ml8VDydfvFrP0o%7C1771508456%7C39a1d45c4e66a4cb765bae4744934dce77fbbf13a13e8550cd10ae35dfdbd968; sdk_source_info=7e276470716a68645a606960273f276364697660272927676c715a6d6069756077273f276364697660272927666d776a68605a607d71606b766c6a6b5a7666776c7571273f275e58272927666a6b766a69605a696c6061273f27636469766027292762696a6764695a7364776c6467696076273f275e592772606761776c7360775927582729277672715a646971273f2763646976602729277f6b5a666475273f2763646976602729276d6a6e5a6b6a716c273f2763646976602729276c6b6f5a7f6367273f27636469766027292771273f27303d3d3330313d353034323234272927676c715a75776a716a666a69273f2763646976602778; bit_env=EfdZivlAl-bNzjljSDMT5I16_ldHLJ3VGfc21GQPg5XmkaKKYkzKA0j5BwrX48fDLMVkNu1tf8xD2OQ8sxbVvBooaNkWi_pj7wHCSNur_Q4V6NPddXFiDEVii_ACUPNREJEDbrK9j2_28buC6BCZdekRwau2giZaIBMjQZIq-X0XdbJDOleqonY5-K6RXs0FQiqpaNZGUXV1lnlfy-CrMqai6nYfmCGRLZH899xEsdnJ3uevp0uD-1s7tsm8kDMMfm_4RlHbSUfy2un6z2O-b-MMv7VsJiv9brfSE5Dwql9iMBG0R9YELnvNg1Dn9T76fJ6mot3wdLK709eUFYd3D-n-u0jq-stniU6-flbWtwLwUMzlldOwnIWtkLWLLoUo3QQ4NxGkTVTsHE2Ng42YjLSNtRes5jsq3wPMiNX8aZ9GsyqgDBIa0c0eIArcJxVkOwoPV8a-dnS-JTLA_QR-xKTPEXkPz7uWJrpSPMjB6x80Cn14xMX8GQzyMcSALktd; gulu_source_res=eyJwX2luIjoiMTM2MDYwZmNhNGM1MWJkZTdhZTRiYjY1Yzk1ZWNhZTRiNjI3MzcyYTk3NDlhZmY4MTBiNThiZjcwZDZlZjZjNSJ9; passport_auth_mix_state=72l8n1en9i83tba60tjuqoz02pbdtxbm; passport_mfa_token=CjeXRVTSP7JvDjfUG5%2BNGArdLCrBDZtotuu6qdVqNg7PUii8mEoO0mm5G17EbOk7KqnyhubbkPewGkoKPAAAAAAAAAAAAABQF12Fn2TGOHHQLR7c6a76LPaax7Q8iyJd1%2FvvN1VGdH3%2Bc3GcNx9XSD74qxTkHUObrhC9h4oOGPax0WwgAiIBAwiI7mc%3D; d_ticket=0ed91aba5f71c2a7f67e781dd39a0adc065d1; odin_tt=1383440e6442016c4cff47541c2eda29187ea9941735fab7ed7dcbdff7f33a1da40ddbd74015fcd41074d34eea7f40523206144cbe1a3f9d841af3851304f88e; passport_assist_user=CkGlBBfoYl1QQTrtoXM-FidUqb020NihgD_8c7cyDvamJQKn8bBfgr_K_mGVjPGwuovzxgHuGi72kqmaT03m8JQsIhpKCjwAAAAAAAAAAAAAUBcgf_5AL_tq-BL8GSNFYguVa1u4mQvCHduPDqwevYUG3TZRDWo4UawtX3nUMCMeJDwQvYeKDhiJr9ZUIAEiAQN9c_oF; n_mh=t8gkCNWIdtsOddp1wxcZHVe-6xeRg5WvNyTvRCIGC5g; passport_auth_status=8728653f60522a173c860e150382eca6%2C; passport_auth_status_ss=8728653f60522a173c860e150382eca6%2C; sid_guard=e43c65fda16291296490491642ffa49c%7C1771508485%7C5184000%7CMon%2C+20-Apr-2026+13%3A41%3A25+GMT; uid_tt=8df34be88efaab675ba26f0a367bac17; uid_tt_ss=8df34be88efaab675ba26f0a367bac17; sid_tt=e43c65fda16291296490491642ffa49c; sessionid=e43c65fda16291296490491642ffa49c; sessionid_ss=e43c65fda16291296490491642ffa49c; session_tlb_tag=sttt%7C14%7C5Dxl_aFikSlkkEkWQv-knP_________uhZcWZFTXvrNIrMsCXI6aORFdU3k1Fri5aIJAwu5GxvU%3D; is_staff_user=false; sid_ucp_v1=1.0.0-KDJkNTk4Y2MzNzA5ZGI3MjAzMjY4NGIyZmFkOWJkZjMzNzg0NWRhYTIKIQjA9cD8ufTjAhCFptzMBhjvMSAMMJD35_kFOAJA8QdIBBoCbHEiIGU0M2M2NWZkYTE2MjkxMjk2NDkwNDkxNjQyZmZhNDlj; ssid_ucp_v1=1.0.0-KDJkNTk4Y2MzNzA5ZGI3MjAzMjY4NGIyZmFkOWJkZjMzNzg0NWRhYTIKIQjA9cD8ufTjAhCFptzMBhjvMSAMMJD35_kFOAJA8QdIBBoCbHEiIGU0M2M2NWZkYTE2MjkxMjk2NDkwNDkxNjQyZmZhNDlj; _bd_ticket_crypt_doamin=2; _bd_ticket_crypt_cookie=746e72bb7334707a5f6ac4715de10d20; __security_mc_1_s_sdk_sign_data_key_web_protect=bca4a58b-43eb-a055; __security_mc_1_s_sdk_cert_key=ea6edbda-4e1c-bdfd; __security_mc_1_s_sdk_crypt_sdk=6649da04-4182-b84b; __security_server_data_status=1; login_time=1771508485672; biz_trace_id=17a4c180; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJFS0dXTmFqV0t2dHpianp6MThMbVFwL3VhdUVxUnRUOXcrbW5Od0dXdDgvWlVwNzQzTEZFV3JEbGxEa2NyM0pPV0pIcS9zOUZoYUgrdk94Z3ZPekV2VT0iLCJ0c19zaWduIjoidHMuMi44Y2E5ZTk1ODk5NzEwODViNjUzYTQ4N2Q1NTNhMDhmZDVmZjYwM2UzZjBkNzkzOTRhMDU1MGIwZGY4NDljODIwYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJ6OC9McllYbC9teUNUeG9YZ2xQVEFxQWdGc3lnTW9yL0ZORXduNmViSytFPSIsInNlY190cyI6IiN5V3JYRk96ZWlqSXlicm9DditJUUZ4VUQ4VUdFL2RvV2dpVUVsRUFtNkRGS0ZzVTFXM2hBeEw4ZWYyY3oifQ%3D%3D; UIFID=1095a6dff7695ad7d7bcf6d11c9f5d2a106aea3524d1e5d99f3ea5d6bdd8961748a91f846752c0b79b66273efe56807f55fddbaf5675e876064842bfcce050c0e912262a30fe4993774fb28bb3a900fe84799949ad9dfd19fc0f3f706bdb00b3ab0d6da6f8211567115dc55742665f4ce07a44ba255397077564618a24ac3ae1d6cb5856c86ccba9e9b3cb724fa5b49cc6dd3e8b098b778b7de81e6ea98b6208; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A0%7D%22; IsDouyinActive=true"

# 小红书 Cookie（必填，不填无法抓取）
# 打开 https://www.xiaohongshu.com 登录后获取
XIAOHONGSHU_COOKIE = "abRequestId=b7b54a42-ef20-5e87-937d-64a1dde77ca4; xsecappid=xhs-pc-web; a1=19c468e87d8i4fkhdkq0t52hhzst78mv8yenyvs6i50000561501; webId=0a7a9d3de035ccb6c41e44e390c81e9c; gid=yjS4KYdjDjYyyjS4KYdYWvhMfY34iTxfTA89dK32JxxuMI289WY6hv8882Ky28y82jDW428W; webBuild=5.11.0; web_session=040069b22b039837bc6b123eb83b4b6f2cf850; id_token=VjEAAGJxGiAE/deALjvsuIY+2PYfU0bU9sxKE7AbusRGTCm5CBW/qHWTvEF462gcm3UNeiHSB9hkqIH8HfHFBhLQ1eOmanKw7mhCslXb4Soqi1D6xle5yijYWu3cww6KdPNIzHlA; loadts=1770878597947; unread={%22ub%22:%22698d2b6c000000001a0299d3%22%2C%22ue%22:%226982ed31000000000a02ddeb%22%2C%22uc%22:29}; websectiga=7750c37de43b7be9de8ed9ff8ea0e576519e8cd2157322eb972ecb429a7735d4"

# 导出设置
OUTPUT_DIR = "output"       # 导出目录
OUTPUT_FORMAT = "csv"       # 导出格式: "csv" 或 "excel"

# 速度档位: "fast" / "normal" / "slow" / "safe"
#   fast   - 0.5~1s   延迟，速度最快，有风控风险
#   normal - 1.5~3s   延迟，默认推荐
#   slow   - 3~6s     延迟，更安全
#   safe   - 5~10s    延迟，最安全，适合大量抓取
DEFAULT_SPEED = "safe"


# ========== LLM 配置 ==========
# 支持任意 OpenAI 兼容接口（DeepSeek、Qwen、OpenAI 等）
# 修改 base_url 和 model 即可切换不同服务商

LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里百炼
LLM_API_KEY = "sk-0ef56d1b3ba54a188ce28a46c54e2a24"                # 百炼 API Key
LLM_MODEL = "deepseek-v3.1"                          # 模型名称（百炼支持: qwen-plus / qwen-turbo / qwen-max / deepseek-v3 等）
LLM_BATCH_SIZE = 50                              # 每批发送给 LLM 的评论数

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


# ========== 话题搜索配置 ==========
TOPIC_MAX_SEARCH = 5        # 每个平台默认搜索结果数
TOPIC_MAX_COMMENTS = 50     # 每个内容默认抓取评论数

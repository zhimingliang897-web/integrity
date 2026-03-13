# 🚨 紧急安全修复清单

**创建日期**: 2026-03-13  
**状态**: 待执行  
**预计完成**: 1-2天内

---

## ⚡ 立即执行（今天必须完成）

### 1. 更改服务器密码 🔴
```bash
# SSH登录服务器
ssh root@8.138.164.133

# 更改密码
passwd

# 使用强密码（至少16位，包含大小写字母、数字、特殊字符）
```

- [ ] 密码已更改
- [ ] 新密码已安全保存（使用密码管理器）
- [ ] 验证新密码可以登录

---

### 2. 轮换API Key 🔴
```bash
# 1. 登录阿里云控制台
# 2. 进入DashScope管理页面
# 3. 生成新的API Key
# 4. 删除旧的API Key
```

- [ ] 新API Key已生成
- [ ] 服务器环境变量已更新
- [ ] 旧API Key已删除
- [ ] 验证API功能正常

---

### 3. 移除代码中的硬编码密码 🔴

**需要修改的文件**:

#### 文件1: `docs/server/deploy_ssh.py`
```python
# 删除第8行的硬编码密码
# PASSWORD = '15232735822Aa'  # ❌ 删除这行

# 改为:
PASSWORD = os.environ.get('SSH_PASSWORD')
if not PASSWORD:
    raise ValueError("请设置SSH_PASSWORD环境变量")
```

- [ ] 已修改 deploy_ssh.py

---

#### 文件2-5: 移除API Key默认值

修改以下文件，移除硬编码的API Key:
- `docs/server/app/tools/video_maker.py:43`
- `docs/server/app/tools/image_prompt.py:32`
- `docs/server/app/tools/ai_compare.py:21`
- `docs/server/app/tools/dialogue_learning.py:52`

```python
# 从:
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'sk-0ef56d1b3ba54a188ce28a46c54e2a24')

# 改为:
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY')
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY environment variable is required")
```

- [ ] 已修改 video_maker.py
- [ ] 已修改 image_prompt.py
- [ ] 已修改 ai_compare.py
- [ ] 已修改 dialogue_learning.py

---

#### 文件6+: 移除JWT Secret默认值

在所有工具文件中搜索并修改:
```bash
# 搜索包含默认secret的文件
grep -r "integrity-lab-secret-key-2026" docs/server/app/tools/
```

```python
# 从:
secret = flask.current_app.config.get('SECRET_KEY', 'integrity-lab-secret-key-2026')

# 改为:
secret = flask.current_app.config.get('SECRET_KEY')
if not secret:
    raise ValueError("SECRET_KEY not configured")
```

- [ ] 已搜索所有文件
- [ ] 已移除所有默认值

---

### 4. 提交代码修改 🔴

```bash
cd /Users/lzm/macbook_space/integrity

# 查看修改
git status
git diff

# 提交修改
git add docs/server/
git commit -m "security: 移除硬编码的密码和API Key

- 删除deploy_ssh.py中的SSH密码
- 移除所有工具文件中的API Key默认值
- 移除JWT Secret的默认值
- 所有敏感信息改为从环境变量读取"

# 推送到远程
git push
```

- [ ] 代码已提交
- [ ] 代码已推送

---

### 5. 更新服务器配置 🔴

```bash
# SSH登录服务器
ssh root@8.138.164.133

# 创建.env文件
cat > /root/integrity-api/server/.env << 'ENVEOF'
SECRET_KEY=<生成一个强密钥>
DASHSCOPE_API_KEY=<新的API Key>
INVITE_CODES=<新的邀请码>
ENVEOF

# 拉取最新代码
cd /root/integrity-api/server
git pull

# 重启服务
pkill gunicorn
SECRET_KEY=$(cat .env | grep SECRET_KEY | cut -d= -f2) \
DASHSCOPE_API_KEY=$(cat .env | grep DASHSCOPE_API_KEY | cut -d= -f2) \
INVITE_CODES=$(cat .env | grep INVITE_CODES | cut -d= -f2) \
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 app.main:app --daemon \
  --error-logfile /root/integrity-api/server/gunicorn.error.log \
  --access-logfile /root/integrity-api/server/gunicorn.access.log
```

- [ ] .env文件已创建
- [ ] 代码已更新
- [ ] 服务已重启
- [ ] 验证服务正常运行

---

## 🔄 明天执行（第2天）

### 6. 清理Git历史 🔴

**⚠️ 警告**: 这会改写Git历史，需要谨慎操作

```bash
# 安装BFG Repo-Cleaner
brew install bfg

# 备份仓库
cd /Users/lzm/macbook_space
cp -r integrity integrity-backup

# 克隆镜像
git clone --mirror https://github.com/zhimingliang897-web/integrity.git

# 创建要替换的敏感信息列表
cat > passwords.txt << 'PWDEOF'
15232735822Aa
sk-0ef56d1b3ba54a188ce28a46c54e2a24
integrity-lab-secret-key-2026
PWDEOF

# 清理敏感信息
bfg --replace-text passwords.txt integrity.git

# 清理引用
cd integrity.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送（需要确认）
# git push --force
```

- [ ] 已备份仓库
- [ ] 已安装BFG
- [ ] 已清理历史
- [ ] 已强制推送（需要团队确认）

---

### 7. 配置域名和SSL 🟠

```bash
# 1. 配置域名解析
# 在域名管理后台添加A记录:
# api.liangyiren.top -> 8.138.164.133

# 2. 在服务器上安装Nginx和Certbot
ssh root@8.138.164.133
apt update
apt install nginx certbot python3-certbot-nginx

# 3. 配置SSL证书
certbot --nginx -d api.liangyiren.top

# 4. 配置Nginx反向代理
# (详见 PROJECT_IMPROVEMENT_PLAN.md)
```

- [ ] 域名解析已配置
- [ ] SSL证书已安装
- [ ] Nginx已配置
- [ ] 验证HTTPS访问正常

---

### 8. 更新前端配置 🟠

```bash
# 批量替换IP为域名
cd /Users/lzm/macbook_space/integrity
find docs -type f \( -name "*.html" -o -name "*.js" \) -exec sed -i '' 's|http://8.138.164.133:5000|https://api.liangyiren.top|g' {} +

# 提交修改
git add docs/
git commit -m "refactor: 使用域名替代硬编码IP地址"
git push
```

- [ ] IP已替换为域名
- [ ] 代码已提交推送
- [ ] 验证前端功能正常

---

## ✅ 验收标准

完成以上所有任务后，确认:

- [ ] 服务器密码已更改，旧密码无法登录
- [ ] API Key已轮换，旧Key已删除
- [ ] 代码中无任何硬编码的密码或API Key
- [ ] Git历史已清理（可选，需谨慎）
- [ ] 使用HTTPS域名访问API
- [ ] 所有工具功能正常运行
- [ ] 前端页面正常访问

---

## 📋 快速检查命令

```bash
# 检查代码中是否还有敏感信息
cd /Users/lzm/macbook_space/integrity
grep -r "15232735822Aa" .
grep -r "sk-0ef56d1b3ba54a188ce28a46c54e2a24" .
grep -r "integrity-lab-secret-key-2026" docs/server/app/tools/

# 检查服务器状态
curl https://api.liangyiren.top/

# 检查API功能
curl -X POST https://api.liangyiren.top/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"lzm","password":"123456"}'
```

---

## 📞 遇到问题？

如果遇到问题，请参考详细文档:
- 完整改进方案: `PROJECT_IMPROVEMENT_PLAN.md`
- 或提交GitHub Issue

---

**最后更新**: 2026-03-13
